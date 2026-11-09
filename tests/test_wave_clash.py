import sys

sys.path.insert(0, ".")

import numpy as np

from wave_clash import carriers, crosstalk_matrix, decode, encode, noise_report


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
