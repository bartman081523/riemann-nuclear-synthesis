"""
EXPERIMENT 016 - INITIAL-PUNKT-REPRODUZIERBARKEIT AUF TOKEN1 (3 Pubs)

Wiederholung des 2026-06-10 #1 Singleshot (TOKEN2) auf TOKEN1 (anderer Account).
Drei Pubs am Initial-Punkt: H_diag, Re(H_PT), Im(H_PT).

Ziel: Verifizieren, dass der bias_PT_re = -0.0133 (Fez 2026-06-10) Account-stabil ist.
     Wenn auch TOKEN1 ~-0.013 ergibt: Bias ist Hardware-strukturell, nicht Account-spezifisch.

Sekundaer: Im-Bias am Initial-Punkt (eine QPU-Messung) als Ankerpunkt fuer M1.
"""
import json
import time
import numpy as np
from pt_structural import jacobi_A, E_DIAG
from pt_token_diagnose import load_token

GAMMA = 0.02
SHOTS = 1024
INITIAL_PARAMS_4 = [0.523, 1.21, -0.45, 0.88]
BACKEND_NAME = "ibm_fez"


def build_operators():
    """Baue H_diag, Re(H_PT), Im(H_PT)."""
    A = jacobi_A(E_DIAG, y=1.0)
    H_diag = np.diag(E_DIAG).astype(complex)
    H_PT = H_diag + 1j * GAMMA * A
    H_real = (H_PT + H_PT.conj().T) / 2
    H_imag = (H_PT - H_PT.conj().T) / (2j)
    return H_diag, H_real, H_imag


def main():
    from qiskit.circuit.library import n_local as n_local_fn
    from qiskit.quantum_info import SparsePauliOp, Operator, Statevector
    from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    t0 = time.time()
    token = load_token("IBMQ_TOKEN")
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend(BACKEND_NAME)
    print(f"[{time.time()-t0:.0f}s] Backend: {BACKEND_NAME}, queue={backend.status().pending_jobs}", flush=True)

    # === Operatoren ===
    H_diag, H_real, H_imag = build_operators()
    pauli_diag = SparsePauliOp.from_operator(Operator(H_diag))
    pauli_real = SparsePauliOp.from_operator(Operator(H_real))
    pauli_imag = SparsePauliOp.from_operator(Operator(H_imag))

    # === Statevector-Referenz (vor QPU) ===
    ansatz = n_local_fn(2, ['ry'], 'cx', 'linear', reps=1)
    n_params = ansatz.num_parameters
    init_p = INITIAL_PARAMS_4
    pd = {p: v for p, v in zip(ansatz.parameters, init_p)}
    sv = Statevector.from_instruction(ansatz.assign_parameters(pd))
    sv_diag = float(np.real(sv.expectation_value(H_diag)))
    sv_real = float(np.real(sv.expectation_value(H_real)))
    sv_imag = float(np.real(sv.expectation_value(H_imag)))
    print(f"\n[{time.time()-t0:.0f}s] STATEVECTOR-REFERENZ am Initial-Punkt:", flush=True)
    print(f"  <H_diag>_sv   = {sv_diag:+.6f}", flush=True)
    print(f"  <Re(H_PT)>_sv = {sv_real:+.6f}", flush=True)
    print(f"  <Im(H_PT)>_sv = {sv_imag:+.6f}", flush=True)

    # === ISA ===
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
    isa_ansatz = pm.run(ansatz)
    isa_diag = pauli_diag.apply_layout(isa_ansatz.layout)
    isa_real = pauli_real.apply_layout(isa_ansatz.layout)
    isa_imag = pauli_imag.apply_layout(isa_ansatz.layout)

    # === Estimator ===
    estimator = Estimator(mode=backend)
    estimator.options.default_shots = SHOTS
    estimator.options.resilience_level = 0
    try:
        estimator.options.dynamical_decoupling.enable = True
        estimator.options.dynamical_decoupling.sequence = "XX"
    except Exception as e:
        print(f"[{time.time()-t0:.0f}s] Warnung: DD: {e}", flush=True)

    # === 3 sequenzielle 1-Pub Jobs ===
    job_ids = []
    meas = {}
    for name, isa_op in [("H_diag", isa_diag), ("Re_H_PT", isa_real), ("Im_H_PT", isa_imag)]:
        print(f"\n[{time.time()-t0:.0f}s] === Job: {name} am Initial-Punkt ===", flush=True)
        try:
            job = estimator.run([(isa_ansatz, isa_op, init_p)])
            jid = job.job_id()
            job_ids.append(jid)
            print(f"[{time.time()-t0:.0f}s]   job_id: {jid}", flush=True)
            result = job.result(timeout=600)
            ev = float(result[0].data.evs)
            meas[name] = ev
            print(f"[{time.time()-t0:.0f}s]   <{name}> = {ev:.6f}", flush=True)
        except Exception as e:
            print(f"[{time.time()-t0:.0f}s]   FEHLER: {e}", flush=True)
            meas[name] = None
            job_ids.append(None)

    # === Bias-Analyse ===
    print(f"\n{'='*70}", flush=True)
    print(f"BIAS-ANALYSE: QPU vs statevector am Initial-Punkt", flush=True)
    print(f"{'='*70}", flush=True)
    biases = {}
    for name, sv_val in [("H_diag", sv_diag), ("Re_H_PT", sv_real), ("Im_H_PT", sv_imag)]:
        qpu_val = meas.get(name)
        if qpu_val is not None:
            bias = qpu_val - sv_val
            biases[name] = bias
            print(f"  {name}: QPU = {qpu_val:+.6f}, SV = {sv_val:+.6f}, bias = {bias:+.6f}", flush=True)
        else:
            print(f"  {name}: KEINE MESSUNG", flush=True)
            biases[name] = None

    # === Vergleich mit Fez-2026-06-10 (TOKEN2) ===
    print(f"\nVERGLEICH MIT Fez-2026-06-10 (TOKEN2):", flush=True)
    print(f"  bias_PT_re (TOKEN2) = -0.0133 (1024 shots, Initial-Punkt)", flush=True)
    if biases.get("Re_H_PT") is not None:
        b = biases["Re_H_PT"]
        match_token2 = abs(b - (-0.0133)) < 0.05  # ±0.05 Toleranz
        print(f"  bias_PT_re (TOKEN1) = {b:+.6f}  -> {'KONSISTENT' if match_token2 else 'ABWEICHEND'}", flush=True)
        verdict_token_comparison = "KONSISTENT" if match_token2 else "ABWEICHEND"
    else:
        verdict_token_comparison = "INCONCLUSIVE"

    # === Speichern ===
    output = {
        "backend": BACKEND_NAME,
        "token": "IBMQ_TOKEN",
        "gamma": GAMMA,
        "shots": SHOTS,
        "method": "3 sequenzielle 1-Pub Jobs am Initial-Punkt, n_local(2, ry, cx, linear, reps=1), DD-XX",
        "theta": INITIAL_PARAMS_4,
        "statevector_reference": {"H_diag": sv_diag, "Re_H_PT": sv_real, "Im_H_PT": sv_imag},
        "qpu_measured": meas,
        "bias_qpu_minus_statevector": biases,
        "fez_2026_06_10_token2_reference": {
            "bias_PT_re": -0.0133,
            "vergleich_verdict": verdict_token_comparison
        },
        "job_ids": job_ids,
        "verdict": f"bias_PT_re TOKEN1 vs TOKEN2: {verdict_token_comparison}",
        "runtime_seconds": float(time.time() - t0)
    }
    with open("pt_potential_vqe_initial_token1_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n[{time.time()-t0:.0f}s] Ergebnisse gespeichert: pt_potential_vqe_initial_token1_results.json", flush=True)
    print(f"[{time.time()-t0:.0f}s] GESAMT-LAUFZEIT: {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
