"""
SAEULE 3 QPU — Schmidt-Entropie auf Fez/TOKEN2 (konservativ, sequenziell).

ARCHITEKTUR (siehe pt_prime_state_qpu_singleshot.py):
  - psi_prime = (U_A^dagger \otimes I_B) |P_N>  in numpy
  - QPU: initialize(psi_prime) + measure System A
  - P(|i>_A) gemessen = s_i^2 (Schmidt-Koeff.quadrate)
  - S_vN = -sum s_i^2 log(s_i^2)

SUBMISSION-STRATEGIE:
  - 5 sequenzielle 1-Pub-Jobs (1 pro N-Wert), 4096 Shots
  - Fez-Queue typisch 0-15, Gesamtwartezeit + QPU-Zeit: ~3-5 Min
  - Passt ins Tageslimit 10 Min (TOKEN2, neuer Account)

PRE-REGISTRIERUNG: pt_prime_state_prereg.json
  Vergleich: alpha = log(S_vN)/log(N) skaliert mit N
"""
import json
import math
import os
import sys
import time
import numpy as np

sys.path.insert(0, '/run/media/julian/ML4/riemann')
from pt_prime_state_qpu_singleshot import (
    construct_P_N, schmidt_decomposition, von_neumann_entropy,
    statevector_after_U_A
)

BACKEND = "ibm_fez"
N_VALUES = [7, 15, 31, 63, 127]
SHOTS = 4096


def load_token():
    """Lade TOKEN2 aus .env."""
    with open(".env") as f:
        for line in f:
            if line.startswith("IBMQ_TOKEN2="):
                return line.split("=", 1)[1].strip()
    raise ValueError("IBMQ_TOKEN2 nicht in .env")


def main():
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    t0 = time.time()
    print(f"[{time.time()-t0:.0f}s] Starting pt_prime_state_qpu_run.py", flush=True)

    token = load_token()
    print(f"[{time.time()-t0:.0f}s] Token loaded (len={len(token)})", flush=True)

    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend(BACKEND)
    print(f"[{time.time()-t0:.0f}s] Backend: {BACKEND}, queue={backend.status().pending_jobs}", flush=True)

    sampler = SamplerV2(backend)
    sampler.options.default_shots = SHOTS
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)

    # === Pre-Registrierung laden ===
    with open("pt_prime_state_prereg.json") as f:
        prereg = json.load(f)
    print(f"[{time.time()-t0:.0f}s] Praeregistrierung geladen: {prereg['N_sweep']}", flush=True)

    # === Aer-Vorhersage (S_vN, alpha) ===
    S_aer = {r['N']: r['S_vN'] for r in prereg['results']}
    alpha_aer = prereg.get('scaling_analysis', {}).get('alpha', 0.27) if False else 0.27
    # Falls keine scaling_analysis: siehe pt_prime_state_results.json
    try:
        with open("pt_prime_state_results.json") as f:
            alpha_aer = json.load(f)['scaling_analysis']['alpha']
    except (FileNotFoundError, KeyError):
        pass
    print(f"[{time.time()-t0:.0f}s] Aer-Skalierung: alpha_AER = {alpha_aer:.4f}", flush=True)

    # === QPU-Messungen ===
    qpu_results = []
    for N in N_VALUES:
        print(f"\n[{time.time()-t0:.0f}s] === N={N} ===", flush=True)

        # 1. Klassische Schmidt-Zerlegung
        psi, primes, dim, n_qubits = construct_P_N(N)
        n_A = int(math.sqrt(dim))
        while dim % n_A != 0 and n_A > 1:
            n_A -= 1
        n_B = dim // n_A
        s, U, Vh = schmidt_decomposition(psi, n_A, n_B)
        S_vN_classical = von_neumann_entropy(s)
        s_sq = (s ** 2).tolist()

        # 2. Statevector psi_prime (F-order flatten für Qiskit-initialize)
        psi_prime = statevector_after_U_A(s, U, psi, n_A, n_B)

        # 3. Verifiziere statevector-Funktion
        n_A_qubits = int(math.log2(n_A))
        p_check = np.array([np.sum(np.abs(psi_prime[i::n_A])**2) for i in range(n_A)])
        p_theo = np.array(s_sq)
        if np.linalg.norm(p_check - p_theo) > 1e-10:
            raise ValueError(f"Statevector-Verifikation fehlgeschlagen: {p_check} != {p_theo}")
        print(f"[{time.time()-t0:.0f}s] Statevector verifiziert: P(|i>_A) = {p_check}", flush=True)

        # 4. Schaltung bauen
        qc = QuantumCircuit(n_qubits, n_A_qubits)
        qc.initialize(psi_prime, range(n_qubits))
        qc.measure(range(n_A_qubits), range(n_A_qubits))

        # 5. ISA transpilieren
        isa_qc = pm.run(qc)
        print(f"[{time.time()-t0:.0f}s] ISA: depth={isa_qc.depth()}, ops={isa_qc.size()}", flush=True)

        # 6. Submit 1-Pub-Job
        job = sampler.run([isa_qc], shots=SHOTS)
        job_id = job.job_id()
        print(f"[{time.time()-t0:.0f}s] Job submitted: {job_id}", flush=True)

        # 7. Warten auf Result
        result = job.result()
        pub_result = result[0]
        if hasattr(pub_result.data, 'c'):
            counts = pub_result.data.c.get_counts()
        else:
            counts = {}
            for key, val in pub_result.quasi_dists[0].items():
                counts[format(int(key), f'0{n_A_qubits}b')] = int(val * SHOTS)

        print(f"[{time.time()-t0:.0f}s] Counts: {counts}", flush=True)

        # 8. Schmidt-Populationen
        s_sq_qpu = np.array([counts.get(format(i, f'0{n_A_qubits}b'), 0) / SHOTS
                             for i in range(n_A)])

        # 9. S_vN
        s_sq_qpu_norm = s_sq_qpu / max(s_sq_qpu.sum(), 1e-12)
        s_sq_qpu_nz = s_sq_qpu_norm[s_sq_qpu_norm > 1e-12]
        S_vN_qpu = -np.sum(s_sq_qpu_nz * np.log(s_sq_qpu_nz))

        print(f"[{time.time()-t0:.0f}s] N={N}: S_vN_qpu={S_vN_qpu:.4f} (klassisch: {S_vN_classical:.4f})", flush=True)
        print(f"[{time.time()-t0:.0f}s] s_i^2 qpu={s_sq_qpu}", flush=True)
        print(f"[{time.time()-t0:.0f}s] |delta S_vN|: {abs(S_vN_qpu - S_vN_classical):.4f}", flush=True)

        qpu_results.append({
            "N": N, "n_A": n_A, "n_B": n_B, "n_qubits": n_qubits,
            "pi_N": len(primes),
            "job_id": job_id,
            "s_sq_classical": s_sq,
            "s_sq_qpu": s_sq_qpu.tolist(),
            "S_vN_classical": float(S_vN_classical),
            "S_vN_qpu": float(S_vN_qpu),
            "S_vN_aer_prereg": S_aer.get(N, None),
            "abs_error": float(abs(S_vN_qpu - S_vN_classical))
        })

        # Speichere nach jedem N (idempotent)
        with open("pt_prime_state_qpu_singleshot_results.json", "w") as f:
            json.dump({
                "backend": BACKEND,
                "shots": SHOTS,
                "alpha_aer": float(alpha_aer),
                "alpha_latorre_sierra": 1.0,
                "results": qpu_results
            }, f, indent=2)

    # === Skalierungsexponent ===
    N_arr = np.array([r['N'] for r in qpu_results])
    S_arr = np.array([r['S_vN_qpu'] for r in qpu_results])
    log_N = np.log(N_arr)
    log_S = np.log(S_arr)
    alpha_qpu, _ = np.polyfit(log_N, log_S, 1)

    print(f"\n{'='*60}")
    print(f"VERGLEICH ALPHA-WERTE")
    print(f"  alpha_AER                   = {alpha_aer:.4f}")
    print(f"  alpha_QPU (Fez/TOKEN2)      = {alpha_qpu:.4f}")
    print(f"  alpha_Latorre-Sierra        = ~1.0")
    print(f"  Konsistenz QPU <-> Latorre: "
          f"{'JA' if abs(alpha_qpu - 1) < 0.3 else 'NEIN (DISSENS wie Aer)'}")
    print(f"{'='*60}", flush=True)

    # Update mit alpha_qpu
    with open("pt_prime_state_qpu_singleshot_results.json", "w") as f:
        json.dump({
            "backend": BACKEND,
            "shots": SHOTS,
            "alpha_aer": float(alpha_aer),
            "alpha_qpu": float(alpha_qpu),
            "alpha_latorre_sierra": 1.0,
            "verdict": (
                "QPU bestaetigt Aer (DISSENS zu Latorre-Sierra)"
                if abs(alpha_qpu - alpha_aer) < 0.2
                else "QPU widerspricht Aer"
            ),
            "results": qpu_results
        }, f, indent=2)

    print(f"\n[fertig] Laufzeit: {time.time()-t0:.0f}s", flush=True)
    print(f"Ergebnisse: pt_prime_state_qpu_singleshot_results.json", flush=True)


if __name__ == "__main__":
    main()
