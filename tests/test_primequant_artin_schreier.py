"""Tests für Artin-Schreier Phasenmatrizen und Deligne-Weil Schranken in primequant."""

from __future__ import annotations

import cmath
import math
import pytest

from primequant import (
    poly_eval_mod,
    artin_schreier_exponential_sum,
    artin_schreier_magnitude_squared,
    artin_schreier_deligne_bound,
    artin_schreier_phase_matrix,
    wigner_semicircle_moment_exact,
    cyc_zero,
    cyc_from_int,
    cyc_eq,
)
from fractions import Fraction


def test_poly_eval_mod():
    # f(x) = 2 + 3x + x^2 mod 5
    # coeffs = [2, 3, 1]
    # x = 0 -> 2
    # x = 1 -> 2 + 3 + 1 = 6 = 1
    # x = 2 -> 2 + 6 + 4 = 12 = 2
    coeffs = [2, 3, 1]
    assert poly_eval_mod(coeffs, 0, 5) == 2
    assert poly_eval_mod(coeffs, 1, 5) == 1
    assert poly_eval_mod(coeffs, 2, 5) == 2


def test_linear_cancellation():
    """H-ASD-1: Lineare Summen sum_{x} omega^{ax+b} verschwinden identisch."""
    for q in [3, 5, 7, 11]:
        for a in [1, 2, q - 1]:
            s = artin_schreier_exponential_sum(q, [0, a])
            assert cyc_eq(s, cyc_zero(q))


def test_quadratic_gauss_saturation():
    """H-ASD-2: Quadratische Gaußsummen saturieren |S|^2 = q bit-exakt."""
    for q in [3, 5, 7, 11]:
        # f(x) = x^2
        mag2 = artin_schreier_magnitude_squared(q, [0, 0, 1])
        assert cyc_eq(mag2, cyc_from_int(q, q))


def test_deligne_bound_cubic():
    """H-ASD-3: Kubische Summen erfuellen |sigma_k(S)|^2 <= 4q fuer alle Einbettungen."""
    for q in [5, 7, 11, 13]:
        coeffs = [0, 1, 0, 1]  # x^3 + x
        s = artin_schreier_exponential_sum(q, coeffs)
        bound = artin_schreier_deligne_bound(q, degree=3)
        assert bound == 4 * q

        for k in range(1, q):
            # Komplexe Einbettung
            val = sum(c * cmath.exp(2j * math.pi * k * a / q) for a, c in enumerate(s))
            mag2 = abs(val) ** 2
            assert mag2 <= bound + 1e-9


def test_phase_matrix_shape():
    """Prüft Dimension und Diagonalität der Phasenmatrix."""
    q = 5
    mat = artin_schreier_phase_matrix(q, [0, 0, 1])
    assert len(mat) == q
    for r in range(q):
        assert len(mat[r]) == q
        for c in range(q):
            if r != c:
                assert cyc_eq(mat[r][c], cyc_zero(q))


def test_wigner_semicircle_moments():
    """Prüft die exakten Wigner-Halbkreis-Momente m_2k = C_k / 4^k."""
    assert wigner_semicircle_moment_exact(0) == Fraction(1, 1)
    assert wigner_semicircle_moment_exact(1) == Fraction(1, 4)
    assert wigner_semicircle_moment_exact(2) == Fraction(1, 8)
    assert wigner_semicircle_moment_exact(3) == Fraction(5, 64)
    assert wigner_semicircle_moment_exact(4) == Fraction(7, 128)

