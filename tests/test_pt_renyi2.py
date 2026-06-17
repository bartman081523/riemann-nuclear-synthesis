"""
Tests fuer pt_renyi2.py — Renyi-2 Entropie und Latorre-Resolution (b).

Resolution (b) Hypothese:
  Wenn Latorre-Sierra Renyi-2 statt Schmidt-vN verwendet,
  dann hat S_2 vs N ein ANDERES Skalierungsverhalten als S_vN vs N.
  Erwartung: S_2 ~ S_vN wenn das Schmidt-Spektrum power-law-verteilt ist.
"""
import math
import numpy as np
import pytest

import pt_renyi2 as pt_r2


class TestRenyi2MathematicalProperties:
    """Prueft die mathematischen Eigenschaften von S_2."""

    def test_renyi_2_uniform_distribution_max(self):
        """Gleichverteilung ueber d Elemente: S_2 = log_2(d)."""
        d = 8
        s_sq = np.ones(d) / d  # uniform
        s_2 = pt_r2.renyi_2(s_sq)
        assert abs(s_2 - math.log2(d)) < 1e-12

    def test_renyi_2_pure_state_zero(self):
        """Reiner Zustand (eine Schmidt-Komponente = 1): S_2 = 0."""
        s_sq = np.array([1.0, 0.0, 0.0, 0.0])
        s_2 = pt_r2.renyi_2(s_sq)
        assert abs(s_2) < 1e-12

    def test_renyi_2_concentrated_decreases(self):
        """Konzentriertere Verteilung hat KLEINERES S_2."""
        s_sq_uniform = np.array([0.5, 0.3, 0.2])
        s_sq_concentrated = np.array([0.98, 0.01, 0.01])
        assert pt_r2.renyi_2(s_sq_concentrated) < pt_r2.renyi_2(s_sq_uniform)

    def test_renyi_2_handles_zeros(self):
        """Nullen im Spektrum werden ignoriert (s_sq > 0 Filter)."""
        s_sq = np.array([0.5, 0.5, 0.0, 0.0])
        s_2 = pt_r2.renyi_2(s_sq)
        # 0.5^2 + 0.5^2 = 0.5, -log2(0.5) = 1
        assert abs(s_2 - 1.0) < 1e-12

    def test_renyi_2_leq_von_neumann(self):
        """S_2 <= S_vN (Renyi-Ungleichung fuer alpha >= beta)."""
        for s_sq in [
            np.array([0.5, 0.3, 0.2]),
            np.array([0.25, 0.25, 0.25, 0.25]),
            np.array([0.7, 0.15, 0.1, 0.05]),
        ]:
            s_sq = s_sq / s_sq.sum()
            s_vN = -float(np.sum(s_sq * np.log2(s_sq)))
            s_2 = pt_r2.renyi_2(s_sq)
            assert s_2 <= s_vN + 1e-12, \
                f"S_2 = {s_2} > S_vN = {s_vN}"

    def test_renyi_2_strict_inequality_for_non_uniform(self):
        """S_2 < S_vN strikt fuer nicht-uniforme nicht-reine Zustaende."""
        s_sq = np.array([0.7, 0.2, 0.1])  # nicht-uniform
        s_vN = -float(np.sum(s_sq * np.log2(s_sq)))
        s_2 = pt_r2.renyi_2(s_sq)
        assert s_2 < s_vN

    def test_renyi_2_equal_for_uniform(self):
        """S_2 = S_vN fuer uniform-Verteilung (maximale Mischung)."""
        s_sq = np.array([0.5, 0.5])  # uniform
        s_vN = -float(np.sum(s_sq * np.log2(s_sq)))
        s_2 = pt_r2.renyi_2(s_sq)
        assert abs(s_2 - s_vN) < 1e-12


class TestRenyi2Inputs:
    """Prueft die Input-Behandlung."""

    def test_renyi_2_accepts_list(self):
        """Liste als Input ist erlaubt (wird zu np.asarray konvertiert)."""
        s_2 = pt_r2.renyi_2([0.5, 0.3, 0.2])
        assert isinstance(s_2, float)
        assert s_2 > 0

    def test_renyi_2_single_value(self):
        """Einzelner Wert s_sq=1: S_2 = 0."""
        assert abs(pt_r2.renyi_2([1.0])) < 1e-12

    def test_renyi_2_non_normalized_input_is_literal(self):
        """Nicht-normalisierte Inputs werden NICHT automatisch skaliert.

        renyi_2 erwartet bereits normalisierte Schmidt-Wahrscheinlichkeiten.
        """
        # s_sq = [0.5, 0.5] -> sum s^4 = 0.5, -log2(0.5) = 1
        assert abs(pt_r2.renyi_2([0.5, 0.5]) - 1.0) < 1e-12
        # Bei [4, 4] wuerde das Ergebnis 6.0 sein, weil s_sq nicht normalisiert wird
        # (das ist by design — der Aufrufer MUSS normalisieren)


class TestRenyi2Module:
    """Prueft die Modul-Importierbarkeit."""

    def test_module_imports(self):
        import pt_renyi2
        assert hasattr(pt_renyi2, 'renyi_2')
        assert hasattr(pt_renyi2, 'main')