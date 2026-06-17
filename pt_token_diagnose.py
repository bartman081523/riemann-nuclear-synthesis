"""
TOKEN-DIAGNOSE: Welcher Account hat QPU-Zeit?

Strategie:
  - Initialisiere Service mit TOKEN1, dann TOKEN2
  - Versuche fuer jeden: backend(ibm_fez).status(), dann minimaler 1-Pub-Submit
  - Bei Limit-Warnung: skip, der naechste Token wird versucht
  - Bei Erfolg: kurze Antwort zurueck, dann Abbruch
  - Output: JSON mit status_pro_token, plus ggf. job_id
"""
import json
import os
import sys
import traceback
import numpy as np

from pt_structural import jacobi_A, E_DIAG
from qiskit.circuit.library import n_local as n_local_fn
from qiskit.quantum_info import SparsePauliOp, Operator
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

BACKEND_NAME = "ibm_fez"
GAMMA = 0.02
SHOTS = 100  # minimal: 1 Sekunde QPU-Zeit


def load_token(name):
    with open(".env") as f:
        for line in f:
            if line.startswith(f"{name}="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError(f"Token {name} nicht in .env")


def check_token(token_name, token):
    """Initialisiert Service und prueft, ob QPU-Zeit verfuegbar ist."""
    result = {
        "token": token_name,
        "backend_status": None,
        "has_quota": None,
        "submit_error": None,
        "job_id": None,
    }
    try:
        service = QiskitRuntimeService(
            channel="ibm_quantum_platform", token=token
        )
        backend = service.backend(BACKEND_NAME)
        # Backend-Status (Queue, operational)
        try:
            status = backend.status()
            result["backend_status"] = {
                "operational": bool(status.operational),
                "pending_jobs": int(status.pending_jobs),
                "status_msg": str(status.status_msg),
            }
        except Exception as e:
            result["backend_status"] = {"error": str(e)}

        # Operator + Ansatz
        A = jacobi_A(E_DIAG, y=1.0)
        H_diag = np.diag(E_DIAG).astype(complex)
        H_PT = H_diag + 1j * GAMMA * A
        H_real = (H_PT + H_PT.conj().T) / 2
        pauli_real = SparsePauliOp.from_operator(Operator(H_real))

        ansatz = n_local_fn(2, ['ry'], 'cx', 'linear', reps=1)
        pm = generate_preset_pass_manager(
            optimization_level=3, backend=backend
        )
        isa_ansatz = pm.run(ansatz)
        isa_real = pauli_real.apply_layout(isa_ansatz.layout)

        estimator = Estimator(mode=backend)
        estimator.options.resilience_level = 1
        estimator.options.dynamical_decoupling.enable = True
        estimator.options.dynamical_decoupling.sequence_type = "XX"
        estimator.options.default_shots = SHOTS

        try:
            # 2 Qubits, 1 rep, ry+ry+cx-Struktur = 4 Parameter
            job = estimator.run([(isa_ansatz, isa_real, [0.5, 0.3, 0.7, 0.1])])
            result["job_id"] = str(job.job_id()) if hasattr(job, "job_id") else "submitted"
            result["has_quota"] = True
        except Exception as e:
            err_str = str(e)
            if "usage limit" in err_str or "Workloads will not run" in err_str:
                result["has_quota"] = False
                result["submit_error"] = "USAGE_LIMIT"
            else:
                result["has_quota"] = False
                result["submit_error"] = err_str[:200]
    except Exception as e:
        result["init_error"] = str(e)[:200]
    return result


def main():
    results = {
        "backend": BACKEND_NAME,
        "gamma": GAMMA,
        "shots": SHOTS,
        "tokens": [],
    }
    for tok_name in ["IBMQ_TOKEN", "IBMQ_TOKEN2"]:
        tok = load_token(tok_name)
        print(f"\n=== Teste {tok_name} ===")
        try:
            r = check_token(tok_name, tok)
        except Exception as e:
            traceback.print_exc()
            r = {"token": tok_name, "fatal": str(e)[:200]}
        results["tokens"].append(r)
        print(json.dumps(r, indent=2))
        # Wenn dieser Token funktioniert, sind wir fertig
        if r.get("has_quota") is True:
            print(f"\n>>> {tok_name} HAT QPU-ZEIT. Job-ID: {r.get('job_id')}")
            break
        else:
            print(f">>> {tok_name} blockiert: {r.get('submit_error', '?')}")

    with open("pt_token_diagnose.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nErgebnisse: pt_token_diagnose.json")

    # Welcher Token hat funktioniert?
    winner = next((t for t in results["tokens"] if t.get("has_quota")), None)
    if winner:
        print(f"\n*** GEWINNER: {winner['token']} ***")
    else:
        print(f"\n*** BEIDE TOKENS BLOCKIERT — Fallback auf GF(5)-Ququint noetig ***")


if __name__ == "__main__":
    main()
