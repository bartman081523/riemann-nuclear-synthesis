"""Zustandsvorbereitung exakt — Sieb, Restklassen, exakte Probvektoren.

EXAKT-Schicht: nur int/Fraction auf dem Wertepfad; keine Wurf-Quelle, kein
numpy. Die drei Pflichtbausteine der RAM-Q/FP48-Familie werden hier
NEU implementiert (dritter audierbarer Codepfad neben dem q=5-Kern
``pt_finite_kernel_check`` und der GF5-Klasse ``pt_ququint_gf5``) — Kreuz-
Checks gegen die Bestandsmodule laufen NUR in tests/, niemals hierher.

Inhalt:
* ``sieve_primes``      — Eratosthenes-Sieb exakt (Primzahlen p mit 2 <= p <= N).
* ``residue_counts``    — n_r = #{p <= P : p ~ r (mod d)} fuer r = 0..d-1.
* ``exakter_probvektor``— |psi(P,d)> = sum_a sqrt(n_a/m)|a>: Amplitudenquadrat
                          n_a/m als Fraction; die Wurzel wird NIE ausgewertet.
* ``ideal_loschmidt_delta`` / ``ideal_leiter_delta`` — Prep -> Prep^-1 = Identitaet
                          heisst Delta auf dem Label 0^nq (ex ante gesaettigt).
* Quote/Parseval-Arithmetik ueber den gefalteten Vektor:
  ``observables.quote_exakt`` — hier liegt nur die Vorbereitungs-Arithmetik.
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Optional, Sequence, Tuple


def sieve_primes(N: int) -> List[int]:
    """Eratosthenes-Sieb: alle Primzahlen p mit 2 <= p <= N, aufsteigend.

    Deterministisch, keine Zufallsquelle. Kleine N (N < 2) -> leere Liste.
    """
    if N < 2:
        return []
    ist_prim = [True] * (N + 1)
    ist_prim[0] = False
    ist_prim[1] = False
    p = 2
    while p * p <= N:
        if ist_prim[p]:
            for vielfach in range(p * p, N + 1, p):
                ist_prim[vielfach] = False
        p += 1
    return [q for q in range(2, N + 1) if ist_prim[q]]


def residue_counts(P: int, d: int) -> List[int]:
    """n_r = #{p <= P : p ~ r (mod d)} fuer r = 0..d-1 (exakte Zaehlung).

    Invarianten: sum_a n_a == pi(P); n_0-Zaehlung ist das 1-Atom (nur die
    Primzahl d selbst liegt auf Klasse 0, fuer d Primzahl — die FP48-Register
    tragen d in {q, q^2, q^3} mit q Primzahl, dort ist Klasse 0 gleichfalls
    das 1-Atom).
    """
    if d <= 0:
        raise ValueError(f"d muss >= 1 sein, erhalten {d}")
    zaehlung = [0] * d
    for p in sieve_primes(P):
        zaehlung[p % d] += 1
    return zaehlung


def exakter_probvektor(n_d: Sequence[int], m: Optional[int] = None) -> List[Fraction]:
    """Exakter Probvektor des Zustands |psi(P,d)> auf den d Register-Labels.

    |amp_a|^2 = n_a/m als Fraction — die Wurzel wird NIE ausgewertet, das
    Amplitudenquadrat ist die registrierte Groesse. Mit m=pi(P) ist der
    Vektor normiert: sum_a n_a/m == 1 exakt.
    """
    if m is None:
        m = sum(n_d)
    if m <= 0:
        raise ValueError(f"Norm m muss >= 1 sein, erhalten {m}")
    if sum(n_d) != m:
        raise ValueError(
            f"Count-Vektor widerspricht m: sum{n_d} = {sum(n_d)} != {m}"
        )
    return [Fraction(int(w), m) for w in n_d]


def labels_2nq(nq: int) -> List[str]:
    """Bitstrings "0"-"1" der 2^nq Messlabels in Count-Map-Reihenfolge."""
    if nq <= 0:
        raise ValueError(f"nq muss >= 1 sein, erhalten {nq}")
    breite = 1 << nq
    return [format(idx, "0%db" % nq) for idx in range(breite)]


def delta_vektor(nq: int, label: int = 0) -> List[Fraction]:
    """Delta-Probvektor auf dem Label (Voreinstellung 0 = alle Qubits |0>)."""
    breite = 1 << nq
    if not 0 <= label < breite:
        raise ValueError(f"label {label} ausserhalb 0..{breite - 1}")
    vek = [Fraction(0)] * breite
    vek[label] = Fraction(1)
    return vek


def ideal_loschmidt_delta(nq: int) -> List[Fraction]:
    """IDEAL-Loschmidt-Ausgang: Prep gefolgt von Prep^-1 ist die Identitaet,
    also Delta auf 0^nq — ex ante gesaettigt, TV gegen gezogene Counts == 0,
    sobald der Count-Vektor selbst auf 0^nq saettigt."""
    return delta_vektor(nq, 0)


def ideal_leiter_delta(nq: int) -> List[Fraction]:
    """IDEAL-Nachbarleiter (echo ladder): gleiche Identitaet-Struktur wie der
    Loschmidt-Arm — Delta auf 0^nq, ex ante gesaettigt."""
    return delta_vektor(nq, 0)


def falt_auf_q(vektor: Sequence[int], d: int, q: int) -> List[int]:
    """Falte den d-Labels-Vektor auf die q Residuenklassen mod q.

    Faltet NUR ueber die ersten d Labels (Register-Bin-Rang; Labels >= d
    gehoeren laut Vorbereitung zu keiner Klasse — der Anker-Test auf Struktur-
    Reihen verifiziert leichte Masse ausserhalb d getrennt). Bei d == q ist
    das Falten die Identitaet (Shuffle-Inertness des gefrorenen Kerns).
    """
    if d <= 0 or q <= 0:
        raise ValueError(f"d/q muessen >= 1 sein, erhalten d={d}, q={q}")
    if len(vektor) < d:
        raise ValueError(
            f"Vektor laenger {len(vektor)} < Registerbreite d={d}"
        )
    gefaltet = [0] * q
    for a in range(d):
        gefaltet[a % q] += int(vektor[a])
    return gefaltet


def register_breite(d: int) -> Tuple[int, int]:
    """(nq, 2^nq) zum Register d — kleinste Potenz von zwei >= d."""
    nq = 0
    breite = 1
    while breite < d:
        breite *= 2
        nq += 1
    return nq, breite