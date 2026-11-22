# -*- coding: utf-8 -*-
"""smoke — p48qpu.transpile_forced END-TO-END offline (GenericBackendV2 27,
Ceilings relaxiert, s1_anchor aus).  KEIN File-Write, KEIN Token."""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from qiskit.providers.fake_provider import GenericBackendV2

import pt_ram_q_hardware3_aer as h3a
import pt_ram_q_prio48 as p48
import pt_ram_q_prio48_qpu as p48qpu
import pt_ram_q6_kingston as k6

# Ceilings NUR im Smoke relaxiert (echtes Gate: 120/6000)
p48qpu.CEILINGS["per_circuit_2q_max"] = 10 ** 9
p48qpu.CEILINGS["total_2q_max"] = 10 ** 9

out = {}
pts, cal, ladder = p48.eval_grid()
circuits = h3a.build_hardware_circuit_set(pts=pts, cal=cal)
assert len(circuits) == p48.N_CIRCUITS, len(circuits)
assert len(circuits) * h3a.SHOTS == p48.TOTAL_SHOTS

if os.path.exists(_ROOT + "/scratches/smoke_report.json"):
    with open(_ROOT + "/scratches/smoke_report.json", encoding="utf-8") as fh:
        report = json.load(fh)
    with open(_ROOT + "/scratches/smoke_gate.json", encoding="utf-8") as fh:
        gate = json.load(fh)
    totals = {"isa_2q_total": gate["total_two_q"],
              "isa_2q_max": gate["max_two_q"]}
    tci = None
else:
    backend = GenericBackendV2(num_qubits=27,
                               basis_gates=["rz", "sx", "x", "ecr"])
    tci, totals, report, gate = p48qpu.transpile_forced(
        backend, circuits, s1_report_path=None)

out["n_tci"] = len(tci) if tci is not None else report["n_circuits"]
out["totals"] = totals
out["report_status"] = report["status"]
out["report_keys"] = sorted(report)
out["report_n"] = report["n_circuits"]
out["total_two_q"] = report["total_two_q"]
out["max_two_q"] = report["max_two_q"]
out["row_assignment_lens"] = {arm: len(v) for arm, v in
                              report["row_assignment"].items()}
out["per_circuit_n"] = len(report["per_circuit"])
forced = {n: v for n, v in report["per_circuit"].items()
          if v["layout_source"] == "forced"}
auto = {n: v for n, v in report["per_circuit"].items()
        if v["layout_source"] == "auto"}
out["forced_n"] = len(forced)
out["auto_n"] = len(auto)
out["auto_names"] = sorted(auto)
out["row_c_prime"] = report["row_c_prime"]
out["ceiling_check"] = report["ceiling_check"]
out["gate_keys"] = sorted(gate)
out["gate_total_eq_report"] = (gate["total_two_q"] == report["total_two_q"]
                               == totals["isa_2q_total"])
out["gate_max_eq_report"] = (gate["max_two_q"] == report["max_two_q"]
                             == totals["isa_2q_max"])
out["k6_validate"] = k6.validate_isa_gate(gate, n_circuits=160)
with open(_ROOT + "/scratches/smoke_report.json", "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=1, ensure_ascii=False)
with open(_ROOT + "/scratches/smoke_gate.json", "w", encoding="utf-8") as fh:
    json.dump(gate, fh, indent=1, ensure_ascii=False)
# JSON-Serialisierbarkeit (Report + Gate)
out["report_json_ok"] = bool(json.dumps(report))
out["gate_json_ok"] = bool(json.dumps(gate))
out["per_circuit_fields"] = sorted(next(iter(forced.values())))
out["determinismus_recheck"] = "skip (Zeit)"

# rows_cprime-Units (synthetisch)
pcd = {"struct_q3_d3_181_r0": {"n_2q": 10, "arm": "q3_d3", "set": "verdict",
                               "P": 181},
       "struct_q3_d3_181_r1": {"n_2q": 12, "arm": "q3_d3",
                               "set": "verdict", "P": 181},
       "struct_q3_d3_181_r2": {"n_2q": 12, "arm": "q3_d3",
                               "set": "verdict", "P": 181},
       "loschmidt_q3_d3_181": {"n_2q": 14, "arm": "q3_d3", "set": "verdict",
                               "P": 181}}
rep_rows = {"q3_d3": [{"row": ["verdict", 181], "slot_index": 0,
                       "slot": [1, 2], "fallback_used": False,
                       "attempts": []}],
            "q5_d5": [{"row": ["verdict", 467], "slot_index": 0,
                       "slot": [3, 4, 5], "fallback_used": False,
                       "attempts": []}]}
cpf = {"verdict|q3_d3|181": 3.5}
s1pc = {"struct_q3_d3_181_r0": {"two_q": 10}, "struct_q3_d3_181_r1":
        {"two_q": 12}, "struct_q3_d3_181_r2": {"two_q": 12},
        "loschmidt_q3_d3_181": {"two_q": 14}}
rc = p48qpu.rows_cprime(pcd, rep_rows, cpf, s1pc)
r = rc["verdict|q3_d3|181"]
out["cprime_unit"] = {"mean_n2q_055": r["mean_n2q_055"],
                      "mean_two_q_s1": r["mean_two_q_s1"],
                      "ratio_bit": r["ratio_2q"],
                      "c_prime": r["c_prime"],
                      "delta_c_bit": r["delta_c_vs_cP"]}
assert r["ratio_2q"] == 1.0 and r["delta_c_vs_cP"] == 0.0

s1pc2 = dict(s1pc)
s1pc2["loschmidt_q3_d3_181"] = {"two_q": 7}   # 10+12+12 = 34/4 = 8.5
rc2 = p48qpu.rows_cprime(pcd, rep_rows, cpf, s1pc2)
r2 = rc2["verdict|q3_d3|181"]
out["cprime_unit_shift"] = {"ratio": r2["ratio_2q"],
                            "c_prime": r2["c_prime"],
                            "delta": r2["delta_c_vs_cP"]}
assert r2["ratio_2q"] == 12.0 / 10.25

s1pc3 = {"struct_q3_d3_181_r0": {"two_q": 0}, "struct_q3_d3_181_r1":
        {"two_q": 0}, "struct_q3_d3_181_r2": {"two_q": 0},
        "loschmidt_q3_d3_181": {"two_q": 0}}
pcd0 = {k: dict(v, n_2q=0) for k, v in pcd.items()}
rc3 = p48qpu.rows_cprime(pcd0, rep_rows, cpf, s1pc3)
out["cprime_unit_null"] = {"ratio": rc3["verdict|q3_d3|181"]["ratio_2q"],
                           "delta": rc3["verdict|q3_d3|181"]["delta_c_vs_cP"]}
assert rc3["verdict|q3_d3|181"]["ratio_2q"] == 1.0

err = None
try:
    p48qpu.rows_cprime(pcd, rep_rows, cpf,
                       {"struct_q3_d3_181_r0": {"two_q": 0},
                        "struct_q3_d3_181_r1": {"two_q": 0},
                        "struct_q3_d3_181_r2": {"two_q": 0},
                        "loschmidt_q3_d3_181": {"two_q": 0},
                        "struct_q3_d3_181_x": {"n_2q": 5, "arm": "q3_d3",
                                               "set": "verdict", "P": 181}})
except RuntimeError as exc:
    err = str(exc)[:60]
out["cprime_unit_degen_err"] = err

# Ladder-Grund-Zweig (frische Reihen ohne S1-Praedecessor)
pcd2 = {n: {"n_2q": 9, "arm": "q5_d5", "set": "cal", "P": 479}
        for n in ("calstruct_q5_d5_479_r0", "calstruct_q5_d5_479_r1",
                  "calstruct_q5_d5_479_r2", "calloschmidt_q5_d5_479")}
rep_rows5 = {"q3_d3": [], "q5_d5": [{"row": ["cal", 479], "slot_index": 2,
                                    "slot": [9, 8, 7], "fallback_used": False,
                                    "attempts": []}]}
rl = p48qpu.rows_cprime(pcd2, rep_rows5, {"cal|q5_d5|479": 2.25}, s1pc)
e = rl["cal|q5_d5|479"]
out["cprime_ladder_missing"] = {"c_prime": e["c_prime"],
                                "grund": e.get("grund", "")}
assert e["c_prime"] is None and "keine S1-Namen" in e.get("grund", "")
rc4 = p48qpu.rows_cprime(pcd2, rep_rows5, {"cal|q5_d5|479": 2.25},
                         {n: {"two_q": 8} for n in pcd2})
e4 = rc4["cal|q5_d5|479"]
out["cprime_ladder_ok"] = {"c_prime": e4["c_prime"],
                           "ratio_bit": e4["ratio_2q"],
                           "delta_c_bit": e4["delta_c_vs_cP"]}
assert e4["ratio_2q"] == 9.0 / 8.0
assert e4["c_prime"] == 2.53125 and e4["delta_c_vs_cP"] == 0.28125

print(json.dumps(out, indent=1, ensure_ascii=False, default=repr))