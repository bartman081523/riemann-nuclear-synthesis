"""
EXPERIMENT 012b - MINIMAL-VARIANTE für TOKEN2 (neuer Account, Tageslimit 10 Min).

Spart QPU-Zeit gegenüber pt_potential_vqe.py:
  - SHOTS 2048 statt 8192 (4x weniger)
  - N_ITERS_VQE 3 statt 10 (3x weniger)
  - 5-Pub-Messung wie Original

Gesamt-QPU-Zeit-Schätzung: ~2-3 Min (passt ins Tageslimit 10 Min).

Verwendet die gleichen strukturellen Operatoren und die gleiche Pre-Registrierung.
"""
import json
import os
import numpy as np
from scipy.optimize import minimize
from pt_structural import jacobi_A, E_DIAG

BACKEND_NAME = "ibm_fez"
GAMMA = 0.02
SHOTS = 2048  # reduziert
N_ITERS_VQE = 3  # reduziert
INITIAL_PARAMS = [0.523, 1.21, -0.45, 0.88]


def load_token():
    """Lade TOKEN2 (neuer Account)."""
    content = open(".env").read()
    return content.split("IBMQ_TOKEN2=")[1].split("\n")[0]


def main():
    from qiskit.circuit.library import TwoLocal
    from qiskit.quantum_info import SparsePauliOp, Operator
    from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    import time

    t0 = time.time()
    print(f"[{time.time()-t0:.0f}s] Starting pt_potential_vqe_minimal.py", flush=True)
    print(f"[{time.time()-t0:.0f}s] SHOTS={SHOTS}, N_ITERS_VQE={N_ITERS_VQE}", flush=True)

    token = load_token()
    print(f"[{time.time()-t0:.0f}s] Token loaded (len={len(token)})", flush=True)

    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend(BACKEND_NAME)
    print(f"[{time.time()-t0:.0f}s] Backend: {BACKEND_NAME}, queue={backend.status().pending_jobs}", flush=True)

    # === Pre-Registrierung (kopiere von Original) ===
    prereg = {}
    if os.path.exists("pt_potential_vqe_prereg.json"):
        with open("pt_potential_vqe_prereg.json") as f:
            prereg = json.load(f)
    print(f"[{time.time()-t0:.0f}s] Prereg loaded: H_diag_exact gaps = {prereg['H_diag_exact']['Delta']}", flush=True)

    # === Operatoren ===
    A = jacobi_A(E_DIAG, y=1.0)
    H_diag = np.diag(E_DIAG).astype(complex)
    H_PT = H_diag + 1j * GAMMA * A
    H_real = (H_PT + H_PT.conj().T) / 2
    H_imag = (H_PT - H_PT.conj().T) / (2j)
    pauli_real = SparsePauliOp.from_operator(Operator(H_real))
    pauli_imag = SparsePauliOp.from_operator(Operator(H_imag))
    pauli_diag = SparsePauliOp.from_operator(Operator(H_diag))

    # === Ansatz + ISA ===
    ansatz = TwoLocal(2, ['ry'], 'cx', 'linear', reps=2)
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)  # opt=1 schneller
    print(f"[{time.time()-t0:.0f}s] Pass manager built (opt_level=1)", flush=True)
    isa_ansatz = pm.run(ansatz)
    isa_real = pauli_real.apply_layout(isa_ansatz.layout)
    isa_imag = pauli_imag.apply_layout(isa_ansatz.layout)
    isa_diag = pauli_diag.apply_layout(isa_ansatz.layout)
    print(f"[{time.time()-t0:.0f}s] ISA built: n_params={isa_ansatz.num_parameters}, depth={isa_ansatz.depth()}", flush=True)

    n_params = isa_ansatz.num_parameters
    initial_params = list(INITIAL_PARAMS)
    if len(initial_params) < n_params:
        initial_params = [initial_params[i % len(initial_params)] for i in range(n_params)]
    print(f"[{time.time()-t0:.0f}s] initial_params: {initial_params}", flush=True)

    # === Estimator ===
    estimator = Estimator(mode=backend)
    estimator.options.resilience_level = 1
    estimator.options.dynamical_decoupling.enable = True
    estimator.options.dynamical_decoupling.sequence_type = "XX"
    estimator.options.default_shots = SHOTS
    print(f"[{time.time()-t0:.0f}s] Estimator configured", flush=True)

    def cost_real(params):
        result = estimator.run([(isa_ansatz, isa_real, list(params))]).result()
        return result[0].data.evs

    # === VQE (nur 3 Iter) ===
    print(f"\n[{time.time()-t0:.0f}s] === VQE START ({N_ITERS_VQE} Iter) ===", flush=True)
    res_vqe = minimize(
        fun=cost_real,
        x0=initial_params,
        method='COBYLA',
        options={'maxiter': N_ITERS_VQE, 'rhobeg': 0.5, 'disp': False}
    )
    E0_meas = res_vqe.fun
    E0_params = res_vqe.x.tolist()
    print(f"[{time.time()-t0:.0f}s] VQE done: E_0 = {E0_meas:.4f} (noiseless {prereg['noiseless']['E'][0]:.4f})", flush=True)

    # === 5-Pub-Messung ===
    print(f"\n[{time.time()-t0:.0f}s] === 5-PUB MESSUNG ===", flush=True)
    np.random.seed(42)
    theta_r = list(np.random.uniform(-np.pi, np.pi, 4))

    result = estimator.run([
        (isa_ansatz, isa_diag, E0_params),
        (isa_ansatz, isa_real, E0_params),
        (isa_ansatz, isa_imag, E0_params),
        (isa_ansatz, isa_real, theta_r),
        (isa_ansatz, isa_imag, theta_r)
    ]).result()
    H_diag_meas = result[0].data.evs
    Re_PT_meas = result[1].data.evs
    Im_PT_meas = result[2].data.evs
    Re_PT_rand = result[3].data.evs
    Im_PT_rand = result[4].data.evs
    print(f"[{time.time()-t0:.0f}s] 5-Pub done", flush=True)

    # === Bias-Analyse ===
    beta_diag = H_diag_meas - 3.3412
    bias_PT_re = Re_PT_meas - H_diag_meas
    Im_at_ground = prereg['noiseless']['Im'][0]
    Im_bias = Im_PT_meas - Im_at_ground

    print(f"\n{'='*60}")
    print(f"ERGEBNIS: {BACKEND_NAME} (TOKEN2, neuer Account)")
    print(f"  VQE E_0 = {E0_meas:.4f} (noiseless: {prereg['noiseless']['E'][0]:.4f})")
    print(f"  <H_diag> = {H_diag_meas:.4f}")
    print(f"  <Re(H_PT)> = {Re_PT_meas:.4f}")
    print(f"  <Im(H_PT)> = {Im_PT_meas:.4f}")
    print(f"  bias_PT_re = {bias_PT_re:+.4f}  <-- ENTSCHEIDEND")
    print(f"  beta_diag  = {beta_diag:+.4f}")
    print(f"  Im_bias    = {Im_bias:+.4f}")
    print(f"  |bias_PT_re| = {abs(bias_PT_re):.4f}")
    if abs(bias_PT_re) < 0.05:
        verdict = "H1/H3 (gaps invariant) — REFRAMING_VECTOR bestaetigt!"
    elif abs(bias_PT_re) > 0.15:
        verdict = "H2 (multiplikative Bias) — REFRAMING_VECTOR widerlegt"
    else:
        verdict = "MITTEL — partial H2-Einfluss"
    print(f"  VERDICT: {verdict}")
    print(f"  Laufzeit: {time.time()-t0:.0f}s")
    print(f"{'='*60}", flush=True)

    # === Speichern ===
    output = {
        "backend": BACKEND_NAME,
        "token": "TOKEN2 (neuer Account)",
        "gamma": GAMMA,
        "shots": SHOTS,
        "n_iter_vqe": N_ITERS_VQE,
        "vqe_result": {
            "E0_meas": float(E0_meas),
            "E0_params": E0_params,
            "n_iterations": int(res_vqe.nfev),
            "E0_noiseless": float(prereg['noiseless']['E'][0])
        },
        "5_pubs": {
            "H_diag_at_vqe_opt": float(H_diag_meas),
            "Re_H_PT_at_vqe_opt": float(Re_PT_meas),
            "Im_H_PT_at_vqe_opt": float(Im_PT_meas),
            "Re_H_PT_at_random": float(Re_PT_rand),
            "Im_H_PT_at_random": float(Im_PT_rand)
        },
        "bias_analysis": {
            "beta_diag": float(beta_diag),
            "bias_PT_re": float(bias_PT_re),
            "Im_bias": float(Im_bias)
        },
        "verdict": verdict,
        "runtime_seconds": float(time.time() - t0),
        "predictions": prereg
    }
    with open("pt_potential_vqe_minimal_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nErgebnisse gespeichert: pt_potential_vqe_minimal_results.json", flush=True)


if __name__ == "__main__":
    main()
