# -*- coding: utf-8 -*-
"""probe2 — Rest-Verifikation: K2-Quelle, Gate-Schema-Konstante, S1-Punkte."""
import inspect
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def load(path):
    with open(os.path.join(_ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


out = {}

import pt_ram_q6_kingston as k6
out["ISA_GATE_SCHEMA_KEYS"] = sorted(k6.ISA_GATE_SCHEMA_KEYS)

# K2-Stage-3aer/Results-Ort
for mod in ("pt_ram_q6_k2_stage3aer", "pt_ram_q6_k2", "pt_ram_q6_kingston"):
    try:
        m = __import__(mod)
        rp = getattr(m, "RESULTS_PATH", None)
        out["mod_results_path_%s" % mod] = rp
    except Exception as exc:
        out["mod_results_path_%s" % mod] = "ERR %s" % exc
hits = []
for f in sorted(os.listdir(_ROOT)):
    if "k2" in f and f.endswith(".json"):
        hits.append(f)
out["k2_json_files"] = hits

try:
    import pt_ram_q6_k2_stage3aer as k2s3
    out["k2s3.RESULTS_PATH"] = k2s3.RESULTS_PATH
    d = load(k2s3.RESULTS_PATH)
    out["k2s3_top_keys"] = sorted(d)
    kk = d.get("b_p_konsistenz", {})
    bad = {k: {kk2: v[kk2] for kk2 in ("abs_diff", "stage3_grid",
                                       "stage3_044", "ok")}
           for k, v in kk.items() if not v["ok"]}
    out["k2_konsistenz_bad"] = bad
    s3p = load("pt_ram_q_prio48_stage3_results.json")
    bp55 = s3p["b_p"]
    cross = {}
    for arm in ("q3_d3", "q5_d5"):
        k55, k2key = "verdict|%s|613" % arm, "cal|%s|613" % arm
        if k55 in bp55 and k2key in kk:
            cross[arm] = {
                "bP_055": bp55[k55],
                "bP_k2": kk[k2key]["stage3_grid"],
                "bp_bit_equal": bp55[k55] == kk[k2key]["stage3_grid"],
                "diff_055": s3p["b_p_konsistenz"][k55]["abs_diff"],
                "diff_k2": kk[k2key]["abs_diff"],
                "diff_bit_equal": (s3p["b_p_konsistenz"][k55]["abs_diff"]
                                   == kk[k2key]["abs_diff"]),
            }
    out["k2_cross_613"] = cross
except Exception as exc:
    out["k2s3_error"] = repr(exc)

# S1-Eval punkte-Schema + 673-Reihe
s1 = load("pt_ram_q_hardware3_eval.json")
rows = sorted(s1["punkte"])
out["s1_punkte_n"] = len(rows)
out["s1_keys_sample"] = rows[:3] + rows[-3:]
v = s1["punkte"]["verdict|q5_d5|673"]
out["s1_verdict_row_fields"] = sorted(v)
out["s1_673"] = {"res_v3": v["res_v3"], "c_p": v["c_p"],
                 "kappa_hat": v["kappa_hat"], "below_sharp": v["below_sharp"]}
out["s1_top_keys"] = sorted(s1)
out["s1_gamma_q5_keys"] = sorted(s1["gamma_arm"])
out["s1_gamma_q5_n_cal"] = s1["gamma_arm"]["q5_d5"]["n_cal"]
out["s1_echo_anchors"] = sorted(s1.get("echo_ladder", {}))

# S1-ISA-Report two_q fuer 055-Reihen-Circuits
s1rep = load("pt_ram_q_isa3_report.json")
pc = s1rep["per_circuit"]
probe_names = ["struct_q5_d5_673_r0", "loschmidt_q5_d5_673",
               "calstruct_q5_d5_631_r0", "calloschmidt_q5_d5_631",
               "struct_q3_d3_181_r0", "loschmidt_q3_d3_181"]
out["s1rep_two_q"] = {n: pc[n]["two_q"] for n in probe_names}
out["s1rep_n_circuits"] = s1rep["n_circuits"]

# p48-QPU-Feldnamen-Vertrag fuer c' (per_circuit-Entries)
s3p = load("pt_ram_q_prio48_stage3_results.json")
out["s055_n_bp"] = len(s3p["b_p"])
out["s055_sets_q5_cal"] = s3p["sets"]["kalibrier"]["q5_d5"]

print(json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True))