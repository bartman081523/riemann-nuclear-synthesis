# -*- coding: utf-8 -*-
"""EXPERIMENT 048b / H-TEST1 — nummerierte Iteration (arm-symmetrische Kanalnormierung), 0 QPU.

Iteration zu 048 (v1 bleibt UNVERAENDERT committet, Praeg MD5 de77b33c...,
Präzedenz H9a 2/n). 048 v1 lieferte CONFIRMED (5/8, exakt an der Kante); die
NICHT-verdict-tragende Diagnostik (scratch_test1_diag_norm.py, Commit 7fae109)
kippte alle 5 favorable Punkte als Kanal-Normalisierungs-Artefakte:
  D1: K2 max-Re-Normierung des Shapes lieferte den Vorteil (q/b 0.73 -> 1.27 arm-symmetrisch)
  D2: K4 ||S||_2-Norm (Verduennung 1/(dim-1)) lieferte den Vorteil (q/b 0.79/0.69 -> 1.06/1.02)
048b uebernimmt die arm-symmetrischen Formen D1/D2 als Prereg-Definitionen:
  K2: S_i = (E_i/span_shared)^2, OHNE max-Re-Normierung
  K4: S_ij = 1 alle Paare, OHNE ||S||_2-Normierung
Damit macht 048b die artefaktfreie Lesart verdict-traegend. Kanaele, Metriken,
Gates, Seed, Vergleichspunkte und Verdict-Regel sind sonst bit-identisch zu 048 v1.

Der Runner liest das gefrorene Praereg und bricht ab, wenn dessen md5 vom
eingefrorenen Wert abweicht (kein Re-Decide: keine Toleranz-Erhoehung, keine
Kanal-Aenderung nach Sichtbarkeit der Zahlen).
"""
import hashlib
import json
import sys

import numpy as np

from pt_structural import E_DIAG, f as zeraoulia_f, jacobi_A

PREREG_PATH = "pt_test1b_gap_invariance_prereg.json"
RESULTS_PATH = "pt_test1b_gap_invariance_results.json"
FROZEN_PREREG_MD5 = "4f7c65d449ee1d56155b76539cb0c0c8"

Y = 1.0                     # eingefroren: Zeraoulia-y aus dem Record
GAMMA_COMPARE = 0.02        # eingefroren: Record-Wert aus pt_ququint_vqe.py
GAMMA_GATE = 0.0
N_DRAWS = 100
SEED = 20261001
EXACT_TOL = 1e-12           # GATE-B "exakt" (fp-Grenze, VOR Freeze fixiert)
CONSIST_TOL = 1e-10         # GATE-A / GATE-C Innen-Konsistenz
CHANNEL_DELTAS = {
    "K1": (0.001, 0.01, 0.05),   # Pflichtkontrolle, beide gamma
    "K2": (0.001, 0.01, 0.05),
    "K3": (0.001, 0.01),
    "K4": (0.001, 0.01),
    "K5": (0.01,),
}
ADVANTAGE_EDGE = 0.10
FAVORABLE_MIN = 5
K5_RED_FLAG_TOL = 1e-10


def assert_prereg():
    with open(PREREG_PATH, "rb") as fh:
        digest = hashlib.md5(fh.read()).hexdigest()
    if digest != FROZEN_PREREG_MD5:
        sys.exit(
            "ABBRUCH: Praereg-md5 %s != eingefroren %s — kein Lauf unter "
            "geaendertem Praereg (kein Re-Decide)." % (digest, FROZEN_PREREG_MD5)
        )
    return digest


def build_arms():
    E4 = np.array(E_DIAG, dtype=float)
    E5 = np.append(E4, zeraoulia_f(float(E4[-1]), Y))
    E_ctrl = np.append(E4, 5.0)
    A4 = jacobi_A(E4, y=Y)
    A5 = jacobi_A(E5, y=Y)
    A_ctrl = np.zeros((5, 5))
    A_ctrl[:4, :4] = A4                      # block_diag(A_4, 0)
    span_shared = float(E4[-1] - E4[0])
    arms = {
        "binary": {"E": E4, "A": A4},
        "ququint_PRIMARY": {"E": E5, "A": A5},
        "ququint_CONTROL": {"E": E_ctrl, "A": A_ctrl},
    }
    return arms, E4, E5, span_shared


def H_arm(arm, gamma, E_pt=None):
    E = arm["E"] if E_pt is None else E_pt
    return np.diag(E).astype(complex) + 1j * gamma * arm["A"]


def spectrum(H):
    ev = sorted(np.linalg.eigvals(H), key=lambda z: z.real)
    re = np.array([z.real for z in ev], dtype=float)
    im_max = float(max(abs(z.imag) for z in ev))
    gaps = np.diff(re)
    ratios = gaps[1:] / gaps[:-1]
    return re, gaps, ratios, im_max


def rel_drift(base, pert):
    return float(np.max(np.abs((pert - base) / base)))


def apply_channel(name, gamma, arm, delta, span_shared, uvec, S_map):
    E = arm["E"]
    if name == "K1":
        return H_arm(arm, gamma) + delta * span_shared * np.eye(len(E))
    if name == "K2":
        # 048b: arm-symmetrische Form (D1) — gleiche Funktion auf jedem Niveau,
        # OHNE armeigene max-Re-Normierung.
        shape = (E / span_shared) ** 2
        return H_arm(arm, gamma, E_pt=E + delta * span_shared * shape)
    if name == "K3":
        return H_arm(arm, gamma, E_pt=E + delta * span_shared * uvec[: len(E)])
    if name == "K4":
        # 048b: arm-symmetrische Form (D2) — per-Paar-Amplitude, OHNE
        # Spektralnorm-(dim-1)-Verduennung.
        return H_arm(arm, gamma) + delta * span_shared * S_map
    if name == "K5":
        alt = np.power(-1.0, np.arange(len(E)))
        alt = alt / np.abs(alt).max()
        return H_arm(arm, gamma, E_pt=E + delta * span_shared * alt)
    raise ValueError("unbekannter Kanal %s" % name)


def S_allpairs(dim):
    # 048b: unnormalisierte alle-Paare-Struktur (D2-Form)
    return np.ones((dim, dim)) - np.eye(dim)


def main():
    md5 = assert_prereg()
    arms, E4, E5, span_shared = build_arms()
    rng = np.random.default_rng(SEED)
    draws = rng.uniform(-1.0, 1.0, size=(N_DRAWS, 5))  # gepaart: bin u[:4], q u[:5]
    S_map = {"binary": S_allpairs(4), "ququint_PRIMARY": S_allpairs(5)}

    out = {
        "experiment": "048b",
        "hypothesis": "H-TEST1",
        "iteration_note": "048 v1 unveraendert committet (de77b33c...); "
                          "048b: K2/K4 arm-symmetrisch aus Diagnostik D1/D2",
        "prereg_md5": md5,
        "frozen_prereg_md5": FROZEN_PREREG_MD5,
        "seed": SEED,
        "n_draws": N_DRAWS,
        "span_shared": span_shared,
        "E4": [float(x) for x in E4],
        "E5": [float(x) for x in E5],
        "gamma_grid": [GAMMA_GATE, GAMMA_COMPARE],
        "gates": {},
        "comparison_points": [],
        "control_diagnostics": {},
    }
    gate_a = None
    gate_b_max = None
    r_bin02 = None
    r_q02 = None

    # ---- GATE-A: gamma=0, kein Kanal — Innen-Ratios identisch (1e-10) -----
    _, _, r_bin0, _ = spectrum(H_arm(arms["binary"], GAMMA_GATE))
    _, _, r_q0, _ = spectrum(H_arm(arms["ququint_PRIMARY"], GAMMA_GATE))
    gate_a = float(np.max(np.abs(r_q0[: len(r_bin0)] - r_bin0)))
    out["gates"]["GATE_A_shared_interior_ratio_diff_gamma0"] = gate_a
    out["gates"]["GATE_A_pass"] = bool(gate_a <= CONSIST_TOL)

    # ---- GATE-B: K1 exakte Invarianz beide Arme, beide gamma --------------
    gate_b = {}
    for gamma in (GAMMA_GATE, GAMMA_COMPARE):
        for delta in CHANNEL_DELTAS["K1"]:
            for name in ("binary", "ququint_PRIMARY"):
                _, _, r0, _ = spectrum(H_arm(arms[name], gamma))
                _, _, rt, _ = spectrum(
                    apply_channel("K1", gamma, arms[name], delta, span_shared,
                                  draws[0], S_map[name]))
                gate_b["K1_d%s_%s_g%s" % (delta, name, gamma)] = rel_drift(r0, rt)
    gate_b_max = float(max(gate_b.values()))
    out["gates"]["GATE_B_max_drift"] = gate_b_max
    out["gates"]["GATE_B_pass"] = bool(gate_b_max <= EXACT_TOL)

    # ---- Baseline-Ratios am Vergleichspunkt gamma=0.02 ---------------------
    _, _, r_bin02, _ = spectrum(H_arm(arms["binary"], GAMMA_COMPARE))
    _, _, r_q02, _ = spectrum(H_arm(arms["ququint_PRIMARY"], GAMMA_COMPARE))

    # ---- Vergleichspunkte bei gamma=0.02 (8 Punkte, ohne K1) ---------------
    comparison = []
    for chan in ("K2", "K3", "K4", "K5"):
        for delta in CHANNEL_DELTAS[chan]:
            if chan == "K3":
                per_draw_b, per_draw_q = [], []
                for k in range(N_DRAWS):
                    _, _, rb, _ = spectrum(
                        apply_channel("K3", GAMMA_COMPARE, arms["binary"],
                                      delta, span_shared, draws[k], S_map["binary"]))
                    _, _, rq, _ = spectrum(
                        apply_channel("K3", GAMMA_COMPARE,
                                      arms["ququint_PRIMARY"], delta,
                                      span_shared, draws[k],
                                      S_map["ququint_PRIMARY"]))
                    per_draw_b.append(rel_drift(r_bin02, rb))
                    per_draw_q.append(rel_drift(r_q02, rq))
                g_b = float(np.quantile(per_draw_b, 0.95))
                g_q = float(np.quantile(per_draw_q, 0.95))
                extra = {"median_binary": float(np.median(per_draw_b)),
                         "median_ququint": float(np.median(per_draw_q))}
            else:
                _, _, rb, _ = spectrum(
                    apply_channel(chan, GAMMA_COMPARE, arms["binary"], delta,
                                  span_shared, draws[0], S_map["binary"]))
                _, _, rq, _ = spectrum(
                    apply_channel(chan, GAMMA_COMPARE, arms["ququint_PRIMARY"],
                                  delta, span_shared, draws[0],
                                  S_map["ququint_PRIMARY"]))
                g_b = rel_drift(r_bin02, rb)
                g_q = rel_drift(r_q02, rq)
                extra = {}
            fav = bool(g_q < g_b * (1.0 - ADVANTAGE_EDGE))
            comparison.append({
                "channel": chan, "delta": delta, "gamma": GAMMA_COMPARE,
                "Gamma_binary": g_b, "Gamma_ququint": g_q,
                "ratio_q_over_b": (g_q / g_b) if g_b > 0 else None,
                "favorable": fav, **extra,
            })

    # ---- Kontrollarm-Diagnose (block-trivial, Platzhalter 5.0) -------------
    ctrl = {}
    _, gaps_c, r_c0, _ = spectrum(H_arm(arms["ququint_CONTROL"], GAMMA_COMPARE))
    ctrl["interior_ratio_diff_vs_binary_gamma002"] = float(
        np.max(np.abs(r_c0[:2] - r_bin02[:2])))
    _, gaps_c0, r_c00, _ = spectrum(H_arm(arms["ququint_CONTROL"], GAMMA_GATE))
    _, _, r_b00, _ = spectrum(H_arm(arms["binary"], GAMMA_GATE))
    ctrl["interior_ratio_diff_vs_binary_gamma0"] = float(
        np.max(np.abs(r_c00[:2] - r_b00[:2])))
    ctrl["placeholder_gap"] = float(gaps_c0[-1])
    for delta in (0.01, 0.05):
        _, _, r_ct, _ = spectrum(
            apply_channel("K2", GAMMA_COMPARE, arms["ququint_CONTROL"], delta,
                          span_shared, draws[0], S_map["ququint_PRIMARY"]))
        ctrl["K2_d%03d_Gamma_control" % int(delta * 1000)] = rel_drift(r_c0, r_ct)

    # ---- K5 Red-Flag-Pruefung ---------------------------------------------
    k5 = [p for p in comparison if p["channel"] == "K5"][0]
    red_flag = bool(k5["Gamma_ququint"] <= K5_RED_FLAG_TOL
                    and k5["Gamma_binary"] > K5_RED_FLAG_TOL)

    gates_ok = out["gates"]["GATE_A_pass"] and out["gates"]["GATE_B_pass"]
    gates_ok = gates_ok and bool(
        ctrl["interior_ratio_diff_vs_binary_gamma0"] <= CONSIST_TOL
        and ctrl["interior_ratio_diff_vs_binary_gamma002"] <= CONSIST_TOL)
    n_fav = sum(1 for p in comparison if p["favorable"])
    if not gates_ok:
        classification = "DEGENERAT"
    elif n_fav >= FAVORABLE_MIN:
        classification = "CONFIRMED"
    elif n_fav == 4:
        classification = "MIXED"
    else:
        classification = "NOTWENDIGKEIT_GEFALLEN"

    out["comparison_points"] = comparison
    out["n_favorable"] = n_fav
    out["favorable_required"] = FAVORABLE_MIN
    out["classification"] = "H-TEST1-QUALIFIER: " + classification
    out["adversarial_invariance_red_flag"] = red_flag
    out["control_diagnostics"] = ctrl
    out["pt_status_gamma_compare"] = {
        "binary": spectrum(H_arm(arms["binary"], GAMMA_COMPARE))[3],
        "ququint_PRIMARY": spectrum(H_arm(arms["ququint_PRIMARY"],
                                          GAMMA_COMPARE))[3],
        "ququint_CONTROL": spectrum(H_arm(arms["ququint_CONTROL"],
                                          GAMMA_COMPARE))[3],
    }

    with open(RESULTS_PATH, "w") as fh:
        json.dump(out, fh, indent=2, default=float, sort_keys=True)

    print("Praereg md5:", md5)
    print("GATE-A Innen-Diff (gamma=0): %.3e  -> %s"
          % (gate_a, "PASS" if out["gates"]["GATE_A_pass"] else "FAIL"))
    print("GATE-B max Drift: %.3e  -> %s"
          % (gate_b_max, "PASS" if out["gates"]["GATE_B_pass"] else "FAIL"))
    print("GATE-C Innen-Diff (gamma=0 / 0.02): %.3e / %.3e"
          % (ctrl["interior_ratio_diff_vs_binary_gamma0"],
             ctrl["interior_ratio_diff_vs_binary_gamma002"]))
    print("PT-Status max|Im| gamma=0.02: binary %.4f | ququint %.4f | ctrl %.4f"
          % (out["pt_status_gamma_compare"]["binary"],
             out["pt_status_gamma_compare"]["ququint_PRIMARY"],
             out["pt_status_gamma_compare"]["ququint_CONTROL"]))
    print("Platzhalter-Gap (Kontrollarm): %.6f" % ctrl["placeholder_gap"])
    print("Kontrollarm Gamma K2 d=0.01/0.05: %.3e / %.3e"
          % (ctrl["K2_d010_Gamma_control"], ctrl["K2_d050_Gamma_control"]))
    print("")
    print("%-4s %-8s %-14s %-14s %-10s %s" %
          ("Kan", "delta", "Gamma_bin", "Gamma_q5", "q/b", "fav"))
    for p in comparison:
        print("%-4s %-8.3f %-14.6e %-14.6e %-10s %s" %
              (p["channel"], p["delta"], p["Gamma_binary"],
               p["Gamma_ququint"],
               ("%.3f" % p["ratio_q_over_b"]) if p["ratio_q_over_b"] else "-",
               "JA" if p["favorable"] else "nein"))
    print("")
    print("favorable: %d/8 (noetig >= %d)" % (n_fav, FAVORABLE_MIN))
    print("ADVERSARIAL_INVARIANCE_RED_FLAG:", red_flag)
    print("Klassifikation:", out["classification"])


if __name__ == "__main__":
    main()