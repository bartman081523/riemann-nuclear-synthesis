import os
import numpy as np
from qiskit.circuit.library import TwoLocal
from qiskit.quantum_info import SparsePauliOp, Operator
from qiskit.primitives import StatevectorEstimator, StatevectorSampler
from qiskit_algorithms import VQD
from qiskit_algorithms.optimizers import COBYLA
from qiskit_algorithms.state_fidelities import ComputeUncompute
from scipy.stats import laplace

def generate_zeraoulia_levels(n=4, y=1.0):
    levels = [2.0]
    for i in range(n - 1):
        noise = laplace.rvs(scale=0.05)
        next_val = levels[-1] + y * np.log(levels[-1]) + noise
        if next_val <= levels[-1]:
            next_val = levels[-1] + 1e-3
        levels.append(next_val)
    return np.array(levels)

def construct_hamiltonian(n_qubits=2):
    dim = 2**n_qubits
    E = generate_zeraoulia_levels(n=dim)
    H_mat = np.diag(E).astype(complex)
    V = (np.random.normal(scale=0.05, size=(dim, dim)) + 
         1j * np.random.normal(scale=0.05, size=(dim, dim)))
    V = (V + V.conj().T) / 2.0
    H_total = H_mat + V
    pauli_op = SparsePauliOp.from_operator(Operator(H_total))
    return pauli_op, E

def run_vqd(pauli_op, n_levels=2):
    print(f"Running Quantum VQD Simulation for {n_levels} levels...")
    
    # Statevector primitives are more robust for small scale tests
    estimator = StatevectorEstimator()
    sampler = StatevectorSampler()
    fidelity = ComputeUncompute(sampler)
    
    # Decompose TwoLocal to ensure it only contains base gates
    ansatz = TwoLocal(pauli_op.num_qubits, ['ry'], 'cx', 'linear', reps=1).decompose()
    optimizer = COBYLA(maxiter=50)
    
    vqd = VQD(estimator, fidelity, ansatz, optimizer, k=n_levels, betas=[10.0] * (n_levels - 1))
    result = vqd.compute_eigenvalues(pauli_op)
    
    return result.eigenvalues.real

def main():
    n_qubits = 2
    n_levels = 2
    pauli_op, theoretical_levels = construct_hamiltonian(n_qubits)
    
    print(f"Target Zeraoulia Levels: {theoretical_levels[:n_levels]}")
    
    try:
        quantum_levels = run_vqd(pauli_op, n_levels)
        print(f"Quantum VQD Levels: {quantum_levels}")
        
        with open("quantum_simulation_results.txt", "w") as f:
            f.write(f"Zeraoulia Quantum Simulation (VQD)\n")
            f.write(f"Theoretical: {theoretical_levels[:n_levels]}\n")
            f.write(f"Quantum: {quantum_levels}\n")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Quantum Simulation failed: {e}")

if __name__ == "__main__":
    main()
