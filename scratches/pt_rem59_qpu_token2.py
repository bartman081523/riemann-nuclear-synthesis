"""059-QPU-Resubmit auf TOKEN2/marrakesh (Scout-Decision 4c5e5e9d…).

Addendum zum gefrorenen 059-QPU-Prereg (md5 8972ce6c…): NUR Backend und
Token wechseln (fez/TOKEN1 → marrakesh/TOKEN2); Vorhersage 529/1984,
Band, Target-Bin und Verdict-Map UNVERÄNDERT (apparatus-agnostische
Arithmetik; Readout-Unterschied via |0>-Cal diagnostiziert, kein
Toleranz-Raise). Eigene Job-ID-Datei (Fez-Job bleibt unberührt).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, "scratches")

from pt_rem59_qpu_fez import build_circuits, SHOTS, SV_MASS, TARGET_BIN

BACKEND = "ibm_marrakesh"
PREREG_PATH = "scratches/pt_rem59_qpu_t2_prereg.json"
JOB_ID_PATH = "scratches/pt_rem59_qpu_marrakesh_job_id.txt"
RAW_PATH = "scratches/pt_rem59_qpu_marrakesh_raw.json"


def freeze():
    payload = {
        "experiment": "059-qpu-marrakesh", "hypothesis": "H-REM59-Q",
        "addendum_zu": "scratches/pt_rem59_qpu_prereg.json (md5 8972ce6c…)",
        "aenderung": "NUR backend+token (fez/TOKEN1 → marrakesh/TOKEN2)",
        "backend": BACKEND, "shots": SHOTS, "target_bin": TARGET_BIN,
        "sv_mass_pred": SV_MASS,
        "band": [0.8 * SV_MASS, 1.25 * SV_MASS],
        "verdict_map": {"HELD": "S*-Masse im Band",
                        "REFUTED": "S*-Masse außerhalb",
                        "INVALID": "Cal-Ausfall oder Backend-Wechsel der Geometrie"},
        "scout_decision_md5": "4c5e5e9d688cdce246e8cbe25e783065",
    }
    doc = dict(payload)
    doc["md5"] = hashlib.md5(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    with open(PREREG_PATH, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    print("T2-PREREG-FREEZE md5:", doc["md5"])
    return doc


def submit():
    json.load(open(PREREG_PATH, encoding="utf-8"))  # Freeze-Pflicht
    if os.path.exists(JOB_ID_PATH):
        print("Job-ID existiert — Resume:",
              open(JOB_ID_PATH).read().strip())
        return open(JOB_ID_PATH).read().strip()
    from pt_token_diagnose import load_token
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform", token=load_token("IBMQ_TOKEN2"))
    backend = service.backend(BACKEND)
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    isa = pm.run(build_circuits())
    print("ISA-2q:", [isa[i].count_ops().get("cz", 0) + isa[i].count_ops().get("ecr", 0)
                      for i in range(len(isa))])
    sampler = SamplerV2(mode=backend)
    sampler.options.default_shots = SHOTS
    job = sampler.run(isa)
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
