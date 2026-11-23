"""Evaluation script fuer EXPERIMENT 068: Frobenius Monodromy Pair Correlation & GUE Bridge."""

from __future__ import annotations
import json
import hashlib

def run_evaluation():
    with open("scratches/pt_frobenius_pair_corr_068_prereg.json", "rb") as f:
        prereg_bytes = f.read()
    computed_sha256 = hashlib.sha256(prereg_bytes).hexdigest()
    prereg = json.loads(prereg_bytes)
    
    with open("pt_frobenius_pair_corr_068_raw.json", "r", encoding="utf-8") as f:
        raw = json.load(f)
        
    assert raw["prereg_sha256"] == computed_sha256, "Preregistration SHA-256 Mismatch!"
    
    results = raw["results"]
    eval_report = {
        "experiment_id": "068",
        "name": "H-FROBENIUS-PAIR-CORRELATION-GUE",
        "prereg_sha256": computed_sha256,
        "hypotheses_evaluation": {},
        "per_modulus": {},
    }
    
    # Pruefung H-FPC-1: Level repulsion R_2(s <= 0.2) <= 0.60
    # Pruefung H-FPC-2: RMSD_GUE < RMSD_Poisson in [0.5, 1.5]
    # Pruefung H-FPC-3: |R_2(s) - 1.0| <= 0.35 in [2.5, 4.0] fuer q >= 300
    # Pruefung H-FPC-4: min_{tau < 0.5} K(tau) < 0.85
    
    h1_pass = True
    h2_pass = True
    h3_pass = True
    h4_pass = True
    
    for q_str, data in results.items():
        q = data["q"]
        rep = data["mean_repulsion_s_le_0_2"]
        rmsd_gue = data["rmsd_gue_mid"]
        rmsd_poi = data["rmsd_poisson_mid"]
        tail_dev = data["mean_tail_dev_large_s"]
        min_k = data["min_k_early_tau"]
        
        q_h1 = rep <= 0.60
        q_h2 = rmsd_gue < rmsd_poi
        q_h3 = tail_dev <= 0.35 if q >= 300 else True
        q_h4 = min_k < 0.85
        
        eval_report["per_modulus"][q_str] = {
            "mean_repulsion_s_le_0_2": rep,
            "h1_pass": q_h1,
            "rmsd_gue_mid": rmsd_gue,
            "rmsd_poisson_mid": rmsd_poi,
            "h2_pass": q_h2,
            "mean_tail_dev_large_s": tail_dev,
            "h3_pass": q_h3,
            "min_k_early_tau": min_k,
            "h4_pass": q_h4,
        }
        
        if not q_h1: h1_pass = False
        if not q_h2: h2_pass = False
        if not q_h3 and q >= 300: h3_pass = False
        if not q_h4: h4_pass = False
        
    eval_report["hypotheses_evaluation"] = {
        "H-FPC-1": {
            "description": "Short-range level repulsion R_2(s) <= 0.60 for s <= 0.2",
            "verdict": "CONFIRMED" if h1_pass else "REFUTED",
        },
        "H-FPC-2": {
            "description": "GUE Correlation Agreement: RMSD(GUE) < RMSD(Poisson) in [0.5, 1.5]",
            "verdict": "CONFIRMED" if h2_pass else "REFUTED",
        },
        "H-FPC-3": {
            "description": "Asymptotic Poisson Recovery for Large Spacing |R_2(s) - 1.0| <= 0.35",
            "verdict": "CONFIRMED" if h3_pass else "REFUTED",
        },
        "H-FPC-4": {
            "description": "Spectral Form Factor Dip min_{tau < 0.5} K(tau) < 0.85",
            "verdict": "CONFIRMED" if h4_pass else "REFUTED",
        },
    }
    
    all_confirmed = h1_pass and h2_pass and h3_pass and h4_pass
    eval_report["overall_verdict"] = "CONFIRMED_ALL_HYPOTHESES" if all_confirmed else "PARTIAL_OR_REFUTED"
    
    with open("pt_frobenius_pair_corr_068_eval.json", "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)
        
    print(f"Overall Verdict: {eval_report['overall_verdict']}")
    print(json.dumps(eval_report["hypotheses_evaluation"], indent=2))
    print(json.dumps(eval_report["per_modulus"], indent=2))

if __name__ == "__main__":
    run_evaluation()
