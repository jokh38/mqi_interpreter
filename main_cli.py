import argparse
from pathlib import Path
import sys # For sys.exit
import subprocess
import shlex
from typing import Optional

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
    print("Please ensure 'mqi_python_scripts' parent directory is in your PYTHONPATH or run as a module.")
    # To allow script to proceed for basic --help, we can set them to None,
    # but actual functionality will fail later if they are not truly available.
    # For this implementation, we'll let it fail here if imports are missing,
    # as they are crucial for the script's purpose.
    sys.exit(1) # Exit if crucial imports fail

def execute_command(command: str) -> dict:
    """Execute a shell command and return the result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e)
        }

def find_dcm_file_in_logdir(case_path: str, logdir: str = "logs") -> Optional[str]:
    """Find .dcm file in the logdir folder."""
    logdir_path = f"{case_path}/{logdir}"
    
    # Search for .dcm files in logdir
    result = execute_command(f"find {shlex.quote(logdir_path)} -name '*.dcm' -type f")
    
    if result["exit_code"] == 0 and result["stdout"].strip():
        dcm_files = result["stdout"].strip().split('\n')
        
        # Prefer RTPLAN.dcm if it exists, otherwise return first .dcm file
        for dcm_file in dcm_files:
            if 'RTPLAN' in dcm_file.upper():
                return dcm_file.strip()
        
        # Return first .dcm file found
        return dcm_files[0].strip()
    
    return None

def main():
    """
    Main function to orchestrate the parsing and generation process.
    """
    parser = argparse.ArgumentParser(description="MQI Data Processing CLI: Parses RTPLAN, PTN logs, and generates MOQUI CSVs.")
    
    parser.add_argument("--logdir", type=Path, required=True, help="Path to the directory containing .ptn log files.")
    parser.add_argument("--outputdir", type=Path, required=True, help="Path to the base directory for output CSV files.")

    args = parser.parse_args()

    print("--- MQI Data Processing Started ---")
    print(f"Log Directory: {args.logdir}")
    print(f"Output Directory: {args.outputdir}")
    
    # Find DCM file in logdir
    rtplan_path = find_dcm_file_in_logdir(str(args.logdir))
    if not rtplan_path:
        raise FileNotFoundError(f"No .dcm file found in {args.logdir}/logs directory")
    
    print(f"Found RTPLAN: {rtplan_path}")

    try:
        # 1. Parse RT Plan first to get TreatmentMachineName
        print(f"\nParsing RT Plan file: {rtplan_path}...")
        if not Path(rtplan_path).is_file():
            raise FileNotFoundError(f"RT Plan file not found: {rtplan_path}")
        rt_plan_data = dicom_parser.parse_rtplan(rtplan_path)
        print("RT Plan parsed successfully.")
        
        # 2. Determine config file based on TreatmentMachineName
        config_file = None
        treatment_machine_names = []
        
        for beam in rt_plan_data.get('beams', []):
            treatment_machine_name = beam.get('treatment_machine_name')
            if treatment_machine_name:
                treatment_machine_names.append(treatment_machine_name)
        
        if not treatment_machine_names:
            raise ValueError("Error: No TreatmentMachineName found in RT Plan beams")
        
        # Check for G1 or G2 in TreatmentMachineName
        has_g1 = any("G1" in name for name in treatment_machine_names)
        has_g2 = any("G2" in name for name in treatment_machine_names)
        
        if has_g1 and has_g2:
            raise ValueError("Error: RT Plan contains both G1 and G2 treatment machines")
        elif has_g1:
            config_file = "scv_init_G1.txt"
        elif has_g2:
            config_file = "scv_init_G2.txt"
        else:
            raise ValueError("Error: No G1 or G2 found in TreatmentMachineName")
        
        print(f"Selected config file: {config_file}")
        
        # 3. Load Configurations
        print(f"\nLoading SCV init parameters from: {config_file}...")
        if not Path(config_file).is_file():
            raise FileNotFoundError(f"SCV init config file not found: {config_file}")
        scv_init_params = config_loader.parse_scv_init(config_file)
        if not scv_init_params: # parse_scv_init returns empty dict on error or if file is empty
             raise ValueError(f"Failed to load or parse SCV init parameters from {config_file}. Ensure file is valid and not empty.")
        print("SCV init parameters loaded successfully.")

        # 5. Discover and Sort Log Files
        print(f"\nDiscovering .ptn log files in: {args.logdir}...")
        if not args.logdir.is_dir():
            raise FileNotFoundError(f"Log directory not found: {args.logdir}")
        
        ptn_file_paths = sorted(list(args.logdir.glob('**/*.ptn')))
        if not ptn_file_paths:
            raise FileNotFoundError(f"No .ptn files found in {args.logdir}.")
        
        num_log_files = len(ptn_file_paths)
        print(f"Found {num_log_files} .ptn files.")

        # 4. Load Dose Monitor Ranges from PlanRange.txt files
        print(f"\nLoading dose monitor ranges from PlanRange.txt files in: {args.logdir}...")
        planrange_data = config_loader.parse_planrange_files(str(args.logdir))
        print("PlanRange.txt files loaded successfully.")
        
        # Combine all dose ranges from all timestamp directories
        all_dose_ranges = []
        for timestamp_dir, dose_ranges in planrange_data.items():
            all_dose_ranges.extend(dose_ranges)
        
        dose_monitor_ranges = all_dose_ranges
        print(f"Total dose monitor ranges loaded: {len(dose_monitor_ranges)}")

        # 6. Parse all PTN Log Files
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

        # 7. Generate MOQUI CSVs
        print("\nGenerating MOQUI CSV files...")
        # Ensure output directory exists, generate_moqui_csvs will create patient/field subdirs
        args.outputdir.mkdir(parents=True, exist_ok=True) 
        
        moqui_generator.generate_moqui_csvs(
            rt_plan_data,
            ptn_data_list,
            dose_monitor_ranges,
            str(args.outputdir) # Function expects string path
        )
        print(f"MOQUI CSV files generated successfully in {args.outputdir}.")

        # 8. Export Aperture/MLC Data (automatic for G1 machines with aperture/MLC)
        # Check if any beam is G1 and has aperture or MLC data
        has_g1_beam = any("G1" in beam.get('treatment_machine_name', '') for beam in rt_plan_data.get('beams', []))
        
        if has_g1_beam:
            print("\nChecking for aperture/MLC data in G1 beams...")
            try:
                # Read DICOM file again to access raw beam data
                import pydicom
                ds = pydicom.dcmread(rtplan_path)
                
                aperture_files = aperture_generator.extract_and_generate_aperture_data_g1(
                    ds, rt_plan_data, str(args.outputdir)
                )
                
                if aperture_files:
                    print(f"Aperture/MLC CSV files generated: {len(aperture_files)} files")
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
