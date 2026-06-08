"""
EXPERIMENT 007 v2 - E_0 VQE + H_diag Referenz auf Fez

Strategie (revidiert nach lokalem Test):
  - VQE auf Fez fuer E_0 von Re(H_PT)  (verifiziert: lokale Tests
    zeigen dass E_0 = 2.00 zuverlaessig gefunden wird)
  - H_diag auf Fez als bias-freie Referenz  (deterministische
    Diagonalniveaus, exakt bekannt, kein VQE noetig)
  - H_PT Spektrum am VQE-Optimum messen (zur Bias-Quantifizierung)

Delta E_n wird aus H_diag abgeleitet (deterministisch), nicht aus
eigenstaendigem VQE fuer E_1..E_3 — das scheitert lokal mit allen
getesteten Ansaetzen (COBYLA lokale Minima auf flacher Landschaft).

Hintergrund: qiskit_algorithms.VQD mit fidelity-Penalty scheitert
auf diesem 4-dim Problem mit den getesteten Ansaetzen (reps=1..3,
EfficientSU2, real_amplitudes). Die exakte Diagonalisierung liefert
die wahren Werte; H_diag auf Hardware ist die bias-freie Vergleichsbasis.
"""
import os
import json
import numpy as np
from scipy.optimize import minimize
from pt_structural import jacobi_A, E_DIAG
from qiskit.circuit.library import TwoLocal
from qiskit.quantum_info import SparsePauliOp, Operator
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

BACKEND_NAME = "ibm_fez"
GAMMA = 0.02
ALPHA = 1.0
SHOTS = 8192
INITIAL_PARAMS = [0.523, 1.21, -0.45, 0.88]
N_ITERS_VQE = 10  # COBYLA-Iterationen fuer E_0 VQE


def load_token():
    return open(".env").read().split("IBMQ_TOKEN=")[1].split("\n")[0]


def precompute_predictions():
    """Vorhersagen H1/H2/H3 + exakte Diagonalisierung von H_diag."""
    A = jacobi_A(E_DIAG, y=1.0)
    H_diag = np.diag(E_DIAG).astype(complex)
    H_PT = H_diag + 1j * GAMMA * A
    eigs_PT = sorted(np.linalg.eigvals(H_PT), key=lambda z: z.real)
    eigs_diag = sorted([float(x.real) for x in np.diag(H_diag)])

    # Noiseless E_n fuer Re(H_PT)
    E_noiseless = [e.real for e in eigs_PT]
    Delta_noiseless = [E_noiseless[i+1] - E_noiseless[i] for i in range(3)]
    Im_noiseless = [e.imag for e in eigs_PT]

    # H1 = noiseless (additiver Bias hebt sich in Deltas auf)
    H1 = {"E": E_noiseless, "Delta": Delta_noiseless, "Im": Im_noiseless}

    # H2 (multiplikativ auf A, k=25)
    k = 25.0
    H_PT_k = H_diag + 1j * GAMMA * k * A
    eigs_k = sorted(np.linalg.eigvals(H_PT_k), key=lambda z: z.real)
    H2 = {
        "E": [e.real for e in eigs_k],
        "Delta": [eigs_k[i+1].real - eigs_k[i].real for i in range(3)],
        "Im": [e.imag for e in eigs_k]
    }

    # H3 (Kohaerenz-Decay p=0.3)
    p = 0.3
    A_d = A.copy()
    for i in range(4):
        for j in range(4):
            if i != j:
                A_d[i, j] *= (1 - p)
    H_PT_d = H_diag + 1j * GAMMA * A_d
    eigs_d = sorted(np.linalg.eigvals(H_PT_d), key=lambda z: z.real)
    H3 = {
        "E": [e.real for e in eigs_d],
        "Delta": [eigs_d[i+1].real - eigs_d[i].real for i in range(3)],
        "Im": [e.imag for e in eigs_d]
    }

    return {
        "noiseless": H1,
        "H1_additive": H1,
        "H2_multiplicative_k25": H2,
        "H3_decoherence_p0.3": H3,
        "H_diag_exact": {
            "E": list(eigs_diag),
            "Delta": [eigs_diag[i+1] - eigs_diag[i] for i in range(3)]
        },
        "decision_rule": (
            "Wenn Delta_E_n_meas (aus H_diag auf Fez) mit H_diag_exact "
            "uebereinstimmt: H_diag ist bias-invariant (gut!). "
            "Wenn E_0 VQE mit noiseless uebereinstimmt: PT-E_0 bias-invariant. "
            "Wenn H_PT am VQE-Optimum ~ 2.00 (oder ~3.27 wie 6.5.4): "
            "Bias = 1.63x wie auf Marrakesh."
        )
    }


def main():
    token = load_token()
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend(BACKEND_NAME)
    print(f"Backend: {BACKEND_NAME}")

    # === Pre-Registrierung ===
    prereg = precompute_predictions()
    with open("pt_vqe_vqd_prereg.json", "w") as f:
        json.dump(prereg, f, indent=2)
    print(f"\nPräregistrierung geschrieben: pt_vqe_vqd_prereg.json")
    print(f"H_diag exakt: E_0..3 = {[f'{x:.4f}' for x in prereg['H_diag_exact']['E']]}")
    print(f"               Delta   = {[f'{x:.4f}' for x in prereg['H_diag_exact']['Delta']]}")
    print(f"Noiseless PT: Delta   = {[f'{x:.4f}' for x in prereg['noiseless']['Delta']]}")
    print(f"H2 (k=25):    Delta   = {[f'{x:.4f}' for x in prereg['H2_multiplicative_k25']['Delta']]}")

    # === Operator-Konstruktion ===
    A = jacobi_A(E_DIAG, y=1.0)
    H_diag = np.diag(E_DIAG).astype(complex)
    H_PT = H_diag + 1j * GAMMA * A
    H_real = (H_PT + H_PT.conj().T) / 2
    H_imag = (H_PT - H_PT.conj().T) / (2j)
    pauli_real = SparsePauliOp.from_operator(Operator(H_real))
    pauli_imag = SparsePauliOp.from_operator(Operator(H_imag))
    pauli_diag = SparsePauliOp.from_operator(Operator(H_diag))

    # === Ansatz + ISA ===
    ansatz = TwoLocal(2, ['ry'], 'cx', 'linear', reps=1)
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    isa_ansatz = pm.run(ansatz)
    isa_real = pauli_real.apply_layout(isa_ansatz.layout)
    isa_imag = pauli_imag.apply_layout(isa_ansatz.layout)
    isa_diag = pauli_diag.apply_layout(isa_ansatz.layout)

    # === Estimator ===
    estimator = Estimator(mode=backend)
    estimator.options.resilience_level = 1
    estimator.options.dynamical_decoupling.enable = True
    estimator.options.dynamical_decoupling.sequence_type = "XX"
    estimator.options.default_shots = SHOTS

    def cost_real(params):
        """VQE Cost fuer Re(H_PT)."""
        result = estimator.run([(isa_ansatz, isa_real, list(params))]).result()
        return result[0].data.evs

    # === VQE fuer E_0 ===
    print("\n" + "=" * 70)
    print("VQE: E_0 von Re(H_PT) auf Fez")
    print("=" * 70)
    res_vqe = minimize(
        fun=cost_real,
        x0=INITIAL_PARAMS,
        method='COBYLA',
        options={'maxiter': N_ITERS_VQE, 'rhobeg': 0.5, 'disp': False}
    )
    E0_meas = res_vqe.fun
    E0_params = res_vqe.x.tolist()
    print(f"  E_0 (VQE) = {E0_meas:.4f}")
    print(f"  E_0 (noiseless) = {prereg['noiseless']['E'][0]:.4f}")
    print(f"  Delta = {E0_meas - prereg['noiseless']['E'][0]:.4f}")
    print(f"  params = {[f'{p:.4f}' for p in E0_params]}")

    # === Messung am VQE-Optimum: H_diag, Re(H_PT), Im(H_PT) ===
    print("\n" + "=" * 70)
    print("MESSUNG AM VQE-OPTIMUM (3 Pubs)")
    print("=" * 70)
    try:
        result = estimator.run([
            (isa_ansatz, isa_diag, E0_params),
            (isa_ansatz, isa_real, E0_params),
            (isa_ansatz, isa_imag, E0_params)
        ]).result()
        H_diag_meas = result[0].data.evs
        Re_PT_meas = result[1].data.evs
        Im_PT_meas = result[2].data.evs
        print(f"  <H_diag>      = {H_diag_meas:.4f}  (noiseless mean 3.3412)")
        print(f"  <Re(H_PT)>    = {Re_PT_meas:.4f}  (noiseless mean 3.3412)")
        print(f"  <Im(H_PT)>    = {Im_PT_meas:.4f}  (noiseless mean 0.0267)")
        job_id = "submitted_in_session"
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"FEHLER: {e}")
        return

    # === Bias-Analyse am VQE-Optimum ===
    # H_diag: Mittelwert = 3.3412 (arith Mittel der 4 Eigenniveaus)
    # Re(H_PT): Mittelwert = 3.3412 (H_real hat spur = H_diag-Spur)
    # Im(H_PT): Mittelwert ~ 0.0267 (Resonanz-Beitrag am Initial-Punkt,
    #           am VQE-Optimum E_0 sehr klein)

    beta_diag = H_diag_meas - 3.3412  # sollte ~0 sein, wenn H_diag bias-invariant
    bias_PT_re = Re_PT_meas - H_diag_meas  # Differenz, sollte nahe 0 sein
    bias_PT_im = Im_PT_meas - 0.0267  # Resonanz-Beitrag-Bias

    # ABER: am VQE-Optimum ist der Zustand |psi_0>, der
    # Im(H_PT)|psi_0> = 0.0299|psi_0> erfuellt. Erwartungswert
    # <psi_0|Im(H_PT)|psi_0> = 0.0299.
    Im_at_ground = prereg['noiseless']['Im'][0]
    Im_bias = Im_PT_meas - Im_at_ground

    print(f"\nBias-Analyse am VQE-Optimum:")
    print(f"  beta_diag  = {beta_diag:+.4f}  (H_diag shift)")
    print(f"  bias_PT_re = {bias_PT_re:+.4f}  (Re(H_PT) - H_diag)")
    print(f"  Im_at_ground (noiseless) = {Im_at_ground:.4f}")
    print(f"  Im_bias = {Im_bias:+.4f}  (Im(H_PT) shift)")

    # === Speichern ===
    output = {
        "backend": BACKEND_NAME,
        "gamma": GAMMA,
        "alpha": ALPHA,
        "initial_params": INITIAL_PARAMS,
        "vqe_result": {
            "E0_meas": float(E0_meas),
            "E0_params": E0_params,
            "n_iterations": int(res_vqe.nfev),
            "E0_noiseless": float(prereg['noiseless']['E'][0])
        },
        "measurement_at_vqe_optimum": {
            "H_diag_meas": float(H_diag_meas),
            "H_diag_noiseless_mean": 3.3412,
            "Re_PT_meas": float(Re_PT_meas),
            "Im_PT_meas": float(Im_PT_meas),
            "Im_PT_noiseless_at_ground": float(Im_at_ground)
        },
        "bias_analysis": {
            "beta_diag": float(beta_diag),
            "bias_PT_re_minus_diag": float(bias_PT_re),
            "Im_bias": float(Im_bias)
        },
        "predictions": prereg,
        "delta_E_from_H_diag": {
            "exact": prereg['H_diag_exact']['Delta'],
            "note": "H_diag ist deterministisch; Delta E aus H_diag exakt. "
                    "Auf Hardware erwartet: H_diag_bias ~ 0, also Delta E "
                    "der Messung ~ exakt."
        }
    }
    with open("pt_vqe_vqd_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nErgebnisse gespeichert: pt_vqe_vqd_results.json")

    with open("pt_vqe_vqd_log.txt", "w") as f:
        f.write("EXPERIMENT 007 v2 - E_0 VQE + H_diag REFERENCE\n")
        f.write("=" * 70 + "\n")
        f.write(f"Backend: {BACKEND_NAME}\n")
        f.write(f"gamma={GAMMA}, alpha={ALPHA}\n")
        f.write(f"VQE Iter: {N_ITERS_VQE}, Shots: {SHOTS}\n\n")
        f.write(f"VQE E_0: {E0_meas:.4f} (noiseless: {prereg['noiseless']['E'][0]:.4f})\n")
        f.write(f"\nMessung am VQE-Optimum:\n")
        f.write(f"  <H_diag>      = {H_diag_meas:.4f}\n")
        f.write(f"  <Re(H_PT)>    = {Re_PT_meas:.4f}\n")
        f.write(f"  <Im(H_PT)>    = {Im_PT_meas:.4f}  (ground: {Im_at_ground:.4f})\n")
        f.write(f"\nBias:\n")
        f.write(f"  beta_diag    = {beta_diag:+.4f}\n")
        f.write(f"  bias_PT_re   = {bias_PT_re:+.4f}\n")
        f.write(f"  Im_bias      = {Im_bias:+.4f}\n")


if __name__ == "__main__":
    main()
