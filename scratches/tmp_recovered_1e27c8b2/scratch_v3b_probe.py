# -*- coding: utf-8 -*-
"""Probe: v3b-Residual-Struktur aus dem gefrorenen Phase-11d-Eval (0 QPU).

Frage (User, 2026-10-01): sind die Session-stabilen Geister / Vorzeichen-
Korrelationen eventuell "physische Fussabdruecke neuer fundamentaler
Arithmetik"? Hier: BLIND-Struktur-Checks an der gefrorenen Tabelle —
klassifikatorische Bewerb von P-Features (mod-3, mod-5, Legendre-Symbole)
und Arm-Konsistenz der Teil-P.
KEIN Fit, KEINE Feature-Suche — nur Vorab-Kandidaten (Legendre mod 5/3)
gegen die gefrorene Tabelle + Arm-Paar-Statistik.
"""
import json
from collections import defaultdict

import numpy as np

EVAL = "/run/media/julian/ML4/riemann/pt_ram_q_hardware3_eval.json"


def legendre(a, p):
    a %= p
    if a == 0:
        return 0
    return 1 if pow(a, (p - 1) // 2, p) == 1 else -1


def spearman(a, b):
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


d = json.load(open(EVAL))
pts = d["punkte"]
rows = []
for key, p in pts.items():
    arm, se, P = key.split("|")
    rows.append({
        "arm": arm, "P": int(P), "set": se,
        "res": p["res_v3"], "in_sharp": p["in_band_sharp"],
        "below": p["below_sharp"], "delta_cal": p["delta_cal"],
        "b_p_aer": p["b_p_aer"], "kappa_hat": p["kappa_hat"],
        "center": p["center_v3"], "ratio_hw": p["ratio_hw"],
        "ceiling": p["ceiling"],
    })

print("== Tabelle je Arm (gefriern-gemaess eval-JSON)")
for arm in sorted({r["arm"] for r in rows}):
    sub = sorted([r for r in rows if r["arm"] == arm], key=lambda x: x["P"])
    n_out = n_bel = 0
    for r in sub:
        if not r["in_sharp"]:
            n_out += 1
        if r["below"] is True:
            n_bel += 1
        print("P=%-4d %-4s res=%+.5f in_sharp=%-5s below=%-5s mod3=%d mod5=%d L5=%+d L3=%+d"
              % (r["P"], r["set"], r["res"], r["in_sharp"], r["below"],
                 r["P"] % 3, r["P"] % 5, legendre(r["P"], 5), legendre(r["P"], 3)))
    print("   n=%d  ausser_scharf=%d  below_scharf=%d" % (len(sub), n_out, n_bel))

print("\n== gleiche P in BEIDEN Armen (Arm-Paar-Konsistenz)")
byP = defaultdict(dict)
for r in rows:
    byP[r["P"]][r["arm"]] = r["res"]
for P, dd in sorted(byP.items()):
    if len(dd) > 1:
        ks = sorted(dd)
        v = [dd[k] for k in ks]
        rel = ("GLEICH" if np.sign(v[0]) == np.sign(v[1]) else "FLIP")
        print("P=%-4d %s -> %s   (Verhaeltnis %.2f)"
              % (P, " ".join("%s=%+.5f" % (k, x) for k, x in zip(ks, v)), rel,
                 abs(v[0] / v[1]) if v[1] else float("nan")))

print("\n== Korrelationen je Arm (nur Deskriptiv — kein Kandidat bewehrt)")
for arm in sorted({r["arm"] for r in rows}):
    sub = [r for r in rows if r["arm"] == arm]
    res = np.array([r["res"] for r in sub], float)
    dc = np.array([r["delta_cal"] for r in sub], float)
    bp = np.array([r["b_p_aer"] for r in sub], float)
    kh = np.array([r["kappa_hat"] for r in sub], float)
    Pp = np.array([float(r["P"]) for r in sub], float)
    print("%s (n=%d): res~delta_cal %+.3f | res~b_p_aer %+.3f | res~kappa_hat %+.3f | res~P %+.3f"
          % (arm, len(sub), spearman(res, dc), spearman(res, bp),
             spearman(res, kh), spearman(res, Pp)))

print("\n== Bewerb der Vorab-Kandidaten auf die gefrorene Tabelle (n=26)")
fals = sorted({r["P"] for r in rows
               if r["arm"] == "q5_d5" and r["set"] == "verdict" and r["below"] is True})
print("Falsifikatoren (HOLDOUT, below_scharf):", fals)
for mod in (3, 5):
    classes = {}
    for m in range(mod):
        mem = sorted({r["P"] for r in rows if r["P"] % mod == m})
        hit = [P for P in mem if P in fals]
        classes[m] = (mem, hit)
        print("mod%d=%d: n=%d fals=%d  %s" % (mod, m, len(mem), len(hit), mem))
    # Lift des Kandidaten 'non-QR mod 5' / 'm mod q'
    print()

print("== Leg-Kandidat 'non-QR mod 5' explizit")
nonqr = sorted({r["P"] for r in rows if legendre(r["P"], 5) == -1})
print("non-QR-Punkte (%d):" % len(nonqr), nonqr)
print("non-QR & fals (Hits):", sorted(set(nonqr) & set(fals)))
qr = sorted({r["P"] for r in rows if legendre(r["P"], 5) == 1})
print("QR-Punkte (%d):" % len(qr), qr)
print("QR & fals:", sorted(set(qr) & set(fals)))

print("\n== Arm-Variable als Konkurrent")
q3n = len([r for r in rows if r["arm"] == "q3_d3"])
q3f = sum(1 for r in rows if r["arm"] == "q3_d3" and r["below"] is True)
q5n = len([r for r in rows if r["arm"] == "q5_d5"])
q5f = sum(1 for r in rows if r["arm"] == 'q5_d5' and r["below"] is True)
print("q3_d3: below_sharp %d/%d ; q5_d5: below_sharp %d/%d  (Falsifikatoren zählen nur HOLDOUT)"
      % (q3f, q3n, q5f, q5n))