"""EXPERIMENT 032 - Ququint V1 (H-STAR-2 Layer 1): Leakage-Sieb-Struktur.

Frage: Trägt das DFT-Leakage (~15% der Masse auf den 39 Außen-Bins, §Z.14)
eine mod-5-Residue-Struktur (Sieb-Fingerprint) — oder ist es unstrukturiert
bzw. nur Hardware-/Routing-Struktur?

Anti-Sharpshooter: das Prereg (Vorhersagen + Schwellen + Kontrast-Familie)
wird VOR dem Fetch der Fez-Counts gefroren (md5). Die Counts selbst sind
KEIN neuer QPU-Job — sie werden vom abgeschlossenen Phase-3c-Job
(dakjk9hhvn6c73cvr1cg, committed 9d73edc) re-abgerufen (0 QPU).

Geometrie (Phase-2/3-Konvention, pt_ququint_ibmq_aer):
  64-dim qiskit little-endian Index = k + 8*l
  k = Register A (q0..q2), l = Register B (q3..q5)
  logisch:   k,l <= 4                        -> 25 Bins
  Leakage:   k >= 5 oder l >= 5              -> 39 Bins
  Ein-Leak:  genau ein Register >= 5         -> 30 Bins (10 pro Klasse)
  Doppel-Leak: beide >= 5                    ->  9 Bins
  Residue-Klasse eines Ein-Leak-Bins = (geleakter Wert) mod 5
  -> Werte 5,6,7 tragen Residue 0,1,2; je Klasse 10 Bins (A- und B-Seite).

Statistik (alle Schwellen hier im Prereg, VOR dem Datenblick):
  T1  Flachheit über die 39 Leakage-Bins (chi2, df=38; p < 0.01 = strukturiert)
      Sekundär: Haar/Dirichlet(1)-Null (Random-Unitary-Steelman, 2000 Samples).
  T2  Sieb: Residue-0-Anteil auf den Ein-Leak-Bins >= 1/3 + 0.05 UND
      Ordnung c0 > c1, c0 > c2.
  T3  Look-Elsewhere: Kontrast-Familie benannter Kandidatenklassen
      (val5_r0, val6_r1, val7_r2, sideA, sideB, other_low, other_high);
      z = (Anteil - Groesse/30) / sqrt(p(1-p)/n). mod5 gewinnt nur, wenn
      val5_r0 das Maximum ist UND z >= 2 (Sonst: Struktur = Hardware-Artefakt).
  Negativkontrolle (soft, kein Gate): Prep-Level-Leakage phi_C+sep_C soll
      KEINE val5-Ueberrepraesentation zeigen.

Verdikte:
  REFUTED_UNIFORM            nicht T1 (Leakage strukturlos -> H-STAR-2 tot)
  PARTIAL_STRUKTUR_KEIN_SIEB T1, T3, nicht T2 (Struktur, kein Sieb)
  PARTIAL_KEIN_MOD5          T1, nicht T3 (Struktur, aber nicht mod-5)
  CONFIRMED                  T1 AND T2 AND T3
"""

import hashlib
import json
import os
import sys

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pt_prereg_audit import audit_prereg_structure  # noqa: F401 (Re-Export)

PREREG_PATH = "pt_leakage_prereg_v1.json"
SOURCE_JOB_ID = "dakjk9hhvn6c73cvr1cg"
SOURCE_COMMIT = "9d73edc"

EXPERIMENT = "032-ququint-v1-leakage-sieve"
DECISION_RULE = "t1_structured AND t2_sieve_r0 AND t3_mod5_dominant"

R0_SHARE_MIN = 1.0 / 3.0 + 0.05   # Sieb-Schwelle (konservativ, ~9 sigma)
T1_P_UNIFORM_MAX = 0.01           # Flachheits-Gate (chi2 df=38)
Z_FLOOR = 2.0                     # Kontrast-Signifikanz-Boden

CONTRAST_FAMILY = (
    "val5_r0", "val6_r1", "val7_r2", "sideA", "sideB",
    "other_low", "other_high",
)

VERDICT_MAP = {
    "REFUTED_UNIFORM": "NOT t1",
    "PARTIAL_STRUKTUR_KEIN_SIEB": "t1 AND t3 AND NOT t2",
    "PARTIAL_KEIN_MOD5": "t1 AND NOT t3",
    "CONFIRMED": "t1 AND t2 AND t3",
}

# deterministische Null-RNG (kein Uhrzeit-Zufall im Prereg-Pfad)
NULL_SEED = 20260923
N_NULL_SAMPLES = 2000

# Circuit-Reihenfolge Phase 3c (pt_ququint_fez / CIRCUIT_ORDER)
CIRCUIT_ORDER = (
    ["phi_C", "phi_D"] + [f"sep_C_{k}" for k in range(5)] + [f"sep_D_{k}" for k in range(5)]
)


# === Geometrie ===

def k_of(idx):
    """Register-A-Wert (q0..q2) des 64-dim little-endian Index."""
    return idx & 7


def l_of(idx):
    """Register-B-Wert (q3..q5) des 64-dim little-endian Index."""
    return idx >> 3


def is_leakage_bin(idx):
    return k_of(idx) >= 5 or l_of(idx) >= 5


def is_double_leak(idx):
    return k_of(idx) >= 5 and l_of(idx) >= 5


LOGICAL_BINS = [i for i in range(64) if not is_leakage_bin(i)]
LEAKAGE_BINS = [i for i in range(64) if is_leakage_bin(i)]
SINGLE_LEAK_BINS = [i for i in LEAKAGE_BINS if not is_double_leak(i)]
DOUBLE_LEAK_BINS = [i for i in LEAKAGE_BINS if is_double_leak(i)]


def residue_class(idx):
    """Residue-Klasse eines EIN-Leak-Bins (geleakter Wert mod 5), sonst None."""
    if not is_leakage_bin(idx) or is_double_leak(idx):
        return None
    k, l = k_of(idx), l_of(idx)
    return (k % 5) if k >= 5 else (l % 5)


# === Prereg (Freeze VOR dem Counts-Fetch) ===

def build_prereg_payload():
    """Deterministischer Prereg-Payload (KEIN Timestamp im gehashten Inhalt)."""
    return {
        "experiment": EXPERIMENT,
        "registered_before": (
            "Der Blick auf die 39-Bin-Leakage-Struktur der Fez-Counts fand "
            "VOR diesem Freeze nicht statt (nur die aggregierten "
            "leakage_rate_* aus §Z.14 sind bekannt). Counts-Fetch ist ein "
            "0-QPU-Re-Fetch des abgeschlossenen Phase-3c-Jobs."
        ),
        "source_job_id": SOURCE_JOB_ID,
        "source_commit": SOURCE_COMMIT,
        "hypothesis": (
            "H-STAR-2 Layer 1: DFT-Leakage ist strukturiert UND mod-5-"
            "Residue-geordnet (Sieb-Fingerprint). Mechanismus: F5-Phasen-"
            "Degeneriertheit x ~ x+5 (mod 5) in der kompilierten DFT-Rotation."
        ),
        "steelman": (
            "Random-Unitary/Haar: Leakage gleichverteilt über die 39 "
            "Außen-Bins — Dirichlet(1)-Null plus Permutations-Null über "
            "Residue-Labels plus Prep-Level-Negativkontrolle (phi_C+sep_C)."
        ),
        "decision_rule": DECISION_RULE,
        "analysis_plan": {
            "positive_family": "phi_D + gepooltes sep_D (DFT-Rotation, "
                               "Leakage 16.8% / 13.7% in §Z.14)",
            "negative_control": "phi_C + gepooltes sep_C (Prep-Level, "
                                "2.2% / 0.3%) — soft, kein Decision-Gate",
            "n_circuits": 12,
            "circuit_order": list(CIRCUIT_ORDER),
        },
        "predictions": {
            "t1_structured": True,
            "t2_sieve_r0": True,
            "t3_mod5_dominant": True,
        },
        "prediction_bands": {
            "r0_share_sieve_band": [1.0 / 3.0, 0.5],
            "t1_p_uniform_band": [0.0, T1_P_UNIFORM_MAX],
        },
        "thresholds": {
            "r0_share_min": R0_SHARE_MIN,
            "ordering": "c0 > c1 AND c0 > c2",
            "t1_p_uniform_max": T1_P_UNIFORM_MAX,
            "z_floor": Z_FLOOR,
        },
        "contrast_family": list(CONTRAST_FAMILY),
        "nulls": {
            "uniform_chisq": "chi2 df=38 ueber die 39 Leakage-Bins",
            "dirichlet_haar": "Dirichlet(1) x 2000 Samples (Haar/Random-"
                              "Unitary-Steelman fuer T1)",
            "permutation_labels": "Residue-Labels permutiert x 2000 "
                                  "(Null fuer r0_share)",
            "negative_control": "phi_C+sep_C Prep-Level-Leakage, qualitativ",
        },
        "verdict_map": dict(VERDICT_MAP),
        "geometry": {
            "logical_bins": 25,
            "leakage_bins": 39,
            "single_leak_bins": 30,
            "double_leak_bins": 9,
            "residue_class_sizes": [10, 10, 10],
            "index_convention": "idx = k + 8*l (qiskit little-endian); "
                                "k = q0..q2, l = q3..q5",
        },
    }


def canonical_payload_json(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def payload_md5(payload):
    return hashlib.md5(canonical_payload_json(payload).encode("utf-8")).hexdigest()


def freeze_prereg(payload=None):
    """Friert ein: FLAT-Format {...payload..., "md5"} (Muster §Z.13.5/Phase 3a)."""
    if payload is None:
        payload = build_prereg_payload()
    doc = dict(payload)
    doc["md5"] = payload_md5(payload)
    return doc


def verify_prereg_md5(doc):
    stripped = {k: v for k, v in doc.items() if k != "md5"}
    return payload_md5(stripped) == doc["md5"]


def load_frozen_prereg(path=PREREG_PATH):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if not verify_prereg_md5(doc):
        raise ValueError(f"Prereg-md5-MISMATCH in {path} — Payload wurde nach "
                         "dem Freeze veraendert")
    return doc


# === Counts ===

def counts_to_vec(counts):
    """6-Bit-Counts-Dict -> 64-Vektor (fehlende Keys = 0)."""
    vec = np.zeros(64)
    for key, cnt in counts.items():
        vec[int(key, 2)] += float(cnt)
    return vec


def load_counts_document(path):
    """Laedt das persistierte Fez-Counts-Dokument (12 Circuits)."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def split_circuit_counts(counts_by_circuit):
    """12-Circuit-Dict -> gepoolte 64-Vektoren (pos/neg Familie)."""
    pos = np.zeros(64)
    pos += counts_to_vec(counts_by_circuit["phi_D"])
    for k in range(5):
        pos += counts_to_vec(counts_by_circuit[f"sep_D_{k}"])
    neg = np.zeros(64)
    neg += counts_to_vec(counts_by_circuit["phi_C"])
    for k in range(5):
        neg += counts_to_vec(counts_by_circuit[f"sep_C_{k}"])
    return {"positive": pos, "negative": neg}


# === Kontrast-Familie ===

def _leaked_value(idx):
    k, l = k_of(idx), l_of(idx)
    return k if k >= 5 else l


def _other_value(idx):
    k, l = k_of(idx), l_of(idx)
    return l if k >= 5 else k


def contrast_bins(name):
    """Bins der benannten Kandidatenklasse über die 30 Ein-Leak-Bins."""
    if name == "val5_r0":
        return [i for i in SINGLE_LEAK_BINS if _leaked_value(i) == 5]
    if name == "val6_r1":
        return [i for i in SINGLE_LEAK_BINS if _leaked_value(i) == 6]
    if name == "val7_r2":
        return [i for i in SINGLE_LEAK_BINS if _leaked_value(i) == 7]
    if name == "sideA":
        return [i for i in SINGLE_LEAK_BINS if k_of(i) >= 5]
    if name == "sideB":
        return [i for i in SINGLE_LEAK_BINS if l_of(i) >= 5]
    if name == "other_low":
        return [i for i in SINGLE_LEAK_BINS if _other_value(i) <= 1]
    if name == "other_high":
        return [i for i in SINGLE_LEAK_BINS if _other_value(i) >= 3]
    raise ValueError(f"unbekannte Kontrastklasse: {name}")


def contrast_family_z(masses):
    """z-Scores aller Kontrastklassen: (Anteil - Groesse/30) / Binomial-sigma."""
    masses = np.asarray(masses, dtype=float)
    n = masses[SINGLE_LEAK_BINS].sum()
    scores = {}
    for name in CONTRAST_FAMILY:
        bins = contrast_bins(name)
        obs = masses[bins].sum()
        p0 = len(bins) / 30.0
        share = obs / n
        sigma = math_sqrt(p0 * (1 - p0) / n)
        scores[name] = float((share - p0) / sigma)
    return scores


def math_sqrt(x):
    return float(np.sqrt(x))


# === Nullen ===

def dirichlet_null_t1(n_leak, n_samples=N_NULL_SAMPLES, seed=NULL_SEED):
    """Haar/Random-Unitary-Steelman: chi2 der Uniform-Null unter Dirichlet(1)."""
    rng = np.random.default_rng(seed)
    draws = rng.dirichlet(np.ones(39), size=n_samples) * n_leak
    chi2 = ((draws - n_leak / 39.0) ** 2 / (n_leak / 39.0)).sum(axis=1)
    return chi2


def permutation_null_r0(n, n_perm=N_NULL_SAMPLES, seed=NULL_SEED):
    """Permutations-Null: uniforme Masse, Residue-Labels zufaellig."""
    rng = np.random.default_rng(seed)
    shares = np.empty(n_perm)
    for j in range(n_perm):
        labels = rng.permutation([residue_class(i) for i in SINGLE_LEAK_BINS])
        mass = rng.multinomial(int(n), np.full(30, 1.0 / 30.0))
        c0 = mass[labels == 0].sum()
        shares[j] = c0 / n
    return shares


# === Analyse ===

def verdict(t1, t2, t3):
    if not t1:
        return "REFUTED_UNIFORM"
    if t2 and t3:
        return "CONFIRMED"
    if t3:
        return "PARTIAL_STRUKTUR_KEIN_SIEB"
    return "PARTIAL_KEIN_MOD5"


def analyze_vector(vec):
    """Prereg-Analyse eines 64-Vektors (Leakage-Struktur)."""
    masses = np.asarray(vec, dtype=float)
    n_leak = float(masses[LEAKAGE_BINS].sum())
    if n_leak <= 0:
        raise ValueError("kein Leakage-Mass im Vektor")

    # T1: Flachheit ueber die 39 Leakage-Bins
    obs39 = masses[LEAKAGE_BINS]
    exp39 = n_leak / 39.0
    chi2_flat = float(((obs39 - exp39) ** 2 / exp39).sum())
    p_flat = float(stats.chisquare(obs39, exp39).pvalue)
    t1 = p_flat < T1_P_UNIFORM_MAX

    # Ein-Leak-Masse + Residue-Klassen (Indizierung auf dem 64-Vektor)
    n_single = float(masses[SINGLE_LEAK_BINS].sum())
    class_mass = {
        r: float(masses[[i for i in SINGLE_LEAK_BINS
                         if residue_class(i) == r]].sum())
        for r in (0, 1, 2)
    }
    r0_share = class_mass[0] / n_single if n_single > 0 else float("nan")
    t2 = (r0_share >= R0_SHARE_MIN
          and class_mass[0] > class_mass[1]
          and class_mass[0] > class_mass[2])

    # T3: Kontrast-Familie (Look-Elsewhere)
    z_scores = contrast_family_z(masses)
    best = max(z_scores, key=z_scores.get)
    t3 = best == "val5_r0" and z_scores["val5_r0"] >= Z_FLOOR

    # Nullen (deterministisch, seeded)
    null_chi2 = dirichlet_null_t1(n_leak)
    p_dirichlet = float((null_chi2 >= chi2_flat).mean())
    perm = permutation_null_r0(int(n_single))
    p_perm_r0 = float((perm >= r0_share).mean())

    return {
        "n_leak": n_leak,
        "n_single_leak": n_single,
        "leakage_bins_mass": obs39.tolist(),
        "chi2_flat": chi2_flat,
        "p_uniform": p_flat,
        "t1_structured": bool(t1),
        "p_dirichlet_haar": p_dirichlet,
        "class_mass_r0_r1_r2": [class_mass[0], class_mass[1], class_mass[2]],
        "r0_share": float(r0_share),
        "t2_sieve_r0": bool(t2),
        "z_scores": z_scores,
        "best_contrast": best,
        "z_val5": z_scores["val5_r0"],
        "t3_mod5_dominant": bool(t3),
        "p_perm_r0": p_perm_r0,
        "verdict": verdict(t1, t2, t3),
    }


def evaluate_leakage(counts_by_circuit):
    """Volle V1-Evaluation: pos-Familie (gates) + neg-Kontrolle (soft)."""
    pools = split_circuit_counts(counts_by_circuit)
    pos = analyze_vector(pools["positive"])
    neg = analyze_vector(pools["negative"])
    # Soft-Konsistenz: Prep-Level-Leakage soll KEINE Sieb-Ueberrepraesentation
    neg_consistent = not (neg["t2_sieve_r0"] and neg["t3_mod5_dominant"])
    return {
        "experiment": EXPERIMENT,
        "source_job_id": SOURCE_JOB_ID,
        "prereg_path": PREREG_PATH,
        "positive": pos,
        "negative_control": neg,
        "negative_control_consistent": bool(neg_consistent),
        "decision_rule": DECISION_RULE,
        "verdict": pos["verdict"],
    }