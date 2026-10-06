"""Exakte statistische Bänder — Integer-Term-Walk ohne Float-Rundung.

EXAKT-Schicht: nur int/Fraction auf dem Wertepfad, keine Zufallsquelle, kein
numpy/scipy (scipy bleibt ABGELEITET-Kreuzcheck in tests/, nie Kern).

Der CDF-Walk haelt die gemeinsame Nenner-Potenz den**S konstant und fuehrt
NUR die Numinator-Ints fort (kein Fraction-gcd pro Schritt — das war die
27-s-Grube der Vorab-Rechnung; der Integer-Walk lief in 0.056 s bei S = 8192,
p = 1/2 — Pflicht):

    n_j = C(S, j) * num^j * (den - num)^(S - j)      (ganzzahlig, exakt)
    n_{j+1} = n_j * (S - j) * num // ((j + 1) * (den - num))

Die Teilbarkeit ist ALGEBRAISCH garantiert (C(S,j)*j = C(S,j-1)*(S-j+1));
der divmod-Rest wird als Beweis-Zeuge geprueft (r != 0 -> ValueError,
tritt nie auf). Fraction(num, den) muss reduziert vorliegen — dann ist
ggT(num, den - num) = 1 automatisch (ggT(num, den) = 1).

Grenzfuelle p in {0, 1} entarten exakt (Delta-Verteilung). Alle Schwell-
Vergleiche laufen in Fractions, niemals in Floats.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Tuple


def _binomial_zweig(p: object) -> Tuple[int, int]:
    """Reduced (num, den) einer Wahrscheinlichkeit in [0, 1]."""
    frac = Fraction(p)
    if frac < Fraction(0) or frac > Fraction(1):
        raise ValueError(f"Wahrscheinlichkeit ausserhalb [0,1]: {frac}")
    return frac.numerator, frac.denominator


def binom_cdf_exakt(
    k: int, S: int, p: object
) -> Fraction:
    """P(X <= k) fuer X ~ Binomial(S, p) — EXAKT via Integer-Term-Walk.

    Gemeinsamer Nenner den**S; der Walk ueber die Numinator-Ints ist ein
    exakter Term-Summe-Pfad (keine Rundung). k ausserhalb [0, S] entartet:
    k < 0 -> 0, k >= S -> 1 (exakte Randsaetze, keine Konvention).
    """
    k = int(k)
    S = int(S)
    if S < 0:
        raise ValueError(f"S muss >= 0 sein, erhalten {S}")
    if k < 0:
        return Fraction(0)
    if k >= S:
        return Fraction(1)
    num, den = _binomial_zweig(p)
    if num == 0:
        return Fraction(1)            # X identisch 0
    if num == den:
        return Fraction(0)            # X identisch S
    n = (den - num) ** S              # Term k = 0
    summe = n
    for j in range(1, k + 1):
        n = n * (S - j + 1) * num
        divisor = j * (den - num)
        quotient, rest = divmod(n, divisor)
        if rest != 0:
            raise ValueError(
                f"Term-Walk Teilbarkeit verletzt bei j={j} — "
                "Term ist nicht ganz; Formel oder p falsch"
            )
        n = quotient
        summe += n
    return Fraction(summe, den ** S)


def binom_tail_exakt(
    k: int, S: int, p: object
) -> Fraction:
    """P(X >= k) EXAKT (Spiegelung: Binomial(S, 1-p) bis S-k)."""
    k = int(k)
    if k <= 0:
        return Fraction(1)
    if k > S:
        return Fraction(0)
    p_mirror = Fraction(p)
    mirrored = 1 - p_mirror
    return binom_cdf_exakt(S - k, S, mirrored)


def p_wert_zweiseitig(
    beobachtet: int, S: int, p: object
) -> Fraction:
    """Zweiseitiger exakter p-Wert: min(1, 2 * min(P(X<=k), P(X>=k))).

    Registrierte Konvention (Doppel-Schwanz, inklusive Grenzterme). Das
    Ergebnis ist die Band-Entscheidung: <= alpha/bonferroni heisst
    AUSSERHALB des Bandausschnitts.
    """
    beobachtet = int(beobachtet)
    links = binom_cdf_exakt(beobachtet, S, p)
    rechts = binom_tail_exakt(beobachtet, S, p)
    kleiner = links if links <= rechts else rechts
    wert = 2 * kleiner
    return wert if wert < 1 else Fraction(1)


def alpha_bonferroni(alpha: object, anzahl: int) -> Fraction:
    """Bonferroni-Aufteilung alpha/anzahl exakt (simultane Familie)."""
    if anzahl <= 0:
        raise ValueError(f"anzahl muss >= 1 sein, erhalten {anzahl}")
    wert = Fraction(alpha)
    if wert <= 0 or wert > 1:
        raise ValueError(f"alpha ausserhalb (0, 1]: {wert}")
    return wert / anzahl


def band_quantile(
    p: object, S: int, alpha: object, bonferroni: int = 1
) -> Tuple[int, int]:
    """Exakte zweiseitige Band-Grenzen (untere, obere) in Anzahl-Skala.

    untere = max {k : P(X <= k) <= a2}, obere = min {j : P(X >= j) <= a2}
    mit a2 = alpha/(bonferroni*2). Die CDF ist monoton, also ist
    {k : F(k) <= a2} ein Praefix — der Walk bricht an der ersten
    Verletzung ab; die obere Kante laeuft ueber dieselbe Walk-Funktion
    auf dem gespiegelten Erfolgswert 1-p (kein zweiter Algorithmus).

    Rueckgabe: (k_lo, k_hi); k_lo = -1 heisst "F(0) > a2" (keine linke
    Kante — nur bei riesigem alpha), k_hi = S + 1 analog rechts.
    Interpretation: count k liegt AUSSEN <=> k <= k_lo oder k >= k_hi.

    Vergleiche laufen ganzzahlig (summe * a2_nenner <= a2_zaehler *
    nenner) — KEINE Fraction-Reduktion pro Schritt (das war die 27-s-
    Grube: gcd auf ~10^4-stelligen Zwischensummen je Schritt).
    """
    bonferroni = int(bonferroni)
    if bonferroni < 1:
        raise ValueError(f"bonferroni muss >= 1 sein, erhalten {bonferroni}")
    wert = Fraction(alpha)
    if wert <= 0 or wert > 1:
        raise ValueError(f"alpha ausserhalb (0, 1]: {wert}")
    a2 = wert / bonferroni / 2
    num, den = _binomial_zweig(p)
    S = int(S)
    if S < 0:
        raise ValueError(f"S muss >= 0 sein, erhalten {S}")
    nenner = den ** S
    a2_zaehler, a2_nenner = a2.numerator, a2.denominator

    def _kante_unten(num_par: int) -> int:
        """max k mit F(k) <= a2 — Walk im gemeinsamen Nenner nenner."""
        n = (den - num_par) ** S             # Term k = 0
        summe = n
        if summe * a2_nenner > a2_zaehler * nenner:
            return -1                        # F(0) > a2 -> leere Kante
        kanten_k = 0
        j = 1
        while j <= S:
            n = n * (S - j + 1) * num_par
            divisor = j * (den - num_par)
            quotient, rest = divmod(n, divisor)
            if rest != 0:
                raise ValueError("Term-Walk Teilbarkeit verletzt")
            n = quotient
            summe += n
            if summe * a2_nenner > a2_zaehler * nenner:
                break                        # F(j) > a2 — Kante gefunden
            kanten_k = j
            j += 1
        return kanten_k

    k_lo = _kante_unten(num)
    k_mirror = _kante_unten(den - num)
    return k_lo, S - k_mirror


def chebyshev_schranke(
    abstand: object, S: int, p: object
) -> Fraction:
    """EXAKTE obere Schranke P(|X - S*p| >= abstand) <= S*p*(1-p)/d^2.

    Ohne Walk, ohne Verteilungs-Form — die Chebyshev-Ungleichung ist eine
    Identitaet am Erwartungswert. abstand <= 0 entartet zu Schranke 1
    (trivial, aber registriert, keine Ausnahme).
    """
    abstand = Fraction(abstand)
    frac = Fraction(p)
    varianz = Fraction(S) * frac * (1 - frac)
    if abstand <= 0:
        return Fraction(1)
    schranke = varianz / (abstand * abstand)
    return schranke if schranke < 1 else Fraction(1)


def cantelli_schranke(
    abstand: object, S: int, p: object
) -> Fraction:
    """EXAKTE einseitige Schranke P(X - S*p >= abstand) <= V/(V + d^2).

    Cantelli (eine Schwanz-Seite) — dieselbe exakte Varianz-Quelle wie
    Chebyshev; abstand <= 0 entartet zu Schranke 1.
    """
    abstand = Fraction(abstand)
    frac = Fraction(p)
    varianz = Fraction(S) * frac * (1 - frac)
    if abstand <= 0:
        return Fraction(1)
    return varianz / (varianz + abstand * abstand)