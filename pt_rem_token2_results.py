"""
pt_rem_token2_results.py - REM-Test QPU-Results + Vergleich.
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
    with open("pt_rem_token2_job_ids.json") as f:
        data = json.load(f)
    jobs = data["jobs"]
    tok = load_token(TOKEN_NAME)
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok, instance=INSTANCE)
    qpu_a = {}
    for rec in jobs:
        use_rem = rec["use_rem"]
        est_id = rec["estimator_job_id"]
        job = service.job(est_id)
        print(f"[REM={use_rem}] Estimator {est_id} status={job.status()}")
        result = job.result()
        pub = result[0]
        qpu_a[use_rem] = float(pub.data.evs)
        print(f"  QPU-<A> (REM={use_rem}) = {qpu_a[use_rem]:.6f}")
    return qpu_a, data


def main():
    print("=" * 70)
    print("REM-TEST QPU-RESULTS Fez/TOKEN2")
    print("=" * 70)

    qpu_a, sweep_data = fetch_results()

    # Statevector reference
    n = 2
    INITIAL = [0.523, 1.21, -0.45, 0.88]
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
    sv_a = float(sv.expectation_value(A_pauli))
    print(f"\nStatevector <A> = {sv_a:.6f}")

    # Biases
    bias_norem = qpu_a[False] - sv_a
    bias_rem = qpu_a[True] - sv_a
    abs_bias_norem = abs(bias_norem)
    abs_bias_rem = abs(bias_rem)
    print(f"Bias (no-REM):  {bias_norem:+.6f}, |Bias|: {abs_bias_norem:.4f}")
    print(f"Bias (REM):     {bias_rem:+.6f}, |Bias|: {abs_bias_rem:.4f}")

    # Hypothesen
    h_pass = abs_bias_rem < 0.025
    print(f"\nH_REM_Reduziert_Bias: |bias_REM| < 0.025 -> {'PASS' if h_pass else 'FAIL'}")

    # Vergleich mit ZNE
    with open("pt_qec_bias_token2_results.json") as f:
        zne_data = json.load(f)
    zne_bias = zne_data["abs_biases"][2]
    zne_ratio = zne_data["ratio_RL2_vs_RL1"]
    print(f"\nZum Vergleich: ZNE (RL=2) |Bias| = {zne_bias:.4f} (3.1x Reduktion vs no-REM)")
    print(f"  REM:        |Bias| = {abs_bias_rem:.4f}")
    rem_vs_norem = abs_bias_norem / abs_bias_rem if abs_bias_rem > 0 else float('inf')
    print(f"  REM vs no-REM Reduktions-Faktor: {rem_vs_norem:.2f}x")

    # Save
    results = {
        "prereg_file": "pt_rem_prereg.json",
        "qpu_A_noREM": qpu_a[False],
        "qpu_A_REM": qpu_a[True],
        "sv_A": sv_a,
        "bias_noREM": bias_norem,
        "bias_REM": bias_rem,
        "abs_bias_noREM": abs_bias_norem,
        "abs_bias_REM": abs_bias_rem,
        "REM_reduction_factor": rem_vs_norem,
        "ZNE_comparison": {
            "ZNE_abs_bias": zne_bias,
            "ZNE_reduction_factor": zne_ratio,
        },
        "H_REM_Reduziert_Bias": {
            "test": "|bias_REM| < 0.025",
            "PASS": bool(h_pass),
        },
        "sweep_metadata": sweep_data,
        "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    }
    out_file = "pt_rem_token2_results.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*70}")
    print(f"H_REM_Reduziert_Bias: {'PASS' if h_pass else 'FAIL'}")
    print(f"Results saved: {out_file}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
