import json, sys
import numpy as np

def avg_ranks(x):
    """Average-Tie-Ranks, numpy-only."""
    x = np.asarray(x, float)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x))
    sx = x[order]
    i = 0
    while i < len(sx):
        j = i
        while j + 1 < len(sx) and sx[j + 1] == sx[i]:
            j += 1
        ranks[order[i: j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return ranks

def spearman(x, y):
    return float(np.corrcoef(avg_ranks(x), avg_ranks(y))[0, 1])

r = json.load(open(sys.argv[1]))
gp = {p["N"]: p for p in r["grid_points"]}
NS = r["valid_points"]
gamma = [gp[n]["K3_q95_001"] for n in NS]
S = [1.2061876309641653, 1.0046698712728896, 1.4748293606806124, 1.753097324817704,
     2.314037122608579, 2.5184856999591734, 3.1900293627988274, 4.672241830479666,
     5.924327731498289, 7.539223986336286]
rA = [float(gp[n]["n_valid_base"]) for n in NS]

rG, rS, rz = avg_ranks(gamma), avg_ranks(S), avg_ranks(rA)
bg, ag = np.polyfit(rz, rG, 1)
bs, as_ = np.polyfit(rz, rS, 1)
resG = rG - (ag + bg * rz)
resS = rS - (as_ + bs * rz)
val = spearman(resG, resS)
import threading
print("threads=%s OPENBLAS=%d partial=%.17f" % (
    __import__("os").environ.get("OMP_NUM_THREADS", "unset"),
    getattr(np.__config__, "get_config", lambda: {}) .get() if False else -1,
    val))
print("bg=%.17f ag=%.17f" % (bg, ag))
print("bs=%.17f as=%.17f" % (bs, as_))
print("resG:", [float(x) for x in resG])
print("resS:", [float(x) for x in resS])
print("resG ranks:", [float(x) for x in avg_ranks(resG)])
print("resS ranks:", [float(x) for x in avg_ranks(resS)])
