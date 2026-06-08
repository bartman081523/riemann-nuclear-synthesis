"""
PHASE 2: H_PT Messung auf den gleichen 3 Backends wie H_ref.
Lauft parallel zu H_ref-Messungen - keine Konflikte (andere Jobs).
"""
import os
import json
import numpy as np
from pt_structural import jacobi_A, E_DIAG
from qiskit.circuit.library import TwoLocal
from qiskit.quantum_info import SparsePauliOp, Operator
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

GAMMA = 0.02
INITIAL_PARAMS = [0.523, 1.21, -0.45, 0.88]


def load_token():
    return open(".env").read().split("IBMQ_TOKEN=")[1].split("\n")[0]


def main():
    token = load_token()
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)

    A = jacobi_A(E_DIAG, y=1.0)
    H_diag = np.diag(E_DIAG).astype(complex)
    H_PT = H_diag + 1j * GAMMA * A
    H_real = (H_PT + H_PT.conj().T) / 2
    H_imag = (H_PT - H_PT.conj().T) / (2j)
    pauli_real = SparsePauliOp.from_operator(Operator(H_real))
    pauli_imag = SparsePauliOp.from_operator(Operator(H_imag))

    backends = ["ibm_marrakesh", "ibm_kingston", "ibm_fez"]
    log_file = "multi_backend_pt_log.txt"
    open(log_file, "w").close()

    pt_jobs = {}
    for bname in backends:
        print(f"--- {bname} ---")
        try:
            backend = service.backend(bname)
            if not backend.status().operational:
                print(f"  nicht operational, skip")
                continue
            ansatz = TwoLocal(2, ['ry'], 'cx', 'linear', reps=1)
            pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
            isa_ansatz = pm.run(ansatz)
            est = Estimator(mode=backend)
            est.options.resilience_level = 1
            est.options.dynamical_decoupling.enable = True
            est.options.dynamical_decoupling.sequence_type = "XX"
            est.options.default_shots = 8192
            isa_real = pauli_real.apply_layout(isa_ansatz.layout)
            isa_imag = pauli_imag.apply_layout(isa_ansatz.layout)
            job = est.run([
                (isa_ansatz, isa_real, INITIAL_PARAMS),
                (isa_ansatz, isa_imag, INITIAL_PARAMS)
            ])
            pt_jobs[bname] = job.job_id()
            print(f"  Job ID: {job.job_id()}")
            with open(log_file, "a") as f:
                f.write(f"H_PT@{bname}: {job.job_id()}\n")
        except Exception as e:
            print(f"  FEHLER: {e}")

    with open("multi_backend_pt_jobs.json", "w") as f:
        json.dump(pt_jobs, f, indent=2)

    eigs = sorted(np.linalg.eigvals(H_PT), key=lambda z: z.real)
    E0_pred = eigs[0]
    with open("multi_backend_prediction.json", "w") as f:
        json.dump({
            "Re_E0_predicted": float(E0_pred.real),
            "Im_E0_predicted": float(E0_pred.imag),
            "gamma": GAMMA,
            "params": INITIAL_PARAMS
        }, f, indent=2)

    print(f"\n{len(pt_jobs)} H_PT Jobs gesendet.")
    print(f"Vorhersage: Re(E_0) = {E0_pred.real:.4f}, Im(E_0) = {E0_pred.imag:.4f}")


if __name__ == "__main__":
    main()
