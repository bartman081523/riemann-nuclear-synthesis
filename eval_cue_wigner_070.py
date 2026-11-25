"""Evaluation script fuer EXPERIMENT 070: H-CUE-WIGNER-SURMISE-GUE-SYNTHESIS."""

from __future__ import annotations
import json
import hashlib

def run_evaluation():
    with open("scratches/pt_cue_wigner_070_prereg.json", "rb") as f:
        prereg_bytes = f.read()
    computed_sha256 = hashlib.sha256(prereg_bytes).hexdigest()

    with open("pt_cue_wigner_070_raw.json", "r", encoding="utf-8") as f:
        raw = json.load(f)

    assert raw["prereg_sha256"] == computed_sha256, "Preregistration SHA-256 Mismatch!"

    results = raw["results"]
    eval_report = {
        "experiment_id": "070",
        "name": "H-CUE-WIGNER-SURMISE-GUE-SYNTHESIS",
        "prereg_sha256": computed_sha256,
        "hypotheses_evaluation": {},
        "per_dimension": {},
    }

    # H-CWS-1: P(s < 0.2) <= 0.02 across N in {50, 100, 200}
    # H-CWS-2: RMSD(GUE) / RMSD(Poisson) <= 0.20 across all dimensions
    # H-CWS-3: min_{tau in (0, 0.4)} K(tau) <= 0.10 across all dimensions
    # H-CWS-4: QPU reference fidelity >= 0.950

    h1_pass = True
    h2_pass = True
    h3_pass = True

    for n_str, data in results.items():
        p_02 = data["fraction_s_le_0_2"]
        ratio_rmsd = data["ratio_rmsd_gue_to_poisson"]
        min_k = data["min_k_early_tau"]

        n_h1 = p_02 <= 0.02
        n_h2 = ratio_rmsd <= 0.20
        n_h3 = min_k <= 0.10

        eval_report["per_dimension"][n_str] = {
            "fraction_s_le_0_2": p_02,
            "h1_pass": n_h1,
            "rmsd_wigner_gue": data["rmsd_wigner_gue"],
            "rmsd_poisson": data["rmsd_poisson"],
            "ratio_rmsd": ratio_rmsd,
            "h2_pass": n_h2,
            "min_k_early_tau": min_k,
            "h3_pass": n_h3,
        }

        if not n_h1: h1_pass = False
        if not n_h2: h2_pass = False
        if not n_h3: h3_pass = False

    qpu_fid = raw["qpu_reference_fidelity"]
    h4_pass = qpu_fid >= 0.950

    eval_report["hypotheses_evaluation"] = {
        "H-CWS-1": {
            "description": "GUE Quadratic Spacing Repulsion: P(s < 0.2) <= 0.02",
            "verdict": "CONFIRMED" if h1_pass else "REFUTED",
        },
        "H-CWS-2": {
            "description": "Global Wigner-GUE Spacing Convergence: RMSD(GUE)/RMSD(Poisson) <= 0.20",
            "verdict": "CONFIRMED" if h2_pass else "REFUTED",
        },
        "H-CWS-3": {
            "description": "Spectral Form Factor Universal Ramp: min_{tau <= 0.4} K(tau) <= 0.10",
            "verdict": "CONFIRMED" if h3_pass else "REFUTED",
        },
        "H-CWS-4": {
            "description": "Quantum Hardware Frobenius-Interferometer Fidelity >= 0.950",
            "verdict": "CONFIRMED" if h4_pass else "REFUTED",
            "value": qpu_fid,
        },
    }

    all_confirmed = h1_pass and h2_pass and h3_pass and h4_pass
    eval_report["overall_verdict"] = "CONFIRMED_ALL_HYPOTHESES" if all_confirmed else "PARTIAL_OR_REFUTED"

    with open("pt_cue_wigner_070_eval.json", "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    print(f"Overall Verdict: {eval_report['overall_verdict']}")
    print(json.dumps(eval_report["hypotheses_evaluation"], indent=2))
    print(json.dumps(eval_report["per_dimension"], indent=2))

if __name__ == "__main__":
    run_evaluation()
