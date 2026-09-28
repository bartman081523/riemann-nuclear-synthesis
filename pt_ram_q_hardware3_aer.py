# -*- coding: utf-8 -*-
"""Stage-3 Aer-Bein fuer H-RAM-Q-4 (EXPERIMENT 044, Phase 11c) — 0 QPU.

Freeze-A''-Prereg (md5 baaca1f6772e07b0847fe436da7e16da,
pt_ram_q_hardware3_prereg.json), two_freeze_architecture.stage3_aer:
  Spiegel des Phase-10b-Stage-2b-Beins (pt_ram_q_hardware2_aer.py) am
  amendierten Run-3-Punktesatz — 26 Punkte (13 Verdict-NEW + 13 Kalibrier)
  x 6 Stresslevel, exakt- und sampled-Bein.  Register Minimal d=q (h3.NQ3=2,
  h3.NQ5=3); Punkte aus dem gefrorenen Payload (prediction_freeze.points,
  kalibrier_bein.points), NICHT re-generiert.

  stress_model      : aer-Praezedenz (Phase-9/10, unveraendert): depolarizing
                      p1 auf 1q-Gates rz/sx/x, ratio*p1 auf cz, ReadoutError
                      ro = 1e-2 — NICHT kalibriert, konservativ.
  b_P               : fuer ALLE 26 Punkte (Phase-10b-Konvention) LSQ deg 1
                      ueber die Exakt-Kurve (6 Levels), gefroren VOR Hardware;
                      das ist das b_P des Verdict-Gesetzes center_v3 an den
                      13 Holdout-P.  Konsistenz: die 13 Kalibrier-b_P werden
                      gegen die committete Phase-11a-Diagnostik geprueft
                      (dieselben Punkte, dieselbe Codebahn) — mit Toleranz
                      1e-3, NICHT Bit-Identitaet: die density_matrix-Evolution
                      ist prozessuebergreifend nur bis ~1e-9 (kappa) bzw.
                      ~1e-5 (b_P nach LSQ-Fit) reproduzierbar (BLAS-Float-
                      Rauschen, Phase-10b-Kurve vs. Re-Lauf gemessen), und
                      b_P-Abweichungen von 1e-5 verschieben center_v3 um
                      b_P*(1-kappa) <= 6e-6 — vier Groessenordnungen unter
                      w_B''.  Die Pruefung ist die Grobe-Fehler-Sicherung
                      (falscher Punkt/Arm/Register gaebe O(1)-Abweichung).
  form_validation   : zweistufig (Phase-10b-Praezedenz, Payload
                      simulation_leg.form_validation).  Gate E (Zentrum):
                      max |res_v2| <= TOL_FORM = 0.03 ueber die Domain-Zellen
                      des EXACT-Beins — in der v2-FORM, NICHT v3, denn auf
                      Aer ist gamma_aer ~ 0 und v3 reduziert exakt auf v2.
                      Gate S (Rauschen): q97.5 der |res_v2| ueber die
                      Domain-Zellen des SAMPLED-Beins <= W_A = 0.05; der
                      per-Zell-Max des sampled-Beins ist registrierte
                      Diagnostik (Estimator-Rauschen), KEIN Gate.
  gamma_aer         : in-Aer-Fit auf den Kalibrier-Zellen (sampled, Domain,
                      per-Ensemble ro_hat — in-Zelle-Kalibrierung wie in-job):
                      gamma = <cP, delta_cal>/<cP, cP> mit delta_cal =
                      ratio_ro_exact + b_P*(kappa-1) - ratio.  ERWARTUNG ~ 0
                      (Aer-Rauschen ist stochastisch, keine kohärente
                      Prep-Komponente) — registrierte Diagnostik, KEIN Gate.
  w_B''             : WIEDERVERWENDET (w_B' = 0.02787029633307472 aus
                      pt_ram_q_stage2b_results.json, design_decision
                      w_b_doppelprime_wiederverwendet).  Das Stage-3-Bein
                      registriert das sampled-Domain-q97.5 als Diagnostik +
                      Gate-S-Konsistenz — es aendert w_B'' NICHT (kein
                      compute_w_b-Recompute; Freeze-B''-Praezedenz Phase 10).
  Echo-Leiter       : Exakt-Bein an den NEUEN Ankern (q3 -> 181, q5 -> 467)
                      ueber alle 6 Levels, geometrischer Fit — registrierte
                      Diagnostik zum Daempfungsgesetz (Fallback-B-Eingang),
                      NICHT verdict-tragend; die verdict-tragende Leiter
                      kommt aus dem Fez-Job.
  Circuits          : build_hardware_circuit_set() = ALLE 116 Circuits des
                      gefrorenen Budgets (39 Verdict-struct + 13 Verdict-
                      loschmidt + 6 Leiter + 39 Kalibrier-struct + 13
                      Kalibrier-loschmidt + 4 negative Kontrollen + 2
                      Readout-Kalibrierung) — EINE Quelle fuer ISA-3-Report
                      (pt_ram_q_isa3.py) und Fez-Job.  r=1 der Leiter ist
                      geteilt mit dem Anker-Loschmidt (echo_ladder.r1_shared).
"""
import json

import numpy as np

import pt_ram_q_hardware as hw
import pt_ram_q_hardware_aer as aer
import pt_ram_q_hardware2_aer as s2b
import pt_ram_q_hardware3 as h3

# --- Delegation: die d-generischen Funktionen (Phase-9/10) werden
# UNVERAENDERT wiederverwendet; Run-3 aendert nur Punktesatz/Zentrum. ---
stress_noise_model = aer.stress_noise_model
readout_apply = aer.readout_apply
share_hw_fft = aer.share_hw_fft
share_hw_folded = aer.share_hw_folded
fold_d = aer.fold_d
p0_fraction = aer.p0_fraction
ratio_from_counts = aer.ratio_from_counts
ratio_ro_exact = aer.ratio_ro_exact
alpha_from_kappa = aer.alpha_from_kappa
center_v1 = aer.center_v1
center_v2 = aer.center_v2
fit_b_p = aer.fit_b_p
stage2_seed = aer.stage2_seed
build_struct_circuit = aer.build_struct_circuit
build_loschmidt_circuit = aer.build_loschmidt_circuit
build_state_circuit = aer.build_state_circuit
build_cal_circuit = aer.build_cal_circuit
exact_point_level = aer.exact_point_level
sampled_point_level = aer.sampled_point_level
build_ladder_circuit = s2b.build_ladder_circuit
ladder_point_level = s2b.ladder_point_level
fit_echo_ladder = s2b.fit_echo_ladder
nq_of = aer.nq_of
lower_prime_band_edge = s2b.lower_prime_band_edge

RO_STRESS = aer.RO_STRESS
BASIS_GATES = aer.BASIS_GATES
TRANSPILE_SEED = aer.TRANSPILE_SEED
SIM_SEED_EXACT = aer.SIM_SEED_EXACT

SHOTS = h3.SHOTS
K_REPEATS = h3.K_REPEATS
W_A = h3.W_A
W_B_FLOOR = h3.W_B_FLOOR
TOL_FORM = h3.TOL_FORM
KAPPA_CEILING = h3.KAPPA_CEILING
STRESS_GRID_P1 = h3.STRESS_GRID_P1
N_ENS = h3.N_ENS
W_B_PRIME = h3.W_B_PRIME
# Grobe-Fehler-Toleranz der Kalibrier-b_P-Konsistenz (Modulkopf: BLAS-Float-
# Rauschen ~1e-5 prozessuebergreifend; 1e-3 = 2 Groessenordnungen darueber,
# falscher Punkt/Arm/Register gaebe O(1)-Abweichung).
BP_KONSISTENZ_TOL = 1e-3

ARMS = ("q3_d3", "q5_d5")
NQ_BY_ARM = {"q3_d3": h3.NQ3, "q5_d5": h3.NQ5}
RESULTS_PATH = "pt_ram_q_stage3_results.json"

SET_VERDICT = "verdict"
SET_CAL = "cal"


def pkey(key, pts):
    """Result-Key 'set|arm|P' — dieselbe Konvention wie die cP_freeze-Tabelle
    des Freeze-A''-Payloads ('verdict|q3_d3|181', 'cal|q3_d3|149')."""
    return f'{pts[key]["set"]}|{key[0]}|{key[1]}'


def _point_pts():
    """Die 13 VERDICT-Punkte (Run-3 NEW-P) aus dem gefrorenen Freeze-A''-
    Payload (prediction_freeze.points)."""
    doc = h3.load_frozen_prereg()
    pts = {}
    for arm in ARMS:
        for p in doc["prediction_freeze"]["points"][arm]:
            p = dict(p)
            p["arm"] = arm
            p["set"] = SET_VERDICT
            pts[(arm, p["P"])] = p
    return pts


def _cal_pts():
    """Die 13 KALIBRIER-Punkte (Run-2-Verdict-P) aus dem gefrorenen Payload
    (kalibrier_bein.points)."""
    doc = h3.load_frozen_prereg()
    pts = {}
    for arm in ARMS:
        for p in doc["kalibrier_bein"]["points"][arm]:
            p = dict(p)
            p["arm"] = arm
            p["set"] = SET_CAL
            pts[(arm, p["P"])] = p
    return pts


def all_points():
    """26 Punkte: 13 Verdict + 13 Kalibrier — Sets sind je Arm disjunkt
    (amendierte P-Regel, test_no_new_point_ever_measured)."""
    pts = dict(_point_pts())
    cal = _cal_pts()
    overlap = set(pts) & set(cal)
    if overlap:
        raise ValueError(f"Verdict/Kalibrier-Overlap: {sorted(overlap)}")
    pts.update(cal)
    return pts


def cP_of(pt):
    """Gefrorene kohärente Empfindlichkeit aus dem Freeze-A''-Payload
    (cP_freeze, Keys 'verdict|arm|P' bzw. 'cal|arm|P')."""
    doc = h3.load_frozen_prereg()
    return doc["prediction_freeze"]["cP_freeze"][
        f'{pt["set"]}|{pt["arm"]}|{pt["P"]}']


def ladder_anchor(arm):
    """Anker-P des Arms (echo_ladder.anchors: q3 -> 181, q5 -> 467)."""
    return h3.LADDER_ANCHORS[arm.split("_")[0]]


def gamma_aer_fit(cells, pts, cp_table):
    """In-Aer gamma-Fit auf den KALIBRIER-Zellen (sampled, Domain): delta_cal
    per Ensemble mit per-Ensemble-ro_hat (in-Zelle-Kalibrierung, B4-
    Praezedenz), gamma = <cP, delta_cal>/<cP, cP> (h3.gamma_lsq, LSQ durch
    Null).  ERWARTUNG ~ 0: das Aer-Rauschen ist stochastisch (depolarizing +
    Readout), das v2-Gesetz mit Aer-b_P absorbiert es komplett — eine
    kohärente Prep-Komponente existiert auf Aer nicht.  Registrierte
    Diagnostik, KEIN Gate."""
    out = {}
    for arm in ARMS:
        nq = NQ_BY_ARM[arm]
        cps, dcs = [], []
        for c in cells:
            if c["arm"] != arm or c["set"] != SET_CAL:
                continue
            if c["leg"] != "sampled" or not c["domain"]:
                continue
            pt = pts[(c["arm"], c["P"])]
            cp = cp_table[f'{pt["set"]}|{arm}|{pt["P"]}']
            delta = (ratio_ro_exact(pt, c["ro_hat"], nq)
                     + c["b_p"] * (c["kappa"] - 1.0) - c["ratio"])
            cps.append(cp)
            dcs.append(delta)
        out[arm] = {"gamma": h3.gamma_lsq(cps, dcs) if cps else 0.0,
                    "n_cells": len(cps)}
    return out


def validate_form(results):
    """Zweistufige Form-Gate-Lesart (Phase-10b-Praezedenz), am v2-ZENTRUM:
    Gate E (exact): max |res_v2| <= TOL_FORM ueber die Domain-Zellen des
    Exakt-Beins.  Gate S (sampled): q97.5 der |res_v2| ueber die Domain-
    Zellen des Sampled-Beins <= W_A; der per-Zell-Max des Sampled-Beins ist
    registrierte Diagnostik, KEIN Gate.  v2-Form statt v3: auf Aer ist
    gamma_aer ~ 0 und center_v3 reduziert exakt auf center_v2 (by
    construction, registrierte Reduktions-Eigenschaft)."""
    cells = results["cells"]
    dom_ex = [c for c in cells
              if c["leg"] == "exact" and c["kappa"] >= KAPPA_CEILING]
    dom_sa = [c for c in cells
              if c["leg"] == "sampled" and c["kappa"] >= KAPPA_CEILING]
    v2_violations = [{"set": c["set"], "arm": c["arm"], "P": c["P"],
                      "p1": c["p1"], "res": c["res_v2"]} for c in dom_ex
                     if abs(c["res_v2"]) > TOL_FORM]
    sampled_q975 = float(np.quantile(
        np.abs(np.asarray([c["res_v2"] for c in dom_sa], dtype=float)),
        0.975)) if dom_sa else 0.0
    sampled_pass = bool(sampled_q975 <= W_A)
    exact_pass = not v2_violations
    v1_fail_cells = sum(1 for c in cells if abs(c["res_v1"]) > TOL_FORM)
    return {"v2_pass": exact_pass and sampled_pass,
            "v2_pass_exact": exact_pass, "v2_pass_sampled": sampled_pass,
            "max_res_v2_exact": max((abs(c["res_v2"]) for c in dom_ex),
                                    default=0.0),
            "max_res_v2_sampled_diag": max((abs(c["res_v2"]) for c in dom_sa),
                                           default=0.0),
            "sampled_q975": sampled_q975,
            "v2_violations": v2_violations,
            "v1_fail_cells": v1_fail_cells,
            "n_domain_cells_exact": len(dom_ex),
            "n_domain_cells_sampled": len(dom_sa),
            "n_cells": len(cells)}


def build_hardware_circuit_set():
    """ALLE 116 Circuits (hardware_parameters.circuit_budget, gefroren):
    Verdict-struct 39 (13 x K_REPEATS) + Verdict-loschmidt 13 + Echo-Leiter 6
    (r in {2,4,8} x 2 Arme; r=1 geteilt mit dem Anker-Loschmidt) +
    Kalibrier-struct 39 + Kalibrier-loschmidt 13 + negative Kontrollen 4
    (Composite + Uniform an den NEUEN Ankern 181/467, Erwartungen aus dem
    gefrorenen controls-Block) + Readout-Kalibrierung 2 — EINE Quelle fuer
    ISA-3-Report und Fez-Job.  Kein Shuffle-Circuit: Shuffle-Inertness-
    Theorem (frozen_theorems.shuffle_inertness_at_dq, t4b) — bei d=q ist
    der Fold die Identitaet, die Kontrolle laege IM Prime-Band."""
    pts = _point_pts()
    cal = _cal_pts()
    doc = h3.load_frozen_prereg()
    ctrls = doc["controls"]["t4_negative_must_not_fire"]
    circuits = []
    for arm in ARMS:
        nq = NQ_BY_ARM[arm]
        for key in sorted(k for k in pts if k[0] == arm):
            pt = pts[key]
            for rep in range(K_REPEATS):
                circuits.append({
                    "name": f"struct_{arm}_{pt['P']}_r{rep}",
                    "kind": "structure", "arm": arm, "set": SET_VERDICT,
                    "P": pt["P"], "rep": rep, "shots": SHOTS,
                    "circuit": build_struct_circuit(pt, nq, measure=True)})
            circuits.append({
                "name": f"loschmidt_{arm}_{pt['P']}",
                "kind": "loschmidt", "arm": arm, "set": SET_VERDICT,
                "P": pt["P"], "shots": SHOTS,
                "circuit": build_loschmidt_circuit(pt, nq, measure=True)})
    for arm in ARMS:
        nq = NQ_BY_ARM[arm]
        P = ladder_anchor(arm)
        pt = pts[(arm, P)]
        for r in h3.LADDER_REPEATS:
            if r == 1:
                continue  # geteilt mit loschmidt_{arm}_{P} (echo_ladder.r1_shared)
            circuits.append({
                "name": f"ladder_{arm}_{P}_r{r}",
                "kind": "echo_ladder", "arm": arm, "set": SET_VERDICT,
                "P": P, "r": r, "shots": SHOTS,
                "circuit": build_ladder_circuit(pt, nq, r, measure=True)})
    for arm in ARMS:
        nq = NQ_BY_ARM[arm]
        for key in sorted(k for k in cal if k[0] == arm):
            pt = cal[key]
            for rep in range(K_REPEATS):
                circuits.append({
                    "name": f"calstruct_{arm}_{pt['P']}_r{rep}",
                    "kind": "kalibrier_structure", "arm": arm,
                    "set": SET_CAL, "P": pt["P"], "rep": rep, "shots": SHOTS,
                    "circuit": build_struct_circuit(pt, nq, measure=True)})
            circuits.append({
                "name": f"calloschmidt_{arm}_{pt['P']}",
                "kind": "kalibrier_loschmidt", "arm": arm, "set": SET_CAL,
                "P": pt["P"], "shots": SHOTS,
                "circuit": build_loschmidt_circuit(pt, nq, measure=True)})
    # Negative Kontrollen (t4): 2 Composite + 2 Uniform an den NEUEN Ankern —
    # Erwartungen direkt aus dem gefrorenen controls-Block des Payloads.
    for arm in ARMS:
        nq = NQ_BY_ARM[arm]
        P_ref = ladder_anchor(arm)
        pt_ref = pts[(arm, P_ref)]
        q = pt_ref["q"]
        tag = f"q{q}"
        comp = ctrls[f"composite_{tag}"]
        circuits.append({
            "name": f"ctrl_composite_P{P_ref}_d{pt_ref['d']}",
            "kind": "negative_control", "arm": arm, "set": SET_VERDICT,
            "P": P_ref, "control": f"composite_q{q}", "shots": SHOTS,
            "expected_share": comp["expected_share"],
            "lower_prime_band_edge": lower_prime_band_edge(pt_ref),
            "circuit": build_state_circuit(comp["n_d"], nq, measure=True)})
        uni = ctrls[f"uniform_{tag}"]
        circuits.append({
            "name": f"ctrl_uniform_q{q}", "kind": "negative_control",
            "arm": arm, "set": SET_VERDICT, "P": P_ref,
            "control": f"uniform_q{q}", "shots": SHOTS,
            "expected_share": uni["expected_share"],
            "lower_prime_band_edge": lower_prime_band_edge(pt_ref),
            "circuit": build_state_circuit([1] * q, nq, measure=True)})
    for nq in (NQ_BY_ARM["q3_d3"], NQ_BY_ARM["q5_d5"]):
        circuits.append({
            "name": f"cal_{nq}q", "kind": "readout_cal", "shots": SHOTS,
            "circuit": build_cal_circuit(nq)})
    return circuits


def run_stage3(n_ens=N_ENS, reps=K_REPEATS, results_path=RESULTS_PATH):
    """Voll-Grid: 26 Punkte x 6 Levels, exakt + sampled; b_P fuer alle 26,
    Gate E/S, gamma_aer-Diagnostik, w_B''-Konsistenz; Echo-Leiter (Exakt-
    Bein) an den NEUEN Ankern ueber alle Levels."""
    pts = all_points()
    levels = list(STRESS_GRID_P1)
    exact_curves = {}
    for key in sorted(pts):
        pt = pts[key]
        nq = NQ_BY_ARM[pt["arm"]]
        exact_curves[key] = [exact_point_level(pt, nq, p1) for p1 in levels]
    b_p, ratio_ro, intercepts = {}, {}, {}
    for key, curve in exact_curves.items():
        pt = pts[key]
        nq = NQ_BY_ARM[pt["arm"]]
        fit = fit_b_p([c["kappa"] for c in curve], [c["ratio"] for c in curve])
        b_p[key] = fit
        ratio_ro[key] = ratio_ro_exact(pt, RO_STRESS, nq)
        intercepts[key] = fit["intercept"] + fit["b_p"]
    # Kalibrier-b_P-Konsistenz gegen die committete Phase-11a-Diagnostik
    # (dieselben Punkte, dieselbe Codebahn) — Grobe-Fehler-Toleranz 1e-3
    # (siehe Modulkopf: prozessuebergreifendes BLAS-Float-Rauschen ~1e-5).
    diag = json.load(open(h3.DIAG_RESULTS, encoding="utf-8"))
    diag_bp = {r["key"]: r["b_p"] for r in diag["punkte"] if r["set"] == "new"}
    bp_kons = {}
    for key, fit in b_p.items():
        if pts[key]["set"] != SET_CAL:
            continue
        k = f"{key[0]}|{key[1]}"  # diag-Key-Konvention 'arm|P'
        diff = abs(fit["b_p"] - diag_bp[k])
        bp_kons[k] = {"stage3_grid": fit["b_p"], "diag_results": diag_bp[k],
                      "abs_diff": diff, "ok": diff < BP_KONSISTENZ_TOL}
    cells, residuals_v2, residuals_v1 = [], [], []
    sampled = {}
    for key in sorted(pts):
        pt = pts[key]
        nq = NQ_BY_ARM[pt["arm"]]
        b = b_p[key]["b_p"]
        for idx, p1 in enumerate(levels):
            ex = exact_curves[key][idx]
            sa = sampled_point_level(pt, nq, p1, n_ens=n_ens, reps=reps,
                                     level_tag=p1)
            sampled[f"{pkey(key, pts)}|{p1:g}"] = {
                "kappa_ens": sa["kappa_ens"], "ratio_ens": sa["ratio_ens"],
                "ro_hat_ens": sa["ro_hat_ens"]}
            for e in range(n_ens):
                kap, rat = sa["kappa_ens"][e], sa["ratio_ens"][e]
                ro_hat = sa["ro_hat_ens"][e]
                r2 = rat - center_v2(kap, pt, ro_hat, b)
                r1 = rat - center_v1(kap, pt)
                residuals_v2.append(r2)
                residuals_v1.append(r1)
                cells.append({"arm": pt["arm"], "set": pt["set"],
                              "P": pt["P"], "p1": p1, "leg": "sampled",
                              "ens": e, "kappa": kap, "ratio": rat,
                              "ro_hat": ro_hat, "b_p": b, "res_v1": r1,
                              "res_v2": r2,
                              "domain": kap >= KAPPA_CEILING})
            cells.append({"arm": pt["arm"], "set": pt["set"], "P": pt["P"],
                          "p1": p1, "leg": "exact", "ens": None,
                          "kappa": ex["kappa"], "ratio": ex["ratio"],
                          "res_v1": ex["res_v1"],
                          "res_v2": ex["ratio"] - center_v2(
                              ex["kappa"], pt, RO_STRESS, b),
                          "domain": ex["kappa"] >= KAPPA_CEILING})
    # Echo-Leiter (Exakt-Bein) an den NEUEN Ankern — registrierte Diagnostik.
    ladder, ladder_ops = {}, {}
    for arm in ARMS:
        nq = NQ_BY_ARM[arm]
        P = ladder_anchor(arm)
        pt = pts[(arm, P)]
        per_level = []
        for p1 in levels:
            kappas = {}
            for r in h3.LADDER_REPEATS:
                lv = ladder_point_level(pt, nq, r, p1)
                kappas[f"r{r}"] = lv["kappa_r"]
                ladder_ops[f"{arm}|r{r}"] = lv["ops_ladder"]
            per_level.append({
                "p1": p1, "kappa_by_r": kappas,
                "fit": fit_echo_ladder(
                    [kappas[f"r{r}"] for r in h3.LADDER_REPEATS],
                    list(h3.LADDER_REPEATS))})
        ladder[arm] = {"P": P, "repeats": list(h3.LADDER_REPEATS),
                       "levels": per_level}
    dom_log_res = [lv["fit"]["max_res_log"]
                   for arm in ARMS for lv in ladder[arm]["levels"]
                   # Domain-Klassifikator = kappa_r(r=1) (das Anker-kappa) —
                   # NICHT der Fit-kappa_block (Extrapolations-Slope, Phase-
                   # 10b-Praezedenz).
                   if lv["kappa_by_r"]["r1"] >= KAPPA_CEILING]
    cp_table = h3.load_frozen_prereg()["prediction_freeze"]["cP_freeze"]
    gamma_aer = gamma_aer_fit(cells, pts, cp_table)
    results = {
        "experiment": h3.EXPERIMENT, "hypothesis": h3.HYPOTHESIS,
        "status": "STAGE3_AER_COMPLETED",
        "prereg_md5": h3.load_frozen_prereg()["md5"],
        "grid": {"levels": levels, "n_ens": n_ens, "reps": reps,
                 "n_points_verdict": 13, "n_points_kalibrier": 13,
                 "domain_rule": "kappa >= KAPPA_CEILING = 0.81 per Zelle "
                                "(Minimalregister: nicht level-basiert)"},
        "sets": {"verdict": {arm: sorted(p for (a, p) in _point_pts()
                                         if a == arm) for arm in ARMS},
                 "kalibrier": {arm: sorted(p for (a, p) in _cal_pts()
                                           if a == arm) for arm in ARMS}},
        "exact": {pkey(k, pts): [
            {"p1": c["p1"], "kappa": c["kappa"], "ratio": c["ratio"],
             "res_v1": c["res_v1"], "alpha": c["alpha"],
             "ops_struct": c["ops_struct"]} for c in v]
            for k, v in exact_curves.items()},
        "b_p": {pkey(k, pts): v["b_p"] for k, v in b_p.items()},
        "b_p_fit": {pkey(k, pts): v for k, v in b_p.items()},
        "ratio_ro": {pkey(k, pts): v for k, v in ratio_ro.items()},
        "intercepts": {pkey(k, pts): v for k, v in intercepts.items()},
        "b_p_kalibrier_konsistenz": bp_kons,
        "sampled": sampled,
        "cells": cells,
        "residuals_v2": residuals_v2, "residuals_v1": residuals_v1,
        "echo_ladder_aer": ladder, "ladder_ops": ladder_ops,
        "ladder_summary": {
            "law_max_res_log_domain": float(max(dom_log_res))
            if dom_log_res else 0.0,
            "n_ladder_domain_levels": len(dom_log_res)},
        "gamma_aer": gamma_aer,
        "gamma_aer_erwartung": "~0 (Aer-Rauschen ist stochastisch, keine "
                               "kohaerente Prep-Komponente) — Diagnostik, "
                               "KEIN Gate",
        "form_validation": None,
        "w_b_doubleprime": {
            "wert": W_B_PRIME, "reused": True,
            "source": "pt_ram_q_stage2b_results.json w_b (EXPERIMENT 043, "
                      "Phase-10b-Konvention q97.5 des sampled-Beins)",
            "note": "Das Stage-3-Bein aendert w_B'' NICHT (design_decision "
                    "w_b_doppelprime_wiederverwendet, Freeze-B''-Praezedenz "
                    "Phase 10)."},
        "w_b_consistency": None,
    }
    results["form_validation"] = validate_form(results)
    sa_q975 = results["form_validation"]["sampled_q975"]
    results["w_b_consistency"] = {
        "sampled_domain_q975": sa_q975, "w_a": W_A,
        "gate_s_ok": bool(sa_q975 <= W_A),
        "note": "registrierte Diagnostik + Gate-S-Konsistenz; aendert "
                "w_B'' NICHT"}
    if results_path:
        with open(results_path, "w") as fh:
            json.dump(results, fh, indent=1, sort_keys=True)
    return results


if __name__ == "__main__":
    res = run_stage3()
    fv = res["form_validation"]
    print(f"b_P: {len(res['b_p'])} Punkte | Domain-Zellen exact "
          f"{fv['n_domain_cells_exact']} / sampled "
          f"{fv['n_domain_cells_sampled']}")
    print(f"Gate E max|res_v2| exact {fv['max_res_v2_exact']:.5f} "
          f"(TOL_FORM {TOL_FORM}) -> {fv['v2_pass_exact']} | Gate S q97.5 "
          f"{fv['sampled_q975']:.5f} (W_A {W_A}) -> {fv['v2_pass_sampled']}")
    for arm in ARMS:
        print(f"gamma_aer {arm}: {res['gamma_aer'][arm]['gamma']:+.6f} "
              f"({res['gamma_aer'][arm]['n_cells']} Zellen)")
    print(f"w_B'' (WIEDERVERWENDET): {res['w_b_doubleprime']['wert']}")
    bad = [k for k, v in res["b_p_kalibrier_konsistenz"].items()
           if not v["ok"]]
    print(f"Kalibrier-b_P-Konsistenz: {len(res['b_p_kalibrier_konsistenz'])} "
          f"Punkte, {len(bad)} Abweichungen")