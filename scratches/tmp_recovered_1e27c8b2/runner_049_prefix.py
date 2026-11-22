#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EXPERIMENT 049 — H-TEST2 Test 2 (Kausal-Glied): Mitwanderung Verschraenkung <-> Robustheit.

Gefroren unter pt_test2_entanglement_comovement_prereg.json (md5-Assert am Dateianfang).
0 QPU, 0 Aer — numpy-only. Fortsetzung der 048/048b-Kette (Branch h-test1-gap-invariance).

Verdict-Regel (gefroren): Spearman rho( Gamma_K3_q95(delta=0.01)(N), S_vN_axis(N) )
ueber VALID Gitterpunkte gegen 1000er-Shuffle-Null (q95 der |rho_null|).
KAUSALGLIED_GEFALLEN | MITWANDERUNG_POSITIV (Leg A) | MITWANDERUNG_NEGATIV (Leg B) | DEGENERAT.
Diagnostik (Konfund-Kit, Blend, Sekundaer-Kanaele) NICHT verdict-tragend.
"""
import hashlib
import json
import math
import sys
import time

import numpy as np

PREREG_PATH = "pt_test2_entanglement_comovement_prereg.json"
RESULTS_PATH = "pt_test2_entanglement_comovement_results.json"
FROZEN_PREREG_MD5 = "857168030a2d16df1f9d9a0cd97a4124"

# ----------------------------------------------------------- gefrorene Konstanten
GATE_A_TOL = 1e-12           # Gamma_K1 <= ...
GATE_B_S_TOL = 1e-10         # |S_frisch - S_committet| je Zeile
GATE_B_LAM_TOL = 1e-8        # rel lam-Abweichung auf gemeinsamem Traeger
SINGLESHOT_ABS_CUTOFF = 1e-12  # pt_prime_state.py-Filter ABS
LAM_CARRIER = 1e-30            # Traeger-Regel (pristine, tilde, GATE-B-Mask)
GAP_FLOOR_REL = 1e-6           # VALID: min(g_k, g_{k+1}) >= 1e-6 * lam_max
SHUFFLE_SEED = 20261005
SHUFFLE_N = 1000
BLEND_N = 1024
BLEND_THETAS = [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]
GATE_D_TOL = 1e-12

with open(PREREG_PATH, "rb") as fh:
    _md5 = hashlib.md5(fh.read()).hexdigest()
if _md5 != FROZEN_PREREG_MD5:
    print("ABBRUCH: Prereg-md5 %s != gefroren %s" % (_md5, FROZEN_PREREG_MD5))
    sys.exit(2)
with open(PREREG_PATH) as fh:
    PREREG = json.load(fh)

ROWS = PREREG["data_basis"]["rows"]
GRID = [r["N"] for r in ROWS]
AXIS_FROZEN = {r["N"]: float(r["axis_S_bits_frisch"]) for r in ROWS}

# --------------------------------------------------------------- Sieve / Zustand
_PRIMES = {}


def primes_upto(N):
    if N not in _PRIMES:
        is_p = bytearray([1]) * (N + 1)
        is_p[0:2] = b"\x00\x00"
        for i in range(2, int(N ** 0.5) + 1):
            if is_p[i]:
                is_p[i * i:: i] = bytearray(len(is_p[i * i:: i]))
        _PRIMES[N] = [i for i in range(2, N + 1) if is_p[i]]
    return _PRIMES[N]


def fresh_psi(N):
    """Uniform-prime Statevector, REAL float64 (gefroren: Zustandsfamilie reell)."""
    n_qubits = int(math.ceil(math.log2(N + 1)))
    primes = primes_upto(N)
    assert max(primes) < 2 ** n_qubits
    psi = np.zeros(2 ** n_qubits)
    psi[primes] = 1.0
    psi /= np.linalg.norm(psi)
    return psi, n_qubits, len(primes)


def svd_lam(psi, d_A, d_B, order):
    A = psi.reshape(d_A, d_B, order=order)
    s = np.linalg.svd(A, compute_uv=False)
    return s ** 2


def carrier_lam(psi, n_qubits):
    """AXIS: reshape((2^floor, 2^ceil), order='F'), Traeger lam > 1e-30, absteigend."""
    n_A = n_qubits // 2
    lam = svd_lam(psi, 2 ** n_A, 2 ** (n_qubits - n_A), "F")
    lam = np.sort(lam)[::-1]
    return lam[lam > LAM_CARRIER]


def s_nats_cutoff(lam):
    lam = np.asarray(lam, float)
    lam = lam[lam > SINGLESHOT_ABS_CUTOFF]
    return float(-(lam * np.log(lam)).sum())


def s_bits(lam):
    lam = np.asarray(lam, float)
    lam = lam[lam > 0]
    return float(-np.sum(lam * np.log2(lam)))


def lam_rel_diff(lam_fresh, lam_comm, floor_both):
    """Rel-Abweichung auf dem gemeinsamen Traeger; None wenn keine gemeinsamen."""
    a = np.sort(np.asarray(lam_fresh, float))[::-1]
    b = np.sort(np.asarray(lam_comm, float))[::-1]
    m = min(len(a), len(b))
    a, b = a[:m], b[:m]
    mask = (a > floor_both) & (b > floor_both)
    if not np.any(mask):
        return None
    return float(np.max(np.abs((a[mask] - b[mask]) / b[mask])))


def ratios_and_valid(lam):
    """r_k = g_k/g_{k+1}, g_k = lam_k - lam_{k+1}; ok: min(g_k, g_{k+1}) >= 1e-6*lam_max."""
    g = lam[:-1] - lam[1:]
    r = g[:-1] / g[1:]
    ok = np.minimum(g[:-1], g[1:]) >= GAP_FLOOR_REL * lam[0]
    return r, ok


def gamma_for_amp(psi, n_qubits, delta, shape_vals, lam_p, r_p, ok_p, idx=None):
    """Ein Draw: amp = 1 + delta*shape an den Positions-Indizes idx (Default:
    Traeger von psi) -> tilde-Lambda -> Ratios an sorted-Position k ueber
    min-Laenge, Gamma_MAX ueber VALID k (Basis-Maske ok_p)."""
    if idx is None:
        idx = np.nonzero(psi)[0]
    amp_full = np.ones(psi.shape[0])
    amp_full[idx] = 1.0 + delta * shape_vals
    psi_t = psi * amp_full
    psi_t = psi_t / np.linalg.norm(psi_t)
    lam_t = carrier_lam(psi_t, n_qubits)
    m = min(len(r_p), len(lam_t) - 2)
    if m <= 0:
        return None, len(lam_t)
    g_t = lam_t[:-1] - lam_t[1:]
    r_t = g_t[:-1] / g_t[1:]
    ok_c = ok_p[:m]
    if not np.any(ok_c):
        return None, len(lam_t)
    rel = np.abs((r_t[:m] - r_p[:m]) / r_p[:m])[ok_c]
    return float(np.max(rel)), len(lam_t)


def q95(x):
    return float(np.quantile(np.asarray(x, float), 0.95))


def avg_ranks(x):
    """Average-Tie-Ranks, numpy-only."""
    x = np.asarray(x, float)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x))
    sx = x[order]
    i = 0
    while i < len(sx):
        j = i
        while j + 1 < len(sx) and sx[j + 1] == sx[i]:
            j += 1
        ranks[order[i: j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return ranks


def spearman(x, y):
    return float(np.corrcoef(avg_ranks(x), avg_ranks(y))[0, 1])


# --------------------------------------------------------------- Hauptlauf
def main():
    t0 = time.time()
    results = {"experiment": "049", "hypothesis": "H-TEST2",
               "prereg_md5": FROZEN_PREREG_MD5,
               "axis_convention": ("floor(n//2)-LSB-Split, order-F, bits, "
                                   "Traeger >1e-30, REAL float64")}

    # ---------------- GATE-B: De-Kodierung je Zeile in der Eigenkonvention
    gate_b = []
    with open("pt_prime_state_qpu_singleshot_results.json") as fh:
        single = json.load(fh)["results"]
    with open("pt_prime_state_N255_results.json") as fh:
        n255 = json.load(fh)["new_data_points"]
    with open("pt_asymptotic_N1e6_results.json") as fh:
        n1e6 = json.load(fh)["new_data_points"]

    for row in single:
        N = row["N"]
        psi, n_q, pi_N = fresh_psi(N)
        lam = svd_lam(psi, row["n_A"], row["n_B"], "C")
        S = s_nats_cutoff(lam)
        dS = abs(S - row["S_vN_classical"])
        dl = lam_rel_diff(lam, row["s_sq_classical"], floor_both=SINGLESHOT_ABS_CUTOFF)
        gate_b.append({"N": N, "src": "singleshot", "dS": dS, "dlam": dl,
                       "ok": bool(dS <= GATE_B_S_TOL and (dl is None or dl <= GATE_B_LAM_TOL))})
    for row in n255:
        N = row["N"]
        psi, n_q, pi_N = fresh_psi(N)
        lam = svd_lam(psi, 2 ** row["n_A"], 2 ** (n_q - row["n_A"]), "F")
        dS = abs(s_bits(lam) - row["S_vN"])
        dl = lam_rel_diff(lam, row["s_sq"], floor_both=LAM_CARRIER)
        gate_b.append({"N": N, "src": "N255", "dS": dS, "dlam": dl,
                       "ok": bool(dS <= GATE_B_S_TOL and (dl is None or dl <= GATE_B_LAM_TOL))})
    for row in n1e6:
        N = row["N"]
        psi, n_q, pi_N = fresh_psi(N)
        lam = svd_lam(psi, 2 ** row["n_A"], 2 ** (n_q - row["n_A"]), "F")
        dS = abs(s_bits(lam) - row["S_vN"])
        gate_b.append({"N": N, "src": "N1e6", "dS": dS, "dlam": None,
                       "ok": bool(dS <= GATE_B_S_TOL)})
    results["gate_b"] = gate_b
    gate_b_ok = all(g["ok"] for g in gate_b)
    results["gate_b_ok"] = bool(gate_b_ok)
    results["gate_b_max_dS"] = float(max(g["dS"] for g in gate_b))

    # ---------------- GATE-D: Achsen-Freeze-Assert + Pristine-Basen
    axis = []
    base_lam = {}
    for r in ROWS:
        N = r["N"]
        psi, n_q, pi_N = fresh_psi(N)
        lam = carrier_lam(psi, n_q)
        S = s_bits(lam)
        d = abs(S - AXIS_FROZEN[N])
        axis.append({"N": N, "n_qubits": n_q, "pi_N": pi_N, "S_bits": S,
                     "axis_frozen_d": d, "ok": bool(d <= GATE_D_TOL),
                     "lam_len": int(len(lam))})
        base_lam[N] = lam
    results["axis_series"] = axis
    gate_d_ok = all(a["ok"] for a in axis)
    results["gate_d_ok"] = bool(gate_d_ok)
    results["alpha_axis_full_fit_frisch"] = float(
        np.polyfit(np.log([a["N"] for a in axis]),
                   np.log([a["S_bits"] for a in axis]), 1)[0])

    # ---------------- Gitterpunkte: Kanaele
    points = []
    for r in ROWS:
        N = r["N"]
        psi, n_q, pi_N = fresh_psi(N)
        primes = primes_upto(N)
        lam_p = base_lam[N]
        r_p, ok_p = ratios_and_valid(lam_p)
        gp = {"N": N, "lam_len_pristine": int(len(lam_p)), "n_valid_base": int(np.sum(ok_p))}
        draws_k3_001, draws_k3_005 = [], []
        tilde_len_k3 = []
        rng = np.random.default_rng(20261002 + N)
        for _ in range(50):
            u = rng.uniform(-1.0, 1.0, pi_N)
            gam, lt = gamma_for_amp(psi, n_q, 0.01, u, lam_p, r_p, ok_p)
            draws_k3_001.append(gam)
            tilde_len_k3.append(lt)
        for _ in range(10):
            u = rng.uniform(-1.0, 1.0, pi_N)
            gam, lt = gamma_for_amp(psi, n_q, 0.05, u, lam_p, r_p, ok_p)
            draws_k3_005.append(gam)
            tilde_len_k3.append(lt)
        gp["K3_q95_001"] = q95(draws_k3_001)
        gp["K3_median_001"] = float(np.median(draws_k3_001))
        gp["K3_q95_005"] = q95(draws_k3_005)
        gp["K3_tilde_len_min"] = int(min(tilde_len_k3))
        gp["K3_tilde_len_max"] = int(max(tilde_len_k3))
        frac = (np.asarray(primes, float) / N) ** 2
        gp["K2_001"] = gamma_for_amp(psi, n_q, 0.01, frac, lam_p, r_p, ok_p)[0]
        gp["K2_005"] = gamma_for_amp(psi, n_q, 0.05, frac, lam_p, r_p, ok_p)[0]
        alt = (-1.0) ** np.arange(pi_N)
        gp["K5_001"] = gamma_for_amp(psi, n_q, 0.01, alt, lam_p, r_p, ok_p)[0]
        ones = np.ones(pi_N)
        gp["K1_001"] = gamma_for_amp(psi, n_q, 0.01, ones, lam_p, r_p, ok_p)[0]
        gp["K1_005"] = gamma_for_amp(psi, n_q, 0.05, ones, lam_p, r_p, ok_p)[0]
        points.append(gp)
    results["grid_points"] = points

    # ---------------- GATE-A, GATE-C
    k1_vals = [v for gp in points for v in (gp["K1_001"], gp["K1_005"]) if v is not None]
    results["gate_a_max_K1"] = float(max(k1_vals))
    gate_a_ok = bool(all(v is not None and v <= GATE_A_TOL for v in k1_vals)
                     and len(k1_vals) == 2 * len(points))
    results["gate_a_ok"] = gate_a_ok

    valids = [gp for gp in points
              if gp["n_valid_base"] >= 1
              and gp["K3_q95_001"] is not None]
    valid_ids = {gp["N"] for gp in valids}
    results["valid_points"] = sorted(valid_ids)
    results["excluded_points"] = [gp["N"] for gp in points if gp["N"] not in valid_ids]
    gate_c_ok = len(valids) >= 8
    results["gate_c_ok"] = bool(gate_c_ok)
    results["gate_c_n_valid"] = len(valids)

    # ---------------- VERDICT (gefrorene Regel)
    gamma_valid = [gp["K3_q95_001"] for gp in valids]
    S_valid = [AXIS_FROZEN[gp["N"]] for gp in valids]
    rho_obs = spearman(gamma_valid, S_valid)
    rng_s = np.random.default_rng(SHUFFLE_SEED)
    g_arr = np.asarray(gamma_valid, float)
    rho_null = np.asarray([spearman(rng_s.permutation(g_arr), S_valid)
                           for _ in range(SHUFFLE_N)])
    q95_null = float(np.quantile(np.abs(rho_null), 0.95))
    results["verdict_inputs"] = {
        "rho_obs": rho_obs, "q95_null_abs": q95_null, "n_valid": len(valids),
        "rho_null_abs_max": float(np.max(np.abs(rho_null))),
        "rho_null_mean_abs": float(np.mean(np.abs(rho_null))),
    }
    if not (gate_a_ok and gate_b_ok and gate_c_ok and gate_d_ok):
        verdict = "DEGENERAT"
    elif abs(rho_obs) <= q95_null:
        verdict = "KAUSALGLIED_GEFALLEN"
    elif rho_obs > q95_null:
        verdict = "MITWANDERUNG_POSITIV"
    else:
        verdict = "MITWANDERUNG_NEGATIV"
    results["verdict"] = verdict

    # ---------------- Konfund-Kit (NOT verdict-tragend)
    NQ = {r["N"]: r["n_qubits"] for r in ROWS}
    N_valid = [float(gp["N"]) for gp in valids]
    S_rel = [AXIS_FROZEN[gp["N"]] / (NQ[gp["N"]] // 2) for gp in valids]
    rank_active = [float(gp["n_valid_base"]) for gp in valids]
    konf = {
        "rho_gamma_vs_N": spearman(gamma_valid, N_valid),
        "rho_gamma_vs_rank_active": spearman(gamma_valid, rank_active),
        "rho_gamma_vs_S_rel": spearman(gamma_valid, S_rel),
    }
    rG, rS, rA = avg_ranks(gamma_valid), avg_ranks(S_valid), avg_ranks(rank_active)
    bg, ag = np.polyfit(rA, rG, 1)
    bs, as_ = np.polyfit(rA, rS, 1)
    konf["partial_rho_gamma_S_given_rank_active"] = spearman(
        rG - (ag + bg * rA), rS - (as_ + bs * rA))
    results["konfund_kit"] = konf

    # ---------------- Blend-Diagnostik fixed N=1023 (NOT verdict-tragend)
    rng_chi = np.random.default_rng(20261003)
    chi = rng_chi.standard_normal(BLEND_N) + 1j * rng_chi.standard_normal(BLEND_N)
    psi_1023, n_q_1023, pi_1023 = fresh_psi(1023)
    primes_1023 = np.asarray(primes_upto(1023))
    rng_bk = np.random.default_rng(20261004)
    blend = []
    for theta in BLEND_THETAS:
        psi_t = (1.0 - theta) * psi_1023.astype(complex) + theta * chi
        psi_t /= np.linalg.norm(psi_t)
        lam_t = carrier_lam(psi_t, n_q_1023)
        r_t, ok_t = ratios_and_valid(lam_t)
        draws = []
        for _ in range(50):
            u = rng_bk.uniform(-1.0, 1.0, pi_1023)
            gam, _lt = gamma_for_amp(psi_t, n_q_1023, 0.01, u, lam_t, r_t, ok_t,
                                     idx=primes_1023)
            draws.append(gam)
        blend.append({"theta": theta, "S_bits": s_bits(lam_t), "K3_q95": q95(draws),
                      "n_valid": int(np.sum(ok_t)), "lam_len": int(len(lam_t))})
    bvalid = [b for b in blend if b["n_valid"] >= 1 and b["K3_q95"] is not None]
    results["blend_diagnostik"] = {
        "points": blend,
        "n_valid_points": len(bvalid),
        "rho_gamma_vs_S": spearman([b["K3_q95"] for b in bvalid],
                                   [b["S_bits"] for b in bvalid])
        if len(bvalid) >= 3 else None,
    }

    # ---------------- Sekundaer-Kanaele: Richtung-Konsistenz (NOT verdict-tragend)
    sec = []
    for ch in ("K3_q95_005", "K2_001", "K2_005", "K5_001"):
        vals = [gp[ch] for gp in valids]
        med_g = float(np.median([gp["K3_q95_001"] for gp in valids]))
        med_c = float(np.median(vals))
        same = sum(1 for gp, v in zip(valids, vals)
                   if np.sign(gp["K3_q95_001"] - med_g) == np.sign(v - med_c))
        sec.append({"channel": ch, "same_median_sign": same,
                    "of": len(valids)})
    results["secondary_sign_consistency"] = sec

    results["total_runtime_seconds"] = time.time() - t0
    with open(RESULTS_PATH, "w") as fh:
        json.dump(results, fh, indent=1, default=float)

    print("VERDICT:", verdict)
    print("rho_obs %.6f | q95_null %.6f | n_valid %d / 11"
          % (rho_obs, q95_null, len(valids)))
    print("GATES: A %s (max %.2e) | B %s (max dS %.2e) | C %s (%d) | D %s"
          % (gate_a_ok, results["gate_a_max_K1"], gate_b_ok,
             results["gate_b_max_dS"], gate_c_ok, len(valids), gate_d_ok))
    print("alpha_axis_full_fit_frisch: %.16f" % results["alpha_axis_full_fit_frisch"])
    print("Runtime %.1f s" % results["total_runtime_seconds"])


if __name__ == "__main__":
    main()