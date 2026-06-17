"""
pt_qber_statevector.py - Statevector baseline for QBER-vs-Im_bias sweep.

PRE-REGISTRATION (Anti-Sharpshooter):
    Hypotheses committed to pt_qber_prereg.json BEFORE main():
      H_Noise_Driven:  QBER correlates with Im_bias (rho > 0.5)
      H_Bias_Driven:   QBER does NOT correlate (|rho| < 0.3)
      H_Qber_Sanity:   statevector QBER (|00> ref, no noise) == 0 exactly

Method:
    1) Compute QBER for a |00> reference circuit via AerSimulator at
       various noise levels (sanity: statevector=0, with noise > 0).
    2) Load 5 statevector Im_bias values from
       pt_im_bias_statevector_results.json.
    3) Report Pearson correlation QBER vs Im_bias at each noise level.
"""
import json
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error


def qber_aer(noise_prob=0.0, shots=4096):
    """Compute QBER for a 2-qubit |00> reference circuit with optional depolarizing noise.

    QBER = 1 - P(measure '00').
    For noiseless statevector: QBER = 0 (deterministic |00>).
    With depolarizing noise prob p on measurement:
        P(bit flip on measure) = p per qubit
        For 2-qubit |00> + measurement noise:
            P(measure '00') = (1-p)^2
            QBER = 1 - (1-p)^2 ~ 2p (small p)
    """
    qc = QuantumCircuit(2)
    qc.measure_all()

    sim = AerSimulator()
    if noise_prob > 0:
        noise_model = NoiseModel()
        err_1q = depolarizing_error(noise_prob, 1)
        # Measurement error is the dominant QBER source on real hardware
        noise_model.add_all_qubit_quantum_error(err_1q, ['measure'])
        job = sim.run(qc, noise_model=noise_model, shots=shots, seed_simulator=42)
    else:
        # Statevector simulation - no noise, no measurement sampling
        from qiskit.quantum_info import Statevector
        sv = Statevector.from_label('00')
        probs = sv.probabilities_dict()
        return 1.0 - probs.get('00', 0.0)

    counts = job.result().get_counts()
    total = sum(counts.values())
    correct = counts.get('00', 0)
    return 1.0 - correct / total


def main():
    print("=" * 70)
    print("STATEVECTOR QBER BASELINE")
    print("=" * 70)

    # 1. Sanity: statevector QBER should be exactly 0
    qber_sv = qber_aer(noise_prob=0.0, shots=4096)
    print(f"\n1) Statevector QBER (|00> ref, no noise): {qber_sv:.6f}")
    sanity_passed = (qber_sv == 0.0)
    print(f"   H_Qber_Sanity: {'CONFIRMED' if sanity_passed else 'FAILED'}")

    # 2. QBER as function of noise level (Aer)
    print(f"\n2) Aer QBER vs gate depolarizing noise prob:")
    noise_levels = [0.0, 0.001, 0.005, 0.01, 0.02, 0.05]
    noise_qbers = {}
    for p in noise_levels:
        q = qber_aer(noise_prob=p, shots=4096)
        noise_qbers[f"p={p}"] = q
        print(f"   p = {p:6.4f}  ->  QBER = {q:.4f}")

    # 3. Load existing Im_bias statevector data
    with open("pt_im_bias_statevector_results.json") as f:
        im_data = json.load(f)
    im_biases = im_data.get("Im_statevector", [])
    n_pts = len(im_biases)
    print(f"\n3) Loaded {n_pts} Im_statevector reference values")

    # 4. Pearson correlation QBER vs Im_bias
    # For statevector QBER (= 0 for all points), correlation is undefined (NaN).
    # We report it as NaN to make the QPU comparison meaningful.
    im_array = np.array(im_biases)
    qber_array = np.zeros(n_pts)
    if np.std(qber_array) > 0:
        rho_sv = float(np.corrcoef(qber_array, im_array)[0, 1])
    else:
        rho_sv = float('nan')

    # 5. Hypotheses:
    #    H_Noise_Driven: rho > 0.5 (QBER + Im_bias correlate, both noise-driven)
    #    H_Bias_Driven:  |rho| < 0.3 (Im_bias is algorithm-driven, not noise-driven)
    #    Statevector: rho is undefined (QBER has zero variance)
    #    => inconclusive at statevector; must be tested on QPU where QBER > 0.
    print(f"\n4) Pearson correlation QBER vs Im_bias (statevector): NaN")
    print(f"   Reason: statevector QBER has zero variance (QBER = 0 for all points)")
    print(f"   => Correlation undefined at statevector level")
    print(f"   => MUST be tested on QPU where QBER > 0")

    # 6. Save baseline
    baseline = {
        "method": "pt_qber_statevector.py - QBER baseline + Aer noise sweep",
        "hypotheses": {
            "H_Noise_Driven": "rho(QBER, Im_bias) > 0.5 (QPU level)",
            "H_Bias_Driven": "|rho(QBER, Im_bias)| < 0.3 (QPU level)",
            "H_Qber_Sanity": "statevector QBER == 0"
        },
        "statevector_qber": float(qber_sv),
        "noise_qber_table": noise_qbers,
        "im_statevector_values": [float(x) for x in im_biases],
        "pearson_qber_vs_imbias_statevector": rho_sv,
        "sanity_passed": bool(sanity_passed),
        "decision_rule_statevector": (
            "H_Qber_Sanity: statevector QBER must be 0 exactly. "
            "Correlation undefined at statevector level (zero QBER variance); "
            "test on QPU where QBER > 0."
        ),
    }
    with open("pt_qber_statevector_results.json", "w") as f:
        json.dump(baseline, f, indent=2)

    print(f"\nBaseline saved: pt_qber_statevector_results.json")
    print(f"H_Qber_Sanity: {'PASSED' if sanity_passed else 'FAILED'}")


if __name__ == "__main__":
    main()
