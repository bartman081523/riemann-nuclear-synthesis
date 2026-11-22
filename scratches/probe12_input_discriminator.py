# -*- coding: utf-8 -*-
"""probe12 — Diskriminator: logischer Input vs Target-Struktur (read-only).

Vergleicht die 6 Probe-Circuits GEBAUT (a) via gefrorenem Default-Grid
(h3a.build_hardware_circuit_set() ohne Args == 044/Legacy-Pfad, suite-
bewiesen bit-identisch) vs (b) via 055-Grid (pts/cal explizit):
(1) StatePreparation-Parameter bit-exakt + n_d/m Integer-Listen;
(2) Transpile der FROZEN-gebauten logischen Circuits gegen das ECHTE
    aktive Target (opt 3, seed 7) -> ops vs S1.  Traefft der Frozen-Pfad
    S1 (kein x) waehrend der 055-Pfad abweicht, liegt der Delta IM INPUT
    (cb3f9c6-Klasse); trifft BEIDE abweichend S1, ist der Delta
    Target-Struktur-Refresh.  KEIN Artefakt-Write, KEIN QPU-Job.
"""
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

import numpy as np  # noqa: E402
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager  # noqa: E402

import pt_ram_q_hardware3_aer as h3a  # noqa: E402
import pt_ram_q_prio48 as p48  # noqa: E402
import pt_ram_q_prio48_qpu as pqr  # noqa: E402

NAMES = ["ladder_q3_d3_181_r2", "ladder_q3_d3_181_r4",
         "ladder_q3_d3_181_r8", "ladder_q5_d5_467_r2",
         "ctrl_composite_P467_d5", "ctrl_uniform_q5"]

out = {"backend": None, "params_equal": {}, "n_d_equal": {},
       "frozen_transpile_vs_s1": {}, "fresh_transpile_vs_s1": {}}

backend = pqr.get_backend(pqr.get_service())
out["backend"] = str(backend.name)

# (a) gefrorenes Default-Grid
c_frozen = {c["name"]: c for c in h3a.build_hardware_circuit_set()}
# (b) 055-Grid
pts, cal, _ladder = p48.eval_grid()
c_fresh = {c["name"]: c for c in h3a.build_hardware_circuit_set(pts=pts, cal=cal)}

def prep_params(qc):
    arrs = []
    for inst in qc.data:
        if inst.operation.name == "state_preparation":
            flat = np.asarray(inst.operation.params, dtype=complex).ravel()
            arrs.append([[float(v.real), float(v.imag)] for v in flat])
    return arrs

for n in NAMES:
    fa, fb = prep_params(c_frozen[n]["circuit"]), prep_params(c_fresh[n]["circuit"])
    out["params_equal"][n] = fa == fb
    ndf = c_frozen[n].get("n_d") or c_frozen[n].get("n_counts")
    ndb = c_fresh[n].get("n_d") or c_fresh[n].get("n_counts")
    out["n_d_equal"][n] = (ndf == ndb)

pm = generate_preset_pass_manager(backend=backend, optimization_level=3,
                                  seed_transpiler=p48.TRANSPILE_SEED)
with open("pt_ram_q_isa3_report.json", encoding="utf-8") as fh:
    s1 = json.load(fh)["per_circuit"]

for tag, store in (("frozen", c_frozen), ("fresh", c_fresh)):
    key = "frozen_transpile_vs_s1" if tag == "frozen" else "fresh_transpile_vs_s1"
    for n in NAMES:
        tc = pm.run([store[n]["circuit"]])[0]
        ops = {str(gn): int(cn) for gn, cn in tc.count_ops().items()}
        t2q = int(tc.count_ops().get("cz", 0) + tc.count_ops().get("cx", 0))
        out[key][n] = {
            "ops": ops, "x": ops.get("x", 0), "two_q": t2q,
            "s1_ops": s1[n]["ops"], "s1_x": s1[n]["ops"].get("x", 0),
            "s1_two_q": s1[n]["two_q"],
            "ops_eq_s1": ops == s1[n]["ops"],
            "two_q_eq_s1": t2q == int(s1[n]["two_q"]),
            "layout": list(tc.layout.initial_index_layout(filter_ancillas=True))}

with open("scratches/probe12_out.json", "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, ensure_ascii=False, default=repr)

print("backend:", out["backend"])
print("params_equal:", out["params_equal"])
print("n_d_equal:", out["n_d_equal"])
for n in NAMES:
    f = out["frozen_transpile_vs_s1"][n]
    print("FROZEN %s ops_eq_s1=%s two_q_eq=%s x(frz/s1)=%d/%d layout=%s"
          % (n, f["ops_eq_s1"], f["two_q_eq_s1"], f["x"], f["s1_x"], f["layout"]))
for n in NAMES:
    f = out["fresh_transpile_vs_s1"][n]
    print("FRESH  %s ops_eq_s1=%s two_q_eq=%s x(frs/s1)=%d/%d layout=%s"
          % (n, f["ops_eq_s1"], f["two_q_eq_s1"], f["x"], f["s1_x"], f["layout"]))