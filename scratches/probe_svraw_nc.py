import json, pathlib
dok = json.loads(pathlib.Path("pt_ram_q_prio48_sv_raw.json").read_text())
rows = dok["counts"]
nc = [r for r in rows if r.get("kind") == "negative_control"]
print("nc rows:", len(nc))
for r in nc:
    keys = sorted(r.keys())
    print("---", r.get("name"), "keys:", keys)
    for k in ("modell", "tv", "nq", "shots_actual"):
        if k in r:
            v = r[k]
            print("   ", k, "=", (v if not isinstance(v, list) else str(v)[:120]))
