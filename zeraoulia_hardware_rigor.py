import os
import numpy as np
from qiskit import transpile
from qiskit.circuit.library import TwoLocal
from qiskit.quantum_info import SparsePauliOp, Operator
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator, SamplerV2 as Sampler
from qiskit_algorithms import VQD
from qiskit_algorithms.optimizers import COBYLA
from qiskit_algorithms.state_fidelities import ComputeUncompute
from scipy.stats import laplace

# SET FIXED SEED FOR REPRODUCIBILITY
SEED = 42
np.random.seed(SEED)

def load_token():
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                if "IBMQ_TOKEN" in line:
                    return line.strip().split("=", 1)[1]
    return None

def generate_zeraoulia_levels_deterministic(n=4, y=1.0):
    # Deterministic sequence using a local random state
    rng = np.random.RandomState(SEED)
    levels = [2.0]
    for i in range(n - 1):
        noise = laplace.rvs(scale=0.05, random_state=rng)
        next_val = levels[-1] + y * np.log(levels[-1]) + noise
        if next_val <= levels[-1]:
            next_val = levels[-1] + 1e-3
        levels.append(next_val)
    return np.array(levels)

def construct_hamiltonian_deterministic(n_qubits=2):
    rng = np.random.RandomState(SEED)
    dim = 2**n_qubits
    E = generate_zeraoulia_levels_deterministic(n=dim)
    H_mat = np.diag(E).astype(complex)
    
    # Deterministic GUE-like fluctuations
    v_real = rng.normal(scale=0.02, size=(dim, dim))
    v_imag = rng.normal(scale=0.02, size=(dim, dim))
    V = v_real + 1j * v_imag
    V = (V + V.conj().T) / 2.0
    
    H_total = H_mat + V
    pauli_op = SparsePauliOp.from_operator(Operator(H_total))
    return pauli_op, E

def main():
    token = load_token()
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.least_busy(operational=True, simulator=False)
    
    pauli_op, theoretical_levels = construct_hamiltonian_deterministic(n_qubits=2)
    
    ansatz = TwoLocal(2, ['ry'], 'cx', 'linear', reps=1)
    # 4 parameters for TwoLocal(2, reps=1, ry)
    params = [0.523, 1.21, -0.45, 0.88] # Fixed deterministic initial point
    
    ansatz_isa = transpile(ansatz, backend=backend, optimization_level=3)
    pauli_op_isa = pauli_op.apply_layout(ansatz_isa.layout)
    
    # INCREASE RIGOR: Higher shots
    # Note: Open plan usually limits shots to 4096 or similar.
    shots = 8192 
    
    est = Estimator(mode=backend)
    est.options.default_shots = shots
    
    print(f"Submitting RIGOROUS DETERMINISTIC job to {backend.name}...")
    print(f"Target Levels: {theoretical_levels[:2]}")
    
    try:
        job = est.run([(ansatz_isa, pauli_op_isa, params)])
        print(f"REPRODUCIBLE JOB SUBMITTED. ID: {job.job_id()}")
        
        with open("rigorous_hardware_log.txt", "a") as f:
            f.write(f"Job ID: {job.job_id()}\nBackend: {backend.name}\nSeed: {SEED}\nShots: {shots}\nTarget: {theoretical_levels[:2]}\n---\n")
            
    except Exception as e:
        print(f"Rigor upgrade failed: {e}")

if __name__ == "__main__":
    main()
