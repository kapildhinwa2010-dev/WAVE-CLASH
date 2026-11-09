import sys

sys.path.insert(0, ".")

import numpy as np

from wave_clash import carriers, crosstalk_matrix, decode, encode, main, noise_report


def test_roundtrip_no_noise():
    C = carriers(8)
    bits = np.array([1, 0, 1, 1, 0, 0, 1, 0])
    out = decode(encode(bits, C), C)
    assert (out == bits).all()


def test_orthogonal_no_crosstalk():
    M = crosstalk_matrix(8)
    off = M - np.diag(np.diag(M))
    assert np.abs(off).max() < 1e-9
    assert np.allclose(np.diag(M), 1.0)


def test_noise_report_shape():
    rows = noise_report(8, [0.01, 1.0], trials=20)
    assert len(rows) == 2
    for r in rows:
        assert 0.0 <= r["bit_error_rate"] <= 1.0
    assert rows[0]["bit_error_rate"] <= rows[1]["bit_error_rate"]


def test_light_noise_survives():
    rows = noise_report(8, [0.01], trials=30)
    assert rows[0]["bit_error_rate"] <= 0.01


def test_carriers_reject_non_orthogonal_dimensions():
    import pytest

    with pytest.raises(ValueError, match="cannot exceed length"):
        carriers(5, length=4)
    with pytest.raises(ValueError, match="at least 1"):
        carriers(0)


def test_noise_report_rejects_empty_trial_count_and_invalid_noise():
    import pytest

    with pytest.raises(ValueError, match="trials must be at least 1"):
        noise_report(2, [0.1], trials=0)
    with pytest.raises(ValueError, match="finite and non-negative"):
        noise_report(2, [-0.1])


def test_cli_reports_invalid_inputs_without_traceback_or_output(monkeypatch, capsys, tmp_path):
    import pytest

    output = tmp_path / "report.json"
    invalid_inputs = [
        (["--slots", "5", "--length", "4"], "cannot exceed length"),
        (["--sigmas", "not-a-number"], "could not convert string to float"),
    ]
    for args, message in invalid_inputs:
        monkeypatch.setattr(sys, "argv", ["wave_clash.py", *args, "--output", str(output)])
        with pytest.raises(SystemExit) as error:
            main()
        assert error.value.code == 2
        captured = capsys.readouterr()
        assert message in captured.err
        assert "Traceback" not in captured.err
        assert captured.out == ""
        assert not output.exists()
