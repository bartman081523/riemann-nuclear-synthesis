"""Exakte Binomial-Baender (Phase B) — Fraction-/int-Arithmetik.

Pins aus den live-verifizierten Probe-Laeufen (C6 + B-Reihe,
scratches/probe_phaseb_pins.py, 2026-10-06): Integer-Term-Walk-CDF
(sehr schnell gegenueber dem Fraction-Walk), zweiseitiger p-Wert,
Bonferroni-alpha, bandoese Quantil-Kanten mit Kanten-Sehung
(CDF-Monotonie-Witness), Chebyshev-/Cantelli-Grenzen.
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


def test_binom_cdf_basis():
    assert pq.binom_cdf_exakt(0, 4, F(1, 2)) == F(1, 16)
    assert pq.binom_cdf_exakt(2, 4, F(1, 2)) == F(11, 16)
    assert pq.binom_cdf_exakt(4, 4, F(1, 2)) == 1
    # Entartete Kanten: k < 0 -> 0, k >= S -> 1
    assert pq.binom_cdf_exakt(-1, 4, F(1, 2)) == 0
    assert pq.binom_cdf_exakt(5, 4, F(1, 2)) == 1
    # Rand-Wahrscheinlichkeiten p = 0 / p = 1
    assert pq.binom_cdf_exakt(0, 8, 0) == 1
    assert pq.binom_cdf_exakt(0, 8, 1) == 0
    with pytest.raises(ValueError, match="S muss >= 0 sein"):
        pq.binom_cdf_exakt(0, -1, F(1, 2))
    with pytest.raises(ValueError, match="Wahrscheinlichkeit ausserhalb"):
        pq.binom_cdf_exakt(0, 4, F(3, 2))


def test_binom_tail_inklusiv():
    # tail(k) = P(X >= k) — die Masse bei k zaehlt mit
    assert pq.binom_tail_exakt(7, 8, F(1, 2)) == F(9, 256)
    assert pq.binom_tail_exakt(8, 8, F(1, 2)) == F(1, 256)
    assert pq.binom_tail_exakt(0, 8, F(1, 2)) == 1
    assert pq.binom_tail_exakt(9, 8, F(1, 2)) == 0
    # Komplement-Identitaet: cdf(k) + tail(k+1) == 1
    assert pq.binom_cdf_exakt(6, 8, F(1, 2)) + \
        pq.binom_tail_exakt(7, 8, F(1, 2)) == 1


def test_p_wert_zweiseitig():
    # S=8 Alles-hoch: links 0, rechts 1/256 -> 2/256 = 1/128
    assert pq.p_wert_zweiseitig(8, 8, F(1, 2)) == F(1, 128)
    assert pq.p_wert_zweiseitig(2, 8, F(1, 2)) == F(37, 128)
    # Mitte: beide Seiten > 1/2 -> Deckel bei 1
    assert pq.p_wert_zweiseitig(4, 8, F(1, 2)) == 1
    # Spiegel-Symmetrie der Muenze
    assert pq.p_wert_zweiseitig(6, 8, F(1, 2)) == \
        pq.p_wert_zweiseitig(2, 8, F(1, 2))


def test_alpha_bonferroni():
    assert pq.alpha_bonferroni(F(1, 20), 5) == F(1, 100)
    assert pq.alpha_bonferroni(1, 4) == F(1, 4)
    with pytest.raises(ValueError, match="anzahl muss >= 1 sein, erhalten 0"):
        pq.alpha_bonferroni(F(1, 2), 0)
    with pytest.raises(ValueError, match=r"alpha ausserhalb \(0, 1\]"):
        pq.alpha_bonferroni(0, 3)
    with pytest.raises(ValueError, match=r"alpha ausserhalb"):
        pq.alpha_bonferroni(F(3, 2), 3)


def test_band_quantile_pins_und_kantensehung():
    assert pq.band_quantile(F(1, 5), 60, F(1, 20), 5) == (4, 21)
    k_lo, k_hi = pq.band_quantile(F(1, 5), 8192, F(1, 20), 5)
    assert (k_lo, k_hi) == (1545, 1733)
    a2 = F(1, 20) / 5 / 2  # alpha / bonferroni / 2
    # Unter-Kante: F(k_lo) <= a2 < F(k_lo + 1)
    assert pq.binom_cdf_exakt(k_lo, 8192, F(1, 5)) <= a2
    assert a2 < pq.binom_cdf_exakt(k_lo + 1, 8192, F(1, 5))
    # Ober-Kante: tail(k_hi) <= a2 < tail(k_hi - 1)
    assert pq.binom_tail_exakt(k_hi, 8192, F(1, 5)) <= a2
    assert a2 < pq.binom_tail_exakt(k_hi - 1, 8192, F(1, 5))
    with pytest.raises(ValueError, match="bonferroni muss >= 1 sein"):
        pq.band_quantile(F(1, 5), 8192, F(1, 20), 0)


def test_schranken_grenzen():
    assert pq.chebyshev_schranke(100, 8192, F(1, 2)) == F(128, 625)
    assert pq.cantelli_schranke(100, 8192, F(1, 2)) == F(128, 753)
    # Cantelli (einseitig) ist nie schwaecher als Chebyshev
    assert pq.cantelli_schranke(100, 8192, F(1, 2)) <= \
        pq.chebyshev_schranke(100, 8192, F(1, 2))
    for schranke in (pq.chebyshev_schranke, pq.cantelli_schranke):
        assert schranke(0, 100, F(1, 2)) == 1