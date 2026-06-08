"""
EXPERIMENT 005 - SEED VARIATION ANTI-SHARPSHOOTER TEST:
PT-Operator (Skala 0.4) mit 10 verschiedenen Seeds.

Frage: Ist die gamma* = 0.475 -> E_0 = 2.0009 Auswahl ein Artefakt
des speziellen Seeds 42, oder ein robustes Phaenomen?

Pre-registriertes Kriterium (Anti-Sharpshooter):
  PASS: Alle 10 Seeds erreichen Re(E_0) in [1.8, 2.2] fuer mindestens
        ein gamma in [0.0, 0.5].
  PARTIAL: 7-9 von 10 Seeds erreichen das Ziel.
  FAIL: <7 von 10 Seeds erreichen das Ziel.
"""
import numpy as np

# Reuse Skala und Diag aus dem Hauptskript
E_DIAG = np.array([2.0, 2.67870172, 3.8, 4.9])
SCALE = 0.4
SEEDS = list(range(1, 11))


def build_herm_V(dim, seed, scale=SCALE):
    rng = np.random.RandomState(seed)
    v_real = rng.normal(scale=scale, size=(dim, dim))
    v_imag = rng.normal(scale=scale, size=(dim, dim))
    V = v_real + 1j * v_imag
    return (V + V.conj().T) / 2.0


def build_antiherm_A(dim, seed, scale=SCALE):
    rng = np.random.RandomState(seed + 100)  # unabhaengig
    v_real = rng.normal(scale=scale, size=(dim, dim))
    v_imag = rng.normal(scale=scale, size=(dim, dim))
    M = v_real + 1j * v_imag
    return (M + M.conj().T) / 2.0


def H_pt(gamma, seed):
    dim = len(E_DIAG)
    H_diag = np.diag(E_DIAG).astype(complex)
    V_herm = build_herm_V(dim, seed=seed)
    A = build_antiherm_A(dim, seed=seed)
    return H_diag + V_herm + 1j * gamma * A


def find_gamma_star(gammas, seed, target_range=(1.8, 2.2)):
    """Fuer gegebenen Seed: finde gamma* mit Re(E_0) im Zielbereich."""
    for g in gammas:
        H = H_pt(g, seed=seed)
        eigs = np.linalg.eigvals(H)
        eigs_sorted = sorted(eigs, key=lambda z: z.real)
        E0 = eigs_sorted[0]
        if target_range[0] <= E0.real <= target_range[1]:
            return g, E0
    return None, None


def main():
    gammas = np.linspace(0.0, 0.5, 51)  # feinere Aufloesung
    target = (1.8, 2.2)

    print("=" * 80)
    print("EXPERIMENT 005 - SEED VARIATION (ANTI-SHARPSHOOTER)")
    print("=" * 80)
    print(f"{'Seed':>4} | {'gamma*':>8} | {'Re(E_0)':>10} | {'Im(E_0)':>10} | in_target")
    print("-" * 80)

    hits = 0
    results = []
    for s in SEEDS:
        g_star, E0 = find_gamma_star(gammas, s, target)
        if g_star is not None:
            hits += 1
            results.append((s, g_star, E0.real, E0.imag))
            print(f"{s:4d} | {g_star:8.4f} | {E0.real:10.4f} | {E0.imag:10.4f} |   YES")
        else:
            results.append((s, None, None, None))
            print(f"{s:4d} |    --   |       --  |       --  |   NO")

    print()
    print("=" * 80)
    print("VERDICT")
    print("=" * 80)
    print(f"  Seeds mit E_0 in [1.8, 2.2]: {hits}/10")

    # Statistik der gamma*-Werte (falls Treffer)
    g_stars = [r[1] for r in results if r[1] is not None]
    if g_stars:
        print(f"  gamma* Verteilung: mean = {np.mean(g_stars):.4f}, "
              f"std = {np.std(g_stars):.4f}, "
              f"min = {min(g_stars):.4f}, max = {max(g_stars):.4f}")

    if hits == 10:
        verdict = "PASS"
        print(f"  -> {verdict}: PT-Resonanz ist SEED-UNABHAENGIG.")
    elif hits >= 7:
        verdict = "PARTIAL"
        print(f"  -> {verdict}: PT-Resonanz haeufig aber nicht universell.")
    else:
        verdict = "FAIL"
        print(f"  -> {verdict}: gamma* = 0.475 ist SEED-ARTEFAKT.")

    with open("pt_seed_variation.txt", "w") as f:
        f.write(f"EXPERIMENT 005 - SEED VARIATION\n")
        f.write(f"Verdict: {verdict} ({hits}/10)\n")
        for s, g, re, im in results:
            if g is not None:
                f.write(f"Seed {s}: gamma* = {g:.4f}, E_0 = {re:+.4f} {im:+.4f}j\n")
            else:
                f.write(f"Seed {s}: NO HIT in [0, 0.5]\n")


if __name__ == "__main__":
    main()
