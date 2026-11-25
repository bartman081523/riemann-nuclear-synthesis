# -*- coding: utf-8 -*-
"""Test suite for Lean 4 multi-kernel verification."""

import pytest
from verify_lean4_multi_kernel import (
    verify_kernel_lean4_trust0,
    verify_kernel_comparator_theorems,
    verify_kernel_exact_metaplectic,
)


def test_kernel_1_lean4_trust0():
    res = verify_kernel_lean4_trust0()
    assert res["status"] == "PASS"
    assert res["has_sorry"] is False
    assert res["theorems_checked"] >= 6
    assert res["returncode"] == 0


def test_kernel_2_comparator_theorems():
    res = verify_kernel_comparator_theorems()
    assert res["status"] == "PASS"
    assert res["matched_in_solution"] == res["headline_theorems_total"]
    assert res["headline_theorems_total"] >= 12


def test_kernel_3_exact_metaplectic_svd():
    res = verify_kernel_exact_metaplectic()
    assert res["status"] == "PASS"
    assert len(res["primes_evaluated"]) >= 5
    for q_str, d in res["details"].items():
        assert d["rank"] == 2
        assert d["tail_max"] < 1e-10
        assert d["projector_idempotent"] is True
        assert d["fluctuation_annihilated"] is True
