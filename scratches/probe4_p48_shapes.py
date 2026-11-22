# -*- coding: utf-8 -*-
"""probe4 — Grid-/Circuit-Shapes + 613-Kreuzprüfung auf der 055-Seite."""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pt_ram_q_prio48 as p48
import pt_ram_q_hardware3_aer as h3a

out = {}

# 613-Kreuzprüfung STATT der leeren Probe-Wraps (Werte direkt verglichen)
k2s3 = json.load(open(_ROOT + "/pt_ram_q6_k2_stage3.json", encoding="utf-8"))
s3p = json.load(open(_ROOT + "/pt_ram_q_prio48_stage3_results.json",
                     encoding="utf-8"))
kk = k2s3["b_p_kalibrier_konsistenz"]
cross = {}
for arm in ("q3_d3", "q5_d5"):
    k55 = "verdict|%s|613" % arm
    k2k = "cal|%s|613" % arm
    cross[arm] = {
        "bP_055": s3p["b_p"][k55],
        "bP_k2": kk[k2k]["stage3_grid"],
        "bp_bit_equal": s3p["b_p"][k55] == kk[k2k]["stage3_grid"],
        "diff_055": s3p["b_p_konsistenz"][k55]["abs_diff"],
        "diff_k2": kk[k2k]["abs_diff"],
        "diff_bit_equal": (s3p["b_p_konsistenz"][k55]["abs_diff"]
                           == kk[k2k]["abs_diff"]),
    }
out["cross615"] = cross

# Grid-Formen
pts, cal, ladder = p48.eval_grid()
out["pts_type"] = type(pts).__name__
out["pts_n"] = len(pts)
keys = sorted(pts)
out["pts_keys_sample"] = [repr(k) for k in keys[:3] + keys[-3:]]
rec = pts[keys[0]]
out["pts_record_fields"] = sorted(rec)
out["pts_record_q3_head"] = {k: rec[k] for k in sorted(rec)
                             if k in ("P", "arm", "m", "n0", "n_d", "q", "d",
                                      "set", "L_q", "ratio_true",
                                      "share_true_reg", "model_share_reg",
                                      "N", "N_tilde", "delta")}
arms = out["arms"] = sorted({k[0] for k in pts})
out["per_arm_verdict"] = {arm: len([k for k in pts
                                    if k[0] == arm and pts[k]["set"]
                                    == "verdict"]) for arm in arms}
out["per_arm_cal"] = {arm: len([k for k in pts
                                if k[0] == arm and pts[k]["set"]
                                == "cal"]) for arm in arms}
out["cal_type"] = type(cal).__name__
out["cal_repr"] = (json.dumps(cal)[:600] if not isinstance(cal, dict)
                   else "dict keys " + str(sorted(cal))[:300])
out["ladder_repr_head"] = (json.dumps(ladder)[:400]
                           if isinstance(ladder, (dict, list)) else repr(ladder)[:400])

# Circuit-Formen (0 QPU, klassisch)
circuits = h3a.build_hardware_circuit_set(pts=pts, cal=cal)
out["circ_n"] = len(circuits)
out["circ_entry_fields"] = sorted(circuits[0])
kinds = {}
for c in circuits:
    kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
out["circ_kinds"] = kinds
names = [c["name"] for c in circuits]
row_names = [n for n in names if n.startswith(
    ("struct_", "calstruct_", "loschmidt_", "calloschmidt_"))]
out["row_n"] = len(row_names)
out["struct_names_sample"] = row_names[:3] + row_names[-3:]
ctrl = [c["name"] for c in circuits if c["kind"] == "negative_control"]
out["ctrl_names"] = ctrl
out["ctrl_fields"] = sorted(next(c for c in circuits
                                 if c["kind"] == "negative_control"))
out["ctrl_detail"] = {
    c["name"]: {k: c[k] for k in sorted(c)
                if k not in ("circuit",)}
    for c in circuits if c["kind"] == "negative_control"}
lad = [c["name"] for c in circuits if "ladder_" in c["name"]]
out["ladder_names"] = sorted(lad)
out["cal_ro_names"] = [c["name"] for c in circuits
                       if c["kind"] not in
                       ("structure", "kalibrier_structure",
                        "negative_control", "echo_ladder_ladder",
                        "echo_ladder_anchor")]

print(json.dumps(out, indent=1, ensure_ascii=False,
                 sort_keys=False, default=repr))