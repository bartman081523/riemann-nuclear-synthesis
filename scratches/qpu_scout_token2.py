"""QPU-Scout (TOKEN2): Pre-Flight-Gate gegen Queue-Starvation + Backend-Entscheid.

Lektion 2026-10-16: drei Jobs (F4/046/055) hingen wochenlang QUEUED auf
ibm_fez trotz global-pending 0 — Open-Plan-Fair-Share-Starvation. Dieser
Scout erkennt das VOR dem Submit:
  G1 Backend operational + status_msg aktiv
  G2 Plan-sichtbare pending_jobs <= MAX_PENDING (20)
  G3 Keine EIGENEN Jobs älter als STALE_DAYS (3) auf demselben Backend
     noch QUEUED (Starvation-Signatur → FAIL, egal was G2 sagt)
  G4 Qubit-Breite ausreichend für die Circuits
Entscheidung: niedrigste Median-2Q-Fehlerrate unter den PASS-Backends
(Readout als Tie-Break), als md5-gefrorene Decision.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MAX_PENDING = 20
STALE_DAYS = 3

KNOWN_IDS = {"daua5hahcrkc73dv9eh0"}  # QUQUINT-F4 (Backlog, keine Job-ID-Datei)

USAGE_CACHE = {}

DECISION_PATH = "scratches/qpu_scout_decision.json"


def inventory_service(service):
    import numpy as np
    rows = []
    for b in service.backends():
        try:
            st = b.status()
            props = b.properties()
            e2 = float(np.median([props.gate_error(g.gate, g.qubits)
                                  for g in props.gates if len(g.qubits) == 2]))
            ro = float(np.median([props.readout_error(q)
                                  for q in range(b.num_qubits)]))
            rows.append({"backend": b.name, "qubits": b.num_qubits,
                         "operational": bool(st.operational),
                         "pending": int(st.pending_jobs),
                         "status_msg": str(st.status_msg)[:40],
                         "median_2q": e2, "median_ro": ro})
        except Exception as e:  # noqa
            rows.append({"backend": b.name, "error": str(e)[:120]})
    return service, rows


def inventory():
    svcs = services()
    return inventory_service([s for n, s in svcs if n == "TOKEN2"][0])


def status_name(job):
    """Runtime-Befund 2026-10-16: job.status() liefert str statt Enum."""
    st = job.status()
    return (st.name if hasattr(st, "name") else str(st)).upper()


def own_tracked_job_ids():
    """Alle lokal registrierten Job-IDs (Resume-Vertrag-Dateien + bekannte
    Backlog-IDs ohne eigene Datei, z. B. QUQUINT-F4)."""
    import glob
    ids = set(KNOWN_IDS)
    for pat in ("*_job_id.txt", "*job_ids.json", "scratches/*job_id*.txt"):
        for path in glob.glob(pat):
            try:
                txt = open(path, encoding="utf-8").read()
            except OSError:
                continue
            import re
            ids.update(re.findall(r"\b[a-z0-9]{20,}\b", txt))
    return sorted(ids)


def services():
    """BEIDE Token-Räume: die QUEUED-Jobs leben unter TOKEN1, der Scout
    submittet unter TOKEN2 — Starvation muss in beiden Räumen geprüft
    werden (Befund 2026-10-16: TOKEN2 sieht TOKEN1-Jobs nicht)."""
    from pt_token_diagnose import load_token
    from qiskit_ibm_runtime import QiskitRuntimeService
    import pt_ququint_fez as fez
    svcs = []
    for name, tok in (("TOKEN1", fez.load_token()),
                      ("TOKEN2", load_token("IBMQ_TOKEN2"))):
        try:
            svcs.append((name, QiskitRuntimeService(
                channel="ibm_quantum_platform", token=tok)))
        except Exception as e:  # noqa
            print(f"WARN: {name}-Service fehlgeschlagen: {str(e)[:100]}")
    return svcs


def own_stale_jobs(services, backend_name):
    """Direkt-Lookup jeder tracked ID in JEDEM Token-Raum: QUEUED + Alter
    > STALE_DAYS auf diesem Backend (egal unter welchem Token)."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    stale = []
    for tok_name, service in services:
        for jid in own_tracked_job_ids():
            try:
                j = service.job(jid)
            except Exception:  # noqa
                continue
            try:
                if status_name(j) != "QUEUED":
                    continue
                if j.backend().name != backend_name:
                    continue
                age = (now - j.creation_date).total_seconds() / 86400.0
                if age > STALE_DAYS:
                    stale.append({"job_id": jid, "age_days": round(age, 1),
                                  "token": tok_name})
            except Exception:  # noqa
                continue
    return stale


def instance_usage(service):
    """G5 (Befund 2026-10-16): Instanz-Quota — usage_limit_reached blockt
    ALLE Submits, egal wie leer die Backend-Queue aussieht."""
    try:
        u = service.usage()
        return {"limit_reached": bool(u.get("usage_limit_reached")),
                "consumed_s": u.get("usage_consumed_seconds"),
                "limit_s": u.get("usage_limit_seconds"),
                "available_at": u.get("time_available_at")}
    except Exception as e:  # noqa
        return {"error": str(e)[:120]}


def decide(min_qubits=6):
    svcs = services()
    usage = {n: instance_usage(s) for n, s in svcs}
    t2 = [s for n, s in svcs if n == "TOKEN2"]
    if not t2:
        raise RuntimeError("Kein TOKEN2-Service — kein Submit möglich")
    service = t2[0]
    t2_blocked = bool(usage.get("TOKEN2", {}).get("limit_reached"))
    _, rows = inventory_service(service)
    scored = []
    for r in rows:
        if "error" in r:
            scored.append({**r, "gate": "FAIL", "reason": r["error"]})
            continue
        reasons = []
        if not r["operational"]:
            reasons.append("nicht operational")
        if r["pending"] > MAX_PENDING:
            reasons.append(f"pending {r['pending']} > {MAX_PENDING}")
        stale = own_stale_jobs(svcs, r["backend"])
        if stale:
            reasons.append(f"STARVATION: eigene QUEUED-Jobs {stale}")
        if r["qubits"] < min_qubits:
            reasons.append("zu schmal")
        if t2_blocked:
            reasons.append("G5: TOKEN2-Quota erschöpft "
                           f"(frei ab {usage['TOKEN2'].get('available_at')})")
        scored.append({**r, "stale_own": stale,
                       "gate": "FAIL" if reasons else "PASS",
                       "reason": "; ".join(reasons) or "ok"})
    passing = [s for s in scored if s["gate"] == "PASS"]
    passing.sort(key=lambda s: (s["median_2q"], s["median_ro"]))
    decision = {"backends": scored,
                "choice": passing[0]["backend"] if passing else None,
                "usage": usage,
                "min_qubits": min_qubits}
    doc = dict(decision)
    doc["md5"] = hashlib.md5(json.dumps(
        decision, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    with open(DECISION_PATH, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    return doc


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-qubits", type=int, default=6)
    args = ap.parse_args()
    d = decide(args.min_qubits)
    for s in d["backends"]:
        print(f"{s['backend']}: {s['gate']} ({s['reason']}) "
              f"2Q={s.get('median_2q')} RO={s.get('median_ro')} "
              f"pend={s.get('pending')}")
    print("CHOICE:", d["choice"], "md5:", d["md5"])


if __name__ == "__main__":
    main()
