"""
EXPERIMENT 023 — Multi-Observable RH Convergence Measurement.

Three independent RH-related observables measured on the same
prime-state family |P_N> for N in {7, 15, 31, 63, 127, 255, 511, 1023}.

  (a) Schmidt-entropy scaling exponent alpha_vN(N)
        - Latorre prediction: alpha -> 1 (linear in log pi(N))
        - RH-consistent if: alpha < 0.5

  (b) Latorre-ratio R(N) = S_vN(P_N) / log pi(N)
        - Latorre prediction: R(N) -> 1 as N -> infinity (if RH true)
        - RH-consistent if: R(N) < 1 for all measured N (sub-logarithmic)

  (c) Hilbert-Pólya proxy: |det(A)| for the Jacobi matrix A
        encoding prime-index differences
        - Hilbert-Pólya conjecture (unproven): if RH true, A is
          self-adjoint with real spectrum
        - RH-consistent if: |det(A)| > 0 and real

The Multi-Observable Convergence Score (MOCS) is the count of
RH-consistent observables. H_MOCS: MOCS >= 2 (falsifiable).

Statevector-only (no QPU). Pre-registered in
pt_rh_multi_observable_prereg.json (MD5-pinned).
"""
import json
import math
import hashlib
import os

import numpy as np

from pt_prime_state import sieve_primes, construct_P_N, measure_entropy

N_SWEEP = [7, 15, 31, 63, 127, 255, 511, 1023]


# ---------- Observable (a): Schmidt-entropy scaling alpha_vN ----------

def alpha_vN_scaling(N_values, S_values):
    """Compute the log-log scaling exponent alpha_vN.

    log(S) ~ alpha * log(N) + const  =>  polyfit(log N, log S)
    """
    log_N = np.log(np.asarray(N_values, dtype=float))
    log_S = np.log(np.asarray(S_values, dtype=float))
    alpha, log_const = np.polyfit(log_N, log_S, 1)
    return float(alpha), float(log_const)


# ---------- Observable (b): Latorre-ratio R(N) ----------

def latorre_ratio(S_vN, pi_N):
    """R(N) = S_vN(P_N) / log pi(N).

    Latorre-Sierra prediction: if RH true, S_vN(P_N) ~ log pi(N),
    so R(N) -> 1 as N -> infinity.
    Sub-RH regime: S_vN << log pi(N) -> R(N) < 1.
    """
    if pi_N <= 1:
        return float("inf")
    return float(S_vN) / float(math.log(pi_N))


# ---------- Observable (c): Hilbert-Pólya proxy via Jacobi matrix A ----------

def jacobi_matrix_for_primes(primes):
    """Build the tridiagonal Jacobi matrix A encoding prime-index differences.

    Off-diagonal entries: |p_{k+1} - p_k| (prime-index difference magnitude).
    Diagonal entries:    p_k (the prime itself, as a 'center of mass').

    This is a heuristic Hilbert-Pólya-style construction: the actual
    Hilbert-Pólya conjecture claims the existence of a self-adjoint
    operator whose spectrum is the imaginary parts of the non-trivial
    zeta zeros. Our A is a proxy, not the conjectured operator.
    """
    n = len(primes)
    if n < 2:
        return np.array([[float(primes[0])]]) if n == 1 else np.array([[]])
    A = np.zeros((n, n))
    for i in range(n):
        A[i, i] = primes[i]
        if i + 1 < n:
            A[i, i + 1] = abs(primes[i + 1] - primes[i])
            A[i + 1, i] = A[i, i + 1]
    return A


def hilbert_polya_proxy(primes):
    """|det(A)| and Im(det(A)) for the Jacobi matrix A.

    RH-consistent: |det(A)| > 0 and det(A) is real (no imaginary part
    arising from the spectrum having complex eigenvalues).
    """
    A = jacobi_matrix_for_primes(primes)
    if A.size == 0:
        return 0.0, 0.0
    det = np.linalg.det(A)
    return float(np.abs(det)), float(np.imag(det))


# ---------- RH-consistency evaluation per observable ----------

def evaluate_alpha(alpha):
    """Observable (a): RH-consistent if alpha < 0.5."""
    return alpha < 0.5


def evaluate_latorre_ratio(R_values):
    """Observable (b): RH-consistent if R(N) < 1 for all measured N."""
    return all(r < 1.0 for r in R_values)


def evaluate_hilbert_polya(abs_det, imag_det, tol=1e-9):
    """Observable (c): RH-consistent if |det| > 0 and imag(det) ~ 0."""
    return abs_det > tol and abs(imag_det) < tol


# ---------- Multi-Observable Convergence Score ----------

def mocs(alpha, R_values, abs_det, imag_det):
    """MOCS = #{a, b, c} : observable is RH-consistent."""
    return sum([
        evaluate_alpha(alpha),
        evaluate_latorre_ratio(R_values),
        evaluate_hilbert_polya(abs_det, imag_det),
    ])


# ---------- Main measurement loop ----------

def measure_all():
    """Run the full Multi-Observable Convergence measurement."""
    rows = []
    S_values = []
    R_values = []
    abs_det_values = []
    imag_det_values = []

    for N in N_SWEEP:
        primes = sieve_primes(N)
        pi_N = len(primes)
        P_N, dim, n_qubits = construct_P_N(N)
        S_vN, S_max, n_A, n_B = measure_entropy(P_N)

        R_N = latorre_ratio(S_vN, pi_N)
        abs_det, imag_det = hilbert_polya_proxy(primes)

        S_values.append(S_vN)
        R_values.append(R_N)
        abs_det_values.append(abs_det)
        imag_det_values.append(imag_det)

        rows.append({
            "N": N,
            "pi_N": pi_N,
            "dim": dim,
            "n_qubits": n_qubits,
            "S_vN": S_vN,
            "S_max": S_max,
            "S_normalized": S_vN / S_max if S_max > 0 else 0.0,
            "R_N": R_N,
            "abs_det_A": abs_det,
            "imag_det_A": imag_det,
        })

    alpha, log_const = alpha_vN_scaling(N_SWEEP, S_values)
    score = mocs(alpha, R_values, abs_det_values[-1], imag_det_values[-1])

    return {
        "N_sweep": N_SWEEP,
        "rows": rows,
        "alpha_vN": alpha,
        "log_const": log_const,
        "mocs": score,
        "verdicts": {
            "observable_a_alpha_rh_consistent": bool(evaluate_alpha(alpha)),
            "observable_b_R_rh_consistent": bool(evaluate_latorre_ratio(R_values)),
            "observable_c_det_rh_consistent": bool(
                evaluate_hilbert_polya(abs_det_values[-1], imag_det_values[-1])
            ),
        },
        "h_MOCS_rejected": score < 2,
    }


def write_outputs(result):
    """Write JSON results + plain-text log (no prereg modification)."""
    out_json = "pt_rh_multi_observable_results.json"
    with open(out_json, "w") as f:
        json.dump(result, f, indent=2)

    log_path = "pt_rh_multi_observable_log.txt"
    with open(log_path, "w") as f:
        f.write("Multi-Observable RH Convergence Measurement\n")
        f.write(f"alpha_vN = {result['alpha_vN']:.4f}\n")
        f.write(f"MOCS = {result['mocs']}\n")
        for k, v in result["verdicts"].items():
            f.write(f"  {k}: {v}\n")
        f.write(f"h_MOCS_rejected = {result['h_MOCS_rejected']}\n")


def main():
    result = measure_all()
    write_outputs(result)

    print("N, pi(N), S_vN, R(N), |det A|")
    for row in result["rows"]:
        print(f"  N={row['N']:4d}, pi={row['pi_N']:3d}, "
              f"S={row['S_vN']:.4f}, R={row['R_N']:.4f}, "
              f"|det|={row['abs_det_A']:.4e}")

    print(f"\nalpha_vN = {result['alpha_vN']:.4f}")
    print(f"MOCS = {result['mocs']}")
    print(f"h_MOCS_rejected = {result['h_MOCS_rejected']}")


if __name__ == "__main__":
    main()