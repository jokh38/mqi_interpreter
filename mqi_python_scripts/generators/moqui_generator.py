import pathlib
import numpy as np
import csv
import os # For os.makedirs in older Python if needed, though pathlib is preferred

# Attempt to import interpolators
try:
    from mqi_python_scripts.processing.interpolation import (
        PROTON_DOSE_INTERPOLATOR,
        MU_COUNT_DOSE_INTERPOLATOR
    )
except ImportError:
    # This allows the module to be imported for basic linting/viewing even if dependencies are missing,
    # but functions using these will fail at runtime if they are None.
    print("Warning: Could not import interpolators from mqi_python_scripts.processing.interpolation.")
    print("Ensure numpy and scipy are installed and the mqi_python_scripts package is structured correctly.")
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
    Generates CSV files for Moqui based on RTPLAN and processed PTN log data.

    Args:
        rt_plan_data: Dictionary containing parsed RTPLAN data.
        ptn_data_list: List of dictionaries, where each dictionary is the 
                       output of parse_ptn_file, corresponding to an energy layer.
        dose_monitor_ranges: List of integers representing monitor range codes,
                             corresponding to each energy layer.
        output_base_dir: Base directory for creating output files.
        dose_dividing_factor: Factor to divide MU values by (default 10).

    Raises:
        KeyError: If essential keys are missing from input data.
        IndexError: If ptn_data_list or dose_monitor_ranges are shorter than
                    the total number of energy layers.
        IOError: If directory or file creation fails.
        RuntimeError: If interpolators are not available.
    """
    if PROTON_DOSE_INTERPOLATOR is None or MU_COUNT_DOSE_INTERPOLATOR is None:
        raise RuntimeError("Interpolators are not available. Cannot proceed with MU corrections.")

    try:
        patient_id = rt_plan_data["patient_id"]
        beams = rt_plan_data["beams"]
    except KeyError as e:
        raise KeyError(f"Error: Missing essential key {e} in rt_plan_data.")

    patient_dir = pathlib.Path(output_base_dir) / str(patient_id)
    
    global_data_idx = 0

    for beam_idx, beam in enumerate(beams):
        try:
            beam_name = beam["beam_name"] # For logging or more detailed dir names if needed
            energy_layers = beam["energy_layers"]
        except KeyError as e:
            raise KeyError(f"Error: Missing essential key {e} in beam data for beam index {beam_idx}.")

        field_dir = patient_dir / f"Field{beam_idx + 1}"
        try:
            field_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise IOError(f"Error creating directory {field_dir}: {e}")

        for layer_idx_in_beam, energy_layer in enumerate(energy_layers):
            if global_data_idx >= len(ptn_data_list):
                raise IndexError(
                    f"Error: Not enough PTN data entries. Needed for layer {global_data_idx + 1}, "
                    f"but only {len(ptn_data_list)} PTN data entries provided."
                )
            if global_data_idx >= len(dose_monitor_ranges):
                raise IndexError(
                    f"Error: Not enough dose monitor range codes. Needed for layer {global_data_idx + 1}, "
                    f"but only {len(dose_monitor_ranges)} codes provided."
                )

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

            # Apply MU Corrections
            # Assuming dose1_au from PTN is the raw MU count that needs correction
            corrected_mu = dose1_au.astype(float) 
            corrected_mu *= PROTON_DOSE_INTERPOLATOR(nominal_energy)
            corrected_mu *= MU_COUNT_DOSE_INTERPOLATOR(nominal_energy)
            corrected_mu *= monitor_range_factor
            
            if dose_dividing_factor == 0:
                raise ValueError("dose_dividing_factor cannot be zero.")
            corrected_mu /= dose_dividing_factor
            
            corrected_mu = np.round(corrected_mu).astype(int)

            # Prepare CSV Data
            # Ensure all arrays are 1D and have the same length
            if not (time_ms.ndim == 1 and x_mm.ndim == 1 and y_mm.ndim == 1 and corrected_mu.ndim == 1 and
                    len(time_ms) == len(x_mm) == len(y_mm) == len(corrected_mu)):
                raise ValueError(
                    f"Dimension mismatch in data for CSV generation for layer index {global_data_idx}. "
                    f"Shapes: time_ms={time_ms.shape}, x_mm={x_mm.shape}, y_mm={y_mm.shape}, corrected_mu={corrected_mu.shape}"
                )
            
            csv_rows = zip(time_ms, x_mm, y_mm, corrected_mu)

            # CSV Filename
            csv_file_name = f"{layer_idx_in_beam + 1:02d}_{nominal_energy:.2f}MeV.csv"
            csv_file_path = field_dir / csv_file_name

            # Write CSV
            try:
                with open(csv_file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Time (ms)", "X (mm)", "Y (mm)", "MU"]) # Header
                    writer.writerows(csv_rows)
                # print(f"Successfully wrote: {csv_file_path}") # For debugging
            except IOError as e:
                raise IOError(f"Error writing CSV file {csv_file_path}: {e}")
            except Exception as e: # Catch any other CSV writing errors
                raise RuntimeError(f"An unexpected error occurred while writing CSV {csv_file_path}: {e}")

            global_data_idx += 1
            
    # Final check to ensure all ptn_data and dose_monitor_ranges were consumed if expected
    total_layers_in_plan = sum(len(b.get("energy_layers", [])) for b in beams)
    if global_data_idx != total_layers_in_plan:
        print(
            f"Warning: Number of processed layers ({global_data_idx}) does not match "
            f"total energy layers in RTPLAN ({total_layers_in_plan}). "
            f"Ensure ptn_data_list and dose_monitor_ranges match the plan structure."
        )
    # Alternatively, if they must match exactly:
    # if global_data_idx < total_layers_in_plan:
    #     raise ValueError("Not all energy layers from RTPLAN were processed due to insufficient ptn_data or dose_monitor_ranges.")
    # elif global_data_idx > total_layers_in_plan and (global_data_idx > len(ptn_data_list) or global_data_idx > len(dose_monitor_ranges)):
    #     # This case is already handled by IndexError above if ptn_data_list or dose_monitor_ranges are too short.
    #     # If they are longer than total_layers_in_plan, it means there's extra log data not associated with a plan layer.
    #     print(f"Warning: More log data entries provided ({global_data_idx}) than total energy layers in RTPLAN ({total_layers_in_plan}). Extra log data ignored.")


if __name__ == '__main__':
    import shutil # For cleaning up test directory
    print("--- Testing generate_moqui_csvs ---")

    # Mock interpolators if they couldn't be imported (e.g., in a CI environment without scipy)
    if PROTON_DOSE_INTERPOLATOR is None:
        print("Mocking interpolators for testing generate_moqui_csvs.")
        # Simple mock that returns 1.0 for any input
        def mock_interpolator(energy_array):
            if isinstance(energy_array, (float, int, np.number)):
                return 1.0
            return np.ones_like(np.asarray(energy_array), dtype=float)
        PROTON_DOSE_INTERPOLATOR = mock_interpolator
        MU_COUNT_DOSE_INTERPOLATOR = mock_interpolator

    # 1. Create Mock Data
    mock_rt_plan = {
        "patient_id": "TestPatient001",
        "beams": [
            { # Beam 1
                "beam_name": "Field1_Protons",
                "energy_layers": [
                    {"nominal_energy": 70.0, "mu": 10.0}, # Layer 1.1
                    {"nominal_energy": 80.0, "mu": 15.0}  # Layer 1.2
                ]
            },
            { # Beam 2
                "beam_name": "Field2_Protons",
                "energy_layers": [
                    {"nominal_energy": 100.0, "mu": 20.0} # Layer 2.1
                ]
            }
        ]
    }

    # Create 3 PTN data entries, one for each layer above
    mock_ptn_data_list = []
    for i in range(3): # 3 total layers
        # Each ptn_data has time, x, y, dose1_au (raw MU counts)
        # Let's make dose1_au increase, e.g., 0 to 90 for 10 time points
        # (so after dividing by 10, it's 0 to 9 MU for that layer segment)
        num_time_points = 10 
        mock_ptn = {
            "time_ms": np.linspace(0, (num_time_points-1)*10, num_time_points, dtype=np.float32), # 0, 10, ..., 90 ms
            "x_mm": np.random.rand(num_time_points).astype(np.float32) * 10 - 5, # Random X between -5, 5
            "y_mm": np.random.rand(num_time_points).astype(np.float32) * 10 - 5, # Random Y
            # "dose1_au" is raw MU count. Let's assume it's already somewhat scaled
            # and will be further processed by interpolators and dose_dividing_factor.
            # For simplicity, let's make it such that after all corrections (assuming factors ~1)
            # and division by 10, it becomes a sequence like 0,1,2...
            # So, if factors are ~1, and dose_dividing_factor is 10, make it sum to e.g. 0, 10, 20 ...
            "dose1_au": np.arange(num_time_points, dtype=np.float32) * (10 if i==0 else 15 if i==1 else 20) # Raw MUs for layer
        }
        mock_ptn_data_list.append(mock_ptn)

    mock_dose_monitor_ranges = [2, 3, 4] # One for each layer

    temp_output_dir = pathlib.Path("./temp_moqui_output")

    # Clean up before test if it exists
    if temp_output_dir.exists():
        shutil.rmtree(temp_output_dir)

    try:
        # 2. Run the generator
        print(f"\nRunning generate_moqui_csvs into: {temp_output_dir.resolve()}")
        generate_moqui_csvs(mock_rt_plan, mock_ptn_data_list, mock_dose_monitor_ranges, str(temp_output_dir))

        # 3. Verify Directory and File Creation
        patient_dir_expected = temp_output_dir / mock_rt_plan["patient_id"]
        assert patient_dir_expected.exists(), f"Patient directory {patient_dir_expected} not created."
        print(f"Patient directory created: {patient_dir_expected}")

        # Field 1
        field1_dir_expected = patient_dir_expected / "Field1"
        assert field1_dir_expected.exists(), "Field1 directory not created."
        csv1_1 = field1_dir_expected / "01_70.00MeV.csv"
        csv1_2 = field1_dir_expected / "02_80.00MeV.csv"
        assert csv1_1.exists(), f"CSV {csv1_1.name} not found in Field1."
        assert csv1_2.exists(), f"CSV {csv1_2.name} not found in Field1."
        print(f"Field1 CSVs created: {csv1_1.name}, {csv1_2.name}")
        
        # Field 2
        field2_dir_expected = patient_dir_expected / "Field2"
        assert field2_dir_expected.exists(), "Field2 directory not created."
        csv2_1 = field2_dir_expected / "01_100.00MeV.csv"
        assert csv2_1.exists(), f"CSV {csv2_1.name} not found in Field2."
        print(f"Field2 CSVs created: {csv2_1.name}")
        
        # Optional: Verify CSV content for one file
        print(f"\nVerifying content of {csv1_1.name}:")
        with open(csv1_1, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ["Time (ms)", "X (mm)", "Y (mm)", "MU"]
            print(f"Header: {header}")
            first_data_row = next(reader)
            print(f"First data row: {first_data_row}")
            # Check number of columns in data row
            assert len(first_data_row) == 4
            # Check MU value of first data point for first layer (should be 0 if dose1_au starts at 0)
            # dose1_au[0] was 0. Interpolators are mocked to 1. monitorRangeFactor for code 2 is 1.
            # So, (0 * 1 * 1 * 1) / 10 = 0. Rounded to int is 0.
            assert int(first_data_row[3]) == 0, f"Expected MU=0 for first data point, got {first_data_row[3]}"
        print("Basic CSV content verification passed for one file.")
        
        print("\nTest generate_moqui_csvs completed successfully.")

    except Exception as e:
        print(f"Error during testing generate_moqui_csvs: {e}")
        # Add traceback for better debugging if needed
        import traceback
        traceback.print_exc()
    finally:
        # 4. Clean up
        if temp_output_dir.exists():
            print(f"\nCleaning up test directory: {temp_output_dir}")
            shutil.rmtree(temp_output_dir)
        print("--- End of generate_moqui_csvs Test ---")
