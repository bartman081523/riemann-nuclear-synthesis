# -*- coding: utf-8 -*-
"""H-RAM-Q-3b Hardware-Auswertung (EXPERIMENT 043): gefrorene verdict_map.

Liest AUSSCHLIESSLICH das committete Raw-Dokument
(pt_ram_q_hardware2_raw.json; Raw-Commit 38a975b VOR dieser Auswertung —
job_integrity: "Job-ID + md5 der Counts committed VOR der Auswertung"), das
committete Stage-2b-Resultat (w_B' = 0.02787029633307472, Freeze B'), den
ISA2-Report (493 2q, ISA_OK) und das gefrorene Prereg (md5 0b9c9968).
KEIN QPU-Kontakt, KEINE neuen Register: die Auswertung wendet nur die
gefrorene Estimator-Kette (operational_definitions, UNVERAENDERT aus
Experiment 042) auf die committeden Counts an — identisch zum Aer-Sampled-
Bein (pt_ram_q_hardware2_aer).

Estimator-Kette (UNVERAENDERT, Zentrum gefroren):
  n_hat_a = m*c_a/S (rational) -> fold_d (Wraparound) -> ABSOLUT-FFT-Share
  ratio_hw = share/model_share_reg; Punkt-Wert = Mittel ueber die 3 Reps
  kappa_hat = P_L/P_ro_ref (gepaarte Loschmidt-/Readout-Cal-Counts, EIN Job)
  Zentrum c(kappa_hat) = kappa_hat*(1-1/S)*ratio_true + L_q
  Band: w_B' aus pt_ram_q_stage2b_results.json (Freeze B'), grob w_A = 0.05.

Verdikt-Praezedenz (die Map selbst gibt keine Reihenfolge an; dokumentiert
in §Z.25, identisch zur Phase-9-Praezedenz §Z.24): T4 verletzt -> DEGENERAT;
sonstige Kontrollen (T3/T5/T6, md5) gescheitert -> EVALUATION_INVALID;
>= 2 Punkte kappa_hat < 0.81 -> VOID_CALIBRATION; Punkt ueber Ceiling
c(1)+w -> INVALID_AMPLIFICATION; >= 2 unter c-w -> REFUTED; alle 13 im
scharfen Band + alle kappa >= 0.81 -> NOISE_LIFT_CONFIRMED; alle im groben
Band, >= 1 ausserhalb w_B' -> COARSE_HOLD_SHARP_MISS; sonst
VERDICT_MAP_UNMATCHED (ehrlicher Nicht-Treffer-Zweig — KEIN erfundener
Verdict, die Map kennt keinen).

T1/T2 sind Offline-Kontrollen und laufen im committeten Test-Suite-Bein
(tests/test_pt_ram_q_hardware2.py); dieses Modul dokumentiert die Vererbung,
statt sie zu behaupten.

Diagnostik-Beine (NICHT verdict-tragend, Freeze-A'-Regel):
  echo_ladder: kappa_r (r in {1,2,4,8}) an den Ankern 149 (q3) / 433 (q5).
    r=1 ist PER KONSTRUKTION der gepaarte Loschmidt-Circuit (echo_ladder.
    r1_shared) — dieselben Counts wie kappa_hat(Anker); die Auswertung
    prueft diese Konsistenz und passt den geometrischen Fit
    kappa_r = kappa_block^r (log-LSQ, gemessenes Daempfungsgesetz statt
    starrer (1-eps)^2-Annahme) ueber ALLE 4 Stufen.
  d_invarianz_bein: die 13 alten P am Minimalregister (d = q, NEU gemessen)
    gegen die committeden Run-1-Werte (Experiment 042, d = q^k) — Regel
    |res_v1_run2 - res_v1_run1| <= W_CROSS = 0.09 (Eichung aus dem
    committeden Run-1-Eval: 2*sqrt(2)*std).  res_v1-Zentrum UNVERAENDERT.
    Ein Bruch hier ist ein Re-Freeze-Trigger-Analyse-Eingang, NIEMALS ein
    Verdict-Ersatz.

Bekannte Spannung der gefrorenen Texte (in §Z.24 dokumentiert, hier
geerbt, NICHT aufgeloest): kappa_floor_void sagt "Punkt EXKLUDIERT"
(einzeln), waehrend die verdict_map fuer CONFIRMED/REFUTED ueber
"alle 13" / ">= 2 der 13" zaehlt.  Primaer gilt die woertliche verdict_map
(Anti-Sharpshooter: keine Interpretations-Latte zur Laufzeit); die
Exklusions-Lesart wird als alternative_lesart_exklusion mitgerechnet und
bei Divergenz ausgewiesen.
"""
import json

import numpy as np

import pt_ram_q_hardware as hw
import pt_ram_q_hardware2 as hw2
import pt_ram_q_hardware2_aer as s2b
import pt_ram_q_hardware2_qpu as qpu2

RAW_PATH = qpu2.RAW_PATH
STAGE2_PATH = s2b.RESULTS_PATH
ISA_PATH = "pt_ram_q_isa2_report.json"  # == pt_ram_q_isa2.ISA_PATH2 (Freeze B')
EVAL_PATH = "pt_ram_q_hardware2_eval.json"
RUN1_EVAL_PATH = "pt_ram_q_hardware_eval.json"  # Experiment 042 (d = q^k)

# Diagnostik-Bein: dieselben 13 alten P — Arm-Label run1 (d = q^k) vs run2
# (Minimalregister d = q).  Die P-Werte selbst sind identisch (gefroren).
RUN1_ARM = {"q3_d3": "q3_d9", "q5_d5": "q5_d25"}

T3_TOL = 1e-12
T6_MASS_TOL = 1e-9

V_CONFIRMED = "H-RAM-Q-3b_NOISE_LIFT_CONFIRMED"
V_COARSE = "H-RAM-Q-3b_COARSE_HOLD_SHARP_MISS"
V_REFUTED = "H-RAM-Q-3b_REFUTED"
V_AMPL = "H-RAM-Q-3b_INVALID_AMPLIFICATION"
V_VOID = "H-RAM-Q-3b_VOID_CALIBRATION"
V_DEGENERAT = "H-RAM-Q-3b_DEGENERAT"
V_INVALID = "EVALUATION_INVALID_KONTROLLE_GESCHEITERT"
V_UNMATCHED = "VERDICT_MAP_UNMATCHED"

D_INV_OK = "HARDWARE-D_INVARIANZ_KONSISTENT"
D_INV_BAD = "HARDWARE-D_INVARIANZ_VERLETZT"


def load_w_b(stage2_path=STAGE2_PATH):
    """w_B' aus dem committeten Freeze-B'-Stage-2b-Resultat (keine Konstante)."""
    with open(stage2_path, encoding="utf-8") as fh:
        return float(json.load(fh)["w_b"])


def decide_verdict(*, t4_violated, t_fail_other, n_kappa_low, n_above_ceiling,
                   n_below_sharp, n_in_sharp, all_in_coarse, n_points):
    """Gefrorene verdict_map mit dokumentierter Praezedenz (§Z.25)."""
    if t4_violated:
        return V_DEGENERAT
    if t_fail_other:
        return V_INVALID
    if n_kappa_low >= 2:
        return V_VOID
    if n_above_ceiling >= 1:
        return V_AMPL
    if n_below_sharp >= 2:
        return V_REFUTED
    if n_in_sharp == n_points and n_kappa_low == 0:
        return V_CONFIRMED
    if all_in_coarse and (n_points - n_in_sharp) >= 1:
        return V_COARSE
    return V_UNMATCHED


def _folded_share(n_hat, pt):
    """Zweiter Weg der t3-Identitaet (041-Theorem); bei d = q ist der Fold
    die Identitaet (Shuffle-Inertness-Theorem) — der Check laeuft trotzdem
    mechanisch ueber beide Wege."""
    N = hw.fold_mod_q(list(n_hat), pt["d"], pt["q"])
    return s2b.share_hw_folded(N, pt["q"], pt["d"], pt["m"])


def evaluate(raw_path=RAW_PATH, stage2_path=STAGE2_PATH, isa_path=ISA_PATH,
             run1_eval_path=RUN1_EVAL_PATH):
    raw = json.load(open(raw_path, encoding="utf-8"))
    with open(stage2_path, encoding="utf-8") as fh:
        stage2 = json.load(fh)
    with open(isa_path, encoding="utf-8") as fh:
        isa = json.load(fh)
    with open(run1_eval_path, encoding="utf-8") as fh:
        run1 = json.load(fh)
    prereg = hw2.load_frozen_prereg()
    w_b = load_w_b(stage2_path)
    w_a = s2b.W_A
    pts = s2b._point_pts()
    dg = s2b._diagnostik_pts()
    cs_by_name = {c["name"]: c for c in s2b.build_hardware_circuit_set()}
    raw_by_name = {e["name"]: e for e in raw["counts"]}

    # --- job_integrity: md5 der committeden Counts ---
    md5_ok = (qpu2.counts_md5([e["counts"] for e in raw["counts"]])
              == raw["counts_md5"])

    # --- t3 (zwei Wege) + t6 (Shots/Masse) ueber die VERDICT-State-Circuits
    #     (structure + negative_control).  Die Diagnostik-Circuits
    #     (diagnostik_structure) NICHT hier: das Bein ist NICHT verdict-
    #     tragend, daher darf sein Zustand den Verdict nicht beruehren —
    #     es wird separat im d_invarianz_bein-Block geprueft (t3d/t6d). ---
    t3_dev = 0.0
    t6_shots_ok = True
    t6_mass_dev = 0.0
    for e in raw["counts"]:
        if e["shots_actual"] != hw.SHOTS:
            t6_shots_ok = False
        if e["kind"] not in ("structure", "negative_control"):
            continue
        pt = pts[(e["arm"], e["P"])]
        rc = s2b.ratio_from_counts(e["counts"], pt, s2b.NQ_BY_ARM[e["arm"]])
        t3_dev = max(t3_dev, abs(rc["share"] - _folded_share(rc["n_hat"], pt)))
        t6_mass_dev = max(t6_mass_dev, abs(rc["m_hat"] - pt["m"]))
    t3_ok = t3_dev <= T3_TOL
    t6_ok = t6_shots_ok and t6_mass_dev <= T6_MASS_TOL

    # --- t4: Negativ-Kontrollen gegen die registrierte Kante (kappa = 0.81-
    #     Ecke, konservativ fuer must-not-fire); Exact-kappa-Variante als
    #     Diagnostik ---
    controls = {}
    t4_ok = True
    for name, c in cs_by_name.items():
        if c["kind"] != "negative_control":
            continue
        e = raw_by_name[name]
        pt_ref = pts[(c["arm"], c["P"])]
        nq = s2b.NQ_BY_ARM[c["arm"]]
        share = s2b.ratio_from_counts(e["counts"], pt_ref, nq)["share"]
        edge = c["lower_prime_band_edge"]
        ok = share < edge
        t4_ok = t4_ok and ok
        controls[name] = {
            "measured_share": share,
            "expected_share": c["expected_share"],
            "lower_prime_band_edge": edge,
            "ok": ok,
        }

    # --- t5: Gate-Set gefroren (Namen, Punkt-Set) + Transpile-Record ==
    #     ISA2-Report (Freeze B') ---
    point_set_raw = {(e["arm"], e["P"]) for e in raw["counts"]
                     if e["kind"] == "structure"}
    point_set_frozen = {(arm, p["P"]) for arm in s2b.ARMS
                        for p in prereg["prediction_freeze"]["points"][arm]}
    name_set_ok = (set(cs_by_name) == set(raw_by_name))
    transpile_ok = (
        raw["transpile"]["optimization_level"] == isa["optimization_level"]
        and raw["transpile"]["seed_transpiler"] == isa["transpile_seed"]
        and raw["transpile"]["isa_2q_total"] == isa["total_two_q"]
        and raw["transpile"]["isa_2q_max"] == isa["max_two_q"]
        and isa["verdict"] == "ISA_OK")
    run_config_ok = (raw["registered_run_config"]
                     == prereg["hardware_parameters"]["run_config"])
    t5_ok = (point_set_raw == point_set_frozen and name_set_ok
             and transpile_ok and run_config_ok
             and raw["n_circuits"] == 90 and len(raw["counts"]) == 90)

    t_fail_other = not (md5_ok and t3_ok and t5_ok and t6_ok)

    # --- p_ro pro Arm (cal_{nq}q, EIN Job) ---
    p_ro_by_nq = {}
    for arm in s2b.ARMS:
        nq = s2b.NQ_BY_ARM[arm]
        cal = raw_by_name.get(f"cal_{nq}q")
        p_ro_by_nq[nq] = (s2b.p0_fraction(cal["counts"], nq)
                          if cal else 0.0)

    # --- Punkte: 3 Reps -> ratio_hw; kappa_hat = P_L/P_ro_ref ---
    points = {}
    for arm in s2b.ARMS:
        nq = s2b.NQ_BY_ARM[arm]
        p_ro = p_ro_by_nq[nq]
        for key in sorted(k for k in pts if k[0] == arm):
            pt = pts[key]
            P = pt["P"]
            ratios, missing = [], []
            for r in range(hw.K_REPEATS):
                e = raw_by_name.get(f"struct_{arm}_{P}_r{r}")
                if e is None:
                    missing.append(r)
                    continue
                ratios.append(s2b.ratio_from_counts(
                    e["counts"], pt, nq)["ratio"])
            ratio = float(np.mean(ratios)) if ratios else None
            los = raw_by_name.get(f"loschmidt_{arm}_{P}")
            p_l = s2b.p0_fraction(los["counts"], nq) if los else 0.0
            kappa = p_l / p_ro if p_ro > 0 else None
            c1 = s2b.center_v1(kappa, pt) if kappa is not None else None
            c1max = s2b.center_v1(1.0, pt)
            res = ratio - c1 if (ratio is not None and c1 is not None) else None
            kappa_ok = kappa is not None and kappa >= s2b.KAPPA_CEILING
            rec = {
                "P": P, "nq": nq, "m": pt["m"],
                "ratio_hw": ratio, "ratio_reps": ratios,
                "ratio_std": (float(np.std(ratios)) if ratios else None),
                "missing_reps": missing,
                "P_L": p_l, "P_ro_ref": p_ro, "kappa_hat": kappa,
                "center_v1": c1, "res_sharp": res,
                "in_band_sharp": (abs(res) <= w_b) if res is not None else None,
                "in_band_coarse": (abs(res) <= w_a) if res is not None else None,
                "below_sharp": (ratio < c1 - w_b)
                if (ratio is not None and c1 is not None) else None,
                "below_coarse": (ratio < c1 - w_a)
                if (ratio is not None and c1 is not None) else None,
                "above_sharp": (ratio > c1 + w_b)
                if (ratio is not None and c1 is not None) else None,
                "ceiling_c1max": c1max,
                "above_ceiling_w_b": (ratio > c1max + w_b)
                if ratio is not None else None,
                "above_ceiling_w_a": (ratio > c1max + w_a)
                if ratio is not None else None,
                "kappa_ok": kappa_ok,
            }
            # Diagnostik (NICHT verdict-tragend): gesetzliche v2-Form mit den
            # committeten Aer-b_P (Stage-2b, Freeze B') und gemessenem ro_hat.
            bp = stage2["b_p"].get(f"{arm}|{P}")
            ro_hat = 1.0 - p_ro ** (1.0 / nq) if p_ro > 0 else None
            c2 = (s2b.center_v2(kappa, pt, ro_hat, bp)
                  if (kappa is not None and bp is not None) else None)
            rec["diagnostisch_v2"] = {
                "nicht_verdict_tragend": True, "b_p_aer": bp,
                "ro_hat": ro_hat, "center_v2": c2,
                "res_v2": (ratio - c2)
                if (ratio is not None and c2 is not None) else None,
            }
            points[f"{arm}|{P}"] = rec

    vals = [v for v in points.values() if v["ratio_hw"] is not None]
    n_kappa_low = sum(1 for v in vals if not v["kappa_ok"])
    n_below_sharp = sum(1 for v in vals if v["below_sharp"])
    n_above_ceiling = sum(1 for v in vals if v["above_ceiling_w_b"])
    n_in_sharp = sum(1 for v in vals if v["in_band_sharp"])
    all_in_coarse = (len(vals) == len(points)
                     and all(v["in_band_coarse"] for v in vals))
    verdict_inputs = {
        "n_points": len(points), "n_evaluated": len(vals),
        "n_kappa_low": n_kappa_low, "n_below_sharp": n_below_sharp,
        "n_above_ceiling_w_b": n_above_ceiling, "n_in_sharp": n_in_sharp,
        "n_outside_sharp": len(vals) - n_in_sharp,
        "all_in_coarse_w_a": all_in_coarse,
        "n_below_coarse_w_a": sum(1 for v in vals if v["below_coarse"]),
    }
    verdict = decide_verdict(
        t4_violated=not t4_ok, t_fail_other=t_fail_other,
        n_kappa_low=n_kappa_low, n_above_ceiling=n_above_ceiling,
        n_below_sharp=n_below_sharp, n_in_sharp=n_in_sharp,
        all_in_coarse=all_in_coarse, n_points=len(points))

    # --- alternative Lesarten (dokumentiert, nicht verdict-ersetzend) ---
    alt = {
        "refuted_mit_w_a": {
            "n_below_coarse_w_a": verdict_inputs["n_below_coarse_w_a"],
            "verdict_waere": V_REFUTED
            if verdict_inputs["n_below_coarse_w_a"] >= 2 else None,
        },
        "amplification_mit_w_a": {
            "n_above_ceiling_w_a": sum(1 for v in vals
                                       if v["above_ceiling_w_a"]),
        },
        "exklusion": None,
    }
    if (verdict not in (V_DEGENERAT, V_INVALID, V_VOID)
            and n_kappa_low == 1 and len(vals) == len(points)):
        # kappa_floor_void-Lesart: der eine Punkt ist EXKLUDIERT; Band-Verdict
        # ueber die 12 verbleibenden Punkte (alle mit kappa >= 0.81).
        inc = [v for v in vals if v["kappa_ok"]]
        alt["exklusion"] = {
            "n_points": len(inc),
            "verdict_waere": decide_verdict(
                t4_violated=False, t_fail_other=False, n_kappa_low=0,
                n_above_ceiling=sum(1 for v in inc if v["above_ceiling_w_b"]),
                n_below_sharp=sum(1 for v in inc if v["below_sharp"]),
                n_in_sharp=sum(1 for v in inc if v["in_band_sharp"]),
                all_in_coarse=all(v["in_band_coarse"] for v in inc),
                n_points=len(inc)),
        }

    # --- Echo-Leiter (Diagnostik, NICHT verdict-tragend): kappa_r an den
    #     Ankern; r=1 geteilt mit dem gepaarten Loschmidt — die Konsistenz
    #     kappa_ladder(r=1) == kappa_hat(Anker) folgt per Konstruktion
    #     (identische Counts) und wird mechanisch geprueft. ---
    ladder = {}
    for arm in s2b.ARMS:
        nq = s2b.NQ_BY_ARM[arm]
        p_ro = p_ro_by_nq[nq]
        P = s2b.ladder_anchor(arm)
        kappas, r1_konsistent = {}, None
        for r in hw2.LADDER_REPEATS:
            name = (f"loschmidt_{arm}_{P}" if r == 1
                    else f"ladder_{arm}_{P}_r{r}")
            e = raw_by_name.get(name)
            if e is None or p_ro <= 0:
                kappas[f"r{r}"] = None
                continue
            kappas[f"r{r}"] = s2b.p0_fraction(e["counts"], nq) / p_ro
            if r == 1:
                r1_konsistent = (kappas[f"r{r}"]
                                 == points[f"{arm}|{P}"]["kappa_hat"])
        fit = None
        if all(kappas[f"r{r}"] is not None for r in hw2.LADDER_REPEATS):
            fit = s2b.fit_echo_ladder(
                [kappas[f"r{r}"] for r in hw2.LADDER_REPEATS],
                list(hw2.LADDER_REPEATS))
        ladder[arm] = {
            "P": P, "repeats": list(hw2.LADDER_REPEATS),
            "r1_shared_with_loschmidt": True,
            "kappa_r": kappas,
            "r1_konsistent_mit_kappa_hat_anker": r1_konsistent,
            "fit_kappa_block": (fit["kappa_block"] if fit else None),
            "fit_max_res_log": (fit["max_res_log"] if fit else None),
            "verdict_role": "NICHT verdict-tragend (Diagnostik)",
        }

    # --- d-Invarianz-Bein (Diagnostik, NICHT verdict-tragend): die 13 alten
    #     P am Minimalregister (d = q) gegen Run 1 (d = q^k, committet) ---
    d_inv_punkte = {}
    for arm in s2b.ARMS:
        nq = s2b.NQ_BY_ARM[arm]
        p_ro = p_ro_by_nq[nq]
        for key in sorted(k for k in dg if k[0] == arm):
            pt = dg[key]
            P = pt["P"]
            e_s = raw_by_name.get(f"diag_struct_{arm}_{P}")
            e_l = raw_by_name.get(f"diag_loschmidt_{arm}_{P}")
            rec1 = run1["punkte"].get(f"{RUN1_ARM[arm]}|{P}")
            if e_s is None or e_l is None or rec1 is None or p_ro <= 0:
                d_inv_punkte[f"{arm}|{P}"] = {"ok": None}
                continue
            # t3d/t6d: Masse-/Identitaets-Integritaet DES Beins (kein
            # Verdict-Eingang — der Bein-Status darf den Verdict nie
            # beruehren).
            rc = s2b.ratio_from_counts(e_s["counts"], pt, nq)
            t3d_dev = abs(rc["share"] - _folded_share(rc["n_hat"], pt))
            t6d_dev = abs(rc["m_hat"] - pt["m"])
            ratio = rc["ratio"]
            p_l = s2b.p0_fraction(e_l["counts"], nq)
            kappa = p_l / p_ro if p_ro > 0 else None
            c1 = s2b.center_v1(kappa, pt) if kappa is not None else None
            res2 = (ratio - c1
                    if (ratio is not None and c1 is not None) else None)
            res1 = rec1.get("res_sharp")
            delta = (res2 - res1
                     if (res2 is not None and res1 is not None) else None)
            ok = (abs(delta) <= hw2.W_CROSS) if delta is not None else None
            d_inv_punkte[f"{arm}|{P}"] = {
                "P": P, "d_run2": pt["d"],
                "ratio_run2": ratio, "kappa_run2": kappa, "center_v1": c1,
                "res_v1_run2": res2, "res_v1_run1": res1, "delta": delta,
                "abs_delta": (abs(delta) if delta is not None else None),
                "ok": ok, "t3d_dev": t3d_dev, "t6d_dev": t6d_dev,
            }
    deltas = [p["delta"] for p in d_inv_punkte.values() if p["delta"] is not None]
    d_invariantz = {
        "nicht_verdict_tragend": True,
        "verdict_role": "Re-Freeze-Trigger-Analyse nur",
        "rule": prereg["diagnostik_bein"]["rule"],
        "w_cross": hw2.W_CROSS,
        "w_cross_derivation": prereg["diagnostik_bein"]["w_cross_derivation"],
        "n_punkte": len(d_inv_punkte),
        "n_ok": sum(1 for p in d_inv_punkte.values() if p["ok"]),
        "max_abs_delta": (max(abs(d) for d in deltas) if deltas else None),
        "integritaet": {
            "t3d_max_dev": max((p["t3d_dev"] for p in d_inv_punkte.values()
                                if p.get("t3d_dev") is not None), default=None),
            "t6d_max_dev": max((p["t6d_dev"] for p in d_inv_punkte.values()
                                if p.get("t6d_dev") is not None), default=None),
        },
        "status": (D_INV_OK if deltas and len(deltas) == len(d_inv_punkte)
                   and all(abs(d) <= hw2.W_CROSS for d in deltas)
                   else D_INV_BAD),
        "punkte": d_inv_punkte,
    }

    vmap = prereg["verdict_map"]
    doc = {
        "experiment": hw2.EXPERIMENT,
        "hypothesis": hw2.HYPOTHESIS,
        "status": "EVALUATED",
        "raw_backend": raw.get("backend"),
        "raw_job_meta": raw.get("job_meta"),
        "raw_counts_md5": raw.get("counts_md5"),
        "counts_md5_verified": md5_ok,
        "w_b": w_b, "w_a": w_a,
        "w_b_source": {"path": stage2_path,
                       "registered": "Freeze B' (Domain-q97.5, unclipped "
                                     "Gate, w_B' == w_B'_geclippt)"},
        "kappa_ceiling": s2b.KAPPA_CEILING,
        "kontrollen": {
            "t1_backcompat": "inherited (committetes Offline-Suite-Bein: "
                             "tests/test_pt_ram_q_hardware2.py)",
            "t2_v2_anchors": "inherited (committetes Offline-Suite-Bein: "
                             "tests/test_pt_ram_q_hardware2.py)",
            "t3_identity_two_ways": {"ok": t3_ok, "max_dev": t3_dev,
                                     "tol": T3_TOL},
            "t4_negative_must_not_fire": {"ok": t4_ok, "controls": controls,
                                          "edge_konvention": "registrierte "
                                          "Freeze-A'-Kante (kappa = 0.81-Ecke, "
                                          "konservativ fuer must-not-fire)"},
            "t5_gate_set_frozen": {"ok": t5_ok,
                                   "point_set_ok":
                                       point_set_raw == point_set_frozen,
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
        "d_invarianz_bein": d_invariantz,
    }
    return doc


def write_eval(doc, path=EVAL_PATH):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    return path


if __name__ == "__main__":
    ev = evaluate()
    write_eval(ev)
    print(f"verdict: {ev['verdict']}")
    vi = ev["verdict_inputs"]
    print(f"inputs: {vi}")
    print(f"kontrollen: t3 {ev['kontrollen']['t3_identity_two_ways']['ok']}, "
          f"t4 {ev['kontrollen']['t4_negative_must_not_fire']['ok']}, "
          f"t5 {ev['kontrollen']['t5_gate_set_frozen']['ok']}, "
          f"t6 {ev['kontrollen']['t6_mass_conservation']['ok']}, "
          f"md5 {ev['counts_md5_verified']}")
    for k, v in ev["punkte"].items():
        print(f"{k}: ratio {v['ratio_hw']:.4f} kappa {v['kappa_hat']:.4f} "
              f"c {v['center_v1']:.4f} res {v['res_sharp']:+.4f} "
              f"sharp {v['in_band_sharp']}")
    for arm, l in ev["echo_ladder"].items():
        print(f"ladder {arm}: kappa_r {l['kappa_r']} "
              f"kappa_block {l['fit_kappa_block']:.4f} "
              f"max_res_log {l['fit_max_res_log']:.4f}")
    di = ev["d_invarianz_bein"]
    print(f"d-invarianz: {di['status']} (max |delta| "
          f"{di['max_abs_delta']:.4f} <= W_CROSS {di['w_cross']}, "
          f"{di['n_ok']}/{di['n_punkte']})")