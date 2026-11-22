# -*- coding: utf-8 -*-
"""probe3 — K2-kalibrier_konsistenz (613-Pins), Echo-Schema, Kontroll-Vertrag."""
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

# K2-Stage-3 kalibrier_konsistenz (die 613-Pins?)
k2s3 = load("pt_ram_q6_k2_stage3.json")
kk = k2s3["b_p_kalibrier_konsistenz"]
out["k2_konsistenz_n"] = len(kk)
out["k2_konsistenz_all"] = {k: {"abs_diff": v.get("abs_diff"),
                                "stage3_grid": v.get("stage3_grid"),
                                "stage3_044": v.get("stage3_044"),
                                "ok": v.get("ok")}
                            for k, v in sorted(kk.items())}
s3p = load("pt_ram_q_prio48_stage3_results.json")
bp55 = s3p["b_p"]
cross = {}
for arm in ("q3_d3", "q5_d5"):
    for setname in ("verdict", "cal"):
        k55 = "%s|%s|%s" % (setname, arm, "613")
        if k55 in bp55 and k55 in kk:
            cross[k55] = {
                "bP_055": bp55[k55], "bP_k2": kk[k55]["stage3_grid"],
                "bp_bit_equal": bp55[k55] == kk[k55]["stage3_grid"],
                "diff_055": s3p["b_p_konsistenz"].get(k55, {}).get("abs_diff"),
                "diff_k2": kk[k55].get("abs_diff"),
                "diff_bit_equal": (s3p["b_p_konsistenz"].get(k55, {})
                                   .get("abs_diff")
                                   == kk[k55].get("abs_diff")),
            }
out["k2_cross_613"] = cross
out["k2_zusammenfassung"] = k2s3["b_p_konsistenz_zusammenfassung"]

# Echo-Ladder-Schema (S1 + S2) — FPrio-5(b)-Vergleichs quelle
s1 = load("pt_ram_q_hardware3_eval.json")
s2 = load("pt_ram_q_hardware3_eval_rep.json")
out["s1_echo_q5"] = s1["echo_ladder"]["q5_d5"]
out["s2_echo_q5"] = s2["echo_ladder"]["q5_d5"]
out["s2_top_keys_equal_s1"] = sorted(s2) == sorted(s1)

# Kontroll-Vertrag aus dem 055-Prereg (t3/t4-Quellen)
pr = load("pt_ram_q_prio48_prereg.json")
out["pr_controls"] = pr["controls"]
out["pr_t4_names"] = sorted(pr["controls"].get("t4", {})
                            if isinstance(pr["controls"].get("t4"), dict)
                            else {})[:6]

print(json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True))