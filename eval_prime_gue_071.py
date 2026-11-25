"""Evaluation script fuer EXPERIMENT 071: H-PRIME-GUE-SPECTRAL-DUALITY."""

from __future__ import annotations
import json
import hashlib

def run_evaluation():
    with open("scratches/pt_prime_gue_071_prereg.json", "rb") as f:
        prereg_bytes = f.read()
    computed_sha256 = hashlib.sha256(prereg_bytes).hexdigest()

    with open("pt_prime_gue_071_raw.json", "r", encoding="utf-8") as f:
        raw = json.load(f)

    assert raw["prereg_sha256"] == computed_sha256, "Preregistration SHA-256 Mismatch!"

    results = raw["results"]
    eval_report = {
        "experiment_id": "071",
        "name": "H-PRIME-GUE-SPECTRAL-DUALITY",
        "prereg_sha256": computed_sha256,
        "hypotheses_evaluation": {},
    }

    # H-PGD-1: P(s < 0.2) <= 0.02
    # H-PGD-2: min_{tau in (0, 0.4)} K(tau) <= 0.20
    # H-PGD-3: C_prime_zeros >= 0.25
    # H-PGD-4: Fidelity >= 0.950

    p_02 = results["fraction_s_le_0_2"]
    min_k = results["min_k_early_tau"]
    c_pz = results["prime_zero_correlation"]
    qpu_fid = results["qpu_reference_fidelity"]

    h1_pass = p_02 <= 0.02
    h2_pass = min_k <= 0.20
    h3_pass = c_pz >= 0.25
    h4_pass = qpu_fid >= 0.950

    eval_report["metrics"] = {
        "n_zeros": results["n_zeros"],
        "mean_spacing": results["mean_spacing"],
        "min_spacing": results["min_spacing"],
        "fraction_s_le_0_2": p_02,
        "min_k_early_tau": min_k,
        "prime_zero_correlation": c_pz,
        "qpu_reference_fidelity": qpu_fid,
    }

    eval_report["hypotheses_evaluation"] = {
        "H-PGD-1": {
            "description": "Riemann Zero Spacing Level Repulsion: P(s < 0.2) <= 0.02",
            "verdict": "CONFIRMED" if h1_pass else "REFUTED",
            "value": p_02,
        },
        "H-PGD-2": {
            "description": "Spectral Form Factor Dip: min_{tau <= 0.4} K(tau) <= 0.20",
            "verdict": "CONFIRMED" if h2_pass else "REFUTED",
            "value": min_k,
        },
        "H-PGD-3": {
            "description": "Prime-Explicit Fourier Dual Resonance: C_prime_zeros >= 0.25",
            "verdict": "CONFIRMED" if h3_pass else "REFUTED",
            "value": c_pz,
        },
        "H-PGD-4": {
            "description": "Hardware Phase-Encoding Verification >= 0.950",
            "verdict": "CONFIRMED" if h4_pass else "REFUTED",
            "value": qpu_fid,
        },
    }

    all_confirmed = h1_pass and h2_pass and h3_pass and h4_pass
    eval_report["overall_verdict"] = "CONFIRMED_ALL_HYPOTHESES" if all_confirmed else "PARTIAL_OR_REFUTED"

    with open("pt_prime_gue_071_eval.json", "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    print(f"Overall Verdict: {eval_report['overall_verdict']}")
    print(json.dumps(eval_report["hypotheses_evaluation"], indent=2))
    print(json.dumps(eval_report["metrics"], indent=2))

if __name__ == "__main__":
    run_evaluation()
