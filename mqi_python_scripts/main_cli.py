import argparse
from pathlib import Path
import sys # For sys.exit

# Attempt to import project-specific modules
try:
    from mqi_common import config_loader
    from parsers import dicom_parser, log_parser
    from generators import moqui_generator
except ImportError as e:
    # This might happen if script is not run as part of a package or PYTHONPATH is not set.
    # For execution, ensure mqi_python_scripts parent directory is in PYTHONPATH
    # or run as 'python -m mqi_python_scripts.main_cli ...'
    print(f"Error: Could not import project modules. Details: {e}")
    print("Please ensure 'mqi_python_scripts' parent directory is in your PYTHONPATH or run as a module.")
    # To allow script to proceed for basic --help, we can set them to None,
    # but actual functionality will fail later if they are not truly available.
    # For this implementation, we'll let it fail here if imports are missing,
    # as they are crucial for the script's purpose.
    sys.exit(1) # Exit if crucial imports fail

def main():
    """
    Main function to orchestrate the parsing and generation process.
    """
    parser = argparse.ArgumentParser(description="MQI Data Processing CLI: Parses RTPLAN, PTN logs, and generates MOQUI CSVs.")
    
    parser.add_argument("--rtplan", type=Path, required=True, help="Path to the DICOM RT Plan file.")
    parser.add_argument("--logdir", type=Path, required=True, help="Path to the directory containing .ptn log files.")
    parser.add_argument("--config", type=Path, required=True, help="Path to the scv_init.txt-like configuration file.")
    parser.add_argument("--dosemon_excel", type=Path, required=True, help="Path to the Excel file for dose monitor ranges.")
    parser.add_argument("--outputdir", type=Path, required=True, help="Path to the base directory for output CSV files.")
    parser.add_argument("--dose_div_factor", type=int, default=10, help="Dose dividing factor for MU calculation (default: 10).")

    args = parser.parse_args()

    print("--- MQI Data Processing Started ---")
    print(f"RTPLAN: {args.rtplan}")
    print(f"Log Directory: {args.logdir}")
    print(f"Config File: {args.config}")
    print(f"Dose Monitor Excel: {args.dosemon_excel}")
    print(f"Output Directory: {args.outputdir}")
    print(f"Dose Dividing Factor: {args.dose_div_factor}")

    try:
        # 1. Load Configurations
        print(f"\nLoading SCV init parameters from: {args.config}...")
        if not args.config.is_file():
            raise FileNotFoundError(f"SCV init config file not found: {args.config}")
        scv_init_params = config_loader.parse_scv_init(str(args.config))
        if not scv_init_params: # parse_scv_init returns empty dict on error or if file is empty
             raise ValueError(f"Failed to load or parse SCV init parameters from {args.config}. Ensure file is valid and not empty.")
        print("SCV init parameters loaded successfully.")

        # 2. Parse RT Plan
        print(f"\nParsing RT Plan file: {args.rtplan}...")
        if not args.rtplan.is_file():
            raise FileNotFoundError(f"RT Plan file not found: {args.rtplan}")
        rt_plan_data = dicom_parser.parse_rtplan(str(args.rtplan))
        print("RT Plan parsed successfully.")
        # print(f"Patient ID: {rt_plan_data.get('patient_id')}, Plan Label: {rt_plan_data.get('rt_plan_label')}")

        # 3. Discover and Sort Log Files
        print(f"\nDiscovering .ptn log files in: {args.logdir}...")
        if not args.logdir.is_dir():
            raise FileNotFoundError(f"Log directory not found: {args.logdir}")
        
        ptn_file_paths = sorted(list(args.logdir.glob('*.ptn')))
        if not ptn_file_paths:
            raise FileNotFoundError(f"No .ptn files found in {args.logdir}.")
        
        num_log_files = len(ptn_file_paths)
        print(f"Found {num_log_files} .ptn files.")

        # 4. Load Dose Monitor Ranges
        print(f"\nLoading dose monitor ranges from: {args.dosemon_excel}...")
        if not args.dosemon_excel.is_file():
            raise FileNotFoundError(f"Dose monitor Excel file not found: {args.dosemon_excel}")
        dose_monitor_ranges = config_loader.parse_dose_monitor_excel(str(args.dosemon_excel), num_log_files)
        print("Dose monitor ranges loaded successfully.")

        # 5. Parse all PTN Log Files
        print("\nParsing PTN log files...")
        ptn_data_list = []
        for ptn_file in ptn_file_paths:
            print(f"Processing log file: {ptn_file.name}...")
            try:
                ptn_data = log_parser.parse_ptn_file(str(ptn_file), scv_init_params)
                ptn_data_list.append(ptn_data)
                print(f"Successfully processed {ptn_file.name}.")
            except Exception as e:
                print(f"Error processing PTN file {ptn_file.name}: {e}")
                # Decide if one bad log file should stop everything or just be skipped.
                # For now, let's be strict and re-raise to stop.
                raise  
        print("All PTN log files parsed successfully.")

        # 6. Generate MOQUI CSVs
        print("\nGenerating MOQUI CSV files...")
        # Ensure output directory exists, generate_moqui_csvs will create patient/field subdirs
        args.outputdir.mkdir(parents=True, exist_ok=True) 
        
        moqui_generator.generate_moqui_csvs(
            rt_plan_data,
            ptn_data_list,
            dose_monitor_ranges,
            str(args.outputdir), # Function expects string path
            args.dose_div_factor
        )
        print(f"MOQUI CSV files generated successfully in {args.outputdir}.")

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
        print(f"Error: Data list mismatch (e.g., not enough log files for plan layers). {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e: # For issues like interpolators not loading
        print(f"Runtime Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        # For debugging, you might want to print the full traceback
        # import traceback
        # traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
```
