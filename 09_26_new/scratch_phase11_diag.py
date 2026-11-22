# -*- coding: utf-8 -*-
"""Phase 11a Diagnostik (0 QPU, NICHT verdict-tragend).

Fragt das committete Run-2-Raw (13 neue Verdict-Punkte + 13 alte
d-Inv-Punkte am Minimalregister) nach der Struktur der Einweg-Suppression:

  delta(P) = ratio_ro_exact(pt, ro_hat) - ratio_hw(P)

Kandidaten-Gesetzesfamilien (alle mit hoehchstens EINEM Arm-Parameter):
  M0  konstantes Delta pro Arm (kohärenter Prep-Fehler-Floor)
  M1  Delta = g_arm + b_arm*(1-kappa_hat)  (Floor + Stochastik-Anteil)
  M2  Delta = gamma_arm * c_P^worst        (kohärentes Share-Gradient-Gesetz:
      worst-case Empfindlichkeit des ABS-FFT-Shares gegen eineunit-norm
      kohärente Amplituden-Störung; c_P klassisch EXAKT berechenbar)
  M3  Delta = gamma_arm * c_P^rms          (RMS-Variante)

Und der Transfer-Test: Fit auf den 13 ALTEN P (d-Inv-Kalibrier-Bein, eigene
paarige Loschmidts im selben Job) -> Vorhersage der 13 NEUEN P.
"""
import json

import numpy as np

import pt_ram_q_hardware_aer as aer
import pt_ram_q_hardware2_aer as s2b
import pt_ram_q_hardware2_eval as evmod


def share_grad(n_d, q, d, m):
    """Gradient des ABS-FFT-Shares nach den Klassen-Populationen n_d."""
    n = np.asarray(n_d, dtype=float)
    G = np.fft.fft(n)
    js = [int(j * d / q) for j in range(1, q)]
    grad = np.zeros(d)
    for a in range(d):
        s = 0.0
        for j in js:
            w = np.exp(-2j * np.pi * j * a / d)
            s += (G[j].conjugate() * w).real
        grad[a] = 2.0 * s / (d * m)
    return grad


def coh_sens(pt, nq, mode="worst"):
    """Kohärente Empfindlichkeit c_P in RATIO-Einheiten: maximaler (worst)
    bzw. RMS (rms) Share-Abfall durch eine unit-norm kohärente Amplituden-
    Störung delta_psi (Realteil-Projektion), normiert auf model_share_reg.

    delta_n_a = 2*sqrt(m*n_a)*Re(delta_psi_a)  (erste Ordnung)
    delta_share = <grad S, delta_n> = 2*sqrt(m)*Re(<v, delta_psi>),
    v_a = sqrt(n_a)*grad_a.
    worst: 2*sqrt(m)*||v||;  rms: 2*sqrt(m)*||v||/sqrt(d)  (Haar-Richtung).
    """
    d, q, m = pt["d"], pt["q"], pt["m"]
    n = np.asarray(pt["n_d"], dtype=float)
    grad = share_grad(n, q, d, m)
    v = np.sqrt(n) * grad
    mag = 2.0 * np.sqrt(m) * float(np.linalg.norm(v))
    if mode == "rms":
        mag /= np.sqrt(d)
    return mag / pt["model_share_reg"]


def load_all():
    e = json.load(open("pt_ram_q_hardware2_eval.json", encoding="utf-8"))
    pts_new = s2b._point_pts()
    pts_old = s2b._diagnostik_pts()
    rows = []
    # ro_hat pro Arm aus dem Verdict-Bein (kal_{nq}q im selben Job)
    ro_hat = {}
    for k, v in e["punkte"].items():
        ro_hat[v["nq"]] = v["diagnostisch_v2"]["ro_hat"]
    for key, pt in sorted(pts_new.items()):
        v = e["punkte"][f"{key[0]}|{key[1]}"]
        nq = s2b.NQ_BY_ARM[key[0]]
        r_ro = aer.ratio_ro_exact(pt, ro_hat[nq], nq)
        rows.append({"set": "new", "key": f"{key[0]}|{key[1]}", "arm": key[0],
                     "pt": pt, "nq": nq, "ro_hat": ro_hat[nq],
                     "ratio": v["ratio_hw"], "kappa": v["kappa_hat"],
                     "r_ro": r_ro, "delta": r_ro - v["ratio_hw"],
                     "res_v1": v["res_sharp"]})
    for key, pt in sorted(pts_old.items()):
        v = e["d_invarianz_bein"]["punkte"][f"{key[0]}|{key[1]}"]
        nq = s2b.NQ_BY_ARM[key[0]]
        r_ro = aer.ratio_ro_exact(pt, ro_hat[nq], nq)
        rows.append({"set": "old", "key": f"{key[0]}|{key[1]}", "arm": key[0],
                     "pt": pt, "nq": nq, "ro_hat": ro_hat[nq],
                     "ratio": v["ratio_run2"], "kappa": v["kappa_run2"],
                     "r_ro": r_ro, "delta": r_ro - v["ratio_run2"],
                     "res_v1": v["res_v1_run2"]})
    return rows


def main():
    rows = load_all()
    for mode in ("worst", "rms"):
        print(f"=== kohärentes Gesetz M2/M3 ({mode}) ===")
        print(f"{'key':12s} {'delta':>7s} {'cP':>7s} {'gamma':>7s} {'kappa':>7s}")
        for r in rows:
            cP = coh_sens(r["pt"], r["nq"], mode)
            r[f"cP_{mode}"] = cP
            r[f"gamma_{mode}"] = r["delta"] / cP if cP > 0 else None
            print(f"{r['key']:12s} {r['delta']:7.4f} {cP:7.4f} "
                  f"{r[f'gamma_{mode}']:7.4f} {r['kappa']:7.4f}")
        for arm in ("q3_d3", "q5_d5"):
            sel = [r for r in rows if r["arm"] == arm]
            for st in ("new", "old"):
                g = [r[f"gamma_{mode}"] for r in sel if r["set"] == st]
                print(f"  {arm} {st}: gamma range "
                      f"[{min(g):.4f}, {max(g):.4f}] mean {np.mean(g):.4f} "
                      f"std {np.std(g):.4f}")
    # M0/M1: konstant bzw. linear in (1-kappa)
    print("=== M0/M1 (Floor, Floor+Stochastik) ===")
    for arm in ("q3_d3", "q5_d5"):
        sel = [r for r in rows if r["arm"] == arm]
        d = np.array([r["delta"] for r in sel])
        kd = np.array([1.0 - r["kappa"] for r in sel])
        A = np.vstack([np.ones_like(kd), kd]).T
        coef, res, *_ = np.linalg.lstsq(A, d, rcond=None)
        pred = A @ coef
        mx = np.abs(d - pred).max()
        c0 = np.mean(d)
        mx0 = np.abs(d - c0).max()
        print(f"{arm}: M0 const {c0:.4f} max|res| {mx0:.4f} | "
              f"M1 g {coef[0]:.4f} b {coef[1]:.3f} max|res| {mx:.4f}")
    # Transfer: Fit auf old, Vorhersage new (M0 und M2-worst)
    print("=== Transfer (Kalibrier = 13 alte P, Test = 13 neue P) ===")
    for mode in ("M0", "worst"):
        for arm in ("q3_d3", "q5_d5"):
            old = [r for r in rows if r["arm"] == arm and r["set"] == "old"]
            new = [r for r in rows if r["arm"] == arm and r["set"] == "new"]
            if mode == "M0":
                g = np.mean([r["delta"] for r in old])
                res = [r["delta"] - g for r in new]
            else:
                g = np.mean([r["delta"] / r["cP_worst"] for r in old])
                res = [r["delta"] - g * r["cP_worst"] for r in new]
            print(f"{arm} {mode}: g_fit(old) {g:.4f} -> new max|res| "
                  f"{max(abs(x) for x in res):.4f} "
                  f"({['%+.4f' % x for x in res]})")


if __name__ == "__main__":
    main()