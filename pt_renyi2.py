"""
EXPERIMENT 008 - Renyi-2 Entropie der Prime States (offline)

Hypothese: Latorre-Sierra benutzt Renyi-2 in ihrer Analyse, nicht
Schmidt-vN. Resolution (b) der LATORE_SPANNUNG_NOTE verlangt Renyi-2
auf demselben N-Sweep.

Renyi-2:
  S_2(rho_A) = -log_2 (tr rho_A^2) = -log_2 (sum_i s_i^4)

Implementierung: aus den klassisch berechneten s_i^2 (s_sq_classical in
pt_prime_state_qpu_singleshot_results.json) Renyi-2 berechnen und
log-log-fit auf S_2 vs N.

Vergleich:
  alpha_vN  = 0.272  (Aer, Schmidt)
  alpha_vN  = 0.348  (QPU, Schmidt)
  alpha_2   = ?      (Aer, Renyi-2)   <-- diese Messung
  alpha_2_QPU = ?    (QPU, Renyi-2)   <-- spaeter, Fez-Reset

Erwartung SciMind 5.0:
  S_2 <= S_vN (always), und S_2 skaliert *strenger* sublinear
  wenn das Spektrum der s_i^2 eine power-law Verteilung hat
  (typisch fuer Primzahl-typische Verteilungen).
"""
import json
import math
import os

import numpy as np


def renyi_2(s_sq):
    """S_2(rho_A) = -log_2 sum(s_i^4) gegeben Schmidt-Wahrscheinlichkeiten s_i^2."""
    s_sq = np.asarray(s_sq, dtype=float)
    s_sq = s_sq[s_sq > 0]
    return -math.log2(np.sum(s_sq ** 2))


def main():
    # Lade QPU-Singleshot Resultate (enthalten s_sq_classical und s_sq_qpu)
    with open("pt_prime_state_qpu_singleshot_results.json") as f:
        d = json.load(f)

    rows = []
    for r in d["results"]:
        N = r["N"]
        s_sq_classical = r["s_sq_classical"]
        s_sq_qpu = r["s_sq_qpu"]
        S2_classical = renyi_2(s_sq_classical)
        S2_qpu = renyi_2(s_sq_qpu)
        rows.append((N, S2_classical, S2_qpu))
        print(f"N={N:4d}  S_2(classical) = {S2_classical:.4f}   "
              f"S_2(QPU) = {S2_qpu:.4f}")

    # Log-log fit
    N_arr = np.array([r[0] for r in rows], dtype=float)
    S2_A = np.array([r[1] for r in rows], dtype=float)
    S2_Q = np.array([r[2] for r in rows], dtype=float)

    # Fit S_2 = a * N^alpha
    log_N = np.log(N_arr)
    log_S2_A = np.log(S2_A)
    log_S2_Q = np.log(S2_Q)

    p_A = np.polyfit(log_N, log_S2_A, 1)
    p_Q = np.polyfit(log_N, log_S2_Q, 1)

    alpha_2_A = p_A[0]
    alpha_2_Q = p_Q[0]

    print()
    print("=" * 60)
    print("Log-log Fit S_2 = a * N^alpha")
    print("=" * 60)
    print(f"Aer  : alpha_2 = {alpha_2_A:.4f}   a = {math.exp(p_A[1]):.4f}")
    print(f"QPU  : alpha_2 = {alpha_2_Q:.4f}   a = {math.exp(p_Q[1]):.4f}")
    print()
    print(f"Vergleich Schmidt-vN:")
    print(f"  alpha_vN_Aer = {d['alpha_aer']:.4f}")
    print(f"  alpha_vN_QPU = {d['alpha_qpu']:.4f}")
    print()
    print("Verdict:")
    if alpha_2_A < 0.5:
        print(f"  alpha_2_Aer = {alpha_2_A:.4f} < 0.5 — Sub-RH-Indikator Bestaetigt")
    else:
        print(f"  alpha_2_Aer = {alpha_2_A:.4f} >= 0.5 — Renyi-2 entspricht eher Latorre-Sierra")
    if alpha_2_Q < 0.5:
        print(f"  alpha_2_QPU = {alpha_2_Q:.4f} < 0.5 — QPU bestaetigt sublinear")
    else:
        print(f"  alpha_2_QPU = {alpha_2_Q:.4f} >= 0.5 — QPU weicht ab (Dekohaerenz-Artefakt?)")

    out = {
        "n_data_points": len(rows),
        "renyi_2_classical": [(int(N), float(S2)) for N, S2, _ in rows],
        "renyi_2_qpu": [(int(N), float(S2)) for N, _, S2 in rows],
        "alpha_2_aer": float(alpha_2_A),
        "alpha_2_qpu": float(alpha_2_Q),
        "alpha_vN_aer": d["alpha_aer"],
        "alpha_vN_qpu": d["alpha_qpu"],
        "alpha_latorre_sierra": d["alpha_latorre_sierra"],
        "verdict": (
            "Renyi-2 entspricht Schmidt-vN im Skalierungsverhalten: "
            "alpha_2 ~ alpha_vN < 0.5. Latorre-Spannung NICHT durch "
            "Renyi-2 vs vN aufgeloest."
        )
        if abs(alpha_2_A - d["alpha_aer"]) < 0.1
        else (
            "Renyi-2 weicht signifikant von Schmidt-vN ab. "
            "Latorre-Spannung MOEGLICHERWEISE durch Renyi-2 aufgeloest."
        ),
    }
    with open("pt_renyi2_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print()
    print(f"Ergebnisse gespeichert: pt_renyi2_results.json")
    print(f"Verdict: {out['verdict']}")


if __name__ == "__main__":
    main()
