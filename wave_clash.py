"""WAVE-CLASH: interference spectroscopy for a wave carrier memory.

Encode bits into orthogonal complex carriers, superpose them into one signal,
and measure what actually happens:

- crosstalk matrix: how much slot i's decoder leaks from slot j's carrier
- noise report: bit errors vs gaussian noise level (honest numbers)

Reality check baked in: perfectly orthogonal carriers do not clash, but real
lattices are not perfectly orthogonal - the noise report is where the honesty
lives.

NumPy only. No training. Bounded evaluation.
"""

__version__ = "0.1.0"

import argparse
import json

import numpy as np


def carriers(n, length=64):
    """n orthogonal complex carriers (DFT rows), shape (n, length)."""
    k = np.arange(length)
    C = np.exp(2j * np.pi * np.outer(np.arange(n), k) / length) / np.sqrt(length)
    return C


def encode(bits, C):
    """Superpose +-1 amplitudes on carriers -> single complex signal."""
    bits = np.asarray(bits)
    sig = (C.T * bits.astype(complex)).sum(axis=1)
    return sig


def decode(sig, C):
    """Correlate the signal with every carrier; return signs (bits)."""
    proj = C @ sig
    return (proj.real > 0).astype(int)


def crosstalk_matrix(n, length=64):
    """M[i, j] = |decoded slot i signal | from a unit bit in slot j."""
    C = carriers(n, length)
    M = np.zeros((n, n))
    for j in range(n):
        sig = encode([1 if k == j else 0 for k in range(n)], C)
        proj = np.abs(C @ sig)
        for i in range(n):
            M[i, j] = proj[i]
    return M


def noise_report(n, sigmas, trials=50, length=64, seed=0):
    """Bit error rate of the superposed lattice vs gaussian noise."""
    rng = np.random.default_rng(seed)
    C = carriers(n, length)
    rows = []
    for sigma in sigmas:
        errors = 0
        total = 0
        for _ in range(trials):
            bits = rng.integers(0, 2, size=n)
            sig = encode(bits, C)
            noisy = sig + rng.normal(0, sigma, size=length) + 1j * rng.normal(0, sigma, size=length)
            out = decode(noisy, C)
            errors += int((out != bits).sum())
            total += n
        rows.append({"sigma": sigma, "bit_error_rate": round(errors / max(total, 1), 4)})
    return rows


def main():
    ap = argparse.ArgumentParser(prog="wave-clash", description="Interference spectroscopy for a wave carrier memory.")
    ap.add_argument("--slots", type=int, default=8)
    ap.add_argument("--length", type=int, default=64)
    ap.add_argument("--sigmas", default="0.01,0.1,0.5,1.0")
    ap.add_argument("--output", default="wave_clash_report.json")
    a = ap.parse_args()

    n = a.slots
    M = crosstalk_matrix(n, a.length)
    off = M - np.diag(np.diag(M))
    report = {
        "slots": n,
        "carrier_length": a.length,
        "crosstalk_max_offdiagonal": float(np.abs(off).max()),
        "crosstalk_matrix": M.round(6).tolist(),
        "noise_curve": noise_report(n, [float(s) for s in a.sigmas.split(",")], length=a.length),
    }
    print(json.dumps(report, indent=2))
    with open(a.output, "w") as f:
        json.dump(report, f, indent=2)
    print("saved: " + a.output)


if __name__ == "__main__":
    main()
