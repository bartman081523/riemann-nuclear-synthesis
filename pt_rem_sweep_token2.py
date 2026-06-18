"""
pt_rem_sweep_token2.py - Readout-Error-Mitigation Test auf Fez/TOKEN2.

Prereg: pt_rem_prereg.json
Strategie: 2 Jobs (n=2, RL=1) — (a) ohne REM, (b) mit REM via MeasurementMitigation.
Trennt Gate-Bias (von ZNE eliminiert) von Readout-Bias (von REM eliminiert).
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


def submit_rem_job(use_rem, label, service, backend, pm, ansatz, theta, pauli_A):
    from qiskit_ibm_runtime import EstimatorV2 as Estimator

    isa_ansatz = pm.run(ansatz)
    isa_A = pauli_A.apply_layout(isa_ansatz.layout)

    estimator = Estimator(mode=backend)
    estimator.options.resilience_level = 1  # Gate-Error-Mitigation aus
    # Readout-Error-Mitigation
    if use_rem:
        try:
            from qiskit_ibm_runtime.options import ResilienceOptionsV2
            # REM via T-REx: twirled readout
            estimator.options.resilience.measure_mitigation = True
        except Exception as e:
            print(f"  Warning: could not set measure_mitigation: {e}")
    try:
        estimator.options.dynamical_decoupling.enable = True
        estimator.options.dynamical_decoupling.sequence_type = "XX"
    except Exception as e:
        print(f"  Warning: {e}")
    estimator.options.default_shots = SHOTS

    job = estimator.run([(isa_ansatz, isa_A, theta)])
    print(f"  Estimator Job ID (REM={use_rem}, {label}): {job.job_id()}")
    return {
        "use_rem": use_rem,
        "label": label,
        "estimator_job_id": job.job_id(),
    }


def main():
    print("=" * 70)
    print("REM-TEST QPU-SWEEP auf Fez/TOKEN2")
    print("=" * 70)
    print(f"Backend: {BACKEND_NAME}, n={N_QUBITS}")
    print(f"Prereg: pt_rem_prereg.json")
    print("=" * 70)

    with open("pt_rem_prereg.json") as f:
        prereg = json.load(f)
    print(f"\nPrereg hypotheses: {list(prereg['hypotheses'].keys())}")

    tok = load_token(TOKEN_NAME)
    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok, instance=INSTANCE)
    backend = service.backend(BACKEND_NAME)
    print(f"Connected: {BACKEND_NAME} ({backend.num_qubits} qubits, status={backend.status().status_msg})")

    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)

    ansatz = n_local_fn(N_QUBITS, 'ry', 'cx', 'linear', reps=1)
    n_params = ansatz.num_parameters
    theta = [INITIAL[i % len(INITIAL)] for i in range(n_params)]
    A_obs = build_observable_A(N_QUBITS)
    pauli_A = SparsePauliOp.from_operator(Operator(A_obs))

    job_records = []
    t0 = time.time()
    # 1. Job: ohne REM (Referenz = §10.12 RL=1)
    print(f"\n--- Sweep no-REM (Ref) ---")
    rec1 = submit_rem_job(False, "norem", service, backend, pm, ansatz, theta, pauli_A)
    job_records.append(rec1)
    # 2. Job: mit REM
    print(f"\n--- Sweep with-REM ---")
    rec2 = submit_rem_job(True, "rem", service, backend, pm, ansatz, theta, pauli_A)
    job_records.append(rec2)

    out = {
        "prereg_file": "pt_rem_prereg.json",
        "backend": BACKEND_NAME,
        "n_qubits": N_QUBITS,
        "gamma": GAMMA,
        "shots": SHOTS,
        "method": "2 sequenzielle Estimator-Jobs (no-REM vs REM) auf n=2 Jacobi-Block",
        "jobs": job_records,
        "submission_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(t0)),
        "status": "submitted",
    }
    out_file = "pt_rem_token2_job_ids.json"
    with open(out_file, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nJob IDs saved: {out_file}")


if __name__ == "__main__":
    main()
