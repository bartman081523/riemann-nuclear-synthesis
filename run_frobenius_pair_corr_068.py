"""Runner fuer EXPERIMENT 068: Frobenius Monodromy Pair Correlation & Montgomery-Odlyzko GUE Spectral Bridge."""

from __future__ import annotations
import json
import math
import numpy as np

from primequant.weil import (
    artin_schreier_frobenius_angles,
    unfold_frobenius_angles,
    spectral_pair_correlation,
    montgomery_odlyzko_gue,
)

PREREG_SHA256 = "79cda144f079633627e5cd3da7c730e8680975e560177dbec0d501acd7757c43"

def spectral_form_factor(unfolded: list[float], tau_grid: list[float]) -> list[float]:
    """Berechnet den spektralen Formfaktor K(tau) = (1/N) * |sum_{j=1}^N exp(2*pi*i*tau*e_j)|^2."""
    n = len(unfolded)
    arr = np.array(unfolded, dtype=float)
    k_vals = []
    for tau in tau_grid:
        phases = 2.0 * np.pi * tau * arr
        s = np.sum(np.exp(1j * phases))
        k = float(np.abs(s) ** 2) / float(n)
        k_vals.append(k)
    return k_vals

def run():
    moduli = [257, 503, 1009]
    results = {}

    for q in moduli:
        print(f"Berechne Frobenius-Winkel fuer q = {q}...")
        angles = artin_schreier_frobenius_angles(q, degree=3)
        unfolded = unfold_frobenius_angles(angles)
        
        # Paarkorrelation R_2(s) auf [0, 4] mit 40 Bins
        s_max = 4.0
        n_bins = 40
        bin_centers, r2 = spectral_pair_correlation(unfolded, s_max=s_max, n_bins=n_bins)
        gue_curve = [montgomery_odlyzko_gue(s) for s in bin_centers]
        poisson_curve = [1.0] * n_bins
        
        # Regionale Metriken
        # Repulsion: s in [0.0, 0.2]
        repulsion_r2 = [r for s, r in zip(bin_centers, r2) if s <= 0.2]
        mean_repulsion = float(np.mean(repulsion_r2)) if repulsion_r2 else 0.0
        
        # Mittlerer Bereich s in [0.5, 1.5]
        mid_indices = [i for i, s in enumerate(bin_centers) if 0.5 <= s <= 1.5]
        rmsd_gue = float(np.sqrt(np.mean([(r2[i] - gue_curve[i])**2 for i in mid_indices])))
        rmsd_poisson = float(np.sqrt(np.mean([(r2[i] - poisson_curve[i])**2 for i in mid_indices])))
        
        # Grosser Bereich s in [2.5, 4.0]
        tail_r2 = [r for s, r in zip(bin_centers, r2) if 2.5 <= s <= 4.0]
        mean_tail_dev = float(np.mean([abs(r - 1.0) for r in tail_r2]))
        
        # Spektraler Formfaktor K(tau)
        tau_grid = [float(t) for t in np.linspace(0.02, 1.0, 50)]
        k_tau = spectral_form_factor(unfolded, tau_grid)
        early_k = [k for t, k in zip(tau_grid, k_tau) if t < 0.5]
        min_early_k = float(np.min(early_k)) if early_k else 1.0
        
        results[str(q)] = {
            "q": q,
            "degree": 3,
            "n_angles": len(angles),
            "bin_centers": bin_centers,
            "r2_empirical": r2,
            "r2_gue": gue_curve,
            "mean_repulsion_s_le_0_2": mean_repulsion,
            "rmsd_gue_mid": rmsd_gue,
            "rmsd_poisson_mid": rmsd_poisson,
            "mean_tail_dev_large_s": mean_tail_dev,
            "tau_grid": tau_grid,
            "spectral_form_factor_k": k_tau,
            "min_k_early_tau": min_early_k,
        }

    raw_payload = {
        "experiment_id": "068",
        "name": "H-FROBENIUS-PAIR-CORRELATION-GUE",
        "prereg_sha256": PREREG_SHA256,
        "results": results,
    }

    with open("pt_frobenius_pair_corr_068_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_payload, f, indent=2)
    print("Rohdaten erfolgreich exportiert nach pt_frobenius_pair_corr_068_raw.json")

if __name__ == "__main__":
    run()
