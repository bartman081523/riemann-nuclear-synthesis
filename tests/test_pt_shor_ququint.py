"""EXPERIMENT 037 — Shor-Oracle auf Ququint/GF(5): Tests.

Engineering-Layer (Statevector, 0 QPU): Digit-Encoding, DFT ueber Z_{5^n}
(direkt vs. ziffern-faktorisiert), Permutations-Unitary U_{a,N}, Zyklus-/
Trace-Identitaeten, CRT-Struktur-Null, Statevector-QPE mit Kettenbruch-
Rekonstruktion, voller Shor-Wrapper, Fermat-Grid inkl. Korselt-Blindheit,
Ensemble-SFF aus Zyklen.
"""

import os
import sys
from math import gcd

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_shor_ququint as sq


# === Register-Utilities ===

def test_digit_encoding_roundtrip():
    for n in (2, 3, 4):
        Q = 5 ** n
        for x in list(range(Q)):
            assert sq.decode_digits(sq.encode_digits(x, n)) == x
    assert sq.encode_digits(156, 4) == (1, 1, 1, 1)   # 1 + 5 + 25 + 125


def test_digit_encoding_range_guard():
    try:
        sq.encode_digits(25, 2)
        raised = False
    except ValueError:
        raised = True
    assert raised


# === DFT ueber Z_{5^n} ===

def test_dft_5n_unitary():
    for n in (2, 3):
        F = sq.dft_5n(n)
        dev = np.max(np.abs(F @ F.conj().T - np.eye(5 ** n)))
        assert dev < 1e-12


def test_dft_factored_matches_direct():
    for n in (2, 3):
        dev = np.max(np.abs(sq.dft_5n_factored(n) - sq.dft_5n(n)))
        assert dev < sq.DFT_TOL, "n=%d dev=%.2e" % (n, dev)


def test_iqft_is_conjugate_inverse():
    F = sq.dft_5n(2)
    assert np.max(np.abs(sq.iqft_5n(2) - F.conj().T)) == 0.0


# === Permutations-Unitary ===

def test_u_an_unitary_and_idle_subspace():
    U = sq.U_an(7, 15, 25)
    assert np.max(np.abs(U @ U.T - np.eye(25))) < 1e-12
    # Idle-Subraum: x >= 15 bleibt x
    for x in range(15, 25):
        assert U[x, x] == 1.0
    assert np.max(np.abs(U[15:, :15])) == 0.0
    assert np.max(np.abs(U[:15, 15:])) == 0.0


def test_u_an_matches_classical_map():
    a, N = 7, 15
    U = sq.U_an(a, N, N)
    for x in range(N):
        assert U[(a * x) % N, x] == 1.0


def test_u_an_rejects_non_coprime():
    try:
        sq.U_an(3, 15, 15)
        raised = False
    except ValueError:
        raised = True
    assert raised


# === Zyklen / Trace ===

def test_perm_cycles_structure_n15_a7():
    cyc = sq.perm_cycles(7, 15)
    # 0, 5, 10 Fixpunkte; drei 4er-Zyklen (u.a. die Einheiten-Orbit von 1)
    assert cyc == [1, 1, 1, 4, 4, 4]


def test_trace_power_from_cycles_exact():
    cyc = sq.perm_cycles(7, 15)
    U = sq.U_an(7, 15, 15)
    for t in range(1, 9):
        lhs = sq.trace_power_from_cycles(cyc, t)
        rhs = round(np.trace(np.linalg.matrix_power(U, t)).real)
        assert lhs == rhs


# === CRT-Identitaeten (strukturelle Null) ===

def test_crt_matrix_is_permutation():
    C = sq.crt_matrix(3, 5)
    assert np.max(np.abs(C @ C.T - np.eye(15))) < 1e-12


def test_crt_factorization_exact_n15_n21():
    for (p, q, a_list) in ((3, 5, (2, 7)), (3, 7, (2, 5))):
        for a in a_list:
            dev = sq.crt_factorization_dev(a, p, q)
            assert dev <= sq.TOL_IDENTITY, (p, q, a, dev)


def test_trace_product_identity():
    for (p, q, a_list) in ((3, 5, (2, 7)), (3, 7, (2, 5))):
        for a in a_list:
            dev = sq.trace_product_dev(a, p, q, ts=sq.TS_CHECK)
            assert dev <= sq.TOL_IDENTITY, (p, q, a, dev)


# === Ordnungs-Arithmetik ===

def test_order_mod():
    assert sq.order_mod(7, 15) == 4
    assert sq.order_mod(2, 21) == 6
    assert sq.order_mod(2, 11) == 10
    assert sq.order_mod(1, 15) == 1


def test_max_order_prime_is_cyclic():
    # primes: zyklische Gruppe -> max_order = p-1 (primitive Wurzel)
    for p in (7, 11, 13):
        assert sq.max_order(p) == p - 1


# === Statevector-QPE ===

def test_qpe_n15_a7_recovers_r4():
    res = sq.qpe_order(7, 15)
    assert res["r"] == 4
    assert 4 in res["denominators"]
    assert pow(7, res["r"], 15) == 1
    # Peaks exakt auf dem s*Q/4-Raster: jede Peak-Position k* = s*Q/4
    # (nicht ganzzahlig fuer Q=625) splittet in zwei Nachbar-Bins ->
    # 7 signifikante Bins (numerisch verifiziert: 0.25 / 0.2026 /
    # 0.0225 / 0.1013 / 0.1013 / 0.0225 / 0.2026, Summe = 1.0000)
    rel = res["probs"] > 0.05 * res["probs"].max()
    assert set(np.nonzero(rel)[0]) == {0, 156, 157, 312, 313, 468, 469}
    assert abs(res["probs"].sum() - 1.0) < 1e-9


def test_qpe_n21_a2_recovers_r6():
    res = sq.qpe_order(2, 21)
    assert res["r"] == 6
    assert 6 in res["denominators"]
    assert pow(2, res["r"], 21) == 1


def test_qpe_n11_a2_recovers_r10():
    res = sq.qpe_order(2, 11)
    assert res["r"] == 10
    assert 10 in res["denominators"]


def test_qpe_register_guard():
    try:
        sq.qpe_order(7, 15, n_x=1)      # 5^1 = 5 < 15
        raised = False
    except ValueError:
        raised = True
    assert raised


# === Voller Shor-Wrapper ===

def test_shor_factor_15():
    assert sq.shor_factor(15) == (3, 5)


def test_shor_factor_21():
    assert sq.shor_factor(21) == (3, 7)


def test_shor_factor_prime_returns_none():
    # primes: a^{r/2} = +-1 immer -> nie nichttrivialer Faktor
    for p in (7, 11, 13, 17):
        assert sq.shor_factor(p) is None, p


def test_shor_factor_gcd_shortcut():
    assert sq.shor_factor(15, a_list=[3]) == (3, 5)


# === Fermat-Grid + Korselt-Blindheit ===

def test_grid_violation_primes_zero():
    for p in (7, 11, 13, 17, 19, 23):
        assert sq.grid_violation_rate(p) == 0.0, p


def test_grid_violation_composites_positive():
    for N in (9, 15, 21, 25, 33, 35, 39):
        rate = sq.grid_violation_rate(N)
        assert rate > 0.05, (N, rate)


def test_grid_blindness_korselt_class():
    # 561 = 3*11*17: Korselt erfuellt (p-1 | 560 fuer p | 561) ->
    # lambda = 80 teilt 560 -> ALLE Orders teilen N-1 -> Rate 0.
    assert sq.grid_violation_rate(561) == 0.0
    # Aber: max_order trennt (zyklische Gruppe nur bei primes)
    assert sq.max_order(561) == 80
    assert sq.max_order(561) != 560


# === Ensemble-SFF aus Zyklen ===

def test_sff_ensemble_matches_direct_matrix():
    N, a_list = 15, [2, 4, 7, 8, 11, 13]
    sff = sq.sff_ensemble(N, a_list, ts=(1, 2, 3, 4))
    for t in (1, 2, 3, 4):
        direct = float(np.mean([
            abs(np.trace(np.linalg.matrix_power(sq.U_an(a, N, N), t))) ** 2
            for a in a_list]))
        assert abs(sff[t] - direct) < 1e-9, (t, sff[t], direct)