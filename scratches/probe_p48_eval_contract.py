# -*- coding: utf-8 -*-
"""probe_p48_eval_contract.py — READ-ONLY-Verifikation der 055-Eval-Firmware.

Kein Schreiben, kein Token.  Prueft:
  1. k6.validate_isa_gate — verpflichtete Keys (Pass-Vertrag fuer das 055-Gate).
  2. cP_freeze-Key-Format + prediction_freeze.points/kalibrier_bein.points.
  3. 044-Stage-3: b_p_kalibrier_konsistenz komplett (ok:false-Keys + Werte) und
     diag_results == heutiges 055 b_P (bistabler Zweig, bit-exakt).
  4. K2-Stage-3: Konsistenz-Block (613-Keys, diffs) — Vorladungs-Quelle 2.
  5. Modul-Oberflaechen (p48/p48qpu/h3a/h3/e2/qpu3/k2-Konstanten).
  6. S1-Eval: punkte-Key-Schema + res_v3/c_p je 13 Verdict-Reihen.
  7. S1-ISA-Report: two_q fuer die 055-Reihen-Circuits (c'-Quelle).
"""
import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def load(path):
    with open(os.path.join(_ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


out = {}

# 1) k6.validate_isa_gate -------------------------------------------------
import inspect
import pt_ram_q6_kingston as k6
src = inspect.getsource(k6.validate_isa_gate)
out["k6_validate_source_head"] = src[:2200]

# 2) cP_freeze / prediction_freeze / kalibrier_bein -----------------------
pr = load("pt_ram_q_prio48_prereg.json")
cpk = sorted(pr["prediction_freeze"]["cP_freeze"])
out["cp_freeze_n"] = len(cpk)
out["cp_freeze_sample"] = cpk[:4] + cpk[-4:]
out["pf_points_type"] = type(pr["prediction_freeze"]["points"]).__name__
pf = pr["prediction_freeze"]["points"]
out["pf_points"] = pf if isinstance(pf, dict) else list(pf)
kb = pr["kalibrier_bein"]["points"]
out["kb_points"] = kb if isinstance(kb, dict) else list(kb)
out["c1_anchors_keys"] = sorted(pr["session_anchors"])

# 3) 044-Stage-3 b_p_kalibrier_konsistenz ---------------------------------
s3 = load("pt_ram_q_stage3_results.json")
kons044 = s3["b_p_kalibrier_konsistenz"]
out["k044_keys"] = sorted(kons044)
out["k044_bad"] = {k: {kk: v[kk] for kk in ("abs_diff", "diag_results",
                                            "stage3_grid", "ok")}
                   for k, v in sorted(kons044.items()) if not v["ok"]}

# heutiges 055 b_P an denselben Keys
s3p = load("pt_ram_q_prio48_stage3_results.json")
bp55 = s3p["b_p"]
cross = {}
for bad in sorted(k for k, v in kons044.items() if not v["ok"]):
    arm, P = bad.split("|")
    k55 = "cal|%s|%s" % (arm, P)
    cross[bad] = {
        "bP_055": bp55[k55],
        "diag_results_044": kons044[bad]["diag_results"],
        "bistable_bit_equal": bp55[k55] == kons044[bad]["diag_results"],
        "abs_diff_055": s3p["b_p_konsistenz"][k55]["abs_diff"],
        "abs_diff_044": kons044[bad]["abs_diff"],
        "diff_bit_equal": s3p["b_p_konsistenz"][k55]["abs_diff"]
        == kons044[bad]["abs_diff"],
    }
out["bistable_cross"] = cross
out["s055_bad_keys"] = sorted(k for k, v in s3p["b_p_konsistenz"].items()
                              if not v["ok"])
out["s055_bad_vals"] = {k: s3p["b_p_konsistenz"][k]["abs_diff"]
                        for k in out["s055_bad_keys"]}

# 4) K2-Stage-3 Konsistenz (613-Keys) ------------------------------------
for cand in ("pt_ram_q6_k2_stage3_results.json",):
    if os.path.exists(os.path.join(_ROOT, cand)):
        k2s3 = load(cand)
        k2k = k2s3.get("b_p_konsistenz", {})
        out["k2_stage3_path"] = cand
        out["k2_konsistenz_keys"] = sorted(k2k)
        bad = {k: {kk: v[kk] for kk in ("abs_diff", "stage3_grid",
                                        "stage3_044", "ok")}
               for k, v in k2k.items() if not v["ok"]}
        out["k2_konsistenz_bad"] = bad
        # 613-Kreuzcheck mit den 055-Verdict-Diffs
        cross613 = {}
        for arm in ("q3_d3", "q5_d5"):
            k55 = "verdict|%s|613" % arm
            k2key = "cal|%s|613" % arm
            if k2key in k2k:
                cross613[arm] = {
                    "bP_055": bp55[k55], "bP_k2": k2k[k2key]["stage3_grid"],
                    "bp_bit_equal": bp55[k55] == k2k[k2key]["stage3_grid"],
                    "diff_055": s3p["b_p_konsistenz"][k55]["abs_diff"],
                    "diff_k2": k2k[k2key]["abs_diff"],
                    "diff_bit_equal": (s3p["b_p_konsistenz"][k55]["abs_diff"]
                                       == k2k[k2key]["abs_diff"]),
                }
        out["k2_cross_613"] = cross613
        break
else:
    out["k2_stage3_path"] = "KEINE Quelle gefunden"

# 5) Modul-Oberflaechen ---------------------------------------------------
import pt_ram_q_prio48 as p48
import pt_ram_q_prio48_qpu as p48q

names_p48 = [n for n in dir(p48) if not n.startswith("__")]
out["p48_surface"] = {n: (repr(getattr(p48, n))[:90])
                       for n in names_p48 if not callable(getattr(p48, n))}
out["p48_fns"] = [n for n in names_p48 if callable(getattr(p48, n))
                  and not n.startswith("__")]

import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_aer as h3a
import pt_ram_q_hardware2_eval as e2
import pt_ram_q_hardware3_qpu as qpu3
need_h3 = ["SHOTS", "KAPPA_CEILING", "LADDER_REPEATS", "V1",
           "MEASURED_UNION", "CAL_Q5_POINTS"]
out["h3_needed"] = {n: repr(getattr(h3, n, None))[:70] for n in need_h3}
need_h3a = ["NQ_BY_ARM", "TRANSPILE_SEED", "W_A", "W_B_PRIME",
            "BP_KONSISTENZ_TOL", "STRESS_GRID_P1", "RO_STRESS",
            "pkey", "ratio_from_counts", "p0_fraction", "fit_b_p",
            "exact_point_level", "ratio_ro_exact", "fit_echo_ladder",
            "ladder_anchor", "build_hardware_circuit_set", "share_hw_folded",
            "RESULTS_PATH"]
out["h3a_needed"] = {n: (repr(getattr(h3a, n))[:110]
                         if callable(getattr(h3a, n))
                         else repr(getattr(h3a, n))[:110])
                     for n in need_h3a}
out["e2_needed"] = {n: repr(getattr(e2, n, None))
                    for n in ("T3_TOL", "T6_MASS_TOL", "STAGE2_PATH")}
out["qpu3_needed"] = {n: type(getattr(qpu3, n, None)).__name__
                      for n in ("counts_md5", "RAW_PATH")}

# 6) S1-Eval punkte-Schema -----------------------------------------------
s1 = load("pt_ram_q_hardware3_eval.json")
rows = sorted(s1["punkte"])
out["s1_punkte_n"] = len(rows)
out["s1_punkte_sample"] = rows[:3] + rows[-3:]
v1 = s1["punkte"]["verdict|q5_d5|673"]
out["s1_verdict_row_fields"] = sorted(v1)
out["s1_673_resv3_cP"] = (v1["res_v3"], v1["c_p"], v1["kappa_hat"],
                          v1["below_sharp"])

# 7) S1-ISA-Report two_q-Stichprobe --------------------------------------
s1rep = load("pt_ram_q_isa3_report.json")
pc = s1rep["per_circuit"]
probe_names = ["struct_q5_d5_673_r0", "loschmidt_q5_d5_673",
               "calstruct_q3_d3_197_r0", "calloschmidt_q3_d3_197"]
out["s1rep_two_q"] = {n: pc[n]["two_q"] for n in probe_names if n in pc}
out["s1rep_names_missing"] = [n for n in probe_names if n not in pc]

print(json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True))