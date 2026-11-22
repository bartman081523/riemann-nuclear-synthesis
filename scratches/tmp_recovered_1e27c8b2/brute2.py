import json
import numpy as np

r = json.load(open('/run/media/julian/ML4/riemann/pt_test2_entanglement_comovement_results.json'))
gp = {p['N']: p for p in r['grid_points']}
NS = [15,31,63,127,255,511,1023,10000,100000,1000000]
g  = np.array([gp[N]['K3_q95_001'] for N in NS], float)
gm = np.array([gp[N]['K3_median_001'] for N in NS], float)
g5 = np.array([gp[N]['K3_q95_005'] for N in NS], float)
rv = np.array([float(gp[N]['n_valid_base']) for N in NS], float)
TARGET = -0.31904242195272137

def avg_ranks(x):
    x = np.asarray(x, float)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x))
    sx = x[order]
    i = 0
    while i < len(sx):
        j = i
        while j + 1 < len(sx) and sx[j+1] == sx[i]:
            j += 1
        ranks[order[i:j+1]] = 0.5*(i+j) + 1.0
        i = j + 1
    return ranks

def spearman(x, y):
    return float(np.corrcoef(avg_ranks(x), avg_ranks(y))[0,1])

SAXIS = [1.2061876309641653, 1.0046698712728896, 1.4748293606806124, 1.753097324817704, 2.314037122608579, 2.5184856999591734, 3.1900293627988274, 4.672241830479666, 5.924327731498289, 7.539223986336286]
rS = np.array(SAXIS)  # echte Werte; Rang-Building in avg_ranks/spearman
rA = avg_ranks(rv)
print("rA", rA)
print("rG", avg_ranks(g))

found = {}
def rec(name, v):
    hit = "  <===== EXAKT TARGET" if v == TARGET else ""
    print("%-44s %.16f%s" % (name, v, hit))
    if v == TARGET: found[name] = v

# A) 049-inline (rechengleich zur committeten Formel)
bg, ag = np.polyfit(rA, avg_ranks(g), 1)
bs, as_ = np.polyfit(rA, rS, 1)
rec("049-inline resid spearman", spearman(avg_ranks(g)-(ag+bg*rA), rS-(as_+bs*rA)))

# A2) Pearson statt Spearman auf den Residuen
rec("pearson(rG_res, rS_res)", float(np.corrcoef(avg_ranks(g)-(ag+bg*rA), rS-(as_+bs*rA))[0,1]))

# B) Differenz-Partial
rec("spearman(rG-rA, rS-rA)", spearman(rG:=avg_ranks(g)-rA, rS-rA))
rec("pearson(rG-rA, rS-rA)", float(np.corrcoef(avg_ranks(g)-rA, rS-rA)[0,1]))

# C) Fisher-z-Partials
rGA = float(r['konfund_kit']['rho_gamma_vs_rank_active'])
rSA = spearman(rv, np.array(SAXIS))
rho_raw = float(r['verdict_inputs']['rho_obs'])
rec("fisher (raw0.939, rGA, rSA)",
    (rho_raw - rGA*rSA)/math.sqrt((1-rGA**2)*(1-rSA**2)))
rec("fisher (0.75757, rGA, rSA)",
    (0.7575757575757575 - rGA*rSA)/math.sqrt((1-rGA**2)*(1-rSA**2)))

# D) z=pi_N
piN = np.array([2.0,11,19,31,53,95,172,1229,9592,78498], float)
rz = avg_ranks(piN)
b1, a1 = np.polyfit(rz, avg_ranks(g), 1)
b2, a2 = np.polyfit(rz, rS, 1)
rec("polyfit z=pi_N resid spearman", spearman(avg_ranks(g)-(a1+b1*rz), rS-(a2+b2*rz)))

# E) gamma-Varianten
for nm, gg in (("gamma=K3_median", gm), ("gamma=K3_q95_005", g5)):
    b1, a1 = np.polyfit(rA, avg_ranks(gg), 1)
    b2, a2 = np.polyfit(rA, rS, 1)
    rec(nm + " resid spearman", spearman(avg_ranks(gg)-(a1+b1*rA), rS-(a2+b2*rA)))

# F) Adjacent-rank-swaps
print()
srt = sorted(range(10), key=lambda i2: g[i2])
for i2 in range(9):
    gf = g.copy()
    p_, q_ = srt[i2], srt[i2+1]
    gf[p_], gf[q_] = gf[q_], gf[p_]
    b1, a1 = np.polyfit(rA, avg_ranks(gf), 1)
    b2, a2 = np.polyfit(rA, rS, 1)
    v = spearman(avg_ranks(gf)-(a1+b1*rA), rS-(a2+b2*rA))
    tag = "  <===== EXAKT TARGET" if v == TARGET else ""
    print("swap %d<->%d: %.16f%s" % (NS[p_], NS[q_], v, tag))
