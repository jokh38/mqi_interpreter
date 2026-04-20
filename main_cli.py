import argparse
from pathlib import Path
import sys  # For sys.exit
import shutil
from typing import Optional, List

# Attempt to import project-specific modules
try:
    from mqi_common import config_loader
    from parsers import dicom_parser, log_parser
    from generators import moqui_generator, aperture_generator
except ImportError as e:
    # This might happen if script is not run as part of a package or PYTHONPATH is not set.
    # For execution, ensure mqi_python_scripts parent directory is in PYTHONPATH
    # or run as 'python -m mqi_python_scripts.main_cli ...'
    print(f"Error: Could not import project modules. Details: {e}")
    print(
        "Please ensure 'mqi_python_scripts' parent directory is in your PYTHONPATH or run as a module."
    )
    # To allow script to proceed for basic --help, we can set them to None,
    # but actual functionality will fail later if they are not truly available.
    # For this implementation, we'll let it fail here if imports are missing,
    # as they are crucial for the script's purpose.
    sys.exit(1)  # Exit if crucial imports fail


def find_dcm_file_in_logdir(logdir_path: str) -> Optional[str]:
    """Find a .dcm file in the logdir folder using a cross-platform approach."""
    logdir = Path(logdir_path)
    if not logdir.is_dir():
        return None

    # Use rglob to recursively find all .dcm files.
    # The result is a generator, so we convert it to a list.
    dcm_files: List[Path] = list(logdir.rglob("*.dcm"))

    if not dcm_files:
        return None

    # Sort files to have a predictable order, as rglob doesn't guarantee it.
    dcm_files.sort()

    # Prefer a file with 'RTPLAN' in its name (case-insensitive).
    for dcm_file in dcm_files:
        if "RTPLAN" in dcm_file.name.upper():
            return str(dcm_file)

    # If no 'RTPLAN' file is found, return the first .dcm file from the sorted list.
    return str(dcm_files[0])


def validate_planinfo_against_rtplan(rt_plan_data: dict, planinfo_data: dict) -> None:
    """Validate PlanInfo fields against RTPLAN-derived metadata."""
    rtplan_patient_id = str(rt_plan_data.get("patient_id", ""))
    beams = rt_plan_data.get("beams", [])
    beams_by_number = {
        beam_number: beam
        for beam in beams
        if (beam_number := beam.get("beam_number")) is not None
    }

    if not rtplan_patient_id:
        raise ValueError(
            "RTPLAN validation failed: missing patient_id in parsed RTPLAN data."
        )

    for timestamp_dir in sorted(planinfo_data):
        info = planinfo_data[timestamp_dir]
        dicom_patient_id = str(info["DICOM_PATIENT_ID"])
        dicom_beam_number = info["DICOM_BEAM_NUMBER"]
        tcsc_field_number = info["TCSC_FIELD_NUMBER"]
        stop_layer_number = info["STOP_LAYER_NUMBER"]

        if dicom_patient_id != rtplan_patient_id:
            raise ValueError(
                f"PlanInfo validation failed in {timestamp_dir}: DICOM_PATIENT_ID "
                f"{dicom_patient_id} does not match RTPLAN PatientID {rtplan_patient_id}."
            )

        beam = beams_by_number.get(dicom_beam_number)
        if beam is None:
            raise ValueError(
                f"PlanInfo validation failed in {timestamp_dir}: DICOM_BEAM_NUMBER "
                f"{dicom_beam_number} was not found in RTPLAN beam numbers "
                f"{sorted(beams_by_number)}."
            )

        max_layers = len(beam.get("energy_layers", []))
        if stop_layer_number < 1 or stop_layer_number > max_layers:
            raise ValueError(
                f"PlanInfo validation failed in {timestamp_dir}: STOP_LAYER_NUMBER "
                f"{stop_layer_number} is out of range [1, {max_layers}] "
                f"for beam {dicom_beam_number}."
            )


def main():
    """
    Main function to orchestrate the parsing and generation process.
    """
    parser = argparse.ArgumentParser(
        description="MQI Data Processing CLI: Parses RTPLAN, PTN logs, and generates MOQUI CSVs."
    )

    parser.add_argument(
        "--logdir",
        type=Path,
        required=True,
        help="Path to the directory containing .ptn log files.",
    )
    parser.add_argument(
        "--outputdir",
        type=Path,
        required=True,
        help="Path to the base directory for output CSV files.",
    )

    args = parser.parse_args()

    print("--- MQI Data Processing Started ---")
    print(f"Log Directory: {args.logdir}")
    print(f"Output Directory: {args.outputdir}")

    runtime_config = config_loader.load_runtime_config()
    processing_config = runtime_config["processing"]
    dose_dividing_factor = processing_config["dose_dividing_factor"]
    generate_log_csv = processing_config["generate_log_csv"]
    generate_plan_csv = processing_config["generate_plan_csv"]
    plan_csv_normalization_factor_by_machine = processing_config[
        "plan_csv_normalization_factor_by_machine"
    ]

    if not generate_log_csv and not generate_plan_csv:
        raise ValueError(
            "At least one CSV generation mode must be enabled in config.yaml."
        )

    # Find DCM file in logdir
    rtplan_path = find_dcm_file_in_logdir(str(args.logdir))
    if not rtplan_path:
        raise FileNotFoundError(f"No .dcm file found in {args.logdir} directory")

    print(f"Found RTPLAN: {rtplan_path}")

    try:
        # 1. Parse RT Plan first to get TreatmentMachineName
        print(f"\nParsing RT Plan file: {rtplan_path}...")
        if not Path(rtplan_path).is_file():
            raise FileNotFoundError(f"RT Plan file not found: {rtplan_path}")
        rt_plan_data = dicom_parser.parse_rtplan(rtplan_path)
        print("RT Plan parsed successfully.")

        # Copy RTPLAN DICOM file to the output 'plan' directory
        patient_id = rt_plan_data.get("patient_id")
        if not patient_id:
            raise ValueError(
                "Could not find PatientID in RTPLAN to create output directory."
            )

        plan_output_dir = args.outputdir / "plan"
        plan_output_dir.mkdir(parents=True, exist_ok=True)

        dicom_filename = Path(rtplan_path).name
        destination_path = plan_output_dir / dicom_filename
        shutil.copy(rtplan_path, destination_path)
        print(f"Copied RTPLAN file to: {destination_path}")

        # 2. Determine config file based on TreatmentMachineName
        config_file = None
        treatment_machine_names = []

        for beam in rt_plan_data.get("beams", []):
            treatment_machine_name = beam.get("treatment_machine_name")
            if treatment_machine_name:
                treatment_machine_names.append(treatment_machine_name)

        if not treatment_machine_names:
            raise ValueError("Error: No TreatmentMachineName found in RT Plan beams")

        # Check for G1 or G2 in TreatmentMachineName
        has_g1 = any("G1" in name for name in treatment_machine_names)
        has_g2 = any("G2" in name for name in treatment_machine_names)

        if has_g1 and has_g2:
            raise ValueError(
                "Error: RT Plan contains both G1 and G2 treatment machines"
            )
        elif has_g1:
            config_file = "scv_init_G1.txt"
            machine_key = "G1"
        elif has_g2:
            config_file = "scv_init_G2.txt"
            machine_key = "G2"
        else:
            raise ValueError("Error: No G1 or G2 found in TreatmentMachineName")

        print(f"Selected config file: {config_file}")

        # Construct absolute path to the config file relative to this script's location
        script_dir = Path(__file__).resolve().parent
        config_path = script_dir / config_file

        # 3. Load Configurations
        print(f"\nLoading SCV init parameters from: {config_path}...")
        if not config_path.is_file():
            raise FileNotFoundError(f"SCV init config file not found: {config_path}")
        scv_init_params = config_loader.parse_scv_init(str(config_path))
        print("SCV init parameters loaded successfully.")

        # Use outputdir directly (already includes patient_id if needed)
        patient_output_dir = args.outputdir
        patient_output_dir.mkdir(parents=True, exist_ok=True)

        if generate_log_csv:
            # 5. Discover and Sort Log Files
            print(f"\nDiscovering .ptn log files in: {args.logdir}...")
            if not args.logdir.is_dir():
                raise FileNotFoundError(f"Log directory not found: {args.logdir}")

            ptn_file_paths = sorted(list(args.logdir.glob("**/*.ptn")))
            if not ptn_file_paths:
                raise FileNotFoundError(f"No .ptn files found in {args.logdir}.")

            num_log_files = len(ptn_file_paths)
            print(f"Found {num_log_files} .ptn files.")

            # 6. Load dose monitor ranges and plan info for PTN-driven generation
            print(
                f"\nLoading dose monitor ranges from PlanRange.txt files in: {args.logdir}..."
            )
            planrange_data = config_loader.parse_planrange_files(str(args.logdir))
            print("PlanRange.txt files loaded successfully.")

            print(f"\nLoading PlanInfo.txt files in: {args.logdir}...")
            planinfo_data = config_loader.parse_planinfo_files(str(args.logdir))
            validate_planinfo_against_rtplan(rt_plan_data, planinfo_data)
            print("PlanInfo.txt files validated successfully.")

            all_dose_ranges = []
            for timestamp_dir, dose_ranges in planrange_data.items():
                all_dose_ranges.extend(dose_ranges)

            dose_monitor_ranges = all_dose_ranges
            print(f"Total dose monitor ranges loaded: {len(dose_monitor_ranges)}")

            print("\nParsing PTN log files...")
            ptn_data_list = []

            print("Processing log file started")
            for ptn_file in ptn_file_paths:
                try:
                    ptn_data = log_parser.parse_ptn_file(str(ptn_file), scv_init_params)
                    ptn_data_list.append(ptn_data)
                except Exception as e:
                    print(f"Error processing PTN file {ptn_file.name}: {e}")
                    raise
            print("All PTN log files parsed successfully.")

            print("\nGenerating log-based MOQUI CSV files...")
            moqui_generator.generate_moqui_csvs(
                rt_plan_data,
                ptn_data_list,
                dose_monitor_ranges,
                str(patient_output_dir),
                dose_dividing_factor=dose_dividing_factor,
            )
            print(f"Log-based MOQUI CSV files generated successfully in {patient_output_dir}.")

        if generate_plan_csv:
            print("\nGenerating RT Plan spot CSV files...")
            moqui_generator.generate_plan_csvs(
                rt_plan_data,
                str(patient_output_dir),
                time_gain_ms=float(scv_init_params["TIMEGAIN"]),
                normalization_factor=float(
                    plan_csv_normalization_factor_by_machine[machine_key]
                ),
            )
            print(f"RT Plan spot CSV files generated successfully in {patient_output_dir}.")

        # 8. Export Aperture/MLC Data (automatic for G1 machines with aperture/MLC)
        # Check if any beam is G1 and has aperture or MLC data
        has_g1_beam = any(
            "G1" in beam.get("treatment_machine_name", "")
            for beam in rt_plan_data.get("beams", [])
        )

        if has_g1_beam:
            print("\nChecking for aperture/MLC data in G1 beams...")
            try:
                # Read DICOM file again to access raw beam data
                import pydicom

                ds = pydicom.dcmread(rtplan_path)

                aperture_files = (
                    aperture_generator.extract_and_generate_aperture_data_g1(
                        ds, rt_plan_data, str(patient_output_dir)
                    )
                )

                if aperture_files:
                    print(
                        f"Aperture/MLC CSV files generated: {len(aperture_files)} files"
                    )
                    for file_path in aperture_files:
                        print(f"  - {file_path}")
                else:
                    print("No aperture or MLC data found in G1 beams.")

            except Exception as e:
                print(f"Error during aperture export: {e}")
                # Don't fail the entire process for aperture export errors

        print("\n--- MQI Data Processing Completed Successfully ---")

    except FileNotFoundError as e:
        print(f"Error: A required file was not found. {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: Invalid data or configuration. {e}", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Missing expected data key. {e}", file=sys.stderr)
        sys.exit(1)
    except IndexError as e:
        print(
            f"Error: Data list mismatch (e.g., not enough log files for plan layers). {e}",
            file=sys.stderr,
        )
        sys.exit(1)
    except RuntimeError as e:  # For issues like interpolators not loading
        print(f"Runtime Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        # For debugging, you might want to print the full traceback
        # import traceback
        # traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
