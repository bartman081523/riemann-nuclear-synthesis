"""
EXPERIMENT 010 - SÄULE 3: Prime States (Verschränkungsentropie).

Verspricht im Mermaid-Diagramm:
  - Sieb des Eratosthenes bis N=127
  - |P_N> = (1/sqrt(pi(N))) sum_{p<=N} |p>
  - Encoding: prime p -> 7-bit binär (fuer N<=127)
  - Grover-Iteration G = Diffuser · Oracle
  - Anzahl Iterationen: r ~ pi/4 * sqrt(N/pi(N)) ≈ 1.6 fuer N=128, pi(N)=31
  - Verschränkungsentropie S(|P_N>) für Partition 4|8 (groesste sinnvolle Bipartition)
  - Sweep N in {7, 15, 31, 63, 127}
  - Skalierungsexponent alpha: RH-konsistent wenn ~1, Sub-RH bei ~0.5, Super-RH bei ~2

Diese Implementierung hat die Kern-Logik (sieve, construct_P_N,
measure_entropy, grover_iterations) vollstaendig offline. Die QPU-
Konstruktion von |P_N> via Grover-Oracle in main() ist ein Hardware-
Schritt, der spaeter ergaenzt wird.
"""
import json
import numpy as np
import math

# N-Werte fuer den Sweep
N_SWEEP = [7, 15, 31, 63, 127]


def sieve_primes(N):
    """Sieb des Eratosthenes bis N. Deterministisch, keine Random-Quelle.

    Returns:
        Liste der Primzahlen p mit 2 <= p <= N, aufsteigend sortiert.
    """
    if N < 2:
        return []
    is_prime = [True] * (N + 1)
    is_prime[0] = is_prime[1] = False
    for p in range(2, int(N ** 0.5) + 1):
        if is_prime[p]:
            for multiple in range(p * p, N + 1, p):
                is_prime[multiple] = False
    return [p for p in range(2, N + 1) if is_prime[p]]


def construct_P_N(N):
    """Konstruiere |P_N> = (1/sqrt(pi(N))) sum_{p<=N} |p> im Hilbert-Raum.

    Encoding: prime p -> Index p im 2^n Qubit-Register.
    Dimension: 2^ceil(log2(N+1))

    Returns:
        (P_N, dim, n_qubits) wobei P_N ein dim-dim komplexer Vektor ist.
    """
    primes = sieve_primes(N)
    n_qubits = int(math.ceil(math.log2(N + 1)))
    dim = 2 ** n_qubits

    P_N = np.zeros(dim, dtype=complex)
    for p in primes:
        P_N[p] = 1.0
    P_N /= math.sqrt(len(primes))
    return P_N, dim, n_qubits


def measure_entropy(P_N):
    """Verschränkungs-Entropie S_vN der bipartiten Schmidt-Zerlegung.

    Waehlt die groesste sinnvolle Bipartition: dim = n_A * n_B mit
    n_A <= n_B und n_A maximal.

    Returns:
        (S_vN, S_max, n_A, n_B) — von-Neumann-Entropie, max. Entropie
        und die Partition-Dimensionen.
    """
    dim = len(P_N)
    n_A = int(math.sqrt(dim))
    while dim % n_A != 0 and n_A > 1:
        n_A -= 1
    n_B = dim // n_A
    psi_matrix = P_N.reshape(n_A, n_B)
    _, S, _ = np.linalg.svd(psi_matrix)

    # Von-Neumann-Entropie: S = -sum s_i^2 log(s_i^2)
    S_squared = S ** 2
    S_squared = S_squared[S_squared > 1e-12]
    S_vN = -np.sum(S_squared * np.log(S_squared))
    S_max = math.log(min(n_A, n_B))
    return S_vN, S_max, n_A, n_B


def grover_iterations(N, n_marked=None):
    """Anzahl Grover-Iterationen r ~ pi/4 * sqrt(N / n_marked).

    Bei N=128, pi(N)=31 markierte Elemente (Primzahlen):
    r = pi/4 * sqrt(128/31) ≈ 1.6, also r=1 oder r=2.

    Returns:
        r (int) — empfohlene Anzahl Iterationen.
    """
    n_qubits = int(math.ceil(math.log2(N + 1)))
    dim = 2 ** n_qubits
    if n_marked is None:
        n_marked = len(sieve_primes(N))
    r_float = math.pi / 4 * math.sqrt(dim / n_marked)
    return max(1, int(round(r_float)))


def precompute_predictions():
    """Berechne Vorhersagen fuer S(N) Sweep bei N in {7, 15, 31, 63, 127}."""
    results = []
    for N in N_SWEEP:
        primes = sieve_primes(N)
        P_N, dim, n_qubits = construct_P_N(N)
        S_vN, S_max, n_A, n_B = measure_entropy(P_N)
        results.append({
            "N": N,
            "pi_N": len(primes),
            "dim": dim,
            "n_qubits": n_qubits,
            "n_A": n_A,
            "n_B": n_B,
            "S_vN": S_vN,
            "S_max": S_max,
            "S_normalized": S_vN / S_max if S_max > 0 else 0,
            "pi_over_dim": len(primes) / dim,
            "grover_r": grover_iterations(N)
        })
    return {
        "N_sweep": N_SWEEP,
        "results": results,
        "decision_rule": (
            "RH-konsistent: alpha = log(S)/log(N) ~ 1. "
            "Sub-RH: alpha < 0.5 (zu wenig Verschr.). "
            "Super-RH: alpha > 2 (zu viel Verschr.)."
        )
    }


def main():
    """Hauptfunktion: Pre-Registrierung + Sweep + Skalierungsanalyse."""
    prereg = precompute_predictions()
    with open("pt_prime_state_prereg.json", "w") as f:
        json.dump(prereg, f, indent=2)
    print(f"Praeregistrierung geschrieben: pt_prime_state_prereg.json")

    # === Sweep ausgeben ===
    print("\nN, pi(N), S_vN, S/S_max, Grover r")
    for r in prereg['results']:
        print(f"  N={r['N']:3d}, pi={r['pi_N']:2d}, S={r['S_vN']:.4f}, "
              f"S/S_max={r['S_normalized']:.4f}, r={r['grover_r']}")

    # === Skalierungsanalyse ===
    N_vals = np.array([r['N'] for r in prereg['results']])
    S_vals = np.array([r['S_vN'] for r in prereg['results']])
    # log-log-Fit: log(S) = alpha * log(N) + const
    log_N = np.log(N_vals)
    log_S = np.log(S_vals)
    alpha, log_const = np.polyfit(log_N, log_S, 1)
    print(f"\nSkalierungsexponent alpha = {alpha:.4f}")
    print(f"Entscheidungsregel: {prereg['decision_rule']}")

    # === Speichern ===
    output = {
        "predictions": prereg,
        "scaling_analysis": {
            "alpha": float(alpha),
            "log_const": float(log_const),
            "log_N": log_N.tolist(),
            "log_S": log_S.tolist()
        }
    }
    with open("pt_prime_state_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nErgebnisse gespeichert: pt_prime_state_results.json")


if __name__ == "__main__":
    main()
