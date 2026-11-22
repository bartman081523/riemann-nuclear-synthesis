# -*- coding: utf-8 -*-
"""probe7 — Schema-Pins aus smoke_report/gate + Zeilen-Pins S1/S2 + Stage3."""
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


rep = load("scratches/smoke_report.json")
gate = load("scratches/smoke_gate.json")
out["report_transpile"] = rep["transpile"]
out["report_unforced_bit_anchor"] = rep["unforced_bit_anchor"]
out["report_isa_ceilings"] = rep["isa_ceilings"]
out["report_run_config_frozen"] = rep["run_config_frozen"]
out["report_c_prime_lesart"] = rep["c_prime_lesart"]
out["report_slots_per_arm"] = rep["slots_per_arm"]
out["report_coupling_map_edges"] = rep["coupling_map_edges"]
rcp = rep["row_c_prime"]
out["row_c_prime_n"] = len(rcp)
out["row_c_prime_fields_verdict"] = sorted(
    rcp.get("verdict|q3_d3|181", {"FEHLT": True}))
sample = rcp.get("verdict|q3_d3|181") or next(iter(rcp.values()))
out["row_c_prime_sample_181"] = sample
out["row_c_prime_keys_verdict"] = [k for k in sorted(rcp)
                                   if k.startswith("verdict|")]
out["row_c_prime_keys_tally_prefix"] = {
    p: sum(1 for k in rcp if k.startswith(p + "|"))
    for p in ("verdict", "cal")}
out["gate_verbatim"] = gate

# --- 055-Prereg: P-Vektoren + Ladder ---
pr = load("pt_ram_q_prio48_prereg.json")
pf = pr["prediction_freeze"]
out["verdict_P_lists"] = {
    arm: [r["P"] for r in pf["points"][arm]] for arm in sorted(pf["points"])}
out["verdict_P_sorted_ok"] = {
    arm: [r["P"] for r in pf["points"][arm]] ==
         sorted(r["P"] for r in pf["points"][arm])
    for arm in pf["points"]}
kb = pr["kalibrier_bein"]
out["cal_P_lists"] = {
    arm: [r["P"] for r in kb["points"][arm]] for arm in sorted(kb["points"])}
out["kb_ladder_P"] = [r["P"] for r in kb["points"]["q5_d5"]][5:]
out["kb_gamma_fit_rule"] = kb["gamma_fit_rule"]
out["h9_prior_chain_keys"] = sorted(pr["prior_chain"])

# --- S1/S2-verdict-Zeilen (C1/C2-Pins) ---
for tag, path in (("S1", "pt_ram_q_hardware3_eval.json"),
                  ("S2", "pt_ram_q_hardware3_eval_rep.json")):
    d = load(path)
    rows = {}
    for key, r in d["punkte"].items():
        if r["set"] != "verdict":
            continue
        rows[key] = {"P": r["P"],
                     "res_v3": r["res_v3"], "c_p": r["c_p"],
                     "kappa_hat": r["kappa_hat"],
                     "ratio_hw": r["ratio_hw"],
                     "below_sharp": r["below_sharp"],
                     "in_band_sharp": r["in_band_sharp"],
                     "gamma_used": r["gamma_used"]}
    out[f"{tag}_verdict_rows"] = rows
    out[f"{tag}_below_sets_q5"] = sorted(
        r["P"] for key, r in rows.items() if "q5" in key and r["below_sharp"])
    out[f"{tag}_gamma_arm"] = {arm: {k: d["gamma_arm"][arm][k]
                                     for k in ("gamma", "n_cal")}
                               for arm in sorted(d["gamma_arm"])}
    out[f"{tag}_verdict"] = d["verdict"]
    out[f"{tag}_echo_ladder"] = {
        arm: {k: d["echo_ladder"][arm][k] for k in (
            "P", "kappa_r", "r1_konsistent_mit_kappa_hat_anker",
            "fit_kappa_block")} for arm in sorted(d["echo_ladder"])}

# --- Stage3-Pins ---
s3 = load("pt_ram_q_prio48_stage3_results.json")
out["stage3_status"] = s3["status"]
out["stage3_b_p_pins"] = {
    "verdict|q3_d3|613": s3["b_p"]["verdict|q3_d3|613"],
    "verdict|q5_d5|613": s3["b_p"]["verdict|q5_d5|613"],
    "verdict|q3_d3|181": s3["b_p"].get("verdict|q3_d3|181"),
    "verdict|q5_d5|467": s3["b_p"].get("verdict|q5_d5|467"),
    "cal|q3_d3|149": s3["b_p"].get("cal|q3_d3|149"),
    "cal|q3_d3|797": s3["b_p"].get("cal|q3_d3|797"),
    "cal|q5_d5|433": s3["b_p"].get("cal|q5_d5|433"),
    "cal|q5_d5|659": s3["b_p"].get("cal|q5_d5|659"),
}
out["stage3_intercepts_pins"] = {
    "verdict|q3_d3|613": s3["intercepts"]["verdict|q3_d3|613"],
    "verdict|q5_d5|613": s3["intercepts"]["verdict|q5_d5|613"],
}
out["stage3_b_p_fit_failed"] = s3["b_p_fit_failed"]
out["stage3_ladder_ps"] = s3["ladder_ps"]
out["stage3_b_p_n"] = len(s3["b_p"])
zz = s3["b_p_konsistenz_zusammenfassung"]
out["stage3_konsistenz_verbatim"] = {
    k: zz[k] for k in sorted(zz) if k != "divergente_keys"}
out["stage3_diverging_row_613_full"] = s3["b_p_konsistenz"][
    "verdict|q3_d3|613"]

print(json.dumps(out, indent=1, ensure_ascii=False, default=repr))