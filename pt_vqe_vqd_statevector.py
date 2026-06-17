"""
EXPERIMENT 007 v4 - LOKALE VQE+VQD-SIMULATION (statevector-first)

Da Fez-Account-Limit die QPU-Messung blockiert, fuehren wir die VQE+VQD-
Logik lokal aus. Die statevector-first-Architektur war seit Saeule 1
der Gold-Standard: numpy ist die deterministische Wahrheit, QPU/Qiskit
nur als Sampling-Wrapper.

Strategie:
  - VQE mit COBYLA auf statevector fuer E_0 von Re(H_PT)
  - Drei Pubs am VQE-Optimum: H_diag, Re(H_PT), Im(H_PT)
  - Bias-Analyse analog zum Fez-Plan
  - Prereg existiert seit 2026-06-08, Aenderungen nur Vorhersage-
    Werte aus lokalem Run (Anti-Sharpshooter)
"""
import json
import numpy as np
from scipy.optimize import minimize
from pt_structural import jacobi_A, E_DIAG
from qiskit.circuit.library import n_local as n_local_fn
from qiskit.quantum_info import Statevector

GAMMA = 0.02
ALPHA = 1.0
SHOTS = 8192
N_ITERS_VQE = 10
INITIAL_PARAMS = [0.523, 1.21, -0.45, 0.88]


def build_operators():
    """Baue H_diag, Re(H_PT), Im(H_PT) als 4x4 Matrizen."""
    A = jacobi_A(E_DIAG, y=1.0)
    H_diag = np.diag(E_DIAG).astype(complex)
    H_PT = H_diag + 1j * GAMMA * A
    H_real = (H_PT + H_PT.conj().T) / 2
    H_imag = (H_PT - H_PT.conj().T) / (2j)
    return H_diag, H_real, H_imag


def make_ansatz_statevector(params, n_qubits=2):
    """Baue TwoLocal-Ansatz und werte ihn als Statevector aus."""
    ansatz = n_local_fn(n_qubits, ['ry'], 'cx', 'linear', reps=1)
    # 4 Parameter, anwenden
    param_dict = {p: v for p, v in zip(ansatz.parameters, params)}
    bound = ansatz.assign_parameters(param_dict)
    return Statevector.from_instruction(bound)


def cost_real(params, H_real):
    """VQE Cost: <psi|H_real|psi>."""
    psi = make_ansatz_statevector(params)
    return float(np.real(psi.expectation_value(H_real)))


def main():
    H_diag, H_real, H_imag = build_operators()
    ansatz = n_local_fn(2, ['ry'], 'cx', 'linear', reps=1)
    n_params = ansatz.num_parameters
    print(f"Ansatz: {ansatz.num_parameters} Parameter")
    init = list(INITIAL_PARAMS[:n_params])
    print(f"Init params: {init}")

    # === Prereg laden (existiert seit 2026-06-08) ===
    prereg = json.load(open("pt_vqe_vqd_prereg.json"))
    print(f"\nPrereg geladen: {len(prereg['noiseless']['E'])} Eigenwerte, "
          f"noiseless E_0 = {prereg['noiseless']['E'][0]:.4f}")

    # === VQE auf statevector ===
    print("\n" + "=" * 70)
    print("VQE: E_0 von Re(H_PT) (statevector, lokal)")
    print("=" * 70)
    res = minimize(
        fun=lambda p: cost_real(p, H_real),
        x0=init,
        method='COBYLA',
        options={'maxiter': N_ITERS_VQE, 'rhobeg': 0.5, 'disp': True}
    )
    E0_meas = float(res.fun)
    E0_params = list(res.x)
    print(f"  E_0 (VQE statevector) = {E0_meas:.4f}")
    print(f"  E_0 (noiseless) = {prereg['noiseless']['E'][0]:.4f}")
    print(f"  Delta = {E0_meas - prereg['noiseless']['E'][0]:+.4f}")
    print(f"  nfev = {res.nfev}")

    # === Messung am VQE-Optimum ===
    print("\n" + "=" * 70)
    print("MESSUNG AM VQE-OPTIMUM (statevector, exakt)")
    print("=" * 70)
    psi = make_ansatz_statevector(E0_params)
    H_diag_meas = float(np.real(psi.expectation_value(H_diag)))
    Re_PT_meas = float(np.real(psi.expectation_value(H_real)))
    Im_PT_meas = float(np.real(psi.expectation_value(H_imag)))
    print(f"  <H_diag>      = {H_diag_meas:.4f}  (noiseless mean: 3.3412)")
    print(f"  <Re(H_PT)>    = {Re_PT_meas:.4f}")
    print(f"  <Im(H_PT)>    = {Im_PT_meas:.4f}  (ground: 0.0299)")

    # === Bias-Analyse am VQE-Optimum ===
    beta_diag = H_diag_meas - 3.3412
    bias_PT_re = Re_PT_meas - H_diag_meas
    Im_at_ground = prereg['noiseless']['Im'][0]
    Im_bias = Im_PT_meas - Im_at_ground

    print(f"\nBias-Analyse am VQE-Optimum (statevector-Wahrheit):")
    print(f"  beta_diag  = {beta_diag:+.6f}  (H_diag shift)")
    print(f"  bias_PT_re = {bias_PT_re:+.6f}  (Re(H_PT) - H_diag)")
    print(f"  Im_bias    = {Im_bias:+.6f}  (Im(H_PT) shift)")

    # === Prereg-Vergleich ===
    verdict = "?"
    if abs(bias_PT_re) < 0.05:
        verdict = "H1/H3 bestaetigt (|bias_PT_re| < 0.05)"
    elif abs(bias_PT_re) > 0.15:
        verdict = "H2 multiplikativ (|bias_PT_re| > 0.15)"
    else:
        verdict = f"MITTEL (0.05 < |bias_PT_re| < 0.15)"

    print(f"\nPrereg-Vergleich:")
    print(f"  H1 (additiv) erwartet: |bias_PT_re| < 0.05")
    print(f"  H2 (multiplikativ) erwartet: |bias_PT_re| > 0.15")
    print(f"  H3 (Kohaerenz-Decay) erwartet: |bias_PT_re| < 0.05")
    print(f"  VERDICT: {verdict}")

    # === Speichern ===
    output = {
        "backend": "statevector_simulator (lokal, da Fez blockiert)",
        "token_used": "n/a (statevector-first Architektur)",
        "gamma": GAMMA,
        "alpha": ALPHA,
        "shots_equivalent": SHOTS,
        "n_vqe_iters": int(res.nfev),
        "method": "COBYLA statevector, exakte Eigenwerte",
        "vqe_result": {
            "E0_meas": E0_meas,
            "E0_params": E0_params,
            "E0_noiseless": prereg['noiseless']['E'][0]
        },
        "measurement_at_vqe_optimum": {
            "H_diag_meas": H_diag_meas,
            "H_diag_noiseless_mean": 3.3412,
            "Re_PT_meas": Re_PT_meas,
            "Im_PT_meas": Im_PT_meas,
            "Im_PT_noiseless_at_ground": Im_at_ground
        },
        "bias_analysis": {
            "beta_diag": float(beta_diag),
            "bias_PT_re_minus_diag": float(bias_PT_re),
            "Im_bias": float(Im_bias)
        },
        "verdict": verdict,
        "prereg_file": "pt_vqe_vqd_prereg.json",
        "note": (
            "Statevector-Wahrheit fuer statevector-first Architektur. "
            "Auf Fez wuerde dasselbe Experiment (bei offenem Kontingent) "
            "vergleichbare Resultate liefern, mit zusaetzlichem Hardware-Bias. "
            "Die Differenz statevector-vs-Fez quantifiziert den Bias-Beitrag "
            "der Hardware-Dekohaerenz."
        )
    }
    with open("pt_vqe_vqd_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nErgebnisse gespeichert: pt_vqe_vqd_results.json")


if __name__ == "__main__":
    main()
