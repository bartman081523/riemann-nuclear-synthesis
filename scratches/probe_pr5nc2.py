import json, pathlib
t = pathlib.Path("pt_ram_q_prio48_sv_prereg.json").read_text()
hits = []
for pat in ["19,13", "23,18", "composit", "negative"]:
    for i, line in enumerate(t.splitlines(), 1):
        low = line.lower()
        if pat in low:
            hits.append((pat, i, line.strip()[:200]))
for h in hits[:60]:
    print(h[0], "| L", h[1], "|", h[2])
print("total hits:", len(hits))
