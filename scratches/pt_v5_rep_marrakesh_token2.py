"""046-marrakesh-Bein (H-V5R) auf TOKEN2 (Scout-Decision 4c5e5e9d…).

Addendum zum gefrorenen 046-Prereg (pt_v5_kingston_rep_prereg.json):
neues Bein 'marrakesh' mit bit-identischer Mechanik (Estimator,
resilience 1, DD-XX, 8192 Shots, EIN est.run mit 3 Pubs, FEZ_PARAMS);
Bänder/Schwellen und Eval-Logik UNVERÄNDERT. Eigene Job-ID/Raw-Pfade
(Fez/Kingston-Beine unberührt).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_v5_kingston as v5
import pt_v5_kingston_rep as rep
from qiskit_ibm_runtime import Estimator

BACKEND = "ibm_marrakesh"
PREREG_PATH = "scratches/pt_v5_rep_marrakesh_prereg.json"
JOBID_PATH = "scratches/pt_v5_kingston_rep_marrakesh_job_id.txt"
RAW_PATH = "scratches/pt_v5_kingston_rep_marrakesh_raw.json"
ISA_PATH = "scratches/pt_v5_kingston_rep_marrakesh_isa.json"


def freeze():
    base_md5 = rep.prereg_md5()
    payload = {
        "experiment": rep.EXPERIMENT, "bein": "marrakesh",
        "addendum_zu": {"prereg": rep.PREREG_PATH, "md5": base_md5},
        "aenderung": "neues Bein marrakesh/TOKEN2, Mechanik bit-identisch",
        "backend": BACKEND,
        "scout_decision_md5": "4c5e5e9d688cdce246e8cbe25e783065",
    }
    doc = dict(payload)
    doc["md5"] = hashlib.md5(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    with open(PREREG_PATH, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    print("046-T2-PREREG-FREEZE md5:", doc["md5"])
    return doc


def submit():
    json.load(open(PREREG_PATH, encoding="utf-8"))
    if os.path.exists(JOBID_PATH):
        print("Job-ID existiert — Resume:",
              open(JOB_ID_PATH).read().strip())
        return open(JOB_ID_PATH).read().strip()
    from pt_token_diagnose import load_token
    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform", token=load_token("IBMQ_TOKEN2"))
    backend = service.backend(BACKEND)
    ops = v5.build_operators()
    isa = v5.isa_ansatz_for(backend)
    counts = v5.isa_gate_counts(isa)
    bound = isa.assign_parameters(v5.FEZ_PARAMS)
    pubs = [(bound, v5._laid_out(ops["ops_real"], isa)),
            (bound, v5._laid_out(ops["ops_diag"], isa)),
            (bound, v5._laid_out(ops["ops_imag"], isa))]
    est = Estimator(mode=backend)
    est.options.resilience_level = 1
    est.options.dynamical_decoupling.enable = True
    est.options.dynamical_decoupling.sequence_type = "XX"
    est.options.default_shots = v5.SHOTS
    job = est.run(pubs)
    jid = job.job_id() if callable(job.job_id) else job.job_id
    with open(JOBID_PATH, "w", encoding="utf-8") as fh:
        fh.write(jid + "\n")
    with open(ISA_PATH, "w", encoding="utf-8") as fh:
        json.dump(counts, fh, indent=1)
    print("submitted:", jid, "backend:", backend.name)
    return jid


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["freeze", "submit"])
    args = ap.parse_args()
    {"freeze": freeze, "submit": submit}[args.cmd]()


if __name__ == "__main__":
    main()
