# -*- coding: utf-8 -*-
"""pt_ram_q_hardware3_eval.py — gefrorene QPU-Auswertung (Phase 11d,
EXPERIMENT 044, H-RAM-Q-4, 0 QPU im Freeze, EIN Fez-Job im Messbein).

Verdict-tragend: das v3b-Gesetz (Freeze A'', md5 baaca1f6772e07b0847fe436da7e16da)

    center_v3(kappa_hat, pt, ro_hat, b_P, gamma_arm, cP)
       = (1 - 1/S) * (ratio_ro_exact(pt, ro_hat, nq) + b_P*(kappa_hat - 1)
                      - gamma_arm*cP) + L_q

mit IN-JOB gamma_arm-Fit am KALIBRIER-Bein (die 13 Run-2-Verdict-P, frisch
gemessen, 3 Reps + gepoolter Loschmidt; LSQ-durch-Null ueber die Punkte DES
ARMS: q3 8, q5 5); Holdout = die 13 NEUEN P.  Registrierte safeguard_limits
(gafroren, md5 baaca1f6):

- band_rule:      ratio_hw ∈ [center_v3 - w_B'', center_v3 + w_B''] an den
                  13 Holdout-P; w_B'' = w_B' = 0.02787029633307472
                  (WIEDERVERWENDET, Quelle pt_ram_q_stage2b_results.json w_b);
                  grob w_A = 0.05.
- amplification:  ratio_hw > (1-1/S)*ratio_true + L_q + w -> INVALID_AMPLIFICATION
                  (einseitig; Verdict-Kante scharf w_B'' nach 10d-Praezedenz
                  -- n_above_ceiling zaehlte dort die scharfe Kante --, die
                  w_A-Lesart wird als alternative Lesart dokumentiert).
- kappa_floor:    kappa_hat < KAPPA_CEILING = 0.81 an >= 2 Punkten der UNION
                  (Verdict-P UND Kalibrier-P) -> VOID_CALIBRATION.
- falsifier:      >= 2 der 13 Holdout-P unter center_v3 - w_B'' -> REFUTED.

Raw-Counts (dat1o6qhcrkc73dtgo60, counts_md5 230098aeeb6e8716d2638e1d5fe3cfeb)
wurden VOR dieser Auswertung committed (9f5f1de, §Z.14-Disziplin); das
b_P-Provenanz-Feld prueft das committete Stage-3-Ergebnis gegen das
gefrorene Prereg (KEIN neuer Gate-Zweig — die Verdict-Map ist gefroren).
"""
import hashlib
import json

import numpy as np

import pt_ram_q_hardware as hw
import pt_ram_q_hardware_aer as aer
import pt_ram_q_hardware2_aer as s2b
import pt_ram_q_hardware2_eval as e2
import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_aer as h3a
import pt_ram_q_hardware3_qpu as qpu3

RAW_PATH = qpu3.RAW_PATH
STAGE3_PATH = "pt_ram_q_stage3_results.json"
ISA_PATH = "pt_ram_q_isa3_report.json"  # == pt_ram_q_isa3.ISA_PATH3 (Freeze B'')
EVAL_PATH = "pt_ram_q_hardware3_eval.json"
PREREG_MD5 = "baaca1f6772e07b0847fe436da7e16da"  # Freeze A''; load_frozen_prereg verifiziert beim Laden

V_CONFIRMED = "H-RAM-Q-4_NOISE_LIFT_CONFIRMED"
V_COARSE = "H-RAM-Q-4_COARSE_HOLD_SHARP_MISS"
V_REFUTED = "H-RAM-Q-4_REFUTED"
V_AMPL = "H-RAM-Q-4_INVALID_AMPLIFICATION"
V_VOID = "H-RAM-Q-4_VOID_CALIBRATION"
V_DEGENERAT = "H-RAM-Q-4_DEGENERAT"
V_INVALID = "EVALUATION_INVALID_CONTROLS_FAILED"
V_UNMATCHED = "VERDICT_MAP_UNMATCHED"


def load_w_b(stage2_path=e2.STAGE2_PATH):
    """w_B'' aus dem committeten Stage-2b-Ergebnis (Wiederverwendung
    laut Registrierung; delegiert an die Phase-10d-Lesart)."""
    return e2.load_w_b(stage2_path)


def decide_verdict(*, t4_violated, t_fail_other, n_kappa_low_union,
                   n_above_ceiling, n_below_sharp, n_in_sharp,
                   all_in_coarse, n_holdout):
    """Gefrorene verdict_map (md5 baaca1f6) mit dokumentierter
    Praezedenz (§Z.25): DEGENERAT -> INVALID -> VOID (Union) ->
    AMPL (einseitig, scharfe Kante) -> REFUTED -> CONFIRMED -> COARSE."""
    if t4_violated:
        return V_DEGENERAT
    if t_fail_other:
        return V_INVALID
    if n_kappa_low_union >= 2:
        return V_VOID
    if n_above_ceiling >= 1:
        return V_AMPL
    if n_below_sharp >= 2:
        return V_REFUTED
    if n_in_sharp == n_holdout and n_kappa_low_union == 0:
        return V_CONFIRMED
    if all_in_coarse and (n_holdout - n_in_sharp) >= 1:
        return V_COARSE
    return V_UNMATCHED


def _folded_share(n_hat, pt):
    """Zweiter Weg der t3-Identitaet (041-Theorem); bei d = q ist der Fold
    die Identitaet (Shuffle-Inertness-Theorem) — der Check laeuft trotzdem
    mechanisch ueber beide Wege."""
    N = hw.fold_mod_q(list(n_hat), pt["d"], pt["q"])
    return aer.share_hw_folded(N, pt["q"], pt["d"], pt["m"])


def fit_gamma_arm(rows):
    """gamma_arm = <cP, delta_cal>/<cP, cP> ueber die Kalibrier-P des Arms
    (LSQ-durch-Null, registrierte Formel); None bei nichtpositivem Nenner."""
    num = sum(r["c_p"] * r["delta_cal"] for r in rows)
    den = sum(r["c_p"] ** 2 for r in rows)
    return num / den if den > 0.0 else None


def center_v3(kappa_hat, pt, ro_hat, b_p, gamma_arm, c_p, nq):
    """Das gefrorene v3b-Gesetz; gamma_arm = 0 reduziert center_v3 exakt
    auf das gefrorene center_v2 (Freeze A', Phase-10b-Konvention)."""
    return (1.0 - 1.0 / h3.SHOTS) * (aer.ratio_ro_exact(pt, ro_hat, nq)
                                     + b_p * (kappa_hat - 1.0)
                                     - gamma_arm * c_p) + pt["L_q"]


def evaluate(raw_path=RAW_PATH, stage3_path=STAGE3_PATH, isa_path=ISA_PATH,
             prereg_path=None, points=None, cal=None,
             stage3_prereg_md5=None):
    """Phase-11d-Auswertung; gefrorene 044-v3b-Gesetze, ungeaendert.

    Override-Parameter (Phase H-RAM-Q-6-Refaktor, D2/D3-Bein K2): alle
    None (Default) = bit-identisches Verhalten auf dem GEFRORENEN
    26-Punkte-Grid (Beweis-Test in tests/test_pt_ram_q6_k2_refactor_proof
    .py gegen committete Fingerprints).  Fuer ein frisches Grid:
    prereg_path = frisches gefrorenes Prereg, points/cal = frische
    Punkt-Records (Verdict/Kalibrier getrennt, wie im Builder),
    stage3_prereg_md5 = md5 des frischen Stage-3-Prereg-Bindings.
    w_b/w_a/Gesetz/Verdict-Map-Struktur kommen UEBERALL aus den
    gefrorenen 044-Konstanten — kein Fork des Gesetzes."""
    raw = json.load(open(raw_path, encoding="utf-8"))
    with open(stage3_path, encoding="utf-8") as fh:
        stage3 = json.load(fh)
    with open(isa_path, encoding="utf-8") as fh:
        isa = json.load(fh)
    if prereg_path is None:
        prereg = h3.load_frozen_prereg()
        prereg_md5_out = PREREG_MD5
    else:
        with open(prereg_path, encoding="utf-8") as fh:
            prereg = json.load(fh)
        with open(prereg_path, "rb") as fh:
            prereg_md5_out = hashlib.md5(fh.read()).hexdigest()
    w_b = load_w_b()
    w_a = h3a.W_A
    pts = h3a.all_points() if (points is None and cal is None) else \
        {**(dict(points) if points else {}), **(dict(cal) if cal else {})}
    cs_by_name = {c["name"]: c
                  for c in h3a.build_hardware_circuit_set(points, cal)}
    raw_by_name = {e["name"]: e for e in raw["counts"]}

    # --- job_integrity: md5 der Counts + b_P-Provenanz (dokumentiert,
    #     kein neuer Gate-Zweig: die Verdict-Map ist gefroren) ---
    md5_ok = (qpu3.counts_md5([e["counts"] for e in raw["counts"]])
              == raw["counts_md5"])
    bp_md5_ok = stage3["prereg_md5"] == (stage3_prereg_md5 or PREREG_MD5)

    # --- t3 (zwei Wege) + t6 (Shots/Masse) ueber ALLE State-Circuits
    #     (structure + negative_control + kalibrier_structure — die
    #     Kalibrier-P sind verdict-tragend in der kappa-Gate-Union,
    #     also ist auch ihr Zustand verdict-relevant).  Echo-Leiter:
    #     NICHT hier (Echo-Block-Struktur, separate Diagnostik). ---
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

    # --- t4: Negativ-Kontrollen gegen die registrierte Kante (kappa =
    #     0.81-Ecke, konservativ fuer must-not-fire); Exact-kappa-Variante
    #     als Diagnostik ---
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

    # --- t5: Gate-Set gefroren (Punkt-Sets beider Beine + Namen) +
    #     Transpile-Record == ISA3-Report (Freeze B'') — das Verdict-Set
    #     ist das gefrorene prediction_freeze.points (13 Holdout), das
    #     Kalibrier-Set das gefrorene kalibrier_leg.points (13); beide
    #     sind REGISTRIERT, also kein neuer Gate-Zweig. ---
    verdict_set_raw = {(e["arm"], e["P"]) for e in raw["counts"]
                       if e["kind"] == "structure"}
    point_set_raw = verdict_set_raw
    point_set_frozen = {(arm, p["P"]) for arm in h3a.ARMS
                        for p in prereg["prediction_freeze"]["points"][arm]}
    cal_set_raw = {(e["arm"], e["P"]) for e in raw["counts"]
                   if e["kind"] == "kalibrier_structure"}
    cal_set_frozen = {(arm, p["P"]) for arm in h3a.ARMS
                      for p in prereg["kalibrier_bein"]["points"][arm]}
    point_set_ok = verdict_set_raw == point_set_frozen
    cal_set_ok = cal_set_raw == cal_set_frozen
    name_set_ok = (set(cs_by_name) == set(raw_by_name))
    transpile_ok = (
        raw["transpile"] == {
            "optimization_level": isa["optimization_level"],
            "seed_transpiler": isa["transpile_seed"],
            "isa_2q_total": isa["total_two_q"],
            "isa_2q_max": isa["max_two_q"],
        }
        and isa["verdict"] == "ISA_OK")
    run_config_ok = (raw["registered_run_config"]
                     == prereg["hardware_parameters"]["run_config"])
    t5_ok = (point_set_ok and cal_set_ok
             and name_set_ok and transpile_ok and run_config_ok
             and raw["n_circuits"] == 116 and len(raw["counts"]) == 116)

    t_fail_other = not (md5_ok and bp_md5_ok and t3_ok and t5_ok and t6_ok)

    # --- p_ro pro Arm (cal_{nq}q, EIN Job) ---
    p_ro_by_nq = {}
    for arm in h3a.ARMS:
        nq = h3a.NQ_BY_ARM[arm]
        cal = raw_by_name.get(f"cal_{nq}q")
        p_ro_by_nq[nq] = (aer.p0_fraction(cal["counts"], nq)
                          if cal else 0.0)

    # --- Punkte (26 = 13 Holdout + 13 Kalibrier): 3 Reps -> ratio_hw;
    #     kappa_hat = P_L/P_ro_ref aus gepooltem Loschmidt + Readout-Kal. ---
    points = {}
    for arm in h3a.ARMS:
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
            in_fit = pt["set"] == "cal"
            rec = {
                "P": P, "nq": nq, "m": pt["m"], "set": pt["set"],
                "ratio_hw": ratio, "ratio_reps": ratios,
                "ratio_std": (float(np.std(ratios)) if ratios else None),
                "missing_reps": missing,
                "P_L": p_l, "P_ro_ref": p_ro, "kappa_hat": kappa,
                "kappa_ok": kappa is not None and kappa >= h3.KAPPA_CEILING,
                "b_p_aer": bp, "c_p": c_p, "in_gamma_fit": in_fit,
            }
            if kappa is not None and bp is not None and ro_hat is not None:
                rec["ratio_ro_exact"] = aer.ratio_ro_exact(pt, ro_hat, nq)
                rec["delta_cal"] = (rec["ratio_ro_exact"] + bp * (kappa - 1.0)
                                    - ratio) if ratio is not None else None
            else:
                rec["ratio_ro_exact"] = None
                rec["delta_cal"] = None
            points[pkey] = rec

    # --- in-job gamma_arm-Fit: NUR die 13 Kalibrier-P (LSQ-durch-Null);
    #     die 13 Holdout-P gehen in KEINEN Fit. ---
    gamma_arm = {}
    for arm in h3a.ARMS:
        rows = []
        for key in sorted(k for k in points if k.startswith(f"cal|{arm}|")):
            v = points[key]
            if v["delta_cal"] is not None:
                rows.append({"c_p": v["c_p"], "delta_cal": v["delta_cal"]})
        g = fit_gamma_arm(rows) if rows else None
        gamma_arm[arm] = {"gamma": g, "n_cal": len(rows), "rows": rows}

    # --- center_v3 + Band-/Deckel-Flags; Deckel = registrierte
    #     (1-1/S)*ratio_true + L_q-Kante mit scharfer w_B''-Verdict-Kante
    #     (10d-Praezedenz), w_A-Lesart dokumentiert. ---
    for pkey, v in points.items():
        arm = pkey.split("|")[1]
        nq = v["nq"]
        kappa, ratio = v["kappa_hat"], v["ratio_hw"]
        g = gamma_arm[arm]["gamma"] if gamma_arm[arm]["gamma"] is not None else 0.0
        c3 = None
        if kappa is not None and v["b_p_aer"] is not None and ratio is not None:
            ro_hat = 1.0 - v["P_ro_ref"] ** (1.0 / nq)
            c3 = center_v3(kappa, pts[(arm, v["P"])], ro_hat,
                           v["b_p_aer"], g, v["c_p"], nq)
            res = ratio - c3
            v["gamma_used"] = g
            v["center_v3"] = c3
            v["res_v3"] = res = ratio - c3
            v["in_band_sharp"] = abs(res) <= w_b
            v["in_band_coarse"] = abs(res) <= w_a
            v["below_sharp"] = ratio < c3 - w_b
            v["below_coarse"] = ratio < c3 - w_a
            v["ceiling"] = (1.0 - 1.0 / h3.SHOTS) \
                * pts[(arm, v["P"])]["ratio_true"] + pts[(arm, v["P"])]["L_q"]
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
        "gamma_arm": {arm: gamma_arm[arm]["gamma"] for arm in h3a.ARMS},
        "n_cal_per_arm": {arm: gamma_arm[arm]["n_cal"] for arm in h3a.ARMS},
    }
    verdict = decide_verdict(
        t4_violated=not t4_ok, t_fail_other=t_fail_other,
        n_kappa_low_union=n_kappa_low, n_above_ceiling=n_above_ceiling,
        n_below_sharp=n_below_sharp, n_in_sharp=n_in_sharp,
        all_in_coarse=all_in_coarse,
        n_holdout=verdict_inputs["n_holdout"])

    # --- alternative Lesarten (dokumentiert, nicht verdict-ersetzend) ---
    alt = {
        "refuted_mit_w_a": {
            "n_below_coarse_w_a": sum(1 for v in holdout_vals
                                      if v["below_coarse"]),
            "verdict_waere": V_REFUTED
            if sum(1 for v in holdout_vals if v["below_coarse"]) >= 2 else None,
        },
        "amplification_mit_w_a": {
            "n_above_ceiling_w_a": sum(1 for v in holdout_vals
                                       if v["above_ceiling_w_a"]),
        },
        "exklusion": None,
    }
    if (verdict not in (V_DEGENERAT, V_INVALID, V_VOID)
            and n_kappa_low == 1 and len(vals) == len(points)):
        # kappa_floor_void-Lesart: der eine Punkt ist EXKLUDIERT; Band-Verdict
        # ueber die 25 verbleibenden Punkte (alle mit kappa >= 0.81).
        inc = [v for v in vals if v["kappa_ok"]]
        inc_holdout = [v for k, v in points.items()
                       if k.startswith("verdict|") and v in inc]
        alt["exklusion"] = {
            "n_points": len(inc),
            "verdict_waere": decide_verdict(
                t4_violated=False, t_fail_other=False, n_kappa_low_union=0,
                n_above_ceiling=sum(1 for v in inc_holdout
                                    if v["above_ceiling_w_b"]),
                n_below_sharp=sum(1 for v in inc_holdout
                                  if v["below_sharp"]),
                n_in_sharp=sum(1 for v in inc_holdout if v["in_band_sharp"]),
                all_in_coarse=all(v["in_band_coarse"] for v in inc_holdout),
                n_holdout=len(inc_holdout)),
        }

    # --- Echo-Leiter (Diagnostik, NICHT verdict-tragend): kappa_r an den
    #     NEUEN Ankern (181/467); r=1 geteilt mit dem gepoolten Loschmidt —
    #     die Konsistenz kappa_ladder(r=1) == kappa_hat(Anker) folgt per
    #     Konstruktion (identische Counts) und wird mechanisch geprueft. ---
    ladder = {}
    for arm in h3a.ARMS:
        nq = h3a.NQ_BY_ARM[arm]
        p_ro = p_ro_by_nq[nq]
        P = h3a.ladder_anchor(arm)
        kappas, r1_consistent = {}, None
        for r in h3.LADDER_REPEATS:
            name = (f"loschmidt_{arm}_{P}" if r == 1
                    else f"ladder_{arm}_{P}_r{r}")
            e = raw_by_name.get(name)
            if e is None or p_ro <= 0:
                kappas[f"r{r}"] = None
                continue
            kappas[f"r{r}"] = aer.p0_fraction(e["counts"], nq) / p_ro
            if r == 1:
                r1_consistent = (kappas[f"r{r}"]
                                 == points[f"verdict|{arm}|{P}"]["kappa_hat"])
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

    vmap = prereg["verdict_map"]
    doc = {
        "experiment": h3.EXPERIMENT,
        "hypothesis": h3.HYPOTHESIS,
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
        },
        "w_b_doubleprime": w_b, "w_a": w_a,
        "w_b_source": {"path": e2.STAGE2_PATH,
                       "registered": "Freeze B'' (WIEDERVERWENDET, "
                                     "w_B'' == w_B', Phase-10b-Konvention "
                                     "q97.5 des sampled-Beins)"},
        "kappa_ceiling": h3.KAPPA_CEILING,
        "gamma_arm": gamma_arm,
        "kontrollen": {
            "t1_backcompat": "inherited (committetes Offline-Suite-Bein: "
                             "tests/test_pt_ram_q_hardware3.py)",
            "t2_v2_anchors": "inherited (committetes Offline-Suite-Bein: "
                             "tests/test_pt_ram_q_hardware3.py)",
            "t3_identity_two_ways": {"ok": t3_ok, "max_dev": t3_dev,
                                     "tol": e2.T3_TOL,
                                     "kinds": ["structure", "negative_control",
                                               "kalibrier_structure"]},
            "t4_negative_must_not_fire": {"ok": t4_ok, "controls": controls,
                                          "edge_convention": "registrierte "
                                          "Freeze-A''-Kante (kappa = 0.81-Ecke, "
                                          "konservativ fuer must-not-fire)"},
            "t5_gate_set_frozen": {"ok": t5_ok,
                                   "point_set_ok": point_set_ok,
                                   "cal_set_ok": cal_set_ok,
                                   "name_set_ok": name_set_ok,
                                   "transpile_ok": transpile_ok,
                                   "run_config_ok": run_config_ok},
            "t6_mass_conservation": {"ok": t6_ok, "shots_ok": t6_shots_ok,
                                     "max_mass_dev": t6_mass_dev},
        },
        "punkte": points,
        "verdict_inputs": verdict_inputs,
        "verdict": verdict,
        "verdict_map_text": vmap.get(verdict,
                                     "kein Treffer der gefrorenen Map — "
                                     "ehrlicher Nicht-Treffer-Zweig (kein "
                                     "erfundener Verdict)"),
        "alternative_lesarten": alt,
        "echo_ladder": ladder,
    }
    return doc


def write_eval(doc, path=EVAL_PATH):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    return path


if __name__ == "__main__":
    doc = evaluate()
    write_eval(doc)
    print(f"verdict: {doc['verdict']}")
    vi = doc["verdict_inputs"]
    print(f"kappa_low(union): {vi['n_kappa_low_union']}/{vi['n_points']} "
          f"below_sharp: {vi['n_below_sharp']} "
          f"in_sharp: {vi['n_in_sharp']}/13 "
          f"above_ceiling: {vi['n_above_ceiling_sharp']}")
    for arm in h3a.ARMS:
        print(f"gamma_arm[{arm}]: {doc['gamma_arm'][arm]['gamma']} "
              f"(n_cal {doc['gamma_arm'][arm]['n_cal']})")