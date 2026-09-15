"""
Tests for pt_ququint_entanglement.py — EXPERIMENT 029.

Genuine two-ququint entanglement (25-dim, true 5 x 5 tensor product — no
zero-padding bipartition, unlike the single-qudit Schmidt analysis in
pt_ququint_empirical.py).

Covered:
  - maximally entangled phi state (1/sqrt(5)) sum_k |k,k>
  - two-ququint GHZ (|0,0> + |4,4>)/sqrt(2)
  - Weyl-displacement-generated entanglement from the kernel-verified
    X (x) X† algebra (pt_finite_kernel_check: X^5=I, X†X=I exact)
  - separable dephased mixture as the population confound
  - Schmidt coefficients / entropy (natural log, d=5 bipartition)
  - universal pure-state concurrence sqrt(2(1 - Tr rho_A^2)), max sqrt(1.6)
  - negativity via partial transpose, N = (||rho^T_B||_1 - 1)/2
  - vectorized multinomial shot sampling with seeded reproducibility + SE
  - the confound check: identical computational-basis populations and
    identical sampled counts, yet negativity 2 vs 0 — populations alone
    cannot witness entanglement (apophenia management for future QPU shots)
"""
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DIM = 25  # 5 x 5 two-ququint Hilbert space


def diag_index(k):
    return k * 5 + k


def product_state(a, b):
    psi = np.zeros(DIM)
    psi[a * 5 + b] = 1.0
    return psi


def unbalanced_bell():
    # (2|0,0> + |1,1>)/sqrt(5): Schmidt spectrum (2/sqrt(5), 1/sqrt(5), 0, 0, 0)
    psi = np.zeros(DIM)
    psi[diag_index(0)] = 2.0 / math.sqrt(5.0)
    psi[diag_index(1)] = 1.0 / math.sqrt(5.0)
    return psi


# === TWO-QUQUINT STATES ===


class TestTwoQuquintStates:
    def test_phi_is_normalized_twentyfive_dim(self):
        import pt_ququint_entanglement as qe
        phi = qe.max_entangled_phi()
        assert phi.shape == (DIM,)
        assert np.linalg.norm(phi) == pytest.approx(1.0)

    def test_phi_has_equal_diagonal_amplitudes(self):
        import pt_ququint_entanglement as qe
        phi = qe.max_entangled_phi()
        expected = np.zeros(DIM)
        for k in range(5):
            expected[diag_index(k)] = 1.0 / math.sqrt(5.0)
        assert np.allclose(phi, expected)

    def test_ghz_is_normalized_bell_pair(self):
        import pt_ququint_entanglement as qe
        ghz = qe.ghz_two_ququint()
        assert np.linalg.norm(ghz) == pytest.approx(1.0)
        support = {int(i) for i in np.nonzero(np.abs(ghz) > 1e-12)[0]}
        assert support == {diag_index(0), diag_index(4)}
        assert np.allclose(np.abs(ghz[list(support)]), 1.0 / math.sqrt(2.0))

    def test_weyl_bell_support_matches_displacement(self):
        # (I + X (x) X†)|0,0> = |0,0> + |1,4>  (X†|0> = |4> since X^5 = I)
        import pt_ququint_entanglement as qe
        psi = qe.weyl_bell_state(1)
        assert np.linalg.norm(psi) == pytest.approx(1.0)
        support = {int(i) for i in np.nonzero(np.abs(psi) > 1e-12)[0]}
        assert support == {diag_index(0), 1 * 5 + 4}
        assert np.allclose(np.abs(psi[list(support)]), 1.0 / math.sqrt(2.0))

    def test_phi_from_weyl_equals_conjugate_bell(self):
        # (1/sqrt(5)) sum_k (X (x) X†)^k |0,0> = (1/sqrt(5)) sum_k |k, -k mod 5>
        import pt_ququint_entanglement as qe
        psi = qe.phi_from_weyl()
        expected = np.zeros(DIM, dtype=complex)
        for k in range(5):
            expected[k * 5 + ((-k) % 5)] = 1.0 / math.sqrt(5.0)
        assert np.allclose(psi, expected)


# === SCHMIDT DECOMPOSITION AND ENTROPY ===


class TestSchmidtEntropy:
    def test_phi_schmidt_coefficients_all_equal(self):
        import pt_ququint_entanglement as qe
        sigma = qe.schmidt_coefficients(qe.max_entangled_phi())
        assert sigma.shape == (5,)
        assert np.allclose(sigma, 1.0 / math.sqrt(5.0))

    def test_phi_entropy_is_ln5(self):
        import pt_ququint_entanglement as qe
        assert qe.schmidt_entropy(qe.max_entangled_phi()) == pytest.approx(math.log(5.0))

    def test_ghz_entropy_is_ln2(self):
        import pt_ququint_entanglement as qe
        assert qe.schmidt_entropy(qe.ghz_two_ququint()) == pytest.approx(math.log(2.0))

    def test_product_state_entropy_zero(self):
        import pt_ququint_entanglement as qe
        assert qe.schmidt_entropy(product_state(2, 3)) == pytest.approx(0.0)

    def test_unbalanced_state_spectrum_and_entropy(self):
        import pt_ququint_entanglement as qe
        psi = unbalanced_bell()
        sigma = qe.schmidt_coefficients(psi)
        assert np.allclose(sigma[:2], [2.0 / math.sqrt(5.0), 1.0 / math.sqrt(5.0)])
        expected_s = -(0.8) * math.log(0.8) - 0.2 * math.log(0.2)
        assert qe.schmidt_entropy(psi) == pytest.approx(expected_s)


# === CONCURRENCE (universal pure-state analogue, d = 5) ===


class TestConcurrence:
    def test_phi_concurrence_sqrt_1p6(self):
        import pt_ququint_entanglement as qe
        c = qe.concurrence_pure(qe.max_entangled_phi())
        assert c == pytest.approx(math.sqrt(1.6))

    def test_ghz_concurrence_one(self):
        import pt_ququint_entanglement as qe
        assert qe.concurrence_pure(qe.ghz_two_ququint()) == pytest.approx(1.0)

    def test_product_concurrence_zero(self):
        import pt_ququint_entanglement as qe
        assert qe.concurrence_pure(product_state(0, 0)) == pytest.approx(0.0)

    def test_unbalanced_concurrence_exact_four_fifths(self):
        # rho_A = diag(4/5, 1/5): C = sqrt(2(1 - 17/25)) = sqrt(16/25) = 0.8
        import pt_ququint_entanglement as qe
        assert qe.concurrence_pure(unbalanced_bell()) == pytest.approx(0.8)

    def test_concurrence_bounded_for_mixed_superposition(self):
        # a generic two-term state with relative phase must stay in [0, sqrt(1.6)]
        import pt_ququint_entanglement as qe
        psi = np.zeros(DIM, dtype=complex)
        psi[diag_index(0)] = math.cos(0.7)
        psi[diag_index(2)] = math.sin(0.7) * np.exp(1.3j)
        c = qe.concurrence_pure(psi)
        assert 0.0 <= c <= math.sqrt(1.6) + 1e-12


# === NEGATIVITY (partial transpose, 5 x 5) ===


class TestNegativity:
    def test_phi_negativity_is_two(self):
        # maximally entangled d x d: N = (d - 1)/2 = 2 for d = 5
        import pt_ququint_entanglement as qe
        rho = qe.density_matrix(qe.max_entangled_phi())
        assert qe.negativity(rho) == pytest.approx(2.0)

    def test_ghz_negativity_is_half(self):
        import pt_ququint_entanglement as qe
        rho = qe.density_matrix(qe.ghz_two_ququint())
        assert qe.negativity(rho) == pytest.approx(0.5)

    def test_product_negativity_zero(self):
        import pt_ququint_entanglement as qe
        rho = qe.density_matrix(product_state(1, 2))
        assert qe.negativity(rho) == pytest.approx(0.0)

    def test_separable_mixture_negativity_zero(self):
        # rho_sep = (1/5) sum_k |kk><kk| is manifestly separable (convex sum of
        # product projectors), so N = 0 must hold — while its computational-basis
        # populations coincide with those of |phi>. Note: in d x d with d > 2 the
        # PPT criterion is necessary but NOT sufficient; here separability is
        # manifest by construction, so no PPT caveat is needed.
        import pt_ququint_entanglement as qe
        rho_sep = qe.separable_dephased_phi()
        assert qe.negativity(rho_sep) == pytest.approx(0.0)

    def test_weyl_bell_negativity_is_half(self):
        import pt_ququint_entanglement as qe
        rho = qe.density_matrix(qe.weyl_bell_state(1))
        assert qe.negativity(rho) == pytest.approx(0.5)


# === WEYL-DISPLACEMENT CONNECTION (kernel-verified algebra) ===


class TestWeylAlgebraConnection:
    def test_weyl_bell_is_maximally_entangled_two_term(self):
        import pt_ququint_entanglement as qe
        psi = qe.weyl_bell_state(1)
        assert qe.schmidt_entropy(psi) == pytest.approx(math.log(2.0))
        assert qe.concurrence_pure(psi) == pytest.approx(1.0)

    def test_weyl_bell_identity_displacement_is_product(self):
        # k = 0: (I + I)|0,0> = 2|0,0> — a single Weyl displacement of a basis
        # state never entangles; only superpositions of displacements do.
        import pt_ququint_entanglement as qe
        psi = qe.weyl_bell_state(0)
        assert qe.schmidt_entropy(psi) == pytest.approx(0.0)
        assert qe.concurrence_pure(psi) == pytest.approx(0.0)
        assert qe.negativity(qe.density_matrix(psi)) == pytest.approx(0.0)

    def test_phi_from_weyl_is_maximally_entangled(self):
        import pt_ququint_entanglement as qe
        psi = qe.phi_from_weyl()
        assert qe.schmidt_entropy(psi) == pytest.approx(math.log(5.0))
        assert qe.concurrence_pure(psi) == pytest.approx(math.sqrt(1.6))
        assert qe.negativity(qe.density_matrix(psi)) == pytest.approx(2.0)


# === VECTORIZED SHOT SAMPLING ===


class TestShotSampling:
    def test_counts_reproducible_with_seed(self):
        import pt_ququint_entanglement as qe
        probs = qe.populations(qe.max_entangled_phi())
        c1 = qe.sample_shots_from_probs(probs, 10_000, seed=42)
        c2 = qe.sample_shots_from_probs(probs, 10_000, seed=42)
        c3 = qe.sample_shots_from_probs(probs, 10_000, seed=43)
        assert np.array_equal(c1, c2)
        assert not np.array_equal(c1, c3)

    def test_counts_sum_to_shots_and_support_matches(self):
        import pt_ququint_entanglement as qe
        phi = qe.max_entangled_phi()
        probs = qe.populations(phi)
        counts = qe.sample_shots_from_probs(probs, 5_000, seed=7)
        assert int(counts.sum()) == 5_000
        nonzero = {int(i) for i in np.nonzero(counts)[0]}
        allowed = {diag_index(k) for k in range(5)}
        assert nonzero <= allowed

    def test_phi_frequencies_within_four_sigma(self):
        import pt_ququint_entanglement as qe
        phi = qe.max_entangled_phi()
        probs = qe.populations(phi)
        n = 50_000
        counts = qe.sample_shots_from_probs(probs, n, seed=42)
        freqs = counts / n
        se = qe.sampling_standard_error(probs, n)
        dev = np.abs(freqs - probs)
        # all 20 off-diagonal bins have p = 0 and must stay empty
        assert counts[[i for i in range(DIM) if i not in [diag_index(k) for k in range(5)]]].sum() == 0
        assert np.all(dev <= 4.0 * se + 1e-15)

    def test_standard_error_matches_formula(self):
        import pt_ququint_entanglement as qe
        probs = qe.populations(qe.max_entangled_phi())
        n = 8_192
        se = qe.sampling_standard_error(probs, n)
        expected = np.sqrt(probs * (1.0 - probs) / n)
        assert np.allclose(se, expected)

    def test_multinomial_handles_large_batch(self):
        # one vectorized call for a million shots — no per-shot loop
        import pt_ququint_entanglement as qe
        probs = qe.populations(qe.max_entangled_phi())
        counts = qe.sample_shots_from_probs(probs, 1_000_000, seed=11)
        assert int(counts.sum()) == 1_000_000


# === POPULATION CONFOUND (apophenia management) ===


class TestPopulationConfound:
    def test_populations_identical_entanglement_differs(self):
        import pt_ququint_entanglement as qe
        phi = qe.max_entangled_phi()
        rho_sep = qe.separable_dephased_phi()
        p_phi = qe.populations(phi)
        p_sep = qe.populations(rho_sep)
        assert np.allclose(p_phi, p_sep)
        # yet: negativity 2 vs 0
        assert qe.negativity(qe.density_matrix(phi)) == pytest.approx(2.0)
        assert qe.negativity(rho_sep) == pytest.approx(0.0)

    def test_confound_report_verdict(self):
        import pt_ququint_entanglement as qe
        report = qe.confound_report(n_shots=20_000, seed=5)
        assert report["populations_identical"] is True
        assert report["sampled_counts_identical"] is True
        assert report["negativity_differs"] is True
        assert report["max_entangled_phi"]["negativity"] == pytest.approx(2.0)
        assert report["separable_mixture"]["negativity"] == pytest.approx(0.0)
        assert int(report["max_entangled_phi"]["counts"].sum()) == 20_000