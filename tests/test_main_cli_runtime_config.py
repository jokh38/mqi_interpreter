from pathlib import Path

import main_cli


def test_main_uses_configured_dose_dividing_factor(
    monkeypatch, tmp_path: Path
) -> None:
    logdir = tmp_path / "logs"
    outputdir = tmp_path / "output"
    logdir.mkdir()
    (logdir / "sample.ptn").write_bytes(b"\x00" * 16)
    (logdir / "sample_RTPLAN.dcm").write_bytes(b"DICOM")

    captured = {}

    monkeypatch.setattr(
        "sys.argv",
        ["main_cli.py", "--logdir", str(logdir), "--outputdir", str(outputdir)],
    )
    monkeypatch.setattr(main_cli.dicom_parser, "parse_rtplan", lambda path: {
        "patient_id": "55061194",
        "beams": [
            {
                "beam_name": "BeamA",
                "beam_number": 1,
                "treatment_machine_name": "G1",
                "energy_layers": [{"nominal_energy": 150.0}],
            }
        ],
    })
    monkeypatch.setattr(
        main_cli.config_loader, "load_runtime_config", lambda config_path=None: {
            "processing": {
                "dose_dividing_factor": 7,
                "calibration_mode": {
                    "enabled": False,
                    "use_correction_factors": True,
                    "multi_energy_layer": False,
                },
            },
            "logging": {"level": "INFO", "show_progress": True},
        }
    )
    monkeypatch.setattr(
        main_cli.config_loader, "parse_scv_init", lambda path: {"TIMEGAIN": 1.0}
    )
    monkeypatch.setattr(
        main_cli.config_loader,
        "parse_planrange_files",
        lambda path: {"2025042401440800": [2]},
    )
    monkeypatch.setattr(
        main_cli.config_loader,
        "parse_planinfo_files",
        lambda path: {
            "2025042401440800": {
                "DICOM_PATIENT_ID": "55061194",
                "DICOM_BEAM_NUMBER": 1,
                "TCSC_FIELD_NUMBER": 1,
                "STOP_LAYER_NUMBER": 1,
            }
        },
    )
    monkeypatch.setattr(
        main_cli.log_parser,
        "parse_ptn_file",
        lambda path, scv_init: {
            "dose1_au": [10],
            "time_ms": [0.0],
            "x_mm": [1.0],
            "y_mm": [2.0],
        },
    )
    monkeypatch.setattr(
        main_cli.aperture_generator,
        "extract_and_generate_aperture_data_g1",
        lambda ds, rt_plan_data, output_base_dir: [],
    )

    def capture_generate_moqui_csvs(
        rt_plan_data, ptn_data_list, dose_monitor_ranges, output_base_dir, dose_dividing_factor=10
    ):
        captured["dose_dividing_factor"] = dose_dividing_factor

    monkeypatch.setattr(
        main_cli.moqui_generator, "generate_moqui_csvs", capture_generate_moqui_csvs
    )

    main_cli.main()

    assert captured["dose_dividing_factor"] == 7
