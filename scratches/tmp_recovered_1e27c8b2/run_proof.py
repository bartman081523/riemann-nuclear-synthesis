import hashlib, json, sys
sys.path.insert(0, "/run/media/julian/ML4/riemann")
import pt_ram_q_hardware3_aer as h3a

def fp_qc(qc):
    parts = [str(qc.num_qubits), str(qc.num_clbits)]
    for inst in qc.data:
        parts.append("|".join([
            inst.operation.name,
            ",".join(repr(float(complex(p).real)) for p in inst.operation.params),
            ",".join(str(qc.find_bit(q).index) for q in inst.qubits),
            ",".join(str(qc.find_bit(c).index) for c in inst.clbits)]))
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()

cs = h3a.build_hardware_circuit_set()
h = hashlib.sha256()
for c in cs:
    h.update(c["name"].encode("utf-8")); h.update(fp_qc(c["circuit"]).encode("utf-8"))
qfp = h.hexdigest()
print("circuits:", len(cs))
print("builder fp:", qfp, "| ok:", qfp == "13d78d1fcd03d4f7d343b62fda282a1052b772d1142a019f3baa06eaf3aa9d0e")

import pt_ram_q_hardware3_eval as h3e
doc = h3e.evaluate()
doc.pop("evaluated_at_utc", None)
s = hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
print("eval fp:", s, "| ok:", s == "37925a1e602370127ceb4f254982467b43e2ffd2c03a9afc3383c869f6557da6")
print("verdict:", doc["verdict"], "| gamma_arm:", doc["gamma_arm"])
