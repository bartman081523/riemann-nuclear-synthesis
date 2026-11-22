"""QUQUINT-F4-Resubmit auf TOKEN2/marrakesh (Scout-Decision 4c5e5e9d…).

Addendum zum gefrorenen 032-Prereg (pt_ququint_fez_prereg.json, md5
committet): NUR backend+token (fez/TOKEN1 → marrakesh/TOKEN2); Circuits
(Phase-2-Reihenfolge), Shots 8192, DD-XX, Witness-Schwellen und
Decision-Rule UNVERÄNDERT. Eigene Job-ID/Raw-Pfade (Fez-Job unberührt).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_ququint_fez as qf
from pt_ququint_prereg import load_frozen_prereg, N_SHOTS

BACKEND = "ibm_marrakesh"
PREREG_PATH = "scratches/pt_ququint_f4_t2_prereg.json"
JOB_ID_PATH = "scratches/pt_ququint_f4_marrakesh_job_id.txt"
RAW_PATH = "scratches/pt_ququint_f4_marrakesh_raw.json"


def freeze():
    base = load_frozen_prereg()
    payload = {
        "experiment": "032-ququint-fez-marrakesh",
        "addendum_zu": {"prereg": "pt_ququint_fez_prereg.json",
                        "md5": base.get("md5")},
        "aenderung": "NUR backend+token (fez/TOKEN1 → marrakesh/TOKEN2)",
        "backend": BACKEND, "n_circuits": 12, "n_shots": N_SHOTS,
        "scout_decision_md5": "4c5e5e9d688cdce246e8cbe25e783065",
    }
    doc = dict(payload)
    doc["md5"] = hashlib.md5(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    with open(PREREG_PATH, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    print("F4-T2-PREREG-FREEZE md5:", doc["md5"])
    return doc


def submit():
    json.load(open(PREREG_PATH, encoding="utf-8"))
    if os.path.exists(JOB_ID_PATH):
        print("Job-ID existiert — Resume:",
              open(JOB_ID_PATH).read().strip())
        return open(JOB_ID_PATH).read().strip()
    from pt_token_diagnose import load_token
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform", token=load_token("IBMQ_TOKEN2"))
    backend = service.backend(BACKEND)
    isa, report = qf.isa_batch(backend)
    print("ISA-2q total:", report["total_two_q"])
    json.dump(report, open(
        "scratches/pt_ququint_f4_marrakesh_isa.json", "w"), indent=1)
    sampler = SamplerV2(mode=backend)
    job = qf.submit(sampler, isa, shots=N_SHOTS)
    jid = job.job_id() if callable(job.job_id) else job.job_id
    with open(JOB_ID_PATH, "w", encoding="utf-8") as fh:
        fh.write(jid + "\n")
    print("submitted:", jid)
    return jid


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["freeze", "submit"])
    args = ap.parse_args()
    {"freeze": freeze, "submit": submit}[args.cmd]()


if __name__ == "__main__":
    main()
