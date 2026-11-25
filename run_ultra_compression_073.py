"""Runner fuer EXPERIMENT 073: H-ULTRA-COMPRESSION-MASTER-KERNEL."""

from __future__ import annotations
import json
import os
import math
import numpy as np

PREREG_SHA256 = "0ae7e84e10bacd80f770ddf24113b6a8a3cd4e18a0c7415d92181581c4155765"

def analyze_master_operators():
    moduli = [3, 5, 7, 11, 13]
    op_results = {}
    for q in moduli:
        omega = np.exp(2j * np.pi / q)
        F = np.zeros((q, q), dtype=complex)
        for j in range(q):
            for k in range(q):
                F[j, k] = omega**(j * k) / np.sqrt(q)
                
        D = np.zeros((q, q), dtype=complex)
        for x in range(q):
            D[x, x] = omega**((x**2) % q)
            
        P = np.zeros((q, q), dtype=complex)
        P[0, 0] = 1.0
        P[1:, 1:] = 1.0 / (q - 1)
        
        W = P @ (D @ F)
        
        # Singulaerwerte von W
        U, s, Vh = np.linalg.svd(W)
        op_norm = float(s[0])
        sigma_2 = float(s[1]) if len(s) > 1 else 0.0
        bound_sigma_2 = 1.0 / math.sqrt(q)
        
        op_results[str(q)] = {
            "q": q,
            "operator_norm": op_norm,
            "norm_diff_from_one": abs(op_norm - 1.0),
            "sigma_2": sigma_2,
            "bound_sigma_2": bound_sigma_2,
            "sigma_2_le_bound": sigma_2 <= bound_sigma_2 + 1e-12,
        }
    return op_results

def run():
    op_results = analyze_master_operators()
    
    # Dateigroessen der fuenf schweren Module
    files_to_compress = [
        "zeta-23-lean-review/Zeta23/Assembly.lean",
        "zeta-23-lean-review/Zeta23/ZeroSide.lean",
        "zeta-23-lean-review/Zeta23/Tail.lean",
        "zeta-23-lean-review/Zeta23/PrimeSideA.lean",
        "zeta-23-lean-review/Zeta23/PrimeSideB.lean",
    ]
    total_original_bytes = sum(os.path.getsize(p) for p in files_to_compress)
    master_kernel_path = "zeta-23-lean-review/Zeta23/Weil/MasterKernel.lean"
    master_kernel_bytes = os.path.getsize(master_kernel_path)
    compression_factor = float(total_original_bytes) / float(master_kernel_bytes)
    
    # Hardware Transpilation
    # 2-Qubit Clifford-Weil Kette auf ibm_fez (aus Exp 063): Tiefe 7, 3 CZ Gates
    hardware_cz_count = 3
    hardware_circuit_depth = 7
    
    results = {
        "operators": op_results,
        "compression": {
            "total_original_bytes": total_original_bytes,
            "master_kernel_bytes": master_kernel_bytes,
            "compression_factor": compression_factor,
        },
        "hardware": {
            "cz_count": hardware_cz_count,
            "circuit_depth": hardware_circuit_depth,
        }
    }
    
    raw_payload = {
        "experiment_id": "073",
        "name": "H-ULTRA-COMPRESSION-MASTER-KERNEL",
        "prereg_sha256": PREREG_SHA256,
        "results": results,
    }
    
    with open("pt_ultra_compression_073_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_payload, f, indent=2)
    print("Rohdaten erfolgreich exportiert nach pt_ultra_compression_073_raw.json")

if __name__ == "__main__":
    run()
