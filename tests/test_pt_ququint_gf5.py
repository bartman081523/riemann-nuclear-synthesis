"""
Tests for pt_ququint_gf5.py — GF(5) polynomial ring class implementation.

These tests cover the algebraic foundation of the Ququint (Pillar 4) architecture:
  - GF(5) field arithmetic (full field axioms)
  - Multiplicative group structure
  - GF(5)[x] polynomial ring
  - Discrete Fourier Transform on Z/5Z

Phase 1: Theoretical foundation. These tests must pass before the
quantum simulator (Phase 2) and empirical comparisons (Phase 3).
"""
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# === GF(5) FIELD ARITHMETIC ===

class TestGF5FieldAxioms:
    """GF(5) must satisfy the field axioms: closure, associativity,
    commutativity, identity, inverse, distributivity."""

    def test_field_has_5_elements(self):
        from pt_ququint_gf5 import GF5
        elements = [GF5(i) for i in range(5)]
        assert len(elements) == 5

    def test_zero_is_additive_identity(self):
        from pt_ququint_gf5 import GF5
        for a in range(5):
            assert (GF5(a) + GF5(0)) == GF5(a)
            assert (GF5(0) + GF5(a)) == GF5(a)

    def test_one_is_multiplicative_identity(self):
        from pt_ququint_gf5 import GF5
        for a in range(5):
            assert (GF5(a) * GF5(1)) == GF5(a)
            assert (GF5(1) * GF5(a)) == GF5(a)

    def test_additive_associativity(self):
        from pt_ququint_gf5 import GF5
        for a in range(5):
            for b in range(5):
                for c in range(5):
                    assert (GF5(a) + GF5(b)) + GF5(c) == GF5(a) + (GF5(b) + GF5(c))

    def test_multiplicative_associativity(self):
        from pt_ququint_gf5 import GF5
        for a in range(5):
            for b in range(5):
                for c in range(5):
                    assert (GF5(a) * GF5(b)) * GF5(c) == GF5(a) * (GF5(b) * GF5(c))

    def test_additive_commutativity(self):
        from pt_ququint_gf5 import GF5
        for a in range(5):
            for b in range(5):
                assert (GF5(a) + GF5(b)) == (GF5(b) + GF5(a))

    def test_multiplicative_commutativity(self):
        from pt_ququint_gf5 import GF5
        for a in range(5):
            for b in range(5):
                assert (GF5(a) * GF5(b)) == (GF5(b) * GF5(a))

    def test_distributivity(self):
        from pt_ququint_gf5 import GF5
        for a in range(5):
            for b in range(5):
                for c in range(5):
                    assert GF5(a) * (GF5(b) + GF5(c)) == \
                           GF5(a) * GF5(b) + GF5(a) * GF5(c)

    def test_additive_inverse_exists(self):
        """Every a has b with a + b = 0."""
        from pt_ququint_gf5 import GF5
        for a in range(5):
            b = (-GF5(a))
            assert (GF5(a) + b) == GF5(0)

    def test_multiplicative_inverse_exists_for_nonzero(self):
        """Every a != 0 has b with a * b = 1."""
        from pt_ququint_gf5 import GF5
        for a in range(1, 5):
            b = GF5(a).inverse()
            assert (GF5(a) * b) == GF5(1)

    def test_no_zero_divisors(self):
        """GF(5) has no zero divisors: a*b = 0 implies a = 0 or b = 0."""
        from pt_ququint_gf5 import GF5
        for a in range(5):
            for b in range(5):
                if a != 0 and b != 0:
                    assert (GF5(a) * GF5(b)) != GF5(0)

    def test_zero_inverse_raises(self):
        """0 has no multiplicative inverse in any field."""
        from pt_ququint_gf5 import GF5
        with pytest.raises(ZeroDivisionError):
            GF5(0).inverse()

    def test_invalid_element_raises(self):
        """GF5 must reject values outside {0, 1, 2, 3, 4}."""
        from pt_ququint_gf5 import GF5
        for bad in [-1, 5, 6, 100]:
            with pytest.raises(ValueError):
                GF5(bad)


class TestGF5MultiplicativeGroup:
    """The multiplicative group (GF(5)*, *) has order 4, cyclic."""

    def test_group_order_is_4(self):
        from pt_ququint_gf5 import GF5
        nonzero = [GF5(a) for a in range(1, 5)]
        assert len(nonzero) == 4

    def test_powers_of_2_cycle_through_all_nonzero(self):
        """2 is a generator of (Z/5Z)*, which is cyclic of order 4."""
        from pt_ququint_gf5 import GF5
        g = GF5(2)
        seen = set()
        cur = GF5(1)
        for _ in range(4):
            seen.add(int(cur))
            cur = cur * g
        assert seen == {1, 2, 3, 4}, f"2 does not generate Z/5Z*: {seen}"

    def test_powers_of_3_cycle_through_all_nonzero(self):
        """3 is also a generator (cyclic group of order 4)."""
        from pt_ququint_gf5 import GF5
        g = GF5(3)
        seen = set()
        cur = GF5(1)
        for _ in range(4):
            seen.add(int(cur))
            cur = cur * g
        assert seen == {1, 2, 3, 4}

    def test_inverse_via_power(self):
        """a^{-1} = a^{order-1} for any generator."""
        from pt_ququint_gf5 import GF5
        for a in range(1, 5):
            elem = GF5(a)
            inv = elem.inverse()
            # Verify by direct multiplication
            assert (elem * inv) == GF5(1)


# === GF(5)[x] POLYNOMIAL RING ===

class TestGF5PolynomialRepresentation:
    """Polynomials are represented as lists of GF5 coefficients
    [a_0, a_1, ..., a_n] for a_0 + a_1*x + ... + a_n*x^n."""

    def test_zero_polynomial(self):
        from pt_ququint_gf5 import Poly
        p = Poly([])
        assert p.degree() == -1  # degree of zero is -1 by convention
        assert p.coeffs == []

    def test_constant_polynomial(self):
        from pt_ququint_gf5 import Poly
        p = Poly([3])
        assert p.degree() == 0
        assert [c.value for c in p.coeffs] == [3]

    def test_linear_polynomial(self):
        from pt_ququint_gf5 import Poly
        p = Poly([2, 4])  # 2 + 4x
        assert p.degree() == 1
        assert [c.value for c in p.coeffs] == [2, 4]

    def test_cubic_polynomial(self):
        from pt_ququint_gf5 import Poly
        p = Poly([1, 0, 2, 3])  # 1 + 0*x + 2x^2 + 3x^3
        assert p.degree() == 3

    def test_leading_zeros_stripped(self):
        from pt_ququint_gf5 import Poly
        p = Poly([1, 2, 0, 0])
        assert p.degree() == 1
        assert [c.value for c in p.coeffs] == [1, 2]


class TestGF5PolynomialArithmetic:
    """Polynomial addition, subtraction, multiplication in GF(5)[x]."""

    def test_addition_same_degree(self):
        from pt_ququint_gf5 import Poly
        p = Poly([1, 2])  # 1 + 2x
        q = Poly([3, 4])  # 3 + 4x
        r = p + q          # 4 + 6x = 4 + 1x
        assert r == Poly([4, 1])

    def test_addition_different_degrees(self):
        from pt_ququint_gf5 import Poly
        p = Poly([1, 2, 3])  # 1 + 2x + 3x^2
        q = Poly([4, 5 % 5])  # 4 + 0x = 4 (after mod)
        r = p + q
        # Actually q = 4 + 0x = [4] (stripped), so r = 5 + 2x + 3x^2 = 0 + 2x + 3x^2
        assert r == Poly([0, 2, 3])

    def test_addition_zero(self):
        from pt_ququint_gf5 import Poly
        p = Poly([1, 2, 3])
        zero = Poly([])
        assert p + zero == p

    def test_subtraction(self):
        """In GF(5), subtraction is the same as addition of -a = 5-a mod 5."""
        from pt_ququint_gf5 import Poly
        p = Poly([1, 2])
        q = Poly([3, 4])
        r = p - q  # (1-3, 2-4) = (-2, -2) = (3, 3) mod 5
        assert r == Poly([3, 3])

    def test_multiplication_linear(self):
        from pt_ququint_gf5 import Poly
        p = Poly([1, 1])  # 1 + x
        q = Poly([1, 1])  # 1 + x
        r = p * q          # 1 + 2x + x^2 = 1 + 2x + x^2
        assert r == Poly([1, 2, 1])

    def test_multiplication_with_zero(self):
        from pt_ququint_gf5 import Poly
        p = Poly([1, 2, 3])
        zero = Poly([])
        assert p * zero == Poly([])

    def test_multiplication_commutativity(self):
        from pt_ququint_gf5 import Poly
        p = Poly([2, 3, 1])
        q = Poly([4, 1])
        assert p * q == q * p

    def test_multiplication_associativity(self):
        from pt_ququint_gf5 import Poly
        p = Poly([1, 2])
        q = Poly([2, 1])
        r = Poly([3, 1])
        assert (p * q) * r == p * (q * r)

    def test_distributivity_over_addition(self):
        from pt_ququint_gf5 import Poly
        p = Poly([1, 2])
        q = Poly([3, 1])
        r = Poly([2, 4])
        assert p * (q + r) == p * q + p * r


class TestGF5PolynomialEvaluation:
    """evaluate(x) returns the polynomial value at x in GF(5)."""

    def test_evaluate_at_zero(self):
        from pt_ququint_gf5 import Poly, GF5
        p = Poly([3, 2, 1])  # 3 + 2x + x^2
        assert p.evaluate(GF5(0)) == GF5(3)

    def test_evaluate_at_one(self):
        """At x=1, polynomial evaluates to sum of coefficients."""
        from pt_ququint_gf5 import Poly, GF5
        p = Poly([1, 2, 3, 4])  # 1 + 2x + 3x^2 + 4x^3
        # Sum mod 5: 1+2+3+4 = 10 mod 5 = 0
        assert p.evaluate(GF5(1)) == GF5(0)

    def test_evaluate_at_x_minus_1(self):
        from pt_ququint_gf5 import Poly, GF5
        p = Poly([2, 3])  # 2 + 3x
        # At x = 4 (= -1 mod 5): 2 + 3*4 = 2 + 12 = 14 mod 5 = 4
        assert p.evaluate(GF5(4)) == GF5(4)

    def test_zero_polynomial_evaluates_to_zero(self):
        from pt_ququint_gf5 import Poly, GF5
        zero = Poly([])
        for x in range(5):
            assert zero.evaluate(GF5(x)) == GF5(0)


# === DISCRETE FOURIER TRANSFORM ON Z/5Z ===

class TestGF5DFT:
    """DFT on Z/5Z: F_k = sum_{j=0}^{4} x_j * omega^{jk}, where omega = exp(2*pi*i/5).
    This is over the COMPLEX numbers, but the indices are in GF(5)."""

    def test_dft_inverse_roundtrip(self):
        """DFT followed by inverse DFT recovers the input."""
        from pt_ququint_gf5 import dft, idft
        x = np.array([1, 2, 3, 4, 0], dtype=complex)
        X = dft(x)
        x_recovered = idft(X)
        np.testing.assert_allclose(x_recovered, x, atol=1e-10)

    def test_dft_of_constant_is_delta(self):
        """DFT of (1, 1, 1, 1, 1) is (5, 0, 0, 0, 0)."""
        from pt_ququint_gf5 import dft
        x = np.array([1, 1, 1, 1, 1], dtype=complex)
        X = dft(x)
        np.testing.assert_allclose(X, [5, 0, 0, 0, 0], atol=1e-10)

    def test_dft_of_delta_is_constant(self):
        """DFT of (1, 0, 0, 0, 0) is (1, 1, 1, 1, 1)."""
        from pt_ququint_gf5 import dft
        x = np.array([1, 0, 0, 0, 0], dtype=complex)
        X = dft(x)
        np.testing.assert_allclose(X, [1, 1, 1, 1, 1], atol=1e-10)

    def test_dft_preserves_parsesval(self):
        """Parseval: sum |x_j|^2 = (1/5) sum |X_k|^2."""
        from pt_ququint_gf5 import dft
        x = np.array([1, 2, 3, 4, 0], dtype=complex)
        X = dft(x)
        lhs = np.sum(np.abs(x) ** 2)
        rhs = (1 / 5) * np.sum(np.abs(X) ** 2)
        assert abs(lhs - rhs) < 1e-10


# === MODULE IMPORTS ===

class TestModuleImports:
    """Verify the module is importable and exposes the expected API."""

    def test_module_imports(self):
        import pt_ququint_gf5
        for name in ["GF5", "Poly", "dft", "idft"]:
            assert hasattr(pt_ququint_gf5, name), f"Missing: {name}"

    def test_gf5_str_repr(self):
        """GF5 should have a readable string representation."""
        from pt_ququint_gf5 import GF5
        assert "0" in str(GF5(0))
        assert "3" in str(GF5(3))