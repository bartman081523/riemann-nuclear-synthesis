#!/usr/bin/env python3
"""EXPERIMENT 067: H-FROBENIUS-BELL-INTERFEROMETER.

Reale Quanten-Spektroskopie der Artin-Schreier Frobenius-Eigenwinkel auf ibm_fez:
- 4 Schaltkreise: Paare (0, 0), (3, 3), (2, 3), (4, 2)
- 8192 Shots pro Circuit
- Frugaler Quota-Verbrauch (< 10 Sekunden)

Disziplin:
--dry-run: Offline-Transpilation & Graphen-Check
--submit: Job-Einreichung auf ibm_fez (Speichert Job-Info in scratches/pt_frobenius_bell_067_job.json)
--fetch: Rohdaten abholen & als pt_frobenius_bell_067_raw.json ablegen (Commit VOR Auswertung!)
--eval: Strikte Auswertung gegen scratches/pt_frobenius_bell_067_prereg.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2


THETAS = {
    0: math.pi / 2,        # 90.0 deg
    1: 2 * math.pi / 5,    # 72.0 deg
    2: 2 * math.pi / 3,    # 120.0 deg
    3: math.pi / 3,        # 60.0 deg
    4: math.pi / 5         # 36.0 deg
}

PAIRS = [(0, 0), (3, 3), (2, 3), (4, 2)]


def get_token() -> str:
    with open(".env") as f:
        for line in f:
            if line.startswith("IBMQ_TOKEN="):
                return line.split("=", 1)[1].strip().strip("\"'")
    raise RuntimeError("IBMQ_TOKEN nicht in .env gefunden")


def build_circuits() -> List[QuantumCircuit]:
    circuits = []
    for a1, a2 in PAIRS:
        th1 = THETAS[a1]
        th2 = THETAS[a2]
        qc = QuantumCircuit(2, 2, name=f"frob_bell_{a1}_{a2}")
        # 1. Bell-Zustand (|00> + |11>) / sqrt(2)
        qc.h(0)
        qc.cx(0, 1)
        # 2. Frobenius-Phasenverschiebung
        qc.rz(th1, 0)
        qc.rz(-th2, 1)
        # 3. Bell-Rueckfuehrung
        qc.cx(0, 1)
        qc.h(0)
        # 4. Messung
        qc.measure([0, 1], [0, 1])
        circuits.append(qc)
    return circuits


def run_dry_run():
    print("[EXP-067] Dry-Run: Erstelle Schaltungen & transpiliere offline fuer ibm_fez...")
    circuits = build_circuits()
    token = get_token()
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend("ibm_fez")
    tc = transpile(circuits, backend=backend, optimization_level=3)
    for p, c in zip(PAIRS, tc):
        print(f"Paar {p}: Tiefe={c.depth()}, Ops={dict(c.count_ops())}")
    print("[EXP-067] Dry-Run erfolgreich: 0 Quota verbraucht.")


def submit_job():
    circuits = build_circuits()
    token = get_token()
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend("ibm_fez")
    tc = transpile(circuits, backend=backend, optimization_level=3)

    sampler = SamplerV2(backend)
    job = sampler.run(tc, shots=8192)
    job_id = job.job_id()
    print(f"[EXP-067] Job erfolgreich eingereicht! Job ID: {job_id}")

    job_info = {
        "job_id": job_id,
        "backend": backend.name,
        "circuits": len(circuits),
        "shots": 8192,
        "status": str(job.status())
    }
    with open("scratches/pt_frobenius_bell_067_job.json", "w") as f:
        json.dump(job_info, f, indent=2)
    print("Job-Info gespeichert in scratches/pt_frobenius_bell_067_job.json")


def fetch_results():
    job_file = Path("scratches/pt_frobenius_bell_067_job.json")
    if not job_file.exists():
        print("Kein aktiver Job in scratches/pt_frobenius_bell_067_job.json gefunden.")
        return
    with open(job_file) as f:
        job_info = json.load(f)

    token = get_token()
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    job = service.job(job_info["job_id"])
    status = str(job.status())
    print(f"[EXP-067] Job {job.job_id()} Status: {status}")

    if status not in ["JobStatus.DONE", "DONE"]:
        print("Job ist noch nicht fertiggestellt. Aktueller Status:", status)
        return

    result = job.result()
    raw_results = []
    for (a1, a2), pub_result in zip(PAIRS, result):
        data_c = pub_result.data.c
        counts = dict(data_c.get_counts())
        raw_results.append({
            "pair": [a1, a2],
            "counts": counts
        })

    prereg_sha256 = hashlib.sha256(open("scratches/pt_frobenius_bell_067_prereg.json", "rb").read()).hexdigest()
    raw_data = {
        "experiment_id": "EXP-067",
        "job_id": job.job_id(),
        "backend": job_info["backend"],
        "prereg_sha256": prereg_sha256,
        "results": raw_results
    }
    with open("pt_frobenius_bell_067_raw.json", "w") as f:
        json.dump(raw_data, f, indent=2)
    print("Rohdaten gespeichert in pt_frobenius_bell_067_raw.json")


def evaluate_results():
    with open("pt_frobenius_bell_067_raw.json") as f:
        raw = json.load(f)

    p00_measured = {}
    for entry in raw["results"]:
        pair_key = tuple(entry["pair"])
        counts = entry["counts"]
        total = sum(counts.values())
        c_00 = counts.get("00", 0)
        p00_measured[pair_key] = c_00 / total

    # 1. H-FBI-1: P00(0, 0) >= 0.85 und P00(3, 3) >= 0.85
    p_00 = p00_measured.get((0, 0), 0.0)
    p_33 = p00_measured.get((3, 3), 0.0)
    h1_pass = (p_00 >= 0.85 and p_33 >= 0.85)
    h1_und = (p_00 >= 0.80 and p_33 >= 0.80)
    h1_status = "CONFIRMED" if h1_pass else ("UNDETERMINED" if h1_und else "REFUTED")

    # 2. H-FBI-2: |P00(2, 3) - 0.7500| <= 0.12
    p_23 = p00_measured.get((2, 3), 0.0)
    dev_23 = abs(p_23 - 0.7500)
    h2_status = "CONFIRMED" if dev_23 <= 0.12 else "REFUTED"

    # 3. H-FBI-3: |P00(4, 2) - 0.5523| <= 0.12
    p_42 = p00_measured.get((4, 2), 0.0)
    dev_42 = abs(p_42 - 0.5523)
    h3_status = "CONFIRMED" if dev_42 <= 0.12 else "REFUTED"

    # 4. H-FBI-4: P00(2, 3) > P00(4, 2) mit Delta P >= 0.10
    delta_p = p_23 - p_42
    h4_status = "CONFIRMED" if delta_p >= 0.10 else ("UNDETERMINED" if delta_p >= 0.08 else "REFUTED")

    overall = (
        "CONFIRMED_ALL_HYPOTHESES"
        if all(s == "CONFIRMED" for s in [h1_status, h2_status, h3_status, h4_status])
        else "MIXED_OR_REFUTED"
    )

    eval_data = {
        "experiment_id": "EXP-067",
        "job_id": raw["job_id"],
        "backend": raw["backend"],
        "prereg_sha256": raw["prereg_sha256"],
        "p00_measured": {
            "(0, 0)": p_00,
            "(3, 3)": p_33,
            "(2, 3)": p_23,
            "(4, 2)": p_42
        },
        "delta_P_23_minus_42": delta_p,
        "verdicts": {
            "H-FBI-1": {"status": h1_status, "p00_00": p_00, "p00_33": p_33, "threshold": 0.85},
            "H-FBI-2": {"status": h2_status, "p00_23": p_23, "dev_from_75": dev_23, "threshold": 0.12},
            "H-FBI-3": {"status": h3_status, "p00_42": p_42, "dev_from_55": dev_42, "threshold": 0.12},
            "H-FBI-4": {"status": h4_status, "delta_P": delta_p, "threshold": 0.10}
        },
        "overall_verdict": overall
    }
    with open("pt_frobenius_bell_067_eval.json", "w") as f:
        json.dump(eval_data, f, indent=2)
    print(f"[EXP-067] Evaluation abgeschlossen: {overall}")
    print(json.dumps(eval_data, indent=2))


def main():
    parser = argparse.ArgumentParser(description="EXP-067 Frobenius Bell Runner")
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
