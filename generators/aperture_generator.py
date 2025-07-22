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
    patient_id = rt_plan_data.get("patient_id", "unknown_patient")
    rtplan_output_dir = Path(output_base_dir) / patient_id / "rtplan"
    log_output_dir = Path(output_base_dir) / patient_id / "log"
    
    rtplan_output_dir.mkdir(parents=True, exist_ok=True)
    log_output_dir.mkdir(parents=True, exist_ok=True)
    
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
            
        # Create field directories for both rtplan and log
        rtplan_field_dir = rtplan_output_dir / beam_name
        log_field_dir = log_output_dir / beam_name
        
        rtplan_field_dir.mkdir(parents=True, exist_ok=True)
        log_field_dir.mkdir(parents=True, exist_ok=True)
        
        # Check aperture first - only export if IonBlockSequence is not None
        if hasattr(beam_ds, 'IonBlockSequence') and beam_ds.IonBlockSequence:
            aperture_data = extract_aperture_data(beam_ds)
            if aperture_data:
                # Generate aperture files in both rtplan and log folders
                rtplan_aperture_path = rtplan_field_dir / f"{beam_name.lower()}_aperture.csv"
                log_aperture_path = log_field_dir / f"{beam_name.lower()}_aperture.csv"
                
                generate_aperture_csv(beam_name, aperture_data, str(rtplan_aperture_path))
                generate_aperture_csv(beam_name, aperture_data, str(log_aperture_path))
                
                aperture_files_created.append(str(rtplan_aperture_path))
                aperture_files_created.append(str(log_aperture_path))
                
                print(f"Generated aperture files for G1 beam: {rtplan_aperture_path} and {log_aperture_path}")
                continue
        
        # Check MLC - only export if MLC positions are greater than -9 (home position)
        if _has_mlc_beyond_home_position(beam_ds):
            mlc_data = extract_mlc_data(beam_ds)
            if mlc_data:
                # Generate MLC files in both rtplan and log folders
                rtplan_mlc_path = rtplan_field_dir / f"{beam_name.lower()}_mlc.csv"
                log_mlc_path = log_field_dir / f"{beam_name.lower()}_mlc.csv"
                
                generate_mlc_csv(beam_name, mlc_data, str(rtplan_mlc_path))
                generate_mlc_csv(beam_name, mlc_data, str(log_mlc_path))
                
                aperture_files_created.append(str(rtplan_mlc_path))
                aperture_files_created.append(str(log_mlc_path))
                
                print(f"Generated MLC files for G1 beam: {rtplan_mlc_path} and {log_mlc_path}")
                continue
        
        print(f"No qualifying aperture or MLC data found for G1 beam: {beam_name}")
    
    return aperture_files_created


def _has_mlc_beyond_home_position(beam_ds):
    """
    Check if MLC positions have changed from home position.
    Reads Segments[0].LeafPositions as N행 2열 format.
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
                N = len(leaf_positions)
                
                if N < 2:
                    return False
                
                # N must be even for proper MLC pair formation
                if N % 2 != 0:
                    print(f"Warning: Odd number of MLC positions ({N}). Using N//2 for middle index calculation.")
                
                # Convert to N행 2열 format: N/2 pairs of (left, right) positions
                # Use N//2 to ensure integer division as required
                N_half = N // 2
                
                if N_half == 0:
                    return False
                
                # Get positions: first N_half are left positions, second N_half are right positions
                left_positions = leaf_positions[:N_half]
                right_positions = leaf_positions[N_half:2*N_half]  # Ensure we take exactly N_half elements
                
                if len(left_positions) != len(right_positions):
                    print(f"Warning: Mismatch in left ({len(left_positions)}) and right ({len(right_positions)}) MLC positions.")
                    return False
                
                # Calculate middle index: N/2 -> N_half, then N_half/2 using integer division
                # This represents the middle MLC pair index
                middle_idx = N_half // 2
                
                if middle_idx >= len(left_positions) or middle_idx >= len(right_positions):
                    print(f"Warning: Middle index ({middle_idx}) out of bounds for MLC positions.")
                    return False
                
                # Compare middle MLC pair with outermost (first) MLC pair
                # Segments[0].LeafPositions[N/2][1] != Segments[0].LeafPositions[0][1] (left positions)
                # or 
                # Segments[0].LeafPositions[N/2][2] != Segments[0].LeafPositions[0][2] (right positions)
                if (left_positions[middle_idx] != left_positions[0] or 
                    right_positions[middle_idx] != right_positions[0]):
                    return True
                    
    return False