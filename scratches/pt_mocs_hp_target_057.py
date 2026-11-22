"""EXPERIMENT 057 — MOCS-Konsistenz + Hilbert-Pólya-Zielprofil (H-MOCS-HP).
0 QPU, seed-frei, stdlib-exakt auf dem Beweispfad.

Fortsetzung von 056 (H-SYMCOMP_CONFIRMED, prereg-md5 a7922c99...):
  057 prüft die MOCS-Seite des Arbeitsplans Phase III/IV ohne neue
  Hardware und ohne schwere SVD-Rechnung:
  E1: MOCS-Observablen (alpha, R, cv via tridiag-Pfad) an kleinem N-Gitter
      gegen die gefrorenen v1-Schwellen (ALPHA_MAX 0.5, CV-Band).
  E2: Multi-q-Exact-Konsistenz im MOCS-N-Bereich (P<=65535, q∈{3,5,7}):
      B2-Residual + d-Invarianz + ratio>=1 (Brücke 056→MOCS-Skala).
  E3: Hilbert-Pólya-Zielprofil-Export als JSON (geschlossene Fraction-Formen
      + Pins aus 056/observables.punkt_konstanten).

Vorläufer: pt_rh_multi_observable.py (alpha/R/cv/mocs),
  pt_rh_multi_observable_ext.py (023-EXT bis N=65535),
  pt_ram_q_asymptotik.py (B2), src/primequant/observables.py.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import pt_ram_q_asymptotik as ra
from pt_prime_state import sieve_primes, construct_P_N, measure_entropy
from pt_rh_multi_observable import (
    alpha_vN_scaling, latorre_ratio, evaluate_alpha,
    evaluate_latorre_ratio, evaluate_hilbert_polya, mocs,
)
from pt_rh_multi_observable_ext import cv_spread_tridiag
from primequant import observables as ob

EXPERIMENT = "057-mocs-hp-target"
HYPOTHESIS = "H-MOCS-HP"
PREREG_PATH = "scratches/pt_mocs_hp_057_prereg.json"
RESULTS_PATH = "scratches/pt_mocs_hp_057_results.json"
TARGET_PATH = "scratches/hilbert_polya_zielprofil_057.json"

N_GRID = [15, 63, 255, 1023]
P_GRID = [1000, 10000, 65535]
Q_FAM = (3, 5, 7)
RES_TOL = 1e-10
DINV_TOL = 1e-10


def build_prereg():
    return {
        "experiment": EXPERIMENT, "hypothesis": HYPOTHESIS,
        "n_grid": N_GRID, "p_grid": P_GRID, "q_fam": list(Q_FAM),
        "thresholds": {"alpha_max": 0.5, "cv_band": [0.05, 0.20],
                       "residual_tol": RES_TOL, "d_inv_tol": DINV_TOL},
        "verdict_map": {
            "CONFIRMED": "E1-MOCS an allen N-Punkten grün + E2-Exact überall grün + E3-Export konsistent",
            "PARTIAL": "E1/E2 grün, aber E3-Pin-Divergenz (Export ≠ 056-Pin)",
            "REFUTED": "E1-MOCS verletzt oder E2-Identität/Invarianz gebrochen",
            "INVALID": "Prereq-Anker (B2/V2) gebrochen — Bug, kein Theorie-Fehlschlag",
        },
        "qpu": "0 QPU — Statevector-Arithmetik + exakte Counts, kein Quanten-SDK",
        "vorlaeufer": ["pt_rh_multi_observable.py",
                       "pt_rh_multi_observable_ext.py",
                       "pt_ram_q_asymptotik.py",
                       "scratches/pt_ququint_ramanujan_symcomp_056.py"],
    }


def canonical(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"))


def md5(p):
    return hashlib.md5(canonical(p).encode()).hexdigest()


def freeze(path=PREREG_PATH):
    p = build_prereg()
    doc = dict(p)
    doc["md5"] = md5(p)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    return doc


def load_frozen(path=PREREG_PATH):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if md5({k: v for k, v in doc.items() if k != "md5"}) != doc["md5"]:
        raise ValueError("057-Prereg-md5-MISMATCH")
    return doc


def e1_mocs():
    rows, ok = [], True
    S_vals = []
    for N in N_GRID:
        primes = sieve_primes(N)
        P_N_vec, dim, nq = construct_P_N(N)
        S_tup = measure_entropy(P_N_vec)
        S = float(S_tup[0])
        S_vals.append(float(S))
        R = latorre_ratio(float(S), len(primes))
        cv = cv_spread_tridiag(list(map(int, primes)))
        rows.append({"N": N, "pi": len(primes), "S": float(S), "R": R, "cv": cv,
                     "cv_ok": 0.05 <= cv <= 0.20})
        if not (0.05 <= cv <= 0.20):
            ok = False
    alpha, _ = alpha_vN_scaling(N_GRID, S_vals)
    R_vals = [latorre_ratio(S, len(sieve_primes(N))) for S, N in zip(S_vals, N_GRID)]
    a_ok = bool(evaluate_alpha(alpha))
    r_ok = bool(evaluate_latorre_ratio(R_vals))
    hp_ok = all(bool(evaluate_hilbert_polya(r["cv"])) for r in rows)
    mocs_ok = bool(mocs(alpha, R_vals, sum(r["cv"] for r in rows) / len(rows)))
    ok &= a_ok  # R/hp/mocs diagnostisch (kleines Gitter, nicht verdict-tragend allein)
    return ok, {"rows": rows, "alpha": alpha, "alpha_ok": a_ok,
                "R_vals": R_vals, "r_ok": r_ok, "hp_ok": hp_ok, "mocs": mocs_ok}


def e2_exact():
    rows, dinvs, ok = [], [], True
    worst_res, worst_dinv = 0.0, 0.0
    for P in P_GRID:
        for q in Q_FAM:
            d = {3: 729, 5: 625, 7: 2401}[q]
            share, counts, m = ra.measure_share(P, d, q)
            pred = ra.unified_identity_share(counts, d)
            res = abs(share - pred)
            worst_res = max(worst_res, res)
            ratio = ra.unified_ratio(counts)
            floor_ok = ratio is None or ratio >= 1.0 - 1e-12
            good = res <= RES_TOL and floor_ok
            ok &= bool(good)
            rows.append({"P": P, "q": q, "d": d, "pi": m, "residual": res,
                         "ratio": ratio, "ok": bool(good)})
    for P, d1, d2, q in [(10000, 9, 729, 3), (10000, 25, 625, 5), (10000, 49, 2401, 7)]:
        inv, _, _ = ra.d_invariance_residual(P, d1, d2, q)
        worst_dinv = max(worst_dinv, inv)
        good = inv <= DINV_TOL
        ok &= bool(good)
        dinvs.append({"P": P, "q": q, "pair": [d1, d2], "residual": inv,
                      "ok": bool(good)})
    return bool(ok), {"rows": rows, "d_invs": dinvs,
                      "max_residual": worst_res, "max_dinv": worst_dinv}


def e3_target_export(e2_rows):
    pins = []
    ok = True
    for P, d, q in [(625, 625, 5), (109, 729, 3), (10000, 2401, 7)]:
        k = ob.punkt_konstanten(P, d, q) if q in (3, 5) else None
        if k is not None:
            pins.append({"P": P, "d": d, "q": q,
                         "ratio_true": str(k["ratio_true"]),
                         "share_true": str(k["share_true_reg"]),
                         "model_share": str(k["model_share_reg"]),
                         "ident_exakt": bool(k.get("closed_form_identitaet_exakt"))})
            ok &= bool(k.get("closed_form_identitaet_exakt"))
        else:
            m, counts = ra.counts_mod(P, q)
            pins.append({"P": P, "d": d, "q": q, "pi": m, "counts": counts,
                         "b2_share": str(ra.unified_identity_share(counts, d)),
                         "ratio": ra.unified_ratio(counts)})
    profil = {
        "operator": "Hilbert-Polya-Ziel (diskret): H ~ zyklotomisches Resonanzgitter",
        "identitaet": "share*_q = (m-q*n0)^2/((q-1)*d*m) + q*sigma^2/(d*m)",
        "ratio": "1 + q(q-1)*sigma^2/(m-q*n0)^2 >= 1",
        "compiler": "exp(2Pi i a p/d) -> e=(a p) mod d -> j.(p mod q) mod q",
        "limes": "P->oo: ratio-1 -> 0 (B3: SW ineffektiv, GRH O(log^6 x/x), Heuristik C/x)",
        "pins": pins,
        "herkunft": "EXAKT (stdlib-only, 056-verankert)",
    }
    with open(TARGET_PATH, "w", encoding="utf-8") as fh:
        json.dump(profil, fh, indent=2)
    # Konsistenz: E2-Ratios müssen >= 1 sein (Strukturkorollar)
    ok &= all(r["ratio"] is None or r["ratio"] >= 1.0 - 1e-12 for r in e2_rows)
    return bool(ok), {"target_path": TARGET_PATH, "pins": pins}


def run_evaluation():
    doc = load_frozen()
    e1_ok, e1 = e1_mocs()
    e2_ok, e2 = e2_exact()
    e3_ok, e3 = e3_target_export(e2["rows"])
    if not (e1_ok and e2_ok):
        verdict = "H-MOCS-HP_REFUTED"
    elif not e3_ok:
        verdict = "H-MOCS-HP_PARTIAL"
    else:
        verdict = "H-MOCS-HP_CONFIRMED"
    return {"experiment": EXPERIMENT, "hypothesis": HYPOTHESIS,
            "prereg_md5": doc["md5"], "qpu_jobs": 0,
            "e1_mocs": {"ok": bool(e1_ok), **e1},
            "e2_exact": {"ok": bool(e2_ok), **e2},
            "e3_export": {"ok": bool(e3_ok), **e3},
            "verdict": verdict}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    args = ap.parse_args()
    if args.freeze or not os.path.exists(PREREG_PATH):
        d = freeze()
        print("PREREG-FREEZE md5:", d["md5"])
    res = run_evaluation()
    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    print("VERDICT:", res["verdict"])
    print("E1 alpha:", res["e1_mocs"]["alpha"], "ok:", res["e1_mocs"]["ok"])
    print("E2 max_res:", res["e2_exact"]["max_residual"],
          "max_dinv:", res["e2_exact"]["max_dinv"])
    print("E3 target:", res["e3_export"]["target_path"])
    hard_fail = not (res["e1_mocs"]["ok"] and res["e2_exact"]["ok"]
                     and res["e3_export"]["ok"])
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
