"""
Tests for pt_ququint_ibmq.py — EXPERIMENT 030, Phase 1 (simulator-only).

Ququint on IBMQ: 3-qubit emulation of the GF(5) architecture. IBMQ exposes
only 2 levels per qubit, so a ququint is encoded into a 3-qubit register
(8 dim, 5 logical states 000..100, 3 leakage states 101/110/111).

Covered:
  - encoding and leakage structure
  - encoded X5/Z5/DFT5 operators, verified against the kernel-audited
    pt_ququint_simulator.pauli_x_5 / pauli_z_5 (Pattern C, §Z.10)
  - Weyl relation ZX = omega XZ exact ON THE LOGICAL SUBSPACE, and its
    documented structural FAILURE on leakage states (order-5 phase orbit
    cannot extend to 8 dims: leakage orbits under the encoded X are
    fixed points, so no faithful 8-dim GF(5) Weyl algebra exists)
  - encoded two-ququint states as embeddings of the §Z.11 states (64 dim)
  - measurement simulation: computational-basis and DFT-basis histograms
  - the population confound at the encoded level (§Z.11 lesson preserved)
  - the DFT-diagonal-weight coherence witness V with separable bound 1/5:
    conditional on maximally-correlated computational support (the
    preregistered confound pair |phi> vs rho_sep), V > 1/5 witnesses
    entanglement from ONE extra measurement setting
  - vectorized multinomial shot sampling + bootstrap SE, leakage rejection
  - Phase-1 guard: numpy only, no qiskit (transpilation is Phase 2)
"""
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ENC_DIM = 8
TWO_DIM = 64
LOGICAL = [(a, b) for a in range(5) for b in range(5)]  # 25 logical pairs


def logical_index(a, b):
    return a * ENC_DIM + b


def leakage_state_two_ququint():
    # pure state with half weight on a leakage position (ququint A in |5>)
    psi = np.zeros(TWO_DIM, dtype=complex)
    psi[logical_index(0, 0)] = 1.0 / math.sqrt(2.0)
    psi[logical_index(5, 0)] = 1.0 / math.sqrt(2.0)
    return psi


# === ENCODING ===


class TestEncoding:
    def test_encode_maps_gf5_states_to_binary_basis(self):
        import pt_ququint_ibmq as qi
        for k in range(5):
            v = qi.encode_ququint(k)
            assert v.shape == (ENC_DIM,)
            assert v[k] == pytest.approx(1.0)
            assert np.linalg.norm(v) == pytest.approx(1.0)

    def test_encode_rejects_non_logical_k(self):
        import pt_ququint_ibmq as qi
        with pytest.raises(ValueError):
            qi.encode_ququint(5)
        with pytest.raises(ValueError):
            qi.encode_ququint(-1)

    def test_leakage_structure(self):
        import pt_ququint_ibmq as qi
        assert qi.ENC_DIM == 8
        assert qi.LEAKAGE_INDICES == (5, 6, 7)
        assert qi.WITNESS_BOUND == pytest.approx(0.2)


# === ENCODED OPERATORS (verified against the kernel-audited layer) ===


class TestEncodedOperators:
    def test_x5_encoded_restriction_matches_kernel_x(self):
        import pt_ququint_ibmq as qi
        from pt_ququint_simulator import pauli_x_5
        X8 = qi.x5_encoded()
        assert np.array_equal(X8[:5, :5], pauli_x_5())

    def test_z5_encoded_restriction_matches_kernel_z(self):
        import pt_ququint_ibmq as qi
        from pt_ququint_simulator import pauli_z_5
        Z8 = qi.z5_encoded()
        assert np.allclose(Z8[:5, :5], pauli_z_5(), atol=1e-15)

    def test_x5_pow5_identity_on_full_eight_dim(self):
        import pt_ququint_ibmq as qi
        X5 = np.linalg.matrix_power(qi.x5_encoded(), 5)
        assert np.array_equal(X5, np.eye(ENC_DIM))

    def test_z5_pow5_identity_on_full_eight_dim(self):
        import pt_ququint_ibmq as qi
        Z5 = np.linalg.matrix_power(qi.z5_encoded(), 5)
        assert np.allclose(Z5, np.eye(ENC_DIM), atol=1e-12)

    def test_weyl_relation_exact_on_logical_subspace(self):
        # Z X = omega X Z must hold exactly on the code space — this is the
        # kernel-verified GF(5) relation (§Z.10) carried into the encoding.
        import pt_ququint_ibmq as qi
        omega = np.exp(2j * np.pi / 5)
        res = qi.z5_encoded() @ qi.x5_encoded() - omega * qi.x5_encoded() @ qi.z5_encoded()
        assert np.allclose(res[:5, :5], 0.0, atol=1e-12)

    def test_weyl_relation_breaks_on_leakage_states(self):
        # Structural finding, not a bug: with leakage states fixed by the
        # encoded X and phase 1 under the encoded Z, (Z X)|5> = |5> but
        # (omega X Z)|5> = omega|5>. The GF(5) Weyl algebra is faithful
        # ONLY on the 5-dim code space — leakage is algebra-breaking.
        import pt_ququint_ibmq as qi
        omega = np.exp(2j * np.pi / 5)
        res = qi.z5_encoded() @ qi.x5_encoded() - omega * qi.x5_encoded() @ qi.z5_encoded()
        assert np.linalg.norm(res[5:, 5:]) > 1.0

    def test_dft5_encoded_unitary_and_block_structure(self):
        import pt_ququint_ibmq as qi
        F = qi.dft5_encoded()
        assert np.allclose(F.conj().T @ F, np.eye(ENC_DIM), atol=1e-12)
        omega = np.exp(2j * np.pi / 5)
        expected_block = np.array(
            [[omega ** (j * k) / math.sqrt(5.0) for k in range(5)] for j in range(5)]
        )
        assert np.allclose(F[:5, :5], expected_block, atol=1e-15)
        assert np.allclose(F[5:, 5:], np.eye(3), atol=0.0)
        assert np.allclose(F[:5, 5:], 0.0, atol=0.0)
        assert np.allclose(F[5:, :5], 0.0, atol=0.0)


# === ENCODED TWO-QUQUINT STATES (embeddings of §Z.11) ===


class TestEncodedStates:
    def test_phi_max_encoded_support_and_norm(self):
        import pt_ququint_ibmq as qi
        phi = qi.phi_max_encoded()
        assert phi.shape == (TWO_DIM,)
        assert np.linalg.norm(phi) == pytest.approx(1.0)
        for a in range(5):
            assert phi[logical_index(a, a)] == pytest.approx(1.0 / math.sqrt(5.0))
        off = [i for i in range(TWO_DIM) if i not in [logical_index(a, a) for a in range(5)]]
        assert np.allclose(np.abs(phi[off]), 0.0, atol=1e-15)

    def test_weyl_bell_encoded_support(self):
        # (|0,0> + |1,4>)/sqrt(2) at 64-dim indices 0 and 1*8+4 = 12
        import pt_ququint_ibmq as qi
        psi = qi.weyl_bell_encoded()
        support = {int(i) for i in np.nonzero(np.abs(psi) > 1e-12)[0]}
        assert support == {logical_index(0, 0), logical_index(1, 4)}

    def test_separable_dephased_encoded_diagonal(self):
        import pt_ququint_ibmq as qi
        rho = qi.separable_dephased_encoded()
        assert rho.shape == (TWO_DIM, TWO_DIM)
        assert np.trace(rho) == pytest.approx(1.0)
        for a in range(5):
            assert rho[logical_index(a, a), logical_index(a, a)] == pytest.approx(0.2)
        off = [i for i in range(TWO_DIM) if i not in [logical_index(a, a) for a in range(5)]]
        assert np.allclose(np.abs(np.diag(rho)[off]), 0.0)

    def test_embed_logical_roundtrip_matches_phi(self):
        # the 64-dim state must be exactly the embedding of the §Z.11 state
        import pt_ququint_entanglement as qe
        import pt_ququint_ibmq as qi
        assert np.allclose(qi.embed_logical_state(qe.max_entangled_phi()),
                           qi.phi_max_encoded(), atol=1e-15)
        assert np.allclose(qi.embed_logical_state(qe.separable_dephased_phi()),
                           qi.separable_dephased_encoded(), atol=1e-15)

    def test_product_encoded(self):
        import pt_ququint_ibmq as qi
        psi = qi.product_encoded(2, 3)
        assert psi[logical_index(2, 3)] == pytest.approx(1.0)
        assert np.linalg.norm(psi) == pytest.approx(1.0)


# === MEASUREMENT SIMULATION (what the QPU would produce) ===


class TestMeasurementHistograms:
    def test_phi_computational_histogram(self):
        import pt_ququint_ibmq as qi
        p = qi.histogram_computational(qi.phi_max_encoded())
        assert p.shape == (TWO_DIM,)
        for a in range(5):
            assert p[logical_index(a, a)] == pytest.approx(0.2)
        rest = [i for i in range(TWO_DIM) if i not in [logical_index(a, a) for a in range(5)]]
        assert np.allclose(p[rest], 0.0, atol=1e-15)

    def test_phi_dft_histogram_is_dft_invariant(self):
        # (F (x) F†)|phi> = |phi>: the maximally entangled state is DFT-invariant,
        # so its DFT-basis histogram equals its computational populations.
        import pt_ququint_ibmq as qi
        p = qi.histogram_dft(qi.phi_max_encoded())
        for a in range(5):
            assert p[logical_index(a, a)] == pytest.approx(0.2, abs=1e-12)
        rest = [i for i in range(TWO_DIM) if i not in [logical_index(a, a) for a in range(5)]]
        assert np.allclose(p[rest], 0.0, atol=1e-12)

    def test_separable_dft_histogram_uniform_logical(self):
        # rho_sep in the DFT basis is uniform over the 25 logical outcomes
        # and exactly zero on leakage: p~(a,b) = (1/5) sum_k |<chi_a chi_b|kk>|^2 = 1/25.
        import pt_ququint_ibmq as qi
        p = qi.histogram_dft(qi.separable_dephased_encoded())
        for (a, b) in LOGICAL:
            assert p[logical_index(a, b)] == pytest.approx(1.0 / 25.0, abs=1e-12)
        leak = [i for i in range(TWO_DIM)
                if (i // ENC_DIM) > 4 or (i % ENC_DIM) > 4]
        assert np.allclose(p[leak], 0.0, atol=1e-12)

    def test_product_and_separable_share_dft_histogram(self):
        # documented degeneracy: the product state |0,0> and rho_sep have the
        # SAME DFT histogram (25 x 1/25). The witness therefore does not need
        # to separate them — both are separable and both sit at the bound.
        import pt_ququint_ibmq as qi
        p_prod = qi.histogram_dft(qi.product_encoded(0, 0))
        p_sep = qi.histogram_dft(qi.separable_dephased_encoded())
        assert np.allclose(p_prod, p_sep, atol=1e-12)

    def test_population_confound_survives_encoding(self):
        # §Z.11 lesson carried into the encoded layer: identical computational
        # histograms for |phi> and rho_sep — settings beyond populations are
        # mandatory on the QPU.
        import pt_ququint_ibmq as qi
        p_phi = qi.histogram_computational(qi.phi_max_encoded())
        p_sep = qi.histogram_computational(qi.separable_dephased_encoded())
        assert np.allclose(p_phi, p_sep, atol=1e-15)


# === COHERENCE WITNESS (DFT-diagonal weight, bound 1/5) ===


class TestCoherenceWitness:
    def test_dft_diagonal_weight_phi_is_one(self):
        import pt_ququint_ibmq as qi
        v = qi.dft_diagonal_weight(qi.histogram_dft(qi.phi_max_encoded()))
        assert v == pytest.approx(1.0, abs=1e-12)

    def test_dft_diagonal_weight_separable_at_bound(self):
        import pt_ququint_ibmq as qi
        v = qi.dft_diagonal_weight(qi.histogram_dft(qi.separable_dephased_encoded()))
        assert v == pytest.approx(qi.WITNESS_BOUND, abs=1e-12)

    def test_dft_diagonal_weight_product_at_bound(self):
        import pt_ququint_ibmq as qi
        v = qi.dft_diagonal_weight(qi.histogram_dft(qi.product_encoded(0, 0)))
        assert v == pytest.approx(qi.WITNESS_BOUND, abs=1e-12)

    def test_witness_is_conditional_documented(self):
        # honesty guard: V alone is NOT an unconditional witness (the product
        # state chi_a (x) chi'_a reaches V = 1). It witnesses entanglement only
        # CONDITIONAL on maximally-correlated computational support, which is
        # verified from the computational-basis setting. The module must carry
        # this caveat in its docstring.
        import pt_ququint_ibmq as qi
        src = open(qi.__file__, encoding="utf-8").read()
        assert "conditional" in src.lower()
        assert "maximally-correlated" in src.lower()


# === SHOT SAMPLING, BOOTSTRAP, LEAKAGE REJECTION ===


class TestShotsAndLeakage:
    def test_sample_shots_reproducible(self):
        import pt_ququint_ibmq as qi
        p = qi.histogram_dft(qi.phi_max_encoded())
        c1 = qi.sample_shots_from_probs(p, 10_000, seed=42)
        c2 = qi.sample_shots_from_probs(p, 10_000, seed=42)
        assert np.array_equal(c1, c2)
        assert int(c1.sum()) == 10_000

    def test_leakage_rejection_counts_and_rate(self):
        import pt_ququint_ibmq as qi
        psi = leakage_state_two_ququint()
        p = qi.histogram_computational(psi)
        counts = qi.sample_shots_from_probs(p, 40_000, seed=7)
        rep = qi.reject_leakage(counts)
        assert int(rep["kept_counts"].sum()) + rep["n_rejected"] == 40_000
        assert rep["leakage_rate"] == pytest.approx(0.5, abs=4.0 * math.sqrt(0.25 / 40_000))
        # |phi> has zero leakage weight: rejection must be exactly zero
        p_phi = qi.histogram_computational(qi.phi_max_encoded())
        rep_phi = qi.reject_leakage(qi.sample_shots_from_probs(p_phi, 10_000, seed=3))
        assert rep_phi["n_rejected"] == 0
        assert rep_phi["leakage_rate"] == 0.0

    def test_leakage_rejection_keeps_logical_histogram(self):
        import pt_ququint_ibmq as qi
        psi = leakage_state_two_ququint()
        p = qi.histogram_computational(psi)
        counts = qi.sample_shots_from_probs(p, 40_000, seed=7)
        rep = qi.reject_leakage(counts)
        assert rep["kept_counts"].shape == (25,)
        # logical counts must be untouched by the rejection
        for (a, b) in [(0, 0), (1, 0), (4, 4)]:
            assert int(rep["kept_counts"][a * 5 + b]) == int(counts[logical_index(a, b)])

    def test_leakage_rejection_no_double_count_on_doubly_leaky_shots(self):
        # regression guard: shots where BOTH ququints land on leakage
        # (a in {5,6,7} AND b in {5,6,7}) must be counted exactly once.
        # The naive "A-leak sum + B-leak sum" double-counts these 9 bins.
        import pt_ququint_ibmq as qi
        psi = np.zeros(TWO_DIM, dtype=complex)
        psi[logical_index(0, 0)] = 1.0 / math.sqrt(3.0)
        psi[logical_index(5, 0)] = 1.0 / math.sqrt(3.0)   # A leaks only
        psi[logical_index(5, 6)] = 1.0 / math.sqrt(3.0)   # BOTH leak
        p = qi.histogram_computational(psi)
        counts = qi.sample_shots_from_probs(p, 60_000, seed=13)
        rep = qi.reject_leakage(counts)
        assert int(rep["kept_counts"].sum()) + rep["n_rejected"] == 60_000
        # expected rejection weight = 1/3 (single-leak half) + 1/3 (double-leak)
        assert rep["leakage_rate"] == pytest.approx(
            2.0 / 3.0, abs=4.0 * math.sqrt((2.0 / 9.0) / 60_000)
        )
        assert int(rep["kept_counts"][0]) == int(counts[logical_index(0, 0)])

    def test_witness_from_shots_near_exact(self):
        import pt_ququint_ibmq as qi
        p = qi.histogram_dft(qi.phi_max_encoded())
        out = qi.witness_from_shots(p, n_shots=50_000, seed=42, n_boot=1000)
        assert out["v_exact"] == pytest.approx(1.0, abs=1e-12)
        assert abs(out["v_hat"] - out["v_exact"]) <= 4.0 * out["se"] + 1e-12
        assert out["se"] > 0.0

    def test_bootstrap_reproducible(self):
        import pt_ququint_ibmq as qi
        p = qi.histogram_dft(qi.phi_max_encoded())
        o1 = qi.witness_from_shots(p, n_shots=20_000, seed=11, n_boot=500)
        o2 = qi.witness_from_shots(p, n_shots=20_000, seed=11, n_boot=500)
        assert o1["v_hat"] == o2["v_hat"]
        assert o1["se"] == o2["se"]

    def test_witness_from_shots_separable_stays_at_bound(self):
        import pt_ququint_ibmq as qi
        p = qi.histogram_dft(qi.separable_dephased_encoded())
        out = qi.witness_from_shots(p, n_shots=50_000, seed=5, n_boot=1000)
        assert abs(out["v_hat"] - qi.WITNESS_BOUND) <= 4.0 * out["se"] + 1e-12


# === PHASE-1 GUARDS ===


class TestPhase1Guards:
    def test_no_qiskit_in_phase1_source(self):
        # Phase 1 is numpy-only: transpilation and Aer noise belong to Phase 2.
        # (Pattern-C-flavoured source guard.)
        import pt_ququint_ibmq as qi
        src = open(qi.__file__, encoding="utf-8").read()
        assert "qiskit" not in src

    def test_kernel_verification_report_all_true(self):
        import pt_ququint_ibmq as qi
        checks = qi.verify_encoded_against_kernel()
        assert checks["x_restriction_matches_kernel"] is True
        assert checks["z_restriction_matches_kernel"] is True
        assert checks["x_pow5_identity"] is True
        assert checks["z_pow5_identity"] is True
        assert checks["weyl_on_logical_subspace"] is True
        assert checks["weyl_breaks_on_leakage"] is True