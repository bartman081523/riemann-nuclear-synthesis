"""
Tests fuer pt_prime_state_N255.py — Saeule 3 N-Erweiterung auf N=255..1023.

Verifiziert die statevector-first Architektur:
  |P_N> = (1/sqrt(pi(N))) * sum_{p<=N} |p>
  Schmidt-Zerlegung in A (n_A Qubits LSB) und B (n_B Qubits MSB)
  Schmidt-vN und Renyi-2 Entropie.

Resolution (c) Hypothese:
  alpha stabilisiert sich bei ~0.347 fuer N >= 255 (Asymptotik).
"""
import math
import numpy as np
import pytest

import pt_prime_state_N255 as pt_n255


class TestIsPrime:
    """Prueft die is_prime Funktion."""

    def test_is_prime_small_values(self):
        """Bekannte Primzahlen bis 20."""
        assert pt_n255.is_prime(2)
        assert pt_n255.is_prime(3)
        assert pt_n255.is_prime(5)
        assert pt_n255.is_prime(7)
        assert pt_n255.is_prime(11)
        assert pt_n255.is_prime(13)
        assert pt_n255.is_prime(17)
        assert pt_n255.is_prime(19)

    def test_is_prime_composites(self):
        """Zusammengesetzte Zahlen sind keine Primzahlen."""
        assert not pt_n255.is_prime(4)
        assert not pt_n255.is_prime(6)
        assert not pt_n255.is_prime(8)
        assert not pt_n255.is_prime(9)
        assert not pt_n255.is_prime(10)
        assert not pt_n255.is_prime(100)
        assert not pt_n255.is_prime(1000)

    def test_is_prime_edge_cases(self):
        """Edge cases: 0, 1, negative Zahlen."""
        assert not pt_n255.is_prime(0)
        assert not pt_n255.is_prime(1)
        assert not pt_n255.is_prime(-5)

    def test_is_prime_known_large(self):
        """Bekannte grosse Primzahlen."""
        assert pt_n255.is_prime(127)
        assert pt_n255.is_prime(997)  # groesste 3-stellige Primzahl
        assert not pt_n255.is_prime(1000)


class TestConstructPN:
    """Prueft die Konstruktion des |P_N> Zustands."""

    def test_construct_P_N_normalization(self):
        """|P_N> muss normiert sein."""
        for N in [7, 15, 31, 63, 127, 255]:
            psi, pi_N, n_qubits = pt_n255.construct_P_N(N)
            assert abs(np.linalg.norm(psi) - 1.0) < 1e-12

    def test_construct_P_N_qubit_count(self):
        """n_qubits = ceil(log2(N+1))."""
        for N in [7, 15, 31, 63, 127, 255, 1023]:
            psi, pi_N, n_qubits = pt_n255.construct_P_N(N)
            expected_qubits = int(math.ceil(math.log2(N + 1)))
            assert n_qubits == expected_qubits

    def test_construct_P_N_prime_count(self):
        """pi(N) = Anzahl der Primzahlen <= N."""
        # pi(10) = 4, pi(100) = 25
        _, pi_10, _ = pt_n255.construct_P_N(10)
        _, pi_100, _ = pt_n255.construct_P_N(100)
        assert pi_10 == 4
        assert pi_100 == 25

    def test_construct_P_N_amplitudes_at_prime_positions(self):
        """|psi[p]| = 1/sqrt(pi(N)) fuer p prim, sonst 0."""
        N = 10
        psi, pi_N, _ = pt_n255.construct_P_N(N)
        expected_amplitude = 1.0 / math.sqrt(pi_N)
        for p in [2, 3, 5, 7]:
            assert abs(abs(psi[p]) - expected_amplitude) < 1e-12
        for c in [0, 1, 4, 6, 8, 9, 10]:
            assert abs(psi[c]) < 1e-12


class TestSchmidtDecomposition:
    """Prueft die Schmidt-Zerlegung."""

    def test_schmidt_probabilities_sum_to_one(self):
        """sum(s_i^2) = 1 (Schmidt-Wahrscheinlichkeiten summieren zu 1)."""
        psi, _, _ = pt_n255.construct_P_N(31)
        n_qubits = int(math.ceil(math.log2(32)))
        n_A = n_qubits // 2
        s_sq = pt_n255.schmidt_decomposition(psi, n_A)
        assert abs(s_sq.sum() - 1.0) < 1e-12

    def test_schmidt_pure_product_has_one_nonzero(self):
        """Produkt-Zustand |00>: 1 NICHT-NULL Schmidt-Komponente mit s^2 = 1."""
        psi = np.zeros(4, dtype=complex)
        psi[0] = 1.0  # |00>
        s_sq = pt_n255.schmidt_decomposition(psi, n_A=1)
        # SVD kann >1 Element liefern, aber nur eines ist nicht-null
        assert s_sq[0] > 1.0 - 1e-12
        assert s_sq.sum() < 1.0 + 1e-12
        # Filtere Nullen
        nonzero = s_sq[s_sq > 1e-12]
        assert len(nonzero) == 1

    def test_schmidt_bell_state(self):
        """Bell-Zustand |Phi+>: 2 Schmidt-Komponenten, beide = 1/2."""
        psi = np.zeros(4, dtype=complex)
        psi[0] = 1.0 / math.sqrt(2)  # |00>
        psi[3] = 1.0 / math.sqrt(2)  # |11>
        s_sq = pt_n255.schmidt_decomposition(psi, n_A=1)
        assert len(s_sq) == 2
        assert abs(s_sq[0] - 0.5) < 1e-12
        assert abs(s_sq[1] - 0.5) < 1e-12


class TestVonNeumannEntropy:
    """Prueft die Schmidt-vN Entropie."""

    def test_vN_pure_product_zero(self):
        """Produkt-Zustand: S_vN = 0."""
        s_sq = np.array([1.0])
        assert abs(pt_n255.von_neumann_entropy(s_sq)) < 1e-12

    def test_vN_maximally_mixed(self):
        """Maximale Verschränkung: S_vN = log_2(d_A)."""
        d = 4
        s_sq = np.ones(d) / d
        s_vN = pt_n255.von_neumann_entropy(s_sq)
        assert abs(s_vN - math.log2(d)) < 1e-12

    def test_vN_decreases_with_concentration(self):
        """Konzentriertere Verteilung: kleinere S_vN."""
        s_sq1 = np.array([0.5, 0.3, 0.2])
        s_sq2 = np.array([0.9, 0.05, 0.05])
        assert pt_n255.von_neumann_entropy(s_sq2) < pt_n255.von_neumann_entropy(s_sq1)

    def test_vN_bell_state(self):
        """Bell-Zustand mit 2 Niveaus: S_vN = 1."""
        s_sq = np.array([0.5, 0.5])
        assert abs(pt_n255.von_neumann_entropy(s_sq) - 1.0) < 1e-12


class TestRenyi2InN255:
    """Prueft die in pt_prime_state_N255 definierte renyi_2."""

    def test_renyi_2_uniform(self):
        """Gleichverteilung: S_2 = log_2(d)."""
        d = 8
        s_sq = np.ones(d) / d
        s_2 = pt_n255.renyi_2(s_sq)
        assert abs(s_2 - math.log2(d)) < 1e-12

    def test_renyi_2_pure_zero(self):
        s_sq = np.array([1.0, 0.0, 0.0])
        assert abs(pt_n255.renyi_2(s_sq)) < 1e-12

    def test_renyi_2_bell_state(self):
        """Bell-Zustand: S_2 = S_vN = 1 (maximal gemischt, S_2 = S_vN)."""
        s_sq = np.array([0.5, 0.5])
        s_2 = pt_n255.renyi_2(s_sq)
        s_vN = pt_n255.von_neumann_entropy(s_sq)
        assert abs(s_2 - s_vN) < 1e-12


class TestN255Module:
    """Prueft die Modul-Importierbarkeit und Konstruktions-Konsistenz."""

    def test_module_imports(self):
        import pt_prime_state_N255
        assert hasattr(pt_prime_state_N255, 'is_prime')
        assert hasattr(pt_prime_state_N255, 'construct_P_N')
        assert hasattr(pt_prime_state_N255, 'schmidt_decomposition')
        assert hasattr(pt_prime_state_N255, 'von_neumann_entropy')
        assert hasattr(pt_prime_state_N255, 'renyi_2')
        assert hasattr(pt_prime_state_N255, 'main')

    def test_full_pipeline_N255(self):
        """Komplette Pipeline: construct -> schmidt -> entropy fuer N=255."""
        psi, pi_N, n_qubits = pt_n255.construct_P_N(255)
        n_A = n_qubits // 2
        s_sq = pt_n255.schmidt_decomposition(psi, n_A)
        s_vN = pt_n255.von_neumann_entropy(s_sq)
        s_2 = pt_n255.renyi_2(s_sq)
        # Sanity bounds: S_vN muss > 0 (kein reiner Produkt-Zustand)
        # und < log2(dim_A)
        dim_A = 2 ** n_A
        assert 0 < s_vN < math.log2(dim_A) + 1e-12
        # Renyi-2 Ungleichung
        assert s_2 <= s_vN + 1e-12
        # Renyi-2 muss positiv sein
        assert s_2 > 0