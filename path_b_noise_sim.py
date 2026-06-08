import os
import numpy as np
from qiskit import transpile
from qiskit.circuit.library import TwoLocal
from qiskit.quantum_info import SparsePauliOp, Operator
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_aer import AerSimulator
from qiskit.primitives import BackendEstimatorV2 as Estimator
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

SEED = 42
np.random.seed(SEED)

def generate_zeraoulia_levels_deterministic(n=4, y=1.0):
    rng = np.random.RandomState(SEED)
    levels = [2.0]
    for i in range(n - 1):
        from scipy.stats import laplace
        noise = laplace.rvs(scale=0.05, random_state=rng)
        next_val = levels[-1] + y * np.log(levels[-1]) + noise
        if next_val <= levels[-1]:
            next_val = levels[-1] + 1e-3
        levels.append(next_val)
    return np.array(levels)

def construct_hamiltonian(n_qubits=2):
    rng = np.random.RandomState(SEED)
    dim = 2**n_qubits
    E = generate_zeraoulia_levels_deterministic(n=dim)
    H_mat = np.diag(E).astype(complex)
    v_real = rng.normal(scale=0.02, size=(dim, dim))
    v_imag = rng.normal(scale=0.02, size=(dim, dim))
    V = v_real + 1j * v_imag
    V = (V + V.conj().T) / 2.0
    H_total = H_mat + V
    return SparsePauliOp.from_operator(Operator(H_total))

def main():
    token = open(".env").read().split("IBMQ_TOKEN=")[1].split("\n")[0]
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    
    print("Fetching noise model from ibm_marrakesh...")
    real_backend = service.backend("ibm_marrakesh")
    
    # Create an Aer simulator from the real backend's properties
    sim_backend = AerSimulator.from_backend(real_backend)
    
    pauli_op = construct_hamiltonian(n_qubits=2)
    ansatz = TwoLocal(2, ['ry'], 'cx', 'linear', reps=1)
    
    pm = generate_preset_pass_manager(optimization_level=3, backend=sim_backend)
    isa_ansatz = pm.run(ansatz)
    isa_observable = pauli_op.apply_layout(isa_ansatz.layout)
    
    params = [0.523, 1.21, -0.45, 0.88] 
    
    estimator = Estimator(backend=sim_backend)
    estimator.options.default_shots = 8192
    
    print("Running Path B: High-Fidelity Noise Simulation...")
    try:
        job = estimator.run([(isa_ansatz, isa_observable, params)])
        result = job.result()
        ev = result[0].data.evs
        print(f"Noise Simulation Result (E0): {ev}")
        
        with open("path_b_simulation_results.txt", "w") as f:
            f.write(f"Aer Noise Simulation (ibm_marrakesh profile)\n")
            f.write(f"Expectation Value: {ev}\n")
            
    except Exception as e:
        print(f"Simulation failed: {e}")

if __name__ == "__main__":
    main()
