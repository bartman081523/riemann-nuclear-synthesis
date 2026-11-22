"""EXPERIMENT 058 — 023-EXT-Repin via Tridiag-Pfad (H-REPIN-EXT).
0 QPU, seed-frei. Rechnet den kompletten 14-Punkt-Sweep
N = 7..65535 mit dem speichereffizienten Tridiag-Pfad nach und pinnt
gegen die committeten 023-EXT-Artefakte.

Anker (committed, NICHT editiert):
  Prereg : pt_rh_multi_observable_ext_prereg.json (md5 334c97545a41bdf0383c7cc35cdfbb2f)
  Results: pt_rh_multi_observable_ext_results.json
  v1-Ref  : pt_rh_multi_observable_results.json
  Pfad   : pt_rh_multi_observable_ext.py:cv_spread_tridiag (solver_pin null_a),
           dense-vs-tridiag-Probe bei N=65535: 0.086356402 (9 Dezimalen).

Eigen-Prereg (dieses Experiments, Freeze VOR der Messung):
  scratches/pt_repin_ext_058_prereg.json
Schwellen (ex ante):
  T1 S/R-Reproduktion <= 1e-12 an allen 14 Punkten
  T2 alpha-v1-8pt-Reproduktion <= 1e-12 gegen Pin 0.2658212701252552
  T3 |cv_tridiag - cv_committed| <= 1e-9 an allen 14 Punkten UND
     9-Dezimal-Probe bei N=65535 (0.086356402)
  T4 Verdict-Regeln: alpha_combined < 0.5, alle R < 1,
     cv-Mittel in [0.05, 0.20], MOCS_ext >= 2
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: F401 (Sieb/Arithmetik-Pfad wie Bestand)

from pt_prime_state import sieve_primes, construct_P_N, measure_entropy
from pt_rh_multi_observable import (
    alpha_vN_scaling, latorre_ratio,
)
from pt_rh_multi_observable_ext import cv_spread_tridiag

EXPERIMENT = "058-repin-ext-tridiag"
HYPOTHESIS = "H-REPIN-EXT"
PREREG_PATH = "scratches/pt_repin_ext_058_prereg.json"
RESULTS_PATH = "scratches/pt_repin_ext_058_results.json"
EXT_PREREG_MD5 = "334c97545a41bdf0383c7cc35cdfbb2f"
EXT_RESULTS = "pt_rh_multi_observable_ext_results.json"

N_SWEEP = [7, 15, 31, 63, 127, 255, 511, 1023,
           2047, 4095, 8191, 16383, 32767, 65535]
ALPHA_V1_PIN = 0.2658212701252552
T_SR, T_ALPHA, T_CV = 1e-12, 1e-12, 1e-9


def build_prereg():
    return {
        "experiment": EXPERIMENT, "hypothesis": HYPOTHESIS,
        "n_sweep": N_SWEEP,
        "anker": {"ext_prereg_md5": EXT_PREREG_MD5,
                  "ext_results": EXT_RESULTS,
                  "alpha_v1_pin": ALPHA_V1_PIN},
        "thresholds": {"t1_sr": T_SR, "t2_alpha": T_ALPHA, "t3_cv": T_CV,
                       "alpha_max": 0.5, "cv_band": [0.05, 0.20]},
        "verdict_map": {
            "CONFIRMED": "T1+T2+T3+T4 alle grün",
            "PARTIAL": "T1+T2 grün, genau ein T3-Punkt über 1e-9 aber unter 1e-6 (Solver-Rauschen), T4 grün",
            "REFUTED": "T4 verletzt oder >=2 T3-Brüche oder T1/T2-Bruch jenseits Solver-Rauschen",
            "INVALID": "Anker-md5-Mismatch oder committed Results unlesbar",
        },
        "qpu": "0 QPU — construct_P_N + SVD + Tridiag-Solver, kein Quanten-SDK",
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
        raise ValueError("058-Prereg-md5-MISMATCH")
    return doc


def run_evaluation():
    doc = load_frozen()
    with open("pt_rh_multi_observable_ext_prereg.json", "rb") as fh:
        raw = fh.read()
    if hashlib.md5(raw).hexdigest() != EXT_PREREG_MD5:
        return {"experiment": EXPERIMENT, "prereg_md5": doc["md5"],
                "verdict": "EVALUATION_INVALID_ANKER_MD5"}
    committed = json.load(open(EXT_RESULTS, encoding="utf-8"))
    com_by_n = {r["N"]: r for r in committed["rows"]}

    rows = []
    worst_sr = worst_alpha = worst_cv = 0.0
    t1_ok = t2_ok = True
    for N in N_SWEEP:
        primes = sieve_primes(N)
        vec, dim, nq = construct_P_N(N)
        S_tup = measure_entropy(vec)
        S = float(S_tup[0])
        R = float(latorre_ratio(S, len(primes)))
        cv = float(cv_spread_tridiag(list(map(int, primes))))
        c = com_by_n[N]
        dS = abs(S - c["S_vN"])
        dR = abs(R - c["R_N"])
        dCV = abs(cv - c["cv_spread_A"])
        worst_sr = max(worst_sr, dS, dR)
        worst_cv = max(worst_cv, dCV)
        if dS > T_SR or dR > T_SR:
            t1_ok = False
        rows.append({"N": N, "S": S, "R": R, "cv": cv,
                     "cS": c["S_vN"], "cR": c["R_N"], "cCV": c["cv_spread_A"],
                     "dS": dS, "dR": dR, "dCV": dCV})

    S_vals = [r["S"] for r in rows]
    import math as _m
    xs = [_m.log(n) for n in N_SWEEP]
    ys = [_m.log(s) for s in S_vals]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    alpha_c = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    v1_idx = slice(0, 8)
    xs1, ys1 = xs[v1_idx], ys[v1_idx]
    mx1, my1 = sum(xs1) / 8, sum(ys1) / 8
    alpha_v1 = sum((x - mx1) * (y - my1) for x, y in zip(xs1, ys1)) / sum((x - mx1) ** 2 for x in xs1)
    d_alpha = abs(alpha_v1 - ALPHA_V1_PIN)
    worst_alpha = d_alpha
    if d_alpha > T_ALPHA:
        t2_ok = False

    cv_ok_all = all(r["dCV"] <= T_CV for r in rows)
    probe_ok = abs(rows[-1]["cv"] - 0.086356402) < 5e-10
    t3_ok = cv_ok_all and probe_ok
    partial_cv = (sum(1 for r in rows if r["dCV"] > T_CV) == 1
                  and all(r["dCV"] <= 1e-6 for r in rows))

    alpha_ok = alpha_c < 0.5
    r_ok = all(r["R"] < 1 for r in rows)
    cv_mean = sum(r["cv"] for r in rows) / len(rows)
    cv_ok = 0.05 <= cv_mean <= 0.20
    mocs_ext = int(alpha_ok) + int(r_ok) + int(cv_ok)
    t4_ok = mocs_ext >= 2 and alpha_ok and r_ok and cv_ok

    if not (t1_ok and t2_ok and t4_ok):
        verdict = "H-REPIN-EXT_REFUTED" if (t1_ok and t2_ok) else "EVALUATION_INVALID_KONTROLLE_GESCHEITERT" if not (t1_ok and t2_ok) else "H-REPIN-EXT_REFUTED"
        if not (t1_ok and t2_ok):
            verdict = "EVALUATION_INVALID_KONTROLLE_GESCHEITERT"
    elif t3_ok:
        verdict = "H-REPIN-EXT_CONFIRMED"
    elif partial_cv and t4_ok:
        verdict = "H-REPIN-EXT_PARTIAL"
    else:
        verdict = "H-REPIN-EXT_REFUTED"
    return {"experiment": EXPERIMENT, "hypothesis": HYPOTHESIS,
            "prereg_md5": doc["md5"], "qpu_jobs": 0,
            "t1_sr_ok": bool(t1_ok), "t2_alpha_ok": bool(t2_ok),
            "t3_cv_ok": bool(t3_ok), "t4_verdict_ok": bool(t4_ok),
            "worst_sr": worst_sr, "d_alpha_v1": d_alpha,
            "worst_cv": worst_cv, "probe_65535_ok": bool(probe_ok),
            "alpha_combined": alpha_c, "alpha_v1": alpha_v1,
            "cv_mean": cv_mean, "mocs_ext": mocs_ext,
            "committed_alpha_combined": committed.get("alpha_combined"),
            "rows": rows, "verdict": verdict}


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
    print("T1/T2/T3/T4:", res.get("t1_sr_ok"), res.get("t2_alpha_ok"),
          res.get("t3_cv_ok"), res.get("t4_verdict_ok"))
    print("worst_sr %.2e d_alpha %.2e worst_cv %.2e" % (
        res.get("worst_sr", -1), res.get("d_alpha_v1", -1), res.get("worst_cv", -1)))
    print("alpha_c %.6f cv_mean %.6f mocs %s" % (
        res.get("alpha_combined", -1), res.get("cv_mean", -1), res.get("mocs_ext")))
    ok = res["verdict"] == "H-REPIN-EXT_CONFIRMED"
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
