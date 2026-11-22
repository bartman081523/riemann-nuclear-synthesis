# -*- coding: utf-8 -*-
"""Maschinen-Smoke fuer pt_test2_entanglement_comovement.py (import, kein main)."""
import sys
sys.path.insert(0, "/run/media/julian/ML4/riemann")
import numpy as np

import pt_test2_entanglement_comovement as R

print("md5-Assert ueberlebt (import ok). MD5 =", R.FROZEN_PREREG_MD5)

psi, n_q, pi_N = R.fresh_psi(15)
print("fresh_psi(15): n=%d pi=%d norm=%.16f" % (n_q, pi_N, np.linalg.norm(psi)))

lam = R.carrier_lam(psi, n_q)
print("carrier len=%d lam_max=%.16f lam_min=%.3e" % (len(lam), lam[0], lam[-1]))
r_p, ok_p = R.ratios_and_valid(lam)
print("ratios=%d valid=%d r_p=%s ok=%s" % (len(r_p), np.sum(ok_p),
                                           np.round(r_p, 4).tolist(), ok_p.astype(int).tolist()))

# K1: exakt proportional
g1, lt = R.gamma_for_amp(psi, n_q, 0.01, np.ones(pi_N), lam, r_p, ok_p)
print("K1 draw: Gamma=%.3e (erwartet ~1e-16), tilde_len=%d" % (g1, lt))

# K3: ein stochastischer Draw
rng = np.random.default_rng(20261002 + 15)
u = rng.uniform(-1, 1, pi_N)
g3, _ = R.gamma_for_amp(psi, n_q, 0.01, u, lam, r_p, ok_p)
print("K3 draw: Gamma=%.6e (float ok)" % g3)

# K2/K5
fr = (np.asarray(R.primes_upto(15), float) / 15) ** 2
g2, _ = R.gamma_for_amp(psi, n_q, 0.01, fr, lam, r_p, ok_p)
alt = (-1.0) ** np.arange(pi_N)
g5, _ = R.gamma_for_amp(psi, n_q, 0.01, alt, lam, r_p, ok_p)
print("K2=%.4e K5=%.4e" % (g2, g5))

# Spearman-Sanity
print("spearman(x,x)=%.2f spearman(asc,desc)=%.2f"
      % (R.spearman([1, 2, 3], [1, 2, 3]), R.spearman([1, 2, 3], [3, 2, 1])))
print("avg_ranks([1,1,2])=%s" % R.avg_ranks([1, 1, 2]).tolist())

# Blend theta=0 (komplexe Pfad-Plumbing)
chi = 0.0 * np.zeros(R.BLEND_N, dtype=complex)
psi_b = psi_ = None
psi_1023, n_q_1023, pi_1023 = R.fresh_psi(1023)
primes_1023 = np.asarray(R.primes_upto(1023))
psi_t = 1.0 * psi_1023.astype(complex) + 0.0 * chi
psi_t /= np.linalg.norm(psi_t)
lam_b = R.carrier_lam(psi_t, n_q_1023)
r_b, ok_b = R.ratios_and_valid(lam_b)
u = np.random.default_rng(20261004).uniform(-1, 1, pi_1023)
g, lt = R.gamma_for_amp(psi_t, n_q_1023, 0.01, u, lam_b, r_b, ok_b, idx=primes_1023)
print("blend theta=0: S=%.16f (axis-frozen 3.1900293627988274) lam_len=%d valid=%d K3-Gamma=%.4e"
      % (R.s_bits(lam_b), len(lam_b), int(np.sum(ok_b)), g))