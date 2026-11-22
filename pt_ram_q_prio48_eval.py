# -*- coding: utf-8 -*-
"""pt_ram_q_prio48_eval.py — gefrorene Auswertung (EXPERIMENT 055,
H-H9 FPrio-4 (C.1/D.7 Session-P-Bindung) + FPrio-8 (D.5 n_cal>=16),
leg FP48-COMBINED, EIN Fez-Job hinter 046).

Verdict-tragend ist die GEFRORENE 055-verdict_map des Preregs
(md5 b7afc42c62a6da75b2e43dd3674f8965) in der Reihenfolge der
safeguard_limits (Register):

1. Kontrolle-Void:  t_fail_other -> EVALUATION_INVALID_KONTROLLE_GESCHEITERT
                    (md5 der Counts, b_P-Provenanz, t3/t5/t6 wie 044; die
                    055-t5-Lesart bindet raw.transpile an den ISA-055-Report
                    (transpile-Subdict) UND an das Gate (C3-c'-Binding).
2. Refit-Void:      kappa_hat < 0.81 an >= 2 der Union-Reihen (Verdict UND
                    Kalibrier) -> UNDETERMINED / refit_status
                    REFIT_INVALID_KAPPA (descriptiv-void; kein kritisches
                    Verdict-Ableiten — wörtlich safeguard_limits.void).
3. GEOMETRYBOUND_D7: (not C1_q5) und C3_feuert_q5 (rho(Delta-res, Delta-c)
                    >= q95-exakt q5 0.7999999999999999) — D.7 gewinnt die
                    Runde auf Session-3-Ebene; H-RAM-Q-4 bleibt REFUTED.
4. P_BOUND_TRANSFER_HELD: C1_q5 UND C1_q3 UND C2 UND kein C3-Feuer (kein
                    Arm) — P-Bindung transferiert auf Session 3.
5. MIXED_PARTIAL:   mindestens ein C1-Arm gehalten, keine klare Konstellation.
6. UNDETERMINED:    sonst.

C1 = Spearman(res'_Arm, res_S1_Arm) an den P-sortierten 055-verdict-Zeilen
     >= committeter Session-1->2-Anker (q5 0.49999999999999994, q3
     0.8095238095238096: die S1->S2-Messung).  C2 = {467, 673} BOTH
     below_sharp (S2-Kern) UND {467, 547, 673} mindest. 2/3 (S1-Zweitstufe).
     C3 = exakt-Permutationen-Spearman(Delta-res, Delta-c) je Arm mit
     Delta-c = c_prime - c_S1 aus dem VOR Messung committeten ISA-Report
     (row_c_prime.delta_c_vs_cP); Delta-c degenerat (alle ratio_2q
     bit-gleich 1) ist die registrierte strukturelle Null.

FPrio-8 (descriptiv + F-Zeile-8-Falsifikatorlinie): gamma-Refit q5 an
n_cal = 16 Kal-Reihen (LSQ-durch-Null = das gamma_arm-Refit selbst), OLS-
Zerlegung F (mit Achsenabschnitt), SE-Provenanz (no-int * c̄) frisch gegen
die S1-Pins, und falsifikatorlinie_f_zeile_8: resid_sd(q5, OLS, ddof=2,
n=16) < 0.01 -> SA-H9-5 kippt, sonst bleibt SA-H9-5.

FPrio-5b (descriptiv): Echo-Leiter an den Ankern 181/467 — die 044-Mechanik
(h3e) wird unverändert benutzt; daneben der Vergleich gegen die committeten
S1/S2-Ladder-Werte (fez-scoped Lesart (b): die 12 Unforced-Circuits des
055-Jobs machen sie auf Fez messbar).

Raw-Counts werden VOR dieser Auswertung committed (§Z.14-Disziplin, 044/
046-Praezedenz); der b_P-Streich entnimmt stage3["b_p"] (Aer-Zweig,
±1-ulp-Transpile-Konvention unverändert, KEINE Toleranz-Erhoehung).
"""
import hashlib
import json
import os

import numpy as np

import pt_ram_q_hardware_aer as aer
import pt_ram_q_hardware2_eval as e2
import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_aer as h3a
import pt_ram_q_hardware3_eval as h3e
import pt_ram_q_prio48 as p48
import pt_ram_q_prio48_qpu as qpu
import pt_ram_q_prio48_stage3aer as s3a

RAW_PATH = qpu.RAW_PATH
STAGE3_PATH = s3a.RESULTS_PATH
ISA_PATH = p48.ISA_REPORT_PATH
GATE_PATH = p48.ISA_GATE_PATH
EVAL_PATH = p48.EVAL_PATH
PREREG_MD5 = "b7afc42c62a6da75b2e43dd3674f8965"

# Verdicts = die gefrorenen bare-Namen der 055-verdict_map (Register).
V_PHELD = "P_BOUND_TRANSFER_HELD"
V_D7 = "GEOMETRYBOUND_D7"
V_MIXED = "MIXED_PARTIAL"
V_UNDET = "UNDETERMINED"
REFIT_OK = "REFIT_OK"
REFIT_INVALID = "REFIT_INVALID_KAPPA"
F8_KIPPT = "SA-H9-5 KIPPT"
F8_BLEIBT = "SA-H9-5 BLEIBT"

# Bit-Delegation an das committete 044-Gesetz (kein Fork; 055 ändert nur
# Grid/Verdict-Map/C-Blocke, NICHT das center_v3-Verdict-Mechanik-Gesetz).
_folded_share = h3e._folded_share
fit_gamma_arm = h3e.fit_gamma_arm
center_v3 = h3e.center_v3
anchor_r1_name = h3e.anchor_r1_name


def decide_verdict_055(*, t_fail_other, refit_invalid, c1_q5, c1_q3, c2,
                       c3_fire_q5, c3_fire_q3):
    """Gefrorene 055-Verdict-Logik: Kcontrol-Void -> Refit-Void (safeguard
    Reihenfolge per Register) -> D.7 -> P-Transfer -> Mixed -> UNDETERMINED."""
    if t_fail_other:
        return "EVALUATION_INVALID_KONTROLLE_GESCHEITERT"
    if refit_invalid:
        return V_UNDET
    if (not c1_q5) and c3_fire_q5:
        return V_D7
    if c1_q5 and c1_q3 and c2 and not (c3_fire_q5 or c3_fire_q3):
        return V_PHELD
    if c1_q5 or c1_q3:
        return V_MIXED
    return V_UNDET


def _echo_from_eval(path, arm):
    """echo_ladder[arm]-Subdict eines committed S1/S2-Eval-Artefakts
    (descriptiv-Vergleich fuer fez_lesart_b)."""
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    lad = d["echo_ladder"][arm]
    return {k: lad[k] for k in sorted(lad)}


def _ols_decomp(cps, dls):
    """Registrierte decomposition_F: OLS-mit-Achsenabschnitt X = [ones, c_p],
    se = sqrt(s2*XtXi[1,1]), resid_sd = sqrt(s2) (ddof=2)."""
    cps = np.asarray(cps, dtype=float)
    dls = np.asarray(dls, dtype=float)
    n = len(cps)
    x = np.column_stack([np.ones(n), cps])
    beta, *_ = np.linalg.lstsq(x, dls, rcond=None)
    resid = dls - x @ beta
    ssres = float(resid @ resid)
    s2 = ssres / (n - 2)
    xtxi = np.linalg.inv(x.T @ x)
    sstot = float(((dls - dls.mean()) ** 2).sum())
    return {
        "intercept": float(beta[0]), "gamma_ols": float(beta[1]),
        "se_gamma": float(np.sqrt(s2 * xtxi[1, 1])),
        "resid_sd_ddof2": float(np.sqrt(s2)), "r2": 1.0 - ssres / sstot,
        "n": int(n),
    }


def _se_no_int(cps, dls):
    """D.5-SE-Provenanz (no-intercept LSQ) in der registrierten
    recompute_anchors-Form (p48 — Bit-Kontrakt der S1-Pins)."""
    cps = np.asarray(cps, dtype=float)
    dls = np.asarray(dls, dtype=float)
    gam = float(cps @ dls) / float(cps @ cps)
    scatter = dls - gam * cps
    se = float(np.sqrt(float(scatter @ scatter) / (len(cps) - 1)
                       / float(cps @ cps)))
    return gam, se


def evaluate(raw_path=RAW_PATH, stage3_path=STAGE3_PATH, isa_path=ISA_PATH,
             gate_path=GATE_PATH, prereg_path=None, points=None, cal=None,
             stage3_prereg_md5=None):
    """Gefrorene 055-Auswertung: 044-v3b-Mechanik (h3e-Delegation) auf dem
    37-Reihen-Grid, + C1/C2/C3-Session-Bloecke, FPrio-8-Refit-Block,
    ISA-leg-Dokumentation, 044-Erbe/γ-Konfund als alternative Lesarten.

    Override-Form wie der h3e-K2-Vertrag: points/cal = gestempelte
    Punkt-Records (Verdict/Kalibrier getrennt), prereg_path = frisches
    gefrorenes Prereg, stage3_prereg_md5 = md5 des Stage-3-Bindings.
    Default = bit-identisches Verhalten auf dem 055-Grid."""
    raw = json.load(open(raw_path, encoding="utf-8"))
    with open(stage3_path, encoding="utf-8") as fh:
        stage3 = json.load(fh)
    with open(isa_path, encoding="utf-8") as fh:
        isa = json.load(fh)
    if prereg_path is None:
        prereg = p48.load_frozen_prereg()
        prereg_md5_out = PREREG_MD5
    else:
        with open(prereg_path, encoding="utf-8") as fh:
            prereg = json.load(fh)
        with open(prereg_path, "rb") as fh:
            prereg_md5_out = hashlib.md5(fh.read()).hexdigest()
    w_b = h3e.load_w_b()
    w_a = h3a.W_A
    if points is None and cal is None:
        pts_e, cal_e, _ladder_e = p48.eval_grid()
    else:
        pts_e, cal_e = points, cal
    pts = {**pts_e, **cal_e}
    cs_by_name = {c["name"]: c
                  for c in h3a.build_hardware_circuit_set(pts_e, cal_e)}
    raw_by_name = {e["name"]: e for e in raw["counts"]}

    # --- md5 der Counts + b_P-Provenanz (044-Streifen, ungeaendert) ---
    md5_ok = (qpu.counts_md5([e["counts"] for e in raw["counts"]]
                             ) == raw["counts_md5"])
    bp_md5_ok = stage3["prereg_md5"] == (stage3_prereg_md5 or PREREG_MD5)

    # --- t3 (zwei Wege) + t6 (Shots/Masse) wie 044 (State-Circuits; Echo-
    #     Leiter nicht verdict-tragend, also nicht hier) ---
    t3_dev = 0.0
    t6_shots_ok = True
    t6_mass_dev = 0.0
    for e in raw["counts"]:
        if e["shots_actual"] != h3.SHOTS:
            t6_shots_ok = False
        if e["kind"] not in ("structure", "negative_control",
                             "kalibrier_structure"):
            continue
        pt = pts[(e["arm"], e["P"])]
        rc = aer.ratio_from_counts(e["counts"], pt, h3a.NQ_BY_ARM[e["arm"]])
        t3_dev = max(t3_dev, abs(rc["share"] - _folded_share(rc["n_hat"], pt)))
        t6_mass_dev = max(t6_mass_dev, abs(rc["m_hat"] - pt["m"]))
    t3_ok = t3_dev <= e2.T3_TOL
    t6_ok = t6_shots_ok and t6_mass_dev <= e2.T6_MASS_TOL

    # --- t4: Negativ-Kontrollen identische Mechanik wie 044 (4 Kontrollen
    #     imselbe (arm, P)-Grid: 181-d3/467-d5) ---
    controls = {}
    t4_ok = True
    for name, c in cs_by_name.items():
        if c["kind"] != "negative_control":
            continue
        e = raw_by_name[name]
        pt_ref = pts[(c["arm"], c["P"])]
        nq = h3a.NQ_BY_ARM[c["arm"]]
        share = aer.ratio_from_counts(e["counts"], pt_ref, nq)["share"]
        edge = c["lower_prime_band_edge"]
        ok = share < edge
        t4_ok = t4_ok and ok
        controls[name] = {
            "measured_share": share,
            "expected_share": c["expected_share"],
            "lower_prime_band_edge": edge,
            "ok": ok,
        }

    # --- t5 (055-Form): Sets gefroren; das transpile-Streifen liest den
    #     055-ISA-Report (transpile-Subdict + top-level Totals) und BESIEGELT
    #     die C3-Bindung an den VOR Messung committeten c'-Block ---
    verdict_set_raw = {(e["arm"], e["P"]) for e in raw["counts"]
                       if e["kind"] == "structure"}
    point_set_frozen = {(arm, p["P"]) for arm in p48.ARMS
                        for p in prereg["prediction_freeze"]["points"][arm]}
    cal_set_raw = {(e["arm"], e["P"]) for e in raw["counts"]
                   if e["kind"] == "kalibrier_structure"}
    cal_set_frozen = {(arm, p["P"]) for arm in p48.ARMS
                      for p in prereg["kalibrier_bein"]["points"][arm]}
    point_set_ok = verdict_set_raw == point_set_frozen
    cal_set_ok = cal_set_raw == cal_set_frozen
    name_set_ok = (set(cs_by_name) == set(raw_by_name))
    transpile_ok = (
        raw["transpile"] == {
            "optimization_level": isa["transpile"]["optimization_level"],
            "seed_transpiler": isa["transpile"]["seed_transpiler"],
            "isa_2q_total": isa["total_two_q"],
            "isa_2q_max": isa["max_two_q"],
        }
        and isa["transpile"]["optimization_level"] == 3
        and isa["transpile"]["seed_transpiler"] == qpu.TRANSPILE_SEED
        and isa["prereg_md5"] == PREREG_MD5
        and isa["status"] == "ISA_FORCED_REPORT_COMPLETED"
        and isa["verdict"] == "ISA_OK")
    run_config_ok = (raw["registered_run_config"]
                     == prereg["hardware_parameters"]["run_config"])
    t5_ok = (point_set_ok and cal_set_ok
             and name_set_ok and transpile_ok and run_config_ok
             and raw["n_circuits"] == p48.N_CIRCUITS
             and len(raw["counts"]) == p48.N_CIRCUITS)

    t_fail_other = not (md5_ok and bp_md5_ok and t3_ok and t5_ok and t6_ok)

    # --- p_ro pro Arm wie 044 (cal_{nq}q aus DEMSELBEN Job) ---
    p_ro_by_nq = {}
    for arm in p48.ARMS:
        nq = h3a.NQ_BY_ARM[arm]
        cal_c = raw_by_name.get(f"cal_{nq}q")
        p_ro_by_nq[nq] = (aer.p0_fraction(cal_c["counts"], nq)
                          if cal_c else 0.0)

    # --- Punkte (37 = 13 Holdout + 24 Kalibrier): 3 Reps -> ratio_hw;
    #     kappa_hat = P_L/P_ro_ref; b_P aus dem committeten Aer-Zweig;
    #     c_p aus der gefrorenen cP_freeze.  044-Mechanik bit-gleich ---
    points = {}
    for arm in p48.ARMS:
        nq = h3a.NQ_BY_ARM[arm]
        p_ro = p_ro_by_nq[nq]
        ro_hat = 1.0 - p_ro ** (1.0 / nq) if p_ro > 0 else None
        for key in sorted(k for k in pts if k[0] == arm):
            pt = pts[key]
            P = pt["P"]
            pkey = h3a.pkey((arm, P), pts)
            prefix = "struct" if pt["set"] == "verdict" else "calstruct"
            lprefix = "loschmidt" if pt["set"] == "verdict" else "calloschmidt"
            ratios, missing = [], []
            for r in range(h3a.K_REPEATS):
                e = raw_by_name.get(f"{prefix}_{arm}_{P}_r{r}")
                if e is None:
                    missing.append(r)
                    continue
                ratios.append(aer.ratio_from_counts(
                    e["counts"], pt, nq)["ratio"])
            ratio = float(np.mean(ratios)) if ratios else None
            los = raw_by_name.get(f"{lprefix}_{arm}_{P}")
            p_l = aer.p0_fraction(los["counts"], nq) if los else 0.0
            kappa = p_l / p_ro if p_ro > 0 else None
            bp = stage3["b_p"].get(pkey)
            c_p = prereg["prediction_freeze"]["cP_freeze"][pkey]
            rec = {
                "P": P, "nq": nq, "m": pt["m"], "set": pt["set"],
                "ratio_hw": ratio, "ratio_reps": ratios,
                "ratio_std": (float(np.std(ratios)) if ratios else None),
                "missing_reps": missing,
                "P_L": p_l, "P_ro_ref": p_ro, "kappa_hat": kappa,
                "kappa_ok": kappa is not None and kappa >= h3.KAPPA_CEILING,
                "b_p_aer": bp, "c_p": c_p,
                "in_gamma_fit": pt["set"] == "cal",
            }
            if kappa is not None and bp is not None and ro_hat is not None:
                rec["ratio_ro_exact"] = aer.ratio_ro_exact(pt, ro_hat, nq)
                rec["delta_cal"] = (rec["ratio_ro_exact"] + bp * (kappa - 1.0)
                                    - ratio) if ratio is not None else None
            else:
                rec["ratio_ro_exact"] = None
                rec["delta_cal"] = None
            points[pkey] = rec

    # --- in-job gamma_arm-Fit (lsq-durch-Null je Arm): q3 n_cal 8,
    #     q5 n_cal 16 (das ist das geforderte FPrio-8-Refit) ---
    gamma_arm = {}
    for arm in p48.ARMS:
        rows = []
        for key in sorted(k for k in points if k.startswith(f"cal|{arm}|")):
            v = points[key]
            if v["delta_cal"] is not None:
                rows.append({"c_p": v["c_p"], "delta_cal": v["delta_cal"]})
        g = fit_gamma_arm(rows) if rows else None
        gamma_arm[arm] = {"gamma": g, "n_cal": len(rows), "rows": rows}

    # --- center_v3 + band-Flags (v3 und v2 identische Mechanik) ---
    for pkey, v in points.items():
        arm = pkey.split("|")[1]
        nq = v["nq"]
        kappa, ratio = v["kappa_hat"], v["ratio_hw"]
        g = gamma_arm[arm]["gamma"] if gamma_arm[arm]["gamma"] is not None else 0.0
        if kappa is not None and v["b_p_aer"] is not None and ratio is not None:
            ro_hat = 1.0 - v["P_ro_ref"] ** (1.0 / nq)
            c3v = float(center_v3(kappa, pts[(arm, v["P"])], ro_hat,
                                  v["b_p_aer"], g, v["c_p"], nq))
            res = ratio - c3v
            v["gamma_used"] = g
            v["center_v3"] = c3v
            v["res_v3"] = res
            v["in_band_sharp"] = bool(abs(res) <= w_b)
            v["in_band_coarse"] = bool(abs(res) <= w_a)
            v["below_sharp"] = bool(ratio < c3v - w_b)
            v["below_coarse"] = bool(ratio < c3v - w_a)
            v["ceiling"] = (1.0 - 1.0 / h3.SHOTS) \
                * pts[(arm, v["P"])]["ratio_true"] + pts[(arm, v["P"])]["L_q"]
            v["above_ceiling_w_b"] = bool(ratio > v["ceiling"] + w_b)
            v["above_ceiling_w_a"] = bool(ratio > v["ceiling"] + w_a)
            v["above_ceiling_w_b"] = ratio > v["ceiling"] + w_b
            v["above_ceiling_w_a"] = ratio > v["ceiling"] + w_a
        else:
            v["gamma_used"] = g
            v["center_v3"] = v["res_v3"] = None
            v["in_band_sharp"] = v["in_band_coarse"] = None
            v["below_sharp"] = v["below_coarse"] = None
            v["ceiling"] = None
            v["above_ceiling_w_b"] = v["above_ceiling_w_a"] = None

    vals = [v for v in points.values() if v["ratio_hw"] is not None]
    holdout_vals = [v for k, v in points.items() if k.startswith("verdict|")
                    and v["ratio_hw"] is not None]
    n_kappa_low = sum(1 for v in vals if not v["kappa_ok"])
    n_below_sharp = sum(1 for v in holdout_vals if v["below_sharp"])
    n_above_ceiling = sum(1 for v in holdout_vals if v["above_ceiling_w_b"])
    n_in_sharp = sum(1 for v in holdout_vals if v["in_band_sharp"])
    all_in_coarse = (len(holdout_vals) == 13
                     and all(v["in_band_coarse"] for v in holdout_vals))
    verdict_inputs = {
        "n_points": len(points), "n_evaluated": len(vals),
        "n_holdout": sum(1 for k in points if k.startswith("verdict|")),
        "n_kalibrier": sum(1 for k in points if k.startswith("cal|")),
        "n_kappa_low_union": n_kappa_low,
        "n_below_sharp": n_below_sharp,
        "n_above_ceiling_sharp": n_above_ceiling,
        "n_in_sharp": n_in_sharp,
        "n_outside_sharp": len(holdout_vals) - n_in_sharp,
        "all_in_coarse_w_a": all_in_coarse,
        "n_below_coarse_w_a": sum(1 for v in holdout_vals if v["below_coarse"]),
        "gamma_arm": {arm: gamma_arm[arm]["gamma"] for arm in p48.ARMS},
        "n_cal_per_arm": {arm: gamma_arm[arm]["n_cal"] for arm in p48.ARMS},
    }

    # --- Safeguard-Void (Reihenfolge per Register): refit-Status aus der
    #     kappa_low-Union (descriptiv-void; kein kritisches Verdict-Ableiten)
    #     ---
    refit_status = REFIT_INVALID if n_kappa_low >= 2 else REFIT_OK

    # --- b_p_konsistenz (Aer-Zweig): die ±1-ulp-Lesart ist REGISTRIERT
    #     (phase-11c-Praezedenz); die Divergenz-Zeilen gehen als Dokumen
    #     mit — KEIN Kontroll-Kanal, keine Toleranz-Erhoehung. ---
    bpk = stage3.get("b_p_konsistenz_zusammenfassung") or {}
    divergent_keys = bpk.get("divergente_keys") or sorted(
        k for k, v in (stage3.get("b_p_konsistenz") or {}).items()
        if not v.get("ok"))
    b_p_konsistenz_doku = {
        "klasse": bpk.get("klasse"),
        "lesung": bpk.get("lesung"),
        "tol": bpk.get("tol"),
        "n_abweichungen": bpk.get("n_abweichungen"),
        "n_legacy_checked": bpk.get("n_legacy_checked"),
        "n_ladder_fresh": bpk.get("n_ladder_fresh"),
        "divergente_zeilen": {k: stage3["b_p_konsistenz"][k]
                              for k in divergent_keys},
    }

    # --- C1: Session-Anker-Paritaet (rho(res', res_S1) an den P-sortierten
    #     verdict-Zeilen >= committeter S1->S2-Anker).  S1/S2-Evals sind
    #     COMMMITETE Artefakte; das Kriterium ist das gefrorene
    #     session_anchors.kriterium_C1_* (kein neuer Fit). ---
    s1_arm = {arm: p48.arm_rows(p48.H3_EVAL_S1, arm)
              for arm in p48.ARMS}
    s2_arm = {arm: p48.arm_rows(p48.H3_EVAL_S2, arm) for arm in p48.ARMS}
    anchor_criteria = {arm: prereg["session_anchors"][f"kriterium_C1_{k}"]
                       for arm, k in (("q5_d5", "q5"), ("q3_d3", "q3"))}
    c1 = {}
    for arm, anchor in (("q5_d5", p48.ANCHOR_RHO_Q5),
                        ("q3_d3", p48.ANCHOR_RHO_Q3)):
        k = "q5" if arm == "q5_d5" else "q3"
        rows_fresh = arm_rows(points, arm)["verdict"]
        rows_s1 = s1_arm[arm]["verdict"]
        Ps = rows_fresh["P"]
        p_arranged = Ps == rows_s1["P"]
        res_ok = all(r is not None for r in rows_fresh["res"])
        if p_arranged and len(Ps) == len(rows_s1["res"]) and res_ok:
            rho = p48.spearman(rows_fresh["res"], rows_s1["res"])
            q95, n_perm = p48.q95_exact_perm(rows_s1["res"], rows_fresh["res"])
            c1[arm] = {
                "kriterium": anchor_criteria[arm],
                "anchor_pin": anchor,
                "rho_fresh_vs_s1": rho, "ok": rho >= anchor,
                "q95_perm_null_fresh": q95, "n_perm": n_perm,
                "q95_rang": "descriptiv (n-Permutationen, Sekundaer-Benchmark)",
                "res_fresh": rows_fresh["res"], "res_s1": rows_s1["res"],
                "P_sortiert": Ps,
                "rho_s1_s2_kontext": prereg["session_anchors"][
                    f"rho_S1_S2_{k}_verdict_pin"],
            }
        else:
            c1[arm] = {"kriterium": anchor_criteria[arm], "anchor_pin": anchor,
                       "rho_fresh_vs_s1": None, "ok": False,
                       "grund": f"P-Reihen/P-Set/res-divergieren (fresh {Ps}, "
                                f"P-Check {p_arranged}, res ok {res_ok}) vs "
                                f'S1 {rows_s1["P"]})'}
    # FPrio-4-Kontext (descriptiv): der Pool-Anker aus dem Prereg (13 Reihen =
    # exakt die 13 055-verdict-Reihen).
    pooled_fresh = (c1["q5_d5"].get("res_fresh", [])
                    + c1["q3_d3"].get("res_fresh", []))
    pooled_s1 = (c1["q5_d5"].get("res_s1", [])
                 + c1["q3_d3"].get("res_s1", []))
    rho_pooled = (p48.spearman(pooled_fresh, pooled_s1)
                  if len(pooled_fresh) == len(pooled_s1) else None)
    c1["pooled"] = {
        "massstab": prereg["session_anchors"]["c1_massstab"],
        "rho_fresh_vs_s1": rho_pooled,
        "rho_S1_S2_pooled_13_pin": prereg["session_anchors"][
            "rho_S1_S2_pooled_13_pin"],
        "anchor_pin": p48.ANCHOR_RHO_POOLED,
        "n": len(pooled_fresh),
        "verdict_role": "descriptiv (nicht verdict-tragend; Pin-Kontext)",
    }

    # --- c1_c_vorprobe frisch (descriptiv): rho(res'_Arm, c_p_Arm) je Arm
    #     gegen die registrierten Vorprobe-Werte (S1-Pins als Kontext) ---
    cvp_reg = prereg.get("c1_c_vorprobe")
    c1_c_vorprobe_fresh = {"registriert_in_prereg": cvp_reg, "arme": {}}
    for arm in p48.ARMS:
        rows_fresh = arm_rows(points, arm)["verdict"]
        res_ok = all(r is not None for r in rows_fresh["res"])
        rho_c = (p48.spearman(rows_fresh["res"], rows_fresh["c_p"])
                 if res_ok else None)
        c1_c_vorprobe_fresh["arme"][arm] = {
            "rho_fresh_res_c_p": rho_c,
            "vorprobe_pin": (p48.RHO_C_VORPROBE_Q5 if arm == "q5_d5"
                             else p48.RHO_C_VORPROBE_Q3),
            "ok_descriptiv": (rho_c is not None
                              and rho_c >= (p48.RHO_C_VORPROBE_Q5
                                            if arm == "q5_d5"
                                            else p48.RHO_C_VORPROBE_Q3)),
            "reihen": rows_fresh["P"],
        }

    # --- C2: below-Sharp-Transfer auf dem frischen Arm q5 (S2-Kern {467,
    #     673} BOTH + S1-Zweitstufe {467, 547, 673} mindest. 2/3) ---
    below_fresh_q5 = sorted(
        P for P in s1_arm["q5_d5"]["verdict"]["P"]
        if points[f"verdict|q5_d5|{P}"]["below_sharp"])
    kern_ok = (467 in below_fresh_q5) and (673 in below_fresh_q5)
    zweitstufe_n = sum(1 for P in (467, 547, 673) if P in below_fresh_q5)
    c2 = {
        "q5_kern": prereg["c2_criteria"]["q5_kern"],
        "q5_zweitstufe": prereg["c2_criteria"]["q5_zweitstufe_S1"],
        "below_fresh_q5": below_fresh_q5,
        "kern_ok": kern_ok, "zweitstufe_n": zweitstufe_n,
        "ok": bool(kern_ok and zweitstufe_n >= 2),
        "S1_below_vergleich": s1_arm["q5_d5"]["verdict"]["below_sharp"],
        "S2_below_vergleich": s2_arm["q5_d5"]["verdict"]["below_sharp"],
    }

    # --- C3: Geometrie-Counter (Delta-res' vs Delta-c je Arm, exakt-
    #     Permutations-Spearman >= q95) — Delta-c NUR aus dem committeten
    #     ISA-Report (row_c_prime.delta_c_vs_cP der verdict-Zeilen).
    #     Delta-c degenerat (alles 0) = registrierte strukturelle Null. ---
    c3 = {
        "statistic": prereg["c3_geometry_counter"]["statistic"],
        "feuer_kriterium": prereg["c3_geometry_counter"]["feuer_kriterium"],
        "delta_res_def": prereg["c3_geometry_counter"]["delta_res"],
        "delta_c_def": prereg["c3_geometry_counter"]["delta_c"],
        "c_prime_lesart": isa["c_prime_lesart"],
        "arme": {},
    }
    for arm, q95_pin in (("q5_d5", p48.Q95_PERM_Q5),
                         ("q3_d3", p48.Q95_PERM_Q3)):
        Ps = c1[arm].get("P_sortiert") or sorted(
            r["P"] for r in prereg["prediction_freeze"]["points"][arm])
        delta_res, delta_c, unklar = [], [], []
        for P in Ps:
            pkey = f"verdict|{arm}|{P}"
            fresh_r = points[pkey]["res_v3"]
            entry = (isa.get("row_c_prime") or {}).get(pkey) \
                if isinstance(isa.get("row_c_prime"), dict) else None
            if fresh_r is None or P not in s1_arm[arm]["verdict"]["P"] \
                    or entry is None or entry.get("delta_c_vs_cP") is None:
                unklar.append({"P": P, "fresh_res": fresh_r,
                               "in_S1_grid": P in s1_arm[arm]["verdict"]["P"],
                               "c_prime_entry": entry})
                continue
            s1_r = dict(zip(s1_arm[arm]["verdict"]["P"],
                            s1_arm[arm]["verdict"]["res"]))[P]
            delta_res.append(fresh_r - s1_r)
            delta_c.append(entry["delta_c_vs_cP"])
        fire = False
        note = None
        rho = None
        q95 = None
        if unklar:
            note = "Delta-Vektoren unvollstaendig (%d unvergleiche: %s)" \
                   % (len(unklar), unklar)
        elif len(delta_c) and max(delta_c) == min(delta_c) == 0.0:
            note = "Delta-c degenerat: alle ratio_2q bit-gleich 1 -> " \
                   "Delta-c == 0 (registrierte strukturelle Null, kein Feuer)"
        else:
            rho = p48.spearman(delta_res, delta_c)
            q95, n_perm3x = p48.q95_exact_perm(delta_res, delta_c)
            fire = bool(rho >= q95_pin)
        c3["arme"][arm] = {
            "n_vergleichbar": len(delta_c), "unvergleiche": unklar,
            "delta_res": delta_res, "delta_c": delta_c,
            "rho": rho, "q95_pin": q95_pin, "q95_fresh_null": q95,
            "feuer": fire, "note": note,
        }
    c3_fire_q5 = c3["arme"]["q5_d5"]["feuer"]
    c3_fire_q3 = c3["arme"]["q3_d3"]["feuer"]

    # --- FPrio-8: Refit + OLS-Zerlegung F + falsifikatorlinie F-Zeile 8 ---
    rows_q5_cal = gamma_arm["q5_d5"]["rows"]
    cps = [r["c_p"] for r in rows_q5_cal]
    dls = [r["delta_cal"] for r in rows_q5_cal]
    ols_q5 = _ols_decomp(cps, dls) if len(cps) >= 3 else None
    ols_q3 = (None if len(gamma_arm["q3_d3"]["rows"]) < 3
              else _ols_decomp([r["c_p"] for r in gamma_arm["q3_d3"]["rows"]],
                               [r["delta_cal"] for r in
                                gamma_arm["q3_d3"]["rows"]]))
    gam_fresh, se_fresh = _se_no_int(cps, dls) if cps else (None, None)
    mean_c_fresh = float(np.mean(cps)) if cps else None
    f8_resid_sd = (ols_q5["resid_sd_ddof2"] if ols_q5 else None)
    fprio8 = {
        "gamma_refit_q5": gamma_arm["q5_d5"]["gamma"],
        "gamma_refit_q3": gamma_arm["q3_d3"]["gamma"],
        "n_cal_q5": gamma_arm["q5_d5"]["n_cal"],
        "n_cal_q3": gamma_arm["q3_d3"]["n_cal"],
        "ols_lesart_q5": ols_q5, "ols_lesart_q3": ols_q3,
        "se_provenanz_fresh": {
            "se_no_int": se_fresh,
            "mean_c": mean_c_fresh,
            "se_times_mean_c": (se_fresh * mean_c_fresh
                                if se_fresh is not None else None),
            "pin_se_no_int_S1": p48.SE_NO_INT_S1_Q5_CAL,
            "pin_se_times_mean_c_S1": p48.SE_C_MEAN_S1,
            "pin_sqrt_skalierung_n16_S1": p48.SQRT_EXPECT_N16,
            "registrierter_text": prereg["fprio8_refit"]["d5_se_provenance"],
            "hinweis": "descriptiv: die Frische-SE stammt aus DEMSELBEN "
                       "055-Job (16 Kal-Reihen), nicht aus den S1-Zeilen; "
                       "die Pins dokumen die S1-Provenanz-Struktur."},
        "falsifikatorlinie_f_zeile_8": {
            "statistik": prereg["fprio8_refit"]["falsifikatorlinie_F_zeile_8"],
            "resid_sd_q5_n16_ddof2": f8_resid_sd,
            "grenze": 0.01,
            "ergebnis": (F8_KIPPT if f8_resid_sd is not None
                         and f8_resid_sd < 0.01 else
                         (F8_BLEIBT if f8_resid_sd is not None else None)),
            "nur_lesbar_bei_refit_ok": refit_status == REFIT_OK},
    }

    # --- FPrio-5b: Echo-Leiter (044-Mechanik bit-gleich; descriptiv gegen
    #     die committeten S1/S2-Ladder-Werte — fez-scoped Lesart (b)) ---
    ladder = {}
    for arm in p48.ARMS:
        nq = h3a.NQ_BY_ARM[arm]
        p_ro = p_ro_by_nq[nq]
        P = h3a.ladder_anchor(arm)
        pkey = f"verdict|{arm}|{P}"
        r1_name = anchor_r1_name(arm, P, pkey)
        kappas, r1_consistent = {}, None
        for r in h3.LADDER_REPEATS:
            name = (r1_name if r == 1 else f"ladder_{arm}_{P}_r{r}")
            e = raw_by_name.get(name)
            if e is None or p_ro <= 0:
                kappas[f"r{r}"] = None
                continue
            kappas[f"r{r}"] = aer.p0_fraction(e["counts"], nq) / p_ro
            if r == 1:
                r1_consistent = bool(kappas[f"r{r}"]
                                     == points[pkey]["kappa_hat"])
        fit = None
        if all(kappas[f"r{r}"] is not None for r in h3.LADDER_REPEATS):
            fit = h3a.fit_echo_ladder(
                [kappas[f"r{r}"] for r in h3.LADDER_REPEATS],
                list(h3.LADDER_REPEATS))
        ladder[arm] = {
            "P": P, "repeats": list(h3.LADDER_REPEATS),
            "r1_shared_with_loschmidt": True,
            "kappa_r": kappas,
            "r1_konsistent_mit_kappa_hat_anker": r1_consistent,
            "fit_kappa_block": (fit["kappa_block"] if fit else None),
            "fit_max_res_log": (fit["max_res_log"] if fit else None),
            "verdict_role": "NICHT verdict-tragend (Diagnostik)",
        }
    for arm in p48.ARMS:
        s1_ladder = _echo_from_eval(p48.H3_EVAL_S1, arm)
        s2_ladder = _echo_from_eval(p48.H3_EVAL_S2, arm)
        ladder[arm]["S1_vergleich"] = s1_ladder
        ladder[arm]["S2_vergleich"] = s2_ladder
        ladder[arm]["fez_lesart_b"] = {
            "lesart": "FPrio-5-Lesart (b): die 12 Unforced-Circuits machen "
                      "die Echo-Leiter auf Fez messbar (der K2-Kingston-Lauf "
                      "kippte die Substrat-Transfer-Lesart (a))",
            "fit_kappa_block_fresh": ladder[arm]["fit_kappa_block"],
            "fit_kappa_block_S1": s1_ladder.get("fit_kappa_block"),
            "fit_kappa_block_S2": s2_ladder.get("fit_kappa_block"),
        }

    # --- alternative Lesarten (dokumentiert, nicht verdict-ersetzend) ---
    alt = {
        "refuted_mit_w_a": {
            "n_below_coarse_w_a": sum(1 for v in holdout_vals
                                      if v["below_coarse"]),
            "verdict_waere": ("REFUTED-Klasse unterm w_A-Streifen"
                              if sum(1 for v in holdout_vals
                                     if v["below_coarse"]) >= 2 else None),
        },
        "amplification_mit_w_a": {
            "n_above_ceiling_w_a": sum(1 for v in holdout_vals
                                       if v["above_ceiling_w_a"]),
        },
        "gamma_konfund_alt": {
            "statistik": "res_v3 mit den KOMMITTIERTEN Session-F-gammas "
                         "(S1-Pins q5 0.038128743451453374 / q3 "
                         "0.009105648402709013) statt der 055-Refits — "
                         "descriptiv (Konfund-Kontrolle gamma->Band).",
            "gamma_committed": {"q5_d5": prereg["fprio8_refit"][
                                    "committed_F_anchors"]["q5"][
                                    "gamma_committed"],
                                "q3_d3": prereg["fprio8_refit"][
                                    "committed_F_anchors"]["q3"][
                                    "gamma_committed"]},
        },
        "erbe_044_gesetz": {
            "statistik": "die 044-decide_verdict-Mechanik auf dem 055-Daten — "
                         "descriptiv (das 055-Verdict folgt der gefrorenen "
                         "055-verdict_map mit Kcontrol/Refit-Void vor den "
                         "kritischen Klassen).",
        },
        "fprio5_lesart_b": "siehe echo_ladder.*.fez_lesart_b",
    }
    verdict_ga_044 = h3e.decide_verdict(
        t4_violated=not t4_ok, t_fail_other=False,
        n_kappa_low_union=n_kappa_low, n_above_ceiling=n_above_ceiling,
        n_below_sharp=n_below_sharp, n_in_sharp=n_in_sharp,
        all_in_coarse=all_in_coarse, n_holdout=verdict_inputs["n_holdout"])
    alt["erbe_044_gesetz"]["verdict_waere"] = verdict_ga_044
    for pkey in sorted(k for k in points if k.startswith("verdict|")):
        v = points[pkey]
        arm = pkey.split("|")[1]
        nq = v["nq"]
        kappa, ratio = v["kappa_hat"], v["ratio_hw"]
        if kappa is None or ratio is None or v["b_p_aer"] is None \
                or v["P_ro_ref"] is None:
            continue
        ro_hat = 1.0 - v["P_ro_ref"] ** (1.0 / nq)
        g_alt = prereg["fprio8_refit"]["committed_F_anchors"][
            "q5" if arm == "q5_d5" else "q3"]["gamma_committed"]
        center_alt = h3e.center_v3(kappa, pts[(arm, v["P"])], ro_hat,
                                   v["b_p_aer"], g_alt, v["c_p"], nq)
        res_alt = ratio - center_alt
        alt["gamma_konfund_alt"].setdefault("zeilen", {})[pkey] = {
            "res_v3_alt_gamma": res_alt,
            "res_v3_fresh_gamma": v["res_v3"],
            "below_sharp_alt": ratio < center_alt - w_b,
            "below_sharp_fresh": v["below_sharp"],
        }

    # --- ISA-leg-Dokumentation (forced/auto-Tally + Gate-Vertrags-Spiegel) ---
    per_circuit = isa["per_circuit"]
    n_forced = sum(1 for v in per_circuit.values()
                   if v["layout_source"] == "forced")
    n_auto = sum(1 for v in per_circuit.values()
                 if v["layout_source"] == "auto")
    unforced = [a["name"] for a in isa["unforced_bit_anchor"]]
    anchor_ok = bool(isa["unforced_bit_anchor"]) \
        and all(a["ok"] for a in isa["unforced_bit_anchor"])
    isa_leg = {
        "status": isa["status"], "verdict": isa["verdict"],
        "backend": isa.get("backend"),
        "layout_tally": {"forced": n_forced, "auto": n_auto,
                         "gesamt": len(per_circuit)},
        "unforced_bit_anchor": {"ok": anchor_ok, "namen": unforced},
        "row_assignment_len": {arm: len(isa["row_assignment"][arm])
                               for arm in sorted(isa["row_assignment"])},
        "fallback_rows": [r["row"] for arm in isa["row_assignment"]
                          for r in isa["row_assignment"][arm]
                          if r["fallback_used"]],
        "slots_per_arm": isa["slots_per_arm"],
        "coupling_map_edges": isa["coupling_map_edges"],
        "ceiling_check": isa["ceiling_check"],
        "c_prime_lesart": isa["c_prime_lesart"],
        "run_config_frozen": isa.get("run_config_frozen"),
    }
    gate = None
    if gate_path and os.path.exists(gate_path):
        with open(gate_path, encoding="utf-8") as fh:
            gate = json.load(fh)
    if gate is not None:
        isa_leg["gate_spiegel"] = {
            "gate_total_two_q": gate.get("total_two_q"),
            "gate_max_two_q": gate.get("max_two_q"),
            "gesammt_two_q_uebereinstimmend":
                gate.get("total_two_q") == isa["total_two_q"],
            "max_two_q_uebereinstimmend":
                gate.get("max_two_q") == isa["max_two_q"],
            "gate_verdict": gate.get("verdict"),
            "gate_prereg_md5": gate.get("prereg_md5"),
            "gate_prereg_md5_ok": gate.get("prereg_md5") == PREREG_MD5,
            "gate_n_circuits": gate.get("n_circuits"),
        }

    # --- Verdict: gefrorene Reihenfolge Kcontrol-void -> Refit-void ->
    #     D.7 -> P-Transfer -> Mixed -> Unklar ---
    verdict = decide_verdict_055(
        t_fail_other=t_fail_other, refit_invalid=(refit_status
                                                  == REFIT_INVALID),
        c1_q5=c1["q5_d5"]["ok"], c1_q3=c1["q3_d3"]["ok"], c2=c2["ok"],
        c3_fire_q5=c3_fire_q5, c3_fire_q3=c3_fire_q3)
    vmap = prereg.get("verdict_map") or {}
    if not vmap:
        raise ValueError("Prereg ohne verdict_map (055-Vertrag verletzt)")

    doc = {
        "experiment": p48.EXPERIMENT,
        "hypothesis": p48.HYPOTHESIS,
        "leg": p48.LEG,
        "status": "EVALUATED",
        "prereg_md5": prereg_md5_out,
        "raw_backend": raw.get("backend"),
        "raw_job_meta": raw.get("job_meta"),
        "raw_counts_md5": raw.get("counts_md5"),
        "counts_md5_verified": md5_ok,
        "b_p_provenance": {
            "source": STAGE3_PATH,
            "prereg_md5_ok": bp_md5_ok,
            "status": stage3["status"],
            "konsistenz": b_p_konsistenz_doku,
        },
        "w_b_doubleprime": w_b, "w_a": w_a,
        "w_b_source": {"path": e2.STAGE2_PATH,
                       "registered": "Wiederverwendung (044-Praezedenz: "
                                     "w_B'' == w_B', Phase-10b-Konvention); "
                                     "055-Prereg-Pin w_band"},
        "kappa_ceiling": h3.KAPPA_CEILING,
        "refit_status": refit_status,
        "gamma_arm": gamma_arm,
        "kontrollen": {
            "t1_backcompat": "inherited (committetes Offline-Suite-Bein: "
                             "tests/test_pt_ram_q_prio48*.py mit 044-Erbe)",
            "t2_v2_anchors": "inherited (committetes Offline-Suite-Bein: "
                             "tests/test_pt_ram_q_prio48*.py mit 044-Erbe)",
            "t3_identity_two_ways": {"ok": t3_ok, "max_dev": t3_dev,
                                     "tol": e2.T3_TOL,
                                     "kinds": ["structure",
                                               "negative_control",
                                               "kalibrier_structure"]},
            "t4_negative_must_not_fire": {"ok": t4_ok, "controls": controls,
                                          "edge_convention":
                                          "registrierte Freeze-A''-Kante "
                                          "(kappa = 0.81-Ecke, konservativ "
                                          "fuer must-not-fire)"},
            "t5_gate_set_frozen": {"ok": t5_ok,
                                   "point_set_ok": point_set_ok,
                                   "cal_set_ok": cal_set_ok,
                                   "name_set_ok": name_set_ok,
                                   "transpile_ok": transpile_ok,
                                   "run_config_ok": run_config_ok,
                                   "praezedenz": "055-Lesart: transpile an "
                                   "den ISA-055-Report gebunden (Subdict "
                                   "transpile + Totals; das C3-c'-Binding "
                                   "ist der VOR-Messung-committete "
                                   "row_c_prime-Block)"},
            "t6_mass_conservation": {"ok": t6_ok, "shots_ok": t6_shots_ok,
                                     "max_mass_dev": t6_mass_dev},
        },
        "punkte": points,
        "verdict_inputs": verdict_inputs,
        "c1_sessions_anker": c1,
        "c1_c_vorprobe_fresh": c1_c_vorprobe_fresh,
        "c2_transfer": c2,
        "c3_geometry_counter": c3,
        "fprio8_refit": fprio8,
        "isa_leg_dokumentation": isa_leg,
        "verdict": verdict,
        "verdict_map_text": vmap.get(verdict,
                                     "kein Treffer der gefrorenen Map — "
                                     "ehrlicher Nicht-Treffer-Zweig (kein "
                                     "erfundener Verdict)"),
        "alternative_lesarten": alt,
        "echo_ladder": ladder,
        "sessions_sources": {"s1_eval": p48.H3_EVAL_S1,
                             "s2_eval": p48.H3_EVAL_S2,
                             "sessions_out": p48.SESSIONS_OUT,
                             "hinweis": "Session-Scratches untracked "
                             "(working-tree); die S1/S2-Eval-Artefakte und "
                             "das 055-Prereg/Stage3 sind committet"},
        "prior_chain": prereg.get("prior_chain"),
        "integritaet_prereg": prereg.get("integritaet"),
    }
    if prereg_path is None:
        doc["prereg_verify"] = p48.verify_frozen()
    else:
        doc["prereg_verify"] = {"skipped": True,
                                "grund": "Override-Grid (prereg_path "
                                         "gesetzt)"}
    return doc


def arm_rows(points_by_pkey, arm):
    """Verdict-Zeilen aus einem frisch berechneten points-Dict (gleiche
    Form wie p48.arm_rows auf einem Eval-Artefakt)."""
    rows = {}
    for pkey, rec in points_by_pkey.items():
        setname, armname, _ps = pkey.split("|")
        if armname != arm:
            continue
        rows.setdefault(setname, {})[rec["P"]] = rec
    out = {}
    for setname, byP in rows.items():
        Ps = sorted(byP)
        out[setname] = {
            "P": Ps,
            "res": [(float(byP[p]["res_v3"])
                     if byP[p]["res_v3"] is not None else None) for p in Ps],
            "c_p": [float(byP[p]["c_p"]) for p in Ps],
            "below_sharp": [p for p in Ps if byP[p]["below_sharp"]],
            "kappa": [(float(byP[p]["kappa_hat"])
                       if byP[p]["kappa_hat"] is not None else None)
                      for p in Ps],
        }
    return out


def write_eval(doc, path=EVAL_PATH):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    return path


if __name__ == "__main__":
    doc = evaluate()
    write_eval(doc)
    print(f"verdict: {doc['verdict']} (refit_status {doc['refit_status']})")
    vi = doc["verdict_inputs"]
    print(f"kappa_low(union): {vi['n_kappa_low_union']}/{vi['n_points']} "
          f"below_sharp: {vi['n_below_sharp']} "
          f"in_sharp: {vi['n_in_sharp']}/13 "
          f"above_ceiling: {vi['n_above_ceiling_sharp']}")
    for arm in p48.ARMS:
        print(f"gamma_arm[{arm}]: {doc['gamma_arm'][arm]['gamma']} "
              f"(n_cal {doc['gamma_arm'][arm]['n_cal']})")
    for arm in p48.ARMS:
        c1a = doc["c1_sessions_anker"][arm]
        c3a = doc["c3_geometry_counter"]["arme"][arm]
        print(f"C1[{arm}]: rho {c1a['rho_fresh_vs_s1']} "
              f">= pin {c1a['anchor_pin']}: {c1a['ok']}")
        print(f"C3[{arm}]: rho {c3a['rho']} vs q95 {c3a['q95_pin']} "
              f"-> feuer {c3a['feuer']}")
    print(f"C2: kern {doc['c2_transfer']['kern_ok']} "
          f"zweitstufe {doc['c2_transfer']['zweitstufe_n']}/3 "
          f"-> ok {doc['c2_transfer']['ok']} "
          f"(below {doc['c2_transfer']['below_fresh_q5']})")
    f8 = doc["fprio8_refit"]["falsifikatorlinie_f_zeile_8"]
    print(f"F-Zeile-8: resid_sd {f8['resid_sd_q5_n16_ddof2']} -> "
          f"{f8['ergebnis']}")