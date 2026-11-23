"""Tests fuer Frobenius-Eigenwinkel, Unfolding und spektrale Paarkorrelation."""

from __future__ import annotations
import math
import pytest

from primequant.weil import (
    artin_schreier_frobenius_angles,
    unfold_frobenius_angles,
    spectral_pair_correlation,
    montgomery_odlyzko_gue,
)


def test_artin_schreier_frobenius_angles_properties():
    q = 5
    angles = artin_schreier_frobenius_angles(q, degree=3)
    assert len(angles) == q
    # Alle Winkel in [0, pi]
    for th in angles:
        assert 0.0 <= th <= math.pi
    # Monoton sortiert
    for i in range(len(angles) - 1):
        assert angles[i] <= angles[i + 1]


def test_unfolding_preserves_count_and_order():
    q = 17
    angles = artin_schreier_frobenius_angles(q, degree=3)
    unfolded = unfold_frobenius_angles(angles)
    assert len(unfolded) == len(angles)
    # Monotonie
    for i in range(len(unfolded) - 1):
        assert unfolded[i] <= unfolded[i + 1]
    # Begrenzung auf [0, N]
    assert unfolded[0] >= 0.0
    assert unfolded[-1] <= float(q)


def test_montgomery_odlyzko_gue_limits():
    # R_2(0) = 0
    assert abs(montgomery_odlyzko_gue(0.0)) < 1e-10
    # Asymptotik fuer grosses s -> 1
    assert abs(montgomery_odlyzko_gue(10.0) - 1.0) < 0.01
    assert abs(montgomery_odlyzko_gue(100.0) - 1.0) < 1e-4


def test_spectral_pair_correlation_bins():
    q = 31
    angles = artin_schreier_frobenius_angles(q, degree=3)
    unfolded = unfold_frobenius_angles(angles)
    centers, r2 = spectral_pair_correlation(unfolded, s_max=2.0, n_bins=10)
    assert len(centers) == 10
    assert len(r2) == 10
    for val in r2:
        assert val >= 0.0
