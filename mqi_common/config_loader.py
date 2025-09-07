import os

def parse_scv_init(file_path: str) -> dict:
    """
    Parses a SCV initialization file and returns a dictionary of key-value pairs.
    Maps config file keys to log_parser expected keys.

    Args:
        file_path: The path to the SCV initialization file.

    Returns:
        A dictionary containing the parsed key-value pairs.
        Numerical values are converted to floats, others are kept as strings.
        Returns an empty dictionary if the file is not found or an error occurs.
    """
    config_data = {}
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return config_data

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split(None, 1)  # Split by any whitespace, max 1 split
                if len(parts) == 2:
                    key, value_str = parts
                    try:
                        value = float(value_str)
                    except ValueError:
                        value = value_str  # Keep as string if not a float
                    config_data[key] = value
                else:
                    print(f"Warning: Could not parse line: {line}")
    except IOError:
        print(f"Error: Could not read file at {file_path}")
    
    # Map config file keys to log_parser expected keys
    mapped_config = {}
    key_mapping = {
        'XPRESETOFFSET': 'XPOSOFFSET',
        'YPRESETOFFSET': 'YPOSOFFSET',
        'XPRESETGAIN': 'XPOSGAIN',  # Using PRESET gain instead of POS gain
        'YPRESETGAIN': 'YPOSGAIN',  # Using PRESET gain instead of POS gain
        'TIMEGAIN': 'TIMEGAIN'
    }
    
    for config_key, parser_key in key_mapping.items():
        if config_key in config_data:
            mapped_config[parser_key] = config_data[config_key]
    
    # Add original keys that don't need mapping
    for key, value in config_data.items():
        if key not in key_mapping and key not in mapped_config:
            mapped_config[key] = value
    
    return mapped_config


def parse_planrange_files(log_dir_path: str) -> dict:
    """
    Parse PlanRange.txt files from timestamp directories in log folder.
    
    Args:
        log_dir_path: Path to the directory containing timestamp subdirectories
        
    Returns:
        A dictionary mapping timestamp_dir -> list of DOSE1_RANGE values
        
    Raises:
        FileNotFoundError: If log directory is not found
        ValueError: If PlanRange.txt files are missing or invalid
    """
    import os
    
    if not os.path.exists(log_dir_path):
        raise FileNotFoundError(f"Error: Log directory not found at {log_dir_path}")
    
    planrange_data = {}
    
    # Find all timestamp directories
    timestamp_dirs = []
    for item in os.listdir(log_dir_path):
        item_path = os.path.join(log_dir_path, item)
        if os.path.isdir(item_path) and item.isdigit():
            timestamp_dirs.append(item)
    
    if not timestamp_dirs:
        raise ValueError(f"Error: No timestamp directories found in {log_dir_path}")
    
    # Parse PlanRange.txt from each timestamp directory
    for timestamp_dir in timestamp_dirs:
        planrange_file = os.path.join(log_dir_path, timestamp_dir, "PlanRange.txt")
        
        if not os.path.exists(planrange_file):
            raise FileNotFoundError(f"Error: PlanRange.txt not found in {timestamp_dir}")
        
        dose_ranges = []
        try:
            with open(planrange_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Skip header line
                for i, line in enumerate(lines):
                    if i == 0:  # Skip header
                        continue
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Split CSV line and get DOSE1_RANGE column (index 5)
                    parts = line.split(',')
                    if len(parts) >= 6:
                        try:
                            dose_range = int(parts[5])  # DOSE1_RANGE column
                            dose_ranges.append(dose_range)
                        except ValueError:
                            raise ValueError(f"Error: Invalid DOSE1_RANGE value in {planrange_file}, line {i+1}")
                    else:
                        raise ValueError(f"Error: Invalid line format in {planrange_file}, line {i+1}")
        
        except IOError:
            raise IOError(f"Error: Could not read PlanRange.txt from {timestamp_dir}")
        
        planrange_data[timestamp_dir] = dose_ranges
    
    return planrange_data

if __name__ == '__main__':
    pass
