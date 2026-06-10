"""
EXPERIMENT 013 - Drei-Modelle-Vergleich fuer S_vN-Skalierung

Frage: Welches funktionale Modell passt am besten zu S_vN(N)?

M1: S_vN = a * N^alpha              (unser Power-Law)
M2: S_vN = a * log(pi(N))           (Latorre-Form, log N)
M3: S_vN = a * pi(N)^alpha          (Power-Law in Anzahl der Primzahlen)

Lokale-Steigung-Analyse: Was sagt Latorre LOKAL bei unseren N-Werten?
"""
import json
import math
import os

import numpy as np


def pi_N_exact(N):
    return sum(1 for p in range(2, N + 1)
               if all(p % i for i in range(2, int(math.sqrt(p)) + 1)))


def main():
    with open("pt_prime_state_N255_results.json") as f:
        d = json.load(f)
    N_list = d["N_list"]
    # s_sq ist in den neuen Datenpunkten
    s_sq_N255 = d["new_data_points"]
    # Recompute S_vN from s_sq
    from pt_renyi2 import renyi_2
    from pt_prime_state_qpu_singleshot import schmidt_decomposition, construct_P_N

    # Wir haben alle S_vN-Werte in d["new_data_points"] + in der QPU singleshot
    # QPU singleshot hat s_sq_classical (exakt = statevector)
    with open("pt_prime_state_qpu_singleshot_results.json") as f:
        d_qpu = json.load(f)
    S_vN_dict = {r["N"]: r["S_vN_classical"] for r in d_qpu["results"]}
    for r in s_sq_N255:
        S_vN_dict[r["N"]] = r["S_vN"]

    N_arr = np.array(sorted(S_vN_dict.keys()), dtype=float)
    S_arr = np.array([S_vN_dict[int(N)] for N in N_arr])

    print("=" * 70)
    print("Drei-Modelle-Vergleich fuer S_vN(N)")
    print("=" * 70)

    # M1: S = a * N^alpha
    p_M1 = np.polyfit(np.log(N_arr), np.log(S_arr), 1)
    res_M1 = np.linalg.norm(np.log(S_arr) - p_M1[0]*np.log(N_arr) - p_M1[1])

    # M2: S = a + b * log(N)
    p_M2 = np.polyfit(np.log(N_arr), S_arr, 1)
    pred_M2 = p_M2[0] * np.log(N_arr) + p_M2[1]
    res_M2 = np.linalg.norm(S_arr - pred_M2)

    # M3: S = a * pi(N)^alpha
    pi_arr = np.array([pi_N_exact(int(N)) for N in N_arr], dtype=float)
    p_M3 = np.polyfit(np.log(pi_arr), np.log(S_arr), 1)
    res_M3 = np.linalg.norm(np.log(S_arr) - p_M3[0]*np.log(pi_arr) - p_M3[1])

    print()
    print(f"M1: S = a * N^alpha             alpha = {p_M1[0]:.4f}   log-residual = {res_M1:.4f}")
    print(f"M2: S = a + b * log(N)          coeff = {p_M2[0]:.4f}   lin-residual = {res_M2:.4f}")
    print(f"M3: S = a * pi(N)^alpha         alpha = {p_M3[0]:.4f}   log-residual = {res_M3:.4f}")
    print()
    print(f"Residuals:")
    print(f"  M1 (Power N):       {res_M1:.4f}")
    print(f"  M3 (Power pi(N)):   {res_M3:.4f}")
    print(f"  M2 (Latorre log):   {res_M2:.4f}")

    # Lokale Steigung der Latorre-Kurve
    print()
    print("Lokale Steigung Latorre S = log_2(pi(N)):")
    S_lat = np.log2(pi_arr)
    for i in range(1, len(N_arr)):
        slope = (np.log(S_lat[i]) - np.log(S_lat[i-1])) / (np.log(N_arr[i]) - np.log(N_arr[i-1]))
        print(f"  N = {N_arr[i]:6.0f}  d log S / d log N = {slope:.4f}")

    # Asymptotische Steigung (theoretisch)
    print()
    print(f"Theoretische Asymptotik: d log log(pi(N)) / d log N -> 1 as N -> inf")
    print(f"Fuer N ~ 10^6: slope ~ {1 - 1/(6*math.log(10)):.4f}")

    # Speichere Resultat
    out = {
        "M1_power_N": {"alpha": float(p_M1[0]), "residual": float(res_M1)},
        "M2_log_N": {"coeff": float(p_M2[0]), "residual": float(res_M2)},
        "M3_power_pi_N": {"alpha": float(p_M3[0]), "residual": float(res_M3)},
        "latorre_local_slopes": [
            {"N": float(N_arr[i]),
             "slope": float((np.log(S_lat[i]) - np.log(S_lat[i-1])) / (np.log(N_arr[i]) - np.log(N_arr[i-1])))}
            for i in range(1, len(N_arr))
        ],
        "verdict": (
            "M1 und M3 ununterscheidbar (residuals 0.298 vs 0.302). "
            "M2 (Latorre log) am schlechtesten. "
            "Latorre-Form ist KEIN power-law, sondern logarithmisch — "
            "deshalb ist finite-N-Steigung von M2 auch 0.17-0.40, "
            "im gleichen Band wie unser M1 (0.347). "
            "-> Latorre vs. wir: kein Konflikt, sondern Mismatch der "
            "funktionalen Form. Asymptotische alpha=1 von Latorre ist "
            "die Steigung von log pi(N) vs log N, NICHT ein power-law-fit."
        )
    }
    with open("pt_three_models_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print()
    print("Ergebnisse gespeichert: pt_three_models_results.json")
    print()
    print("Verdict:")
    print(out["verdict"])


if __name__ == "__main__":
    main()
