# -*- coding: utf-8 -*-
"""Probe B: Amplifikations-Nagel. H (cfg 0, signs_6) gegen H + delta*v
(deterministische Richtung, Frobenius-normiert) -> Delta-r. Kette:
H-Entry-Level (l3_max_dev 3.554e-15 gemessen) -> r-Level 1e-8."""
import sys
sys.path.insert(0, "/run/media/julian/ML4/riemann")
import numpy as np
import pt_s4_closure_theorem as s4
import pt_hstar5_execution as h5

configs = h5.get_config_family()
cfg = configs[0]
pats = s4.two_minus_patterns()
sig_6 = tuple(pats[6][p] for p in sorted(pats[6]))
eps = h5.EPS_PRIMARY

cache = {cfg: {"t_h": h5.unfold_spectrum(cfg)[1]}}
H0 = h5.folded_hamiltonian(cfg, sig_6, eps)
n = H0.shape[0]
V = np.ones((n, n)); V /= np.linalg.norm(V)  # deterministische Richtung
_, st0 = h5._config_stats(cfg, eps, sig_6, cache)
r0, k1_0 = st0["r_median"], st0["k1"]
print(f"n={n}  r0={r0:.12f}  k1={k1_0:.6f}  t_H={cache[cfg]['t_h']:.6f}")
print(f"{'delta':>10} {'max|dEig|':>12} {'max|dK|':>10} {'dr':>14} {'dr/delta':>12}")
for delta in (1e-15, 3.554447978966673e-15, 1e-14, 1e-13, 1e-12):
    evs1 = h5.re_eigs(H0 + delta * V)
    t_h = cache[cfg]["t_h"]
    k1_1 = h5.k_norm(evs1, h5.TAU1 * t_h)
    k2_1 = h5.k_norm(evs1, h5.TAU2 * t_h)
    r1 = k2_1 / k1_1
    evs0 = h5.re_eigs(H0)
    k1_0b = h5.k_norm(evs0, h5.TAU1 * t_h)
    k2_0b = h5.k_norm(evs0, h5.TAU2 * t_h)
    print(f"{delta:10.3e} {np.max(np.abs(evs1-evs0)):12.3e} "
          f"{abs(k1_1-k1_0b):10.3e} {r1-r0:+14.6e} {(r1-r0)/delta:12.2e}")
