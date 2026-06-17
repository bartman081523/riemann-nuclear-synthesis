"""
EXPERIMENT 007 v3 - E_0 VQE + 3-Pub-Messung auf Fez, TOKEN1-Front

Nutzt IBMQ_TOKEN (statt TOKEN2 wie das Original pt_vqe_vqd.py).
TOKEN1-Front war 8 Tage blockiert, jetzt offen (Job d8p7sa8q90bc73e7e2ng lief durch).

Identische Strategie wie v2: VQE + H_diag, H_PT_re, H_PT_im am Optimum.
"""
import os
import json
import numpy as np
from scipy.optimize import minimize
from pt_structural import jacobi_A, E_DIAG
from qiskit.circuit.library import n_local as n_local_fn
from qiskit.quantum_info import SparsePauliOp, Operator
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

BACKEND_NAME = "ibm_fez"
GAMMA = 0.02
ALPHA = 1.0
SHOTS = 8192
INITIAL_PARAMS = [0.523, 1.21, -0.45, 0.88]
N_ITERS_VQE = 10


def load_token():
    with open(".env") as f:
        for line in f:
            if line.startswith("IBMQ_TOKEN="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("IBMQ_TOKEN nicht in .env")


def main():
    token = load_token()
    print(f"Verwende IBMQ_TOKEN (TOKEN1-Front)")

    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend(BACKEND_NAME)
    print(f"Backend: {BACKEND_NAME}")

    # === Operator-Konstruktion (deterministisch) ===
    A = jacobi_A(E_DIAG, y=1.0)
    H_diag = np.diag(E_DIAG).astype(complex)
    H_PT = H_diag + 1j * GAMMA * A
    H_real = (H_PT + H_PT.conj().T) / 2
    H_imag = (H_PT - H_PT.conj().T) / (2j)
    pauli_real = SparsePauliOp.from_operator(Operator(H_real))
    pauli_imag = SparsePauliOp.from_operator(Operator(H_imag))
    pauli_diag = SparsePauliOp.from_operator(Operator(H_diag))

    # === Ansatz + ISA (4 Parameter fuer 2 Qubits, reps=1, ry+linear) ===
    ansatz = n_local_fn(2, ['ry'], 'cx', 'linear', reps=1)
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    isa_ansatz = pm.run(ansatz)
    isa_real = pauli_real.apply_layout(isa_ansatz.layout)
    isa_imag = pauli_imag.apply_layout(isa_ansatz.layout)
    isa_diag = pauli_diag.apply_layout(isa_ansatz.layout)
    print(f"isa_ansatz num_parameters: {isa_ansatz.num_parameters}")

    # === Estimator ===
    estimator = Estimator(mode=backend)
    estimator.options.resilience_level = 1
    estimator.options.dynamical_decoupling.enable = True
    estimator.options.dynamical_decoupling.sequence_type = "XX"
    estimator.options.default_shots = SHOTS

    def cost_real(params):
        result = estimator.run([(isa_ansatz, isa_real, list(params))]).result()
        return result[0].data.evs

    # === VQE fuer E_0 ===
    print("\n" + "=" * 70)
    print("VQE: E_0 von Re(H_PT) auf Fez (TOKEN1)")
    print("=" * 70)

    # VQE-Initialisierung mit korrekter Anzahl Parameter
    init = list(INITIAL_PARAMS[:isa_ansatz.num_parameters])
    print(f"  init params: {[f'{p:.4f}' for p in init]}")

    res_vqe = minimize(
        fun=cost_real,
        x0=init,
        method='COBYLA',
        options={'maxiter': N_ITERS_VQE, 'rhobeg': 0.5, 'disp': False}
    )
    E0_meas = float(res_vqe.fun)
    E0_params = list(res_vqe.x)
    print(f"  E_0 (VQE) = {E0_meas:.4f}")
    print(f"  E_0 (noiseless) = 2.0019")
    print(f"  Delta = {E0_meas - 2.0019:+.4f}")
    print(f"  nfev = {res_vqe.nfev}")

    # === Messung am VQE-Optimum: 3 Pubs ===
    print("\n" + "=" * 70)
    print("MESSUNG AM VQE-OPTIMUM (3 Pubs)")
    print("=" * 70)
    job_ids = []
    try:
        job = estimator.run([
            (isa_ansatz, isa_diag, E0_params),
            (isa_ansatz, isa_real, E0_params),
            (isa_ansatz, isa_imag, E0_params)
        ])
        job_id = job.job_id()
        job_ids.append(str(job_id))
        result = job.result()
        H_diag_meas = float(result[0].data.evs)
        Re_PT_meas = float(result[1].data.evs)
        Im_PT_meas = float(result[2].data.evs)
        print(f"  job_id = {job_id}")
        print(f"  <H_diag>      = {H_diag_meas:.4f}")
        print(f"  <Re(H_PT)>    = {Re_PT_meas:.4f}")
        print(f"  <Im(H_PT)>    = {Im_PT_meas:.4f}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"FEHLER: {e}")
        return

    # === Bias-Analyse am VQE-Optimum ===
    beta_diag = H_diag_meas - 3.3412
    bias_PT_re = Re_PT_meas - H_diag_meas
    Im_at_ground = 0.0299
    Im_bias = Im_PT_meas - Im_at_ground

    print(f"\nBias-Analyse am VQE-Optimum:")
    print(f"  beta_diag  = {beta_diag:+.4f}")
    print(f"  bias_PT_re = {bias_PT_re:+.4f}")
    print(f"  Im_bias    = {Im_bias:+.4f}")

    # === Prereg-Vergleich ===
    prereg = json.load(open("pt_vqe_vqd_prereg.json"))
    verdict = "?"
    if abs(bias_PT_re) < 0.05:
        verdict = "H1/H3_bestaetigt (|bias_PT_re| < 0.05)"
    elif abs(bias_PT_re) > 0.15:
        verdict = "H2_multiplikativ (|bias_PT_re| > 0.15)"
    else:
        verdict = f"MITTEL (0.05 < |bias_PT_re| < 0.15)"

    print(f"\nPrereg-Vergleich:")
    print(f"  H1 (additiv) erwartet: bias_PT_re ~ 0")
    print(f"  H2 (multiplikativ) erwartet: bias_PT_re ~ +0.4..0.6")
    print(f"  H3 (Kohaerenz-Decay) erwartet: bias_PT_re ~ -0.02..-0.04")
    print(f"  VERDICT: {verdict}")

    # === Speichern ===
    output = {
        "backend": BACKEND_NAME,
        "token_used": "IBMQ_TOKEN (TOKEN1-Front)",
        "gamma": GAMMA,
        "alpha": ALPHA,
        "shots": SHOTS,
        "n_vqe_iters": int(res_vqe.nfev),
        "vqe_result": {
            "E0_meas": E0_meas,
            "E0_params": E0_params,
            "E0_noiseless": 2.0019
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
        "job_ids": job_ids,
        "verdict": verdict,
        "prereg_file": "pt_vqe_vqd_prereg.json"
    }
    with open("pt_vqe_vqd_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nErgebnisse gespeichert: pt_vqe_vqd_results.json")


if __name__ == "__main__":
    main()
