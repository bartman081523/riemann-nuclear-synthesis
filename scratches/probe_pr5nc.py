import json, pathlib
pr5 = json.loads(pathlib.Path("pt_ram_q_prio48_sv_prereg.json").read_text())
t = pathlib.Path("pt_ram_q_prio48_sv_prereg.json").read_text()
for pat in ["19,13,10", "23,18,17,15,18", "composite"]:
    for i, line in enumerate(t.splitlines(), 1):
        if pat in line:
            print(pat, "line", i, ":", line.strip()[:220])
