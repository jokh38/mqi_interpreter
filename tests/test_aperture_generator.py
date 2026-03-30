from pathlib import Path
from types import SimpleNamespace

from generators.aperture_generator import extract_and_generate_aperture_data_g1


def test_extract_and_generate_aperture_data_g1_exports_both_aperture_and_mlc(
    monkeypatch, tmp_path: Path
) -> None:
    beam_ds = SimpleNamespace(
        BeamName="Field1",
        TreatmentMachineName="G1",
        BeamDescription="",
        IonBlockSequence=[object()],
        IonControlPointSequence=[
            SimpleNamespace(
                BeamLimitingDevicePositionSequence=[
                    SimpleNamespace(
                        RTBeamLimitingDeviceType="MLCX",
                        LeafJawPositions=[-80.0, -70.0],
                    )
                ]
            )
        ],
    )
    ds = SimpleNamespace(IonBeamSequence=[beam_ds])

    monkeypatch.setattr(
        "parsers.dicom_parser.extract_aperture_data",
        lambda beam: {
            "device_type": "aperture",
            "thickness_cm": 1.0,
            "material": "CERROBEND",
            "coordinate_system": "DICOM_IEC",
            "block_data": [[1.0, 2.0]],
        },
    )
    monkeypatch.setattr(
        "parsers.dicom_parser.extract_mlc_data",
        lambda beam: {
            "device_type": "mlc",
            "num_leaves": 2,
            "leaf_width_cm": 0.5,
            "coordinate_system": "DICOM_IEC",
            "leaf_positions": [
                {
                    "layer_energy_mev": 150.0,
                    "leaf_index": 1,
                    "left_pos_cm": -1.0,
                    "right_pos_cm": 1.0,
                }
            ],
        },
    )

    created = extract_and_generate_aperture_data_g1(ds, {}, str(tmp_path))

    assert len(created) == 4
    assert (tmp_path / "plan" / "Field1" / "field1_aperture.csv").is_file()
    assert (tmp_path / "log" / "Field1" / "field1_aperture.csv").is_file()
    assert (tmp_path / "plan" / "Field1" / "field1_mlc.csv").is_file()
    assert (tmp_path / "log" / "Field1" / "field1_mlc.csv").is_file()
