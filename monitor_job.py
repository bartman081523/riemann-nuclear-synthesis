import os
import time
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
        return

    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    job_id = "d8j5kotv8cos73f6d5dg"
    
    print(f"Background monitor started for Job: {job_id}")
    
    while True:
        try:
            job = service.job(job_id)
            status = job.status()
            status_str = status.name if hasattr(status, "name") else str(status)
            
            log_entry = f"{time.ctime()}: Status {status_str}"
            if status_str == "DONE":
                result = job.result()
                with open("job_result_final.txt", "w") as f:
                    f.write(str(result))
                print(f"Job {job_id} DONE. Result saved.")
                break
            elif status_str in ["ERROR", "CANCELLED"]:
                print(f"Job {job_id} failed with status {status_str}")
                break
            
            # Write status to a hidden log for the agent to check
            with open(".job_status", "w") as f:
                f.write(log_entry)
                
        except Exception as e:
            with open(".job_error", "w") as f:
                f.write(str(e))
        
        time.sleep(300) # Poll every 5 minutes

if __name__ == "__main__":
    main()
