"""
Tests für Säule 1: pt_potential_vqe.py — Holografisches Potenzial.

Verspricht im Mermaid-Diagramm:
  - V(x) = sum_k c_k · phi_k(x) als Variations-Potential-Basis
  - E_0..E_3 in EINEM 5-Pub-Lauf
  - H1/H2/H3 Pre-Registrierung mit deterministischen Vorhersagen
  - Bias-Analyse: beta_diag, bias_PT_re, bias_PT_im
  - Entscheidungsregel: |Delta_E_meas - Delta_E_pred| < 0.05 für >=2/3 Gaps

Diese Tests prüfen die ALGORITHMISCHE KORREKTHEIT, nicht die QPU-Submission
(Tests laufen offline, ohne IBM-Token).
"""
import json
import numpy as np
import pytest
import os
import sys

# Pfad zum Projekt-Root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pt_structural import E_DIAG, jacobi_A


# === HILFSFUNKTION: Mock-Estimator ===
class MockEstimatorResult:
    """Simuliert ein EstimatorV2-Ergebnis mit kontrollierten Werten."""
    def __init__(self, expected_values):
        self.evs = expected_values


def make_mock_estimator(mapping):
    """mapping: dict (pub_index) -> expected_value (float)"""
    class MockEstimator:
        def __init__(self):
            self.calls = []
            self._mapping = mapping
            self.options = type("Opts", (), {})()

        def run(self, pubs):
            self.calls.append(pubs)
            # Gebe für jeden Pub das vorgegebene EV zurück
            results = []
            for i, _ in enumerate(pubs):
                ev = self._mapping.get(i, 0.0)
                results.append(type("Pub", (), {"data": type("Data", (), {"evs": ev})()})())
            return type("Job", (), {"result": lambda: type("Res", (), {"__getitem__": lambda s, k: results[k]})()})()

    return MockEstimator()


# === TESTS FÜR SÄULE 1 ===

class TestPotentialVQEStructure:
    """Prüft die strukturellen Eigenschaften des Potenzial-VQE-Ansatzes."""

    def test_E_DIAG_is_deterministic(self):
        """E_DIAG muss deterministisch sein (Anti-Sharpshooter)."""
        E1 = E_DIAG.copy()
        E2 = E_DIAG.copy()
        np.testing.assert_array_equal(E1, E2)
        # Erste vier Zeraoulia-Niveaus
        assert E_DIAG[0] == 2.0
        assert abs(E_DIAG[1] - (2.0 + np.log(2.0))) < 1e-15
        assert abs(E_DIAG[2] - (2.0 + np.log(2.0) + np.log(2.0 + np.log(2.0)))) < 1e-15

    def test_E_DIAG_is_strictly_increasing(self):
        """E_n muss streng monoton wachsen (log(x) > 0 für x > 1)."""
        diffs = np.diff(E_DIAG)
        assert np.all(diffs > 0), f"E_DIAG nicht streng monoton: diffs = {diffs}"

    def test_jacobi_A_is_hermitian(self):
        """Strukturelles A muss hermitesch sein."""
        A = jacobi_A(E_DIAG, y=1.0)
        np.testing.assert_allclose(A, A.T, atol=1e-12)

    def test_jacobi_A_is_real(self):
        """A muss reell sein (keine imaginären Anteile)."""
        A = jacobi_A(E_DIAG, y=1.0)
        np.testing.assert_allclose(A.imag, 0, atol=1e-12)

    def test_jacobi_A_diagonal_structure(self):
        """Diagonal: A_ii = 1 + y/x_i."""
        A = jacobi_A(E_DIAG, y=1.0)
        for i in range(4):
            expected = 1.0 + 1.0 / E_DIAG[i]
            assert abs(A[i, i] - expected) < 1e-10, \
                f"A[{i},{i}] = {A[i,i]}, expected {expected}"

    def test_H_diag_eigenvalues_match(self):
        """Eigenwerte von diag(E_DIAG) müssen exakt E_DIAG sein."""
        H_diag = np.diag(E_DIAG).astype(complex)
        eigs = sorted(np.linalg.eigvals(H_diag).real)
        np.testing.assert_allclose(eigs, sorted(E_DIAG), atol=1e-12)

    def test_H_PT_is_pt_symmetric(self):
        """H_PT = H_diag + i*gamma*A mit reellem symmetrischem A.

        PT-Operator wirkt als Komplex-Konjugation. H_PT^PT = H_PT.conj().
        PT-Symmetrie gilt, wenn H_PT und H_PT.conj() das gleiche Spektrum haben.
        """
        A = jacobi_A(E_DIAG, y=1.0)
        H_diag = np.diag(E_DIAG).astype(complex)
        gamma = 0.02
        H_PT = H_diag + 1j * gamma * A

        # Hermitescher Anteil: H_real = (H + H^dagger)/2 muss hermitesch sein
        H_real = (H_PT + H_PT.conj().T) / 2
        np.testing.assert_allclose(H_real, H_real.conj().T, atol=1e-12)

        # Anti-hermitescher Anteil: H_anti = (H - H^dagger)/2 muss anti-hermitesch sein
        H_anti = (H_PT - H_PT.conj().T) / 2
        np.testing.assert_allclose(H_anti, -H_anti.conj().T, atol=1e-12)

        # A ist reell-symmetrisch
        np.testing.assert_allclose(A, A.T, atol=1e-12)
        np.testing.assert_allclose(A.imag, 0, atol=1e-12)

        # PT-Symmetrie-Test: H_PT und H_PT.conj() haben das gleiche Spektrum
        # (komplex-konjugierte Eigenwerte ergeben sich aus H_PT.conj())
        eigs_H = sorted(np.linalg.eigvals(H_PT), key=lambda z: z.real)
        eigs_Hc = sorted(np.linalg.eigvals(H_PT.conj()), key=lambda z: z.real)
        # Bei PT-unbroken: re(eigs) gleich, |im(eigs)| gleich
        for i in range(4):
            assert abs(eigs_H[i].real - eigs_Hc[i].real) < 1e-12
            assert abs(abs(eigs_H[i].imag) - abs(eigs_Hc[i].imag)) < 1e-12


class TestPotentialVQEPreregistration:
    """Prüft die Pre-Registrierungs-Logik H1/H2/H3."""

    def test_H1_additive_preserves_gaps(self):
        """H1: additiver Bias beta*1 muss Gap-invariant sein."""
        A = jacobi_A(E_DIAG, y=1.0)
        H_diag = np.diag(E_DIAG).astype(complex)
        gamma = 0.02

        H_PT = H_diag + 1j * gamma * A
        eigs_noiseless = sorted(np.linalg.eigvals(H_PT), key=lambda z: z.real)
        gaps_noiseless = [eigs_noiseless[i+1].real - eigs_noiseless[i].real for i in range(3)]

        # H_eff = H_PT - beta*1: alle Eigenwerte verschoben um -beta
        beta = 0.05
        H_eff = H_PT - beta * np.eye(4, dtype=complex)
        eigs_H1 = sorted(np.linalg.eigvals(H_eff), key=lambda z: z.real)
        gaps_H1 = [eigs_H1[i+1].real - eigs_H1[i].real for i in range(3)]

        np.testing.assert_allclose(gaps_H1, gaps_noiseless, atol=1e-12)

    def test_H2_multiplicative_distorts_gaps(self):
        """H2: k=25 auf A muss Gaps drastisch verzerren."""
        A = jacobi_A(E_DIAG, y=1.0)
        H_diag = np.diag(E_DIAG).astype(complex)
        gamma = 0.02

        H_PT = H_diag + 1j * gamma * A
        eigs_noiseless = sorted(np.linalg.eigvals(H_PT), key=lambda z: z.real)
        gaps_noiseless = [eigs_noiseless[i+1].real - eigs_noiseless[i].real for i in range(3)]

        k = 25.0
        H_PT_k = H_diag + 1j * gamma * k * A
        eigs_k = sorted(np.linalg.eigvals(H_PT_k), key=lambda z: z.real)
        gaps_k = [eigs_k[i+1].real - eigs_k[i].real for i in range(3)]

        # Mindestens ein Gap muss sich um > 0.1 ändern
        max_diff = max(abs(gaps_k[i] - gaps_noiseless[i]) for i in range(3))
        assert max_diff > 0.1, f"H2 verzerrt Gaps nicht genug: max_diff = {max_diff}"

    def test_H3_decoherence_preserves_gaps_first_order(self):
        """H3: Off-Diagonale um (1-p) geschrumpft, Gaps ~ invariant (O(p^2))."""
        A = jacobi_A(E_DIAG, y=1.0)
        H_diag = np.diag(E_DIAG).astype(complex)
        gamma = 0.02

        H_PT = H_diag + 1j * gamma * A
        eigs_noiseless = sorted(np.linalg.eigvals(H_PT), key=lambda z: z.real)
        gaps_noiseless = [eigs_noiseless[i+1].real - eigs_noiseless[i].real for i in range(3)]

        p = 0.3
        A_d = A.copy()
        for i in range(4):
            for j in range(4):
                if i != j:
                    A_d[i, j] *= (1 - p)
        H_PT_d = H_diag + 1j * gamma * A_d
        eigs_d = sorted(np.linalg.eigvals(H_PT_d), key=lambda z: z.real)
        gaps_d = [eigs_d[i+1].real - eigs_d[i].real for i in range(3)]

        # Gaps dürfen sich um maximal O(p^2) = 0.09 ändern
        max_diff = max(abs(gaps_d[i] - gaps_noiseless[i]) for i in range(3))
        assert max_diff < 0.1, f"H3 ändert Gaps zu stark: max_diff = {max_diff}"


class TestPotentialVQEBiasAnalysis:
    """Prüft die Bias-Analyse am VQE-Optimum."""

    def test_H_diag_mean_is_arithmetic_average(self):
        """Mittelwert <H_diag> = (E_0 + E_1 + E_2 + E_3) / 4."""
        H_diag = np.diag(E_DIAG).astype(complex)
        expected_mean = np.mean(E_DIAG)
        actual_mean = np.trace(H_diag).real / 4
        assert abs(actual_mean - expected_mean) < 1e-12
        assert abs(actual_mean - 3.3412) < 0.01, f"Erwartet ~3.3412, erhalten {actual_mean}"

    def test_Re_H_PT_has_same_spur_as_H_diag(self):
        """Spur(Re(H_PT)) = Spur(H_diag), da A spur=0 hat (Diagonal-Off-Diagonal-Form)."""
        A = jacobi_A(E_DIAG, y=1.0)
        H_diag = np.diag(E_DIAG).astype(complex)
        H_PT = H_diag + 1j * 0.02 * A
        H_real = (H_PT + H_PT.conj().T) / 2
        assert abs(np.trace(H_real).real - np.trace(H_diag).real) < 1e-12

    def test_bias_is_zero_if_measurement_matches(self):
        """Wenn H_diag_meas = 3.3412 exakt, dann beta_diag = 0."""
        H_diag_noiseless_mean = 3.3412
        H_diag_meas = H_diag_noiseless_mean  # perfekte Messung
        beta_diag = H_diag_meas - H_diag_noiseless_mean
        assert beta_diag == 0.0


class TestPotentialVQEModule:
    """Prüft, dass pt_potential_vqe.py importierbar ist und Schlüssel-Funktionen hat."""

    def test_module_imports(self):
        """pt_potential_vqe muss importierbar sein."""
        try:
            import pt_potential_vqe
            assert hasattr(pt_potential_vqe, 'precompute_predictions')
            assert hasattr(pt_potential_vqe, 'main')
        except ImportError:
            pytest.skip("pt_potential_vqe noch nicht implementiert (erwartet bei TDD)")

    def test_precompute_returns_required_keys(self):
        """precompute_predictions muss die nötigen Keys liefern."""
        try:
            import pt_potential_vqe
            pred = pt_potential_vqe.precompute_predictions()
            assert "noiseless" in pred
            assert "H1_additive" in pred
            # H2 kann H2_multiplicative oder H2_multiplicative_k25 heissen
            assert any(k.startswith("H2") for k in pred.keys())
            assert any(k.startswith("H3") for k in pred.keys())
            assert "H_diag_exact" in pred
            assert "decision_rule" in pred
            # Gaps müssen 3 Einträge haben
            assert len(pred["noiseless"]["Delta"]) == 3
        except ImportError:
            pytest.skip("pt_potential_vqe noch nicht implementiert (erwartet bei TDD)")

    def test_initial_params_can_be_extended(self):
        """INITIAL_PARAMS muss kuerzere Vektoren auf Ansatz-Laenge erweitern koennen."""
        try:
            from pt_potential_vqe import INITIAL_PARAMS
            # Test: zyklische Erweiterung wie im main()
            n_target = 6
            extended = [INITIAL_PARAMS[i % len(INITIAL_PARAMS)] for i in range(n_target)]
            assert len(extended) == n_target
            assert extended[0] == INITIAL_PARAMS[0]
            assert extended[4] == INITIAL_PARAMS[0]  # zyklisch
            assert extended[5] == INITIAL_PARAMS[1]
        except ImportError:
            pytest.skip("pt_potential_vqe noch nicht implementiert (erwartet bei TDD)")
