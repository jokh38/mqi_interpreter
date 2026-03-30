from pathlib import Path

import numpy as np

from generators.moqui_generator import generate_moqui_csvs


def test_generate_moqui_csvs_writes_only_log_output(tmp_path: Path) -> None:
    rt_plan_data = {
        "beams": [
            {
                "beam_name": "BeamA",
                "energy_layers": [{"nominal_energy": 150.0}],
            }
        ]
    }
    ptn_data_list = [
        {
            "dose1_au": np.array([10, 20], dtype=np.float32),
            "time_ms": np.array([0.0, 1.0], dtype=np.float32),
            "x_mm": np.array([1.0, 2.0], dtype=np.float32),
            "y_mm": np.array([3.0, 4.0], dtype=np.float32),
        }
    ]
    dose_monitor_ranges = [2]

    generate_moqui_csvs(rt_plan_data, ptn_data_list, dose_monitor_ranges, str(tmp_path))

    log_csv = tmp_path / "log" / "BeamA" / "01_150.00MeV.csv"
    assert log_csv.is_file()
    assert not (tmp_path / "plan").exists()


def test_generate_moqui_csvs_skips_setup_beam_name(tmp_path: Path) -> None:
    rt_plan_data = {
        "beams": [
            {
                "beam_name": "SETUP",
                "energy_layers": [{"nominal_energy": 100.0}],
            },
            {
                "beam_name": "BeamB",
                "energy_layers": [{"nominal_energy": 150.0}],
            },
        ]
    }
    ptn_data_list = [
        {
            "dose1_au": np.array([10, 20], dtype=np.float32),
            "time_ms": np.array([0.0, 1.0], dtype=np.float32),
            "x_mm": np.array([1.0, 2.0], dtype=np.float32),
            "y_mm": np.array([3.0, 4.0], dtype=np.float32),
        },
        {
            "dose1_au": np.array([30, 40], dtype=np.float32),
            "time_ms": np.array([0.0, 1.0], dtype=np.float32),
            "x_mm": np.array([5.0, 6.0], dtype=np.float32),
            "y_mm": np.array([7.0, 8.0], dtype=np.float32),
        },
    ]
    dose_monitor_ranges = [2, 2]

    generate_moqui_csvs(rt_plan_data, ptn_data_list, dose_monitor_ranges, str(tmp_path))

    assert not (tmp_path / "log" / "SETUP").exists()
    assert (tmp_path / "log" / "BeamB" / "01_150.00MeV.csv").is_file()


def test_setup_skip_does_not_consume_ptn_entries(tmp_path: Path) -> None:
    rt_plan_data = {
        "beams": [
            {
                "beam_name": "SETUP",
                "energy_layers": [{"nominal_energy": 100.0}],
            },
            {
                "beam_name": "BeamB",
                "energy_layers": [{"nominal_energy": 150.0}],
            },
        ]
    }
    ptn_data_list = [
        {
            "dose1_au": np.array([10], dtype=np.float32),
            "time_ms": np.array([0.0], dtype=np.float32),
            "x_mm": np.array([1.0], dtype=np.float32),
            "y_mm": np.array([3.0], dtype=np.float32),
        }
    ]
    dose_monitor_ranges = [2]

    generate_moqui_csvs(rt_plan_data, ptn_data_list, dose_monitor_ranges, str(tmp_path))

    log_csv = tmp_path / "log" / "BeamB" / "01_150.00MeV.csv"
    assert log_csv.is_file()
    assert log_csv.read_text(encoding="utf-8").startswith("0.0,1.0,3.0,")


def test_setup_beam_not_counted_in_total_layer_warning(
    tmp_path: Path, capsys
) -> None:
    rt_plan_data = {
        "beams": [
            {
                "beam_name": "SETUP",
                "is_setup_field": True,
                "energy_layers": [{"nominal_energy": 100.0}],
            },
            {
                "beam_name": "BeamB",
                "energy_layers": [{"nominal_energy": 150.0}],
            },
        ]
    }
    ptn_data_list = [
        {
            "dose1_au": np.array([10], dtype=np.float32),
            "time_ms": np.array([0.0], dtype=np.float32),
            "x_mm": np.array([1.0], dtype=np.float32),
            "y_mm": np.array([3.0], dtype=np.float32),
        }
    ]
    dose_monitor_ranges = [2]

    generate_moqui_csvs(rt_plan_data, ptn_data_list, dose_monitor_ranges, str(tmp_path))

    captured = capsys.readouterr()
    assert "Number of processed layers" not in captured.out
