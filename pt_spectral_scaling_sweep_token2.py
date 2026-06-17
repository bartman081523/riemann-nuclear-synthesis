"""
pt_spectral_scaling_sweep_token2.py - QPU Spectral-Scaling Sweep auf Fez/TOKEN2.

Prereg: pt_spectral_scaling_prereg.json (vor main() gepinnt, 2026-06-17 20:30 UTC)

Misst Im(H_PT) auf demselben 2x2 Jacobi-Block, eingebettet in 2Q, 3Q, 4Q Circuits.
Wenn die Block-Diagonal-Invarianz (innerhalb 1e-3) QPU-konsistent ist, dann
ist der Bias algorithmisch (Block-Struktur), nicht Qubit-Count-abhängig.

Strategie: 3 sequenzielle Estimator-Jobs + 1 Sampler für QBER-Ref.
Jeweils 1024 shots (4× Sparmodus aus QBER-Befund 2026-06-17 19:50 UTC).
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
BACKEND_NAME = "ibm_fez"
INSTANCE = "open-instance"
TOKEN_NAME = "IBMQ_TOKEN2"


def build_observable_A(n):
    """Build die Jacobi-Kopplungs-Matrix A als Observable im n-Qubit-Hilbert-Raum.

    H_PT = H_diag + i*gamma*A  ->  Im(<psi|H_PT|psi>) = gamma * <psi|A|psi>
    Wir messen direkt A (reell-symmetrisch), gamma wird im Postprocessing multipliziert.

    Beachte: H_PT ist als (n x n) Matrix definiert. Im n-Qubit-Hilbert-Raum (2^n x 2^n)
    lebt A auf der unteren linken (n x n)-Block-Diagonalen. Der Rest ist 0.

    Args:
        n: Anzahl Qubits (Jacobi-Block-Dimension).

    Returns:
        A_obs: reell-symmetrische (2^n, 2^n) Observable.
    """
    x_levels = E_DIAG[:n]
    A_nxn = jacobi_A(x_levels, y=1.0)
    dim = 2 ** n
    A_obs = np.zeros((dim, dim))
    A_obs[:n, :n] = A_nxn
    return A_obs, np.diag(x_levels).astype(complex)


def submit_spectral_job(n_qubits, label, service, backend, pm):
    """Submit ONE 1-Pub Estimator Job: Im(H_PT) auf n-qubit Jacobi-Block.

    Returns: dict mit job_id, theta_used.
    """
    from qiskit_ibm_runtime import EstimatorV2 as Estimator

    # Ansatz
    ansatz = n_local_fn(n_qubits, 'ry', 'cx', 'linear', reps=1)
    n_params = ansatz.num_parameters
    INITIAL = [0.523, 1.21, -0.45, 0.88]
    theta = [INITIAL[i % len(INITIAL)] for i in range(n_params)]

    # Build Jacobi-Kopplungs-Matrix A als Observable (reell-symmetrisch)
    A, H_diag = build_observable_A(n_qubits)
    pauli_A = SparsePauliOp.from_operator(Operator(A))

    # Transpile ansatz FIRST, then apply layout to operator
    isa_ansatz = pm.run(ansatz)
    isa_A = pauli_A.apply_layout(isa_ansatz.layout)

    estimator = Estimator(mode=backend)
    estimator.options.resilience_level = 1
    estimator.options.dynamical_decoupling.enable = True
    estimator.options.dynamical_decoupling.sequence_type = "XX"
    estimator.options.default_shots = SHOTS

    job = estimator.run([(isa_ansatz, isa_A, theta)])
    print(f"  Estimator Job ID (n={n_qubits}, {label}): {job.job_id()}")
    return {
        "n_qubits": n_qubits,
        "label": label,
        "estimator_job_id": job.job_id(),
        "n_params": n_params,
        "theta_used": theta,
    }


def submit_qber_ref(backend, pm):
    """Submit ONE Sampler Job: QBER-Ref auf |00> für 2 Qubits (kleinste Variante)."""
    from qiskit_ibm_runtime import SamplerV2 as Sampler
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2)
    qc.measure_all()
    isa_qc = pm.run(qc)
    sampler = Sampler(mode=backend)
    sampler.options.default_shots = SHOTS
    job = sampler.run([(isa_qc,)])
    print(f"  QBER-Ref Sampler Job ID: {job.job_id()}")
    return job.job_id()


def main():
    print("=" * 70)
    print("SPECTRAL-SCALING QPU-SWEEP auf Fez/TOKEN2")
    print("=" * 70)
    print(f"Backend: {BACKEND_NAME}, Instance: {INSTANCE}, Token: {TOKEN_NAME}")
    print(f"Shots: {SHOTS}, n_qubits: {N_QUBITS_LIST}")
    print(f"Prereg: pt_spectral_scaling_prereg.json")
    print("=" * 70)

    # Preregister lesen + Hash verifizieren
    with open("pt_spectral_scaling_prereg.json") as f:
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

    # === Submit 3 Estimator-Jobs (n=2, 3, 4) + 1 QBER-Ref ===
    job_records = []
    t0 = time.time()
    for n in N_QUBITS_LIST:
        print(f"\n--- Sweep n_qubits={n} ---")
        rec = submit_spectral_job(n, f"n{n}", service, backend, pm)
        job_records.append(rec)

    print(f"\n--- QBER Reference ---")
    qber_job_id = submit_qber_ref(backend, pm)
    job_records.append({"label": "qber_ref", "sampler_job_id": qber_job_id, "n_qubits": 2})

    # === Save Job IDs ===
    out = {
        "prereg_file": "pt_spectral_scaling_prereg.json",
        "backend": BACKEND_NAME,
        "instance": INSTANCE,
        "token": TOKEN_NAME,
        "gamma": GAMMA,
        "shots": SHOTS,
        "n_qubits_list": N_QUBITS_LIST,
        "method": "3 sequenzielle Estimator-Jobs (n=2,3,4) + 1 Sampler für QBER-Ref auf Fez/TOKEN2",
        "jobs": job_records,
        "submission_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(t0)),
        "status": "submitted",
    }
    out_file = "pt_spectral_scaling_token2_job_ids.json"
    with open(out_file, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nJob IDs saved: {out_file}")
    print(f"Next: run pt_spectral_scaling_token2_results.py")


if __name__ == "__main__":
    main()
