import os
from pathlib import Path
import csv


def generate_aperture_csv(beam_name: str, aperture_data: dict, output_path: str):
    """
    Generate CSV file for aperture data.
    
    Args:
        beam_name: Name of the beam
        aperture_data: Dictionary containing aperture information
        output_path: Full path for the output CSV file
    """
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        # Write header with metadata
        csvfile.write(f"# beam_name={beam_name}\n")
        csvfile.write(f"# device_type={aperture_data['device_type']}\n")
        csvfile.write(f"# thickness_cm={aperture_data['thickness_cm']}\n")
        csvfile.write(f"# material={aperture_data['material']}\n") 
        csvfile.write(f"# coordinate_system={aperture_data['coordinate_system']}\n")
        
        # Write coordinate data
        writer = csv.writer(csvfile)
        writer.writerow(['x_coord_cm', 'y_coord_cm'])
        
        for coord in aperture_data['block_data']:
            writer.writerow([f"{coord[0]:.3f}", f"{coord[1]:.3f}"])


def generate_mlc_csv(beam_name: str, mlc_data: dict, output_path: str):
    """
    Generate CSV file for MLC data.
    
    Args:
        beam_name: Name of the beam
        mlc_data: Dictionary containing MLC information
        output_path: Full path for the output CSV file
    """
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        # Write header with metadata
        csvfile.write(f"# beam_name={beam_name}\n")
        csvfile.write(f"# device_type={mlc_data['device_type']}\n")
        csvfile.write(f"# num_leaves={mlc_data['num_leaves']}\n")
        csvfile.write(f"# leaf_width_cm={mlc_data['leaf_width_cm']:.3f}\n")
        csvfile.write(f"# coordinate_system={mlc_data['coordinate_system']}\n")
        
        # Write leaf position data
        writer = csv.writer(csvfile)
        writer.writerow(['layer_energy_mev', 'leaf_index', 'left_pos_cm', 'right_pos_cm'])
        
        for leaf_pos in mlc_data['leaf_positions']:
            writer.writerow([
                f"{leaf_pos['layer_energy_mev']:.1f}",
                leaf_pos['leaf_index'],
                f"{leaf_pos['left_pos_cm']:.3f}",
                f"{leaf_pos['right_pos_cm']:.3f}"
            ])





def extract_and_generate_aperture_data_g1(ds, rt_plan_data: dict, output_base_dir: str):
    """
    Extract aperture/MLC data from DICOM dataset and generate CSV files for G1 machines only.
    Only exports when:
    - TreatmentMachineName contains "G1"
    - Aperture: IonBlockSequence is not None
    - MLC: MLC position is greater than -9 (home position)
    
    Files are saved in both rtplan and log folders.
    
    Args:
        ds: Original DICOM dataset
        rt_plan_data: Parsed RT plan data
        output_base_dir: Base directory for output files
        
    Returns:
        list: List of created aperture/MLC CSV file paths
    """
    from parsers.dicom_parser import extract_aperture_data, extract_mlc_data
    
    # Create output directories with patient_id subdirectory for both rtplan and log
    aperture_files_created = []
    if not hasattr(ds, 'IonBeamSequence') or not ds.IonBeamSequence:
        print("No ion beams found in DICOM file")
        return aperture_files_created
    
    for i, beam_ds in enumerate(ds.IonBeamSequence):
        beam_name = getattr(beam_ds, 'BeamName', f'Field{i+1}')
        treatment_machine_name = getattr(beam_ds, 'TreatmentMachineName', '')
        
        # Filter out Site Setup and SETUP beams
        beam_description = getattr(beam_ds, 'BeamDescription', '')
        if beam_description == "Site Setup" or beam_name == "SETUP":
            continue
        
        # Only process G1 machines
        if "G1" not in treatment_machine_name:
            continue

        output_dir = Path(output_base_dir)
        
        # Check aperture first - only export if IonBlockSequence is not None
        if hasattr(beam_ds, 'IonBlockSequence') and beam_ds.IonBlockSequence:
            aperture_data = extract_aperture_data(beam_ds)
            if aperture_data:
                output_path = output_dir / f"{beam_name.lower()}_aperture.csv"
                generate_aperture_csv(beam_name, aperture_data, str(output_path))
                aperture_files_created.append(str(output_path))
                
                print(f"Generated aperture files for G1 beam: {output_path}")
                continue
        
        # Check MLC - only export if MLC positions are greater than -9 (home position)
        if _has_mlc_beyond_home_position(beam_ds):
            mlc_data = extract_mlc_data(beam_ds)
            if mlc_data:
                output_path = output_dir / f"{beam_name.lower()}_mlc.csv"
                generate_mlc_csv(beam_name, mlc_data, str(output_path))
                
                aperture_files_created.append(str(output_path))
                
                print(f"Generated MLC files for G1 beam: {output_path}")
                continue
        
        print(f"No qualifying aperture or MLC data found for G1 beam: {beam_name}")
    
    return aperture_files_created


def _has_mlc_beyond_home_position(beam_ds):
    """
    Check if MLC positions have changed from home position.
    A home position is considered to be a large negative value (e.g., <= -9.0 cm).
    N/2 is forced to be integer using N//2.
    
    Args:
        beam_ds: DICOM beam dataset
        
    Returns:
        bool: True if MLC positions are beyond home position
    """
    if not hasattr(beam_ds, 'IonControlPointSequence') or not beam_ds.IonControlPointSequence:
        return False
    
    # Check first control point (Segments[0])
    first_cp = beam_ds.IonControlPointSequence[0]
    
    if not hasattr(first_cp, 'BeamLimitingDevicePositionSequence'):
        return False
    
    for device_pos in first_cp.BeamLimitingDevicePositionSequence:
        if hasattr(device_pos, 'RTBeamLimitingDeviceType') and 'MLC' in device_pos.RTBeamLimitingDeviceType:
            if hasattr(device_pos, 'LeafJawPositions'):
                leaf_positions = device_pos.LeafJawPositions
                # LeafJawPositions are in mm. We check if any position is greater than -90mm (-9cm).
                # A value greater than this indicates the leaf is not in its home/retracted position.
                for pos in leaf_positions:
                    try:
                        if float(pos) > -90.0: # -90mm is -9cm
                            return True
                    except (ValueError, TypeError):
                        # Ignore if position is not a valid number
                        continue
                    
    return False