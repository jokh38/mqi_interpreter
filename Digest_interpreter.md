This document provides an overview of the MQI Data Processing CLI program, generated from the docstrings within the Python source code.

## 1. Overview: Main Command-Line Interface (`main_cli.py`)

The main script orchestrates the entire data processing workflow. It is a command-line interface (CLI) that takes a log directory and an output directory as inputs.

### `main()`
The main function that drives the parsing and generation process. It performs the following steps:
1.  **Parses Command-Line Arguments**: Takes `--logdir` and `--outputdir` as input paths.
2.  **Finds RTPLAN DICOM File**: Locates the `.dcm` file within the provided log directory.
3.  **Parses RTPLAN**: Reads and extracts data from the DICOM file.
4.  **Determines Configuration**: Selects the appropriate `scv_init_G1.txt` or `scv_init_G2.txt` configuration file based on the `TreatmentMachineName` found in the RTPLAN.
5.  **Loads Configuration**: Parses the selected SCV initialization file.
6.  **Discovers and Parses Log Files**: Finds all `.ptn` log files, sorts them, and parses each one.
7.  **Loads Dose Monitor Ranges**: Parses `PlanRange.txt` files to get dose monitor range codes.
8.  **Generates MOQUI CSVs**: Creates the final CSV files for Moqui based on the parsed plan and log data.
9.  **Exports Aperture/MLC Data**: If the treatment machine is a "G1" type, it extracts and generates CSV files for any aperture or MLC data found in the DICOM plan.

### `find_dcm_file_in_logdir(logdir_path: str)`
This helper function finds a `.dcm` file in the specified log directory. It prioritizes files with "RTPLAN" in the name, but if none are found, it returns the first `.dcm` file it encounters.

---

## 2. Parsers (`parsers/`)

This package is responsible for reading and parsing various input file formats.

### `dicom_parser.py`

#### `parse_rtplan(file_path: str)`
Parses an RTPLAN DICOM file and extracts relevant information into a dictionary.
* **Args**:
    * `file_path`: The path to the RTPLAN DICOM file.
* **Returns**: A dictionary containing the parsed RTPLAN data.
* **Raises**: `FileNotFoundError`, `InvalidDicomError`, `ValueError` for issues like incorrect file type or missing critical DICOM tags.

#### `extract_aperture_data(beam_ds)`
Extracts aperture block information from a single DICOM beam dataset.
* **Args**:
    * `beam_ds`: A DICOM beam dataset object.
* **Returns**: A dictionary containing the aperture data, or `None` if no aperture is found.

#### `extract_mlc_data(beam_ds)`
Extracts Multi-Leaf Collimator (MLC) information from a single DICOM beam dataset.
* **Args**:
    * `beam_ds`: A DICOM beam dataset object.
* **Returns**: A dictionary containing MLC data, or `None` if no MLC is found.

### `log_parser.py`

#### `parse_ptn_file(file_path: str, config_params: dict)`
Parses a `.ptn` binary log file into a dictionary of NumPy arrays.
* **Args**:
    * `file_path`: Path to the `.ptn` file.
    * `config_params`: A dictionary with calibration parameters (`TIMEGAIN`, `XPOSOFFSET`, etc.).
* **Returns**: A dictionary where keys are descriptive strings (e.g., "time\_ms", "x\_raw") and values are the corresponding 1D NumPy arrays.
* **Raises**: `FileNotFoundError`, `KeyError`, `ValueError`.

#### `parse_mgn_file(file_path: str, config_params: dict)`
This is a placeholder for a function that will parse `.mgn` binary log files. It is not yet implemented.

---

## 3. Generators (`generators/`)

This package is responsible for generating the final output files.

### `moqui_generator.py`

#### `generate_moqui_csvs(...)`
Generates CSV files for Moqui based on the parsed RTPLAN and processed PTN log data. It creates two separate folder structures:
* **plan**: Contains data directly from the RT plan, without monitor range factors or MU corrections.
* **log**: Contains data from the log files, with monitor range factors applied.
* **Args**:
    * `rt_plan_data`: The dictionary of parsed RTPLAN data.
    * `ptn_data_list`: A list of dictionaries, where each dictionary is the output of `parse_ptn_file`.
    * `dose_monitor_ranges`: A list of integers representing the monitor range codes for each energy layer.
    * `output_base_dir`: The base directory where the output files will be created.
* **Raises**: `KeyError`, `IndexError`, `IOError`, `RuntimeError`.

#### `interpolate_rtplan_data(beam: dict, time_step_ms: float = 0.06)`
Interpolates RT Plan data to generate time-series data, mimicking the logic from `Dicom_reader_F.py`.
* **Args**:
    * `beam`: A dictionary containing beam data, including control point details.
    * `time_step_ms`: The time step for interpolation in milliseconds.
* **Returns**: A list of lists, where each inner list contains `[time_ms, x_mm, y_mm, mu]`.

#### `calculate_layer_doserate(...)`
Calculates the layer dose rate based on the logic from `Dicom_reader_F.py`.
* **Args**:
    * `positions`: A NumPy array of spot positions (n, 2).
    * `weights`: A NumPy array of spot weights (n,).
    * `energy`: The energy in MeV.
* **Returns**: The calculated layer dose rate in MU/s.

#### `get_monitor_range_factor(monitor_range_code: int)`
Determines the `monitorRangeFactor` based on a given code, with values derived from the C++ Moqui source code.

### `aperture_generator.py`

#### `extract_and_generate_aperture_data_g1(...)`
Extracts aperture/MLC data from a DICOM dataset and generates CSV files, but **only for G1 machines**. It saves files to both the `rtplan` and `log` output folders.
* **Args**:
    * `ds`: The original DICOM dataset.
    * `rt_plan_data`: The parsed RT plan data.
    * `output_base_dir`: The base directory for the output files.
* **Returns**: A list of the created aperture/MLC CSV file paths.

#### `generate_aperture_csv(...)`
Generates a CSV file for aperture data.
* **Args**:
    * `beam_name`: The name of the beam.
    * `aperture_data`: A dictionary containing the aperture information.
    * `output_path`: The full path for the output CSV file.

#### `generate_mlc_csv(...)`
Generates a CSV file for MLC data.
* **Args**:
    * `beam_name`: The name of the beam.
    * `mlc_data`: A dictionary containing the MLC information.
    * `output_path`: The full path for the output CSV file.

#### `_has_mlc_beyond_home_position(beam_ds)`
Checks if the MLC positions have moved from their home position by comparing the middle MLC pair with the outermost pair.

---

## 4. Common Utilities (`mqi_common/`)

### `config_loader.py`

#### `parse_scv_init(file_path: str)`
Parses an SCV initialization file (e.g., `scv_init_G1.txt`) and returns a dictionary of key-value pairs. It also maps the keys from the config file to the keys expected by the `log_parser`.
* **Args**:
    * `file_path`: The path to the SCV initialization file.
* **Returns**: A dictionary containing the parsed key-value pairs.

#### `parse_planrange_files(log_dir_path: str)`
Parses `PlanRange.txt` files found within timestamped subdirectories of the log folder.
* **Args**:
    * `log_dir_path`: The path to the directory containing timestamp subdirectories.
* **Returns**: A dictionary that maps each `timestamp_dir` to a list of `DOSE1_RANGE` values.
* **Raises**: `FileNotFoundError`, `ValueError`.

---

## 5. Processing (`processing/`)

### `interpolation.py`

This module provides interpolation and data correction functionalities.

#### `ConstExtrapPchipInterpolator`
A wrapper for SciPy's `PchipInterpolator` that provides constant value extrapolation for values outside the defined energy range.

#### `gaussian_energy_spread(energy: float)`
Calculates the Gaussian energy spread based on the input energy using the formula: `0.7224 * exp(-(((energy - 82.75) / 168.5)^2))`.