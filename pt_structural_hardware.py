"""
EXPERIMENT 005 - HARDWARE VALIDATION: STRUKTURELLES A
PT-Operator mit Jacobi-Matrix aus Zeraoulia-Iteration.

Vorhersage (deterministisch berechnet):
    gamma_eff = 0.02, alpha = 1.0
    Re(E_0) = 2.0019, Im(E_0) = 0.0299

Ansatz: TwoLocal(2, ry, cx, linear, reps=1) -> 4 Parameter
Initial-Punkt: [0.523, 1.21, -0.45, 0.88] (gleiche Konvention wie vorher)
EstimatorV2 auf ibm_marrakesh, 8192 Shots, DD XX.
"""
import os
import numpy as np
from pt_structural import jacobi_A, E_DIAG, f

GAMMA = 0.02  # effektive Kopplungsstaerke
ALPHA = 1.0   # Skalierung des strukturellen A


def build_PT_op():
    """Baut die SparsePauliOp-Repraesentation des PT-Operators."""
    A = jacobi_A(E_DIAG, y=1.0)
    H_diag = np.diag(E_DIAG).astype(complex)
    H_PT = H_diag + 1j * GAMMA * ALPHA * A
    return H_PT


def main():
    # 1. Strukturelle Vorhersage (deterministisch)
    H_PT = build_PT_op()
    eigs = sorted(np.linalg.eigvals(H_PT), key=lambda z: z.real)
    E0_pred = eigs[0]
    print("=" * 70)
    print("EXPERIMENT 005 - HARDWARE: STRUKTURELLES A")
    print("=" * 70)
    print(f"Vorhersage (exakte Diagonalisierung):")
    print(f"  E_0 = {E0_pred.real:.4f} {E0_pred.imag:+.4f}j")
    print(f"  |Im(E_0)| = {abs(E0_pred.imag):.4f} (Linienbreite)")
    print(f"  gamma_eff = {GAMMA}")
    print(f"  Skalierung alpha = {ALPHA}")

    # 2. Initial-Punkt fuer VQD-Ansatz
    # TwoLocal(2, ['ry'], 'cx', linear, reps=1) hat 4 Parameter
    # [theta_0, theta_1] (ry Gates) + [phi_0] (CX params sind 0)
    # Qiskit-Konvention: rx vor cx, also 2 ry + 1 cx = 2 freie Winkel
    # Tatsaechlich: 2 ry Gates = 2 Parameter, CX hat keine
    # TwoLocal(2, 'ry', 'cx', reps=1) hat tatsaechlich 4 Parameter
    # (2 ry Schichten mit je 2 Gates = 4)
    initial_params = [0.523, 1.21, -0.45, 0.88]

    # 3. VQD-Vorbereitung
    from qiskit.circuit.library import TwoLocal
    from qiskit.quantum_info import SparsePauliOp, Operator
    from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    # Konvertiere H_PT in SparsePauliOp
    pauli_op = SparsePauliOp.from_operator(Operator(H_PT))

    # Lade Token
    token = open(".env").read().split("IBMQ_TOKEN=")[1].split("\n")[0]
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.least_busy(operational=True, simulator=False)
    print(f"\nGewaehltes Backend: {backend.name}")

    # Ansatz
    ansatz = TwoLocal(2, ['ry'], 'cx', 'linear', reps=1)
    print(f"Ansatz: TwoLocal(2, ry, cx, linear, reps=1) -> {ansatz.num_parameters} Parameter")

    # ISA-Transpilierung
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    isa_ansatz = pm.run(ansatz)
    isa_obs = pauli_op.apply_layout(isa_ansatz.layout)

    # Estimator mit Mitigations-Optionen
    estimator = Estimator(mode=backend)
    estimator.options.resilience_level = 1  # TREX + Measurement Mitigation
    estimator.options.dynamical_decoupling.enable = True
    estimator.options.dynamical_decoupling.sequence_type = "XX"
    estimator.options.default_shots = 8192

    print(f"Estimator: resilience=1 (TREX), DD=XX, shots=8192")
    print(f"Initial-Parameter: {initial_params}")

    # 4. Run: <H_PT> bei fixen Parametern (kein VQE, nur ein Punkt)
    # Da H_PT nicht-hermitesch ist, ist <H> komplexwertig
    # EstimatorV2 gibt standardmaessig Realteil bei nicht-H Observable
    # Wir muessen Real- und Imaginaerteil getrennt messen
    # Trick: messe <Re(H)> und <Im(H)> separat
    H_real = (H_PT + H_PT.conj().T) / 2
    H_imag = (H_PT - H_PT.conj().T) / (2j)

    pauli_real = SparsePauliOp.from_operator(Operator(H_real))
    pauli_imag = SparsePauliOp.from_operator(Operator(H_imag))
    isa_real = pauli_real.apply_layout(isa_ansatz.layout)
    isa_imag = pauli_imag.apply_layout(isa_ansatz.layout)

    print(f"\nMesse <Re(H_PT)> und <Im(H_PT)> separat...")
    try:
        job = estimator.run([
            (isa_ansatz, isa_real, initial_params),
            (isa_ansatz, isa_imag, initial_params)
        ])
        print(f"  Job ID: {job.job_id()}")
        print(f"  Pub 0: <Re(H_PT)>")
        print(f"  Pub 1: <Im(H_PT)>")

        with open("pt_structural_hardware_log.txt", "w") as f:
            f.write(f"EXPERIMENT 005 - HARDWARE: STRUKTURELLES A\n")
            f.write(f"Backend: {backend.name}\n")
            f.write(f"Job ID: {job.job_id()}\n")
            f.write(f"gamma_eff: {GAMMA}\n")
            f.write(f"alpha: {ALPHA}\n")
            f.write(f"Initial-Parameter: {initial_params}\n")
            f.write(f"Resilience: 1 (TREX + Measurement Mitigation)\n")
            f.write(f"DD: XX\n")
            f.write(f"Shots: 8192\n")
            f.write(f"Predicted: Re(E_0) = {E0_pred.real:.4f}, Im(E_0) = {E0_pred.imag:.4f}\n")
            f.write("---\n")

        print(f"\nErwartete Hardware-Ergebnisse (Vorbehalt der Queue-Auswertung):")
        print(f"  <Re(H_PT)> ~ 2.0 +/- Rauschterm")
        print(f"  <Im(H_PT)> ~ 0.03 +/- Rauschterm")
        print(f"\nVergleich mit dem hermiteschen Zeraoulia-Operator (Section 9.1):")
        print(f"  ibm_marrakesh: <H_herm> = 3.366 (68% ueber 2.0)")
        print(f"  Strukturell PT: erwartet <Re(H_PT)> ~ 2.0 (Hardware-Bias eliminiert)")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Hardware-Run fehlgeschlagen: {e}")


if __name__ == "__main__":
    main()
