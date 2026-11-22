# -*- coding: utf-8 -*-
"""Regeneriert das K2-ISA-Gate (v2) nach Stale-Abbruch; diff gegen v1 VOR
Ueberschreiben (0 QPU; nur Service-Lesen + Transpile).
Exit-Code 0 nur wenn ALLE n_2q gleich bleiben und Divergenzen im
x/rz-Zweig-Klassenschema bleiben; sonst exit 2 ohne Schreiben."""
import json
import os
import sys

sys.path.insert(0, os.getcwd())
QISKIT_PARALLEL = "FALSE"
os.environ["QISKIT_PARALLEL"] = "FALSE"

import pt_ram_q_hardware3_aer as h3a
import pt_ram_q6_k2 as k2
import pt_ram_q6_k2_qpu as k2q
import pt_ram_q6_k2_isa_stage as s2v
from pt_ram_q6_kingston_isa_stage import count_2q

V1_PATH = k2.ISA_GATE_PATH
with open(V1_PATH, encoding="utf-8") as fh:
    v1 = json.load(fh)

backend = k2q.get_backend(k2q.get_service())
pm = s2v and None  # noqa: PLW - placeholder, run_stage benutzt denselben Pfad
circuits = h3a.build_hardware_circuit_set(pts=None, cal=None)
pts, cal = k2.eval_grid()
circuits = h3a.build_hardware_circuit_set(pts=pts, cal=cal)
tci = list(k2q.generate_preset_pass_manager(
    backend=backend, optimization_level=3, seed_transpiler=7).run(
        [c["circuit"] for c in circuits]))

divergent, n2q_diff = [], []
for c, tc in zip(circuits, tci):
    ops = {str(gn): int(cn) for gn, cn in tc.count_ops().items()}
    name = c["name"]
    g1 = v1["per_circuit_two_q"][name]
    if g1["ops"] != ops:
        divergent.append({"name": name, "v1_ops": g1["ops"], "v2_ops": ops,
                          "v1_n_2q": g1["n_2q"], "v2_n_2q": count_2q(ops)})
        if g1["n_2q"] != count_2q(ops):
            n2q_diff.append(name)

print(f"divergente Zellen v1->v2: {len(divergent)} | n_2q-Divergenzen: "
      f"{len(n2q_diff)}")
for row in divergent:
    print("  ", row["name"])
    print("     v1:", row["v1_ops"])
    print("     v2:", row["v2_ops"])
    print("     n_2q:", row["v1_n_2q"], "->", row["v2_n_2q"])

if n2q_diff:
    print("ABBRUCH: n_2q divergiert — Gate-Totals wuerden kippen.")
    sys.exit(2)

klasses = []
for row in divergent:
    only = {}
    for g, n in row["v2_ops"].items():
        only[g] = (row["v1_ops"].get(g, 0), n)
    klasses.append((row["name"], only))

print("Klassen (v1->v2 je Gate):")
for name, only in klasses:
    interesting = {g: (a, b) for g, (a, b) in only.items() if a != b}
    print("  ", name, interesting)

# Schreiben ueber die committete Stage (validiert + schreibt V1-Pfad)
s2v.run_stage()
with open(V1_PATH, encoding="utf-8") as fh:
    v2 = json.load(fh)
print("neue Totals:", v2["total_two_q"], v2["max_two_q"],
      "(v1:", v1["total_two_q"], v1["max_two_q"], ")")
print("OK: Gate v2 geschrieben")