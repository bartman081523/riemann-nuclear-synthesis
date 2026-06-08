import os
import numpy as np
from qiskit import transpile
from qiskit.circuit.library import TwoLocal
from qiskit.quantum_info import SparsePauliOp, Operator
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

# USE THE SAME SEED AS THE RIGOR JOB
SEED = 42
np.random.seed(SEED)

def generate_zeraoulia_levels_deterministic(n=4, y=1.0):
    rng = np.random.RandomState(SEED)
    levels = [2.0]
    for i in range(n - 1):
        # Scale 0.05 from rigor script
        from scipy.stats import laplace
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
    v_real = rng.normal(scale=0.02, size=(dim, dim))
    v_imag = rng.normal(scale=0.02, size=(dim, dim))
    V = v_real + 1j * v_imag
    V = (V + V.conj().T) / 2.0
    H_total = H_mat + V
    pauli_op = SparsePauliOp.from_operator(Operator(H_total))
    return pauli_op, E

def main():
    token = open(".env").read().split("IBMQ_TOKEN=")[1].split("\n")[0]
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend("ibm_marrakesh")
    
    pauli_op, theoretical_levels = construct_hamiltonian_deterministic(n_qubits=2)
    
    # 1. SETUP ESTIMATOR WITH RESILIENCE LEVEL 2 (ZNE + TREX)
    # This is the "Mitigation Deepening" step
    estimator = Estimator(mode=backend)
    estimator.options.resilience_level = 2 
    # Use exponential extrapolator for better ZNE results in noisy systems
    estimator.options.resilience.zne.extrapolator = "exponential"
    estimator.options.default_shots = 8192
    
    # 2. ISA PREPARATION (Instruction Set Architecture)
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    ansatz = TwoLocal(2, ['ry'], 'cx', 'linear', reps=1)
    isa_ansatz = pm.run(ansatz)
    isa_observable = pauli_op.apply_layout(isa_ansatz.layout)
    
    # 3. USE THE SAME PARAMS AS RIGOR JOB
    params = [0.523, 1.21, -0.45, 0.88] 
    
    print(f"Submitting DEEP MITIGATED job (ZNE + TREX) to {backend.name}...")
    try:
        job = estimator.run([(isa_ansatz, isa_observable, params)])
        print(f"MITIGATED JOB SUBMITTED. ID: {job.job_id()}")
        
        with open("mitigation_deepening_log.txt", "a") as f:
            f.write(f"Job ID: {job.job_id()}\nBackend: {backend.name}\nResilience: 2 (ZNE+TREX)\nExtrapolator: exponential\n")
            
    except Exception as e:
        print(f"Mitigation upgrade failed: {e}")

if __name__ == "__main__":
    main()
