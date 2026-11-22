"""EXPERIMENT 060: Weil-Theta-Lift und Stepanov-Multiplizitaet.

Ledger-Disziplin (ExperimentLedgerMind):
  - Preregistrierung gefroren in scratches/pt_weil_theta_060_prereg.json
  - Preregistrierungs-SHA256: 4ea634855a3e018c4bcbe64facd5b7c0e314f80fcbdcbc61dacc3a83a16f3c0f
  - Raw Commit VOR Auswertung: --run erzeugt pt_weil_theta_060_raw.json
  - --eval wertet die Rohdaten streng gegen gefrorene Schwellen aus
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from fractions import Fraction
from typing import Any, Dict, List

import numpy as np

# Lokaler Import aus src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from primequant.weil import (
    trace_galois,
    trace_gram_matrix,
    trace_gram_eigenschaften,
    stepanov_multiplicity_bound,
)
from primequant.theta_chain import (
    simulate_theta_chain,
    verify_stepanov_resonance,
)
from primequant.observables import ramanujan_summe

PREREG_PATH = os.path.join("scratches", "pt_weil_theta_060_prereg.json")
EXPECTED_PREREG_SHA256 = "4ea634855a3e018c4bcbe64facd5b7c0e314f80fcbdcbc61dacc3a83a16f3c0f"
RAW_OUTPUT_PATH = "pt_weil_theta_060_raw.json"
EVAL_OUTPUT_PATH = "pt_weil_theta_060_eval.json"


def verify_prereg_hash() -> Dict[str, Any]:
    """Prueft die kryptografische Integritaet der Preregistrierung."""
    if not os.path.exists(PREREG_PATH):
        raise FileNotFoundError(f"Preregistrierung fehlt: {PREREG_PATH}")
    with open(PREREG_PATH, "rb") as f:
        content = f.read()
    digest = hashlib.sha256(content).hexdigest()
    if digest != EXPECTED_PREREG_SHA256:
        raise ValueError(
            f"PREREG-HASH-MISMATCH!\nErwartet: {EXPECTED_PREREG_SHA256}\nGefunden: {digest}"
        )
    return json.loads(content.decode("utf-8"))


def run_experiment_060() -> Dict[str, Any]:
    """Fuehrt alle Berechnungen der Preregistrierung aus (Phase 3: 0 QPU)."""
    prereg = verify_prereg_hash()
    suite = prereg["falsifier_suite"]
    
    # 1. H-WT-1: Trace-Gram vs Ramanujan Identitaet & Spektrum
    gram_results = {}
    for q in suite["primes_exact_algebraic"]:
        G = trace_gram_matrix(q)
        dim = q - 1
        max_diff = 0
        for i in range(dim):
            for j in range(dim):
                c_val = ramanujan_summe(q, (i - j) % q)
                diff = abs(G[i][j] - c_val)
                if diff > max_diff:
                    max_diff = diff
                    
        prop = trace_gram_eigenschaften(q)
        gram_results[str(q)] = {
            "dimension": dim,
            "max_abs_diff_to_ramanujan": max_diff,
            "determinant": prop["determinante"],
            "eigenwert_triv": prop["eigenwert_triv"],
            "eigenwert_std": prop["eigenwert_std"],
        }
        
    # 2. H-WT-2: Stepanov-Resonanz fuer walk_primes [3, 5, 7]
    walk_results = {}
    for q in suite["walk_primes"]:
        history = simulate_theta_chain(q, max_steps=6, p_noise=0.0)
        expected_L = stepanov_multiplicity_bound(q)
        r_vals = [h["R"] for h in history]
        actual_peak_L = int(np.argmax(r_vals[1:])) + 1
        
        walk_results[str(q)] = {
            "expected_L": expected_L,
            "actual_peak_L": actual_peak_L,
            "stepanov_matched": (actual_peak_L == expected_L),
            "baseline_R": history[0]["R"],
            "peak_R": history[actual_peak_L]["R"],
            "stepanov_L_R": history[expected_L]["R"],
            "stepanov_L_purity": history[expected_L]["purity"],
            "stepanov_L_gap": history[expected_L]["gap_over_baseline"],
            "history": history,
        }
        
    # 3. H-WT-3: Depolarisations-Rausch-Sweep fuer q=5
    noise_results = {}
    for p in suite["tested_noise_levels"]:
        history_p = simulate_theta_chain(5, max_steps=5, p_noise=float(p))
        rec_L2 = history_p[2]
        noise_results[f"p_{p:.2f}"] = {
            "p_noise": float(p),
            "R2": rec_L2["R"],
            "gap_over_baseline": rec_L2["gap_over_baseline"],
            "purity": rec_L2["purity"],
        }
        
    raw_payload = {
        "experiment": prereg["experiment"],
        "prereg_sha256": EXPECTED_PREREG_SHA256,
        "gram_results": gram_results,
        "walk_results": walk_results,
        "noise_results": noise_results,
    }
    
    with open(RAW_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(raw_payload, f, indent=2)
    print(f"[OK] Rohdaten erfolgreich gespeichert: {RAW_OUTPUT_PATH}")
    return raw_payload


def evaluate_experiment_060() -> Dict[str, Any]:
    """Wertet pt_weil_theta_060_raw.json gegen die gefrorenen Prereg-Schwellen aus."""
    if not os.path.exists(RAW_OUTPUT_PATH):
        raise FileNotFoundError(f"Rohdaten fehlen: {RAW_OUTPUT_PATH}. Zuerst --run ausfuehren!")
        
    with open(RAW_OUTPUT_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
        
    prereg = verify_prereg_hash()
    theses = prereg["thesis"]["sub_hypotheses"]
    
    # Pruefung H-WT-1
    t1_max_dev = theses["H-WT-1"]["threshold_T1_max_dev"]
    gram_pass = True
    for q_str, res in raw["gram_results"].items():
        if res["max_abs_diff_to_ramanujan"] > t1_max_dev:
            gram_pass = False
    verdict_hwt1 = "CONFIRMED" if gram_pass else "REFUTED"
    
    # Pruefung H-WT-2 (q=5)
    t2_min_R2 = theses["H-WT-2"]["falsification_threshold_T2_min_R2"]
    q5_res = raw["walk_results"]["5"]
    q5_peak_L = q5_res["actual_peak_L"]
    q5_expected_L = q5_res["expected_L"]
    q5_R2 = q5_res["stepanov_L_R"]
    
    verdict_hwt2 = (
        "CONFIRMED"
        if (q5_peak_L == q5_expected_L and q5_R2 > t2_min_R2)
        else "REFUTED"
    )
    
    # Pruefung H-WT-3 (Rauschen p=0.05)
    t3_noise_gap = theses["H-WT-3"]["falsification_threshold_T3_noise_gap"]
    p005_gap = raw["noise_results"]["p_0.05"]["gap_over_baseline"]
    verdict_hwt3 = (
        "CONFIRMED"
        if p005_gap > t3_noise_gap
        else "INCONCLUSIVE_NOISE_WASHED_OUT"
    )
    
    # Pruefung H-WT-4 (Verschraenkung / Purity gamma2 < 0.90)
    t4_max_purity = theses["H-WT-4"]["falsification_threshold_T4_max_purity"]
    q5_purity2 = q5_res["stepanov_L_purity"]
    verdict_hwt4 = (
        "CONFIRMED"
        if q5_purity2 < t4_max_purity
        else "REFUTED"
    )
    
    all_confirmed = (
        verdict_hwt1 == "CONFIRMED"
        and verdict_hwt2 == "CONFIRMED"
        and verdict_hwt3 == "CONFIRMED"
        and verdict_hwt4 == "CONFIRMED"
    )
    
    overall_verdict = "CONFIRMED_ALL_HYPOTHESES" if all_confirmed else "PARTIAL_OR_REFUTED"
    
    eval_payload = {
        "experiment": raw["experiment"],
        "prereg_sha256": raw["prereg_sha256"],
        "verdicts": {
            "H-WT-1_TRACE_GRAM": {
                "verdict": verdict_hwt1,
                "criterion": f"max_diff <= {t1_max_dev}",
                "detail": raw["gram_results"],
            },
            "H-WT-2_STEPANOV_RESONANCE": {
                "verdict": verdict_hwt2,
                "criterion": f"peak_L == 2 AND R2 > {t2_min_R2}",
                "observed_R2": q5_R2,
                "observed_peak_L": q5_peak_L,
            },
            "H-WT-3_NOISE_ROBUSTNESS": {
                "verdict": verdict_hwt3,
                "criterion": f"gap_at_p005 > {t3_noise_gap}",
                "observed_gap_p005": p005_gap,
            },
            "H-WT-4_ENTANGLEMENT": {
                "verdict": verdict_hwt4,
                "criterion": f"purity_L2 < {t4_max_purity}",
                "observed_purity": q5_purity2,
            },
        },
        "overall_verdict": overall_verdict,
    }
    
    with open(EVAL_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_payload, f, indent=2)
    print(f"[OK] Evaluation erfolgreich gespeichert: {EVAL_OUTPUT_PATH}")
    print(f"Gesamturteil: {overall_verdict}")
    return eval_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Experiment 060 Runner")
    parser.add_argument("--run", action="store_true", help="Berechne und speichere Rohdaten")
    parser.add_argument("--eval", action="store_true", help="Werte gespeicherte Rohdaten aus")
    args = parser.parse_args()
    
    if args.run:
        run_experiment_060()
    elif args.eval:
        evaluate_experiment_060()
    else:
        parser.print_help()
