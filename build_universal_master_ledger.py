#!/usr/bin/env python3
"""Erzeugt das universelle Master-Ergebnis-Ledger für ALLE Experimente im Projekt.

Klassifiziert alle 84 Ergebnisdateien in:
- QPU (Reale Quantenhardware: ibm_fez, ibm_marrakesh, ibm_kingston)
- Statevector (Exakte Quantensimulation & Aer)
- Analytical / Cyclotomic Z[zeta_q] (Exakte Ringarithmetik & Theoreme)
- Classical Asymptotics / Sieve / Tensor SVD
- Historical Benchmarks & Diag

Schreibt:
- pt_universal_all_experiments_master_ledger.json
- docs/universal_all_experiments_master_report.md
"""

from __future__ import annotations

import datetime
import glob
import json
import os
from pathlib import Path
from typing import Dict, Any, List


def classify_experiment(filepath: str, data: Dict[str, Any]) -> Dict[str, Any]:
    name = Path(filepath).stem
    category = "Unknown"
    mode = "Unknown"
    backend = "None"
    verdict = "UNKNOWN"
    summary = ""

    # 1. Erkennung anhand von Dateinamen und Inhalt
    if "qpu" in name or "fez" in name or "kingston" in name or "marrakesh" in name or "063" in name or "067" in name:
        mode = "Real QPU Hardware"
        if "fez" in name or "063" in name or "067" in name:
            backend = "ibm_fez"
        elif "marrakesh" in name:
            backend = "ibm_marrakesh"
        elif "kingston" in name:
            backend = "ibm_kingston"
        else:
            backend = "IBM Quantum Hardware"
    elif "sv" in name or "statevector" in name or "aer" in name or "sim" in name:
        mode = "Statevector Simulation"
    elif "asymptotic" in name or "sieve" in name or "entanglement" in name:
        mode = "Classical Asymptotics / SVD"
    else:
        mode = "Analytical / Exact Numerics"

    # Verdict-Extraktion
    if isinstance(data, dict):
        if "overall_verdict" in data:
            verdict = str(data["overall_verdict"])
        elif "verdict" in data:
            verdict = str(data["verdict"])
        elif "status" in data:
            verdict = str(data["status"])
        elif "h1_status" in data:
            verdict = str(data["h1_status"])
        elif "rule_holds" in data:
            verdict = "RULE_HOLDS" if data["rule_holds"] else "RULE_REFUTED"

    # Kategorisierung in die Forschungssäulen
    if any(k in name for k in ["prime_state", "alpha", "asymptotic", "renyi", "entanglement"]):
        category = "Pillar 3: Prime State & Entanglement Scaling (Latorre-Sierra)"
    elif any(k in name for k in ["potential", "vqe", "spectral", "rh_multi", "im_bias", "qber"]):
        category = "Pillar 2: Hilbert-Polya Potential & Spectral Gaps"
    elif any(k in name for k in ["ququint", "crossover", "gue", "leakage", "multin"]):
        category = "Pillar 1: QuQuint & GF(5) Geometry"
    elif any(k in name for k in ["zqz", "goe"]):
        category = "Pillar 1b: ZQZ Random Matrix Ensembles"
    elif any(k in name for k in ["ram_q", "prio48", "rem", "hardware", "s4"]):
        category = "Pillar 4: RAM-Q & FP48 Resonance Infrastructure"
    elif "v5" in name:
        category = "Pillar 5: H-V5 Hardware Gap Invariance"
    elif any(k in name for k in ["weil_theta_060", "path_quadric_061", "grh_decay_062", "clifford_weil_063", "artin_schreier_064", "wigner_sato_tate_066", "frobenius_bell_067", "frobenius_pair_corr_068", "jacobi_frobenius_069", "cue_wigner_070", "prime_gue_071", "metaplectic_simplification_072", "ultra_compression_073"]):
        category = "Pillar 6: Alpoge-Claude Lean-4 Synthesis & Deligne-Weil Spectral Resonance"
    elif any(k in name for k in ["symcomp", "mocs", "repin"]):
        category = "Special Audits: SymComp, MOCS & Repin"
    else:
        category = "General / Multi-Observable Diagnostic"

    return {
        "file": filepath,
        "name": name,
        "category": category,
        "mode": mode,
        "backend": backend,
        "verdict": verdict,
        "size_bytes": os.path.getsize(filepath),
    }


def main():
    files = sorted(
        glob.glob("*_eval.json")
        + glob.glob("*_results.json")
        + glob.glob("scratches/*_eval.json")
        + glob.glob("scratches/*_results.json")
    )
    # Entferne Dubletten
    files = list(dict.fromkeys(files))

    records = []
    category_counts = {}
    verdict_counts = {}

    for f in files:
        try:
            with open(f, "r") as fp:
                data = json.load(fp)
        except Exception as e:
            data = {"error": str(e)}

        meta = classify_experiment(f, data)
        records.append(meta)

        cat = meta["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

        v = meta["verdict"]
        # Grobe Normalisierung
        v_norm = "CONFIRMED" if "CONFIRM" in v.upper() else ("REFUTED" if "REFUT" in v.upper() else ("UNDETERMINED" if "UNDET" in v.upper() else "REPORTED/DONE"))
        verdict_counts[v_norm] = verdict_counts.get(v_norm, 0) + 1

    master_ledger = {
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_experiments_recorded": len(records),
        "category_summary": category_counts,
        "verdict_summary": verdict_counts,
        "experiments": records
    }

    out_json = Path("pt_universal_all_experiments_master_ledger.json")
    with open(out_json, "w") as f:
        json.dump(master_ledger, f, indent=2)
    print(f"Master-Ledger gespeichert in {out_json} ({len(records)} Experimente erfasst).")

    # Erzeuge Markdown-Report
    out_md = Path("docs/universal_all_experiments_master_report.md")
    with open(out_md, "w") as f:
        f.write("# Universal Master Experiment Ledger & Report (All Experiments)\n\n")
        f.write(f"Timestamp: {master_ledger['generated_at_utc']}\n\n")
        f.write(f"**Total Experiments Recorded:** {len(records)}\n\n")
        f.write("## Summary by Research Pillar\n\n")
        f.write("| Pillar / Category | Experiment Count |\n|---|---|\n")
        for cat, cnt in sorted(category_counts.items()):
            f.write(f"| {cat} | {cnt} |\n")
        f.write("\n## Summary of Verdicts\n\n")
        f.write("| Normalized Verdict | Count |\n|---|---|\n")
        for v, cnt in sorted(verdict_counts.items()):
            f.write(f"| {v} | {cnt} |\n")
        f.write("\n## Complete Table of All Experiments\n\n")
        f.write("| File | Pillar | Mode | Backend | Verdict |\n|---|---|---|---|---|\n")
        for r in records:
            f.write(f"| `{r['file']}` | {r['category']} | {r['mode']} | {r['backend']} | `{r['verdict']}` |\n")

    print(f"Markdown report generated in {out_md}.")


if __name__ == "__main__":
    main()
