# -*- coding: utf-8 -*-
"""Stage-2b Aer-Bein fuer H-RAM-Q-3b (EXPERIMENT 043) — 0 QPU.

Freeze-A'-Prereg (Re-Freeze R1, md5 0b9c9968dc5e99a3cc22962a8b760e44;
alter Freeze md5 5b91119b925ae365bcd0618a2a15fa30 ist in
simulation_leg.re_freeze_r1 dokumentiert), simulation_leg:
  Spiegel der Phase-9-simulation_leg am Minimalregister d=q statt d=q^k.
  stress_model      : aer-Praezedenz (depolarizing p1 auf 1q-Gates rz/sx/x,
                      ratio*p1 auf cz, ReadoutError ro=1e-2) — NICHT
                      kalibriert, konservativ.
  form_validation   : RE-FREEZE R1 — zweistufig.  TOL_FORM = 0.03 vergleicht
                      das DETERMINISTISCHE Zentrum (exact-Bein, 13 Punkte x 6
                      Stresslevel): max |res_v2| <= 0.03 ueber die
                      Domain-Zellen des exact-Beins.  Das sampled-Bein wird
                      noise-aware geprueft: w_B' = q97.5 der |res_v2| <=
                      W_A = 0.05; der per-Zell-Max des sampled-Beins ist
                      registrierte Diagnostik (Estimator-Rauschen), KEIN
                      Gate.  Verletzung eines der beiden Gates ->
                      Re-Freeze-Zyklus (dokumentiert, Hardware blockiert)
                      — v1->v2-Disziplin (Phase-9-Praezedenz).  Triggern
                      tat R1: Erst-Grid sampled max 0.0396 = 3.4 sigma
                      (std 0.0117), exact max 0.0022, q97.5 0.0279 <= W_A.
  freeze_b'         : w_B' = max(W_B_FLOOR, q97.5 der Ensemble-Residuen auf
                      den DOMAIN-Zellen kappa >= KAPPA_CEILING = 0.81),
                      w_B' <= W_A = 0.05; Zentrum bleibt gefroren (kein
                      Aer-Re-Zentrieren nach Freeze B').

Domain-Regel am Minimalregister (kappa-basiert, NICHT level-basiert):
  eine Zelle ist Domain, wenn kappa >= KAPPA_CEILING = 0.81 (die gefrorene
  VOID-Regel).  Bei realen Tiefen ist der q3-Arm auch bei p1=3e-3 noch
  Domain (kappa ~ 0.92) — der q5-Arm nicht mehr (kappa ~ 0.76).  Die
  Phase-9-Level-Tupel DOMAIN_LEVELS/SUB_DOMAIN_LEVELS gelten fuer das
  FLACHE Register (d=q^k) und werden hier bewusst NICHT uebernommen.

Exakt-Diagnose VOR dem Modulbau (scratch_stage2b_probe.py, 0 QPU):
  - Echo-Tiefen am Minimalregister (Aer-Basis, opt 3): q3 struct cz=1 /
    loschmidt cz=2; q5 struct cz=4 / loschmidt cz=8 — gegen Phase 9
    (~76 2q pro Loschmidt) um ~38x (q3) bzw. ~9.5x (q5) reduziert.  Die
    echten Fez-Tiefen folgen erst im Freeze-B'-ISA-Report.
  - v1 VERSAGT an saemtlichen Exakt-Zellen (res_v1 ~ -0.12 schon bei
    p1=0: kappa kuerzt den Readout raus, das Ratio traegt das
    Readout-Smearing ratio_ro - ratio_true ~ -0.12) — die registrierte
    v1->v2-Disziplin, am Minimalregister SCHAERFER als in Phase 9
    (dort 595/702).
  - v2 haelt an ALLEN Domain-Zellen: b_P (LSQ ueber Domain-Nodes
    kappa >= 0.81) max_res_fit 2.3e-4 (q3) / 2.2e-3 (q5); Arm-Ranges
    b_P q3 [1.695, 1.790], q5 [1.016, 1.044] — Arm-Universalitaet erneut
    REFUTED (per-Punkt-Steigung, Anti-Sharpshooter, Phase-9-Praezedenz).
  - Echo-Leiter (exakt-Bein an den Ankern): geometrisches Gesetz
    kappa_r = kappa_block^r haelt im Domainbereich (max log-Residual
    ~1e-4 (q3, 3e-4) / ~6e-4 (q5, 3e-4)) und bricht deep-sub-domain
    bei p1=1e-2 (log-Residual ~0.13 (q3) / ~0.32 (q5)) — registrierte
    Diagnostik, das gemessene Daempfungsgesetz fuer Fallback-B.

Diagnostik-Bein (13 alte P am Minimalregister): Circuits im 90er-Set
(fuer ISA und Fez-Job), aber KEINE Aer-Grid-Zellen — die Regel
|res_v1_run2 - res_v1_run1| <= W_CROSS vergleicht Hardware-Laeufe
(committed run-1-Eval vs. Lauf 2); Aer liefert dort keine Zusatzevidenz.
"""
import json

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import StatePreparation
from qiskit_aer import AerSimulator

import pt_ram_q_hardware as hw
import pt_ram_q_hardware_aer as aer
import pt_ram_q_hardware2 as hw2

# --- Delegation: die d-generischen Phase-9-Funktionen werden UNVERAENDERT
# wiederverwendet (Minimalregister = nur ein anderes (d, nq)-Paar). ---
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
_amp_vector = aer._amp_vector
build_struct_circuit = aer.build_struct_circuit
build_loschmidt_circuit = aer.build_loschmidt_circuit
build_state_circuit = aer.build_state_circuit
build_cal_circuit = aer.build_cal_circuit
exact_point_level = aer.exact_point_level
sampled_point_level = aer.sampled_point_level
# validate_form NICHT delegiert: Re-Freeze R1 praezisiert die Form-Gate-
# Lesart zweistufig (exact-Bein = Zentrum-Check via TOL_FORM, sampled-Bein
# noise-aware via w_B'-q97.5) — siehe validate_form unten.
compute_w_b = aer.compute_w_b
nq_of = aer.nq_of
lower_prime_band_edge_ratio = aer.lower_prime_band_edge  # Phase-9-Variante (Ratio-Einheiten, kappa=1)

RO_STRESS = aer.RO_STRESS
RATIO_2Q = aer.RATIO_2Q
BASIS_GATES = aer.BASIS_GATES
TRANSPILE_SEED = aer.TRANSPILE_SEED
SIM_SEED_EXACT = aer.SIM_SEED_EXACT

W_A = hw.W_A
W_B_FLOOR = hw.W_B_FLOOR
TOL_FORM = hw.TOL_FORM
KAPPA_CEILING = hw.KAPPA_CEILING
SHOTS = hw.SHOTS
K_REPEATS = hw.K_REPEATS
N_ENS = hw.N_ENS
STRESS_GRID_P1 = hw.STRESS_GRID_P1

ARMS = ("q3_d3", "q5_d5")
NQ_BY_ARM = {"q3_d3": hw2.NQ3, "q5_d5": hw2.NQ5}
RESULTS_PATH = "pt_ram_q_stage2b_results.json"


def ladder_anchor(arm):
    """Anker-P des Arms (echo_ladder.anchors: q3 -> 149, q5 -> 433)."""
    return hw2.LADDER_ANCHORS[arm.split("_")[0]]


def lower_prime_band_edge(pt):
    """Untere Prime-Bandkante in SHARE-Einheiten — konservativste Ecke
    kappa = KAPPA_CEILING, w = W_A (gefrorene t4-Regel:
    share_ctrl_hw < kappa_hat*(1-1/S)*share_true_reg + L_q - w; die
    Bandkante benutzt die niedrigste legal kappa-Ecke, damit must-not-fire
    auch bei kappa_hat = KAPPA_CEILING noch greift)."""
    c = (KAPPA_CEILING * (1.0 - 1.0 / SHOTS) * pt["share_true_reg"]
         + pt["L_q"] - W_A)
    return float(c)


def build_ladder_circuit(pt, nq, r, measure=True):
    """Echo-Leiter-Stufe r: r Bloecke (Prep + BARRIER + exakte Inverse) mit
    Separator-Barriern zwischen Bloecken, KEIN trailing Barrier.

    r=1 ist EXAKT der gepaarte Loschmidt-Circuit (echo_ladder.r1_shared)
    — per Konstruktion, nicht nur per Aehnlichkeit.  Die Barrieren
    verhindern die Transpiler-Kuerzung (Phase-9-Konvention).
    """
    if r not in hw2.LADDER_REPEATS:
        raise ValueError(f"r={r} nicht in der gefrorenen Leiter {hw2.LADDER_REPEATS}")
    if r == 1:
        return aer.build_loschmidt_circuit(pt, nq, measure=measure)
    qc = QuantumCircuit(nq, nq) if measure else QuantumCircuit(nq)
    amp = aer._amp_vector(pt, nq)
    prep = StatePreparation(amp)
    inv = StatePreparation(amp).inverse()
    for i in range(r):
        qc.append(prep, range(nq))
        qc.barrier(range(nq))
        qc.append(inv, range(nq))
        if i < r - 1:
            qc.barrier(range(nq))
    if measure:
        qc.measure(range(nq), range(nq))
    return qc


def _point_pts():
    """Die 13 VERDICT-Punkte (neue P) aus dem gefrorenen Freeze-A'-Payload."""
    doc = hw2.load_frozen_prereg()
    pts = {}
    for arm in ARMS:
        for p in doc["prediction_freeze"]["points"][arm]:
            p = dict(p)
            p["arm"] = arm
            pts[(arm, p["P"])] = p
    return pts


def _diagnostik_pts():
    """Die 13 alten P am Minimalregister (diagnostik_bein.points, gefroren)."""
    doc = hw2.load_frozen_prereg()
    pts = {}
    for arm in ARMS:
        for p in doc["diagnostik_bein"]["points"][arm]:
            p = dict(p)
            p["arm"] = arm
            pts[(arm, p["P"])] = p
    return pts


def ladder_point_level(pt, nq, r, p1, seed=SIM_SEED_EXACT):
    """Echo-Leiter-Stufe auf dem Exakt-Bein: density_matrix (Kanaele EXAKT,
    ro=0 im Kanal, Readout ANALYTISCH via T_ro) -> kappa_r = P_L/P_ro_ref
    mit P_ro_ref = (1-ro)^nq."""
    nm = aer.stress_noise_model(p1, ro=0.0)
    qc = transpile(build_ladder_circuit(pt, nq, r, measure=False),
                   basis_gates=BASIS_GATES, optimization_level=3,
                   seed_transpiler=TRANSPILE_SEED)
    qc.save_density_matrix()
    sim = AerSimulator(method="density_matrix", noise_model=nm,
                       seed_simulator=seed)
    res = sim.run(qc, shots=1).result()
    rho = np.asarray(res.data(0)["density_matrix"])
    pl_ro = float(aer.readout_apply(np.real(np.diag(rho)), RO_STRESS, nq)[0])
    pro = (1.0 - RO_STRESS) ** nq
    return {"p1": p1, "r": r, "kappa_r": pl_ro / pro,
            "ops_ladder": dict(qc.count_ops())}


def fit_echo_ladder(kappas, repeats):
    """Geometrisches Gesetz kappa_r = kappa_block^r: log-LSQ ueber die
    Leiter-Stufen (gemessenes Daempfungsgesetz statt starrer (1-eps)^2-
    Annahme).  Ruegabe: slope/intercept (log-Einheiten), kappa_block und
    der maximale log-Residual (Fit-Guete)."""
    if len(kappas) != len(repeats) or len(kappas) < 2:
        raise ValueError("Leiter-Fit braucht >= 2 Stufen, kappa/repeats gleich lang")
    xs = np.asarray(repeats, dtype=float)
    logs = np.log(np.asarray(kappas, dtype=float))
    slope, intercept = np.polyfit(xs, logs, 1)
    res = logs - (intercept + slope * xs)
    return {"slope": float(slope), "intercept": float(intercept),
            "kappa_block": float(np.exp(slope)),
            "max_res_log": float(np.abs(res).max())}


def validate_form(results):
    """Re-Freeze R1 — zweistufige Form-Gate-Lesart (dokumentiert im Payload,
    simulation_leg.form_validation + re_freeze_r1).

    Gate E (Zentrum): max |res_v2| <= TOL_FORM = 0.03 ueber die
    Domain-Zellen des EXACT-Beins — das deterministische Gesetz (die
    registrierten 13 Punkte x 6 Stresslevel).
    Gate S (Rauschen): q97.5 der |res_v2| ueber die Domain-Zellen des
    SAMPLED-Beins <= W_A = 0.05 (dieselbe Groesse wie das freeze_b'-q97.5) —
    der per-Zell-Max des sampled-Beins misst das Estimator-Rauschen
    (Erst-Grid: max 0.0396 = 3.4 sigma bei std 0.0117) und ist registrierte
    Diagnostik, KEIN Gate.
    """
    cells = results["cells"]
    dom_ex = [c for c in cells
              if c["leg"] == "exact" and c["kappa"] >= KAPPA_CEILING]
    dom_sa = [c for c in cells
              if c["leg"] == "sampled" and c["kappa"] >= KAPPA_CEILING]
    v2_violations = [{"arm": c["arm"], "P": c["P"], "p1": c["p1"],
                      "res": c["res_v2"]} for c in dom_ex
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
    """ALLE 90 Circuits (hardware_parameters.circuit_budget, gefroren):
    struktur 39 + loschmidt 13 + echo_ladder 6 + diagnostik_struktur 13 +
    diagnostik_loschmidt 13 + negative_kontrollen 4 + readout_kalibrierung 2
    — EINE Quelle fuer ISA-Report und Fez-Job.

    r=1 der Leiter ist der gepaarte Loschmidt-Circuit des Ankers (geteilt,
    kein doppeltes Circuit) — deshalb 6 Leiter-Circuits (r in {2,4,8} x 2
    Arme) und 13 Loschmidts (inklusive der 2 Anker-Loschmidts).
    """
    pts = _point_pts()
    dg = _diagnostik_pts()
    circuits = []
    for arm in ARMS:
        nq = NQ_BY_ARM[arm]
        for key in sorted(k for k in pts if k[0] == arm):
            pt = pts[key]
            for rep in range(K_REPEATS):
                circuits.append({
                    "name": f"struct_{arm}_{pt['P']}_r{rep}",
                    "kind": "structure", "arm": arm, "P": pt["P"],
                    "rep": rep, "shots": SHOTS,
                    "circuit": build_struct_circuit(pt, nq, measure=True)})
            circuits.append({
                "name": f"loschmidt_{arm}_{pt['P']}",
                "kind": "loschmidt", "arm": arm, "P": pt["P"],
                "shots": SHOTS,
                "circuit": build_loschmidt_circuit(pt, nq, measure=True)})
    for arm in ARMS:
        nq = NQ_BY_ARM[arm]
        P = ladder_anchor(arm)
        pt = pts[(arm, P)]
        for r in hw2.LADDER_REPEATS:
            if r == 1:
                continue  # geteilt mit loschmidt_{arm}_{P} (echo_ladder.r1_shared)
            circuits.append({
                "name": f"ladder_{arm}_{P}_r{r}",
                "kind": "echo_ladder", "arm": arm, "P": P, "r": r,
                "shots": SHOTS,
                "circuit": build_ladder_circuit(pt, nq, r, measure=True)})
    for arm in ARMS:
        nq = NQ_BY_ARM[arm]
        for key in sorted(k for k in dg if k[0] == arm):
            pt = dg[key]
            circuits.append({
                "name": f"diag_struct_{arm}_{pt['P']}",
                "kind": "diagnostik_structure", "arm": arm, "P": pt["P"],
                "rep": 0, "shots": SHOTS,
                "circuit": build_struct_circuit(pt, nq, measure=True)})
            circuits.append({
                "name": f"diag_loschmidt_{arm}_{pt['P']}",
                "kind": "diagnostik_loschmidt", "arm": arm, "P": pt["P"],
                "shots": SHOTS,
                "circuit": build_loschmidt_circuit(pt, nq, measure=True)})
    # Negative Kontrollen (t4): 2 Composite + 2 Uniform — exakte Erwartungen
    # gefroren im Payload; Referenz = Anker-Punkt des Arms (gleiche Arm-,
    # gleiche P-Ecke).  Kein Shuffle-Circuit: Shuffle-Inertness-Theorem
    # (frozen_theorems.shuffle_inertness_at_dq) — bei d=q ist der Fold die
    # Identitaet, die Kontrolle laege IM Prime-Band.
    for arm in ARMS:
        nq = NQ_BY_ARM[arm]
        P_ref = ladder_anchor(arm)
        pt_ref = pts[(arm, P_ref)]
        q = pt_ref["q"]
        comp = hw.composite_control(P_ref, pt_ref["d"], q)
        circuits.append({
            "name": f"ctrl_composite_P{P_ref}_d{pt_ref['d']}",
            "kind": "negative_control", "arm": arm, "P": P_ref,
            "control": f"composite_q{q}", "shots": SHOTS,
            "expected_share": comp["expected_share"],
            "lower_prime_band_edge": lower_prime_band_edge(pt_ref),
            "circuit": build_state_circuit(comp["n_d"], nq, measure=True)})
        uni = hw2.uniform_control(q)
        circuits.append({
            "name": f"ctrl_uniform_q{q}", "kind": "negative_control",
            "arm": arm, "P": P_ref, "control": f"uniform_q{q}",
            "shots": SHOTS,
            "expected_share": uni["expected_share"],
            "lower_prime_band_edge": lower_prime_band_edge(pt_ref),
            "circuit": build_state_circuit([1] * q, nq, measure=True)})
    for nq in (NQ_BY_ARM["q3_d3"], NQ_BY_ARM["q5_d5"]):
        circuits.append({
            "name": f"cal_{nq}q", "kind": "readout_cal", "shots": SHOTS,
            "circuit": build_cal_circuit(nq)})
    return circuits


def run_stage2b(n_ens=N_ENS, reps=K_REPEATS, results_path=RESULTS_PATH):
    """Voll-Grid: 13 Punkte x 6 Levels, exakt + sampled; b_P, w_B', Form;
    Echo-Leiter am Anker (Exakt-Bein ueber alle Levels, geometrischer Fit)."""
    pts = _point_pts()
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
            sampled[f"{key[0]}|{key[1]}|{p1:g}"] = {
                "kappa_ens": sa["kappa_ens"], "ratio_ens": sa["ratio_ens"],
                "ro_hat_ens": sa["ro_hat_ens"]}
            for e in range(n_ens):
                kap, rat = sa["kappa_ens"][e], sa["ratio_ens"][e]
                ro_hat = sa["ro_hat_ens"][e]
                r2 = rat - center_v2(kap, pt, ro_hat, b)
                r1 = rat - center_v1(kap, pt)
                residuals_v2.append(r2)
                residuals_v1.append(r1)
                cells.append({"arm": pt["arm"], "P": pt["P"], "p1": p1,
                              "leg": "sampled", "ens": e, "kappa": kap,
                              "ratio": rat, "res_v1": r1, "res_v2": r2,
                              "domain": kap >= KAPPA_CEILING})
            cells.append({"arm": pt["arm"], "P": pt["P"], "p1": p1,
                          "leg": "exact", "ens": None, "kappa": ex["kappa"],
                          "ratio": ex["ratio"], "res_v1": ex["res_v1"],
                          "res_v2": ex["ratio"] - center_v2(
                              ex["kappa"], pt, RO_STRESS, b),
                          "domain": ex["kappa"] >= KAPPA_CEILING})
    # Echo-Leiter am Anker: Exakt-Bein ueber alle Levels, geometrischer Fit.
    ladder, ladder_ops = {}, {}
    for arm in ARMS:
        nq = NQ_BY_ARM[arm]
        P = ladder_anchor(arm)
        pt = pts[(arm, P)]
        per_level = []
        for p1 in levels:
            kappas = {}
            for r in hw2.LADDER_REPEATS:
                lv = ladder_point_level(pt, nq, r, p1)
                kappas[f"r{r}"] = lv["kappa_r"]
                ladder_ops[f"{arm}|r{r}"] = lv["ops_ladder"]
            per_level.append({
                "p1": p1, "kappa_by_r": kappas,
                "fit": fit_echo_ladder(
                    [kappas[f"r{r}"] for r in hw2.LADDER_REPEATS],
                    list(hw2.LADDER_REPEATS))})
        ladder[arm] = {"P": P, "repeats": list(hw2.LADDER_REPEATS),
                       "levels": per_level}
    dom_log_res = [lv["fit"]["max_res_log"]
                   for arm in ARMS for lv in ladder[arm]["levels"]
                   # Domain-Klassifikator = kappa_r(r=1) (das Anker-kappa,
                   # kappa >= KAPPA_CEILING = VOID-Regel) — NICHT der
                   # Fit-kappa_block (der Extrapolations-Slope wuerde bei
                   # p1=1e-2 q3 0.875 >= 0.81 melden, obwohl kappa_1 = 0.757
                   # sub-domain ist und das Gesetz dort BRICHT).
                   if lv["kappa_by_r"]["r1"] >= KAPPA_CEILING]
    n_law_total = sum(len(ladder[arm]["levels"]) for arm in ARMS)
    results = {
        "experiment": hw2.EXPERIMENT, "hypothesis": hw2.HYPOTHESIS,
        "status": "STAGE2B_AER_COMPLETED",
        "prereg_md5": hw2.load_frozen_prereg()["md5"],
        "grid": {"levels": levels, "n_ens": n_ens, "reps": reps,
                 "domain_rule": "kappa >= KAPPA_CEILING = 0.81 per Zelle "
                                "(Minimalregister: nicht level-basiert)"},
        "exact": {f"{k[0]}|{k[1]}": [
            {"p1": c["p1"], "kappa": c["kappa"], "ratio": c["ratio"],
             "res_v1": c["res_v1"], "alpha": c["alpha"],
             "ops_struct": c["ops_struct"]} for c in v]
            for k, v in exact_curves.items()},
        "b_p": {f"{k[0]}|{k[1]}": v["b_p"] for k, v in b_p.items()},
        "b_p_fit": {f"{k[0]}|{k[1]}": v for k, v in b_p.items()},
        "ratio_ro": {f"{k[0]}|{k[1]}": v for k, v in ratio_ro.items()},
        "intercepts": {f"{k[0]}|{k[1]}": v for k, v in intercepts.items()},
        "sampled": sampled,
        "cells": cells,
        "residuals_v2": residuals_v2, "residuals_v1": residuals_v1,
        "echo_ladder": ladder, "ladder_ops": ladder_ops,
        "ladder_summary": {
            "law_max_res_log_domain": float(max(dom_l for dom_l in dom_log_res)
                                            if dom_log_res else 0.0),
            "n_ladder_domain_levels": len(dom_log_res)},
        "form_validation": None, "w_b": None,
    }
    results["form_validation"] = validate_form(results)
    results["w_b"] = compute_w_b(results)
    if results_path:
        with open(results_path, "w") as fh:
            json.dump(results, fh, indent=1, sort_keys=True)
    return results