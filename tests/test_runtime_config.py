from pathlib import Path

import pytest

from mqi_common import config_loader


def test_load_runtime_config_returns_defaults_when_file_missing(tmp_path: Path) -> None:
    config = config_loader.load_runtime_config(str(tmp_path / "missing.yaml"))

    assert config["processing"]["dose_dividing_factor"] == 1
    assert config["processing"]["generate_log_csv"] is True
    assert config["processing"]["generate_plan_csv"] is False
    assert config["processing"]["plan_csv_normalization_factor_by_machine"] == {
        "G1": 2.1125e-8,
        "G2": 2.12e-8,
    }
    assert config["processing"]["calibration_mode"] == {
        "enabled": False,
        "use_correction_factors": True,
        "multi_energy_layer": False,
    }
    assert config["logging"] == {
        "level": "INFO",
        "show_progress": True,
    }


def test_load_runtime_config_merges_yaml_overrides(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "processing:",
                "  dose_dividing_factor: 7",
                "  generate_log_csv: false",
                "  generate_plan_csv: true",
                "  plan_csv_normalization_factor_by_machine:",
                "    G2: 5.0e-8",
                "  calibration_mode:",
                "    enabled: true",
                "logging:",
                "  level: DEBUG",
            ]
        ),
        encoding="utf-8",
    )

    config = config_loader.load_runtime_config(str(config_path))

    assert config["processing"]["dose_dividing_factor"] == 7
    assert config["processing"]["generate_log_csv"] is False
    assert config["processing"]["generate_plan_csv"] is True
    assert config["processing"]["plan_csv_normalization_factor_by_machine"] == {
        "G1": 2.1125e-8,
        "G2": 5.0e-8,
    }
    assert config["processing"]["calibration_mode"] == {
        "enabled": True,
        "use_correction_factors": True,
        "multi_energy_layer": False,
    }
    assert config["logging"] == {
        "level": "DEBUG",
        "show_progress": True,
    }
