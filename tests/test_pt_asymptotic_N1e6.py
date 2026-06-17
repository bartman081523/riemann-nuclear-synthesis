"""
Tests fuer pt_asymptotic_N1e6.py — Asymptotik-Validierung N=10^4..10^6.

Prereg-Hypothesen:
  H_A: alpha stabil bei 0.347 (Sub-RH)
  H_B: alpha -> 1 (Latorre-Sierra)
  H_C: anderes Power-Law (z.B. alpha sinkt mit N)

Diese Tests pruefen die mathematische Korrektheit der Skript-Bausteine.
"""
import json
import math
import numpy as np
import pytest

import pt_asymptotic_N1e6 as pt_asymp


class TestSieveOfEratosthenes:
    """Prueft die Sieve-Implementierung."""

    def test_sieve_small(self):
        """Bekannte kleine Primzahl-Listen."""
        assert pt_asymp.is_prime_sieve(1) == []
        assert pt_asymp.is_prime_sieve(2) == [2]
        assert pt_asymp.is_prime_sieve(10) == [2, 3, 5, 7]
        assert pt_asymp.is_prime_sieve(20) == [2, 3, 5, 7, 11, 13, 17, 19]

    def test_sieve_count(self):
        """pi(N) stimmt mit bekannten Werten ueberein."""
        # pi(100) = 25, pi(1000) = 168, pi(10000) = 1229
        assert len(pt_asymp.is_prime_sieve(100)) == 25
        assert len(pt_asymp.is_prime_sieve(1000)) == 168
        assert len(pt_asymp.is_prime_sieve(10000)) == 1229

    def test_sieve_order(self):
        """Primes sind aufsteigend sortiert."""
        primes = pt_asymp.is_prime_sieve(1000)
        assert primes == sorted(primes)

    def test_sieve_no_composites(self):
        """Keine zusammengesetzten Zahlen in der Liste."""
        primes = set(pt_asymp.is_prime_sieve(1000))
        for p in primes:
            for d in range(2, int(math.isqrt(p)) + 1):
                assert p % d != 0, f"{p} ist nicht prim (teilbar durch {d})"

    def test_sieve_returns_primes(self):
        """Alle Zahlen in der Liste sind tatsaechlich prim."""
        for p in pt_asymp.is_prime_sieve(500):
            # Schneller Primality-Test
            assert p >= 2
            for d in range(2, int(math.isqrt(p)) + 1):
                assert p % d != 0


class TestConstructPN:
    """Prueft die statevector-Konstruktion (verwendet primes-Liste direkt)."""

    def test_construct_normalization(self):
        """|P_N> ist normiert."""
        primes = pt_asymp.is_prime_sieve(100)
        n_qubits = 7  # ceil(log2(101))
        psi = pt_asymp.construct_P_N(primes, n_qubits)
        assert abs(np.linalg.norm(psi) - 1.0) < 1e-12

    def test_construct_amplitudes(self):
        """|psi[p]| = 1/sqrt(pi(N)) fuer p prim, sonst 0."""
        primes = pt_asymp.is_prime_sieve(20)
        pi_N = len(primes)
        n_qubits = 5
        psi = pt_asymp.construct_P_N(primes, n_qubits)
        expected = 1.0 / math.sqrt(pi_N)
        for p in primes:
            assert abs(abs(psi[p]) - expected) < 1e-12
        for c in [0, 1, 4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20]:
            assert abs(psi[c]) < 1e-12


class TestSchmidtVonNeumann:
    """Prueft Schmidt-Dekomposition + vN-Entropie."""

    def test_schmidt_normalization(self):
        """sum(s_i^2) = 1."""
        primes = pt_asymp.is_prime_sieve(31)
        n_qubits = 5
        n_A = 2
        psi = pt_asymp.construct_P_N(primes, n_qubits)
        s_sq = pt_asymp.schmidt_decomposition(psi, n_A)
        assert abs(s_sq.sum() - 1.0) < 1e-12

    def test_vN_bell_state(self):
        """Bell-Zustand mit 2 Niveaus: S_vN = 1."""
        s_sq = np.array([0.5, 0.5])
        assert abs(pt_asymp.von_neumann_entropy(s_sq) - 1.0) < 1e-12

    def test_vN_pure_zero(self):
        """Reiner Zustand: S_vN = 0."""
        s_sq = np.array([1.0])
        assert abs(pt_asymp.von_neumann_entropy(s_sq)) < 1e-12

    def test_vN_uniform_max(self):
        """Uniform-Verteilung: S_vN = log_2(d)."""
        d = 16
        s_sq = np.ones(d) / d
        s_vN = pt_asymp.von_neumann_entropy(s_sq)
        assert abs(s_vN - math.log2(d)) < 1e-12

    def test_renyi_2_leq_vN(self):
        """S_2 <= S_vN (Renyi-Ungleichung)."""
        s_sq = np.array([0.7, 0.2, 0.1])
        s_vN = pt_asymp.von_neumann_entropy(s_sq)
        s_2 = pt_asymp.renyi_2(s_sq)
        assert s_2 <= s_vN + 1e-12


class TestPrereg:
    """Prueft die Prae-Registrierung."""

    def test_prereg_structure(self):
        """Prereg enthaelt die noetigen Felder."""
        assert "hypotheses" in pt_asymp.PREREG
        assert "n_values" in pt_asymp.PREREG
        assert "decision_rule" in pt_asymp.PREREG
        assert "anti_sharpshooter" in pt_asymp.PREREG

    def test_prereg_three_hypotheses(self):
        """Genau 3 Hypothesen: H_A, H_B, H_C."""
        h = pt_asymp.PREREG["hypotheses"]
        assert "H_A_sub_rh_alpha_0347" in h
        assert "H_B_latorre_alpha_1" in h
        assert "H_C_other" in h

    def test_prereg_n_values(self):
        """N-Werte: 10^4, 10^5, 10^6."""
        assert pt_asymp.PREREG["n_values"] == [10_000, 100_000, 1_000_000]

    def test_prereg_decision_rule_documented(self):
        """Decision Rule ist explizit und testbar."""
        rule = pt_asymp.PREREG["decision_rule"]
        # Sollte konkrete numerische Schwellen enthalten
        assert "0.347" in rule or "0.30" in rule or "0.40" in rule
        assert "0.7" in rule  # Latorre-Schwelle


class TestLoadExistingData:
    """Prueft das Laden der existierenden Datenpunkte."""

    def test_load_returns_list(self):
        rows = pt_asymp.load_existing_data()
        assert isinstance(rows, list)
        assert len(rows) > 0

    def test_load_sorted_by_N(self):
        """Daten sind nach N aufsteigend sortiert."""
        rows = pt_asymp.load_existing_data()
        N_list = [r["N"] for r in rows]
        assert N_list == sorted(N_list)

    def test_load_has_required_fields(self):
        """Jede Row hat N, n_qubits, n_A, pi_N, S_vN."""
        rows = pt_asymp.load_existing_data()
        for r in rows:
            assert "N" in r
            assert "n_qubits" in r
            assert "n_A" in r
            assert "pi_N" in r
            assert "S_vN" in r

    def test_load_includes_N255(self):
        """N=255 (aus N255-Skript) ist enthalten."""
        rows = pt_asymp.load_existing_data()
        N_list = [r["N"] for r in rows]
        assert 255 in N_list
        assert 1023 in N_list


class TestAsymptoticModule:
    """Prueft die Modul-Importierbarkeit."""

    def test_module_imports(self):
        import pt_asymptotic_N1e6
        assert hasattr(pt_asymptotic_N1e6, 'is_prime_sieve')
        assert hasattr(pt_asymptotic_N1e6, 'construct_P_N')
        assert hasattr(pt_asymptotic_N1e6, 'schmidt_decomposition')
        assert hasattr(pt_asymptotic_N1e6, 'von_neumann_entropy')
        assert hasattr(pt_asymptotic_N1e6, 'renyi_2')
        assert hasattr(pt_asymptotic_N1e6, 'main')
        assert hasattr(pt_asymptotic_N1e6, 'PREREG')

    def test_pipeline_small(self):
        """Vollstaendige Pipeline fuer N=100 (schneller Smoke-Test)."""
        N = 100
        primes = pt_asymp.is_prime_sieve(N)
        n_qubits = int(math.ceil(math.log2(N + 1)))
        n_A = n_qubits // 2
        psi = pt_asymp.construct_P_N(primes, n_qubits)
        s_sq = pt_asymp.schmidt_decomposition(psi, n_A)
        S_vN = pt_asymp.von_neumann_entropy(s_sq)
        S_2 = pt_asymp.renyi_2(s_sq)
        # Sanity: S_vN > 0, S_vN < log2(dim_A)
        dim_A = 2 ** n_A
        assert 0 < S_vN < math.log2(dim_A) + 1e-12
        assert S_2 <= S_vN + 1e-12
        assert S_2 > 0


class TestAsymptoticResults:
    """Prueft die existierenden Result-File (vom 2026-06-17 Run)."""

    @pytest.fixture
    def results(self):
        try:
            with open("pt_asymptotic_N1e6_results.json") as f:
                return json.load(f)
        except FileNotFoundError:
            pytest.skip("pt_asymptotic_N1e6_results.json nicht gefunden")

    def test_results_have_11_points(self, results):
        """11 Datenpunkte total (8 existing + 3 new)."""
        assert results["n_existing_points"] == 8
        assert results["n_new_points"] == 3
        assert len(results["N_list_all"]) == 11

    def test_results_N_list_includes_asymptotic(self, results):
        """N-Liste enthaelt 10^4, 10^5, 10^6."""
        N_list = results["N_list_all"]
        assert 10_000 in N_list
        assert 100_000 in N_list
        assert 1_000_000 in N_list

    def test_results_verdict_is_valid(self, results):
        """Verdict ist H_A, H_B oder H_C."""
        verdict = results["verdict"]
        assert verdict.startswith("H_A") or verdict.startswith("H_B") or verdict.startswith("H_C")

    def test_results_incremental_alpha_decreasing(self, results):
        """Inkrementelles alpha faellt monoton (kritische Beobachtung)."""
        incremental = results["incremental_alpha_vN"]
        # Nimm nur die letzten 4 Punkte (asymptotische Region)
        last_few = incremental[-4:]
        alphas = [p["alpha_vN"] for p in last_few]
        # Sollte fallend sein (alpha sinkt mit N)
        for i in range(1, len(alphas)):
            assert alphas[i] <= alphas[i-1] + 1e-9, \
                f"alpha steigt zwischen N={last_few[i-1]['N_max']} und N={last_few[i]['N_max']}"

    def test_results_asymptotic_alpha_below_latorre(self, results):
        """alpha(N=10^6) ist signifikant < 1 (Latorre)."""
        incremental = results["incremental_alpha_vN"]
        alpha_at_1e6 = incremental[-1]["alpha_vN"]
        assert alpha_at_1e6 < 0.5, \
            f"alpha(N=10^6) = {alpha_at_1e6} sollte < 0.5 sein (Latorre sagt 1)"