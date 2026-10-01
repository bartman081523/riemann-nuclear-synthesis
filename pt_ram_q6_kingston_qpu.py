# -*- coding: utf-8 -*-
"""EXPERIMENT 050 (H-RAM-Q-6 Leg D1 Substrat): EIN Kingston-Job (TOKEN2)
+ RAW-Fetch — der EINZIGE QPU-Griff des D1-Beins.

Identische Form wie das 11d-Fez-Bein (pt_ram_q_hardware3_qpu), mit
genau drei Untercheidungen:
  1. Backend ibm_kingston, Service via pt_v5_kingston._make_service
     (IBMQ_TOKEN2, instance "open-instance").  TOKEN1 WIRD NIE GELESEN.
  2. Die transpile-Totals (isa_2q_total/isa_2q_max) im Raw kommen aus
     dem VOR der Submission committed Gate-Artefakt
     pt_ram_q6_kingston_isa_gate.json — NIE hartkodiert (die Fez-
     Session-Totals des 11d-Reports sind hier NICHT gueltig).
  3. ISA-Gate-Kreuzcheck: die lokale Transpile (identischer Passmanager)
     wird Zelle-fuer-Zelle gegen das Gate verglichen; jede Abweichung
     bricht VOR der Submission ab (Gate-stale -> Gate neu erzeugen +
     committen).

Disziplin wie 11d: job_id sofort persistiert (resume contract), raw
counts_md5, COMMIT VOR jeder Auswertung — kein kappa/ratio/gamma/verdict
hier.
"""
import hashlib
import json
import os
import time
from datetime import datetime, timezone

from qiskit_ibm_runtime import SamplerV2
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

import pt_ram_q6_kingston as k6
import pt_ram_q6_kingston_isa_stage as stage6
import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_aer as h3a

BACKEND_NAME = k6.BACKEND_NAME
TRANSPILE_SEED = h3a.TRANSPILE_SEED  # 7 — identisch zum gefrorenen run_config
JOB_ID_PATH, RAW_PATH = k6.JOB_ID_PATH, k6.RAW_PATH
POLL_SECONDS = 20
POLL_MAX_S = 6 * 3600


def load_token():
    """TOKEN2 — pt_v5_kingston.load_token liest IBMQ_TOKEN2 aus .env."""
    import pt_v5_kingston as v5k
    return v5k.load_token()


def get_service(token=None):
    import pt_v5_kingston as v5k
    return v5k._make_service()


def get_backend(service):
    return service.backend(BACKEND_NAME)


def isa_circuits(backend, circuits, isa_gate=stage6.OUT_PATH):
    """Passmanager des gefrorenen run_config + Gate-Kreuzcheck (Zelle)."""
    with open(isa_gate, encoding="utf-8") as fh:
        gate = json.load(fh)
    k6.validate_isa_gate(gate)
    pm = generate_preset_pass_manager(
        backend=backend, optimization_level=3, seed_transpiler=7)
    tci = list(pm.run([c["circuit"] for c in circuits]))
    for c, tc in zip(circuits, tci):
        ops = {str(gn): int(cn) for gn, cn in tc.count_ops().items()}
        gate_entry = gate["per_circuit_two_q"][c["name"]]
        if gate_entry["ops"] != ops:
            raise AssertionError(
                "ISA-Gate-Stale: ops divergieren fuer %s (gate-local %r != "
                "aktuell %r)" % (c["name"], gate_entry["ops"], ops))
        if gate_entry["n_2q"] != stage6.count_2q(ops):
            raise AssertionError("ISA-Gate-Stale: n_2q divergiert fuer %s"
                                 % c["name"])
    totals = {"optimization_level": 3, "seed_transpiler": 7,
              "isa_2q_total": int(gate["total_two_q"]),
              "isa_2q_max": int(gate["max_two_q"])}
    return tci, totals


def counts_md5(counts_list):
    """Kanonische Counts-Serialisierung -> md5 (identisch zum 11d-Format)."""
    payload = json.dumps(counts_list, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.md5(payload).hexdigest()


def submit_job(sampler, isa_circuits_list, shots=None):
    """EIN SamplerV2-Job: alle 116 Circuits, default_shots, DD XX."""
    shots = int(h3.SHOTS if shots is None else shots)
    sampler.options.default_shots = shots
    if hasattr(sampler.options, "dynamical_decoupling"):
        sampler.options.dynamical_decoupling.enable = True
        sampler.options.dynamical_decoupling.sequence_type = "XX"
    return sampler.run(list(isa_circuits_list))


def fetch_raw(job_result, circuits, job_meta, backend_name, totals):
    """V2-Result -> RAW-Dokument (KEIN Estimator, KEIN Verdict)."""
    per = []
    for i, c in enumerate(circuits):
        counts = job_result[i].data.c.get_counts()
        per.append({
            "name": c["name"], "kind": c["kind"], "arm": c.get("arm"),
            "set": c.get("set"), "P": c.get("P"), "rep": c.get("rep"),
            "r": c.get("r"),
            "shots_actual": int(sum(counts.values())),
            "counts": counts,
        })
    doc = {
        "experiment": k6.EXPERIMENT,
        "hypothesis": k6.HYPOTHESIS,
        "leg": k6.LEG,
        "status": "QPU_RAW_FETCHED",
        "backend": str(backend_name),
        "job_meta": dict(job_meta),
        "transpile": dict(totals),
        "registered_run_config":
            k6.load_frozen_prereg()["hardware_parameters"]["run_config"],
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_circuits": len(circuits),
        "shots_per_circuit": int(h3.SHOTS),
        "counts_md5": counts_md5([e["counts"] for e in per]),
        "counts": per,
        # ABSICHTLICH ABWESEND: kappa, ratio, gamma, band, verdict.
    }
    return doc


def write_raw(doc, results_path=RAW_PATH):
    with open(results_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    return results_path


def _job_done(job):
    try:
        return str(job.status()).upper().split(".")[-1] in ("DONE",
                                                            "COMPLETED")
    except Exception:
        return False


def run_qpu_job(backend_getter=None, service_getter=None,
                results_path=RAW_PATH, job_id_path=JOB_ID_PATH, poll=True,
                fetch=True):
    """Submit (falls noetig) -> persistiere job_id -> fetch Raw.

    Resume-Vertrag wie 11d: existiert RAW_PATH, geschieht NICHTS;
    existiert nur die Job-ID-Datei, wird der Job wiederaufgenommen.
    poll=False + fetch=False: NUR Submission + Job-ID-Persistenz
    (Submit-Only-Bein, Pollen/Auslesen spaeter ueber denselben Pfad).
    """
    if os.path.exists(results_path):
        with open(results_path, encoding="utf-8") as fh:
            return json.load(fh)
    if backend_getter is None:
        backend = get_backend(get_service())
    else:
        backend = backend_getter()
    backend_name = str(getattr(backend, "name", BACKEND_NAME))

    circuits = h3a.build_hardware_circuit_set()
    tci, totals = isa_circuits(backend, circuits)

    if os.path.exists(job_id_path):
        with open(job_id_path, encoding="utf-8") as fh:
            job_id = fh.read().strip()
        service = (service_getter or get_service)()
        job = service.job(job_id)
        print(f"[qpu] resume job {job_id}")
    else:
        sampler = SamplerV2(mode=backend)
        job = submit_job(sampler, tci)
        job_id = job.job_id()
        with open(job_id_path, "w", encoding="utf-8") as fh:
            fh.write(job_id)
        print(f"[qpu] submitted {job_id} ({len(circuits)} circuits)")

    if job is None:
        return {"status": "QPU_JOB_ID_SAVED", "job_id": job_id,
                "backend": backend_name}
    if poll:
        t0 = time.time()
        while not _job_done(job):
            if time.time() - t0 > POLL_MAX_S:
                return {"status": "QPU_POLL_TIMEOUT", "job_id": job_id,
                        "backend": backend_name}
            time.sleep(POLL_SECONDS)
    if not fetch:
        return {"status": "QPU_JOB_ID_SAVED", "job_id": job_id,
                "backend": backend_name}
    job_result = job.result()
    doc = fetch_raw(job_result, circuits,
                    {"job_id": job_id, "backend": backend_name,
                     "shots_per_circuit": int(h3.SHOTS)},
                    backend_name, totals)
    write_raw(doc, results_path)
    print(f"[qpu] raw fetched: {doc['counts_md5']} "
          f"({doc['n_circuits']} circuits)")
    return doc


if __name__ == "__main__":
    doc = run_qpu_job()
    print(f"status: {doc.get('status')}")
    if "job_id" in doc:
        print(f"job_id: {doc['job_id']}")
    if "counts_md5" in doc:
        print(f"counts_md5: {doc['counts_md5']}")