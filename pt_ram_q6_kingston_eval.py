# -*- coding: utf-8 -*-
"""EXPERIMENT 050 (H-RAM-Q-6 Leg D1) — Auswertung (NACH Raw-Commit).

Zwei Ebenen, beide registriert im Freeze pt_ram_q6_kingston_prereg.json:
  1. GEERBTES Verdict: pt_ram_q_hardware3_eval.evaluate() ueber das
     Kingston-Raw mit dem Kingston-ISA-Gate (Schema-kompatibel, 044-v3b-
     Gesetz md5 baaca1f6 UNVERAENDERT — kein Fork des Gesetzes).
  2. D1-Legs L1/L2/L3 ex ante gegen S1 (11d) und S2 (047).

Verdict-Ordnung (gefreten Prereg-Map): DEGENERAT (geerbte Kontrollen t3-t6
verletzt) -> VOID_SUBSTRAT (n_kappa_low_union >= 2) -> pro-Session-Paare:
D1_REFUTED (kein Paar bestaetigt) / D1_PARTIAL (mindestens ein Paar:
L1_pass UND L2_roh-pass je GLEICHER Session) / D1_CONFIRMED (alle
Session-Paare bestehen).
"""
import json
import os
from datetime import datetime, timezone

import pt_ram_q6_kingston as k6
import pt_ram_q_hardware3_eval as h3e
import pt_ram_q_hardware3 as h3

KONTROLLE_KEYS = ("t3_identity_two_ways", "t4_negative_must_not_fire",
                  "t5_gate_set_frozen", "t6_mass_conservation")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def check_raw_against_gate(raw, isa):
    """Verteidigungs-Check parallel zu h3e (Schema + Totals aus dem Gate)."""
    k6.validate_isa_gate(isa)
    want = {"optimization_level": isa["optimization_level"],
            "transpile_seed": isa["transpile_seed"],
            "isa_2q_total": isa["total_two_q"],
            "isa_2q_max": isa["max_two_q"]}
    if raw["transpile"] != want:
        raise AssertionError("raw-transpile != committed ISA-Gate: %r != %r"
                             % (raw["transpile"], want))
    assert str(raw["backend"]).lower().startswith(k6.BACKEND_NAME), raw["backend"]
    assert len(raw["counts"]) == 116
    assert int(raw["shots_per_circuit"]) == int(h3.SHOTS)
    return True


def degenerat_flag(inherited):
    kont = inherited.get("kontrollen") or {}
    failed = [key for key in KONTROLLE_KEYS if not (kont.get(key) or {}).get("ok")]
    return failed


def decide_d1(degenerat_failed, n_kappa_low_union, l1, l2):
    """Gefrorene verdict_map (order im Prereg)."""
    if degenerat_failed:
        return "DEGENERAT"
    if n_kappa_low_union >= 2:
        return "VOID_SUBSTRAT"
    pairs = {s: bool(l1[s]["pass"] and l2[s]["lesart_roh"]["pass"])
             for s in l1}
    if any(pairs.values()):
        return ("D1_CONFIRMED_SUBSTRAT_UNIVERSAL" if all(pairs.values())
                else "D1_PARTIAL")
    return "D1_REFUTED_SUBSTRAT_SPEZIFISCH"


def evaluate(raw_path=k6.RAW_PATH,
             stage3_path=h3e.STAGE3_PATH,
             isa_path=k6.ISA_GATE_PATH):
    prereg = k6.load_frozen_prereg()
    isa = load_json(isa_path)
    raw = load_json(raw_path)
    check_raw_against_gate(raw, isa)

    inherited = h3e.evaluate(raw_path=raw_path, stage3_path=stage3_path,
                             isa_path=isa_path)
    with open(k6.INHERITED_EVAL_PATH, "w", encoding="utf-8") as fh:
        json.dump(inherited, fh, ensure_ascii=False, indent=1)

    degenerat_failed = degenerat_flag(inherited)
    s1 = load_json(prereg["frozen_inputs"]["s1_eval"])
    s2 = load_json(prereg["frozen_inputs"]["s2_eval"])
    res_k = k6.holdout_residuen(inherited)
    res_s1 = k6.holdout_residuen(s1)
    res_s2 = k6.holdout_residuen(s2)
    order = list(res_s1)  # registrierte (arm,P)-Reihenfolge aus S1
    vals = {"S1": [res_s1[x] for x in order],
            "S2": [res_s2[x] for x in order],
            "K": [res_k[x] for x in order]}

    seeds = prereg["legs"]["L1_Substrat_Kohaerenz"]["seeds"]
    l1 = {"S1": k6.leg_l1(vals["S1"], vals["K"], seeds["S1"]),
          "S2": k6.leg_l1(vals["S2"], vals["K"], seeds["S2"])}
    l2 = {"S1": k6.leg_l2(vals["S1"], vals["K"]),
          "S2": k6.leg_l2(vals["S2"], vals["K"])}

    kappa_k = k6.kappa_map(inherited)
    kappa_s1 = k6.kappa_map(s1)
    keys = sorted(kappa_k)
    n_low = sum(1 for kk in keys if kappa_k[kk] < k6.KAPPA_CEILING)
    l3 = {"n_kappa_low_union": int(n_low),
          "kappa_ceiling": k6.KAPPA_CEILING,
          "kappa_band_K": [min(kappa_k[kk] for kk in keys),
                           max(kappa_k[kk] for kk in keys)],
          "diag_spearman_kappa_K_vs_S1_nicht_verdict_tragend":
              k6.spearman([kappa_k[kk] for kk in keys],
                          [kappa_s1[kk] for kk in keys]),
          "n_points": len(keys)}

    d1 = decide_d1(degenerat_failed, n_low, l1, l2)
    doc = {
        "experiment": k6.EXPERIMENT,
        "hypothesis": k6.HYPOTHESIS,
        "leg": k6.LEG,
        "status": "EVALUATED",
        "prereg_md5": k6.PREREG_MD5,
        "raw_path": raw_path,
        "raw_job_meta": raw.get("job_meta"),
        "raw_counts_md5": raw.get("counts_md5"),
        "counts_md5_verified": True,
        "inherited_eval_path": k6.INHERITED_EVAL_PATH,
        "inherited_verdict": inherited.get("verdict"),
        "inherited_degenerat_failed": degenerat_failed,
        "res_K": res_k,
        "L1": l1,
        "L2": l2,
        "L3": l3,
        "d1_verdict": d1,
        "verdict": d1,
        "verdict_map_text": prereg["verdict_map"],
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    with open(k6.EVAL_PATH, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    print("D1:", {s: {"rho": l1[s]["rho_obs"], "L1": l1[s]["pass"],
                      "agree_roh": l2[s]["lesart_roh"]["agree"],
                      "L2": l2[s]["lesart_roh"]["pass"]}
                 for s in ("S1", "S2")})
    print("kappa_low_union:", n_low, "| inherited:", inherited.get("verdict"),
          "| degenerate_blocks:", degenerat_failed, "| D1:", d1)
    return doc


if __name__ == "__main__":
    evaluate()