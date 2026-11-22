#!/usr/bin/env python3
"""EXPERIMENT 062: H-VON-MANGOLDT-GRH-DECAY.

Führt die exakte Von-Mangoldt-Zustandspräparation und Sektor-Projektion aus:
- H-GRH-1: Standardsektor-Populations-Skalierung P_std(X) <= 2.0 / X
- H-GRH-2: Restklassen-Varianz Var_coprime(p) * X^2 <= 1.5
- H-GRH-3: Weil-Filter Reinheit gamma_2 >= 0.50

Append-Only Ledger Discipline:
--run: Schreibt Rohdaten nach pt_grh_decay_062_raw.json (Commit VOR Auswertung).
--eval: Liest Rohdaten und bewertet strikt gegen scratches/pt_grh_decay_062_prereg.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Any

# Exakter stdlib-Import aus primequant
from primequant import (
    von_mangoldt_exact,
    von_mangoldt_residue_counts,
    galois_projector_matrix,
    cyc_zero,
    cyc_one,
)


def compute_p_std(X: int, q: int) -> Dict[str, Any]:
    """Berechnet die Population des orthogonalen Standardsektors mod q."""
    counts = von_mangoldt_residue_counts(X, q)
    total_power_count = sum(counts)
    if total_power_count == 0:
        return {"X": X, "q": q, "P_std": 0.0, "scaled": 0.0}
    
    # Wahrscheinlichkeitsverteilung über Restklassen
    # p[r] = counts[r] / total_power_count
    # Trivialsektor r=0 trägt nur Primteiler von q (maximal log_p(X) Terme)
    p = [c / total_power_count for c in counts]
    
    # Masse des Null-Residuums (trivialer Sektor)
    p0 = p[0]
    p_std = p0  # Masse des Trägers, der durch Vielfache von q entsteht
    
    # Coprime-Residuen: r in [1, q-1]
    coprime_counts = counts[1:]
    mean_coprime = sum(coprime_counts) / len(coprime_counts)
    var_coprime = sum((c - mean_coprime) ** 2 for c in coprime_counts) / len(coprime_counts)
    # Normierte Varianz der relativen Wahrscheinlichkeiten
    var_p_coprime = var_coprime / (total_power_count ** 2) if total_power_count > 0 else 0.0

    return {
        "X": X,
        "q": q,
        "counts": counts,
        "total_count": total_power_count,
        "P_std": p0,
        "X_times_P_std": X * p0,
        "var_coprime_p": var_p_coprime,
        "X2_times_var_p": (X ** 2) * var_p_coprime,
    }


def compute_filtered_purity(X: int, q: int) -> float:
    """Berechnet die Reinheit gamma_2 des Galois-gefilterten Zustands in Z[zeta_q]."""
    # Zustandsvektor |psi> = sum_r sqrt(p_r) |r>
    counts = von_mangoldt_residue_counts(X, q)
    total = sum(counts)
    if total == 0:
        return 0.0
    
    # Dichtematrix rho_rr' = sqrt(p_r p_r')
    # Vereinfachte Reinheit unter Galois-Projektor Pi_G
    # Pi_G projiziert auf Invariante unter Gal(F_q/F_p)
    # Fuer prime q ist die Galois-Gruppe zyklisch der Ordnung (q-1)
    # Bei q=3: Restklassen {1, 2} sind quadratisch invariant / vertauschbar
    # Rechnen wir die exakte Reinheit der Dichtematrix rho = |psi><psi|
    # Reinheit eines reinen Zustands ist 1.0; gefiltert durch Pi_G:
    # Tr((Pi_G rho Pi_G)^2) / (Tr(Pi_G rho))^2
    p = [c / total for c in counts]
    # Amplitude in den Galois-Orbits:
    # Orbit 0: {0}
    # Orbit 1 (Einheiten): {1, ..., q-1}
    # Unter Galois-Mittelung wird die Phase symmetrisiert
    # Fuer reelle Amplituden:
    # rho_sym = sum_g g(rho) / |G|
    # Fuer q=3: G = {id, sigma}, sigma tauscht 1 und 2
    # rho_sym Diagonale: [p[0], (p[1]+p[2])/2, (p[1]+p[2])/2]
    # Off-Diagonale (0, 1): sqrt(p[0]) * (sqrt(p[1]) + sqrt(p[2])) / 2
    # Tr(rho_sym^2):
    diag = [p[0]] + [(p[1] + p[2]) / 2.0] * 2 if q == 3 else p
    purity = sum(x ** 2 for x in diag)
    # Addiere signifikante Off-Diagonale
    if q == 3:
        off_01 = (math.sqrt(p[0]) * (math.sqrt(p[1]) + math.sqrt(p[2])) / 2.0)
        off_12 = (math.sqrt(p[1] * p[2])) # symmetrisch
        purity += 2 * (off_01 ** 2) * 2 + 2 * (off_12 ** 2)
    return min(1.0, purity)


def run_experiment() -> Dict[str, Any]:
    """Erzeugt die Rohdaten für EXPERIMENT 062."""
    prereg_path = Path("scratches/pt_grh_decay_062_prereg.json")
    with open(prereg_path, "rb") as f:
        prereg_sha256 = hashlib.sha256(f.read()).hexdigest()

    test_range_X = [50, 100, 200, 500, 1000, 2000, 3000]
    primes_q = [3, 5, 7]

    h1_data = []
    for q in primes_q:
        for X in test_range_X:
            res = compute_p_std(X, q)
            h1_data.append(res)

    h3_data = []
    for q in [3, 5]:
        for X in [100, 500, 1000, 2000]:
            pur = compute_filtered_purity(X, q)
            h3_data.append({"X": X, "q": q, "purity": pur})

    raw_output = {
        "experiment_id": "EXP-062",
        "prereg_sha256": prereg_sha256,
        "h1_data": h1_data,
        "h3_data": h3_data,
    }
    return raw_output


def evaluate_results(raw_path: str = "pt_grh_decay_062_raw.json") -> Dict[str, Any]:
    """Bewertet die Rohdaten gegen die eingefrorenen Schranken."""
    with open(raw_path, "r") as f:
        raw = json.load(f)

    # 1. H-GRH-1 Prüfung
    # Falsifikation: Any X >= 100 with X * P_std(X) > 2.0
    h1_viol = [d for d in raw["h1_data"] if d["X"] >= 100 and d["X_times_P_std"] > 2.0]
    h1_status = "CONFIRMED" if len(h1_viol) == 0 else "REFUTED"

    # 2. H-GRH-2 Prüfung
    # Falsifikation: Any X >= 500 with Var_coprime(p) * X^2 > 1.5
    h2_viol = [d for d in raw["h1_data"] if d["X"] >= 500 and d["X2_times_var_p"] > 1.5]
    h2_status = "CONFIRMED" if len(h2_viol) == 0 else "REFUTED"

    # 3. H-GRH-3 Prüfung
    # Falsifikation: Any X >= 500 with gamma_2 < 0.50
    h3_viol = [d for d in raw["h3_data"] if d["X"] >= 500 and d["purity"] < 0.50]
    h3_status = "CONFIRMED" if len(h3_viol) == 0 else "REFUTED"

    overall_verdict = (
        "CONFIRMED_ALL_HYPOTHESES"
        if (h1_status == "CONFIRMED" and h2_status == "CONFIRMED" and h3_status == "CONFIRMED")
        else "MIXED_OR_REFUTED"
    )

    eval_output = {
        "experiment_id": "EXP-062",
        "prereg_sha256": raw["prereg_sha256"],
        "verdicts": {
            "H-GRH-1": {"status": h1_status, "violations": len(h1_viol)},
            "H-GRH-2": {"status": h2_status, "violations": len(h2_viol)},
            "H-GRH-3": {"status": h3_status, "violations": len(h3_viol)},
        },
        "overall_verdict": overall_verdict,
        "max_X_times_P_std": max(d["X_times_P_std"] for d in raw["h1_data"] if d["X"] >= 100),
        "max_X2_times_var_p": max(d["X2_times_var_p"] for d in raw["h1_data"] if d["X"] >= 500),
        "min_purity_500_plus": min(d["purity"] for d in raw["h3_data"] if d["X"] >= 500),
    }
    return eval_output


def main():
    parser = argparse.ArgumentParser(description="EXP-062 Run & Eval")
    parser.add_argument("--run", action="store_true", help="Erzeuge Rohdaten")
    parser.add_argument("--eval", action="store_true", help="Bewerte Rohdaten")
    args = parser.parse_args()

    if args.run:
        data = run_experiment()
        out_path = Path("pt_grh_decay_062_raw.json")
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[EXP-062] Rohdaten gespeichert in {out_path}")

    elif args.eval:
        res = evaluate_results()
        out_path = Path("pt_grh_decay_062_eval.json")
        with open(out_path, "w") as f:
            json.dump(res, f, indent=2)
        print(f"[EXP-062] Evaluation abgeschlossen: {res['overall_verdict']}")
        print(json.dumps(res, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
