# -*- coding: utf-8 -*-
# Diagnostik-Probe 4 (0 QPU, NICHT verdict-tragend): relabel-PAIR-Test.
# Frage: ist die per-Instanz-ratio (ratio_stat, eigener t') relabel-invariant
# auf den KORREKT gepaarten (P,c) <-> (sigma P, sigma c)-Paaren, die P0 auf
# P9 bzw. P35 abbilden?
#   - ratio paarweise identisch (< 1e-5): Multiset-Gleichheit der Bahnen
#     erzwungen -> der rmedian-Roster-Widerspruch liegt woanders.
#   - evs paarweise O(1) differiert: die unitare Relabel-Aequivalenz der
#     Matrizen ist gebrochen (nicht nur t').
# Konvention = t'-Probe (evs-validiert): inv = perm_inverse(sigma), so dass
# inv[v] = Position von v in sigma; img[(x,y)] = P[(inv x, inv y)]; cfg'[i] =
# cfg[inv i]. orbit_rep (h9_atom_n5) benutzt dieselbe Konvention.
# 10 Instanzen (5 cfgs x 2 Targets) a ~23 s eig (d 3125) -> ~4-5 min.
import itertools
import sys
import time

sys.path.insert(0, "/run/media/julian/ML4/riemann/scratches")
sys.path.insert(0, "/run/media/julian/ML4/riemann")
import numpy as np

import h9_atom_n5 as m
import pt_hstar5_execution as h5
import pt_s4_closure_theorem as s4

n = 5
pats = m.make_patterns(n)
cfgs = m.family_shape("min", 5)


def image_pair(P, cfg, sigma):
    inv = s4.perm_inverse(sigma)
    img = dict(zip(sorted(P),
                   (P[tuple(sorted((inv[x], inv[y])))] for x, y in sorted(P))))
    sig = tuple(img[q] for q in sorted(img))
    cfg2 = tuple(cfg[inv[i]] for i in range(n))
    return sig, cfg2


def instance(sig, cfg):
    evs = h5.re_eigs(h5.folded_hamiltonian(cfg, sig, h5.EPS_PRIMARY))
    t_pr = h5.heisenberg_time(evs)
    r = h5.ratio_stat(evs)
    return evs, t_pr, (None if r is None else float(r))


sig0 = tuple(pats[0][p] for p in sorted(pats[0]))
base = {cfg: instance(sig0, cfg) for cfg in cfgs}
print("[Basis] (P0,c) fuer die 5 cfgs aus rosters rekonstruiert:", flush=True)
for cfg, (evs, t_pr, r) in base.items():
    print(f"  {''.join(str(g).replace('0.', '') for g in cfg)}: "
          f"t' {t_pr:.6f}, ratio {'None' if r is None else f'{r:.6f}'}",
          flush=True)

t0all = time.time()
for target in (9, 35):
    sigT = tuple(pats[target][p] for p in sorted(pats[target]))
    hit = None
    for sigma in itertools.permutations(range(n)):
        s_q, _ = image_pair(pats[0], cfgs[0], sigma)
        if s_q == sigT:
            hit = sigma
            break
    if hit is None:
        print(f"[{target}] Ziel NICHT im Bild-Orbit von P0", flush=True)
        continue
    print(f"\n=== P0 -> P{target} via sigma {hit} ===", flush=True)
    for cfg in cfgs:
        sig2, cfg2 = image_pair(pats[0], cfg, hit)
        ev0, t0_, r0 = base[cfg]
        ev1 = h5.re_eigs(h5.folded_hamiltonian(cfg2, sig2, h5.EPS_PRIMARY))
        t1 = h5.heisenberg_time(ev1)
        r1 = h5.ratio_stat(ev1)
        dq = float(np.max(np.abs(np.sort(ev0) - np.sort(ev1))))
        f0 = "None" if r0 is None else f"{r0:.6f}"
        f1 = "None" if r1 is None else f"{r1:.6f}"
        rt = (abs(t1 - t0_) / t0_) if t0_ else float("nan")
        tag = ("gleich" if (r0 is not None and r1 is not None
                            and abs(r0 - r1) < 1e-4) else "SPRUNG")
        print(f"  {''.join(str(g).replace('0.', '') for g in cfg)} -> "
              f"{''.join(str(g).replace('0.', '') for g in cfg2)}: "
              f"evs-diff {dq:.2e}, dt'/t0 {rt:.2e}, ratio {f0} -> {f1} {tag}",
              flush=True)
print(f"\n[Ergebnis] Laufzeit {time.time()-t0all:.0f}s", flush=True)