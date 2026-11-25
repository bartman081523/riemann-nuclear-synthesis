"""Runner fuer EXPERIMENT 069: H-JACOBI-FROBENIUS-GUE-ASYMPTOTICS."""

from __future__ import annotations
import json
import math
import numpy as np

PREREG_SHA256 = "1746f0efda38a2522c8d715b89d4c29af7f95e67d741bc905f315991e38833bc"

def random_usp2g(g: int, rng: np.random.Generator) -> np.ndarray:
    """Erzeugt eine 2g x 2g Matrix aus dem Haar-Mass von USp(2g) via Quaternionen-QR."""
    blocks = []
    for i in range(g):
        row = []
        for j in range(g):
            a, b, c, d = rng.standard_normal(4) / 2.0
            blk = np.array([[complex(a, b), complex(c, d)], [complex(-c, d), complex(a, -b)]])
            row.append(blk)
        blocks.append(row)
    M = np.block(blocks)
    Q, _ = np.linalg.qr(M)
    return Q

def get_positive_eigenphases(Q: np.ndarray) -> np.ndarray:
    """Extrahiert die g positiven Eigenwinkel theta in (0, pi) der symplektischen Matrix Q."""
    eig = np.linalg.eigvals(Q)
    ang = np.angle(eig)
    pos = np.sort(ang[ang > 0])
    return pos

def spectral_form_factor(unfolded: np.ndarray, tau_grid: list[float]) -> list[float]:
    """Berechnet den Formfaktor K(tau) fuer das entfaltete Spektrum."""
    n = len(unfolded)
    k_vals = []
    for tau in tau_grid:
        phases = 2.0 * np.pi * tau * unfolded
        s = np.sum(np.exp(1j * phases))
        k = float(np.abs(s) ** 2) / float(n)
        k_vals.append(k)
    return k_vals

def pair_correlation(unfolded_levels: list[float], s_max: float = 3.0, n_bins: int = 30) -> tuple[list[float], list[float]]:
    """Paarkorrelation R_2(s) auf dem Einheitsdichte-Spektrum."""
    n = len(unfolded_levels)
    ds = s_max / float(n_bins)
    counts = np.zeros(n_bins)
    levels = np.sort(unfolded_levels)
    for i in range(n):
        for j in range(i + 1, n):
            diff = levels[j] - levels[i]
            if diff >= s_max:
                break
            bin_idx = int(diff / ds)
            if 0 <= bin_idx < n_bins:
                counts[bin_idx] += 2
    r2 = counts / (float(n) * ds)
    bin_centers = [(i + 0.5) * ds for i in range(n_bins)]
    return bin_centers, [float(x) for x in r2]

def run():
    genera = [20, 50, 100]
    n_samples = 50
    seed_base = 20261125
    rng = np.random.default_rng(seed_base)

    results = {}

    for g in genera:
        print(f"Generiere USp(2g) fuer g = {g} (2g={2*g}), {n_samples} Samples...")
        all_pos_phases = []
        all_spacings = []
        min_angles = []

        for _ in range(n_samples):
            Q = random_usp2g(g, rng)
            pos = get_positive_eigenphases(Q)
            all_pos_phases.append(pos)
            min_angles.append(float(pos[0]))
            
            # Unfolding auf (0, pi): e_j = theta_j * (g / pi)
            unf = pos * (float(g) / np.pi)
            sp = np.diff(unf)
            all_spacings.extend(sp)

        all_spacings = np.array(all_spacings)
        frac_s_le_0_2 = float(np.mean(all_spacings < 0.2))
        frac_s_le_0_05 = float(np.mean(all_spacings < 0.05))

        # Origin Repulsion: Anteil theta_1 < 0.1 * (pi / g)
        origin_threshold = 0.1 * (np.pi / float(g))
        frac_origin_close = float(np.mean(np.array(min_angles) < origin_threshold))

        # Paarkorrelation ueber alle Samples aggregiert
        s_max = 3.0
        n_bins = 30
        r2_acc = np.zeros(n_bins)
        k_tau_acc = np.zeros(40)
        tau_grid = [float(t) for t in np.linspace(0.02, 0.8, 40)]

        for pos in all_pos_phases:
            unf = list(pos * (float(g) / np.pi))
            bc, r2 = pair_correlation(unf, s_max=s_max, n_bins=n_bins)
            r2_acc += np.array(r2)
            k_vals = spectral_form_factor(np.array(unf), tau_grid)
            k_tau_acc += np.array(k_vals)

        mean_r2 = (r2_acc / float(n_samples)).tolist()
        mean_k_tau = (k_tau_acc / float(n_samples)).tolist()

        # Metriken gegen GUE und Poisson
        # GUE: R_2(s) = 1 - (sin(pi*s)/(pi*s))^2
        gue_curve = [1.0 if abs(s) < 1e-12 else 1.0 - (math.sin(math.pi * s) / (math.pi * s))**2 for s in bc]
        poi_curve = [1.0] * n_bins

        # RMSD fuer s in [0.2, 2.0]
        eval_idx = [i for i, s in enumerate(bc) if 0.2 <= s <= 2.0]
        rmsd_gue = float(np.sqrt(np.mean([(mean_r2[i] - gue_curve[i])**2 for i in eval_idx])))
        rmsd_poi = float(np.sqrt(np.mean([(mean_r2[i] - poi_curve[i])**2 for i in eval_idx])))

        # min K(tau) fuer tau in (0, 0.4)
        early_k = [mean_k_tau[i] for i, t in enumerate(tau_grid) if t <= 0.4]
        min_k_early = float(np.min(early_k)) if early_k else 1.0

        results[str(g)] = {
            "g": g,
            "matrix_dim": 2 * g,
            "n_samples": n_samples,
            "total_spacings_evaluated": len(all_spacings),
            "fraction_s_le_0_2": frac_s_le_0_2,
            "fraction_s_le_0_05": frac_s_le_0_05,
            "fraction_origin_close": frac_origin_close,
            "bin_centers": bc,
            "mean_r2": mean_r2,
            "gue_curve": gue_curve,
            "rmsd_gue_bulk": rmsd_gue,
            "rmsd_poisson_bulk": rmsd_poi,
            "tau_grid": tau_grid,
            "mean_spectral_form_factor": mean_k_tau,
            "min_k_early_tau": min_k_early,
        }

    raw_payload = {
        "experiment_id": "069",
        "name": "H-JACOBI-FROBENIUS-GUE-ASYMPTOTICS",
        "prereg_sha256": PREREG_SHA256,
        "results": results,
    }

    with open("pt_jacobi_frobenius_069_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_payload, f, indent=2)
    print("Rohdaten erfolgreich exportiert nach pt_jacobi_frobenius_069_raw.json")

if __name__ == "__main__":
    run()
