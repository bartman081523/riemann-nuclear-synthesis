"""EXPERIMENT 040 — RAM-Q Zyklizität (H-RAM-Q-1): Zyklotomische Ableitung der
Fünf + GF(3)-Verallgemeinerungsvorhersage.

Frage: Warum EXAKT (m - 5)^2 im Ramanujan-Fingerprint (EXPERIMENT 034, B+,
prereg-md5 a2fc4875)? Ist die Fünf eine Fit-Konstante — oder die Signatur
einer zyklotomischen Struktur, die eine parameterfreie Verallgemeinerung
erzwingt?

Baustein B1 (VOR dem Freeze hergeleitet; die gesamte Ableitung ist exakte
Algebra, verifiziert gegen die gefrorenen q=5-Konstanten):

  Setup: Prime-Support {p <= P}, m = pi(P), Register d = q^k (k >= 2).
  Einzelregister-DFT-Diagonale: G(a) = sum_p omega_d^{a p},
  Profil p(a) = |G(a)|^2/(d*m) (Parseval: Summe = 1, Normalisierung no-op).
  Klasse S*_q = {a = j*d/q : j = 1..q-1} (a=0 trivial: G(0)=m fuer JEDEN
  Support). Dort gilt omega_d^{j*d*p/q} = omega_q^{j*(p mod q)} — S*_q misst
  die Primzahl-Residuen mod q, UNABHAENGIG von d.

  Residuen-Counts: n_r = #{p <= P : p ≡ r mod q}, Summe_r n_r = m.
  Fuer q prim ist n_0 = 1 (nur p = q selbst, P >= q).

  CYCLOTOMISCHER KERN (Ramanujan-Summe): fuer j ≢ 0 mod q ist
      sum_{r=1}^{q-1} omega_q^{j r} = -1,
  denn sum_{r=0}^{q-1} omega_q^{j r} = 0 (geometrische Reihe); dies ist
  exakt die Ramanujan-Summe c_q(j) = mu(q) = -1 fuer q prim. Die
  Amplitude ist KLASSENUNABHAENGIG (identisch fuer alle j), weil die
  Spur ganzzahlig ist: diskrete Stabilitaet = ganzzahlige Spur.

  ATOME-IDENTITAET (B1): unter Ramanujan-Aequipartition der m-1 Nicht-q-
  Primes auf die q-1 Nicht-Null-Klassen (n_r = (m-1)/(q-1)) gilt fuer alle
  j in {1..q-1}:
      G(j*d/q) = n_0 + (m-1)/(q-1) * sum_{r=1}^{q-1} omega_q^{jr}
               = n_0 - (m-1)/(q-1) = (q*n_0 - m)/(q-1),
  und damit
      share*_model(P, d, q) = (q-1) * ((m - q*n_0)/(q-1))^2 / (d*m)
                            = (m - q*n_0)^2 / ((q-1) * d * m).

  Die "Fuenf" zerfaellt in ZWEI Strukturfaktoren:
    - das ATOM n_0 = 1 (p = q ist der einzige Prime ≡ 0 mod q),
    - die KLASSENZAHL q-1 (Aequipartition der uebrigen m-1 Primes).
  m - q = (m-1) - (q-1): Abweichung der Nicht-q-Primes von der
  Aequipartition pro Klasse. KEINE Fit-Konstante.

  Spezialfaelle:
    q=5, n_0=1: (m-5)^2/(4dm) — bit-exakt die gefrorene Formel aus 034
                ((m-5)**2/(4.0*float(d)*m)). Der Nenner 4 ist (q-1), KEINE
                freie Konstante.
    q=3, n_0=1: (m-3)^2/(2dm) — GF(3)-Vorhersage (Zaehler UND Nenner).

  Korrollare (Lift = share*_model / generisch, generisch = (q-1)/d):
      lift_q(m) = (m - q)^2 / ((q-1)^2 * m).
    Transition lift=1: (m-q)^2 = (q-1)^2 m.
      q=5: m^2 - 26m + 25 = 0 -> m = 25  (= TRANSITION_M aus 034)
      q=3: m^2 - 10m + 9  = 0 -> m = 9   (P = 23, pi(23) = 9)
    Exakte Null: m = q (q=5: m=5, P=11 aus 034; q=3: m=3, P=5).
    Suppression: 1 < m < Transition (q=3: 4 <= m <= 8).

  ZWEIKLASSEN-IDENTITAET (q=3, EXAKT, keine Naeherung): mit
  delta = (n_1 - n_2)/2 und omega_3 = -1/2 + i*sqrt(3)/2 gilt
      G = n_0 + n_1*omega_3 + n_2*omega_3^2
        = (3-m)/2 + i*sqrt(3)*delta   (denn omega_3+omega_3^2 = -1,
                                       omega_3 - omega_3^2 = i*sqrt(3))
      |G|^2 = (m-3)^2/4 + 3*delta^2,
  und G(2d/3) = conj(G(d/3)) (exakt, da n_1,n_2 reell), also
      share*_gemessen = (m-3)^2/(2dm) + 6*delta^2/(d*m)
      gemessen/Modell = 1 + 12*delta^2/(m-3)^2   (monoton in der
      mod-3-Race-Asymmetrie; bei 2 Klassen kollabiert die Abweichung auf
      EINE Zahl delta^2 — bei 4 Klassen (q=5) gibt es Kreuzterme).

Anti-Sharpshooter: Prereg (Modellwerte, Gate-Set, Baender, Verdict-Map,
Kontrollfamilie, Seeds) VOR der ersten Auswertung gefroren (md5 ueber
Payload-Kanonik ohne md5-Feld, wie 032/034) und VOR der Auswertung
committet. Fuer q=3 existiert KEIN Einzelpunkt-Anker: das Band [0.8, 1.25]
ist registrierte Annahme (registered_assumptions), nicht Kalibration.

Registrierte Alternativmodelle (Steelman derselben Klasse, nicht "Zufall"):
  crude_fixed_4:  (m-q*n0)^2/(4dm) — Zaehler-Generalisierung mit
                  eingefrorenem Nenner 4; bei q=3 Faktor 0.5 unter der
                  Vorhersage -> vom Band diskriminiert (ratio 0.5 < 0.8).
  no_zero_class:  m^2/((q-1)dm) — ohne das Atom n_0=1; Lift = m/(q-1)^2,
                  an der Transition m=9: 2.25x generisch statt kein Lift
                  -> von der NEGATIV-Vorhersage Transition diskriminiert.

0 QPU: reine Arithmetik (Einzelregister-DFT-Profil) — offline, kein
Quanten-SDK.
"""

import hashlib
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_ququint_multin as mn
import pt_ramanujan_replication as rr
from pt_prime_state import sieve_primes

PREREG_PATH = "pt_ram_q_prereg.json"
RESULTS_PATH = "pt_ram_q_results.json"
EXPERIMENT = "040-ram-q-zyklizitaet"
HYPOTHESIS = "H-RAM-Q-1"
PLAN_PATH = "~/.claude/plans/riemann-phase-ram-q-zyklizitaet.md"

Q_TEST = 3             # die getestete Familie (GF(3))
D_GRID = (9, 81, 729)  # (3^2, 3^4, 3^6) — Spiegel von (25, 625) = (5^2, 5^4)

GATE_MIN_PI = 29    # Kriterium 2: band_lo >= 3x generisch
                    # <=> 0.8*(m-3)^2/(4m) >= 3 <=> (m-3)^2 >= 15m
                    # <=> m >= 20.56 (m >= 21, pi(73)=21); registrierte Marge
                    # darueber (Race-Slack, analog q=5: Root 19 -> Gate 79)
                    # -> pi(109) = 29
BAND_LO = 0.8
BAND_HI = 1.25
FALSIFIER_MIN_OUTSIDE = 2
TOLERANCE = 1e-9

# 21 Prime-Punkte: d=9 (2), d=81 (7), d=729 (12). Alle Primzahlen < d
# (d = 3^k ist nie prim, also p mod d = p).
# Deskriptiv: (5,·) exakte Null (m=q), (23,·) Transition (m=9),
# (7/13/19,·) Suppression. Gated: die 8 Punkte auf d=729 mit m >= 29.
PRIME_POINTS = (
    (5, 9), (7, 9),
    (7, 81), (13, 81), (19, 81), (23, 81), (31, 81), (47, 81), (71, 81),
    (7, 729), (23, 729), (31, 729), (71, 729), (109, 729), (163, 729),
    (211, 729), (307, 729), (401, 729), (541, 729), (625, 729), (729, 729),
)
COMPOSITE_POINTS = ((15, 729), (121, 729), (341, 729), (625, 729))
RANDOM_SEED_BASE = 20260926

# d-Skalierungs-Invarianz: gleiches P ueber d in {9, 81, 729}
D_SCALING_POINTS = (7, 23, 31, 71)
D_SCALING_TOL = 1e-9

VERDICT_GENERALIZED = "H-RAM-Q-1_Q_DEFORMATION_GENERALIZED"
VERDICT_PARTIAL = "H-RAM-Q-1_PARTIAL_EIN_PUNKT_AUSSEN"
VERDICT_REFUTED = "H-RAM-Q-1_REFUTED_Q_DEFORMATION_KOLLABIERT"
VERDICT_INVALID = "EVALUATION_INVALID_KONTROLLE_GESCHEITERT"


# === Baustein B1: Modell-Arithmetik (allgemeines q) ===

def residue_counts(P, q):
    """n_r = #{p <= P : p ≡ r mod q} fuer r = 0..q-1 (exakte Arithmetik)."""
    counts = [0] * q
    for p in sieve_primes(P):
        counts[p % q] += 1
    return counts


def model_share_star_q(P, d, q):
    """(m - q*n0)^2 / ((q-1)*d*m) mit m = pi(P), n0 = #{p<=P: p≡0 mod q}.

    q=5, n0=1: bit-exakt rr.model_share_star aus 034 ((m-5)**2/(4dm)).
    q=3, n0=1: (m-3)^2/(2dm) — GF(3)-Vorhersage (Zaehler UND Nenner).
    """
    m = len(sieve_primes(P))
    n0 = residue_counts(P, q)[0]
    return (m - q * n0) ** 2 / ((q - 1) * float(d) * m)


def generic_baseline_q(d, q):
    """Generische Baseline (q-1)/d — fuer q=5: 4/d (= rr.generic_baseline)."""
    return (q - 1) / float(d)


def lift_m(m, q):
    """lift_q auf direktem m (ohne Sieb)."""
    return (m - q) ** 2 / ((q - 1) ** 2 * m)


def lift_q(P, q):
    """lift = share*_model / generisch = (m-q*n0)^2 / ((q-1)^2 * m).

    q=5: (m-5)^2/(16m) — bit-exakt rr.lift_factor aus 034.
    """
    m = len(sieve_primes(P))
    n0 = residue_counts(P, q)[0]
    return (m - q * n0) ** 2 / ((q - 1) ** 2 * m)


def transition_m(q):
    """Kleinste ganze m >= q mit lift >= 1: (m-q)^2 = (q-1)^2 * m.

    q=5: m=25 (= rr.TRANSITION_M); q=3: m=9 (P=23); q=2: m=4.
    """
    m = q
    while lift_m(m, q) < 1.0:
        m += 1
    return m


def cyclotomic_core_check(q, tol=1e-12):
    """sum_{r=1}^{q-1} zeta_q^{jr} = -1 fuer alle j = 1..q-1
    (= c_q(j) = mu(q) = -1 fuer q prim) — der cyclotomische Kern von B1."""
    worst = 0.0
    for j in range(1, q):
        s = sum(np.exp(2j * np.pi * j * r / q) for r in range(1, q))
        worst = max(worst, abs(s + 1.0))
    return worst <= tol


def share_star_q(prof, d, q):
    """Masse der Klasse S*_q = {a = j*d/q, j=1..q-1} im Profil.

    q=5: identisch zu mn.share_star (gleiche Iteration, bit-exakt).
    """
    step = d // q
    return float(sum(prof[a] for a in range(step, d, step)))


def synthetic_support(counts, d):
    """Distincter synthetischer Support: n_r Positionen p ≡ r (mod q), p < d.

    Indicator-Konvention wie der echte Prime-Support (jede Position einmal)
    -> Parseval-Normalisierung in mn.single_register_profile ist no-op.
    Auf der Klasse S*_q gilt fuer p = r + q*t:
        omega_d^{j*d*p/q} = omega_q^{j*p/q} = omega_q^{j*r},
    der Beitrag haengt NUR vom Residuum ab, nicht von der konkreten
    Position — identisch zum reelen Prime-Profil (dort ebenfalls
    G(j*d/q) = sum_r n_r * omega_q^{jr}). Nur fuer Tests/deskriptive
    Erwartungen (keine Prime-Daten noetig).
    """
    q = len(counts)
    support = []
    for r, n in enumerate(counts):
        slots = list(range(r if r else q, d, q))
        if len(slots) < n:
            raise ValueError(
                f"Residuenklasse r={r}: {n} distincte Positionen < d={d} "
                f"nicht moeglich (max {len(slots)})")
        support.extend(slots[:n])
    return support


def share_star_from_counts(counts, d):
    """share*_q eines synthetischen Residuen-Profils (counts = [n_0..n_{q-1}]).

    Support via synthetic_support (distincte Positionen je Residuenklasse).
    Nur fuer Tests/deskriptive Erwartungen (keine Prime-Daten noetig).
    """
    q = len(counts)
    prof = mn.single_register_profile(synthetic_support(counts, d), d)
    return share_star_q(prof, d, q)


def delta_identity_analytic(n1, n2, d):
    """q=3-EXAKTidentitaet (Algebra): share* = (m-3)^2/(2dm) + 6*delta^2/(dm),
    delta = (n1-n2)/2, m = 1 + n1 + n2 (n0=1 fuer q prim)."""
    m = 1 + n1 + n2
    delta = (n1 - n2) / 2.0
    return (m - 3) ** 2 / (2.0 * d * m) + 6.0 * delta ** 2 / (d * m)


def alt_crude_fixed_4(P, d, q):
    """Registriertes Alternativmodell: Zaehler-Generalisierung mit
    eingefrorenem Nenner 4 (nicht (q-1))."""
    m = len(sieve_primes(P))
    n0 = residue_counts(P, q)[0]
    return (m - q * n0) ** 2 / (4.0 * float(d) * m)


def alt_no_zero_class(P, d, q):
    """Registriertes Alternativmodell: ohne das Atom n_0=1 (alle m Primes
    aequipartitioniert ueber q-1 Klassen)."""
    m = len(sieve_primes(P))
    return m ** 2 / ((q - 1) * float(d) * m)


# === Prereg ===

def is_gated_q3(P, d):
    """Gate: d = 729 (Gate-Power-Traeger) und m >= GATE_MIN_PI."""
    return d == 729 and len(sieve_primes(P)) >= GATE_MIN_PI


def point_role(P, d):
    m = len(sieve_primes(P))
    t = transition_m(Q_TEST)
    if m == Q_TEST:
        return "exakte_null_deskriptiv"
    if m < t:
        return "suppression_deskriptiv"
    if m == t:
        return "transition_deskriptiv"
    if is_gated_q3(P, d):
        return "gated"
    return "ueber_transition_deskriptiv"


def composite_limit():
    """Kontroll-Limit = band_lo des KLEINSTEN gated Punkts (109, 729)."""
    return BAND_LO * model_share_star_q(109, 729, Q_TEST)


def build_prereg_payload():
    points = []
    for P, d in PRIME_POINTS:
        m = len(sieve_primes(P))
        model = model_share_star_q(P, d, Q_TEST)
        counts = residue_counts(P, Q_TEST)
        delta = (counts[1] - counts[2]) / 2.0
        points.append({
            "P": P, "d": d, "pi": m,
            "model": model,
            "band_lo": BAND_LO * model,
            "band_hi": BAND_HI * model,
            "gated": is_gated_q3(P, d),
            "role": point_role(P, d),
            "residue_counts_mod3": counts,
            "delta": delta,
            "delta_expectation": delta_identity_analytic(counts[1], counts[2], d),
        })
    alt = []
    for P, d in PRIME_POINTS:
        if is_gated_q3(P, d):
            alt.append({
                "P": P, "d": d,
                "crude_ratio_vs_model": alt_crude_fixed_4(P, d, Q_TEST)
                                        / model_share_star_q(P, d, Q_TEST),
                "no_zero_lift_vs_generic": alt_no_zero_class(P, d, Q_TEST)
                                           / generic_baseline_q(d, Q_TEST),
            })
    return {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "registered_before": (
            "Baustein B1 VOR dem Freeze im Modul hergeleitet (ATOME-"
            "IDENTITAET): share*_model = (m - q*n0)^2/((q-1)*d*m) — die "
            "'Fuenf' ist (n0=1-Atom) + ((q-1)-Klassenzahl), keine Fit-"
            "Konstante. Verifiziert gegen die gefrorenen q=5-Konstanten aus "
            "EXPERIMENT 034 (prereg-md5 a2fc4875) bit-exakt. Die gemessenen "
            "share*-Werte der 21 Prime-Punkte wurden VOR diesem Freeze NICHT "
            "berechnet; der Freeze bindet Verdict-Regelwerk, Gate-Set, "
            "Baender, Seeds und Kontrollfamilie."),
        "model": {
            "general_formula": "share*_model(P, d=q^k) = (m - q*n0)^2 / "
                               "((q-1)*d*m), m = pi(P), n0 = #{p<=P: p≡0 mod q}",
            "q5_specialization": "(m-5)^2/(4dm) — bit-exakt EXPERIMENT 034",
            "q3_prediction": "(m-3)^2/(2*d*m), d in {9, 81, 729} — ZAEHLER UND "
                             "NENNER aendern sich ((q-1)=2, keine freie "
                             "Konstante 4)",
            "cyclotomic_core": "sum_{r=1}^{q-1} zeta_q^{j r} = -1 = c_q(j) = "
                               "mu(q) — Klassenunabhaengigkeit via ganzzahliger Spur",
            "q3_exact_deviation_identity": (
                "share*_gemessen = (m-3)^2/(2dm) + 6*delta^2/(d*m), "
                "delta = (n1-n2)/2 — EXAKT (Zwei-Klassen-Kollaps)"),
            "q3_measured_over_model": "1 + 12*delta^2/(m-3)^2 — monoton in "
                                      "der mod-3-Race-Asymmetrie",
            "atom_decomposition": "m - q = (m-1) - (q-1): Nicht-q-Primes "
                                  "minus Klassenzahl — Abweichung von der "
                                  "Aequipartition pro Klasse",
        },
        "extraordinarity_score": {
            "score": 5, "max": 10,
            "reason": "strukturelle Extrapolation von q=5 auf q=3 mit "
                      "parameterfreier, abgeleiteter (nicht gefitteter) Formel; "
                      "aber nur EIN q bisher beobachtet, und die (q-1)-Nenner-"
                      "Komponente ist eine echte neue Vorhersage (nie bei q≠5 "
                      "gemessen). Beweislast: Band-Test an 8 gated Punkten + "
                      "Transitions-Diskriminierung der Alternativmodelle.",
        },
        "d_grid": list(D_GRID),
        "prime_points": points,
        "model_by_point": {f"{P}@{d}": model_share_star_q(P, d, Q_TEST)
                           for P, d in PRIME_POINTS},
        "gated_points": [[P, d] for P, d in PRIME_POINTS if is_gated_q3(P, d)],
        "gate": {
            "gate_min_pi": GATE_MIN_PI,
            "criteria": [
                "Kriterium 1 (Band-Fairness): relative Abweichung ~ 12*delta^2/"
                "(m-3)^2 mit delta^2 <= (m-3)^2/48 als registrierte ANNAHME "
                "(kein q=3-Einzelpunkt-Anker; q=5-Anker: ratio 1.0248); "
                "25%-Band fair fuer m >= 29 (empirisch delta(P=109) = -1, "
                "Bindung 3.75).",
                "Kriterium 2 (Separations-Sicherheit): band_lo >= 3x generisch "
                "<=> 0.8*(m-3)^2/(4m) >= 3 <=> (m-3)^2 >= 15m <=> m >= 20.56 "
                "(m >= 21, pi(73) = 21) -> registrierte Marge darueber: "
                "GATE_MIN_PI = 29 (pi(109) = 29); die Marge ist dem Race-"
                "Asymmetrie-Slack bei kleinem m geschuldet (P=7: gemessen/"
                "Modell = 4.0), analog q=5 in 034 (Root 19 -> Gate 79).",
                "NUR d=729 traegt gated Punkte: auf d=81 ist m <= pi(71) = 20 "
                "< 21 (Kriterium 2 unerreichbar) -> d81/d9 rein deskriptiv.",
            ],
        },
        "thresholds": {
            "band_lo": BAND_LO, "band_hi": BAND_HI,
            "falsifier_min_outside": FALSIFIER_MIN_OUTSIDE,
            "tolerance": TOLERANCE,
            "d_scaling_tol": D_SCALING_TOL,
        },
        "registered_alternative_models": {
            "crude_fixed_4": {
                "formula": "(m-q*n0)^2/(4dm)",
                "why": "Zaehler-Generalisierung mit eingefrorenem Nenner 4 — "
                       "wird vom Band diskriminiert (ratio 0.5 < 0.8 bei q=3)",
                "values_at_gated": {f"{a['P']}@{a['d']}": a["crude_ratio_vs_model"]
                                    for a in alt},
            },
            "no_zero_class": {
                "formula": "m^2/((q-1)*d*m)",
                "why": "ohne das Atom n0=1 — Lift = m/(q-1)^2; an der Transition "
                       "m=9: 2.25x generisch statt kein Lift -> von der "
                       "NEGATIV-Vorhersage Transition diskriminiert",
                "lift_at_transition_m9": 9.0 / 4.0,
                "values_at_gated": {f"{a['P']}@{a['d']}": a["no_zero_lift_vs_generic"]
                                    for a in alt},
            },
        },
        "negative_predictions": [
            {"point": [5, 9], "prediction": "Modell EXAKT 0 (m = q = 3); "
             "deskriptive Mess-Erwartung via delta^2-Identitaet: n1=0, n2=2 "
             "-> delta=-1 -> gemessen = 2/9 = generisch EXAKT (maximale "
             "Race-Asymmetrie kompensiert die Modell-Null)"},
            {"point": [23, 729], "prediction": "Transition: Modell = generisch "
             "EXAKT (2/729, kein Lift); deskriptive Erwartung: gemessen = "
             "2/729 + 6/(729*9) (delta=-1 bei m=9: n1=3, n2=5)"},
            {"point": [7, 729], "prediction": "Suppression: Modell UNTER "
             "generisch (m=4 < 9); deskriptive Erwartung: delta=-0.5 bei P=7 "
             "(n1=1 [7], n2=2 [2,5]) -> gemessen = 1/18 = 4x Modell, immer "
             "noch unter generisch 2/9 (Race-Asymmetrie dominiert bei kleinem "
             "m — einer der Gruende fuer das Gate m >= 29)"},
        ],
        "registered_assumptions": [
            "Band [0.8, 1.25] ist fuer q=3 registrierte ANNAHME, nicht "
            "Kalibration (kein Einzelpunkt-Anker). Fairness-Bedingung aus "
            "der delta^2-Identitaet: delta^2 <= (m-3)^2/48.",
            "Chebyshev-Race-Drift (mod 3) kann das Band brechen — das ist "
            "ein realer Befund (REFUTED/PARTIAL), kein Designfehler.",
            "Modellgueltigkeit m >= q (P >= 5 fuer q=3); kleinere m rein "
            "deskriptiv-crude.",
        ],
        "controls": {
            "t1_backcompat_q5": (
                "model_share_star_q/lift_q/generic_baseline_q mit q=5 "
                "reproduzieren EXPERIMENT 034 bit-exakt: (625,625) = "
                "109^2/(4*625*114), transition_m(5) = 25 = TRANSITION_M, "
                "(11,25) = 0, share_star_q ≡ mn.share_star"),
            "t2_v2_anchor": "V2-Prime-Anker 0.04272280701754398 bit-exakt via "
                            "mn.dft_profile(625,625) + share_star_q(.,625,5)",
            "t3_d_scaling": "d-Skalierungs-Invarianz: d*gemessen invariant "
                            "fuer gleiches P ueber d in {9,81,729} (P in "
                            "(7, 23, 31, 71)), tol 1e-9",
            "t4_control_overlap": "Random (Seeds base+Index) und Composite "
                                  "(rank-matched, erste m Composites) an jedem "
                                  "gated Punkt < band_lo des Punkts; "
                                  "composite_limit = 0.8 * model(109,729)",
            "t5_gate_set_frozen": "gated Set = genau die 8 registrierten "
                                  "Punkte auf d=729 mit m >= 29; keine "
                                  "nachtraeglichen Ergaenzungen",
            "t6_alternatives_discriminated": "crude_fixed_4 ratio 0.5 < 0.8 "
                                             "am kleinsten gated Punkt",
            "random_seed_base": RANDOM_SEED_BASE,
            "composite_points": [list(p) for p in COMPOSITE_POINTS],
        },
        "verdict_map": {
            VERDICT_GENERALIZED: "alle 8 gated Punkte im Band UND Kontrollen "
                                 "gruen",
            VERDICT_PARTIAL: "exakt 1 gated Punkt ausserhalb des Bandes, "
                             "Kontrollen gruen",
            VERDICT_REFUTED: ">= 2 gated Punkte ausserhalb ODER Kontroll-"
                             "Overlap (T4)",
            VERDICT_INVALID: "T1/T2/T3/T5/T6 gescheitert (Anker/Struktur/"
                             "Gate-Set/Diskriminierung) — Auswertung void",
        },
        "qpu": "0 QPU — reine Arithmetik (Einzelregister-DFT-Profil), "
               "offline, kein Quanten-SDK",
        "plan": PLAN_PATH,
        "q5_reference_chain": {
            "experiment_034_prereg_md5": "a2fc4875e10dd198e95d4996b1692759",
            "experiment_032_v2_prereg_md5": "d9da292c7863810840b86ae2f069a365",
            "v2_share_star_prime_committed": rr.V2_SHARE_STAR_PRIME_COMMITTED,
            "exact_model_625_625": rr.EXACT_MODEL_625_625,
        },
    }


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
        raise ValueError(f"RAM-Q-Prereg-md5-MISMATCH in {path}")
    return doc


# === Auswertung (NUR nach dem Freeze-Commit) ===

def run_evaluation(prereg_path=PREREG_PATH):
    doc = load_frozen_prereg(prereg_path)
    q = Q_TEST
    rows = []
    for entry in doc["prime_points"]:
        P, d = entry["P"], entry["d"]
        primes = sieve_primes(P)
        prof = mn.single_register_profile(primes, d)
        measured = share_star_q(prof, d, q)
        model = entry["model"]
        ratio = measured / model if model > 0 else None
        counts = residue_counts(P, q)
        residual = measured - delta_identity_analytic(counts[1], counts[2], d)
        rows.append({
            "P": P, "d": d, "pi": entry["pi"], "role": entry["role"],
            "model": model, "measured": measured,
            "ratio": ratio,
            "band_lo": entry["band_lo"], "band_hi": entry["band_hi"],
            "gated": entry["gated"],
            # Band in Share-Space gegen die gefrorenen Schwellen
            # (aequivalent zu BAND_LO <= ratio <= BAND_HI, da
            # band_lo = BAND_LO*model > 0)
            "in_band": (entry["band_lo"] <= measured <= entry["band_hi"])
                       if ratio is not None else None,
            "delta": (counts[1] - counts[2]) / 2.0,
            "delta_identity_residual": residual,
        })

    # T1: q=5-Rueckkompatibilitaet (bit-exakt 034)
    prof625 = mn.dft_profile(625, 625)
    t1 = (
        model_share_star_q(625, 625, 5) == rr.model_share_star(625, 625)
        and model_share_star_q(97, 625, 5) == rr.model_share_star(97, 625)
        and lift_q(625, 5) == rr.lift_factor(625)
        and generic_baseline_q(625, 5) == rr.generic_baseline(625)
        and transition_m(5) == rr.TRANSITION_M
        and model_share_star_q(11, 25, 5) == 0.0
        and share_star_q(prof625, 625, 5) == mn.share_star(prof625, 625)
    )
    # T2: V2-Anker bit-exakt
    t2 = abs(share_star_q(prof625, 625, 5) - rr.V2_SHARE_STAR_PRIME_COMMITTED) \
        <= rr.V2_SHARE_STAR_TOL
    # T3: d-Skalierungs-Invarianz (strukturell exakt)
    t3 = True
    d_scale_rows = []
    for P in D_SCALING_POINTS:
        vals = {}
        for d in D_GRID:
            if P >= d:
                continue
            prof = mn.single_register_profile(sieve_primes(P), d)
            vals[d] = d * share_star_q(prof, d, q)
        ref = vals[max(vals)]
        ok = all(math.isclose(v, ref, rel_tol=D_SCALING_TOL, abs_tol=D_SCALING_TOL)
                 for v in vals.values())
        t3 = t3 and ok
        d_scale_rows.append({"P": P, "d_times_measured": vals, "ok": ok})
    # T4: Kontroll-Overlap (Random + rank-matched Composite an gated Punkten)
    limit = composite_limit()
    t4_rows = []
    t4 = True
    gated_entries = [e for e in doc["prime_points"] if e["gated"]]
    for idx, entry in enumerate(gated_entries):
        P, d, m = entry["P"], entry["d"], entry["pi"]
        rand = mn.random_diagonal_support(m, d, RANDOM_SEED_BASE + idx)
        s_rand = share_star_q(mn.single_register_profile(rand, d), d, q)
        try:
            comp_support = mn.composite_support(P)
        except ValueError:
            comp_support = rr.composite_rank_matched(m)
        s_comp = share_star_q(mn.single_register_profile(comp_support, d), d, q)
        ok = s_rand < entry["band_lo"] and s_comp < entry["band_lo"]
        t4 = t4 and ok
        t4_rows.append({"P": P, "d": d, "random": s_rand, "composite": s_comp,
                        "band_lo": entry["band_lo"], "ok": ok})
    # T5: Gate-Set gefroren
    t5 = ([list(p) for p in doc["gated_points"]]
          == [[P, d] for P, d in PRIME_POINTS if is_gated_q3(P, d)])
    # T6: Alternativmodell diskriminiert (ratio 0.5 < band_lo-Faktor)
    smallest_gated = min((e for e in doc["prime_points"] if e["gated"]),
                         key=lambda e: e["P"])
    t6 = (alt_crude_fixed_4(smallest_gated["P"], smallest_gated["d"], q)
          / smallest_gated["model"] < BAND_LO)
    controls = {
        "t1_backcompat_q5": bool(t1), "t2_v2_anchor": bool(t2),
        "t3_d_scaling": bool(t3), "t4_control_overlap": bool(t4),
        "t5_gate_set_frozen": bool(t5), "t6_alternatives": bool(t6),
        "d_scaling_rows": d_scale_rows, "overlap_rows": t4_rows,
        "composite_limit": limit,
    }
    hard = t1 and t2 and t3 and t5 and t6
    verdict = VERDICT_INVALID
    if hard:
        if not t4:
            verdict = VERDICT_REFUTED
        else:
            outside = sum(1 for r in rows if r["gated"] and not r["in_band"])
            if outside >= FALSIFIER_MIN_OUTSIDE:
                verdict = VERDICT_REFUTED
            elif outside == 1:
                verdict = VERDICT_PARTIAL
            else:
                verdict = VERDICT_GENERALIZED
    return {
        "experiment": EXPERIMENT, "hypothesis": HYPOTHESIS,
        "prereg_path": prereg_path, "prereg_md5": doc["md5"],
        "q": q, "d_grid": list(D_GRID),
        "rows": rows, "controls": controls,
        "gated_outside": sum(1 for r in rows if r["gated"] and not r["in_band"]),
        "gated_total": sum(1 for r in rows if r["gated"]),
        "verdict": verdict,
    }


def main():
    res = run_evaluation()
    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    print("VERDICT:", res["verdict"])
    print(f"gated: {res['gated_total'] - res['gated_outside']}/"
          f"{res['gated_total']} im Band")
    print("Kontrollen:", {k: v for k, v in res["controls"].items()
                          if k.startswith("t")})
    for r in res["rows"]:
        ratio = "-" if r["ratio"] is None else f"{r['ratio']:.4f}"
        gate = "GATED" if r["gated"] else "desk "
        band = "" if not r["gated"] else ("  im Band" if r["in_band"] else "  AUSSEN")
        print(f"P={r['P']:4d} d={r['d']:4d} m={r['pi']:3d} {gate} "
              f"model={r['model']:.6f} gemessen={r['measured']:.6f} "
              f"ratio={ratio}{band}")


if __name__ == "__main__":
    main()