# -*- coding: utf-8 -*-
"""fez046_orphan_inputs.py — SHAPE der Orphan-Job-INPUTS (read-only).

daua5hahcrkc73dv9eh0 = Sampler-Job auf ibm_fez, created 2026-09-30 07:48.
Identifikation via Pub/CIRCUIT-SHAPE: NUR Struktur (Pubs-Zahl, Circuit-Name,
num_qubits, ops-Count, params-Shape), KEINE Circuit-Bodies/Parameterwerte,
NOCH weniger die Bas64-Blöcke — die INPUTS selbst können Mega-Byte-Groesse
haben. KEIN cancel, KEIN .env-Output.
"""
import sys

sys.path.insert(0, "/run/media/julian/ML4/riemann")

import pt_v5_kingston_rep as rep  # noqa: E402

ORPHAN = "daua5hahcrkc73dv9eh0"
MAX_ITEMS = 12
MAX_DEPTH = 3


def shape(v, depth=0):
    """Typ-/Shape-Baum ohne Blob-Inhalte."""
    if depth > MAX_DEPTH:
        return f"<str-len {len(str(v))}>"
    if isinstance(v, dict):
        items = list(v.items())[:MAX_ITEMS]
        out = {k: shape(x, depth + 1) for k, x in items}
        if len(v) > MAX_ITEMS:
            out["<weitere>"] = len(v) - MAX_ITEMS
        return out
    if isinstance(v, (list, tuple)):
        out = [shape(x, depth + 1) for x in v[:MAX_ITEMS]]
        if len(v) > MAX_ITEMS:
            out.append(f"<{len(v) - MAX_ITEMS} mehr von {len(v)}>")
        return out
    s = str(v)
    return s if len(s) <= 80 else f"<str len {len(s)}: {s[:60]}...>"


def main():
    svc = rep.make_service_for("fez")
    job = svc.job(ORPHAN)
    print("status:", job.status())
    try:
        logs = job.logs()
        if logs:
            lines = logs.splitlines()
            print("--- job.logs() letzte 30 Zeilen ---")
            for line in lines[-30:]:
                print(line)
    except Exception as exc:  # noqa: BLE001
        print("logs_error:", type(exc).__name__, exc)
    inp = job.inputs
    print("--- inputs SHAPE ---")
    print(shape(inp))


if __name__ == "__main__":
    main()