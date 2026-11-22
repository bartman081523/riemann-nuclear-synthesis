import json
p = json.load(open("/run/media/julian/ML4/riemann/pt_ram_q6_k2_prereg.json", encoding="utf-8"))
print("KEYS:", list(p))
for k in p:
    if "leg" in k or "zug" in k or "map" in k or "grid" in k:
        v = p[k]
        print("=== ", k, "->", list(v.keys()) if isinstance(v, dict) else (type(v).__name__, v if not isinstance(v, (list, dict)) else ""))
        if k == "d2_leg":
            for kk, vv in v.items():
                if kk == "predictions":
                    fam = vv.get("family") if isinstance(vv, dict) else None
                    print("   predictions keys:", list(vv.keys()) if isinstance(vv, dict) else type(vv))
                    if isinstance(vv, dict) and "family" in vv:
                        print("   family:", fam if not isinstance(fam, dict) else list(fam))
                elif kk in ("registered_expectation", "alpha_family"):
                    print("  ", kk, "=", vv)
                else:
                    print("  ", kk, ":", (list(vv) if isinstance(vv, dict) else vv) if not isinstance(vv, dict) else list(vv)[:6])
        if k == "d3_leg":
            for kk, vv in v.items():
                if isinstance(vv, dict):
                    print("   ", kk, "keys:", list(vv)[:8])
                else:
                    print("   ", kk, "=", vv)
        if k == "zugtabelle":
            print("   m0:", v.get("m0_predictions"))
            print("   rule:", v.get("m0_rule") if "m0_rule" in v else v.get("rule"))
            tr = v.get("train", {})
            print("   train keys:", list(tr.keys()))
            for tk, tv in tr.items():
                if isinstance(tv, dict):
                    print("    ", tk, "->", list(tv)[:4], "... len", len(tv))
                else:
                    print("    ", tk, "=", tv)
        if k == "run4_grid":
            print("   ", {kk: (vv if not isinstance(vv, dict) else list(vv)[:4]) for kk, vv in v.items()})
