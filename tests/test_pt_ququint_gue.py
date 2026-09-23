"""V3 (H-STAR-3): GUE-r-Statistik im encodierten H_PT-Spektrum.

Alle Tests OFFLINE (pure numpy, kein qiskit). Prereg (Klassen-Baender,
Kontroll-Gates, Falsifikator-Erwartung) wird VOR der Kurven-Berechnung
gefriert (pt_gue_prereg_v3.json, md5).

Referenzkonstanten (Atas et al., arXiv:1212.5611, large-N):
  Poisson 0.3863 | GOE 0.5307 | GUE 0.5996 | GSE 0.6744.
  KORREKTUR: der Plan §Z.15 fuehrt 0.5359 als "<r>_GUE" — das ist die
  GOE-Surmise-Konstante (4 - 2 sqrt(3)). Die Korrektur ist VOR dem Freeze
  registriert (Feld reference_correction im Prereg-Payload).
"""

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_ququint_gue as gue


# === Block-Spektren ===

def test_block_spectrum_5_levels_isolated_level_exact():
    # Das 5. Niveau (block_diag, 0) ist ENTKOPPELT -> E = 5.0 exakt
    for gamma in gue.GAMMA_FAMILY:
        spec = gue.block_spectrum(gamma)
        assert spec.size == 5
        assert any(abs(v - 5.0) < 1e-9 for v in spec), (gamma, spec)


def test_block_spectrum_quasi_harmonisch_nicht_gue():
    # Ein Block allein: 4 Abstaende, stark ungleichmaessig (kein WD-Fluss)
    spec = gue.block_spectrum(0.02)
    r = gue.r_statistic(spec)
    assert r is not None
    assert r < gue.GOE_BAND[0]  # Block allein NICHT in einer WD-Klasse


# === Kollabieren + r-Statistik ===

def test_collapse_sorted_exact_and_near_duplicates():
    out = gue.collapse_sorted([2.0, 1.0, 1.0 + 1e-12, 2.0, 3.0])
    assert np.allclose(out, [1.0, 2.0, 3.0])
    # Untergrenze respektiert: 0.0122-Gap (gamma=0.002) wird NICHT kollabiert
    assert gue.collapse_sorted(gue.block_spectrum(0.002)).size == 5


def test_r_statistic_edges_and_harmonic():
    assert gue.r_statistic(np.array([1.0, 2.0])) is None
    assert gue.r_statistic(np.array([])) is None
    # Harmonisch (aequidistant) -> r = 1
    assert math.isclose(gue.r_statistic(np.arange(10, dtype=float)), 1.0)


def test_r_statistic_estimator_matches_poisson():
    # Schaetzer-Validierung: 5000 iid-exponential gaps -> <r> ≈ 0.3863
    rng = np.random.default_rng(42)
    gaps = rng.exponential(1.0, size=5000)
    x = np.concatenate([[0.0], np.cumsum(gaps)])
    r = gue.r_statistic(x)
    assert abs(r - gue.POISSON_R) < 0.02, r


# === Ensemble-Kontrollen (Schaetzer + Referenzkonstanten) ===

def test_gue_control_25_in_band():
    # Korrigierte GUE-Referenz 0.5996 (NICHT 0.5359 — das ist GOE-Surmise)
    r = gue.gue_control(25, 200)
    assert abs(r - gue.GUE_R) <= gue.CONTROL_TOL, r
    # GUE liegt deutlich ueber GOE (Differenz 0.069, aufloesbar)
    assert r > gue.GOE_R + 0.05


def test_goe_control_25_in_band():
    r = gue.goe_control(25, 200)
    assert abs(r - gue.GOE_R) <= gue.CONTROL_TOL, r


def test_poisson_control_25_in_band():
    r = gue.poisson_control(25, 200)
    assert abs(r - gue.POISSON_R) <= gue.CONTROL_TOL, r


def test_controls_deterministic_seeded():
    assert gue.gue_control(25, 20) == gue.gue_control(25, 20)
    assert gue.goe_control(25, 20) == gue.goe_control(25, 20)
    assert gue.poisson_control(25, 20) == gue.poisson_control(25, 20)


def test_reference_constants_corrected():
    # Die korrigierte Atas-et-al-Tabelle (arXiv:1212.5611)
    assert math.isclose(gue.POISSON_R, 2 * math.log(2) - 1, abs_tol=1e-3)
    assert math.isclose(gue.GOE_R, 0.5307, abs_tol=1e-4)
    assert math.isclose(gue.GUE_R, 0.5996, abs_tol=1e-4)
    # 0.5359 (GOE-Surmise 4 - 2*sqrt(3)) darf NICHT als GUE-Referenz dienen
    assert abs(gue.GUE_R - (4 - 2 * math.sqrt(3))) > 0.05
    assert gue.GUE_R - gue.GOE_R > 0.05  # GOE/GUE aufloesbar


# === Encodierte Summen-Spektren ===

def test_encoded_spectrum_d25_count_and_distinct():
    raw = gue.encoded_re_spectrum((0.02, 0.2))
    assert raw.size == 25
    assert gue.collapse_sorted(raw).size == 25  # keine exakte Degeneration


def test_encoded_spectrum_d625_twin_collapse():
    # (0.002, 0.02, 0.2, 0.02): Bloecke 2 und 4 identisch -> Zwillingssummen
    # E_i+E_j = E_j+E_i (i<->l) -> exakt 125 + 250 = 375 distinct
    raw = gue.encoded_re_spectrum((0.002, 0.02, 0.2, 0.02))
    assert raw.size == 625
    assert gue.collapse_sorted(raw).size == 375


def test_equal_gamma_config_has_symmetry_degeneracy():
    # Diagonal-Konfiguration (g, g): E_i+E_j = E_j+E_i -> Kollaps auf 15
    spec = gue.collapse_sorted(gue.encoded_re_spectrum((0.02, 0.02)))
    assert spec.size == 15  # Grund fuer den Ausschluss aus der Primaerfamilie


def test_family_configs():
    fam25 = gue.family_configs_25()
    assert len(fam25) == 3  # combinations(3,2); (g1,g2) ≡ (g2,g1) spektral
    for g1, g2 in fam25:
        assert g1 < g2
    fam625 = gue.family_configs_625()
    assert len(fam625) == 78  # 81 - 3 diagonal
    assert all(len(set(c)) >= 2 for c in fam625)


# === Klassen + Verdict ===

def test_classify_bands():
    assert gue.classify(0.30) == "DEGENERAT"
    assert gue.classify(0.40) == "POISSON"
    assert gue.classify(0.47) == "GRAU"
    assert gue.classify(0.53) == "GOE"
    assert gue.classify(0.5996) == "GUE"
    assert gue.classify(0.655) == "GRAU"
    assert gue.classify(0.80) == "REGULAER"
    assert gue.classify(None) == "LEER"


def test_verdict_matrix():
    V = gue.verdict
    assert V("GUE", "GUE") == "H-STAR-3_CONFIRMED_GUE_KLASSE"
    assert V("GOE", "GUE") == "H-STAR-3_TEILWEISE_WD_GOE"
    assert V("GOE", "GOE") == "H-STAR-3_TEILWEISE_WD_GOE"
    assert V("POISSON", "GUE") == "H-STAR-3_REFUTED"
    assert V("GUE", "REGULAER") == "H-STAR-3_REFUTED"
    assert V("GRAU", "GUE") == "H-STAR-3_INKONKLUSIV"
    assert V("DEGENERAT", "POISSON") == "H-STAR-3_REFUTED"
    assert V("DEGENERAT", "GRAU") == "H-STAR-3_INKONKLUSIV"


# === Shuffle-Null ===

def test_shuffle_null_harmonic_invariant_and_edges():
    # Harmonisch: alle gaps gleich -> Permutation aendert nichts (r = 1)
    assert math.isclose(gue.shuffle_null(np.arange(10, dtype=float)), 1.0)
    assert gue.shuffle_null(np.array([1.0, 2.0])) is None


def test_shuffle_null_deterministic():
    x = np.array([0.0, 1.0, 1.1, 2.1, 3.1])
    assert gue.shuffle_null(x, n_perm=100) == gue.shuffle_null(x, n_perm=100)


# === Prereg ===

def test_prereg_payload_predictions_bands_correction(tmp_path):
    p = gue.build_prereg_payload()
    assert p["experiment"] == "032-ququint-v3-gue-rstat"
    assert p["decision_rule"] == "t25_gue_band AND t625_gue_band (nach Kontroll-Gates)"
    # Falsifikator-Erwartung: GUE wird NICHT erwartet (REGULAER/POISSON)
    assert p["predictions"]["t25_gue"] is False
    assert p["predictions"]["t625_gue"] is False
    assert p["thresholds"]["gue_band"] == [0.565, 0.63]
    assert p["thresholds"]["goe_band"] == [0.50, 0.565]
    assert p["thresholds"]["poisson_band"] == [0.34, 0.45]
    assert p["thresholds"]["regular_min"] == 0.70
    assert p["thresholds"]["control_references"]["gue"] == 0.5996
    assert p["thresholds"]["control_references"]["goe"] == 0.5307
    # Konstanten-Korrektur registriert (Anti-Sharpshooter: Dokumentation
    # der 0.5359-Verwechslung VOR der Kurven-Berechnung)
    assert "reference_correction" in p
    assert "1212.5611" in p["reference_correction"]
    assert "0.5996" in p["reference_correction"]
    assert "3 Konfigurationen" in p["families"]["d25"]
    assert "78" in p["families"]["d625"]
    assert p["controls"]["gate"] == "Kontrollfehler -> EVALUATION_INVALID"
    assert p["controls"]["goe_625"][0] == 50


def test_prereg_md5_freeze_verify_tamper(tmp_path):
    payload = gue.build_prereg_payload()
    doc = gue.freeze_prereg(payload)
    assert gue.verify_prereg_md5(doc)
    tampered = dict(doc)
    tampered["thresholds"] = dict(tampered["thresholds"])
    tampered["thresholds"]["gue_band"] = [0.50, 0.58]  # Band-Manipulation
    assert not gue.verify_prereg_md5(tampered)
    path = tmp_path / "prereg.json"
    path.write_text(json.dumps(doc))
    reloaded = gue.load_frozen_prereg(str(path))
    assert reloaded["md5"] == doc["md5"]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(tampered, fh)
    try:
        gue.load_frozen_prereg(str(path))
        raise AssertionError("manipulierter Prereg wurde akzeptiert")
    except ValueError:
        pass


# === Offline-Guard ===

def test_offline_module_no_qiskit_ibm_import():
    src = open(gue.__file__, encoding="utf-8").read()
    assert "qiskit_ibm" not in src
    assert "QiskitRuntimeService" not in src
    assert "IBMQ_TOKEN" not in src