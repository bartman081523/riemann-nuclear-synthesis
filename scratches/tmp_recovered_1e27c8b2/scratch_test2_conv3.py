# -*- coding: utf-8 -*-
"""Pre-Freeze-Check 3 EXPERIMENT 049: vollstaendige Zeilen-De-Kodierung + frische
einheitliche Achsenreihe + frischer alpha-Fit vs. committet (Einheits-Fallstrick).
"""
import sys
sys.path.insert(0, "/run/media/julian/ML4/riemann")
import json
import math

import numpy as np

LN2 = math.log(2.0)


def sieve(n):
    is_p = bytearray([1]) * (n + 1)
    is_p[0:2] = b"\x00\x00"
    for i in range(2, int(n ** 0.5) + 1):
        if is_p[i]:
            is_p[i * i:: i] = bytearray(len(is_p[i * i:: i]))
    return [i for i in range(2, n + 1) if is_p[i]]


def svd_s_sq(psi, d_A, d_B, order):
    A = psi.reshape(d_A, d_B, order=order)
    s = np.linalg.svd(A, compute_uv=False)
    return s ** 2


def s_nats(lam, floor_abs=None):
    lam = np.asarray(lam, float)
    if floor_abs is not None:
        lam = lam[lam > floor_abs]
    else:
        lam = lam[lam > 0]
    return float(-(lam * np.log(lam)).sum())


def s_bits(lam):
    lam = np.asarray(lam, float)
    lam = lam[lam > 0]
    return float(-np.sum(lam * np.log2(lam)))


PRIMES_CACHE = {}
def primes_upto(N):
    if N not in PRIMES_CACHE:
        PRIMES_CACHE[N] = [p for p in sieve(N)]
    return PRIMES_CACHE[N]


def fresh_psi(N):
    n_qubits = int(math.ceil(math.log2(N + 1)))
    primes = [p for p in primes_upto(N) if p < 2 ** n_qubits]
    assert len(primes) == len(primes_upto(N))
    psi = np.zeros(2 ** n_qubits)
    psi[primes] = 1.0
    psi /= np.linalg.norm(psi)
    return psi, n_qubits, len(primes)


def axis_series(N):
    """AXIS-Konvention: reshape((2^floor, 2^ceil), order='F') + log2."""
    psi, n_q, pi_N = fresh_psi(N)
    n_A = n_q // 2
    lam = svd_s_sq(psi, 2 ** n_A, 2 ** (n_q - n_A), "F")
    return lam, s_bits(lam), n_q, pi_N


# ---------- GATE-B je Zeile in der Eigenkonvention -------------------------
print("=== GATE-B-Checks je Quelle (Zeilen-Konvention) ===")
with open("/run/media/julian/ML4/riemann/pt_prime_state_qpu_singleshot_results.json") as fh:
    singleshot = json.load(fh)["results"]
for row in singleshot:
    N = row["N"]
    psi, n_q, pi_N = fresh_psi(N)
    d_A_dim = row["n_A"]              # als DIMENSION
    d_B_dim = row["n_B"]
    assert d_A_dim * d_B_dim == 2 ** n_q
    lam = svd_s_sq(psi, d_A_dim, d_B_dim, "C")
    S = s_nats(lam, floor_abs=1e-12)  # pt_prime_state: Filter > 1e-12 ABS
    d = abs(S - row["S_vN_classical"])
    lam_comm = np.sort(np.asarray(row["s_sq_classical"], float))[::-1]
    lam_f = np.sort(lam)[::-1]
    m = min(len(lam_comm), len(lam_f))
    dl = float(np.max(np.abs((lam_f[:m] - lam_comm[:m]) / lam_comm[:m]))) if m else 0.0
    print("single N=%-6d S_fresh=%.16f comm=%.16f d=%.2e | lam_d=%.2e | %s"
          % (N, S, row["S_vN_classical"], d, dl, "OK" if d <= 1e-10 and dl <= 1e-8 else "FAIL"))

with open("/run/media/julian/ML4/riemann/pt_prime_state_N255_results.json") as fh:
    n255 = json.load(fh)["new_data_points"]
for row in n255:
    N = row["N"]
    psi, n_q, pi_N = fresh_psi(N)
    n_A = row["n_A"]                  # als COUNT
    lam = svd_s_sq(psi, 2 ** n_A, 2 ** (n_q - n_A), "F")
    S_bits = s_bits(lam)
    d = abs(S_bits - row["S_vN"])
    lam_comm = np.sort(np.asarray(row["s_sq"], float))[::-1]
    lam_f = np.sort(lam)[::-1]
    m = min(len(lam_comm), len(lam_f))
    dl = float(np.max(np.abs((lam_f[:m] - lam_comm[:m]) / lam_comm[:m]))) if m else 0.0
    print("N255  N=%-6d S_fresh=%.16f comm=%.16f d=%.2e | lam_d=%.2e | %s"
          % (N, S_bits, row["S_vN"], d, dl, "OK" if d <= 1e-10 and dl <= 1e-8 else "FAIL"))

with open("/run/media/julian/ML4/riemann/pt_asymptotic_N1e6_results.json") as fh:
    n1e6 = json.load(fh)["new_data_points"]
for row in n1e6:
    N = row["N"]
    psi, n_q, pi_N = fresh_psi(N)
    n_A = row["n_A"]                  # als COUNT, floor(n/2)
    lam = svd_s_sq(psi, 2 ** n_A, 2 ** (n_q - n_A), "F")
    S_bits = s_bits(lam)
    d = abs(S_bits - row["S_vN"])
    print("N1e6  N=<%-8d S_fresh=%.16f comm=%.16f d=%.2e | %s"
          % (N, S_bits, row["S_vN"], d, "OK" if d <= 1e-10 else "FAIL"))

# ---------- frische einheitliche Achsenreihe + alpha-Fit -------------------
print("")
print("=== Frische ACHSENREIHE (bits, floor-F, uniform-prime) ===")
GRID = [7, 15, 31, 63, 127, 255, 511, 1023, 10000, 100000, 1000000]
rows = []
for N in GRID:
    lam, S, n_q, pi_N = axis_series(N)
    rows.append({"N": N, "n_q": n_q, "pi_N": pi_N, "S_bits": S,
                 "n_nonzero": int(np.sum(lam > 0))})
    print("N=%-8d n=%2d pi=%-6d S_bits=%.16f nnz=%d"
          % (N, n_q, pi_N, S, int(np.sum(lam > 0))))

lnN = np.log(np.array([r["N"] for r in rows], float))
lnS = np.log(np.array([r["S_bits"] for r in rows], float))
p = np.polyfit(lnN, lnS, 1)
print("frischer alpha-Fit (bits, 11 Punkte): %.16f   (committet gemischt: 0.22275345050922138)"
      % p[0])
print("inkrementell (bits, konsistent):")
for i in range(2, len(rows)):
    pp = np.polyfit(np.log(np.array([r["N"] for r in rows[: i + 1]], float)),
                    np.log(np.array([r["S_bits"] for r in rows[: i + 1]], float)), 1)
    print("  N_max=%-8d alpha=%.4f" % (rows[i]["N"], pp[0]))

# ---------- frische Reihe in NATS (Vergleich) ------------------------------
print("")
print("=== Frische Reihe NATS (nur Referenz) ===")
for N in GRID:
    lam, S, n_q, pi_N = axis_series(N)
    print("N=%-8d S_nats=%.16f" % (N, float(-(np.sort(lam)[::-1][np.sort(lam)[::-1] > 0]
                                            * np.log(np.sort(lam)[::-1][np.sort(lam)[::-1] > 0])).sum())))