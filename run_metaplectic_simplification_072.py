"""Runner fuer EXPERIMENT 072: H-METAPLECTIC-SIMPLIFICATION-PROOF."""

from __future__ import annotations
import json
import os
import numpy as np
from fractions import Fraction
from primequant.weil import galois_projector_matrix

PREREG_SHA256 = "9e74164671248b00f516b854234f959355590e26165d5e941f06f1806bffbcf2"

def verify_algebraic_projectors():
    moduli = [3, 5, 7, 11, 13]
    projector_results = {}
    for q in moduli:
        mat_frac = galois_projector_matrix(q)
        P = np.array([[float(x) for x in row] for row in mat_frac], dtype=float)
        
        # Idempotenz P^2 == P
        P_sq = P @ P
        diff_sq = float(np.max(np.abs(P_sq - P)))
        
        # Annihilation des Standard-Unterraums
        # V_std = {v in C^q : sum_{j=1}^{q-1} v_j = 0, v_0 = 0}
        # Basis fuer V_std: e_1 - e_j fuer j=2..q-1
        max_annihilation_err = 0.0
        for j in range(2, q):
            v_std = np.zeros(q)
            v_std[1] = 1.0
            v_std[j] = -1.0
            pv = P @ v_std
            max_annihilation_err = max(max_annihilation_err, float(np.max(np.abs(pv))))
            
        projector_results[str(q)] = {
            "q": q,
            "max_idempotency_error": diff_sq,
            "max_standard_annihilation_error": max_annihilation_err,
        }
    return projector_results

def run():
    # 1. Algebraische Projektor-Pruefung
    proj_res = verify_algebraic_projectors()
    
    # 2. Resonanz-Kontrast
    # Aus Exp 060 (Statevector) und Exp 063 (QPU)
    with open("pt_clifford_weil_063_eval.json") as f:
        qpu_data = json.load(f)
        
    p_q0_zero = qpu_data["p_q0_zero"]
    delta_P_hardware = qpu_data["delta_P"]
    p_q0_res = p_q0_zero["2"]
    
    # 3. Code-Kondensations-Metrik
    # Vergleiche Dateigroessen von PrimeSideA.lean + PrimeSideB.lean vs Metaplectic.lean
    size_side_a = os.path.getsize("zeta-23-lean-review/Zeta23/PrimeSideA.lean")
    size_side_b = os.path.getsize("zeta-23-lean-review/Zeta23/PrimeSideB.lean")
    size_metaplectic = os.path.getsize("zeta-23-lean-review/Zeta23/Weil/Metaplectic.lean")
    total_original_bytes = size_side_a + size_side_b
    condensation_ratio = float(total_original_bytes) / float(size_metaplectic)
    
    results = {
        "projectors": proj_res,
        "hardware_resonance": {
            "job_id": qpu_data["job_id"],
            "backend": qpu_data["backend"],
            "p_q0_resonance_L2": p_q0_res,
            "delta_P": delta_P_hardware,
        },
        "code_condensation": {
            "size_PrimeSideA_bytes": size_side_a,
            "size_PrimeSideB_bytes": size_side_b,
            "total_original_bytes": total_original_bytes,
            "size_Metaplectic_bytes": size_metaplectic,
            "condensation_ratio": condensation_ratio,
        }
    }
    
    raw_payload = {
        "experiment_id": "072",
        "name": "H-METAPLECTIC-SIMPLIFICATION-PROOF",
        "prereg_sha256": PREREG_SHA256,
        "results": results,
    }
    
    with open("pt_metaplectic_simplification_072_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_payload, f, indent=2)
    print("Rohdaten erfolgreich exportiert nach pt_metaplectic_simplification_072_raw.json")

if __name__ == "__main__":
    run()
