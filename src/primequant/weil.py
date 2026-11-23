"""primequant.weil — Exakte endliche Weil-Darstellung und Galois-Projektion.

Garantie: EXAKT (stdlib-only: int, Fraction, Tuple; zero numpy/sympy/RNG).
Mathematische Grundlage:
  1. Finite Weil-Darstellung Mp_2(F_q) ueber GF(q):
     Erzeugt von diskreter Fourier-Transformation F_q, quadratischen Gauss-Phasen
     D_t = diag(omega^{t x^2}) und Modulo-Skalierungen M_a |x> = |a*x mod q>.
  2. Galois-Projektor Pi_G:
     Mittelt ueber die multiplikative Gruppe GF(q)*:
         Pi_G = (1/(q-1)) sum_{a in GF(q)*} M_a
     Isoliert den 1D symmetrischen Zustand |psi_triv> = (1/sqrt(q-1)) sum_{x=1}^{q-1} |x>
     und vernichtet den (q-2)-dimensionalen Standard-Symmetrie-Unterraum exakt.
  3. Zyklotomische Trace-Gram-Matrix G_{ij} = Tr_{Q(zeta_q)/Q}(zeta_q^{i-j}):
     Entspricht bit-exakt der Ramanujan-Matrix G_{ij} = c_q(i-j).
     Spektrum: Eigenwert 1 (Multiplizitaet 1), Eigenwert q (Multiplizitaet q-2),
     Determinante det(G) = q^{q-2} = Diskriminante des maximalen reellen Teilkoerpers.
  4. Stepanov-Multiplizitaets-Schranke:
     L = floor(sqrt(X)) Kettenlaenge von Theta-Lifts.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import List, Sequence, Tuple

from ._gfq import ist_primzahl
from ._cyc import (
    Element,
    Matrix,
    cyc_add,
    cyc_sub,
    cyc_mul,
    cyc_conj,
    cyc_omega,
    cyc_from_int,
    cyc_zero,
    cyc_one,
    cyc_make,
)


def trace_galois(element: Sequence[int], q: int) -> int:
    """Spur Tr_{Q(zeta_q)/Q}(X) = sum_{k=1}^{q-1} sigma_k(X).
    
    Garantie: EXAKT, Herkunft: exakt-definiert.
    Fuer X = sum_{a=0}^{q-2} c_a omega^a:
      Tr(omega^0) = q - 1
      Tr(omega^a) = -1 fuer a in {1, ..., q-2}
    Ergebnis ist immer eine ganze Zahl int.
    """
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl >= 2 sein, erhalten {q}")
    if len(element) != q - 1:
        raise ValueError(f"Element muss Laenge q-1 = {q-1} haben, erhalten {len(element)}")
    c0 = int(element[0])
    rest_sum = sum(int(c) for c in element[1:])
    return c0 * (q - 1) - rest_sum


def trace_gram_matrix(q: int) -> List[List[int]]:
    """Ganzzahlige (q-1)x(q-1) Gram-Matrix der Basis {1, omega, ..., omega^{q-2}}.
    
    Garantie: EXAKT, Herkunft: exakt-definiert.
    Eintrag G[i, j] = Tr(omega^{i - j}) = c_q(i - j):
      G[i, j] = q - 1 falls i == j
      G[i, j] = -1     falls i != j
    """
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl >= 2 sein, erhalten {q}")
    dim = q - 1
    G = []
    for i in range(dim):
        row = []
        for j in range(dim):
            row.append(q - 1 if i == j else -1)
        G.append(row)
    return G


def trace_gram_eigenschaften(q: int) -> dict:
    """Analytische Eigenschaften der Trace-Gram-Matrix.
    
    Garantie: EXAKT, Herkunft: abgeleitet.
    Da G = q * I_{q-1} - J_{q-1} (wobei J die Einsermatrix ist):
      J hat Eigenwert (q-1) mit Multiplizitaet 1 (All-Eins-Vektor)
      und Eigenwert 0 mit Multiplizitaet q-2.
      Daher hat G:
        Eigenwert q - (q - 1) = 1 (Multiplizitaet 1)
        Eigenwert q - 0 = q       (Multiplizitaet q - 2)
      Determinante det(G) = 1 * q^{q-2} = q^{q-2}.
    """
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl >= 2 sein, erhalten {q}")
    return {
        "q": q,
        "dimension": q - 1,
        "eigenwert_triv": 1,
        "multiplizitaet_triv": 1,
        "eigenwert_std": q,
        "multiplizitaet_std": q - 2,
        "determinante": q ** (q - 2),
    }


def weil_F_matrix(q: int) -> Matrix:
    """Unnormierte q x q diskrete Fourier-Matrix ueber Z[zeta_q].
    
    Garantie: EXAKT, Herkunft: exakt-definiert.
    F_{jk} = omega^{j * k mod q}.
    """
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl >= 2 sein, erhalten {q}")
    F = []
    for j in range(q):
        row = []
        for k in range(q):
            row.append(cyc_omega(q, (j * k) % q))
        F.append(row)
    return F


def weil_D_matrix(q: int, t: int = 1) -> Matrix:
    """Diagonale q x q quadratische Gauss-Phasen-Matrix D_t ueber Z[zeta_q].
    
    Garantie: EXAKT, Herkunft: exakt-definiert.
    D_{xx} = omega^{t * x^2 mod q}, D_{xy} = 0 fuer x != y.
    """
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl >= 2 sein, erhalten {q}")
    t_mod = t % q
    D = []
    zero = cyc_zero(q)
    for x in range(q):
        row = []
        for y in range(q):
            if x == y:
                row.append(cyc_omega(q, (t_mod * (x * x)) % q))
            else:
                row.append(zero)
        D.append(row)
    return D


def dilation_matrix(q: int, a: int) -> List[List[int]]:
    """Permutationsmatrix M_a |x> = |(a * x) mod q> fuer a in GF(q)*.
    
    Garantie: EXAKT, Herkunft: exakt-definiert.
    """
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl >= 2 sein, erhalten {q}")
    if a % q == 0:
        raise ValueError(f"a darf nicht durch q={q} teilbar sein")
    a_mod = a % q
    M = []
    for x in range(q):
        row = [0] * q
        row[(a_mod * x) % q] = 1
        M.append(row)
    return M


def galois_projector_matrix(q: int) -> List[List[Fraction]]:
    """q x q rationale Projektormatrix Pi_G.
    
    Garantie: EXAKT, Herkunft: exakt-definiert.
    Wirkung auf |0>: Pi_G |0> = |0>.
    Wirkung auf active Subspace (1 .. q-1):
      Pi_G |psi_triv> = |psi_triv> (Projektion auf 1D symmetrischen Zustand)
      Pi_G |psi_std> = 0 (Vernichtung aller nicht-trivialen Symmetrien).
    """
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl >= 2 sein, erhalten {q}")
    dim = q
    frac_inv = Fraction(1, q - 1)
    Pi = [[Fraction(0) for _ in range(dim)] for _ in range(dim)]
    
    Pi[0][0] = Fraction(1)
    for x in range(1, q):
        for y in range(1, q):
            Pi[y][x] = frac_inv
    return Pi


def trivial_state_amplitudes_squared(q: int) -> Tuple[Fraction, ...]:
    """Exakte Wahrscheinlichkeiten |<x|psi_triv>|^2 fuer x in {0, ..., q-1}.
    
    Garantie: EXAKT, Herkunft: exakt-definiert.
    p(0) = 0, p(x) = 1/(q-1) fuer x in {1, ..., q-1}.
    """
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl >= 2 sein, erhalten {q}")
    frac = Fraction(1, q - 1)
    return (Fraction(0),) + (frac,) * (q - 1)


def stepanov_multiplicity_bound(X: int) -> int:
    """Berechnet die exakte Theta-Kettenlaenge L = floor(sqrt(X)).
    
    Garantie: EXAKT, Herkunft: abgeleitet.
    """
    if X < 1:
        raise ValueError(f"X muss >= 1 sein, erhalten {X}")
    return math.isqrt(X)


def path_quadric_phase(q: int, x_vec: Sequence[int]) -> int:
    """Berechnet Q(x) = sum_{j=0}^{k-2} x_j * x_{j+1} mod q.
    
    Garantie: EXAKT, Herkunft: exakt-definiert.
    Kanonische Pfad-Quadrik nach Alpöge-Claude (Footnote 3 / Remark).
    """
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl sein, erhalten {q}")
    k = len(x_vec)
    if k < 2:
        return 0
    return sum((int(x_vec[j]) * int(x_vec[j + 1])) for j in range(k - 1)) % q


def path_quadric_ramanujan_sum(q: int, x_vec: Sequence[int]) -> int:
    """Exakte Summe sum_{h in GF(q)*} e_q(h * Q(x)) == c_q(Q(x)).
    
    Garantie: EXAKT, Herkunft: Theorem (Alpöge-Claude / Ramanujan Identität).
    Liefert q - 1 falls Q(x) == 0 mod q, sonst -1.
    """
    phase = path_quadric_phase(q, x_vec)
    return (q - 1) if (phase % q == 0) else -1


def path_quadric_gauss_sum_even(q: int, k: int) -> int:
    """Exakte ganzzahlige Gauss-Summe G(h, Q) = sum_{x in GF(q)^k} e_q(h * Q(x)) fuer gerades k.
    
    Garantie: EXAKT, Herkunft: Theorem (Weil-Schranke fuer quadratische Hyperflaechen).
    Fuer nicht-ausgeartete Pfad-Quadriken gerader Laenge k = 2m gilt fuer jedes h in GF(q)*:
      G(h, Q) = q^{k/2} = q^m.
    Die Summe ist rein reell, unabhaengig von h und saturiert exakt die Quadratwurzel-Schranke
    |G|^2 = q^k = dim.
    """
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl sein, erhalten {q}")
    if k < 2 or k % 2 != 0:
        raise ValueError(f"k muss gerade und >= 2 sein, erhalten {k}")
    m = k // 2
    return q ** m


# ---------------------------------------------------------------------------
# Artin-Schreier Exponentialsummen & Deligne-Weil Schranken
# ---------------------------------------------------------------------------

def poly_eval_mod(coeffs: Sequence[int], x: int, q: int) -> int:
    """Horner-Schema zur Auswertung von sum_i coeffs[i] * x^i mod q.
    
    Garantie: EXAKT, Herkunft: exakt-definiert.
    coeffs[0] ist der konstante Term, coeffs[d] ist der Leitkoeffizient.
    """
    res = 0
    for c in reversed(coeffs):
        res = (res * x + int(c)) % q
    return res % q


def artin_schreier_exponential_sum(q: int, coeffs: Sequence[int]) -> Element:
    """Berechnet die exakte Exponentialsumme S(f) = sum_{x=0}^{q-1} omega^{f(x) mod q} in Z[zeta_q].
    
    Garantie: EXAKT, Herkunft: exakt-definiert.
    Liefert das Element in Z[zeta_q] ueber die kanonische Basis (1, omega, ..., omega^{q-2}).
    """
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl >= 2 sein, erhalten {q}")
    s = cyc_zero(q)
    for x in range(q):
        fx = poly_eval_mod(coeffs, x, q)
        s = cyc_add(s, cyc_omega(q, fx))
    return s


def artin_schreier_magnitude_squared(q: int, coeffs: Sequence[int]) -> Element:
    """Berechnet das algebraische Betragsquadrat |S(f)|^2 = S(f) * conj(S(f)) in Z[zeta_q].
    
    Garantie: EXAKT, Herkunft: Theorem (Deligne / Weil).
    Fuer quadratische Gauss-Summen (Grad d=2, a != 0 mod q) gilt bit-identisch:
      |S(f)|^2 = (q, 0, ..., 0) = q * 1.
    """
    s = artin_schreier_exponential_sum(q, coeffs)
    s_conj = cyc_conj(s, q)
    return cyc_mul(s, s_conj, q)


def artin_schreier_deligne_bound(q: int, degree: int) -> int:
    """Deligne-Schranke fuer das Betragsquadrat: Bound = (d - 1)^2 * q.
    
    Garantie: EXAKT, Herkunft: Theorem (Deligne, Weil I, 1974).
    Fuer jedes Polynom f(x) mit Grad d >= 1 und gcd(d, q) = 1 gilt
    fuer jede komplexe Einbettung: |sigma_k(S(f))|^2 <= (d - 1)^2 * q.
    """
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl >= 2 sein, erhalten {q}")
    if degree < 1:
        raise ValueError(f"degree muss >= 1 sein, erhalten {degree}")
    return ((degree - 1) ** 2) * q


def artin_schreier_phase_matrix(q: int, coeffs: Sequence[int]) -> Matrix:
    """Erzeugt die q x q Artin-Schreier Phasenmatrix U_f = diag(omega^{f(x) mod q}).
    
    Garantie: EXAKT, Herkunft: exakt-definiert.
    """
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl >= 2 sein, erhalten {q}")
    zero = cyc_zero(q)
    mat: Matrix = []
    for x in range(q):
        zeile = [zero] * q
        fx = poly_eval_mod(coeffs, x, q)
        zeile[x] = cyc_omega(q, fx)
        mat.append(zeile)
    return mat


def wigner_semicircle_moment_exact(k: int) -> Fraction:
    """Exaktes 2k-tes Moment des Wigner-Halbkreisgesetzes rho(t) = (2/pi)*sqrt(1-t^2) auf [-1, 1].
    
    Garantie: EXAKT, Herkunft: Theorem (Wigner / Sato-Tate).
    m_{2k} = integral_{-1}^1 t^{2k} rho(t) dt = C_k / 4^k = (1 / (4^k * (k + 1))) * binom(2k, k).
    Ungerade Momente m_{2k+1} sind aus Symmetriegruenden identisch 0.
    """
    if k < 0:
        raise ValueError(f"k muss >= 0 sein, erhalten {k}")
    if k == 0:
        return Fraction(1, 1)
    # Catalan-Zahl C_k = (2k)! / ((k+1)! * k!)
    c_k = math.comb(2 * k, k) // (k + 1)
    return Fraction(c_k, 4 ** k)


def artin_schreier_frobenius_angles(q: int, degree: int = 3) -> list[float]:
    """Berechnet die Frobenius-Eigenwinkel theta_a in [0, pi] der Artin-Schreier-Familie f_a(x) = x^d + a*x.
    
    Garantie: numerisch exakt gemaess Deligne-Schranke |S(f)| <= (d-1)*sqrt(q).
    Fuer kubische Artin-Schreier-Kurven (d=3) gilt: S(x^3 + ax) = 2*sqrt(q)*cos(theta_a).
    """
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl >= 2 sein, erhalten {q}")
    angles: list[float] = []
    bound = float(degree - 1) * math.sqrt(float(q))
    for a in range(q):
        coeffs = [0] * (degree + 1)
        coeffs[degree] = 1
        coeffs[1] = a
        # Berechne S(f) als komplexe Zahl via Einbettung k=1
        val_c = 0.0 + 0.0j
        for x in range(q):
            fx = poly_eval_mod(coeffs, x, q)
            phi = 2.0 * math.pi * fx / float(q)
            val_c += complex(math.cos(phi), math.sin(phi))
        # Da f(x) reell ist bezueglich Permutationen, ist S(f) reell fuer x^3+ax
        re_val = val_c.real
        # Clamping gegen minimale Rundungsabweichungen an den Deligne-Grenzen
        norm_val = max(-1.0, min(1.0, re_val / bound))
        theta = math.acos(norm_val)
        angles.append(theta)
    return sorted(angles)


def unfold_frobenius_angles(angles: Sequence[float]) -> list[float]:
    """Entfaltet (unfolds) die Frobenius-Eigenwinkel mit der Sato-Tate/Wigner-Dichte.
    
    Fuer Sato-Tate gilt F(theta) = integral_0^theta (2/pi)*sin^2(t) dt = (theta - sin(2*theta)/2) / pi.
    Das entfaltete Spektrum e_j = N * F(theta_j) besitzt mittlere Dichte 1 und mittleren Spacing 1.
    """
    n = len(angles)
    if n == 0:
        return []
    unfolded: list[float] = []
    for th in angles:
        # F(th) = (th - 0.5 * sin(2*th)) / pi auf [0, pi]
        f_val = (th - 0.5 * math.sin(2.0 * th)) / math.pi
        unfolded.append(float(n) * f_val)
    return unfolded


def spectral_pair_correlation(unfolded_levels: Sequence[float], s_max: float = 3.0, n_bins: int = 30) -> tuple[list[float], list[float]]:
    """Berechnet die 2-Punkte-Paarkorrelationsfunktion R_2(s) des entfalteten Spektrums.
    
    R_2(s) = (1 / N) * #{(j, k): j != k, |e_j - e_k| in [s, s + ds]} / ds.
    Fuer ein GUE-Spektrum (Montgomery-Odlyzko / Riemann-Nullstellen) gilt:
      R_2^{GUE}(s) = 1 - (sin(pi * s) / (pi * s))^2.
    Fuer ein unkorreliertes Poisson-Spektrum gilt:
      R_2^{Poisson}(s) = 1.
    """
    n = len(unfolded_levels)
    if n < 2:
        return [], []
    ds = s_max / float(n_bins)
    bin_counts = [0] * n_bins
    bin_centers = [(i + 0.5) * ds for i in range(n_bins)]
    
    # Paar-Distanzen |e_j - e_k|
    levels = sorted(unfolded_levels)
    for i in range(n):
        for j in range(i + 1, n):
            diff = levels[j] - levels[i]
            if diff >= s_max:
                break
            bin_idx = int(diff / ds)
            if 0 <= bin_idx < n_bins:
                bin_counts[bin_idx] += 2  # symmetrisch (j,k) und (k,j)
    
    # Normierung: Dichte pro N und pro ds
    r2_values = [count / (float(n) * ds) for count in bin_counts]
    return bin_centers, r2_values


def montgomery_odlyzko_gue(s: float) -> float:
    """Theoretische Montgomery-Odlyzko GUE Paarkorrelation: R_2(s) = 1 - (sin(pi*s)/(pi*s))^2."""
    if abs(s) < 1e-12:
        return 0.0
    val = math.sin(math.pi * s) / (math.pi * s)
    return 1.0 - val * val





