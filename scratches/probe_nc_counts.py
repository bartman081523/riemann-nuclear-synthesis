import json, pathlib
dok = json.loads(pathlib.Path("pt_ram_q_prio48_sv_raw.json").read_text())
for r in dok["counts"]:
    if r.get("kind") != "negative_control":
        continue
    c = r["counts"]
    print("---", r["name"], "nq=", max(len(k) for k in c))
    for k in sorted(c, key=lambda s: int(s.replace(" ", "") or "0", 2)):
        print("   ", repr(k), "->", c[k])
