"""
EXPERIMENT 012c — 5-Pub-Messung separat nach VQE (Konsolidierung Säule 1).

Aus pt_potential_vqe_minimal_vqe_run.log (212s):
  VQE-Result: E_0 = 2.3610 (noiseless 2.0019)
  VQE-Params (4 von 6 genutzt): [-0.78828768, 2.83192151, 1.45766093, 0.61988954]

Bug in Original: E0_params hatte 4 Elemente, isa_ansatz braucht 6.
Fix: 5 Pub-Messung mit 6 params = E0_params + Wiederholungen.
"""
import json
import os
import time
import numpy as np
from pt_structural import jacobi_A, E_DIAG

BACKEND = "ibm_fez"
GAMMA = 0.02
SHOTS = 1024  # reduziert fuer Tageslimit
VQE_PARAMS_4 = [-0.78828768, 2.83192151, 1.45766093, 0.61988954]


def load_token():
    with open(".env") as f:
        for line in f:
            if line.startswith("IBMQ_TOKEN2="):
                return line.split("=", 1)[1].strip()
    raise ValueError("IBMQ_TOKEN2 nicht in .env")


def main():
    from qiskit.circuit.library import TwoLocal
    from qiskit.quantum_info import SparsePauliOp, Operator
    from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    t0 = time.time()
    print(f"[{time.time()-t0:.0f}s] Starting pt_potential_vqe_5pub.py", flush=True)

    token = load_token()
    service = QiskitRuntimeService(channel="ibm_ibm_quantum_platform" if False else "ibm_quantum_platform", token=token)
    backend = service.backend(BACKEND)
    print(f"[{time.time()-t0:.0f}s] Backend: {BACKEND}, queue={backend.status().pending_jobs}", flush=True)

    # Pre-Registrierung
    with open("pt_potential_vqe_prereg.json") as f:
        prereg = json.load(f)
    print(f"[{time.time()-t0:.0f}s] Prereg loaded", flush=True)

    # Operatoren
    A = jacobi_A(E_DIAG, y=1.0)
    H_diag = np.diag(E_DIAG).astype(complex)
    H_PT = H_diag + 1j * GAMMA * A
    H_real = (H_PT + H_PT.conj().T) / 2
    H_imag = (H_PT - H_PT.conj().T) / (2j)
    pauli_real = SparsePauliOp.from_operator(Operator(H_real))
    pauli_imag = SparsePauliOp.from_operator(Operator(H_imag))
    pauli_diag = SparsePauliOp.from_operator(Operator(H_diag))

    # Ansatz + ISA (6 params, TwoLocal reps=2)
    ansatz = TwoLocal(2, ['ry'], 'cx', 'linear', reps=2)
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
    isa_ansatz = pm.run(ansatz)
    isa_real = pauli_real.apply_layout(isa_ansatz.layout)
    isa_imag = pauli_imag.apply_layout(isa_ansatz.layout)
    isa_diag = pauli_diag.apply_layout(isa_ansatz.layout)
    n_params = isa_ansatz.num_parameters
    print(f"[{time.time()-t0:.0f}s] ISA: n_params={n_params}", flush=True)

    # VQE-Params auf 6 Dimensionen erweitern (zyklisch wiederholt)
    E0_params = [VQE_PARAMS_4[i % len(VQE_PARAMS_4)] for i in range(n_params)]
    print(f"[{time.time()-t0:.0f}s] E0_params (6-dim): {E0_params}", flush=True)

    np.random.seed(42)
    theta_r_4 = list(np.random.uniform(-np.pi, np.pi, 4))
    theta_r = [theta_r_4[i % len(theta_r_4)] for i in range(n_params)]

    # Estimator
    estimator = Estimator(mode=backend)
    estimator.options.resilience_level = 1
    estimator.options.dynamical_decoupling.enable = True
    estimator.options.dynamical_decoupling.sequence_type = "XX"
    estimator.options.default_shots = SHOTS

    # === 5-Pub sequenziell (1-Pub-pro-Job, Fez-Queue-Optimierung) ===
    pubs = [
        (isa_diag, E0_params, "H_diag_at_vqe_opt"),
        (isa_real, E0_params, "Re_H_PT_at_vqe_opt"),
        (isa_imag, E0_params, "Im_H_PT_at_vqe_opt"),
        (isa_real, theta_r, "Re_H_PT_at_random"),
        (isa_imag, theta_r, "Im_H_PT_at_random")
    ]
    results_dict = {}
    job_ids = []
    for isa_obs, params, name in pubs:
        print(f"\n[{time.time()-t0:.0f}s] === Pub: {name} ===", flush=True)
        job = estimator.run([(isa_ansatz, isa_obs, params)])
        job_id = job.job_id()
        job_ids.append(job_id)
        result = job.result()
        evs = result[0].data.evs
        results_dict[name] = float(evs)
        print(f"[{time.time()-t0:.0f}s] {name}: {evs:.4f} (job={job_id})", flush=True)

    H_diag_meas = results_dict["H_diag_at_vqe_opt"]
    Re_PT_meas = results_dict["Re_H_PT_at_vqe_opt"]
    Im_PT_meas = results_dict["Im_H_PT_at_vqe_opt"]
    Re_PT_rand = results_dict["Re_H_PT_at_random"]
    Im_PT_rand = results_dict["Im_H_PT_at_random"]

    # === Bias-Analyse ===
    beta_diag = H_diag_meas - 3.3412
    bias_PT_re = Re_PT_meas - H_diag_meas
    Im_at_ground = prereg['noiseless']['Im'][0]
    Im_bias = Im_PT_meas - Im_at_ground

    print(f"\n{'='*60}")
    print(f"5-Pub-Messung auf {BACKEND} (TOKEN2)")
    print(f"  <H_diag>      = {H_diag_meas:.4f}")
    print(f"  <Re(H_PT)>    = {Re_PT_meas:.4f}")
    print(f"  <Im(H_PT)>    = {Im_PT_meas:.4f}")
    print(f"  <Re(H_PT)>_r  = {Re_PT_rand:.4f}  (random)")
    print(f"  <Im(H_PT)>_r  = {Im_PT_rand:.4f}  (random)")
    print(f"  bias_PT_re    = {bias_PT_re:+.4f}  <-- ENTSCHEIDEND")
    print(f"  beta_diag     = {beta_diag:+.4f}")
    print(f"  Im_bias       = {Im_bias:+.4f}")
    if abs(bias_PT_re) < 0.05:
        verdict = "H1/H3 (gaps invariant) — REFRAMING_VECTOR bestaetigt!"
    elif abs(bias_PT_re) > 0.15:
        verdict = "H2 (multiplikative Bias) — REFRAMING_VECTOR widerlegt"
    else:
        verdict = "MITTEL — partial H2-Einfluss"
    print(f"  VERDICT: {verdict}")
    print(f"  Laufzeit: {time.time()-t0:.0f}s")
    print(f"{'='*60}", flush=True)

    output = {
        "backend": BACKEND,
        "token": "TOKEN2 (neuer Account)",
        "shots": SHOTS,
        "vqe_params_source": "pt_potential_vqe_minimal (E0=2.3610)",
        "vqe_E0_meas": 2.3610,
        "vqe_E0_noiseless": float(prereg['noiseless']['E'][0]),
        "5_pubs": {
            "H_diag_at_vqe_opt": float(H_diag_meas),
            "Re_H_PT_at_vqe_opt": float(Re_PT_meas),
            "Im_H_PT_at_vqe_opt": float(Im_PT_meas),
            "Re_H_PT_at_random": float(Re_PT_rand),
            "Im_H_PT_at_random": float(Im_PT_rand)
        },
        "job_ids": job_ids,
        "bias_analysis": {
            "beta_diag": float(beta_diag),
            "bias_PT_re": float(bias_PT_re),
            "Im_bias": float(Im_bias)
        },
        "verdict": verdict,
        "runtime_seconds": float(time.time() - t0)
    }
    with open("pt_potential_vqe_5pub_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nErgebnisse: pt_potential_vqe_5pub_results.json", flush=True)


if __name__ == "__main__":
    main()
