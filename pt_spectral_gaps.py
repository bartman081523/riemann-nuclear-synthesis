"""
EXPERIMENT 006 v4 - PRÄREGISTRIERTER GROUND-TRUTH-RUN

Drei konkurrierende Bias-Topologien H1/H2/H3 mit VORHER festgelegten
Vorhersagen für die gemessenen Erwartungswerte und die daraus
abgeleiteten Niveauabstände ΔE_n.

Pre-Registrierung (SciMind 4.0 Anti-Sharpshooter):
  Die Vorhersagen H1/H2/H3 in pt_spectral_gaps_prereg.json sind
  VOR der Hardware-Submission generiert (siehe precompute_predictions()
  unten) und werden nach der Messung ohne Anpassung verglichen.

Vorhersage (noiseless, gamma=0.02):
  E_0..E_3 = 2.0019, 2.6917, 3.6699, 4.9872  (Real-Teile)
  Delta E_n  = 0.6898, 0.9782, 1.3173
  Im(E_0)    = +0.0299  (Resonanzbreite)
"""
import os
import json
import numpy as np
from pt_structural import jacobi_A, E_DIAG
from qiskit.circuit.library import TwoLocal
from qiskit.quantum_info import SparsePauliOp, Operator
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

BACKEND_NAME = "ibm_fez"
GAMMA = 0.02
ALPHA = 1.0
SHOTS = 8192
INITIAL_PARAMS = [0.523, 1.21, -0.45, 0.88]


def load_token():
    return open(".env").read().split("IBMQ_TOKEN=")[1].split("\n")[0]


def precompute_predictions():
    """Berechne Vorhersagen für H1/H2/H3 VOR der Hardware-Submission.

    H1 (additiver Bias beta*1):
      H_eff = H - beta*1
      E_n(H_eff) = E_n(H) - beta
      Delta E_n(H_eff) = Delta E_n(H)         <- invariant
      Im(E_0)(H_eff)  = Im(E_0)(H)             <- invariant

    H2 (multiplikativ auf A, Faktor k~25):
      H_eff = H_diag + i*gamma*k*A
      A wurde numerisch k=25 skaliert
      Erwartungswert: H_eff ~ H_diag + i*0.5*A   (gamma*k=0.5)
      Real-Teile:     E_0..E_3 ~ 2.30, 3.14, 3.27, 4.65
      Delta E_n:      0.84, 0.13, 1.37           <- massiv verzerrt
      Im(E_0):        ~0.09

    H3 (Kohärenz-Decay, p=0.3 Decoherence):
      rho -> (1-p)*rho + p*1/2
      H_eff:  Off-Diagonale um Faktor (1-p) geschrumpft
      Erwartungswerte: Real-Teile ~ noiseless, Im-Teile geschrumpft
      Delta E_n:        ~ noiseless (bis O(p^2))
    """
    A = jacobi_A(E_DIAG, y=1.0)
    H_diag = np.diag(E_DIAG).astype(complex)

    # Noiseless
    H_PT = H_diag + 1j * GAMMA * A
    eigs = sorted(np.linalg.eigvals(H_PT), key=lambda z: z.real)
    E_noiseless = [e.real for e in eigs]
    Delta_noiseless = [E_noiseless[i+1] - E_noiseless[i] for i in range(3)]
    Im_noiseless = [e.imag for e in eigs]

    # H1: additiv
    H1_pred = {
        "Re_E": E_noiseless,
        "Delta_E": Delta_noiseless,
        "Im_E": Im_noiseless,
        "rationale": "Bias beta*1, E_n verschoben um -beta, Gaps invariant"
    }

    # H2: multiplikativ auf A (k=25)
    k = 25.0
    H_PT_k = H_diag + 1j * GAMMA * k * A
    eigs_k = sorted(np.linalg.eigvals(H_PT_k), key=lambda z: z.real)
    E_k = [e.real for e in eigs_k]
    Delta_k = [E_k[i+1] - E_k[i] for i in range(3)]
    H2_pred = {
        "Re_E": E_k,
        "Delta_E": Delta_k,
        "Im_E": [e.imag for e in eigs_k],
        "rationale": f"Bias skaliert A um Faktor k={k} (Verstaerkungsfaktor aus 6.5.7)"
    }

    # H3: Kohaerenz-Decay (p=0.3 auf Off-Diag)
    p = 0.3
    A_decayed = A.copy()
    for i in range(4):
        for j in range(4):
            if i != j:
                A_decayed[i, j] *= (1 - p)
    H_PT_d = H_diag + 1j * GAMMA * A_decayed
    eigs_d = sorted(np.linalg.eigvals(H_PT_d), key=lambda z: z.real)
    E_d = [e.real for e in eigs_d]
    Delta_d = [E_d[i+1] - E_d[i] for i in range(3)]
    H3_pred = {
        "Re_E": E_d,
        "Delta_E": Delta_d,
        "Im_E": [e.imag for e in eigs_d],
        "rationale": f"Decoherence p={p}: Off-Diagonal von A um (1-p) skaliert"
    }

    return {
        "noiseless": {
            "Re_E": E_noiseless,
            "Delta_E": Delta_noiseless,
            "Im_E": Im_noiseless
        },
        "H1_additive": H1_pred,
        "H2_multiplicative": H2_pred,
        "H3_decoherence": H3_pred,
        "decision_rule": (
            "Vergleich |Delta_E_meas - Delta_E_pred| < 0.05 fuer >=2 von 3 Gaps. "
            "H1: Gaps ~ noiseless. H2: Gaps drastisch verschoben (siehe Tabelle). "
            "H3: Gaps ~ noiseless, Im-Teile geschrumpft."
        )
    }


def main():
    token = load_token()
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend(BACKEND_NAME)
    print(f"Backend: {BACKEND_NAME}")

    # === Pre-Registrierung SCHREIBEN vor jeder Hardware-Submission ===
    prereg = precompute_predictions()
    prereg_file = "pt_spectral_gaps_prereg.json"
    with open(prereg_file, "w") as f:
        json.dump(prereg, f, indent=2)
    print(f"\nPräregistrierung geschrieben: {prereg_file}")
    print(f"Noiseless: Delta E = {[f'{d:.4f}' for d in prereg['noiseless']['Delta_E']]}")
    print(f"H2 (k=25): Delta E = {[f'{d:.4f}' for d in prereg['H2_multiplicative']['Delta_E']]}")
    print(f"H3 (p=0.3): Delta E = {[f'{d:.4f}' for d in prereg['H3_decoherence']['Delta_E']]}")

    # === Operator-Konstruktion ===
    A = jacobi_A(E_DIAG, y=1.0)
    H_diag = np.diag(E_DIAG).astype(complex)
    H_PT = H_diag + 1j * GAMMA * ALPHA * A
    H_real = (H_PT + H_PT.conj().T) / 2
    H_imag = (H_PT - H_PT.conj().T) / (2j)
    pauli_real = SparsePauliOp.from_operator(Operator(H_real))
    pauli_imag = SparsePauliOp.from_operator(Operator(H_imag))
    pauli_diag = SparsePauliOp.from_operator(Operator(H_diag))

    # === Ansatz + ISA ===
    ansatz = TwoLocal(2, ['ry'], 'cx', 'linear', reps=1)
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    isa_ansatz = pm.run(ansatz)

    isa_real = pauli_real.apply_layout(isa_ansatz.layout)
    isa_imag = pauli_imag.apply_layout(isa_ansatz.layout)
    isa_diag = pauli_diag.apply_layout(isa_ansatz.layout)

    # === Estimator (3 Pubs in 1 Job) ===
    estimator = Estimator(mode=backend)
    estimator.options.resilience_level = 1
    estimator.options.dynamical_decoupling.enable = True
    estimator.options.dynamical_decoupling.sequence_type = "XX"
    estimator.options.default_shots = SHOTS

    print("\n" + "=" * 70)
    print("SUBMISSION: H_diag (Referenz) + Re(H_PT) + Im(H_PT)")
    print("=" * 70)
    try:
        job = estimator.run([
            (isa_ansatz, isa_diag, INITIAL_PARAMS),
            (isa_ansatz, isa_real, INITIAL_PARAMS),
            (isa_ansatz, isa_imag, INITIAL_PARAMS)
        ])
        print(f"  Job ID: {job.job_id()}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"FEHLER: {e}")
        return

    with open("pt_spectral_gaps_jobs.json", "w") as f:
        json.dump({"job_id": job.job_id(), "backend": BACKEND_NAME}, f, indent=2)

    with open("pt_spectral_gaps_log.txt", "w") as f:
        f.write("EXPERIMENT 006 v4 - PRÄREGISTRIERTER GROUND-TRUTH-RUN\n")
        f.write("=" * 70 + "\n")
        f.write(f"Backend: {BACKEND_NAME}\n")
        f.write(f"Job ID: {job.job_id()}\n")
        f.write(f"gamma={GAMMA}, alpha={ALPHA}\n")
        f.write(f"Initial params: {INITIAL_PARAMS}\n")
        f.write(f"Shots: {SHOTS}, DD: XX, resilience: 1\n\n")
        f.write("VORHERSAGEN (pre-registriert):\n")
        for h in ["noiseless", "H1_additive", "H2_multiplicative", "H3_decoherence"]:
            d = prereg[h]["Delta_E"]
            f.write(f"  {h:20s}: Delta E = {[f'{x:.4f}' for x in d]}\n")

    print(f"\nLog: pt_spectral_gaps_log.txt")
    print(f"Jobs: pt_spectral_gaps_jobs.json")


if __name__ == "__main__":
    main()
