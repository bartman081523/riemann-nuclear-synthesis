"""
Tests for pt_alpha_derivative.py — dα/d(log N) QPU cross-check.

H_dalpha: the sign of dalpha/d(log N) at N=127 (QPU-validatable)
matches the sign of dalpha/d(log N) at N=10^6 (statevector).

This test file verifies:
  - Local log-log slope calculation
  - Sign assignment (positive/negative/zero)
  - The H_dalpha evaluation distinguishes local-fluctuation from
    global-trend mismatch
  - The asymptotic sign is read from pt_asymptotic_N1e6.py results
"""
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLocalAlphaSlope:
    """Local log-log slope between (N_lo, S_lo) and (N_hi, S_hi)."""

    def test_local_slope_power_law_recovers_exponent(self):
        from pt_alpha_derivative import local_alpha_slope
        # S = N^0.3 -> slope = 0.3
        slope = local_alpha_slope(10, 100, 10 ** 0.3, 100 ** 0.3)
        assert abs(slope - 0.3) < 1e-9

    def test_local_slope_handles_zero_or_negative(self):
        from pt_alpha_derivative import local_alpha_slope
        assert math.isnan(local_alpha_slope(0, 10, 1, 2))
        assert math.isnan(local_alpha_slope(10, 100, 0, 1))
        assert math.isnan(local_alpha_slope(10, 100, 1, 0))


class TestSignAt:
    """Find the slope whose midpoint is closest to N_target and report its sign."""

    def test_sign_positive(self):
        from pt_alpha_derivative import sign_at
        slopes = [
            {"N_lo": 7, "N_hi": 15, "alpha_local": 0.5},
            {"N_lo": 15, "N_hi": 31, "alpha_local": 0.1},
        ]
        # N=10 -> midpoint closest is [7,15] with slope 0.5 -> positive
        assert sign_at(slopes, 10) == "positive"

    def test_sign_negative(self):
        from pt_alpha_derivative import sign_at
        slopes = [
            {"N_lo": 7, "N_hi": 15, "alpha_local": 0.5},
            {"N_lo": 15, "N_hi": 31, "alpha_local": -0.1},
        ]
        assert sign_at(slopes, 25) == "negative"

    def test_sign_zero(self):
        from pt_alpha_derivative import sign_at
        slopes = [
            {"N_lo": 7, "N_hi": 15, "alpha_local": 0.0},
        ]
        assert sign_at(slopes, 10) == "zero"

    def test_sign_empty_slopes(self):
        from pt_alpha_derivative import sign_at
        assert sign_at([], 10) is None


class TestEvaluateHdalpha:
    """H_dalpha evaluation: local-fluctuation vs global-trend mismatch."""

    def test_H_dalpha_distinguishes_local_from_global(self):
        from pt_alpha_derivative import evaluate_H_dalpha
        slopes = [
            {"N_lo": 63, "N_hi": 127, "alpha_local": 0.4},   # local positive
            {"N_lo": 127, "N_hi": 255, "alpha_local": 0.2},  # local positive
        ]
        result = evaluate_H_dalpha(slopes)
        assert result["H_dalpha_evaluable"] is True
        assert result["sign_at_N_127_local"] == "positive"
        assert result["sign_at_N_1e6_global"] == "negative"
        # H_dalpha FAILS (sign mismatch) — but the result is informative
        assert result["H_dalpha_holds"] is False
        assert "interpretation" in result

    def test_H_dalpha_holds_when_signs_match(self):
        from pt_alpha_derivative import evaluate_H_dalpha
        slopes = [
            {"N_lo": 63, "N_hi": 127, "alpha_local": -0.1},
            {"N_lo": 127, "N_hi": 255, "alpha_local": -0.2},
        ]
        result = evaluate_H_dalpha(slopes)
        assert result["H_dalpha_holds"] is True


class TestDalphaDLogNCurve:
    """Full dalpha/d(log N) curve computation."""

    def test_dalpha_curve_returns_data_and_slopes(self):
        from pt_alpha_derivative import dalpha_d_logN_curve
        data, slopes = dalpha_d_logN_curve([7, 15, 31, 63, 127])
        assert len(data) == 5
        # N+1 pairs of consecutive slopes from N data points
        assert len(slopes) == 4
        for d in data:
            assert "N" in d and "S_vN" in d and "log_N" in d
        for s in slopes:
            assert "N_lo" in s and "N_hi" in s and "alpha_local" in s
            assert math.isfinite(s["alpha_local"])


class TestModuleImports:
    """Verify the module exposes the expected API."""

    def test_module_imports(self):
        try:
            import pt_alpha_derivative
            for name in ["alpha_at_N", "local_alpha_slope", "dalpha_d_logN_curve",
                         "sign_at", "evaluate_H_dalpha", "N_SWEEP_DENSE",
                         "N_QPU_VALIDATABLE"]:
                assert hasattr(pt_alpha_derivative, name), \
                    f"Missing attribute: {name}"
        except ImportError:
            pytest.skip("pt_alpha_derivative nicht importierbar")