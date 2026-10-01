#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""H-TEST1 Diagnostik-Probe an den Phase-11d v3b-Residuen (0 QPU, NICHT verdict-tragend).

User-Frage (2026-10-01): sind die Session-stabilen Geister / Vorzeichen-
Korrelationen "physische Fussabdruecke einer neuen fundamentalen Arithmetik"?
Antwortkette: (1) wie viel freie Varianz hat der Geist JENSEITS der
Kalibrations-Kette (res~delta_cal, Residuen-Korrelation Partiale)? (2) ist das
Vorzeichen eine P-Funktion (Arm-Paar-Konsistenz ueber 6 gemeinsame P)? (3)
traegt eine Legendre-Mod-5-Klassenregel die Falsifikator-Lage (Band- und
Falsifikator-Klassifikator, Hypergeom)? Referenzrahmen: Haus-Null
(Mitwanderungs-Shuffle q95 |rho| 0.636 bei n=10 aus 049), Phase-10b-Regel
(frische P fuer neue Preregs), 046 Backend-Drift.

Gefrorene Inputs: pt_ram_q_hardware3_eval.json (Phase-11d, Fez
dat1o6qhcrkc73dtgo60, Prereg baaca1f6) — nur gelesen, nichts veraendert.
KEIN Fit, KEINE ex-post-Klassenwahl als Beweismittel — die Legendre-Klasse
ist VORAB-Kandidat und wird BLIND bewertet (Band-Klassifikator), der
Falsifikator-Vergleich 3/3 ist ex-post-Sichtweise und nur zur Transparenz
mitgefuehrt.
"""
import json
import math
import time

import numpy as np
from scipy.stats import hypergeom

EVAL = "pt_ram_q_hardware3_eval.json"
OUT = "scratches/h_test1_v3b_ghost_probe_out.json"


def legendre(a, p):
    a %= p
    if a == 0:
        return 0
    return 1 if pow(a, (p - 1) // 2, p) == 1 else -1


def avg_ranks(x):
    x = np.asarray(x, float)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x))
    sx = x[order]
    i = 0
    while i < len(sx):
        j = i
        while j + 1 < len(sx) and sx[j + 1] == sx[i]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return ranks


def spearman(x, y):
    return float(np.corrcoef(avg_ranks(x), avg_ranks(y))[0, 1])


def partial_spearman(x, y, z):
    """Partielle Spearman ueber Rang-Residuen der linearen Rang-Fits (049-Präzedenz)."""
    rx, ry, rz = avg_ranks(x), avg_ranks(y), avg_ranks(z)
    bx, ax = np.polyfit(rz, rx, 1)
    by_, ay = np.polyfit(rz, ry, 1)
    return spearman(rx - (ax + bx * rz), ry - (ay + by_ * rz))


# ------------------------------------------------------------------ laden
d = json.load(open(EVAL))
pts = d["punkte"]
rows = []
for key, p in pts.items():
    se, arm, P = key.split("|")
    rows.append({
        "arm": arm, "set": se, "P": int(P),
        "res": p["res_v3"], "in_sharp": p["in_band_sharp"],
        "below": p["below_sharp"], "delta_cal": p["delta_cal"],
        "b_p_aer": p["b_p_aer"], "kappa_hat": p["kappa_hat"],
        "echo_kappa": p.get("echo_block", {}).get("kappa_block")
        if isinstance(p.get("echo_block"), dict) else None,
    })
out = {"eval_prereg_md5": d["prereg_md5"], "raw_job": d["raw_job_meta"], "n_points": len(rows)}
print("Prereg md5:", d["prereg_md5"], "| job:", d["raw_job_meta"], "| Punkte:", len(rows))

# ------------------------------------------------------------------ (1) Geist-Fesseln
fals = sorted({r["P"] for r in rows
               if r["arm"] == "q5_d5" and r["set"] == "verdict" and r["below"] is True})
out["falsifikatoren_holdout_q5"] = fals
print("\nFalsifikatoren (HOLDOUT below_sharp):", fals)

corr = {}
for arm in sorted({r["arm"] for r in rows}):
    sub = [r for r in rows if r["arm"] == arm]
    res = np.array([r["res"] for r in sub], float)
    dc = np.array([r["delta_cal"] for r in sub], float)
    kh = np.array([r["kappa_hat"] for r in sub], float)
    Pv = np.array([float(r["P"]) for r in sub], float)
    ranks = len(sub)
    # Rest-Spannweite: Range der Rang-Residuen des linearen Fits rG ~ r(dc)
    # (Einheit: Rang-Stufen von 0..n-1) — wie viel Rang-Varianz bleibt
    # JENSEITS der Kalibrations-Kette, bevor P/kappa um ihre Ersatzrechnung ringen?
    rG = avg_ranks(res)
    rdc = avg_ranks(dc)
    bg, ag = np.polyfit(rdc, rG, 1)
    rest = rG - (ag + bg * rdc)
    span_rest = float(np.max(rest) - np.min(rest))
    c = {
        "n": ranks,
        "res_vs_delta_cal": spearman(res, dc),
        "res_vs_kappa_hat": spearman(res, kh),
        "res_vs_P": spearman(res, Pv),
        "partial_res_P_given_delta_cal": partial_spearman(res, Pv, dc),
        "partial_res_kappa_given_delta_cal": partial_spearman(res, kh, dc),
        "rangspanne_res": float(max(res) - min(res)),
        "rest_spannweite_nach_dc": span_rest,
    }
    corr[arm] = c
    print("%-6s n=%d: res~dc %+.3f | res~kappa_hat %+.3f | res~P %+.3f | "
          "partial(res,P|dc) %+.3f | partial(res,kappa|dc) %+.3f | Rest-Spannweite %.2f von %d"
          % (arm, ranks, c["res_vs_delta_cal"], c["res_vs_kappa_hat"], c["res_vs_P"],
             c["partial_res_P_given_delta_cal"],
             c["partial_res_kappa_given_delta_cal"],
             span_rest, ranks - 1))
out["korrelationen_gewehr"] = corr

out["set_korrektur"] = {}
for se in sorted({r["set"] for r in rows}):
    sub = [r for r in rows if r["set"] == se]
    out["set_korrektur"][se] = {"n": len(sub),
                                "res_vs_delta_cal": spearman(
                                    [r["res"] for r in sub],
                                    [r["delta_cal"] for r in sub])}
    print("set %-7s n=%d: res~delta_cal %+.3f"
          % (se, len(sub), out["set_korrektur"][se]["res_vs_delta_cal"]))

# ------------------------------------------------------------------ (2) Vorzeichen = P-Funktion?
byP = {}
for r in rows:
    byP.setdefault(r["P"], {})[r["arm"]] = r["res"]
pairs = []
for P, dd in sorted(byP.items()):
    if len(dd) > 1:
        ks = sorted(dd)
        v = [dd[k] for k in ks]
        pairs.append({"P": P, "arms": ks, "res": v,
                      "relation": "GLEICH" if (np.sign(v[0]) == np.sign(v[1])) else "FLIP",
                      "abs_ratio": abs(v[0] / v[1]) if v[1] else None})
n_gleich = sum(1 for p in pairs if p["relation"] == "GLEICH")
out["arm_paare"] = {"pairs": pairs, "n_gleich": n_gleich,
                    "n_flip": len(pairs) - n_gleich}
print("\nArm-Paare: %d GLEICH / %d FLIP" % (n_gleich, len(pairs) - n_gleich))
for p in pairs:
    print("P=%-4d %s %s" % (p["P"], " ".join(
        "%s=%+.5f" % (a, x) for a, x in zip(p["arms"], p["res"])), p["relation"]))

# ------------------------------------------------------------------ (3) Legendre-Mod-5-Kandidat BLIND (Band-Klassifikator je Arm)
band = {}
for arm in sorted({r["arm"] for r in rows}):
    sub = [r for r in rows if r["arm"] == arm]
    n_arm = len(sub)
    out_sharp = sorted({r["P"] for r in sub if not r["in_sharp"]})
    non_qr = sorted({r["P"] for r in sub if legendre(r["P"], 5) == -1})
    hit = sorted(set(out_sharp) & set(non_qr))
    if out_sharp:
        # Blind-Test: unter H0 (kein Zusammenhang) zieht man len(out_sharp)
        # Punkte aus den len(sub) Punkten des Arms und fragt, wie oft liegen
        # >= len(hit) davon in der non-QR-Klasse (K = len(non_qr))?
        pval = float(hypergeom.sf(len(hit) - 1, n_arm, len(non_qr), len(out_sharp)))
    else:
        pval = None
    band[arm] = {"ausser_sharp": out_sharp, "non_QR": non_qr, "treffer": hit,
                 "n_arm": n_arm,
                 "hypergeom_P_min_treffer_so_viele": pval,
                 "klassifikator_identisch": out_sharp == non_qr}
    print("\n%s (Arm-Bein n=%d): ausser_sharp %d %s" % (arm, n_arm, len(out_sharp), out_sharp))
    print("      non-QR    %d %s   -> Klassifikator identisch: %s | Hypergeom P %.4f "
          "(Blind-Band-Test, ex-ante-Klasse)"
          % (len(non_qr), non_qr, out_sharp == non_qr, pval if pval is not None else float("nan")))
nqr_all = sorted({r["P"] for r in rows if legendre(r["P"], 5) == -1})
qr_all = sorted({r["P"] for r in rows if legendre(r["P"], 5) == 1})
out["legendre_kandidat"] = {
    "je_arm": band,
    "non_QR_gesamt": nqr_all, "QR_gesamt": qr_all,
    "fals_in_nonQR": sorted(set(fals) & set(nqr_all)),
    "fals_in_QR": sorted(set(fals) & set(qr_all)),
    "P_f_nach_nonQR": len(set(fals) & set(nqr_all)) / len(nqr_all),
    "P_f_nach_QR": len(set(fals) & set(qr_all)) / len(qr_all),
    "hypergeom_fals_ganz_in_nonQR": float(
        hypergeom.sf(3 - 1, len(nqr_all) + len(qr_all), len(nqr_all), len(fals))),
    "ex_post_warn": ("3/3-Falsifikator-Zeile ist ex-post-Klassenwahl (Anti-Sharpshooter: "
                     "KEINE Beweiskraft ohne ex-ante-Registrierung)"),
}
print("\nFalsifikator-Zeile (ex-post, nur Transparenz): %d/%d in non-QR; "
      "Hypergeom P(>=3 in non-QR) = %.6f"
      % (len(out["legendre_kandidat"]["fals_in_nonQR"]), len(fals),
         out["legendre_kandidat"]["hypergeom_fals_ganz_in_nonQR"]))

out["runtime_seconds"] = time.time()
with open(OUT, "w") as fh:
    json.dump(out, fh, indent=1, default=float)
print("\nOK ->", OUT)