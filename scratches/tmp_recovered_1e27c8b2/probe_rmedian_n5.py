# Diagnostik-Probe (0 QPU, nicht verdict-tragend): Mechanismus hinter dem
# r_median-Sprung innerhalb der n=5-adj-Bahn (idx 0 vs 9 vs 35).
# Prueft: (a) Bahnen identisch (orbit_rep), (b) Per-Instanz-K1(t') nahe der
# 1e-12-Verwerfungsgrenze, (c) None-Anteile je Orbit-Member, (d) Multiset-
# Gleichheit der Per-Instanz-Werte bis auf K1-Flips.
import json, sys
sys.path.insert(0, "/run/media/julian/ML4/riemann/scratches")
sys.path.insert(0, "/run/media/julian/ML4/riemann")
import numpy as np
import h9_atom_n5 as m
import pt_hstar5_execution as h5

pats = m.make_patterns(5)
groups = {}
for i, p in enumerate(pats):
    groups.setdefault(m.orbit_rep(p, 5), []).append(i)
# adj-Bahn mit idx 0 / 9 / 35, dis-Bahn mit idx 6
adj_grp = sorted(groups[m.orbit_rep(pats[0], 5)])
dis_grp = sorted(groups[m.orbit_rep(pats[6], 5)])
print("adj-Bahn", len(adj_grp), adj_grp)
print("dis-Bahn", len(dis_grp), dis_grp)
assert 0 in adj_grp and 9 in adj_grp and 35 in adj_grp
assert 6 in dis_grp

cfgs = m.family_shape("min", 5)
cache = {c: {"t_h": h5.unfold_spectrum(c)[1]} for c in cfgs}

def per_instance(idx, pattern):
    signs = tuple(pattern[p] for p in sorted(pattern))
    out = []
    for cfg in cfgs:
        evs, st = h5._config_stats(cfg, h5.EPS_PRIMARY, signs, cache)
        out.append((cfg, st["k1"], st["k2"], st["r_median"]))
    return out

sel = [("adj0", 0), ("adj9", 9), ("adj35", 35), ("dis6", 6),
       (f"dis{dis_grp[1]}", dis_grp[1])]
for tag, idx in sel:
    rows = per_instance(idx, pats[idx])
    k1fs = [r[1] for r in rows]
    rms = [r[3] for r in rows]
    n_none = sum(1 for r in rms if r is None)
    print(f"\n[{tag}] idx {idx} adj {is_adj_tag(pats[idx]) if False else ''}"
          f"K1-Range [{min(k1fs):.3e}, {max(k1fs):.3e}], None {n_none}/5, "
          f"r_median {float(np.median([r for r in rms if r is not None])) if n_none < 5 else None}")
    for (cfg, k1, k2, r) in rows:
        print(f"   {''.join(str(x) for x in cfg)} k1 {k1:.6e} k2 {k2:.6e} "
              f"ratio {'None' if r is None else f'{r:.6f}'}")
