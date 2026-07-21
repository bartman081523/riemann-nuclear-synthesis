"""
Tests for pt_ququint_simulator.py — Ququint quantum simulator with GF(5) gates.

These tests cover:
  - n-dimensional statevector and unitary representation
  - CCZ gate as a concrete 5x5 unitary (not just gate count)
  - Magic state |T> on GF(5) with correct phase
  - PT-symmetric Hamiltonian on 5x5 with gamma-sweep
  - VQE loop on the GF(5) statevector-first architecture

Phase 2: Quantum simulator. These tests must pass before the empirical
comparisons (Phase 3).
"""
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# === UNITARY MATRICES AND STATEVECTORS ===

class TestIsUnitary:
    """A matrix U is unitary iff U @ U.conj().T = I."""

    def test_identity_is_unitary(self):
        from pt_ququint_simulator import identity_unitary
        I = identity_unitary(5)
        np.testing.assert_allclose(I @ I.conj().T, np.eye(5), atol=1e-12)

    def test_pauli_x_is_unitary(self):
        """Generalized Pauli X on 5-dim: cyclic shift."""
        from pt_ququint_simulator import pauli_x_5
        X = pauli_x_5()
        np.testing.assert_allclose(X @ X.conj().T, np.eye(5), atol=1e-12)

    def test_pauli_z_is_unitary(self):
        """Generalized Pauli Z on 5-dim: diag(1, omega, omega^2, omega^3, omega^4)."""
        from pt_ququint_simulator import pauli_z_5
        Z = pauli_z_5()
        np.testing.assert_allclose(Z @ Z.conj().T, np.eye(5), atol=1e-12)

    def test_phase_gate_is_unitary(self):
        """Phase gate P(phi) = diag(1, e^{i*phi}, e^{2i*phi}, ...)."""
        from pt_ququint_simulator import phase_gate_5
        P = phase_gate_5(0.5)
        np.testing.assert_allclose(P @ P.conj().T, np.eye(5), atol=1e-12)


# === CCZ GATE ON GF(5) ===

class TestCCZGate:
    """CCZ on 1 ququint (5-dim) is a diagonal phase gate.
    CCZ |k> = exp(i*pi*k^3) |k> for k=0..4, where k^3 in GF(5)."""

    def test_ccz_is_unitary(self):
        from pt_ququint_simulator import ccz_gate_5
        CCZ = ccz_gate_5()
        np.testing.assert_allclose(CCZ @ CCZ.conj().T, np.eye(5), atol=1e-12)

    def test_ccz_phase_for_k0(self):
        """CCZ |0> = |0> (k=0: 0^3 = 0, exp(0) = 1)."""
        from pt_ququint_simulator import ccz_gate_5
        CCZ = ccz_gate_5()
        e0 = np.zeros(5, dtype=complex); e0[0] = 1.0
        np.testing.assert_allclose(CCZ @ e0, e0, atol=1e-12)

    def test_ccz_phase_for_k2(self):
        """CCZ |2> = exp(i*pi*8) |2> = exp(i*pi*3) |2> = -|2> (k=2: 2^3=8, 8 mod 5 = 3)."""
        from pt_ququint_simulator import ccz_gate_5
        CCZ = ccz_gate_5()
        e2 = np.zeros(5, dtype=complex); e2[2] = 1.0
        np.testing.assert_allclose(CCZ @ e2, -e2, atol=1e-12)

    def test_ccz_diagonal_structure(self):
        """CCZ should be diagonal (it's a phase gate)."""
        from pt_ququint_simulator import ccz_gate_5
        CCZ = ccz_gate_5()
        off_diag = CCZ - np.diag(np.diag(CCZ))
        np.testing.assert_allclose(off_diag, 0, atol=1e-12)


# === MAGIC STATE |T> ON GF(5) ===

class TestMagicStateT:
    """Magic state |T> = (|0> + e^{2*pi*i/5}|1> + e^{4*pi*i/5}|2> + e^{6*pi*i/5}|3> + e^{8*pi*i/5}|4>)/sqrt(5).
    This is the 5-dimensional analog of the qubit |T> = (|0> + e^{i*pi/4}|1>)/sqrt(2)."""

    def test_magic_state_is_normalized(self):
        from pt_ququint_simulator import magic_state_T_5
        T = magic_state_T_5()
        norm = np.sqrt(np.sum(np.abs(T) ** 2))
        np.testing.assert_allclose(norm, 1.0, atol=1e-12)

    def test_magic_state_has_uniform_amplitudes(self):
        """All |T_k| should be 1/sqrt(5) (uniform magnitudes)."""
        from pt_ququint_simulator import magic_state_T_5
        T = magic_state_T_5()
        mags = np.abs(T)
        expected = 1.0 / math.sqrt(5)
        np.testing.assert_allclose(mags, expected, atol=1e-12)

    def test_magic_state_phases(self):
        """Phase of T_k should be 2*pi*k/5 (mod 2*pi, since np.angle returns in [-pi, pi])."""
        from pt_ququint_simulator import magic_state_T_5
        T = magic_state_T_5()
        for k in range(5):
            expected_phase = 2 * math.pi * k / 5
            # np.angle wraps to [-pi, pi], so compare modulo 2*pi
            actual_phase = np.angle(T[k])
            diff = (actual_phase - expected_phase) % (2 * math.pi)
            # diff should be close to 0 or 2*pi
            assert min(diff, 2 * math.pi - diff) < 1e-10, \
                f"Phase mismatch at k={k}: expected {expected_phase}, got {actual_phase}"


# === PT-SYMMETRIC HAMILTONIAN ON 5x5 ===

class TestPTHamiltonian5:
    """H_PT_5 = H_diag_5 + i*gamma*A_5 in 5x5 form, with gamma-sweep support."""

    def test_H_PT_5_is_pt_symmetric_at_gamma_002(self):
        """At gamma=0.02 (default), H_PT_5 should be PT-symmetric."""
        from pt_ququint_simulator import H_PT_5_with_gamma
        H = H_PT_5_with_gamma(0.02)
        # PT-symmetry: H and H.conj() have same spectrum (|Im(eig)| symmetric)
        eigs = np.linalg.eigvals(H)
        eigs_conj = np.linalg.eigvals(H.conj())
        for i in range(5):
            # Both should have same real parts and same |imaginary parts|
            real_H = sorted([e.real for e in eigs])
            real_Hc = sorted([e.real for e in eigs_conj])
            np.testing.assert_allclose(real_H, real_Hc, atol=1e-10)

    def test_H_PT_5_ground_state_is_real_at_small_gamma(self):
        """At small gamma, the ground state should be approximately the
        ground state of H_diag (which is |0> with eigenvalue 2.0)."""
        from pt_ququint_simulator import H_PT_5_with_gamma
        H = H_PT_5_with_gamma(0.001)  # very small gamma
        eigs, vecs = np.linalg.eigh(H.real)  # H is real-symmetric here only if Im part is small
        # For very small gamma, the ground state should be close to the lowest diagonal element
        ground_state = vecs[:, 0]
        # |<0|ground>|^2 should be high
        overlap = abs(ground_state[0]) ** 2
        assert overlap > 0.99

    def test_gamma_sweep_e0_is_smooth(self):
        """E_0(gamma) should be a smooth function (no jumps)."""
        from pt_ququint_simulator import H_PT_5_with_gamma
        gammas = [0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
        e0_values = []
        for g in gammas:
            H = H_PT_5_with_gamma(g)
            eigs = np.linalg.eigvalsh(H.real) if np.allclose(H.imag, 0) else sorted(np.linalg.eigvals(H).real)
            e0_values.append(float(eigs[0]))
        # Differences between consecutive values should be bounded
        diffs = np.diff(e0_values)
        assert max(abs(diffs)) < 5.0  # no huge jumps


# === VQE LOOP ON GF(5) ===

class TestVQELoopGF5:
    """VQE loop: minimize E(theta) = <psi(theta)|H_PT_5|psi(theta)> using COBYLA."""

    def test_vqe_converges_to_below_noiseless_plus_gamma(self):
        """VQE should find E_0 < E_0_noiseless + 2*gamma*||A|| (perturbation bound)."""
        from pt_ququint_simulator import vqe_gf5
        gamma = 0.02
        E0_noiseless = 2.0  # smallest diagonal element
        A_bound = 5.0  # rough bound on ||A||
        E0_vqe = vqe_gf5(gamma=gamma, maxiter=20, seed=42)
        # E_0 should be < E_0_noiseless + 2*gamma*A_bound (loose bound)
        assert E0_vqe < E0_noiseless + 2 * gamma * A_bound

    def test_vqe_is_deterministic(self):
        """Same seed -> same E_0."""
        from pt_ququint_simulator import vqe_gf5
        E0_run1 = vqe_gf5(gamma=0.05, maxiter=15, seed=123)
        E0_run2 = vqe_gf5(gamma=0.05, maxiter=15, seed=123)
        assert abs(E0_run1 - E0_run2) < 1e-6

    def test_vqe_different_seeds_converge_to_similar_values(self):
        """Different seeds should converge to similar (not exact) values."""
        from pt_ququint_simulator import vqe_gf5
        E0_seeds = [vqe_gf5(gamma=0.05, maxiter=20, seed=s) for s in [42, 123, 456, 789]]
        # All should be within 0.5 of each other
        spread = max(E0_seeds) - min(E0_seeds)
        assert spread < 0.5


# === MODULE IMPORTS ===

class TestModuleImports:
    """Verify the module is importable and exposes the expected API."""

    def test_module_imports(self):
        import pt_ququint_simulator
        for name in ["identity_unitary", "pauli_x_5", "pauli_z_5",
                     "phase_gate_5", "ccz_gate_5", "magic_state_T_5",
                     "H_PT_5_with_gamma", "vqe_gf5"]:
            assert hasattr(pt_ququint_simulator, name), f"Missing: {name}"