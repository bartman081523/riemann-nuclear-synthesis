"""Tests fuer primequant.theta_chain — Stepanov-Multiplizitaet und Weil-Theta-Kette."""

import pytest
import numpy as np

from primequant.theta_chain import (
    fourier_matrix,
    gauss_phase_matrix,
    controlled_add_matrix,
    trivial_state_vector,
    weil_theta_step_unitary,
    simulate_theta_chain,
    verify_stepanov_resonance,
)


def test_fourier_matrix_is_unitary():
    for q in (2, 3, 5, 7):
        F = fourier_matrix(q)
        assert np.allclose(F.conj().T @ F, np.eye(q), atol=1e-12)


def test_gauss_phase_matrix_is_unitary():
    for q in (3, 5, 7):
        D = gauss_phase_matrix(q, 1)
        assert np.allclose(D.conj().T @ D, np.eye(q), atol=1e-12)


def test_controlled_add_is_unitary_permutation():
    for q in (3, 5):
        C = controlled_add_matrix(q)
        dim2 = q * q
        assert np.allclose(C.conj().T @ C, np.eye(dim2), atol=1e-12)
        # Permutationsmatrix: genau eine 1 pro Zeile und Spalte
        assert np.all(np.sum(C, axis=0) == 1.0)
        assert np.all(np.sum(C, axis=1) == 1.0)


def test_step_operator_is_unitary():
    for q in (3, 5, 7):
        W = weil_theta_step_unitary(q)
        dim2 = q * q
        assert np.allclose(W.conj().T @ W, np.eye(dim2), atol=1e-12)


def test_q5_stepanov_resonance_peak_and_purity():
    """Fuer q=5: L=2 = floor(sqrt(5)) erzeugt das globale Maximum R=0.4272."""
    res = verify_stepanov_resonance(q=5, p_noise=0.0)
    assert res["verdict"] == "CONFIRMED_STEPANOV_RESONANCE"
    assert res["expected_L"] == 2
    assert res["actual_peak_L"] == 2
    
    sim = res["history"]
    assert sim[0]["step"] == 0
    assert pytest.approx(sim[0]["R"], abs=1e-4) == 0.2500
    assert pytest.approx(sim[0]["purity"], abs=1e-4) == 1.0000
    
    # Peak bei L=2
    r2 = sim[2]
    assert pytest.approx(r2["R"], abs=1e-4) == 0.4272
    assert pytest.approx(r2["purity"], abs=1e-4) == 0.4520
    assert r2["gap_over_baseline"] > 0.17  # +70.9% ueber Baseline 0.25


def test_q5_noise_robustness():
    """Unter 5% depolarisierendem Rauschen bleibt die Resonanz deutlich ueber Floor."""
    res_noisy = verify_stepanov_resonance(q=5, p_noise=0.05)
    assert res_noisy["actual_peak_L"] == 2
    r2 = res_noisy["stepanov_record"]
    assert r2["R"] >= 0.4000
    assert r2["gap_over_baseline"] > 0.15  # Weit ueber der Falsifikationsschwelle 0.015


def test_q7_stepanov_resonance_peak():
    """Fuer q=7: L=2 = floor(sqrt(7)) erzeugt das Maximum R=0.2312 (Baseline 0.1667)."""
    res = verify_stepanov_resonance(q=7, p_noise=0.0)
    assert res["expected_L"] == 2
    assert res["actual_peak_L"] == 2
    r2 = res["stepanov_record"]
    assert pytest.approx(r2["R"], abs=1e-4) == 0.2312
    assert r2["gap_over_baseline"] > 0.06
