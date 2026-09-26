"""EXPERIMENT 040 — RAM-Q Zyklizitaet (H-RAM-Q-1): Tests.

OFFLINE (reine numpy-Arithmetik, kein qiskit — Guard). Die Suite prueft die
zyklotomische Ableitung (Baustein B1) gegen die gefrorenen q=5-Konstanten
aus EXPERIMENT 034 (md5 a2fc4875) und die q=3-Korrollare auf exakter
Algebra.

Anti-Peeking: Die Suite berechnet KEINE q=3-Messwerte (kein Prime-Support
auf d in {9, 81, 729} vor dem Freeze-Commit). Alle Identitaets-Tests laufen
auf SYNTHETISCHEN Residuen-Counts (share_star_from_counts) und exakter
Algebra (delta_identity_analytic). Modellwerte, pi(P) und Residuen-Counts
sind deterministische Sieb-Arithmetik und duerfen vor dem Freeze
registriert werden — gemessene q=3-DFT-Profile nicht. Der q=5-Anker
(mn.dft_profile(625, 625)) ist der bereits committete 034-Kontrollwert
(V2_SHARE_STAR_PRIME_COMMITTED) und dient nur T1/T2 als Rueckkopplung.
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_ququint_multin as mn
import pt_ramanujan_replication as rr
import pt_ram_q_zyklizitaet as rq


# === Cyclotomischer Kern (Ramanujan-Summe) ===

def test_cyclotomic_core_identity():
    """sum_{r=1}^{q-1} zeta_q^{jr} = -1 fuer q in {2,3,5,7} (c_q(j)=mu(q))."""
    for q in (2, 3, 5, 7):
        assert rq.cyclotomic_core_check(q), f"Kern-Identitaet failt fuer q={q}"
    # Explizit: q=5, j=1: i + i^2 + i^3 = i - 1 - i = -1
    s = sum(complex(0, 1) ** r for r in (1, 2, 3))
    assert s == -1 + 0j


def test_cyclotomic_core_negative_for_all_j():
    """Klassenunabhaengigkeit: die Spur ist fuer ALLE j identisch -1."""
    import cmath
    for q in (3, 5, 7):
        for j in range(1, q):
            s = sum(cmath.exp(2j * cmath.pi * j * r / q) for r in range(1, q))
            assert abs(s + 1.0) < 1e-12


# === T1-Vorab: q=5-Rueckkompatibilitaet bit-exakt (034-Anker) ===

def test_q5_backcompat_bitexact():
    assert rq.model_share_star_q(625, 625, 5) == rr.model_share_star(625, 625)
    assert rq.model_share_star_q(97, 625, 5) == rr.model_share_star(97, 625)
    assert rq.lift_q(625, 5) == rr.lift_factor(625)
    assert rq.generic_baseline_q(625, 5) == rr.generic_baseline(625) == 4 / 625
    assert rq.transition_m(5) == rr.TRANSITION_M == 25
    # Exakte Null (11, 25) aus 034
    assert rq.model_share_star_q(11, 25, 5) == 0.0
    assert rq.lift_m(5, 5) == 0.0
    # share_star_q ≡ mn.share_star fuer q=5 (bit-exakt, gleiche Iteration)
    prof = mn.dft_profile(625, 625)
    assert rq.share_star_q(prof, 625, 5) == mn.share_star(prof, 625)


def test_q5_synthetic_equipartition_matches_model():
    """Synthetische Aequipartition n=[1,25,25,25,25] (m=101): share = Modell."""
    counts = [1, 25, 25, 25, 25]
    m = sum(counts)
    got = rq.share_star_from_counts(counts, 625)
    expected = (m - 5) ** 2 / (4.0 * 625.0 * m)
    assert math.isclose(got, expected, rel_tol=1e-12)


# === q=3-Korrollare (Transition / Null / Suppression) ===

def test_transition_and_lift_q3():
    assert rq.transition_m(3) == 9            # P = 23, pi(23) = 9
    assert rq.transition_m(2) == 4
    assert rq.lift_q(23, 3) == 1.0            # Transition: kein Lift
    assert rq.lift_m(9, 3) == 1.0
    # Suppression 4 <= m <= 8
    for m in (4, 5, 6, 7, 8):
        assert rq.lift_m(m, 3) < 1.0
    assert rq.lift_m(3, 3) == 0.0             # exakte Null
    # Lift jenseits der Transition
    assert math.isclose(rq.lift_q(625, 3), 111 ** 2 / (4 * 114), rel_tol=1e-12)
    assert rq.lift_q(729, 3) > rq.lift_q(109, 3) > 1.0


def test_q3_model_values_exact():
    assert rq.model_share_star_q(5, 9, 3) == 0.0          # exakte Null (m=q=3)
    assert rq.model_share_star_q(7, 9, 3) == 1 / 72       # m=4
    assert rq.model_share_star_q(23, 729, 3) == 2 / 729   # Transition = generisch
    assert rq.model_share_star_q(23, 729, 3) \
        == rq.generic_baseline_q(729, 3) == 2 / 729
    assert math.isclose(rq.model_share_star_q(109, 729, 3),
                        676 / 42282, rel_tol=1e-12)       # m=29
    assert rq.generic_baseline_q(9, 3) == 2 / 9
    assert rq.generic_baseline_q(81, 3) == 2 / 81


# === Residuen-Counts (deterministische Sieb-Arithmetik, vor Freeze ok) ===

def test_residue_counts_handverified():
    assert rq.residue_counts(5, 3) == [1, 0, 2]    # 2,3,5
    assert rq.residue_counts(7, 3) == [1, 1, 2]    # +7
    assert rq.residue_counts(23, 3) == [1, 3, 5]   # n1={7,13,19}, n2={2,5,11,17,23}
    assert rq.residue_counts(109, 3) == [1, 13, 15]
    assert sum(rq.residue_counts(109, 3)) == 29    # pi(109)
    assert len(rq.residue_counts(5, 3)) == 3


# === Zweiklassen-Identitaet (q=3, exakt) auf SYNTHETISCHEN Counts ===

def test_delta_identity_synthetic_counts():
    """share* = (m-3)^2/(2dm) + 6*delta^2/(dm) — exakt, synthetische Counts."""
    cases = [
        ([1, 0, 2], 9),     # P=5-artig: maximale Asymmetrie, delta=-1
        ([1, 1, 2], 9),     # P=7-artig: delta=-0.5
        ([1, 2, 3], 81),    # P=13-artig
        ([1, 3, 5], 729),   # P=23-artig (Transition), delta=-1
        ([1, 13, 15], 729), # P=109-artig (Gate), delta=-1
        ([1, 3, 3], 81),    # exakte Aequipartition, delta=0 -> G = (3-m)/2
        ([1, 40, 38], 729), # Race-Flip, delta=+1
    ]
    for counts, d in cases:
        n1, n2 = counts[1], counts[2]
        got = rq.share_star_from_counts(counts, d)
        expected = rq.delta_identity_analytic(n1, n2, d)
        assert math.isclose(got, expected, rel_tol=1e-12), \
            f"delta^2-Identitaet failt fuer counts={counts}, d={d}"


def test_delta_identity_equipartition_is_pure_model():
    """delta=0 -> gemessen = Modell exakt (kein Race-Term)."""
    counts = [1, 3, 3]  # m=7
    d = 81
    got = rq.share_star_from_counts(counts, d)
    model = (7 - 3) ** 2 / (2.0 * d * 7)
    assert math.isclose(got, model, rel_tol=1e-12)


def test_measured_over_model_ratio_identity():
    """gemessen/Modell = 1 + 12*delta^2/(m-3)^2 — exakt (Zwei-Klassen-Kollaps)."""
    for counts, d in [([1, 13, 15], 729), ([1, 1, 2], 9), ([1, 40, 38], 729)]:
        n1, n2 = counts[1], counts[2]
        m = 1 + n1 + n2
        delta = (n1 - n2) / 2.0
        model = (m - 3) ** 2 / (2.0 * d * m)
        got = rq.share_star_from_counts(counts, d) / model
        expected = 1.0 + 12.0 * delta ** 2 / (m - 3) ** 2
        assert math.isclose(got, expected, rel_tol=1e-12)
    # Konkret: P=109-artig -> ratio 1 + 12/676
    model_109 = 26 ** 2 / (2.0 * 729.0 * 29.0)
    assert math.isclose(
        rq.share_star_from_counts([1, 13, 15], 729) / model_109,
        1.0 + 12.0 / 676.0, rel_tol=1e-12)
    # P=7-artig: Race dominiert (ratio 4.0) — Grund fuer das Gate
    model_7 = 1 / 72.0
    assert math.isclose(rq.share_star_from_counts([1, 1, 2], 9) / model_7,
                        4.0, rel_tol=1e-12)


def test_conjugate_symmetry_d3_and_2d3():
    """G(2d/3) = conj(G(d/3)) -> prof[d/3] == prof[2d/3] (synthetisch)."""
    counts = [1, 13, 15]
    prof = mn.single_register_profile(rq.synthetic_support(counts, 729), 729)
    assert math.isclose(prof[243], prof[486], rel_tol=1e-12)
    # und share_star_q ist genau die Doppelmasse
    assert math.isclose(rq.share_star_q(prof, 729, 3),
                        prof[243] + prof[486], rel_tol=1e-15)


# === Grid / Gate-Struktur ===

def test_grid_structure():
    assert len(rq.PRIME_POINTS) == 21
    for P, d in rq.PRIME_POINTS:
        # d = 3^k ist nie prim -> alle Primzahlen <= P sind < d (p mod d = p)
        assert max(rq.sieve_primes(P)) < d, \
            f"P={P}: Prime >= d={d} (p mod d != p verletzt)"
    assert rq.D_GRID == (9, 81, 729) == (3 ** 2, 3 ** 4, 3 ** 6)
    # Spiegel-Beziehung zum q=5-Grid (25, 625) = (5^2, 5^4)
    assert rr.D_GRID == (25, 625)
    assert all(dd == q ** (2 * i + 2)
               for i, (dd, q) in enumerate(zip(rq.D_GRID, (3, 3, 3))))


def test_gate_set_frozen_structure():
    expected = [[109, 729], [163, 729], [211, 729], [307, 729],
                [401, 729], [541, 729], [625, 729], [729, 729]]
    got = [[P, d] for P, d in rq.PRIME_POINTS if rq.is_gated_q3(P, d)]
    assert got == expected
    assert len(got) == 8
    # d=81 traegt NIE gated Punkte (m <= pi(71) = 20 < 25)
    assert not rq.is_gated_q3(625, 81)
    assert not rq.is_gated_q3(71, 81)
    # Transition/Null/Suppression sind nie gated
    assert not rq.is_gated_q3(23, 729)   # m=9 < 29
    assert not rq.is_gated_q3(5, 9)
    # Kriterium 2 am kleinsten gated Punkt: band_lo >= 3x generisch
    assert rq.BAND_LO * rq.model_share_star_q(109, 729, 3) \
        >= 3.0 * rq.generic_baseline_q(729, 3)
    # Kriterium 2 exakt aufgelöst: (m-3)^2 >= 15m <=> m >= 20.56 (m >= 21);
    # GATE_MIN_PI = 29 ist registrierte Marge darueber (Race-Slack, analog
    # q=5 in 034: Root 19 -> Gate 79)
    assert rq.GATE_MIN_PI == 29
    assert rq.BAND_LO * rq.lift_m(21, 3) >= 3.0
    assert rq.BAND_LO * rq.lift_m(20, 3) < 3.0
    assert rq.model_share_star_q(73, 729, 3)  # pi(73) = 21: Root-Punkt existiert
    assert not rq.is_gated_q3(73, 729)  # aber bewusst nicht gated (Marge)


def test_composite_limit_matches_smallest_gated():
    assert rq.composite_limit() \
        == rq.BAND_LO * rq.model_share_star_q(109, 729, 3)
    assert math.isclose(rq.composite_limit(), 0.0127903, rel_tol=1e-4)


def test_smallest_gated_selection_is_109_729():
    """T6-Regression: Auswahl ueber GATED Punkte (nicht ueber alle — (5,9)
    hat Modell-Null und wuerde den Ratio-Zweig in eine Division durch 0
    laufen lassen)."""
    payload = rq.build_prereg_payload()
    gated = [e for e in payload["prime_points"] if e["gated"]]
    smallest = min(gated, key=lambda e: e["P"])
    assert (smallest["P"], smallest["d"]) == (109, 729)
    assert smallest["model"] > 0.0
    # und T6 selbst: crude_fixed_4 / Modell = 0.5 < band_lo am gated Punkt
    assert rq.alt_crude_fixed_4(109, 729, 3) / smallest["model"] \
        < rq.BAND_LO


def test_point_roles():
    assert rq.point_role(5, 9) == "exakte_null_deskriptiv"
    assert rq.point_role(7, 9) == "suppression_deskriptiv"
    assert rq.point_role(7, 729) == "suppression_deskriptiv"
    assert rq.point_role(13, 81) == "suppression_deskriptiv"
    assert rq.point_role(19, 81) == "suppression_deskriptiv"
    assert rq.point_role(23, 81) == "transition_deskriptiv"
    assert rq.point_role(23, 729) == "transition_deskriptiv"
    assert rq.point_role(31, 81) == "ueber_transition_deskriptiv"
    assert rq.point_role(109, 729) == "gated"
    assert rq.point_role(729, 729) == "gated"


# === Registrierte deskriptive Erwartungen (aus der delta^2-Identitaet) ===

def test_registered_negative_predictions():
    # (5, 9): gemessen = 2/9 = generisch EXAKT (delta=-1 kompensiert Modell-Null)
    exp_5 = rq.delta_identity_analytic(0, 2, 9)
    assert math.isclose(exp_5, 2 / 9, rel_tol=1e-12)
    assert math.isclose(exp_5, rq.generic_baseline_q(9, 3), rel_tol=1e-12)
    assert rq.share_star_from_counts([1, 0, 2], 9) == exp_5 or \
        math.isclose(rq.share_star_from_counts([1, 0, 2], 9), exp_5, rel_tol=1e-12)
    # (7, 729): gemessen = 1/18 = 4x Modell, unter generisch 2/9
    exp_7 = rq.delta_identity_analytic(1, 2, 9)
    assert math.isclose(exp_7, 1 / 18, rel_tol=1e-12)
    assert math.isclose(exp_7 / rq.model_share_star_q(7, 9, 3), 4.0, rel_tol=1e-12)
    assert exp_7 < rq.generic_baseline_q(9, 3)
    # (23, 729): Transition — gemessen = 2/729 + 6/(729*9) = 8/2187
    exp_23 = rq.delta_identity_analytic(3, 5, 729)
    assert math.isclose(exp_23, 8 / 2187, rel_tol=1e-12)
    assert math.isclose(exp_23, rq.generic_baseline_q(729, 3) + 6.0 / (729.0 * 9.0),
                        rel_tol=1e-12)


# === Registrierte Alternativmodelle (diskriminiert) ===

def test_alternative_models_discriminated():
    # crude_fixed_4: ratio 0.5 am Gate — vom Band diskriminiert
    ratio = rq.alt_crude_fixed_4(109, 729, 3) / rq.model_share_star_q(109, 729, 3)
    assert ratio == 0.5
    assert ratio < rq.BAND_LO
    # no_zero_class: Lift m/(q-1)^2 = 9/4 an der Transition m=9
    lift = rq.alt_no_zero_class(23, 729, 3) / rq.generic_baseline_q(729, 3)
    assert math.isclose(lift, 9.0 / 4.0, rel_tol=1e-12)
    assert lift > 1.0  # sagte LIFT an der Transition voraus — falsifiziert


# === Prereg-Payload (Anti-Peeking + Struktur) ===

def test_prereg_payload_no_measured_values():
    """Freeze-Payload enthaelt KEINE gemessenen DFT-Werte (Anti-Peeking)."""
    payload = rq.build_prereg_payload()
    blob = rq.canonical_payload_json(payload)
    # Kein Schluessel "measured"/"ratio"/"in_band" (das sind Results-Felder)
    assert '"measured":' not in blob
    assert '"ratio":' not in blob
    assert '"in_band":' not in blob
    # Keine Mess-Funktionsnamen im Payload
    assert "single_register_profile" not in blob
    assert "share_prime" not in blob
    # prime_points-Eintraege tragen GENAU das registrierte Modell-Schema
    expected_keys = {"P", "d", "pi", "model", "band_lo", "band_hi", "gated",
                     "role", "residue_counts_mod3", "delta", "delta_expectation"}
    for entry in payload["prime_points"]:
        assert set(entry) == expected_keys, f"Schema-Drift bei {entry['P']}"
    # Aber: Modellwerte + Gate + Verdict-Map + Alternativen + Seeds sind drin
    assert "model_by_point" in payload
    assert len(payload["model_by_point"]) == 21
    assert payload["gate"]["gate_min_pi"] == 29
    assert payload["thresholds"]["falsifier_min_outside"] == 2
    assert payload["controls"]["random_seed_base"] == 20260926
    assert len(payload["gated_points"]) == 8
    assert payload["extraordinarity_score"]["score"] == 5
    # Verweis-Kette auf die q=5-Anker (034)
    assert payload["q5_reference_chain"]["experiment_034_prereg_md5"] \
        == "a2fc4875e10dd198e95d4996b1692759"
    assert payload["q5_reference_chain"]["v2_share_star_prime_committed"] \
        == rr.V2_SHARE_STAR_PRIME_COMMITTED


def test_prereg_payload_model_values_consistent():
    payload = rq.build_prereg_payload()
    for entry in payload["prime_points"]:
        P, d = entry["P"], entry["d"]
        assert entry["pi"] == len(rq.sieve_primes(P))
        assert entry["model"] == rq.model_share_star_q(P, d, 3)
        assert entry["band_lo"] == rq.BAND_LO * entry["model"]
        assert entry["band_hi"] == rq.BAND_HI * entry["model"]
        assert entry["gated"] == rq.is_gated_q3(P, d)
        assert sum(entry["residue_counts_mod3"]) == entry["pi"]
        # delta-Identitaet: Erwartung konsistent mit Counts
        counts = entry["residue_counts_mod3"]
        assert entry["delta_expectation"] \
            == rq.delta_identity_analytic(counts[1], counts[2], d)


def test_verdict_map_constants():
    assert rq.VERDICT_GENERALIZED == "H-RAM-Q-1_Q_DEFORMATION_GENERALIZED"
    assert rq.VERDICT_PARTIAL == "H-RAM-Q-1_PARTIAL_EIN_PUNKT_AUSSEN"
    assert rq.VERDICT_REFUTED == "H-RAM-Q-1_REFUTED_Q_DEFORMATION_KOLLABIERT"
    assert rq.VERDICT_INVALID == "EVALUATION_INVALID_KONTROLLE_GESCHEITERT"
    payload = rq.build_prereg_payload()
    assert set(payload["verdict_map"]) == {
        rq.VERDICT_GENERALIZED, rq.VERDICT_PARTIAL,
        rq.VERDICT_REFUTED, rq.VERDICT_INVALID}
    assert rq.FALSIFIER_MIN_OUTSIDE == rr.FALSIFIER_MIN_OUTSIDE == 2
    assert (rq.BAND_LO, rq.BAND_HI) == (rr.BAND_LO, rr.BAND_HI) == (0.8, 1.25)


# === Freeze-Mechanik (Kanonik wie 032/034: md5 OHNE md5-Feld) ===

def test_freeze_roundtrip_and_tamper(tmp_path):
    payload = rq.build_prereg_payload()
    path = tmp_path / "prereg.json"
    doc = rq.freeze_prereg(payload, path=str(path))
    # md5 ist ueber Payload OHNE md5-Feld gerechnet
    assert doc["md5"] == rq.payload_md5(payload)
    assert rq.verify_prereg_md5(doc)
    loaded = rq.load_frozen_prereg(path=str(path))
    assert loaded == doc
    # md5 stabil ueber Re-Freeze (deterministische Kanonik)
    doc2 = rq.freeze_prereg(payload, path=str(tmp_path / "prereg2.json"))
    assert doc2["md5"] == doc["md5"]
    # Tamper -> Verifikation failt / Load wirft
    bad = dict(doc)
    bad["gate"] = dict(doc["gate"])
    bad["gate"]["gate_min_pi"] = 5
    assert not rq.verify_prereg_md5(bad)
    tampered_path = tmp_path / "tampered.json"
    with open(tampered_path, "w", encoding="utf-8") as fh:
        json.dump(bad, fh, indent=2)
    try:
        rq.load_frozen_prereg(path=str(tampered_path))
        assert False, "Tamper nicht erkannt"
    except ValueError as exc:
        assert "MISMATCH" in str(exc)


def test_offline_guard_no_qiskit_no_token():
    src = open(rq.__file__, encoding="utf-8").read()
    assert "qiskit" not in src.lower()
    assert "IBMQ_TOKEN" not in src
    assert "QiskitRuntimeService" not in src
    assert "SamplerV2" not in src and "EstimatorV2" not in src