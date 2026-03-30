from pathlib import Path

import numpy as np

from parsers.log_parser import parse_ptn_file


def test_parse_ptn_file_returns_integer_layer_and_beam_flags(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.ptn"
    raw_values = np.array(
        [
            10,
            20,
            30,
            40,
            50,
            60,
            7,
            1,
            11,
            21,
            31,
            41,
            51,
            61,
            8,
            0,
        ],
        dtype=">u2",
    )
    raw_values.tofile(file_path)

    parsed = parse_ptn_file(
        str(file_path),
        {
            "TIMEGAIN": 0.1,
            "XPOSOFFSET": 0.0,
            "YPOSOFFSET": 0.0,
            "XPOSGAIN": 1.0,
            "YPOSGAIN": 1.0,
        },
    )

    assert parsed["layer_num"].dtype == np.int32
    assert parsed["beam_on_off"].dtype == np.int32
    assert parsed["layer_num"].tolist() == [7, 8]
    assert parsed["beam_on_off"].tolist() == [1, 0]
