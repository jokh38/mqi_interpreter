import pydicom
from pydicom.errors import InvalidDicomError
import os

def parse_rtplan(file_path: str) -> dict:
    """
    Parses an RTPLAN DICOM file and extracts relevant information.

    Args:
        file_path: The path to the RTPLAN DICOM file.

    Returns:
        A dictionary containing the parsed RTPLAN data.

    Raises:
        FileNotFoundError: If the DICOM file is not found.
        InvalidDicomError: If the file is not a valid DICOM file.
        ValueError: If the Modality is not "RTPLAN", or if critical DICOM tags are missing.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Error: DICOM file not found at {file_path}")

    try:
        ds = pydicom.dcmread(file_path)
    except InvalidDicomError:
        raise InvalidDicomError(f"Error: Invalid DICOM file at {file_path}")
    except Exception as e:
        raise IOError(f"Error reading DICOM file: {e}")

    # 1. Validate Modality
    if ds.get("Modality") != "RTPLAN":
        raise ValueError("Error: DICOM file is not an RTPLAN. Modality is '{}'.".format(ds.get("Modality")))

    rt_plan_data = {}

    # 2. Extract Top-Level Data
    try:
        rt_plan_data["patient_id"] = ds.PatientID
    except AttributeError:
        raise ValueError("Error: Missing critical tag PatientID (0010,0020)")
        
    rt_plan_data["rt_plan_label"] = ds.get("RTPlanLabel", None) # (300A,0003) - RTPlanName is (300A,0002)
    rt_plan_data["rt_plan_date"] = ds.get("RTPlanDate", None)  # (300A,0006)
    
    # Optional: Extract Number of Beams from FractionGroupSequence
    # This is more of a high-level info, actual beam data comes from IonBeamSequence
    num_beams_from_fraction_group = None
    if "FractionGroupSequence" in ds and ds.FractionGroupSequence:
        # Typically one item in this sequence for RTPLAN
        fraction_group = ds.FractionGroupSequence[0]
        if "NumberOfBeams" in fraction_group:
            num_beams_from_fraction_group = fraction_group.NumberOfBeams
            rt_plan_data["number_of_beams_in_fraction_group"] = num_beams_from_fraction_group
            
    rt_plan_data["beam_energy_unit"] = None # Will be extracted from the first control point of the first beam
    rt_plan_data["beams"] = []

    if not hasattr(ds, 'IonBeamSequence') or not ds.IonBeamSequence:
        # No ion beams, could be an empty plan or a different type of plan not covered
        # Depending on requirements, this could be an error or just return empty beams list.
        # For now, return with empty beams list if sequence is missing/empty.
        # If beams are expected, a stricter check might be needed.
        return rt_plan_data 

    first_beam_first_cp_energy_unit_found = False

    for i, beam_ds in enumerate(ds.IonBeamSequence):
        beam_data = {}
        try:
            beam_data["beam_name"] = beam_ds.BeamName
        except AttributeError:
            beam_data["beam_name"] = f"Beam_{i+1}_Unnamed" # Or raise error
            # raise ValueError(f"Error: Missing BeamName for beam index {i}")

        beam_data["snout_position"] = None # From first control point of this beam
        beam_data["has_range_shifter"] = "RangeShifterSequence" in beam_ds and bool(beam_ds.RangeShifterSequence)
        beam_data["energy_layers"] = []

        if not hasattr(beam_ds, 'IonControlPointSequence') or not beam_ds.IonControlPointSequence:
            # No control points for this beam, skip MU calculation for it or error
            rt_plan_data["beams"].append(beam_data) # Add beam with empty energy layers
            continue

        control_points = beam_ds.IonControlPointSequence
        
        # Extract SnoutPosition from the first control point of this beam
        if control_points:
            try:
                beam_data["snout_position"] = control_points[0].SnoutPosition
            except AttributeError:
                # Optional: Log warning or handle as per requirements if missing
                pass 

        # Extract NominalBeamEnergyUnit from the first control point of the *first* beam
        if not first_beam_first_cp_energy_unit_found and control_points:
            try:
                rt_plan_data["beam_energy_unit"] = control_points[0].NominalBeamEnergyUnit
                first_beam_first_cp_energy_unit_found = True
            except AttributeError:
                 # Optional: Log warning if missing, but it's quite important
                pass


        # MU Calculation Logic
        processed_cps = [] # Stores (energy, cumulative_mu) for this beam
        for cp_ds in control_points:
            try:
                energy = cp_ds.NominalBeamEnergy
                cumulative_mu = cp_ds.CumulativeMetersetWeight
                processed_cps.append({"energy": float(energy), "cumulative_mu": float(cumulative_mu)})
            except AttributeError:
                raise ValueError(f"Error: Missing NominalBeamEnergy or CumulativeMetersetWeight in a control point for beam '{beam_data['beam_name']}'.")
            except (TypeError, ValueError):
                raise ValueError(f"Error: Non-numeric NominalBeamEnergy or CumulativeMetersetWeight in a control point for beam '{beam_data['beam_name']}'.")

        if not processed_cps:
            rt_plan_data["beams"].append(beam_data) # No control points with MU data
            continue

        # Sort by cumulative MU just in case control points are not strictly ordered by MU (should be, but defensive)
        # However, the primary sort/grouping key for layers is energy, and MU diffs are sequential.
        # The DICOM standard implies control points are ordered.

        current_layer_nominal_energy = None
        last_cumulative_mu_for_energy_layer_calculation = 0.0
        
        # Iterate through sorted control points to calculate MU per energy layer
        # This logic assumes control points are ordered correctly.
        # The MU for an energy layer is the difference between its CumulativeMetersetWeight 
        # and the CumulativeMetersetWeight of the previous distinct energy layer's last control point.
        # For the very first energy layer, its MU is its own CumulativeMetersetWeight.

        # Let's group by energy first, then process
        # No, the C++ logic iterates and calculates when energy changes or at the end.

        # Simplified logic attempt:
        # Group control points by energy, maintaining order of first appearance of that energy.
        # Then calculate MU for each energy block.

        # More direct approach based on iterating CPs and detecting energy changes:
        
        # Store (energy, cumulative_mu_at_end_of_layer)
        # This will hold the *final* cumulative MU for each energy layer block.
        # e.g. if energy 70 has CPs with MU 2, 5, 7, then (70, 7) is stored.
        # if energy 80 has CPs with MU 10, 12, then (80, 12) is stored.
        
        # Corrected MU calculation logic:
        # Iterate through control points. When energy changes, the MU for the *previous*
        # energy layer is the CumulativeMetersetWeight of the *last control point of that previous energy*
        # minus the CumulativeMetersetWeight of the *last control point of the layer before that*.
        
        layer_end_points = [] # list of (energy, cumulative_mu_at_end_of_layer)
        if processed_cps:
            current_energy = processed_cps[0]['energy']
            for k in range(len(processed_cps)):
                # If energy changes or it's the last CP, then the previous CP (k-1) was the end of an energy layer
                if k + 1 < len(processed_cps) and processed_cps[k+1]['energy'] != current_energy:
                    layer_end_points.append({'energy': current_energy, 'cumulative_mu': processed_cps[k]['cumulative_mu']})
                    current_energy = processed_cps[k+1]['energy']
                elif k == len(processed_cps) - 1: # Last control point
                    layer_end_points.append({'energy': current_energy, 'cumulative_mu': processed_cps[k]['cumulative_mu']})
        
        previous_layer_ending_mu = 0.0
        for layer_info in layer_end_points:
            mu_for_layer = layer_info['cumulative_mu'] - previous_layer_ending_mu
            if mu_for_layer < 0: # Should not happen in a valid plan
                # Potentially raise error or warning
                print(f"Warning: Negative MU calculated for energy {layer_info['energy']} in beam {beam_data['beam_name']}. MU: {mu_for_layer}")
            
            # Avoid adding layers with zero or negative MU if that's a requirement
            # For now, adding them as calculated.
            beam_data["energy_layers"].append({
                "nominal_energy": layer_info['energy'],
                "mu": round(mu_for_layer, 7) # Round to avoid floating point issues, precision can be adjusted
            })
            previous_layer_ending_mu = layer_info['cumulative_mu']
            
        rt_plan_data["beams"].append(beam_data)

    return rt_plan_data

if __name__ == '__main__':
    # This is a placeholder for testing.
    # To test properly, a sample RTPLAN DICOM file is needed.
    # Example:
    # try:
    #     # Assume 'sample_rtplan.dcm' exists in the same directory or provide full path
    #     # Create a dummy file for basic testing if pydicom is installed
    #     from pydicom.dataset import Dataset, FileMetaDataset
    #     from pydicom.sequence import Sequence
    #     
    #     file_meta = FileMetaDataset()
    #     file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.481.5' # RT Plan Storage
    #     file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    #     file_meta.ImplementationClassUID = pydicom.uid.generate_uid()
    #     file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    # 
    #     ds = Dataset()
    #     ds.file_meta = file_meta
    #     ds.Modality = "RTPLAN"
    #     ds.PatientID = "TestPatientID"
    #     ds.RTPlanLabel = "TestPlan"
    #     ds.RTPlanDate = "20240101"
    # 
    #     # IonBeamSequence
    #     ion_beam_sequence = Sequence()
    #     ds.IonBeamSequence = ion_beam_sequence
    # 
    #     beam1 = Dataset()
    #     beam1.BeamName = "TestBeam1"
    #     beam1.RangeShifterSequence = Sequence() # Empty, so has_range_shifter = True but no details
    #     
    #     # IonControlPointSequence for beam1
    #     cp_sequence_b1 = Sequence()
    #     beam1.IonControlPointSequence = cp_sequence_b1
    # 
    #     cp1_b1 = Dataset()
    #     cp1_b1.NominalBeamEnergyUnit = "MeV"
    #     cp1_b1.SnoutPosition = 100.0
    #     cp1_b1.NominalBeamEnergy = 70.0
    #     cp1_b1.CumulativeMetersetWeight = 5.0
    #     cp_sequence_b1.append(cp1_b1)
    # 
    #     cp2_b1 = Dataset()
    #     # SnoutPosition and NominalBeamEnergyUnit usually same for subsequent CPs in a beam
    #     cp2_b1.NominalBeamEnergy = 70.0 # Same energy
    #     cp2_b1.CumulativeMetersetWeight = 12.0 # 12-5 = 7 MU for this segment, total 12 for 70 MeV
    #     cp_sequence_b1.append(cp2_b1)
    # 
    #     cp3_b1 = Dataset()
    #     cp3_b1.NominalBeamEnergy = 80.0 # New energy
    #     cp3_b1.CumulativeMetersetWeight = 20.0 # 20-12 = 8 MU for this 80MeV layer
    #     cp_sequence_b1.append(cp3_b1)
    #     
    #     ion_beam_sequence.append(beam1)
    #     
    #     ds.is_little_endian = True
    #     ds.is_implicit_VR = False # Explicit VR
    # 
    #     pydicom.dcmwrite("dummy_rtplan.dcm", ds, write_like_original=False)
    #     print("Created dummy_rtplan.dcm for basic testing.")
    # 
    #     parsed_plan = parse_rtplan("dummy_rtplan.dcm")
    #     print("\nParsed RTPLAN data:")
    #     import json
    #     print(json.dumps(parsed_plan, indent=4))
    #     
    #     # Test modality validation
    #     # ds.Modality = "CT"
    #     # pydicom.dcmwrite("dummy_ct.dcm", ds, write_like_original=False)
    #     # try:
    #     #     parse_rtplan("dummy_ct.dcm")
    #     # except ValueError as e:
    #     #     print(f"\nCorrectly caught error for wrong modality: {e}")
    #     # finally:
    #     #     if os.path.exists("dummy_ct.dcm"): os.remove("dummy_ct.dcm")
    # 
    # except ImportError:
    #     print("pydicom is not installed. Skipping dummy file creation and test.")
    # except Exception as e:
    #     print(f"An error occurred during dummy file testing: {e}")
    # finally:
    try:
        from pydicom.dataset import Dataset, FileMetaDataset
        from pydicom.sequence import Sequence
        import pydicom.uid

        file_meta = FileMetaDataset()
        file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.481.5' # RT Plan Storage
        file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        file_meta.ImplementationClassUID = pydicom.uid.generate_uid()
        file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian # Explicit VR Little Endian

        ds = Dataset()
        ds.file_meta = file_meta
        ds.is_little_endian = True # Ensure correct byte order for writing
        ds.is_implicit_VR = False  # Ensure explicit VR for writing

        ds.Modality = "RTPLAN"
        ds.PatientID = "TestPatient123"
        ds.RTPlanLabel = "TestPlanLabel01"
        ds.RTPlanDate = "20240315"

        # Optional: FractionGroupSequence
        fraction_group_sequence = Sequence()
        fg = Dataset()
        fg.NumberOfBeams = 1
        fraction_group_sequence.append(fg)
        ds.FractionGroupSequence = fraction_group_sequence
        
        ion_beam_sequence = Sequence()
        ds.IonBeamSequence = ion_beam_sequence

        # Beam 1
        beam1 = Dataset()
        beam1.BeamName = "ProtonBeam1"
        # RangeShifterSequence: Not adding one means has_range_shifter should be False
        # beam1.RangeShifterSequence = Sequence() # To make it True

        cp_sequence_b1 = Sequence()
        beam1.IonControlPointSequence = cp_sequence_b1

        # CP1 for Beam1 (Energy Layer 1, part 1)
        cp1_b1 = Dataset()
        cp1_b1.NominalBeamEnergyUnit = "MeV" # Should be picked up for the plan
        cp1_b1.SnoutPosition = 100.0        # Should be picked for beam1
        cp1_b1.NominalBeamEnergy = 70.0
        cp1_b1.CumulativeMetersetWeight = 5.0
        cp_sequence_b1.append(cp1_b1)

        # CP2 for Beam1 (Energy Layer 1, part 2)
        cp2_b1 = Dataset()
        cp2_b1.NominalBeamEnergy = 70.0 # Same energy
        cp2_b1.CumulativeMetersetWeight = 12.0 # Total for 70MeV layer is 12 MU
        cp_sequence_b1.append(cp2_b1)
        
        # CP3 for Beam1 (Energy Layer 2)
        cp3_b1 = Dataset()
        cp3_b1.NominalBeamEnergy = 80.0 # New energy
        cp3_b1.CumulativeMetersetWeight = 20.0 # 80MeV layer MU is 20-12=8 MU
        cp_sequence_b1.append(cp3_b1)

        ion_beam_sequence.append(beam1)
        
        dummy_file_path = "dummy_rtplan_test.dcm"
        pydicom.dcmwrite(dummy_file_path, ds, write_like_original=False) # write_like_original=False for new files
        print(f"Created dummy DICOM file: {dummy_file_path}")

        parsed_plan = parse_rtplan(dummy_file_path)
        print("\nParsed RTPLAN data from dummy file:")
        import json
        print(json.dumps(parsed_plan, indent=4))

        # Expected MU for Beam1:
        # Layer 1 (70 MeV): 12.0 MU (CumulativeMetersetWeight of last CP of 70MeV)
        # Layer 2 (80 MeV): 20.0 - 12.0 = 8.0 MU
        expected_beam1_layers = [
            {"nominal_energy": 70.0, "mu": 12.0},
            {"nominal_energy": 80.0, "mu": 8.0}
        ]
        assert parsed_plan["beams"][0]["energy_layers"] == expected_beam1_layers
        assert parsed_plan["beam_energy_unit"] == "MeV"
        assert parsed_plan["beams"][0]["snout_position"] == 100.0
        assert not parsed_plan["beams"][0]["has_range_shifter"] # Since we didn't add the sequence
        print("\nBasic assertions passed for dummy RTPLAN.")

    except ImportError:
        print("pydicom is not installed. Skipping dummy RTPLAN test.")
    except Exception as e:
        print(f"An error occurred during dummy RTPLAN testing: {e}")
    finally:
        if os.path.exists(dummy_file_path):
            os.remove(dummy_file_path)
            print(f"Cleaned up {dummy_file_path}.")
