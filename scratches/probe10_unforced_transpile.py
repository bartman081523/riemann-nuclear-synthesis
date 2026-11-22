# -*- coding: utf-8 -*-
"""probe10 — Mechanismus-Analyse der Gate-Anchor-Verletzung (read-only).

Vergleicht frische Auto-Layout-Transpile (opt 3, seed 7) der 12 UNFORCED
055-Circuits gegen pt_ram_q_isa3_report.json (S1/044, 116er-Batch):
(a) Batch-of-12 wie im Gate-Code; (b) Singles (Batch=1) fuer die 4
gebrochenen + 1 Kontroll-Passenden. KEIN Artefakt-Write, KEIN QPU-Job.
Meldet ops-Delta + Layout-Bits; schreibt Probe-Output nach scratches/.
"""
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager  # noqa: E402

import pt_ram_q_hardware3_aer as h3a  # noqa: E402
import pt_ram_q_prio48 as p48  # noqa: E402
import pt_ram_q_prio48_qpu as pqr  # noqa: E402

TRANSPILE_SEED = p48.TRANSPILE_SEED

out = {}
backend = pqr.get_backend(pqr.get_service())
out["backend"] = str(backend.name)


def fresh_ops(tcs):
    res = []
    for tc in tcs:
        ops = {str(gn): int(cn) for gn, cn in tc.count_ops().items()}
        layout = None
        if tc.layout is not None:
            layout = list(tc.layout.initial_index_layout(
                filter_ancillas=True))
        res.append({"ops": ops,
                    "two_q": tc.count_ops().get("cz", 0)
                    + tc.count_ops().get("cx", 0),
                    "depth": int(tc.depth()),
                    "layout": layout})
    return res


pts, cal, _ladder = p48.eval_grid()
circuits = h3a.build_hardware_circuit_set(pts=pts, cal=cal)
unforced = [c for c in circuits
            if c["name"] in {
                "ladder_q3_d3_181_r2", "ladder_q3_d3_181_r4",
                "ladder_q3_d3_181_r8", "ladder_q5_d5_467_r2",
                "ladder_q5_d5_467_r4", "ladder_q5_d5_467_r8",
                "ctrl_composite_P181_d3", "ctrl_composite_P467_d5",
                "ctrl_uniform_q3", "ctrl_uniform_q5", "cal_2q", "cal_3q"}]
out["builder_order"] = [c["name"] for c in unforced]
assert len(unforced) == 12, out["builder_order"]

# (a) Batch-of-12 (exakt der Gate-Code-Situation)
pm = generate_preset_pass_manager(
    backend=backend, optimization_level=3, seed_transpiler=TRANSPILE_SEED)
batch12 = fresh_ops(pm.run([c["circuit"] for c in unforced]))
out["batch12"] = dict(zip([c["name"] for c in unforced], batch12))

# (b) Singles fuer 5 Kontrollen (4 gebrochen im 12er-Batch + 1 q5-Echo)
singles_names = ["ladder_q3_d3_181_r2", "ladder_q3_d3_181_r4",
                 "ladder_q3_d3_181_r8", "ladder_q5_d5_467_r2",
                 "ctrl_composite_P467_d5"]
singles = {}
by_name = {c["name"]: c for c in unforced}
for n in singles_names:
    tc = pm.run([by_name[n]["circuit"]])[0]
    singles[n] = fresh_ops([tc])[0]
out["singles"] = singles
for n in singles:
    out["singles_eq_batch12_" + n] = out["singles"][n]["ops"] \
        == out["batch12"][n]["ops"]

# Vergleich gegen S1-Report
with open("pt_ram_q_isa3_report.json", encoding="utf-8") as fh:
    s1 = json.load(fh)["per_circuit"]
cmp = {}
for n, b in out["batch12"].items():
    e = s1[n]
    cmp[n] = {
        "s1_ops": e["ops"], "fresh_ops": b["ops"],
        "s1_two_q": e["two_q"], "fresh_two_q": b["two_q"],
        "ops_equal": b["ops"] == e["ops"],
        "two_q_equal": b["two_q"] == e["two_q"],
    }
out["cmp_s1"] = cmp
out["broken"] = [n for n, v in cmp.items() if not v["ops_equal"]]

# Input-Circuit-Identitaets-Proxy: ops des LOGISCHEN (untranspilierten)
# Circuits je Name + QDEP
out["logical_ops"] = {c["name"]: {str(gn): int(cn) for gn, cn
                                  in c["circuit"].count_ops().items()}
                      for c in unforced}

with open("scratches/probe10_out.json", "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, ensure_ascii=False, default=repr)
print("backend:", out["backend"])
print("builder_order:", out["builder_order"])
print("broken(ops vs S1):", out["broken"])
for n, v in cmp.items():
    print(("OK  " if v["ops_equal"] else "DIFF"), n,
          "s1_two_q", v["s1_two_q"], "fresh_two_q", v["fresh_two_q"])
for n in singles_names:
    print("singles==batch12:", n, out["singles_eq_batch12_" + n])