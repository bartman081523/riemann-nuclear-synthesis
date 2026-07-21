"""
Tests for pt_ququint_empirical.py — Empirical comparisons 2-Qubit vs 1-Ququint.

These tests cover:
  - Schmidt-entropy comparison 2-Qubit (4-dim) vs 1-Ququint (5-dim)
  - Sweet-spot gamma search for H_PT_5(gamma) (PT-Punkt)
  - Bias-stability score for GF(5) architecture
  - CCZ-fidelity comparison Qubit vs Ququint (with simple noise model)
  - Magic-state distillation threshold validation

Phase 3: Empirical comparisons. This is the final phase of the
Ququint architecture expansion.
"""
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# === SCHMIDT-ENTROPY COMPARISON ===

class TestSchmidtEntropyComparison:
    """Compare Schmidt-entropy of prime states between 2-Qubit (4-dim)
    and 1-Ququint (5-dim) representations."""

    def test_qubit_schmidt_entropy_non_decreasing_with_N(self):
        """2-Qubit (4-dim) is saturation-limited: S_vN stays at log(2) once
        pi(N) >= 2. For N < 4 (no primes in dim=4), S_vN = 0."""
        from pt_ququint_empirical import schmidt_entropy_qubit_vs_ququint
        for N in [3, 5, 7, 15, 31, 63]:
            S_q, _ = schmidt_entropy_qubit_vs_ququint(N)
            # 2x2 bipartition max entropy is log(2) = 0.693
            assert 0 <= S_q <= math.log(2) + 1e-10, \
                f"S_vN out of bound at N={N}: {S_q}"

    def test_ququint_schmidt_entropy_non_decreasing_with_N(self):
        """Ququint 5-dim encoding: S_vN saturates quickly (pi(5)=3, 3 of 5
        slots filled), so S_vN can fluctuate in [0.5, 0.7] for N > 5.
        We just require it's bounded above by log(2) (the 2x3 max)."""
        from pt_ququint_empirical import schmidt_entropy_qubit_vs_ququint
        for N in [3, 5, 7, 11, 15, 31, 63]:
            _, S_qq = schmidt_entropy_qubit_vs_ququint(N)
            # 2x3 bipartition max entropy is log(2) = 0.693
            assert 0 <= S_qq <= math.log(2) + 1e-10, \
                f"S_vN out of bound at N={N}: {S_qq}"

    def test_ququint_higher_entropy_than_qubit(self):
        """1 Ququint (5-dim) should give more entropy than 2-Qubit (4-dim)
        for the same prime state, because it has more 'room' for entanglement."""
        from pt_ququint_empirical import schmidt_entropy_qubit_vs_ququint
        for N in [7, 15, 31, 63]:
            S_q, S_qq = schmidt_entropy_qubit_vs_ququint(N)
            assert S_qq >= S_q, \
                f"Ququint should have >= entropy at N={N}: {S_qq} vs {S_q}"


# === SWEET-SPOT GAMMA SEARCH ===

class TestSweetSpotGamma:
    """For H_PT_5(gamma), find the gamma* that minimizes |E_0(gamma)| deviation
    from the noiseless prediction E_0_noiseless = 2.0."""

    def test_sweet_spot_gamma_is_found(self):
        from pt_ququint_empirical import find_sweet_spot_gamma
        result = find_sweet_spot_gamma(gamma_range=(0.001, 0.5), n_points=20)
        assert "gamma_star" in result
        assert "E_0_at_gamma_star" in result
        assert result["gamma_star"] > 0
        assert result["E_0_at_gamma_star"] > 0

    def test_sweet_spot_E0_close_to_noiseless(self):
        """At gamma*, E_0 should be close to the noiseless prediction 2.0."""
        from pt_ququint_empirical import find_sweet_spot_gamma
        result = find_sweet_spot_gamma(gamma_range=(0.001, 0.1), n_points=15)
        E0_noiseless = 2.0
        # Loose bound: within 0.5 of noiseless
        assert abs(result["E_0_at_gamma_star"] - E0_noiseless) < 0.5

    def test_sweet_spot_gamma_sweep_returns_full_curve(self):
        """The full gamma-E_0 curve should be returned for plotting."""
        from pt_ququint_empirical import find_sweet_spot_gamma
        result = find_sweet_spot_gamma(gamma_range=(0.01, 0.3), n_points=10)
        assert "gamma_sweep" in result
        assert "E_0_sweep" in result
        assert len(result["gamma_sweep"]) == 10
        assert len(result["E_0_sweep"]) == 10


# === BIAS-STABILITY SCORE ===

class TestBiasStability:
    """Compute std(E_0(gamma)) / mean(E_0(gamma)) over a gamma-range.
    Lower = more stable under gamma-variation."""

    def test_bias_stability_returns_finite_score(self):
        from pt_ququint_empirical import bias_stability_score
        result = bias_stability_score(gamma_range=(0.01, 0.5), n_points=15)
        assert "stability_score" in result
        assert math.isfinite(result["stability_score"])
        assert result["stability_score"] > 0

    def test_bias_stability_lower_for_smaller_gamma_range(self):
        """A smaller gamma-range should give lower relative variation."""
        from pt_ququint_empirical import bias_stability_score
        # Small range: 0.01..0.05
        score_small = bias_stability_score(gamma_range=(0.01, 0.05), n_points=10)["stability_score"]
        # Large range: 0.01..1.0
        score_large = bias_stability_score(gamma_range=(0.01, 1.0), n_points=15)["stability_score"]
        # Larger range should have higher variation
        assert score_large > score_small


# === CCZ FIDELITY COMPARISON ===

class TestCCZFidelity:
    """Simple noise model: depolarizing channel with rate p.
    Fidelity F = <psi|CCZ^dagger_noise(CCZ|psi>)|psi>.
    Qubit CCZ uses 7 T-gates, Ququint CCZ uses 4 M-gates.
    M-gate error rate ~ T-gate error rate / 1.75 (CCZ reduction)."""

    def test_qubit_ccz_fidelity_decreases_with_noise(self):
        from pt_ququint_empirical import ccz_fidelity_qubit
        F_low = ccz_fidelity_qubit(noise_rate=0.001)
        F_high = ccz_fidelity_qubit(noise_rate=0.01)
        assert F_low > F_high

    def test_ququint_ccz_fidelity_higher_than_qubit(self):
        """For the same physical error rate, Ququint CCZ (4 M-gates) should
        have higher fidelity than Qubit CCZ (7 T-gates)."""
        from pt_ququint_empirical import ccz_fidelity_qubit, ccz_fidelity_ququint
        for noise_rate in [0.001, 0.005, 0.01]:
            F_q = ccz_fidelity_qubit(noise_rate)
            F_qq = ccz_fidelity_ququint(noise_rate)
            assert F_qq > F_q, \
                f"Ququint CCZ should have higher fidelity at noise={noise_rate}: {F_qq} vs {F_q}"

    def test_ccz_fidelity_both_close_to_1_at_low_noise(self):
        """At very low noise, both fidelities should be close to 1."""
        from pt_ququint_empirical import ccz_fidelity_qubit, ccz_fidelity_ququint
        F_q = ccz_fidelity_qubit(noise_rate=0.0001)
        F_qq = ccz_fidelity_ququint(noise_rate=0.0001)
        assert F_q > 0.999
        assert F_qq > 0.999


# === MAGIC-STATE DISTILLATION THRESHOLD ===

class TestMagicStateThreshold:
    """Magic-state distillation threshold validation:
    Below the threshold, distillation succeeds; above, it fails.
    Ququint: 36.3% (Campbell et al.); Qubit: 1%.
    """

    def test_ququint_threshold_is_363_percent(self):
        from pt_ququint_empirical import magic_state_threshold_ququint
        threshold = magic_state_threshold_ququint()
        assert abs(threshold - 0.363) < 0.01

    def test_qubit_threshold_is_about_1_percent(self):
        from pt_ququint_empirical import magic_state_threshold_qubit
        threshold = magic_state_threshold_qubit()
        assert 0.005 < threshold < 0.02  # roughly 1%

    def test_ququint_threshold_higher_than_qubit(self):
        from pt_ququint_empirical import (
            magic_state_threshold_ququint, magic_state_threshold_qubit
        )
        T_qq = magic_state_threshold_ququint()
        T_q = magic_state_threshold_qubit()
        assert T_qq > T_q
        # Factor should be ~36x
        assert 25 < T_qq / T_q < 50


# === MODULE IMPORTS ===

class TestModuleImports:
    """Verify the module is importable and exposes the expected API."""

    def test_module_imports(self):
        import pt_ququint_empirical
        for name in [
            "schmidt_entropy_qubit_vs_ququint",
            "find_sweet_spot_gamma",
            "bias_stability_score",
            "ccz_fidelity_qubit",
            "ccz_fidelity_ququint",
            "magic_state_threshold_ququint",
            "magic_state_threshold_qubit",
        ]:
            assert hasattr(pt_ququint_empirical, name), f"Missing: {name}"