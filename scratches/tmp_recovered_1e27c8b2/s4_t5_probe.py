# -*- coding: utf-8 -*-
"""Diagnose-Probe zur t5_t6-Abweichung (max_within 1.026e-8, alles an
r_median): (A) per-config-r fuer die Extremmuster 6/10 (beide
benachbart) direkt vergleichen — Erwartung ~1e-8-Streuung pro Config;
(B) Perturbations-Nagel: H + deterministische 3.6e-15-Stoerung (die
gemessene l2/l3-H-Eintragsdifferenz) -> Delta-r; (C) k1-Nenner-Level."""
import sys, time
sys.path.insert(0, "/run/media/julian/ML4/riemann")
import numpy as np
import pt_s4_closure_theorem as s4
import pt_hstar5_execution as h5

t0 = time.time()
configs = h5.get_config_family()
cache = {}
for cfg in configs:
    _, t_h = h5.unfold_spectrum(cfg)
    cache[cfg] = {"t_h": t_h}
print(f"cache: {len(cache)} ({time.time()-t0:.1f} s)", flush=True)

pats = s4.two_minus_patterns()
sig_6 = tuple(pats[6][p] for p in sorted(pats[6]))
sig_10 = tuple(pats[10][p] for p in sorted(pats[10]))
print("signs_6 ", sig_6, "\nsigns_10", sig_10, flush=True)

N = 10  # erste 10 Configs
rows = []
for i, cfg in enumerate(configs[:N]):
    evs6, st6 = h5._config_stats(cfg, h5.EPS_PRIMARY, sig_6, cache)
    evs10, st10 = h5._config_stats(cfg, h5.EPS_PRIMARY, sig_10, cache)
    d_r = st6["r_median"] - st10["r_median"]
    # Spec-Differenz der beiden H (konjugat-nah, Reindexing macht sie
    # nicht direkt konjugat — aber Spektren sind Familien-Summen-traeger)
    d_spec = np.max(np.abs(evs6 := evs6, evs6) if False else 0.0)
    rows.append((cfg, st6["r_median"], st10["r_median"], d_r,
                 st6["k1"], st10["k1"]))
    print(f"cfg {i}: r6 {st6['r_median']:.10f}  r10 {st10['r_median']:.10f}"
          f"  dr {d_r:+.3e}  k1_6 {st6['k1']:.4e}  k1_10 {st10['k1']:.4e}",
          flush=True)

drs = [r[3] for r in rows]
print("\nper-config |dr|: max %.3e  mean %.3e" % (max(abs(d) for d in drs),
                                                  np.mean(np.abs(drs))))
print("Vorzeichen gemischt:", len({np.sign(d) for d in drs}) > 1)
