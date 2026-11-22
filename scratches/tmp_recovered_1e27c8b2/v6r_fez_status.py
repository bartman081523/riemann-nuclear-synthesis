# -*- coding: utf-8 -*-
"""Job-Status-Diagnostik fuer den hängenden 046-Fez-Job (NUR LESE-Zugriff).
Token-Disziplin: TOKEN1 via pt_ququint_fez (Fez-Pfad), KEINE Token-Ausgabe.
"""
import json
import sys

sys.path.insert(0, "/run/media/julian/ML4/riemann")
import os as _os
_os.chdir("/run/media/julian/ML4/riemann")

import pt_ququint_fez as fez

JOB_ID = "dat3q9dvr3kc73ektkv0"

svc = fez.get_service(fez.load_token())

job = svc.job(JOB_ID)
info = {
    "job_id": JOB_ID,
    "status": str(job.status()),
    "creation_date": str(getattr(job, "creation_date", None)),
    "backend": str(getattr(job, "backend", None)),
    "error_message": getattr(job, "error_message", None),
}
print("== JOB ==")
print(json.dumps(info, ensure_ascii=False, default=str))

b = svc.backend("ibm_fez")
bs = b.status()
print("== BACKEND ibm_fez ==")
print(json.dumps({
    "operational": bs.operational,
    "pending_jobs": bs.pending_jobs,
    "status_msg": getattr(bs, "status_msg", None),
    "qubits": b.num_qubits,
}, ensure_ascii=False, default=str))

print("== LETZTE 12 JOBS (TOKEN1-Service, eigenes Konto) ==")
rows = []
for j in svc.jobs(limit=12):
    rows.append({
        "id": j.job_id(),
        "created": str(getattr(j, "creation_date", None)),
        "status": str(j.status()),
        "backend": str(getattr(j, "backend", None)),
        "tags": getattr(j, "tags", None),
    })
print(json.dumps(rows, ensure_ascii=False, default=str, indent=1))