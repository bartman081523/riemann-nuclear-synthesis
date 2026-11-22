# -*- coding: utf-8 -*-
"""Scratch: isa3-Smoke auf FakeFez (offline, kein Netz)."""
import pt_ram_q_isa3 as isa_mod
from qiskit_ibm_runtime.fake_provider import FakeFez

_isa, rep = isa_mod.isa_report(FakeFez())
print("n_circuits:", rep["n_circuits"])
print("total_two_q:", rep["total_two_q"], "| max_two_q:", rep["max_two_q"])
print("kinds:", sorted({e["kind"] for e in rep["per_circuit"].values()}))
pc = rep["per_circuit"]
for r in (2, 4, 8):
    print(f"ladder q3 181 r{r}:", pc[f"ladder_q3_d3_181_r{r}"]["two_q"],
          "| q5 467 r{0}:".format(r), pc[f"ladder_q5_d5_467_r{r}"]["two_q"])
print("ladder r1 existiert:", "ladder_q3_d3_181_r1" in pc)
print("loschmidt q3 181 two_q:", pc["loschmidt_q3_d3_181"]["two_q"],
      "| q5 467:", pc["loschmidt_q5_d5_467"]["two_q"])
sets = sorted({e.get("set") for e in pc.values() if e.get("set")})
print("sets:", sets)
ctrl = {k: (pc[k]["set"], pc[k]["two_q"]) for k in pc if pc[k]["kind"] == "negative_control"}
print("ctrl (set, 2q):", ctrl)
check = isa_mod.ceiling_check(rep)
print("ceiling ok:", check["ok"], "| per_max:", check["per_circuit_max"],
      "| total_max:", check["total_max"])
doc = isa_mod.run_isa_report(backend_getter=FakeFez, results_path=None)
print("verdict:", doc["verdict"], "| backend:", doc["backend"],
      "| experiment:", doc["experiment"], "| hypothesis:", doc["hypothesis"],
      "| seed:", doc["transpile_seed"], "| opt:", doc["optimization_level"])
print("run_config md5:", doc["run_config_frozen"]["md5"])
print("ceilings:", doc["isa_ceilings"])
