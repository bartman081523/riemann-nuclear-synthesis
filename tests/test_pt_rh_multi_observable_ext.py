"""
Tests for pt_rh_multi_observable_ext.py — EXPERIMENT 023-EXT.

Freeze-commit part: prereg integrity (MD5 pin), frozen constants,
closed-form witness machinery, solver-path consistency, effective-
observables rule. Results-document tests live in the same file's
TestCommittedExtResults class (skipped if the results file is absent).
"""
import hashlib
import json
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREREG_PATH = os.path.join(REPO, "pt_rh_multi_observable_ext_prereg.json")
RESULTS_PATH = os.path.join(REPO, "pt_rh_multi_observable_ext_results.json")
V1_RESULTS_PATH = os.path.join(REPO, "pt_rh_multi_observable_results.json")


class TestPreregIntegrity:
    """The frozen prereg must exist, match the pinned MD5, and hold the
    v1 thresholds unchanged."""

    def test_prereg_file_exists(self):
        assert os.path.exists(PREREG_PATH)

    def test_prereg_md5_matches_pin(self):
        from pt_rh_multi_observable_ext import PREREG_MD5
        with open(PREREG_PATH, "rb") as f:
            raw = f.read()
        assert hashlib.md5(raw).hexdigest() == PREREG_MD5

    def test_load_frozen_prereg_verifies_md5(self):
        from pt_rh_multi_observable_ext import load_frozen_prereg
        prereg = load_frozen_prereg()
        assert prereg["prereg_id"] == "pt_rh_multi_observable_ext_v1"
        assert prereg["do_not_modify_after_lock"] is True

    def test_prereg_n_values_match_module_constants(self):
        from pt_rh_multi_observable_ext import (N_V1, N_EXT, load_frozen_prereg)
        prereg = load_frozen_prereg()
        assert prereg["n_values_v1"] == N_V1
        assert prereg["n_values_ext"] == N_EXT
        assert len(N_V1) + len(N_EXT) == 14

    def test_prereg_thresholds_unchanged_from_v1(self):
        from pt_rh_multi_observable_ext import load_frozen_prereg
        v1_path = os.path.join(REPO, "pt_rh_multi_observable_prereg.json")
        with open(v1_path) as f:
            v1 = json.load(f)
        prereg = load_frozen_prereg()
        assert prereg["thresholds_frozen_from_v1_unchanged"]["alpha_vN"].startswith("< 0.5")
        assert v1["rh_consistency_thresholds"]["cv_spread_A"]["rh_consistent_if"] == \
            "cv_spread in [0.05, 0.20] (stable empirical band)"
        assert "UNCHANGED" in prereg["thresholds_frozen_from_v1_unchanged"]["alpha_vN"] \
            or "v1 thresholds UNCHANGED" in prereg["scope"]["extension_leg"]

    def test_prereg_probe_disclosure_present(self):
        from pt_rh_multi_observable_ext import load_frozen_prereg
        prereg = load_frozen_prereg()
        disc = prereg["probe_disclosure"]
        assert "UNMEASURED at freeze time" in disc["what_the_probe_did_NOT_measure"]
        assert prereg["independence_audit"]["I3_nulls_diagnostic"]["status"] == \
            "DIAGNOSTIC, NOT verdict-tragend (probe already ran this leg, see probe_disclosure)"

    def test_prereg_reproduction_pin_value(self):
        from pt_rh_multi_observable_ext import load_frozen_prereg
        prereg = load_frozen_prereg()
        assert prereg["reproduction_pin"]["alpha_v1_8pt"] == 0.2658212701252552
        assert prereg["reproduction_pin"]["alpha_tolerance"] == 1e-12


class TestFrozenConstants:
    """Frozen thresholds and witness coefficients."""

    def test_threshold_constants(self):
        from pt_rh_multi_observable_ext import ALPHA_MAX, CV_BAND, RHO_AB_MAX
        assert ALPHA_MAX == 0.5
        assert CV_BAND == (0.05, 0.20)
        assert RHO_AB_MAX == 0.9

    def test_witness_coefficients(self):
        from pt_rh_multi_observable_ext import W1_COEF, W1_EXP, W2_COEF, W2_EXP
        assert (W1_COEF, W1_EXP) == (1.0, 0.4)
        assert (W2_COEF, W2_EXP) == (0.01, 0.55)

    def test_n_sweep_ascending_14(self):
        from pt_rh_multi_observable_ext import N_SWEEP
        assert len(N_SWEEP) == 14
        assert N_SWEEP == sorted(N_SWEEP)
        assert N_SWEEP[-1] == 65535


class TestSolverPaths:
    """cv_spread dense (v1-identical) vs tridiagonal (null legs)."""

    def test_cv_spread_dense_matches_v1_path_on_small_input(self):
        from pt_rh_multi_observable import hilbert_polya_proxy
        from pt_rh_multi_observable_ext import cv_spread_dense
        primes = [2, 3, 5, 7, 11]
        _, _, cv_v1 = hilbert_polya_proxy(primes)
        assert cv_spread_dense(primes) == cv_v1

    def test_cv_spread_dense_vs_tridiag_agree_small(self):
        from pt_prime_state import sieve_primes
        from pt_rh_multi_observable_ext import cv_spread_dense, cv_spread_tridiag
        primes = sieve_primes(127)
        assert abs(cv_spread_dense(primes) - cv_spread_tridiag(primes)) < 1e-9

    def test_cv_spread_tridiag_uniform_null_close_to_one_twelfth(self):
        # odd integers <= 32767: near-uniform spectrum, cv -> 1/12
        from pt_rh_multi_observable_ext import cv_spread_tridiag
        cv = cv_spread_tridiag(list(range(3, 32768, 2)))
        assert abs(cv - 1.0 / 12.0) < 1e-3

    def test_cv_spread_single_point_is_zero(self):
        from pt_rh_multi_observable_ext import cv_spread_dense, cv_spread_tridiag
        assert cv_spread_dense([2]) == 0.0
        assert cv_spread_tridiag([2]) == 0.0


class TestWitnesses:
    """I1: both verdict-divergence directions on the frozen 14-point grid."""

    def test_w1_diverges_a_true_b_false(self):
        from pt_rh_multi_observable_ext import W1_COEF, W1_EXP, witness_eval
        w1 = witness_eval(W1_COEF, W1_EXP)
        assert w1["alpha_within_tol"] is True
        assert abs(w1["alpha"] - 0.4) <= 1e-9
        assert w1["a_consistent"] is True
        assert w1["b_consistent"] is False
        assert w1["R_min"] > 1.0

    def test_w2_diverges_a_false_b_true(self):
        from pt_rh_multi_observable_ext import W2_COEF, W2_EXP, witness_eval
        w2 = witness_eval(W2_COEF, W2_EXP)
        assert w2["alpha_within_tol"] is True
        assert abs(w2["alpha"] - 0.55) <= 1e-9
        assert w2["a_consistent"] is False
        assert w2["b_consistent"] is True
        assert w2["R_max"] < 1.0

    def test_witnesses_use_full_frozen_grid(self):
        from pt_rh_multi_observable_ext import N_SWEEP, witness_eval
        w1 = witness_eval(1.0, 0.4)
        assert len(w1["R_values"]) == len(N_SWEEP)

    def test_witness_alpha_recovery_is_exact_for_power_law(self):
        from pt_rh_multi_observable_ext import ALPHA_TOL, witness_eval
        w = witness_eval(0.03, 0.7)
        assert w["alpha_dev_from_exponent"] <= ALPHA_TOL


class TestEffectiveObservables:
    """I2: frozen effective-independence rule."""

    def test_perfect_rank_dependence_collapses_b_onto_a(self):
        from pt_rh_multi_observable_ext import effective_observables
        eff_ab, eff_total = effective_observables(1.0)
        assert eff_ab == 1.0
        assert eff_total == 2.0

    def test_zero_correlation_gives_full_independence(self):
        from pt_rh_multi_observable_ext import effective_observables
        eff_ab, eff_total = effective_observables(0.0)
        assert eff_ab == 2.0
        assert eff_total == 3.0

    def test_moderate_correlation_matches_section_5_5_regime(self):
        # rho = 0.15 (§5.5 v1 estimate) -> effective_total = 2.85
        from pt_rh_multi_observable_ext import effective_observables
        _, eff_total = effective_observables(0.15)
        assert abs(eff_total - 2.85) < 1e-12

    def test_negative_rho_uses_absolute_value(self):
        from pt_rh_multi_observable_ext import effective_observables
        eff_ab, _ = effective_observables(-0.3)
        assert eff_ab == 1.7


class TestNullSequences:
    """I3 (diagnostic): deterministic null construction."""

    def test_null_a_is_odd_integers(self):
        from pt_rh_multi_observable_ext import null_sequences
        null_a, _ = null_sequences(31)
        assert null_a == [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31]

    def test_null_b_is_powers_of_two(self):
        from pt_rh_multi_observable_ext import null_sequences
        _, null_b = null_sequences(1000)
        assert null_b == [2, 4, 8, 16, 32, 64, 128, 256, 512]

    def test_null_b_at_65535_ends_at_32768(self):
        # int(log2(65535)) = 15 -> k = 1..15, last = 2^15 = 32768 (2^16 > N)
        from pt_rh_multi_observable_ext import null_sequences
        _, null_b = null_sequences(65535)
        assert null_b[-1] == 32768
        assert len(null_b) == 15


class TestModuleImports:
    def test_module_imports(self):
        import pt_rh_multi_observable_ext
        for name in ["load_frozen_prereg", "cv_spread_dense",
                     "cv_spread_tridiag", "witness_eval",
                     "effective_observables", "null_sequences",
                     "measure_all", "PREREG_MD5"]:
            assert hasattr(pt_rh_multi_observable_ext, name), \
                f"Missing attribute: {name}"


class TestCommittedExtResults:
    """Results-document tests (skipped until the measurement has run)."""

    @pytest.fixture(scope="class")
    def results(self):
        if not os.path.exists(RESULTS_PATH):
            pytest.skip("pt_rh_multi_observable_ext_results.json noch nicht committet")
        with open(RESULTS_PATH) as f:
            return json.load(f)

    def test_schema(self, results):
        for key in ["prereg_md5", "n_sweep", "rows", "alpha_combined",
                    "cv_spread_mean", "mocs_ext", "verdicts",
                    "v1_reproduction", "witnesses", "rho_ab",
                    "effective_total", "nulls", "claims",
                    "h_MOCS_EXT_rejected"]:
            assert key in results, f"Missing key: {key}"
        assert len(results["rows"]) == 14
        assert results["n_sweep"] == [7, 15, 31, 63, 127, 255, 511, 1023,
                                      2047, 4095, 8191, 16383, 32767, 65535]

    def test_prereg_md5_echo(self, results):
        from pt_rh_multi_observable_ext import PREREG_MD5
        assert results["prereg_md5"] == PREREG_MD5

    def test_verdicts_and_mocs_consistent(self, results):
        v = results["verdicts"]
        expected = sum([v["observable_a_alpha_rh_consistent"],
                        v["observable_b_R_rh_consistent"],
                        v["observable_c_cv_rh_consistent"]])
        assert results["mocs_ext"] == expected
        assert 0 <= results["mocs_ext"] <= 3

    def test_v1_reproduction_pins(self, results):
        repro = results["v1_reproduction"]
        assert repro["ok"] is True
        assert repro["alpha_dev"] <= 1e-12
        assert repro["max_S_dev"] <= 1e-12
        assert repro["max_R_dev"] <= 1e-12
        assert repro["max_cv_dev"] == 0.0
        assert repro["alpha_v1_recomputed"] == pytest.approx(
            0.2658212701252552, abs=1e-12)

    def test_witness_claims(self, results):
        w = results["witnesses"]
        assert w["w1"]["divergent"] is True
        assert w["w1"]["matches_expected"] is True
        assert w["w2"]["divergent"] is True
        assert w["w2"]["matches_expected"] is True
        assert results["claims"]["H_WITNESSES_hold"] is True

    def test_rho_ab_claim(self, results):
        assert results["claims"]["H_INDEP_holds"] is True
        assert abs(results["rho_ab"]) < 0.9
        assert results["effective_total"] >= 2.0

    def test_nulls_diagnostic_block(self, results):
        assert len(results["nulls"]) == 14
        for n in results["nulls"]:
            for key in ["cv_primes", "cv_null_a_odd", "cv_null_b_pow2",
                        "delta_a", "delta_b"]:
                assert key in n
            assert math.isfinite(n["cv_null_a_odd"])
            assert math.isfinite(n["cv_null_b_pow2"])

    def test_ext_rows_have_leg_labels(self, results):
        legs = {r["leg"] for r in results["rows"]}
        assert legs == {"v1", "ext"}
        ext = [r for r in results["rows"] if r["leg"] == "ext"]
        assert [r["N"] for r in ext] == [2047, 4095, 8191, 16383, 32767, 65535]