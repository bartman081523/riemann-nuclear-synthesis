# -*- coding: utf-8 -*-
"""EXPERIMENT 050 (H-RAM-Q-6 Leg D1) — Kingston ISA-Gate-Stage (0 QPU).

Transpiliert die 116 Circuits des GEFRORENEN Phase-11b-Payloads auf
ibm_kingston (optimization_level 3, seed 7, identisch zum gefrorenen
run_config) und schreibt das Gate-Artefakt
pt_ram_q6_kingston_isa_gate.json mit dem SCHEMA, das der GEFRORENE
Eval (pt_ram_q_hardware3_eval) vom isa_path erwartet:
  optimization_level / transpile_seed / total_two_q / max_two_q /
  verdict == "ISA_OK"

0 QPU: KEIN Job-Submission — nur Service-Lesen (Coupling-Map/Properties).
TOKEN-DISZIPLIN: NUR TOKEN2 via pt_v5_kingston._make_service; nie echo.
"""
import json
import os
from datetime import datetime, timezone

from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

import pt_ram_q6_kingston as k6
import pt_ram_q_hardware3_aer as h3a

OUT_PATH = k6.ISA_GATE_PATH

# Gate-Klassen (Whitelist; alles andere RAISED, kein stiller Absorb)
ONE_QU = {"rz", "sx", "x", "id", "measure", "barrier", "delay", "reset"}
TWO_QU = {"cz", "ecr", "cx", "cy", "zz"}


def count_2q(ops):
    total = 0
    for name, cnt in ops.items():
        if name in ONE_QU:
            continue
        if name in TWO_QU:
            total += int(cnt)
        else:
            raise ValueError("unbekannte Gate-Klasse in Kingston-Transpile: "
                             "%r (ops=%r)" % (name, dict(ops)))
    return total


def run_stage(backend=None, service=None, out_path=OUT_PATH, pts=None,
              cal=None):
    prereg = k6.load_frozen_prereg()
    circuits = h3a.build_hardware_circuit_set(pts=pts, cal=cal)
    assert len(circuits) == 116, len(circuits)

    if backend is None:
        import pt_v5_kingston as v5k
        if service is None:
            service = v5k._make_service()
        backend = service.backend(k6.BACKEND_NAME)

    pm = generate_preset_pass_manager(
        backend=backend, optimization_level=3, seed_transpiler=7)
    tci = list(pm.run([c["circuit"] for c in circuits]))
    per = {}
    total_2q = 0
    max_2q = 0
    for c, tc in zip(circuits, tci):
        ops = {str(gn): int(gn_cnt)
               for gn, gn_cnt in tc.count_ops().items()}
        n2q = count_2q(ops)
        per[c["name"]] = {"ops": ops, "n_2q": n2q}
        total_2q += n2q
        max_2q = max(max_2q, n2q)
    verdict = "ISA_OK" if (max_2q <= k6.ISA_CEILINGS["per_circuit_2q_max"]
                           and total_2q <= k6.ISA_CEILINGS["total_2q_max"]
                           ) else "ISA_BUDGET_FAIL"
    doc = {
        "experiment": k6.EXPERIMENT,
        "backend": k6.BACKEND_NAME,
        "optimization_level": 3,
        "transpile_seed": 7,
        "n_circuits": len(circuits),
        "total_two_q": int(total_2q),
        "max_two_q": int(max_2q),
        "isa_ceiling": dict(k6.ISA_CEILINGS),
        "per_circuit_two_q": per,
        "verdict": verdict,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    if verdict == "ISA_OK":
        k6.validate_isa_gate(doc)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    print("ISA gate:", verdict, "| total 2q:", total_2q, "| max:", max_2q,
          "| prereg md5:", k6.PREREG_MD5)
    return doc


if __name__ == "__main__":
    run_stage()