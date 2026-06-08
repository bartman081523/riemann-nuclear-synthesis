import os
import json
import numpy as np
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
        ("d8j5j7u6983c73dste00", "shots_kingston.json"),
        ("d8j5kotv8cos73f6d5dg", "shots_marrakesh_rigor.json")
    ]
    
    for job_id, filename in jobs:
        print(f"Retrieving granular counts for {job_id}...")
        try:
            job = service.job(job_id)
            result = job.result()
            
            serializable_result = []
            for pub_res in result:
                # V2 Estimator stores expectation values in 'evs' and standard errors in 'stds'
                # Note: EstimatorV2 does NOT typically return bitstrings unless specifically requested 
                # (e.g., via metadata or custom execution modes). 
                # For basic Estimator runs, we only get 'evs' and 'stds'.
                # If these were Sampler runs, we would have 'meas' or 'counts'.
                
                data_dict = {}
                # DataBin is a custom object. We access it by name.
                try:
                    data_dict["evs"] = pub_res.data.evs.tolist() if hasattr(pub_res.data.evs, "tolist") else pub_res.data.evs
                    data_dict["stds"] = pub_res.data.stds.tolist() if hasattr(pub_res.data.stds, "tolist") else pub_res.data.stds
                    if hasattr(pub_res.data, "ensemble_standard_error"):
                         data_dict["ensemble_standard_error"] = pub_res.data.ensemble_standard_error.tolist()
                except AttributeError:
                    # Fallback for Sampler-like data
                    for field in getattr(pub_res.data, '_fields', []):
                         val = getattr(pub_res.data, field)
                         data_dict[field] = val.tolist() if hasattr(val, "tolist") else val

                serializable_result.append({
                    "data": data_dict,
                    "metadata": pub_res.metadata
                })
            
            with open(filename, "w") as f:
                json.dump(serializable_result, f, indent=2)
                
            print(f"Granular JSON data saved to {filename}")
        except Exception as e:
            print(f"Failed to retrieve counts for {job_id}: {e}")

if __name__ == "__main__":
    main()
