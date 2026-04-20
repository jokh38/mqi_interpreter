from pathlib import Path

import numpy as np
import pytest

from generators.moqui_generator import generate_moqui_csvs, generate_plan_csvs


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


def test_generate_moqui_csvs_writes_one_row_per_sample(tmp_path: Path) -> None:
    rt_plan_data = {
        "beams": [
            {
                "beam_name": "BeamC",
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

    log_csv = tmp_path / "log" / "BeamC" / "01_150.00MeV.csv"
    rows = log_csv.read_text(encoding="utf-8").splitlines()
    assert rows == [
        "0.0,1.0,3.0,10",
        "1.0,2.0,4.0,20",
    ]


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


def test_generate_plan_csvs_writes_plan_output_only(tmp_path: Path) -> None:
    rt_plan_data = {
        "beams": [
            {
                "beam_name": "BeamPlan",
                "control_point_details": [
                    {
                        "energy": 150.0,
                        "scan_spot_positions": [1.0, 2.0, 3.0, 4.0],
                        "scan_spot_meterset_weights": [0.25, 0.5],
                    }
                ],
                "energy_layers": [{"nominal_energy": 150.0, "mu": 0.75}],
            }
        ]
    }

    generate_plan_csvs(rt_plan_data, str(tmp_path), time_gain_ms=25.0, normalization_factor=None)

    plan_csv = tmp_path / "plan" / "BeamPlan" / "01_150.00MeV.csv"
    assert plan_csv.is_file()
    assert not (tmp_path / "log").exists()


def test_generate_plan_csvs_uses_mm_positions_and_log_interval_sampling(tmp_path: Path) -> None:
    rt_plan_data = {
        "beams": [
            {
                "beam_name": "BeamPlan",
                "control_point_details": [
                    {
                        "energy": 150.0,
                        "scan_spot_positions": [1.0, 2.0, 3.0, 4.0],
                        "scan_spot_meterset_weights": [0.25, 0.5],
                    }
                ],
                "energy_layers": [{"nominal_energy": 150.0, "mu": 0.75}],
            }
        ]
    }

    generate_plan_csvs(rt_plan_data, str(tmp_path), time_gain_ms=5.0, normalization_factor=None)

    plan_csv = tmp_path / "plan" / "BeamPlan" / "01_150.00MeV.csv"
    rows = [
        [float(value) for value in row.split(",")]
        for row in plan_csv.read_text(encoding="utf-8").splitlines()
    ]
    assert rows[0] == [0.0, 1.0, 2.0, 0.25]
    assert rows[1][0] == pytest.approx(5.0)
    assert rows[2][0] == pytest.approx(10.0)
    assert rows[-1][0] == pytest.approx(25.0)
    assert rows[-1][1:] == pytest.approx([3.0, 4.0, 0.1])
    assert sum(row[3] for row in rows) == pytest.approx(0.75)


def test_generate_plan_csvs_skips_setup_beams(tmp_path: Path) -> None:
    rt_plan_data = {
        "beams": [
            {
                "beam_name": "SETUP",
                "is_setup_field": True,
                "control_point_details": [
                    {
                        "energy": 100.0,
                        "scan_spot_positions": [1.0, 2.0],
                        "scan_spot_meterset_weights": [0.25],
                    }
                ],
                "energy_layers": [{"nominal_energy": 100.0, "mu": 0.25}],
            },
            {
                "beam_name": "BeamPlan",
                "control_point_details": [
                    {
                        "energy": 150.0,
                        "scan_spot_positions": [3.0, 4.0],
                        "scan_spot_meterset_weights": [0.5],
                    }
                ],
                "energy_layers": [{"nominal_energy": 150.0, "mu": 0.5}],
            },
        ]
    }

    generate_plan_csvs(rt_plan_data, str(tmp_path), time_gain_ms=25.0, normalization_factor=None)

    assert not (tmp_path / "plan" / "SETUP").exists()
    assert (tmp_path / "plan" / "BeamPlan" / "01_150.00MeV.csv").is_file()


def test_generate_plan_csvs_normalizes_weights_to_layer_mu(tmp_path: Path) -> None:
    rt_plan_data = {
        "beams": [
            {
                "beam_name": "BeamPlan",
                "control_point_details": [
                    {
                        "energy": 150.0,
                        "scan_spot_positions": [1.0, 2.0, 1.0, 2.0],
                        "scan_spot_meterset_weights": [1.0, 3.0],
                    }
                ],
                "energy_layers": [{"nominal_energy": 150.0, "mu": 8.0}],
            }
        ]
    }

    generate_plan_csvs(rt_plan_data, str(tmp_path), time_gain_ms=1.0, normalization_factor=None)

    plan_csv = tmp_path / "plan" / "BeamPlan" / "01_150.00MeV.csv"
    rows = [
        [float(value) for value in row.split(",")]
        for row in plan_csv.read_text(encoding="utf-8").splitlines()
    ]
    assert rows[0][0:3] == [0.0, 1.0, 2.0]
    assert all(row[1:3] == pytest.approx([1.0, 2.0]) for row in rows)
    assert sum(row[3] for row in rows) == pytest.approx(8.0)


def test_generate_plan_csvs_applies_inverse_normalization_factor(tmp_path: Path) -> None:
    rt_plan_data = {
        "beams": [
            {
                "beam_name": "BeamPlan",
                "control_point_details": [
                    {
                        "energy": 150.0,
                        "scan_spot_positions": [1.0, 2.0],
                        "scan_spot_meterset_weights": [1.0],
                    }
                ],
                "energy_layers": [{"nominal_energy": 150.0, "mu": 2.12e-8}],
            }
        ]
    }

    generate_plan_csvs(
        rt_plan_data,
        str(tmp_path),
        time_gain_ms=1.0,
        normalization_factor=2.12e-8,
    )

    plan_csv = tmp_path / "plan" / "BeamPlan" / "01_150.00MeV.csv"
    rows = [
        [float(value) for value in row.split(",")]
        for row in plan_csv.read_text(encoding="utf-8").splitlines()
    ]
    assert rows == [[0.0, 1.0, 2.0, 1.0]]


def test_generate_plan_csvs_rounds_normalized_counts_to_integers(tmp_path: Path) -> None:
    rt_plan_data = {
        "beams": [
            {
                "beam_name": "BeamPlan",
                "control_point_details": [
                    {
                        "energy": 150.0,
                        "scan_spot_positions": [1.0, 2.0, 2.0, 2.0],
                        "scan_spot_meterset_weights": [1.0, 1.0],
                    }
                ],
                "energy_layers": [{"nominal_energy": 150.0, "mu": 3.0}],
            }
        ]
    }

    generate_plan_csvs(
        rt_plan_data,
        str(tmp_path),
        time_gain_ms=10.0,
        normalization_factor=2.0,
    )

    plan_csv = tmp_path / "plan" / "BeamPlan" / "01_150.00MeV.csv"
    rows = plan_csv.read_text(encoding="utf-8").splitlines()
    assert rows
    for row in rows:
        count_text = row.split(",")[3]
        assert count_text == str(int(count_text))
