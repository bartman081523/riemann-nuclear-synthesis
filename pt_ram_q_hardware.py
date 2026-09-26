# -*- coding: utf-8 -*-
"""EXPERIMENT 042 — H-RAM-Q-3: die q-universelle RAM-Q-Identität unter Hardware-Rauschen.

Freeze-A-Prereg, Status REGISTERED_NOT_MEASURED, 0 QPU.

Kette:
    034 (q=5 Fingerprint, md5 a2fc4875) -> 040 (H-RAM-Q-1 q=3, md5 bd9dfee7)
    -> 041 (H-RAM-Q-2 q-universelle Identität, md5 704916f9)
    -> 032 (§Z.14 Fez-QPU-Präzedenz, md5 18fb1e62) -> DIESER Freeze (A).

Klassischer Kern (gefroren, aus 040/034/041 bit-exakt reproduziert):
    ratio_true = (q-1) * (q * sum_r N_r^2 - m^2) / (m - q*n0)^2
    q=3:  ratio_true = 1 + 12*delta^2/(m-3)^2        (delta = (N1-N2)/2, n0 = 1-Atom)
    q=5:  ratio_true = 1 + 20*sigma^2/(m-5)^2

Rauschgesetz (NEU, hier gefroren):
    ratio_hw = kappa * (1 - 1/S) * ratio_true + L_q
    L_q      = (q-1)^2 * m^2 / (S * (m - q*n0)^2)
    kappa_p  = P_L / P_ro_ref  (gepaarte Loschmidt-/Readout-Kalibrier-Circuits im selben Job)

Die Loschmidt-Survival kappa ~= (1 - eps_C)^2 ist exakt der Dämpfungsfaktor der
kohärenten Harmonischen-Struktur: unter Depolarisierung rho -> (1-eps)*rho + eps*I/d
verschwindet der Uniform-Anteil in allen Nicht-Null-Harmonischen, |G_j|^2 dämpft als
(1-eps)^2. kappa wird gemessen, nicht gefittet; das Gesetz koppelt zwei operationell
UNABHÄNGIGE Messungen (Loschmidt-Survival und Harmonischen-Anteil der Counts).

Register-Topologie (d-Invarianz-Theorem, 041 T3 exakt): der Ratio ist d-frei, deshalb
tragen die Punkte die flachen Register d=9 (4 Qubits, q=3) und d=25 (5 Qubits, q=5)
mit IDENTISCHEN Ratio-Vorhersagen; für d >= P reduziert sich |psi(P,d)>
= sum_a sqrt(n_a/m)|a> auf den Prime-State (1/sqrt(m)) sum_p |p>.
"""

import hashlib
import json
import os

import numpy as np

from pt_ram_q_zyklizitaet import residue_counts, sieve_primes

EXPERIMENT = "042-ram-q-hardware-noise-lift"
HYPOTHESIS = "H-RAM-Q-3"
STATUS = "REGISTERED_NOT_MEASURED"
REGISTERED_BEFORE = "2026-09-26"
PREREG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "pt_ram_q_hardware_prereg.json")

SHOTS = 8192
K_REPEATS = 3
W_A = 0.05                  # Freeze-A-Bandhalbbreite (grob), Freeze B darf nur verengen
KAPPA_CEILING = 0.81        # kappa >= 0.81 <=> eps_C <= 0.10 (Struktur-Garantie)
TOL_FORM = 0.03             # Stage-2-Form-Validierung (Aer, relativ auf dem Ratio)
W_B_FLOOR = 0.01            # w_B = max(floor, Aer-Ensemble-Residuen), capped bei W_A
ISA_2Q_PER_CIRCUIT_MAX = 120
ISA_2Q_TOTAL_MAX = 6000
STRESS_GRID_P1 = [0.0, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2]
N_ENS = 8

Q3_POINTS = [109, 163, 211, 307, 401, 541, 625, 729]
Q5_POINTS = [401, 463, 541, 599, 625]
D3_REGISTER = 9
D5_REGISTER = 25
SHUFFLE_SEEDS = [421, 422]
COMPOSITE_P = 625


# === exakte Arithmetik (aus dem gefrorenen 040/034/041-Kern) ===

def fold_mod_q(n_d, d, q):
    """Falte den d-langen Count-Vektor auf die q Residuenklassen."""
    return [sum(n_d[a] for a in range(d) if a % q == r) for r in range(q)]


def arm_point(P, d, q):
    """Exakte Konstanten eines gated Punkts auf dem Register d.

    Enthaelt die gefrorenen Counts n_d (Integer-Vektor), die daraus abgeleiteten
    klassischen Konstanten (ratio_true etc.) und die Register-Share-Werte.
    """
    primes = sieve_primes(P)
    m = len(primes)
    n_d = residue_counts(P, d)
    if sum(n_d) != m:
        raise ValueError(f"Count-Vektor P={P}, d={d}: Summe {sum(n_d)} != m {m}")
    N = fold_mod_q(n_d, d, q)
    n0 = N[0]
    sq = sum(x * x for x in N)
    num = q * sq - m * m
    den = (m - q * n0) ** 2
    ratio_true = (q - 1) * num / den
    share_true_reg = num / (float(d) * m)
    model_share_reg = den / ((q - 1) * float(d) * m)
    L_q = (q - 1) ** 2 * m * m / (SHOTS * den)
    point = {
        "P": P, "d": d, "q": q, "m": m,
        "n_d": n_d, "N": N, "n0": n0,
        "q_sum_N_sq_minus_m2": num,
        "ratio_true": ratio_true,
        "L_q": L_q,
        "share_true_reg": share_true_reg,
        "model_share_reg": model_share_reg,
    }
    if q == 3:
        delta = (N[1] - N[2]) / 2.0
        point["delta"] = delta
        point["delta_sq"] = delta * delta
        point["closed_form"] = 1.0 + 12.0 * delta * delta / (m - 3) ** 2
    else:
        sigma2 = (q * sq - m * m - (m - q * n0) ** 2 / (q - 1)) / float(q)
        point["sigma2"] = sigma2
        point["closed_form"] = 1.0 + 20.0 * sigma2 / (m - 5) ** 2
    if abs(point["closed_form"] - ratio_true) > 1e-12:
        raise ValueError(f"closed_form != ratio_true bei P={P}, q={q}")
    return point


def _load_040_ratios():
    rows = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "pt_ram_q_results.json")))["rows"]
    return {r["P"]: r["ratio"] for r in rows if r.get("gated")}


def _load_034_ratios():
    rows = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "pt_ramanujan_results.json")))["rows"]
    return {r["P"]: r["share_prime"] / r["model"] for r in rows if r.get("gated")}


def _verify_anchors(q3_points, q5_points, tol=1e-9):
    """T1: ratio_true aller 13 Punkte bit-exakt gegen die gefrorenen 040/034-Ketten."""
    r40 = _load_040_ratios()
    r34 = _load_034_ratios()
    problems = []
    for pt in q3_points:
        ref = r40.get(pt["P"])
        if ref is None:
            problems.append(f"040 kennt P={pt['P']} nicht")
        elif abs(ref - pt["ratio_true"]) > tol:
            problems.append(f"040 P={pt['P']}: {ref} != {pt['ratio_true']}")
    for pt in q5_points:
        ref = r34.get(pt["P"])
        if ref is None:
            problems.append(f"034 kennt P={pt['P']} nicht")
        elif abs(ref - pt["ratio_true"]) > tol:
            problems.append(f"034 P={pt['P']}: {ref} != {pt['ratio_true']}")
    if problems:
        raise ValueError("Anker-Verifikation gescheitert: " + "; ".join(problems))
    return {"q3_vs_040": "8/8 bit-exakt (tol 1e-9)",
            "q5_vs_034": "5/5 bit-exakt (tol 1e-9)"}


def shuffle_control(P, d, q, seed):
    """Negativ-Kontrolle: gefrorene Label-Permutation zerstört die mod-q-Struktur."""
    n_d = residue_counts(P, d)
    m = len(sieve_primes(P))
    perm = np.random.RandomState(seed).permutation(d).tolist()
    n_sh = [0] * d
    for a in range(d):
        n_sh[perm[a]] = n_d[a]
    N_sh = fold_mod_q(n_sh, d, q)
    sq = sum(x * x for x in N_sh)
    expected_share = (q * sq - m * m) / (float(d) * m)
    return {"kind": "shuffle_q3", "P": P, "d": d, "q": q, "seed": seed,
            "permutation": perm, "n_shuffled": n_sh, "N_tilde": N_sh,
            "expected_share": expected_share,
            "rule": "share_hw < kappa*(1-1/S)*share_true_reg + L_q - w (untere Prime-Bandkante)"}


def _first_composites(k):
    """Die ersten k kompositen Zahlen (034-Konvention rank-matched)."""
    primes = set(sieve_primes(max(4 * k, 600)))
    out, x = [], 4
    while len(out) < k:
        if x not in primes:
            out.append(x)
        x += 1
    return out


def composite_control(P, d, q):
    """Negativ-Kontrolle q=5: erste m Composites mod d (034-Konvention)."""
    m = len(sieve_primes(P))
    n_d = [0] * d
    for c in _first_composites(m):
        n_d[c % d] += 1
    N_c = fold_mod_q(n_d, d, q)
    sq = sum(x * x for x in N_c)
    expected_share = (q * sq - m * m) / (float(d) * m)
    return {"kind": "composite_q5", "P": P, "d": d, "q": q, "m": m,
            "n_d": n_d, "N_tilde": N_c, "expected_share": expected_share,
            "rule": "share_hw < kappa*(1-1/S)*share_true_reg + L_q - w (untere Prime-Bandkante)"}


# === Payload ===

def build_prereg_payload():
    q3 = [arm_point(P, D3_REGISTER, 3) for P in Q3_POINTS]
    q5 = [arm_point(P, D5_REGISTER, 5) for P in Q5_POINTS]
    anchor_report = _verify_anchors(q3, q5)
    shuffles = [shuffle_control(109, D3_REGISTER, 3, seed) for seed in SHUFFLE_SEEDS]
    composite = composite_control(COMPOSITE_P, D5_REGISTER, 5)

    payload = {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "status": STATUS,
        "registered_before": REGISTERED_BEFORE,
        "registered_by": "pt_ram_q_hardware.freeze_prereg — payload_md5 = "
                         "md5(json.dumps(payload, sort_keys=True, separators=(',',':'))) "
                         "OHNE md5-Feld (Haus-Konvention, pt_hshor1/pt_ram_q_zyklizitaet)",
        "user_anchor": (
            "Baue das Prereg-Skelett für diese q-universelle Identität im Status "
            "REGISTERED_NOT_MEASURED auf. ... Vorhersage-Freeze: Exakte Fixierung der "
            "Rausch-Vorhersage und der erwarteten Ratio-Verschiebung samt MD5-Hash, "
            "isoliert von jeglichem Hardware-Kontakt. Hardware-Parameter: Festlegung der "
            "Register-Topologie, der physikalischen Fehler-Modelle (Fez-Noise) und der "
            "exakten Shot-Metriken für den IBMQ-Lauf. Sicherungs-Limits: Eindeutige "
            "Deklaration der Abbruchbedingungen, Konfundierungsgrenzen und Trennschärfen. "
            "Die Spiegel verbleiben als reiner kartografischer Index, während die "
            "Arithmetik der verrauschten Counts das Experiment diktiert. Setze das "
            "Skelett auf, damit wir den Zustand vor dem ersten QPU-Kontakt absolut sauber "
            "einfrieren können."),
        "layer_separation": {
            "hermeneutic_index": "M1-M5 bleiben kartografischer Index über dem Bestand "
                                 "(Branch gematria-mirror-synthesis); sie ordnen die "
                                 "dokumentierte Reihenfolge und generieren niemals Evidenz.",
            "encoding_verbot": "Die hermeneutischen Werte 1025/348/879/5683 werden NIEMALS "
                               "als Encoding-Parameter auf Quanten-Register gepresst. Dieses "
                               "Experiment codiert ausschließlich exakte arithmetische "
                               "Größen (Primzahlen, Residuen, Counts).",
            "evidence_layer": "Die Arithmetik der verrauschten Counts diktiert: share*_hw "
                              "aus den Hardware-Counts via ABSOLUT-FFT bei j*d/q, Ratio "
                              "gegen GEFRORENE Modell-Denominatoren (n0, m aus der "
                              "wahren Arithmetik, kein Refit).",
        },
        "prior_chain": {
            "a2fc4875e10dd198e95d4996b1692759": "EXPERIMENT 034 — q=5 Fingerprint, "
                                                "5 gated Punkte @ d=625",
            "bd9dfee77b9fada8a230347f9d45f5a7": "EXPERIMENT 040 — H-RAM-Q-1 q=3 Deformation, "
                                                "8 gated Punkte @ d=729",
            "704916f946beedf49c51ab6bc9bf37bd": "EXPERIMENT 041 — H-RAM-Q-2 q-universelle "
                                                "Identität (CONFIRMED B)",
            "18fb1e62a3dd71c6f595416cdd40bcc1": "EXPERIMENT 032 — §Z.14 Fez-QPU-Präzedenz "
                                                "(12 Circuits x 8192 Shots, TOKEN1)",
        },
        "frozen_theorems": {
            "B2_q_universal_identity": "share* = (m - q*n0)^2/((q-1)*d*m) + q*sigma^2/(d*m) "
                                       "für ALLE Count-Vektoren inkl. Wraparound (041, "
                                       "CONFIRMED B, 716-Test-Suite)",
            "d_invariance": "d*m*share* hängt nur von den mod-q gefalteten Counts ab (041 T3 "
                            "exakt) -> Ratio-Vorhersagen sind d-frei; die flachen Register "
                            "d=9/d=25 tragen die IDENTISCHEN Ratio-Vorhersagen",
            "ratio_forms": {
                "q3": "ratio_true = 1 + 12*delta^2/(m-3)^2",
                "q5": "ratio_true = 1 + 20*sigma^2/(m-5)^2",
                "general": "ratio_true = (q-1)*(q*sum_r N_r^2 - m^2)/(m - q*n0)^2",
            },
        },
        "operational_definitions": {
            "state": "|psi(P,d)> = sum_a sqrt(n_a/m)|a> mit n_a = #{p <= P prim : "
                     "p ≡ a mod d}; für d >= P identisch mit dem Prime-State "
                     "(1/sqrt(m)) sum_p |p>, für d < P die kollabierte Normalisierung "
                     "(Kollisionen mergen Amplituden).",
            "hw_counts": "n_hat_a = m*c_a/S (rational, KEIN Rounding); unter Depolarisierung "
                         "erhält die Uniform-Masse m exakt: sum_a n_hat_a = m.",
            "share_hw": "share*_hw = sum_{j=1}^{q-1} |DFT_d(n_hat)[j*d/q]|^2/(d*m), "
                        "ABSOLUT-FFT-Konvention (Haus-Lektion, kein Vorzeichen-Mix).",
            "ratio_hw": "share*_hw / model_share_reg mit model_share_reg = "
                        "(m - q*n0_true)^2/((q-1)*d*m) GEFROREN auf wahre Arithmetik-Werte.",
            "kappa": "kappa_p = P_L/P_ro_ref. P_L: gepaarter Loschmidt-Circuit "
                     "(State-Prep + exakte Inverse, gleiche Tiefe), P(0^n); P_ro_ref: "
                     "Readout-Kalibrier-Circuit |0>^n im SELBEN Job. kappa ~= (1-eps_C)^2 "
                     "ist exakt der Dämpfungsfaktor der kohärenten Struktur — gemessen, "
                     "nicht gefittet.",
            "idle_labels": "Labels a >= d des 2^n-Qubit-Registers sind ideal leer; "
                           "Leakage-Masse wird von der Stage-2-Form-Validierung erfasst "
                           "(Hintergrund-Asymmetrie 2^n/d-Klassen).",
        },
        "prediction_freeze": {
            "classical_core": {
                "q3": "ratio_true = 1 + 12*delta^2/(m-3)^2 — die User-Headline",
                "q5": "ratio_true = 1 + 20*sigma^2/(m-5)^2",
                "verdict_in_040_034": "8/8 und 5/5 gated Punkte im Band [0.8, 1.25]",
            },
            "noise_law": {
                "ratio_hw": "ratio_hw = kappa*(1 - 1/S)*ratio_true + L_q",
                "L_q": "L_q = (q-1)^2*m^2/(S*(m-q*n0)^2) — exakte multinomiale Erwartung "
                       "E[share*_hw] = (1-1/S)*share*_true + (q-1)*m/(S*d); der Lift ist "
                       "UNTER dem Shot-Noise (6e-4..2e-3 auf dem Ratio) und wird im "
                       "Zentrum registriert, nicht als separierbar behauptet",
                "suppression": "kappa = P_L/P_ro_ref dämpft die kohärente Struktur; die "
                               "SUPPRESSION ist das dominante messbare Hardware-Signal "
                               "((1-eps)^2: -4% bei eps=0.02 ≈ 2.9σ, -6% bei eps=0.03 "
                               "≈ 4.2σ bei K=3 gepoolt)",
                "honesty": "Das Gesetz koppelt zwei operationell unabhängige Messungen "
                           "(Loschmidt-Survival und Harmonischen-Share); Verletzung der "
                           "Kopplung = Falsifikation via Band.",
            },
            "points": {"q3_d9": q3, "q5_d25": q5},
            "anchor_verification": anchor_report,
        },
        "hardware_parameters": {
            "backend": "ibm_fez",
            "token": "TOKEN1 (IBMQ_TOKEN); TOKEN2 unberuehrt",
            "n_shots": SHOTS,
            "register_topology": {
                "q3": {"d": D3_REGISTER, "n_qubits": 4, "labels": 16,
                       "note": "n_d gefroren je Punkt; Amplituden sqrt(n_a/m); "
                               "Labels 9..15 ideal leer"},
                "q5": {"d": D5_REGISTER, "n_qubits": 5, "labels": 32,
                       "note": "n_d gefroren je Punkt; Amplituden sqrt(n_a/m); "
                               "Labels 25..31 ideal leer"},
            },
            "state_prep": "Qiskit StatePreparation aus den gefrorenen n_d-Vektoren; "
                          "Loschmidt = Prep + exakte Inverse (gleiche Gate-Menge).",
            "circuit_budget": {
                "structure": 13 * K_REPEATS,
                "loschmidt": 13,
                "negative_controls": 4,
                "readout_cal": 2,
                "total": 13 * K_REPEATS + 13 + 4 + 2,
                "total_shots": (13 * K_REPEATS + 13 + 4 + 2) * SHOTS,
                "jobs": 1,
            },
            "run_config": {"optimization_level": 3, "dynamical_decoupling": "XX",
                           "resilience": "none (raw SamplerV2 counts)"},
            "isa_ceilings": {
                "per_circuit_2q_max": ISA_2Q_PER_CIRCUIT_MAX,
                "total_2q_max": ISA_2Q_TOTAL_MAX,
                "measured_when": "Stage-2-Transpilation VOR Hardware; Backend-Target-Laden "
                                 "= kein Quota-Kontakt (kein Job), §Z.14-Phase-3b-Präzedenz",
                "abort": "Ceiling-Überschreitung vor dem QPU-Lauf -> Abbruch, Re-Freeze",
            },
        },
        "simulation_leg": {
            "purpose": "0 QPU: Validierung der Dämpfungsform auf dem gefrorenen "
                       "STRESS-Modell VOR Hardware; Freeze-B-Bandbreiten.",
            "stress_model": "pt_ququint_ibmq_aer.build_noise_model (depolarizing p1 auf "
                            "1q-Gates, ratio*p1 auf cx, ReadoutError ro=1e-2) — NICHT "
                            "kalibriert, konservativ (§Z.13/§Z.14-Präzedenz).",
            "stress_grid_p1": STRESS_GRID_P1,
            "n_ens": N_ENS,
            "form_validation": "|ratio_Aer - c(kappa_hat_Aer)| <= TOL_FORM = 0.03 an ALLEN "
                               "13 Punkten x 6 Stresslevel; sonst Re-Freeze-Zyklus "
                               "(dokumentiert, Hardware blockiert) — v1->v2-Disziplin "
                               "(H-STAR-5-Präzedenz).",
            "freeze_b": "w_B = max(W_B_FLOOR, q97.5-Halbbreite der Ensemble-Residuen über "
                        "alle Punkte x Stresslevel), w_B <= W_A = 0.05, sonst Re-Freeze; "
                        "Zentrum c(kappa) bleibt GEFROREN (kein Aer-Re-Zentrieren).",
        },
        "safeguard_limits": {
            "band_rule": "ratio_hw ∈ [c(kappa_hat) - w, c(kappa_hat) + w]; Freeze A: "
                         "w_A = 0.05; Freeze B darf nur VERENGEN (w_B <= w_A); das "
                         "Zentrum c(kappa_hat) = kappa_hat*(1-1/S)*ratio_true + L_q "
                         "bleibt gefroren.",
            "amplification_ceiling": "ratio_hw > (1-1/S)*ratio_true + L_q + w -> "
                                     "H-RAM-Q-3_INVALID_AMPLIFICATION (einseitig: "
                                     "Depolarisierung dämpft Prime-Harmonische, hebt sie "
                                     "nie über das rauschfreie Niveau + Band)",
            "kappa_floor_void": "kappa_hat_p < KAPPA_CEILING = 0.81 -> Punkt EXKLUDIERT "
                                "(VOID_CALIBRATION); >= 2 exkludierte Punkte -> "
                                "H-RAM-Q-3_VOID_CALIBRATION_GLOBAL",
            "falsifier": ">= 2 der 13 Punkte UNTERHALB c(kappa_hat) - w -> H-RAM-Q-3_REFUTED",
            "trennschaerfe": {
                "band_vs_shot_noise": "gepoolte K=3-Ratio-SE ≈ 1.4-2.0% (S=8192) gegen "
                                      "w_A = 5% -> >= 2.5σ Auflösung",
                "kappa_se": "SE(kappa_hat) ≈ 0.005 (Loschmidt, 8192 Shots) -> "
                            "SE(Zentrum) ≈ 0.005 << w",
                "coupling": "kappa_hat (Loschmidt) und share-Ratio (Harmonische) sind "
                            "operationell UNABHÄNGIG; das gefrorene Gesetz koppelt sie.",
            },
            "job_integrity": "EIN Fez-Job (TOKEN1), 58 Circuits; Job-ID + md5 der Counts "
                             "committed VOR der Auswertung (§Z.14-Disziplin).",
        },
        "controls": {
            "t1_backcompat": anchor_report,
            "t2_v2_anchors": "034-Prime-Anker (625,625) = 0.04272280701754398 über die "
                             "d=625-Kette unberührt — klassisch, kein QPU-Kontakt.",
            "t3_identity_two_ways": "share*_hw = sum_j |G_j|^2/(d*m) auf den HW-Counts "
                                    "zwei Wege (FFT bei j*d/q vs gefaltete Formel "
                                    "(q*sum N_hat^2 - m_hat^2)/(d*m)), exakt 1e-12 "
                                    "(041-Theorem); Verletzung -> EVALUATION_INVALID.",
            "t4_negative_must_not_fire": {
                "shuffle": shuffles,
                "composite": composite,
                "rule": "share_ctrl_hw < kappa_hat*(1-1/S)*share_true_reg + L_q - w "
                        "(untere Prime-Bandkante); Verletzung -> H-RAM-Q-3_DEGENERAT "
                        "(REFUTED-zulässig, Degenerat-Lektion)",
            },
            "t5_gate_set_frozen": "13 Punkte = genau die 8 gated (040, d-Invarianz) + die "
                                  "5 gated (034); keine nachträglichen Ergänzungen.",
            "t6_mass_conservation": "sum_r N_hat_r = m_hat unter Depolarisierung "
                                    "(Uniform-Masse erhält m exakt); Verletzung -> "
                                    "EVALUATION_INVALID.",
        },
        "verdict_map": {
            "H-RAM-Q-3_NOISE_LIFT_CONFIRMED": "alle 13 Punkte im Band "
                                              "[c(kappa_hat)-w_B, c(kappa_hat)+w_B], "
                                              "Kontrollen grün, alle kappa_hat >= 0.81",
            "H-RAM-Q-3_COARSE_HOLD_SHARP_MISS": "alle Punkte im groben Band (w_A), "
                                                ">= 1 Punkt außerhalb w_B",
            "H-RAM-Q-3_REFUTED": ">= 2 Punkte unter c(kappa_hat) - w",
            "H-RAM-Q-3_INVALID_AMPLIFICATION": "irgendein Punkt über "
                                               "(1-1/S)*ratio_true + L_q + w",
            "H-RAM-Q-3_VOID_CALIBRATION": "kappa_hat < 0.81 an >= 2 Punkten",
            "H-RAM-Q-3_DEGENERAT": "Kontroll-Regel T4 verletzt (Prime-Share auf "
                                   "Kontroll-Niveau) — REFUTED-zulässig",
            "EVALUATION_INVALID_KONTROLLE_GESCHEITERT": "T1-T6 gescheitert — Auswertung void",
        },
        "two_freeze_architecture": {
            "freeze_a": "DIESER Freeze: analytischer Kern + alle 13 Punkt-Konstanten "
                        "+ Regeln + md5, VOR jedem Hardware-/Simulations-Kontakt, "
                        "0 QPU.",
            "stage2_aer": "Aer-Bein (0 QPU) mit gefrorenem STRESS-Modell: "
                          "Form-Validierung + w_B + ISA-Report.",
            "freeze_b": "w_B-Registrierung (<= w_A) + ISA-Report VOR dem QPU-Lauf; "
                        "Zentrum unverändert; erst danach QPU-Kontakt.",
            "hardware": "EIN Fez-Job (TOKEN1) erst nach Freeze-B-Commit; alle "
                        "Abbruchbedingungen exakt in safeguard_limits registriert.",
        },
        "anti_sharpshooter": {
            "no_ex_post_fit": "Die 13 Punkte sind exakt die gefrorenen gated Sets aus 040/034 "
                              "(T5); die Konstanten m, n0, delta, sigma2, ratio_true sind "
                              "aus der Arithmetik VOR dem Freeze berechnet und gegen die "
                              "bit-exakten 040/034-Ketten verifiziert (T1).",
            "registered_alternative_models": "keine — die Dämpfungsform (1-eps)^2 folgt aus "
                                             "Depolarisierung; die Stage-2-Form-Validierung "
                                             "prüft sie VOR Hardware (Re-Freeze bei "
                                             "Misserfolg, kein Still-Swap).",
            "negative_predictions": "Shuffle-/Composite-Erwartungen exakt registriert "
                                    "(T4); der Sampling-Lift L_q ist unter dem Shot-Noise "
                                    "und wird NICHT als separierbar behauptet (Ehrlichkeit).",
        },
        "qpu": "0 QPU (Freeze A); Stage-2 Aer 0 QPU; EIN Fez-Job (TOKEN1) erst nach "
               "Freeze B",
        "suite_state": 716,
        "future_phase_numbering": {
            "synthesis": "§Z.24 (SYNTHESIS)",
            "log": "§10.25 (RIEMANN) — §Z.23/§10.24 durch den Gematria-Spiegel-Layer "
                   "belegt (Branch gematria-mirror-synthesis); bewusste Lücke, "
                   "Zusammenführung chronologisch",
        },
    }
    return payload


# === Freeze (Haus-Konvention) ===

def canonical_payload_json(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def payload_md5(payload):
    return hashlib.md5(canonical_payload_json(payload).encode("utf-8")).hexdigest()


def freeze_prereg(payload=None, path=PREREG_PATH):
    if payload is None:
        payload = build_prereg_payload()
    doc = dict(payload)
    doc["md5"] = payload_md5(payload)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    return doc


def verify_prereg_md5(doc):
    stripped = {k: v for k, v in doc.items() if k != "md5"}
    return payload_md5(stripped) == doc["md5"]


def load_frozen_prereg(path=PREREG_PATH):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if not verify_prereg_md5(doc):
        raise ValueError(f"H-RAM-Q-3-Prereg-md5-MISMATCH in {path}")
    return doc