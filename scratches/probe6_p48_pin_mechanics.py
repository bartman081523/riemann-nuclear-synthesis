# -*- coding: utf-8 -*-
"""probe6 — Design-Scratch (verify-Funktion der Pins) + Stage3/Dok-Strukturen."""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

out = {}


def load(path):
    with open(os.path.join(_ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


# --- Design-Scratch verbatim (die PIN-Rechenweise) ---
ds = load("scratches/h9_fprio48_design_out.json")
out["design_scratch_top_keys"] = sorted(ds)
out["design_scratch"] = ds

# --- 055-Stage3-Dokumentarstruktur ---
s3p = load("pt_ram_q_prio48_stage3_results.json")
out["stage3_top_keys"] = sorted(s3p)
out["stage3_prereg_md5"] = s3p.get("prereg_md5")
out["stage3_prereg_md5_field_type"] = type(s3p.get("prereg_md5")).__name__
out["stage3_meta_head"] = {k: s3p[k] for k in sorted(s3p)
                           if k not in ("b_p", "b_p_konsistenz")}
bk = s3p["b_p_konsistenz"]
out["b_p_konsistenz_n"] = len(bk)
out["b_p_konsistenz_bad"] = {k: v for k, v in sorted(bk.items())
                             if not v.get("ok")}
out["b_p_konsistenz_sample_ok"] = {
    k: v for k, v in sorted(bk.items()) if v.get("ok")
    and ("379" in k or "467" in k)} if isinstance(bk, dict) else None
zz = s3p.get("b_p_konsistenz_zusammenfassung")
out["stage3_zusammenfassung"] = zz

# --- S2-Eval (rep) below/sharp-Set an den q5-verdict-P (C2-Kern-Kontext) ---
s2e = load("pt_ram_q_hardware3_eval_rep.json")
s2e_rows = s2e["punkte"]
out["s2e_verdict_q5"] = {}
for key, r in s2e_rows.items():
    ks = str(key)
    if r["set"] == "verdict" and "q5" in ks:
        out["s2e_verdict_q5"][ks] = {
            k: r[k] for k in ("P", "res_v3", "below_sharp", "above_ceiling_w_b",
                              "in_band_sharp") if k in r}
out["s2e_top_keys_eq_s1e"] = sorted(s2e) == sorted(
    load("pt_ram_q_hardware3_eval.json"))

# --- h3a/b_P-Referenzpunkte (K2-Remap-Namenskonvention) ---
k2 = load("pt_ram_q6_k2_stage3.json")
out["k2_top_keys"] = sorted(k2)
out["k2_prereg_md5"] = k2.get("prereg_md5")

print(json.dumps(out, indent=1, ensure_ascii=False,
                 sort_keys=False, default=repr))