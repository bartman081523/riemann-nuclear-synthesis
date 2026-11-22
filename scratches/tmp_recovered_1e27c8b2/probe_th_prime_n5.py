# Diagnostik-Probe (0 QPU): t'-Diskontinuitaet auf relabel-AEQUIVALENTEM Paar.
# (P,c) vs (sigmaP, sigma-c) sind unitär aequivalent -> eigvals identisch
# bis Rounding, t' identisch bis Rounding. Gemessen: evs <= 1e-9, t' springt.
import sys
sys.path.insert(0, "/run/media/julian/ML4/riemann/scratches")
sys.path.insert(0, "/run/media/julian/ML4/riemann")
import itertools
import numpy as np
import h9_atom_n5 as m
import pt_hstar5_execution as h5

n = 5
pats = m.make_patterns(n)
P = pats[0]
sig0 = tuple(P[p] for p in sorted(P))
cfg0 = m.family_shape("min", 5)[0]

def image_signs(sigma):
    inv_map = [0] * n
    for i, v in enumerate(sigma):
        inv_map[v] = i
    img = {}
    for x, y in sorted(P):
        img[(x, y)] = P[tuple(sorted((inv_map[x], inv_map[y])))]
    return tuple(img[q] for q in sorted(img)), tuple(cfg0[inv_map[i]] for i in range(n))

imgs = []
seen = {(sig0, cfg0)}
for sigma in itertools.permutations(range(n)):
    pair = image_signs(sigma)
    if pair not in seen:
        seen.add(pair)
        imgs.append(pair)
print(f"[Dedupe] {len(imgs)} distincte relabel-Bilder", flush=True)

evs0 = h5.re_eigs(h5.folded_hamiltonian(cfg0, sig0, h5.EPS_PRIMARY))
t0 = h5.heisenberg_time(evs0)
ev0 = np.sort(evs0)
gaps0 = np.diff(ev0); pos0 = gaps0[gaps0 > 1e-12]
print(f"[Basis] (P0,c0) t' {t0:.9f}, d {ev0.size}, min pos gap {pos0.min():.3e}, "
      f"median pos gap {float(np.median(pos0)):.6e}, Luecken <=1e-12: "
      f"{int(np.sum(gaps0 <= 1e-12))}/{gaps0.size}", flush=True)
sprung = 0
for sigQ, cfgQ in imgs[:10]:
    evsQ = h5.re_eigs(h5.folded_hamiltonian(cfgQ, sigQ, h5.EPS_PRIMARY))
    tq = h5.heisenberg_time(evsQ)
    dq = float(np.max(np.abs(ev0 - np.sort(evsQ))))
    assert dq <= 1e-6, (dq,)
    fakt = tq / t0
    status = "t'-SPRUNG" if abs(fakt - 1.0) > 1e-6 else "t' gleich"
    print(f"[rel] cfg {''.join(str(g) for g in cfgQ)}: max|evs diff| {dq:.2e}, "
          f"t' {tq:.9f} (t'/t0 {fakt:.6f}) -> {status}", flush=True)
    if abs(fakt - 1.0) > 1e-6:
        sprung += 1
print(f"[Ergebnis] {sprung} t'-Spruenge in {min(10, len(imgs))} Bildern, "
      f"alle evs-Gleichheiten <= 1e-6", flush=True)
