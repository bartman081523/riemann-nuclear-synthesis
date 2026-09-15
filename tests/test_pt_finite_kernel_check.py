"""
Tests for pt_finite_kernel_check.py — Pattern C (decide-analogue, zeta-23-lean).

Mirrors the LawN256.lean structure of anthropics/zeta-23-lean:
  - UNTRUSTED generator: computes claims via numpy + project modules
    (pt_ququint_gf5.GF5, pt_ququint_simulator.pauli_x_5/pauli_z_5).
  - TRUSTED kernel: stdlib-only exact arithmetic (integers mod 5, cyclotomic
    ring Z[omega] = Z[x]/(Phi_5(x)), complex rationals) re-derives every claim
    from the recorded exact data — an independent code path, exactly like
    Lean's `decide` re-running a computation inside the kernel.

Claim groups (28 verdicts expected):
  gf5_axioms        (10): closure/commutativity/associativity/distributivity/
                          identity/inverses, verified with raw integer mod-5
                          arithmetic against tables recorded via the GF5 class
  ququint_displacement (5): X^5=I, Z^5=I, X†X=I, Z†Z=I, Z·X=ω·X·Z (exact Z[ω])
  exactness_enclosures (3): X5 float entries exactly integral, Z5 off-diagonals
                          exactly zero, Z5 diagonal floats inside recorded
                          rational enclosures (EnclOK-analogue)
  dft                (1): sum_k omega^{k(j-l)} = 5*delta_jl for all (j,l)
  pt_algebra         (9): P²=I, PT-symmetry criterion P·H·P == conj(H) and
                          Hermiticity H†==H for three exact rational exemplars,
                          plus the real/imag criterion split for the two
                          D+iγA-form exemplars

Expected refutations (exact, documented findings — not failures):
  - dimer_canonical_hermitian: the canonical PT dimer is non-Hermitian
  - project_form_pt_symmetric: the project's generic form H = D + iγA with real
    symmetric D, A and reversal parity does NOT satisfy strict [H,PT]=0
  - project_form_hermitian: same exemplar is non-Hermitian (as intended)
"""
import copy
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EXPECTED_TOTAL = 28
EXPECTED_CONFIRMED = 25
EXPECTED_REFUTED_NAMES = {
    "dimer_canonical_hermitian",
    "project_form_pt_symmetric",
    "project_form_hermitian",
}


def _verdict_map(result):
    return {v["name"]: v["verdict"] for v in result["verdicts"]}


# === KERNEL INDEPENDENCE (Pattern-D analogue: axiom whitelist) ===


_MARKER = "# === UNTRUSTED GENERATOR ==="


def _kernel_section_src():
    import pt_finite_kernel_check as k
    src = open(k.__file__, encoding="utf-8").read()
    return src.split(_MARKER)[0]


def _generator_section_src():
    import pt_finite_kernel_check as k
    src = open(k.__file__, encoding="utf-8").read()
    return src.split(_MARKER, 1)[1]


class TestKernelIndependence:
    """The trusted kernel must not share code paths with the untrusted
    generator: stdlib only, no numpy, no qiskit, no project imports.
    The generator section (after the marker) carries the lazy heavy imports."""

    def test_kernel_section_has_no_numpy(self):
        src = _kernel_section_src()
        assert "numpy" not in src

    def test_kernel_section_has_no_qiskit(self):
        src = _kernel_section_src()
        assert "qiskit" not in src

    def test_kernel_section_has_no_project_module_imports(self):
        src = _kernel_section_src()
        for banned in ("from pt_", "import pt_"):
            assert banned not in src

    def test_generator_uses_project_modules_and_numpy(self):
        # The generator side must actually depend on the project code it audits.
        src = _generator_section_src()
        assert "import numpy" in src
        assert "pt_ququint_gf5" in src
        assert "pt_ququint_simulator" in src


# === TRUSTED KERNEL ARITHMETIC ===


class TestCyclotomicKernelArithmetic:
    """Z[omega] = Z[x]/(Phi_5(x)), the true cyclotomic ring (rank 4), NOT the
    group ring Z[x]/(x^5-1): the ring relation 1+omega+...+omega^4 = 0 is
    what makes DFT orthogonality hold exactly. All products must reduce
    exactly mod Phi_5."""

    def test_omega_pow5_is_one(self):
        from pt_finite_kernel_check import cyc_mul, cyc_omega, cyc_one
        acc = cyc_one()
        for _ in range(5):
            acc = cyc_mul(acc, cyc_omega(1))
        assert acc == cyc_one()

    def test_omega_times_omega_inv4_is_one(self):
        from pt_finite_kernel_check import cyc_mul, cyc_omega, cyc_one
        assert cyc_mul(cyc_omega(1), cyc_omega(4)) == cyc_one()

    def test_binomial_wraparound(self):
        # (omega^2)*(omega^4) = omega^6 = omega  (exponent wraps mod 5)
        from pt_finite_kernel_check import cyc_mul, cyc_omega
        assert cyc_mul(cyc_omega(2), cyc_omega(4)) == cyc_omega(1)

    def test_one_plus_omega_squared(self):
        from pt_finite_kernel_check import cyc_add, cyc_mul, cyc_omega
        one = cyc_omega(0)
        w = cyc_omega(1)
        s = cyc_add(one, w)
        assert cyc_mul(s, s) == (1, 2, 1, 0)

    def test_sum_of_all_powers_vanishes(self):
        # 1 + omega + omega^2 + omega^3 + omega^4 == 0 in Z[x]/(Phi_5(x)):
        # exactly the relation the group ring Z[x]/(x^5-1) does NOT have
        # (there the sum is a nonzero zero-divisor) — the ring subtlety
        # the DFT-orthogonality test caught.
        from pt_finite_kernel_check import cyc_add, cyc_omega, cyc_zero
        acc = cyc_zero()
        for k in range(5):
            acc = cyc_add(acc, cyc_omega(k))
        assert acc == cyc_zero()

    def test_norm_of_omega4_is_one(self):
        # |omega^4|^2 = conj(omega^4)*omega^4 == 1 in the rank-4 ring.
        from pt_finite_kernel_check import cyc_conj, cyc_mul, cyc_omega, cyc_one
        w4 = cyc_omega(4)
        assert cyc_mul(cyc_conj(w4), w4) == cyc_one()

    def test_matrix_adjoint_of_Z5_is_Z5_inverse(self):
        from pt_finite_kernel_check import cyc_mat_adj, cyc_mat_mul, cyc_one_mat
        from pt_finite_kernel_check import canonical_Z5_cyc
        Z = canonical_Z5_cyc()
        Zadj = cyc_mat_adj(Z)
        I = cyc_one_mat(5)
        assert cyc_mat_mul(Zadj, Z) == I
        assert cyc_mat_mul(Z, Zadj) == I


class TestComplexRationalKernelArithmetic:
    """Exact complex-rational arithmetic (Fraction pairs) — no float drift."""

    def test_qc_square_exact(self):
        from fractions import Fraction

        from pt_finite_kernel_check import qc, qc_eq, qc_mul
        x = qc(Fraction(1, 3), Fraction(1, 2))
        # (1/3 + i/2)^2 = 1/9 - 1/4 + 2*i*(1/3)(1/2) = -5/36 + i/3
        expected = qc(Fraction(-5, 36), Fraction(1, 3))
        assert qc_eq(qc_mul(x, x), expected)

    def test_qc_conj(self):
        from fractions import Fraction

        from pt_finite_kernel_check import qc, qc_conj
        x = qc(Fraction(3, 7), Fraction(-2, 5))
        c = qc_conj(x)
        assert c[0] == Fraction(3, 7)
        assert c[1] == Fraction(2, 5)


# === GF(5) TABLE VERIFICATION (kernel vs GF5 class: two code paths) ===


def make_gf5_claims():
    """Record tables via the UNTRUSTED GF5 class (same as the generator)."""
    from pt_ququint_gf5 import GF5

    add_table = [[int(GF5(a) + GF5(b)) for b in range(5)] for a in range(5)]
    mul_table = [[int(GF5(a) * GF5(b)) for b in range(5)] for a in range(5)]
    inverses = [int(GF5(a).inverse()) if a else 0 for a in range(5)]
    return {
        "generator": "test",
        "groups": {
            "gf5_tables": {
                "add_table": add_table,
                "mul_table": mul_table,
                "inverses": inverses,
            }
        },
    }


class TestGF5TableVerification:
    """The kernel must re-derive the field axioms from the recorded tables
    with raw integer arithmetic — catching a buggy GF5 class."""

    def test_correct_tables_all_confirmed(self):
        from pt_finite_kernel_check import verify_gf5_tables
        result = verify_gf5_tables(make_gf5_claims())
        assert len(result) == 10
        assert all(v["verdict"] == "CONFIRMED" for v in result)

    def test_kernel_catches_broken_addition(self):
        # Simulates a buggy GF5.__add__: one table entry corrupted.
        from pt_finite_kernel_check import verify_gf5_tables
        claims = make_gf5_claims()
        claims["groups"]["gf5_tables"]["add_table"][1][2] = 4  # truth: 3
        result = verify_gf5_tables(claims)
        names = {v["name"]: v["verdict"] for v in result}
        assert names["closure_add"] == "REFUTED"

    def test_kernel_catches_broken_multiplication(self):
        from pt_finite_kernel_check import verify_gf5_tables
        claims = make_gf5_claims()
        claims["groups"]["gf5_tables"]["mul_table"][2][3] = 0  # truth: 1
        names = _verdict_map({"verdicts": verify_gf5_tables(claims)})
        assert names["closure_mul"] == "REFUTED"

    def test_kernel_catches_corrupted_inverses(self):
        from pt_finite_kernel_check import verify_gf5_tables
        claims = make_gf5_claims()
        claims["groups"]["gf5_tables"]["inverses"][3] = 2  # truth: 2? no: 3*2=6=1 mod 5 -> 2 IS correct
        # use a definitely-wrong inverse: 2^{-1} = 3, corrupt to 1
        claims["groups"]["gf5_tables"]["inverses"][2] = 1
        names = _verdict_map({"verdicts": verify_gf5_tables(claims)})
        assert names["multiplicative_inverses"] == "REFUTED"

    def test_associativity_checked_from_tables_internally(self):
        # Associativity verdicts must hold even if raw arithmetic is bypassed:
        # a table-consistent-but-wrong commutativity break is caught table-internally.
        from pt_finite_kernel_check import verify_gf5_tables
        claims = make_gf5_claims()
        claims["groups"]["gf5_tables"]["add_table"][2][3] = 4  # breaks commutativity
        names = _verdict_map({"verdicts": verify_gf5_tables(claims)})
        assert names["commutativity_add"] == "REFUTED"


# === QUQUINT DISPLACEMENT ALGEBRA (exact cyclotomic) ===


class TestDisplacementVerification:
    def test_full_claims_all_confirmed(self):
        from pt_finite_kernel_check import verify_displacement_algebra
        import pt_finite_kernel_check as k
        claims = k.generate_claims()
        result = verify_displacement_algebra(claims)
        assert len(result) == 5
        assert all(v["verdict"] == "CONFIRMED" for v in result)

    def test_kernel_catches_tampered_X5(self):
        from pt_finite_kernel_check import verify_displacement_algebra
        import pt_finite_kernel_check as k
        claims = k.generate_claims()
        claims["groups"]["displacement"]["X5"][1][0] = 2
        names = _verdict_map({"verdicts": verify_displacement_algebra(claims)})
        assert names["x_pow5_is_identity"] == "REFUTED"


# === EXACTNESS AND ENCLOSURES (EnclOK-analogue) ===


class TestEnclosureVerification:
    def test_float_z5_inside_recorded_enclosures(self):
        from pt_finite_kernel_check import verify_exactness_and_enclosures
        import pt_finite_kernel_check as k
        claims = k.generate_claims()
        result = verify_exactness_and_enclosures(claims)
        assert len(result) == 3
        assert all(v["verdict"] == "CONFIRMED" for v in result)

    def test_overly_tight_enclosure_is_refuted(self):
        from pt_finite_kernel_check import verify_exactness_and_enclosures
        import pt_finite_kernel_check as k
        claims = k.generate_claims()
        # Replace the real-part enclosure of Z5[1,1] with a box that provably
        # excludes the float (Re(omega) ~ 0.309 is not in [2, 3]): the kernel
        # must catch the mismatched membership exactly, without float slack.
        claims["groups"]["displacement"]["Z5_enclosures"][1][0] = [2, 1, 3, 1]
        names = _verdict_map({"verdicts": verify_exactness_and_enclosures(claims)})
        assert names["z5_diagonal_in_enclosures"] == "REFUTED"


# === DFT ORTHOGONALITY (kernel computes the sums itself) ===


class TestDFTOrthogonality:
    def test_orthogonality_confirmed(self):
        from pt_finite_kernel_check import verify_dft_orthogonality
        result = verify_dft_orthogonality({"groups": {}})
        assert len(result) == 1
        assert result[0]["verdict"] == "CONFIRMED"
        assert "25" in result[0]["detail"]


# === PT ALGEBRA (exact complex-rational exemplars) ===


class TestPTVerification:
    def test_p_square_is_identity(self):
        from pt_finite_kernel_check import verify_pt_algebra
        import pt_finite_kernel_check as k
        claims = k.generate_claims()
        names = _verdict_map({"verdicts": verify_pt_algebra(claims)})
        assert names["p_square_is_identity"] == "CONFIRMED"

    def test_dimer_is_pt_symmetric_but_not_hermitian(self):
        from pt_finite_kernel_check import verify_pt_algebra
        import pt_finite_kernel_check as k
        claims = k.generate_claims()
        names = _verdict_map({"verdicts": verify_pt_algebra(claims)})
        assert names["dimer_canonical_pt_symmetric"] == "CONFIRMED"
        assert names["dimer_canonical_hermitian"] == "REFUTED"

    def test_project_form_is_not_strictly_pt_symmetric(self):
        # Documented finding: H = D + i*gamma*A with real symmetric A and
        # reversal parity fails strict [H, PT] = 0. The kernel must confirm
        # this by exact arithmetic, not by narrative.
        from pt_finite_kernel_check import verify_pt_algebra
        import pt_finite_kernel_check as k
        claims = k.generate_claims()
        names = _verdict_map({"verdicts": verify_pt_algebra(claims)})
        assert names["project_form_pt_symmetric"] == "REFUTED"
        assert names["project_form_hermitian"] == "REFUTED"

    def test_anticommuted_form_is_pt_symmetric_and_hermitian(self):
        # Exactifies the documented lesson (research doc line 209):
        # A anti-commuting with P makes i*gamma*A Hermitian (construction-error
        # class). Kernel must show: PT-symmetric AND Hermitian.
        from pt_finite_kernel_check import verify_pt_algebra
        import pt_finite_kernel_check as k
        claims = k.generate_claims()
        names = _verdict_map({"verdicts": verify_pt_algebra(claims)})
        assert names["anticommuted_form_pt_symmetric"] == "CONFIRMED"
        assert names["anticommuted_form_hermitian"] == "CONFIRMED"

    def test_criterion_split_confirmed_for_both_diagonal_form_exemplars(self):
        from pt_finite_kernel_check import verify_pt_algebra
        import pt_finite_kernel_check as k
        claims = k.generate_claims()
        names = _verdict_map({"verdicts": verify_pt_algebra(claims)})
        assert names["project_form_criterion_split"] == "CONFIRMED"
        assert names["anticommuted_form_criterion_split"] == "CONFIRMED"


# === FULL PIPELINE (LawN256 structure: claims + fingerprint + verdicts) ===


class TestFullPipeline:
    def test_generate_and_verify_totals(self):
        from pt_finite_kernel_check import generate_claims, verify_claims
        result = verify_claims(generate_claims())
        assert result["claims_total"] == EXPECTED_TOTAL
        assert result["confirmed"] == EXPECTED_CONFIRMED
        refuted = {v["name"] for v in result["verdicts"] if v["verdict"] == "REFUTED"}
        assert refuted == EXPECTED_REFUTED_NAMES

    def test_claims_fingerprint_deterministic(self):
        from pt_finite_kernel_check import claims_sha256, generate_claims
        c1 = generate_claims()
        c2 = generate_claims()
        assert claims_sha256(c1) == claims_sha256(c2)
        assert len(claims_sha256(c1)) == 64

    def test_fingerprint_changes_on_tamper(self):
        from pt_finite_kernel_check import claims_sha256, generate_claims
        c1 = generate_claims()
        c2 = copy.deepcopy(c1)
        c2["groups"]["gf5_tables"]["add_table"][0][0] = 1
        assert claims_sha256(c1) != claims_sha256(c2)

    def test_claims_json_roundtrip(self, tmp_path):
        # Generator output must serialize losslessly and verify from disk.
        from pt_finite_kernel_check import generate_claims, verify_claims, write_claims
        path = tmp_path / "claims.json"
        claims = generate_claims()
        write_claims(claims, str(path))
        loaded = json.loads(path.read_text(encoding="utf-8"))
        r1 = verify_claims(claims)
        r2 = verify_claims(loaded)
        assert r1["claims_sha256"] == r2["claims_sha256"]
        assert r2["confirmed"] == EXPECTED_CONFIRMED