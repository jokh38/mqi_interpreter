from pathlib import Path

import pytest

from mqi_common import config_loader
from main_cli import validate_planinfo_against_rtplan


def test_parse_planinfo_files_reads_timestamp_directories(tmp_path: Path) -> None:
    first_dir = tmp_path / "2025042401440800"
    second_dir = tmp_path / "2025042401501400"
    first_dir.mkdir()
    second_dir.mkdir()

    (first_dir / "PlanInfo.txt").write_text(
        "\n".join(
            [
                "DICOM_PATIENT_ID,55061194",
                "DICOM_BEAM_NUMBER,2",
                "TCSC_FIELD_NUMBER,2",
                "STOP_LAYER_NUMBER,34",
            ]
        ),
        encoding="utf-8",
    )
    (second_dir / "PlanInfo.txt").write_text(
        "\n".join(
            [
                "DICOM_PATIENT_ID,55061194",
                "DICOM_BEAM_NUMBER,3",
                "TCSC_FIELD_NUMBER,3",
                "STOP_LAYER_NUMBER,32",
            ]
        ),
        encoding="utf-8",
    )

    parsed = config_loader.parse_planinfo_files(str(tmp_path))

    expected = {
        "2025042401440800": {
            "DICOM_PATIENT_ID": "55061194",
            "DICOM_BEAM_NUMBER": 2,
            "TCSC_FIELD_NUMBER": 2,
            "STOP_LAYER_NUMBER": 34,
        },
        "2025042401501400": {
            "DICOM_PATIENT_ID": "55061194",
            "DICOM_BEAM_NUMBER": 3,
            "TCSC_FIELD_NUMBER": 3,
            "STOP_LAYER_NUMBER": 32,
        },
    }
    if parsed != expected:
        pytest.fail(f"Unexpected parsed PlanInfo data: {parsed!r}")


def test_validate_planinfo_against_rtplan_accepts_matching_data() -> None:
    rt_plan_data = {
        "patient_id": "55061194",
        "beams": [
            {"beam_name": "SETUP", "energy_layers": [{"nominal_energy": 100.0}]},
            {"beam_name": "BeamA", "energy_layers": [{} for _ in range(34)]},
            {"beam_name": "BeamB", "energy_layers": [{} for _ in range(32)]},
        ],
    }
    planinfo_data = {
        "2025042401440800": {
            "DICOM_PATIENT_ID": "55061194",
            "DICOM_BEAM_NUMBER": 2,
            "TCSC_FIELD_NUMBER": 2,
            "STOP_LAYER_NUMBER": 34,
        },
        "2025042401501400": {
            "DICOM_PATIENT_ID": "55061194",
            "DICOM_BEAM_NUMBER": 3,
            "TCSC_FIELD_NUMBER": 3,
            "STOP_LAYER_NUMBER": 32,
        },
    }

    validate_planinfo_against_rtplan(rt_plan_data, planinfo_data)


def test_validate_planinfo_against_rtplan_rejects_mismatched_stop_layer() -> None:
    rt_plan_data = {
        "patient_id": "55061194",
        "beams": [
            {"beam_name": "SETUP", "energy_layers": [{"nominal_energy": 100.0}]},
            {"beam_name": "BeamA", "energy_layers": [{} for _ in range(34)]},
        ],
    }
    planinfo_data = {
        "2025042401440800": {
            "DICOM_PATIENT_ID": "55061194",
            "DICOM_BEAM_NUMBER": 2,
            "TCSC_FIELD_NUMBER": 2,
            "STOP_LAYER_NUMBER": 33,
        }
    }

    with pytest.raises(ValueError, match="STOP_LAYER_NUMBER"):
        validate_planinfo_against_rtplan(rt_plan_data, planinfo_data)


def test_validate_planinfo_against_rtplan_rejects_mismatched_field_number() -> None:
    rt_plan_data = {
        "patient_id": "55061194",
        "beams": [
            {"beam_name": "SETUP", "energy_layers": [{"nominal_energy": 100.0}]},
            {"beam_name": "BeamA", "energy_layers": [{} for _ in range(34)]},
        ],
    }
    planinfo_data = {
        "2025042401440800": {
            "DICOM_PATIENT_ID": "55061194",
            "DICOM_BEAM_NUMBER": 2,
            "TCSC_FIELD_NUMBER": 1,
            "STOP_LAYER_NUMBER": 34,
        }
    }

    with pytest.raises(ValueError, match="TCSC_FIELD_NUMBER"):
        validate_planinfo_against_rtplan(rt_plan_data, planinfo_data)
