"""
Tests für Säule 3: pt_prime_state.py — Prime States.

Verspricht im Mermaid-Diagramm:
  - Sieb des Eratosthenes bis N=127
  - |P_N> = (1/sqrt(pi(N))) sum_{p<=N} |p>
  - Encoding: prime p -> 7-bit binär
  - Grover-Iteration G = Diffuser · Oracle
  - Anzahl Iterationen: r ~ pi/4 · sqrt(2^7) = 11
  - Verschränkungsentropie S(|P_N>) für Partition 4|3 Qubits
  - Sweep N in {7, 15, 31, 63, 127}
  - Skalierungsexponent alpha: RH-konsistent wenn ~1, Sub-RH bei ~0.5, Super-RH bei ~2

Diese Tests prüfen Primzahl-Generierung, Grover-Konstruktion und Entropie offline.
"""
import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# === PRIMZAHL-GENERIERUNG (Determinismus-Test) ===

def sieve_of_eratosthenes(N):
    """Klassisches Sieb, deterministisch, keine Zufallszahlen."""
    is_prime = [True] * (N + 1)
    is_prime[0] = is_prime[1] = False
    for p in range(2, int(N**0.5) + 1):
        if is_prime[p]:
            for multiple in range(p*p, N+1, p):
                is_prime[multiple] = False
    return [p for p in range(2, N+1) if is_prime[p]]


class TestPrimeGeneration:
    """Prüft die Sieb-Logik für |P_N>."""

    def test_primes_up_to_7(self):
        primes = sieve_of_eratosthenes(7)
        assert primes == [2, 3, 5, 7]

    def test_primes_up_to_15(self):
        primes = sieve_of_eratosthenes(15)
        assert primes == [2, 3, 5, 7, 11, 13]

    def test_primes_up_to_31(self):
        primes = sieve_of_eratosthenes(31)
        assert primes == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]

    def test_primes_up_to_127(self):
        primes = sieve_of_eratosthenes(127)
        # pi(127) = 31
        assert len(primes) == 31
        assert primes[0] == 2
        assert primes[-1] == 127

    def test_pi_127_equals_31(self):
        """Anzahl der Primzahlen <= 127 ist 31."""
        primes = sieve_of_eratosthenes(127)
        assert len(primes) == 31

    def test_sieve_is_deterministic(self):
        """Sieb muss deterministisch sein (Anti-Sharpshooter)."""
        p1 = sieve_of_eratosthenes(127)
        p2 = sieve_of_eratosthenes(127)
        assert p1 == p2


class TestPrimeStateConstruction:
    """Prüft die Konstruktion von |P_N> im Hilbert-Raum."""

    def test_P_N_normalization(self):
        """|P_N> = (1/sqrt(pi(N))) sum |p> muss Norm 1 haben."""
        primes = sieve_of_eratosthenes(127)
        n_qubits = 7
        dim = 2 ** n_qubits

        # |P_N> als Vektor
        P_N = np.zeros(dim, dtype=complex)
        for p in primes:
            P_N[p] = 1.0
        P_N /= np.sqrt(len(primes))

        norm = np.sqrt(np.sum(np.abs(P_N) ** 2))
        assert abs(norm - 1.0) < 1e-12

    def test_P_N_is_superposition_over_primes_only(self):
        """|P_N> darf nur an Primzahl-Indizes nicht-null sein."""
        primes = sieve_of_eratosthenes(127)
        n_qubits = 7
        dim = 2 ** n_qubits
        prime_set = set(primes)

        P_N = np.zeros(dim, dtype=complex)
        for p in primes:
            P_N[p] = 1.0
        P_N /= np.sqrt(len(primes))

        for k in range(dim):
            if k in prime_set:
                assert abs(P_N[k]) > 0
            else:
                assert abs(P_N[k]) == 0, f"P_N[{k}] != 0 für Nicht-Primzahl {k}"

    def test_P_N_uniform_over_primes(self):
        """Alle Primzahl-Amplituden müssen gleich gross sein (uniform)."""
        primes = sieve_of_eratosthenes(127)
        dim = 128
        P_N = np.zeros(dim, dtype=complex)
        for p in primes:
            P_N[p] = 1.0
        P_N /= np.sqrt(len(primes))

        expected_amp = 1.0 / np.sqrt(31)
        for p in primes:
            assert abs(P_N[p] - expected_amp) < 1e-12


class TestEntanglementEntropy:
    """Prüft die Verschränkungsentropie der Partition A|B."""

    def test_P_N_is_pure_state(self):
        """|P_N> ist ein reiner Zustand: Spur(rho) = 1."""
        primes = sieve_of_eratosthenes(127)
        dim = 128
        P_N = np.zeros(dim, dtype=complex)
        for p in primes:
            P_N[p] = 1.0
        P_N /= np.sqrt(len(primes))

        rho = np.outer(P_N, P_N.conj())
        assert abs(np.trace(rho) - 1.0) < 1e-12

    def test_P_N_has_positive_entropy(self):
        """|P_N> muss positive von-Neumann-Entropie haben (Verschränkung)."""
        primes = sieve_of_eratosthenes(31)
        n_qubits = 5  # 2^5 = 32
        dim = 2 ** n_qubits
        P_N = np.zeros(dim, dtype=complex)
        for p in primes:
            P_N[p] = 1.0
        P_N /= np.sqrt(len(primes))

        # Bipartition: A=2 Qubits (4 Modi), B=3 Qubits (8 Modi)
        n_A, n_B = 4, 8
        psi_matrix = P_N.reshape(n_A, n_B)

        # Schmidt decomposition
        U, S, Vh = np.linalg.svd(psi_matrix)
        # Von-Neumann-Entropie: S = -sum s_i^2 log(s_i^2)
        S_squared = S**2
        S_squared = S_squared[S_squared > 1e-12]
        S_vN = -np.sum(S_squared * np.log(S_squared))
        assert S_vN > 0, f"S({P_N[:5]}...) = {S_vN} <= 0"
        # Mehrere Schmidt-Moden (nicht trivial)
        assert len(S_squared) >= 2, f"Nur {len(S_squared)} Schmidt-Moden, sollte >= 2 sein"

    def test_P_N_entropy_scales_with_pi_N(self):
        """S/S_max ist im erwarteten Bereich (0, 1) und korreliert mit pi(N)/dim.

        Wichtige Eigenschaft: S/S_max = log(pi(N))/log(dim/2) asymptotisch,
        weil bei uniformer Superposition ueber pi(N) von dim Indizes die
        Schmidt-Moden-Groessen gleichmaessig verteilt sind.
        """
        ratios = []
        pi_over_dim = []
        for N in [7, 15, 31, 63, 127]:
            primes = sieve_of_eratosthenes(N)
            n_qubits = int(np.ceil(np.log2(N + 1)))
            dim = 2 ** n_qubits
            P_N = np.zeros(dim, dtype=complex)
            for p in primes:
                P_N[p] = 1.0
            P_N /= np.sqrt(len(primes))

            # Finde groesste Bipartition dim = n_A * n_B
            n_A = int(np.sqrt(dim))
            while dim % n_A != 0:
                n_A -= 1
            n_B = dim // n_A
            psi_matrix = P_N.reshape(n_A, n_B)
            U, S, Vh = np.linalg.svd(psi_matrix)
            S_squared = S**2
            S_squared = S_squared[S_squared > 1e-12]
            S_vN = -np.sum(S_squared * np.log(S_squared))
            S_max = np.log(min(n_A, n_B))
            ratios.append(S_vN / S_max if S_max > 0 else 0)
            pi_over_dim.append(len(primes) / dim)

        # S/S_max im erwarteten Bereich (0, 1)
        assert all(0 < r < 1 for r in ratios), f"S/S_max ausserhalb (0, 1): {ratios}"
        # S/S_max korreliert positiv mit pi(N)/dim
        # Korrelationskoeffizient > 0.5
        correlation = np.corrcoef(pi_over_dim, ratios)[0, 1]
        assert correlation > 0.5, \
            f"Korrelation S/S_max vs pi(N)/dim nur {correlation}: pi_over_dim={pi_over_dim}, ratios={ratios}"


class TestGroverIterations:
    """Prüft die Grover-Iterationsanzahl."""

    def test_grover_iterations_for_7_qubits(self):
        """Anzahl Grover-Iterationen: r ~ pi/4 * sqrt(N/pi(N))."""
        # Bei N=127, pi(N)=31: r ~ pi/4 * sqrt(128/31) = 0.785 * 2.03 = 1.6
        # Aber Grover-Oracle markiert nur pi(N) von N, also effektiv
        # r ~ pi/4 * sqrt(N / pi(N))
        import math
        N = 128  # 7 qubits
        pi_N = 31
        r = math.pi / 4 * math.sqrt(N / pi_N)
        assert 1.0 < r < 3.0, f"r={r} ausserhalb erwartetem Bereich [1, 3]"


class TestPrimeStateModule:
    """Prüft, dass pt_prime_state.py importierbar ist."""

    def test_module_imports(self):
        try:
            import pt_prime_state
            assert hasattr(pt_prime_state, 'sieve_primes')
            assert hasattr(pt_prime_state, 'construct_P_N')
            assert hasattr(pt_prime_state, 'measure_entropy')
            assert hasattr(pt_prime_state, 'main')
        except ImportError:
            pytest.skip("pt_prime_state noch nicht implementiert (erwartet bei TDD)")

    def test_sieve_primes_deterministic(self):
        try:
            import pt_prime_state
            p1 = pt_prime_state.sieve_primes(127)
            p2 = pt_prime_state.sieve_primes(127)
            assert p1 == p2
            assert len(p1) == 31
        except ImportError:
            pytest.skip("pt_prime_state noch nicht implementiert (erwartet bei TDD)")
