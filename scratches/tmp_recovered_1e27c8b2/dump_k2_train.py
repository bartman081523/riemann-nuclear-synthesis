import json
p = json.load(open("/run/media/julian/ML4/riemann/pt_ram_q6_k2_prereg.json", encoding="utf-8"))
tr = p["zugtabelle"]["train"]
print("pool n", tr["n_pool"], ":", [k for k in tr["pool"]])
print("excluded n", tr["n_excluded"], ":", [k for k in tr["excluded"]])
k0 = list(tr["excluded"])[:2]
for k in k0:
    print(k, "->", json.dumps(tr["excluded"][k], sort_keys=True)[:300])
print("eligible_abs_min:", tr["eligible_abs_min"])
print("pool type of first:", type(tr["pool"][0]), json.dumps(tr["pool"][0], sort_keys=True)[:200] if isinstance(tr["pool"][0], dict) else tr["pool"][0])
print("other zugtabelle keys:", [k for k in p["zugtabelle"] if k not in ("train", "m0_predictions")])
print("diagnostik keys:", list(p.get("diagnostik_nicht_verdict_tragend", {}))[:8])
g = p["grid"]
print("grid.run4 keys:", list(g["run4"].keys()))
print("rotationsregel:", json.dumps(g["rotationsregel"], sort_keys=True)[:220])
print("kalibrier_bein:", json.dumps(p.get("kalibrier_bein"), sort_keys=True)[:300])
print("prediction_freeze:", json.dumps(p.get("prediction_freeze"), sort_keys=True)[:300])
