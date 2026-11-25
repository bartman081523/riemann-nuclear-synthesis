"""Evaluation script fuer EXPERIMENT 069: H-JACOBI-FROBENIUS-GUE-ASYMPTOTICS."""

from __future__ import annotations
import json
import hashlib

def run_evaluation():
    with open("scratches/pt_jacobi_frobenius_069_prereg.json", "rb") as f:
        prereg_bytes = f.read()
    computed_sha256 = hashlib.sha256(prereg_bytes).hexdigest()
    prereg = json.loads(prereg_bytes)

    with open("pt_jacobi_frobenius_069_raw.json", "r", encoding="utf-8") as f:
        raw = json.load(f)

    assert raw["prereg_sha256"] == computed_sha256, "Preregistration SHA-256 Mismatch!"

    results = raw["results"]
    eval_report = {
        "experiment_id": "069",
        "name": "H-JACOBI-FROBENIUS-GUE-ASYMPTOTICS",
        "prereg_sha256": computed_sha256,
        "hypotheses_evaluation": {},
        "per_genus": {},
    }

    # H-JF-1: P(s < 0.2) <= 0.03 and P(s < 0.05) <= 0.002 across g in {20, 50, 100}
    # H-JF-2: RMSD_GUE < 0.5 * RMSD_Poisson for s in [0.2, 2.0] at g = 100
    # H-JF-3: P(theta_1 < 0.1 * (pi / g)) <= 0.02 across all g
    # H-JF-4: min_{tau in (0, 0.4)} K(tau) <= 0.15 across all g

    h1_pass = True
    h3_pass = True
    h4_pass = True

    for g_str, data in results.items():
        g = data["g"]
        p_02 = data["fraction_s_le_0_2"]
        p_005 = data["fraction_s_le_0_05"]
        p_origin = data["fraction_origin_close"]
        rmsd_gue = data["rmsd_gue_bulk"]
        rmsd_poi = data["rmsd_poisson_bulk"]
        min_k = data["min_k_early_tau"]

        g_h1 = (p_02 <= 0.03) and (p_005 <= 0.002)
        g_h3 = p_origin <= 0.02
        g_h4 = min_k <= 0.15

        eval_report["per_genus"][g_str] = {
            "fraction_s_le_0_2": p_02,
            "fraction_s_le_0_05": p_005,
            "h1_pass": g_h1,
            "fraction_origin_close": p_origin,
            "h3_pass": g_h3,
            "rmsd_gue_bulk": rmsd_gue,
            "rmsd_poisson_bulk": rmsd_poi,
            "min_k_early_tau": min_k,
            "h4_pass": g_h4,
        }

        if not g_h1: h1_pass = False
        if not g_h3: h3_pass = False
        if not g_h4: h4_pass = False

    data_100 = results["100"]
    h2_pass = data_100["rmsd_gue_bulk"] < 0.5 * data_100["rmsd_poisson_bulk"]
    eval_report["h2_ratio_g100"] = {
        "rmsd_gue": data_100["rmsd_gue_bulk"],
        "rmsd_poisson": data_100["rmsd_poisson_bulk"],
        "ratio": data_100["rmsd_gue_bulk"] / data_100["rmsd_poisson_bulk"],
        "pass": h2_pass,
    }

    eval_report["hypotheses_evaluation"] = {
        "H-JF-1": {
            "description": "Quadratic Level Repulsion (Wigner Surmise / GUE): P(s < 0.2) <= 0.03 and P(s < 0.05) <= 0.002",
            "verdict": "CONFIRMED" if h1_pass else "REFUTED",
        },
        "H-JF-2": {
            "description": "Montgomery-Odlyzko GUE Pair Correlation Convergence: RMSD(GUE) < 0.5 * RMSD(Poisson) at g=100",
            "verdict": "CONFIRMED" if h2_pass else "REFUTED",
        },
        "H-JF-3": {
            "description": "Symplectic Hard-Edge Origin Repulsion: P(theta_1 < 0.1 * (pi / g)) <= 0.02",
            "verdict": "CONFIRMED" if h3_pass else "REFUTED",
        },
        "H-JF-4": {
            "description": "Spectral Form Factor Dip Recovery: min_{tau in (0, 0.4)} K(tau) <= 0.15",
            "verdict": "CONFIRMED" if h4_pass else "REFUTED",
        },
    }

    all_confirmed = h1_pass and h2_pass and h3_pass and h4_pass
    eval_report["overall_verdict"] = "CONFIRMED_ALL_HYPOTHESES" if all_confirmed else "PARTIAL_OR_REFUTED"

    with open("pt_jacobi_frobenius_069_eval.json", "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    print(f"Overall Verdict: {eval_report['overall_verdict']}")
    print(json.dumps(eval_report["hypotheses_evaluation"], indent=2))
    print(json.dumps(eval_report["per_genus"], indent=2))
    print("H2 ratio at g=100:", eval_report["h2_ratio_g100"])

if __name__ == "__main__":
    run_evaluation()
