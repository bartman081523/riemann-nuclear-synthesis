"""
pt_spectral_scaling_rl2_sweep_token2.py - Spectral-Scaling Re-Run mit RL=2.

Prereg: pt_spectral_scaling_rl2_prereg.json
Strategie: 3 sequenzielle Jobs (n=2,3,4) mit resilience_level=2 (ZNE).
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
N_QUBITS_LIST = [2, 3, 4]
RESILIENCE_LEVEL = 2
BACKEND_NAME = "ibm_fez"
INSTANCE = "open-instance"
TOKEN_NAME = "IBMQ_TOKEN2"


def build_observable_A(n):
    x_levels = E_DIAG[:n]
    A_nxn = jacobi_A(x_levels, y=1.0)
    dim = 2 ** n
    A_obs = np.zeros((dim, dim))
    A_obs[:n, :n] = A_nxn
    return A_obs


def submit_spectral_job_rl2(n_qubits, label, service, backend, pm, ansatz, theta, pauli_A):
    from qiskit_ibm_runtime import EstimatorV2 as Estimator

    isa_ansatz = pm.run(ansatz)
    isa_A = pauli_A.apply_layout(isa_ansatz.layout)

    estimator = Estimator(mode=backend)
    estimator.options.resilience_level = RESILIENCE_LEVEL
    try:
        estimator.options.dynamical_decoupling.enable = True
        estimator.options.dynamical_decoupling.sequence_type = "XX"
    except Exception as e:
        print(f"  Warning: {e}")
    estimator.options.default_shots = SHOTS

    job = estimator.run([(isa_ansatz, isa_A, theta)])
    print(f"  Estimator Job ID (n={n_qubits}, RL={RESILIENCE_LEVEL}, {label}): {job.job_id()}")
    return {
        "n_qubits": n_qubits,
        "label": label,
        "estimator_job_id": job.job_id(),
        "resilience_level": RESILIENCE_LEVEL,
    }


def main():
    print("=" * 70)
    print("SPECTRAL-SCALING RL=2 RE-RUN auf Fez/TOKEN2")
    print("=" * 70)
    print(f"Backend: {BACKEND_NAME}, n_qubits: {N_QUBITS_LIST}, RL={RESILIENCE_LEVEL}")
    print(f"Prereg: pt_spectral_scaling_rl2_prereg.json")
    print("=" * 70)

    with open("pt_spectral_scaling_rl2_prereg.json") as f:
        prereg = json.load(f)
    print(f"\nPrereg hypotheses: {list(prereg['hypotheses'].keys())}")

    tok = load_token(TOKEN_NAME)
    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok, instance=INSTANCE)
    backend = service.backend(BACKEND_NAME)
    print(f"Connected: {BACKEND_NAME} ({backend.num_qubits} qubits, status={backend.status().status_msg})")

    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)

    INITIAL = [0.523, 1.21, -0.45, 0.88]
    pauli_A_by_n = {}
    for n in N_QUBITS_LIST:
        A_obs = build_observable_A(n)
        pauli_A_by_n[n] = SparsePauliOp.from_operator(Operator(A_obs))

    job_records = []
    t0 = time.time()
    for n in N_QUBITS_LIST:
        print(f"\n--- Sweep n_qubits={n} ---")
        ansatz = n_local_fn(n, 'ry', 'cx', 'linear', reps=1)
        n_params = ansatz.num_parameters
        theta = [INITIAL[i % len(INITIAL)] for i in range(n_params)]
        rec = submit_spectral_job_rl2(n, f"n{n}_rl2", service, backend, pm, ansatz, theta, pauli_A_by_n[n])
        job_records.append(rec)

    out = {
        "prereg_file": "pt_spectral_scaling_rl2_prereg.json",
        "backend": BACKEND_NAME,
        "instance": INSTANCE,
        "token": TOKEN_NAME,
        "gamma": GAMMA,
        "shots": SHOTS,
        "resilience_level": RESILIENCE_LEVEL,
        "n_qubits_list": N_QUBITS_LIST,
        "method": "3 sequenzielle Estimator-Jobs (n=2,3,4) mit RL=2 (ZNE) auf Fez/TOKEN2",
        "jobs": job_records,
        "submission_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(t0)),
        "status": "submitted",
    }
    out_file = "pt_spectral_scaling_rl2_token2_job_ids.json"
    with open(out_file, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nJob IDs saved: {out_file}")


if __name__ == "__main__":
    main()
