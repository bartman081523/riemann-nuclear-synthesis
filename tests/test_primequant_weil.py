"""Tests fuer primequant.weil — Exakte endliche Weil-Darstellung, Trace-Gram und Galois-Projektion.

Garantie-Pruefung: EXAKT (Fraction- und Integer-Identitaeten).
"""

from __future__ import annotations

from fractions import Fraction
import math
import pytest

from primequant.weil import (
    trace_galois,
    trace_gram_matrix,
    trace_gram_eigenschaften,
    weil_F_matrix,
    weil_D_matrix,
    dilation_matrix,
    galois_projector_matrix,
    trivial_state_amplitudes_squared,
    stepanov_multiplicity_bound,
    path_quadric_phase,
    path_quadric_ramanujan_sum,
    path_quadric_gauss_sum_even,
)
from primequant.observables import ramanujan_summe


def test_trace_galois_basis_identities():
    """Tr(omega^0) = q-1 und Tr(omega^k) = -1 fuer alle k in {1, ..., q-2}."""
    for q in (2, 3, 5, 7, 11):
        dim = q - 1
        # omega^0 Basisvektor: (1, 0, ..., 0)
        e0 = (1,) + (0,) * (dim - 1)
        assert trace_galois(e0, q) == q - 1

        # omega^k fuer k >= 1
        for k in range(1, dim):
            ek = tuple(1 if i == k else 0 for i in range(dim))
            assert trace_galois(ek, q) == -1


def test_trace_gram_matrix_matches_ramanujan():
    """G_{ij} = c_q(i - j) exakt bit-identisch fuer alle q in {2, 3, 5, 7, 11}."""
    for q in (2, 3, 5, 7, 11):
        G = trace_gram_matrix(q)
        dim = q - 1
        assert len(G) == dim
        for i in range(dim):
            assert len(G[i]) == dim
            for j in range(dim):
                diff = (i - j) % q
                assert G[i][j] == ramanujan_summe(q, diff)


def test_trace_gram_determinant_and_eigenschaften():
    """det(G) = q^{q-2} und Eigenwerte {1 (mult 1), q (mult q-2)}."""
    for q in (2, 3, 5, 7):
        prop = trace_gram_eigenschaften(q)
        assert prop["determinante"] == q ** (q - 2)
        assert prop["eigenwert_triv"] == 1
        assert prop["multiplizitaet_triv"] == 1
        assert prop["eigenwert_std"] == q
        assert prop["multiplizitaet_std"] == q - 2


def test_galois_projector_idempotent_and_rational():
    """Pi_G^2 == Pi_G bit-identisch mit Fraction-Arithmetik."""
    for q in (2, 3, 5, 7):
        Pi = galois_projector_matrix(q)
        dim = q
        # Matrix-Multiplikation Pi @ Pi
        Pi_sq = []
        for r in range(dim):
            row = []
            for c in range(dim):
                val = sum(Pi[r][k] * Pi[k][c] for k in range(dim))
                row.append(val)
            Pi_sq.append(row)
        
        assert Pi == Pi_sq


def test_galois_projector_annihilates_standard_irrep():
    """Pi_G vernichtet jeden mittelwertfreien Vektor auf GF(q)* exakt."""
    for q in (3, 5, 7):
        Pi = galois_projector_matrix(q)
        # Erzeuge mittelwertfreien Vektor v auf GF(q)*: sum_{x=1}^{q-1} v_x = 0
        v = [Fraction(0)] * q
        v[1] = Fraction(1)
        v[2] = Fraction(-1)
        
        # Berechne Pi @ v
        res = [sum(Pi[r][k] * v[k] for k in range(q)) for r in range(q)]
        assert all(x == Fraction(0) for x in res)


def test_trivial_state_amplitudes():
    for q in (3, 5, 7):
        p = trivial_state_amplitudes_squared(q)
        assert len(p) == q
        assert p[0] == Fraction(0)
        assert all(p[x] == Fraction(1, q - 1) for x in range(1, q))
        assert sum(p) == Fraction(1)


def test_stepanov_bound_scaling():
    assert stepanov_multiplicity_bound(1) == 1
    assert stepanov_multiplicity_bound(4) == 2
    assert stepanov_multiplicity_bound(5) == 2
    assert stepanov_multiplicity_bound(9) == 3
    assert stepanov_multiplicity_bound(25) == 5
    assert stepanov_multiplicity_bound(100) == 10


def test_path_quadric_phase_and_ramanujan_identity():
    """Prueft die Pfad-Quadrik sum_{h=1}^{q-1} e_q(h * Q(x)) == c_q(Q(x)) exakt."""
    for q in (2, 3, 5, 7):
        # k = 2: Q(x0, x1) = x0 * x1
        for x0 in range(q):
            for x1 in range(q):
                phase = path_quadric_phase(q, (x0, x1))
                assert phase == (x0 * x1) % q
                r_sum = path_quadric_ramanujan_sum(q, (x0, x1))
                expected = ramanujan_summe(q, phase)
                assert r_sum == expected


def test_path_quadric_gauss_sum_even_saturation():
    """Fuer k=2,4 saturiert die Gauss-Summe der Pfad-Quadrik exakt q^{k/2} = sqrt(dim)."""
    for q in (2, 3, 5):
        for k in (2, 4):
            g = path_quadric_gauss_sum_even(q, k)
            assert g == q ** (k // 2)
            assert g * g == q ** k  # saturiert dim bit-exakt

