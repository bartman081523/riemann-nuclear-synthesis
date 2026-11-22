# -*- coding: utf-8 -*-
"""probe5 — 055-Prereg-Interna verbatim + S1-two_q-Presence + S1-C1-Rows."""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pt_ram_q_hardware3_aer as h3a
import pt_ram_q_prio48 as p48
import pt_ram_q_prio48_qpu as p48qpu

out = {}


def load(path):
    with open(os.path.join(_ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


# --- 055-Prereg-Interna ---
pr = load("pt_ram_q_prio48_prereg.json")
out["pr_top_keys"] = sorted(pr)
pf = pr["prediction_freeze"]
out["pf_keys"] = sorted(pf)
pts_arm = pf["points"]
out["pf_points_type"] = type(pts_arm).__name__
out["pf_points_arm_keys"] = sorted(pts_arm) if isinstance(pts_arm, dict) else None
if isinstance(pts_arm, dict):
    out["pf_points_detail"] = {
        arm: {"n": len(v), "type": type(v).__name__,
              "head": [e if not isinstance(e, dict) else {k: e[k] for k in
                                                         sorted(e)}
                       for e in list(v)[:2]]}
        for arm, v in sorted(pts_arm.items())}
kb = pr["kalibrier_bein"]
out["kb_keys"] = sorted(kb)
out["kb_points_detail"] = {
    arm: {"n": len(v), "type": type(v).__name__}
    for arm, v in sorted(kb["points"].items())}
out["cP_freeze_n"] = len(pf["cP_freeze"])
out["cP_freeze_prefix_tally"] = {}
for k in pf["cP_freeze"]:
    pfx = k.split("|")[0]
    out["cP_freeze_prefix_tally"][pfx] = \
        out["cP_freeze_prefix_tally"].get(pfx, 0) + 1
out["c_blocks_keys"] = {k: pr[k] for k in sorted(pr) if k.startswith(
    ("c1", "c2", "c3", "fprio"))}
out["verdict_map"] = pr.get("verdict_map")
out["banned_from_raw"] = pr.get("banned_from_raw")
out["integritaet"] = pr.get("integritaet")
out["pr_other_keys_verbatim"] = {
    k: pr[k] for k in sorted(pr) if k not in (
        "prediction_freeze", "kalibrier_bein", "c1_session_anchors",
        "c2_criteria", "c3_geometry_counter", "verdict_map",
        "fprio8_refit", "controls", "banned_from_raw", "integritaet")}

# --- p48qpu-Konstanten ---
out["p48qpu_consts"] = {}
for name in sorted(dir(p48qpu)):
    if name.isupper():
        v = getattr(p48qpu, name)
        out["p48qpu_consts"][name] = (v if isinstance(v, (int, str, float))
                                      else repr(v)[:200])

# --- S1-ISA-Report two_qPresence fuer die 148 Row-Namen ---
s1rep = load("pt_ram_q_isa3_report.json")
pts, cal, ladder = p48.eval_grid()
circuits = h3a.build_hardware_circuit_set(pts=pts, cal=cal)
row_names = [c["name"] for c in circuits if (
    c["kind"] in ("structure", "kalibrier_structure", "loschmidt",
                  "kalibrier_loschmidt"))]
pc = s1rep["per_circuit"]
missing = [n for n in row_names if n not in pc]
zero_keys = [n for n in row_names
             if n in pc and int(pc[n].get("two_q", -1)) <= 0]
out["s1_twoq_presence"] = {"n_rows": len(row_names), "n_missing": len(missing),
                           "n_zero_or_neg": len(zero_keys),
                           "missing_head": missing[:5],
                           "s1rep_pc_n": len(pc),
                           "s1rep_pc_fields": sorted(next(iter(pc.values())))}

# --- S1-eval Rows (C1-Anker-Quelle) ---
s1e = load("pt_ram_q_hardware3_eval.json")
s1e_rows = s1e["punkte"]
out["s1e_punkte_type"] = type(s1e_rows).__name__
out["s1e_n"] = len(s1e_rows)
row0 = next(iter(s1e_rows.values()))
out["s1e_row_fields"] = sorted(row0)
out["s1e_verdict_rows"] = {}
for key, r in s1e_rows.items():
    if r["set"] == "verdict":
        out["s1e_verdict_rows"][str(key)] = {
            k: r[k] for k in sorted(r) if k in ("res", "res_v3", "c_p",
                                                "kappa_hat", "ratio_hw")}
# c_p-Identitaet vs cP_freeze (Pin c_p_identisch_s1_s2 true)
ident = []
for key, r in s1e_rows.items():
    kstr = str(key)
    if kstr in pf["cP_freeze"]:
        ident.append((kstr, pf["cP_freeze"][kstr] == r["c_p"]))
out["c_p_ident_bit_tally"] = {"n": len(ident),
                              "n_equal": sum(1 for _, eq in ident if eq)}

print(json.dumps(out, indent=1, ensure_ascii=False,
                 sort_keys=False, default=repr))