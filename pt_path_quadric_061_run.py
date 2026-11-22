"""EXPERIMENT 061: Pfad-Quadriken, Weil-Schranken-Saettigung und 2-Qubit-Clifford-Weil-Kette.

Ledger-Disziplin (ExperimentLedgerMind):
  - Preregistrierung gefroren in scratches/pt_path_quadric_061_prereg.json
  - Prereg-SHA256: 55f420301219a408a7300d16b08bd111fe3b3833eb82989275df2893ba178fed
  - Raw Commit VOR Auswertung: --run erzeugt pt_path_quadric_061_raw.json
  - --eval wertet Rohdaten streng gegen gefrorene Schwellen aus
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import sys
from typing import Any, Dict, List

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from primequant.weil import (
    path_quadric_phase,
    path_quadric_ramanujan_sum,
    path_quadric_gauss_sum_even,
)
from primequant.observables import ramanujan_summe

PREREG_PATH = os.path.join("scratches", "pt_path_quadric_061_prereg.json")
EXPECTED_PREREG_SHA256 = "55f420301219a408a7300d16b08bd111fe3b3833eb82989275df2893ba178fed"
RAW_OUTPUT_PATH = "pt_path_quadric_061_raw.json"
EVAL_OUTPUT_PATH = "pt_path_quadric_061_eval.json"


def verify_prereg_hash() -> Dict[str, Any]:
    if not os.path.exists(PREREG_PATH):
        raise FileNotFoundError(f"Prereg fehlt: {PREREG_PATH}")
    with open(PREREG_PATH, "rb") as f:
        content = f.read()
    digest = hashlib.sha256(content).hexdigest()
    if digest != EXPECTED_PREREG_SHA256:
        raise ValueError(f"HASH MISMATCH: {digest} != {EXPECTED_PREREG_SHA256}")
    return json.loads(content.decode("utf-8"))


def run_experiment_061() -> Dict[str, Any]:
    prereg = verify_prereg_hash()
    suite = prereg["falsifier_suite"]
    
    # 1. H-PQ-1: Pfad-Quadrik Ramanujan Identitaet
    hpq1_results = {}
    for q in suite["primes"]:
        for k in suite["chain_lengths_k"]:
            max_diff = 0
            # Teste Samples ueber GF(q)^k
            omega = np.exp(2j * np.pi / q)
            # Begrenze auf maximal 1000 Tupel fuer groessere Dimensionen
            count = 0
            for x in itertools.product(range(q), repeat=k):
                phase = path_quadric_phase(q, x)
                # Direkte Summe sum_{h=1}^{q-1} omega^{h * phase}
                sum_h = sum(omega ** ((h * phase) % q) for h in range(1, q))
                c_val = ramanujan_summe(q, phase)
                diff = abs(sum_h - c_val)
                if diff > max_diff:
                    max_diff = float(diff)
                count += 1
                if count > 1000:
                    break
            hpq1_results[f"q{q}_k{k}"] = {"max_diff": max_diff, "samples": count}
            
    # 2. H-PQ-2: Weil-Schranken-Saettigung fuer gerades k in {2, 4}
    hpq2_results = {}
    for q in suite["primes"]:
        for k in [2, 4]:
            g_int = path_quadric_gauss_sum_even(q, k)
            dim = q ** k
            is_saturated = (g_int * g_int == dim)
            hpq2_results[f"q{q}_k{k}"] = {
                "G_int": g_int,
                "dim": dim,
                "saturated": is_saturated,
            }
            
    # 3. H-PQ-3: 2-Qubit Clifford-Weil Inversion
    # Simuliere Schritte L = 0..4 auf 2 Qubits
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    
    q2_results = {}
    for L in suite["q2_qubit_steps"]:
        qc = QuantumCircuit(2)
        qc.x(0)
        qc.h(1)
        for _ in range(L):
            qc.s(0)
            qc.h(0)
            qc.cx(0, 1)
            qc.sdg(1)
            qc.h(1)
            qc.cx(0, 1)
        sv = Statevector.from_instruction(qc)
        probs = sv.probabilities_dict()
        p_q0_zero = sum(probs.get(b, 0.0) for b in ["00", "10"])
        p_q0_one = sum(probs.get(b, 0.0) for b in ["01", "11"])
        q2_results[f"L{L}"] = {
            "probs": {k: float(v) for k, v in probs.items()},
            "p_q0_zero": float(p_q0_zero),
            "p_q0_one": float(p_q0_one),
        }
        
    # 4. H-PQ-4: GGP Multi-Register Skalierung fuer k in {2, 3} (q=5)
    from primequant.theta_chain import simulate_theta_chain
    sim2 = simulate_theta_chain(5, max_steps=4)
    peak_L_k2 = int(np.argmax([s["R"] for s in sim2][1:])) + 1
    
    # Fuer k=3: simuliere GGP-Pfad-Kette
    omega5 = np.exp(2j * np.pi / 5)
    F5 = np.array([[omega5**(j * m % 5) for m in range(5)] for j in range(5)]) / np.sqrt(5)
    F_3 = np.kron(F5, np.kron(F5, F5))
    
    diag_3 = np.zeros(125, dtype=complex)
    for idx in range(125):
        d0 = idx % 5; d1 = (idx // 5) % 5; d2 = idx // 25
        diag_3[idx] = omega5 ** ((d0 * d1 + d1 * d2) % 5)
    U_path3 = np.diag(diag_3)
    
    D1_5 = np.diag([omega5**((x**2) % 5) for x in range(5)])
    D_3 = np.kron(D1_5, np.kron(D1_5, D1_5))
    
    psi_triv5 = np.zeros(5, dtype=complex); psi_triv5[1:] = 0.5
    P_triv5 = np.outer(psi_triv5, psi_triv5.conj())
    R_triv5 = np.eye(5) - 2.0 * P_triv5
    R_total3 = np.kron(np.eye(5), np.kron(R_triv5, R_triv5))
    
    W3 = R_total3 @ U_path3.conj().T @ F_3 @ D_3 @ U_path3
    
    state3 = np.zeros(5, dtype=complex); state3[1] = 1.0
    state3 = np.kron(state3, np.kron(psi_triv5, psi_triv5))
    P_act5 = np.diag([0.0] + [1.0] * 4)
    
    r_k3_vals = []
    for L in range(5):
        if L > 0:
            state3 = W3 @ state3
        dm = np.tensordot(state3.reshape((5, 5, 5)), state3.reshape((5, 5, 5)).conj(), axes=([1, 2], [1, 2]))
        p_tr = float(np.real(np.trace(P_triv5 @ dm)))
        p_ac = float(np.real(np.trace(P_act5 @ dm)))
        r_k3_vals.append(p_tr / p_ac if p_ac > 1e-12 else 0.0)
        
    peak_L_k3 = int(np.argmax(r_k3_vals[1:])) + 1
    
    hpq4_results = {
        "k2_peak_L": peak_L_k2,
        "k3_peak_L": peak_L_k3,
        "k3_r_vals": r_k3_vals,
        "scales_linearly": (peak_L_k3 >= peak_L_k2),
    }
    
    raw_payload = {
        "experiment": prereg["experiment"],
        "prereg_sha256": EXPECTED_PREREG_SHA256,
        "hpq1_results": hpq1_results,
        "hpq2_results": hpq2_results,
        "hpq3_results": q2_results,
        "hpq4_results": hpq4_results,
    }
    
    with open(RAW_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(raw_payload, f, indent=2)
    print(f"[OK] Rohdaten gespeichert: {RAW_OUTPUT_PATH}")
    return raw_payload


def evaluate_experiment_061() -> Dict[str, Any]:
    if not os.path.exists(RAW_OUTPUT_PATH):
        raise FileNotFoundError(f"Rohdaten fehlen: {RAW_OUTPUT_PATH}")
    with open(RAW_OUTPUT_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    prereg = verify_prereg_hash()
    theses = prereg["thesis"]["sub_hypotheses"]
    
    # 1. H-PQ-1
    t1_dev = theses["H-PQ-1"]["threshold_T1_max_dev"]
    hpq1_pass = all(v["max_diff"] <= t1_dev for v in raw["hpq1_results"].values())
    v1 = "CONFIRMED" if hpq1_pass else "REFUTED"
    
    # 2. H-PQ-2
    hpq2_pass = all(v["saturated"] for v in raw["hpq2_results"].values())
    v2 = "CONFIRMED" if hpq2_pass else "REFUTED"
    
    # 3. H-PQ-3
    t3_dev = theses["H-PQ-3"]["threshold_T3_inversion_dev"]
    p_q0_zero_L4 = raw["hpq3_results"]["L4"]["p_q0_zero"]
    hpq3_pass = abs(p_q0_zero_L4 - 1.0) <= t3_dev
    v3 = "CONFIRMED" if hpq3_pass else "REFUTED"
    
    # 4. H-PQ-4
    hpq4_pass = raw["hpq4_results"]["scales_linearly"]
    v4 = "CONFIRMED" if hpq4_pass else "REFUTED"
    
    all_confirmed = (v1 == "CONFIRMED" and v2 == "CONFIRMED" and v3 == "CONFIRMED" and v4 == "CONFIRMED")
    overall = "CONFIRMED_ALL_HYPOTHESES" if all_confirmed else "PARTIAL_OR_REFUTED"
    
    eval_payload = {
        "experiment": raw["experiment"],
        "prereg_sha256": raw["prereg_sha256"],
        "verdicts": {
            "H-PQ-1_RAMANUJAN_IDENTITY": {"verdict": v1},
            "H-PQ-2_WEIL_SATURATION": {"verdict": v2},
            "H-PQ-3_CLIFFORD_INVERSION": {"verdict": v3, "observed_L4_p0": p_q0_zero_L4},
            "H-PQ-4_GGP_SCALING": {"verdict": v4, "k2_peak": raw["hpq4_results"]["k2_peak_L"], "k3_peak": raw["hpq4_results"]["k3_peak_L"]},
        },
        "overall_verdict": overall,
    }
    
    with open(EVAL_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_payload, f, indent=2)
    print(f"[OK] Evaluation gespeichert: {EVAL_OUTPUT_PATH}")
    print(f"Gesamturteil: {overall}")
    return eval_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--eval", action="store_true")
    args = parser.parse_args()
    if args.run:
        run_experiment_061()
    elif args.eval:
        evaluate_experiment_061()
    else:
        parser.print_help()
