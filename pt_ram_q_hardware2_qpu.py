# -*- coding: utf-8 -*-
"""H-RAM-Q-3b Hardware-Bein (EXPERIMENT 043): EIN Fez-Job (TOKEN1) + RAW-Fetch.

Der EINZIGE QPU-Griff des Experiments.  Disziplin (Freeze-B'-Vertrag,
Phase-9-Praezedenz: der Payload-md5 0b9c9968 bleibt bei Freeze B' unangetastet):
  1. Transpilation identisch zum ISA2-Report (optimization_level 3, seed 7
     -> bit-dieselben 493 2q / max 84, pt_ram_q_isa2_report.json).
  2. SamplerV2 (raw counts, resilience none), DD XX (Prereg run_config),
     default_shots 8192, ALLE 90 Circuits in EINEM Job.
  3. job_id wird SOFORT nach Submission persistiert (pt_ram_q_fez2_job_id.txt)
     — bei Queue/Timeout kann der Fetch ueber die Job-ID resumed werden.
  4. Raw-Counts werden als pt_ram_q_hardware2_raw.json geschrieben und
     COMMITTET, BEVOR irgendein Estimator/Verdict laeuft (kein kappa, kein
     ratio, kein Band in diesem Modul — das ist die Auswertungsebene).

TOKEN-DISZIPLIN: nur TOKEN1 (IBMQ_TOKEN aus .env via pt_ququint_fez).
TOKEN2 wird NIE gelesen.  Kein Sampler-V2-Local-Pfad hier: dieses Modul ist
der Hardware-Griff, das Aer-Bein lebt in pt_ram_q_hardware2_aer.py.
"""
import hashlib
import json
import os
import time
from datetime import datetime, timezone

from qiskit_ibm_runtime import SamplerV2
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

import pt_ram_q_hardware2 as hw2
import pt_ram_q_hardware2_aer as s2b

BACKEND_NAME = "ibm_fez"
TRANSPILE_SEED = s2b.TRANSPILE_SEED  # 7 — identisch zum ISA2-Report
JOB_ID_PATH = "pt_ram_q_fez2_job_id.txt"
RAW_PATH = "pt_ram_q_hardware2_raw.json"
POLL_SECONDS = 20
POLL_MAX_S = 6 * 3600


def load_token(env_path=".env"):
    """TOKEN1 (IBMQ_TOKEN) — identisch zum Phase-3c-Muster (pt_ququint_fez)."""
    import pt_ququint_fez as fez
    return fez.load_token(env_path)


def get_service(token):
    import pt_ququint_fez as fez
    return fez.get_service(token)


def get_backend(service):
    import pt_ququint_fez as fez
    return fez.get_backend(service)


def isa_circuits(backend, circuits=None):
    """Transpilation bit-identisch zum ISA2-Report (seed 7, opt level 3)."""
    if circuits is None:
        circuits = s2b.build_hardware_circuit_set()
    pm = generate_preset_pass_manager(
        optimization_level=3, backend=backend, seed_transpiler=TRANSPILE_SEED)
    return pm.run([c["circuit"] for c in circuits])


def counts_md5(counts_list):
    """Kanonische Counts-Serialisierung -> md5 (COMMIT VOR Auswertung)."""
    payload = json.dumps(counts_list, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.md5(payload).hexdigest()


def submit_job(sampler, isa_circuits_list, shots=None):
    """EIN SamplerV2-Job: alle 90 Circuits, default_shots, DD XX (Prereg)."""
    shots = int(hw2.SHOTS if shots is None else shots)
    sampler.options.default_shots = shots
    if hasattr(sampler.options, "dynamical_decoupling"):
        sampler.options.dynamical_decoupling.enable = True
        sampler.options.dynamical_decoupling.sequence_type = "XX"
    return sampler.run(list(isa_circuits_list))


def fetch_raw(job_result, circuits, job_meta, backend_name):
    """V2-Result -> RAW-Dokument (KEIN Estimator, KEIN Verdict)."""
    per = []
    for i, c in enumerate(circuits):
        counts = job_result[i].data.c.get_counts()
        per.append({
            "name": c["name"], "kind": c["kind"], "arm": c.get("arm"),
            "P": c.get("P"), "rep": c.get("rep"), "r": c.get("r"),
            "shots_actual": int(sum(counts.values())),
            "counts": counts,
        })
    doc = {
        "experiment": hw2.EXPERIMENT,
        "hypothesis": hw2.HYPOTHESIS,
        "status": "QPU_RAW_FETCHED",
        "backend": str(backend_name),
        "job_meta": dict(job_meta),
        "transpile": {
            "optimization_level": 3,
            "seed_transpiler": TRANSPILE_SEED,
            "isa_2q_total": 493,   # ISA2-Report (Freeze B', pt_ram_q_isa2_report.json)
            "isa_2q_max": 84,
        },
        "registered_run_config":
            hw2.load_frozen_prereg()["hardware_parameters"]["run_config"],
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_circuits": len(circuits),
        "shots_per_circuit": int(hw2.SHOTS),
        "counts_md5": counts_md5([e["counts"] for e in per]),
        "counts": per,
        # ABSICHTLICH ABWESEND: kappa, ratio, band, verdict — die Auswertung
        # ist ein separater Commit NACH diesem Raw-Commit (Freeze-B'-Vertrag).
    }
    return doc


def write_raw(doc, results_path=RAW_PATH):
    with open(results_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    return results_path


def _job_done(job):
    # JobStatus ist hier kein str-Subclass (str(JobStatus.DONE) ==
    # "JobStatus.DONE") — daher Enum-Name extrahieren; reine Strings
    # ("DONE") gehen denselben Pfad.
    try:
        return str(job.status()).upper().split(".")[-1] in ("DONE",
                                                            "COMPLETED")
    except Exception:
        return False


def run_qpu_job(backend_getter=None, service_getter=None,
                results_path=RAW_PATH, job_id_path=JOB_ID_PATH, poll=True):
    """Submit (falls noetig) -> persistiere job_id -> fetch Raw.

    Resume-Vertrag: existiert RAW_PATH, geschieht NICHTS.  Existiert nur
    die Job-ID-Datei, wird der Job ueber service.job(id) wiederaufgenommen
    (service_getter-Injektion fuer Offline-Tests; Default: echter Service).
    """
    if os.path.exists(results_path):
        with open(results_path, encoding="utf-8") as fh:
            return json.load(fh)
    if backend_getter is None:
        backend = get_backend(get_service(load_token()))
    else:
        backend = backend_getter()
    backend_name = str(getattr(backend, "name", BACKEND_NAME))

    circuits = s2b.build_hardware_circuit_set()
    isa = isa_circuits(backend, circuits)

    if os.path.exists(job_id_path):
        with open(job_id_path, encoding="utf-8") as fh:
            job_id = fh.read().strip()
        if service_getter is None:
            service_getter = lambda: get_service(load_token())
        job = service_getter().job(job_id)
        print(f"[qpu] resume job {job_id}")
    else:
        sampler = SamplerV2(mode=backend)
        job = submit_job(sampler, isa)
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
    job_result = job.result()
    doc = fetch_raw(job_result, circuits,
                    {"job_id": job_id, "backend": backend_name,
                     "shots_per_circuit": int(hw2.SHOTS)},
                    backend_name)
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