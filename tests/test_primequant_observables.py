"""Exakte Observablen (Phase B): Punkt-Konstanten, Quote, Ring-DFT.

Die Punkt-Tabelle ist die 10-Punkte-Streichung der live-verifizierten
Probe-Laeufe (2026-10-06): jede Zeile exakt gegen die Probe-Ausgabe,
plus Guards mit exakten Texten (Nennner entartet, Klasse-0-Atom),
Mini-Quote synthetisch, Galois-Konjugationen und Ramanujan c_q(n).
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

# (P, d, q, shots) -> gefrorene Felder (alle live, Flag True)
PUNKT_TABELLE = [
    dict(P=181, d=3, q=3, shots=8192, m=42, n_d=[1, 19, 22], N=[1, 19, 22],
         num=774, den=1521, ratio=F(172, 169), share_t=F(43, 7),
         share_m=F(169, 28), L_q=F(49, 86528), delta=F(-3, 2),
         d_sq=F(9, 4)),
    dict(P=181, d=5, q=5, shots=8192, m=42, n_d=[1, 9, 12, 11, 9],
         N=[1, 9, 12, 11, 9], num=376, den=1369, ratio=F(1504, 1369),
         share_t=F(188, 105), share_m=F(1369, 840), L_q=F(441, 175232),
         sigma2=F(27, 4)),
    dict(P=269, d=3, q=3, shots=8192, m=57, n_d=[1, 25, 31], N=[1, 25, 31],
         num=1512, den=2916, ratio=F(28, 27), share_t=F(168, 19),
         share_m=F(162, 19), L_q=F(361, 663552), delta=F(-3),
         d_sq=F(9)),
    dict(P=269, d=5, q=5, shots=8192, m=57, n_d=[1, 13, 15, 15, 13],
         N=[1, 13, 15, 15, 13], num=696, den=2704, ratio=F(174, 169),
         share_t=F(232, 95), share_m=F(676, 285), L_q=F(3249, 1384448),
         sigma2=F(4)),
    dict(P=467, d=3, q=3, shots=8192, m=91, n_d=[1, 43, 47], N=[1, 43, 47],
         num=3896, den=7744, ratio=F(487, 484), share_t=F(3896, 273),
         share_m=F(3872, 273), L_q=F(8281, 15859712), delta=F(-2),
         d_sq=F(4)),
    dict(P=467, d=5, q=5, shots=8192, m=91, n_d=[1, 21, 24, 24, 21],
         N=[1, 21, 24, 24, 21], num=1894, den=7396, ratio=F(1894, 1849),
         share_t=F(1894, 455), share_m=F(1849, 455), L_q=F(8281, 3786752),
         sigma2=F(9)),
    dict(P=673, d=3, q=3, shots=8192, m=122, n_d=[1, 58, 63], N=[1, 58, 63],
         num=7118, den=14161, ratio=F(14236, 14161), share_t=F(3559, 183),
         share_m=F(14161, 732), L_q=F(3721, 7250432), delta=F(-5, 2),
         d_sq=F(25, 4)),
    dict(P=673, d=5, q=5, shots=8192, m=122, n_d=[1, 29, 32, 32, 28],
         N=[1, 29, 32, 32, 28], num=3486, den=13689, ratio=F(4648, 4563),
         share_t=F(1743, 305), share_m=F(13689, 2440), L_q=F(3721, 1752192),
         sigma2=F(51, 4)),
    dict(P=2005, d=3, q=3, shots=8192, m=304, n_d=[1, 148, 155],
         N=[1, 148, 155], num=45374, den=90601, ratio=F(1852, 1849),
         share_t=F(22687, 456), share_m=F(90601, 1824), L_q=F(361, 724808),
         delta=F(-7, 2), d_sq=F(49, 4)),
    dict(P=2005, d=5, q=5, shots=8192, m=304, n_d=[1, 73, 78, 79, 73],
         N=[1, 73, 78, 79, 73], num=22504, den=89401, ratio=F(90016, 89401),
         share_t=F(2813, 190), share_m=F(89401, 6080), L_q=F(361, 178802),
         sigma2=F(123, 4)),
]


def test_punkt_konstanten_tabelle():
    for zeile in PUNKT_TABELLE:
        konst = pq.punkt_konstanten(zeile["P"], zeile["d"], zeile["q"],
                                    shots=zeile["shots"])
        m_wert = konst["m"]
        assert m_wert == zeile["m"]
        assert konst["n_d"] == zeile["n_d"]
        assert konst["N"] == zeile["N"]
        assert konst["q_sum_N_sq_minus_m2"] == zeile["num"]
        assert konst["den"] == zeile["den"]
        assert konst["ratio_true"] == zeile["ratio"]
        assert konst["share_true_reg"] == zeile["share_t"]
        assert konst["model_share_reg"] == zeile["share_m"]
        assert konst["L_q"] == zeile["L_q"]
        assert konst["closed_form"] == zeile["ratio"]
        # geschlossene Identitaet ist exakt fuer q in {3, 5} bei n0 == 1
        assert konst["closed_form_identitaet_exakt"] is True
        if zeile["q"] == 3:
            assert konst["delta"] == zeile["delta"]
            assert konst["delta_sq"] == zeile["d_sq"]
        else:
            assert konst["sigma2"] == zeile["sigma2"]


def test_punkt_d_faltung_identitaet():
    # d = 9, q = 3: die Faltung der (181, 3)-Counts reproduziert exakt die
    # (181, 3, 3)-Konstanten — die d-Vielfachen-Struktur, live
    neun = pq.punkt_konstanten(181, 9, 3)
    drei = pq.punkt_konstanten(181, 3, 3)
    assert neun["N"] == drei["N"] == [1, 19, 22]
    assert neun["q_sum_N_sq_minus_m2"] == 774
    assert neun["den"] == 1521
    assert neun["ratio_true"] == F(172, 169)
    assert neun["delta"] == F(-3, 2)
    assert neun["closed_form_identitaet_exakt"] is True


def test_punkt_mini_shots():
    mini = pq.punkt_konstanten(13, 3, 3, shots=12)
    assert mini["m"] == 6
    assert mini["n_d"] == [1, 2, 3]
    assert mini["N"] == [1, 2, 3]
    assert mini["q_sum_N_sq_minus_m2"] == 6
    assert mini["den"] == 9
    assert mini["ratio_true"] == F(4, 3)
    assert mini["share_true_reg"] == F(1, 3)
    assert mini["model_share_reg"] == F(1, 4)
    assert mini["L_q"] == F(4, 3)
    assert mini["delta"] == F(-1, 2)
    assert mini["closed_form"] == F(4, 3)
    # q = 7: keine geschlossen-identitaets-Registrierung, aber ratio exakt
    sieben = pq.punkt_konstanten(31, 7, 7, shots=56)
    assert sieben["m"] == 11
    assert sieben["n_d"] == [1, 1, 2, 3, 1, 2, 1]
    assert sieben["q_sum_N_sq_minus_m2"] == 26
    assert sieben["den"] == 16
    assert sieben["ratio_true"] == F(39, 4)
    assert sieben["closed_form_identitaet_exakt"] is False


def test_punkt_guards():
    # P = 11, d = 5: m = 5 == q*n0 (n0 = 1) -> degenerater Nenner, exakt
    with pytest.raises(ValueError, match="Nennner entartet"):
        pq.punkt_konstanten(11, 5, 5)
    # P = 7, d = 7: Klasse-0-Masse {7} -> n0 = 2, Atom-Verweigerung
    with pytest.raises(ValueError, match="Klasse-0-Atom erwartet n0 == 1"):
        pq.punkt_konstanten(7, 7, 3)
    with pytest.raises(ValueError, match="keine Primzahlen <= P=1"):
        pq.punkt_konstanten(1, 3, 3)


def test_quote_exakt_mini_synth():
    konst = pq.punkt_konstanten(13, 3, 3, shots=12)
    # Uniform ueber 3 der 4 Labels: Faltung trifft die Klassen exakt gleich
    uniform = pq.quote_exakt({"00": 4, "01": 4, "10": 4}, konst, shots=12)
    assert uniform["m_hat"] == 6
    assert uniform["N_hut"] == [2, 2, 2]
    assert uniform["q_sum_N_sq_minus_m2"] == 0
    assert uniform["anteil_falt"] == 0
    assert uniform["anteil_modell"] == F(1, 4)
    assert uniform["quote"] == 0
    # Delta auf Label 0: maximale Masse-Verschiebung
    delta = pq.quote_exakt({"00": 12}, konst, shots=12)
    assert delta["N_hut"] == [6, 0, 0]
    assert delta["q_sum_N_sq_minus_m2"] == 72
    assert delta["anteil_falt"] == 4
    assert delta["quote"] == 16


def test_quote_exakt_label_verschiebung_und_guards():
    konst = pq.punkt_konstanten(13, 3, 3, shots=12)
    # Verschiebung auf Label 1 ("01"): gleiche Struktur wie Delta auf 0
    versch = pq.quote_exakt({"01": 12}, konst, shots=12)
    assert versch["N_hut"] == [0, 6, 0]
    assert versch["quote"] == 16
    # d % q != 0 verweigert — synthetische Konstanten (das Feld liest nur
    # P/d/q/m/model_share_reg)
    synth = {"P": 10, "d": 5, "q": 3, "m": 4, "model_share_reg": F(1)}
    with pytest.raises(ValueError, match="Quote-Identitaet verlangt d"):
        pq.quote_exakt({"00": 2, "01": 2}, synth)
    with pytest.raises(ValueError, match="shots muss >= 1 sein"):
        pq.quote_exakt({"00": 12}, konst, shots=0)
    with pytest.raises(ValueError, match="Counts-Summe 10 != shots 12"):
        pq.quote_exakt({"00": 10}, konst, shots=12)
    # Label 16 (binaer "10000") liegt ausserhalb 0..d-1 = 0..3
    with pytest.raises(ValueError, match=r"label 16 ausserhalb 0..3"):
        pq.quote_exakt({"10000": 12}, konst, shots=12)


def test_ring_dft_pins():
    assert pq.ring_dft([1, 1, 1], 3) == [(3, 0), (0, 0), (0, 0)]
    assert pq.ring_dft([0, 1, 0], 3) == [(1, 0), (-1, -1), (0, 1)]
    # DC-allein bleibt konstant unter der DFT (Rank-4-Basis bei q=5)
    assert pq.ring_dft([1, 0, 0, 0, 0], 5) == [(1, 0, 0, 0)] * 5
    with pytest.raises(ValueError, match="ring_dft verlangt einen int-Vektor"):
        pq.ring_dft([0.5, 1, 1], 3)


def test_quad_und_norm():
    assert pq.quad_magnitude((2,), 2) == (4,)
    assert pq.quad_magnitude((0, 1), 3) == (1, 0)
    # N(1 - omega_q) == q — algebraischer Anker fuer alle Primzahl-q
    for q_val in (3, 5, 7, 11):
        element = tuple([-1, 1] + [0] * (q_val - 3))
        assert pq.norm_galois(element, q_val) == q_val
    # q = 2: Ring == Z, Norm = Wert selbst
    assert pq.norm_galois((2,), 2) == 2
    with pytest.raises(ValueError, match="q muss >= 2 sein, erhalten 1"):
        pq.norm_galois((0, 1), 1)


def test_galois_konjugiert_sigma_wirkung():
    # sigma_k: a ↦ a*k (mod q); auf omega wirkt es als omega^k
    assert pq.galois_konjugiert((0, 1), 3, 1) == (0, 1)
    assert pq.galois_konjugiert((0, 1), 3, 2) == (-1, -1)  # omega^2 = -1-omega
    assert pq.galois_konjugiert((0, 1), 3, 0) == (1, 0)   # sigma_0 = Identitaet
    # q = 5, k = 2: omega ↦ omega^2 = (0, 0, 1, 0) in 1, omega, omega^2, omega^3
    assert pq.galois_konjugiert((0, 1), 5, 2) == (0, 0, 1, 0)
    # Komposition: sigma_l(sigma_k(a)) == sigma_{l*k}(a)
    element = (1, 2, 0, 1)
    links = pq.galois_konjugiert(pq.galois_konjugiert(element, 5, 2), 5, 3)
    assert links == pq.galois_konjugiert(element, 5, (2 * 3) % 5)
    # Norm bleibt unter Konjugation fix
    assert pq.norm_galois(pq.galois_konjugiert(element, 5, 2), 5) == \
        pq.norm_galois(element, 5)


def test_ramanujan_summe():
    assert pq.ramanujan_summe(5, 10) == 4
    assert pq.ramanujan_summe(5, 11) == -1
    assert pq.ramanujan_summe(3, 9) == 2
    with pytest.raises(ValueError, match="q muss Primzahl >= 2 sein, erhalten 1"):
        pq.ramanujan_summe(1, 10)