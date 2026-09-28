# -*- coding: utf-8 -*-
"""pt_ram_q_hardware3_rep_qpu.py — EXPERIMENT 047 (H-RAM-Q-5):
RAM-Q-Phase-11d-Wiederholung, Prereg pt_ram_q_hardware3_rep_prereg.json
(REGISTERED_NOT_MEASURED VOR dem Job).

Protokoll bit-identisch zu Phase 11d (EXPERIMENT 044): dieselben 116
Circuits (s3a.build_hardware_circuit_set, deterministisch), dieselbe
ISA3-Transpilation (opt level 3, seed 7), SamplerV2, DD XX, 8192 Shots,
EIN Fez-Job (TOKEN1 via pt_ququint_fez).

Neu gegenueber 11d:
- Submission-Gate: ISA3-Re-Verifikation gegen pt_ram_q_isa3_report.json
  (total 2q 559, max 84, per-Circuit-Op-Sets bit-gleich). Mismatch ->
  ABBRUCH VOR Submission (kein Job auf unstabiler Transpilation).
- NEUE Pfade: pt_ram_q_hardware3_rep_job_id.txt /
  pt_ram_q_hardware3_raw_rep.json — die 11d-Originale bleiben
  unangetastet.
- Raw wird VOR der Auswertung geschrieben und committed (§Z.14).

Auswertung: pt_ram_q_hardware3_eval.evaluate(raw_path=<raw_rep>) — die
GEFRORENE Phase-11-Auswertung UNVERAENDERT (dieselbe Verdict-Map, md5
baaca1f6, dasselbe w_B'' = w_B' 0.02787, dasselbe Stage-3/ISA3-Artefakt);
sie liefert automatisch das gefrorene H-RAM-Q-4-Verdict AUF DEM NEUEN
Raw. Die Repetitions-Hypothesen (H-RAM-Q-5a Session-Robustheit des
Falsifikators, H-RAM-Q-5b Echo-Leiter-Diagnostik) werden in
pt_ram_q_hardware3_rep_eval.py aus dem NEUEN Eval-Dokument + dem
committeten 11d-Eval (Vergleichsanker) registriert-klassifiziert — NICHT
in der gefrorenen Auswertung selbst (kein neuer Gate-Zweig).
"""
import argparse
import json
import os

import pt_ram_q_hardware3_qpu as qpu3
import pt_ram_q_hardware3_aer as s3a
from pt_ram_q_isa3 import isa_report

EXPERIMENT = "047-ram-q-phase11d-repetition"
HYPOTHESIS = "H-RAM-Q-5"
PREREG_PATH = "pt_ram_q_hardware3_rep_prereg.json"
JOB_ID_PATH = "pt_ram_q_hardware3_rep_job_id.txt"
RAW_PATH = "pt_ram_q_hardware3_raw_rep.json"
ISA3_FROZEN = "pt_ram_q_isa3_report.json"  # Freeze B''; NIE überschreiben


def isa_gate(backend, circuits):
    """ISA3-Re-Verifikation VOR Submission: neues isa_report gegen das
    gefrorene Freeze-B''-Artefakt (bit-gleiche per-Circuit-Ops, 559/84).
    Gibt (ok, detail) zurueck; bricht NICHT selbst ab (der Aufrufer
    entscheidet)."""
    with open(ISA3_FROZEN, encoding="utf-8") as fh:
        frozen = json.load(fh)
    _, live = isa_report(backend, circuits)  # isa_report liefert (isa, report)
    same_per_circuit = all(
        live["per_circuit"].get(name, {}).get("ops") == rec["ops"]
        and live["per_circuit"].get(name, {}).get("two_q") == rec["two_q"]
        for name, rec in frozen["per_circuit"].items()
    ) and set(live["per_circuit"]) == set(frozen["per_circuit"])
    ok = (same_per_circuit
          and live["total_two_q"] == frozen["total_two_q"]
          and live["max_two_q"] == frozen["max_two_q"]
          and frozen.get("optimization_level") == 3
          and frozen.get("transpile_seed", 7) == 7)
    detail = {
        "frozen_total_two_q": frozen["total_two_q"],
        "live_total_two_q": live["total_two_q"],
        "frozen_max_two_q": frozen["max_two_q"],
        "live_max_two_q": live["max_two_q"],
        "per_circuit_bitgleich": bool(same_per_circuit),
        "optimization_level": frozen.get("optimization_level"),
    }
    return ok, detail


def run_rep(backend_getter=None, service_getter=None, poll=True):
    """EIN Fez-Job auf den IDENTISCHEN Circuits; Gate VOR Submission."""
    if backend_getter is None:
        from pt_ququint_fez import load_token, get_service, get_backend
        backend_getter = lambda: get_backend(get_service(load_token()))
    backend = backend_getter()
    circuits = s3a.build_hardware_circuit_set()
    if os.path.exists(RAW_PATH):
        with open(RAW_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    ok, detail = isa_gate(backend, circuits)
    print("[isa3-gate]", json.dumps(detail))
    if not ok:
        print("ISA3-GATE FEHLGESCHLAGEN — kein Job (Prereg-Submission-"
              "Gate). Transpilation ist nicht bit-stabil gegenueber "
              "Freeze B''.")
        return {"status": "ISA3_GATE_FAILED", "detail": detail}
    return qpu3.run_qpu_job(
        backend_getter=lambda: backend,
        service_getter=service_getter,
        results_path=RAW_PATH,
        job_id_path=JOB_ID_PATH,
        poll=poll,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=EXPERIMENT)
    parser.add_argument("--quota", action="store_true",
                        help="Fez-Quota-Pruefung")
    parser.add_argument("--gate", action="store_true",
                        help="ISA3-Re-Verifikation OHNE Submission")
    parser.add_argument("--submit", action="store_true",
                        help="EIN Fez-Job (Resume-Vertrag) + Raw, "
                             "OHNE Auswertung")
    args = parser.parse_args(argv)

    if args.quota:
        from pt_ququint_fez import load_token, get_service
        service = get_service(load_token())
        backend = service.backend(qpu3.BACKEND_NAME)
        status = backend.status()
        print(json.dumps({"backend": qpu3.BACKEND_NAME,
                          "operational": bool(status.operational),
                          "pending_jobs": int(status.pending_jobs)}))
        return 0 if status.operational else 1
    if args.gate:
        from pt_ququint_fez import load_token, get_service, get_backend
        backend = get_backend(get_service(load_token()))
        circuits = s3a.build_hardware_circuit_set()
        ok, detail = isa_gate(backend, circuits)
        print(json.dumps({"ok": ok, **detail}, indent=1))
        return 0 if ok else 2
    if args.submit:
        doc = run_rep()
        print(f"status: {doc.get('status')}")
        if "job_id" in doc:
            print(f"job_id: {doc['job_id']}")
        if "counts_md5" in doc:
            print(f"counts_md5: {doc['counts_md5']} "
                  f"({doc.get('n_circuits')} circuits)")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())