#!/usr/bin/env python3
"""EXPERIMENT 065: H-ENTANGLEMENT-LOG-ASYMPTOTICS.

Analytische Aufloesung der Latorre-Sierra-Spannung ueber logarithmische
Versschraenkungsskalierung S_vN ~ a * ln(N) + b:
- H-ELA-1: R^2 >= 0.990 fuer S_vN = a * ln(N) + b ueber nq in [5, 14]
- H-ELA-2: Globaler effektiver Exponent alpha_eff <= 0.35 (Ausschluss alpha=1)
- H-ELA-3: Struktur-Entropie-Luecke Delta S = S_rand - S_prime >= 0.10 fuer nq in [6, 10]

Disziplin:
--run: Schreibt Rohdaten nach pt_entanglement_log_065_raw.json (Commit VOR Auswertung).
--eval: Liest Rohdaten und bewertet strikt gegen scratches/pt_entanglement_log_065_prereg.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Dict, Any, List

import numpy as np


def sieve(N: int) -> List[int]:
    if N < 2:
        return []
    is_p = [True] * (N + 1)
    is_p[0] = is_p[1] = False
    for p in range(2, math.isqrt(N) + 1):
        if is_p[p]:
            for i in range(p * p, N + 1, p):
                is_p[i] = False
    return [i for i, p in enumerate(is_p) if p]


def svn_entropy(state: np.ndarray, nA: int, nB: int) -> float:
    mat = state.reshape((2 ** nA, 2 ** nB))
    s = np.linalg.svd(mat, compute_uv=False)
    s = s[s > 1e-12]
    probs = s ** 2
    return float(-np.sum(probs * np.log2(probs)))


def run_experiment() -> Dict[str, Any]:
    prereg_path = Path("scratches/pt_entanglement_log_065_prereg.json")
    with open(prereg_path, "rb") as f:
        prereg_sha256 = hashlib.sha256(f.read()).hexdigest()

    records = []
    # nq von 5 bis 14 (N von 31 bis 16383)
    for nq in range(5, 15):
        N = 2 ** nq - 1
        primes = sieve(N)
        pi_N = len(primes)
        nA = nq // 2
        nB = nq - nA

        # Prime state
        sv_prime = np.zeros(2 ** nq, dtype=np.float64)
        for p in primes:
            sv_prime[p] = 1.0 / math.sqrt(pi_N)
        s_prime = svn_entropy(sv_prime, nA, nB)

        # Random control (nur fuer nq <= 10 wegen Rechenzeit)
        s_rand_mean = None
        delta_s = None
        if nq <= 10:
            rng = np.random.default_rng(42 + nq)
            rands = []
            for _ in range(15):
                rand_idx = rng.choice(range(1, N + 1), size=pi_N, replace=False)
                sv_rand = np.zeros(2 ** nq, dtype=np.float64)
                for r in rand_idx:
                    sv_rand[r] = 1.0 / math.sqrt(pi_N)
                rands.append(svn_entropy(sv_rand, nA, nB))
            s_rand_mean = float(np.mean(rands))
            delta_s = s_rand_mean - s_prime

        records.append({
            "nq": nq,
            "N": N,
            "pi_N": pi_N,
            "nA": nA,
            "nB": nB,
            "S_prime": s_prime,
            "S_rand_mean": s_rand_mean,
            "delta_S": delta_s
        })

    # Logarithmischer Fit S = a * ln(N) + b
    N_arr = np.array([r["N"] for r in records], dtype=np.float64)
    S_arr = np.array([r["S_prime"] for r in records], dtype=np.float64)
    logN = np.log(N_arr)
    slope, intercept = np.polyfit(logN, S_arr, 1)
    preds = slope * logN + intercept
    ss_tot = float(np.sum((S_arr - np.mean(S_arr)) ** 2))
    ss_res = float(np.sum((S_arr - preds) ** 2))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Effektiver Exponent zwischen N=31 und N=16383
    s_first = records[0]["S_prime"]
    s_last = records[-1]["S_prime"]
    n_first = records[0]["N"]
    n_last = records[-1]["N"]
    alpha_eff = float((math.log(s_last) - math.log(s_first)) / (math.log(n_last) - math.log(n_first)))

    return {
        "experiment_id": "EXP-065",
        "prereg_sha256": prereg_sha256,
        "fit_slope_a": float(slope),
        "fit_intercept_b": float(intercept),
        "fit_r2": float(r2),
        "alpha_eff_5_to_14": alpha_eff,
        "records": records
    }


def evaluate_results(raw_path: str = "pt_entanglement_log_065_raw.json") -> Dict[str, Any]:
    with open(raw_path) as f:
        raw = json.load(f)

    # 1. H-ELA-1: R^2 >= 0.990
    r2 = raw["fit_r2"]
    h1_status = "CONFIRMED" if r2 >= 0.990 else "REFUTED"

    # 2. H-ELA-2: alpha_eff <= 0.35
    alpha = raw["alpha_eff_5_to_14"]
    h2_status = "CONFIRMED" if alpha <= 0.35 else ("UNDETERMINED" if alpha <= 0.40 else "REFUTED")

    # 3. H-ELA-3: Delta S >= 0.10 fuer nq in [6, 10]
    delta_s_vals = [r["delta_S"] for r in raw["records"] if 6 <= r["nq"] <= 10]
    min_delta = min(delta_s_vals) if delta_s_vals else 0.0
    h3_status = "CONFIRMED" if min_delta >= 0.10 else ("UNDETERMINED" if min_delta >= 0.05 else "REFUTED")

    overall = (
        "CONFIRMED_ALL_HYPOTHESES"
        if all(s == "CONFIRMED" for s in [h1_status, h2_status, h3_status])
        else "MIXED_OR_REFUTED"
    )

    return {
        "experiment_id": "EXP-065",
        "prereg_sha256": raw["prereg_sha256"],
        "verdicts": {
            "H-ELA-1": {"status": h1_status, "r2": r2, "threshold": 0.990},
            "H-ELA-2": {"status": h2_status, "alpha_eff": alpha, "threshold": 0.35},
            "H-ELA-3": {"status": h3_status, "min_delta_S": min_delta, "threshold": 0.10},
        },
        "overall_verdict": overall,
        "asymptotic_model": f"S_vN(N) = {raw['fit_slope_a']:.4f} * ln(N) + {raw['fit_intercept_b']:.4f}"
    }


def main():
    parser = argparse.ArgumentParser(description="EXP-065 Runner & Evaluator")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--eval", action="store_true")
    args = parser.parse_args()

    if args.run:
        data = run_experiment()
        out = Path("pt_entanglement_log_065_raw.json")
        with open(out, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[EXP-065] Rohdaten gespeichert in {out}")
    elif args.eval:
        res = evaluate_results()
        out = Path("pt_entanglement_log_065_eval.json")
        with open(out, "w") as f:
            json.dump(res, f, indent=2)
        print(f"[EXP-065] Evaluation abgeschlossen: {res['overall_verdict']}")
        print(json.dumps(res, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
