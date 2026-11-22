"""Downloader fuer alle verbleibenden DONE-QPU-Jobs (0 QPU-Quota-Verbrauch).

Holt:
1. daua5hahcrkc73dv9eh0 (QUQUINT F4 auf ibm_fez, TOKEN1) -> scratches/pt_ququint_f4_fez_raw.json
2. db8tqp5ckpjs73b1mdr0 (Exp 055 Prio48 auf ibm_marrakesh, TOKEN2) -> scratches/pt_ram_q_prio48_marrakesh_raw.json
"""

import json
import os
import sys

from qiskit_ibm_runtime import QiskitRuntimeService

def get_tokens():
    tokens = {}
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line.startswith("IBMQ_TOKEN="):
                tokens["TOKEN1"] = line.split("=", 1)[1].strip()
            elif line.startswith("IBMQ_TOKEN2="):
                tokens["TOKEN2"] = line.split("=", 1)[1].strip()
    return tokens

def fetch_and_save(service, job_id, output_path, desc):
    print(f"\n--- Fetching {desc} (Job {job_id}) ---")
    if os.path.exists(output_path):
        print(f"Output existiert bereits: {output_path}")
        return
    job = service.job(job_id)
    status = str(job.status()).split(".")[-1]
    print(f"Job Status: {status}")
    if status != "DONE":
        print(f"Job ist nicht DONE ({status}) — ueberspringe.")
        return
        
    res = job.result()
    circuits_data = []
    for i in range(len(res)):
        qd = res[i].data
        # Finde Bit-Array / Counts
        counts = None
        for attr in ["c", "meas", "m"]:
            if hasattr(qd, attr):
                counts = getattr(qd, attr).get_counts()
                break
        if counts is None:
            # Fallback: erstes Attribut im data dict
            for key in dir(qd):
                if not key.startswith("_"):
                    val = getattr(qd, key)
                    if hasattr(val, "get_counts"):
                        counts = val.get_counts()
                        break
        if counts is None:
            raise ValueError(f"Konnte counts nicht extrahieren fuer Circuit {i}: {dir(qd)}")
        circuits_data.append({k: int(v) for k, v in counts.items()})
        
    doc = {
        "job_id": job_id,
        "backend": job.backend().name if hasattr(job.backend(), "name") else str(job.backend()),
        "created": str(job.creation_date),
        "n_circuits": len(circuits_data),
        "counts": circuits_data,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
    print(f"[OK] Gespeichert in {output_path} ({len(circuits_data)} Circuits)")

def main():
    tokens = get_tokens()
    
    # 1. daua5hahcrkc73dv9eh0 (TOKEN1, ibm_fez)
    s1 = QiskitRuntimeService(channel="ibm_quantum_platform", token=tokens["TOKEN1"])
    fetch_and_save(s1, "daua5hahcrkc73dv9eh0", "scratches/pt_ququint_f4_fez_raw.json", "QUQUINT F4 (Fez)")
    
    # 2. db8tqp5ckpjs73b1mdr0 (TOKEN2, ibm_marrakesh)
    s2 = QiskitRuntimeService(channel="ibm_quantum_platform", token=tokens["TOKEN2"])
    fetch_and_save(s2, "db8tqp5ckpjs73b1mdr0", "scratches/pt_ram_q_prio48_marrakesh_raw.json", "Prio48 (Marrakesh)")

if __name__ == "__main__":
    main()
