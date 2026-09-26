# -*- coding: utf-8 -*-
"""Stage-2 Aer-Bein fuer H-RAM-Q-3 (EXPERIMENT 042) — 0 QPU.

Freeze-A-Prereg (md5 432d43fe1bc9e2594efd3b35266d2d81), simulation_leg:
  stress_model      : depolarizing p1 auf 1q, ratio*p1 auf 2q (ibm_fez nativ
                      cz statt cx — dokumentierte Adaption), ReadoutError
                      ro=1e-2 — NICHT kalibriert, konservativ.
  form_validation   : |ratio_Aer - c(kappa_hat_Aer)| <= TOL_FORM = 0.03;
                      Re-Freeze-Zyklus (dokumentiert) fuehrt zur gesetzlichen
                      v2-Form mit Domain kappa >= KAPPA_CEILING = 0.81 (die
                      gefrorene VOID-Regel definiert genau diese Domain als
                      Struktur-Garantie; Zellen darunter sind im verdict_map
                      ohnehin VOID — Amendment wird in Freeze B registriert).
  freeze_b          : w_B = max(W_B_FLOOR, q97.5 der Ensemble-Residuen),
                      w_B <= W_A = 0.05; Zentrum bleibt gefroren (kein
                      Aer-Re-Zentrieren nach Freeze B).

v2-Gesetz (Exakt-Diagnose vor dem Modulbau, 0 QPU):
  c2(kappa_hat, P) = (1-1/S) * [ ratio_ro(P, ro_hat) + b_P * (kappa_hat - 1) ]
                     + L_q(P)
  - ratio_ro(P, ro): EXAKTER Anker aus gefrorener Arithmetik (T_ro(ro) auf
    den gefrorenen n_d -> fold -> ABSOLUT-FFT-Share -> / model_share_reg);
    bei ro=0 identisch ratio_true (kappa=1-Anker per Konstruktion).
  - b_P: per-Punkt-Steigung aus der exakten Stress-Kurve (LSQ ueber die 3
    Domain-Levels {0, 1e-4, 3e-4}); die starke Arm-Universalitaet der
    Steigung ist REFUTED (q3: 0.898 vs 0.862, q5: 0.672 vs 0.713) — eine
    arm-geteilte Steigung wuerde eine falsche Universalitaet einfrieren
    (Anti-Sharpshooter). Arm-Ranges als sekundaere Beobachtung registriert.
  - Korrigierte Inversion: alpha_hat = sqrt((kappa_hat - u)/(1 - u)) mit
    u = 2^-nq / P_ro_ref (die verworfene Formel sqrt(1+(1-kappa)/(1-u))-1
    ist ein Vorzeichenfehler, Spot-Check-Z.87).

Kontrollen: t3 Zwei-Wege-Identitaet (ABSOLUT-FFT bei j*d/q vs gefaltete
Formel (q*sum N_hat^2 - m_hat^2)/(d*m), 1e-12), t6 Massenerhaltung
(sum N_hat = m unter Depolarisierung via Uniform-Masse), 4 Negativ-
Kontrollen mit exakten Erwartungen (die 4. — shuffle@(625,d=25,seed 421) —
wird in Freeze B registriert).
"""
import hashlib
import json
import os

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import StatePreparation
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error

import pt_ram_q_hardware as hw

BASIS_GATES = ["rz", "sx", "x", "cz"]
RO_STRESS = 0.01
RATIO_2Q = 10.0
TRANSPILE_SEED = 7
SIM_SEED_EXACT = 11
NQ_BY_ARM = {"q3_d9": 4, "q5_d25": 5}
DOMAIN_LEVELS = (0.0, 1e-4, 3e-4)   # VOID-Regel-Domain; kappa >= 0.81 dort
SUB_DOMAIN_LEVELS = (1e-3, 3e-3, 1e-2)  # registrierte Diagnostik

W_A = hw.W_A
W_B_FLOOR = hw.W_B_FLOOR
TOL_FORM = hw.TOL_FORM
KAPPA_CEILING = hw.KAPPA_CEILING

RESULTS_PATH = "pt_ram_q_stage2_results.json"
ISA_PATH = "pt_ram_q_isa_report.json"


def two_qubit_depolarizing_param(p1, ratio_2q=RATIO_2Q):
    """Gefrorene Adaption: ibm_fez nativ cz (statt cx) => 2q-Fehler ratio*p1."""
    return min(ratio_2q * p1, 1.0)


def stress_noise_model(p1, ro=RO_STRESS, ratio_2q=RATIO_2Q):
    """Gefrorenes STRESS-Modell (simulation_leg.stress_model, nicht kalibriert)."""
    nm = NoiseModel()
    if p1 > 0:
        nm.add_all_qubit_quantum_error(depolarizing_error(p1, 1),
                                       ["rz", "sx", "x"])
        nm.add_all_qubit_quantum_error(
            depolarizing_error(two_qubit_depolarizing_param(p1, ratio_2q), 2),
            ["cz"])
    if ro > 0:
        nm.add_all_qubit_readout_error(ReadoutError([[1 - ro, ro],
                                                     [ro, 1 - ro]]))
    return nm


def readout_apply(probs, ro, nq):
    """Analytischer Readout-Kanal T_ro^tensor per Qubit (Flachregister)."""
    c = np.asarray(probs, dtype=float).reshape([2] * nq)
    T = np.array([[1 - ro, ro], [ro, 1 - ro]])
    for k in range(nq):
        c = np.moveaxis(np.tensordot(T, c, axes=([1], [k])), 0, k)
    return c.reshape(-1)


def share_hw_fft(n_d, q, d, m):
    """Gefrorene share*_hw-Definition: ABSOLUT-FFT-Konvention.

    sum_{j=1}^{q-1} |DFT_d(n_hat)[j*d/q]|^2 / (d*m)  (operational_definitions)
    """
    G = np.fft.fft(np.asarray(n_d, dtype=float))
    js = [int(j * d / q) for j in range(1, q)]
    return float(sum(abs(G[j]) ** 2 for j in js) / (d * m))


def share_hw_folded(N, q, d, m):
    """Gefaltete Form der Identitaet (041-Theorem): (q*sum N^2 - m^2)/(d*m).

    G[j*d/q] haengt nur von n mod q ab => G[j*d/q] = DFT_q(N)[j]; Parseval
    ueber die q-Laenge: sum_{j=1}^{q-1} |DFT_q(N)[j]|^2 = q*sum N^2 - m^2.
    """
    N = np.asarray(N, dtype=float)
    return float((q * np.sum(N ** 2) - m * m) / (d * m))


def fold_d(n_full, d):
    """Wraparound-Fold eines Label-Vektors auf d Klassen: n_d[a] = sum n_full[a::d]."""
    n_full = np.asarray(n_full, dtype=float)
    return np.array([n_full[a::d].sum() for a in range(d)])


def p0_fraction(counts, nq):
    """P(0^n): Anteil der All-Zeros-Bitstrings (Loschmidt/Readout-Kalibrierung)."""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return sum(v for k, v in counts.items()
               if set(k.replace(" ", "")) == {"0"}) / total


def ratio_from_counts(counts, pt, nq):
    """Gefrorene hw_counts-Kette auf einem Counts-Dict: n_hat = m*c/S (rational,
    kein Rounding) -> fold -> ABSOLUT-FFT-Share -> ratio = share/model_share_reg.
    t6-Massenerhaltung: sum_a n_hat_a = m exakt (Depolarisierung erhaelt die
    Uniform-Masse)."""
    d, q, m = pt["d"], pt["q"], pt["m"]
    n_labels = 2 ** nq
    n_full = np.zeros(n_labels)
    for bits, c in counts.items():
        n_full[int(bits.replace(" ", ""), 2)] += c
    n_hat = m * fold_d(n_full, d) / hw.SHOTS
    share = share_hw_fft(n_hat, q, d, m)
    return {"share": share, "ratio": share / pt["model_share_reg"],
            "n_hat": n_hat.tolist(), "m_hat": float(n_hat.sum())}


def ratio_ro_exact(pt, ro, nq):
    """EXAKTER kappa=1-Anker: T_ro(ro) auf den gefrorenen n_d (Arithmetik,
    kein Simulation).  Bei ro=0 identisch ratio_true."""
    d, q, m = pt["d"], pt["q"], pt["m"]
    n_labels = 2 ** nq
    n_full = np.zeros(n_labels)
    n_full[:d] = pt["n_d"]
    p_ro = readout_apply(n_full / m, ro, nq)
    n_hat = m * p_ro
    share = share_hw_fft(fold_d(n_hat, d), q, d, m)
    return share / pt["model_share_reg"]


def alpha_from_kappa(kappa_hat, u):
    """KORRIGIERTE Inversion: alpha = sqrt((kappa-u)/(1-u)).

    Verworfen (Vorzeichenfehler): sqrt(1 + (1-kappa)/(1-u)) - 1.
    """
    return float(np.sqrt(max((kappa_hat - u) / (1.0 - u), 0.0)))


def center_v1(kappa_hat, pt):
    """Freeze-A-Zentrum (v1) — EXPECTED-FAIL-Dokumentation der Exakt-Diagnose."""
    return kappa_hat * (1.0 - 1.0 / hw.SHOTS) * pt["ratio_true"] + pt["L_q"]


def nq_of(pt):
    """Register-Breite aus d (9 -> 4 Qubits, 25 -> 5 Qubits)."""
    return int(np.ceil(np.log2(pt["d"])))


def center_v2(kappa_hat, pt, ro_hat, b_p):
    """Gesetzliche v2-Form: per-Punkt-Anker + per-Punkt-Steigung (siehe Modul-Doc)."""
    S = hw.SHOTS
    return (1.0 - 1.0 / S) * (ratio_ro_exact(pt, ro_hat, nq_of(pt))
                              + b_p * (kappa_hat - 1.0)) + pt["L_q"]


def fit_b_p(kappas, ratios, ceiling=KAPPA_CEILING):
    """Per-Punkt-Steigung: LSQ Grad 1 ueber die Domain-Nodes (kappa >= ceiling)."""
    pts = [(k, r) for k, r in zip(kappas, ratios) if k >= ceiling]
    if len(pts) < 2:
        raise ValueError("weniger als 2 Domain-Nodes — b_P nicht identifizierbar")
    xs = np.array([k for k, _ in pts])
    ys = np.array([r for _, r in pts])
    b, a = np.polyfit(xs, ys, 1)
    res = ys - (a + b * xs)
    return {"b_p": float(b), "intercept": float(a),
            "max_res": float(np.abs(res).max()), "n_nodes": len(pts)}


def stage2_seed(*parts):
    """Deterministische Seeds (md5-Hash ueber die Argumente)."""
    tag = "|".join(str(p) for p in parts).encode("utf-8")
    return int(hashlib.md5(tag).hexdigest()[:8], 16)


def _amp_vector(pt, nq):
    n_labels = 2 ** nq
    amp = [np.sqrt(n / pt["m"]) if n > 0 else 0.0 for n in pt["n_d"]]
    return amp + [0.0] * (n_labels - len(amp))


def build_struct_circuit(pt, nq, measure=True):
    """Struktur-Circuit: StatePreparation(sqrt(n_a/m)) [+ measure_all]."""
    qc = QuantumCircuit(nq, nq) if measure else QuantumCircuit(nq)
    qc.append(StatePreparation(_amp_vector(pt, nq)), range(nq))
    if measure:
        qc.measure(range(nq), range(nq))
    return qc


def build_loschmidt_circuit(pt, nq, measure=False):
    """Gepaarter Loschmidt-Circuit: Prep + BARRIER + exakte Inverse (gleiche
    Tiefe); P_L = P(0^n) nach dem Echo.  Der Barrier verhindert, dass der
    Transpiler Prep*Prep^-1 wegkuerzt."""
    qc = QuantumCircuit(nq, nq) if measure else QuantumCircuit(nq)
    amp = _amp_vector(pt, nq)
    qc.append(StatePreparation(amp), range(nq))
    qc.barrier(range(nq))
    qc.append(StatePreparation(amp).inverse(), range(nq))
    if measure:
        qc.measure(range(nq), range(nq))
    return qc


def build_state_circuit(n_counts, nq, measure=True):
    """Kontroll-State aus einem Counts-Vektor (Shuffle/Composite)."""
    m = float(sum(n_counts))
    amp = [np.sqrt(n / m) if n > 0 else 0.0 for n in n_counts]
    amp += [0.0] * (2 ** nq - len(amp))
    qc = QuantumCircuit(nq, nq) if measure else QuantumCircuit(nq)
    qc.append(StatePreparation(amp), range(nq))
    if measure:
        qc.measure(range(nq), range(nq))
    return qc


def build_cal_circuit(nq):
    """Readout-Kalibrier-Circuit |0>^n -> P_ro_ref = P(0^n) im selben Job."""
    qc = QuantumCircuit(nq, nq)
    qc.measure(range(nq), range(nq))
    return qc


def _point_pts():
    doc = hw.load_frozen_prereg()
    pts = {}
    for arm in ("q3_d9", "q5_d25"):
        for p in doc["prediction_freeze"]["points"][arm]:
            p = dict(p)
            p["arm"] = arm
            pts[(arm, p["P"])] = p
    return pts


def lower_prime_band_edge(pt):
    """Untere Prime-Bandkante (share-Einheiten) bei kappa=1 — MAXIMALE Kante
    (c monoton wachsend in kappa), konservative Vorab-Registrierung fuer die
    Must-not-fire-Regel der Negativ-Kontrollen (t4)."""
    c1 = (1.0 - 1.0 / hw.SHOTS) * pt["ratio_true"] + pt["L_q"]
    return (c1 - W_A) * pt["model_share_reg"]


def build_hardware_circuit_set():
    """ALLE 58 Circuits (circuit_budget): struktur 39 + loschmidt 13 +
    negativ_kontrollen 4 + readout_kalibrierung 2 — EINE Quelle fuer
    ISA-Report und Fez-Job."""
    pts = _point_pts()
    circuits = []
    for arm in ("q3_d9", "q5_d25"):
        nq = NQ_BY_ARM[arm]
        for key in sorted(k for k in pts if k[0] == arm):
            pt = pts[key]
            for rep in range(hw.K_REPEATS):
                circuits.append({
                    "name": f"struct_{arm}_{pt['P']}_r{rep}",
                    "kind": "structure", "arm": arm, "P": pt["P"],
                    "rep": rep, "shots": hw.SHOTS,
                    "circuit": build_struct_circuit(pt, nq, measure=True)})
            circuits.append({
                "name": f"loschmidt_{arm}_{pt['P']}",
                "kind": "loschmidt", "arm": arm, "P": pt["P"],
                "shots": hw.SHOTS,
                "circuit": build_loschmidt_circuit(pt, nq, measure=True)})
    for P, d, q, seed, name in ((109, 9, 3, 421, "ctrl_shuffle_421_P109_d9"),
                                (109, 9, 3, 422, "ctrl_shuffle_422_P109_d9"),
                                (625, 25, 5, 421, "ctrl_shuffle_421_P625_d25")):
        ctrl = hw.shuffle_control(P, d, q, seed)
        pt_ref = _point_pts()[(("q3_d9" if q == 3 else "q5_d25"), P)]
        circuits.append({
            "name": name, "kind": "negative_control", "arm": pt_ref["arm"],
            "P": P, "seed": seed, "shots": hw.SHOTS,
            "expected_share": ctrl["expected_share"],
            "lower_prime_band_edge": lower_prime_band_edge(pt_ref),
            "circuit": build_state_circuit(ctrl["n_shuffled"], NQ_BY_ARM[pt_ref["arm"]], measure=True)})
    comp = hw.composite_control(625, 25, 5)
    pt_ref = _point_pts()[("q5_d25", 625)]
    circuits.append({
        "name": "ctrl_composite_P625_d25", "kind": "negative_control",
        "arm": "q5_d25", "P": 625, "shots": hw.SHOTS,
        "expected_share": comp["expected_share"],
        "lower_prime_band_edge": lower_prime_band_edge(pt_ref),
        "circuit": build_state_circuit(comp["n_d"], 5, measure=True)})
    for nq in (4, 5):
        circuits.append({
            "name": f"cal_{nq}q", "kind": "readout_cal", "shots": hw.SHOTS,
            "circuit": build_cal_circuit(nq)})
    return circuits


def exact_point_level(pt, nq, p1, seed=SIM_SEED_EXACT):
    """Exakt-Bein: density_matrix (Quanten-Kanaele EXAKT, kein Sampling),
    Readout ANALYTISCH via T_ro; kappa = P_L/P_ro_ref mit P_ro_ref=(1-ro)^nq."""
    d, q, m = pt["d"], pt["q"], pt["m"]
    nm = stress_noise_model(p1, ro=0.0)
    los = transpile(build_loschmidt_circuit(pt, nq, measure=False),
                    basis_gates=BASIS_GATES, optimization_level=3,
                    seed_transpiler=TRANSPILE_SEED)
    st = transpile(build_struct_circuit(pt, nq, measure=False),
                   basis_gates=BASIS_GATES, optimization_level=3,
                   seed_transpiler=TRANSPILE_SEED)
    los.save_density_matrix()
    st.save_density_matrix()
    sim = AerSimulator(method="density_matrix", noise_model=nm,
                       seed_simulator=seed)
    res = sim.run([los, st], shots=1).result()
    rho_l = np.asarray(res.data(0)["density_matrix"])
    rho_s = np.asarray(res.data(1)["density_matrix"])
    pl_bare = float(np.real(rho_l[0, 0]))
    probs_s = np.real(np.diag(rho_s))
    ro = RO_STRESS
    pl_ro = float(readout_apply(np.real(np.diag(rho_l)), ro, nq)[0])
    pro = (1.0 - ro) ** nq
    kappa = pl_ro / pro
    u = 2.0 ** -nq / pro
    alpha = alpha_from_kappa(kappa, u)
    n_hat = m * readout_apply(probs_s, ro, nq)
    share = share_hw_fft(fold_d(n_hat, d), q, d, m)
    ratio = share / pt["model_share_reg"]
    out = {"p1": p1, "pl_bare": pl_bare, "kappa": kappa, "u": u,
           "alpha": alpha, "share": share, "ratio": ratio,
           "res_v1": ratio - center_v1(kappa, pt),
           "ops_struct": dict(st.count_ops()),
           "ops_loschmidt": dict(los.count_ops())}
    return out


def sampled_point_level(pt, nq, p1, n_ens=hw.N_ENS, reps=hw.K_REPEATS,
                        level_tag=None):
    """Sampled-Bein: pro Ensemble EIN Batch [struct x reps, loschmidt, cal]
    mit 8192 Shots (mirrors Hardware-Job-Struktur); kappa_ens = P_L/P_ro_ref
    aus dem Batch-eigenen Loschmidt + Kalibrierung; ratio_ens = Mittel der
    per-Rep-Ratios."""
    nm = stress_noise_model(p1, ro=RO_STRESS)
    struct = [build_struct_circuit(pt, nq, measure=True) for _ in range(reps)]
    los = build_loschmidt_circuit(pt, nq, measure=True)
    cal = build_cal_circuit(nq)
    batch = transpile(struct + [los, cal], basis_gates=BASIS_GATES,
                      optimization_level=3, seed_transpiler=TRANSPILE_SEED)
    tag = level_tag if level_tag is not None else p1
    kappa_ens, ratio_ens, ro_hat_ens = [], [], []
    for ens in range(n_ens):
        seed = stage2_seed(pt["P"], pt["d"], tag, ens)
        sim = AerSimulator(method="density_matrix", noise_model=nm,
                           seed_simulator=seed)
        res = sim.run(batch, shots=hw.SHOTS).result()
        cnts = [res.get_counts(i) for i in range(len(batch))]
        p_ro = p0_fraction(cnts[-1], nq)
        pl = p0_fraction(cnts[-2], nq)
        kappa_ens.append(pl / p_ro if p_ro > 0 else float("inf"))
        ro_hat = 1.0 - p_ro ** (1.0 / nq)
        ro_hat_ens.append(ro_hat)
        ratios = [ratio_from_counts(cnts[i], pt, nq)["ratio"]
                  for i in range(reps)]
        ratio_ens.append(float(np.mean(ratios)))
    return {"kappa_ens": kappa_ens, "ratio_ens": ratio_ens,
            "ro_hat_ens": ro_hat_ens,
            "kappa_mean": float(np.mean(kappa_ens)),
            "ratio_mean": float(np.mean(ratio_ens))}


def validate_form(results):
    """Form-Validierung gegen das gefrorene Gesetz.

    v2: max |res_v2| <= TOL_FORM ueber die DOMAIN-Zellen (kappa >= 0.81).
    v1: Anzahl der FAIL-Zellen (dokumentierter Re-Freeze-Trigger).
    Sub-Domain-Zellen = registrierte Diagnostik (Amendment in Freeze B).
    """
    cells = results["cells"]
    dom = [c for c in cells if c["kappa"] >= KAPPA_CEILING]
    v2_violations = [{"arm": c["arm"], "P": c["P"], "p1": c["p1"],
                      "res": c["res_v2"]} for c in dom
                     if abs(c["res_v2"]) > TOL_FORM]
    v1_fail_cells = sum(1 for c in cells if abs(c["res_v1"]) > TOL_FORM)
    return {"v2_pass": not v2_violations, "v2_violations": v2_violations,
            "v1_fail_cells": v1_fail_cells,
            "n_domain_cells": len(dom), "n_cells": len(cells),
            "max_res_v2_domain": max((abs(c["res_v2"]) for c in dom),
                                     default=0.0)}


def compute_w_b(results):
    """Freeze-B-Halbbreite: w_B = clip(q97.5 der |Ensemble-Residuen| ueber die
    DOMAIN-Zellen (kappa >= KAPPA_CEILING, gefroren in Freeze A), W_B_FLOOR,
    W_A).  Sub-Domain-Residuen bleiben registrierte Diagnostik — das Gesetz
    ist domain-restriktiv (unterhalb 0.81 versagt es strukturimmanent, dort
    sind die v2-Residuen bis ~0.25 gross), und die verdict_map verlangt
    kappa_hat >= 0.81 fuer CONFIRMED.  Der rohe q97.5 geht als w_b_raw_q975
    in das Result, damit der Prereg-Gate-Text ('w_B <= W_A = 0.05, sonst
    Re-Freeze') gegen den UNGECLIPPTEN Wert geprueft werden kann."""
    cells = results["cells"]
    dom = [abs(c["res_v2"]) for c in cells
           if c["leg"] == "sampled" and c["domain"]]
    if not dom:
        return W_B_FLOOR
    raw = float(np.quantile(np.asarray(dom, dtype=float), 0.975))
    results["w_b_raw_q975"] = raw
    results["w_b_gate_ok"] = bool(raw <= W_A)
    return float(np.clip(raw, W_B_FLOOR, W_A))


def run_stage2(n_ens=hw.N_ENS, reps=hw.K_REPEATS,
               results_path=RESULTS_PATH):
    """Voll-Grid: 13 Punkte x 6 Levels, exakt + sampled; b_P, w_B, Form."""
    pts = _point_pts()
    levels = list(hw.STRESS_GRID_P1)
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
    results = {
        "experiment": hw.EXPERIMENT, "hypothesis": hw.HYPOTHESIS,
        "status": "STAGE2_AER_COMPLETED",
        "prereg_md5": hw.load_frozen_prereg()["md5"],
        "grid": {"levels": levels, "n_ens": n_ens, "reps": reps,
                 "domain_levels": list(DOMAIN_LEVELS),
                 "sub_domain_levels": list(SUB_DOMAIN_LEVELS)},
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
        "form_validation": None, "w_b": None,
    }
    results["form_validation"] = validate_form(results)
    results["w_b"] = compute_w_b(results)
    if results_path:
        with open(results_path, "w") as fh:
            json.dump(results, fh, indent=1, sort_keys=True)
    return results