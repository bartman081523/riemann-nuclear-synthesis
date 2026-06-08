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
    if not token:
        print("Error: IBMQ_TOKEN not found.")
        return

    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    
    # The Job ID from the previous attempt
    job_id = "d8j5j7u6983c73dste00"
    
    print(f"Retrieving results for Job ID: {job_id}...")
    try:
        job = service.job(job_id)
        status = job.status()
        status_str = status.name if hasattr(status, "name") else str(status)
        print(f"Current Status: {status_str}")
        
        if status_str == "DONE":
            result = job.result()
            print("Job Finished. Results:")
            print(result)
            
            # Save raw results for analysis
            with open("hardware_raw_results.txt", "w") as f:
                f.write(str(result))
        elif status.name in ["INITIALIZING", "QUEUED", "RUNNING"]:
            print(f"Job is still in progress. Queue position: {job.usage_estimation.get('queue_position', 'unknown')}")
        else:
            print(f"Job ended with status: {status}")
            
    except Exception as e:
        print(f"Failed to retrieve job: {e}")

if __name__ == "__main__":
    main()
