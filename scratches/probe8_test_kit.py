# -*- coding: utf-8 -*-
"""probe8 — Test-Baukasten: Signaturen + getsource der kleinen Funktionen
+ Prereg-FPrio8 verbatim + S1/S2-Zeilen-Pins + OLS-Anker-Re-Identifikation."""
import inspect
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


import pt_ram_q_prio48 as p48  # noqa: E402
import pt_ram_q_prio48_eval as ev  # noqa: E402

out["p48_attrs"] = sorted(a for a in dir(p48) if not a.startswith("__"))
out["ev_attrs"] = sorted(a for a in dir(ev) if not a.startswith("__"))

sigs = {}
for mod, tag in ((p48, "p48"), (ev, "ev")):
    for a in dir(mod):
        if a.startswith("__"):
            continue
        o = getattr(mod, a)
        if callable(o):
            try:
                sigs[tag + "." + a] = str(inspect.signature(o))
            except (TypeError, ValueError):
                sigs[tag + "." + a] = "<sig?>"
out["signatures"] = sigs

for fname in ("decide_verdict_055", "_ols_decomp", "_se_no_int",
              "arm_rows", "_echo_from_eval", "write_eval"):
    o = getattr(ev, fname, None)
    out["src_ev_" + fname] = inspect.getsource(o) if o else "<fehlt>"

for fname in ("arm_rows", "spearman", "q95_exact_perm", "slot_assignment",
              "recompute_anchors", "verify_frozen", "eval_grid", "ladder_ps",
              "cP_freeze_fresh", "load_frozen_prereg", "eval_points",
              "forced_row_order"):
    o = getattr(p48, fname, None)
    out["src_p48_" + fname] = inspect.getsource(o) if o else "<fehlt>"

out["p48_const"] = {}
for k in ("EXPERIMENT", "LEG", "N_CIRCUITS", "SHOTS", "TOTAL_SHOTS",
          "KAPPA_CEILING", "K_REPEATS", "LADDER_REPEATS", "CP_TOL",
          "ISA_CEILING_2Q", "ISA_CEILING_TOTAL", "TRANSPILE_SEED",
          "SE_NO_INT_S1_Q5_CAL", "RAW_PATH", "ISA_PATH", "GATE_PATH",
          "EVAL_PATH", "PREREG_MD5", "H3_EVAL_S1", "H3_EVAL_S2",
          "SET_VERDICT", "SET_CAL", "ARMS"):
    out["p48_const"][k] = getattr(p48, k, "<fehlt>")

pr = load("pt_ram_q_prio48_prereg.json")
out["fprio8_refit"] = pr["fprio8_refit"]
out["prereg_top_keys"] = sorted(pr)
out["hyp_verbatim"] = pr["hypothesis"]
out["session_anchors_verbatim"] = pr["session_anchors"]
out["prediction_freeze_keys"] = sorted(pr["prediction_freeze"])
out["c1_c_vorprobe_verbatim"] = pr.get("c1_c_vorprobe")
out["kalibrier_bein_keys"] = sorted(pr["kalibrier_bein"])
out["kb_keys_sub"] = sorted(pr["kalibrier_bein"])
out["kb_ladder_rule_verbatim"] = pr["kalibrier_bein"].get("ladder_rule",
                                                          "<fehlt>")
out["hardware_parameters_verbatim"] = pr["hardware_parameters"]

# --- S1/S2-verdict-Zeilen (für C1/C2/F-Anker-Tests) ---
for tag, path in (("S1", "pt_ram_q_hardware3_eval.json"),
                  ("S2", "pt_ram_q_hardware3_eval_rep.json")):
    d = load(path)
    rows = {}
    for key, r in sorted(d["punkte"].items()):
        if r["set"] != "verdict":
            continue
        rows[key] = {"P": r["P"], "res_v3": r["res_v3"], "c_p": r["c_p"],
                     "kappa_hat": r["kappa_hat"], "ratio_hw": r["ratio_hw"],
                     "below_sharp": r["below_sharp"],
                     "in_band_sharp": r["in_band_sharp"],
                     "gamma_used": r["gamma_used"]}
    out[tag + "_verdict_rows"] = rows
    out[tag + "_below_sets"] = {
        arm: sorted(r["P"] for k, r in rows.items() if arm in k
                    and r["below_sharp"])
        for arm in ("q3_d3", "q5_d5")}
    out[tag + "_verdict"] = d["verdict"]
    out[tag + "_gamma_arm"] = {arm: {k: d["gamma_arm"][arm][k]
                                     for k in sorted(d["gamma_arm"][arm])}
                               for arm in sorted(d["gamma_arm"])}
    out[tag + "_echo_ladder"] = {
        arm: {k: d["echo_ladder"][arm][k] for k in sorted(
            d["echo_ladder"][arm])} for arm in sorted(d["echo_ladder"])}

# --- OLS-Anker-Re-Identifikation (committed_F_anchors) ---
anc = pr["fprio8_refit"]["committed_F_anchors"]
for arm, n_expect in (("q5_d5", 5), ("q3_d3", 8)):
    keys = [k for k in sorted(
        (tag + "_verdict_rows").split() and [])]  # noop placeholder
out["fprio8_commit_anchor_keys"] = sorted(anc)
for arm in sorted(anc):
    cand = {}
    rows = {}
    for tag, path in (("S1", "pt_ram_q_hardware3_eval.json"),
                      ("S2", "pt_ram_q_hardware3_eval_rep.json")):
        d = load(path)
        sel = {k: r for k, r in sorted(d["punkte"].items())
               if r["set"] == "verdict" and arm in k}
        cps = [r["c_p"] for r in sel.values()]
        for fld in ("res_v3", "ratio_hw"):
            dls = [r[fld] for r in sel.values()]
            if len(cps) != len(dls) or not cps:
                continue
            try:
                f = ev._ols_decomp(cps, dls)
                cand[tag + ":" + fld] = {
                    k: round(f[k], 14) for k in
                    ("gamma_ols", "se_gamma", "resid_sd_ddof2", "r2")}
            except Exception as exc:  # noqa: BLE001
                cand[tag + ":" + fld] = {"ERR": repr(exc)}
    out["ols_ident_" + arm] = {
        "committed": {k: anc[arm][k] for k in
                      ("gamma_ols", "se_gamma", "resid_sd", "r2",
                       "n") if k in anc[arm]},
        "candidates_gerundet": cand}

stage3 = load("pt_ram_q_prio48_stage3_results.json")
out["stage3_verbatim_bits"] = {
    "status": stage3["status"],
    "b_p_n": len(stage3["b_p"]),
    "divergente_keys": stage3["b_p_konsistenz_zusammenfassung"].get(
        "divergente_keys"),
    "ladder_ps": stage3.get("ladder_ps"),
    "b_p_fit_failed": stage3.get("b_p_fit_failed")}

print(json.dumps(out, indent=1, ensure_ascii=False, default=repr))