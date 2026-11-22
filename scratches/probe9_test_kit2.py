# -*- coding: utf-8 -*-
"""probe9 — Test-Baukasten 2: Konstanten-Dump + Prereg-Verbatim + Sess-Rows
+ OLS-Anker-Re-Identifikation Runde 2 (Sess-/Delta-Varianten)."""
import importlib
import inspect
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

out = {}


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


p48 = importlib.import_module("pt_ram_q_prio48")
ev = importlib.import_module("pt_ram_q_prio48_eval")

out["p48_const_full"] = {
    k: getattr(p48, k) for k in (
        "ANCHOR_RHO_POOLED", "ANCHOR_RHO_Q3", "ANCHOR_RHO_Q5", "ARMS",
        "CAL_OLD_P", "CP_TOL", "D_FAM_BY_ARM", "D_MIN_BY_ARM", "D_TOL",
        "EXPERIMENT", "FAM_BY_ARM", "FEZ_BACKLOG", "H3_EVAL_S1",
        "H3_EVAL_S2", "H3_PREREG", "HYPOTHESIS", "ISA_2Q_PER_CIRCUIT_MAX",
        "ISA_2Q_TOTAL_MAX", "ISA_GATE_PATH", "ISA_REPORT_PATH", "JOB046_ID",
        "JOB_ID_PATH", "K2_EVAL", "K2_PREREG", "KAPPA_CEILING",
        "KAPPA_S1_Q5_CAL_MIN", "LEG", "NQ3", "NQ5", "NQ_BY_ARM",
        "N_CAL_Q5_TARGET", "N_CIRCUITS", "N_NEW_CAL_Q5", "PREREG_PATH",
        "Q95_PERM_Q3", "Q95_PERM_Q5", "Q_BY_ARM", "RAW_PATH",
        "RHO_C_VORPROBE_Q3", "RHO_C_VORPROBE_Q5", "SESSIONS_OUT",
        "SE_C_MEAN_S1", "SE_NO_INT_S1_Q5_CAL", "SHOTS", "SQRT_EXPECT_N16",
        "TOTAL_SHOTS", "TRANSPILE_SEED", "VERDICT_P", "W_A", "W_B_DP")}
out["src_layout_slots"] = inspect.getsource(p48.layout_slots)

pts_e, cal_e, ladder = p48.eval_grid()
out["pts_e_first_keys"] = [repr(k) for k in sorted(pts_e)[:3]]
out["pts_e_sample"] = {repr(k): v for k, v in sorted(pts_e.items())[:1]}
out["cal_e_first_keys"] = [repr(k) for k in sorted(cal_e)[:3]]
out["cal_e_sample"] = {repr(k): v for k, v in sorted(cal_e.items())[:1]}

q5, q3 = p48._sess_rows()
out["sess_rows_q5_first"] = q5[0] if q5 else None
out["sess_rows_q5_keys"] = sorted(q5[0]) if q5 else []
out["sess_rows_count"] = (len(q5), len(q3))
sess_q5 = q5
sess_q3 = q3

# c_p je sess row falls vorhanden
def ols_variants(tag, cps, dlss):
    res = {}
    for fld, dls in dlss.items():
        try:
            f = ev._ols_decomp(cps, dls)
            res[fld] = {k: round(f[k], 14) for k in
                        ("gamma_ols", "se_gamma", "resid_sd_ddof2", "r2")}
        except Exception as exc:  # noqa: BLE001
            res[fld] = {"ERR": repr(exc)}
    return res

# Variante A: Sess-Rows (s1/s2-Paare)
for arm, rows in (("q5", sess_q5), ("q3", sess_q3)):
    keys0 = sorted(rows[0])
    cps = ([r["c_p"] for r in rows] if "c_p" in keys0 else None)
    variants = {}
    fields = [k for k in keys0 if k not in ("P",)]
    for fld in fields:
        dls = [r[fld] for r in rows]
        if not all(isinstance(x, (int, float)) for x in dls):
            continue
        if cps:
            variants["cp_vs_" + fld] = []
        variants["plain_" + fld] = dls
    if cps:
        cand = {}
        for fld in fields:
            dls = [r[fld] for r in rows]
            if not all(isinstance(x, (int, float)) for x in dls):
                continue
            try:
                f = ev._ols_decomp(cps, dls)
                cand["cp_vs_" + fld] = {k: round(f[k], 14) for k in
                                        ("gamma_ols", "se_gamma",
                                         "resid_sd_ddof2", "r2")}
            except Exception as exc:  # noqa: BLE001
                cand["cp_vs_" + fld] = {"ERR": repr(exc)}
        if "s1" in keys0 and "s2" in keys0:
            diffs = [r["s2"] - r["s1"] for r in rows]
            try:
                f = ev._ols_decomp(cps, diffs)
                cand["cp_vs_s2_minus_s1"] = {k: round(f[k], 14) for k in
                                             ("gamma_ols", "se_gamma",
                                              "resid_sd_ddof2", "r2")}
            except Exception as exc:  # noqa: BLE001
                cand["cp_vs_s2_minus_s1"] = {"ERR": repr(exc)}
        if "s1" in keys0 and "s2" in keys0:
            try:
                f = ev._ols_decomp([r["s1"] for r in rows],
                                   [r["s2"] for r in rows])
                cand["s1_vs_s2"] = {k: round(f[k], 14) for k in
                                    ("gamma_ols", "se_gamma",
                                     "resid_sd_ddof2", "r2")}
            except Exception as exc:  # noqa: BLE001
                cand["s1_vs_s2"] = {"ERR": repr(exc)}
        out["ols_ident2_" + arm] = cand
    else:
        out["ols_ident2_" + arm] = {"cps_fehlt_keys": keys0,
                                    "row0": rows[0]}

pr = load("pt_ram_q_prio48_prereg.json")
for k in ("verdict_map", "safeguard_limits", "c2_criteria",
          "c3_geometry_counter", "controls", "banned_from_raw",
          "integritaet", "status", "user_directive", "anti_sharpshooter",
          "kalibrier_bein", "echo_ladder", "fallback_lesart_b_inherited",
          "layer_separation", "design_decision", "inherited_freeze_note",
          "future_phase_numbering", "phase10_verdict_context",
          "registered_before", "registered_by"):
    out["prereg_" + k] = pr.get(k, "<fehlt>")

pf = pr["prediction_freeze"]
out["cP_verdict_q5d5_467"] = pf["cP_freeze"].get("verdict|q5_d5|467")
out["cP_cal_q5d5_433"] = pf["cP_freeze"].get("cal|q5_d5|433")
out["cP_cal_q3d3_149"] = pf["cP_freeze"].get("cal|q3_d3|149")
out["cP_size"] = len(pf["cP_freeze"])
out["pf_calibration_points"] = pf.get("calibration_points")

h3a = p48.h3a
out["h3a_const"] = {
    k: getattr(h3a, k) for k in (
        "SET_VERDICT", "SET_CAL", "K_REPEATS", "LADDER_REPEATS", "SHOTS",
        "TRANSPILE_SEED") if hasattr(h3a, k)}
out["src_h3a_pkey"] = inspect.getsource(h3a.pkey)

s3 = load("pt_ram_q_prio48_stage3_results.json")
out["b_p_pins"] = {
    "verdict|q3_d3|613": s3["b_p"]["verdict|q3_d3|613"],
    "verdict|q5_d5|613": s3["b_p"]["verdict|q5_d5|613"],
    "verdict|q5_d5|467": s3["b_p"]["verdict|q5_d5|467"],
    "verdict|q3_d3|181": s3["b_p"].get("verdict|q3_d3|181"),
    "cal|q3_d3|149": s3["b_p"].get("cal|q3_d3|149"),
    "cal|q5_d5|433": s3["b_p"].get("cal|q5_d5|433"),
    "ladder|q5_d5|479": s3["b_p"].get("cal|q5_d5|479")}
out["b_p_ladder_key_sample"] = [k for k in sorted(s3["b_p"])
                                if "479" in k]
out["intercepts_pins"] = {
    "verdict|q3_d3|613": s3["intercepts"]["verdict|q3_d3|613"],
    "verdict|q5_d5|613": s3["intercepts"]["verdict|q5_d5|613"]}

print(json.dumps(out, indent=1, ensure_ascii=False, default=repr))