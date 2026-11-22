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
print("circuits:", len(cs))
print("QASM_FINGERPRINT:", h.hexdigest())

import pt_ram_q_hardware3_eval as h3e
doc = json.load(open("/run/media/julian/ML4/riemann/pt_ram_q_hardware3_eval.json"))
doc.pop("evaluated_at_utc", None)
print("EVAL_FINGERPRINT:", hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()).hexdigest())
print("TOP_KEYS:", sorted(doc))
