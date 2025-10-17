import pathlib
import numpy as np
import os
import re

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


def generate_moqui_csvs(rt_plan_data: dict,
                        ptn_data_list: list[dict],
                        dose_monitor_ranges: list[int],
                        output_base_dir: str,
                        dose_dividing_factor: int = 10):
    """
    Generates CSV files for MOQUI based on RTPLAN and processed PTN log data.
    Uses log-based approach: directly uses time, position, and MU data from PTN files.

    Args:
        rt_plan_data: Dictionary containing parsed RTPLAN data.
        ptn_data_list: List of dictionaries, where each dictionary is the
                       output of parse_ptn_file, corresponding to an energy layer.
        dose_monitor_ranges: List of integers representing monitor range codes,
                             corresponding to each energy layer.
        output_base_dir: Base directory for creating output files.
        dose_dividing_factor: Factor to divide dose values (default: 10).

    Raises:
        KeyError: If essential keys are missing from input data.
        IndexError: If ptn_data_list or dose_monitor_ranges are shorter than
                    the total number of energy layers.
        IOError: If directory or file creation fails.
        RuntimeError: If interpolators are not available.
    """
    if PROTON_DOSE_INTERPOLATOR is None or MU_COUNT_DOSE_INTERPOLATOR is None:
        print("Warning: Interpolators are not available. MU corrections will not be applied.")
        use_interpolation = False
    else:
        use_interpolation = True

    try:
        beams = rt_plan_data["beams"]
    except KeyError as e:
        raise KeyError(f"Error: Missing essential key {e} in rt_plan_data.")

    # Create separate directories for Plan and Log data
    base_dir = pathlib.Path(output_base_dir)
    plan_base_dir = base_dir / "plan"
    log_base_dir = base_dir / "log"
    
    global_data_idx = 0

    for beam_idx, beam in enumerate(beams):
        try:
            beam_name = beam["beam_name"]
            beam_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', beam_name)
            energy_layers = beam["energy_layers"]
            is_setup_field = beam.get("is_setup_field", False)
        except KeyError as e:
            raise KeyError(f"Error: Missing essential key {e} in beam data for beam index {beam_idx}.")

        plan_field_dir = plan_base_dir / beam_name
        log_field_dir = log_base_dir / beam_name
        try:
            plan_field_dir.mkdir(parents=True, exist_ok=True)
            log_field_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise IOError(f"Error creating directory {field_dir}: {e}")

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

            # Apply MU Corrections using log-based approach (matching C++ MOQUIThread)
            # Use dose1_au from PTN as the raw MU count
            corrected_mu = dose1_au.astype(float)

            # Apply energy-dependent correction factors if available
            if use_interpolation:
                corrected_mu *= PROTON_DOSE_INTERPOLATOR(nominal_energy)
                corrected_mu *= MU_COUNT_DOSE_INTERPOLATOR(nominal_energy)

            # Apply monitor range factor
            corrected_mu *= monitor_range_factor

            # Apply dose dividing factor
            corrected_mu = corrected_mu / dose_dividing_factor

            # Round to integers
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
            
            # Write Plan CSV (interpolated)
            plan_csv_path = plan_field_dir / csv_file_name
            try:
                with open(plan_csv_path, 'w', encoding='utf-8') as f:
                    if interpolated_rtplan_data:
                        # Flatten the list of lists into a single list of values
                        all_values = [item for sublist in interpolated_rtplan_data for item in sublist]
                        # Convert all values to string and join with a comma
                        output_string = ",".join(map(str, all_values))
                        f.write(output_string)
            except IOError as e:
                raise IOError(f"Error writing Plan CSV file {plan_csv_path}: {e}")
            except Exception as e:
                raise RuntimeError(f"An unexpected error occurred while writing Plan CSV {plan_csv_path}: {e}")

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