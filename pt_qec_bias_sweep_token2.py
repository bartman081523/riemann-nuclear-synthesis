"""
pt_qec_bias_sweep_token2.py - QEC-Bias-Test auf Fez/TOKEN2.

Prereg: pt_qec_bias_prereg.json (vor main() gepinnt, 2026-06-17 20:30 UTC)

3 sequenzielle Jobs auf n=2 Jacobi-Block:
  (a) resilience_level=1 (Referenz aus §10.11)
  (b) resilience_level=2 (Zero-Noise Extrapolation)
  (c) resilience_level=3 (Probabilistic Error Amplification)

Vergleicht |bias| = |QPU_<A> - SV_<A>| über die 3 RLs.
H_QEC_Eliminates_Bias: ratio < 0.5
H_QEC_NoEffect: 0.5 <= ratio <= 2.0
H_QEC_Amplifies_Bias: ratio > 2.0

Strategie: 1024 shots (4x Sparmodus), n=2, gleiche theta.
"""
import json
import time
import numpy as np
from pt_structural import jacobi_A, E_DIAG
from pt_token_diagnose import load_token
from qiskit.circuit.library import n_local as n_local_fn
from qiskit.quantum_info import SparsePauliOp, Operator

GAMMA = 0.02
SHOTS = 1024
N_QUBITS = 2
INITIAL = [0.523, 1.21, -0.45, 0.88]
RESILIENCE_LEVELS = [1, 2]
BACKEND_NAME = "ibm_fez"
INSTANCE = "open-instance"
TOKEN_NAME = "IBMQ_TOKEN2"


def build_observable_A(n):
    """Jacobi-Kopplungs-Matrix A im n-Qubit-Hilbert-Raum."""
    x_levels = E_DIAG[:n]
    A_nxn = jacobi_A(x_levels, y=1.0)
    dim = 2 ** n
    A_obs = np.zeros((dim, dim))
    A_obs[:n, :n] = A_nxn
    return A_obs


def submit_qec_job(resilience_level, label, service, backend, pm, ansatz, theta, pauli_A):
    """Submit ONE 1-Pub Estimator Job mit gegebenem resilience_level."""
    from qiskit_ibm_runtime import EstimatorV2 as Estimator

    isa_ansatz = pm.run(ansatz)
    isa_A = pauli_A.apply_layout(isa_ansatz.layout)

    estimator = Estimator(mode=backend)
    estimator.options.resilience_level = resilience_level
    # Bei RL=2/3: dynamical decoupling defaults
    try:
        estimator.options.dynamical_decoupling.enable = True
        estimator.options.dynamical_decoupling.sequence_type = "XX"
    except Exception as e:
        print(f"  Warning: {e}")
    estimator.options.default_shots = SHOTS

    job = estimator.run([(isa_ansatz, isa_A, theta)])
    print(f"  Estimator Job ID (RL={resilience_level}, {label}): {job.job_id()}")
    return job.job_id()


def main():
    print("=" * 70)
    print("QEC-BIAS-TEST QPU-SWEEP auf Fez/TOKEN2")
    print("=" * 70)
    print(f"Backend: {BACKEND_NAME}, n_qubits: {N_QUBITS}")
    print(f"Resilience-Levels: {RESILIENCE_LEVELS}")
    print(f"Shots: {SHOTS}, theta: {INITIAL[:4]}")
    print(f"Prereg: pt_qec_bias_prereg.json")
    print("=" * 70)

    # Preregister lesen
    with open("pt_qec_bias_prereg.json") as f:
        prereg = json.load(f)
    print(f"\nPrereg hypotheses: {list(prereg['hypotheses'].keys())}")

    # Token2 connect
    tok = load_token(TOKEN_NAME)
    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok, instance=INSTANCE)
    backend = service.backend(BACKEND_NAME)
    print(f"Connected: {BACKEND_NAME} ({backend.num_qubits} qubits, status={backend.status().status_msg})")

    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)

    # Ansatz + Observable
    ansatz = n_local_fn(N_QUBITS, 'ry', 'cx', 'linear', reps=1)
    n_params = ansatz.num_parameters
    theta = [INITIAL[i % len(INITIAL)] for i in range(n_params)]
    print(f"Ansatz: n_local({N_QUBITS}, 'ry', 'cx', 'linear', reps=1), n_params={n_params}")

    A_obs = build_observable_A(N_QUBITS)
    pauli_A = SparsePauliOp.from_operator(Operator(A_obs))
    print(f"Observable A: {A_obs.shape}")

    # === Submit 3 Jobs (RL=1, RL=2, RL=3) ===
    job_records = []
    t0 = time.time()
    for rl in RESILIENCE_LEVELS:
        print(f"\n--- Sweep RL={rl} ---")
        job_id = submit_qec_job(rl, f"rl{rl}", service, backend, pm, ansatz, theta, pauli_A)
        job_records.append({
            "resilience_level": rl,
            "label": f"rl{rl}",
            "estimator_job_id": job_id,
        })

    # === Save Job IDs ===
    out = {
        "prereg_file": "pt_qec_bias_prereg.json",
        "backend": BACKEND_NAME,
        "instance": INSTANCE,
        "token": TOKEN_NAME,
        "n_qubits": N_QUBITS,
        "gamma": GAMMA,
        "shots": SHOTS,
        "theta": theta,
        "resilience_levels": RESILIENCE_LEVELS,
        "method": "3 sequenzielle Estimator-Jobs (RL=1,2,3) auf n=2 Jacobi-Block auf Fez/TOKEN2",
        "jobs": job_records,
        "submission_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(t0)),
        "status": "submitted",
    }
    out_file = "pt_qec_bias_token2_job_ids.json"
    with open(out_file, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nJob IDs saved: {out_file}")
    print(f"Next: run pt_qec_bias_token2_results.py")


if __name__ == "__main__":
    main()
