import copy
from pathlib import Path

import yaml


DEFAULT_RUNTIME_CONFIG = {
    "processing": {
        "dose_dividing_factor": 1,
        "generate_log_csv": True,
        "generate_plan_csv": False,
        "calibration_mode": {
            "enabled": False,
            "use_correction_factors": True,
            "multi_energy_layer": False,
        },
    },
    "logging": {
        "level": "INFO",
        "show_progress": True,
    },
}


def _merge_dicts(base: dict, overrides: dict) -> dict:
    merged = copy.deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_runtime_config(config_path: str = None) -> dict:
    """
    Load runtime configuration from config.yaml and merge it with defaults.

    Args:
        config_path: Optional path to config.yaml. Defaults to project root config.yaml.

    Returns:
        A dictionary containing runtime configuration values.
    """
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        print(f"Warning: Config file not found at {config_path}")
        print("Using default runtime configuration")
        return copy.deepcopy(DEFAULT_RUNTIME_CONFIG)

    try:
        with open(config_path, "r", encoding="utf-8") as file_handle:
            loaded_config = yaml.safe_load(file_handle)
    except yaml.YAMLError as exc:
        print(f"Error parsing config file at {config_path}: {exc}")
        print("Using default runtime configuration")
        return copy.deepcopy(DEFAULT_RUNTIME_CONFIG)
    except OSError as exc:
        print(f"Error reading config file at {config_path}: {exc}")
        print("Using default runtime configuration")
        return copy.deepcopy(DEFAULT_RUNTIME_CONFIG)

    if loaded_config is None:
        print(f"Warning: Config file is empty at {config_path}")
        print("Using default runtime configuration")
        return copy.deepcopy(DEFAULT_RUNTIME_CONFIG)

    if not isinstance(loaded_config, dict):
        raise ValueError(
            f"Error: Runtime config at {config_path} must be a YAML mapping."
        )

    return _merge_dicts(DEFAULT_RUNTIME_CONFIG, loaded_config)


def parse_scv_init(file_path: str) -> dict:
    """
    Parses a SCV initialization file and returns a dictionary of key-value pairs.
    Keeps all parameters with their original names (PRESET and POS are different).

    Args:
        file_path: The path to the SCV initialization file.

    Returns:
        A dictionary containing the parsed key-value pairs.
        Numerical values are converted to floats, others are kept as strings.
        Returns an empty dictionary if the file is not found or an error occurs.
    """
    config_path = Path(file_path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Error: File not found at {config_path}")

    config_data = {}

    try:
        with config_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
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
                    raise ValueError(
                        f"Error: Could not parse line in {config_path}: {line}"
                    )
    except OSError as exc:
        raise IOError(f"Error: Could not read file at {config_path}") from exc

    if not config_data:
        raise ValueError(f"Error: No SCV init parameters found in {config_path}")

    return config_data


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
    log_dir = Path(log_dir_path)
    if not log_dir.is_dir():
        raise FileNotFoundError(f"Error: Log directory not found at {log_dir}")

    planrange_data = {}

    timestamp_dirs = sorted(
        item.name for item in log_dir.iterdir() if item.is_dir() and item.name.isdigit()
    )

    if not timestamp_dirs:
        raise ValueError(f"Error: No timestamp directories found in {log_dir}")

    for timestamp_dir in timestamp_dirs:
        timestamp_path = log_dir / timestamp_dir
        planrange_file = timestamp_path / "PlanRange.csv"
        if not planrange_file.exists():
            planrange_file = timestamp_path / "PlanRange.txt"

        if not planrange_file.exists():
            raise FileNotFoundError(
                f"Error: PlanRange file (.csv or .txt) not found in {timestamp_dir}"
            )

        dose_ranges = []
        try:
            with planrange_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if i == 0:
                        continue

                    line = line.strip()
                    if not line:
                        continue

                    # Split CSV line and get DOSE1_RANGE column (index 5)
                    parts = line.split(",")
                    if len(parts) >= 6:
                        try:
                            dose_range = int(parts[5])  # DOSE1_RANGE column
                            dose_ranges.append(dose_range)
                        except ValueError:
                            raise ValueError(
                                f"Error: Invalid DOSE1_RANGE value in {planrange_file}, line {i + 1}"
                            )
                    else:
                        raise ValueError(
                            f"Error: Invalid line format in {planrange_file}, line {i + 1}"
                        )
        except OSError as exc:
            raise IOError(
                f"Error: Could not read PlanRange.txt from {timestamp_dir}"
            ) from exc

        planrange_data[timestamp_dir] = dose_ranges

    return planrange_data


def parse_planinfo_files(log_dir_path: str) -> dict:
    """
    Parse PlanInfo.txt files from timestamp directories in log folder.

    Args:
        log_dir_path: Path to the directory containing timestamp subdirectories

    Returns:
        A dictionary mapping timestamp_dir -> parsed PlanInfo fields

    Raises:
        FileNotFoundError: If log directory or PlanInfo.txt files are missing
        ValueError: If required fields are missing or invalid
    """
    log_dir = Path(log_dir_path)
    if not log_dir.is_dir():
        raise FileNotFoundError(f"Error: Log directory not found at {log_dir}")

    planinfo_data = {}
    timestamp_dirs = sorted(
        item.name for item in log_dir.iterdir() if item.is_dir() and item.name.isdigit()
    )

    if not timestamp_dirs:
        raise ValueError(f"Error: No timestamp directories found in {log_dir}")

    required_integer_fields = {
        "DICOM_BEAM_NUMBER",
        "TCSC_FIELD_NUMBER",
        "STOP_LAYER_NUMBER",
    }
    required_fields = required_integer_fields | {"DICOM_PATIENT_ID"}

    for timestamp_dir in timestamp_dirs:
        planinfo_file = log_dir / timestamp_dir / "PlanInfo.txt"

        if not planinfo_file.exists():
            raise FileNotFoundError(f"Error: PlanInfo.txt not found in {timestamp_dir}")

        parsed_fields = {}
        try:
            with planinfo_file.open("r", encoding="utf-8") as f:
                for line_number, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split(",", 1)
                    if len(parts) != 2:
                        raise ValueError(
                            f"Error: Invalid line format in {planinfo_file}, line {line_number}"
                        )

                    key, value = parts[0].strip(), parts[1].strip()
                    if key in required_integer_fields:
                        try:
                            parsed_fields[key] = int(value)
                        except ValueError as exc:
                            raise ValueError(
                                f"Error: Invalid integer value for {key} in {planinfo_file}, line {line_number}"
                            ) from exc
                    elif key in required_fields:
                        parsed_fields[key] = value
        except OSError as exc:
            raise IOError(
                f"Error: Could not read PlanInfo.txt from {timestamp_dir}"
            ) from exc

        missing_fields = sorted(required_fields - parsed_fields.keys())
        if missing_fields:
            raise ValueError(
                f"Error: Missing required PlanInfo fields in {planinfo_file}: {', '.join(missing_fields)}"
            )

        planinfo_data[timestamp_dir] = parsed_fields

    return planinfo_data


if __name__ == "__main__":
    pass
