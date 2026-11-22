import json, sys, math
sys.path.insert(0, "/run/media/julian/ML4/riemann")
import pt_ram_q_hardware3 as h3
import pt_ram_q6_kingston as k6

def res_map(eval_doc):
    out = {}
    for k, p in (eval_doc.get("punkte") or {}).items():
        out[k] = p.get("res_v3")
    return out

s1 = json.load(open("/run/media/julian/ML4/riemann/pt_ram_q_hardware3_eval.json"))
s2 = json.load(open("/run/media/julian/ML4/riemann/pt_ram_q_hardware3_eval_rep.json"))
kk = json.load(open("/run/media/julian/ML4/riemann/pt_ram_q6_kingston_inherited_eval.json"))
r1, r2, r3 = res_map(s1), res_map(s2), res_map(kk)
assert set(r1) == set(r2) == set(r3), (len(r1), len(r2), len(r3))
order = [k for k in sorted(r1) if k.startswith("verdict|")]
order += [k for k in sorted(r1) if k.startswith("cal|")]
AMIN = k6.ELIGIBLE_ABS_MIN
train = {}
for k in order:
    v = [r1[k], r2[k], r3[k]]
    el = [x for x in v if x is not None and abs(x) >= AMIN]
    s = [math.copysign(1.0, x) for x in el if x != 0.0]
    maj = None
    if len(s) >= 2:
        maj = 1.0 if s.count(1.0) > s.count(-1.0) else (-1.0 if s.count(-1.0) > s.count(1.0) else None)
    train[k] = {"res": v, "n_elig": len(el), "majority_sign": maj,
                "in_train_pool": maj is not None}
n_pool = sum(1 for t in train.values() if t["in_train_pool"])
print("train pool:", n_pool, "/ 26")
for k in order:
    t = train[k]
    if not t["in_train_pool"]:
        print("EXKLUDIERT", k, [None if x is None else round(x, 4) for x in t["res"]])
json.dump(train, open("/home/julian/.claude/jobs/1e27c8b2/tmp/train_pool.json", "w"), indent=1)

def legendre(a, p):
    x = pow(a % p, (p - 1) // 2, p)
    return 0 if x == 0 else (1 if x == 1 else -1)
def feats(P):
    return {"L3": (P % 3 if P != 3 else 0),
            "L5": legendre(P, 5),
            "L3L5": (P % 3, legendre(P, 5)),
            "chi4": 1 if P % 4 == 1 else -1,
            "chi8": (1 if P % 8 in (1, 3) else -1),
            "P10": P % 10}

# per-arm train-majority for M0 + feature class tables
pools = {"q3_d3": [k for k in train if train[k]["in_train_pool"] and "|q3_d3|" in k],
         "q5_d5": [k for k in train if train[k]["in_train_pool"] and "|q5_d5|" in k]}
print("pool per arm:", {a: len(p) for a, p in pools.items()})
m0 = {}
for arm, pk in pools.items():
    sg = [train[k]["majority_sign"] for k in pk]
    m0[arm] = 1.0 if sg.count(1.0) > sg.count(-1.0) else -1.0
    print("M0", arm, m0[arm], "| pool +:", sg.count(1.0), "-", sg.count(-1.0))
# feature class tables per arm (freeze in prereg)
ftab = {}
for arm, pk in pools.items():
    per = {}
    for f in ("L3", "L5", "L3L5", "chi4", "chi8", "P10"):
        classes = {}
        for k in pk:
            P = int(k.split("|")[-1]); c = feats(P)[f]
            classes.setdefault(json.dumps(c, sort_keys=True), []).append(train[k]["majority_sign"])
        per[f] = {c: {"n": len(v), "majority": (1.0 if sum(v) > 0 else (-1.0 if sum(v) < 0 else None))}
                  for c, v in sorted(classes.items())}
        per[f] = {c: vv for c, vv in sorted(per[f].items(), key=lambda kv: -kv[1]["n"])}
    ftab[arm] = per
    print(arm, "feature-classes:")
    for f, per_f in per.items():
        print("  ", f, per_f)
json.dump({"m0": m0, "ftab": ftab}, open("/home/julian/.claude/jobs/1e27c8b2/tmp/ftab.json", "w"), indent=1)
# ex-ante predictions at fresh points
fresh = {"q3_d3": [223, 263, 317, 419, 503, 647, 727, 829],
         "q5_d5": [503, 587, 647, 709, 727]}
print("=== ex-ante Pruef-Tabelle (Vorhersagen; Messwerte ABWESEND) ===")
for arm, fl in fresh.items():
    for Pf in fl:
        row = {"M0": m0[arm]}
        for f in ("L3", "L5", "L3L5", "chi4", "chi8", "P10"):
            classes = {c: vv for c, cdict in ftab[arm][f].items()}
            pass
        c = feats(Pf)
        for f in ("L3", "L5", "L3L5", "chi4", "chi8", "P10"):
            key = json.dumps(c[f], sort_keys=True)
            maj = ftab[arm][f].get(key, {}).get("majority")
            row[f] = maj
        dnn, nn = min((abs(Pf - Po), Po) for Po in sorted(int(k.split("|")[-1]) for k in pools[arm]))
        nn_sign = train[f"verdict|{arm}|{nn}"] if f"verdict|{arm}|{nn}" in train else train[f"cal|{arm}|{nn}"]
        row["D3_1NN"] = {"nn_P": nn, "delta": dnn, "sign": nn_sign["majority_sign"]}
        preds = {f: row[f] for f in row}
        print(f"{arm} P={Pf} feats={c} | " + " ".join(
            f"{f}:{('+' if row[f]==1.0 else ('-' if row[f]==-1.0 else '?'))}" for f in ("M0","L3","L5","L3L5","chi4","chi8","P10"))
            + f" | 1NN(=={nn},d={dnn}):{('+' if row['D3_1NN']['sign']==1.0 else '-')}")
