# -*- coding: utf-8 -*-
"""Phase 11a — kohärentes Prep-Fehler-Diagnostik-Modul (EXPERIMENT 044-Vorstufe).

0 QPU, NICHT verdict-tragend. Das Modul fragt das COMMITTED Run-2-Raw
(pt_ram_q_hardware2_eval.json, Verdict H-RAM-Q-3b_REFUTED; Raw-Job
dartdg5vr3kc73ejcrgg, counts_md5 16ca44bd02f81cf623862b4910ccedf8) nach der
Struktur der Einweg-Suppression

    delta(P) = ratio_ro_exact(pt, ro_hat) - ratio_hw(P)

und begründet das Gesetz des Freeze A" (H-RAM-Q-4):

    center_v3 = (1-1/S) * (ratio_ro_exact + b_P*(kappa_hat-1) - gamma_arm*cP)
                + L_q

Befunde (alle aus committeten Daten rekonstruierbar):

  B1  q3: corr(1-kappa_hat, delta) ~ 0 (-0.047) — die Suppression ist NICHT
      kappa-skaliert. Die Punkte mit grossem Echo-Defizit (211/307/729) haben
      KEIN verstaerktes delta. Mechanismus (Phase 10d): der Loschmidt-Echo
      refokussiert kohärente/unäre Prep-Fehler, kappa_hat misst die Echo-TIEFE
      (eigene Dekohärenz), nicht die Struktur-Daempfung.
  B2  Die Aer-kalibrierte Steigung b_P*(1-kappa_hat) unterschätzt die
      hardware-Suppression (res_v2 alle negativ): auf q3-alt sind die
      gamma-Werte delta_cal/cP ANTI-korreliert mit (1-kappa_hat) — die
      kappa-Form der v2-Steigung fehlt in den Hardwaredaten.
  B3  Das kohärente Share-Gradient-Gesetz delta = gamma*cP (worst-case
      Empfindlichkeit gegen eine unit-norm kohärente Amplituden-Störung,
      klassisch EXAKT berechenbar) hat arm-stabile gamma: q3 new 0.0164
      (std 0.0018) vs q3 old 0.0158 (std 0.0024).
  B4  TRANSFER-TEST (Kalibrier = 13 alte P, Test = 13 neue P): das v3-Gesetz
      mit gamma_arm per LSQ-durch-Null aus dem Kalibrier-Bein vorhergesagt
      haette auf Run-2 REFUTED vermieden: max |res| q3 0.0152 / q5 0.0197,
      beide unter w_B' 0.02787 — unter der Voraussetzung, dass kappa_hat und
      ro_hat aus demselben Job stammen (in-job Kalibrier).
  B5  Das q5|541-Anomal (delta 0.2095) ist register-/session-spezifisch:
      run-1 (d=25) hatte res_v1 +0.0248 (POSITIV), run-2 (d=5) -0.1453.
      Die Run-1-P werden deshalb nicht wiederverwendet; die Run-3-Kalibrier-
      punkte sind die Run-2-Verdict-P, die auf Run-2-Evidenz sauber sind.

Physik des Gradient-Gesetzes (erste Ordnung):
    |psi> = sum_a sqrt(n_a/m)|a>, kohärente Stoerung delta_psi (||delta_psi||
    = gamma, <psi|delta_psi> = 0) verschiebt Populationen
    delta_n_a = 2*sqrt(m*n_a)*Re(delta_psi_a), also
    delta_share = 2*sqrt(m)*Re(<v|delta_psi>) mit v_a = sqrt(n_a)*grad_a und
    grad_a = d share / d n_a des exakten ABS-FFT-Shares.
    worst-case (Schranke ueber alle Richtungen): 2*sqrt(m)*||v||_2;
    cP ist diese Groesse normiert auf model_share_reg (Ratio-Einheiten).
    Die Konvention worst-vs-rms ist gamma-arm-spezifisch absorbierbar
    (cP_rms = cP_worst/sqrt(d) je Arm konstanter Faktor) — das Gesetz ist
    in beiden Konventionen identisch, worst-case ist die konservative Lesart.
"""
import hashlib
import json
import math
import os

import numpy as np

import pt_ram_q_hardware2_aer as s2b
import pt_ram_q_hardware_aer as aer

EXPERIMENT = "044-ram-q-coherent-prep-error"
HYPOTHESIS = "H-RAM-Q-4"
STATUS = "DIAGNOSTIC_ONLY_NOT_VERDICT_TRAGEND"
RESULTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "pt_ram_q_hardware3_diag_results.json")

ARMS = ("q3_d3", "q5_d5")
NQ_BY_ARM = dict(s2b.NQ_BY_ARM)


# === exakte Share-Arithmetik (float-Version des committeten Funktional) ===

def share_abs_fft(n, q, d, m):
    """ABS-FFT-Share des (float) Count-Vektors — identisch zu
    aer.share_hw_fft, aber ohne Counts-Vorbedingung (fuer Gradienten-Tests)."""
    G = np.fft.fft(np.asarray(n, dtype=float))
    js = [int(j * d / q) for j in range(1, q)]
    s = sum(abs(G[j]) ** 2 for j in js)
    return float(s) / (d * m)


def share_grad(n_d, q, d, m):
    """Gradient des ABS-FFT-Shares nach den Klassen-Populationen."""
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


def coh_sens(pt, mode="worst"):
    """Kohärente Empfindlichkeit cP in Ratio-Einheiten (siehe Modulkopf)."""
    d, q, m = pt["d"], pt["q"], pt["m"]
    n = np.asarray(pt["n_d"], dtype=float)
    grad = share_grad(n, q, d, m)
    v = np.sqrt(n) * grad
    mag = 2.0 * math.sqrt(m) * float(np.linalg.norm(v))
    if mode == "rms":
        mag /= math.sqrt(d)
    return mag / pt["model_share_reg"]


# === Run-2-Datenladen (nur committete Quellen) ===

def _load_frozen_prereg_points():
    """Die 26 Run-2-Punkte: 13 neue Verdict-P + 13 alte Diagnostik-P."""
    return {"q3_d3": [dict(pt) for pt in list(s2b._point_pts().values())
                      + list(s2b._diagnostik_pts().values())
                      if pt["q"] == 3],
            "q5_d5": [dict(pt) for pt in list(s2b._point_pts().values())
                      + list(s2b._diagnostik_pts().values())
                      if pt["q"] == 5]}


def load_run2_rows():
    """26 Zeilen aus dem committeten Eval (punkte + d_invarianz_bein)."""
    e = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "pt_ram_q_hardware2_eval.json"),
                       encoding="utf-8"))
    ro_hat = {}
    for v in e["punkte"].values():
        ro_hat[v["nq"]] = v["diagnostisch_v2"]["ro_hat"]
    rows = []
    for key, pt in sorted(s2b._point_pts().items()):
        v = e["punkte"][f"{key[0]}|{key[1]}"]
        nq = NQ_BY_ARM[key[0]]
        r_ro = aer.ratio_ro_exact(pt, ro_hat[nq], nq)
        rows.append({"set": "new", "key": f"{key[0]}|{key[1]}", "arm": key[0],
                     "pt": pt, "nq": nq, "ratio": v["ratio_hw"],
                     "kappa": v["kappa_hat"], "r_ro": r_ro,
                     "delta": r_ro - v["ratio_hw"],
                     "res_v2": v["diagnostisch_v2"]["res_v2"],
                     "b_p": None})
    for key, pt in sorted(s2b._diagnostik_pts().items()):
        v = e["d_invarianz_bein"]["punkte"][f"{key[0]}|{key[1]}"]
        nq = NQ_BY_ARM[key[0]]
        r_ro = aer.ratio_ro_exact(pt, ro_hat[nq], nq)
        rows.append({"set": "old", "key": f"{key[0]}|{key[1]}", "arm": key[0],
                     "pt": pt, "nq": nq, "ratio": v["ratio_run2"],
                     "kappa": v["kappa_run2"], "r_ro": r_ro,
                     "delta": r_ro - v["ratio_run2"],
                     "res_v2": None, "b_p": None})
    return rows


def _bp_old_from_grid(rows):
    """b_P der 13 alten P aus dem Aer-Exact-Bein (deterministisch)."""
    for r in rows:
        if r["set"] != "old":
            continue
        curve = [aer.exact_point_level(r["pt"], r["nq"], p1)
                 for p1 in s2b.STRESS_GRID_P1]
        fit = aer.fit_b_p([c["kappa"] for c in curve], [c["ratio"] for c in curve])
        r["b_p"] = fit["b_p"]
    for r in rows:
        if r["set"] == "new":
            r["b_p"] = json.load(open(
                os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "pt_ram_q_stage2b_results.json"),
                encoding="utf-8"))["b_p"][r["key"]]
    return rows


# === gamma-Fit + Transfer ===

def gamma_lsq(cps, deltas):
    """LSQ-Daempfung durch den Ursprung: gamma = <cP, delta>/<cP, cP>."""
    cp = np.asarray(cps, dtype=float)
    dc = np.asarray(deltas, dtype=float)
    denom = float(cp @ cp)
    if denom <= 0:
        raise ValueError("cP-Vektor degeneriert")
    return float(cp @ dc / denom)


def delta_cal_of(row):
    """Kohärenter Floor-Anteil: ratio_ro + b_P*(kappa-1) - ratio."""
    return row["r_ro"] + row["b_p"] * (row["kappa"] - 1.0) - row["ratio"]


def _arm_stats(rows, arm):
    sel = [r for r in rows if r["arm"] == arm]
    old = [r for r in sel if r["set"] == "old"]
    new = [r for r in sel if r["set"] == "new"]
    cps_old = [coh_sens(r["pt"], "worst") for r in old]
    dcals_old = [delta_cal_of(r) for r in old]
    g = gamma_lsq(cps_old, dcals_old)
    res_transfer = [delta_cal_of(r) - g * coh_sens(r["pt"], "worst") for r in new]
    res_in_cal = [delta_cal_of(r) - g * coh_sens(r["pt"], "worst") for r in old]
    # Run-3-Kalibrier-Bein = Run-2-Verdict-P: gamma IN-JOB auf genau diesen
    # Punkten gefittet -> die Stabilitaet dieses Fits ist die Kalibrier-Sauberkeit.
    cps_new = [coh_sens(r["pt"], "worst") for r in new]
    dcals_new = [delta_cal_of(r) for r in new]
    g_new = gamma_lsq(cps_new, dcals_new)
    res_cal_fit = [d - g_new * c for d, c in zip(dcals_new, cps_new)]
    v3a_new = [r["delta"] / coh_sens(r["pt"], "worst") for r in new]
    v3a_old = [r["delta"] / coh_sens(r["pt"], "worst") for r in old]
    kdef = np.array([1.0 - r["kappa"] for r in new])
    dl = np.array([r["delta"] for r in new])
    corr = float(np.corrcoef(kdef, dl)[0, 1])
    return {
        "gamma_lsq": g,
        "in_cal_max_abs_res": max(abs(x) for x in res_in_cal),
        "transfer_max_abs_res": max(abs(x) for x in res_transfer),
        "transfer_res": res_transfer,
        "gamma_cal_fit": g_new,
        "cal_fit_max_abs_res": max(abs(x) for x in res_cal_fit),
        "v3a_gamma_new_mean": float(np.mean(v3a_new)),
        "v3a_gamma_new_std": float(np.std(v3a_new)),
        "v3a_gamma_old_mean": float(np.mean(v3a_old)),
        "v3a_gamma_old_std": float(np.std(v3a_old)),
        "corr_kdef_delta": corr,
    }


def build_results():
    rows = _bp_old_from_grid(load_run2_rows())
    e = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "pt_ram_q_hardware2_eval.json"),
                       encoding="utf-8"))
    punkte = []
    for r in rows:
        punkte.append({
            "key": r["key"], "set": r["set"],
            "P": r["pt"]["P"], "d": r["pt"]["d"], "q": r["pt"]["q"],
            "pt": r["pt"], "nq": r["nq"],
            "ratio": r["ratio"], "kappa": r["kappa"], "r_ro": r["r_ro"],
            "delta": r["delta"], "b_p": r["b_p"], "cP": coh_sens(r["pt"], "worst"),
            "delta_cal": delta_cal_of(r), "res_v2": r["res_v2"],
        })
    querk = []
    for key, v in sorted(e["d_invarianz_bein"]["punkte"].items()):
        querk.append({"key": key, "P": v["P"],
                      "res_v1_run1": v["res_v1_run1"],
                      "res_v1_run2": v["res_v1_run2"],
                      "delta": v["delta"]})
    w_b_ref = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "pt_ram_q_hardware2_eval.json"),
                             encoding="utf-8"))["w_b"]
    return {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "status": STATUS,
        "qpu_jobs": 0,
        "w_a": aer.W_A if hasattr(aer, "W_A") else s2b.W_A,
        "w_b_ref": w_b_ref,
        "kappa_ceiling": s2b.KAPPA_CEILING,
        "run2_counts_md5": e["raw_counts_md5"],
        "punkte": punkte,
        "q3_d3": _arm_stats(rows, "q3_d3"),
        "q5_d5": _arm_stats(rows, "q5_d5"),
        "d_inv_querkonsistenz": querk,
    }


def freeze_results(results=None, path=RESULTS_PATH):
    if results is None:
        results = build_results()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1, sort_keys=False)
    return path


def results_md5(path=RESULTS_PATH):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


if __name__ == "__main__":
    p = freeze_results()
    print(f"geschrieben: {p}")
    r = json.load(open(p, encoding="utf-8"))
    for arm in ARMS:
        s = r[arm]
        print(f"{arm}: gamma_lsq {s['gamma_lsq']:.5f}  in-cal max|res| "
              f"{s['in_cal_max_abs_res']:.4f}  transfer max|res| "
              f"{s['transfer_max_abs_res']:.4f}  corr(kdef,delta) "
              f"{s['corr_kdef_delta']:+.3f}")
        print(f"     v3a gamma new {s['v3a_gamma_new_mean']:.4f}"
              f"(±{s['v3a_gamma_new_std']:.4f})  old "
              f"{s['v3a_gamma_old_mean']:.4f}(±{s['v3a_gamma_old_std']:.4f})")