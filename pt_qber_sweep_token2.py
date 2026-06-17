"""
pt_qber_sweep_token2.py - QBER-vs-Im_bias correlation test on Fez/TOKEN2.

Hintergrund: TOKEN2 seit 2026-06-17 17:15 UTC offen.
QPU-Validation der in pt_qber_prereg.json prae-registrierten Hypothesen:

  H_Noise_Driven:  rho(QBER, Im_bias) > 0.5
  H_Bias_Driven:   |rho(QBER, Im_bias)| < 0.3

Strategie: 5 sequenzielle 1-Pub-Jobs, jeder misst (a) Im(H_PT) auf dem
2-Qubit-Ansatz mit theta-Parametern, und (b) QBER auf einem |00>
Reference-Circuit. Beide auf demselben Backend, gleiche Shot-Anzahl,
gleiche Coupling-Map.

Prereg: pt_qber_prereg.json (committed VOR diesem Skript, 2026-06-17 18:35 UTC)
"""
import json
import os
import time
import sys
import numpy as np
from pt_structural import jacobi_A, E_DIAG
from qiskit.circuit.library import n_local as n_local_fn
from qiskit.quantum_info import Statevector, SparsePauliOp, Operator
from pt_token_diagnose import load_token

GAMMA = 0.02
SHOTS = 4096
INITIAL_PARAMS_4 = [0.523, 1.21, -0.45, 0.88]
N_THETA = 5
BACKEND_NAME = "ibm_fez"
INSTANCE = "open-instance"
TOKEN_NAME = "IBMQ_TOKEN2"


def cyclic_extend(params_4, n_target):
    return [params_4[i % len(params_4)] for i in range(n_target)]


def build_im_operator():
    A = jacobi_A(E_DIAG, y=1.0)
    H_diag = np.diag(E_DIAG).astype(complex)
    H_PT = H_diag + 1j * GAMMA * A
    H_imag = (H_PT - H_PT.conj().T) / (2j)
    return H_diag, H_imag


def submit_qber_job(theta_4, label, idx, t0, ansatz, qber_circuit, service, backend, pm, n_params):
    """Submit ONE 1-Pub Job: Im(H_PT) on ansatz + QBER on |00> reference.

    Note: Im(H_PT) uses Estimator; QBER uses Sampler (since it's a
    measurement-only experiment). For efficiency, we use TWO separate
    jobs to keep the protocol simple and minimize QPU time.
    """
    from qiskit_ibm_runtime import EstimatorV2 as Estimator, SamplerV2 as Sampler
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    isa_ansatz = pm.run(ansatz)
    H_diag, H_imag = build_im_operator()
    pauli_imag = SparsePauliOp.from_operator(Operator(H_imag))
    isa_imag = pauli_imag.apply_layout(isa_ansatz.layout)

    # === Estimator job: Im(H_PT) ===
    estimator = Estimator(mode=backend)
    estimator.options.resilience_level = 1
    estimator.options.dynamical_decoupling.enable = True
    estimator.options.dynamical_decoupling.sequence_type = "XX"
    estimator.options.default_shots = SHOTS

    isa_imag_layout = pauli_imag.apply_layout(isa_ansatz.layout)
    theta_cyclic = cyclic_extend(theta_4, n_params)

    job_est = estimator.run([(isa_ansatz, isa_imag_layout, theta_cyclic)])
    print(f"  Estimator Job ID ({label}): {job_est.job_id()}")

    # === Sampler job: QBER on |00> reference ===
    sampler = Sampler(mode=backend)
    sampler.options.default_shots = SHOTS
    isa_qber = pm.run(qber_circuit)
    job_sampler = sampler.run([(isa_qber,)])
    print(f"  Sampler  Job ID ({label}): {job_sampler.job_id()}")

    return {
        "theta_label": label,
        "estimator_job_id": job_est.job_id(),
        "sampler_job_id": job_sampler.job_id(),
        "theta_4": theta_4,
        "theta_used": theta_cyclic,
    }


def main():
    print("=" * 70)
    print("QBER-vs-Im_bias SWEEP auf Fez/TOKEN2")
    print("=" * 70)
    print(f"Backend: {BACKEND_NAME}, Instance: {INSTANCE}")
    print(f"Token: {TOKEN_NAME}, Shots: {SHOTS}")
    print(f"Prereg: pt_qber_prereg.json")
    print(f"Hypothesen: H_Noise_Driven, H_Bias_Driven, H_Qber_Sanity")
    print("=" * 70)

    # === Preregister: load committed prereg ===
    with open("pt_qber_prereg.json") as f:
        prereg = json.load(f)
    print(f"\nPrereg hypotheses loaded: {list(prereg['hypotheses'].keys())}")

    # === Load same theta_values as pt_im_bias_token2 ===
    with open("pt_im_bias_token2_results.json") as f:
        im_data = json.load(f)
    theta_values = im_data.get("theta_values", [])
    theta_labels = im_data.get("theta_labels", [])
    if len(theta_values) != N_THETA:
        print(f"WARNING: expected {N_THETA} theta values, got {len(theta_values)}")
        return

    # === Build ansatz and QBER reference circuit ===
    ansatz = n_local_fn(2, 'ry', 'cx', 'linear', reps=1)
    n_params = ansatz.num_parameters
    print(f"Ansatz: n_local(2, ry, cx, linear, reps=1), n_params = {n_params}")

    qber_circuit = None
    from qiskit import QuantumCircuit
    qber_circuit = QuantumCircuit(2)
    qber_circuit.measure_all()
    print(f"QBER reference: |00> + measure_all (2 qubits)")

    # === Connect to Fez/TOKEN2 ===
    tok = load_token(TOKEN_NAME)
    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok, instance=INSTANCE)
    backend = service.backend(BACKEND_NAME)
    print(f"Connected: {BACKEND_NAME} ({backend.num_qubits} qubits, status={backend.status().status_msg})")

    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)

    # === Submit 5 sequential jobs ===
    job_records = []
    t0 = time.time()
    for idx, (theta_4, label) in enumerate(zip(theta_values, theta_labels)):
        print(f"\n--- Sweep {idx+1}/{N_THETA}: {label} ---")
        rec = submit_qber_job(
            theta_4, label, idx, t0,
            ansatz, qber_circuit,
            service, backend, pm, n_params
        )
        job_records.append(rec)

    # === Save job IDs (do NOT wait for results in this script) ===
    out = {
        "prereg_file": "pt_qber_prereg.json",
        "backend": BACKEND_NAME,
        "instance": INSTANCE,
        "token": TOKEN_NAME,
        "gamma": GAMMA,
        "shots": SHOTS,
        "method": "5 sequenzielle 2-Job-Paare (Estimator + Sampler) auf Fez/TOKEN2",
        "n_theta": N_THETA,
        "theta_labels": theta_labels,
        "theta_values": theta_values,
        "jobs": job_records,
        "submission_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(t0)),
        "status": "submitted",
    }
    out_file = "pt_qber_token2_job_ids.json"
    with open(out_file, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nJob IDs saved: {out_file}")
    print(f"Next: run pt_qber_token2_results.py to fetch results and compute correlation.")


if __name__ == "__main__":
    main()
