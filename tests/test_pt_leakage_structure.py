"""V1 (H-STAR-2 Layer 1): Leakage-Sieb-Struktur vs. Random-Unitary-Steelman.

Alle Tests laufen OFFLINE auf synthetischen Counts — der Fez-Fetch passiert
erst NACH dem Prereg-Freeze (pt_leakage_prereg_v1.json, md5). Die
Bin-Klassifikation folgt der Phase-2/3-Konvention:

  64-dim qiskit little-endian Index = k + 8*l
  k = Register A (q0..q2), l = Register B (q3..q5)
  logisch: k,l <= 4 (25 Bins) | Leakage: k >= 5 oder l >= 5 (39 Bins)
  Ein-Leak: genau ein Register >= 5 (30 Bins, 10 pro Residue-Klasse)
"""

import json
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_leakage_structure as ls


# === Bin-Klassifikation (die Prereg-Geometrie) ===

def test_bin_counts():
    assert len(ls.LOGICAL_BINS) == 25
    assert len(ls.LEAKAGE_BINS) == 39
    assert len(ls.SINGLE_LEAK_BINS) == 30
    assert len(ls.DOUBLE_LEAK_BINS) == 9
    assert set(ls.LOGICAL_BINS) | set(ls.LEAKAGE_BINS) == set(range(64))
    assert not (set(ls.LOGICAL_BINS) & set(ls.LEAKAGE_BINS))
    assert set(ls.SINGLE_LEAK_BINS) | set(ls.DOUBLE_LEAK_BINS) == set(ls.LEAKAGE_BINS)


def test_bin_examples():
    # k=5,l=0 -> Ein-Leak, Residue 0
    assert ls.residue_class(5) == 0
    # k=7,l=6 -> Doppel-Leak
    assert ls.is_double_leak(7 + 8 * 6)
    # k=3,l=5 -> Ein-Leak (B-Seite), Residue 0
    assert ls.residue_class(3 + 8 * 5) == 0
    # k=0,l=6 -> Residue 1
    assert ls.residue_class(0 + 8 * 6) == 1
    # k=2,l=7 -> Residue 2
    assert ls.residue_class(2 + 8 * 7) == 2
    # logisch
    assert not ls.is_leakage_bin(3 + 8 * 4)


def test_residue_class_sizes_exact():
    counts = {r: 0 for r in (0, 1, 2)}
    for idx in ls.SINGLE_LEAK_BINS:
        counts[ls.residue_class(idx)] += 1
    assert counts == {0: 10, 1: 10, 2: 10}


# === Prereg-Freeze ===

def test_prereg_payload_contains_thresholds():
    p = ls.build_prereg_payload()
    assert p["experiment"] == "032-ququint-v1-leakage-sieve"
    assert p["predictions"]["t1_structured"] is True
    assert p["predictions"]["t2_sieve_r0"] is True
    assert p["predictions"]["t3_mod5_dominant"] is True
    assert math.isclose(p["thresholds"]["r0_share_min"], 1 / 3 + 0.05)
    assert p["thresholds"]["t1_p_uniform_max"] == 0.01
    assert p["thresholds"]["z_floor"] == 2.0
    # Kontrast-Familie (Look-Elsewhere): mod5 (val=5) muss unter ALLEN
    # benannten Kandidatenklassen den groessten z-Score haben.
    assert p["contrast_family"] == [
        "val5_r0", "val6_r1", "val7_r2", "sideA", "sideB",
        "other_low", "other_high",
    ]


def test_prereg_md5_freeze_verify_tamper(tmp_path):
    payload = ls.build_prereg_payload()
    doc = ls.freeze_prereg(payload)
    assert ls.verify_prereg_md5(doc)
    tampered = dict(doc)
    tampered["thresholds"] = dict(tampered["thresholds"])
    tampered["thresholds"]["r0_share_min"] = 0.34
    assert not ls.verify_prereg_md5(tampered)
    # Freeze-Roundtrip
    path = tmp_path / "prereg.json"
    path.write_text(json.dumps(doc))
    reloaded = ls.load_frozen_prereg(str(path))
    assert reloaded["md5"] == doc["md5"]


# === Counts-Loader ===

def _synth_counts(vec):
    """64-Vektor -> Counts-Dict im 6-Bit-Format."""
    return {format(i, "06b"): int(v) for i, v in enumerate(vec) if v}


def test_counts_loader_roundtrip():
    vec = np.zeros(64)
    vec[0] = 1000.0
    vec[5] = 50.0
    vec[43] = 30.0
    c = _synth_counts(vec)
    back = ls.counts_to_vec(c)
    assert back[0] == 1000 and back[5] == 50 and back[43] == 30
    assert back.sum() == 1080


def test_loader_missing_keys_zero_and_sum_kept():
    counts = {"000000": 4096, "111111": 4096}  # 63 = k=7,l=7 Doppel-Leak
    vec = ls.counts_to_vec(counts)
    assert vec[0] == 4096 and vec[63] == 4096
    assert vec.sum() == 8192
    assert ls.is_double_leak(63)


# === Analyse-Statistik ===

def test_uniform_leakage_fails_t1():
    rng = np.random.default_rng(7)
    # uniform ueber die 39 Leakage-Bins
    vec = np.zeros(64)
    vec[ls.LEAKAGE_BINS] = rng.multinomial(7000, np.full(39, 1 / 39))
    res = ls.analyze_vector(vec)
    assert res["n_leak"] == 7000
    assert not res["t1_structured"]
    assert res["verdict"] == "REFUTED_UNIFORM"


def test_residue0_concentrated_passes_t2():
    rng = np.random.default_rng(11)
    vec = np.zeros(64)
    probs = np.zeros(64)
    # 50% der Masse auf Residue-0-Ein-Leak-Bins
    r0_bins = [i for i in ls.SINGLE_LEAK_BINS if ls.residue_class(i) == 0]
    others = [i for i in ls.SINGLE_LEAK_BINS if ls.residue_class(i) != 0]
    for i in r0_bins:
        probs[i] = 0.5 / len(r0_bins)
    for i in others:
        probs[i] = 0.5 / len(others)
    n = 200_000
    draws = rng.choice(64, size=n, p=probs / probs.sum())
    counts = np.bincount(draws, minlength=64).astype(float)
    res = ls.analyze_vector(counts)
    assert res["r0_share"] >= 0.49
    assert res["t2_sieve_r0"]


def test_residue_share_at_chance_fails_t2():
    rng = np.random.default_rng(13)
    probs = np.zeros(64)
    for i in ls.SINGLE_LEAK_BINS:
        probs[i] = 1.0 / 30
    draws = rng.choice(64, size=200_000, p=probs)
    counts = np.bincount(draws, minlength=64).astype(float)
    res = ls.analyze_vector(counts)
    assert abs(res["r0_share"] - 1 / 3) < 0.01
    assert not res["t2_sieve_r0"]


def test_val6_dominant_fails_t3():
    rng = np.random.default_rng(17)
    probs = np.zeros(64)
    # Struktur auf val=6 (mod3-Residue 0), nicht auf val=5 (Sieb-Klasse)
    v6_bins = [i for i in ls.SINGLE_LEAK_BINS
               if (ls.k_of(i) if ls.k_of(i) >= 5 else ls.l_of(i)) == 6]
    others = [i for i in ls.SINGLE_LEAK_BINS if i not in v6_bins]
    for i in v6_bins:
        probs[i] = 0.5 / len(v6_bins)
    for i in others:
        probs[i] = 0.5 / len(others)
    draws = rng.choice(64, size=200_000, p=probs / probs.sum())
    counts = np.bincount(draws, minlength=64).astype(float)
    res = ls.analyze_vector(counts)
    assert res["t1_structured"]
    assert res["best_contrast"] == "val6_r1"
    assert not res["t3_mod5_dominant"]
    assert res["verdict"] == "PARTIAL_KEIN_MOD5"


def test_weak_val5_structure_gives_partial_not_confirmed():
    rng = np.random.default_rng(19)
    probs = np.zeros(64)
    # val=5 bekommt 35% (>1/3, aber < 0.3833 Schwelle): Struktur ja,
    # Sieb-Bestaetigung nein -> PARTIAL_STRUKTUR_KEIN_SIEB
    v5_bins = [i for i in ls.SINGLE_LEAK_BINS if ls.residue_class(i) == 0]
    others = [i for i in ls.SINGLE_LEAK_BINS if ls.residue_class(i) != 0]
    for i in v5_bins:
        probs[i] = 0.35 / len(v5_bins)
    for i in others:
        probs[i] = 0.65 / len(others)
    draws = rng.choice(64, size=200_000, p=probs / probs.sum())
    counts = np.bincount(draws, minlength=64).astype(float)
    res = ls.analyze_vector(counts)
    assert res["t1_structured"]
    assert res["t3_mod5_dominant"]
    assert abs(res["r0_share"] - 0.35) < 0.005
    assert not res["t2_sieve_r0"]
    assert res["verdict"] == "PARTIAL_STRUKTUR_KEIN_SIEB"


def test_verdict_matrix():
    assert ls.verdict(False, False, False) == "REFUTED_UNIFORM"
    assert ls.verdict(False, True, True) == "REFUTED_UNIFORM"
    assert ls.verdict(True, True, True) == "CONFIRMED"
    assert ls.verdict(True, False, True) == "PARTIAL_STRUKTUR_KEIN_SIEB"
    assert ls.verdict(True, True, False) == "PARTIAL_KEIN_MOD5"
    assert ls.verdict(True, False, False) == "PARTIAL_KEIN_MOD5"


def test_nulls_deterministic_seeded():
    a = ls.permutation_null_r0(n=4000, n_perm=500)
    b = ls.permutation_null_r0(n=4000, n_perm=500)
    assert len(a) == 500
    assert np.array_equal(a, b)
    assert abs(np.mean(a) - 1 / 3) < 0.02


def test_offline_module_no_qiskit_ibm_import():
    src = open(ls.__file__, encoding="utf-8").read()
    assert "qiskit_ibm" not in src
    assert "QiskitRuntimeService" not in src