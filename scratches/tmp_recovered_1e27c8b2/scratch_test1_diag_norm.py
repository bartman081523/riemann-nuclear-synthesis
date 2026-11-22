# -*- coding: utf-8 -*-
"""EXPERIMENT 048-DIAGNOSTIK (H-TEST1) — Normalisierungs-Zerlegung, 0 QPU.

NICHT VERDICT-TRAGEND (Phase-11-Präzedenz): das gefrorene Verdict von 048
steht; dieses Skript zerlegt NUR, ob die 5 favorable Punkte eine eigentliche
Architektur-Eigenschaft oder einen Normalisierungs-Artefakt tragen.

Drei Fragen:
  D1: K2 mit ARM-SYMMETRISCHER Form (shape = (E/span_shared)^2 OHNE
      max-Re-Normierung — identischer Input auf gemeinsamen Niveaus)
      -> verschwindet der K2-Vorteil (q/b -> 1)?
  D2: K4 mit PER-PAIR-Normierung (S = alle-Paare-Offdiag OHNE Norm —
      gleiche Koppelstaerke pro Paar in beiden Armen)
      -> verschwindet der K4-Vorteil (Projektions-Verduennung 3/4)?
  D3: Kontrollarm (Platzhalter-Gap 0.0122) unter K3 — Level-Crossing-Zaehler
      (Fragilitaets-Diagnose des bestehenden pt_ququint_vqe-Arms).
"""
import numpy as np

from pt_test1_gap_invariance import GAMMA_COMPARE, N_DRAWS, build_arms


def spectrum(H):
    ev = sorted(np.linalg.eigvals(H), key=lambda z: z.real)
    re = np.array([z.real for z in ev], dtype=float)
    gaps = np.diff(re)
    ratios = gaps[1:] / gaps[:-1]
    return re, gaps, ratios


def rel_drift(base, pert):
    return float(np.max(np.abs((pert - base) / base)))

def main():
    arms, E4, E5, span_shared = build_arms()
    rng = np.random.default_rng(20261001)
    draws = rng.uniform(-1.0, 1.0, size=(N_DRAWS, 5))

    r_bin0 = spectrum(np.diag(arms["binary"]["E"]).astype(complex)
                      + 1j * GAMMA_COMPARE * arms["binary"]["A"])[2]
    r_q0 = spectrum(np.diag(arms["ququint_PRIMARY"]["E"]).astype(complex)
                     + 1j * GAMMA_COMPARE * arms["ququint_PRIMARY"]["A"])[2]

    print("Diagnostik 048-D (NICHT verdict-tragend), gamma=0.02:")
    print("")
    print("D1: K2 arm-symmetrisch (shape=(E/span_shared)^2, keine Re-Norm):")
    for delta in (0.001, 0.01, 0.05):
        Hb = (np.diag(arms["binary"]["E"] + delta * span_shared
                      * (arms["binary"]["E"] / span_shared) ** 2)
              + 1j * GAMMA_COMPARE * arms["binary"]["A"])
        Hq = (np.diag(arms["ququint_PRIMARY"]["E"] + delta * span_shared
                      * (arms["ququint_PRIMARY"]["E"] / span_shared) ** 2)
              + 1j * GAMMA_COMPARE * arms["ququint_PRIMARY"]["A"])
        gb, gq = rel_drift(r_bin0, spectrum(Hb)[2]), rel_drift(r_q0, spectrum(Hq)[2])
        print("   delta=%.3f  Gamma_bin=%.6e  Gamma_q5=%.6e  q/b=%.4f"
              % (delta, gb, gq, gq / gb))

    print("")
    print("D2: K4 per-pair (S = alle-Paare-Offdiag unnormalisiert):")
    for delta in (0.001, 0.01):
        Sb = np.ones((4, 4)) - np.eye(4)
        Sq = np.ones((5, 5)) - np.eye(5)
        Hb = (np.diag(arms["binary"]["E"]).astype(complex)
              + 1j * GAMMA_COMPARE * arms["binary"]["A"]
              + delta * span_shared * Sb)
        Hq = (np.diag(arms["ququint_PRIMARY"]["E"]).astype(complex)
              + 1j * GAMMA_COMPARE * arms["ququint_PRIMARY"]["A"]
              + delta * span_shared * Sq)
        gb, gq = rel_drift(r_bin0, spectrum(Hb)[2]), rel_drift(r_q0, spectrum(Hq)[2])
        print("   delta=%.3f  Gamma_bin=%.6e  Gamma_q5=%.6e  q/b=%.4f"
              % (delta, gb, gq, gq / gb))

    print("")
    print("D3: Kontrollarm unter K3 (Platzhalter-Gap-Fragilitaet):")
    Hc0 = (np.diag(arms["ququint_CONTROL"]["E"]).astype(complex)
           + 1j * GAMMA_COMPARE * arms["ququint_CONTROL"]["A"])
    _, gaps_c0, r_c0 = spectrum(Hc0)
    for delta in (0.001, 0.01):
        crossings = 0
        for k in range(N_DRAWS):
            u = draws[k][:5]
            Hc = (np.diag(arms["ququint_CONTROL"]["E"]
                          + delta * span_shared * u).astype(complex)
                  + 1j * GAMMA_COMPARE * arms["ququint_CONTROL"]["A"])
            _, gaps_c, _ = spectrum(Hc)
            if gaps_c[-1] <= 0.0:
                crossings += 1
        print("   delta=%.3f  Level-Crossings im Platzhalter-Gap: %d/%d"
              % (delta, crossings, N_DRAWS))


if __name__ == "__main__":
    main()