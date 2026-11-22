# -*- coding: utf-8 -*-
"""Probe B v2: (1) t_H-Quellen getrennt (cache/unfold vs eigvals), (2)
r an beiden t_H, (3) Eintrags-Perturbation 3.55e-15 -> ratio_stat-Kette."""
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
_, t_h_cache = h5.unfold_spectrum(cfg)
cache = {cfg: {"t_h": t_h_cache}}
evs0 = h5.re_eigs(h5.folded_hamiltonian(cfg, sig_6, eps))
t_h_eig = h5.heisenberg_time(evs0)
print(f"t_H(unfold/cache) {t_h_cache:.10f}")
print(f"t_H(eigvals)      {t_h_eig:.10f}   diff {t_h_eig-t_h_cache:+.3e}")
ev = np.sort(evs0); gaps = np.diff(ev); pos = gaps[gaps > 1e-12]
print(f"median pos gap {np.median(pos):.6e}  min pos gap {pos.min():.6e} "
      f" n_gaps {pos.size}")
r_int = h5.ratio_stat(evs0)
r_cache = h5.k_norm(evs0, h5.TAU2*t_h_cache) / h5.k_norm(evs0, h5.TAU1*t_h_cache)
print(f"r(eigen-t_H) {r_int:.10f}   r(cache-t_H) {r_cache:.10f} "
      f" dr {r_int-r_cache:+.3e}")
# Eintrags-Perturbation auf l3_max_dev-Level:
H0 = h5.folded_hamiltonian(cfg, sig_6, eps)
for delta in (3.554447978966673e-15, 1e-14, 1e-13):
    H1 = H0.copy(); H1[0, 0] += delta
    evs1 = h5.re_eigs(H1)
    r1 = h5.ratio_stat(evs1)
    t1 = h5.heisenberg_time(evs1)
    print(f"delta {delta:.3e}: dr(rationa-t_H) {r1-r_int:+.3e}  "
          f"dt_H {t1-t_h_eig:+.3e}  dEig {np.max(np.abs(evs1-evs0)):.3e}")
