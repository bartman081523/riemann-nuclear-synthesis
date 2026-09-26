# -*- coding: utf-8 -*-
"""EXPERIMENT 043 — H-RAM-Q-3b: Minimalregister + Echo-Leiter (Freeze A').

Freeze-A'-Prereg, Status REGISTERED_NOT_MEASURED, 0 QPU.

Kette:
    034 (q=5 Fingerprint, md5 a2fc4875) -> 040 (H-RAM-Q-1 q=3, md5 bd9dfee7)
    -> 041 (H-RAM-Q-2 q-universelle Identitaet, md5 704916f9)
    -> 032 (§Z.14 Fez-QPU-Praezedenz, md5 18fb1e62)
    -> 042 (H-RAM-Q-3, Freeze-A md5 432d43fe, Run-1-Raw d19f4a56)
    -> DIESER Freeze (A').

Phase-9-Befund (VOID_CALIBRATION): alle 13 kappa_hat < 0.81 [0.6608..0.8080],
Kontrollen gruen — das Defizit ist die Loschmidt-Echo-TIEFE (4q-Arm 30 2q,
5q-Arm 76 2q), nicht der Readout. Die unveraenderte Struktur-Garantie
kappa_hat >= KAPPA_CEILING = 0.81 verlangt Echo <= ~29.7 2q (4q, KNAPP) bzw.
<= ~38.7-42.9 2q (5q, via Synthese unerreichbar).

Design-Hebel (User-Freigabe): die bewiesene d-Invarianz (041 T3 exakt) macht
das Register zum INSTRUMENT, nicht zur Hypothese — die Ratio-Vorhersagen sind
d-frei. Deshalb tragen die 13 VERDICT-Punkte die MINIMALREPRÄSENTANTEN
    q=3 auf d=3 (2 Qubits, Echo ~2-6 2q)  und  q=5 auf d=5 (3 Qubits, ~8-12 2q)
mit IDENTISCHEN Ratio-Vorhersagen; kappa_hat ~0.94-0.98 (q3) bzw. ~0.93-0.96
(q5) loest die Garantie mit Marge ein. Die 13 alten P-Werte (durch die
ermittelte Reskalierung vorbelastet) werden NICHT wiederverwendet — neue P
nach registrierter Regel.

P-Regel (registriert-deterministisch, vor jeder Messung):
    P_neu = kleinste Primzahl p mit p > P_alt + 30  (je alter Punkt).

Echo-Tiefen-Leiter (Kalibrier-Diagnostik): r-fache (Prep + exakte Inverse)-
Bloecke, r ∈ {1, 2, 4, 8}, je Arm am Ankerpunkt — misst Survival-vs-Tiefe
geometrisch und liefert das GEMESSENE Daempfungsgesetz statt der starren
(1-eps)^2-Annahme; r=1 ist identisch mit dem gepaarten Loschmidt-Circuit des
Ankerpunkts (geteilt, kein doppeltes Circuit).

Kontrollen bei d=q: die Phase-9-Shuffle-Kontrolle ist am Minimalregister
strukturell INERT (Fold = Identitaet, Label-Permutation laesst sum N^2
invariant => expected_share == share_true_reg EXAKT, laege IM Prime-Band) —
dokumentiertes Theorem, ersetzt durch Composite- (beide Arme) und
Uniform-Null-Kontrollen (beide Arme) mit exakten Erwartungen.
"""

import hashlib
import json
import os

import pt_ram_q_hardware as hw

EXPERIMENT = "043-ram-q-minimal-register-echo"
HYPOTHESIS = "H-RAM-Q-3b"
STATUS = "REGISTERED_NOT_MEASURED"
REGISTERED_BEFORE = "2026-09-26"
PREREG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "pt_ram_q_hardware2_prereg.json")

# Gefrorene Konstanten — UNVERAENDERT aus Phase 9 (Freeze A, md5 432d43fe)
SHOTS = hw.SHOTS                    # 8192
K_REPEATS = hw.K_REPEATS            # 3
W_A = hw.W_A                        # 0.05 (Freeze B' darf nur verengen)
KAPPA_CEILING = hw.KAPPA_CEILING    # 0.81 (unveraendert gefrorene Garantie)
TOL_FORM = hw.TOL_FORM              # 0.03
W_B_FLOOR = hw.W_B_FLOOR            # 0.01
ISA_2Q_PER_CIRCUIT_MAX = hw.ISA_2Q_PER_CIRCUIT_MAX   # 120 (Phase-9-Praezedenz)
ISA_2Q_TOTAL_MAX = hw.ISA_2Q_TOTAL_MAX               # 6000
STRESS_GRID_P1 = hw.STRESS_GRID_P1
N_ENS = hw.N_ENS

# Register: Minimalrepraesentanten (d = q) statt flacher Register d = q^k
D3_MIN = 3
D5_MIN = 5
NQ3 = 2                             # 2^2 = 4 Labels, 3 real, 1 idle (Label 3)
NQ5 = 3                             # 2^3 = 8 Labels, 5 real, 3 idle (Labels 5..7)
D3_WIDE = hw.D3_REGISTER            # 9  (Run-1-Register, Diagnostik-Vergleich)
D5_WIDE = hw.D5_REGISTER            # 25

# Alte 13 Punkte (Run-1, vorbelastet) -> Diagnostik-Bein; neue P -> Verdict
OLD_Q3_POINTS = list(hw.Q3_POINTS)
OLD_Q5_POINTS = list(hw.Q5_POINTS)

LADDER_REPEATS = (1, 2, 4, 8)

# Diagnostik-Band (Kreuz-Register, res_v1-Differenz ueber die Laeufe)
W_CROSS = 0.09
RUN1_EVAL = "pt_ram_q_hardware_eval.json"
RUN1_COUNTS_MD5 = RUN1_COUNTS_MD5_KEY = "d19f4a563d88e0cf3ffd4b187a10ca73"
RUN1_JOB = "darq1stvr3kc73ej96ig"


def smallest_prime_above(x):
    """Kleinste Primzahl p mit p > x (registrierte P-Regel, deterministisch)."""
    y = x + 1
    while True:
        primes = hw.sieve_primes(y)
        if primes and primes[-1] == y:
            return y
        y += 1


def new_points_for(old_points):
    """Registrierte P-Regel: P_neu = kleinste Primzahl > P_alt + 30."""
    return [smallest_prime_above(P + 30) for P in old_points]


NEW_Q3_POINTS = new_points_for(OLD_Q3_POINTS)
NEW_Q5_POINTS = new_points_for(OLD_Q5_POINTS)
LADDER_ANCHORS = {"q3": NEW_Q3_POINTS[0], "q5": NEW_Q5_POINTS[0]}


# === exakte Arithmetik (gefrorener Kern, Wiederverwendung aus 042) ===

def arm_point(P, d, q):
    """Exakte Konstanten eines Punkts (042-Kern, d-frei per 041-T3)."""
    return hw.arm_point(P, d, q)


def _load_040_ratios():
    return hw._load_040_ratios()


def _load_034_ratios():
    return hw._load_034_ratios()


def verify_anchors_minimal(r3_points, r5_points, tol=1e-9):
    """T1': d-Invarianz am Minimalregister bit-exakt gegen die 040/034-Ketten.

    (a) alle 8 alten q3-P auf d=3 == 040-Ratio (bit-exakt), alle 5 alten q5-P
        auf d=5 == 034-Ratio — das Register d=q ist der minimale Repraesenant.
    (b) alle 13 NEUEN P: d=q == d=q^2 == d=q^3 (identische Ratio-Vorhersagen;
        Familie q | d — d=P liegt AUSSERHALB: arm_point verweigert dort via
        closed_form-Guard, weil die Primzahl P im Label P mod P = 0 landet).
    """
    r40 = _load_040_ratios()
    r34 = _load_034_ratios()
    problems = []
    for pt in r3_points:
        if pt["P"] in OLD_Q3_POINTS:
            ref = r40.get(pt["P"])
            if ref is None:
                problems.append(f"040 kennt P={pt['P']} nicht")
            elif abs(ref - pt["ratio_true"]) > tol:
                problems.append(f"040 P={pt['P']}: {ref} != {pt['ratio_true']}")
    for pt in r5_points:
        if pt["P"] in OLD_Q5_POINTS:
            ref = r34.get(pt["P"])
            if ref is None:
                problems.append(f"034 kennt P={pt['P']} nicht")
            elif abs(ref - pt["ratio_true"]) > tol:
                problems.append(f"034 P={pt['P']}: {ref} != {pt['ratio_true']}")
    # d-Invarianz der neuen Punkte ueber die q^k-Registerfamilie (q | d noetig;
    # d = P liegt AUSSERHALB der Familie, wenn q nicht P teilt — Wraparound)
    for P in NEW_Q3_POINTS:
        a = arm_point(P, D3_MIN, 3)
        for d in (D3_WIDE, 27):
            if abs(arm_point(P, d, 3)["ratio_true"] - a["ratio_true"]) > 1e-12:
                problems.append(f"d-Invarianz q3 P={P} d={d}")
    for P in NEW_Q5_POINTS:
        a = arm_point(P, D5_MIN, 5)
        for d in (D5_WIDE, 125):
            if abs(arm_point(P, d, 5)["ratio_true"] - a["ratio_true"]) > 1e-12:
                problems.append(f"d-Invarianz q5 P={P} d={d}")
    if problems:
        raise ValueError("Anker-Verifikation gescheitert: " + "; ".join(problems))
    return {"old_P_at_dq_vs_040": "8/8 bit-exakt (tol 1e-9)",
            "old_P_at_dq_vs_034": "5/5 bit-exakt (tol 1e-9)",
            "new_P_d_invariance": "13/13 identisch (d=q, d=q^2, d=q^3; tol 1e-12)"}


# === Kontrollen am Minimalregister ===

def uniform_control(q):
    """Negativ-Kontrolle: Uniform-State (1/sqrt(q)) sum_{a<q} |a> hat exakt
    null Nicht-DC-Masse an den Bins j*d/q => expected_share == 0 exakt."""
    return {"kind": f"uniform_q{q}", "q": q,
            "n_classes": q, "expected_share": 0.0,
            "rule": "share_ctrl_hw < kappa_hat*(1-1/S)*share_true_reg + L_q - w "
                    "(untere Prime-Bandkante)",
            "note": "Konstante q-Klasse: DFT_q verschwindet an allen Nicht-DC-Bins "
                    "(exakt, keine Arithmetik-Konstante noetig)."}


def shuffle_inert_expected(P, d, q, seed):
    """Theorem-Manifest: bei d=q ist die Label-Permutation eine Symmetrie von
    sum N^2 (Fold = Identitaet) => expected_share == share_true_reg EXAKT.
    Die Shuffle-Kontrolle wuerde IM Prime-Band liegen und ist deshalb am
    Minimalregister durch Composite + Uniform ersetzt (kein Circuit)."""
    sh = hw.shuffle_control(P, d, q, seed)
    pt = arm_point(P, d, q)
    return {"seed": seed, "expected_share": sh["expected_share"],
            "share_true_reg": pt["share_true_reg"],
            "delta": abs(sh["expected_share"] - pt["share_true_reg"])}


def composite_control(P, d, q):
    """Negativ-Kontrolle: erste m Composites mod d (034-Konvention), jetzt
    auf d = q fuer BEIDE Arme (Phase 9 nur q=5)."""
    return hw.composite_control(P, d, q)


# === Run-1-Referenz (Diagnostik-Ableitung, 0 QPU, aus committed Eval) ===

def run1_residual_stats():
    """max |res_v1| und std der run-1-v1-Residuen (Ratio_hw - center_v1).

    Eicht das Diagnostik-Band W_CROSS; die Werte kommen aus dem committed
    run-1-Eval (VOID_CALIBRATION), nicht aus einer neuen Messung.
    """
    doc = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      RUN1_EVAL)))
    res = [rec["ratio_hw"] - rec["center_v1"] for rec in doc["punkte"].values()]
    n = len(res)
    mean = sum(res) / n
    var = sum((r - mean) ** 2 for r in res) / n
    std = var ** 0.5
    two_sq2_std = 2.0 * (2.0 ** 0.5) * std
    return {"n": n, "max_abs": max(abs(r) for r in res),
            "std": std,
            "two_sqrt2_std": two_sq2_std,
            "w_cross_rule": f"|res_v1_run2 - res_v1_run1| <= W_CROSS = {W_CROSS} "
                            f"(= 2*sqrt(2)*std_run1 = {two_sq2_std:.4f}, aufgerundet)"}


# === Payload ===

def build_prereg_payload():
    q3 = [arm_point(P, D3_MIN, 3) for P in NEW_Q3_POINTS]
    q5 = [arm_point(P, D5_MIN, 5) for P in NEW_Q5_POINTS]
    diag3 = [arm_point(P, D3_MIN, 3) for P in OLD_Q3_POINTS]
    diag5 = [arm_point(P, D5_MIN, 5) for P in OLD_Q5_POINTS]
    anchor_report = verify_anchors_minimal(diag3, diag5)
    comp3 = composite_control(NEW_Q3_POINTS[0], D3_MIN, 3)
    comp5 = composite_control(NEW_Q5_POINTS[0], D5_MIN, 5)
    unif3 = uniform_control(3)
    unif5 = uniform_control(5)
    inert3 = shuffle_inert_expected(NEW_Q3_POINTS[0], D3_MIN, 3, 421)
    inert5 = shuffle_inert_expected(NEW_Q5_POINTS[0], D5_MIN, 5, 421)
    res_stats = run1_residual_stats()

    n_structure = len(NEW_Q3_POINTS) * K_REPEATS + len(NEW_Q5_POINTS) * K_REPEATS
    n_loschmidt = len(NEW_Q3_POINTS) + len(NEW_Q5_POINTS)
    n_ladder = (len(LADDER_REPEATS) - 1) * 2          # r=1 geteilt mit Anker
    n_diag_struct = len(OLD_Q3_POINTS) + len(OLD_Q5_POINTS)
    n_diag_lo = n_diag_struct
    n_controls = 4
    n_cal = 2
    total = (n_structure + n_loschmidt + n_ladder + n_diag_struct
             + n_diag_lo + n_controls + n_cal)

    payload = {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "status": STATUS,
        "registered_before": REGISTERED_BEFORE,
        "registered_by": "pt_ram_q_hardware2.freeze_prereg — payload_md5 = "
                         "md5(json.dumps(payload, sort_keys=True, separators=(',',':'))) "
                         "OHNE md5-Feld (Haus-Konvention, pt_ram_q_hardware)",
        "user_anchor": (
            "Setze genau diesen Pfad um. Option A über die bewiesene d-Invarianz ist "
            "der einzig saubere Weg, das Hardware-Design zu reparieren, ohne die "
            "Epistemik zu verbiegen. Indem wir das Register auf die minimalen "
            "Repräsentanten (q=3 auf d=3, q=5 auf d=5) verdichten, schrumpft die "
            "Echo-Tiefe drastisch. So machen wir die unverändert gefrorene Garantie "
            "kappa >= 0.81 physikalisch einlösbar, anstatt die Metrik nach einem Void "
            "rückwirkend aufzuweichen. Die Wahl neuer P-Werte ist essenziell, da die "
            "13 alten Ratios durch die ermittelte Reskalierung vorbelastet sind. Die "
            "Echo-Tiefen-Leiter liefert uns parallel dazu das gemessene "
            "Dämpfungsgesetz, was die Fehleranfälligkeit starrer Assumptions "
            "(= (1-eps)^2) eliminiert. Die Möglichkeit, die d-Invarianz über Lauf 1 "
            "und Lauf 2 hinweg hardwareseitig zu testen, ist ein massiver analytischer "
            "Bonus. Erstelle das neue Prereg-Skelett im Status REGISTERED_NOT_MEASURED. "
            "Integriere die Minimalregister, die Echo-Leiter, die neuen P-Werte und "
            "dokumentiere Option B explizit nur als nachgelagerte Fallback-Lesart. "
            "Sobald das Skelett steht und die Hashes generiert sind, können wir den "
            "Zustand vor dem neuen QPU-Kontakt absolut sauber einfrieren."),
        "layer_separation": {
            "hermeneutic_index": "M1-M5 bleiben kartografischer Index über dem Bestand "
                                 "(Branch gematria-mirror-synthesis); sie ordnen die "
                                 "dokumentierte Reihenfolge und generieren niemals Evidenz.",
            "encoding_verbot": "Die hermeneutischen Werte 1025/348/879/5683 werden NIEMALS "
                               "als Encoding-Parameter auf Quanten-Register gepresst. "
                               "Dieses Experiment codiert ausschließlich exakte "
                               "arithmetische Größen (Primzahlen, Residuen, Counts).",
            "evidence_layer": "Die Arithmetik der verrauschten Counts diktiert: share*_hw "
                              "aus den Hardware-Counts via ABSOLUT-FFT bei j*d/q (Wraparound-"
                              "Fold n_full[a::d] am Minimalregister), Ratio gegen GEFRORENE "
                              "Modell-Denominatoren (n0, m aus der wahren Arithmetik, kein "
                              "Refit).",
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
            "432d43fe1bc9e2594efd3b35266d2d81": "EXPERIMENT 042 — H-RAM-Q-3 Freeze A "
                                                "(REGISTERED_NOT_MEASURED, 58 Circuits)",
            RUN1_COUNTS_MD5_KEY: "EXPERIMENT 042 — Fez-Raw-Counts " + RUN1_JOB
                                 + " (committed VOR Auswertung)",
        },
        "phase9_verdict_context": {
            "verdict": "H-RAM-Q-3_VOID_CALIBRATION",
            "befund": "alle 13 kappa_hat < 0.81 [0.6608..0.8080], Kontrollen t3/t4/t5/t6/md5 "
                      "gruen, 0 Amplification -> kalibrierbedingt, nicht pipeline-bedingt",
            "echo_tiefen": "4q-Arm (d=9) Loschmidt 30 2q (Prep 13), 5q-Arm (d=25) 76 2q "
                           "(Prep 36) — per-2q-Survival 0.990-0.993 (4q) bzw. 0.9946-0.9951 "
                           "(5q), Readout nur 0.33-0.39 %/Qubit",
            "budget_arithmetik": "Garantie kappa >= 0.81 verlangt Echo <= ~29.7 2q (4q, KNAPP "
                                 "verfehlt: max 0.8080) bzw. <= ~38.7-42.9 2q (5q, generische "
                                 "5-Qubit-Prep sitzt am Tiefe-Optimum, unerreichbar)",
            "korrektur": "§10.25/§Z.24-Korrektur (armspezifische eps_C-Rueckrechnung, "
                         "committet): die urspruengliche gemischte Rueckrechnung (0.17 %/2q) "
                         "hatte einen q3-kappa-Wert mit der 5q-Echo-Tiefe kombiniert",
        },
        "design_decision": {
            "option_a_gewaehlt": "Minimalregister d=q via bewiesener d-Invarianz (041 T3 "
                                 "exakt): das Register ist ein INSTRUMENT, nicht die "
                                 "Hypothese — die Ratio-Vorhersagen sind d-frei, N = "
                                 "Primzahlverteilung mod q ist VOLLIG d-unabhaengig.",
            "why_not_synthese": "Der 5q-Arm muesste 76 -> <= ~38.7-42.9 2q schrumpfen; die "
                                "generische 5-Qubit-Prep sitzt nahe am Tiefe-Optimum "
                                "(~2^n CNOT) — via Synthese unerreichbar. Der 4q-Arm ist "
                                "KNAPP (29.7 vs 30 real).",
            "why_not_option_b_primaer": "per-GATE-eps ist NICHT arm-transferierbar (4q ~2x "
                                        "verlustreicher pro Gate); Latte-Verschiebungs-Optik; "
                                        "Identifikations-Spannung bei niedrigem kappa_hat. "
                                        "Option B bleibt Fallback-Lesart (siehe "
                                        "fallback_lesart_b).",
            "garantie_unveraendert": "KAPPA_CEILING = 0.81 bleibt EXAKT gefroren — die "
                                     "Garantie wird physikalisch einloesbar gemacht, nicht "
                                     "metrisch aufgeweicht (User-Direktive).",
        },
        "frozen_theorems": {
            "B2_q_universal_identity": "share* = (m - q*n0)^2/((q-1)*d*m) + q*sigma^2/(d*m) "
                                       "für ALLE Count-Vektoren inkl. Wraparound (041, "
                                       "CONFIRMED B)",
            "d_invariance": "d*m*share* haengt nur von den mod-q gefalteten Counts ab "
                            "(041 T3 exakt, k=1 Eingeschlossen) -> die Minimalregister "
                            "d=3/d=5 tragen die IDENTISCHEN Ratio-Vorhersagen wie d=9/25/729/625",
            "ratio_forms": {
                "q3": "ratio_true = 1 + 12*delta^2/(m-3)^2",
                "q5": "ratio_true = 1 + 20*sigma^2/(m-5)^2",
                "general": "ratio_true = (q-1)*(q*sum_r N_r^2 - m^2)/(m - q*n0)^2",
            },
            "shuffle_inertness_at_dq": "Bei d=q ist der Fold die Identitaet; eine "
                                       "Label-Permutation permutiert N und laesst sum N^2 "
                                       "invariant => expected_share(Shuffle) == "
                                       "share_true_reg EXAKT. Die Phase-9-Shuffle-Kontrolle "
                                       "ist am Minimalregister strukturell inert (wuerde IM "
                                       "Prime-Band liegen) und wird durch Composite- + "
                                       "Uniform-Null-Kontrollen ersetzt.",
        },
        "operational_definitions": {
            "state": "|psi(P,d)> = sum_a sqrt(n_a/m)|a> mit n_a = #{p <= P prim : "
                     "p ≡ a mod d}; am Minimalregister d=q direkt die q Residuenklassen "
                     "(q=3: 3 Labels von 4 auf 2 Qubits, Label 3 ideal leer; "
                     "q=5: 5 Labels von 8 auf 3 Qubits, Labels 5..7 ideal leer).",
            "hw_counts": "n_hat = m*c/S auf dem 2^n-Label-Vektor, dann Wraparound-Fold "
                         "n_d[a] = sum n_full[a::d] (Idle-Labels fallen via a mod d in "
                         "echte Klassen); unter Depolarisierung erhaelt die Uniform-Masse "
                         "m exakt: sum n_hat = m.",
            "share_hw": "share*_hw = sum_{j=1}^{q-1} |DFT_d(n_hat)[j*d/q]|^2/(d*m), "
                        "ABSOLUT-FFT-Konvention (Haus-Lektion, kein Vorzeichen-Mix).",
            "ratio_hw": "share*_hw / model_share_reg mit model_share_reg = "
                        "(m - q*n0_true)^2/((q-1)*d*m) GEFROREN auf wahre Arithmetik-Werte.",
            "kappa": "kappa_p = P_L/P_ro_ref. P_L: gepaarter Loschmidt-Circuit "
                     "(State-Prep + exakte Inverse, gleiche Tiefe), P(0^n); P_ro_ref: "
                     "Readout-Kalibrier-Circuit |0>^n im SELBEN Job. kappa ~= (1-eps_C)^2 "
                     "ist exakt der Daempfungsfaktor der kohaerenten Struktur — gemessen, "
                     "nicht gefittet.",
            "idle_labels": "Am Minimalregister sind 1/4 (q3, d=3: Label 3) bzw. 3/8 "
                           "(q5, d=5: Labels 5..7) Labels ideal leer; ihre Leakage-Masse "
                           "faellt via Wraparound-Fold in echte Klassen (Label a faellt "
                           "in Klasse a mod d). Stage-2-Form-Validierung am ECHTEN Fold "
                           "prueft das VOR Hardware; der kappa-Kanal (P(0^n)) ist davon "
                           "unabhaengig.",
        },
        "prediction_freeze": {
            "classical_core": {
                "q3": "ratio_true = 1 + 12*delta^2/(m-3)^2 — die User-Headline",
                "q5": "ratio_true = 1 + 20*sigma^2/(m-5)^2",
                "verdict_in_040_034": "8/8 und 5/5 gated Punkte im Band [0.8, 1.25]",
            },
            "p_rule": {
                "rule": "P_neu = kleinste Primzahl p mit p > P_alt + 30 (je alter Punkt, "
                        "deterministisch, VOR jeder Messung berechnet)",
                "motivation": "Die 13 alten Ratios sind durch die ermittelte Reskalierung "
                              "vorbelastet (Anti-Sharpshooter); neue P nie gemessen.",
                "old_q3": OLD_Q3_POINTS,
                "old_q5": OLD_Q5_POINTS,
                "new_q3": NEW_Q3_POINTS,
                "new_q5": NEW_Q5_POINTS,
            },
            "noise_law": {
                "ratio_hw": "ratio_hw = kappa*(1 - 1/S)*ratio_true + L_q (UNVERAENDERT "
                            "aus Freeze A/042)",
                "L_q": "L_q = (q-1)^2*m^2/(S*(m-q*n0)^2) — exakte multinomiale Erwartung; "
                       "der Lift ist UNTER dem Shot-Noise und wird im Zentrum registriert, "
                       "nicht als separierbar behauptet",
                "suppression": "kappa = P_L/P_ro_ref daempft die kohaerente Struktur; bei "
                               "Echo ~2-6 2q (q3) bzw. ~8-12 2q (q5) ist kappa_hat ~ "
                               "0.94-0.98 bzw. ~0.93-0.96 erwartet (aus per-2q-Survival "
                               "0.990-0.993 / 0.9946-0.9951 mal Echo-Tiefe abgeleitet; "
                               "exakte Tiefe erst im Freeze-B'-ISA-Report) — beide oberhalb "
                               "der unverändert gefrorenen Garantie 0.81 mit Marge",
                "honesty": "Das Gesetz koppelt zwei operationell unabhaengige Messungen "
                           "(Loschmidt-Survival und Harmonischen-Share); Verletzung der "
                           "Kopplung = Falsifikation via Band.",
            },
            "points": {"q3_d3": q3, "q5_d5": q5},
            "anchor_verification": anchor_report,
        },
        "echo_ladder": {
            "purpose": "GEMESSENES Daempfungsgesetz statt starrer (1-eps)^2-Annahme: "
                       "r-fache (Prep + exakte Inverse)-Bloecke, r in " +
                       str(list(LADDER_REPEATS)) + ", je Arm am Ankerpunkt; log kappa_r "
                       "vs r (LSQ) liefert per-Block-Survival und die Kalibrier-Konstanten "
                       "fuer den Fallback-B-Pfad.",
            "repeats": list(LADDER_REPEATS),
            "anchors": {"q3": LADDER_ANCHORS["q3"], "q5": LADDER_ANCHORS["q5"]},
            "r1_shared": "r=1 ist EXAKT der gepaarte Loschmidt-Circuit des Ankerpunkts "
                         "(geteilt, kein doppeltes Circuit) — Konsistenz kappa_ladder(r=1) "
                         "== kappa_hat(Anker) per Konstruktion.",
            "barriers": "Barrier zwischen allen Bloecken (Transpiler-Kuerzung verboten, "
                        "Phase-9-Konvention).",
            "erwartungsbereich_diagnostisch": "aus der §10.25/§Z.24-Korrektur abgeleitet "
                                              "(NICHT verdict-tragend): q3 per-2q-Survival "
                                              "0.990-0.993, Block-Tiefe ~2-6 2q => kappa_block "
                                              "~0.94-0.98; q5 per-2q-Survival 0.9946-0.9951, "
                                              "Block-Tiefe ~8-12 2q => kappa_block ~0.93-0.96 "
                                              "(exakte Tiefen erst im Freeze-B'-ISA-Report)",
            "verdict_role": "Kalibrier-Diagnostik: liefert das gemessene Daempfungsgesetz "
                            "kappa(Tiefe) fuer Fallback-B und die Tiefenkonsistenz; das "
                            "Verdict bleibt an die per-Punkt kappa-Paarung gekoppelt.",
        },
        "hardware_parameters": {
            "backend": "ibm_fez",
            "token": "TOKEN1 (IBMQ_TOKEN); TOKEN2 unberuehrt",
            "n_shots": SHOTS,
            "register_topology": {
                "q3_d3": {"d": D3_MIN, "n_qubits": NQ3, "labels": 2 ** NQ3,
                          "real_labels": 3, "idle_labels": 2 ** NQ3 - 3,
                          "note": "Minimalrepraesentant: d=q=3; Amplituden sqrt(n_a/m) "
                                  "auf 3 Labels, Label 3 ideal leer (Wraparound-Fold: "
                                  "Label a faellt in Klasse a mod 3)"},
                "q5_d5": {"d": D5_MIN, "n_qubits": NQ5, "labels": 2 ** NQ5,
                          "real_labels": 5, "idle_labels": 3,
                          "note": "Minimalrepraesentant: d=q=5; Amplituden sqrt(n_a/m) "
                                  "auf 5 Labels, Labels 5..7 ideal leer"},
            },
            "state_prep": "Qiskit StatePreparation aus den gefrorenen n_d-Vektoren; "
                          "Loschmidt = Prep + exakte Inverse (gleiche Gate-Menge); "
                          "Leiter = r Bloecke mit Barrieren.",
            "circuit_budget": {
                "structure": n_structure,
                "loschmidt": n_loschmidt,
                "echo_ladder": n_ladder,
                "diagnostik_structure": n_diag_struct,
                "diagnostik_loschmidt": n_diag_lo,
                "negative_controls": n_controls,
                "readout_cal": n_cal,
                "total": total,
                "total_shots": total * SHOTS,
                "jobs": 1,
            },
            "run_config": {"optimization_level": 3, "dynamical_decoupling": "XX",
                           "resilience": "none (raw SamplerV2 counts)"},
            "isa_ceilings": {
                "per_circuit_2q_max": ISA_2Q_PER_CIRCUIT_MAX,
                "total_2q_max": ISA_2Q_TOTAL_MAX,
                "erwartung": "max ~96 2q (Leiter r=8, q5) je Circuit, total ~500-1100 2q "
                             "(Prognose); die echten Werte werden in Freeze B' am "
                             "ISA-Report registriert",
                "measured_when": "Stage-2-Transpilation VOR Hardware; Backend-Target-Laden "
                                 "= kein Quota-Kontakt (kein Job), §Z.14-Phase-3b-Praezedenz",
                "abort": "Ceiling-Überschreitung vor dem QPU-Lauf -> Abbruch, Re-Freeze",
            },
        },
        "simulation_leg": {
            "purpose": "0 QPU: Validierung der Daempfungsform auf dem gefrorenen "
                       "STRESS-Modell am Minimalregister VOR Hardware (inkl. "
                       "Wraparound-Fold der Idle-Labels); Freeze-B'-Bandbreiten.",
            "stress_model": "pt_ram_q_hardware_aer.build_noise_model-Präzedenz "
                            "(depolarizing p1 auf 1q-Gates, ratio*p1 auf cz, "
                            "ReadoutError ro=1e-2) — NICHT kalibriert, konservativ.",
            "stress_grid_p1": STRESS_GRID_P1,
            "n_ens": N_ENS,
            "form_validation": "RE-FREEZE R1 (dokumentiert, VOR jedem QPU-Kontakt): "
                               "TOL_FORM = 0.03 vergleicht das DETERMINISTISCHE Zentrum "
                               "(exact-Bein = die registrierten 13 Punkte x 6 Stresslevel): "
                               "max |res_v2| <= 0.03 ueber die Domain-Zellen (kappa >= 0.81) "
                               "des exact-Beins. Das sampled-Bein wird noise-aware geprueft: "
                               "w_B' = q97.5 der |res_v2| ueber die Domain-Zellen "
                               "<= W_A = 0.05 (freeze_b'); der per-Zell-Max des sampled-Beins "
                               "ist registrierte Diagnostik (Estimator-Rauschen), KEIN Gate. "
                               "Verletzung eines der beiden Gates -> Re-Freeze-Zyklus "
                               "(dokumentiert, Hardware blockiert) — v1->v2-Disziplin "
                               "(H-STAR-5-/Phase-9-Praezedenz).",
            "re_freeze_r1": {
                "old_md5": "5b91119b925ae365bcd0618a2a15fa30",
                "trigger": "Stage-2b-Aer-Erstlauf (0 QPU): das v2-Form-Gate scheiterte am "
                           "per-Zell-Max des sampled-Beins (0.0396 > TOL_FORM = 0.03); "
                           "exact-Bein max 0.0022 (q5) / 0.0009 (q3), sampled q97.5 = 0.0279 "
                           "<= W_A. Diagnose: Estimator-Rauschen (std 0.0117; max = 3.4 sigma "
                           "bei 480 domain-sampled-Zellen), KEIN Zentrum-Defizit — TOL_FORM "
                           "= 0.03 liegt am Minimalregister unterhalb der eigenen "
                           "Rauschskala (share-Quadratform-Rauschen, d = 3/5).",
                "measured": "0 QPU-Kontakt, keine Hardware-Messung. Freeze A' Register "
                            "(Minimalregister, 13 neue P, Echo-Leiter, Budget 90, alle "
                            "gefrorenen Konstanten) UNVERAENDERT.",
                "rule": "Nur die Form-Gate-Lesart wird praezisiert (Rausch-Gate fuer das "
                        "sampled-Bein via bereits gefrorenem w_B'-q97.5). Kein "
                        "Zentrum-Weakening, kein Metrik-Weakening: das exact-Bein-Gate "
                        "ist SCHAERFER, weil es das deterministische Zentrum ALLEIN "
                        "prueft (Phase-9-Wert 0.0276 war ein sampled-Max).",
            },
            "freeze_b": "w_B = max(W_B_FLOOR, q97.5-Halbbreite der Ensemble-Residuen über "
                        "alle Punkte x Stresslevel), w_B <= W_A = 0.05, sonst Re-Freeze; "
                        "Zentrum c(kappa) bleibt GEFROREN (kein Aer-Re-Zentrieren).",
        },
        "diagnostik_bein": {
            "purpose": "Hardware-d-Invarianz ÜBER DIE LÄUFE (User: massiver analytischer "
                       "Bonus): die 13 alten P werden am Minimalregister d=q NEU gemessen "
                       "(nie bei diesen Registern gemessen => Messung nicht vorbelastet) "
                       "und gegen das committed run-1-Eval (" + RUN1_EVAL + ", Job "
                       + RUN1_JOB + ") verglichen.",
            "points": {"q3_d3": diag3, "q5_d5": diag5},
            "reps": 1,
            "loschmidt_gepaart": True,
            "verdict_role": "NICHT verdict-tragend; Re-Freeze-Trigger-Analyse nur.",
            "rule": "res_v1(P, d=q, run 2) - res_v1(P, d=q^k, run 1) mit "
                    "res_v1 = ratio_hw - [kappa_hat*(1-1/S)*ratio_true + L_q] "
                    "(Zentrum UNVERAENDERT); |Delta res| <= W_CROSS = 0.09 => "
                    "HARDWARE-D_INVARIANZ_KONSISTENT, sonst "
                    "HARDWARE-D_INVARIANZ_VERLETZT (dokumentierte Analyse).",
            "w_cross_derivation": res_stats,
            "leckage_dokumentiert": "Die run-1-Ratios sind als Zahlen bekannt (durch die "
                                    "Reskalierungs-Analyse); die d=q-MESSUNGEN dieser P "
                                    "sind nie gemacht worden. Das VERDICT nutzt ausschliesslich "
                                    "die 13 NEUEN P — die alten P tragen nur dieses "
                                    "Diagnostik-Bein.",
        },
        "safeguard_limits": {
            "band_rule": "ratio_hw ∈ [c(kappa_hat) - w, c(kappa_hat) + w]; Freeze A': "
                         "w_A = 0.05; Freeze B' darf nur VERENGEN (w_B <= w_A); das "
                         "Zentrum c(kappa_hat) = kappa_hat*(1-1/S)*ratio_true + L_q "
                         "bleibt gefroren.",
            "amplification_ceiling": "ratio_hw > (1-1/S)*ratio_true + L_q + w -> "
                                     "H-RAM-Q-3b_INVALID_AMPLIFICATION (einseitig: "
                                     "Depolarisierung daempft Prime-Harmonische, hebt sie "
                                     "nie über das rauschfreie Niveau + Band)",
            "kappa_floor_void": "kappa_hat_p < KAPPA_CEILING = 0.81 -> Punkt EXKLUDIERT "
                                "(VOID_CALIBRATION); >= 2 exkludierte Punkte -> "
                                "H-RAM-Q-3b_VOID_CALIBRATION_GLOBAL. UNVERAENDERT gefrorene "
                                "Garantie — physikalisch einloesbar durch das "
                                "Minimalregister, nicht metrisch aufgeweicht.",
            "falsifier": ">= 2 der 13 Punkte UNTERHALB c(kappa_hat) - w -> "
                         "H-RAM-Q-3b_REFUTED",
            "trennschaerfe": {
                "band_vs_shot_noise": "gepoolte K=3-Ratio-SE ≈ 1.4-2.0% (S=8192) gegen "
                                      "w_A = 5% -> >= 2.5σ Auflösung",
                "kappa_se": "SE(kappa_hat) ≈ 0.005 (Loschmidt, 8192 Shots) -> "
                            "SE(Zentrum) ≈ 0.005 << w",
                "coupling": "kappa_hat (Loschmidt) und share-Ratio (Harmonische) sind "
                            "operationell UNABHÄNGIG; das gefrorene Gesetz koppelt sie.",
            },
            "job_integrity": "EIN Fez-Job (TOKEN1), " + str(total) + " Circuits; Job-ID + "
                             "md5 der Counts committed VOR der Auswertung (§Z.14-Disziplin).",
        },
        "controls": {
            "t1_backcompat_minimal": anchor_report,
            "t2_v2_anchors": "034-Prime-Anker (625,625) = 0.04272280701754398 über die "
                             "d=625-Kette unberührt — klassisch, kein QPU-Kontakt.",
            "t3_identity_two_ways": "share*_hw = sum_j |G_j|^2/(d*m) auf den HW-Counts "
                                    "zwei Wege (FFT bei j*d/q vs gefaltete Formel "
                                    "(q*sum N_hat^2 - m_hat^2)/(d*m)), exakt 1e-12 "
                                    "(041-Theorem); Verletzung -> EVALUATION_INVALID.",
            "t4_negative_must_not_fire": {
                "composite_q3": comp3,
                "composite_q5": comp5,
                "uniform_q3": unif3,
                "uniform_q5": unif5,
                "rule": "share_ctrl_hw < kappa_hat*(1-1/S)*share_true_reg + L_q - w "
                        "(untere Prime-Bandkante, konservativste Ecke kappa = "
                        "KAPPA_CEILING, w = W_A); Verletzung -> H-RAM-Q-3b_DEGENERAT "
                        "(REFUTED-zulaessig, Degenerat-Lektion)",
            },
            "t4b_shuffle_inert_theorem": {
                "q3_seed421": inert3,
                "q5_seed421": inert5,
                "statement": "Kein Shuffle-Circuit am Minimalregister: expected_share "
                             "== share_true_reg EXAKT (Theorem, frozen_theorems."
                             "shuffle_inertness_at_dq); die Kontrolle wuerde IM Band "
                             "liegen und kann nicht must-not-fire.",
            },
            "t5_gate_set_frozen": "13 VERDICT-Punkte = exakt die 13 P nach registrierter "
                                  "Regel (kleinste Primzahl > P_alt + 30); die 13 alten P "
                                  "nur Diagnostik-Bein; keine nachträglichen Ergänzungen.",
            "t6_mass_conservation": "sum_r N_hat_r = m_hat unter Depolarisierung "
                                    "(Uniform-Masse erhält m exakt); Verletzung -> "
                                    "EVALUATION_INVALID.",
        },
        "verdict_map": {
            "H-RAM-Q-3b_NOISE_LIFT_CONFIRMED": "alle 13 Punkte im Band "
                                               "[c(kappa_hat)-w_B, c(kappa_hat)+w_B], "
                                               "Kontrollen gruen, alle kappa_hat >= 0.81",
            "H-RAM-Q-3b_COARSE_HOLD_SHARP_MISS": "alle Punkte im groben Band (w_A), "
                                                 ">= 1 Punkt außerhalb w_B",
            "H-RAM-Q-3b_REFUTED": ">= 2 Punkte unter c(kappa_hat) - w",
            "H-RAM-Q-3b_INVALID_AMPLIFICATION": "irgendein Punkt über "
                                                "(1-1/S)*ratio_true + L_q + w",
            "H-RAM-Q-3b_VOID_CALIBRATION": "kappa_hat < 0.81 an >= 2 Punkten",
            "H-RAM-Q-3b_DEGENERAT": "Kontroll-Regel T4 verletzt (Prime-Share auf "
                                    "Kontroll-Niveau) — REFUTED-zulaessig",
            "EVALUATION_INVALID_KONTROLLE_GESCHEITERT": "T1-T6 gescheitert — Auswertung void",
        },
        "fallback_lesart_b": {
            "status": "REGISTRIERT, NUR-NACHGELAGERT, NIE stiller Patch",
            "trigger": "AUSLÖSUNG NUR FALLS kappa_hat trotz Minimalregister < 0.81 an "
                       ">= 2 Punkten (VOID trotz Echo-Verkürzung) — sonst nie.",
            "mechanism": "Separat gefrorenes NEUES Prereg: Resolutionsanalyse + "
                         "Kalibrier-Konstanten aus der Echo-Leiter (gemessenes "
                         "Daempfungsgesetz) — die Dämpfung geht als expliziter, "
                         "gemessener Fehlerterm ins Zentrum (v2-Form-Präzedenz aus "
                         "Phase 9 Freeze B), NIE als nachträgliche Metrik-Aufweichung.",
            "anti_option_b_evidenz": "per-GATE-eps nicht arm-transferierbar (4q ~2x "
                                     "verlustreicher); Latte-Verschiebungs-Optik; "
                                     "Identifikations-Spannung bei niedrigem kappa_hat.",
            "primär_pfad": "Option A (dieser Freeze): die Garantie 0.81 bleibt UNVERÄNDERT "
                           "gefroren und wird am Minimalregister physikalisch eingelöst.",
        },
        "two_freeze_architecture": {
            "freeze_a": "DIESER Freeze (A'): analytischer Kern + alle 13 neuen "
                        "Punkt-Konstanten + Echo-Leiter + Diagnostik-Regeln + md5, VOR "
                        "jedem Hardware-/Simulations-Kontakt, 0 QPU.",
            "stage2_aer": "Aer-Bein (0 QPU) am Minimalregister mit gefrorenem "
                          "STRESS-Modell: Form-Validierung (inkl. Wraparound-Fold) + "
                          "w_B + ISA-Report.",
            "freeze_b": "w_B-Registrierung (<= w_A) + ISA-Report VOR dem QPU-Lauf; "
                        "Zentrum unverändert; erst danach QPU-Kontakt.",
            "hardware": "EIN Fez-Job (TOKEN1) erst nach Freeze-B'-Commit; alle "
                        "Abbruchbedingungen exakt in safeguard_limits registriert.",
        },
        "anti_sharpshooter": {
            "no_ex_post_fit": "Die 13 VERDICT-Punkte sind nach registrierter Regel "
                              "(kleinste Primzahl > P_alt + 30) VOR dem Freeze "
                              "berechnet — nie gemessen, keine Vorbelastung. Die "
                              "Kontroll-Erwartungen sind modell-abgeleitet (0 QPU).",
            "registered_alternative_models": "keine — die Dämpfungsform folgt aus "
                                             "Depolarisierung; die Echo-Leiter MISST das "
                                             "Gesetz (ersetzt die starre (1-eps)^2-"
                                             "Annahme); die Stage-2-Form-Validierung "
                                             "prüft es VOR Hardware.",
            "negative_predictions": "Composite- (beide Arme) und Uniform-Kontrollen mit "
                                    "exakten Erwartungen registriert (T4); Shuffle-Inertness "
                                    "als Theorem dokumentiert (T4b); der Sampling-Lift L_q "
                                    "ist unter dem Shot-Noise und wird NICHT als "
                                    "separierbar behauptet (Ehrlichkeit).",
        },
        "qpu": "0 QPU (Freeze A'); Stage-2 Aer 0 QPU; EIN Fez-Job (TOKEN1) erst nach "
               "Freeze B'",
        "suite_state": 831,
        "future_phase_numbering": {
            "synthesis": "§Z.25 (SYNTHESIS)",
            "log": "§10.26 (RIEMANN) — §Z.23/§10.24 Gematria-Layer, §Z.24/§10.25 Phase 9",
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
        raise ValueError(f"H-RAM-Q-3b-Prereg-md5-MISMATCH in {path}")
    return doc