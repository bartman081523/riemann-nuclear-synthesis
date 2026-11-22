# -*- coding: utf-8 -*-
"""fez046_orphan_circuits.py — CIRCUIT-IDENTITÄT des Orphan-Jobs (read-only).

daua5hahcrkc73dv9eh0 (Sampler, ibm_fez, created 2026-09-30 07:48) hat 4 Pubs.
Jetzt die vier Circuits als OBJEKTE auslesen: name, num_qubits, depth,
count_ops, evtl. metadata — das findet den Erzeuger unter den pt_-Runnern.
KEIN cancel, KEIN .env-Output, keine Circuit-Bodies.
"""
import sys

sys.path.insert(0, "/run/media/julian/ML4/riemann")

import pt_v5_kingston_rep as rep  # noqa: E402

ORPHAN = "daua5hahcrkc73dv9eh0"


def circuit_fingerprint(circ):
    info = {
        "type": type(circ).__name__,
        "name": getattr(circ, "name", None),
        "num_qubits": getattr(circ, "num_qubits", None),
        "num_clbits": getattr(circ, "num_clbits", None),
    }
    for meth in ["num_qubits", "num_clbits"]:
        try:
            info[meth] = getattr(circ, meth)()
        except Exception:  # noqa: BLE001
            pass
    try:
        info["name"] = circ.name
    except Exception:  # noqa: BLE001
        pass
    try:
        d = circ.count_ops()
        info["count_ops"] = {str(k): int(v) for k, v in
                             sorted(d.items(), key=lambda kv: -kv[1])[:14]}
    except Exception as exc:  # noqa: BLE001
        info["count_ops"] = f"err {type(exc).__name__}"
    try:
        info["depth"] = int(circ.depth())
    except Exception:  # noqa: BLE001
        pass
    try:
        info["metadata"] = str(getattr(circ, "metadata", None))[:200]
    except Exception:  # noqa: BLE001
        pass
    return info


def main():
    svc = rep.make_service_for("fez")
    job = svc.job(ORPHAN)
    inp = job.inputs
    pubs = inp.get("pubs") if isinstance(inp, dict) else None
    print("num_pubs:", len(pubs) if pubs else None)
    if not pubs:
        print("input keys:", sorted(inp.keys()) if isinstance(inp, dict)
              else type(inp).__name__)
        return
    for i, pub in enumerate(pubs):
        circ = pub[0]
        print(f"--- pub[{i}] ---")
        print(circuit_fingerprint(circ))


if __name__ == "__main__":
    main()