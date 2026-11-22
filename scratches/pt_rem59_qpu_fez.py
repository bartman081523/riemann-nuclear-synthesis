"""EXPERIMENT 059-QPU — q=2-Fingerprint Spot-Check auf ibm_fez (H-REM59-Q).
V.3-Phase, nach Freigabe. Prereg-Freeze VOR Submit; Resume-Vertrag: Job-ID
existiert → kein neuer Job, nur fetch.

Circuit (6 Qubits): initialize(Counts→Amplituden, P=100, d=64) → QFT(6,
lib, do_swaps=True) → measure_all. Kalibrier-Circuit: |0>^6 → measure
(Readout-Bias-Schaetzung). Shots 8192 (Konvention SHOTS).
Vorhersage (ex ante, aus 059-Prereg): S*-Masse 529/1984 ≈ 0.266633 an Bin
<a=32> — Bin per Aer-Kalibrierlauf mit IDENTISCHEM Circuit bestätigt
(Konventions-Check, kein Tuning: Binsuche über volle Verteilung, kein Fit).
Band: [0.8, 1.25] × Vorhersage auf der S*-Masse (Analog H-RAM-Q-Band);
Verdict: HELD / REFUTED / INVALID (Anker: Aer-Bin ≠ 32 → INVALID).
Token: NUR TOKEN1 (IBMQ_TOKEN aus .env via pt_ququint_fez).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import QFT

import pt_ram_q_asymptotik as ra
import pt_ququint_fez as fez

P, D, Q = 100, 64, 2
SHOTS = 8192
TARGET_BIN = D // Q  # a = 32
PREREG_PATH = "scratches/pt_rem59_qpu_prereg.json"
JOB_ID_PATH = "scratches/pt_rem59_qpu_job_id.txt"
RAW_PATH = "scratches/pt_rem59_qpu_raw.json"

SV_MASS = 529 / 1984  # ex ante aus 059-Prereg (G(32) = -23, Σn² = 31)


def build_circuits():
    primes = ra.numpy_primes(P)
    cnt = np.zeros(D)
    for pp in primes:
        cnt[int(pp) % D] += 1.0
    psi0 = cnt / math.sqrt(float((cnt ** 2).sum()))
    qc = QuantumCircuit(6, 6)
    qc.initialize(psi0, range(6))
    qc.append(QFT(6), range(6))
    qc.measure(range(6), range(6))
    cal = QuantumCircuit(6, 6)
    cal.measure(range(6), range(6))
    return [qc, cal]


def calibrate():
    """Aer-Check mit IDENTISCHEM Circuit (QFT-lib): wo liegt die S*-Masse?"""
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    circuits = build_circuits()
    sim = AerSimulator(method="statevector")
    probs = {}
    for i, qc in enumerate(circuits):
        qc2 = qc.remove_final_measurements(inplace=False)
        qc2 = transpile(qc2, backend=sim, optimization_level=1)
        qc2.save_statevector()
        sv = sim.run(qc2).result().get_statevector()
        pv = np.abs(np.asarray(sv)) ** 2
        probs[i] = pv
    mass32 = float(probs[0][TARGET_BIN])
    top = sorted(enumerate(probs[0]), key=lambda t: -t[1])[:4]
    print("Aer S*-Masse Bin 32:", mass32, "vs 529/1984 =", SV_MASS)
    print("Top-4 Bins:", [(int(a), round(float(b), 6)) for a, b in top])
    print("Cal |0>-Masse Bin 0:", float(probs[1][0]))
    return mass32


def freeze():
    payload = {
        "experiment": "059-qpu-fez", "hypothesis": "H-REM59-Q",
        "circuit": "initialize(P=100,d=64) + QFT(6,lib) + measure_all; +|0>-cal",
        "backend": "ibm_fez", "shots": SHOTS,
        "target_bin": TARGET_BIN, "sv_mass_pred": SV_MASS,
        "band": [0.8 * SV_MASS, 1.25 * SV_MASS],
        "verdict_map": {"HELD": "S*-Masse im Band",
                        "REFUTED": "S*-Masse außerhalb",
                        "INVALID": "Aer-Bin ≠ 32 oder Cal-Ausfall"},
        "token": "TOKEN1-only (IBMQ_TOKEN)",
    }
    doc = dict(payload)
    doc["md5"] = hashlib.md5(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    with open(PREREG_PATH, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    print("QPU-PREREG-FREEZE md5:", doc["md5"])
    return doc


def submit():
    doc = json.load(open(PREREG_PATH, encoding="utf-8"))
    if os.path.exists(JOB_ID_PATH):
        print("Job-ID existiert — Resume, kein neuer Submit:",
              open(JOB_ID_PATH).read().strip())
        return open(JOB_ID_PATH).read().strip()
    token = fez.load_token()
    service = fez.get_service(token)
    backend = fez.get_backend(service)
    print("backend:", backend.name)
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    isa = pm.run(build_circuits())
    from qiskit_ibm_runtime import SamplerV2
    sampler = SamplerV2(mode=backend)
    sampler.options.default_shots = SHOTS
    job = sampler.run(isa)
    jid = job.job_id() if callable(job.job_id) else job.job_id
    with open(JOB_ID_PATH, "w", encoding="utf-8") as fh:
        fh.write(jid + "\n")
    print("submitted:", jid)
    return jid


def fetch():
    jid = open(JOB_ID_PATH).read().strip()
    service = fez.get_service(fez.load_token())
    job = service.job(jid)
    print("status:", job.status())
    res = job.result()
    out = []
    for i in range(2):
        qd = res[i].data
        c = qd.c if hasattr(qd, "c") else qd["c"]
        counts = c.get_counts()
        out.append({"counts": {k: int(v) for k, v in counts.items()}})
    with open(RAW_PATH, "w", encoding="utf-8") as fh:
        json.dump({"job_id": jid, "circuits": out}, fh, indent=2)
    print("raw geschrieben:", RAW_PATH)
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["calibrate", "freeze", "submit", "fetch"])
    args = ap.parse_args()
    {"calibrate": calibrate, "freeze": freeze,
     "submit": submit, "fetch": fetch}[args.cmd]()


if __name__ == "__main__":
    main()
