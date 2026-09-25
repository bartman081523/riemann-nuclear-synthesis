"""EXPERIMENT 036 Phase 6a — H-STAR-5 AUSFUEHRUNG: exakte klassische
SFF-Ensembles der prime-gefalzten Hamiltonians (0 QPU, reine numpy).

Ausfuehrungs-Prereg (DIESE Datei, VOR der ersten Prime-vs-Null-Auswertung
gefroren, eigenes md5; Skelett-MD5 f915729e fix):

Konstruktion (registriert, deterministisch, kein RNG in der Primaer-
faltung):
  Block:   H_PT_5(gamma) = H_diag_5 + i*gamma*A_5 (EXPERIMENT 011/032)
  Familie: 625-dim, 4-fache Tensor-Summe ueber die registrierte
           V3-Konfigurationsfamilie (78, pt_ququint_gue.family_configs_625)
  Faltung: H_folded = kron_sum(blocks) + eps * Sum_{a<b} s_ab * (A_5 (x) A_5)
           an Positionen (a,b), I sonst
  Zeichen: s_ab = +1 falls (p_b mod p_a) quadratischer Rest mod p_a
           (inkl. 0 = 0*0), sonst -1 — Prim-Residuen-Instruktion
           (Vorzeichen-Instanz der registrierten These; Gewichte/Teilmengen
           bleiben unregistrierte Varianten, s. instantiierungs_noten)
  eps:     0.25 (Viertel der Block-Skala O(1)); Ladder 0.05/0.5 deskriptiv

Spektrum-Konvention (eingefroren):
  Re-Teile der Eigenwerte (Projektkonvention pt_spectral_gaps /
  EXPERIMENT 032), KEIN Kollaps (SFF sieht Multiplizitaeten). Die
  Faktorisierungs-Null Tr e^{-iHt} = Prod_p Tr e^{-iH_p t} gilt am
  Re-Spektrum EXAKT (Re(a+b) = Re(a)+Re(b), Kron-Summen-Spektrum =
  Summenmenge) und ist frei von Wachstums-Artefakten komplexer
  Eigenwerte (nicht-hermitesche PT-Bloecke).

Unfolding-Regel: t_H_c = 2*pi / median(Luecken) des UNGEFALTETEN
Tensor-Summen-Re-Spektrums von Konfiguration c (Kanten-robust, gleiche
Regel fuer Prime/Shuffle/Composite/Kontrollen). Tau-Grid (0.1, 0.5, 2.0).

Observablen:
  O1 (Verdict-relevant): R = <K>(tau2) / <K>(tau1) mit
      <K>(tau) = Mittel ueber Konfigurationen von
      K_norm(tau*t_H_c) = |Sum_k exp(-i*Re(E_k)*tau*t_H_c)|^2 / d
  O1b (deskriptiv): Median der Per-Konfigurations-Ratios
  O2: R2(t) = log K_raw_gefaltet(t) - Sum_p log K_raw_p(t) — fuer die
      UNGEFALTETE Tensor-Summe EXAKT 0 (raw-K, keine d-Normierung);
      Abweichung = Faktorisierungs-Brechung.

Kontrollfamilie (Kontrollen-zuerst-Regel des Skeletts):
  Positiv:  GUE (Ginibre-Hermitisch) — analytischer Ramp K_norm(tau) = tau
            -> R_GUE = tau2/tau1 = 5.0; Gate [3.5, 6.5] MUSS zünden, sonst
            VOID (Protokoll sieht Chaos nicht, wo es nachweislich ist).
  Negativ:  Poisson (iid-uniform) — kein Ramp; Gate [0.2, 1.8].
  Negativ:  Composite-rang-matched (4,6,8,9,10), 034-Idiom — muss im
            Shuffle-Band bleiben.
  Strukturell: Identitaet am Re-Spektrum, tol 1e-9 (Skelett-Fenster).

Verdict-Map (Skelett, unveraenderlich):
  CONFIRMED  H-STAR5_CONFIRMED_PRIME_SFF_SEPARATION
  REFUTED    H-STAR5_REFUTED_INTEGRABLE_IN_ALL_PROBES
  DEGENERAT  H-STAR5_REFUTED_UNTER_NULL_DEGENERAT
  VOID       H-STAR5_VOID_POSITIVKONTROLLE_ZUENDET_NICHT
  INVALID    H-STAR5_INVALID_KONTROLLE_GESCHEITERT
"""

import hashlib
import itertools
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pt_ququint_vqe import H_PT_ququint
from pt_ququint_gue import family_configs_625

PREREG_PATH = "pt_hstar5_execution_prereg.json"
EXPERIMENT = "036-ququint-hstar5-sff-ensemble-phase6a"
HYPOTHESIS = "H-STAR-5"
SKELETON_MD5 = "f915729ef5fb9943c68ec6feeb9a300b"
STATUS = "AUSFUEHRUNG_PREREG_GEFROREN_VOR_MESSUNG"

# === Eingefrorene Konstanten (VOR der ersten Messung) ===

EPS_PRIMARY = 0.25
EPS_LADDER_DESKRIPTIV = (0.05, 0.5)
TAU_GRID = (0.1, 0.5, 2.0)          # tau1, tau2 (Verdict), tau3 (deskriptiv)
TAU1, TAU2, TAU3 = TAU_GRID

N_SHUFFLE = 200
NULL_SEED = 20260923
N_CONTROLS = 100
Q_UPPER = 0.975
Q_LOWER = 0.025

GUE_GATE = (3.5, 6.5)      # analytisch 5.0 = tau2/tau1 (GUE-Ramp)
POISSON_GATE = (0.2, 1.8)  # kein Ramp (sinc-Effekt an tau1 eingepreist)

O2_THRESHOLD = 1e-6        # echte Brechung vs numerisches Rauschen (~1e-12)
IDENTITY_TOL = 1e-9
K_FACTOR_FLOOR = 1e-12     # O2 skip-Regel an K_p-Nullstellen
MIN_VALID_O2_PAIRS = 100   # von max 78*3 = 234 Paaren

PRIME_SET = (2, 3, 5, 7, 11)
COMPOSITE_SET = (4, 6, 8, 9, 10)
TS_CHECK_EXECUTION = (0.0, 0.31, 1.7, 5.0)  # Skelett-Fenster (Identitaet)

# Verdict-Klassen (Skelett)
V_CONFIRMED = "H-STAR5_CONFIRMED_PRIME_SFF_SEPARATION"
V_REFUTED = "H-STAR5_REFUTED_INTEGRABLE_IN_ALL_PROBES"
V_DEGENERAT = "H-STAR5_REFUTED_UNTER_NULL_DEGENERAT"
V_VOID = "H-STAR5_VOID_POSITIVKONTROLLE_ZUENDET_NICHT"
V_INVALID = "H-STAR5_INVALID_KONTROLLE_GESCHEITERT"

# Lazy (Tests monkeypatchen CONFIG_FAMILY/CANONICAL_FAMILY direkt)
CONFIG_FAMILY = None
CANONICAL_FAMILY = None

# v2-Abweichung vom v1-Freeze (S₄-Schluss-Theorem) — VOR der Messung
# registriert, dokumentiert im Prereg-Feld "deviation_reason".
PREREG_VERSION = 2
PREREG_PATH_V2 = "pt_hstar5_execution_prereg_v2.json"
V1_SUPERSEDED_MD5 = "aa8e77cc3bbd88a0307f3a9f44ccd0c0"


def get_config_family():
    """Registrierte V3-Familie (78 4-Tupel, >= 2 verschiedene gamma)."""
    global CONFIG_FAMILY
    if CONFIG_FAMILY is None:
        CONFIG_FAMILY = tuple(family_configs_625())
    return CONFIG_FAMILY


def canonical_family_configs():
    """Kanonische O1-Familie (v2): ein sortierter Repraesentant je
    gamma-Multimenge — 12 nicht-konstante 4-Tupel ueber (0.002, 0.02, 0.2).

    Grund (S₄-Schluss-Theorem): die 78er-Familie ist unter Block-
    Positions-Permutationen abgeschlossen; jede Familiensumme ist daher
    Orbit-invariant im Zeichen-Muster (v1-Null: genau 2 Atome). Ein
    Repraesentant je Multimenge bricht die Abgeschlossenheit.
    """
    global CANONICAL_FAMILY
    if CANONICAL_FAMILY is None:
        vals = (0.002, 0.02, 0.2)
        CANONICAL_FAMILY = tuple(sorted(set(
            t for t in itertools.product(vals, repeat=4)
            if len(set(t)) > 1 and t == tuple(sorted(t)))))
    return CANONICAL_FAMILY


# === Prereg-Payload (Freeze VOR der ersten Messung) ===

def build_execution_prereg():
    return {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "status": STATUS,
        "qpu": 0,
        "skeleton_md5": SKELETON_MD5,
        "skeleton_path": "pt_hstar5_prereg.json",
        "scope": (
            "Phase 6a: exakte klassische SFF-Ensembles (0 QPU, numpy). "
            "Phase 6b (Aer-Protokoll-Validierung A1) nur bei sichtbarer "
            "Prime-Separation; QPU-Spot-Check nur danach (PLAN.md Phase 6)."),
        "construction": {
            "blocks": "H_PT_ququint(gamma) 5x5 PT-Bloecke (EXPERIMENT 011)",
            "gamma_family": (0.002, 0.02, 0.2),
            "config_family": "pt_ququint_gue.family_configs_625 (78, "
                             "EXPERIMENT 032 Registrierung)",
            "operator_V": "A_5 (Jacobi, real-symmetrisch, pt_ququint_vqe)",
            "folding": "H_folded = kron_sum(blocks) + eps*Sum_{a<b} s_ab*"
                       "(A_5 (x) A_5) an Positionen (a,b)",
            "sign_rule": "+1 falls (p_b mod p_a) quadratischer Rest mod p_a "
                         "(inkl. 0=0*0), sonst -1",
            "prime_set_4": PRIME_SET[:4],
            "composite_set_4": COMPOSITE_SET[:4],
            "eps_primary": EPS_PRIMARY,
            "eps_ladder_deskriptiv": EPS_LADDER_DESKRIPTIV,
            "spectrum_convention": (
                "Re-Teile der Eigenwerte, KEIN Kollaps (SFF sieht "
                "Multiplizitaeten) — Projektkonvention EXPERIMENT 032; "
                "frei von Wachstums-Artefakten nicht-hermitescher "
                "Eigenwerte"),
            "unfolding_rule": (
                "t_H_c = 2*pi/Median der POSITIVEN Luecken (> 1e-12) des "
                "UNGEFALTETEN Tensor-Summen-Re-Spektrums der Konfiguration "
                "c — exakte Multiplizitaeten (identische Bloecke bei "
                "wiederholtem gamma) ergeben Luecken exakt 0 und werden "
                "fuer die Regel ausgeschlossen; die SFF selbst sieht alle "
                "Multiplizitaeten (kein Kollaps). Identische Regel fuer "
                "alle Familien (Prime/Shuffle/Composite/Kontrollen)"),
            "tau_grid": TAU_GRID,
            "k_norm": "|Sum_k exp(-i*Re(E_k)*t)|^2 / d",
            "o2_raw_k": "R2(t) = log K_raw_folded(t) - Sum_p log K_p(t) "
                        "(raw, ohne d-Normierung — sonst keine exakte Null)",
        },
        "observables": {
            "O1": ("R = <K>(tau2)/<K>(tau1), <K> = Mittel ueber die "
                   "kanonische 12er-Familie (v2: ein Repraesentant je "
                   "gamma-Multimenge) — bridge-getreu (Keating-Snaith: "
                   "ensemble-gemittelte SFF)"),
            "O1b_deskriptiv": "Median der Per-Konfigurations-Ratios",
            "O2": ("Median von |R2| ueber gueltige (Config, tau)-Paare der "
                   "PRIME-Instanzen; skip falls K < 1e-12; Mechanismus-Check"
                   ", nicht Verdict-Ersatz"),
        },
        "thresholds": {
            "n_shuffle": N_SHUFFLE,
            "null_seed": NULL_SEED,
            "q_upper": Q_UPPER,
            "q_lower": Q_LOWER,
            "n_controls": N_CONTROLS,
            "gue_gate": GUE_GATE,
            "poisson_gate": POISSON_GATE,
            "o2_mechanism_threshold": O2_THRESHOLD,
            "o2_min_valid_pairs": MIN_VALID_O2_PAIRS,
            "identity_tol": IDENTITY_TOL,
            "k_factor_floor": K_FACTOR_FLOOR,
        },
        "verdict_logic": {
            "rule_1_kontrollen_zuerst": (
                "strukturelle Null exakt UND GUE-Gate UND Poisson-Gate UND "
                "Composite im Shuffle-Band — sonst VOID (GUE zündet nicht) "
                "bzw. INVALID (Kontrollfehler)"),
            "rule_2_confirmed": "R_prime > q_upper UND O2-Mechanismus UND "
                                "Composite im Band",
            "rule_3_refuted": "R_prime im Shuffle-Band [q_lower, q_upper]",
            "rule_4_degenerat": "R_prime < q_lower (super-degenerat, "
                                "REFUTED-zulaessig, Steelman-Lektion)",
            "rule_5_kein_post_hoc_patch": (
                "Fenster/Ensemble/Schwellen eingefroren VOR der ersten "
                "Messung; GaPPen dokumentiert, nicht still korrigiert"),
        },
        "compute_calibration": (
            "VOR der ersten Auswertung kalibriert (Compute, keine Daten): "
            "zgeev 625x625 komplex ~0.47 s -> v2: 78 Prime (O2 auf der "
            "vollen Familie, O1 daraus auf den 12 Kanonischen) + 2*12 "
            "eps-Ladder + 12 Composite + 200*12 Shuffle = 2,514 "
            "Dekompositionen ~20 min CPU, 0 QPU; Kontrollen 2*100 zheevd "
            "~40 s. Checkpoint/Resume pro Shuffle-Instanz."),
        "instantiierungs_noten": (
            "GaPPen dokumentiert (kein stiller Patch): (1) 25-dim-Stufe "
            "enthaelt nur 1 Paar -> Shuffle-Null waere identitaets-"
            "Permutation; Stufe entfaellt. (2) Die registrierte Faltung ist "
            "die VORZEICHEN-Instanz ('Vorzeichen aus Prim-Residuen'); "
            "Gewichte/Teilmengen bleiben unregistrierte Varianten. (3) "
            "3125-dim (5 Bloecke) aus Compute-Budget nicht in dieser "
            "Phase; das 5-elementige Composite-Aequivalent waere "
            "(4,6,8,9,10). (4) Kontroll-n 100 (V3: 50) fuer Gate-"
            "Robustheit des Ramp-Klassifikators, vor der ersten "
            "Auswertung registriert. (5) Composite-Rang-Matching: die 4 "
            "kleinsten Komposita (4,6,8,9) auf denselben 4 Block-"
            "Positionen gegen (2,3,5,7) — gleiche Anzahl, benachbarte "
            "Groessenordnung, 6 Paare wie beim Prime-Fold. (6) "
            "Verwerfungs-Regel: Instanz aus dem r_median-Baustein "
            "ausgeschlossen falls K(tau1) < 1e-12 (destruktive "
            "Interferenz im Referenzpunkt); das Ensemble-O1 "
            "(mean k2/mean k1) verwirft nicht."),
        "version": PREREG_VERSION,
        "supersedes": {
            "md5": V1_SUPERSEDED_MD5,
            "status": ("v1-Freeze (O1 auf der 78er-Familie), nie zu "
                       "Verdict ausgewertet — Lauf bei Shuffle 131/200 "
                       "abgebrochen nach Design-Entdeckung; v1-Artefakte "
                       "archiviert als *_v1_degenerate.*"),
        },
        "deviation_reason": (
            "S₄-Schluss-Theorem: die 78er-Familie ist unter Block-"
            "Positions-Permutationen sigma abgeschlossen; fuer gefaltete "
            "Hamiltonians gilt k(sigma(cfg), s) = k(cfg, sigma.s) "
            "(unitaere Aequivalenz), daher ist JEDE Familiensumme "
            "Orbit-invariant im Zeichen-Muster. Die 15 Zwei-Minus-Muster "
            "fallen in genau 2 S₄-Orbits (benachbart 12 / disjunkt 3); "
            "Prime- und Composite-Zeichen liegen BEIDE im benachbarten "
            "Orbit -> composite_o1 = o1_prime bit-exakt, die Composite-"
            "Kontrolle ist zahnlos. Empirie: 132 v1-Shuffle-Instanzen -> "
            "genau 2 Atome (R=1.082955 n=110, R=1.188108 n=22; 110/132 = "
            "83.3% ~ 12/15 Orbit-Anteil), obwohl 54/78 Konfigurationen "
            "O(1)-Schwankungen der Per-Konfigurations-k zeigen, die sich "
            "in der Familiensumme bis 5.8e-11 exakt heben."),
        "s4_closure_note": (
            "Fix: O1/Composite/Ladder/Shuffle laufen auf der kanonischen "
            "Familie (12 sortierte Repraesentanten je gamma-Multimenge, "
            "gleiche Gewichte) — Zeichen-Regel UNVERAENDERT; O2 bleibt "
            "auf der vollen 78er-Familie (Per-Konfigurations-Residuum, "
            "keine Familiensumme — vom Theorem unberuehrt). Empirische "
            "Verifikation VOR diesem Freeze: alle 15 Zwei-Minus-Muster "
            "geben 15 VERSCHIEDENE R-Werte auf der kanonischen Familie "
            "(Bereich 0.799-1.883) — die Null ist reich."),
        "family_o1": {
            "kind": "canonical",
            "n": 12,
            "rule": ("ein sortierter Repraesentant je gamma-Multimenge "
                     "ueber (0.002, 0.02, 0.2), gleiche Gewichte; "
                     "bricht die S₄-Abgeschlossenheit der O1-Familie"),
        },
        "family_o2": {
            "kind": "full",
            "n": 78,
            "rule": ("pt_ququint_gue.family_configs_625; O2 ist "
                     "Per-Konfigurations-Residuum, keine Familiensumme"),
        },
    }


def payload_md5(payload):
    return hashlib.md5(
        json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def freeze_execution_prereg(payload=None, path=PREREG_PATH):
    if payload is None:
        payload = build_execution_prereg()
    doc = dict(payload)
    doc["md5"] = payload_md5(payload)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    return doc


def verify_execution_prereg_md5(doc):
    body = {k: v for k, v in doc.items() if k != "md5"}
    return payload_md5(body) == doc.get("md5")


def load_frozen_execution_prereg(path=PREREG_PATH):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if not verify_execution_prereg_md5(doc):
        raise ValueError("Ausfuehrungs-Prereg-MD5 verletzt: " + path)
    if doc.get("skeleton_md5") != SKELETON_MD5:
        raise ValueError("Skelett-MD5-Anker verletzt: " + path)
    return doc


# === Zeichen-Regeln (Prim-Residuen) ===

def legendre_sign_rule(a, b):
    """+1 falls (b mod a) quadratischer Rest mod a (inkl. 0), sonst -1."""
    residues = {x * x % a for x in range(a)}
    return +1 if (b % a) in residues else -1


def _signs_for_set(vals, n):
    vs = vals[:n]
    return tuple(legendre_sign_rule(vs[i], vs[j])
                 for i, j in itertools.combinations(range(n), 2))


def prime_signs(n_blocks):
    return _signs_for_set(PRIME_SET, n_blocks)


def composite_signs(n_blocks):
    return _signs_for_set(COMPOSITE_SET, n_blocks)


def shuffle_null_signs(base, n_perm=N_SHUFFLE, seed=NULL_SEED):
    """Permutationen des Zeichen-Multisets (seed-Stream, deterministisch).

    Erhaelt die Multimenge, bricht nur die prime-strukturierte Zuordnung.
    """
    arr = np.asarray(base)
    rng = np.random.default_rng(seed)
    for _ in range(n_perm):
        yield tuple(int(x) for x in rng.permutation(arr))


# === Konstruktion ===

def pt_block(gamma):
    """Registrierter 5x5-PT-Block (EXPERIMENT 011)."""
    return H_PT_ququint(gamma=gamma)[0]


def kron_sum_c(blocks):
    """Tensor-Summe komplexer Bloecke (Kron-Summen-Spektrum = Summenmenge)."""
    n = len(blocks)
    dims = [b.shape[0] for b in blocks]
    d = int(np.prod(dims))
    H = np.zeros((d, d), dtype=complex)
    for i, B in enumerate(blocks):
        left = int(np.prod(dims[:i])) if i else 1
        right = int(np.prod(dims[i + 1:])) if i + 1 < n else 1
        H += np.kron(np.kron(np.eye(left), B), np.eye(right))
    return H


def folded_hamiltonian(config, signs, eps):
    """H_folded = kron_sum(blocks) + eps * Sum_{a<b} s_ab * (A (x) A)_(a,b)."""
    blocks = [pt_block(g) for g in config]
    n = len(blocks)
    dims = [b.shape[0] for b in blocks]
    d = int(np.prod(dims))
    H = kron_sum_c(blocks)
    if eps == 0.0:
        return H
    A = H_PT_ququint(gamma=config[0])[1]
    for idx, (a, b) in enumerate(itertools.combinations(range(n), 2)):
        ops = ["I"] * n
        ops[a] = "A"
        ops[b] = "A"
        term = np.array([[1.0 + 0j]])
        for op in ops:
            M = A if op == "A" else np.eye(5)
            term = np.kron(term, M)
        H = H + eps * signs[idx] * term
    assert H.shape == (d, d)
    return H


# === SFF-Utilities (Re-Konvention, kein Kollaps) ===

def re_eigs(H):
    """Re-Teile der Eigenwerte, aufsteigend sortiert, Multiplizitaeten
    bleiben (Projektkonvention; Kollaps ist eine r-Statistik-Konvention)."""
    return np.sort(np.linalg.eigvals(H).real)


def unfold_spectrum(config):
    """UNGEFALTETES Tensor-Summen-Spektrum via Summenmenge (exakt, ohne
    Matrix-Diagonalisierung) + Heisenberg-Regel (positive Luecken)."""
    ev = np.array([0.0])
    for g in config:
        block_ev = np.linalg.eigvals(pt_block(g))
        ev = (ev[:, None] + block_ev[None, :]).ravel()
    ev_re = np.sort(ev.real)
    return ev_re, heisenberg_time(ev_re)


def heisenberg_time(re_eigs_arr):
    """t_H = 2*pi/Median der POSITIVEN Luecken (Schwelle 1e-12).

    Exakte Multiplizitaeten (identische Bloecke bei wiederholtem gamma ->
    exakt doppelte Summen-Eigenwerte) ergeben Luecken exakt 0; die Regel
    schliesst sie aus. Die SFF selbst (K-Norm, O2) sieht alle
    Multiplizitaeten — kein Kollaps.
    """
    ev = np.sort(np.asarray(re_eigs_arr, dtype=float))
    gaps = np.diff(ev)
    pos = gaps[gaps > 1e-12]
    if pos.size == 0:
        raise ValueError("keine positive Luecke im Spektrum")
    return 2.0 * np.pi / float(np.median(pos))


def trace_exp_re(re_eigs_arr, t):
    return complex(np.sum(np.exp(-1j * re_eigs_arr * t)))


def k_norm(re_eigs_arr, t):
    return abs(trace_exp_re(re_eigs_arr, t)) ** 2 / re_eigs_arr.size


def k_raw(re_eigs_arr, t):
    return abs(trace_exp_re(re_eigs_arr, t)) ** 2


def ratio_stat(re_eigs_arr):
    """O1-Baustein: K(tau2*t_H)/K(tau1*t_H); None falls K(tau1) < 1e-12
    (destruktive Interferenz exakt im Referenzpunkt — Verwerfungs-Regel,
    registriert; ein echtes Spektrum liegt um Groessenordnungen drueber)."""
    t_h = heisenberg_time(re_eigs_arr)
    k1 = k_norm(re_eigs_arr, TAU1 * t_h)
    if not k1 > 1e-12:
        return None
    k2 = k_norm(re_eigs_arr, TAU2 * t_h)
    return k2 / k1


def o2_values(re_eigs_folded, block_re_evs, taus=TAU_GRID):
    """R2(tau) = log K_raw_gefaltet - Sum_p log K_p an den tau-Punkten.

    None an Punkte mit K < K_FACTOR_FLOOR (log-Wache)."""
    t_h = heisenberg_time(re_eigs_folded)
    out = []
    for tau in taus:
        t = tau * t_h
        kf = k_raw(re_eigs_folded, t)
        kps = [k_raw(b, t) for b in block_re_evs]
        if kf < K_FACTOR_FLOOR or min(kps) < K_FACTOR_FLOOR:
            out.append(None)
            continue
        out.append(float(np.log(kf) - np.sum(np.log(kps))))
    return out


def o2_residual(re_eigs_folded, block_re_evs, taus=TAU_GRID):
    """Max |R2| ueber gueltige Punkte (0.0 falls keine gueltigen)."""
    vals = [v for v in o2_values(re_eigs_folded, block_re_evs, taus)
            if v is not None]
    if not vals:
        return 0.0
    return max(abs(v) for v in vals)


# === Kontrollen (V3-Idiom, seed NULL_SEED) ===

def gue_eigs(d, rng):
    g = (rng.standard_normal((d, d))
         + 1j * rng.standard_normal((d, d))) / np.sqrt(2.0)
    return np.linalg.eigvalsh((g + g.conj().T) / 2.0)


def poisson_eigs(d, rng):
    return np.sort(rng.uniform(0.0, float(d), size=d))


def control_ratio_stat(sampler, d, n, seed=NULL_SEED):
    """Ensemble-O1 der Kontrollen: mean(k2)/mean(k1) ueber n Samples.

    Derselbe Estimator wie im Prime-Ensemble (O1-Definition) — NICHT das
    Mittel der Per-Sample-Ratios: k1 ist ~exponential-verteilt, der
    Quotient k2/k1 hat schweren Tail und unendlichen Erwartungswert
    (Empirie vor der Korrektur: GUE 18 statt 5, Poisson 2.3 statt 1.0).
    """
    rng = np.random.default_rng(seed)
    k1s, k2s = [], []
    for _ in range(n):
        ev = np.asarray(sampler(d, rng), dtype=float)
        t_h = heisenberg_time(ev)
        k1s.append(k_norm(ev, TAU1 * t_h))
        k2s.append(k_norm(ev, TAU2 * t_h))
    k1m, k2m = float(np.mean(k1s)), float(np.mean(k2s))
    if not k1m > 1e-300:
        return None
    return k2m / k1m


# === Verdict-Logik (Kontrollen zuerst, Skelett-Regeln 1-4) ===

def verdict(r_prime, shuffle_ratios, controls, o2_ok):
    sh = np.asarray(shuffle_ratios, dtype=float)
    q_lower, q_upper = (float(np.quantile(sh, Q_LOWER)),
                        float(np.quantile(sh, Q_UPPER)))
    if not controls.get("gue_ok", True):
        return {"verdict": "VOID", "verdict_class": V_VOID,
                "q_lower": q_lower, "q_upper": q_upper,
                "reasons": ["Positivkontrolle (GUE-Ramp) zündet nicht"]}
    if not (controls.get("structural_ok", True)
            and controls.get("poisson_ok", True)
            and controls.get("composite_in_band", True)):
        return {"verdict": "INVALID", "verdict_class": V_INVALID,
                "q_lower": q_lower, "q_upper": q_upper,
                "reasons": ["Kontrollfehler (strukturell/Poisson/Composite)"]}
    if r_prime > q_upper and o2_ok:
        return {"verdict": "CONFIRMED", "verdict_class": V_CONFIRMED,
                "q_lower": q_lower, "q_upper": q_upper,
                "reasons": ["Prime über Shuffle-q97.5, O2-Brechung echt, "
                            "Composite sauber"]}
    if r_prime < q_lower:
        return {"verdict": "DEGENERAT", "verdict_class": V_DEGENERAT,
                "q_lower": q_lower, "q_upper": q_upper,
                "reasons": ["Prime UNTER der Shuffle-Null (super-degenerat)"]}
    reasons = []
    if r_prime > q_upper and not o2_ok:
        reasons.append("R ueber q97.5, aber O2-Brechung nicht echt")
    else:
        reasons.append("Prime innerhalb der Shuffle-Null-Verteilung")
    return {"verdict": "REFUTED", "verdict_class": V_REFUTED,
            "q_lower": q_lower, "q_upper": q_upper, "reasons": reasons}


# === Runner Phase 6a ===

def _config_stats(config, eps, signs, block_cache):
    """(R, K1, K2, K3, r_median, o2-Werte) einer (Config, signs)-Instanz."""
    evs = re_eigs(folded_hamiltonian(config, signs, eps))
    t_h = block_cache[config]["t_h"]
    k1 = k_norm(evs, TAU1 * t_h)
    k2 = k_norm(evs, TAU2 * t_h)
    k3 = k_norm(evs, TAU3 * t_h)
    r_med = ratio_stat(evs)
    return evs, {"k1": k1, "k2": k2, "k3": k3,
                 "r_median": r_med}


def run_phase6a(out_path="pt_hstar5_phase6a_v2_results.json",
                n_shuffle=None, n_controls=None, eps=EPS_PRIMARY,
                verbose=True, checkpoint=True):
    """Exakte klassische SFF-Ensembles (0 QPU). Kontrollen zuerst.

    v2 (S₄-Schluss-Fix): O1/Composite/eps-Ladder/Shuffle auf der
    kanonischen 12er-Familie, O2 auf der vollen 78er-Familie.
    Shuffle-Loop mit Checkpoint/Resume (JSONL) — deterministisch, da die
    Permutationen vorab aus dem Seed-Stream gezogen werden.
    """
    prereg_path = PREREG_PATH_V2
    prereg_mode = "live"
    prereg = None
    if os.path.exists(prereg_path):
        try:
            prereg = load_frozen_execution_prereg(prereg_path)
            prereg_mode = "frozen_v2"
        except ValueError:
            prereg = None
    if prereg is None:
        prereg = build_execution_prereg()

    n_shuffle = N_SHUFFLE if n_shuffle is None else n_shuffle
    n_controls = N_CONTROLS if n_controls is None else n_controls
    configs_o1 = canonical_family_configs()
    configs_o2 = get_config_family()

    # Block-/Unfolding-Cache (Konstruktion, konfig-abhaengig, sign-frei)
    # ueber der vollen O2-Familie; die kanonische O1-Familie ist Teilmenge
    cache = {}
    for cfg in configs_o2:
        blocks = [pt_block(g) for g in cfg]
        ev_unf, t_h = unfold_spectrum(cfg)
        # strukturelle Null (Re-Konvention) am ungefalteten Spektrum
        ident_max = 0.0
        for t in TS_CHECK_EXECUTION:
            lhs = trace_exp_re(ev_unf, t)
            rhs = np.prod([trace_exp_re(np.sort(np.linalg.eigvals(B).real), t)
                           for B in blocks])
            ident_max = max(ident_max, abs(lhs - rhs))
        block_re_evs = [np.sort(np.linalg.eigvals(B).real) for B in blocks]
        cache[cfg] = {"blocks": blocks, "t_h": t_h,
                      "block_re_evs": block_re_evs,
                      "identity_max": ident_max}

    structural_ok = all(c["identity_max"] <= IDENTITY_TOL
                        for c in cache.values())
    family_dim = 5 ** len(configs_o2[0])

    # --- Kontrollen zuerst (Regel 1) ---
    r_gue = control_ratio_stat(gue_eigs, family_dim, n_controls)
    r_poisson = control_ratio_stat(poisson_eigs, family_dim, n_controls)
    gue_ok = GUE_GATE[0] <= r_gue <= GUE_GATE[1]
    poisson_ok = POISSON_GATE[0] <= r_poisson <= POISSON_GATE[1]

    if verbose:
        print("Kontrollen: R_GUE=%.3f (Gate %.1f-%.1f, ok=%s) "
              "R_Poisson=%.3f (Gate %.1f-%.1f, ok=%s) "
              "strukturell=%s (max %.2e)"
              % (r_gue, GUE_GATE[0], GUE_GATE[1], gue_ok,
                 r_poisson, POISSON_GATE[0], POISSON_GATE[1], poisson_ok,
                 structural_ok, max(c["identity_max"] for c in
                                    cache.values())))

    # Prime-Instanzen (Zeichen = Identitaets-Zuordnung) auf der vollen
    # O2-Familie (O2 ist Per-Konfigurations-Statistik); die O1-Ensemble-
    # Summen laufen unten auf der kanonischen Teilfamilie
    prime_stats, o2_abs = {}, []
    for cfg in configs_o2:
        evs, st = _config_stats(cfg, eps, prime_signs(len(cfg)), cache)
        prime_stats[cfg] = st
        o2_vals = o2_values(evs, cache[cfg]["block_re_evs"])
        o2_abs.extend(abs(v) for v in o2_vals if v is not None)
    for cfg in configs_o1:      # Teilmenge — sonst hier nachgerechnet
        if cfg not in prime_stats:
            prime_stats[cfg] = _config_stats(cfg, eps,
                                             prime_signs(len(cfg)),
                                             cache)[1]
    k1s = [prime_stats[c]["k1"] for c in configs_o1]
    k2s = [prime_stats[c]["k2"] for c in configs_o1]
    k3s = [prime_stats[c]["k3"] for c in configs_o1]
    r_meds = [prime_stats[c]["r_median"] for c in configs_o1
              if prime_stats[c]["r_median"] is not None]
    k1_mean, k2_mean, k3_mean = (float(np.mean(k1s)), float(np.mean(k2s)),
                                 float(np.mean(k3s)))
    o1_prime = k2_mean / k1_mean
    o1b_median = float(np.median(r_meds)) if r_meds else None

    o2_median = float(np.median(o2_abs)) if o2_abs else 0.0
    o2_n_valid = len(o2_abs)
    o2_ok = (o2_median >= O2_THRESHOLD
             and o2_n_valid >= MIN_VALID_O2_PAIRS)

    # eps-Ladder (deskriptiv, kein Verdict)
    eps_ladder = {}
    for eps_d in EPS_LADDER_DESKRIPTIV:
        if eps_d == eps:
            continue
        ks = [_config_stats(cfg, eps_d, prime_signs(len(cfg)), cache)[1]
              for cfg in configs_o1]
        eps_ladder[str(eps_d)] = {
            "o1": float(np.mean([s["k2"] for s in ks]))
                  / float(np.mean([s["k1"] for s in ks]))}

    # Composite-Null (rang-matched, 034-Idiom) auf der kanonischen Familie
    ck1s, ck2s, cr_meds = [], [], []
    for cfg in configs_o1:
        cevs = re_eigs(folded_hamiltonian(cfg, composite_signs(len(cfg)),
                                          eps))
        t_h = cache[cfg]["t_h"]
        ck1s.append(k_norm(cevs, TAU1 * t_h))
        ck2s.append(k_norm(cevs, TAU2 * t_h))
        rm = ratio_stat(cevs)
        if rm is not None:
            cr_meds.append(rm)
    composite_o1 = float(np.mean(ck2s)) / float(np.mean(ck1s))

    # Shuffle-Null (Multiset erhalten, Zuordnung permutiert) — kanonisch
    base = prime_signs(len(configs_o1[0]))
    perms = list(shuffle_null_signs(base, n_perm=n_shuffle,
                                    seed=NULL_SEED))
    cp = out_path + ".shuffle.jsonl"
    done = {}
    if checkpoint and os.path.exists(cp):
        with open(cp, encoding="utf-8") as fh:
            for line in fh:
                rec = json.loads(line)
                done[rec["j"]] = rec
    shuffle_ratios = []
    for j, perm in enumerate(perms):
        if j in done:
            shuffle_ratios.append(done[j]["R"])
            continue
        s1s, s2s, rms = [], [], []
        for cfg in configs_o1:
            sevs = re_eigs(folded_hamiltonian(cfg, perm, eps))
            t_h = cache[cfg]["t_h"]
            s1s.append(k_norm(sevs, TAU1 * t_h))
            s2s.append(k_norm(sevs, TAU2 * t_h))
            rm = ratio_stat(sevs)
            if rm is not None:
                rms.append(rm)
        rec = {"j": j, "R": float(np.mean(s2s) / np.mean(s1s)),
               "r_median": float(np.median(rms)) if rms else None,
               "k2_mean": float(np.mean(s2s)),
               "k1_mean": float(np.mean(s1s))}
        if checkpoint:
            with open(cp, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
        shuffle_ratios.append(rec["R"])
        if verbose and (j + 1) % 10 == 0:
            print("  shuffle %d/%d R=%.4f" % (j + 1, len(perms), rec["R"]),
                  flush=True)
    shuffle_arr = np.asarray(shuffle_ratios, dtype=float)

    controls = {"structural_ok": structural_ok, "gue_ok": gue_ok,
                "poisson_ok": poisson_ok,
                "composite_in_band": False,  # placeholder, unten ersetzt
                "r_gue": r_gue, "r_poisson": r_poisson,
                "composite_o1": composite_o1}
    q_lower = float(np.quantile(shuffle_arr, Q_LOWER))
    q_upper = float(np.quantile(shuffle_arr, Q_UPPER))
    controls["composite_in_band"] = bool(q_lower <= composite_o1 <= q_upper)

    v = verdict(o1_prime, shuffle_arr, controls, o2_ok)

    res = {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "qpu": 0,
        "prereg_mode": prereg_mode,
        "prereg_md5": prereg.get("md5"),
        "skeleton_md5": SKELETON_MD5,
        "family_o1": {"kind": "canonical", "n": len(configs_o1)},
        "family_o2": {"kind": "full", "n": len(configs_o2)},
        "s4_closure_v1_note": (
            "v1 (O1 auf der 78er-Familie, md5 "
            "aa8e77cc3bbd88a0307f3a9f44ccd0c0): KEIN Verdict — Lauf bei "
            "Shuffle 131/200 abgebrochen, nachdem alle 132 "
            "Shuffle-Instanzen nur 2 Atome zeigten (R=1.082955 n=110, "
            "R=1.188108 n=22): S₄-Schluss-Theorem (Familiensummen sind "
            "Orbit-invariant im Zeichen-Muster; Prime- und Composite-"
            "Zeichen im selben benachbarten Orbit -> Composite-Kontrolle "
            "zahnlos). v2: O1 kanonisch (12), O2 unveraendert voll (78); "
            "v1-Artefakte als *_v1_degenerate.* archiviert."),
        "construction": {"eps": eps, "prime_signs": base,
                         "composite_signs":
                             composite_signs(len(configs_o1[0])),
                         "n_configs_o1": len(configs_o1),
                         "n_configs_o2": len(configs_o2),
                         "dim": family_dim},
        "o1_prime": o1_prime,
        "o1_k": {"k1_mean": k1_mean, "k2_mean": k2_mean,
                 "k3_mean_deskriptiv": k3_mean},
        "o1b_median_deskriptiv": o1b_median,
        "shuffle_null": {"n": len(shuffle_arr), "q_lower": q_lower,
                         "q_upper": q_upper,
                         "median": float(np.median(shuffle_arr)),
                         "ratios": [float(x) for x in shuffle_arr]},
        "composite_o1": composite_o1,
        "o2": {"median_abs": o2_median, "n_valid": o2_n_valid,
               "threshold": O2_THRESHOLD, "ok": o2_ok},
        "eps_ladder_deskriptiv": eps_ladder,
        "controls": controls,
        "verdict": v["verdict"],
        "verdict_class": v["verdict_class"],
        "reasons": v["reasons"],
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    if verbose:
        print("VERDICT: %s (%s) R_prime=%.4f Band [%.4f, %.4f]"
              % (v["verdict"], v["verdict_class"], o1_prime,
                 q_lower, q_upper))
    return res


def main():
    return run_phase6a()


if __name__ == "__main__":
    main()