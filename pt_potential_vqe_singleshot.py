"""
EXPERIMENT 012c - MINIMALSTER TEST für TOKEN2/Fez (1 Pub, kein VQE).

Misst nur EINEN einzigen Erwartungswert am Initial-Punkt: <H_diag>.
Dauer: ~30s QPU-Zeit. 1 Job in der Queue.

Verifiziert: TOKEN2/Fez liefert physikalisch sinnvolle Erwartungswerte.
"""
import os
import json
import numpy as np
from pt_structural import jacobi_A, E_DIAG

GAMMA = 0.02
SHOTS = 1024  # minimal
INITIAL_PARAMS = [0.523, 1.21, -0.45, 0.88, 0.523, 1.21]


def load_token():
    return open(".env").read().split("IBMQ_TOKEN2=")[1].split("\n")[0]


def main():
    from qiskit.circuit.library import TwoLocal
    from qiskit.quantum_info import SparsePauliOp, Operator
    from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    import time

    t0 = time.time()
    token = load_token()
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend("ibm_fez")
    print(f"[{time.time()-t0:.0f}s] Backend: ibm_fez, queue={backend.status().pending_jobs}", flush=True)

    # H_PT = H_diag + i·gamma·A
    A = jacobi_A(E_DIAG, y=1.0)
    H_diag = np.diag(E_DIAG).astype(complex)
    H_PT = H_diag + 1j * GAMMA * A
    H_real = (H_PT + H_PT.conj().T) / 2
    H_imag = (H_PT - H_PT.conj().T) / (2j)
    pauli_real = SparsePauliOp.from_operator(Operator(H_real))
    pauli_imag = SparsePauliOp.from_operator(Operator(H_imag))
    pauli_diag = SparsePauliOp.from_operator(Operator(H_diag))

    ansatz = TwoLocal(2, ['ry'], 'cx', 'linear', reps=2)
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
    isa_ansatz = pm.run(ansatz)
    isa_diag = pauli_diag.apply_layout(isa_ansatz.layout)
    isa_real = pauli_real.apply_layout(isa_ansatz.layout)
    isa_imag = pauli_imag.apply_layout(isa_ansatz.layout)

    # Auto-extend params
    n_params = isa_ansatz.num_parameters
    init_p = INITIAL_PARAMS[:n_params] if len(INITIAL_PARAMS) >= n_params else \
             [INITIAL_PARAMS[i % len(INITIAL_PARAMS)] for i in range(n_params)]
    np.random.seed(42)
    theta_r = list(np.random.uniform(-np.pi, np.pi, n_params))

    estimator = Estimator(mode=backend)
    estimator.options.default_shots = SHOTS
    estimator.options.resilience_level = 0
    print(f"[{time.time()-t0:.0f}s] Estimator ready, submitting 1-Pub (H_diag am Initial-Punkt)...", flush=True)

    # 1 Pub: H_diag am Initial-Punkt
    job = estimator.run([(isa_ansatz, isa_diag, init_p)])
    print(f"[{time.time()-t0:.0f}s] Job submitted: {job.job_id()}", flush=True)
    result = job.result(timeout=600)
    H_diag_meas = result[0].data.evs
    print(f"[{time.time()-t0:.0f}s] H_diag (1-Pub) = {H_diag_meas:.4f}", flush=True)

    # 2. Pub: H_diag am random-Punkt
    job2 = estimator.run([(isa_ansatz, isa_diag, theta_r)])
    print(f"[{time.time()-t0:.0f}s] Job 2 submitted: {job2.job_id()}", flush=True)
    result2 = job2.result(timeout=600)
    H_diag_rand = result2[0].data.evs
    print(f"[{time.time()-t0:.0f}s] H_diag (random) = {H_diag_rand:.4f}", flush=True)

    # 3. Pub: Re(H_PT) am Initial-Punkt
    job3 = estimator.run([(isa_ansatz, isa_real, init_p)])
    print(f"[{time.time()-t0:.0f}s] Job 3 submitted: {job3.job_id()}", flush=True)
    result3 = job3.result(timeout=600)
    Re_PT_init = result3[0].data.evs
    print(f"[{time.time()-t0:.0f}s] Re(H_PT) (init) = {Re_PT_init:.4f}", flush=True)

    # Speichern
    bias_PT_re = Re_PT_init - H_diag_meas
    output = {
        "backend": "ibm_fez",
        "token": "TOKEN2 (neuer Account)",
        "shots": SHOTS,
        "H_diag_at_init": float(H_diag_meas),
        "H_diag_at_random": float(H_diag_rand),
        "Re_H_PT_at_init": float(Re_PT_init),
        "bias_PT_re": float(bias_PT_re),
        "abs_bias_PT_re": float(abs(bias_PT_re)),
        "verdict": "H1/H3" if abs(bias_PT_re) < 0.05 else ("H2" if abs(bias_PT_re) > 0.15 else "MITTEL"),
        "runtime_seconds": float(time.time() - t0),
        "note": "3 Pubs sequenziell (1 Pub pro Job wegen Fez-Queue-Optimierung)"
    }
    with open("pt_potential_vqe_singleshot_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n{'='*60}")
    print(f"ERGEBNIS:")
    print(f"  H_diag am Initial-Punkt: {H_diag_meas:.4f} (noiseless mean: 3.34)")
    print(f"  H_diag am random-Punkt:  {H_diag_rand:.4f}")
    print(f"  Re(H_PT) am Initial:     {Re_PT_init:.4f}")
    print(f"  bias_PT_re = {bias_PT_re:+.4f}")
    print(f"  |bias_PT_re| = {abs(bias_PT_re):.4f}")
    print(f"  VERDICT: {output['verdict']}")
    print(f"  Laufzeit: {time.time()-t0:.0f}s")
    print(f"{'='*60}")
    print(f"Ergebnisse gespeichert: pt_potential_vqe_singleshot_results.json", flush=True)


if __name__ == "__main__":
    main()
