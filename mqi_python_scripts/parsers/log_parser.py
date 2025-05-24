import numpy as np
import os

def parse_ptn_file(file_path: str, config_params: dict) -> dict:
    """
    Parses a .ptn binary log file into a dictionary of numpy arrays.

    Args:
        file_path: Path to the .ptn file.
        config_params: Dictionary containing calibration parameters:
                       'TIMEGAIN', 'XPOSOFFSET', 'YPOSOFFSET', 
                       'XPOSGAIN', 'YPOSGAIN'.

    Returns:
        A dictionary where keys are descriptive strings (e.g., "time_ms", 
        "x_raw", "y_raw", "x_mm", "y_mm", etc.) and values are the 
        corresponding 1D numpy arrays.

    Raises:
        FileNotFoundError: If file_path does not exist.
        KeyError: If config_params is missing essential keys.
        ValueError: If the file data cannot be reshaped (not multiple of 8 shorts),
                    or if other data processing errors occur.
    """
    # 1. Check for file existence
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Error: File not found at {file_path}")

    # 2. Check for essential config_params
    required_keys = ['TIMEGAIN', 'XPOSOFFSET', 'YPOSOFFSET', 'XPOSGAIN', 'YPOSGAIN']
    for key in required_keys:
        if key not in config_params:
            raise KeyError(f"Error: Missing essential key '{key}' in config_params.")

    try:
        # 3. Read binary data using numpy, big-endian 2-byte unsigned integers
        raw_data_1d = np.fromfile(file_path, dtype='>u2')
    except Exception as e:
        raise IOError(f"Error reading binary data from {file_path}: {e}")

    # 4. Check if data can be reshaped (multiple of 8)
    if raw_data_1d.size % 8 != 0:
        raise ValueError(
            f"Error: File data size ({raw_data_1d.size} shorts) "
            "is not a multiple of 8. Cannot reshape."
        )
    
    # Reshape to 2D array with 8 columns
    data_2d = raw_data_1d.reshape(-1, 8)

    # 5. Convert data type to float32
    data_2d_float = data_2d.astype(np.float32)

    # 6. Generate Time Column
    num_rows = data_2d_float.shape[0]
    time_gain = float(config_params['TIMEGAIN']) # Ensure float for calculation
    time_column = np.arange(num_rows, dtype=np.float32) * time_gain
    time_column = time_column.reshape(-1, 1)

    # 7. Combine Time and Data
    # Columns: Time, RawX, RawY, RawXSize, RawYSize, Dose1, Dose2, LayerNum, BeamOnOff
    data_with_time = np.hstack((time_column, data_2d_float))

    # Extract individual raw columns for clarity and calculations
    # Indices based on data_2d_float (original 8 columns after reshape)
    raw_x_col = data_2d_float[:, 0]
    raw_y_col = data_2d_float[:, 1]
    raw_x_size_col = data_2d_float[:, 2]
    raw_y_size_col = data_2d_float[:, 3]
    dose1_col = data_2d_float[:, 4]
    dose2_col = data_2d_float[:, 5]
    layer_num_col = data_2d_float[:, 6] # Should these be int? Kept as float32 for now.
    beam_on_off_col = data_2d_float[:, 7] # Should these be int?

    # 8. Apply Calibrations
    xpos_offset = float(config_params['XPOSOFFSET'])
    ypos_offset = float(config_params['YPOSOFFSET'])
    xpos_gain = float(config_params['XPOSGAIN'])
    ypos_gain = float(config_params['YPOSGAIN'])

    corrected_x_col = (raw_x_col - xpos_offset) * xpos_gain
    corrected_y_col = (raw_y_col - ypos_offset) * ypos_gain
    # As per C++ logFileLoadingThread, XPOSGAIN for XSize, YPOSGAIN for YSize
    corrected_x_size_col = raw_x_size_col * xpos_gain 
    corrected_y_size_col = raw_y_size_col * ypos_gain

    # 9. Return Data as dictionary of 1D arrays
    return {
        "time_ms": time_column.flatten(), # time_column is already 1D after reshape(-1,1).flatten() or direct
        "x_raw": raw_x_col,
        "y_raw": raw_y_col,
        "x_size_raw": raw_x_size_col,
        "y_size_raw": raw_y_size_col,
        "dose1_au": dose1_col,
        "dose2_au": dose2_col,
        "layer_num": layer_num_col, # Consider converting to int if appropriate: .astype(np.int32)
        "beam_on_off": beam_on_off_col, # Consider converting to int if appropriate
        "x_mm": corrected_x_col,
        "y_mm": corrected_y_col,
        "x_size_mm": corrected_x_size_col,
        "y_size_mm": corrected_y_size_col,
    }

def parse_mgn_file(file_path: str, config_params: dict) -> dict:
    """
    Placeholder for parsing .mgn binary log files.
    This function will be implemented later.
    """
    print(f"Placeholder: Would parse .mgn file {file_path} with params {config_params}")
    return {}

if __name__ == '__main__':
    print("--- Testing parse_ptn_file ---")

    # Define sample config parameters
    sample_config = {
        'TIMEGAIN': 0.1,      # ms per row
        'XPOSOFFSET': 32768,  # Raw offset
        'YPOSOFFSET': 32768,
        'XPOSGAIN': 0.005,    # mm per raw unit
        'YPOSGAIN': 0.005
    }

    # Create a dummy .ptn file
    # Each row: X, Y, XSize, YSize, Dose1, Dose2, Layer, BeamOnOff (8 shorts)
    # Values are chosen to be simple after offset.
    # (32768, 32768, 100, 100, 1000, 2000, 1, 1) -> X=0, Y=0, XSize=0.5, YSize=0.5
    # (32768+200, 32768-200, 200, 50, 1001, 2001, 1, 0) -> X=1, Y=-1, XSize=1, YSize=0.25
    dummy_data = np.array([
        32768, 32768, 100, 100, 1000, 2000, 1, 1,        # Row 1
        32768+200, 32768-200, 200, 50, 1001, 2001, 1, 0, # Row 2
        32768+400, 32768+400, 50, 200, 1002, 2002, 2, 1  # Row 3
    ], dtype='>u2') # Big-endian unsigned short

    dummy_file_path = "dummy_test.ptn"
    try:
        dummy_data.tofile(dummy_file_path)
        print(f"Created dummy file: {dummy_file_path}")

        # Test Case 1: Valid file and config
        print("\nTest Case 1: Valid file and config")
        parsed_data = parse_ptn_file(dummy_file_path, sample_config)
        
        assert parsed_data["time_ms"].shape == (3,)
        assert parsed_data["x_raw"].shape == (3,)
        assert parsed_data["x_mm"].shape == (3,)
        assert parsed_data["layer_num"].shape == (3,)

        print(f"Time (ms): {parsed_data['time_ms']}")
        print(f"Raw X: {parsed_data['x_raw']}")
        print(f"Corrected X (mm): {parsed_data['x_mm']}")
        print(f"Raw Y: {parsed_data['y_raw']}")
        print(f"Corrected Y (mm): {parsed_data['y_mm']}")
        print(f"Raw XSize: {parsed_data['x_size_raw']}")
        print(f"Corrected XSize (mm): {parsed_data['x_size_mm']}")
        print(f"Raw YSize: {parsed_data['y_size_raw']}")
        print(f"Corrected YSize (mm): {parsed_data['y_size_mm']}")
        print(f"Layer Num: {parsed_data['layer_num']}")
        print(f"Beam On/Off: {parsed_data['beam_on_off']}")

        # Check specific calculated values for the first row
        # RawX = 32768, RawY = 32768
        # CorrectedX = (32768 - 32768) * 0.005 = 0.0
        # CorrectedY = (32768 - 32768) * 0.005 = 0.0
        # RawXSize = 100 -> CorrectedXSize = 100 * 0.005 = 0.5
        # RawYSize = 100 -> CorrectedYSize = 100 * 0.005 = 0.5
        assert np.isclose(parsed_data['time_ms'][0], 0.0)
        assert np.isclose(parsed_data['x_mm'][0], 0.0)
        assert np.isclose(parsed_data['y_mm'][0], 0.0)
        assert np.isclose(parsed_data['x_size_mm'][0], 0.5)
        assert np.isclose(parsed_data['y_size_mm'][0], 0.5)
        assert np.isclose(parsed_data['layer_num'][0], 1.0)
        assert np.isclose(parsed_data['beam_on_off'][0], 1.0)

        # Check specific calculated values for the second row
        # RawX = 32768+200 = 32968 -> CorrectedX = (32968 - 32768) * 0.005 = 200 * 0.005 = 1.0
        # RawY = 32768-200 = 32568 -> CorrectedY = (32568 - 32768) * 0.005 = -200 * 0.005 = -1.0
        # RawXSize = 200 -> CorrectedXSize = 200 * 0.005 = 1.0
        # RawYSize = 50 -> CorrectedYSize = 50 * 0.005 = 0.25
        assert np.isclose(parsed_data['time_ms'][1], 0.1)
        assert np.isclose(parsed_data['x_mm'][1], 1.0)
        assert np.isclose(parsed_data['y_mm'][1], -1.0)
        assert np.isclose(parsed_data['x_size_mm'][1], 1.0)
        assert np.isclose(parsed_data['y_size_mm'][1], 0.25)
        assert np.isclose(parsed_data['beam_on_off'][1], 0.0)
        print("Assertions for specific values passed.")

    except Exception as e:
        print(f"Error in Test Case 1: {e}")

    # Test Case 2: File not found
    print("\nTest Case 2: File not found")
    try:
        parse_ptn_file("non_existent.ptn", sample_config)
        print("Error: Expected FileNotFoundError not raised.")
    except FileNotFoundError as e:
        print(f"Caught expected error: {e}")
    except Exception as e:
        print(f"Unexpected error in Test Case 2: {e}")

    # Test Case 3: Missing config key
    print("\nTest Case 3: Missing config key")
    incomplete_config = sample_config.copy()
    del incomplete_config['TIMEGAIN']
    try:
        parse_ptn_file(dummy_file_path, incomplete_config)
        print("Error: Expected KeyError not raised.")
    except KeyError as e:
        print(f"Caught expected error: {e}")
    except Exception as e:
        print(f"Unexpected error in Test Case 3: {e}")

    # Test Case 4: Invalid file format (not multiple of 8 shorts)
    print("\nTest Case 4: Invalid file format (bad length)")
    bad_data = np.array([1, 2, 3, 4, 5, 6, 7], dtype='>u2') # 7 shorts
    bad_file_path = "bad_dummy.ptn"
    try:
        bad_data.tofile(bad_file_path)
        parse_ptn_file(bad_file_path, sample_config)
        print("Error: Expected ValueError not raised for bad file length.")
    except ValueError as e:
        print(f"Caught expected error: {e}")
    except Exception as e:
        print(f"Unexpected error in Test Case 4: {e}")
    finally:
        if os.path.exists(bad_file_path):
            os.remove(bad_file_path)

    # Placeholder call
    print("\n--- Testing parse_mgn_file (placeholder) ---")
    parse_mgn_file("dummy.mgn", {})

    print("\n--- End of Tests ---")

    # Clean up dummy file from Test Case 1
    if os.path.exists(dummy_file_path):
        os.remove(dummy_file_path)
        print(f"Cleaned up {dummy_file_path}")
