"""
pt_spectral_scaling_rl2_token2_results.py - RL=2 QPU-Results + Vergleich.
"""
import json
import time
import numpy as np
from pt_token_diagnose import load_token
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit.circuit.library import n_local as n_local_fn
from qiskit.quantum_info import Statevector, SparsePauliOp
from pt_structural import jacobi_A, E_DIAG

TOKEN_NAME = "IBMQ_TOKEN2"
INSTANCE = "open-instance"


def fetch_results():
    with open("pt_spectral_scaling_rl2_token2_job_ids.json") as f:
        data = json.load(f)
    jobs = data["jobs"]
    tok = load_token(TOKEN_NAME)
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok, instance=INSTANCE)
    qpu_a = {}
    for rec in jobs:
        n = rec["n_qubits"]
        est_id = rec["estimator_job_id"]
        job = service.job(est_id)
        print(f"[n={n}] Estimator {est_id} status={job.status()}")
        result = job.result()
        pub = result[0]
        qpu_a[n] = float(pub.data.evs)
        print(f"  QPU-<A> (n={n}, RL=2) = {qpu_a[n]:.6f}")
    return qpu_a, data


def main():
    print("=" * 70)
    print("SPECTRAL-SCALING RL=2 QPU-RESULTS Fez/TOKEN2")
    print("=" * 70)

    qpu_a, sweep_data = fetch_results()

    # Statevector reference (gleiche theta wie §10.11)
    INITIAL = [0.523, 1.21, -0.45, 0.88]
    sv_a = {}
    for n in [2, 3, 4]:
        ansatz = n_local_fn(n, 'ry', 'cx', 'linear', reps=1)
        n_params = ansatz.num_parameters
        theta = [INITIAL[i % len(INITIAL)] for i in range(n_params)]
        bound = ansatz.assign_parameters(theta)
        sv = Statevector.from_instruction(bound)
        x_levels = E_DIAG[:n]
        A_nxn = jacobi_A(x_levels, y=1.0)
        dim = 2 ** n
        A_obs = np.zeros((dim, dim))
        A_obs[:n, :n] = A_nxn
        A_pauli = SparsePauliOp.from_operator(A_obs)
        sv_a[n] = float(sv.expectation_value(A_pauli))
    print(f"\nStatevector <A> (n=2,3,4): {sv_a}")

    # Bias RL=2
    biases = {n: qpu_a[n] - sv_a[n] for n in [2, 3, 4]}
    abs_biases = {n: abs(b) for n, b in biases.items()}
    print(f"Biases (RL=2): {biases}")
    print(f"|Bias| (RL=2): {abs_biases}")

    # Vergleich mit RL=1
    with open("pt_spectral_scaling_token2_results.json") as f:
        rl1_data = json.load(f)
    rl1_qpu_a = {int(k): v for k, v in rl1_data["qpu_A_observable"].items()}
    rl1_biases = {n: rl1_qpu_a[n] - sv_a[n] for n in [2, 3, 4]}
    print(f"\nZum Vergleich: Biases (RL=1): {rl1_biases}")

    # Hypothesen
    max_abs_bias = max(abs_biases.values())
    h1_pass = max_abs_bias < 0.025
    print(f"\nH_Algorithmus_Bias_Klein_nach_QEC: max |bias_RL2| = {max_abs_bias:.4f} -> {'PASS' if h1_pass else 'FAIL'}")

    qpu_values = [qpu_a[n] for n in [2, 3, 4]]
    qpu_mean = float(np.mean(qpu_values))
    qpu_std = float(np.std(qpu_values))
    h2_pass = all(abs(v - qpu_mean) < 2 * qpu_std for v in qpu_values) if qpu_std > 0 else True
    print(f"H_Block_Diag_Invariance_Post_QEC: 2σ-Band [{qpu_mean - 2*qpu_std:.4f}, {qpu_mean + 2*qpu_std:.4f}] -> {'PASS' if h2_pass else 'FAIL'}")

    # Save
    results = {
        "prereg_file": "pt_spectral_scaling_rl2_prereg.json",
        "qpu_A_RL2": qpu_a,
        "sv_A": sv_a,
        "biases_RL2": biases,
        "abs_biases_RL2": abs_biases,
        "biases_RL1": rl1_biases,
        "bias_reduction_factor": {n: abs(rl1_biases[n])/abs_biases[n] if abs_biases[n] > 0 else float('inf') for n in [2, 3, 4]},
        "H_Algorithmus_Bias_Klein_nach_QEC": {
            "test": "max_n |bias_RL2_n| < 0.025",
            "max_abs_bias": max_abs_bias,
            "PASS": bool(h1_pass),
        },
        "H_Block_Diag_Invariance_Post_QEC": {
            "test": "QPU-<A>_RL2 in 2σ-Band",
            "values": qpu_values,
            "mean": qpu_mean,
            "std": qpu_std,
            "PASS": bool(h2_pass),
        },
        "sweep_metadata": sweep_data,
        "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    }
    out_file = "pt_spectral_scaling_rl2_token2_results.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*70}")
    print(f"H1: {'PASS' if h1_pass else 'FAIL'}  H2: {'PASS' if h2_pass else 'FAIL'}")
    print(f"Results saved: {out_file}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
