import json, collections
p = json.load(open("/run/media/julian/ML4/riemann/pt_ram_q6_k2_prereg.json", encoding="utf-8"))
tr = p["zugtabelle"]["train"]
reasons = collections.Counter(v.get("reason") for v in tr["excluded"].values())
print("reasons:", dict(reasons))
print("pool first:", json.dumps(tr["pool"]["cal|q3_d3|149"], sort_keys=True)[:400])
print("pool verdict-first:", json.dumps(tr["pool"]["verdict|q3_d3|229"], sort_keys=True)[:400])
g = p["grid"]
print("grid.run4 keys:", list(g["run4"].keys()))
print("rotationsregel:", json.dumps(g["rotationsregel"], sort_keys=True)[:300])
print("kalibrier_bein:", json.dumps(p.get("kalibrier_bein"), sort_keys=True)[:400])
print("prediction_freeze:", json.dumps(p.get("prediction_freeze"), sort_keys=True)[:400])
print("punktemenge_vertraege:", json.dumps(p.get("punktemenge_vertraege"), sort_keys=True)[:400])
print("ladder_anchors:", json.dumps(p.get("ladder_anchors"), sort_keys=True)[:200])
print("frozen_inputs:", json.dumps(p.get("frozen_inputs"), sort_keys=True)[:300])
