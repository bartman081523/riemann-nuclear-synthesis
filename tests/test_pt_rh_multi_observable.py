"""
Tests for pt_rh_multi_observable.py — Multi-Observable RH Convergence.

The Multi-Observable Convergence Score (MOCS) measures whether three
independent observables (Schmidt-entropy alpha, Latorre-Ratio R(N),
Hilbert-Pólya proxy det(A)) are jointly RH-consistent.

These tests verify:
  - All three observables return numerical values
  - The RH-consistency evaluation is deterministic
  - MOCS is in {0, 1, 2, 3}
  - The pre-registered observable thresholds are respected
"""
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAlphaVNObservable:
    """Observable (a): Schmidt-entropy scaling alpha_vN."""

    def test_alpha_vN_scaling_returns_finite(self):
        from pt_rh_multi_observable import alpha_vN_scaling
        N_values = [7, 15, 31, 63, 127]
        S_values = [0.5, 0.8, 1.0, 1.2, 1.4]
        alpha, log_const = alpha_vN_scaling(N_values, S_values)
        assert math.isfinite(alpha)
        assert math.isfinite(log_const)

    def test_alpha_vN_scaling_uniform_gives_log_pi_over_log_N(self):
        from pt_rh_multi_observable import alpha_vN_scaling
        # Synthetic linear log-log: S = N^0.3 -> alpha = 0.3
        N = np.array([7, 15, 31, 63, 127], dtype=float)
        S = N ** 0.3
        alpha, _ = alpha_vN_scaling(N.tolist(), S.tolist())
        assert abs(alpha - 0.3) < 1e-9

    def test_evaluate_alpha_threshold_0_5(self):
        from pt_rh_multi_observable import evaluate_alpha
        assert evaluate_alpha(0.1) is True
        assert evaluate_alpha(0.3) is True
        assert evaluate_alpha(0.499) is True
        assert evaluate_alpha(0.5) is False
        assert evaluate_alpha(0.7) is False


class TestLatorreRatioObservable:
    """Observable (b): Latorre-ratio R(N) = S_vN / log pi(N)."""

    def test_latorre_ratio_basic(self):
        from pt_rh_multi_observable import latorre_ratio
        # pi(N)=4 -> log 4 ≈ 1.386
        R = latorre_ratio(0.5, 4)
        assert abs(R - 0.5 / math.log(4)) < 1e-9

    def test_latorre_ratio_pi_one_is_inf(self):
        from pt_rh_multi_observable import latorre_ratio
        R = latorre_ratio(0.5, 1)
        assert R == float("inf")

    def test_latorre_ratio_R_less_than_one_is_rh_consistent(self):
        from pt_rh_multi_observable import latorre_ratio
        # If S_vN << log pi(N), R << 1: Sub-RH regime
        R = latorre_ratio(0.4, 100)  # log 100 ≈ 4.6
        assert R < 1.0

    def test_evaluate_latorre_ratio_threshold(self):
        from pt_rh_multi_observable import evaluate_latorre_ratio
        assert evaluate_latorre_ratio([0.3, 0.4, 0.5]) is True
        assert evaluate_latorre_ratio([0.5, 1.5]) is False
        assert evaluate_latorre_ratio([1.0]) is False


class TestHilbertPolyaObservable:
    """Observable (c): Hilbert-Pólya proxy via det of Jacobi matrix A."""

    def test_jacobi_matrix_is_symmetric(self):
        from pt_rh_multi_observable import jacobi_matrix_for_primes
        primes = [2, 3, 5, 7, 11]
        A = jacobi_matrix_for_primes(primes)
        assert A.shape == (5, 5)
        np.testing.assert_array_equal(A, A.T)

    def test_jacobi_matrix_diagonal_is_primes(self):
        from pt_rh_multi_observable import jacobi_matrix_for_primes
        primes = [2, 3, 5, 7, 11]
        A = jacobi_matrix_for_primes(primes)
        np.testing.assert_array_equal(np.diag(A), primes)

    def test_hilbert_polya_proxy_returns_real_for_small_input(self):
        from pt_rh_multi_observable import hilbert_polya_proxy
        primes = [2, 3, 5, 7, 11]
        abs_det, imag_det = hilbert_polya_proxy(primes)
        assert abs_det > 0
        assert abs(imag_det) < 1e-9

    def test_hilbert_polya_proxy_handles_single_prime(self):
        from pt_rh_multi_observable import hilbert_polya_proxy
        abs_det, imag_det = hilbert_polya_proxy([2])
        assert abs_det == 2.0
        assert imag_det == 0.0

    def test_evaluate_hilbert_polya_threshold(self):
        from pt_rh_multi_observable import evaluate_hilbert_polya
        assert evaluate_hilbert_polya(1.0, 0.0) is True
        assert evaluate_hilbert_polya(1e-10, 0.0) is False  # below tol
        assert evaluate_hilbert_polya(1.0, 0.5) is False   # imag part too large


class TestMOCSScore:
    """Multi-Observable Convergence Score (MOCS)."""

    def test_mocs_all_consistent(self):
        from pt_rh_multi_observable import mocs
        score = mocs(0.3, [0.4, 0.5], 1.0, 0.0)
        assert score == 3

    def test_mocs_only_alpha(self):
        from pt_rh_multi_observable import mocs
        # alpha good, R bad (>=1), det bad
        score = mocs(0.3, [1.5, 0.5], 0.0, 0.0)
        assert score == 1

    def test_mocs_none_consistent(self):
        from pt_rh_multi_observable import mocs
        score = mocs(0.7, [1.5, 2.0], 0.0, 1.0)
        assert score == 0

    def test_mocs_in_valid_range(self):
        from pt_rh_multi_observable import mocs
        for alpha in [0.1, 0.3, 0.5, 0.9]:
            for R in [[0.1, 0.2], [0.5, 1.5], [1.0, 1.1]]:
                for d, im in [(1.0, 0.0), (0.0, 0.0), (1.0, 0.5)]:
                    s = mocs(alpha, R, d, im)
                    assert 0 <= s <= 3


class TestMeasureAll:
    """Full measurement loop on the prime-state family."""

    def test_measure_all_returns_valid_structure(self):
        from pt_rh_multi_observable import measure_all
        result = measure_all()
        assert "N_sweep" in result
        assert "rows" in result
        assert "alpha_vN" in result
        assert "mocs" in result
        assert "verdicts" in result
        assert "h_MOCS_rejected" in result
        assert len(result["rows"]) == 8
        assert 0 <= result["mocs"] <= 3
        assert isinstance(result["h_MOCS_rejected"], bool)

    def test_measure_all_mocs_matches_verdicts(self):
        from pt_rh_multi_observable import measure_all
        result = measure_all()
        v = result["verdicts"]
        expected_score = sum([
            v["observable_a_alpha_rh_consistent"],
            v["observable_b_R_rh_consistent"],
            v["observable_c_det_rh_consistent"],
        ])
        assert result["mocs"] == expected_score

    def test_measure_all_alpha_positive(self):
        from pt_rh_multi_observable import measure_all
        result = measure_all()
        assert result["alpha_vN"] > 0
        # Sub-RH regime: alpha < 0.5
        assert result["alpha_vN"] < 0.5


class TestModuleImports:
    """Verify the module is importable and exposes the expected API."""

    def test_module_imports(self):
        try:
            import pt_rh_multi_observable
            for name in ["alpha_vN_scaling", "latorre_ratio",
                         "hilbert_polya_proxy", "mocs", "measure_all",
                         "N_SWEEP"]:
                assert hasattr(pt_rh_multi_observable, name), \
                    f"Missing attribute: {name}"
        except ImportError:
            pytest.skip("pt_rh_multi_observable nicht importierbar")


class TestPreregIntegrity:
    """Verify the preregistration file is intact and well-formed."""

    def test_prereg_file_exists(self):
        import os
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "pt_rh_multi_observable_prereg.json",
        )
        assert os.path.exists(path), f"Prereg not found at {path}"

    def test_prereg_contains_required_keys(self):
        import json
        import os
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "pt_rh_multi_observable_prereg.json",
        )
        with open(path) as f:
            prereg = json.load(f)
        for key in ["prereg_id", "scope", "n_values", "rh_consistency_thresholds",
                    "mocs_definition", "falsifiable_statement"]:
            assert key in prereg, f"Missing prereg key: {key}"

    def test_prereg_locked_flag_set(self):
        import json
        import os
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "pt_rh_multi_observable_prereg.json",
        )
        with open(path) as f:
            prereg = json.load(f)
        assert prereg.get("do_not_modify_after_lock") is True