import pathlib
import numpy as np
import csv
import os # For os.makedirs in older Python if needed, though pathlib is preferred
import re
from functools import lru_cache

# Attempt to import interpolators
try:
    from processing.interpolation import (
        PROTON_DOSE_INTERPOLATOR,
        MU_COUNT_DOSE_INTERPOLATOR
    )
except ImportError:
    # This allows the module to be imported for basic linting/viewing even if dependencies are missing,
    # but functions using these will fail at runtime if they are None.
    print("Warning: Could not import interpolators from processing.interpolation.")
    print("Ensure numpy and scipy are installed and the processing package is structured correctly.")
    PROTON_DOSE_INTERPOLATOR = None
    MU_COUNT_DOSE_INTERPOLATOR = None

# Constants from Dicom_reader_F.py
MIN_DOSERATE = 1.4  # (MU/s)    
MAX_SPEED = 20.0 * 100  # (cm/s)
MIN_SPEED = 0.1 * 100  # (cm/s)
TIME_RESOLUTION = 0.1/1000  # (s) = 0.1ms

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
DOSERATE_TABLE_PATH = SCRIPT_DIR / 'LS_doserate.csv'

def get_monitor_range_factor(monitor_range_code: int) -> float:
    """
    Determines the monitorRangeFactor based on the monitor_range_code.
    Codes and values from C++ Moqui code options.
    """
    if monitor_range_code == 2:
        return 1.0
    elif monitor_range_code == 3:
        return 2.978723404255319
    elif monitor_range_code == 4:
        return 8.936170212765957
    elif monitor_range_code == 5:
        return 26.80851063829787
    else:
        # Default or error based on strictness. C++ code defaults to 1.0 if not recognized.
        print(f"Warning: Unrecognized monitor_range_code {monitor_range_code}. Defaulting factor to 1.0.")
        return 1.0

@lru_cache(maxsize=1)
def _load_doserate_table() -> np.ndarray:
    """선량율 테이블을 로드하고 캐싱 (한 번만 로드)"""
    try:
        return np.loadtxt(DOSERATE_TABLE_PATH, delimiter=',', encoding='utf-8-sig')
    except FileNotFoundError:
        print(f"Warning: 선량율 테이블 파일을 찾을 수 없습니다: {DOSERATE_TABLE_PATH}")
        return np.array([])
    except ValueError:
        print("Warning: 선량율 테이블 형식이 올바르지 않습니다.")
        return np.array([])
    except Exception as e:
        print(f"Warning: 선량율 테이블 로드 오류: {e}")
        return np.array([])

@lru_cache(maxsize=64)
def get_doserate_for_energy(energy: float) -> float:
    """에너지에 대한 선량율 반환 (캐싱 활용)"""
    LS_doserate = _load_doserate_table()
    if LS_doserate.size == 0:
        return MIN_DOSERATE  # 기본값 사용
        
    # 해당 에너지에 대한 선량율 찾기
    mask = (LS_doserate[:, 0] >= energy + 0.0) & (LS_doserate[:, 0] < energy + 0.3)
    max_doserate_ind = np.where(mask)[0]
    
    if len(max_doserate_ind) > 0:
        max_doserate = LS_doserate[max_doserate_ind[0], 1]
        return max_doserate
    return MIN_DOSERATE  # 기본값 사용

def calculate_layer_doserate(positions: np.ndarray, weights: np.ndarray, energy: float) -> float:
    """
    Calculate layer dose rate based on Dicom_reader_F.py logic
    
    Args:
        positions: Position array (n, 2)
        weights: Weight array (n,)
        energy: Energy in MeV
        
    Returns:
        Layer dose rate in MU/s
    """
    if len(positions) <= 1 or len(weights) <= 1:
        return MIN_DOSERATE
        
    # Calculate distances between consecutive positions
    diff_vectors = np.diff(positions, axis=0)
    distances = np.sqrt(np.sum(diff_vectors**2, axis=1))  # in cm
    
    # Calculate MU per distance for each segment (skip first segment)
    segments_weights = weights[1:]  # weights for segments (starting from index 1)
    
    # MU/cm calculation (vectorized)
    mu_per_dist = np.zeros_like(segments_weights)
    mask = distances > 0
    mu_per_dist[mask] = segments_weights[mask] / distances[mask]
    
    # Temporary dose rates calculation
    dose_rates = MAX_SPEED * mu_per_dist
    
    # Get doserate_provider from energy table
    doserate_provider = get_doserate_for_energy(energy)
    
    # Determine layer dose rate
    if len(dose_rates) > 0:
        valid_dose_rates = dose_rates[dose_rates > 0]  # Exclude zeros
        if len(valid_dose_rates) > 0:
            min_dr = np.min(valid_dose_rates)
            if min_dr < MIN_DOSERATE:
                layer_doserate = MIN_DOSERATE
            elif min_dr > doserate_provider:
                layer_doserate = doserate_provider
            else:
                layer_doserate = min_dr
        else:
            layer_doserate = MIN_DOSERATE
    else:
        layer_doserate = MIN_DOSERATE
        
    return layer_doserate

def interpolate_rtplan_data(beam: dict, time_step_ms: float = 0.06) -> list:
    """
    Interpolates RT Plan data to generate time-series data based on Dicom_reader_F.py logic.
    
    Args:
        beam: A dictionary containing the beam data, including control_point_details.
        time_step_ms: The time step for interpolation in milliseconds (default: 0.06).

    Returns:
        A list of lists, where each inner list contains [time_ms, x_mm, y_mm, mu].
    """
    interpolated_data = []

    if not beam.get("control_point_details"):
        print(f"Warning: No control point details found for beam {beam.get('beam_name')}. Skipping interpolation.")
        return interpolated_data
    
    total_time_ms = 0.0
    
    for cp_detail in beam.get("control_point_details", []):
        spot_positions = cp_detail['scan_spot_positions']
        spot_weights = cp_detail['scan_spot_meterset_weights']
        energy = cp_detail['energy']
        
        if len(spot_positions) == 0 or len(spot_weights) == 0:
            continue
            
        num_spots = len(spot_weights)
        if num_spots * 2 != len(spot_positions):
            print(f"Warning: Mismatch in scan spot positions and weights for a control point. Skipping.")
            continue

        # Convert to numpy arrays and reshape positions
        positions_array = np.array(spot_positions).reshape(-1, 2)  # Convert mm to cm (positions are already in mm from parser)
        weights_array = np.array(spot_weights)
        
        # Calculate layer dose rate using Dicom_reader_F.py logic
        layer_doserate = calculate_layer_doserate(positions_array, weights_array, energy)
        
        # Create line segments and calculate scan times
        if len(positions_array) <= 1:
            continue
            
        # Calculate distances between consecutive positions
        diff_vectors = np.diff(positions_array, axis=0)
        distances = np.sqrt(np.sum(diff_vectors**2, axis=1))  # distances in mm
        
        # Process each segment starting from index 1 (skip first position)
        for i in range(1, len(positions_array)):
            current_pos = positions_array[i]
            prev_pos = positions_array[i-1]
            current_weight = weights_array[i]
            distance = distances[i-1]
            
            # Calculate scan time using Dicom_reader_F.py logic
            if current_weight < 1e-7:
                raw_scan_time = distance / MAX_SPEED  # in seconds
            else:
                raw_scan_time = current_weight / layer_doserate  # in seconds
                
            # Round to TIME_RESOLUTION (0.1ms)
            rounded_scan_time = TIME_RESOLUTION * round(raw_scan_time / TIME_RESOLUTION)
            rounded_scan_time_ms = rounded_scan_time * 1000.0  # Convert to ms
            
            # Calculate speed
            if distance > 0:
                speed = distance / raw_scan_time  # mm/s
            else:
                speed = MAX_SPEED
            
            # Interpolate along the line segment
            if rounded_scan_time_ms > 0:
                num_steps = max(1, int(np.ceil(rounded_scan_time_ms / time_step_ms)))
                mu_per_step = current_weight / num_steps if num_steps > 0 else 0
                
                for step in range(num_steps):
                    step_time_ms = total_time_ms + (step + 1) * time_step_ms
                    
                    # Linear interpolation along line segment
                    progress = (step + 1) / num_steps
                    interp_x = prev_pos[0] + (current_pos[0] - prev_pos[0]) * progress
                    interp_y = prev_pos[1] + (current_pos[1] - prev_pos[1]) * progress
                    
                    interpolated_data.append([step_time_ms, interp_x, interp_y, mu_per_step])
                
                total_time_ms += rounded_scan_time_ms
            
    return interpolated_data

def generate_moqui_csvs(rt_plan_data: dict, 
                        ptn_data_list: list[dict], 
                        dose_monitor_ranges: list[int], 
                        output_base_dir: str):
    """
    Generates CSV files for Moqui based on RTPLAN and processed PTN log data.
    Creates separate folders:
    - RTPlan: Data from RT plan (no monitor range factor applied, no MU correction)
    - Log: Data from logs (with monitor range factor applied)

    Args:
        rt_plan_data: Dictionary containing parsed RTPLAN data.
        ptn_data_list: List of dictionaries, where each dictionary is the 
                       output of parse_ptn_file, corresponding to an energy layer.
        dose_monitor_ranges: List of integers representing monitor range codes,
                             corresponding to each energy layer.
        output_base_dir: Base directory for creating output files.

    Raises:
        KeyError: If essential keys are missing from input data.
        IndexError: If ptn_data_list or dose_monitor_ranges are shorter than
                    the total number of energy layers.
        IOError: If directory or file creation fails.
        RuntimeError: If interpolators are not available.
    """
    if PROTON_DOSE_INTERPOLATOR is None or MU_COUNT_DOSE_INTERPOLATOR is None:
        print("Warning: Interpolators are not available. Using default correction factors.")
        use_interpolation = False
    else:
        use_interpolation = True

    try:
        patient_id = rt_plan_data["patient_id"]
        beams = rt_plan_data["beams"]
    except KeyError as e:
        raise KeyError(f"Error: Missing essential key {e} in rt_plan_data.")

    # Create separate directories for RTPlan and Log data inside the patient directory
    rtplan_base_dir = pathlib.Path(output_base_dir) / "rtplan"
    log_base_dir = pathlib.Path(output_base_dir) / "log"
    
    global_data_idx = 0

    for beam_idx, beam in enumerate(beams):
        try:
            beam_name = beam["beam_name"] # For logging or more detailed dir names if needed
            beam_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', beam_name)
            energy_layers = beam["energy_layers"]
        except KeyError as e:
            raise KeyError(f"Error: Missing essential key {e} in beam data for beam index {beam_idx}.")

        rtplan_field_dir = rtplan_base_dir / beam_name
        log_field_dir = log_base_dir / beam_name
        try:
            rtplan_field_dir.mkdir(parents=True, exist_ok=True)
            log_field_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise IOError(f"Error creating directories: {e}")

        for layer_idx_in_beam, energy_layer in enumerate(energy_layers):
            if global_data_idx >= len(ptn_data_list):
                print(
                    f"Warning: Not enough PTN data entries. Needed for layer {global_data_idx + 1}, "
                    f"but only {len(ptn_data_list)} PTN data entries provided. Skipping remaining layers."
                )
                break
            if global_data_idx >= len(dose_monitor_ranges):
                print(
                    f"Warning: Not enough dose monitor range codes. Needed for layer {global_data_idx + 1}, "
                    f"but only {len(dose_monitor_ranges)} codes provided. Skipping remaining layers."
                )
                break

            ptn_data = ptn_data_list[global_data_idx]
            monitor_range_code = dose_monitor_ranges[global_data_idx]

            try:
                nominal_energy = float(energy_layer["nominal_energy"])
                # MU from rt_plan_data["energy_layers"]["mu"] is the total MU for this layer,
                # not used directly in this CSV generation per log point, but for context.
                
                dose1_au = ptn_data["dose1_au"] # This is an array of MU counts from the log for each time point
                time_ms = ptn_data["time_ms"]
                x_mm = ptn_data["x_mm"]
                y_mm = ptn_data["y_mm"]
            except KeyError as e:
                raise KeyError(
                    f"Error: Missing essential key {e} in PTN data for layer index {global_data_idx} "
                    f"(Beam {beam_idx+1}, Layer in beam {layer_idx_in_beam+1})."
                )
            except TypeError as e: # For float(nominal_energy) if it's not convertible
                 raise ValueError(
                    f"Error: Could not convert nominal_energy to float for layer index {global_data_idx}. Value: {energy_layer.get('nominal_energy')}. Error: {e}"
                )


            monitor_range_factor = get_monitor_range_factor(monitor_range_code)

            # Filter control points for the current energy layer
            all_beam_cps = beam.get("control_point_details", [])
            layer_nominal_energy = float(energy_layer["nominal_energy"])
            layer_cps = [cp for cp in all_beam_cps if float(cp['energy']) == layer_nominal_energy]

            # Create a temporary "beam-like" object for the layer to pass to the interpolator
            layer_beam_obj = {'control_point_details': layer_cps, 'beam_name': beam_name}
            
            # Prepare RTPlan data using interpolation for the layer
            # The layer dose rate is now calculated inside interpolate_rtplan_data function
            interpolated_rtplan_data = interpolate_rtplan_data(layer_beam_obj)

            if not interpolated_rtplan_data:
                print(f"Warning: Interpolation for beam {beam_name}, layer {layer_idx_in_beam+1} ({layer_nominal_energy} MeV) resulted in no data. Creating an empty CSV with a header.")

            # Apply MU Corrections for Log data
            # Assuming dose1_au from PTN is the raw MU count that needs correction
            corrected_mu = dose1_au.astype(float) 
            if use_interpolation:
                corrected_mu *= PROTON_DOSE_INTERPOLATOR(nominal_energy)
                corrected_mu *= MU_COUNT_DOSE_INTERPOLATOR(nominal_energy)
            else:
                # Use default correction factors when interpolation is not available
                corrected_mu *= 1.0  # Default proton/dose correction
                corrected_mu *= 1.0  # Default MU count/dose correction
            corrected_mu *= monitor_range_factor
            
            corrected_mu = np.round(corrected_mu).astype(int)

            # Prepare CSV Data
            # Ensure all arrays are 1D and have the same length
            if not (time_ms.ndim == 1 and x_mm.ndim == 1 and y_mm.ndim == 1 and corrected_mu.ndim == 1 and
                    len(time_ms) == len(x_mm) == len(y_mm) == len(corrected_mu)):
                raise ValueError(
                    f"Dimension mismatch in data for CSV generation for layer index {global_data_idx}. "
                    f"Shapes: time_ms={time_ms.shape}, x_mm={x_mm.shape}, y_mm={y_mm.shape}, corrected_mu={corrected_mu.shape}"
                )
            
            # CSV Filename
            csv_file_name = f"{layer_idx_in_beam + 1:02d}_{nominal_energy:.2f}MeV.csv"
            
            # Write RTPlan CSV (interpolated)
            rtplan_csv_path = rtplan_field_dir / csv_file_name
            try:
                with open(rtplan_csv_path, 'w', encoding='utf-8') as f:
                    if interpolated_rtplan_data:
                        # Flatten the list of lists into a single list of values
                        all_values = [item for sublist in interpolated_rtplan_data for item in sublist]
                        # Convert all values to string and join with a comma
                        output_string = ",".join(map(str, all_values))
                        f.write(output_string)
            except IOError as e:
                raise IOError(f"Error writing RTPlan CSV file {rtplan_csv_path}: {e}")
            except Exception as e:
                raise RuntimeError(f"An unexpected error occurred while writing RTPlan CSV {rtplan_csv_path}: {e}")

            # Write Log CSV (with monitor range factor)
            log_csv_path = log_field_dir / csv_file_name
            log_csv_rows = zip(time_ms, x_mm, y_mm, corrected_mu)
            try:
                with open(log_csv_path, 'w', encoding='utf-8') as f:
                    # Flatten the zipped rows into a single list of values
                    all_values = [item for row in log_csv_rows for item in row]
                    # Convert all values to string and join with a comma
                    output_string = ",".join(map(str, all_values))
                    f.write(output_string)
            except IOError as e:
                raise IOError(f"Error writing Log CSV file {log_csv_path}: {e}")
            except Exception as e:
                raise RuntimeError(f"An unexpected error occurred while writing Log CSV {log_csv_path}: {e}")

            global_data_idx += 1
            
    # Final check to ensure all ptn_data and dose_monitor_ranges were consumed if expected
    total_layers_in_plan = sum(len(b.get("energy_layers", [])) for b in beams)
    if global_data_idx != total_layers_in_plan:
        print(
            f"Warning: Number of processed layers ({global_data_idx}) does not match "
            f"total energy layers in RTPLAN ({total_layers_in_plan}). "
            f"Ensure ptn_data_list and dose_monitor_ranges match the plan structure."
        )

if __name__ == '__main__':
    pass