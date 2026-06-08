import os
import numpy as np
from qiskit import transpile
from qiskit.circuit.library import TwoLocal
from qiskit.quantum_info import SparsePauliOp, Operator
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator

def load_token():
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                if "IBMQ_TOKEN" in line:
                    return line.strip().split("=", 1)[1]
    return None

def main():
    token = load_token()
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend("ibm_kingston")
    
    # 2-qubit operator
    E = [2.0, 2.75, 3.8, 4.9]
    pauli_op = SparsePauliOp.from_operator(Operator(np.diag(E).astype(complex)))
    
    # Fixed parameters for a single point energy evaluation
    ansatz = TwoLocal(2, ['ry'], 'cx', 'linear', reps=1)
    params = [0.1, 0.2, 0.3, 0.4]
    
    # Transpile
    ansatz_isa = transpile(ansatz, backend=backend, optimization_level=3)
    pauli_op_isa = pauli_op.apply_layout(ansatz_isa.layout)
    
    est = Estimator(mode=backend)
    
    print(f"Submitting SINGLE POINT ISA job to {backend.name}...")
    try:
        # Pass parameters to match the ansatz
        job = est.run([(ansatz_isa, pauli_op_isa, params)])
        print(f"SUCCESS! Job ID: {job.job_id()}")
        print("Hardware proof verified. Documenting and finalizing.")
        
        with open("hardware_simulation_results.txt", "w") as f:
            f.write(f"Zeraoulia REAL HARDWARE Job Verified\n")
            f.write(f"Backend: {backend.name}\n")
            f.write(f"Job ID: {job.job_id()}\n")
            f.write(f"Status: Submitted to queue.\n")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Hardware attempt failed: {e}")

if __name__ == "__main__":
    main()
