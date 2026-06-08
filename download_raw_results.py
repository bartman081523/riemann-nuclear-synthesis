import os
from qiskit_ibm_runtime import QiskitRuntimeService

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
    
    jobs = [
        ("d8j5j7u6983c73dste00", "raw_result_1_kingston.txt"),
        ("d8j5kotv8cos73f6d5dg", "raw_result_2_marrakesh_rigor.txt")
    ]
    
    for job_id, filename in jobs:
        print(f"Fetching full data for {job_id}...")
        try:
            job = service.job(job_id)
            result = job.result()
            
            with open(filename, "w") as f:
                f.write(f"Job ID: {job_id}\n")
                f.write(f"Backend: {job.backend().name}\n")
                f.write(f"Status: {job.status()}\n")
                f.write("-" * 20 + "\n")
                f.write(str(result))
                
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error fetching {job_id}: {e}")

if __name__ == "__main__":
    main()
