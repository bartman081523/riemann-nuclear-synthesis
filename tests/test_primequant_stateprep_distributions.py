"""EXAKT-Schicht: Zustandsvorbereitung + Verteilungen (Phase-B-Tests).

Alles Fraction-/int-Arithmetik — jede behauptete Zeile ist eine exakte
Identitaet oder ein exakter Guard-Text gegen die live-verifizierten Pins
der Probe-Laeufe (scratches/probe_phaseb_pins.py, 2026-10-06). Kein Seed,
kein Float-Vergleich in einer EXAKT-Zeile; Float-Pins leben in der
Kanal-Suite (ABGELEITET-Anker mit absoluten Toleranzen).
"""
import os
import sys
from fractions import Fraction as F

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)
try:
    import primequant as pq
except ImportError:  # editable install fehlt: src-Fallback
    sys.path.insert(0, os.path.join(_REPO, "src"))
    import primequant as pq


def test_sieve_primes_basis():
    assert pq.sieve_primes(0) == []
    assert pq.sieve_primes(1) == []
    assert pq.sieve_primes(2) == [2]
    assert pq.sieve_primes(30) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    primzahlen = pq.sieve_primes(100)
    assert len(primzahlen) == 25  # pi(100) = 25
    assert primzahlen[-1] == 97


def test_residue_counts_pins():
    assert pq.residue_counts(13, 3) == [1, 2, 3]
    assert pq.residue_counts(31, 7) == [1, 1, 2, 3, 1, 2, 1]
    assert pq.residue_counts(181, 3) == [1, 19, 22]
    assert pq.residue_counts(467, 5) == [1, 21, 24, 24, 21]
    assert pq.residue_counts(673, 5) == [1, 29, 32, 32, 28]
    assert pq.residue_counts(181, 9) == [0, 7, 8, 1, 6, 8, 0, 6, 6]
    for p_prim, d_dim in ((13, 3), (31, 7), (181, 3), (467, 5), (673, 5),
                          (181, 9)):
        assert sum(pq.residue_counts(p_prim, d_dim)) == \
            len(pq.sieve_primes(p_prim))
    with pytest.raises(ValueError, match="d muss >= 1 sein"):
        pq.residue_counts(31, 0)


def test_exakter_probvektor_pins():
    # Default-Norm m == Summe; explizite Norm m == 6 — identisches Ergebnis
    assert pq.exakter_probvektor([1, 2, 3]) == [F(1, 6), F(1, 3), F(1, 2)]
    assert pq.exakter_probvektor([1, 2, 3], 6) == [F(1, 6), F(1, 3), F(1, 2)]
    assert pq.exakter_probvektor([19, 13, 10], 42) == [
        F(19, 42), F(13, 42), F(10, 42)]
    vier = pq.exakter_probvektor([1, 1, 1, 1], 4)
    assert vier == [F(1, 4)] * 4
    assert sum(vier) == 1
    with pytest.raises(ValueError, match="Norm m muss >= 1 sein"):
        pq.exakter_probvektor([1], 0)
    with pytest.raises(ValueError, match="Count-Vektor widerspricht m"):
        pq.exakter_probvektor([1, 2, 3], 5)


def test_labels_und_delta_vektor():
    assert pq.labels_2nq(1) == ["0", "1"]
    assert pq.labels_2nq(2) == ["00", "01", "10", "11"]
    assert pq.labels_2nq(3)[:2] == ["000", "001"]
    assert len(pq.labels_2nq(3)) == 8
    assert pq.delta_vektor(1) == [1, 0]
    assert pq.delta_vektor(2, 3) == [0, 0, 0, 1]
    assert pq.delta_vektor(3) == [1, 0, 0, 0, 0, 0, 0, 0]
    with pytest.raises(ValueError, match="nq muss >= 1 sein"):
        pq.labels_2nq(0)
    with pytest.raises(ValueError, match="label 3 ausserhalb 0..1"):
        pq.delta_vektor(1, 3)


def test_ideal_deltas_zwillinge():
    for nq in (1, 2, 3):
        loschmidt = pq.ideal_loschmidt_delta(nq)
        leiter = pq.ideal_leiter_delta(nq)
        delta = pq.delta_vektor(nq, 0)
        assert loschmidt == leiter == delta
        assert loschmidt[0] == 1
        assert sum(loschmidt) == 1


def test_falt_auf_q_pins():
    assert pq.falt_auf_q([1, 2, 3, 4], 4, 2) == [4, 6]
    assert pq.falt_auf_q([1, 2, 3, 4, 5, 6], 6, 3) == [5, 7, 9]
    # d == q ist die Identitaet (Shuffle-Inertness)
    assert pq.falt_auf_q([1, 2, 3], 3, 3) == [1, 2, 3]
    assert pq.falt_auf_q([1, 2, 3, 4, 5, 6], 6, 3) == [5, 7, 9]
    assert pq.falt_auf_q(pq.residue_counts(673, 5), 5, 5) == [1, 29, 32, 32, 28]
    with pytest.raises(ValueError,
                       match="d/q muessen >= 1 sein, erhalten d=0, q=2"):
        pq.falt_auf_q([1], 0, 2)
    with pytest.raises(ValueError,
                       match="d/q muessen >= 1 sein, erhalten d=3, q=0"):
        pq.falt_auf_q([1, 2, 3], 3, 0)
    with pytest.raises(ValueError,
                       match="Vektor laenger 2 < Registerbreite d=3"):
        pq.falt_auf_q([1, 2], 3, 3)


def test_register_breite():
    assert pq.register_breite(1) == (0, 1)
    assert pq.register_breite(3) == (2, 4)
    assert pq.register_breite(8) == (3, 8)
    assert pq.register_breite(9) == (4, 16)
    assert pq.register_breite(17) == (5, 32)


def test_reihenarten_konstanten():
    assert pq.STRUKTUR_REIHENARTEN == ("structure", "kalibrier_structure")
    assert pq.DELTA_REIHENARTEN == (
        "loschmidt", "kalibrier_loschmidt", "echo_ladder", "readout_cal")
    for art in ("structure", "kalibrier_structure"):
        assert art not in pq.DELTA_REIHENARTEN


def test_fuele_modell():
    acht = pq.fuele_modell([F(1, 3)] * 3, 8)
    assert acht == [F(1, 3)] * 3 + [0] * 5
    assert len(acht) == 8 and sum(acht) == 1
    # int-Eintraege konvertieren nach Fraction
    assert pq.fuele_modell([1], 4) == [1, 0, 0, 0]
    with pytest.raises(ValueError,
                       match="Modelllaenge 9 ueber Registerbreite 8"):
        pq.fuele_modell([F(1, 4)] * 9, 8)


def test_modell_kontrollen():
    assert pq.modell_kontrolle_uniform(3) == [F(1, 3)] * 3
    assert pq.modell_kontrolle_uniform(5) == [F(1, 5)] * 5
    with pytest.raises(ValueError, match="q muss >= 2 sein"):
        pq.modell_kontrolle_uniform(1)
    komposit = pq.modell_kontrolle_composite([19, 13, 10], 42)
    assert komposit == [F(19, 42), F(13, 42), F(10, 42)]
    # m-Default: m == Summe des deklarierten Vektors
    assert pq.modell_kontrolle_composite([19, 13, 10]) == komposit
    with pytest.raises(ValueError,
                       match="deklarierter Count-Vektor widerspricht m"):
        pq.modell_kontrolle_composite([1, 2], 4)


def test_modell_fuer_art_dispatcher():
    struktur = [F(19, 42), F(13, 42), F(10, 42), 0, 0, 0, 0, 0]
    assert pq.modell_fuer_art("structure", 3, n_d=[19, 13, 10], m=42) == \
        struktur
    assert pq.modell_fuer_art("kalibrier_structure", 3, n_d=[19, 13, 10],
                              m=42) == struktur
    # Delta-Familie: alle vier Arten liefern das Delta auf 0^nq
    for art in pq.DELTA_REIHENARTEN:
        modell = pq.modell_fuer_art(art, 3)
        assert modell == [1, 0, 0, 0, 0, 0, 0, 0]
    # negative_control: uniform ueber q Klassen (n_d-frei) ...
    assert pq.modell_fuer_art("negative_control", 3, q=3) == \
        [F(1, 3)] * 3 + [0] * 5
    # ... oder composite ueber den deklarierten Count-Vektor (n_d-Pfad;
    # das Label "composite_q5" eines Bestands-Preregs bleibt unmassgeblich)
    assert pq.modell_fuer_art("negative_control", 3, n_d=[19, 13, 10],
                              m=42) == struktur
    with pytest.raises(ValueError,
                       match="art structure: n_d/m Pflichtargumente"):
        pq.modell_fuer_art("structure", 3)
    with pytest.raises(ValueError,
                       match="art structure: n_d/m Pflichtargumente"):
        pq.modell_fuer_art("structure", 3, n_d=[1, 1, 1], m=0)
    with pytest.raises(ValueError,
                       match=r"negative_control \(uniform\) verlangt q"):
        pq.modell_fuer_art("negative_control", 3)
    with pytest.raises(ValueError, match="unbekannte Reihen-Art 'zoe'"):
        pq.modell_fuer_art("zoe", 3)


def test_zaehlung_auf_labels():
    assert pq.zaehlung_auf_labels({"00": 1, "10": 2}, 4) == [1, 0, 2, 0]
    # Label-Fusion: "1" und "01" sind derselbe Label-Int
    assert pq.zaehlung_auf_labels({"1": 2, "01": 3}, 4) == [0, 5, 0, 0]
    assert pq.zaehlung_auf_labels({"1": 2, "01": 3}, 2) == [0, 5]
    assert pq.zaehlung_auf_labels({" 11 ": 2}, 4) == [0, 0, 0, 2]
    assert pq.zaehlung_auf_labels({}, 3) == [0, 0, 0]
    with pytest.raises(ValueError, match="breite muss >= 1 sein"):
        pq.zaehlung_auf_labels({"0": 1}, 0)
    with pytest.raises(ValueError, match=r"ausserhalb 0..1"):
        pq.zaehlung_auf_labels({"100": 1}, 2)
    with pytest.raises(ValueError, match="ist nicht ganz"):
        pq.zaehlung_auf_labels({"1": 1.5}, 2)
    with pytest.raises(ValueError, match="negatives Count-Masse -2"):
        pq.zaehlung_auf_labels({"1": -2}, 2)


def test_exakte_masse_am_label():
    assert pq.exakte_masse_am_label({"01": 2, "10": 3}, 2) == 3
    assert pq.exakte_masse_am_label({"1": 2, "01": 3}, 1) == 5
    assert pq.exakte_masse_am_label({}, 5) == 0
    # Label-Breite wird hier nicht geprueft (Label-Int-Vergleich)
    assert pq.exakte_masse_am_label({"0001": 7}, 1) == 7
    with pytest.raises(ValueError, match="label muss >= 0 sein"):
        pq.exakte_masse_am_label({"0": 1}, -1)


def test_tv_exakt_konvention_und_guards():
    delta = pq.delta_vektor(2)  # [1, 0, 0, 0]
    assert pq.tv_exakt({"00": 10}, delta) == 0
    assert pq.tv_exakt({"10": 10}, delta) == 1  # volle Verdrängung
    assert pq.tv_exakt({"0": 4, "1": 2}, [F(1, 2), F(1, 2)]) == F(1, 6)
    # Masse jenseits der Modelllaenge faellt mit Modellmasse 0 voll an
    assert pq.tv_exakt({"1": 3}, [F(1)]) == 1
    with pytest.raises(ValueError, match="Modell-Summe 1/2 != 1"):
        pq.tv_exakt({"0": 1}, [F(1, 2)])
    with pytest.raises(ValueError, match="Counts-Summe muss >= 1 sein"):
        pq.tv_exakt({"0": 0}, [F(1)])
    with pytest.raises(ValueError,
                       match="label 1 ausserhalb Register-Breite 1"):
        pq.tv_exakt({"0": 1, "1": 1}, [F(1, 2), F(1, 2)], breite=1)
    with pytest.raises(ValueError, match="ist nicht ganz"):
        pq.tv_exakt({"0": 1.5}, [F(1)])