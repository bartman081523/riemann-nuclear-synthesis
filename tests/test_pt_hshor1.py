"""EXPERIMENT 038 — H-SHOR-1: Tests (HYPOTHESE + gefrorenes Prereg + Auswertung).

Prueft: Registrierungs-Markierung (Hypothese, kein Finding), ECREE-Score,
Korselt-Ausschluss gegen das unabhaengige Kriterium, gefrorene
Fenster/Schwellen, Verdict-Map + synthetische Verdict-Faelle, md5-Freeze/
Verify, die Auswertung selbst (CONFIRMED mit md5-Verifikation) und die
Anti-Sharpshooter-Invariante (md5 unveraendert nach Auswertung).
Regression: Label-Ausrichtung der Shuffle-Null (Run-1-Vorfall).
"""

import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_hshor1 as hh

# Gefrorenes Prereg (payload-md5) — im Test PINGIRT gegen den Freeze:
FROZEN_MD5 = "73bc664ae3475a79a692cd7735b2b387"


# === Registrierungs-Markierung ===

def test_thesis_marked_as_hypothesis_with_frozen_prereg():
    assert hh.STATUS == "HYPOTHESE_PREREG_GEFROREN_VOR_AUSWERTUNG"
    assert hh.HYPOTHESIS == "H-SHOR-1"
    assert hh.QPU_THIS_PHASE == 0
    for key in ("id", "name", "bridge", "bridge_assumptions",
                "claim", "falsifiable_form"):
        assert key in hh.THESIS, key
    assert hh.THESIS["id"] == "H-SHOR-1"
    assert len(hh.THESIS["bridge_assumptions"]) == 3
    # Die Bruecke nennt die wandernde Groesse (Ordnungsraster)
    assert "Ordnungsraster" in hh.THESIS["bridge"]


def test_ecree_score_and_standard():
    assert hh.EXTRAORDINARINESS_SCORE == 5
    assert "Standard" in hh.EVIDENCE_STANDARD
    assert hh.EXTRAORDINARINESS_SCORE == hh.build_prereg_skeleton()[
        "extraordinariness"]["score"]


def test_korselt_blindness_registered_as_must_fire_control():
    # CAGE-Diagnose benennt die Korselt-Klasse als THEOREM-genau
    # abgegrenzte Blindheit (Korrektur ggue. Plan-Entwurf, vor dem Freeze)
    assert "Korselt" in hh.CAGE_DIAGNOSIS["blindness_1_fermat_grid_korselt"]
    assert "561" in hh.CAGE_DIAGNOSIS["blindness_1_fermat_grid_korselt"]
    assert "sharper_discriminator" in hh.CAGE_DIAGNOSIS


# === Korselt-Ausschluss: gefrorene Liste vs. unabhaengiges Kriterium ===

def test_korselt_exclusion_matches_criterion():
    window = hh.CLASSICAL_WINDOW
    members = window["composites"]
    flagged = [n for n in members if hh.korselt_criterion_check(n)]
    assert flagged == window["korselt_excluded"] == [561]
    # und die anderen Composites sind wirklich nicht Korselt
    for n in members:
        assert hh.korselt_criterion_check(n) == (n == 561), n


# === Fenster / Schwellen (gefroren) ===

def test_frozen_windows_and_thresholds():
    th = hh.THRESHOLDS
    assert th["composite_min_rate"] == 0.05
    assert th["prime_max_rate"] == 0.0
    assert th["tol_identity"] == 1e-9
    assert th["crt_pairs"] == [[3, 5], [3, 7], [5, 7]]
    assert th["n_shuffle"] == 200 and th["shuffle_seed"] == 0
    assert th["shuffle_max_p"] == 0.05
    assert th["bridge_match_min"] == 1.0
    q = hh.QPE_WINDOW
    assert q["Q"] == 625 and q["XD"] == 25
    assert q["primes"] == [7, 11, 13, 17, 19, 23]
    assert q["composites"] == [15, 21]
    assert 561 in hh.CLASSICAL_WINDOW["composites"]


def test_control_family_complete():
    for key in ("positive_must_fire", "negative_must_not_fire",
                "structural_exact", "blindness_control"):
        assert key in hh.CONTROL_FAMILY, key


def test_verdict_map_has_5_classes():
    vm = hh.FALSIFIER["verdict_map"]
    assert set(vm) == {"CONFIRMED", "REFUTED", "DEGENERAT", "VOID",
                       "INVALID"}
    for code in vm.values():
        assert code.startswith("HSHOR1_"), code
    rules = hh.FALSIFIER["decision_rules"]
    assert len(rules) == 5
    assert any("post-hoc" in r for r in rules)


# === Verdict-Logik (synthetische Faelle, alle 5 Klassen) ===

def _base_results():
    """CONFIRMED-Konfiguration als Basis (wie Run 2)."""
    return {
        "o1_prime_rate_max": 0.0,
        "o1_composite_rate_min_nonkorselt": 0.5714,
        "o1_blindness_561_rate": 0.0,
        "o1_max_order_561": 80,
        "o1_blindness_561_confirmed": True,
        "o1p_composite_factored_all": True,
        "o1p_prime_factored_any": False,
        "o1b_bridge_match_min": 1.0,
        "o2_crt_max_dev": 0.0,
        "o2_trace_max_dev": 0.0,
        "shuffle": {"p": 0.0, "delta_obs": 0.6903,
                    "n_shuffle": 200, "seed": 0},
    }


def test_verdict_synthetic_all_classes():
    th = hh.THRESHOLDS
    assert hh._verdict(_base_results(), th) == "CONFIRMED"

    res = _base_results(); res["o2_crt_max_dev"] = 1e-3
    assert hh._verdict(res, th) == "VOID"

    res = _base_results(); res["o2_trace_max_dev"] = 1e-3
    assert hh._verdict(res, th) == "VOID"

    res = _base_results(); res["o1_prime_rate_max"] = 0.25
    assert hh._verdict(res, th) == "INVALID"

    res = _base_results(); res["o1_blindness_561_confirmed"] = False
    assert hh._verdict(res, th) == "INVALID"

    res = _base_results(); res["o1_composite_rate_min_nonkorselt"] = 0.01
    assert hh._verdict(res, th) == "DEGENERAT"

    res = _base_results(); res["o1p_composite_factored_all"] = False
    assert hh._verdict(res, th) == "REFUTED"

    res = _base_results(); res["o1p_prime_factored_any"] = True
    assert hh._verdict(res, th) == "REFUTED"

    res = _base_results(); res["o1b_bridge_match_min"] = 0.97
    assert hh._verdict(res, th) == "REFUTED"

    res = _base_results(); res["shuffle"]["p"] = 0.12
    assert hh._verdict(res, th) == "REFUTED"


# === Freeze / MD5 ===

def test_freeze_and_md5_verify_roundtrip(tmpdir):
    payload = hh.build_prereg_skeleton()
    path = os.path.join(str(tmpdir), "prereg.json")
    hh.freeze_prereg(payload, path)
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    assert hh.verify_prereg_md5(doc)
    assert doc["md5"] == hh.payload_md5(payload)
    # Manipulation im Speicher bricht die Verifikation
    tampered = copy.deepcopy(doc)
    tampered["falsifier"]["thresholds"]["composite_min_rate"] = 0.9
    assert not hh.verify_prereg_md5(tampered)
    assert hh.payload_md5(payload) == FROZEN_MD5


def test_alternatives_and_vectors_registered():
    alt = hh.ALTERNATIVES
    assert alt["H-SHOR-1a-UNITARY_INVARIANCE"]["status"] == "VOID"
    assert alt["H-SHOR-1b-SCALING"]["status"] == "HELD"
    assert alt["H-SHOR-1b-SCALING"]["score"] == 4
    # H-STAR-5 bleibt unangetastet (kein stilles Upgrade)
    assert hh.VECTORS["H_STAR_5"]["grade"].startswith("unveraendert")
    assert "f915729e" in hh.VECTORS["H_STAR_5"]["grade"]
    assert hh.HYPOTHESIS != "H-STAR-5"


# === Auswertung gegen das GEFRORENE Prereg ===

def test_run_evaluation_confirmed_with_md5():
    out = hh.run_evaluation()
    assert out["md5_verified"] is True
    assert out["prereg_md5"] == FROZEN_MD5
    assert out["verdict"] == "CONFIRMED"
    r = out["results"]
    # O1: Theorem-Positive-Kontrolle + Trennung
    assert r["o1_prime_rate_max"] == 0.0
    assert r["o1_composite_rate_min_nonkorselt"] > 0.05
    # 561: registrierte Blindheit (Korselt), max_order trennt
    assert r["o1_blindness_561_rate"] == 0.0
    assert r["o1_max_order_561"] == 80
    assert r["o1_blindness_561_confirmed"] is True
    # O1': Oracle-Output
    assert r["o1p_composite_factored_all"] is True
    assert r["o1p_shor"]["15"] == (3, 5)
    assert r["o1p_shor"]["21"] == (3, 7)
    assert r["o1p_prime_factored_any"] is False
    # O1b: Bridge-Match = 1.0 (QPE-Readout == Ordnungsraster)
    assert r["o1b_bridge_match_min"] == 1.0
    assert r["o1b_bridge_mismatches"] == {}
    # O2: strukturelle Null exakt
    assert r["o2_crt_max_dev"] == 0.0
    assert r["o2_trace_max_dev"] == 0.0
    # Negativkontrolle
    assert r["shuffle"]["p"] <= 0.05
    assert r["shuffle"]["delta_obs"] > 0.5


def test_shuffle_labels_aligned_to_window():
    """Regression zum Run-1-Vorfall: Labels muessen aus der
    Fenstergliederschaft abgeleitet sein (nicht aus Gruppen-Groessen an
    sortierten Schluesseln)."""
    rates = {7: 0.0, 9: 0.8, 11: 0.0, 13: 0.0, 15: 0.5714, 17: 0.0,
             19: 0.0, 21: 0.7273, 23: 0.0, 25: 0.8421, 33: 0.8421,
             35: 0.8696, 39: 0.8696, 561: 0.0}
    comp = {9, 15, 21, 25, 33, 35, 39, 561}
    out = hh._shuffle_null(rates, comp, n_shuffle=200, seed=0)
    # delta_obs muss mean(composites) - mean(primes) sein (positiv!)
    mean_c = sum(rates[n] for n in comp) / len(comp)
    mean_p = sum(rates[n] for n in rates if n not in comp) / 6
    assert abs(out["delta_obs"] - (mean_c - mean_p)) < 1e-12
    assert out["delta_obs"] > 0.5
    assert out["p"] <= 0.05


def test_md5_unchanged_after_evaluation():
    before = hh.load_frozen_prereg()["md5"]
    hh.run_evaluation()
    after = hh.load_frozen_prereg()["md5"]
    assert before == after == FROZEN_MD5