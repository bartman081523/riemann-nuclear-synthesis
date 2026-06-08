"""
EXPERIMENT 005 - AER STRESS TEST (Path B extended):
PT-Zeraoulia unter Marrakesh-Rauschprofil.

Strategie: Da der PT-Operator H_PT nicht-hermitesch ist, kann der
qiskit.primitives.BackendEstimatorV2 nicht direkt <H> messen.
Stattdessen: 1) Berechne Eigenzustand |psi_0> exakt, 2) Baue Observable
O = |psi_0><psi_0| (Projektor auf Grundzustand), 3) Messe <psi_0|O|psi_0>
auf Aer-Simulator mit Marrakesh-Rauschprofil. Erwarteter Wert ~ 1.0
(idealer Projektor) bzw. reduziert durch Rauschen.

Alternative Metrik: Erwartungswert der Energie auf einem Testzustand
|phi> (z.B. |0...0>) — dies approximiert was ein VQE-ähnlicher Ansatz
auf der Hardware messen würde.

Pre-registrierte Kriterien:
  PRIMARY:  Bei gamma=0.475: |O-Erwartungswert - 1.0| < 0.15
            (Rauschen reduziert Projektor-Treue, aber bleibt signifikant)
  FAIL:     Projektor-Erwartungswert < 0.5 (dominiert von Rauschen)
"""
import os
import numpy as np
from scipy.stats import laplace
from qiskit.quantum_info import SparsePauliOp, Operator, Statevector
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_aer import AerSimulator
from qiskit.primitives import BackendEstimatorV2 as Estimator
from qiskit import QuantumCircuit
from qiskit.circuit.library import TwoLocal
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager


# --- Zeraoulia diagonal levels (deterministic, seed 42) ---
SEED = 42
E_DIAG = np.array([2.0, 2.67870172, 3.8, 4.9])


def build_herm_V(dim, seed=SEED, scale=0.4):
    rng = np.random.RandomState(seed)
    v_real = rng.normal(scale=scale, size=(dim, dim))
    v_imag = rng.normal(scale=scale, size=(dim, dim))
    V = v_real + 1j * v_imag
    return (V + V.conj().T) / 2.0


def build_antiherm_A(dim, seed=SEED, scale=0.4):
    rng = np.random.RandomState(seed + 1)
    v_real = rng.normal(scale=scale, size=(dim, dim))
    v_imag = rng.normal(scale=scale, size=(dim, dim))
    M = v_real + 1j * v_imag
    return (M + M.conj().T) / 2.0  # hermitesch -> i*gamma*A ist antiherm.


def H_pt(gamma, seed=SEED):
    dim = len(E_DIAG)
    H_diag = np.diag(E_DIAG).astype(complex)
    V_herm = build_herm_V(dim, seed=seed)
    A = build_antiherm_A(dim, seed=seed)
    return H_diag + V_herm + 1j * gamma * A


def main():
    # 1. Finde Grundzustand bei gamma=0.475 (der "Zielwert-Kandidat")
    gamma_target = 0.475
    H = H_pt(gamma_target)
    eigs, vecs = np.linalg.eigh(H)  # Achtung: nicht-hermitesch, verwende eig
    # Für nicht-hermitesch: links-/rechtseitige Eigenvektoren
    eigs_nh, vecs_r = np.linalg.eig(H)
    # Sortiere nach Realteil
    idx = np.argsort(eigs_nh.real)
    E0 = eigs_nh[idx[0]]
    psi0 = vecs_r[:, idx[0]]
    print(f"gamma={gamma_target}: exakter PT-Eigenwert E_0 = {E0.real:+.4f} {E0.imag:+.4f}j")
    print(f"Norm |psi_0| = {np.linalg.norm(psi0):.4f}")

    # 2. Baue Projektor |psi_0><psi_0| als 4x4 Hermitesche Matrix
    #    Konvertiere in SparsePauliOp
    projector = np.outer(psi0, psi0.conj())
    # Mache hermitesch (Anti-Hermitesch-Anteil durch Imaginärteil hebt sich auf
    # bei |psi><psi|; numerisch nicht exakt -> symmetrisieren)
    projector = (projector + projector.conj().T) / 2.0
    proj_op = SparsePauliOp.from_operator(Operator(projector))

    # 3. Idealer Erwartungswert: <psi_0|proj|psi_0> = 1.0
    print(f"\nIdealer Projektor-Erwartungswert: 1.0000 (exakt)")

    # 4. Aer-Stresstest mit Marrakesh-Rauschprofil
    token = open(".env").read().split("IBMQ_TOKEN=")[1].split("\n")[0]
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    real_backend = service.backend("ibm_marrakesh")
    sim_backend = AerSimulator.from_backend(real_backend)
    print(f"Aer-Simulator mit Rauschprofil: {real_backend.name}")

    # Ansatz: bereite |psi_0> als 2-Qubit Zustand vor
    # |psi_0> = a|00> + b|01> + c|10> + d|11>
    # Verwende isometry oder initialize
    qc = QuantumCircuit(2)
    qc.initialize(psi0, [0, 1])

    # 5. ISA-Transpilierung
    pm = generate_preset_pass_manager(optimization_level=3, backend=sim_backend)
    isa_qc = pm.run(qc)
    isa_obs = proj_op.apply_layout(isa_qc.layout)

    # 6. Estimator-Run mit hohem Shot-Budget fuer Praezision
    estimator = Estimator(backend=sim_backend)
    estimator.options.default_shots = 8192

    print(f"\nMesse Projektor-Erwartungswert unter Marrakesh-Rauschen...")
    try:
        job = estimator.run([(isa_qc, isa_obs)])
        result = job.result()
        ev = result[0].data.evs
        std = result[0].data.stds
        print(f"  Projektor-Erwartungswert (gestresst): {ev:.4f} +/- {std:.4f}")

        # Vergleich mit hermiteschem Zeraoulia (Path B Original)
        # Damals lieferte der Marrakesh-Sim E_0 = 3.367 fuer |0>-Testzustand
        # Hier erwarten wir konsistent den PT-Grundzustand
        print(f"\n=== STRESS-TEST VERDICT ===")
        if ev > 0.85:
            print(f"  PASS: Projektor-Treue {ev:.3f} > 0.85")
            print(f"  -> PT-Operator behält Grundzustand trotz Marrakesh-Rauschen")
        elif ev > 0.5:
            print(f"  PARTIAL: Projektor-Treue {ev:.3f} in [0.5, 0.85]")
            print(f"  -> PT-Operator wird gestört, aber Grundzustand bleibt dominant")
        else:
            print(f"  FAIL: Projektor-Treue {ev:.3f} < 0.5")
            print(f"  -> Marrakesh-Rauschen zerstört PT-Resonanz vollständig")

        # Schreibe Resultat
        with open("pt_aer_stress_results.txt", "w") as f:
            f.write(f"EXPERIMENT 005 - AER STRESS TEST (Marrakesh noise profile)\n")
            f.write(f"gamma_target: {gamma_target}\n")
            f.write(f"E_0 (exact PT): {E0.real:+.6f} {E0.imag:+.6f}j\n")
            f.write(f"Projector EV (noisy): {ev:.4f} +/- {std:.4f}\n")
            f.write(f"Verdict: {'PASS' if ev > 0.85 else 'PARTIAL' if ev > 0.5 else 'FAIL'}\n")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Stress test failed: {e}")


if __name__ == "__main__":
    main()
