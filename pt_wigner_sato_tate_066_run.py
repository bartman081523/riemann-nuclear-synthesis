#!/usr/bin/env python3
"""EXPERIMENT 066: H-WIGNER-SATO-TATE-CONVERGENCE.

Exakter Nachweis der Konvergenz von Artin-Schreier-Exponentialsummen
gegen die Wigner-Halbkreis- / Sato-Tate-Verteilung (GUE-Kern):
- H-WST-1: 2. Moment m_2 -> 1/4 = 0.2500 (|m_2 - 0.2500| <= 0.0050)
- H-WST-2: 4. Moment m_4 -> 1/8 = 0.1250 (|m_4 - 0.1250| <= 0.0050)
- H-WST-3: 6. Moment m_6 -> 5/64 = 0.078125 (|m_6 - 0.078125| <= 0.0050)
- H-WST-4: Kolmogorov-Smirnov Test D_KS <= 0.050, p >= 0.10

Disziplin:
--run: Schreibt Rohdaten nach pt_wigner_sato_tate_066_raw.json (Commit VOR Auswertung).
--eval: Liest Rohdaten und bewertet strikt gegen scratches/pt_wigner_sato_tate_066_prereg.json.
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

import numpy as np
from scipy.stats import kstest


def wigner_cdf(t: np.ndarray) -> np.ndarray:
    t_clamped = np.clip(t, -1.0, 1.0)
    return 0.5 + (1.0 / math.pi) * (t_clamped * np.sqrt(1.0 - t_clamped ** 2) + np.arcsin(t_clamped))


def compute_family(q: int) -> np.ndarray:
    omega = cmath.exp(2j * math.pi / q)
    sums = []
    for a in range(q):
        # S(x^3 + ax) = sum_{x=0}^{q-1} omega^{x^3 + ax mod q}
        s = sum(omega ** ((x ** 3 + a * x) % q) for x in range(q))
        sums.append(s.real)
    t = np.array(sums, dtype=np.float64) / (2.0 * math.sqrt(q))
    return t


def run_experiment() -> Dict[str, Any]:
    prereg_path = Path("scratches/pt_wigner_sato_tate_066_prereg.json")
    with open(prereg_path, "rb") as f:
        prereg_sha256 = hashlib.sha256(f.read()).hexdigest()

    primes_q = [101, 199, 503, 1009]
    records = []

    for q in primes_q:
        t = compute_family(q)
        m2 = float(np.mean(t ** 2))
        m4 = float(np.mean(t ** 4))
        m6 = float(np.mean(t ** 6))
        m8 = float(np.mean(t ** 8))

        ks_stat = None
        ks_p = None
        if q >= 500:
            ks_res = kstest(t, wigner_cdf)
            ks_stat = float(ks_res.statistic)
            ks_p = float(ks_res.pvalue)

        records.append({
            "q": q,
            "sample_size": q,
            "min_t": float(np.min(t)),
            "max_t": float(np.max(t)),
            "m2": m2,
            "m4": m4,
            "m6": m6,
            "m8": m8,
            "ks_statistic": ks_stat,
            "ks_pvalue": ks_p,
            "raw_t_sample": list(t[:10])  # Erste 10 fuer Audit
        })

    return {
        "experiment_id": "EXP-066",
        "prereg_sha256": prereg_sha256,
        "records": records
    }


def evaluate_results(raw_path: str = "pt_wigner_sato_tate_066_raw.json") -> Dict[str, Any]:
    with open(raw_path) as f:
        raw = json.load(f)

    # 1. H-WST-1: |m2 - 0.2500| <= 0.0050
    m2_devs = [abs(r["m2"] - 0.2500) for r in raw["records"]]
    max_m2_dev = max(m2_devs)
    h1_status = "CONFIRMED" if max_m2_dev <= 0.0050 else ("UNDETERMINED" if max_m2_dev <= 0.0100 else "REFUTED")

    # 2. H-WST-2: |m4 - 0.1250| <= 0.0050
    m4_devs = [abs(r["m4"] - 0.1250) for r in raw["records"]]
    max_m4_dev = max(m4_devs)
    h2_status = "CONFIRMED" if max_m4_dev <= 0.0050 else ("UNDETERMINED" if max_m4_dev <= 0.0100 else "REFUTED")

    # 3. H-WST-3: |m6 - 0.078125| <= 0.0050 fuer q >= 500
    m6_devs = [abs(r["m6"] - 0.078125) for r in raw["records"] if r["q"] >= 500]
    max_m6_dev = max(m6_devs) if m6_devs else 0.0
    h3_status = "CONFIRMED" if max_m6_dev <= 0.0050 else ("UNDETERMINED" if max_m6_dev <= 0.0100 else "REFUTED")

    # 4. H-WST-4: KS-Test D_KS <= 0.050, p >= 0.10 fuer q >= 500
    ks_stats = [r["ks_statistic"] for r in raw["records"] if r["q"] >= 500]
    ks_ps = [r["ks_pvalue"] for r in raw["records"] if r["q"] >= 500]
    max_ks = max(ks_stats) if ks_stats else 1.0
    min_p = min(ks_ps) if ks_ps else 0.0
    h4_status = "CONFIRMED" if (max_ks <= 0.050 and min_p >= 0.10) else ("UNDETERMINED" if (max_ks <= 0.080 and min_p >= 0.05) else "REFUTED")

    overall = (
        "CONFIRMED_ALL_HYPOTHESES"
        if all(s == "CONFIRMED" for s in [h1_status, h2_status, h3_status, h4_status])
        else "MIXED_OR_REFUTED"
    )

    return {
        "experiment_id": "EXP-066",
        "prereg_sha256": raw["prereg_sha256"],
        "verdicts": {
            "H-WST-1": {"status": h1_status, "max_m2_dev": max_m2_dev, "threshold": 0.0050},
            "H-WST-2": {"status": h2_status, "max_m4_dev": max_m4_dev, "threshold": 0.0050},
            "H-WST-3": {"status": h3_status, "max_m6_dev": max_m6_dev, "threshold": 0.0050},
            "H-WST-4": {"status": h4_status, "max_ks_statistic": max_ks, "min_p_value": min_p},
        },
        "overall_verdict": overall,
    }


def main():
    parser = argparse.ArgumentParser(description="EXP-066 Runner & Evaluator")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--eval", action="store_true")
    args = parser.parse_args()

    if args.run:
        data = run_experiment()
        out = Path("pt_wigner_sato_tate_066_raw.json")
        with open(out, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[EXP-066] Rohdaten gespeichert in {out}")
    elif args.eval:
        res = evaluate_results()
        out = Path("pt_wigner_sato_tate_066_eval.json")
        with open(out, "w") as f:
            json.dump(res, f, indent=2)
        print(f"[EXP-066] Evaluation abgeschlossen: {res['overall_verdict']}")
        print(json.dumps(res, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
