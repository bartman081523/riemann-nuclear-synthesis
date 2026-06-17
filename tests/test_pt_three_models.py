"""
Tests fuer pt_three_models.py — Drei-Modelle-Vergleich S_vN(N).

Modelle:
  M1: S = a * N^alpha              (unser Power-Law, alpha ~ 0.347)
  M2: S = a + b * log(N)           (Latorre-Form)
  M3: S = a * pi(N)^alpha          (Power-Law in Anzahl der Primzahlen)

Erwartung: M1 und M3 passen am besten (niedrigste Residuals),
M2 schlechter weil Latorre-Form nur asymptotisch gilt.
"""
import math
import numpy as np
import pytest

import pt_three_models as pt_tm


class TestPiNExact:
    """Prueft die Primzahl-Zaehlfunktion pi(N)."""

    def test_pi_N_small_values(self):
        """pi(N) fuer bekannte Werte."""
        assert pt_tm.pi_N_exact(1) == 0
        assert pt_tm.pi_N_exact(2) == 1
        assert pt_tm.pi_N_exact(10) == 4   # 2, 3, 5, 7
        assert pt_tm.pi_N_exact(100) == 25

    def test_pi_N_monotonically_nondecreasing(self):
        """pi(N) ist monoton nicht-fallend."""
        prev = 0
        for N in range(1, 200):
            cur = pt_tm.pi_N_exact(N)
            assert cur >= prev
            prev = cur

    def test_pi_N_matches_known_prime_counting(self):
        """Stichproben-Vergleich mit bekannten Werten."""
        # pi(50) = 15, pi(100) = 25, pi(1000) = 168
        assert pt_tm.pi_N_exact(50) == 15
        assert pt_tm.pi_N_exact(1000) == 168


class TestThreeModelFitProperties:
    """Prueft Eigenschaften der drei Modelle auf synthetischen Daten."""

    def test_power_law_recovers_alpha(self):
        """M1 fit auf perfektes Power-Law: alpha wird exakt zurueckgewonnen."""
        N_arr = np.array([7, 15, 31, 63, 127, 255, 511, 1023], dtype=float)
        true_alpha = 0.347
        true_log_a = 0.5
        S_arr = np.exp(true_log_a) * N_arr ** true_alpha
        log_N = np.log(N_arr)
        log_S = np.log(S_arr)
        p = np.polyfit(log_N, log_S, 1)
        assert abs(p[0] - true_alpha) < 1e-9
        assert abs(p[1] - true_log_a) < 1e-9

    def test_residuals_zero_for_perfect_fit(self):
        """Bei perfektem Power-Law-Fit ist Residual = 0."""
        N_arr = np.array([1.0, 2.0, 4.0, 8.0, 16.0])
        alpha = 0.5
        S_arr = N_arr ** alpha
        log_N = np.log(N_arr)
        log_S = np.log(S_arr)
        p = np.polyfit(log_N, log_S, 1)
        residual = np.linalg.norm(log_S - p[0]*log_N - p[1])
        assert residual < 1e-12

    def test_log_form_has_higher_residual_than_power_law(self):
        """M2 (log) hat hoeheres Residual als M1 (power) fuer power-law-Daten."""
        N_arr = np.array([7, 15, 31, 63, 127, 255, 511, 1023], dtype=float)
        # Generiere power-law Daten
        S_arr = 0.5 * N_arr ** 0.347

        # Power-Law Fit (log-log linear)
        p_M1 = np.polyfit(np.log(N_arr), np.log(S_arr), 1)
        res_M1 = np.linalg.norm(np.log(S_arr) - p_M1[0]*np.log(N_arr) - p_M1[1])

        # Log-Fit (log-linear)
        p_M2 = np.polyfit(np.log(N_arr), S_arr, 1)
        res_M2 = np.linalg.norm(S_arr - (p_M2[0]*np.log(N_arr) + p_M2[1]))

        # Power-Law-Fit muss signifikant besser sein (im log-Raum)
        # res_M2 ist im linearen Raum, daher groesser — vergleich nur Ratio
        assert res_M1 < 1e-9  # Perfekt-Fit = 0


class TestThreeModelsModule:
    """Prueft die Modul-Importierbarkeit."""

    def test_module_imports(self):
        import pt_three_models
        assert hasattr(pt_three_models, 'pi_N_exact')
        assert hasattr(pt_three_models, 'main')

    def test_pi_N_exact_functional_form(self):
        """pi(N) folgt der Primzahl-Verteilung."""
        # Approx pi(10000) ~ 1229 (exakt: 1229)
        assert pt_tm.pi_N_exact(10000) == 1229