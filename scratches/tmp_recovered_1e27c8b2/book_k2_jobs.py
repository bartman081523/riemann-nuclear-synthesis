# -*- coding: utf-8 -*-
"""Bucht die zwei Kingston-Jobs (D1 + K2) ins Inventar-Archiv
pt_downloaded_job_results.json — TOKEN2-ONLY (Kingston-Disziplin: TOKEN1
in Kingston-Beinen NIE lesen; das generische --fetch des Inventar-Moduls
probiert beide Accounts und ist hier unverwendbar).

Muster = 2e348f1-Präzedenz (Inventar 20->21, --fetch, DONE): minimaler
Metadaten-Eintrag je Job, counts verbleiben in den committed Raw-Artefakten
(raw_ref mit counts_md5).  Nur-Dokumentation, kein Messwert neu.
"""
import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/run/media/julian/ML4/riemann")

import pt_v5_kingston as k5

JOBS = [
    ("davf0ns92g1c7398pfv0", "pt_ram_q6_kingston_raw.json",
     "f4da706dd542c306a96cba2001e1a6b9", "D1 (EXPERIMENT 050, H-RAM-Q-6)"),
    ("davfridj371s73dmqstg", "pt_ram_q6_k2_raw.json",
     "72f6729ac9261f50b5bfc9e56c6d7e46", "K2 (EXPERIMENT 051, H-RAM-Q-6)"),
]
ARCHIVE = "/run/media/julian/ML4/riemann/pt_downloaded_job_results.json"

svc = k5._make_service()  # TOKEN2 only (Kingston)
entries_new = []
for jid, raw_path, cmd5, label in JOBS:
    job = svc.job(jid)
    entry = {
        "job_id": jid,
        "status": str(job.status()),
        "backend": str(job.backend().name),
        "creation_date": str(job.creation_date),
        "data": {},
        "raw_ref": {
            "path": raw_path,
            "counts_md5": cmd5,
            "note": label + " — Raw-Counts committed VOR Auswertung",
        },
    }
    if entry["status"] != "DONE":
        print("NICHT DONE:", jid, entry["status"]); sys.exit(2)
    if entry["backend"] != "ibm_kingston":
        print("NICHT Kingston:", jid, entry["backend"]); sys.exit(2)
    entries_new.append(entry)
    print(f"geprobt: {jid} {entry['status']} {entry['backend']} "
          f"{entry['creation_date'][:19]}")

with open(ARCHIVE, encoding="utf-8") as fh:
    doc = json.load(fh)
have = {e["job_id"] for e in doc["results"].get("IBMQ_TOKEN2", [])}
for e in entries_new:
    if e["job_id"] in have:
        print("bereits gebucht:", e["job_id"]); continue
    doc["results"].setdefault("IBMQ_TOKEN2", []).append(e)
    print("gebucht:", e["job_id"])

with open(ARCHIVE, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, ensure_ascii=False, indent=2, default=str)
print("written", ARCHIVE,
      "| IBMQ_TOKEN2:", len(doc["results"]["IBMQ_TOKEN2"]),
      "| IBMQ_TOKEN:", len(doc["results"]["IBMQ_TOKEN"]))
