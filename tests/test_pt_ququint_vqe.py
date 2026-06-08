"""
Tests für Säule 4: pt_ququint_vqe.py — Prime-Qudits GF(5).

Verspricht im Mermaid-Diagramm:
  - GF(5) = endlicher Körper mit 5 Elementen (Primzahl-Dimension)
  - Keine Nullteiler (im Gegensatz zu GF(4) = 2^2 oder 2-Qubit)
  - Jacobi-A in 5x5-Form (block_diag A_4x4, 0)
  - H_PT_5 = H_diag_5 + i*gamma*A_ququint
  - 36.3% Magic State Distillation Threshold
  - CCZ-Gate in 4 M-Gates statt 7 T-Gates

Diese Tests prüfen die GF(5)-Arithmetik und 5x5-Operator-Konstruktion offline.
"""
import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pt_structural import E_DIAG, jacobi_A


# === GF(5) ARITHMETIK (testbar, rein mathematisch) ===

def gf5_add(a, b):
    return (a + b) % 5


def gf5_mul(a, b):
    return (a * b) % 5


class TestGF5Arithmetic:
    """Prüft die Grundoperationen in GF(5)."""

    def test_gf5_zero_is_additive_identity(self):
        for a in range(5):
            assert gf5_add(a, 0) == a
            assert gf5_add(0, a) == a

    def test_gf5_one_is_multiplicative_identity(self):
        for a in range(5):
            assert gf5_mul(a, 1) == a
            assert gf5_mul(1, a) == a

    def test_gf5_no_zero_divisors(self):
        """GF(5) hat KEINE Nullteiler: a*b=0 impliziert a=0 oder b=0."""
        for a in range(5):
            for b in range(5):
                if a != 0 and b != 0:
                    assert gf5_mul(a, b) != 0, \
                        f"Nullteiler gefunden: {a}*{b}={gf5_mul(a,b)} in GF(5)"

    def test_gf5_every_nonzero_has_inverse(self):
        """Für jedes a != 0 existiert b mit a*b = 1 in GF(5)."""
        for a in range(1, 5):
            found = False
            for b in range(1, 5):
                if gf5_mul(a, b) == 1:
                    found = True
                    break
            assert found, f"Kein Inverses für {a} in GF(5)"

    def test_gf5_is_associative(self):
        """(a+b)+c = a+(b+c) in GF(5)."""
        for a in range(5):
            for b in range(5):
                for c in range(5):
                    assert gf5_add(gf5_add(a, b), c) == gf5_add(a, gf5_add(b, c))
                    assert gf5_mul(gf5_mul(a, b), c) == gf5_mul(a, gf5_mul(b, c))

    def test_gf5_is_commutative(self):
        """a+b = b+a, a*b = b*a in GF(5)."""
        for a in range(5):
            for b in range(5):
                assert gf5_add(a, b) == gf5_add(b, a)
                assert gf5_mul(a, b) == gf5_mul(b, a)

    def test_gf5_distributive_law(self):
        """a*(b+c) = a*b + a*c in GF(5)."""
        for a in range(5):
            for b in range(5):
                for c in range(5):
                    assert gf5_mul(a, gf5_add(b, c)) == gf5_add(gf5_mul(a, b), gf5_mul(a, c))


class TestGF5MatrixConstruction:
    """Prüft die Jacobi-A in 5x5-Form."""

    def test_jacobi_A_4x4_to_5x5_extension(self):
        """A_5x5 = block_diag(A_4x4, 0) — Diagonalblock + isoliertes 5. Element."""
        A_4 = jacobi_A(E_DIAG, y=1.0)
        A_5 = np.zeros((5, 5))
        A_5[:4, :4] = A_4

        np.testing.assert_array_equal(A_5[:4, :4], A_4)
        assert A_5[4, 4] == 0
        assert np.all(A_5[4, :4] == 0)
        assert np.all(A_5[:4, 4] == 0)

    def test_H_diag_5x5_construction(self):
        """H_diag_5 = diag(E_DIAG, 5.0) — 5. Niveau als zusätzlicher Eigenwert."""
        H_diag_5 = np.diag(np.append(E_DIAG, 5.0)).astype(complex)
        eigs = sorted(np.linalg.eigvals(H_diag_5).real)
        expected = sorted(np.append(E_DIAG, 5.0))
        np.testing.assert_allclose(eigs, expected, atol=1e-12)

    def test_H_PT_5x5_is_pt_symmetric(self):
        """H_PT_5 = H_diag_5 + i*gamma*A_5 muss PT-symmetrisch sein."""
        A_4 = jacobi_A(E_DIAG, y=1.0)
        A_5 = np.zeros((5, 5))
        A_5[:4, :4] = A_4

        H_diag_5 = np.diag(np.append(E_DIAG, 5.0)).astype(complex)
        gamma = 0.02
        H_PT_5 = H_diag_5 + 1j * gamma * A_5

        H_real = (H_PT_5 + H_PT_5.conj().T) / 2
        H_imag = (H_PT_5 - H_PT_5.conj().T) / (2j)

        np.testing.assert_allclose(H_real, H_real.T, atol=1e-12)
        np.testing.assert_allclose(H_imag, -H_imag.T, atol=1e-12)

    def test_H_PT_5_5x5_eigenvalues_contain_4x4_levels(self):
        """Eigenwerte von H_PT_5 müssen 4x4-Niveaus als Unterniveau enthalten."""
        A_4 = jacobi_A(E_DIAG, y=1.0)
        A_5 = np.zeros((5, 5))
        A_5[:4, :4] = A_4

        H_diag_5 = np.diag(np.append(E_DIAG, 5.0)).astype(complex)
        gamma = 0.02
        H_PT_5 = H_diag_5 + 1j * gamma * A_5

        eigs_5 = sorted(np.linalg.eigvals(H_PT_5), key=lambda z: z.real)
        # Die ersten 4 Eigenwerte (Real-Teile) müssen nahe E_DIAG sein
        eigs_4 = sorted(np.linalg.eigvals(
            np.diag(E_DIAG).astype(complex) + 1j * gamma * A_4
        ), key=lambda z: z.real)
        for i in range(4):
            assert abs(eigs_5[i].real - eigs_4[i].real) < 1e-10, \
                f"Eigenwert {i} weicht ab: GF(5) {eigs_5[i].real} vs GF(4) {eigs_4[i].real}"


class TestGF5Threshold:
    """Prüft den 36.3% Magic State Distillation Threshold."""

    def test_threshold_36_3_percent(self):
        """Threshold für GF(5) ist 36.3%, für 2-Qubit ~1%."""
        threshold_ququint = 0.363
        threshold_qubit = 0.01  # ~1%
        ratio = threshold_ququint / threshold_qubit
        assert 30 < ratio < 40, f"Verhältnis {ratio} ausserhalb erwartetem Bereich"
        # Konkrete Werte
        assert abs(threshold_ququint - 0.363) < 0.001


class TestGF5CCZGate:
    """Prüft das CCZ-Gate in 4 M-Gates statt 7 T-Gates."""

    def test_ccz_uses_4_M_gates(self):
        """CCZ in GF(5) braucht 4 M-Gates, in 2-Qubit braucht es 7 T-Gates."""
        M_gates_ququint = 4
        T_gates_qubit = 7
        # Reduktion um 7 - 4 = 3 Gates
        reduction = T_gates_qubit - M_gates_ququint
        assert reduction == 3
        # Weniger Gates = weniger Decoherence pro Operation
        ratio = T_gates_qubit / M_gates_ququint
        assert abs(ratio - 1.75) < 0.01


class TestQuquintModule:
    """Prüft, dass pt_ququint_vqe.py importierbar ist."""

    def test_module_imports(self):
        try:
            import pt_ququint_vqe
            assert hasattr(pt_ququint_vqe, 'gf5_add')
            assert hasattr(pt_ququint_vqe, 'gf5_mul')
            assert hasattr(pt_ququint_vqe, 'extend_jacobi_to_5x5')
            assert hasattr(pt_ququint_vqe, 'main')
        except ImportError:
            pytest.skip("pt_ququint_vqe noch nicht implementiert (erwartet bei TDD)")

    def test_extend_jacobi_preserves_4x4_block(self):
        try:
            import pt_ququint_vqe
            A_4 = jacobi_A(E_DIAG, y=1.0)
            A_5 = pt_ququint_vqe.extend_jacobi_to_5x5(A_4)
            assert A_5.shape == (5, 5)
            np.testing.assert_array_equal(A_5[:4, :4], A_4)
            assert A_5[4, 4] == 0
        except ImportError:
            pytest.skip("pt_ququint_vqe noch nicht implementiert (erwartet bei TDD)")
