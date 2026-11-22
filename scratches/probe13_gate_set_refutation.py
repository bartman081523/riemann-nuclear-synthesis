# -*- coding: utf-8 -*-
"""probe13 — Ziel-Nachweis: 1q-Gate-Set-Deklaration (x/xslow) waehlt die
Euler-Branch (read-only).

Entfernt aus einer Target-Kopie die Deklarationen von 'x' und 'xslow'
(klassisches ZSX-Gefuege, wie es S1 zur ISA3-Zeit traf) und transpiliert
die 4 ops-Divergenten + 1 Passenden.  Traefft das ops-Set dann S1
(kein x) => Mechanismus KONKRET: Fez-1q-Gefuege-Refresh seit 2026-09-28
fuehrt ZSXX ein und kippt den equal-rank-Euler-Zweig.  KEIN QPU-Job.
"""
import copy
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from qiskit.transpiler import Target  # noqa: E402
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager  # noqa: E402

import pt_ram_q_hardware3_aer as h3a  # noqa: E402
import pt_ram_q_prio48 as p48  # noqa: E402
import pt_ram_q_prio48_qpu as pqr  # noqa: E402

NAMES = ["ladder_q3_d3_181_r2", "ladder_q3_d3_181_r4",
         "ladder_q3_d3_181_r8", "ctrl_composite_P467_d5",
         "ladder_q5_d5_467_r2"]

out = {}
backend = pqr.get_backend(pqr.get_service())
out["backend"] = str(backend.name)

target = copy.deepcopy(backend.target)
removed = []
for inst_name in ("x", "xslow"):
    if inst_name in target.operation_names:
        props = dict(target[inst_name])
        target.delete_instruction(inst_name)
        removed.append(inst_name)
out["removed"] = removed
out["x_still_in_names"] = "x" in target.operation_names

pts, cal, _ladder = p48.eval_grid()
by_name = {c["name"]: c for c in
           h3a.build_hardware_circuit_set(pts=pts, cal=cal)}

pm = generate_preset_pass_manager(backend=backend, optimization_level=3,
                                  seed_transpiler=p48.TRANSPILE_SEED)
pm_zsx = generate_preset_pass_manager(target=target, optimization_level=3,
                                      seed_transpiler=p48.TRANSPILE_SEED)
with open("pt_ram_q_isa3_report.json", encoding="utf-8") as fh:
    s1 = json.load(fh)["per_circuit"]

res = {}
for n in NAMES:
    tc = pm_zsx.run([by_name[n]["circuit"]])[0]
    ops = {str(gn): int(cn) for gn, cn in tc.count_ops().items()}
    t2q = int(tc.count_ops().get("cz", 0) + tc.count_ops().get("cx", 0))
    res[n] = {"ops": ops, "x": ops.get("x", 0), "two_q": t2q,
              "s1_x": s1[n]["ops"].get("x", 0), "s1_two_q": s1[n]["two_q"],
              "ops_eq_s1": ops == s1[n]["ops"],
              "two_q_eq_s1": t2q == int(s1[n]["two_q"]),
              "layout": list(tc.layout.initial_index_layout(
                  filter_ancillas=True))}
out["zsx_probe"] = res

with open("scratches/probe13_out.json", "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, ensure_ascii=False, default=repr)

print("backend:", out["backend"], "removed:", out["removed"])
for n, r in res.items():
    print("%s: x=%d (S1 %d) ops_eq_s1=%s two_q_eq=%s layout=%s"
          % (n, r["x"], r["s1_x"], r["ops_eq_s1"], r["two_q_eq_s1"],
             r["layout"]))