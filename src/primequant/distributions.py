"""Exakte Verteilungen pro Reihen-Art + exakte Total-Variation (TV).

EXAKT-Schicht: nur int/Fraction auf dem Wertepfad, keine Zufallsquelle, kein
numpy. Jede Reihen-Art der RAM-Q/FP48-Familie traegt eine ex ante
DEKLARIERTE Wahrscheinlichkeitsverteilung auf dem Messregister
(label-int == Index, Identitaet-Bitordnung):

* structure / kalibrier_structure: n_a/m auf den Labels 0..d-1 (die
  Vorbereitungs-Struktur |psi(P,d)>), Labels >= d tragen 0.
* loschmidt / kalibrier_loschmidt / echo_ladder / readout_cal: Delta auf dem
  Label 0^nq (Prep + inverses Prep = Identitaet; die 45 committeten
  Muss-Reihen der SV-Ebene sind exakt gesaettigt — TV == 0).
* negative_control (composite): n_d/m aus dem committeten Prereg (044-t4),
  Labels 0..d-1.
* negative_control (uniform): 1/q auf Labels 0..q-1 — die "Konstante
  q-Klasse"-Lesart des 041-Notes (DFT_q verschwindet an allen Nicht-DC-
  Bins). Explizit NICHT die Register-Uniformverteilung 1/2^nq: gegen die
  vier committeten Kontrollreihen scheitert diese (TV 0.25..0.375).

TV-Konvention (bit-exakt an den vier committeten 055b-Kontrollreihen
gepinnt; TV = (1/(2*S)) * sum_a |c_a - S*p_a|, S = Counts-Summe, Masse
jenseits des Modells geht voll in die TV):
    composite_q3 = 551/86016   = 0.0064057850
    uniform_q3   =  79/24576   = 0.0032145182
    composite_q5 = 835/106496  = 0.0078406701
    uniform_q5   =  31/2560    = 0.0121093750

Alle Rueckgaben tragen Arithmetik-Klasse EXAKT (int/Fraction, herkunft
"exakt-definiert"); die Deklaration der Klassen verlangt nichts hier,
weil die Arithmetik konstruktionsbedingt ganzrational bleibt.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from .stateprep import exakter_probvektor, ideal_leiter_delta, ideal_loschmidt_delta

STRUKTUR_REIHENARTEN: Tuple[str, str] = ("structure", "kalibrier_structure")
DELTA_REIHENARTEN: Tuple[str, str, str, str] = (
    "loschmidt", "kalibrier_loschmidt", "echo_ladder", "readout_cal",
)


def fuele_modell(
    modell: Sequence[Fraction], breite: int
) -> List[Fraction]:
    """Modell-Vektor auf Register-Breite auffuellen (Masse 0 auf neuen Labels).

    Identitaet-Bitordnung: Modell-Index == Label-int. Fuellung ist eine
    Verlaengerung mit exakt 0 — kein Gewichts-Verteilen, keine Zufallsquelle.
    """
    if breite < len(modell):
        raise ValueError(
            f"Modelllaenge {len(modell)} ueber Registerbreite {breite}"
        )
    return [Fraction(p) for p in modell] + [Fraction(0)] * (breite - len(modell))


def modell_struktur(
    n_d: Sequence[int], m: Optional[int] = None
) -> List[Fraction]:
    """Exakter Prep-Probvektor: p_a = n_a/m exakt (Wurzel nie ausgewertet)."""
    return exakter_probvektor(n_d, m)


def modell_kontrolle_uniform(q: int) -> List[Fraction]:
    """Uniforme Kontrolle auf Klassen-Ebene: p_a = 1/q, a = 0..q-1.

    Die Klasse "Konstante q-Klasse" des 041-Notes: DFT_q verschwindet an
    allen Nicht-DC-Bins — die Kontrolle muss in der Quote NICHT aufsteigen.
    """
    if q < 2:
        raise ValueError(f"q muss >= 2 sein, erhalten {q}")
    return [Fraction(1, q)] * q


def modell_kontrolle_composite(
    n_d: Sequence[int], m: Optional[int] = None
) -> List[Fraction]:
    """Composite-Kontrolle: deklarierte n_d/m aus dem committeten Prereg.

    Die Kontrolle soll die Prime-Band-Kante NICHT verletzen — ihr Modell
    ist die Prep-Struktur selbst (044-t4: n_d = [19,13,10] fuer P=181,d=3
    bzw. [23,18,17,15,18] fuer P=467,d=5, m aus dem committeten Bytes).
    """
    if m is None:
        m = sum(int(v) for v in n_d)
    if sum(int(v) for v in n_d) != m:
        raise ValueError(
            f"deklarierter Count-Vektor widerspricht m: sum{n_d} != {m}"
        )
    return [Fraction(int(v), m) for v in n_d]


def modell_fuer_art(
    art: str,
    nq: int,
    n_d: Optional[Sequence[int]] = None,
    m: Optional[int] = None,
    q: Optional[int] = None,
) -> List[Fraction]:
    """Dispatcher Reihen-Art -> deklariertes Modell auf vollem Register.

    negative_control: mit n_d -> Composite-Struktur; ohne n_d -> Q-uniforme
    Klasse (dann ist q Pflichtargument).
    """
    breite = 1 << int(nq)
    if art in STRUKTUR_REIHENARTEN:
        if n_d is None or int(m) <= 0:
            raise ValueError(
                f"art {art}: n_d/m Pflichtargumente (deklarierte Prep-Struktur)"
            )
        return fuele_modell(modell_struktur(n_d, int(m)), breite)
    if art in DELTA_REIHENARTEN:
        if art == "echo_ladder":
            return list(ideal_leiter_delta(int(nq)))
        return list(ideal_loschmidt_delta(int(nq)))
    if art == "negative_control":
        if n_d is None:
            if q is None:
                raise ValueError(
                    "negative_control (uniform) verlangt q (Klassen-Ebene 1/q)"
                )
            return fuele_modell(modell_kontrolle_uniform(int(q)), breite)
        return fuele_modell(modell_kontrolle_composite(n_d, m), breite)
    raise ValueError(
        f"unbekannte Reihen-Art {art!r}; zulaessig: STRUKTUR ({', '.join(STRUKTUR_REIHENARTEN)}) "
        f"DELTA ({', '.join(DELTA_REIHENARTEN)}) negative_control"
    )


def zaehlung_auf_labels(
    counts: Dict[str, int], breite: int
) -> List[int]:
    """Counts-Dict -> voller Label-Vektor (label = int(bits, 2), exakt).

    Spiegel der gefrorenen Label-Parse-Kette (bits.replace(" ",""), 2);
    Labels jenseits der Breite werden verweigert, negative Massen ebenfalls.
    """
    if breite <= 0:
        raise ValueError(f"breite muss >= 1 sein, erhalten {breite}")
    vektor = [0] * breite
    for bits, masse in counts.items():
        label = int(bits.replace(" ", ""), 2)
        if not 0 <= label < breite:
            raise ValueError(
                f"label {bits!r} ({label}) ausserhalb 0..{breite - 1}"
            )
        if int(masse) != masse:
            raise ValueError(f"Count-Masse {masse!r} ist nicht ganz")
        if masse < 0:
            raise ValueError(f"negatives Count-Masse {masse} bei label {label}")
        vektor[label] += int(masse)
    return vektor


def exakte_masse_am_label(counts: Dict[str, int], label: int) -> int:
    """Beobachtete Masse EXAKT am Label (Label-Int, Identitaet-Bitordnung)."""
    if label < 0:
        raise ValueError(f"label muss >= 0 sein, erhalten {label}")
    gesamt = 0
    for bits, masse in counts.items():
        if int(bits.replace(" ", ""), 2) == label:
            gesamt += int(masse)
    return gesamt


def tv_exakt(
    counts: Dict[str, int],
    modell: Sequence[Fraction],
    breite: Optional[int] = None,
) -> Fraction:
    """Total-Variation-Abstand EXAKT: TV = (1/(2*S)) * sum_a |c_a - S*p_a|.

    p_a = Modellmasse am Label a (Identitaet-Bitordnung), S = Counts-Summe.
    Masse jenseits der Modelllaenge fuehrt mit Modellmasse 0 voll in die
    TV. Anker-Pins (bit-exakt, aus den vier committeten 055b-Kontrollreihen):
    composite_q3 551/86016, uniform_q3 79/24576, composite_q5 835/106496,
    uniform_q5 31/2560 (siehe Modul-Docstring).
    """
    modell_vektor = [Fraction(p) for p in modell]
    modell_summe = sum(modell_vektor)
    if modell_summe != 1:
        raise ValueError(
            f"Modell-Summe {modell_summe} != 1 — kein exakter Probvektor"
        )
    S = sum(int(masse) for masse in counts.values())
    if S <= 0:
        raise ValueError(f"Counts-Summe muss >= 1 sein, erhalten {S}")
    max_label = -1
    massen: Dict[int, int] = {}
    for bits, masse in counts.items():
        if int(masse) != masse:
            raise ValueError(f"Count-Masse {masse!r} ist nicht ganz")
        if masse < 0:
            raise ValueError(f"negatives Count-Masse {masse} bei label {bits}")
        label = int(bits.replace(" ", ""), 2)
        max_label = max(max_label, label)
        massen[label] = massen.get(label, 0) + int(masse)
    if breite is None:
        breite = max(len(modell_vektor), max_label + 1)
    if max_label >= breite:
        raise ValueError(
            f"label {max_label} ausserhalb Register-Breite {breite}"
        )
    if len(modell_vektor) > breite:
        raise ValueError(
            f"Modelllaenge {len(modell_vektor)} ueber Register-Breite {breite}"
        )
    numerator = Fraction(0)
    for a in range(breite):
        masse = massen.get(a, 0)
        p = modell_vektor[a] if a < len(modell_vektor) else Fraction(0)
        abstand = abs(Fraction(masse) - Fraction(S) * p)
        numerator += abstand
    return numerator / (2 * S)