"""
pt_qec_bias_token2_results.py - QEC-Bias-Test QPU-Results + Analyse.

Liest pt_qec_bias_token2_job_ids.json, holt Estimator-Results, vergleicht
Bias über resilience_level=1 vs resilience_level=2 (Zero-Noise Extrapolation).
"""
import json
import time
import numpy as np
from pt_token_diagnose import load_token
from qiskit_ibm_runtime import QiskitRuntimeService

TOKEN_NAME = "IBMQ_TOKEN2"
INSTANCE = "open-instance"
BACKEND_NAME = "ibm_fez"


def fetch_results():
    with open("pt_qec_bias_token2_job_ids.json") as f:
        data = json.load(f)
    jobs = data["jobs"]

    tok = load_token(TOKEN_NAME)
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok, instance=INSTANCE)

    qpu_a = {}
    for rec in jobs:
        rl = rec["resilience_level"]
        est_id = rec["estimator_job_id"]
        job = service.job(est_id)
        print(f"[RL={rl}] Estimator {est_id} status={job.status()}")
        result = job.result()
        pub = result[0]
        a_qpu = float(pub.data.evs)
        qpu_a[rl] = a_qpu
        print(f"  QPU-<A> (RL={rl}) = {a_qpu:.6f}")

    return qpu_a, data


def main():
    print("=" * 70)
    print("QEC-BIAS-TEST QPU-RESULTS Fez/TOKEN2")
    print("=" * 70)

    qpu_a, sweep_data = fetch_results()

    # === Statevector reference ===
    from pt_structural import jacobi_A, E_DIAG
    from qiskit.circuit.library import n_local as n_local_fn
    from qiskit.quantum_info import Statevector, SparsePauliOp
    n = 2
    ansatz = n_local_fn(n, 'ry', 'cx', 'linear', reps=1)
    n_params = ansatz.num_parameters
    INITIAL = [0.523, 1.21, -0.45, 0.88]
    theta = [INITIAL[i % len(INITIAL)] for i in range(n_params)]
    bound = ansatz.assign_parameters(theta)
    sv = Statevector.from_instruction(bound)
    x_levels = E_DIAG[:n]
    A_nxn = jacobi_A(x_levels, y=1.0)
    dim = 2 ** n
    A_obs = np.zeros((dim, dim))
    A_obs[:n, :n] = A_nxn
    A_pauli = SparsePauliOp.from_operator(A_obs)
    sv_a = float(sv.expectation_value(A_pauli))
    print(f"\nStatevector <A> = {sv_a:.6f}")

    # === Bias pro RL ===
    biases = {rl: qpu_a[rl] - sv_a for rl in [1, 2]}
    abs_biases = {rl: abs(b) for rl, b in biases.items()}
    print(f"\nBiases: {biases}")
    print(f"|Bias|: {abs_biases}")

    # === Ratio Test ===
    if abs_biases[1] > 0:
        ratio = abs_biases[2] / abs_biases[1]
    else:
        ratio = float('inf')

    if ratio < 0.5:
        verdict = "H_QEC_Eliminates_Bias"
        implication = "QEC (ZNE) reduziert Bias um >= 2x. QPU-Bias ist depolarisierungsdominiert."
    elif ratio <= 2.0:
        verdict = "H_QEC_NoEffect"
        implication = "QEC hat keinen signifikanten Effekt. QPU-Bias ist algorithmus-dominiert. QBER-Studie §10.10 doppelt bestätigt."
    else:
        verdict = "H_QEC_Amplifies_Bias"
        implication = "QEC amplifiziert Bias. QEC fügt systematischen Fehler hinzu."

    print(f"\nratio = |bias_RL2| / |bias_RL1| = {ratio:.4f}")
    print(f"Verdict: {verdict}")

    # === Save results ===
    results = {
        "prereg_file": "pt_qec_bias_prereg.json",
        "qpu_A_per_RL": qpu_a,
        "sv_A": sv_a,
        "biases": biases,
        "abs_biases": abs_biases,
        "ratio_RL2_vs_RL1": ratio,
        "verdict": verdict,
        "implication": implication,
        "sweep_metadata": sweep_data,
        "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    }
    out_file = "pt_qec_bias_token2_results.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*70}")
    print(f"VERDICT: {verdict}")
    print(f"  ratio = {ratio:.4f}")
    print(f"  {implication}")
    print(f"Results saved: {out_file}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
