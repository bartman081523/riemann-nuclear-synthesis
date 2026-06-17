"""
pt_qber_token2_results.py - Fetch results and compute Pearson correlation.

Liest pt_qber_token2_job_ids.json, holt Estimator + Sampler Results,
berechnet Im_bias und QBER pro Sweep, und Pearson rho(QBER, Im_bias).
"""
import json
import sys
import time
import numpy as np
from pt_token_diagnose import load_token
from qiskit_ibm_runtime import QiskitRuntimeService

TOKEN_NAME = "IBMQ_TOKEN2"
INSTANCE = "open-instance"
BACKEND_NAME = "ibm_fez"
SHOTS = 4096


def fetch_results():
    with open("pt_qber_token2_job_ids.json") as f:
        data = json.load(f)
    jobs = data["jobs"]
    theta_labels = data["theta_labels"]
    n_theta = data["n_theta"]

    tok = load_token(TOKEN_NAME)
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok, instance=INSTANCE)
    backend = service.backend(BACKEND_NAME)

    im_biases_qpu = []
    qbers = []

    for idx, job_rec in enumerate(jobs):
        label = job_rec["theta_label"]
        est_id = job_rec["estimator_job_id"]
        samp_id = job_rec["sampler_job_id"]

        # === Estimator: Im(H_PT) ===
        job_est = service.job(est_id)
        print(f"[{idx+1}/{n_theta}] {label}: Estimator {est_id} status={job_est.status()}")
        result_est = job_est.result()
        # EstimatorV2: pub_result.data.evs is the expectation value
        pub_result = result_est[0]
        im_qpu = float(pub_result.data.evs)
        im_biases_qpu.append(im_qpu)
        print(f"  Im(H_PT) QPU = {im_qpu:.6f}")

        # === Sampler: QBER ===
        job_samp = service.job(samp_id)
        print(f"  Sampler {samp_id} status={job_samp.status()}")
        result_samp = job_samp.result()
        # SamplerV2: pub_result.data.meas is the counts (or BitArray)
        pub_result_s = result_samp[0]
        # Get counts
        try:
            counts = pub_result_s.data.meas.get_counts()
        except AttributeError:
            counts = pub_result_s.data.c.get_counts()
        total = sum(counts.values())
        correct = counts.get('00', 0)
        qber = 1.0 - correct / total
        qbers.append(qber)
        print(f"  QBER = {qber:.4f} ({correct}/{total} '00')")

    return theta_labels, im_biases_qpu, qbers, data


def main():
    print("=" * 70)
    print("QBER-vs-Im_bias RESULTS Fez/TOKEN2")
    print("=" * 70)

    theta_labels, im_qpu, qbers, sweep_data = fetch_results()
    n = len(theta_labels)

    # === Load statevector reference ===
    with open("pt_im_bias_statevector_results.json") as f:
        sv = json.load(f)
    im_sv = sv["Im_statevector"]

    # === Im_bias (QPU - statevector) ===
    im_biases = [q - s for q, s in zip(im_qpu, im_sv)]
    abs_biases = [abs(b) for b in im_biases]

    # === Pearson correlation QBER vs Im_bias ===
    qber_array = np.array(qbers)
    bias_array = np.array(im_biases)
    if np.std(qber_array) > 0 and np.std(bias_array) > 0:
        rho = float(np.corrcoef(qber_array, bias_array)[0, 1])
    else:
        rho = float('nan')

    # === Preregistered decision rule ===
    # H_Noise_Driven: rho > 0.5
    # H_Bias_Driven:  |rho| < 0.3
    # AMBIGUOUS: 0.3 <= |rho| <= 0.5
    if not np.isnan(rho):
        if abs(rho) < 0.3:
            verdict = "H_Bias_Driven"
        elif abs(rho) > 0.5:
            verdict = "H_Noise_Driven"
        else:
            verdict = "AMBIGUOUS"
    else:
        verdict = "UNDEFINED"

    # === Save results ===
    results = {
        "prereg_file": "pt_qber_prereg.json",
        "theta_labels": theta_labels,
        "im_qpu": im_qpu,
        "im_statevector": im_sv,
        "im_biases": im_biases,
        "abs_biases": abs_biases,
        "qbers": qbers,
        "pearson_rho_qber_vs_imbias": rho,
        "verdict": verdict,
        "sweep_metadata": sweep_data.get("jobs", []),
        "submission_timestamp": sweep_data.get("submission_timestamp"),
        "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    }
    out_file = "pt_qber_token2_results.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*70}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*70}")
    print(f"Theta labels: {theta_labels}")
    print(f"Im_bias:      {[f'{b:+.4f}' for b in im_biases]}")
    print(f"|Im_bias|:    {[f'{b:.4f}' for b in abs_biases]}")
    print(f"QBER:         {[f'{q:.4f}' for q in qbers]}")
    print(f"")
    print(f"Pearson rho(QBER, Im_bias) = {rho:.4f}")
    print(f"Verdict: {verdict}")
    print(f"")
    if verdict == "H_Bias_Driven":
        print(f"INTERPRETATION: Im_bias is NOT driven by hardware noise (QBER).")
        print(f"Im_bias is algorithm-/ansatz-driven and irreducible by QEC.")
    elif verdict == "H_Noise_Driven":
        print(f"INTERPRETATION: Im_bias IS driven by hardware noise (QBER).")
        print(f"Im_bias could potentially be reduced by stronger error mitigation.")
    elif verdict == "AMBIGUOUS":
        print(f"INTERPRETATION: Correlation in 0.3-0.5 range. Need more data points.")
    print(f"\nResults saved: {out_file}")


if __name__ == "__main__":
    main()
