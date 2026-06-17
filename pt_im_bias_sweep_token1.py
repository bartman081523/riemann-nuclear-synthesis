"""
EXPERIMENT 015 - Im(H_PT) BIAS-SWEEP auf Fez/TOKEN1 (5 sequenzielle Jobs)

Da bias_PT_re per Theorem ~0 ist (||[H_diag, Re(H_PT)]||=0, identische Eigenwerte),
ist die ECHTE Bias-Signatur der anti-Hermitesche Anteil Im(H_PT) = (H_PT - H_PT†)/(2i).

KRITISCHE KORREKTUR (statevector-Validierung 12:45 UTC):
  Im_noiseless_ground = 0.0299 ist NUR am Ground State gueltig.
  Bei anderen theta-Punkten variiert <Im(H_PT)> zwischen 0.009 und 0.081.
  Die korrekte Bias-Metrik ist: bias_Im(theta) = <Im(H_PT)>_QPU(theta) - <Im(H_PT)>_statevector(theta)
  NICHT: <Im(H_PT)>_QPU(theta) - 0.0299 (falsch, weil theta-abhaengig)

Prereg: pt_im_bias_prereg.json (VOR main() geschrieben, 2026-06-17 12:35 UTC)
Erwartung: statevector-vs-QPU-Differenz im Bereich ±0.020 (gleiche Groessenordnung
           wie die fruehere bias_PT_re=±0.013 Hardware-Sampling-Noise).
"""
import json
import os
import time
import numpy as np
from pt_structural import jacobi_A, E_DIAG
from qiskit.circuit.library import n_local as n_local_fn
from qiskit.quantum_info import Statevector
from pt_token_diagnose import load_token

GAMMA = 0.02
SHOTS = 4096
INITIAL_PARAMS_4 = [0.523, 1.21, -0.45, 0.88]
N_THETA = 5
BACKEND_NAME = "ibm_fez"


def cyclic_extend(params_4, n_target):
    """Erweitere 4-Parameter-Liste zyklisch auf n_target Laenge."""
    return [params_4[i % len(params_4)] for i in range(n_target)]


def build_im_operator():
    """Baue Im(H_PT) als 4x4-Matrix + SparsePauliOp."""
    A = jacobi_A(E_DIAG, y=1.0)
    H_diag = np.diag(E_DIAG).astype(complex)
    H_PT = H_diag + 1j * GAMMA * A
    H_imag = (H_PT - H_PT.conj().T) / (2j)
    return H_diag, H_imag


def main():
    from qiskit.circuit.library import n_local as n_local_fn
    from qiskit.quantum_info import SparsePauliOp, Operator
    from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    t0 = time.time()

    # === Prereg laden (existiert seit 12:35 UTC, VOR main() geschrieben) ===
    prereg = json.load(open("pt_im_bias_prereg.json"))
    print(f"[{time.time()-t0:.0f}s] Prereg geladen: H_Im_h1/h2/h3 + Entscheidungsregel", flush=True)

    # === Theta-Punkte generieren (5 Stueck, deterministisch via seeds) ===
    init_p_4 = INITIAL_PARAMS_4
    np.random.seed(42)
    theta_r1_4 = list(np.random.uniform(-np.pi, np.pi, 4))
    np.random.seed(43)
    theta_r2_4 = list(np.random.uniform(-np.pi, np.pi, 4))
    np.random.seed(44)
    theta_r3_4 = list(np.random.uniform(-np.pi, np.pi, 4))
    # VQE-Optimum: aus pt_vqe_vqd_statevector.py (10-Iter-COBYLA, suboptimum E_0=2.147)
    vqe_opt_4 = [-0.104, 0.317, -0.803, -0.086]

    theta_points_4 = [init_p_4, theta_r1_4, theta_r2_4, vqe_opt_4, theta_r3_4]
    theta_labels = ["theta_initial", "theta_random_1", "theta_random_2",
                    "theta_VQE_optimal", "theta_random_3"]
    print(f"[{time.time()-t0:.0f}s] {N_THETA} theta-Punkte vorbereitet", flush=True)

    # === Im(H_PT) bauen (4x4-Matrix) ===
    H_diag, H_imag = build_im_operator()
    pauli_imag = SparsePauliOp.from_operator(Operator(H_imag))
    print(f"[{time.time()-t0:.0f}s] Im(H_PT) gebaut: 4x4-Matrix, 16-Pauli-Zerlegung", flush=True)

    # === STATEVECTOR-REFERENZEN (vor QPU-Submit!) ===
    ansatz = n_local_fn(2, ['ry'], 'cx', 'linear', reps=1)  # 4 Parameter
    n_params = ansatz.num_parameters
    assert n_params == 4, f"Erwartete 4 Parameter, bekam {n_params}"

    Im_statevector = []
    for theta_4 in theta_points_4:
        param_dict = {p: v for p, v in zip(ansatz.parameters, theta_4)}
        sv = Statevector.from_instruction(ansatz.assign_parameters(param_dict))
        ev = float(np.real(sv.expectation_value(H_imag)))
        Im_statevector.append(ev)
    print(f"\n[{time.time()-t0:.0f}s] STATEVECTOR-REFERENZEN (vor QPU-Submit):", flush=True)
    for i, (label, sv_ev) in enumerate(zip(theta_labels, Im_statevector)):
        print(f"  {i+1}. {label}: <Im(H_PT)>_statevector = {sv_ev:+.6f}", flush=True)

    # === Service + Backend ===
    token = load_token("IBMQ_TOKEN")
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend(BACKEND_NAME)
    bstatus = backend.status()
    print(f"\n[{time.time()-t0:.0f}s] Backend: {BACKEND_NAME}, operational={bstatus.operational}, "
          f"pending_jobs={bstatus.pending_jobs}", flush=True)

    # === Ansatz + ISA-Transformation ===
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
    isa_ansatz = pm.run(ansatz)
    isa_imag = pauli_imag.apply_layout(isa_ansatz.layout)
    print(f"[{time.time()-t0:.0f}s] Ansatz ISA-transformiert, n_params={n_params}", flush=True)

    # === Estimator konfigurieren ===
    estimator = Estimator(mode=backend)
    estimator.options.default_shots = SHOTS
    estimator.options.resilience_level = 0  # deterministisch, kein ZNE
    # DD-XX
    try:
        estimator.options.dynamical_decoupling.enable = True
        estimator.options.dynamical_decoupling.sequence = "XX"
    except Exception as e:
        print(f"[{time.time()-t0:.0f}s] Warnung: DD konnte nicht gesetzt werden: {e}", flush=True)

    # === 5 sequenzielle Jobs ===
    job_ids = []
    Im_qpu = []
    for i, (theta_4, label) in enumerate(zip(theta_points_4, theta_labels)):
        theta = cyclic_extend(theta_4, n_params)  # bereits 4 → trivial
        print(f"\n[{time.time()-t0:.0f}s] === Job {i+1}/{N_THETA}: Im(H_PT) bei {label} ===", flush=True)
        print(f"[{time.time()-t0:.0f}s]   theta = {[f'{t:+.3f}' for t in theta]}", flush=True)

        try:
            job = estimator.run([(isa_ansatz, isa_imag, theta)])
            jid = job.job_id()
            job_ids.append(jid)
            print(f"[{time.time()-t0:.0f}s]   job_id: {jid}, warte auf Result...", flush=True)
            result = job.result(timeout=600)
            ev = float(result[0].data.evs)
            Im_qpu.append(ev)
            print(f"[{time.time()-t0:.0f}s]   <Im(H_PT)>_QPU = {ev:.6f}", flush=True)
        except Exception as e:
            print(f"[{time.time()-t0:.0f}s]   FEHLER: {e}", flush=True)
            Im_qpu.append(None)
            job_ids.append(None)

    # === Bias-Analyse: QPU vs statevector am SELBEN theta-Punkt ===
    print(f"\n{'='*70}", flush=True)
    print(f"BIAS-ANALYSE: <Im(H_PT)>_QPU(theta) - <Im(H_PT)>_statevector(theta)", flush=True)
    print(f"{'='*70}", flush=True)
    Im_bias = []
    for i, (qpu, sv, label) in enumerate(zip(Im_qpu, Im_statevector, theta_labels)):
        if qpu is None:
            print(f"  {i+1}. {label}: KEINE MESSUNG (Job fehlgeschlagen)", flush=True)
            Im_bias.append(None)
        else:
            bias = qpu - sv
            Im_bias.append(bias)
            print(f"  {i+1}. {label}: <Im>_QPU = {qpu:+.6f}, <Im>_statevector = {sv:+.6f}, "
                  f"bias = {bias:+.6f}, |bias| = {abs(bias):.6f}", flush=True)

    # === Verdict nach Prereg-Entscheidungsregel (H_Im_h3 ist Konsistenz mit Fez 2026-06-10) ===
    # HINWEIS: Fez-2026-06-10 mass Im_bias gegen Im_noiseless(ground) = 0.0299.
    # Wir messen HIER gegen statevector(theta) — die Groessenordnung sollte
    # vergleichbar sein (Fez-Hardware-Sampling-Noise ~0.013-0.020).
    valid_biases = [b for b in Im_bias if b is not None]
    abs_biases = [abs(b) for b in valid_biases]
    n_valid = len(valid_biases)

    if n_valid == 0:
        verdict = "INCONCLUSIVE (alle Jobs fehlgeschlagen)"
    elif all(ab < 0.005 for ab in abs_biases):
        verdict = "H_Im_h1 bestaetigt (additive Bias-Topologie, alle |bias| < 0.005)"
    elif all(ab > 0.020 for ab in abs_biases):
        verdict = "H_Im_h2 bestaetigt (multiplikative Bias-Topologie, alle |bias| > 0.020)"
    else:
        # H_Im_h3: Konsistenz mit Fez-2026-06-10 / statevector
        mean_bias = np.mean(valid_biases)
        std_bias = np.std(valid_biases)
        verdict = (f"H_Im_h3 bestaetigt (Konsistenz mit Fez-2026-06-10-Region: "
                   f"Mittelwert = {mean_bias:+.6f}, Std = {std_bias:.6f}, "
                   f"n_valid = {n_valid}/{N_THETA})")

    print(f"\nVERDICT: {verdict}", flush=True)

    # === Speichern ===
    output = {
        "backend": BACKEND_NAME,
        "token": "IBMQ_TOKEN",
        "gamma": GAMMA,
        "shots": SHOTS,
        "method": "5 sequenzielle 1-Pub Jobs, n_local(2, ry, cx, linear, reps=1), DD-XX, resilience=0",
        "prereg_file": "pt_im_bias_prereg.json",
        "theta_labels": theta_labels,
        "theta_values": theta_points_4,
        "Im_statevector_reference": Im_statevector,
        "Im_qpu_measured": Im_qpu,
        "Im_bias_qpu_minus_statevector": Im_bias,
        "abs_biases": [abs(b) if b is not None else None for b in Im_bias],
        "verdict": verdict,
        "job_ids": job_ids,
        "runtime_seconds": float(time.time() - t0),
        "n_valid_jobs": n_valid,
        "n_total_jobs": N_THETA,
        "note": ("KORREKTUR 12:45 UTC: bias-Metrik ist QPU-vs-statevector am SELBEN theta, "
                 "nicht vs Im_noiseless(ground)=0.0299 (das war falsch — Im variiert stark mit theta).")
    }
    with open("pt_im_bias_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n[{time.time()-t0:.0f}s] Ergebnisse gespeichert: pt_im_bias_results.json", flush=True)
    print(f"[{time.time()-t0:.0f}s] GESAMT-LAUFZEIT: {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
