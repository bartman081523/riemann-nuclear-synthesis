"""
pt_spectral_scaling_token2_results.py - QPU-Ergebnisse holen + Vergleich.

Liest pt_spectral_scaling_token2_job_ids.json, holt die Estimator- und Sampler-Results,
vergleicht Im(H_PT) auf 2Q, 3Q, 4Q Jacobi-Block-Encodings, prüft H_BlockDiag_Invariance_QPU.
"""
import json
import time
import numpy as np
from pt_token_diagnose import load_token
from qiskit_ibm_runtime import QiskitRuntimeService

TOKEN_NAME = "IBMQ_TOKEN2"
INSTANCE = "open-instance"
BACKEND_NAME = "ibm_fez"
SHOTS = 1024


def fetch_results():
    with open("pt_spectral_scaling_token2_job_ids.json") as f:
        data = json.load(f)
    jobs = data["jobs"]
    n_qubits_list = data["n_qubits_list"]

    tok = load_token(TOKEN_NAME)
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok, instance=INSTANCE)

    # === Estimator results: Im(H_PT) for n=2, 3, 4 ===
    qpu_im = {}
    for rec in jobs:
        if rec.get("label", "").startswith("n"):
            n = rec["n_qubits"]
            label = rec["label"]
            est_id = rec["estimator_job_id"]
            job = service.job(est_id)
            print(f"[n={n}] Estimator {est_id} status={job.status()}")
            result = job.result()
            pub = result[0]
            im_qpu = float(pub.data.evs)
            qpu_im[n] = im_qpu
            print(f"  Im(H_PT) QPU (n={n}) = {im_qpu:.6f}")

    # === Sampler result: QBER ===
    qber = None
    for rec in jobs:
        if rec.get("label") == "qber_ref":
            samp_id = rec["sampler_job_id"]
            job = service.job(samp_id)
            print(f"\n[QBER-Ref] Sampler {samp_id} status={job.status()}")
            result = job.result()
            pub = result[0]
            try:
                counts = pub.data.meas.get_counts()
            except AttributeError:
                counts = pub.data.c.get_counts()
            total = sum(counts.values())
            correct = counts.get('00', 0)
            qber = 1.0 - correct / total
            print(f"  QBER = {qber:.4f} ({correct}/{total} '00')")

    return qpu_im, qber, data


def main():
    print("=" * 70)
    print("SPECTRAL-SCALING QPU-RESULTS Fez/TOKEN2")
    print("=" * 70)

    qpu_im, qber, sweep_data = fetch_results()

    # === Statevector reference (alle n) ===
    with open("pt_spectral_scaling_statevector_results.json") as f:
        sv = json.load(f)
    sv_im = {int(n): sv["spectra"][n][0]["im"] for n in ["2", "3", "4"]}
    # nimm den niedrigsten Im-Eigenwert (E_0)
    print(f"\nStatevector Im_E_0 (n=2,3,4): {sv_im}")

    # === Im_bias (QPU - statevector) ===
    im_biases = {n: qpu_im[n] - sv_im[n] for n in [2, 3, 4]}
    abs_biases = {n: abs(b) for n, b in im_biases.items()}
    print(f"Im_biases: {im_biases}")
    print(f"|Im_bias|: {abs_biases}")

    # === QPU-BlockDiag-Invarianz (QPU-vs-QPU, alle n) ===
    ref_im_qpu = qpu_im[2]
    qpu_diffs = {n: abs(qpu_im[n] - ref_im_qpu) for n in [3, 4]}
    print(f"\nQPU-Invariance (vs n=2): {qpu_diffs}")
    max_qpu_diff = max(qpu_diffs.values())
    qpu_pass = max_qpu_diff < 0.005  # QPU bias band (QBER-Studie)
    print(f"  max |Im_QPU_n - Im_QPU_2| = {max_qpu_diff:.4f} -> {'PASS' if qpu_pass else 'FAIL'}")

    # === H_BlockDiag_Invariance_Statevector (aus Baseline) ===
    sv_pass = sv["H_BlockDiag_Invariance_Statevector"]["PASS"]
    print(f"\nStatevector baseline PASS: {sv_pass}")

    # === Save results ===
    results = {
        "prereg_file": "pt_spectral_scaling_prereg.json",
        "qpu_im": qpu_im,
        "sv_im": sv_im,
        "im_biases": im_biases,
        "abs_biases": abs_biases,
        "qber": qber,
        "qpu_invariance_diffs": qpu_diffs,
        "H_BlockDiag_Invariance_QPU": {
            "test": "max |Im_QPU_n - Im_QPU_2| < 0.005",
            "max_diff": max_qpu_diff,
            "PASS": bool(qpu_pass),
        },
        "H_BlockDiag_Invariance_Statevector_PASS": bool(sv_pass),
        "verdict": (
            "CONFIRMED: QPU-BlockDiag-Invarianz hält. Im(H_PT) auf dem 2x2-Block "
            "ist unabhängig von der Qubit-Anzahl (innerhalb 0.005 QPU-Bias-Band). "
            "Embedding-Korrektur 2. Ordnung ist QPU-irrelevant."
        ) if qpu_pass else (
            f"QPU-Invariance marginal: max_diff={max_qpu_diff:.4f} > 0.005"
        ),
        "sweep_metadata": sweep_data,
        "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    }
    out_file = "pt_spectral_scaling_token2_results.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*70}")
    print(f"VERDICT: H_BlockDiag_Invariance_QPU = {'PASS' if qpu_pass else 'FAIL'}")
    print(f"QBER: {qber:.4f}")
    print(f"Results saved: {out_file}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
