"""Quota probe for both IBMQ paths — NO token output.

TOKEN1 (.env IBMQ_TOKEN) -> ibm_fez (Fez path only).
TOKEN2 (.env IBMQ_TOKEN2) -> ibm_kingston (Kingston path only).
"""
import json
import os
import sys

REPO = "/run/media/julian/ML4/riemann"
sys.path.insert(0, REPO)
os.chdir(REPO)


def load_env_token(env_path, key):
    with open(env_path) as fh:
        for line in fh:
            line = line.strip()
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"')
    raise RuntimeError(key + " not in .env")


def probe(token_key, backend_name):
    from qiskit_ibm_runtime import QiskitRuntimeService
    tok = load_env_token(os.path.join(REPO, ".env"), token_key)
    svc = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok)
    be = svc.backend(backend_name)
    st = be.status()
    out = {
        "token_key": token_key,
        "backend": backend_name,
        "operational": bool(st.operational),
        "pending_jobs": int(getattr(st, "pending_jobs", -1)),
        "status_msg": str(getattr(st, "status_msg", ""))[:120],
    }
    try:
        jobs = svc.jobs(backend_name=backend_name, limit=6)
        out["recent_jobs_n"] = len(jobs)
        out["recent_jobs"] = [
            {
                "id": str(j.job_id() if callable(j.job_id) else j.job_id),
                "status": str(j.status() if callable(j.status) else j.status),
            }
            for j in jobs[:6]
        ]
    except Exception as e:  # noqa: BLE001
        out["recent_jobs_error"] = str(e)[:200]
    return out


result = []
for key, name in (("IBMQ_TOKEN", "ibm_fez"), ("IBMQ_TOKEN2", "ibm_kingston")):
    try:
        result.append(probe(key, name))
    except Exception as e:  # noqa: BLE001
        result.append({"token_key": key, "backend": name, "error": str(e)[:300]})

print(json.dumps(result, indent=2))