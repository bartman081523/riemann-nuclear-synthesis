"""EXPERIMENT 041 — RAM-Q Asymptotik (H-RAM-Q-2): q-Universalität + Konvergenz
bis unendlich.

User-Direktive (2026-09-26): "wir testen ja nur bis 1 million. unsere theorie
sollte aber bis unendlich halten." Diese Phase schliesst die Finitheits-Luecke
des B1-Fingerprints in drei Schichten — 0 QPU, reine Arithmetik:

  (i)   d -> unendlich: EXAKT (Theorem, kein empirischer Rest),
  (ii)  P -> unendlich: asymptotisches Theorem B3 + numerische Skans bis
        10^7 (prereg-gated) / 10^8 (deskriptive Erweiterung),
  (iii) q -> unendlich: B2 ist q-universal; blinder Out-of-Family-Test q=7.

BAUSTEIN B2 (q-universelle EXAKTidentität, VOR dem Freeze im Modul
hergeleitet; Verallgemeinerung der q=3-Zweiklassen-Identität aus
EXPERIMENT 040 auf ALLE q):

  Setup wie dort: Prime-Support {p <= P}, m = pi(P), Register d = q^k
  (k >= 1, d Vielfaches von q). Auf der Klasse S*_q = {a = j*d/q, j=1..q-1}
  gilt omega_d^{a p} = omega_q^{j (p mod q)} — der Beitrag haengt NUR vom
  Residuum mod q ab, NICHT von der Groesse von p (auch bei Wraparound
  P >> d) und NICHT von d:

      G(j*d/q) = n_0 + sum_{r=1}^{q-1} n_r * zeta_q^{j r},
      n_r = #{p <= P : p ≡ r mod q}, m = sum_r n_r.

  Direkte Expansion mit den Ramanujan-Teilsummen c_q(t) =
  sum_{j=1}^{q-1} zeta_q^{j t} = q-1 falls q|t, sonst -1 (fuer q prim;
  identischer Kern wie B1):

      sum_{j=1}^{q-1} |G(j*d/q)|^2
          = (q-1) n_0^2 - 2 n_0 A + q sum_{r=1}^{q-1} n_r^2 - A^2,
      A = m - n_0 (Anzahl der Nicht-q-Primes).

  Mit der Klassendispersion sigma^2 = sum_{r=1}^{q-1} (n_r - A/(q-1))^2
  gilt q sum n_r^2 - A^2 = A^2/(q-1) + q sigma^2, also insgesamt

      share*_q = (m - q*n_0)^2/((q-1)*d*m) + q*sigma^2/(d*m)   (EXAKT)
      gemessen/Modell = 1 + q(q-1)*sigma^2/(m-q)^2             (n_0=1, m>q)

  Spezialfaelle (Rueckkompatibilitaet, bit-genau verifiziert):
    q=3: sigma^2 = 2*delta^2 (delta = (n1-n2)/2) -> die gefrorene
         Zweiklassen-Identität share* = (m-3)^2/(2dm) + 6 delta^2/(dm)
         aus EXPERIMENT 040 (prereg-md5 bd9dfee7).
    q=5, Aequipartition: sigma^2 = 0 -> (m-5)^2/(4dm) — bit-exakt die
         gefrorene 034-Formel (prereg-md5 a2fc4875).
    q=5 allgemein: 1 + 20 sigma^2/(m-5)^2 — der bislang unbemerkte
         Race-Term ERKLAERT die 034-Ratio 1.0248 exakt aus den
         Residuen-Counts (Kontrolle T1 bindet den V2-Anker).

  Strukturkorollar (einseitiges Band): sigma^2 >= 0, also
      gemessen/Modell >= 1 IMMER.
  Das Band [0.8, 1.25] kann nur am OBEREN Rand verletzt werden; der
  Race-Tterm hebt die Fingerprint-Masse niemals unter das Modell.

  d-Invarianz-Theorem: d * share*_q * m haengt NUR von den Counts mod q
  ab — exakt fuer ALLE d = q^k, inkl. Wraparound (P >> d). Die
  d-Skalierungs-Kontrolle T3 aus Phase 7 war damit ein Theorem-Check
  ohne eigenen empirischen Inhalt; hier wird sie in einem NEUEN Regime
  geprueft (P = 10^7 >> d = 2401, Wraparound-Faktor ~ 4170).

BAUSTEIN B3 (asymptotisches Theorem — Theorem-Schicht, kein Experiment):

  ratio - 1 = q(q-1) sigma^2/(m-q)^2 -> 0 fuer P -> unendlich, q fest.
  Grund: Primaerverteilung in Residuenklassen (PNT-AP).
    - UNBEDINGT (Siegel-Walfisz, ineffektive Konstanten): fuer festes q
      ist |n_r - A/(q-1)| = O(x e^{-c sqrt(log x)}), also
      ratio - 1 = O(e^{-c' sqrt(log x)} log^2 x) -> 0. Fuer JEDE feste q
      liegt das Band [0.8, 1.25] schliesslich vollstaendig — die Theorie
      haelt bis unendlich (ineffektive Schwelle, keine explizite
      Crossover-Grenze aus SW).
    - UNTER GRH (effektiv): sigma_r = O(sqrt(x) log^2 x) ->
      ratio - 1 = O(log^6 x / x).
  Heuristik (Chebyshev-Bias / Rubinstein-Sarnak): der Race-Bias waechst
  wie c*sqrt(x)/log x mit langsam oszillierendem c = O(1) -> demnach
      ratio - 1 ~ C/x mit C = q (q-1)^2 c^2 = O(1),
  Log-Log-Slope ~ -1. Registriert als DESKRIPTIVE Erwartung (slope in
  [-1.5, -0.5], C(P) = P (ratio-1) <= 10^4) — Heuristik, nicht B2/B3,
  kein Verdict-Gate. Ein anwachsendes C waere das Signal eines
  Bias-Drifts Richtung Siegel-Null-Skala (x^{2 beta - 1} fuer beta > 1/2).

  Epistemische Einordnung: das kleine Ende ist das HARTE Ende — der
  relative Race-Term q(q-1) sigma^2/(m-q)^2 ist bei kleinem m maximal
  (Phase 7 testete genau dort); asymptotisch wird das Modell EXAKT.
  Die Finitheit der Tests ist keine Schwaeche der Theorie, sondern die
  konservative Seite.

ANTI-SHARPSHOOTER: q=7-Prereg (registrierte Sieb-Counts, EXAKTE
B2-Vorhersagen, Baender, Residual-Schranken, d-Invarianz-Schranken,
Verdict-Map) wird VOR der ersten q=7-DFT-Messung gefroren (md5) und
VOR der Auswertung committet. Die q=7-Punkte sind Out-of-Family in
ZWEI Dimensionen gleichzeitig (q=7 nie gemessen; P >> d Wraparound-
Regime nie gemessen). Die Band-Punkte sind asymptotisch erzwungen
(B3) — der scharfe neue Inhalt ist die EXAKTidentität (Residual)
und die d-Invarianz bei Wraparound, nicht das Band.

0 QPU: reine Arithmetik — numpy-Sieb + FFT ueber Count-Vektoren,
offline, kein Quanten-SDK.
"""

import functools
import hashlib
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_ququint_multin as mn
import pt_ramanujan_replication as rr
import pt_ram_q_zyklizitaet as rq

# === Konstanten ===

EXPERIMENT = "041-ram-q-asymptotik"
HYPOTHESIS = "H-RAM-Q-2"
PREREG_PATH = "pt_ram_q7_asymptotik_prereg.json"
RESULTS_PATH = "pt_ram_q_asymptotik_results.json"
PLAN_PATH = "~/.claude/plans/riemann-phase-ram-q-zyklizitaet.md"

Q3_PREREG_MD5 = "bd9dfee77b9fada8a230347f9d45f5a7"  # EXPERIMENT 040

# (iii) q -> unendlich: q=7 blind out-of-family (6 Race-Klassen, die
# Zweiklassen-Kollaps-Identität von q=3 existiert dort NICHT).
Q7 = 7
D7_GRID = (49, 2401)        # 7^2, 7^4 — Spiegel von (9, 729) bei q=3
D7_PRIMARY = 2401
P7_NULL_DESKRIPTIV = 17     # m = pi(17) = 7 = q: exakte Null-Analog zu (5,9)
P7_BAND_POINTS = (10**4, 10**5, 10**6, 10**7)

# (ii) P -> unendlich: deskriptive Skans (B3-Konvergenz)
SCAN_Q = (3, 5)
SCAN_D = {3: 729, 5: 625}   # dieselben Register wie Phase 7 / 034
SCAN_P_GRID = (10**3, 10**4, 10**5, 10**6, 10**7)   # prereg-Gitter
SCAN_P_EXTENSION = 10**8    # deskriptive Erweiterung JENSEITS des Preregs

# Band + Schranken (Spiegel von rq.BAND_LO/HI)
BAND_LO = 0.8
BAND_HI = 1.25
RESIDUAL_TOL = 1e-10        # |share_DFT - share_B2| (erwartet ~1e-16)
D_INV_TOL = 1e-10           # |d1*share1 - d2*share2| relativ
NULL_TOL = 1e-12            # T6: gemessen == q*sigma^2/(dm) an m=q
TOLERANCE = 1e-9
ANCHOR_TOL = 1e-12          # T1: B2-Ratio vs. V2-Anker (relativ)
FALSIFIER_MIN_OUTSIDE = 2   # Spiegel von rq: >= 2 Band-Brueche = REFUTED

# Deskriptive Erwartungen (KEINE Verdict-Gates — Heuristik, nicht B2/B3)
SLOPE_BAND = (-1.5, -0.5)
C_MAX = 1e4

VERDICT_CONFIRMED = "H-RAM-Q-2_Q_UNIVERSALITAET_ASYMPTOTIK_CONFIRMED"
VERDICT_PARTIAL = "H-RAM-Q-2_PARTIAL"
VERDICT_REFUTED = "H-RAM-Q-2_REFUTED_Q_UNIVERSALITAET_KOLLABIERT"
VERDICT_INVALID = "EVALUATION_INVALID_KONTROLLE_GESCHEITERT"


# === B2: q-universelle EXAKTidentität ===

def class_dispersion(counts):
    """sigma^2 = sum_{r=1}^{q-1} (n_r - A/(q-1))^2, A = m - n_0.

    Fuer q=3: sigma^2 = 2*delta^2 (Zweiklassen-Kollaps).
    """
    counts = list(counts)
    q = len(counts)
    rest = counts[1:]
    a_bar = sum(rest) / (q - 1)
    return sum((n - a_bar) ** 2 for n in rest)


def unified_identity_share(counts, d):
    """B2 EXAKTidentität (geschlossene Form, n0 beliebig):

    share* = (m - q*n0)^2/((q-1)*d*m) + q*sigma^2/(d*m).

    Fuer sigma^2 = 0 bit-kompatibel zu rq.model_share_star_q (n0=1).
    """
    counts = list(counts)
    q = len(counts)
    m = sum(counts)
    n0 = counts[0]
    sigma2 = class_dispersion(counts)
    model = (m - q * n0) ** 2 / ((q - 1) * float(d) * m)
    return model + q * sigma2 / (float(d) * m)


def unified_identity_share_closed(counts, d):
    """B2 in der direkten Expansionsform (gleicher Wert, andere Algebra):

    share* = [(q-1) n0^2 - 2 n0 A + q sum n_r^2 - A^2]/(d*m),
    A = m - n0.  Zwei Formen muessen uebereinstimmen (Test).
    """
    counts = list(counts)
    q = len(counts)
    m = sum(counts)
    n0 = counts[0]
    A = m - n0
    total = ((q - 1) * n0 ** 2 - 2 * n0 * A
             + q * sum(n * n for n in counts[1:]) - A ** 2)
    return total / (float(d) * m)


def unified_ratio(counts):
    """gemessen/Modell = 1 + q(q-1)*sigma^2/(m-q*n0)^2  (m > q*n0).

    Fuer Primes ist n0 = 1: die registrierte Form 1 + q(q-1)sigma^2/(m-q)^2.
    Strukturkorollar: >= 1 IMMER (sigma^2 >= 0, Nenner > 0). None bei
    m <= q*n0 (Modell-Null: der Race-Term IST die gesamte Masse bzw. das
    Modell verschwindet — Ratio undefiniert).
    """
    counts = list(counts)
    q = len(counts)
    m = sum(counts)
    n0 = counts[0]
    if m <= q * n0:
        return None
    return 1.0 + q * (q - 1) * class_dispersion(counts) / (m - q * n0) ** 2


def race_only_share(counts, d):
    """B2 an der Modell-Null (m = q): share* = q*sigma^2/(d*m) EXAKT —
    der Race-Term IST die gesamte Fingerprint-Masse (q=3: (5,9) = 2/9;
    q=7: (17,49))."""
    counts = list(counts)
    q = len(counts)
    m = sum(counts)
    return q * class_dispersion(counts) / (float(d) * m)


# === Skalierbare Arithmetik (numpy-Sieb + FFT ueber Count-Vektoren) ===

@functools.lru_cache(maxsize=8)
def numpy_primes(N):
    """Primzahlen <= N als numpy-Array (Sieb des Eratosthenes, bool-Masken).

    Deterministisch; gegen pt_prime_state.sieve_primes bit-exakt
    verifiziert (Test). lru_cache: N <= 10^8 kostet < 1 s, max ~170 MB.
    Read-only behandeln ( Rueckgabe wird geteilt).
    """
    mask = np.ones(N + 1, dtype=bool)
    mask[:2] = False
    for p in range(2, int(N ** 0.5) + 1):
        if mask[p]:
            mask[p * p::p] = False
    return np.nonzero(mask)[0]


def counts_mod(P, mod):
    """(m, counts) fuer Residuen mod `mod` der Primes <= P (numpy-Schnellpfad)."""
    pr = numpy_primes(P)
    counts = np.bincount(pr % mod, minlength=mod)
    return int(pr.size), [int(c) for c in counts]


def profile_from_count_vector(cnt_d, d):
    """Einzelregister-Profil aus dem Residuen-Count-Vektor mod d — ABSOLUTE
    Konvention: prof(a) = |G(a)|^2/(d*m), KEINE Renormalisierung.

    Konventionsbefund (vor dem Freeze geklaert, entscheidend fuer
    Wraparound): G(a) = sum_r cnt[r] * omega_d^{a r} ist der DFT des
    Count-Vektors und identisch zu mn.single_register_profile's G fuer
    denselben Support (|G|^2 unempfindlich gegen das Vorzeichen im
    Exponenten). ABER: Parseval ueber den Support gibt
    sum_a |G(a)|^2 = d * sum_r n_r^2, nicht d*m — die Renormalisierung
    prof/prof.sum() in mn ist nur dann ein No-op, wenn alle n_r in {0,1}
    (d.h. P <= d, keine Kollisionen). ALLE 21 gefrorenen 040-Punkte lagen
    bei P <= d, dort war die Konvention unsichtbar (Residual 3.2e-16).
    Bei Wraparound (P >> d) wuerde die Renormalisierung das B2-Theorem
    brechen (direct geprueft: (211,81) Residual 6.5e-2 unter mn-Pfad).
    Diese Phase misst deshalb ABSOLUT; bei P <= d fallen beide
    Konventionen zusammen (Test bindet mn bei P < d bit-nahe).
    """
    cnt = np.asarray(cnt_d, dtype=float)
    m = int(cnt.sum())
    G = np.fft.fft(cnt)
    return np.abs(G) ** 2 / (float(d) * m)


def measure_share(P, d, q):
    """(share, counts_q, m) im Schnellpfad: Sieb -> Counts mod d ->
    FFT-Profil -> rq.share_star_q; Counts mod q fuer B2."""
    pr = numpy_primes(P)
    m = int(pr.size)
    cnt_d = np.bincount(pr % d, minlength=d)
    prof = profile_from_count_vector(cnt_d, d)
    share = rq.share_star_q(prof, d, q)
    counts_q = np.bincount(pr % q, minlength=q)
    return share, [int(c) for c in counts_q], m


def identity_residual(P, d, q):
    """|share_DFT - share_B2| an einem echten Prime-Punkt (B2-Verifikation
    an der Skala; erwartet ~1e-16, Schranke RESIDUAL_TOL)."""
    share, counts, m = measure_share(P, d, q)
    predicted = unified_identity_share(counts, d)
    return abs(share - predicted), share, counts, m


def d_invariance_residual(P, d1, d2, q):
    """|d1*share1 - d2*share2| relativ (d-Invarianz-Theorem bei Skala)."""
    s1, _, _ = measure_share(P, d1, q)
    s2, _, _ = measure_share(P, d2, q)
    scale = 0.5 * (d1 * s1 + d2 * s2)
    return abs(d1 * s1 - d2 * s2) / scale, s1, s2


# === Deskriptive Skans (B3-Konvergenz) ===

def scan_row(P, q, d):
    """Eine Skan-Zeile: Counts, sigma^2, Modell, B2-Share, Ratio, C=P*(ratio-1)."""
    m, counts = counts_mod(P, q)
    model = rq.model_share_star_q(P, d, q)
    share_b2 = unified_identity_share(counts, d)
    ratio = unified_ratio(counts)
    c_p = P * (ratio - 1.0) if ratio is not None else None
    return {
        "P": P, "d": d, "pi": m,
        "residue_counts": counts,
        "sigma2": class_dispersion(counts),
        "model": model,
        "share_b2": share_b2,
        "ratio": ratio,
        "c_p": c_p,
    }


def loglog_slope(rows):
    """Least-Squares-Slope von log(ratio-1) gegen log(P) (deskriptiv).

    ValueError, wenn ein Punkt ratio <= 1 (Strukturkorollar verbietet
    ratio < 1; ratio == 1 waere Aequipartition — dann kein Log definiert).
    """
    xs = [math.log(r["P"]) for r in rows]
    ys = []
    for r in rows:
        y = r["ratio"] - 1.0
        if y <= 0.0:
            raise ValueError(f"ratio-1 <= 0 bei P={r['P']} — kein Log")
        ys.append(math.log(y))
    n = len(rows)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den


# === q=7-Prereg (Freeze VOR jeder q=7-DFT-Messung) ===

def q7_point_payload(P, d):
    """Registrierte Sieb-Arithmetik + EXAKTE B2-Vorhersagen fuer einen Punkt.

    Counts/Vorhersagen sind deterministische Arithmetik (dieselbe
    epistemische Klasse wie residue_counts_mod3 im Phase-7-Prereg);
    die DFT-Messung des Profils erfolgt ERST nach dem Freeze-Commit.
    """
    m, counts = counts_mod(P, Q7)
    model = (m - Q7) ** 2 / ((Q7 - 1) * float(d) * m) if m > Q7 else 0.0
    sigma2 = class_dispersion(counts)
    ratio_pred = unified_ratio(counts)
    return {
        "P": P, "d": d, "pi": m,
        "model": model,
        "band_lo": BAND_LO * model if m > Q7 else None,
        "band_hi": BAND_HI * model if m > Q7 else None,
        "gated": m > Q7 and d == D7_PRIMARY,
        "role": "null_deskriptiv" if m == Q7 else "band",
        "residue_counts_mod7": counts,
        "sigma2": sigma2,
        "b2_share_exact": unified_identity_share(counts, d),
        "ratio_pred_exact": ratio_pred,
    }


def build_prereg_payload():
    point_specs = [(P7_NULL_DESKRIPTIV, D7_GRID[0])]
    point_specs += [(P, D7_PRIMARY) for P in P7_BAND_POINTS]
    points = [q7_point_payload(P, d) for P, d in point_specs]
    return {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "registered_before": (
            "Baustein B2 VOR dem Freeze im Modul hergeleitet (q-universelle "
            "EXAKTidentitaet): share* = (m-q*n0)^2/((q-1)dm) + q*sigma^2/(dm) "
            "mit sigma^2 = Klassendispersion — Verallgemeinerung der q=3-"
            "Zweiklassen-Identitaet (EXPERIMENT 040, md5 bd9dfee7) auf ALLE q; "
            "verifiziert gegen die gefrorenen q=5- (034, md5 a2fc4875) und "
            "q=3-Konstanten. Die DFT-Profil-Messung der q=7-Punkte wurde VOR "
            "diesem Freeze NICHT berechnet; der Freeze bindet registrierte "
            "Sieb-Counts, EXAKTE B2-Vorhersagen, Baender, Residual- und "
            "d-Invarianz-Schranken, Kontrollfamilie und Verdict-Map."),
        "model": {
            "general_identity": (
                "share*_q = (m-q*n0)^2/((q-1)*d*m) + q*sigma^2/(d*m) EXAKT "
                "fuer alle ganzzahligen Counts; sigma^2 = sum_{r=1}^{q-1} "
                "(n_r - A/(q-1))^2, A = m - n0"),
            "ratio_identity": "gemessen/Modell = 1 + q(q-1)*sigma^2/(m-q)^2 "
                              "(n0=1, m>q)",
            "structural_corollary": "ratio >= 1 IMMER (sigma^2 >= 0) — "
                                    "einseitiges Band, nur der obere Rand "
                                    "1.25 ist Falsifikator",
            "d_invariance_theorem": "d*share**m haengt NUR von den Counts mod "
                                    "q ab — exakt fuer alle d=q^k, inkl. "
                                    "Wraparound P >> d",
            "q3_specialization": "sigma^2 = 2*delta^2 -> gefrorene "
                                 "Zweiklassen-Identitaet aus 040",
            "q5_specialization": "sigma^2 = 0 (Aequipartition) -> gefrorene "
                                 "034-Formel (m-5)^2/(4dm)",
        },
        "asymptotic_theorem_b3": {
            "statement": "ratio - 1 = q(q-1)*sigma^2/(m-q)^2 -> 0 fuer "
                         "P -> unendlich, q fest (PNT-AP)",
            "unconditional": "Siegel-Walfisz (ineffektiv): ratio - 1 = "
                             "O(e^{-c sqrt(log x)} log^2 x) -> 0; das Band "
                             "[0.8, 1.25] liegt schliesslich vollstaendig",
            "grh_effective": "sigma_r = O(sqrt(x) log^2 x) -> ratio - 1 = "
                             "O(log^6 x / x)",
            "heuristic_deskriptiv": "Chebyshev/Rubinstein-Sarnak-Bias "
                                    "c*sqrt(x)/log x -> ratio - 1 ~ C/x mit "
                                    "C = q(q-1)^2 c^2 = O(1), Log-Log-Slope "
                                    "~ -1 — DESKRIPTIVE Erwartung, kein Gate",
            "epistemic_point": "kleines m ist das HARTE Ende (relativer "
                               "Race-Term maximal); das empirische Fenster "
                               "ist die konservative Seite, nicht die "
                               "optimistische",
        },
        "extraordinarity_score": {
            "score": 6, "max": 10,
            "reason": "Out-of-Family in ZWEI Dimensionen gleichzeitig (q=7 "
                      "nie gemessen — 6 Race-Klassen ohne Zweiklassen-Kollaps; "
                      "P >> d Wraparound-Regime nie gemessen) mit EXAKT-"
                      "Vorhersagen aus reiner Algebra. Aber: die Band-Punkte "
                      "sind asymptotisch erzwungen (B3) — der scharfe Inhalt "
                      "ist die Identitaet (Residual) und die d-Invarianz bei "
                      "Wraparound, nicht das Band. Theorem-Konsistenz, kein "
                      "Grade-Minting (B-Klasse).",
        },
        "q7_family": {
            "q": Q7,
            "d_grid": list(D7_GRID),
            "phi_q_classes": Q7 - 1,
            "note": "6 Race-Klassen — die q=3-Zweiklassen-Kollaps-Identitaet "
                    "existiert hier NICHT; B2 ist der einzige Weg zur "
                    "exakten Vorhersage",
        },
        "prime_points": points,
        "model_by_point": {f"{pt['P']}@{pt['d']}": pt["b2_share_exact"]
                           for pt in points},
        "gated_points": [[pt["P"], pt["d"]] for pt in points if pt["gated"]],
        "gate": {
            "criteria": [
                "Alle 4 Band-Punkte liegen auf d=7^4=2401 mit m >= pi(10^4) "
                "= 1229; Separations-Kriterium: band_lo >= 3x generisch "
                "(generisch = (q-1)/d = 6/2401 = 0.00249896; band_lo(10^4) "
                "= 0.8 * 0.084341 = 0.067473, Faktor ~27 ueber generisch).",
                "(17,49) ist rein deskriptiv (m = q = 7: Modell-Null, "
                "gemessen = q*sigma^2/(dm) = 2/49 EXAKT via B2).",
            ],
        },
        "thresholds": {
            "band_lo": BAND_LO, "band_hi": BAND_HI,
            "residual_tol": RESIDUAL_TOL,
            "d_inv_tol": D_INV_TOL,
            "null_tol": NULL_TOL,
            "anchor_tol": ANCHOR_TOL,
            "tolerance": TOLERANCE,
        },
        "deskriptive_expectations": [
            {"name": "slope_q3", "prediction": "Log-Log-Slope von ratio-1 "
             "ueber das Skan-Gitter in [−1.5, −0.5] (Heuristik C/x mit "
             "C = 3*4*c^2, c = O(1))", "kind": "heuristik_kein_gate"},
            {"name": "slope_q5", "prediction": "Log-Log-Slope von ratio-1 "
             "ueber das Skan-Gitter in [−1.5, −0.5] (C = 5*16*c^2)",
             "kind": "heuristik_kein_gate"},
            {"name": "c_max", "prediction": "C(P) = P*(ratio-1) <= 1e4 auf "
             "allen Skan-Punkten (Bindung gegen Bias-Drift Richtung "
             "Siegel-Null-Skala x^{2 beta - 1})", "kind": "heuristik_kein_gate"},
            {"name": "envelope", "prediction": "ratio-1(10^7) < ratio-1(10^3) "
             "fuer q in {3,5} (Konvergenz-Richtung, nicht Monotonie)",
             "kind": "heuristik_kein_gate"},
        ],
        "controls": {
            "t1_q5_anchor": (
                "B2-Ratio bei (625, 625), q=5 (Counts mod 5 via "
                "rq.residue_counts, Sieb-Arithmetik): 1 + 20*sigma^2/(m-5)^2 "
                "muss den V2-Anker reproduzieren: |ratio_B2 - "
                "V2_SHARE_STAR_PRIME_COMMITTED/rr.model_share_star(625,625)| "
                "relativ <= 1e-12 — der bislang unbemerkte q=5-Race-Term "
                "erklaert die 034-Ratio 1.0248 exakt"),
            "t2_q3_bridge": (
                "B2 ≡ delta_identity_analytic auf den GEFRORENEN q=3-Prereg-"
                "Counts (EXPERIMENT 040 md5 bd9dfee7, md5-verifiziert "
                "geladen): rel. Differenz <= 1e-15 an allen 21 Punkten — "
                "keine neue Messung, nur Algebra-Konsistenz"),
            "t3_d_invariance_q3": (
                "d*share invariant bei (729, 729), q=3, ueber d in "
                "{9, 81, 729} im Schnellpfad, rel. <= 1e-9 (Spiegel der "
                "Phase-7-Kontrolle an der Skala)"),
            "t4_ratio_ge_1_structural": (
                "ratio >= 1 - 1e-12 an allen Skan- und q=7-Band-Punkten "
                "(Strukturkorollar; Verletzung = Algorithmus-/Praemissen-"
                "Bug -> INVALID, nicht REFUTED"),
            "t5_gate_set_frozen": (
                "gated Set = genau die 4 registrierten Punkte auf d=2401"),
            "t6_null_points_exact": (
                "m=q-Null-Punkte: gemessen == q*sigma^2/(dm) exakt (tol "
                "1e-12) an (17,49) q=7 UND (5,9) q=3 (Schnellpfad) — "
                "der Race-Term IST die gesamte Masse"),
        },
        "verdict_map": {
            VERDICT_CONFIRMED: "alle 4 Band-Punkte im Band UND Residual "
                               "<= 1e-10 an allen q=7-Punkten UND d-Invarianz "
                               "<= 1e-10 UND T1-T6 gruen",
            VERDICT_PARTIAL: "exakt 1 Band-Punkt ausserhalb, Rest gruen",
            VERDICT_REFUTED: ">= 2 Band-Punkte ausserhalb ODER Residual > "
                             "1e-10 ODER d-Invarianz gebrochen (T4 -> "
                             "INVALID, nicht REFUTED)",
            VERDICT_INVALID: "T1/T2/T3/T5/T6 gescheitert oder T4 verletzt "
                             "(Anker/Algebra/Struktur) — Auswertung void",
        },
        "scan_registration": {
            "q_values": list(SCAN_Q),
            "d_by_q": {str(q): SCAN_D[q] for q in SCAN_Q},
            "p_grid": list(SCAN_P_GRID),
            "p_extension_deskriptiv": SCAN_P_EXTENSION,
            "note": "Skans sind DESKRIPTIV (B3-Konvergenzverifikation), "
                    "keine Band-Gates; Slope/C/envelope als deskriptive "
                    "Erwartungen registriert",
        },
        "qpu": "0 QPU — reine Arithmetik (numpy-Sieb + FFT), offline, "
               "kein Quanten-SDK",
        "plan": PLAN_PATH,
        "q3_reference_chain": {
            "experiment_040_prereg_md5": Q3_PREREG_MD5,
            "experiment_034_prereg_md5": "a2fc4875e10dd198e95d4996b1692759",
            "v2_share_star_prime_committed": rr.V2_SHARE_STAR_PRIME_COMMITTED,
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
        raise ValueError(f"RAM-Q-Asymptotik-Prereg-md5-MISMATCH in {path}")
    return doc


# === Auswertung (NUR nach dem Freeze-Commit) ===

def run_evaluation(prereg_path=PREREG_PATH):
    doc = load_frozen_prereg(prereg_path)

    q7_rows = []
    residuals = []
    d_invs = []
    outside = 0
    for pt in doc["prime_points"]:
        P, d = pt["P"], pt["d"]
        share, counts, m = measure_share(P, d, Q7)
        residual = abs(share - pt["b2_share_exact"])
        residuals.append({"P": P, "d": d, "residual": residual})
        row = {
            "P": P, "d": d, "pi": m,
            "residue_counts_mod7": counts,
            "sigma2": class_dispersion(counts),
            "model": pt["model"],
            "b2_share_exact": pt["b2_share_exact"],
            "share_measured": share,
            "residual": residual,
            "gated": pt["gated"],
            "role": pt["role"],
            "in_band": None,
            "ratio_measured": None,
            "ratio_pred_exact": pt["ratio_pred_exact"],
        }
        if pt["ratio_pred_exact"] is not None:
            ratio = share / pt["model"]
            row["ratio_measured"] = ratio
            row["in_band"] = bool(
                pt["band_lo"] <= share <= pt["band_hi"])
            if not row["in_band"]:
                outside += 1
        q7_rows.append(row)

    # d-Invarianz an allen Band-Punkten (Wraparound-Regime, neu)
    for pt in doc["prime_points"]:
        if pt["gated"]:
            inv, s1, s2 = d_invariance_residual(pt["P"], D7_GRID[0],
                                                D7_GRID[1], Q7)
            d_invs.append({"P": pt["P"], "d_pair": list(D7_GRID),
                           "residual": inv,
                           "share_d49": s1, "share_d2401": s2})

    # T1: q=5-Anker-Tie (B2-Ratio vs. V2-committed/Modell)
    _, counts5 = counts_mod(625, 5)
    ratio_b2_q5 = unified_ratio(counts5)
    anchor_ratio = (rr.V2_SHARE_STAR_PRIME_COMMITTED
                    / rr.model_share_star(625, 625))
    t1_ok = math.isclose(ratio_b2_q5, anchor_ratio, rel_tol=ANCHOR_TOL)

    # T2: B2 ≡ delta_identity_analytic auf den gefrorenen q=3-Counts
    q3 = rq.load_frozen_prereg()
    t2_ok = True
    t2_worst = 0.0
    for pt in q3["prime_points"]:
        counts = pt["residue_counts_mod3"]
        b2 = unified_identity_share(counts, pt["d"])
        delta = rq.delta_identity_analytic(counts[1], counts[2], pt["d"])
        diff = abs(b2 - delta) / max(abs(delta), 1e-300)
        t2_worst = max(t2_worst, diff)
        if diff > 1e-15:
            t2_ok = False

    # T3: d-Invarianz q=3 an der Skala
    t3_inv, _, _ = d_invariance_residual(729, 9, 729, 3)
    t3_ok = t3_inv <= TOLERANCE

    # Skans (deskriptiv) + T4
    scans = {}
    t4_ok = True
    for q in SCAN_Q:
        d = SCAN_D[q]
        rows = [scan_row(P, q, d) for P in SCAN_P_GRID]
        ext = scan_row(SCAN_P_EXTENSION, q, d)
        for row in rows + [ext]:
            if row["ratio"] is not None and row["ratio"] < 1.0 - 1e-12:
                t4_ok = False
        for row in q7_rows:
            if row["ratio_measured"] is not None \
                    and row["ratio_measured"] < 1.0 - 1e-12:
                t4_ok = False
        slope = loglog_slope(rows)
        c_max = max(r["c_p"] for r in rows)
        envelope_ok = rows[-1]["ratio"] - 1.0 < rows[0]["ratio"] - 1.0
        slope_ok = slope is not None and SLOPE_BAND[0] <= slope <= SLOPE_BAND[1]
        scans[str(q)] = {
            "rows": rows,
            "extension_row_deskriptiv": ext,
            "slope": slope,
            "slope_in_registered_band": slope_ok,
            "c_max_prereg_grid": c_max,
            "c_max_ok": c_max <= C_MAX,
            "envelope_decreasing": envelope_ok,
        }

    # T6: m=q-Null-Punkte exakt
    s7, counts7_17, _ = measure_share(P7_NULL_DESKRIPTIV, D7_GRID[0], Q7)
    t6_res_7 = abs(s7 - race_only_share(counts7_17, D7_GRID[0]))
    s3, counts3_5, _ = measure_share(5, 9, 3)
    t6_res_3 = abs(s3 - race_only_share(counts3_5, 9))
    t6_ok = t6_res_7 <= NULL_TOL and t6_res_3 <= NULL_TOL

    # T5: Gate-Set gefroren
    eval_gated = sorted([r["P"] for r in q7_rows if r["gated"]])
    t5_ok = eval_gated == sorted(P7_BAND_POINTS)

    controls = {
        "t1_q5_anchor": t1_ok,
        "t2_q3_bridge": t2_ok,
        "t3_d_invariance_q3": t3_ok,
        "t4_ratio_ge_1_structural": t4_ok,
        "t5_gate_set_frozen": t5_ok,
        "t6_null_points_exact": t6_ok,
    }
    control_details = {
        "t1": {"ratio_b2_q5": ratio_b2_q5, "anchor_ratio": anchor_ratio,
               "abs_diff": abs(ratio_b2_q5 - anchor_ratio)},
        "t2_worst_rel_diff": t2_worst,
        "t3_residual": t3_inv,
        "t6": {"residual_17_49_q7": t6_res_7, "residual_5_9_q3": t6_res_3},
    }

    residual_fail = any(r["residual"] > RESIDUAL_TOL for r in residuals)
    d_inv_fail = any(r["residual"] > D_INV_TOL for r in d_invs)

    # Verdict-Map (per Prereg): T1/T2/T3/T5/T6 + T4 sind Struktur-/Anker-
    # Kontrollen — ihr Scheitern ist ein Algorithmus-Bug (INVALID), kein
    # Theorie-Fehlschlag. Falsifikation des Theorems nur ueber Band-Brueche
    # (>= 2), Identitaets-Residual oder d-Invarianz.
    hard = (controls["t1_q5_anchor"] and controls["t2_q3_bridge"]
            and controls["t3_d_invariance_q3"]
            and controls["t5_gate_set_frozen"]
            and controls["t6_null_points_exact"])
    if not t4_ok or not hard:
        verdict = VERDICT_INVALID
    elif outside >= FALSIFIER_MIN_OUTSIDE or residual_fail or d_inv_fail:
        verdict = VERDICT_REFUTED
    elif outside == 1:
        verdict = VERDICT_PARTIAL
    else:
        verdict = VERDICT_CONFIRMED

    return {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "verdict": verdict,
        "prereg_md5": doc["md5"],
        "qpu_jobs": 0,
        "q7_rows": q7_rows,
        "identity_residuals": residuals,
        "d_invariance": d_invs,
        "gated_total": sum(1 for r in q7_rows if r["gated"]),
        "gated_outside": outside,
        "max_residual": max(r["residual"] for r in residuals),
        "max_d_inv_residual": max(r["residual"] for r in d_invs),
        "scans": scans,
        "deskriptive_checks": {
            str(q): {
                "slope": scans[str(q)]["slope"],
                "slope_in_registered_band": scans[str(q)]["slope_in_registered_band"],
                "c_max": scans[str(q)]["c_max_prereg_grid"],
                "envelope_decreasing": scans[str(q)]["envelope_decreasing"],
            } for q in SCAN_Q
        },
        "controls": controls,
        "control_details": control_details,
        "b3_note": "Theorem-Schicht: ratio -> 0 Abweichung unconditionally "
                   "(Siegel-Walfisz, ineffektiv); effektiv unter GRH "
                   "O(log^6 x/x); Skans verifizieren die Konvergenzrichtung "
                   "deskriptiv bis 10^8",
    }


def main():
    res = run_evaluation()
    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    print(f"VERDICT: {res['verdict']}")
    print(f"gated: {res['gated_total']} total, {res['gated_outside']} outside")
    print(f"max residual: {res['max_residual']:.3e}")
    print(f"max d-invariance residual: {res['max_d_inv_residual']:.3e}")
    for q in SCAN_Q:
        dc = res["deskriptive_checks"][str(q)]
        print(f"q={q}: slope {dc['slope']:.4f} (band {list(SLOPE_BAND)}), "
              f"C_max {dc['c_max']:.4g}")
    for r in res["q7_rows"]:
        print(f"q7 {r['P']}@{r['d']}: model {r['model']:.6f} "
              f"measured {r['share_measured']:.6f} "
              f"ratio {r['ratio_measured']} in_band {r['in_band']}")
    return 0 if res["verdict"] in (VERDICT_CONFIRMED, VERDICT_PARTIAL) else 1


if __name__ == "__main__":
    sys.exit(main())