# -*- coding: utf-8 -*-
"""EXPERIMENT 051 (H-RAM-Q-6 Leg D2/D3) — Kingston-ISA-Gate-Stage für das
FRISCHE Run-4-Grid (0 QPU).

K2-Wrapper über die committeten D1-Bausteine (pt_ram_q6_kingston_isa_
stage): dieselbe Transpile-Route (Kingston, optimization_level 3,
transpile_seed 7) und dasselbe Gate-Schema, das der gefrorene Eval vom
isa_path erwartet; die Gate-Logik (ISA-GATE-Schema, 116-Circuit-Budget,
Ceilings) kommt aus k6.validate_isa_gate — experiment-agnostisch.

Unterschied zum D1-Bein: die Circuits kommen aus dem FRISCHEN Run-4-Grid
(k2.eval_grid → pts = Run-4-Verdict-P, cal = Run-3-Verdict-P als
Run-4-Kalibrier), Session-Anker 181/467 UNVERAENDERT (liegen im
Kalibrier-Bein; siehe _anchor_records-Vertrag).  Dokument-Binding auf
K2 (experiment 051, prereg_md5 ef702976 — der D2/D3-Freeze vor Messung).

0 QPU: NUR Transpile (Service-Lesen der Coupling-Map) — KEIN Job-
Submission.  TOKEN-DISZIPLIN: NUR TOKEN2 via pt_v5_kingston._make_
service; nie echo; TOKEN1 wird nie gelesen.
"""
import json
from datetime import datetime, timezone

from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

import pt_ram_q_hardware3_aer as h3a
import pt_ram_q6_k2 as k2
import pt_ram_q6_kingston as k6
from pt_ram_q6_kingston_isa_stage import count_2q

OUT_PATH = k2.ISA_GATE_PATH


def run_stage(backend=None, service=None, out_path=OUT_PATH, pts=None,
              cal=None):
    """Transpiliert die 116 frischen Circuits auf ibm_kingston und
    schreibt pt_ram_q6_k2_isa_gate.json (Verbrauch: h3e.t5-Schema)."""
    if pts is None and cal is None:
        pts, cal = k2.eval_grid()
    prereg = k2.load_frozen_prereg()
    circuits = h3a.build_hardware_circuit_set(pts=pts, cal=cal)
    assert len(circuits) == 116, len(circuits)

    if backend is None:
        import pt_v5_kingston as v5k
        if service is None:
            service = v5k._make_service()
        backend = service.backend(k2.BACKEND_NAME)

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
        "experiment": k2.EXPERIMENT, "hypothesis": k2.HYPOTHESIS,
        "leg": k2.LEG,
        "prereg_md5": k2.PREREG_MD5,
        "backend": k2.BACKEND_NAME,
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
    print("ISA gate (K2, frisches Grid):", verdict, "| total 2q:", total_2q,
          "| max:", max_2q, "| prereg md5:", k2.PREREG_MD5)
    return doc


if __name__ == "__main__":
    run_stage()