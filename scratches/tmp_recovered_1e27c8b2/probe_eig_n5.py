import sys, time
sys.path.insert(0, "/run/media/julian/ML4/riemann")
import numpy as np
np.random.seed(0)
import itertools
import pt_hstar5_execution as h5
import pt_ququint_gue as gue
print("GAMMA_FAMILY =", gue.GAMMA_FAMILY)
for n in (3, 4, 5):
    cfg = tuple([gue.GAMMA_FAMILY[0]] * (n - 2) + [gue.GAMMA_FAMILY[1], gue.GAMMA_FAMILY[2]])
    t0 = time.time()
    H = h5.folded_hamiltonian(cfg, [1.0] * (n * (n - 1) // 2), h5.EPS_PRIMARY)
    t1 = time.time()
    d = H.shape[0]
    evs = h5.re_eigs(H)
    t2 = time.time()
    t_h = h5.heisenberg_time(h5.unfold_spectrum(cfg)[0])
    t3 = time.time()
    print(f"n={n} d={d}: build {t1-t0:.2f}s eig {t2-t1:.2f}s unfold+tH {t3-t2:.2f}s", flush=True)
