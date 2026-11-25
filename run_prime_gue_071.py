"""Runner fuer EXPERIMENT 071: H-PRIME-GUE-SPECTRAL-DUALITY."""

from __future__ import annotations
import json
import math
import numpy as np
from scipy.special import loggamma
from scipy.optimize import brentq

PREREG_SHA256 = "aa04615dacc42f82d4b6a56cd559eba0c97685bae2b641a15e959ce40655bd72"

def riemann_siegel_theta(t: float) -> float:
    z = 0.25 + 0.5j * t
    return float(np.imag(loggamma(z)) - 0.5 * t * np.log(np.pi))

def riemann_siegel_Z(t: float) -> float:
    N = int(np.floor(np.sqrt(t / (2.0 * np.pi))))
    th = riemann_siegel_theta(t)
    main_sum = sum(np.cos(th - t * np.log(n)) / np.sqrt(n) for n in range(1, N + 1)) * 2.0
    p = np.sqrt(t / (2.0 * np.pi)) - N
    C0 = np.cos(2.0 * np.pi * (p**2 - p - 1.0/16.0)) / np.cos(2.0 * np.pi * p)
    remainder = ((-1)**(N - 1)) * (t / (2.0 * np.pi))**(-0.25) * C0
    return main_sum + remainder

def find_riemann_zeros(t_min=10.0, t_max=150.0, step=0.2) -> list[float]:
    t_vals = np.arange(t_min, t_max, step)
    z_vals = [riemann_siegel_Z(t) for t in t_vals]
    zeros = []
    for i in range(len(t_vals) - 1):
        if z_vals[i] * z_vals[i+1] < 0:
            root = float(brentq(riemann_siegel_Z, t_vals[i], t_vals[i+1]))
            zeros.append(root)
    return zeros

def unfold_zeros(gammas: list[float]) -> list[float]:
    unfolded = []
    for t in gammas:
        n_t = (t / (2.0 * math.pi)) * math.log(t / (2.0 * math.pi * math.e)) + 7.0 / 8.0
        unfolded.append(float(n_t))
    return unfolded

def spectral_form_factor(unfolded: list[float], tau_grid: list[float]) -> list[float]:
    n = len(unfolded)
    arr = np.array(unfolded, dtype=float)
    k_vals = []
    for tau in tau_grid:
        phases = 2.0 * math.pi * tau * arr
        s = np.sum(np.exp(1j * phases))
        k = float(np.abs(s)**2) / float(n)
        k_vals.append(k)
    return k_vals

def prime_zeta_cross_correlation(gammas: list[float], max_p: int = 100) -> float:
    # Berechne Primzahlen bis max_p
    primes = []
    for n in range(2, max_p + 1):
        if all(n % d != 0 for d in range(2, int(math.isqrt(n)) + 1)):
            primes.append(n)
    
    # Duale Summe nach Weil / Cramer: S(gamma) = sum_{p <= max_p} (ln(p) / sqrt(p)) * cos(gamma * ln(p))
    # Wir berechnen das Signal auf den Nullstellen und mitteln:
    # C = (1 / N) * sum_{j=1}^N sum_{p} (ln(p) / sqrt(p)) * cos(gamma_j * ln(p))
    # Da die Nullstellen die Resonanzen der Primzahlen sind, ist die destruktive Interferenz
    # im Spektral-Mittel charakteristisch moduliert.
    # Normierte Korrelation zwischen Nullstellen-Abstaenden und Primzahl-Frequenzen:
    n_zeros = len(gammas)
    total_corr = 0.0
    for g in gammas:
        val = sum((math.log(p) / math.sqrt(p)) * math.cos(g * math.log(p)) for p in primes)
        total_corr += val
    
    # Mittlere Amplitude pro Nullstelle
    mean_val = total_corr / float(n_zeros)
    # Normiere auf theoretische Standardabweichung sqrt(sum ln(p)^2 / (2p))
    theoretical_std = math.sqrt(sum((math.log(p)**2) / (2.0 * p) for p in primes))
    normed_corr = abs(mean_val) / theoretical_std
    return float(normed_corr)

def run():
    print("Suche Nullstellen von Z(t) in [10, 150]...")
    gammas = find_riemann_zeros(10.0, 150.0, step=0.2)
    print(f"Gefundene Nullstellen: {len(gammas)}")
    
    unfolded = unfold_zeros(gammas)
    spacings = [unfolded[i+1] - unfolded[i] for i in range(len(unfolded) - 1)]
    
    frac_s_le_0_2 = float(np.mean(np.array(spacings) < 0.2))
    min_spacing = float(np.min(spacings))
    mean_spacing = float(np.mean(spacings))
    
    # Spektraler Formfaktor
    tau_grid = [float(t) for t in np.linspace(0.02, 0.8, 40)]
    k_tau = spectral_form_factor(unfolded, tau_grid)
    early_k = [k_tau[i] for i, t in enumerate(tau_grid) if t <= 0.4]
    min_k_early = float(np.min(early_k)) if early_k else 1.0
    
    # Duale Primzahl-Nullstellen-Resonanz
    c_prime_zeros = prime_zeta_cross_correlation(gammas, max_p=100)
    
    # QPU Hardware-Referenz (ibm_fez, Exp 067)
    qpu_fidelity = 0.9808
    
    results = {
        "n_zeros": len(gammas),
        "gammas": gammas,
        "unfolded_zeros": unfolded,
        "mean_spacing": mean_spacing,
        "min_spacing": min_spacing,
        "fraction_s_le_0_2": frac_s_le_0_2,
        "tau_grid": tau_grid,
        "k_tau": k_tau,
        "min_k_early_tau": min_k_early,
        "prime_zero_correlation": c_prime_zeros,
        "qpu_reference_fidelity": qpu_fidelity,
    }
    
    raw_payload = {
        "experiment_id": "071",
        "name": "H-PRIME-GUE-SPECTRAL-DUALITY",
        "prereg_sha256": PREREG_SHA256,
        "results": results,
    }
    
    with open("pt_prime_gue_071_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_payload, f, indent=2)
    print("Rohdaten erfolgreich exportiert nach pt_prime_gue_071_raw.json")

if __name__ == "__main__":
    run()
