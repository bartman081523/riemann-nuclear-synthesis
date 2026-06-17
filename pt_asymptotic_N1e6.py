"""
EXPERIMENT 014 - Saeule 3 Asymptotik-Validierung N=10^4..10^6 (offline)

Hintergrund: LATORE_SPANNUNG_NOTE Resolution (c) verlangt asymptotische
Daten. Bisher: N ∈ {7, 15, 31, 63, 127, 255, 511, 1023} (8 Punkte).
Mit N ∈ {10^4, 10^5, 10^6} erreichen wir 3 weitere Punkte und koennen
die Latorre-Hypothese "alpha -> 1 as N -> inf" empirisch testen.

Prereg-Hypothese (geschrieben VOR diesem Skript):
  H_A: alpha stabilisiert sich bei 0.347 (unsere Messung) — Sub-RH beibehalten
  H_B: alpha -> 1 (Latorre-Sierra Asymptotik) — Latorre hat Recht
  H_C: alpha ist ein anderes Power-Law mit anderem Exponenten

Implementierung: statevector-first, numpy, KEIN QPU.
  - Primzahl-Liste via Sieve of Eratosthenes
  - psi = (1/sqrt(pi(N))) * sum_{p<=N} |p>
  - Schmidt-Dekomposition mit bipartition n_A = n_qubits // 2
  - Schmidt-vN-Entropie
  - Log-log fit auf alle 11 Datenpunkte
  - Inkrementeller alpha (zeigt Asymptotik-Trend)
"""
import json
import math
import os
import time

import numpy as np


# === PREREG (VOR Ausfuehrung geschrieben) ===

PREREG = {
    "hypotheses": {
        "H_A_sub_rh_alpha_0347": "alpha stabilisiert sich bei ~0.347 — unsere finite-N-Messung extrapoliert",
        "H_B_latorre_alpha_1": "alpha -> 1 as N -> inf — Latorre-Sierra Asymptotik korrekt",
        "H_C_other": "alpha konvergiert zu einem anderen Power-Law-Exponenten"
    },
    "n_values": [10_000, 100_000, 1_000_000],
    "decision_rule": (
        "H_A bestaetigt: alpha_full (11 Punkte) ∈ [0.30, 0.40] "
        "UND alpha(N_max=10^6) ∈ [0.30, 0.40] "
        "UND |alpha(N_max=10^6) - alpha(N_max=1023)| < 0.05. "
        "H_B bestaetigt: alpha(N_max=10^6) > 0.7. "
        "H_C sonst."
    ),
    "anti_sharpshooter": (
        "Prereg wurde VOR Ausfuehrung von main() geschrieben. "
        "Keine ex-post Anpassung der Hypothesen."
    )
}


def is_prime_sieve(n):
    """Sieve of Eratosthenes: alle Primzahlen <= n."""
    if n < 2:
        return []
    sieve = bytearray([1]) * (n + 1)
    sieve[0] = sieve[1] = 0
    for i in range(2, int(math.isqrt(n)) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = 0
    return [i for i in range(n + 1) if sieve[i]]


def construct_P_N(primes, n_qubits):
    """Berechne |P_N> als numpy statevector (qiskit-agnostisch)."""
    dim = 2 ** n_qubits
    psi = np.zeros(dim, dtype=complex)
    for p in primes:
        psi[p] = 1.0
    psi /= np.linalg.norm(psi)
    return psi


def schmidt_decomposition(psi, n_A):
    """Schmidt-Zerlegung von |psi> in System A (n_A Qubits, LSB) und B (n_B Qubits).

    Qiskit-Konvention: q_0 = LSB, Index p = q_0 + 2*q_1 + ... + 2^(n-1) q_{n-1}
    System A = Bits 0..n_A-1, System B = Bits n_A..n-1.

    Reshape: psi[A + n_A * B] (F-order / column-major).
    """
    n = int(round(math.log2(psi.shape[0])))
    n_B = n - n_A
    dim_A = 2 ** n_A
    dim_B = 2 ** n_B
    psi_mat = psi.reshape((dim_A, dim_B), order="F")
    U, s, Vh = np.linalg.svd(psi_mat, full_matrices=False)
    return s ** 2  # Schmidt-Wahrscheinlichkeiten


def von_neumann_entropy(s_sq):
    s_sq = np.asarray(s_sq, dtype=float)
    s_sq = s_sq[s_sq > 0]
    return -float(np.sum(s_sq * np.log2(s_sq)))


def renyi_2(s_sq):
    s_sq = np.asarray(s_sq, dtype=float)
    s_sq = s_sq[s_sq > 0]
    return -float(math.log2(np.sum(s_sq ** 2)))


def load_existing_data():
    """Lade existierende N ∈ {7..1023} Datenpunkte."""
    rows = []
    # Aus QPU-Singleshot (deterministische statevector-Werte)
    with open("pt_prime_state_qpu_singleshot_results.json") as f:
        d_qpu = json.load(f)
    for r in d_qpu["results"]:
        rows.append({
            "N": r["N"],
            "n_qubits": r["n_qubits"],
            "n_A": r["n_A"],
            "pi_N": r["pi_N"],
            "S_vN": r["S_vN_classical"],
        })
    # Aus N255-Erweiterung
    with open("pt_prime_state_N255_results.json") as f:
        d_n255 = json.load(f)
    for r in d_n255["new_data_points"]:
        rows.append({
            "N": r["N"],
            "n_qubits": r["n_qubits"],
            "n_A": r["n_A"],
            "pi_N": r["pi_N"],
            "S_vN": r["S_vN"],
        })
    # Sortiere nach N
    rows.sort(key=lambda r: r["N"])
    return rows


def main():
    t0 = time.time()

    # === Schritt 1: Prereg schreiben (VOR Berechnung) ===
    with open("pt_asymptotic_N1e6_prereg.json", "w") as f:
        json.dump(PREREG, f, indent=2)
    print(f"Praeregistrierung geschrieben: pt_asymptotic_N1e6_prereg.json")
    print(f"Hypothesen: H_A (alpha=0.347), H_B (alpha=1), H_C (andere)")

    # === Schritt 2: Existierende Daten laden ===
    existing = load_existing_data()
    print(f"\nExistierende Datenpunkte: {len(existing)}")
    print(f"  N ∈ {[r['N'] for r in existing]}")

    # === Schritt 3: Neue N ∈ {10^4, 10^5, 10^6} ===
    N_new_list = PREREG["n_values"]
    new_rows = []
    for N in N_new_list:
        print(f"\n[{time.time()-t0:.1f}s] === N = {N:,} ===")
        t_n = time.time()

        # Primzahlen via Sieve
        primes = is_prime_sieve(N)
        pi_N = len(primes)
        n_qubits = int(math.ceil(math.log2(N + 1)))
        n_A = n_qubits // 2
        print(f"  pi({N}) = {pi_N}, n_qubits = {n_qubits}, n_A = {n_A}")

        # Statevector (16 MB bei N=10^6)
        psi = construct_P_N(primes, n_qubits)
        print(f"  psi memory: {psi.nbytes/1e6:.1f} MB, |psi| = {np.linalg.norm(psi):.6f}")

        # Schmidt-Dekomposition (teuer)
        t_svd = time.time()
        s_sq = schmidt_decomposition(psi, n_A)
        print(f"  SVD dauerte: {time.time()-t_svd:.2f}s, "
              f"#Schmidt = {len(s_sq[s_sq>1e-12])}")

        # Entropien
        S_vN = von_neumann_entropy(s_sq)
        S_2 = renyi_2(s_sq)
        print(f"  S_vN = {S_vN:.4f}, S_2 = {S_2:.4f}")

        new_rows.append({
            "N": N,
            "n_qubits": n_qubits,
            "n_A": n_A,
            "pi_N": pi_N,
            "S_vN": S_vN,
            "S_2": S_2,
            "n_schmidt_nonzero": int(len(s_sq[s_sq>1e-12])),
            "computation_seconds": float(time.time() - t_n)
        })

    # === Schritt 4: Kombinierte Auswertung ===
    all_rows = existing + new_rows
    N_arr = np.array([r["N"] for r in all_rows], dtype=float)
    S_vN_arr = np.array([r["S_vN"] for r in all_rows], dtype=float)
    S_2_arr = np.array([r.get("S_2", renyi_2(np.array([r["N"]]))) for r in all_rows], dtype=float)
    # Falls S_2 nicht existiert, einfachheitshalber mit N-Wert ueberschreiben spaeter

    # Log-log fit (alle Punkte)
    log_N = np.log(N_arr)
    log_S_vN = np.log(S_vN_arr)
    p_vN = np.polyfit(log_N, log_S_vN, 1)
    alpha_vN_full = p_vN[0]
    log_a_vN = p_vN[1]

    # Renyi-2 fit (nur neue + existierende mit S_2)
    s2_existing = [r for r in existing if "S_2" in r]
    if s2_existing:
        # Lade aus N255-Results
        with open("pt_prime_state_N255_results.json") as f:
            d255 = json.load(f)
        # s_sq aus N255-Rows
        s2_data = []
        for r in d255["new_data_points"]:
            s2_data.append((r["N"], r["S_2"]))
        # QPU-Singleshot hat kein S_2 direkt, also ueberspringen
        for r in s2_existing:
            pass  # None
    # Besser: alle 11 Punkte (existing + new) — S_2 nur fuer die, die es haben
    s2_rows = [r for r in all_rows if "S_2" in r]
    if s2_rows:
        N_s2 = np.array([r["N"] for r in s2_rows], dtype=float)
        S_2_clean = np.array([r["S_2"] for r in s2_rows], dtype=float)
        p_s2 = np.polyfit(np.log(N_s2), np.log(S_2_clean), 1)
        alpha_2_full = p_s2[0]
    else:
        alpha_2_full = float("nan")

    # === Schritt 5: Inkrementeller alpha (zeigt Asymptotik-Trend) ===
    print()
    print("=" * 70)
    print("INKREMENTELLER ALPHA (Asymptotik-Trend):")
    print("=" * 70)
    incremental = []
    for i in range(2, len(N_arr)):
        sub_N = N_arr[:i + 1]
        sub_S = S_vN_arr[:i + 1]
        p_sub = np.polyfit(np.log(sub_N), np.log(sub_S), 1)
        alpha_sub = p_sub[0]
        incremental.append({
            "N_max": int(N_arr[i]),
            "n_pts": i + 1,
            "alpha_vN": float(alpha_sub)
        })
        print(f"  N_max = {N_arr[i]:>10.0f}  n_pts = {i+1:2d}  alpha = {alpha_sub:.4f}")

    # === Schritt 6: Verdict ===
    print()
    print("=" * 70)
    print("VERDICT:")
    print("=" * 70)
    print(f"  alpha_vN (alle {len(N_arr)} Punkte) = {alpha_vN_full:.4f}")
    if not math.isnan(alpha_2_full):
        print(f"  alpha_Renyi-2 ({len(s2_rows)} Punkte mit S_2) = {alpha_2_full:.4f}")

    # H_A / H_B / H_C Entscheidung
    alpha_asymptotic = incremental[-1]["alpha_vN"]  # letzter Punkt
    alpha_finite_1023 = next(x["alpha_vN"] for x in incremental if x["N_max"] == 1023)
    if 0.30 <= alpha_vN_full <= 0.40 and 0.30 <= alpha_asymptotic <= 0.40 and \
            abs(alpha_asymptotic - alpha_finite_1023) < 0.05:
        verdict = "H_A_bestaetigt (alpha stabil bei 0.347)"
    elif alpha_asymptotic > 0.7:
        verdict = "H_B_bestaetigt (alpha -> 1, Latorre hat recht)"
    else:
        verdict = "H_C (anderes Power-Law)"

    print(f"  alpha(N=10^6) = {alpha_asymptotic:.4f}  (N=1023: {alpha_finite_1023:.4f})")
    print(f"  VERDICT: {verdict}")

    # === Schritt 7: Speichern ===
    output = {
        "prereg_file": "pt_asymptotic_N1e6_prereg.json",
        "n_existing_points": len(existing),
        "n_new_points": len(new_rows),
        "N_list_all": [int(r["N"]) for r in all_rows],
        "alpha_vN_full_fit": float(alpha_vN_full),
        "log_a_vN": float(log_a_vN),
        "alpha_2_full_fit": float(alpha_2_full) if not math.isnan(alpha_2_full) else None,
        "incremental_alpha_vN": incremental,
        "new_data_points": new_rows,
        "verdict": verdict,
        "total_runtime_seconds": float(time.time() - t0)
    }
    with open("pt_asymptotic_N1e6_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nErgebnisse gespeichert: pt_asymptotic_N1e6_results.json")
    print(f"Gesamtlaufzeit: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
