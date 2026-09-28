"""
EXPERIMENT 023-EXT — MOCS extension beyond N=1023 + §5.5 hardening.

Statevector-only (0 QPU). Prereg frozen in
pt_rh_multi_observable_ext_prereg.json (MD5-pinned, verified on load).

Extension leg: the three v1 observables (alpha_vN, R(N), cv_spread(A))
on the combined 14-point sweep N_V1 + N_EXT, v1 thresholds unchanged.
Independence leg: I1 divergence witnesses (closed-form, both directions),
I2 Spearman rho_ab + effective-observables rule, I3 deterministic nulls
(diagnostic, NOT verdict-tragend — see prereg["probe_disclosure"]).
"""
import hashlib
import json
import math

import numpy as np
from scipy.linalg import eigh_tridiagonal
from scipy.stats import spearmanr

from pt_prime_state import sieve_primes, construct_P_N, measure_entropy
from pt_rh_multi_observable import (
    alpha_vN_scaling,
    latorre_ratio,
    evaluate_alpha,
    evaluate_latorre_ratio,
    evaluate_hilbert_polya,
    mocs,
)

PREREG_MD5 = "334c97545a41bdf0383c7cc35cdfbb2f"
PREREG_PATH = "pt_rh_multi_observable_ext_prereg.json"
V1_RESULTS_PATH = "pt_rh_multi_observable_results.json"

N_V1 = [7, 15, 31, 63, 127, 255, 511, 1023]
N_EXT = [2047, 4095, 8191, 16383, 32767, 65535]
N_SWEEP = N_V1 + N_EXT  # ascending, 14 points

ALPHA_MAX = 0.5          # v1 threshold, frozen
CV_BAND = (0.05, 0.20)   # v1 band, frozen
RHO_AB_MAX = 0.9         # I2 frozen claim
ALPHA_TOL = 1e-9         # witness alpha pin
REPRO_TOL = 1e-12        # v1 alpha/S/R reproduction pin

W1_COEF, W1_EXP = 1.0, 0.4
W2_COEF, W2_EXP = 0.01, 0.55


def load_frozen_prereg(path=PREREG_PATH):
    """Load the frozen prereg and verify its MD5 (abort on mismatch)."""
    with open(path, "rb") as f:
        raw = f.read()
    if hashlib.md5(raw).hexdigest() != PREREG_MD5:
        raise SystemExit(
            f"PREREG-MISMATCH: {path} md5 {hashlib.md5(raw).hexdigest()} "
            f"!= {PREREG_MD5} — freeze broken, abort."
        )
    return json.loads(raw.decode("utf-8"))


# ---------- Observable (c) solver paths ----------

def cv_spread_dense(primes):
    """cv_spread via the v1-identical dense path (eigvalsh on Jacobi A).

    The det branch of v1's hilbert_polya_proxy is skipped here: |det(A)|
    overflows for large N (documented in the v1 prereg correction_log).
    Eigen-solver and matrix construction are identical to v1.
    """
    n = len(primes)
    if n < 2:
        return 0.0
    A = np.zeros((n, n))
    for i in range(n):
        A[i, i] = primes[i]
        if i + 1 < n:
            A[i, i + 1] = abs(primes[i + 1] - primes[i])
            A[i + 1, i] = A[i, i + 1]
    eigs = np.linalg.eigvalsh(A)
    spread = eigs[-1] - eigs[0]
    if spread <= 0:
        return 0.0
    return float(np.var(eigs) / (spread ** 2))


def cv_spread_tridiag(seq):
    """cv_spread via scipy tridiagonal solver (memory-bound legs: null_a).

    The Jacobi matrix is tridiagonal (diag = values, off-diag = gaps);
    eigh_tridiagonal computes the same spectrum without materializing
    the dense matrix. Probe: dense-vs-tridiag identical at N=65535
    (0.086356402, 9 decimals).
    """
    d = np.asarray(seq, dtype=float)
    if d.size < 2:
        return 0.0
    e = np.abs(np.diff(d))
    eigs = eigh_tridiagonal(d, e, eigvals_only=True)
    spread = eigs[-1] - eigs[0]
    if spread <= 0:
        return 0.0
    return float(np.var(eigs) / (spread ** 2))


# ---------- I1: divergence witnesses (closed-form) ----------

def witness_eval(coef, exp, N_values=N_SWEEP):
    """Evaluate a closed-form witness series S(N) = coef * N**exp.

    Returns alpha (polyfit-recovered), per-point R(N), and the two
    observable verdicts the MOCS machinery assigns to the series.
    """
    S_values = [coef * float(N) ** exp for N in N_values]
    R_values = [
        latorre_ratio(S, len(sieve_primes(N)))
        for S, N in zip(S_values, N_values)
    ]
    alpha, _ = alpha_vN_scaling(N_values, S_values)
    alpha_dev = abs(alpha - exp)
    a_ok = evaluate_alpha(alpha)
    b_ok = evaluate_latorre_ratio(R_values)
    return {
        "formula": f"S(N) = {coef} * N^{exp}",
        "alpha": alpha,
        "alpha_dev_from_exponent": alpha_dev,
        "alpha_within_tol": alpha_dev <= ALPHA_TOL,
        "R_values": R_values,
        "R_min": min(R_values),
        "R_max": max(R_values),
        "a_consistent": bool(a_ok),
        "b_consistent": bool(b_ok),
    }


# ---------- I2: rank dependence + effective observables ----------

def effective_observables(rho_ab):
    """§5.5 effective-independence rule (frozen in prereg I2).

    effective_ab = 1 + max(0, 1 - |rho_ab|); observable (c) shares no
    variable with (a)/(b), so it contributes a full 1.
    """
    effective_ab = 1.0 + max(0.0, 1.0 - abs(rho_ab))
    return effective_ab, effective_ab + 1.0


# ---------- I3: deterministic nulls (diagnostic) ----------

def null_sequences(N):
    """null_a: odd integers <= N (uniform density); null_b: powers of two <= N."""
    null_a = list(range(3, N + 1, 2))
    k_max = int(math.log2(N))
    null_b = [2 ** k for k in range(1, k_max + 1)]
    return null_a, null_b


# ---------- Main measurement ----------

def measure_all():
    """Run the frozen extension + independence measurement."""
    prereg = load_frozen_prereg()
    assert prereg["n_values_v1"] == N_V1
    assert prereg["n_values_ext"] == N_EXT

    rows = []
    S_values = []
    R_values = []
    cv_values = []

    for N in N_SWEEP:
        primes = sieve_primes(N)
        pi_N = len(primes)
        P_N, dim, n_qubits = construct_P_N(N)
        S_vN, S_max, n_A, n_B = measure_entropy(P_N)

        R_N = latorre_ratio(S_vN, pi_N)
        cv_N = cv_spread_dense(primes)

        S_values.append(float(S_vN))
        R_values.append(float(R_N))
        cv_values.append(float(cv_N))
        rows.append({
            "N": N,
            "pi_N": pi_N,
            "dim": dim,
            "n_qubits": n_qubits,
            "leg": "v1" if N in N_V1 else "ext",
            "S_vN": float(S_vN),
            "S_max": float(S_max),
            "R_N": float(R_N),
            "cv_spread_A": float(cv_N),
        })

    alpha_combined, log_const = alpha_vN_scaling(N_SWEEP, S_values)
    alpha_v1, _ = alpha_vN_scaling(N_V1, S_values[:len(N_V1)])
    alpha_ext, _ = alpha_vN_scaling(N_EXT, S_values[len(N_V1):])
    cv_mean = float(np.mean(cv_values))
    cv_range = [float(min(cv_values)), float(max(cv_values))]

    # v1 reproduction pin (committed v1 artifact)
    with open(V1_RESULTS_PATH) as f:
        v1 = json.load(f)
    v1_by_N = {r["N"]: r for r in v1["rows"]}
    repro = {
        "alpha_v1_recomputed": float(alpha_v1),
        "alpha_v1_committed": float(v1["alpha_vN"]),
        "alpha_dev": float(abs(alpha_v1 - v1["alpha_vN"])),
        "max_S_dev": float(max(
            abs(rows[i]["S_vN"] - v1_by_N[N]["S_vN"])
            for i, N in enumerate(N_V1)
        )),
        "max_R_dev": float(max(
            abs(rows[i]["R_N"] - v1_by_N[N]["R_N"])
            for i, N in enumerate(N_V1)
        )),
        "max_cv_dev": float(max(
            abs(cv_values[i] - v1_by_N[N]["cv_spread_A"])
            for i, N in enumerate(N_V1)
        )),
        "alpha_ok": bool(abs(alpha_v1 - v1["alpha_vN"]) <= REPRO_TOL),
        "S_R_ok": True,
        "cv_bitexact": True,
    }
    repro["S_R_ok"] = bool(
        repro["max_S_dev"] <= REPRO_TOL and repro["max_R_dev"] <= REPRO_TOL
    )
    repro["cv_bitexact"] = bool(repro["max_cv_dev"] == 0.0)
    repro["ok"] = bool(
        repro["alpha_dev"] <= REPRO_TOL
        and repro["S_R_ok"]
        and repro["cv_bitexact"]
    )

    # verdicts on the combined 14-point sweep (v1 thresholds unchanged)
    verdicts = {
        "observable_a_alpha_rh_consistent": bool(evaluate_alpha(alpha_combined)),
        "observable_b_R_rh_consistent": bool(evaluate_latorre_ratio(R_values)),
        "observable_c_cv_rh_consistent": bool(evaluate_hilbert_polya(cv_mean)),
    }
    score = mocs(alpha_combined, R_values, cv_mean)

    # I1 witnesses
    w1 = witness_eval(W1_COEF, W1_EXP)
    w2 = witness_eval(W2_COEF, W2_EXP)
    w1["expected_a_consistent"] = True
    w1["expected_b_consistent"] = False
    w2["expected_a_consistent"] = False
    w2["expected_b_consistent"] = True
    w1["divergent"] = w1["a_consistent"] and not w1["b_consistent"]
    w2["divergent"] = (not w2["a_consistent"]) and w2["b_consistent"]
    w1["matches_expected"] = (
        w1["divergent"]
        and w1["a_consistent"] == w1["expected_a_consistent"]
        and w1["b_consistent"] == w1["expected_b_consistent"]
        and w1["alpha_within_tol"]
    )
    w2["matches_expected"] = (
        w2["divergent"]
        and w2["a_consistent"] == w2["expected_a_consistent"]
        and w2["b_consistent"] == w2["expected_b_consistent"]
        and w2["alpha_within_tol"]
    )

    # I2 rank dependence
    log_S = np.log(np.asarray(S_values))
    log_R = np.log(np.asarray(R_values))
    rho_ab, _ = spearmanr(log_S, log_R)
    rho_ab = float(rho_ab)
    effective_ab, effective_total = effective_observables(rho_ab)

    # I3 nulls (diagnostic)
    nulls = []
    for N in N_SWEEP:
        null_a, null_b = null_sequences(N)
        cv_a = cv_spread_tridiag(null_a)
        cv_b = cv_spread_tridiag(null_b)
        cv_p = cv_values[N_SWEEP.index(N)]
        nulls.append({
            "N": N,
            "cv_primes": cv_p,
            "cv_null_a_odd": cv_a,
            "cv_null_b_pow2": cv_b,
            "delta_a": cv_p - cv_a,
            "delta_b": cv_p - cv_b,
            "in_band_primes": CV_BAND[0] <= cv_p <= CV_BAND[1],
            "in_band_null_a": CV_BAND[0] <= cv_a <= CV_BAND[1],
            "in_band_null_b": CV_BAND[0] <= cv_b <= CV_BAND[1],
        })

    claims = {
        "H_MOCS_EXT_holds": score >= 2,
        "H_WITNESSES_hold": w1["matches_expected"] and w2["matches_expected"],
        "H_INDEP_holds": abs(rho_ab) < RHO_AB_MAX and effective_total >= 2.0,
        "H_REPRO_holds": repro["ok"],
    }

    return {
        "prereg_md5": PREREG_MD5,
        "n_sweep": N_SWEEP,
        "rows": rows,
        "alpha_combined": alpha_combined,
        "alpha_v1_8pt": alpha_v1,
        "alpha_ext_6pt": alpha_ext,
        "log_const": log_const,
        "cv_spread_mean": cv_mean,
        "cv_spread_range": cv_range,
        "mocs_ext": score,
        "verdicts": verdicts,
        "v1_reproduction": repro,
        "witnesses": {"w1": w1, "w2": w2},
        "rho_ab": rho_ab,
        "effective_ab": effective_ab,
        "effective_total": effective_total,
        "nulls": nulls,
        "claims": claims,
        "h_MOCS_EXT_rejected": score < 2,
    }


def write_outputs(result):
    """Write JSON results + plain-text log (no prereg modification)."""
    out_json = "pt_rh_multi_observable_ext_results.json"
    with open(out_json, "w") as f:
        json.dump(result, f, indent=2)

    log_path = "pt_rh_multi_observable_ext_log.txt"
    with open(log_path, "w") as f:
        f.write("EXPERIMENT 023-EXT — MOCS extension + §5.5 hardening\n")
        f.write(f"prereg_md5 = {result['prereg_md5']}\n")
        f.write(f"alpha_combined = {result['alpha_combined']:.6f}\n")
        f.write(f"alpha_v1_8pt  = {result['alpha_v1_8pt']:.6f}\n")
        f.write(f"alpha_ext_6pt = {result['alpha_ext_6pt']:.6f}\n")
        f.write(f"cv_spread_mean = {result['cv_spread_mean']:.6f}\n")
        f.write(f"cv_spread_range = {result['cv_spread_range']}\n")
        f.write(f"MOCS_ext = {result['mocs_ext']}\n")
        for k, v in result["verdicts"].items():
            f.write(f"  {k}: {v}\n")
        f.write(f"v1_reproduction_ok = {result['v1_reproduction']['ok']}\n")
        f.write(f"w1_divergent = {result['witnesses']['w1']['divergent']}\n")
        f.write(f"w2_divergent = {result['witnesses']['w2']['divergent']}\n")
        f.write(f"rho_ab = {result['rho_ab']:.6f}\n")
        f.write(f"effective_total = {result['effective_total']:.6f}\n")
        for k, v in result["claims"].items():
            f.write(f"  {k}: {v}\n")


def main():
    result = measure_all()
    write_outputs(result)

    print("N, pi(N), leg, S_vN, R(N), cv_spread(A)")
    for row in result["rows"]:
        print(f"  N={row['N']:6d}, pi={row['pi_N']:5d}, {row['leg']}, "
              f"S={row['S_vN']:.4f}, R={row['R_N']:.4f}, "
              f"cv={row['cv_spread_A']:.4f}")

    print(f"\nalpha_combined = {result['alpha_combined']:.6f}")
    print(f"alpha_v1_8pt   = {result['alpha_v1_8pt']:.6f} "
          f"(pin dev {result['v1_reproduction']['alpha_dev']:.2e})")
    print(f"alpha_ext_6pt  = {result['alpha_ext_6pt']:.6f}")
    print(f"MOCS_ext = {result['mocs_ext']}")
    print(f"rho_ab = {result['rho_ab']:.6f}, "
          f"effective_total = {result['effective_total']:.6f}")
    print(f"w1 divergent = {result['witnesses']['w1']['divergent']}, "
          f"w2 divergent = {result['witnesses']['w2']['divergent']}")
    print(f"h_MOCS_EXT_rejected = {result['h_MOCS_EXT_rejected']}")
    for k, v in result["claims"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()