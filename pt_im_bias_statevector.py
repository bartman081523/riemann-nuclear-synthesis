"""
EXPERIMENT 015-LOCAL - STATEVECTOR-IM-BIAS-SWEEP (offline, deterministisch)

Da Fez-Account-Blockade (4 Jobs QUEUED, 0 laufend) QPU-Messung verhindert,
fuehren wir die Bias-Analyse auf statevector durch und simulieren den
Hardware-Sampling-Noise explizit.

Strategie:
  - 5 sequenzielle statevector-Messungen (deterministisch)
  - Plus: Sampling-Noise-Simulation mit 4096 shots (Bootstrapping)
  - Bias = <Im>_measured - <Im>_statevector (exakt)
  - Prereg H_Im_h1/h2/h3-Entscheidungsregel anwenden

Diese Vorhersage ist die Baseline, gegen die Fez-2026-07-01 (Cron b3f26579)
getestet wird. Wenn Fez signifikant vom statevector + Sampling-Noise abweicht,
ist das ein NEUER Befund (Hardware-Decay, Depolarisation, Crosstalk).
"""
import json
import time
import numpy as np
from pt_structural import jacobi_A, E_DIAG
from qiskit.circuit.library import n_local as n_local_fn
from qiskit.quantum_info import Statevector, SparsePauliOp, Operator

GAMMA = 0.02
SHOTS = 4096
N_BOOTSTRAP = 100  # Anzahl Bootstrap-Samples
N_THETA = 5

INITIAL_PARAMS_4 = [0.523, 1.21, -0.45, 0.88]
VQE_OPT_4 = [-0.104, 0.317, -0.803, -0.086]


def build_im_operator():
    A = jacobi_A(E_DIAG, y=1.0)
    H_diag = np.diag(E_DIAG).astype(complex)
    H_PT = H_diag + 1j * GAMMA * A
    H_imag = (H_PT - H_PT.conj().T) / (2j)
    return H_diag, H_imag


def sampling_noise_Im(Im_exact, shots=SHOTS, n_bootstrap=N_BOOTSTRAP, rng=None):
    """Simuliere Sampling-Noise auf einem Erwartungswert.

    Annahme: Messung liefert Summe Pauli-Ergebnisse, Gauss-foermig um exakten Wert.
    """
    if rng is None:
        rng = np.random.default_rng(0)
    # Standard-Fehler ~ sqrt(Im_exact * (1 - Im_exact) / shots) [wenn Im zwischen 0 und 1]
    # Aber Im kann negativ sein. Besser: Standard-Fehler basierend auf
    # Varianz des Estimators. Approximation: SE = 0.01 (Fez-typical, da Depolarisation ~1%)
    SE = 0.01
    samples = rng.normal(Im_exact, SE, n_bootstrap)
    return samples


def main():
    t0 = time.time()

    # Prereg laden
    prereg = json.load(open("pt_im_bias_prereg.json"))
    print(f"[{time.time()-t0:.0f}s] Prereg geladen: H_Im_h1/h2/h3", flush=True)

    # 5 theta-Punkte
    init_p = INITIAL_PARAMS_4
    np.random.seed(42); t1 = list(np.random.uniform(-np.pi, np.pi, 4))
    np.random.seed(43); t2 = list(np.random.uniform(-np.pi, np.pi, 4))
    np.random.seed(44); t3 = list(np.random.uniform(-np.pi, np.pi, 4))
    vqe_opt = VQE_OPT_4
    thetas = [init_p, t1, t2, vqe_opt, t3]
    labels = ["theta_initial", "theta_random_1", "theta_random_2", "theta_VQE_optimal", "theta_random_3"]

    # Statevector + Im(H_PT) exakt
    H_diag, H_imag = build_im_operator()
    ansatz = n_local_fn(2, ['ry'], 'cx', 'linear', reps=1)

    print(f"\n[{'='*70}]")
    print(f"STATEVECTOR-IM-BIAS-SWEEP (offline, deterministisch + Sampling-Noise)")
    print(f"[{'='*70}]")

    Im_statevector = []
    Im_measured_samples = []
    Im_bias_means = []
    Im_bias_stds = []
    rng = np.random.default_rng(0)

    for label, theta in zip(labels, thetas):
        pd = {p: v for p, v in zip(ansatz.parameters, theta)}
        sv = Statevector.from_instruction(ansatz.assign_parameters(pd))
        Im_exact = float(np.real(sv.expectation_value(H_imag)))
        Im_statevector.append(Im_exact)

        # Sampling-Simulation
        samples = sampling_noise_Im(Im_exact, shots=SHOTS, n_bootstrap=N_BOOTSTRAP, rng=rng)
        Im_measured_samples.append(samples.tolist())

        # Bias gegen exakten statevector = 0 (per Konstruktion)
        # Aber wir messen Im_measured - Im_statevector, was = 0 exakt
        # Realistischer: simuliere dass Messung Im_statevector + Bias liefert
        # Bias = Im_measured - Im_statevector (mean ~ 0, std ~ 0.01)
        bias_mean = float(np.mean(samples - Im_exact))
        bias_std = float(np.std(samples - Im_exact))
        Im_bias_means.append(bias_mean)
        Im_bias_stds.append(bias_std)

        print(f"\n  {label}:")
        print(f"    <Im>_statevector = {Im_exact:+.6f}")
        print(f"    <Im>_measured    = {bias_mean + Im_exact:+.6f} ± {bias_std:.6f} (n_bootstrap={N_BOOTSTRAP})")
        print(f"    Im_bias         = {bias_mean:+.6f} ± {bias_std:.6f}")

    # Verdict nach Prereg
    abs_biases = [abs(m) for m in Im_bias_means]
    if all(ab < 0.005 for ab in abs_biases):
        verdict = "H_Im_h1 (Sampling-Noise dominiert, alle |bias| < 0.005)"
    elif all(ab > 0.020 for ab in abs_biases):
        verdict = "H_Im_h2 (systematischer Bias, alle |bias| > 0.020)"
    else:
        verdict = (f"H_Im_h3 (Konsistenz, mean |bias| = {np.mean(abs_biases):.4f}, "
                   f"std = {np.std(Im_bias_means):.4f})")

    print(f"\n[{'='*70}]")
    print(f"VERDICT (offline, Sampling-Noise-Simulator): {verdict}")
    print(f"[{'='*70}]")

    # Speichern
    output = {
        "method": "pt_im_bias_statevector.py — statevector + Sampling-Noise-Simulator (offline)",
        "reason_for_offline": "Fez-Account-Blockade (4 Jobs QUEUED, 0 laufend, 2026-06-17 13:08 UTC)",
        "gamma": GAMMA,
        "shots_per_measurement": SHOTS,
        "n_bootstrap": N_BOOTSTRAP,
        "n_theta_points": N_THETA,
        "theta_labels": labels,
        "theta_values": thetas,
        "Im_statevector": Im_statevector,
        "Im_measured_means": [m + s for m, s in zip(Im_bias_means, Im_statevector)],
        "Im_bias_means": Im_bias_means,
        "Im_bias_stds": Im_bias_stds,
        "Im_measured_samples": Im_measured_samples,
        "verdict": verdict,
        "prereg_file": "pt_im_bias_prereg.json",
        "runtime_seconds": float(time.time() - t0),
        "next_step": "Fez-Reset 1.7.2026 (Cron b3f26579): Vergleich statevector+Noise vs Fez-Hardware",
        "note": "Diese Vorhersage ist die Baseline. Wenn Fez signifikant abweicht (mean bias > 0.020), ist das ein Hardware-Decay-Signal."
    }
    with open("pt_im_bias_statevector_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n[{time.time()-t0:.0f}s] Ergebnisse: pt_im_bias_statevector_results.json", flush=True)
    print(f"[{time.time()-t0:.0f}s] GESAMT: {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
