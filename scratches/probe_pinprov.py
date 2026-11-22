import json, pathlib, hashlib
dok = json.loads(pathlib.Path("pt_ram_q_prio48_sv_raw.json").read_text())
def find(d, pfad=""):
    if isinstance(d, dict):
        for k, v in d.items():
            p = pfad + "/" + str(k)
            if "prereg" in str(k).lower() or "sha" in str(k).lower():
                print(p, "=", json.dumps(v, ensure_ascii=False)[:220])
            if isinstance(v, (dict, list)):
                find(v, p)
    elif isinstance(d, list):
        for i, v in enumerate(d):
            if i < 2:
                find(v, pfad + "/" + str(i))
find(dok)
for f in ["pt_ram_q_prio48_sv_prereg.json", "pt_ram_q_prio48_isa_gate_R0.json", "pt_ram_q_prio48_sv_isa_gate.json", "pt_ram_q_prio48_sv_isa_gate_R0.json"]:
    b = pathlib.Path(f).read_bytes()
    print(f, len(b), hashlib.sha256(b).hexdigest())
    try:
        j = json.loads(b)
        if isinstance(j, dict) and "status" in j:
            print("   status:", j["status"])
    except Exception:
        print("   no json")
