# -*- coding: utf-8 -*-
"""probe11 — Error-Aware-Nachweis fuer den x-Zweig-Delta (read-only).

Hypothese: die 4 ops-Divergenzen der UNFORCED gegen S1 (nur x-Zaehl-Delta,
two_q bitgleich) stammen aus der error-gewichteten 1q/2q-Synthese —
Eingaben bit-identisch (n_d/m ganzzahlig), Fez-Kalibrier-Refresh seit
0/116-Re-Verifikation 2026-09-28.  Beweis-Design: je gebruchtem Circuit
ZWEI Transpiles desselben logischen Inputs gegen (a) echtes Target vs
(b) Target-Kopie mit ALLEN error=0.0.  Differieren die ops => Fehlerkarte
ist die Branch-Koordinate.  KEIN Artefakt-Write, KEIN QPU-Job.
"""
import copy
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

BROKEN = ["ladder_q3_d3_181_r2", "ladder_q3_d3_181_r4",
          "ladder_q3_d3_181_r8", "ctrl_composite_P467_d5"]
MATCHING = ["ladder_q5_d5_467_r2", "ctrl_uniform_q5"]

out = {"backend": None, "zero_probe": {}, "matching_probe": {}}

backend = pqr.get_backend(pqr.get_service())
out["backend"] = str(backend.name)

pts, cal, _ladder = p48.eval_grid()
circuits = h3a.build_hardware_circuit_set(pts=pts, cal=cal)
by_name = {c["name"]: c for c in circuits}

def t2q(tc):
    cc = tc.count_ops()
    return int(cc.get("cz", 0) + cc.get("cx", 0))

def ops_of(tc):
    return {str(gn): int(cn) for gn, cn in tc.count_ops().items()}

# Fehler-null-Target-Kopie (DEEPCOPY der Anweisungs-Properties)
target = copy.deepcopy(backend.target)
n_err = 0
for inst_name in target.operation_names:
    props = target[inst_name]
    for qargs in list(props.keys()):
        entry = props[qargs]
        if entry is not None and entry.error is not None and entry.error > 0.0:
            entry.error = 0.0
            n_err += 1
out["zeroed_error_entries"] = int(n_err)

pm = generate_preset_pass_manager(backend=backend, optimization_level=3,
                                  seed_transpiler=p48.TRANSPILE_SEED)
pm0 = generate_preset_pass_manager(target=target, optimization_level=3,
                                   seed_transpiler=p48.TRANSPILE_SEED)

with open("pt_ram_q_isa3_report.json", encoding="utf-8") as fh:
    s1 = json.load(fh)["per_circuit"]

for n in BROKEN + MATCHING:
    tc_real = pm.run([by_name[n]["circuit"]])[0]
    tc_zero = pm0.run([by_name[n]["circuit"]])[0]
    o_real, o_zero = ops_of(tc_real), ops_of(tc_zero)
    rec = {"real_ops": o_real, "zero_ops": o_zero,
           "real_x": o_real.get("x", 0), "zero_x": o_zero.get("x", 0),
           "real_two_q": t2q(tc_real), "zero_two_q": t2q(tc_zero),
           "s1_x": s1[n]["ops"].get("x", 0), "s1_two_q": s1[n]["two_q"],
           "real_eq_s1": o_real == s1[n]["ops"],
           "zero_eq_s1": o_zero == s1[n]["ops"],
           "real_eq_zero": o_real == o_zero,
           "layout_real": list(tc_real.layout.initial_index_layout(
               filter_ancillas=True)),
           "layout_zero": list(tc_zero.layout.initial_index_layout(
               filter_ancillas=True))}
    grp = "zero_probe" if n in BROKEN else "matching_probe"
    out[grp][n] = rec

# Klassen-Schuessel: fehlt der real-vs-zero-Unterschied ueberhaupt?
out["any_real_vs_zero_ops_diff"] = any(
    rec["real_ops"] != rec["zero_ops"]
    for rec in list(out["zero_probe"].values())
    + list(out["matching_probe"].values()))

with open("scratches/probe11_out.json", "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, ensure_ascii=False, default=repr)

print("backend:", out["backend"])
print("zeroed_error_entries:", out["zeroed_error_entries"])
print("any_real_vs_zero_ops_diff:", out["any_real_vs_zero_ops_diff"])
for grp, names in (("zero_probe", BROKEN), ("matching_probe", MATCHING)):
    for n in names:
        r = out[grp][n]
        print("%s %s: real_x=%d zero_x=%d s1_x=%d zero_eq_s1=%s "
              "real_eq_zero=%s layout_real=%s"
              % (grp, n, r["real_x"], r["zero_x"], r["s1_x"],
                 r["zero_eq_s1"], r["real_eq_zero"], r["layout_real"]))