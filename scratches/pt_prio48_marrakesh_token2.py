"""055-Marrakesh-Port auf TOKEN2 (Scout-Decision 4c5e5e9d…).

Addendum zum gefrorenen 055-Prereg (md5 b7afc42c…): NUR backend+token
(fez/TOKEN1 → marrakesh/TOKEN2) + Geometrie-Port (Forced-Slot-Enumeration
auf der Marrakesh-Kopplungsmap, gleiche Algorithmen: layout_slots,
slot_assignment start=1, Skip-Forward bei Ceiling). S1-Bit-Anker (fez)
ersetzt durch Marrakesh-Gate-Selbst-Anker (Gate-Crosscheck wie
K2-Präzedenz); Vorhersagen, Bänder, Eval-Gesetz, Shots, DD-XX
UNVERÄNDERT. Eigene Report-/Gate-/Job-/Raw-Pfade (Fez-Artefakte unberührt).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_ram_q_hardware3_aer as h3a
import pt_ram_q_prio48 as p48
import pt_ram_q_prio48_qpu as qpu

BACKEND = "ibm_marrakesh"
PREREG_PATH = "scratches/pt_prio48_t2_prereg.json"
REPORT_PATH = "scratches/pt_ram_q_prio48_marrakesh_isa_report.json"
GATE_PATH = "scratches/pt_ram_q_prio48_marrakesh_isa_gate.json"
JOB_ID_PATH = "scratches/pt_ram_q_prio48_marrakesh_job_id.txt"
RAW_PATH = "scratches/pt_ram_q_prio48_marrakesh_raw.json"


def freeze():
    base_md5 = p48.payload_md5(
        {k: v for k, v in json.load(
            open("pt_ram_q_prio48_prereg.json", encoding="utf-8")).items()
         if k != "md5"})
    payload = {
        "experiment": p48.EXPERIMENT, "bein": "marrakesh",
        "addendum_zu": {"prereg": "pt_ram_q_prio48_prereg.json",
                        "md5": base_md5},
        "aenderung": ("backend+token fez/TOKEN1 → marrakesh/TOKEN2; "
                      "Forced-Geometrie auf Marrakesh-Map neu enumeriert "
                      "(gleiche Algorithmen); S1-Anker → Gate-Selbst-Anker"),
        "backend": BACKEND, "n_circuits": p48.N_CIRCUITS,
        "shots": qpu.SHOTS,
        "scout_decision_md5": "4c5e5e9d688cdce246e8cbe25e783065",
    }
    doc = dict(payload)
    doc["md5"] = hashlib.md5(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    with open(PREREG_PATH, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    print("055-T2-PREREG-FREEZE md5:", doc["md5"])
    return doc


def backend_token2():
    from pt_token_diagnose import load_token
    from qiskit_ibm_runtime import QiskitRuntimeService
    return QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=load_token("IBMQ_TOKEN2")).backend(BACKEND)


def gate():
    json.load(open(PREREG_PATH, encoding="utf-8"))
    if os.path.exists(REPORT_PATH) and os.path.exists(GATE_PATH):
        print("Gate existiert — nichts überschrieben")
        return json.load(open(GATE_PATH, encoding="utf-8"))
    backend = backend_token2()
    pts, cal, _ladder = p48.eval_grid()
    circuits = h3a.build_hardware_circuit_set(pts=pts, cal=cal)
    assert len(circuits) == p48.N_CIRCUITS, len(circuits)
    _tci, _totals, report, gate = qpu.transpile_forced(
        backend, circuits, s1_report_path=None)
    report["addendum"] = ("S1-Bit-Anker abgeschaltet (fez-spezifisch); "
                          "Gate-Selbst-Anker via Crosscheck vor Submit")
    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    with open(GATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(gate, fh, indent=1)
    print("Gate geschrieben: total_2q %d, max %d"
          % (gate["total_two_q"], gate["max_two_q"]))
    return gate


def submit():
    json.load(open(PREREG_PATH, encoding="utf-8"))
    gate_doc = json.load(open(GATE_PATH, encoding="utf-8"))
    if os.path.exists(JOB_ID_PATH):
        print("Job-ID existiert — Resume:",
              open(JOB_ID_PATH).read().strip())
        return open(JOB_ID_PATH).read().strip()
    backend = backend_token2()
    pts, cal, _ladder = p48.eval_grid()
    circuits = h3a.build_hardware_circuit_set(pts=pts, cal=cal)
    tci, totals, _rep, _g = qpu.transpile_forced(
        backend, circuits, s1_report_path=None)
    for c, tc in zip(circuits, tci):
        ops = {str(gn): int(cn) for gn, cn in tc.count_ops().items()}
        from pt_ram_q6_kingston_isa_stage import count_2q
        entry = gate_doc["per_circuit_two_q"][c["name"]]
        if entry["ops"] != ops or int(entry["n_2q"]) != count_2q(ops):
            raise AssertionError("Gate-Stale: %s" % c["name"])
    from qiskit_ibm_runtime import SamplerV2
    sampler = SamplerV2(mode=backend)
    job = qpu.submit_job(sampler, tci)
    jid = job.job_id() if callable(job.job_id) else job.job_id
    with open(JOB_ID_PATH, "w", encoding="utf-8") as fh:
        fh.write(jid + "\n")
    print("submitted:", jid, "(160 circuits, 8192 shots)")
    return jid


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["freeze", "gate", "submit"])
    args = ap.parse_args()
    {"freeze": freeze, "gate": gate, "submit": submit}[args.cmd]()


if __name__ == "__main__":
    main()
