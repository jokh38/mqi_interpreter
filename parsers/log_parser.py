import numpy as np
import os

def parse_ptn_file(file_path: str, config_params: dict) -> dict:
    """
    Parses a .ptn binary log file into a dictionary of numpy arrays.

    Args:
        file_path: Path to the .ptn file.
        config_params: Dictionary containing calibration parameters.
                       Required keys: 'TIMEGAIN', 'XPOSOFFSET', 'YPOSOFFSET',
                                     'XPOSGAIN', 'YPOSGAIN'

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

    # 2. Check for essential config_params (PTN uses POS parameters)
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
    Parses a .mgn binary log file into a dictionary of numpy arrays.

    MGN files contain magnet position data with 6 columns per row:
    Time[us], ?, ?, X position, Y position, Beam on/off

    Args:
        file_path: Path to the .mgn file.
        config_params: Dictionary containing calibration parameters.
                       Required keys: 'XPRESETOFFSET', 'YPRESETOFFSET',
                                     'XPRESETGAIN', 'YPRESETGAIN'

    Returns:
        A dictionary where keys are descriptive strings and values are
        corresponding 1D numpy arrays.

    Raises:
        FileNotFoundError: If file_path does not exist.
        KeyError: If config_params is missing essential keys.
        ValueError: If the file data cannot be processed correctly.
    """
    # 1. Check for file existence
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Error: File not found at {file_path}")

    # 2. Check for essential config_params (MGN uses PRESET parameters)
    required_keys = ['XPRESETOFFSET', 'YPRESETOFFSET', 'XPRESETGAIN', 'YPRESETGAIN']
    for key in required_keys:
        if key not in config_params:
            raise KeyError(f"Error: Missing essential key '{key}' in config_params.")

    try:
        # 3. Open and read binary file
        with open(file_path, 'rb') as f:
            # Get file length
            f.seek(0, 2)  # Seek to end
            file_length = f.tell()
            f.seek(0, 0)  # Seek back to start

            # Calculate modified length (6 values per 14 bytes: 1x4byte + 5x2byte)
            # Each record: 4 bytes (time) + 2 bytes + 2 bytes + 2 bytes (X) + 2 bytes (Y) + 2 bytes (beam)
            num_records = file_length // 14
            modified_length = num_records * 6

            # Read data
            data_array = np.zeros(modified_length, dtype=np.float32)

            for i in range(num_records):
                base_idx = i * 6

                # Read time (4 bytes, unsigned int, big-endian)
                time_bytes = f.read(4)
                if len(time_bytes) != 4:
                    break
                time_value = int.from_bytes(time_bytes, byteorder='big', signed=False)
                data_array[base_idx] = float(time_value)

                # Read 5 more 2-byte values (unsigned short, big-endian)
                for j in range(1, 6):
                    component_bytes = f.read(2)
                    if len(component_bytes) != 2:
                        break
                    component_value = int.from_bytes(component_bytes, byteorder='big', signed=False)
                    data_array[base_idx + j] = float(component_value)

    except Exception as e:
        raise IOError(f"Error reading binary data from {file_path}: {e}")

    # 4. Reshape to 6 columns
    if modified_length % 6 != 0:
        raise ValueError(
            f"Error: MGN file data size ({modified_length} values) "
            "is not a multiple of 6. Cannot reshape."
        )

    data_2d = data_array.reshape(-1, 6)

    # 5. Extract columns
    # Columns: Time[us], ?, ?, X position (raw), Y position (raw), Beam on/off
    time_col_us = data_2d[:, 0]
    unknown1_col = data_2d[:, 1]
    unknown2_col = data_2d[:, 2]
    raw_x_col = data_2d[:, 3]
    raw_y_col = data_2d[:, 4]
    beam_on_off_col = data_2d[:, 5]

    # 6. Apply Calibrations (using PRESET parameters)
    xpreset_offset = float(config_params['XPRESETOFFSET'])
    ypreset_offset = float(config_params['YPRESETOFFSET'])
    xpreset_gain = float(config_params['XPRESETGAIN'])
    ypreset_gain = float(config_params['YPRESETGAIN'])

    corrected_x_col = (raw_x_col - xpreset_offset) * xpreset_gain
    corrected_y_col = (raw_y_col - ypreset_offset) * ypreset_gain

    # 7. Return Data as dictionary of 1D arrays
    return {
        "time_us": time_col_us,
        "unknown1": unknown1_col,
        "unknown2": unknown2_col,
        "x_raw": raw_x_col,
        "y_raw": raw_y_col,
        "beam_on_off": beam_on_off_col,
        "x_mm": corrected_x_col,
        "y_mm": corrected_y_col,
    }

if __name__ == '__main__':
    pass
