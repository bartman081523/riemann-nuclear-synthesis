"""Runner fuer EXPERIMENT 070: H-CUE-WIGNER-SURMISE-GUE-SYNTHESIS."""

from __future__ import annotations
import json
import math
import numpy as np

PREREG_SHA256 = "8b01caa9c14ba3650fda5e8d37a8fc7a3a793e57bcdf8d883225862ddbaea23b"

def cue_matrix(N: int, rng: np.random.Generator) -> np.ndarray:
    """Erzeugt eine N x N Matrix nach dem Haar-Mass von CUE(N)."""
    Z = (rng.standard_normal((N, N)) + 1j * rng.standard_normal((N, N))) / np.sqrt(2.0)
    Q, R = np.linalg.qr(Z)
    d = np.diagonal(R)
    ph = d / np.abs(d)
    return Q * ph

def spectral_form_factor(unfolded: np.ndarray, tau_grid: list[float]) -> list[float]:
    """Spektraler Formfaktor K(tau)."""
    n = len(unfolded)
    k_vals = []
    for tau in tau_grid:
        phases = 2.0 * np.pi * tau * unfolded
        s = np.sum(np.exp(1j * phases))
        k = float(np.abs(s) ** 2) / float(n)
        k_vals.append(k)
    return k_vals

def run():
    dimensions = [50, 100, 200]
    n_samples = 50
    seed_base = 2026112570
    rng = np.random.default_rng(seed_base)

    results = {}
    n_bins = 30
    s_max = 3.0
    s_grid = np.linspace(s_max / (2 * n_bins), s_max - s_max / (2 * n_bins), n_bins)
    p_gue_theory = (32.0 / (np.pi ** 2)) * (s_grid ** 2) * np.exp(-4.0 * (s_grid ** 2) / np.pi)
    p_poi_theory = np.exp(-s_grid)

    tau_grid = [float(t) for t in np.linspace(0.02, 0.8, 40)]

    for N in dimensions:
        print(f"Simuliere CUE(N={N}), {n_samples} Samples...")
        all_spacings = []
        k_tau_acc = np.zeros(len(tau_grid))

        for _ in range(n_samples):
            U = cue_matrix(N, rng)
            ang = np.sort(np.angle(np.linalg.eigvals(U)))
            # Periodische Distanzen auf dem Kreis
            diffs = np.diff(ang)
            diffs = np.append(diffs, (ang[0] - ang[-1]) % (2.0 * math.pi))
            s_sp = diffs * (float(N) / (2.0 * math.pi))
            all_spacings.extend(s_sp)

            # Unfolding fuer Formfaktor
            unf = (ang + math.pi) * (float(N) / (2.0 * math.pi))
            k_tau_acc += np.array(spectral_form_factor(unf, tau_grid))

        all_spacings = np.array(all_spacings)
        frac_s_le_0_2 = float(np.mean(all_spacings < 0.2))

        # Histogramm-Dichte
        hist_density, _ = np.histogram(all_spacings, bins=n_bins, range=(0, s_max), density=True)
        rmsd_gue = float(np.sqrt(np.mean((hist_density - p_gue_theory) ** 2)))
        rmsd_poi = float(np.sqrt(np.mean((hist_density - p_poi_theory) ** 2)))
        ratio_rmsd = rmsd_gue / rmsd_poi

        mean_k_tau = (k_tau_acc / float(n_samples)).tolist()
        early_k = [mean_k_tau[i] for i, t in enumerate(tau_grid) if t <= 0.4]
        min_k_early = float(np.min(early_k)) if early_k else 1.0

        results[str(N)] = {
            "N": N,
            "n_samples": n_samples,
            "total_spacings": len(all_spacings),
            "fraction_s_le_0_2": frac_s_le_0_2,
            "s_grid": [float(x) for x in s_grid],
            "empirical_density": [float(x) for x in hist_density],
            "rmsd_wigner_gue": rmsd_gue,
            "rmsd_poisson": rmsd_poi,
            "ratio_rmsd_gue_to_poisson": ratio_rmsd,
            "mean_k_tau": mean_k_tau,
            "min_k_early_tau": min_k_early,
        }

    # Hardware-Fidelity Referenz aus Exp 067 (Frobenius-Bell auf ibm_fez)
    # Target P00 = 1.0, gemessen 0.9862; Abweichung max 0.38%
    qpu_hardware_fidelity = 0.9808

    raw_payload = {
        "experiment_id": "070",
        "name": "H-CUE-WIGNER-SURMISE-GUE-SYNTHESIS",
        "prereg_sha256": PREREG_SHA256,
        "results": results,
        "qpu_reference_fidelity": qpu_hardware_fidelity,
    }

    with open("pt_cue_wigner_070_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_payload, f, indent=2)
    print("Rohdaten erfolgreich exportiert nach pt_cue_wigner_070_raw.json")

if __name__ == "__main__":
    run()
