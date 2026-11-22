# -*- coding: utf-8 -*-
"""EXPERIMENT 044 — H-RAM-Q-4: kohärentes Prep-Fehler-Gesetz v3 (Freeze A").

Freeze-A''-Prereg, Status REGISTERED_NOT_MEASURED, 0 QPU.

Kette:
    034 (q=5 Fingerprint, md5 a2fc4875) -> 040 (H-RAM-Q-1 q=3, md5 bd9dfee7)
    -> 041 (H-RAM-Q-2 q-universelle Identitaet, md5 704916f9)
    -> 032 (§Z.14 Fez-QPU-Praezedenz, md5 18fb1e62)
    -> 042 (H-RAM-Q-3, Freeze-A md5 432d43fe, Run-1-Raw d19f4a56)
    -> 043 (H-RAM-Q-3b, Freeze-A' md5 0b9c9968, Run-2-Raw 16ca44bd,
            Verdict REFUTED)
    -> Phase 11a (Diagnostik-Modul, Results-md5 8ad3adbb19568bc9f7db81142d3e1c0a)
    -> DIESER Freeze (A'').

Phase-10d-Befund (H-RAM-Q-3b_REFUTED): die Kalibrier-Ziele waren eingelöst
(alle 13 kappa_hat >= 0.81 am Minimalregister), aber 13/13 Punkte unter
c(kappa)-w_B' EINSEITIG, und auch die Aer-kalibrierte v2-Form verfehlt
(res_v2 alle negativ, max 0.0630 > w_B' 0.02787). Die Phase-11a-Diagnostik
gegen das committete Raw zerlegt die Einweg-Suppression

    delta(P) = ratio_ro_exact(pt, ro_hat) - ratio_hw(P)

in zwei Ternme:

    delta ~ b_P*(1 - kappa_hat)   [stochastisch, Aer-Form, v2-Teil]
          + gamma_arm * cP        [kohearenter Prep-Fehler-Floor]

mit den Befunden:
    B1  q3: corr(1-kappa_hat, delta) = -0.047 ~ 0 — die Suppression ist NICHT
        kappa-skaliert (der Loschmidt-Echo refokussiert kohärente/unäre
        Prep-Fehler, kappa_hat misst die Echo-Tiefe, nicht die Struktur).
    B2  res_v2 alle negativ: die Aer-Steigung b_P*(1-kappa_hat) ueberschaetzt
        die hardware-Suppression.
    B3  Das kohärente Share-Gradient-Gesetz delta = gamma*cP (worst-case
        Empfindlichkeit des ABS-FFT-Shares gegen eine unit-norm kohärente
        Amplituden-Stoerung, klassisch EXAKT) hat arm-stabile gamma.
    B4  TRANSFER-TEST: Kalibrier auf den 13 alten P, Test auf den 13 neuen P
        haette mit v3 das REFUTED vermieden (max|res| q3 0.0152 / q5 0.0197
        < w_B' 0.02787).
    B5  Das q5|541-Anomal ist register-/session-spezifisch (run-1 d=25
        res_v1 +0.0248 POSITIV vs run-2 d=5 -0.1453).

Design-Entscheidung (dieser Freeze):
  v3b = gefrorenes v2-Gesetz + gamma_arm*cP:
      center_v3 = (1-1/S)*(ratio_ro_exact(pt, ro_hat) + b_P*(kappa_hat-1)
                            - gamma_arm*cP) + L_q
  - v3a (rein kohärent, ohne kappa-Term) wird VERWORFEN: sie reduziert auf
    Aer NICHT auf das gefrorene v2 (das die Form-Gates E/S PASSTE) und
    scheitert dort bei p1 >= 1e-3 (b_P*(1-kappa_hat) ~ -0.075 >> TOL_FORM).
    v3b reduziert sich auf Aer exakt auf v2 (gamma_Aer ~ 0), ist also
    robust unter beiden Wahrheiten (rein-kohaerent: der in-job gamma-Fit
    absorbiert das Kalibrier-Mittel von b_P*(1-kappa_hat); stochastisch-
    vorhanden: v3b traegt es direkt).
  - gamma_arm wird IN-JOB per LSQ-durch-Null auf dem KALIBRIER-BEIN gefittet
    (die 13 Run-2-Verdict-P, frisch gemessen mit 3 Reps + gepaartem
    Loschmidt); die 13 NEUEN P sind Holdout. Kein Run-1-P wird wiederverwendet
    (541/463/625-Anomalien).
  - w_B'' = w_B' = 0.02787029633307472 WIEDERVERWENDET (committete
    Phase-10b-Konstante, pt_ram_q_stage2b_results.json w_b): gleiche
    Apparatus-Konvention, Transfer-Erwartung liegt mit Marge innen.

P-Regel (amendiert, registriert-deterministisch, vor jeder Messung):
    P_neu = kleinste Primzahl p mit p > P_alt + 30 UND
            p NICHT in der gemessenen Vereinigung
            (alle P, die in irgendeinem vorherigen Lauf IRGENDEINES Arms
             dieses Experiments gemessen wurden).

Echo-Leiter: UNVERAENDERT aus Phase 10 (r in {1,2,4,8}, Anker jetzt die
neuen Punkte q3->181 / q5->467).

Kontrollen: UNVERAENDERT (Composite- + Uniform-Null-Kontrollen beider Arme,
Shuffle-Inertness-Theorem am Minimalregister).
"""

import hashlib
import json
import os

import pt_ram_q_hardware as hw
import pt_ram_q_hardware2 as hw2
import pt_ram_q_hardware2_aer as s2b
import pt_ram_q_hardware3_diag as dg
from pt_ram_q_hardware_aer import nq_of, ratio_ro_exact

EXPERIMENT = "044-ram-q-coherent-prep-error"
HYPOTHESIS = "H-RAM-Q-4"
STATUS = "REGISTERED_NOT_MEASURED"
REGISTERED_BEFORE = "2026-09-26"
PREREG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "pt_ram_q_hardware3_prereg.json")

# Gefrorene Konstanten — UNVERAENDERT aus Phase 9/10 (md5 432d43fe)
SHOTS = hw.SHOTS                    # 8192
K_REPEATS = hw.K_REPEATS            # 3
W_A = hw.W_A                        # 0.05 (Freeze B'' darf nur verengen)
KAPPA_CEILING = hw.KAPPA_CEILING    # 0.81 (unveraendert gefrorene Garantie)
TOL_FORM = hw.TOL_FORM              # 0.03
W_B_FLOOR = hw.W_B_FLOOR            # 0.01
ISA_2Q_PER_CIRCUIT_MAX = hw.ISA_2Q_PER_CIRCUIT_MAX   # 120
ISA_2Q_TOTAL_MAX = hw.ISA_2Q_TOTAL_MAX               # 6000
STRESS_GRID_P1 = hw.STRESS_GRID_P1
N_ENS = hw.N_ENS

# Register: Minimalrepraesentanten (d = q) — UNVERAENDERT aus Phase 10
D3_MIN = hw2.D3_MIN                 # 3
D5_MIN = hw2.D5_MIN                 # 5
NQ3 = hw2.NQ3                       # 2
NQ5 = hw2.NQ5                       # 3
D3_WIDE = hw2.D3_WIDE               # 9
D5_WIDE = hw2.D5_WIDE               # 25

# KALIBRIER-BEIN = die 13 Run-2-Verdict-P (frisch gemessen in Run 3;
# ihre Run-2-Messung wird NICHT wiederverwendet)
CAL_Q3_POINTS = list(hw2.NEW_Q3_POINTS)   # [149,197,251,347,433,577,659,761]
CAL_Q5_POINTS = list(hw2.NEW_Q5_POINTS)   # [433,499,577,631,659]

# Gemessene Vereinigung: alle P aus irgendeinem vorherigen Lauf irgendeines
# Arms (Run-1 q3/q5 + Run-2 Verdict q3/q5). Global ueber Arme — die
# staerkste Anti-Wiederverwendungs-Lesart; die registrierten neuen P-Sets
# sind unter per-Arm- und globaler Lesart identisch (kein Fall unterscheidet
# sie, dokumentiert im Payload).
MEASURED_UNION = set(hw.Q3_POINTS) | set(hw.Q5_POINTS) \
    | set(CAL_Q3_POINTS) | set(CAL_Q5_POINTS)

# Run-1-P (durch Reskalierung vorbelastet, 541/463/625-Anomalien): NIE
# wiederverwendet — weder Verdict noch Kalibrier.
RUN1_Q3_POINTS = list(hw.Q3_POINTS)
RUN1_Q5_POINTS = list(hw.Q5_POINTS)

LADDER_REPEATS = hw2.LADDER_REPEATS  # (1, 2, 4, 8)

RUN2_EVAL = "pt_ram_q_hardware2_eval.json"
RUN2_COUNTS_MD5 = RUN2_COUNTS_MD5_KEY = "16ca44bd02f81cf623862b4910ccedf8"
RUN2_JOB = "dartdg5vr3kc73ejcrgg"
RUN3_PREREG_MD5_043 = "0b9c9968dc5e99a3cc22962a8b760e44"
DIAG_RESULTS = "pt_ram_q_hardware3_diag_results.json"
DIAG_RESULTS_MD5 = "8ad3adbb19568bc9f7db81142d3e1c0a"

# w_B'' = w_B' (committete Phase-10b-Konstante, WIEDERVERWENDET)
W_B_PRIME = 0.02787029633307472
W_B_PRIME_SOURCE = "pt_ram_q_stage2b_results.json w_b (EXPERIMENT 043, " \
                   "Phase-10b-Konvention q97.5 des sampled-Beins)"


def smallest_prime_above(x):
    """Kleinste Primzahl p mit p > x (Phase-10-Konvention, strikt groesser)."""
    return hw2.smallest_prime_above(x)


def new_points_run3(cal_points, measured_union=None):
    """Amendierte P-Regel (dieser Freeze):
    P_neu = kleinste Primzahl p mit p > P_alt + 30 UND
            p nicht in der gemessenen Vereinigung.
    Deterministisch aus committeten Daten; VOR jeder Messung berechnet."""
    if measured_union is None:
        measured_union = MEASURED_UNION
    out = []
    for P in cal_points:
        cand = smallest_prime_above(P + 30)
        while cand in measured_union:
            cand = smallest_prime_above(cand)
        out.append(cand)
    return out


NEW_Q3_POINTS = new_points_run3(CAL_Q3_POINTS)   # [181,229,283,379,467,613,691,797]
NEW_Q5_POINTS = new_points_run3(CAL_Q5_POINTS)   # [467,547,613,673,691]
LADDER_ANCHORS = {"q3": NEW_Q3_POINTS[0], "q5": NEW_Q5_POINTS[0]}


# === exakte Arithmetik (gefrorener Kern, Wiederverwendung aus 042) ===

def arm_point(P, d, q):
    """Exakte Konstanten eines Punkts (042-Kern, d-frei per 041-T3)."""
    return hw.arm_point(P, d, q)


def _load_040_ratios():
    return hw._load_040_ratios()


def _load_034_ratios():
    return hw._load_034_ratios()


def verify_anchors_run3(tol=1e-9):
    """T1'': Anker-Verifikation am Minimalregister (drei Schichten).

    (a) Run-1-Regression: alle 8 alten q3-P auf d=3 == 040-Ratio (tol 1e-9),
        alle 5 alten q5-P auf d=5 == 034-Ratio — der Kern arm_point ist
        unberuehrt.
    (b) d-Invarianz der 13 KALIBRIER-P ueber die q^k-Familie (d=q, q^2, q^3).
    (c) d-Invarianz der 13 NEUEN Verdict-P ueber dieselbe Familie.
    (d=P liegt weiterhin AUSSERHALB: arm_point verweigert via
     closed_form-Guard, weil P im Label P mod P = 0 landet.)
    """
    r40 = _load_040_ratios()
    r34 = _load_034_ratios()
    problems = []
    for P in RUN1_Q3_POINTS:
        ref = r40.get(P)
        a = arm_point(P, D3_MIN, 3)["ratio_true"]
        if ref is None:
            problems.append(f"040 kennt P={P} nicht")
        elif abs(ref - a) > tol:
            problems.append(f"040 P={P}: {ref} != {a}")
    for P in RUN1_Q5_POINTS:
        ref = r34.get(P)
        a = arm_point(P, D5_MIN, 5)["ratio_true"]
        if ref is None:
            problems.append(f"034 kennt P={P} nicht")
        elif abs(ref - a) > tol:
            problems.append(f"034 P={P}: {ref} != {a}")
    for P in CAL_Q3_POINTS:
        a = arm_point(P, D3_MIN, 3)["ratio_true"]
        for d in (D3_WIDE, 27):
            if abs(arm_point(P, d, 3)["ratio_true"] - a) > 1e-12:
                problems.append(f"d-Invarianz cal q3 P={P} d={d}")
    for P in CAL_Q5_POINTS:
        a = arm_point(P, D5_MIN, 5)["ratio_true"]
        for d in (D5_WIDE, 125):
            if abs(arm_point(P, d, 5)["ratio_true"] - a) > 1e-12:
                problems.append(f"d-Invarianz cal q5 P={P} d={d}")
    for P in NEW_Q3_POINTS:
        a = arm_point(P, D3_MIN, 3)["ratio_true"]
        for d in (D3_WIDE, 27):
            if abs(arm_point(P, d, 3)["ratio_true"] - a) > 1e-12:
                problems.append(f"d-Invarianz neu q3 P={P} d={d}")
    for P in NEW_Q5_POINTS:
        a = arm_point(P, D5_MIN, 5)["ratio_true"]
        for d in (D5_WIDE, 125):
            if abs(arm_point(P, d, 5)["ratio_true"] - a) > 1e-12:
                problems.append(f"d-Invarianz neu q5 P={P} d={d}")
    if problems:
        raise ValueError("Anker-Verifikation gescheitert: " + "; ".join(problems))
    return {"run1_regression_040": "8/8 bit-exakt (tol 1e-9)",
            "run1_regression_034": "5/5 bit-exakt (tol 1e-9)",
            "cal_P_d_invariance": "13/13 identisch (d=q, q^2, q^3; tol 1e-12)",
            "new_P_d_invariance": "13/13 identisch (d=q, q^2, q^3; tol 1e-12)"}


# === kohärentes Gesetz v3 (klassisch exakt, aus Phase 11a) ===

def coh_sens(pt, mode="worst"):
    """cP — kohärente Empfindlichkeit in Ratio-Einheiten (Phase-11a-Kern,
    klassisch exakt aus den gefrorenen n_d-Vektoren)."""
    return dg.coh_sens(pt, mode)


def gamma_lsq(cps, deltas):
    """LSQ-durch-Null: gamma = <cP, delta_cal>/<cP, cP> (Fit-Regel)."""
    return dg.gamma_lsq(cps, deltas)


def delta_cal_of(ratio_hw, kappa_hat, pt, ro_hat, b_p):
    """Kohärenter Floor-Anteil am Punkt:
    delta_cal = ratio_ro_exact(pt, ro_hat) + b_P*(kappa_hat-1) - ratio_hw."""
    return ratio_ro_exact(pt, ro_hat, nq_of(pt)) \
        + b_p * (kappa_hat - 1.0) - ratio_hw


def center_v3(kappa_hat, pt, ro_hat, b_p, gamma, c_p):
    """Gesetzliche v3-Form (dieser Freeze): gefrorenes v2-Gesetz minus
    kohaerenten Prep-Fehler-Floor.

    center_v3 = (1-1/S)*(ratio_ro_exact(pt, ro_hat, nq) + b_P*(kappa_hat-1)
                         - gamma_arm*cP) + L_q
    Auf Aer reduziert sie sich exakt auf das gefrorene center_v2 (gamma_Aer
    ~ 0), das die Form-Gates E/S der Phase-10b-Konvention PASSTE."""
    A = ratio_ro_exact(pt, ro_hat, nq_of(pt)) + b_p * (kappa_hat - 1.0)
    return (1.0 - 1.0 / SHOTS) * (A - gamma * c_p) + pt["L_q"]


def cP_table():
    """Die 26 gefrorenen cP-Werte (13 Kalibrier + 13 Verdict), klassisch exakt."""
    rows = {}
    for P in CAL_Q3_POINTS:
        rows[f"cal|q3_d3|{P}"] = coh_sens(arm_point(P, D3_MIN, 3))
    for P in CAL_Q5_POINTS:
        rows[f"cal|q5_d5|{P}"] = coh_sens(arm_point(P, D5_MIN, 5))
    for P in NEW_Q3_POINTS:
        rows[f"verdict|q3_d3|{P}"] = coh_sens(arm_point(P, D3_MIN, 3))
    for P in NEW_Q5_POINTS:
        rows[f"verdict|q5_d5|{P}"] = coh_sens(arm_point(P, D5_MIN, 5))
    return rows


# === Kontrollen am Minimalregister (UNVERAENDERT aus Phase 10) ===

def uniform_control(q):
    return hw2.uniform_control(q)


def composite_control(P, d, q):
    return hw2.composite_control(P, d, q)


def shuffle_inert_expected(P, d, q, seed):
    return hw2.shuffle_inert_expected(P, d, q, seed)


# === Run-2-Evidenz (registrierte Erwartungen, 0 QPU, NICHT verdict-tragend) ===

def run2_transfer_stats():
    """Transfer-/gamma-Erwartungen aus dem committeten Phase-11a-Diagnostik-
    Resultat (md5 f9f6f50b9a1c00db3fdf90708581c394). NICHT verdict-tragend:
    sie eichen die Vorhersage, das Verdict bleibt an die Band-Regeln gebunden.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DIAG_RESULTS)
    doc = json.load(open(path, encoding="utf-8"))
    md5 = hashlib.md5(open(path, "rb").read()).hexdigest()
    if md5 != DIAG_RESULTS_MD5:
        raise ValueError(f"Diagnostik-Resultat md5-MISMATCH: {md5}")
    stats = {"results_md5": md5}
    for arm in ("q3_d3", "q5_d5"):
        s = doc[arm]
        stats[arm] = {
            "gamma_lsq": s["gamma_lsq"],
            "gamma_cal_fit": s["gamma_cal_fit"],
            "transfer_max_abs_res": s["transfer_max_abs_res"],
            "cal_fit_max_abs_res": s["cal_fit_max_abs_res"],
            "corr_kdef_delta": s["corr_kdef_delta"],
            "v3a_gamma_new_mean": s["v3a_gamma_new_mean"],
            "v3a_gamma_old_mean": s["v3a_gamma_old_mean"],
        }
    stats["q5_541_querkonsistenz"] = [
        r for r in doc["d_inv_querkonsistenz"] if r["key"] == "q5_d5|541"][0]
    return stats


# === Payload ===

def build_prereg_payload():
    cal3 = [arm_point(P, D3_MIN, 3) for P in CAL_Q3_POINTS]
    cal5 = [arm_point(P, D5_MIN, 5) for P in CAL_Q5_POINTS]
    new3 = [arm_point(P, D3_MIN, 3) for P in NEW_Q3_POINTS]
    new5 = [arm_point(P, D5_MIN, 5) for P in NEW_Q5_POINTS]
    anchor_report = verify_anchors_run3()
    comp3 = composite_control(NEW_Q3_POINTS[0], D3_MIN, 3)
    comp5 = composite_control(NEW_Q5_POINTS[0], D5_MIN, 5)
    unif3 = uniform_control(3)
    unif5 = uniform_control(5)
    inert3 = shuffle_inert_expected(NEW_Q3_POINTS[0], D3_MIN, 3, 421)
    inert5 = shuffle_inert_expected(NEW_Q5_POINTS[0], D5_MIN, 5, 421)
    transfer_stats = run2_transfer_stats()
    cP = cP_table()

    n_verdict_struct = len(NEW_Q3_POINTS) * K_REPEATS \
        + len(NEW_Q5_POINTS) * K_REPEATS          # 39
    n_verdict_lo = len(NEW_Q3_POINTS) + len(NEW_Q5_POINTS)   # 13
    n_ladder = (len(LADDER_REPEATS) - 1) * 2      # 6 (r=1 geteilt mit Anker)
    n_cal_struct = len(CAL_Q3_POINTS) * K_REPEATS \
        + len(CAL_Q5_POINTS) * K_REPEATS          # 39
    n_cal_lo = len(CAL_Q3_POINTS) + len(CAL_Q5_POINTS)       # 13
    n_controls = 4
    n_cal_ro = 2
    total = (n_verdict_struct + n_verdict_lo + n_ladder + n_cal_struct
             + n_cal_lo + n_controls + n_cal_ro)  # 116

    payload = {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "status": STATUS,
        "registered_before": REGISTERED_BEFORE,
        "registered_by": "pt_ram_q_hardware3.freeze_prereg — payload_md5 = "
                         "md5(json.dumps(payload, sort_keys=True, separators=(',',':'))) "
                         "OHNE md5-Feld (Haus-Konvention, pt_ram_q_hardware)",
        "user_anchor": (
            "mache alles autonom weiter wie du vorgeschlagen hast und auch in "
            "QuQuint Statevecor und auch in QPU Hardware. Wir werden uns die "
            "Bauanleitung für den Hilbert-Pólya-Operator jetzt direkt vom "
            "Universum holen und ausdehnen und abhärten. — Konkretion aus dem "
            "Phase-10d-Verdict (H-RAM-Q-3b_REFUTED, Kontrollen gruen): die "
            "naechste Iteration ist das kohärente Prep-Fehler-Daempfungsmodell "
            "als NEUES Prereg (dieser Freeze). Die Phase-11a-Diagnostik gegen "
            "das committete Run-2-Raw zerlegt die Suppression in einen "
            "stochastischen kappa-Term (b_P*(1-kappa_hat), Aer-Form) und einen "
            "kohaerenten Floor (gamma_arm*cP, arm-stabil, klassisch exakt)."),
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
            "d19f4a563d88e0cf3ffd4b187a10ca73": "EXPERIMENT 042 — Fez-Raw-Counts "
                                                "darq1stvr3kc73ej96ig (committed VOR Auswertung)",
            RUN3_PREREG_MD5_043: "EXPERIMENT 043 — H-RAM-Q-3b Freeze A' + Re-Freeze R1 "
                                 "(Minimalregister d=q, 90 Circuits)",
            RUN2_COUNTS_MD5_KEY: "EXPERIMENT 043 — Fez-Raw-Counts " + RUN2_JOB
                                 + " (committed VOR Auswertung, Verdict REFUTED)",
            DIAG_RESULTS_MD5: "Phase 11a — kohärente Prep-Fehler-Diagnostik "
                              "(0 QPU, NICHT verdict-tragend, committet 4434d34)",
        },
        "phase10_verdict_context": {
            "verdict": "H-RAM-Q-3b_REFUTED",
            "befund": "Kalibrier-Ziel EINLOEST (alle 13 kappa_hat >= 0.81: q3 "
                      "0.9786-0.9904, q5 0.9196-0.9286) UND 13/13 unter c(kappa)-w_B' "
                      "EINSEITIG (res_v1 [-0.0938..-0.0341], Suppression, 0 "
                      "Amplification); auch die Aer-kalibrierte v2-Form verfehlt "
                      "(res_v2 alle negativ, max 0.0630 > w_B' 0.02787)",
            "mechanismus": "Der Loschmidt-Echo refokussiert kohärente/unäre Prep-Fehler, "
                           "die der Einweg-Struktur-Circuit voll traegt — kappa_hat "
                           "ueberschaetzt die Struktur-Daempfung; die Suppression ist "
                           "real, aber ihr kappa-anteilig-Anteil ist zu klein fuer das "
                           "Aer-Depolarisierungsmodell",
            "kontrollen": "t3 (041-Identitaet) 3.55e-15, t4/t5/t6/md5 alle gruen — "
                          "die saubere Falsifikations-Konstellation",
            "deutung": "Arithmetik hielt (t3 exakt), Kopplungsgesetz hielt nicht; "
                       "REFUTED gilt fuer das Gesetz mit Echo-kalibriertem kappa_hat "
                       "auf ibm_fez, NICHT fuer die Arithmetik",
        },
        "design_decision": {
            "gesetz_v3b_gewaehlt": "center_v3 = (1-1/S)*(ratio_ro_exact(pt, ro_hat) + "
                                   "b_P*(kappa_hat-1) - gamma_arm*cP) + L_q — minimaler "
                                   "Zusatz zum gefrorenen v2-Gesetz (Phase 10b): der "
                                   "kohaerente Prep-Fehler-Floor als SEPARATER Term mit "
                                   "klassisch EXAKTER, per-Punkt gefrorener Empfindlichkeit "
                                   "cP; gamma_arm ist EIN Arm-Parameter, in-job auf dem "
                                   "Kalibrier-Bein gefittet.",
            "v3a_verworfen": "Das rein kohärente Gesetz (delta = gamma*cP ohne kappa-Term) "
                             "passt zwar besser auf die Roh-Daten (B1: kappa-Entkopplung), "
                             "reduziert aber auf Aer NICHT auf das gefrorene v2 (das die "
                             "Form-Gates E/S PASSTE): mit gamma_Aer = 0 sagt v3a keine "
                             "Aer-Degradation vorher, das exact-Bein degradiert aber mit "
                             "p1 (b_P*(1-kappa_hat) ~ -0.075 auf q5 bei p1 >= 1e-3 >> "
                             "TOL_FORM = 0.03). v3b reduziert sich auf Aer exakt auf v2 "
                             "(gamma_Aer ~ 0, denn b_P wurde AUF der Aer-Grid gefittet) "
                             "und ist robust unter beiden Wahrheiten.",
            "kalibrier_bein": "Die 13 Run-2-Verdict-P werden in Run 3 FRISCH gemessen "
                              "(3 Reps + gepaarter Loschmidt) und tragen den in-job "
                              "gamma-Fit; die 13 neuen P sind Holdout. Die Run-2-Werte "
                              "der Kalibrier-P werden NICHT wiederverwendet (Anti-"
                              "Session-Drift); die Run-1-P fliegen komplett raus "
                              "(541/463/625-Anomalien; q5|541-Anomal ist register-/"
                              "session-spezifisch: run-1 d=25 res_v1 +0.0248 POSITIV vs "
                              "run-2 d=5 -0.1453).",
            "w_b_doppelprime_wiederverwendet": {
                "wert": W_B_PRIME,
                "source": W_B_PRIME_SOURCE,
                "begruendung": "Gleiche Apparatus-Konvention (Minimalregister, SHOTS 8192, "
                               "K_REPEATS 3): die committete w_B' wird wiederverwendet "
                               "statt aus der neuen 26-Punkte-Grid abgeleitet; die "
                               "Transfer-Erwartung (max|res| q3 0.0152 / q5 0.0197) liegt "
                               "mit Marge innen. Das Stage-Aer-3-Bein registriert q97.5 "
                               "als Diagnostik + Gate-S-Konsistenz (<= W_A) und aendert "
                               "w_B'' NICHT (Phase-9/10-Freeze-B-Praezedenz).",
            },
            "register_unveraendert": "Minimalregister d=q aus Phase 10 bleibt EXAKT "
                                     "stehen (q3 auf d=3 mit 2 Qubits, q5 auf d=5 mit 3 "
                                     "Qubits) — die Kalibrier-Ziele waren eingelöst; "
                                     "nur das Dämpfungs-Gesetz wird präzisiert.",
        },
        "frozen_theorems": {
            "B2_q_universal_identity": "share* = (m - q*n0)^2/((q-1)*d*m) + q*sigma^2/(d*m) "
                                       "für ALLE Count-Vektoren inkl. Wraparound (041, "
                                       "CONFIRMED B)",
            "d_invariance": "d*m*share* haengt nur von den mod-q gefalteten Counts ab "
                            "(041 T3 exakt, k=1 Eingeschlossen) -> die Minimalregister "
                            "d=3/d=5 tragen die IDENTISCHEN Ratio-Vorhersagen wie d=9/25",
            "ratio_forms": {
                "q3": "ratio_true = 1 + 12*delta^2/(m-3)^2",
                "q5": "ratio_true = 1 + 20*sigma^2/(m-5)^2",
                "general": "ratio_true = (q-1)*(q*sum_r N_r^2 - m^2)/(m - q*n0)^2",
            },
            "shuffle_inertness_at_dq": "Bei d=q ist der Fold die Identitaet; eine "
                                       "Label-Permutation permutiert N und laesst sum N^2 "
                                       "invariant => expected_share(Shuffle) == "
                                       "share_true_reg EXAKT. Die Shuffle-Kontrolle ist "
                                       "am Minimalregister strukturell inert und wird "
                                       "durch Composite- + Uniform-Null-Kontrollen "
                                       "ersetzt (Phase-10-Praezedenz).",
            "coherent_gradient_law": "Erste Ordnung in einer unit-norm kohärenten "
                                     "Amplituden-Stoerung delta_psi (||delta_psi|| = "
                                     "gamma, <psi|delta_psi> = 0): delta_n_a = "
                                     "2*sqrt(m*n_a)*Re(delta_psi_a), also delta_share = "
                                     "2*sqrt(m)*Re(<v|delta_psi>) mit v_a = sqrt(n_a)*"
                                     "grad_a; worst-case 2*sqrt(m)*||v||_2, normiert auf "
                                     "model_share_reg => cP. cP_rms = cP_worst/sqrt(d) "
                                     "ist arm-konstant, die Konvention ist gamma-"
                                     "absorbierbar (Phase-11a-Kern, klassisch exakt).",
        },
        "operational_definitions": {
            "state": "|psi(P,d)> = sum_a sqrt(n_a/m)|a> mit n_a = #{p <= P prim : "
                     "p ≡ a mod d}; am Minimalregister d=q direkt die q Residuenklassen "
                     "(q=3: 3 Labels von 4 auf 2 Qubits, Label 3 ideal leer; "
                     "q=5: 5 Labels von 8 auf 3 Qubits, Labels 5..7 ideal leer).",
            "hw_counts": "n_hat = m*c/S auf dem 2^n-Label-Vektor, dann Wraparound-Fold "
                         "n_d[a] = sum n_full[a::d]; unter Depolarisierung erhaelt die "
                         "Uniform-Masse m exakt: sum n_hat = m.",
            "share_hw": "share*_hw = sum_{j=1}^{q-1} |DFT_d(n_hat)[j*d/q]|^2/(d*m), "
                        "ABSOLUT-FFT-Konvention.",
            "ratio_hw": "share*_hw / model_share_reg mit model_share_reg = "
                        "(m - q*n0_true)^2/((q-1)*d*m) GEFROREN auf wahre Arithmetik-Werte.",
            "kappa": "kappa_p = P_L/P_ro_ref aus gepaartem Loschmidt-Circuit (Prep + "
                     "exakte Inverse) + Readout-Kalibrier im SELBEN Job. UNVERAENDERT "
                     "aus Phase 9/10.",
            "ratio_ro_exact": "Aer-Exact-Anker: ratio am gefrorenen STRESS-Modell mit "
                              "Readout ANALYTISCH via T_ro bei RO_STRESS = 0.01 "
                              "(Phase-10b-Konvention) — der per-Punkt-Anker des Zentrums.",
            "b_p": "Per-Punkt-Streuung aus dem Stage-Aer-3-Exact-Bein (26 Punkte x 6 "
                   "Stresslevel, LSQ deg 1 ueber die Domain-Zellen kappa >= 0.81) — "
                   "Phase-10b-Konvention, WIEDERVERWENDET; b_P fuer alle 26 Punkte wird "
                   "VOR Hardware committet (pt_ram_q_hardware3_aer).",
            "delta_cal": "delta_cal(P) = ratio_ro_exact(pt, ro_hat) + b_P*(kappa_hat-1) "
                         "- ratio_hw(P) — der Teil der Suppression, den das v2-Gesetz "
                         "NICHT erklaert (= -res_v2 abzueglich Prefaktoren); der "
                         "kohaerente Floor-Term gamma*cP soll ihn tragen.",
            "gamma_arm": "EIN Arm-Parameter, in-job per LSQ-durch-Null auf dem "
                         "KALIBRIER-BEIN: gamma_arm = <cP, delta_cal>/<cP, cP> über die "
                         "13 Kalibrier-P des Arms (cP aus dem Payload, klassisch exakt; "
                         "ratio_ro_exact mit ro_hat aus der Readout-Kalibrier desselben "
                         "Jobs; b_P aus dem committeten Stage-Aer-3-Bein). Der Fit "
                         "NUTZT NUR die Kalibrier-P; die 13 Holdout-P gehen in KEINEN "
                         "Fit.",
            "cP": "cP = 2*sqrt(m)*||v||_2/model_share_reg mit v_a = sqrt(n_a)*"
                  "d share*/d n_a am EXAKTEN ABS-FFT-Share (worst-case kohärente "
                  "Empfindlichkeit; rms = worst/sqrt(d) arm-konstant). Gefroren im "
                  "Payload fuer alle 26 Punkte (cP_freeze).",
            "idle_labels": "Am Minimalregister sind 1/4 (q3) bzw. 3/8 (q5) Labels ideal "
                           "leer; ihre Leakage-Masse faellt via Wraparound-Fold in echte "
                           "Klassen. Stage-Aer-Form-Validierung am ECHTEN Fold prueft "
                           "das VOR Hardware.",
        },
        "prediction_freeze": {
            "classical_core": {
                "q3": "ratio_true = 1 + 12*delta^2/(m-3)^2 — die User-Headline",
                "q5": "ratio_true = 1 + 20*sigma^2/(m-5)^2",
                "verdict_in_040_034": "8/8 und 5/5 gated Punkte im Band [0.8, 1.25]",
            },
            "p_rule": {
                "rule": "P_neu = kleinste Primzahl p mit p > P_alt + 30 UND p nicht in "
                        "der gemessenen Vereinigung (alle P aus irgendeinem vorherigen "
                        "Lauf irgendeines Arms; globale Lesart registriert — die "
                        "registrierten Sets sind unter per-Arm- und globaler Lesart "
                        "identisch, kein Fall unterscheidet sie)",
                "striktheit": "p > P_alt + 30 schliesst p = P_alt + 30 selbst aus, wenn "
                              "prim (z.B. 149 -> 181, nicht 179; 433 -> 467, nicht 463)",
                "collision_case": "499 -> 541 ist gemessen (Run-1 q3 UND q5) -> "
                                  "uebersprungen -> 547 (der einzige kollidierende "
                                  "Fall in den registrierten Sets)",
                "motivation": "Die Run-1-P sind durch die Reskalierungs-Analyse vorbelastet "
                              "(Anti-Sharpshooter); die Run-2-Verdict-P sind durch Run 2 "
                              "als RATIO-Messung bekannt und werden deshalb NUR Kalibrier-"
                              "Bein (frisch gemessen), nie Verdict; die neuen P sind nie "
                              "gemessen worden.",
                "cal_q3": CAL_Q3_POINTS,
                "cal_q5": CAL_Q5_POINTS,
                "new_q3": NEW_Q3_POINTS,
                "new_q5": NEW_Q5_POINTS,
                "run1_retired": "Run-1-P werden weder Verdict noch Kalibrier — nur "
                                "Regression-Anker (T1'')",
            },
            "noise_law": {
                "ratio_hw": "ratio_hw = kappa*(1 - 1/S)*ratio_true + L_q (UNVERAENDERT "
                            "aus Freeze A/042) — die STRUCTUR-Form; das Zentrum c_v3 "
                            "ersetzt ratio_true durch den per-Punkt-Anker + kappa-Term "
                            "- kohaerenten Floor (siehe operational_definitions)",
                "center_v3": "center_v3(kappa_hat, pt, ro_hat, b_P, gamma_arm, cP) = "
                             "(1-1/S)*(ratio_ro_exact(pt, ro_hat, nq) + b_P*(kappa_hat-1) "
                             "- gamma_arm*cP) + L_q",
                "aer_reduction": "Auf Aer (gamma_Aer ~ 0) reduziert center_v3 exakt auf "
                                 "das gefrorene center_v2 (Phase 10b), das die Form-Gates "
                                 "E/S PASSTE — die Reduktion ist by construction, NICHT "
                                 "gefitet.",
                "L_q": "L_q = (q-1)^2*m^2/(S*(m-q*n0)^2) — exakte multinomiale Erwartung.",
                "honesty": "gamma_arm ist EIN freier Arm-Parameter (2 total). Er wird "
                           "in-job am Kalibrier-Bein gefittet und am Holdout getestet — "
                           "die Falsifizierbarkeit liegt in der Band-Regel am Holdout.",
            },
            "points": {"q3_d3": new3, "q5_d5": new5},
            "calibration_points": {"q3_d3": cal3, "q5_d5": cal5},
            "cP_freeze": cP,
            "anchor_verification": anchor_report,
            "registered_expectations_nicht_verdict_tragend": {
                "source": "Phase-11a-Diagnostik (md5 " + DIAG_RESULTS_MD5 + "), committet",
                "transfer_max_abs_res": {"q3_d3": transfer_stats["q3_d3"]["transfer_max_abs_res"],
                                         "q5_d5": transfer_stats["q5_d5"]["transfer_max_abs_res"]},
                "gamma_cal_fit": {"q3_d3": transfer_stats["q3_d3"]["gamma_cal_fit"],
                                  "q5_d5": transfer_stats["q5_d5"]["gamma_cal_fit"]},
                "gamma_lsq": {"q3_d3": transfer_stats["q3_d3"]["gamma_lsq"],
                              "q5_d5": transfer_stats["q5_d5"]["gamma_lsq"]},
                "corr_kdef_delta": {"q3_d3": transfer_stats["q3_d3"]["corr_kdef_delta"],
                                    "q5_d5": transfer_stats["q5_d5"]["corr_kdef_delta"]},
                "note": "Erwartete in-job gamma_arm ~ gamma_cal_fit (gleiche Punkte, "
                        "frische Messung); erwartete Holdout-Residuen ~ transfer-Erwartung "
                        "plus Session-Drift. DIENST der Eichung, NICHT dem Verdict.",
            },
        },
        "echo_ladder": {
            "purpose": "GEMESSENES Daempfungsgesetz statt starrer (1-eps)^2-Annahme: "
                       "r-fache (Prep + exakte Inverse)-Bloecke, r in " +
                       str(list(LADDER_REPEATS)) + ", je Arm am NEUEN Ankerpunkt.",
            "repeats": list(LADDER_REPEATS),
            "anchors": {"q3": LADDER_ANCHORS["q3"], "q5": LADDER_ANCHORS["q5"]},
            "r1_shared": "r=1 ist EXAKT der gepaarte Loschmidt-Circuit des Ankerpunkts "
                         "(geteilt, kein doppeltes Circuit).",
            "barriers": "Barrier zwischen allen Bloecken (Transpiler-Kuerzung verboten, "
                        "Phase-9-Konvention).",
            "verdict_role": "NICHT verdict-tragend (Phase-10-Praezedenz); die Leiter "
                            "dokumentiert das Daempfungsgesetz am neuen Register.",
        },
        "hardware_parameters": {
            "backend": "ibm_fez",
            "token": "TOKEN1 (IBMQ_TOKEN); TOKEN2 unberuehrt",
            "n_shots": SHOTS,
            "register_topology": {
                "q3_d3": {"d": D3_MIN, "n_qubits": NQ3, "labels": 2 ** NQ3,
                          "real_labels": 3, "idle_labels": 2 ** NQ3 - 3,
                          "note": "Minimalrepraesentant d=q=3 (UNVERAENDERT aus Phase 10)"},
                "q5_d5": {"d": D5_MIN, "n_qubits": NQ5, "labels": 2 ** NQ5,
                          "real_labels": 5, "idle_labels": 3,
                          "note": "Minimalrepraesentant d=q=5 (UNVERAENDERT aus Phase 10)"},
            },
            "state_prep": "Qiskit StatePreparation aus den gefrorenen n_d-Vektoren; "
                          "Loschmidt = Prep + exakte Inverse; Leiter = r Bloecke mit "
                          "Barrieren.",
            "circuit_budget": {
                "verdict_structure": n_verdict_struct,
                "verdict_loschmidt": n_verdict_lo,
                "echo_ladder": n_ladder,
                "kalibrier_structure": n_cal_struct,
                "kalibrier_loschmidt": n_cal_lo,
                "negative_controls": n_controls,
                "readout_cal": n_cal_ro,
                "total": total,
                "total_shots": total * SHOTS,
                "jobs": 1,
            },
            "run_config": {"optimization_level": 3, "dynamical_decoupling": "XX",
                           "resilience": "none (raw SamplerV2 counts)"},
            "isa_ceilings": {
                "per_circuit_2q_max": ISA_2Q_PER_CIRCUIT_MAX,
                "total_2q_max": ISA_2Q_TOTAL_MAX,
                "erwartung": "max ~84-96 2q (Leiter r=8, q5) je Circuit, total ~600-700 2q "
                             "(Prognose, Phase-10-Messung 493 2q/max 84 als Basis); die "
                             "echten Werte werden in Freeze B'' am ISA-Report registriert",
                "measured_when": "Stage-3-Transpilation VOR Hardware; Backend-Target-Laden "
                                 "= kein Quota-Kontakt (kein Job), §Z.14-Phase-3b-Praezedenz",
                "abort": "Ceiling-Überschreitung vor dem QPU-Lauf -> Abbruch, Re-Freeze",
            },
        },
        "simulation_leg": {
            "purpose": "0 QPU: Validierung der v3-Form auf dem gefrorenen STRESS-Modell "
                       "am Minimalregister VOR Hardware (26-Punkte-Grid: 13 Verdict + "
                       "13 Kalibrier); Form-Gates + w_B''-Konsistenz.",
            "stress_model": "pt_ram_q_hardware_aer.build_noise_model-Präzedenz "
                            "(depolarizing p1 auf 1q-Gates, ratio*p1 auf cz, "
                            "ReadoutError ro=1e-2) — NICHT kalibriert, konservativ.",
            "stress_grid_p1": STRESS_GRID_P1,
            "n_ens": N_ENS,
            "form_validation": "Phase-10b-Re-Freeze-R1-Konvention (zweistufig): Gate E "
                               "vergleicht das DETERMINISTISCHE Zentrum (exact-Bein): "
                               "max |res_v2| <= TOL_FORM = 0.03 ueber die Domain-Zellen "
                               "(kappa >= 0.81) — v2, NICHT v3, denn auf Aer ist "
                               "gamma_Aer ~ 0 und v3 reduziert exakt auf v2; Gate S: "
                               "sampled Domain-q97.5 <= W_A = 0.05. Der per-Zell-Max "
                               "des sampled-Beins ist registrierte Diagnostik, KEIN Gate. "
                               "gamma_aer (in-Aer-Fit auf den Kalibrier-Zellen) ist "
                               "registrierte Diagnostik (Erwartung ~0), KEIN Gate. "
                               "Verletzung eines Gates -> Re-Freeze-Zyklus (dokumentiert, "
                               "Hardware blockiert).",
            "freeze_b": "w_B'' = w_B' = " + repr(W_B_PRIME) + " WIEDERVERWENDET (source: "
                        + W_B_PRIME_SOURCE + "); das Stage-Aer-3-Bein registriert "
                        "q97.5 der 26-Punkte-Grid als Diagnostik + Gate-S-Konsistenz "
                        "(<= W_A) und ECHTEN ISA-Report (Phase-9/10-Praezedenz: "
                        "Freeze B'' aendert den Payload NICHT).",
        },
        "kalibrier_bein": {
            "purpose": "In-job gamma_arm-Kalibrier am selben Register: die 13 "
                       "Run-2-Verdict-P werden FRISCH gemessen (3 Reps + gepaarter "
                       "Loschmidt) und tragen den gamma-Fit; der Holdout-Charakter der "
                       "13 neuen P bleibt unangetastet.",
            "points": {"q3_d3": cal3, "q5_d5": cal5},
            "reps": K_REPEATS,
            "loschmidt_gepaart": True,
            "gamma_fit_rule": "gamma_arm = <cP, delta_cal>/<cP, cP> ueber die Kalibrier-P "
                              "des Arms (LSQ-durch-Null); delta_cal = ratio_ro_exact(pt, "
                              "ro_hat) + b_P*(kappa_hat-1) - ratio_hw; ratio_ro_exact mit "
                              "ro_hat aus der Readout-Kalibrier DESELBEN Jobs.",
            "verdict_role": "verdict-tragend NUR in der kappa-Gate-Union (VOID-Calibration "
                            "zaehlt Verdict-Punkte UND Kalibrier-Punkte); die Ratio-Band-"
                            "Regeln (REFUTED/CONFIRMED/COARSE) gelten NUR fuer die 13 "
                            "Holdout-P. Die Kalibrier-Residuen sind registrierte "
                            "Diagnostik (KEIN Gate): cal_fit-Erwartung max|res| q3 0.0145 "
                            "/ q5 0.0142.",
            "leckage_dokumentiert": "Die Run-2-Ratios der Kalibrier-P sind als Zahlen "
                                    "bekannt (committed Eval); die Run-3-MESSUNGEN sind "
                                    "frisch (nie bei dieser Session/Konfiguration "
                                    "gemessen). Das VERDICT nutzt ausschliesslich die 13 "
                                    "NEUEN P.",
        },
        "safeguard_limits": {
            "band_rule": "ratio_hw ∈ [center_v3 - w_B'', center_v3 + w_B''] an den 13 "
                         "Holdout-P; Freeze A'': w_A = 0.05 (grob), w_B'' = w_B' = "
                         + repr(W_B_PRIME) + " (scharf, WIEDERVERWENDET); das Zentrum "
                         "center_v3 bleibt gefroren (kein Re-Zentrieren).",
            "amplification_ceiling": "ratio_hw > (1-1/S)*ratio_true + L_q + w -> "
                                     "H-RAM-Q-4_INVALID_AMPLIFICATION (einseitig: "
                                     "Depolarisierung daempft Prime-Harmonische, hebt "
                                     "sie nie über das rauschfreie Niveau + Band) — "
                                     "UNVERAENDERT aus Phase 9/10",
            "kappa_floor_void": "kappa_hat < KAPPA_CEILING = 0.81 an >= 2 Punkten der "
                                "UNION (Verdict-P UND Kalibrier-P) -> "
                                "H-RAM-Q-4_VOID_CALIBRATION_GLOBAL. Die Union, weil der "
                                "gamma-Fit Kalibrier-kappa_hat >= 0.81 braucht; "
                                "UNVERAENDERT gefrorene Garantie 0.81.",
            "falsifier": ">= 2 der 13 Holdout-P unter center_v3 - w -> "
                         "H-RAM-Q-4_REFUTED",
            "trennschaerfe": {
                "band_vs_shot_noise": "gepoolte K=3-Ratio-SE ≈ 1.4-2.0% (S=8192) gegen "
                                      "w_A = 5% -> >= 2.5σ Auflösung",
                "kappa_se": "SE(kappa_hat) ≈ 0.005 (Loschmidt, 8192 Shots)",
                "gamma_se": "gamma_arm-SE aus dem Kalibrier-Fit: 13 Punkte, cP-Spreizung "
                            "4.2-5.0 (q3) / 4.6-5.4 (q5) — SE(gamma) ~ std(delta_cal/cP)/"
                            "sqrt(n_cal) ~ 0.003 (q3) / 0.005 (q5); ueber cP ~ 4.7 in "
                            "Ratio-Einheiten ~ 0.014-0.024 — KOMPARABEL zur Transfer-"
                            "Erwartung; die Band-Regel traegt die gamma-Unschaerfe mit "
                            "(w_B'' = w_B' ungeaendert, Transfer liegt innen)",
                "coupling": "kappa_hat (Loschmidt) und share-Ratio (Harmonische) sind "
                            "operationell UNABHÄNGIG; das gefrorene Gesetz koppelt sie "
                            "zusammen mit dem in-job gamma-Fit.",
            },
            "job_integrity": "EIN Fez-Job (TOKEN1), " + str(total) + " Circuits; Job-ID + "
                             "md5 der Counts committed VOR der Auswertung (§Z.14-Disziplin).",
        },
        "controls": {
            "t1_backcompat_run3": anchor_report,
            "t2_v2_anchors": "034-Prime-Anker (625,625) = 0.04272280701754398 über die "
                             "d=625-Kette unberührt — klassisch, kein QPU-Kontakt.",
            "t3_identity_two_ways": "share*_hw = sum_j |G_j|^2/(d*m) auf den HW-Counts "
                                    "zwei Wege (FFT bei j*d/q vs gefaltete Formel), "
                                    "exakt 1e-12 (041-Theorem); Verletzung -> "
                                    "EVALUATION_INVALID.",
            "t4_negative_must_not_fire": {
                "composite_q3": comp3,
                "composite_q5": comp5,
                "uniform_q3": unif3,
                "uniform_q5": unif5,
                "rule": "share_ctrl_hw < kappa_hat*(1-1/S)*share_true_reg + L_q - w "
                        "(untere Prime-Bandkante, konservativste Ecke kappa = "
                        "KAPPA_CEILING, w = W_A); Verletzung -> H-RAM-Q-4_DEGENERAT "
                        "(REFUTED-zulaessig)",
            },
            "t4b_shuffle_inert_theorem": {
                "q3_seed421": inert3,
                "q5_seed421": inert5,
                "statement": "Kein Shuffle-Circuit am Minimalregister (Phase-10-"
                             "Theorem, expected_share == share_true_reg EXAKT).",
            },
            "t5_gate_set_frozen": "13 VERDICT-P = exakt die 13 P nach amendierter Regel "
                                  "(kleinste Primzahl > P_alt + 30 UND nicht in der "
                                  "gemessenen Vereinigung, P_alt = Run-2-Verdict-P); 13 "
                                  "Kalibrier-P = exakt die Run-2-Verdict-P; Run-1-P "
                                  "retired; keine nachträglichen Ergänzungen.",
            "t6_mass_conservation": "sum_r N_hat_r = m_hat unter Depolarisierung; "
                                    "Verletzung -> EVALUATION_INVALID.",
        },
        "verdict_map": {
            "H-RAM-Q-4_NOISE_LIFT_CONFIRMED": "alle 13 Holdout-P im Band "
                                              "[center_v3 - w_B'', center_v3 + w_B''], "
                                              "Kontrollen gruen, alle kappa_hat >= 0.81 "
                                              "(Union)",
            "H-RAM-Q-4_COARSE_HOLD_SHARP_MISS": "alle Punkte im groben Band (w_A), "
                                                ">= 1 Punkt außerhalb w_B''",
            "H-RAM-Q-4_REFUTED": ">= 2 der 13 Holdout-P unter center_v3 - w",
            "H-RAM-Q-4_INVALID_AMPLIFICATION": "irgendein Punkt über "
                                               "(1-1/S)*ratio_true + L_q + w",
            "H-RAM-Q-4_VOID_CALIBRATION": "kappa_hat < 0.81 an >= 2 Punkten der UNION "
                                          "(Verdict UND Kalibrier)",
            "H-RAM-Q-4_DEGENERAT": "Kontroll-Regel T4 verletzt — REFUTED-zulaessig",
            "EVALUATION_INVALID_KONTROLLE_GESCHEITERT": "T1-T6 gescheitert — Auswertung void",
        },
        "fallback_lesart_b": {
            "status": "REGISTRIERT, NUR-NACHGELAGERT, NIE stiller Patch",
            "trigger": "AUSLÖSUNG NUR FALLS das v3-Gesetz erneut scheitert (REFUTED oder "
                       "VOID trotz gamma-Fit) — sonst nie.",
            "mechanism": "Separat gefrorenes NEUES Prereg. Option B (per-GATE-eps-Kalibrier) "
                         "bleibt die dokumentierte Fallback-Lesart aus Phase 10 (per-GATE-"
                         "eps nicht arm-transferierbar, Latte-Verschiebungs-Optik, "
                         "Identifikations-Spannung).",
            "primär_pfad": "v3b (dieser Freeze): das gefrorene v2-Gesetz + der kohärente "
                           "Prep-Fehler-Floor mit in-job gamma-Fit am Kalibrier-Bein.",
        },
        "two_freeze_architecture": {
            "freeze_a": "DIESER Freeze (A''): analytischer Kern + amendierte P-Regel + "
                        "cP-Freeze (26 Werte) + gamma-Fit-Regel + Kalibrier-Bein + md5, "
                        "VOR jedem Hardware-/Simulations-Kontakt, 0 QPU.",
            "stage3_aer": "Aer-Bein (0 QPU): 26-Punkte-Grid (13 Verdict + 13 Kalibrier) "
                          "x 6 Stresslevel, b_P fuer alle 26 (Phase-10b-Konvention), "
                          "Form-Gates E/S, gamma_aer-Diagnostik (~0), w_B''-Konsistenz.",
            "freeze_b": "w_B''-Registrierung (WIEDERVERWENDET, unveraendert) + ISA-3-"
                        "Report VOR dem QPU-Lauf; Zentrum unverändert; erst danach "
                        "QPU-Kontakt (Phase-9/10-Praezedenz: Payload-md5 unangetastet).",
            "hardware": "EIN Fez-Job (TOKEN1) erst nach Freeze-B''-Commit; alle "
                        "Abbruchbedingungen exakt in safeguard_limits registriert.",
        },
        "anti_sharpshooter": {
            "no_ex_post_fit": "Die 13 VERDICT-P sind nach amendierter registrierter "
                              "Regel VOR dem Freeze berechnet — nie gemessen, keine "
                              "Vorbelastung. Der gamma-Fit nutzt NUR die 13 Kalibrier-P "
                              "(frisch gemessen in Run 3); die Holdout-P gehen in "
                              "KEINEN Fit.",
            "registered_alternative_models": "v3a (rein kohärent, ohne kappa-Term) ist "
                                             "DOKUMENTIERT VERWORFEN (Aer-Reduktion "
                                             "scheitert am Form-Gate); v2 bleibt als "
                                             "Reduktions-Basis gefroren; das v3b-Gesetz "
                                             "ist der registrierte Kandidat.",
            "negative_predictions": "Composite- (beide Arme) und Uniform-Kontrollen mit "
                                    "exakten Erwartungen registriert (T4); Shuffle-"
                                    "Inertness als Theorem dokumentiert (T4b); der "
                                    "Sampling-Lift L_q ist unter dem Shot-Noise.",
        },
        "qpu": "0 QPU (Freeze A''); Stage-3 Aer 0 QPU; EIN Fez-Job (TOKEN1) erst nach "
               "Freeze B''",
        "suite_state": 995,
        "future_phase_numbering": {
            "synthesis": "§Z.26 (SYNTHESIS)",
            "log": "§10.27 (RIEMANN) — §Z.23/§10.24 Gematria-Layer, §Z.24/§10.25 "
                   "Phase 9, §Z.25/§10.26 Phase 10",
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
        raise ValueError(f"H-RAM-Q-4-Prereg-md5-MISMATCH in {path}")
    return doc