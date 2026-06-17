"""
EXPERIMENT 015 (TOKEN2-Variante) - Im(H_PT) BIAS-SWEEP auf Fez/TOKEN2

Hintergrund: TOKEN1 in Quarantäne-Blockade. TOKEN2 seit 2026-06-17 17:15 UTC
wieder offen (DONE nach 1s bestätigt). Resubmit der 5 sequenziellen M1-Sweep-Jobs.

Strategie: 5 sequenzielle 1-Pub-Jobs, nicht parallel, damit
Kontingent nicht über Nacht aufgebraucht wird. Jeder Job ca. 1-2 Min.

Prereg: pt_im_bias_prereg.json (VOR main() geschrieben, 2026-06-17 12:35 UTC)
Korrektur: bias-Metrik = QPU-vs-statevector am SELBEN theta.
"""
import json
import os
import time
import sys
import numpy as np
from pt_structural import jacobi_A, E_DIAG
from qiskit.circuit.library import n_local as n_local_fn
from qiskit.quantum_info import Statevector, SparsePauliOp, Operator
from pt_token_diagnose import load_token

GAMMA = 0.02
SHOTS = 4096
INITIAL_PARAMS_4 = [0.523, 1.21, -0.45, 0.88]
N_THETA = 5
BACKEND_NAME = "ibm_fez"
INSTANCE = "open-instance"
TOKEN_NAME = "IBMQ_TOKEN2"


def cyclic_extend(params_4, n_target):
    return [params_4[i % len(params_4)] for i in range(n_target)]


def build_im_operator():
    A = jacobi_A(E_DIAG, y=1.0)
    H_diag = np.diag(E_DIAG).astype(complex)
    H_PT = H_diag + 1j * GAMMA * A
    H_imag = (H_PT - H_PT.conj().T) / (2j)
    return H_diag, H_imag


def submit_one(theta_4, label, idx, t0, ansatz, pauli_imag, service, backend, pm, n_params):
    """Reicht genau EINEN 1-Pub-Job ein und gibt job_id zurueck. Wartet NICHT auf Done."""
    from qiskit_ibm_runtime import EstimatorV2 as Estimator
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    isa_ansatz = pm.run(ansatz)
    isa_imag = pauli_imag.apply_layout(isa_ansatz.layout)

    theta = cyclic_extend(theta_4, n_params)
    print(f"[{time.time()-t0:.0f}s] === Job {idx+1}/{N_THETA}: Im(H_PT) bei {label} ===", flush=True)
    print(f"[{time.time()-t0:.0f}s]   theta = {[f'{t:+.3f}' for t in theta]}", flush=True)

    estimator = Estimator(mode=backend)
    estimator.options.default_shots = SHOTS
    estimator.options.resilience_level = 0
    try:
        estimator.options.dynamical_decoupling.enable = True
        estimator.options.dynamical_decoupling.sequence_type = "XX"
    except Exception as e:
        try:
            estimator.options.dynamical_decoupling.sequence = "XX"
        except Exception:
            print(f"[{time.time()-t0:.0f}s]   Warnung DD: {e}", flush=True)

    job = estimator.run([(isa_ansatz, isa_imag, theta)])
    jid = job.job_id()
    print(f"[{time.time()-t0:.0f}s]   SUBMITTED job_id={jid}", flush=True)
    return jid


def wait_and_fetch(jid, theta_4, label, idx, t0, ansatz, H_imag, sv_refs):
    """Wartet auf einen einzelnen Job und gibt Messwert zurueck."""
    from qiskit_ibm_runtime import QiskitRuntimeService
    from qiskit.quantum_info import Statevector

    tok = load_token(TOKEN_NAME)
    svc = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok)
    job = svc.job(jid)
    print(f"[{time.time()-t0:.0f}s]   Polling {jid} (initial: {job.status()})...", flush=True)

    # Polling in 15s-Schritten, max 10 Min
    for attempt in range(40):
        st = str(job.status())
        if st == "DONE":
            break
        if st in ("ERROR", "CANCELLED"):
            print(f"[{time.time()-t0:.0f}s]   Job {jid} endete mit status={st}", flush=True)
            return None
        time.sleep(15)
    else:
        print(f"[{time.time()-t0:.0f}s]   TIMEOUT nach 10 Min fuer {jid}", flush=True)
        return None

    result = job.result()
    ev_qpu = float(result[0].data.evs)

    # Statevector-Referenz am SELBEN theta-Punkt
    param_dict = {p: v for p, v in zip(ansatz.parameters, theta_4)}
    sv = Statevector.from_instruction(ansatz.assign_parameters(param_dict))
    ev_sv = float(np.real(sv.expectation_value(H_imag)))
    bias = ev_qpu - ev_sv

    print(f"[{time.time()-t0:.0f}s]   <Im>_QPU = {ev_qpu:+.6f}, <Im>_statevector = {ev_sv:+.6f}, "
          f"bias = {bias:+.6f}", flush=True)
    return {"qpu": ev_qpu, "sv": ev_sv, "bias": bias}


def main():
    from qiskit_ibm_runtime import QiskitRuntimeService
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    t0 = time.time()

    prereg = json.load(open("pt_im_bias_prereg.json"))
    print(f"[{time.time()-t0:.0f}s] Prereg geladen: H_Im_h1/h2/h3 + Entscheidungsregel", flush=True)

    # Theta-Punkte
    init_p_4 = INITIAL_PARAMS_4
    np.random.seed(42); theta_r1_4 = list(np.random.uniform(-np.pi, np.pi, 4))
    np.random.seed(43); theta_r2_4 = list(np.random.uniform(-np.pi, np.pi, 4))
    np.random.seed(44); theta_r3_4 = list(np.random.uniform(-np.pi, np.pi, 4))
    vqe_opt_4 = [-0.104, 0.317, -0.803, -0.086]
    theta_points_4 = [init_p_4, theta_r1_4, theta_r2_4, vqe_opt_4, theta_r3_4]
    theta_labels = ["theta_initial", "theta_random_1", "theta_random_2",
                    "theta_VQE_optimal", "theta_random_3"]
    print(f"[{time.time()-t0:.0f}s] {N_THETA} theta-Punkte vorbereitet", flush=True)

    # Im(H_PT) + Ansatz
    H_diag, H_imag = build_im_operator()
    pauli_imag = SparsePauliOp.from_operator(Operator(H_imag))
    ansatz = n_local_fn(2, ['ry'], 'cx', 'linear', reps=1)
    n_params = ansatz.num_parameters
    assert n_params == 4
    print(f"[{time.time()-t0:.0f}s] Im(H_PT) + Ansatz gebaut, n_params={n_params}", flush=True)

    # Service + Backend
    token = load_token(TOKEN_NAME)
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend(BACKEND_NAME, instance=INSTANCE)
    bstatus = backend.status()
    print(f"[{time.time()-t0:.0f}s] Backend: {BACKEND_NAME}, instance={INSTANCE}, "
          f"pending={bstatus.pending_jobs}", flush=True)

    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)

    # Argumente: welcher Job (1-basiert) oder "all"
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <idx|all>  (idx: 1..{N_THETA})", flush=True)
        sys.exit(1)
    arg = sys.argv[1]

    job_ids = [None] * N_THETA
    measurements = [None] * N_THETA

    if arg == "all":
        # SUBMIT alle 5 sequenziell, ohne zu warten
        print(f"[{time.time()-t0:.0f}s] SUBMITTE alle 5 sequenziell...", flush=True)
        for i, (theta_4, label) in enumerate(zip(theta_points_4, theta_labels)):
            jid = submit_one(theta_4, label, i, t0, ansatz, pauli_imag, service, backend, pm, n_params)
            job_ids[i] = jid
        # Speichere ID-Liste
        with open("pt_im_bias_token2_job_ids.json", "w") as f:
            json.dump({"job_ids": job_ids, "theta_labels": theta_labels,
                       "submitted_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}, f, indent=2)
        print(f"[{time.time()-t0:.0f}s] Alle {N_THETA} Jobs submitted, IDs gespeichert in "
              f"pt_im_bias_token2_job_ids.json", flush=True)
    else:
        idx = int(arg) - 1
        if idx < 0 or idx >= N_THETA:
            print(f"FEHLER: idx muss 1..{N_THETA} sein, bekam {idx+1}", flush=True)
            sys.exit(1)
        # Einzelner Job: SUBMIT + WAIT
        result_path = f"pt_im_bias_token2_job{idx+1}.json"
        jid = submit_one(theta_points_4[idx], theta_labels[idx], idx, t0,
                         ansatz, pauli_imag, service, backend, pm, n_params)
        job_ids[idx] = jid
        meas = wait_and_fetch(jid, theta_points_4[idx], theta_labels[idx], idx, t0,
                              ansatz, H_imag, sv_refs=None)
        measurements[idx] = meas
        out = {"job_id": jid, "label": theta_labels[idx], "theta": theta_points_4[idx],
               "measurement": meas, "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}
        with open(result_path, "w") as f:
            json.dump(out, f, indent=2)
        print(f"[{time.time()-t0:.0f}s] Gespeichert: {result_path}", flush=True)


if __name__ == "__main__":
    main()
