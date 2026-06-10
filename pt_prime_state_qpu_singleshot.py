"""
SAEULE 3 QPU — Schmidt-Entropie auf Fez/TOKEN2.

ARCHITEKTUR (statevector-first, qiskit-agnostisch):
  1. statevector psi = |P_N> explizit in numpy
  2. Schmidt-Zerlegung psi = sum_i s_i |a_i>_A |b_i>_B in numpy (linalg.svd)
  3. QPU-Implementierung: initialize(psi_prime) wo psi_prime = (U_A^dagger \otimes I_B) psi
     - NICHT qc.unitary() mit Qiskit-Indizierung (die haben wir nicht verifiziert)
     - initialize() haben wir verifiziert: statevector-Population an Index p
  4. Messung: Sampler misst System A in Computational-Basis
  5. P(|i>_A) = s_i^2 (per Konstruktion)

WARUM STATEVECTOR-FIRST:
  Wir verifizieren die Schmidt-Mathematik in numpy, bevor wir den
  Qiskit-Schaltkreis beruehren. Wenn statevector-P und QPU-P uebereinstimmen,
  wissen wir dass die QPU-Messung das gleiche misst wie die Theorie.

QUBIT-LAYOUT (Qiskit little-endian):
  Index p = q_0 + 2*q_1 + 4*q_2 + 8*q_3 (q_0 = LSB)
  System A: q_0..q_{n_A-1} (Bits 0..n_A_qubits-1, LSB-Seite)
  System B: q_{n_A}..q_{n-1} (Bits n_A_qubits..n-1, MSB-Seite)
  reshape((n_A, n_B)) C-order: A = col, B = row

WAS WIR MESSEN:
  QPU initialize(psi_prime) + measure(q_0..q_{n_A-1})
  => Bitstring-Verteilung gibt s_i^2
  => S_vN = -sum s_i^2 log(s_i^2)
  => alpha = d log(S_vN) / d log(N)

PRE-REGISTRIERUNG: pt_prime_state_prereg.json (S_vN klassisch, alpha-Aer)

Verwendet TOKEN2 (neuer Account, Tageslimit 10 Min).
"""
import json
import math
import os
import sys
import numpy as np
from scipy.optimize import minimize

# ============================================================
# KONFIG
# ============================================================
BACKEND = "ibm_fez"
# N_Sweep: alle 5 Werte aus pt_prime_state_prereg.json
# N=7: 3 Qubits (8-dim), 4 primes
# N=15: 4 Qubits (16-dim), 6 primes
# N=31: 5 Qubits (32-dim), 11 primes
# N=63: 6 Qubits (64-dim), 18 primes
# N=127: 7 Qubits (128-dim), 31 primes
# Fez hat 156 Qubits, also alle machbar
N_VALUES = [7, 15, 31, 63, 127]
SHOTS = 4096  # brauchen mehr als Singleshot (1024) wg. Schmidt-Sampling


# ============================================================
# HILFSFUNKTIONEN
# ============================================================
def sieve_primes(N):
    """Alle Primzahlen p <= N."""
    return [p for p in range(2, N + 1)
            if all(p % d != 0 for d in range(2, int(math.sqrt(p)) + 1))]


def construct_P_N(N):
    """Konstruiere |P_N> = (1/sqrt(pi(N))) sum_{p<=N} |p> als statevector."""
    primes = sieve_primes(N)
    n_qubits = int(math.ceil(math.log2(N + 1)))
    dim = 2 ** n_qubits
    psi = np.zeros(dim, dtype=complex)
    for p in primes:
        psi[p] = 1.0 / math.sqrt(len(primes))
    return psi, primes, dim, n_qubits


def schmidt_decomposition(psi, n_A, n_B):
    """Schmidt-Zerlegung: psi = sum_i s_i |a_i>_A |b_i>_B.

    Qubit-Layout (Qiskit little-endian):
      Index p = q_0 + 2*q_1 + ... + 2^{n-1} q_{n-1}
      System A = Bits 0..n_A_qubits-1 (LSB-Seite, q_0..q_{n_A-1})
      System B = Bits n_A_qubits..n-1 (MSB-Seite)
      psi.reshape((n_A, n_B)) C-order: A = col, B = row
        (col index = p mod n_A, row index = p div n_A)
        p = q_0 + 2q_1 + ... = (q_0 + 2q_1 + ... + 2^{n_A-1} q_{n_A-1})
                              + 2^{n_A} (q_{n_A} + ... + q_{n-1})
        Mit n_A = 2^k, n_B = 2^l: p = A_index + n_A * B_index
        A_index = p mod n_A, B_index = p div n_A  ✓

    Returns:
        s_i (Singulärwerte, sortiert absteigend)
        U (n_A x n_A, Schmidt-Basis |a_i> = U |i>_A)
        Vh (n_B x n_B, Schmidt-Basis |b_i> = V |i>_B)
    """
    psi_matrix = psi.reshape((n_A, n_B))  # A=col, B=row
    U, s, Vh = np.linalg.svd(psi_matrix)
    return s, U, Vh


def von_neumann_entropy(s):
    """S_vN = -sum s_i^2 log(s_i^2)."""
    s_sq = s ** 2
    s_sq = s_sq[s_sq > 1e-12]
    return -np.sum(s_sq * np.log(s_sq))


def statevector_after_U_A(s, U, psi, n_A, n_B):
    """Berechne psi_prime = (U_A^dagger \otimes I_B) psi als statevector.

    Konvention: Schmidt-Zerlegung psi = U S Vh
    U_A^dagger @ psi_matrix = S Vh (diagonal in Schmidt-Basis)
    Wir wollen (U_A^dagger \otimes I_B) |psi>:
      psi_prime_matrix = U^H @ psi_matrix  (Matrix-Mult auf A-Achse)

    Qubit-Layout: A = q_0..q_{n_A-1} (LSB-Seite), B = q_{n_A}..q_{n-1} (MSB-Seite)
    Qiskit statevector-Index: p = q_0 + 2q_1 + 4q_2 + 8q_3 = A + n_A * B
      => flatten(order='F') mit i + j*n_A = A + n_A*B = p ✓
      (C-order flatten wäre i*n_B + j = q_0 + 2q_1 + (q_2+4q_3)*4 ≠ p)
    """
    psi_matrix = psi.reshape((n_A, n_B))  # A=col, B=row
    psi_prime_matrix = U.conj().T @ psi_matrix
    return psi_prime_matrix.flatten(order='F')


def verify_statevector(s, U, Vh, psi, n_A, n_B):
    """Verifiziere: psi_prime = (U^H \otimes I) psi hat Populationen s_i^2 an Index (i + 0*n_B)."""
    psi_prime = statevector_after_U_A(s, U, psi, n_A, n_B)
    # Qiskit-statevector-Index p = A + n_A * B, B = p // n_A
    p = np.array([np.sum(np.abs(psi_prime[i::n_A])**2) for i in range(n_A)])
    s_sq = s ** 2
    return p, s_sq


# ============================================================
# OFFLINE / AER SANITY CHECK
# ============================================================
def offline_check():
    """Verifiziere die Schmidt-Mathematik offline mit statevector (numpy only)."""
    print("=" * 60)
    print("OFFLINE / STATEVECTOR-VERIFIKATION")
    print("=" * 60)
    results = []
    for N in N_VALUES:
        psi, primes, dim, n_qubits = construct_P_N(N)
        n_A = 2 ** (n_qubits // 2)
        n_B = dim // n_A
        s, U, Vh = schmidt_decomposition(psi, n_A, n_B)
        S_vN = von_neumann_entropy(s)

        p, s_sq = verify_statevector(s, U, Vh, psi, n_A, n_B)
        print(f"\nN={N}, n_qubits={n_qubits}, n_A={n_A}, n_B={n_B}")
        print(f"  primes = {primes}")
        print(f"  s_i (Singulärwerte)  = {s}")
        print(f"  s_i^2 (theoretisch)  = {s_sq}")
        print(f"  s_i^2 (verify_statevector) = {p}")
        print(f"  ||diff||: {np.linalg.norm(p - s_sq):.2e}")
        print(f"  S_vN (klassisch):    {S_vN:.6f}")

        results.append({
            "N": N, "primes": primes, "dim": dim, "n_qubits": n_qubits,
            "n_A": n_A, "n_B": n_B, "s": s.tolist(), "s_sq": s_sq.tolist(),
            "S_vN": float(S_vN), "psi_prime": statevector_after_U_A(s, U, psi, n_A, n_B).tolist()
        })

    N_arr = np.array([r['N'] for r in results])
    S_arr = np.array([r['S_vN'] for r in results])
    log_N = np.log(N_arr)
    log_S = np.log(S_arr)
    alpha, log_const = np.polyfit(log_N, log_S, 1)
    print(f"\nSkalierungsexponent alpha (offline) = {alpha:.4f}")
    print(f"  log_const = {log_const:.4f}")
    print(f"  Vergleich: Latorre-Sierra alpha ~ 1, Aer-Wert = 0.27")
    return results, alpha


# ============================================================
# QPU
# ============================================================
def run_on_qpu(offline_results, alpha_offline, token):
    """Submidiere initialize(psi_prime) + Sampler-Messung an Fez/TOKEN2."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend(BACKEND)
    print(f"\n[QPU] Backend: {BACKEND}, queue={backend.status().pending_jobs}")

    sampler = SamplerV2(backend)
    sampler.options.default_shots = SHOTS
    sampler.options.resilience_level = 0
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)

    qpu_results = []
    for r in offline_results:
        N = r['N']
        n_qubits = r['n_qubits']
        n_A = r['n_A']
        n_B = r['n_B']
        psi_prime = np.array(r['psi_prime'], dtype=complex)

        print(f"\n[QPU] N={N}, n_qubits={n_qubits}")

        # Verifikation: statevector-p vs s_i^2 (Qiskit-statevector-Index p = A + n_A*B)
        p_statevec = np.array([np.sum(np.abs(psi_prime[i::n_A])**2) for i in range(n_A)])
        s_sq = np.array(r['s_sq'])
        print(f"  P(|i>_A) statevector = {p_statevec}")
        print(f"  s_i^2 theoretisch    = {s_sq}")

        # === Schaltung: initialize(psi_prime) + measure System A ===
        qc = QuantumCircuit(n_qubits, n_A.bit_length() - 1)  # n_A_qubits classical
        qc.initialize(psi_prime, range(n_qubits))
        n_A_qubits = int(math.log2(n_A))
        qc.measure(range(n_A_qubits), range(n_A_qubits))

        # Verifikation: statevector sollte Populationen p_statevec zeigen
        sv_check = Statevector.from_instruction(qc.remove_final_measurements(inplace=False))
        pop_check = np.array([abs(sv_check.data[i::n_A])**2 for i in range(n_A)])
        p_check = np.array([pop_check[i].sum() for i in range(n_A)])
        print(f"  P(|i>_A) qiskit sv   = {p_check}")
        print(f"  ||diff sv - np||: {np.linalg.norm(p_check - p_statevec):.2e}")

        # Submit
        isa_qc = pm.run(qc)
        job = sampler.run([isa_qc], shots=SHOTS)
        result = job.result()
        pub_result = result[0]
        if hasattr(pub_result.data, 'c'):
            counts = pub_result.data.c.get_counts()
        else:
            counts = {}
            for key, val in pub_result.quasi_dists[0].items():
                counts[format(int(key), f'0{n_A_qubits}b')] = int(val * SHOTS)

        # Schmidt-Populationen aus QPU-Counts
        s_sq_qpu = np.array([counts.get(format(i, f'0{n_A_qubits}b'), 0) / SHOTS
                             for i in range(n_A)])

        # Verschränkungsentropie
        s_sq_qpu_norm = s_sq_qpu / max(s_sq_qpu.sum(), 1e-12)
        s_sq_qpu_nonzero = s_sq_qpu_norm[s_sq_qpu_norm > 1e-12]
        S_vN_qpu = -np.sum(s_sq_qpu_nonzero * np.log(s_sq_qpu_nonzero))

        print(f"  s_i^2 QPU gemessen  = {s_sq_qpu}")
        print(f"  S_vN QPU            = {S_vN_qpu:.4f}")
        print(f"  S_vN klassisch      = {r['S_vN']:.4f}")
        print(f"  ||abs error||:      {abs(S_vN_qpu - r['S_vN']):.4f}")

        qpu_results.append({
            "N": N, "n_A": n_A, "n_B": n_B, "n_qubits": n_qubits,
            "s_sq_theoretical": s_sq.tolist(),
            "s_sq_qpu": s_sq_qpu.tolist(),
            "S_vN_classical": r['S_vN'],
            "S_vN_qpu": float(S_vN_qpu),
            "abs_error": float(abs(S_vN_qpu - r['S_vN']))
        })

    # Skalierungsexponent
    N_arr = np.array([r['N'] for r in qpu_results])
    S_arr = np.array([r['S_vN_qpu'] for r in qpu_results])
    log_N = np.log(N_arr)
    log_S = np.log(S_arr)
    alpha_qpu, _ = np.polyfit(log_N, log_S, 1)

    print(f"\n{'='*60}")
    print(f"VERGLEICH: alpha-Werte")
    print(f"  alpha_offline (statevector) = {alpha_offline:.4f}")
    print(f"  alpha_AER                   = 0.27")
    print(f"  alpha_QPU (Fez/TOKEN2)      = {alpha_qpu:.4f}")
    print(f"  alpha_Latorre-Sierra        = ~1.0")
    print(f"  Konsistenz QPU <-> Latorre: "
          f"{'JA' if abs(alpha_qpu - 1) < 0.3 else 'NEIN (DISSENS wie Aer)'}")
    print(f"{'='*60}")

    return qpu_results, alpha_qpu


# ============================================================
# HAUPTPROGRAMM
# ============================================================
def main():
    # 1. Offline / statevector
    offline_results, alpha_offline = offline_check()

    # 2. QPU (optional, nur wenn --qpu Flag)
    if "--qpu" not in sys.argv:
        print("\n[Fertig ohne QPU-Submission. Für Fez/TOKEN2: --qpu Flag]")
        with open("pt_prime_state_offline_results.json", "w") as f:
            json.dump({
                "alpha_offline": float(alpha_offline),
                "results": [{k: v for k, v in r.items() if k != 'psi_prime'}
                            for r in offline_results]
            }, f, indent=2)
        return

    token = os.environ.get("QISKIT_IBM_TOKEN")
    if not token:
        try:
            token = open(".env").read().split("IBMQ_TOKEN2=")[1].split("\n")[0]
        except (FileNotFoundError, IndexError):
            raise ValueError("QISKIT_IBM_TOKEN oder .env IBMQ_TOKEN2 nicht gefunden")

    qpu_results, alpha_qpu = run_on_qpu(offline_results, alpha_offline, token)

    with open("pt_prime_state_qpu_singleshot_results.json", "w") as f:
        json.dump({
            "backend": BACKEND,
            "shots": SHOTS,
            "alpha_offline": float(alpha_offline),
            "alpha_qpu": float(alpha_qpu),
            "results": qpu_results
        }, f, indent=2)
    print(f"\nErgebnisse: pt_prime_state_qpu_singleshot_results.json")


if __name__ == "__main__":
    main()
