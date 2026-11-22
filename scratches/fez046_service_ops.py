# -*- coding: utf-8 -*-
"""fez046_service_ops.py — SERVICE-OPERATIONEN fuer das Fez-046-Bein.

Scratches-Variante 2026-10-03 (User-Direktive: nicht mehr in Job-Tmp arbeiten):
OUT zeigt nach scratches/ statt Job-Tmp, sonst byte-gleiche Fortfuehrung von
tmp_recovered_1e27c8b2/fez046_service_ops.py (md5 0849daa2, MCP-rekonstruiert).

Modes:
  probe   — Status von pt_v5_kingston_rep_fez_job_id.txt + alle derzeit
            Abrufbaren (status/creation_date/metrics/logs) nach
            scratches/fez046_service_dump.json dumpen. READ_ONLY.
  cancel  — job.cancel() + Nach-Status. Nur bei EXPLIZITEM User-Auftrag.

TOKEN-DISZIPLIN: wie im Runner leg fez -> TOKEN1 via fez.load_token(),
KEIN instance-Parameter. KEIN Token-Print, KEIN .env-Output.
"""
import json
import os
import sys

sys.path.insert(0, "/run/media/julian/ML4/riemann")
os.chdir("/run/media/julian/ML4/riemann")

import pt_v5_kingston_rep as rep  # noqa: E402

OUT = "/run/media/julian/ML4/riemann/scratches/fez046_service_dump.json"


def py2json(obj):
    """JSON-sichere Fassung: alles Nicht-Primitive via str()."""
    try:
        json.dumps(obj)
        return obj
    except TypeError:
        if isinstance(obj, dict):
            return {str(k): py2json(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [py2json(v) for v in obj]
        return str(obj)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "probe"
    svc = rep.make_service_for("fez")
    jid = open(rep.JOBID_PATHS["fez"], encoding="utf-8").read().strip()
    job = svc.job(jid)
    doc = {"job_id": jid, "mode": mode,
           "status": str(job.status()),
           "creation_date": str(getattr(job, "creation_date", None))}
    doc["metrics"] = None
    try:
        doc["metrics"] = job.metrics()
    except Exception as exc:
        doc["metrics_error"] = type(exc).__name__
    doc["logs"] = None
    try:
        doc["logs"] = job.logs()
    except Exception as exc:
        doc["logs_error"] = type(exc).__name__
    try:
        doc["error_message"] = py2json(job.error_message())
    except Exception as exc:
        doc["error_message"] = None
        doc["error_message_error"] = f"{type(exc).__name__}: {exc}"
    try:
        doc["backend_pending"] = int(
            svc.backend("ibm_fez").status().pending_jobs)
    except Exception as exc:
        doc["backend_pending_error"] = type(exc).__name__
    try:
        hist = svc.jobs(backend_name="ibm_fez", limit=10)
        doc["fez_recent_jobs"] = [
            {"job_id": j.job_id(), "status": str(j.status()),
             "created": str(getattr(j, "creation_date", None))}
            for j in hist]
    except Exception as exc:
        doc["fez_recent_jobs_error"] = type(exc).__name__

    if mode == "cancel":
        if doc["status"] not in ("QUEUED", "JobStatus.QUEUED"):
            print("GUARD: status", doc["status"], "-> NICHT gecancelt")
        else:
            doc["cancel"] = None
            try:
                doc["cancel"] = job.cancel()
            except Exception as exc:
                doc["cancel_error"] = f"{type(exc).__name__}: {exc}"
            try:
                doc["status_after"] = str(job.status())
            except Exception as exc:
                doc["status_after_error"] = type(exc).__name__

    doc = py2json(doc)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    print("STATUS:", doc["status"])
    print("creation:", doc["creation_date"])
    print("backend_pending:", doc["backend_pending"])
    print("metrics_present:", doc["metrics"] is not None)
    print("logs_present:", doc["logs"] is not None)
    print("recent_jobs:", len(doc.get("fez_recent_jobs") or
                              doc.get("fez_recent_jobs_error", "?")))
    if mode == "cancel":
        print("cancel:", doc.get("cancel"), "| status_after:",
              doc.get("status_after"))


if __name__ == "__main__":
    main()