#!/usr/bin/env python3
"""EXPERIMENT 063: H-CLIFFORD-WEIL-QPU-RESONANCE.

Frugaler 2-Qubit Clifford-Weil Walk & Stepanov-Resonanz auf ibm_fez:
- 4 Schaltkreise (L in {1, 2, 3, 4})
- Tiefe <= 7, insgesamt nur 3 CZ-Gates
- 8192 Shots pro Circuit
- Geschätzter Quota-Verbrauch: < 2.5 Sekunden von 600s frei.

Disziplin:
1. --dry-run: Offline-Transpilation & Graphen-Check
2. --submit: Job-Einreichung auf ibm_fez
3. --fetch: Rohdaten abholen & als pt_clifford_weil_063_raw.json ablegen
4. --eval: Strikte Auswertung gegen scratches/pt_clifford_weil_063_prereg.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2


def get_token() -> str:
    with open(".env") as f:
        for line in f:
            if line.startswith("IBMQ_TOKEN="):
                return line.split("=", 1)[1].strip().strip("\"'")
    raise RuntimeError("IBMQ_TOKEN nicht in .env gefunden")


def build_circuits() -> List[QuantumCircuit]:
    circuits = []
    for L in [1, 2, 3, 4]:
        qc = QuantumCircuit(2, 2, name=f"clifford_weil_L{L}")
        qc.h(0)
        qc.h(1)
        for _ in range(L):
            qc.s(0)
            qc.cz(0, 1)
            qc.h(0)
        qc.measure([0, 1], [0, 1])
        circuits.append(qc)
    return circuits


def run_dry_run():
    print("[EXP-063] Dry-Run: Erstelle Schaltungen & transpiliere offline...")
    circuits = build_circuits()
    token = get_token()
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend("ibm_fez")
    tc = transpile(circuits, backend=backend, optimization_level=3)
    for L, c in zip([1, 2, 3, 4], tc):
        print(f"L={L}: Tiefe={c.depth()}, Ops={dict(c.count_ops())}")
    print("[EXP-063] Dry-Run erfolgreich: 0 Quota verbraucht.")


def submit_job():
    circuits = build_circuits()
    token = get_token()
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend("ibm_fez")
    tc = transpile(circuits, backend=backend, optimization_level=3)
    
    sampler = SamplerV2(backend)
    job = sampler.run(tc, shots=8192)
    job_id = job.job_id()
    print(f"[EXP-063] Job erfolgreich eingereicht! Job ID: {job_id}")
    
    job_info = {
        "job_id": job_id,
        "backend": backend.name,
        "circuits": len(circuits),
        "shots": 8192,
        "status": str(job.status())
    }
    with open("scratches/pt_clifford_weil_063_job.json", "w") as f:
        json.dump(job_info, f, indent=2)
    print("Job-Info gespeichert in scratches/pt_clifford_weil_063_job.json")


def fetch_results():
    job_file = Path("scratches/pt_clifford_weil_063_job.json")
    if not job_file.exists():
        print("Kein aktiver Job in scratches/pt_clifford_weil_063_job.json gefunden.")
        return
    with open(job_file) as f:
        job_info = json.load(f)
    
    token = get_token()
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    job = service.job(job_info["job_id"])
    status = str(job.status())
    print(f"[EXP-063] Job {job.job_id()} Status: {status}")
    
    if status != "JobStatus.DONE" and status != "DONE":
        print("Job ist noch nicht fertiggestellt. Aktueller Status:", status)
        return

    result = job.result()
    raw_counts = []
    # SamplerV2 Rückgabe verarbeiten
    for i, pub_result in enumerate(result):
        # bitstrings von 'c'
        data_c = pub_result.data.c
        counts = dict(data_c.get_counts())
        raw_counts.append({
            "L": i + 1,
            "counts": counts
        })

    prereg_sha256 = hashlib.sha256(open("scratches/pt_clifford_weil_063_prereg.json", "rb").read()).hexdigest()
    raw_data = {
        "experiment_id": "EXP-063",
        "job_id": job.job_id(),
        "backend": job_info["backend"],
        "prereg_sha256": prereg_sha256,
        "results": raw_counts
    }
    with open("pt_clifford_weil_063_raw.json", "w") as f:
        json.dump(raw_data, f, indent=2)
    print("Rohdaten gespeichert in pt_clifford_weil_063_raw.json")


def evaluate_results():
    with open("pt_clifford_weil_063_raw.json") as f:
        raw = json.load(f)
    
    # Auswertung der Randverteilung auf q1
    # Bitstring in Qiskit: 'c[1] c[0]' -> bit 1 ist links, bit 0 ist rechts
    # Bei Measure([0, 1], [0, 1]): bit 0 -> c[0], bit 1 -> c[1]
    # Bitstring '00' -> q1=0, q0=0
    # Bitstring '01' -> q1=0, q0=1
    # Bitstring '10' -> q1=1, q0=0
    # Bitstring '11' -> q1=1, q0=1
    # q1 = 0 entspricht bitstrings mit erster Ziffer '0' (d.h. '00' und '01')
    p_q1_zero = {}
    for entry in raw["results"]:
        L = entry["L"]
        counts = entry["counts"]
        total = sum(counts.values())
        c_q1_0 = counts.get("00", 0) + counts.get("01", 0)
        p_q1_zero[L] = c_q1_0 / total

    # 1. H-CW-1: P_{L=2}(q1=0) >= 0.85
    p_L2 = p_q1_zero.get(2, 0.0)
    h1_status = "CONFIRMED" if p_L2 >= 0.85 else ("UNDETERMINED" if p_L2 >= 0.80 else "REFUTED")

    # 2. H-CW-2: max |P_L - 0.50| <= 0.12 fuer L in {1, 3, 4}
    devs = [abs(p_q1_zero[L] - 0.50) for L in [1, 3, 4] if L in p_q1_zero]
    max_dev = max(devs) if devs else 0.0
    h2_status = "CONFIRMED" if max_dev <= 0.12 else ("UNDETERMINED" if max_dev <= 0.15 else "REFUTED")

    # 3. H-CW-3: Delta P >= 0.35
    mean_non_res = sum(p_q1_zero[L] for L in [1, 3, 4]) / 3.0
    delta_p = p_L2 - mean_non_res
    h3_status = "CONFIRMED" if delta_p >= 0.35 else ("UNDETERMINED" if delta_p >= 0.30 else "REFUTED")

    overall = (
        "CONFIRMED_ALL_HYPOTHESES"
        if (h1_status == "CONFIRMED" and h2_status == "CONFIRMED" and h3_status == "CONFIRMED")
        else "MIXED_OR_REFUTED"
    )

    eval_data = {
        "experiment_id": "EXP-063",
        "job_id": raw["job_id"],
        "prereg_sha256": raw["prereg_sha256"],
        "p_q1_zero": p_q1_zero,
        "delta_P": delta_p,
        "verdicts": {
            "H-CW-1": {"status": h1_status, "value": p_L2},
            "H-CW-2": {"status": h2_status, "max_dev": max_dev},
            "H-CW-3": {"status": h3_status, "delta_P": delta_p},
        },
        "overall_verdict": overall,
    }
    with open("pt_clifford_weil_063_eval.json", "w") as f:
        json.dump(eval_data, f, indent=2)
    print(f"[EXP-063] Evaluation abgeschlossen: {overall}")
    print(json.dumps(eval_data, indent=2))


def main():
    parser = argparse.ArgumentParser(description="EXP-063 Clifford-Weil Runner")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--eval", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        run_dry_run()
    elif args.submit:
        submit_job()
    elif args.fetch:
        fetch_results()
    elif args.eval:
        evaluate_results()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
