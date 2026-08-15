"""
Tests for pt_prereg_audit.py — Trusted-Statement / Untrusted-Solution pattern.

This implements a "comparator"-style audit (after anthropics/zeta-23-lean):
the preregistration file is the trusted CHALLENGE (what we predicted),
the result file is the untrusted SOLUTION (what we measured). The auditor
verifies that:

  (A) Statement coincidence: every predicted key appears in the result with
      the same value (no result-side rewriting of predictions).
  (B) Decision-rule consistency: the result file's `decision_rule` must
      agree with the prereg's (no post-hoc decision rule change).
  (C) Axiom whitelist: the audit only depends on standard structural checks
      (file existence, JSON validity, key set equality). It does NOT depend
      on the experimental code's internals.

This is the Python analogue of the Lean comparator pattern:
  - prereg.json ≡ Challenge.lean (sorry'd statements, trusted)
  - results.json ≡ Solution.lean (proved statements, untrusted)
  - pt_prereg_audit.main() ≡ comparator runner
"""
import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPreregChallengeStructure:
    """The CHALLENGE side: a prereg.json must declare exactly what is being
    claimed BEFORE any measurement is taken. Anti-Sharpshooter Protocol."""

    def test_prereg_requires_md5_field(self):
        """Prereg must be hash-pinned so its content cannot be retroactively
        edited without breaking the audit."""
        from pt_prereg_audit import audit_prereg_structure
        # An empty prereg must report missing md5
        bad = {"predictions": {"x": 1}}
        report = audit_prereg_structure(bad)
        assert not report["ok"]
        assert "md5" in report["missing_fields"]

    def test_prereg_requires_decision_rule(self):
        """Without an explicit decision_rule, an audit cannot classify the
        experiment as CONFIRMED / REFUTED / INCONCLUSIVE."""
        from pt_prereg_audit import audit_prereg_structure
        bad = {"md5": "deadbeef", "predictions": {"x": 1}}
        report = audit_prereg_structure(bad)
        assert not report["ok"]
        assert "decision_rule" in report["missing_fields"]

    def test_prereg_requires_predictions_section(self):
        """Prereg without `predictions` cannot be compared to results."""
        from pt_prereg_audit import audit_prereg_structure
        bad = {"md5": "deadbeef", "decision_rule": "x >= 0"}
        report = audit_prereg_structure(bad)
        assert not report["ok"]
        assert "predictions" in report["missing_fields"]

    def test_valid_prereg_passes(self):
        """A well-formed prereg passes the structural audit."""
        from pt_prereg_audit import audit_prereg_structure
        good = {
            "md5": "deadbeef",
            "decision_rule": "x >= 0",
            "predictions": {"x": 1.0, "y": 2.0},
        }
        report = audit_prereg_structure(good)
        assert report["ok"], report


class TestSolutionStatementCoincidence:
    """The SOLUTION side: a results.json must contain every prediction key
    from the prereg (statement coincidence). Comparator's first check."""

    def test_solution_missing_key_fails(self):
        """If the result omits a predicted key, the solution is incomplete."""
        from pt_prereg_audit import compare_statement_sets
        prereg = {"predictions": {"x": 1.0, "y": 2.0}}
        result = {"x": 1.0}  # y missing
        diff = compare_statement_sets(prereg, result)
        assert not diff["match"]
        assert "y" in diff["missing_in_result"]

    def test_solution_extra_keys_warn_not_fail(self):
        """Extra keys in result are allowed (new observables) but flagged.
        This is the dual of the zeta-23 comparator: extra structure is OK
        as long as the core statements coincide."""
        from pt_prereg_audit import compare_statement_sets
        prereg = {"predictions": {"x": 1.0}}
        result = {"x": 1.0, "z_extra": 99.0}
        diff = compare_statement_sets(prereg, result)
        assert diff["match"]
        assert "z_extra" in diff["extra_in_result"]

    def test_identical_keys_pass(self):
        """Coincident statement sets pass."""
        from pt_prereg_audit import compare_statement_sets
        diff = compare_statement_sets(
            {"predictions": {"x": 1.0, "y": 2.0}},
            {"x": 1.0, "y": 2.0},
        )
        assert diff["match"]


class TestDecisionRuleApplication:
    """Apply the prereg's decision_rule to the result's measured values.
    This is the Python analogue of `decide` for finite numeric checks —
    we evaluate the rule bit-by-bit, no interpretation."""

    def test_decision_rule_passes_when_inequality_holds(self):
        from pt_prereg_audit import evaluate_decision_rule
        # x >= 0 should pass when x = 1.0
        ok = evaluate_decision_rule("x >= 0", {"x": 1.0})
        assert ok

    def test_decision_rule_fails_when_inequality_violated(self):
        from pt_prereg_audit import evaluate_decision_rule
        ok = evaluate_decision_rule("x >= 0", {"x": -1.0})
        assert not ok

    def test_decision_rule_supports_multiple_keys(self):
        from pt_prereg_audit import evaluate_decision_rule
        # Both x >= 0 and y <= 5 must hold
        ok = evaluate_decision_rule("x >= 0 AND y <= 5", {"x": 1.0, "y": 3.0})
        assert ok
        ok2 = evaluate_decision_rule("x >= 0 AND y <= 5", {"x": 1.0, "y": 10.0})
        assert not ok2

    def test_decision_rule_handles_tolerance(self):
        """Real measurements have finite precision. Allow |measured - predicted| <= tol."""
        from pt_prereg_audit import evaluate_decision_rule
        # abs(x - 1.0) <= 0.05
        ok = evaluate_decision_rule("abs(x - 1.0) <= 0.05", {"x": 1.02})
        assert ok
        bad = evaluate_decision_rule("abs(x - 1.0) <= 0.05", {"x": 1.20})
        assert not bad


class TestFullAuditPipeline:
    """End-to-end: write temp prereg + result files, run main audit."""

    def test_full_pipeline_confirmed(self):
        from pt_prereg_audit import audit_run
        with tempfile.TemporaryDirectory() as tmpdir:
            prereg = {
                "md5": "test_md5_placeholder",
                "decision_rule": "abs(E_0 - 2.5) <= 0.1",
                "predictions": {"E_0": 2.5},
            }
            result = {"E_0": 2.52, "extra_field": "ok"}
            prereg_path = os.path.join(tmpdir, "prereg.json")
            result_path = os.path.join(tmpdir, "result.json")
            with open(prereg_path, "w") as f:
                json.dump(prereg, f)
            with open(result_path, "w") as f:
                json.dump(result, f)
            verdict = audit_run(prereg_path, result_path)
            assert verdict["status"] == "CONFIRMED"
            assert verdict["statement_coincidence"] is True
            assert verdict["decision_rule_holds"] is True

    def test_full_pipeline_refuted(self):
        from pt_prereg_audit import audit_run
        with tempfile.TemporaryDirectory() as tmpdir:
            prereg = {
                "md5": "test_md5_placeholder",
                "decision_rule": "abs(E_0 - 2.5) <= 0.01",
                "predictions": {"E_0": 2.5},
            }
            result = {"E_0": 3.7}  # Way off
            prereg_path = os.path.join(tmpdir, "prereg.json")
            result_path = os.path.join(tmpdir, "result.json")
            with open(prereg_path, "w") as f:
                json.dump(prereg, f)
            with open(result_path, "w") as f:
                json.dump(result, f)
            verdict = audit_run(prereg_path, result_path)
            assert verdict["status"] == "REFUTED"
            assert verdict["decision_rule_holds"] is False

    def test_full_pipeline_inconclusive_on_missing_statement(self):
        from pt_prereg_audit import audit_run
        with tempfile.TemporaryDirectory() as tmpdir:
            prereg = {
                "md5": "test_md5_placeholder",
                "decision_rule": "abs(E_0 - 2.5) <= 0.1",
                "predictions": {"E_0": 2.5, "extra_pred": 99.0},
            }
            result = {"E_0": 2.5}  # extra_pred missing
            prereg_path = os.path.join(tmpdir, "prereg.json")
            result_path = os.path.join(tmpdir, "result.json")
            with open(prereg_path, "w") as f:
                json.dump(prereg, f)
            with open(result_path, "w") as f:
                json.dump(result, f)
            verdict = audit_run(prereg_path, result_path)
            assert verdict["status"] == "INCONCLUSIVE"
            assert verdict["statement_coincidence"] is False


class TestAxiomWhitelist:
    """The audit only depends on a small whitelist of structural operations.
    Document this explicitly so future modifications don't accidentally
    introduce hidden dependencies on experimental internals."""

    def test_audit_imports_no_experimental_modules(self):
        """pt_prereg_audit must not import pt_vqe_vqd, pt_im_bias, or any
        other experimental module. This is the Python analogue of the Lean
        comparator's Mathlib-only-on-trusted-side rule."""
        import pt_prereg_audit as mod
        source = open(mod.__file__).read()
        forbidden = [
            "pt_vqe_vqd", "pt_im_bias", "pt_prime_state",
            "pt_qpu_", "pt_aer_stress", "pt_qec_bias",
        ]
        for f in forbidden:
            assert f not in source, \
                f"pt_prereg_audit must not import {f} (trusted-side rule)"
