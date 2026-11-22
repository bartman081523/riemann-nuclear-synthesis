# -*- coding: utf-8 -*-
"""fez046_queue_probe.py — WHO-IS daua5hahcrkc73dv9eh0 (read-only).

Umgebungsecho der Fez-046-Neuanlage: in scratches/fez046_service_dump.json
(fez046_service_ops.py probe, 2026-10-03) surfte ein ZWEITER QUEUED-Job
daua5hahcrkc73dv9eh0 auf, created 2026-09-30 07:48 — 50 Minuten VOR dem
046-Repeat-Job dauassrojkfs738rrcsg (08:38). In keinem Submit-Log erklärt
(v5r_fez_submit.log = alter Job dat3q9dv, v5r_fez_submit2.log = 08:38).

Dieses Skript ruft fuer BEIDE Jobs NUR lesende Metadaten ab:
  job_id, status, name, program_id, creation_date, backend,
  est. start (falls verfuegbar), error_message
KEIN cancel, KEIN submit, KEIN Token-Print, KEIN instance-Parameter.
"""
import sys

sys.path.insert(0, "/run/media/julian/ML4/riemann")

import pt_v5_kingston_rep as rep  # noqa: E402

IDS = [
    "dauassrojkfs738rrcsg",  # 046-repeat, job-id-File (Resume-Vertrag)
    "daua5hahcrkc73dv9eh0",  # Unbekannter Zweit-Job, Herkunft unklar
]

FIELDS = ["name", "program_id", "creation_date", "backend"]


def main():
    svc = rep.make_service_for("fez")
    for jid in IDS:
        job = svc.job(jid)
        out = {"job_id": jid, "status": str(job.status())}
        for f in FIELDS:
            try:
                out[f] = str(getattr(job, f, None))
            except Exception as exc:  # noqa: BLE001
                out[f] = f"{type(exc).__name__}: {exc}"
        try:
            out["error_message"] = job.error_message()
        except Exception as exc:  # noqa: BLE001
            out["error_message"] = f"{type(exc).__name__}: {exc}"
        try:
            m = job.metrics()
            out["metrics_keys"] = sorted(m.keys()) if isinstance(m, dict) else str(type(m))
        except Exception as exc:  # noqa: BLE001
            out["metrics"] = f"{type(exc).__name__}: {exc}"
        print(out)


if __name__ == "__main__":
    main()