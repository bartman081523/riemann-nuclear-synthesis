"""EXPERIMENT 036 — H-STAR-5 (HYPOTHESE, PhiSci4-Runde): Tests.

OFFLINE (reine numpy-Arithmetik + Struktur-Checks, kein qiskit — Guard).
Die These wird REGISTRIERT, NICHT ausgefuehrt: Tests pruefen die
Architektur (Markierung, Brücke, Steelman, Kontrollfamilie, Falsifikator,
Prereg-Skelett) und die strukturelle Null (exakte Tensor-Summen-
Faktorisierung) — KEINE Messung von Prime vs. Shuffle.
"""

import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_hstar5_hypothesis as hh


# === Hypothesen-Markierung (Pflicht, nicht Etikett) ===

def test_thesis_marked_as_hypothesis_not_finding():
    assert hh.STATUS == "HYPOTHESE_REGISTRIERT_NICHT_AUSGEFUEHRT"
    assert hh.QPU_THIS_PHASE == 0
    assert "NICHT" in hh.EXECUTION_PHASE
    # Extraordinaritaet berichtet VOR jeder Messung (ECREE)
    assert 1 <= hh.EXTRAORDINARINESS_SCORE <= 10
    assert "Extraordinary" in hh.EVIDENCE_STANDARD
    assert "ECREE" in hh.EVIDENCE_STANDARD
    # Die These selbst traegt die These-Struktur: Bruecke + Annahmen + Claim
    for key in ("id", "name", "bridge", "bridge_assumptions", "claim",
                "falsifiable_form"):
        assert key in hh.THESIS and hh.THESIS[key]
    assert hh.THESIS["id"] == "H-STAR-5"
    assert len(hh.THESIS["bridge_assumptions"]) == 3
    # Bruecke benennt, WELCHE Groesse aus WELCHER Kategorie wandert
    assert "Spectral Form Factor" in hh.THESIS["bridge"]
    assert "Keating" in hh.THESIS["bridge"]
    # Mechanismus-Annahme ist als offen markiert (HYPOTHESE, nicht Befund)
    assert any("offen" in a for a in hh.THESIS["bridge_assumptions"])


def test_cage_diagnosis_names_both_blindnesses():
    cd = hh.CAGE_DIAGNOSIS
    assert "blindness_1_tensor_sum_factorization" in cd
    assert "blindness_2_unitary_invariance" in cd
    # (i) die exakte Faktorisierung
    assert "Prod_p" in cd["blindness_1_tensor_sum_factorization"]
    # (ii) Basis-Randomisierung ist spektral-blind
    assert "invariant" in cd["blindness_2_unitary_invariance"]
    # V3-Lektion: Schiene, nicht Primes, ist der Engpass
    assert "Schiene" in cd["why_v3_failed"]


def test_steelman_is_not_pure_chance():
    anti = hh.STEELMAN["antithesis"]
    # staerkstes etabliertes Modell, kein 'reiner Zufall'
    assert "Integrable-in-all-probes" in anti
    assert "EXAKT" in anti
    assert hh.STEELMAN["why_strongest"]
    assert len(hh.STEELMAN["how_killed"]) == 2


def test_control_family_complete():
    cf = hh.CONTROL_FAMILY
    # Positivkontrolle: muss zuenden, sonst VOID
    assert cf["positive"]["must_fire"] is True
    assert "VOID" in cf["positive"]["spec"]
    # Negativkontrollen: Shuffle-Null + Composite (muss NICHT zuenden)
    assert "shuffle_null" in cf["negative"] and "composite_null" in cf["negative"]
    assert cf["negative"]["must_not_fire"] is True
    # Strukturelle Null: EXAKTE Identitaet
    assert "EXAKT" in cf["structural"]["identity"]
    assert "Prod_p" in cf["structural"]["identity"]


def test_falsifier_verdict_map_and_degenerat_rule():
    fm = hh.FALSIFIER["verdict_map"]
    assert set(fm) == {"CONFIRMED", "REFUTED", "DEGENERAT", "VOID", "INVALID"}
    assert fm["CONFIRMED"] == "H-STAR5_CONFIRMED_PRIME_SFF_SEPARATION"
    assert fm["REFUTED"] == "H-STAR5_REFUTED_INTEGRABLE_IN_ALL_PROBES"
    # DEGENERAT-Lektion: Klasse UNTER der Null ist REFUTED-zulaessig
    assert "REFUTED" in fm["DEGENERAT"]
    assert len(hh.FALSIFIER["decision_rules"]) == 5
    rules = " ".join(hh.FALSIFIER["decision_rules"])
    assert "VOID" in rules and "post-hoc" in rules
    # Schwellen freeze VOR der ersten Messung
    assert "VOR der ersten Messung" in rules
    assert set(hh.FALSIFIER["observables"]) == {"O1_ramp_classifier",
                                                "O2_factorization_residual"}


def test_alternatives_void_and_held():
    ids = {a["id"] for a in hh.ALTERNATIVES}
    assert ids == {"H-STAR-5a-VOID", "H-STAR-5b-HELD"}
    void_alt = hh.ALTERNATIVES[0]
    # Haar-Basis-Kandidat ist VOR der Messung als LEER registriert
    # (spektral-invariant => SFF-blind)
    assert void_alt["status"] == "VOID_VOR_REGISTRIERT"
    assert "Invarianz" in void_alt["reason"]
    held = hh.ALTERNATIVES[1]
    # Held-Alternative mit Score und Bruecke zu Paket 3
    assert held["status"] == "BEREITGEHALTEN_NICHT_PREREG"
    assert 1 <= held["score"] <= 10
    assert "VQE" in held["reason"]


# === Strukturelle Null: EXAKTE Tensor-Summen-Faktorisierung ===

def _blocks_2():
    X = np.array([[0.0, 1.0], [1.0, 0.0]])
    Z = np.array([[1.0, 0.0], [0.0, -1.0]])
    return [X, Z]


def _blocks_3():
    X = np.array([[0.0, 1.0], [1.0, 0.0]])
    Z = np.array([[1.0, 0.0], [0.0, -1.0]])
    B3 = np.array([[0.5, 0.3, 0.0], [0.3, -1.0, 0.2], [0.0, 0.2, 2.0]])
    return [X, Z, B3]


def test_tensor_sum_factorization_identity_exact():
    for blocks in (_blocks_2(), _blocks_3()):
        assert hh.tensor_sum_factorization_ok(blocks)
        for t in hh.TS_CHECK:
            assert hh.tensor_sum_factorization_dev(blocks, t) <= hh.TOL_IDENTITY
    # ein Block: Identitaet trivial
    assert hh.tensor_sum_factorization_dev(_blocks_2()[:1], 1.3) == 0.0
    # SFF-Seite: K(Tensor-Summe) = Produkt der Block-Ks
    blocks = _blocks_3()
    t = 0.7
    lhs = hh.sff_trace(hh.kron_sum(blocks), t)
    rhs = np.prod([hh.sff_trace(B, t) for B in blocks])
    assert abs(lhs - rhs) <= hh.TOL_IDENTITY


def test_factorization_breaks_with_coupling():
    """Die strukturelle Null ist ein echter Diskriminator: ein nicht-
    faktorisierender Kopplungsterm bricht die Identitaet (Positiv-Sanity
    fuer den benchmark-Kontrollweg)."""
    X = np.array([[0.0, 1.0], [1.0, 0.0]])
    Z = np.array([[1.0, 0.0], [0.0, -1.0]])
    eps = 0.1
    H_coupled = hh.kron_sum([X, Z]) + eps * (np.kron(X, Z) + np.kron(Z, X))
    # Identitaet mit dem GEBUNDENEN H ist nicht mehr die Block-Produkt-Form
    lhs = hh.trace_exp_minus_iHt(H_coupled, 1.7)
    rhs = hh.trace_exp_minus_iHt(X, 1.7) * hh.trace_exp_minus_iHt(Z, 1.7)
    assert abs(lhs - rhs) > 1e-6


def test_sff_utilities_structure():
    X = np.array([[0.0, 1.0], [1.0, 0.0]])
    Z = np.array([[1.0, 0.0], [0.0, -1.0]])
    # t = 0: |Tr I|^2 = d^2 fuer jedes hermitesche H
    for H in (X, Z, hh.kron_sum([X, Z])):
        assert hh.sff_trace(H, 0.0) == H.shape[0] ** 2
    # Determinismus + reeller Wert
    assert hh.sff_trace(X, 1.0) == hh.sff_trace(X, 1.0)
    assert isinstance(hh.trace_exp_minus_iHt(X, 1.0), complex)


# === Prereg-Skelett ===

def test_prereg_skeleton_fields():
    p = hh.build_prereg_skeleton()
    assert p["experiment"] == "036-ququint-hstar5-sff-ensemble"
    assert p["hypothesis"] == "H-STAR-5"
    assert "NICHT" in p["status"]
    assert "0 QPU" in p["qpu"]
    rb = p["registered_before"]
    assert "VOR erster Messung" in rb["pipeline"]
    assert "post-hoc" in rb["anti_sharpshooter"]
    assert "REFUTED" in rb["degenerat_lesson"]
    assert "Primaerliteratur" in rb["reference_check"]
    assert "Meaning-Making" in rb["epoche_rule"]
    assert "C (tot" in rb["vectors"] and "KEIN stilles Upgrade" in rb["vectors"]
    assert "TDD-verifiziert" in rb["structural_null_verified"]
    ex = p["extraordinariness"]
    assert ex["score"] == hh.EXTRAORDINARINESS_SCORE
    assert ex["standard"] == hh.EVIDENCE_STANDARD
    # Architektur, nicht numerische Fenster
    assert p["control_family"] == hh.CONTROL_FAMILY
    assert p["falsifier"] == hh.FALSIFIER
    assert p["thesis"] == hh.THESIS


def test_prereg_freeze_verify_tamper(tmp_path):
    payload = hh.build_prereg_skeleton()
    path = str(tmp_path / "prereg.json")
    doc = hh.freeze_prereg_skeleton(payload, path=path)
    assert hh.verify_prereg_md5(doc)
    reloaded = hh.load_frozen_prereg(path)
    assert reloaded["md5"] == doc["md5"]
    tampered = dict(doc)
    tampered["extraordinariness"] = dict(tampered["extraordinariness"])
    tampered["extraordinariness"]["score"] = 2  # Score-Manipulation
    assert not hh.verify_prereg_md5(tampered)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(tampered, fh)
    try:
        hh.load_frozen_prereg(path)
        raise AssertionError("manipulierter Prereg wurde akzeptiert")
    except ValueError:
        pass


# === Offline-Guard (kein qiskit, kein Token, KEIN Mess-Einstieg) ===

def test_offline_guard_no_qiskit_no_token_no_measurement():
    src = open(hh.__file__, encoding="utf-8").read()
    assert "qiskit" not in src.lower()
    assert "IBMQ_TOKEN" not in src
    assert "QiskitRuntimeService" not in src
    assert "Sampler" not in src and "Estimator" not in src
    assert re.search(r"\b[0-9a-fA-F]{40,}\b", src) is None
    assert "apikey" not in src.lower()
    # Die These wird NICHT ausgefuehrt: kein Mess-Einstiegspunkt
    callables = [n for n in dir(hh) if not n.startswith("_")
                 and callable(getattr(hh, n))]
    assert not any(n.startswith("run_") for n in callables)
    assert hh.STATUS.startswith("HYPOTHESE")