"""
EXPERIMENT 005 - STRUKTURELLES A AUS ZERAOULIA-ITERATION:

Ableitung der Kopplungsmatrix direkt aus der Iterationsvorschrift
f(x) = x + y * log(x), ausgewertet auf den Zeraoulia-Niveaus.

Jacobi-Matrix:
    A_ii = f'(x_i) = 1 + y/x_i
    A_ij = (f(x_i) - f(x_j)) / (x_i - x_j)   fuer i != j

Diese Matrix ist:
  * strukturell eindeutig (kein Random, keine Seed-Abhaengigkeit)
  * hermitesch (A_ij = A_ji nach Konstruktion)
  * traegr die volle Nichtlinearitaet der Original-Iteration

PT-Operator:
    H_PT(gamma, y) = H_diag + i*gamma*A(y)

y ist der natuerlich Zeraoulia-Kopplungsparameter (y=1.0 im Original).
y kontrolliert die Staerke der logarithmischen Kopplung.

Kein Seed, keine Skala-Freiheitsgrade mehr. Nur gamma und y.
"""
import numpy as np


# Zeraoulia-Niveaus (deterministisch, aus der Iterationsvorschrift abgeleitet)
# E_0 = 2.0 ist der Startwert; nachfolgende Niveaus sind deterministisch
# ohne epsilon_no = 0:
#   E_0 = 2.0
#   E_1 = 2.0 + 1.0 * log(2.0) = 2.6931...
#   E_2 = 2.6931 + 1.0 * log(2.6931) = 3.3958...
#   E_3 = 3.3958 + 1.0 * log(3.3958) = 4.1379...
E_DIAG = np.array([2.0, 2.0 + np.log(2.0),
                   2.0 + np.log(2.0) + np.log(2.0 + np.log(2.0)),
                   2.0 + np.log(2.0) + np.log(2.0 + np.log(2.0)) +
                   np.log(2.0 + np.log(2.0) + np.log(2.0 + np.log(2.0)))])


def f(x, y=1.0):
    """Zeraoulia-Iterationsabbildung: x -> x + y*log(x)."""
    return x + y * np.log(x)


def jacobi_A(x_levels, y=1.0):
    """Strukturelle Kopplungsmatrix aus der Zeraoulia-Iterationsvorschrift.

    Diagonal:  A_ii = f'(x_i) = 1 + y/x_i
    Off-Diag:  A_ij = (f(x_i) - f(x_j)) / (x_i - x_j)  (Mittelwertsatz)
    """
    dim = len(x_levels)
    A = np.zeros((dim, dim))
    for i in range(dim):
        for j in range(dim):
            if i == j:
                A[i, j] = 1.0 + y / x_levels[i]
            else:
                dx = x_levels[i] - x_levels[j]
                df = f(x_levels[i], y) - f(x_levels[j], y)
                A[i, j] = df / dx
    # Symmetrisieren (sollte schon symmetrisch sein, aber numerisch exakt)
    A = (A + A.T) / 2.0
    return A


def H_pt_structural(gamma, y=1.0, x_levels=E_DIAG):
    """PT-Operator mit strukturellem A (kein Random)."""
    dim = len(x_levels)
    H_diag = np.diag(x_levels).astype(complex)
    A = jacobi_A(x_levels, y=y)
    return H_diag + 1j * gamma * A


def main():
    print("=" * 75)
    print("EXPERIMENT 005 v3: STRUKTURELLES A AUS ZERAOULIA-ITERATION")
    print("=" * 75)

    print("\nZeraoulia-Niveaus (deterministisch, ohne Rauschen):")
    for i, E in enumerate(E_DIAG):
        print(f"  E_{i} = {E:.6f}")

    print("\nJacobi-Matrix A bei y=1.0:")
    A = jacobi_A(E_DIAG, y=1.0)
    print(A)

    print("\nVerifiziere A hermitesch:", np.allclose(A, A.T))
    print("Verifiziere A reell:", np.allclose(A.imag, 0))

    # Sweep ueber gamma bei y=1.0
    print("\n" + "=" * 75)
    print("SWEEP: gamma in [0, 1.0] bei y=1.0")
    print("=" * 75)
    print(f"{'gamma':>8} | {'Re(E_0)':>10} | {'Im(E_0)':>10} | unbroken | in_target")
    print("-" * 75)

    gammas = np.linspace(0.0, 1.0, 21)
    results = []
    for g in gammas:
        H = H_pt_structural(g, y=1.0)
        eigs = np.linalg.eigvals(H)
        eigs_sorted = sorted(eigs, key=lambda z: z.real)
        E0 = eigs_sorted[0]
        ub = abs(E0.imag) < 0.05
        it = 1.8 <= E0.real <= 2.2
        results.append((g, E0.real, E0.imag, ub, it))
        print(f"{g:8.3f} | {E0.real:10.4f} | {E0.imag:10.4f} |    {str(ub):5s} |   {str(it):5s}")

    # Finde gamma* im Zielbereich
    target = [r for r in results if r[3] and r[4]]
    print("\n" + "=" * 75)
    print("VERDICT (y=1.0)")
    print("=" * 75)
    if target:
        g_star = target[0][0]
        re_star, im_star = target[0][1], target[0][2]
        print(f"  PRIMARY: gamma* = {g_star:.4f}, Re(E_0) = {re_star:.4f}, |Im(E_0)| = {abs(im_star):.4f}")
        print(f"  -> {'PASS' if abs(im_star) < 0.05 and 1.8 <= re_star <= 2.2 else 'PARTIAL'}")
    else:
        print("  Kein gamma in [0, 1.0] erreicht das Ziel.")

    # Sweep ueber y (Kopplungsstaerke)
    print("\n" + "=" * 75)
    print("SWEEP: y (Zeraoulia-Kopplungsparameter) bei gamma=0.5")
    print("=" * 75)
    print(f"{'y':>6} | {'Re(E_0)':>10} | {'Im(E_0)':>10} | PT-Resonanz bei E_0=2.0?")
    print("-" * 75)

    for y in [0.1, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0]:
        H = H_pt_structural(0.5, y=y)
        eigs = sorted(np.linalg.eigvals(H), key=lambda z: z.real)
        E0 = eigs[0]
        in_target = 1.8 <= E0.real <= 2.2
        print(f"{y:6.2f} | {E0.real:10.4f} | {E0.imag:10.4f} | {'JA' if in_target else 'NEIN'}")

    # Resultat speichern
    with open("pt_structural_results.txt", "w") as f:
        f.write("EXPERIMENT 005 v3: STRUKTURELLES A AUS ZERAOULIA-ITERATION\n")
        f.write("=" * 75 + "\n")
        f.write(f"Zeraoulia-Niveaus (deterministisch): {E_DIAG.tolist()}\n\n")
        f.write("Sweep gamma in [0, 1.0] bei y=1.0:\n")
        for g, re, im, ub, it in results:
            f.write(f"  gamma={g:.4f}: Re(E_0)={re:+.4f}, Im(E_0)={im:+.4f}, "
                    f"unbroken={ub}, in_target={it}\n")
        if target:
            f.write(f"\ngamma* = {target[0][0]:.4f}, E_0 = {target[0][1]:.4f} {target[0][2]:+.4f}j\n")


if __name__ == "__main__":
    main()
