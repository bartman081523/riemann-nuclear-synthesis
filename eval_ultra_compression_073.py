"""Evaluation script fuer EXPERIMENT 073: H-ULTRA-COMPRESSION-MASTER-KERNEL."""

from __future__ import annotations
import json
import hashlib

def run_evaluation():
    with open("scratches/pt_ultra_compression_073_prereg.json", "rb") as f:
        prereg_bytes = f.read()
    computed_sha256 = hashlib.sha256(prereg_bytes).hexdigest()

    with open("pt_ultra_compression_073_raw.json", "r", encoding="utf-8") as f:
        raw = json.load(f)

    assert raw["prereg_sha256"] == computed_sha256, "Preregistration SHA-256 Mismatch!"

    results = raw["results"]
    eval_report = {
        "experiment_id": "073",
        "name": "H-ULTRA-COMPRESSION-MASTER-KERNEL",
        "prereg_sha256": computed_sha256,
        "hypotheses_evaluation": {},
    }

    # H-UCM-1: abs(||W_q||_op - 1.0) <= 1e-12
    # H-UCM-2: sigma_2(W_q) <= 1.0 / sqrt(q) + 1e-12
    ops = results["operators"]
    h1_pass = True
    h2_pass = True
    for q_str, d in ops.items():
        if d["norm_diff_from_one"] > 1e-12:
            h1_pass = False
        if not d["sigma_2_le_bound"]:
            h2_pass = False

    # H-UCM-3: Condensation factor >= 100.0x
    comp = results["compression"]
    factor = comp["compression_factor"]
    h3_pass = factor >= 100.0

    # H-UCM-4: CZ count <= 3 and Circuit depth <= 8
    hw = results["hardware"]
    h4_pass = (hw["cz_count"] <= 3) and (hw["circuit_depth"] <= 8)

    eval_report["hypotheses_evaluation"] = {
        "H-UCM-1": {
            "description": "Master Operator Spectral Contractivity: ||W_q||_op = 1.000000",
            "verdict": "CONFIRMED" if h1_pass else "REFUTED",
            "max_norm_diff": max(d["norm_diff_from_one"] for d in ops.values()),
        },
        "H-UCM-2": {
            "description": "Standard Subspace Spectral Annihilation: sigma_2(W_q) <= 1/sqrt(q)",
            "verdict": "CONFIRMED" if h2_pass else "REFUTED",
        },
        "H-UCM-3": {
            "description": "Extreme Code Condensation Across All Heavy Modules >= 100.0x",
            "verdict": "CONFIRMED" if h3_pass else "REFUTED",
            "condensation_factor": factor,
            "original_heavy_modules_bytes": comp["total_original_bytes"],
            "master_kernel_bytes": comp["master_kernel_bytes"],
        },
        "H-UCM-4": {
            "description": "Hardware Gate Count Parity: CZ <= 3 and depth <= 8 on ibm_fez",
            "verdict": "CONFIRMED" if h4_pass else "REFUTED",
            "cz_count": hw["cz_count"],
            "circuit_depth": hw["circuit_depth"],
        },
    }

    all_confirmed = h1_pass and h2_pass and h3_pass and h4_pass
    eval_report["overall_verdict"] = "CONFIRMED_ALL_HYPOTHESES" if all_confirmed else "PARTIAL_OR_REFUTED"

    with open("pt_ultra_compression_073_eval.json", "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    print(f"Overall Verdict: {eval_report['overall_verdict']}")
    print(json.dumps(eval_report["hypotheses_evaluation"], indent=2))

if __name__ == "__main__":
    run_evaluation()
