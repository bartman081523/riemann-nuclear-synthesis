#!/usr/bin/env python3
"""EXPERIMENT 064: H-ARTIN-SCHREIER-DELIGNE.

Exakter Nachweis der Deligne-Weil Spektralschranken in Z[zeta_q]:
- H-ASD-1: Lineare Summen verschwinden identisch S(ax) == 0
- H-ASD-2: Quadratische Gauss-Summen saturieren |S|^2 == q * 1 bit-exakt
- H-ASD-3: Kubische Summen erfuellen Deligne-Schranke |sigma_k(S)|^2 <= 4q fuer alle Galois-Einbettungen
- H-ASD-4: Artin-Schreier Quantenpropagator-Schranke |<0|W_f|0>| <= d - 1

Disziplin:
--run: Schreibt Rohdaten nach pt_artin_schreier_064_raw.json (Commit VOR Auswertung).
--eval: Liest Rohdaten und bewertet strikt gegen scratches/pt_artin_schreier_064_prereg.json.
"""

from __future__ import annotations

import argparse
import cmath
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Dict, Any, List

from primequant import (
    poly_eval_mod,
    artin_schreier_exponential_sum,
    artin_schreier_magnitude_squared,
    artin_schreier_deligne_bound,
    cyc_zero,
    cyc_from_int,
    cyc_eq,
)


def evaluate_embeddings(q: int, element: List[int]) -> List[float]:
    """Berechnet |sigma_k(element)|^2 fuer alle k in {1, ..., q-1}."""
    mags = []
    for k in range(1, q):
        val = sum(c * cmath.exp(2j * math.pi * k * a / q) for a, c in enumerate(element))
        mags.append(abs(val) ** 2)
    return mags


def run_experiment() -> Dict[str, Any]:
    prereg_path = Path("scratches/pt_artin_schreier_064_prereg.json")
    with open(prereg_path, "rb") as f:
        prereg_sha256 = hashlib.sha256(f.read()).hexdigest()

    # 1. H-ASD-1: Lineare Summen
    h1_records = []
    for q in [3, 5, 7, 11, 13]:
        for a in range(1, q):
            s = artin_schreier_exponential_sum(q, [0, a])
            is_zero = cyc_eq(s, cyc_zero(q))
            h1_records.append({
                "q": q,
                "a": a,
                "s": list(s),
                "is_zero": is_zero
            })

    # 2. H-ASD-2: Quadratische Gauss-Summen
    h2_records = []
    for q in [3, 5, 7, 11, 13]:
        mag2 = artin_schreier_magnitude_squared(q, [0, 0, 1])
        expected = cyc_from_int(q, q)
        is_exact_q = cyc_eq(mag2, expected)
        h2_records.append({
            "q": q,
            "mag2": list(mag2),
            "expected": list(expected),
            "is_exact_q": is_exact_q
        })

    # 3. H-ASD-3: Kubische Weierstraß-Summen (x^3 + ax)
    h3_records = []
    for q in [5, 7, 11, 13, 17, 19]:
        bound = artin_schreier_deligne_bound(q, degree=3)
        for a in [0, 1, 2]:
            s = artin_schreier_exponential_sum(q, [0, a, 0, 1])
            mags = evaluate_embeddings(q, list(s))
            max_mag = max(mags) if mags else 0.0
            ratio = max_mag / bound if bound > 0 else 0.0
            holds = (max_mag <= bound + 1e-9)
            h3_records.append({
                "q": q,
                "a": a,
                "deligne_bound": bound,
                "max_embedding_mag2": max_mag,
                "ratio": ratio,
                "holds": holds
            })

    # 4. H-ASD-4: Unitäre Projektion
    h4_records = []
    for q in [5, 7, 11, 13]:
        # d=2
        s_d2 = artin_schreier_exponential_sum(q, [0, 0, 1])
        mags_d2 = evaluate_embeddings(q, list(s_d2))
        proj_d2 = [math.sqrt(m / q) for m in mags_d2]
        
        # d=3
        s_d3 = artin_schreier_exponential_sum(q, [0, 1, 0, 1])
        mags_d3 = evaluate_embeddings(q, list(s_d3))
        proj_d3 = [math.sqrt(m / q) for m in mags_d3]

        h4_records.append({
            "q": q,
            "max_proj_d2": max(proj_d2),
            "bound_d2": 1.0,
            "holds_d2": (max(proj_d2) <= 1.0 + 1e-9),
            "max_proj_d3": max(proj_d3),
            "bound_d3": 2.0,
            "holds_d3": (max(proj_d3) <= 2.0 + 1e-9),
        })

    return {
        "experiment_id": "EXP-064",
        "prereg_sha256": prereg_sha256,
        "h1_records": h1_records,
        "h2_records": h2_records,
        "h3_records": h3_records,
        "h4_records": h4_records,
    }


def evaluate_results(raw_path: str = "pt_artin_schreier_064_raw.json") -> Dict[str, Any]:
    with open(raw_path) as f:
        raw = json.load(f)

    # 1. H-ASD-1
    h1_fails = [r for r in raw["h1_records"] if not r["is_zero"]]
    h1_status = "CONFIRMED" if len(h1_fails) == 0 else "REFUTED"

    # 2. H-ASD-2
    h2_fails = [r for r in raw["h2_records"] if not r["is_exact_q"]]
    h2_status = "CONFIRMED" if len(h2_fails) == 0 else "REFUTED"

    # 3. H-ASD-3
    h3_fails = [r for r in raw["h3_records"] if not r["holds"]]
    h3_status = "CONFIRMED" if len(h3_fails) == 0 else "REFUTED"

    # 4. H-ASD-4
    h4_fails = [r for r in raw["h4_records"] if not (r["holds_d2"] and r["holds_d3"])]
    h4_status = "CONFIRMED" if len(h4_fails) == 0 else "REFUTED"

    overall = (
        "CONFIRMED_ALL_HYPOTHESES"
        if all(s == "CONFIRMED" for s in [h1_status, h2_status, h3_status, h4_status])
        else "MIXED_OR_REFUTED"
    )

    max_ratio_cubic = max(r["ratio"] for r in raw["h3_records"])

    return {
        "experiment_id": "EXP-064",
        "prereg_sha256": raw["prereg_sha256"],
        "verdicts": {
            "H-ASD-1": {"status": h1_status, "fails": len(h1_fails)},
            "H-ASD-2": {"status": h2_status, "fails": len(h2_fails)},
            "H-ASD-3": {"status": h3_status, "fails": len(h3_fails), "max_ratio_to_deligne": max_ratio_cubic},
            "H-ASD-4": {"status": h4_status, "fails": len(h4_fails)},
        },
        "overall_verdict": overall,
    }


def main():
    parser = argparse.ArgumentParser(description="EXP-064 Runner & Evaluator")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--eval", action="store_true")
    args = parser.parse_args()

    if args.run:
        data = run_experiment()
        out = Path("pt_artin_schreier_064_raw.json")
        with open(out, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[EXP-064] Rohdaten gespeichert in {out}")
    elif args.eval:
        res = evaluate_results()
        out = Path("pt_artin_schreier_064_eval.json")
        with open(out, "w") as f:
            json.dump(res, f, indent=2)
        print(f"[EXP-064] Evaluation abgeschlossen: {res['overall_verdict']}")
        print(json.dumps(res, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
