"""Evaluation script fuer EXPERIMENT 072: H-METAPLECTIC-SIMPLIFICATION-PROOF."""

from __future__ import annotations
import json
import hashlib

def run_evaluation():
    with open("scratches/pt_metaplectic_simplification_072_prereg.json", "rb") as f:
        prereg_bytes = f.read()
    computed_sha256 = hashlib.sha256(prereg_bytes).hexdigest()

    with open("pt_metaplectic_simplification_072_raw.json", "r", encoding="utf-8") as f:
        raw = json.load(f)

    assert raw["prereg_sha256"] == computed_sha256, "Preregistration SHA-256 Mismatch!"

    results = raw["results"]
    eval_report = {
        "experiment_id": "072",
        "name": "H-METAPLECTIC-SIMPLIFICATION-PROOF",
        "prereg_sha256": computed_sha256,
        "hypotheses_evaluation": {},
    }

    # H-MSP-1: max_idempotency_error <= 1e-15 and max_standard_annihilation_error <= 1e-15
    projs = results["projectors"]
    h1_pass = True
    for q_str, d in projs.items():
        if d["max_idempotency_error"] > 1e-15 or d["max_standard_annihilation_error"] > 1e-15:
            h1_pass = False

    # H-MSP-2 & H-MSP-3: delta_P >= 0.35 and P(q0=0) >= 0.950
    hw = results["hardware_resonance"]
    p_q0 = hw["p_q0_resonance_L2"]
    delta_P = hw["delta_P"]
    h2_pass = delta_P >= 0.35
    h3_pass = (p_q0 >= 0.950) and (delta_P >= 0.40)

    # H-MSP-4: Condensation ratio >= 30.0x
    cc = results["code_condensation"]
    ratio = cc["condensation_ratio"]
    h4_pass = ratio >= 30.0

    eval_report["hypotheses_evaluation"] = {
        "H-MSP-1": {
            "description": "Algebraic Projector Idempotency & Standard Sector Annihilation (q in 3..13)",
            "verdict": "CONFIRMED" if h1_pass else "REFUTED",
            "max_idempotency_err": max(d["max_idempotency_error"] for d in projs.values()),
            "max_annihilation_err": max(d["max_standard_annihilation_error"] for d in projs.values()),
        },
        "H-MSP-2": {
            "description": "Multiplicity Resonance contrast delta_P >= 0.35 at L = floor(sqrt(q))",
            "verdict": "CONFIRMED" if h2_pass else "REFUTED",
            "delta_P": delta_P,
        },
        "H-MSP-3": {
            "description": "Hardware Fidelity on ibm_fez >= 0.950 and delta_P >= 0.40",
            "verdict": "CONFIRMED" if h3_pass else "REFUTED",
            "measured_P_q0": p_q0,
            "measured_delta_P": delta_P,
        },
        "H-MSP-4": {
            "description": "Proof Complexity Condensation ratio >= 30.0x (bytes replaced)",
            "verdict": "CONFIRMED" if h4_pass else "REFUTED",
            "condensation_ratio": ratio,
            "original_bytes": cc["total_original_bytes"],
            "metaplectic_bytes": cc["size_Metaplectic_bytes"],
        },
    }

    all_confirmed = h1_pass and h2_pass and h3_pass and h4_pass
    eval_report["overall_verdict"] = "CONFIRMED_ALL_HYPOTHESES" if all_confirmed else "PARTIAL_OR_REFUTED"

    with open("pt_metaplectic_simplification_072_eval.json", "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    print(f"Overall Verdict: {eval_report['overall_verdict']}")
    print(json.dumps(eval_report["hypotheses_evaluation"], indent=2))

if __name__ == "__main__":
    run_evaluation()
