"""
EXPERIMENT 005 - MULTI-BACKEND BIAS-KALIBRIERUNG

Phase 1: Messe einen UNABHAENGIGEN Referenz-Operator
         H_ref = diag(1.0, 2.0, 3.0, 4.0)
         auf mehreren IBM-Backends.
         Erwarteter Erwartungswert: Mittelwert = 2.5, alle EWs reell.
         Beobachteter Wert: <H_ref>_HW
         Bias pro Backend: beta = <H_ref>_HW - 2.5

Phase 2: Messe den PT-Operator H_PT(gamma=0.02) auf den gleichen Backends.
         Roher HW-Wert: <Re(H_PT)>_HW (siehe Job d8j90eu6983c73dt1ek0 fuer Marrakesh)
         Korrigierter Wert: <Re(H_PT)>_HW - beta
         Vorhersage: 2.0019

Erfolgskriterium: |korrigierter Wert - 2.0019| < 0.1
                  auf MEHREREN Backends (>=3 von 4)

Backends: ibm_marrakesh, ibm_kingston, ibm_fez, ibm_torino
"""
import os
import numpy as np
from qiskit.circuit.library import TwoLocal
from qiskit.quantum_info import SparsePauliOp, Operator
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

# === KONFIGURATION ===
BACKENDS = ["ibm_marrakesh", "ibm_kingston", "ibm_fez", "ibm_torino"]
SHOTS = 8192
INITIAL_PARAMS = [0.523, 1.21, -0.45, 0.88]


def load_token():
    return open(".env").read().split("IBMQ_TOKEN=")[1].split("\n")[0]


def make_estimator(backend):
    """Estimator mit DD XX + TREX resilience 1, 8192 Shots."""
    est = Estimator(mode=backend)
    est.options.resilience_level = 1
    est.options.dynamical_decoupling.enable = True
    est.options.dynamical_decoupling.sequence_type = "XX"
    est.options.default_shots = SHOTS
    return est


def make_isa_ansatz(backend):
    """TwoLocal(2, ry, cx, linear, reps=1) - 4 Parameter."""
    ansatz = TwoLocal(2, ['ry'], 'cx', 'linear', reps=1)
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    isa_ansatz = pm.run(ansatz)
    return isa_ansatz


def submit_measurement(estimator, isa_ansatz, observable, label, log_file, backend_name):
    """Misst <observable> fuer gegebenen Ansatz + Parameter."""
    isa_obs = observable.apply_layout(isa_ansatz.layout)
    try:
        job = estimator.run([(isa_ansatz, isa_obs, INITIAL_PARAMS)])
        with open(log_file, "a") as f:
            f.write(f"{label}: job_id={job.job_id()}, backend={backend_name}\n")
        return job
    except Exception as e:
        print(f"  FEHLER bei {label}: {e}")
        return None


def main():
    token = load_token()
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)

    # Pruefe welche Backends verfuegbar sind
    available = []
    for bname in BACKENDS:
        try:
            b = service.backend(bname)
            if b.status().operational:
                available.append(b)
                print(f"  {bname}: operational")
            else:
                print(f"  {bname}: NICHT operational ({b.status().status_msg})")
        except Exception as e:
            print(f"  {bname}: nicht verfuegbar ({e})")

    print(f"\n{len(available)}/{len(BACKENDS)} Backends verfuegbar.")
    if len(available) < 2:
        print("FEHLER: zu wenig Backends.")
        return

    # === H_ref = diag(1.0, 2.0, 3.0, 4.0) ===
    # Erwarteter Erwartungswert = (1+2+3+4)/4 = 2.5 (bei uniformem Ansatz)
    # Tatsaechlich haengt der Erwartungswert von den Initial-Parametern ab
    # Wir messen ihn und vergleichen mit dem gleichen Setup wie H_PT spaeter
    H_ref = np.diag([1.0, 2.0, 3.0, 4.0]).astype(complex)
    pauli_ref = SparsePauliOp.from_operator(Operator(H_ref))

    log_file = "multi_backend_calibration_log.txt"
    open(log_file, "w").close()  # leeren

    # Phase 1: H_ref Kalibrierungsmessung
    print("\n" + "=" * 70)
    print("PHASE 1: H_ref KALIBRIERUNG AUF ALLEN BACKENDS")
    print("=" * 70)

    ref_jobs = {}
    for backend in available:
        print(f"\n--- {backend.name} ---")
        try:
            isa_ansatz = make_isa_ansatz(backend)
            estimator = make_estimator(backend)
            job = submit_measurement(estimator, isa_ansatz, pauli_ref,
                                    f"H_ref@{backend.name}", log_file, backend.name)
            if job:
                ref_jobs[backend.name] = job
                print(f"  Job submitted: {job.job_id()}")
        except Exception as e:
            print(f"  FEHLER: {e}")

    # Speichere Job-IDs
    with open("multi_backend_jobs.json", "w") as f:
        import json
        json.dump({b: j.job_id() for b, j in ref_jobs.items()}, f, indent=2)

    print(f"\n{len(ref_jobs)} Kalibrierungs-Jobs gesendet.")
    print(f"Warte auf Fertigstellung, dann Phase 2...")


if __name__ == "__main__":
    main()
