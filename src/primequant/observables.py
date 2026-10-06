"""Exakte Observable-Schicht — Punkt-Konstanten, Quote, Ring-DFT, Ramanujan.

EXAKT-Schicht: nur int/Fraction auf dem Wertepfad. Alle Formeln sind der
gespiegelte exakte Stand der gefrorenen Bestandskette (arm_point, fold_mod_q,
share_hw_fft/share_hw_folded/fold_d, ratio_from_counts), die in tests/ gegen
die Bestandsmodule bit-genau verankert wird — niemals Refit, niemals
Zufallsquelle.

Wissenschaftlicher Kern (bewusst als SUMMEN-Aussage, nicht per-Bin):
* Per-Bin-Magnitude |X_hut_j|^2 liegt i.A. im reellen Teilkoerper von Q(w_q)
  und ist NICHT rational (V4-Grube) — die Quote-Arithmetik benutzt deshalb
  die Parseval-Identitaet  sum_{j=1}^{q-1} |X_hut_j|^2 = q*sum N_hut_r^2 - m_hut^2,
  welche im Z[omega_q]-Ring exakt ganzrational ist (041-Theorem-Form).
* Division durch SHOTS = 8192 = 2^13 ist eine Zweierpotenz-Division:
  m*c/S ist exakt im Binaer-Format darstellbar (nur Exponenten-Verschiebung).
* Die Gefalt-Form hat EINE Rundung (ein Divisionsschritt), die exakte
  Fraction hat keine — float(Fraction(num, den)) ist daraus bit-identisch
  zur gefalteten Float-Form (Anker-Test H-055C-4: Delta == 0.0).

Inhalt:
* ``punkt_konstanten``      — exakte Spiegel aller arm_point-Felder.
* ``falte_restklassen``     — Wraparound-Fold des GESAMTEN Register-Vektors
                              (label mod d; Spiegel von fold_d).
* ``falte_q_fraction``      — mod-q-Falt ueber die d Klassen, Fraction-erhaltend.
* ``quote_exakt``           — exakte Quote-Kette aus einem Counts-Dict.
* ``ring_dft`` / ``norm_galois`` / ``ramanujan_summe`` — Ring-Ansichten.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Sequence, Tuple

from . import _cyc
from .stateprep import register_breite, residue_counts, sieve_primes

SHOTS = 8192  # gefrorene Apparatus-Konvention der RAM-Q/FP48-Familie


def falte_restklassen(zaehlung: Sequence[int], d: int) -> List[int]:
    """Wraparound-Fold: Klasse = label mod d, ueber das GESAMTE Register.

    Exakte Spiegel von fold_d (pt_ram_q_hardware_aer, gefroren):
    n_d[a] = sum n_full[a::d]. Anders als falte_auf_q erfasst dies auch
    Masse auf Labels >= d — sie faellt via mod d auf Klasse label mod d
    zurueck (bei d = q die Struktur des Minimalregisters: Label q faellt
    auf Klasse 0, Label q+1 auf Klasse 1, ...).
    """
    if d <= 0:
        raise ValueError(f"d muss >= 1 sein, erhalten {d}")
    ergebnis = [0] * d
    for label, masse in enumerate(zaehlung):
        ergebnis[label % d] += int(masse)
    return ergebnis


def falte_q_fraction(vektor: Sequence[Fraction], d: int, q: int) -> List[Fraction]:
    """mod-q-Falt ueber die ersten d Klassen, Fraction-erhaltend.

    Spiegel von fold_mod_q(n_d, d, q) (arm_point-Kern): N_r = sum n_a fuer
    a ~ r (mod q), a < d. Bei d == q ist die Falt die Identitaet.
    """
    if d <= 0 or q <= 0:
        raise ValueError(f"d/q muessen >= 1 sein, erhalten d={d}, q={q}")
    if len(vektor) < d:
        raise ValueError(
            f"Vektor laenger {len(vektor)} < Registerbreite d={d}"
        )
    gefaltet: List[Fraction] = []
    for r in range(q):
        gesamt = Fraction(0)
        for a in range(r, d, q):
            gesamt += vektor[a]
        gefaltet.append(gesamt)
    return gefaltet


def punkt_konstanten(
    P: int, d: int, q: int, shots: int = SHOTS
) -> Dict[str, object]:
    """Exakte Spiegel aller arm_point-Felder (Kreuz-Check-Anker in tests/).

    Feldnamen folgen der Bestandskonvention, damit die Anker-Tests Feld fuer
    Feld vergleichen koennen (bes. ``q_sum_N_sq_minus_m2`` = num). Die
    geschlossene Form ist fuer q in {3, 5} mit n0 == 1 ALGEBRAISCH identisch
    mit ratio_true — das wird hier als exakte Fraction-Gleichheit ASSERTIERT
    (schaerfer als der gefrorene Float-Guard 1e-12; die Identitaet bricht
    fuer andere q, dort wird nur die Bestands-Naeherung ohne Identitaets-
    Assert rekonstruiert).

    Liefert EXAKTE Groessen:
      n_d (Liste[int]), m (int), N (Liste[int]), n0 (int),
      q_sum_N_sq_minus_m2 = q*sum(N^2) - m^2 (int, num),
      den = (m - q*n0)^2 (int),
      ratio_true (Fraction), L_q (Fraction),
      share_true_reg (Fraction), model_share_reg (Fraction),
      delta/delta_sq (Fraction, q==3) bzw sigma2 (Fraction, q != 3),
      closed_form (Fraction).
    """
    primzahlen = sieve_primes(P)
    m = len(primzahlen)
    if m <= 0:
        raise ValueError(f"keine Primzahlen <= P={P}")
    n_d = residue_counts(P, d)
    if sum(n_d) != m:
        raise ValueError(
            f"Count-Vektor P={P}, d={d}: Summe {sum(n_d)} != m {m}"
        )
    klassen: List[int] = []
    for r in range(q):
        klassen.append(sum(n_d[a] for a in range(r, d, q)))
    n0 = klassen[0]
    quadrat = sum(x * x for x in klassen)
    num = q * quadrat - m * m
    den = (m - q * n0) ** 2
    if den <= 0:
        raise ValueError(
            f"Nennner entartet (m == q*n0) bei P={P}, d={d}, q={q}"
        )
    konstanten: Dict[str, object] = {
        "P": P, "d": d, "q": q, "m": m, "n_d": n_d, "N": klassen, "n0": n0,
        "q_sum_N_sq_minus_m2": num, "den": den,
        "ratio_true": Fraction((q - 1) * num, den),
        "share_true_reg": Fraction(num, d * m),
        "model_share_reg": Fraction(den, (q - 1) * d * m),
        "L_q": Fraction((q - 1) ** 2 * m * m, shots * den),
        # Gefrorene Apparatus-Konvention L_q: SHOTS = 8192 im Bestandsmodul —
        # shots hier default 8192, abweichende Werte nur mit Quelle.
    }
    if n0 != 1:
        raise ValueError(
            f"Klasse-0-Atom erwartet n0 == 1 (d in {{q, q^2, q^3}}, d "
            f"Vielfaches von q): P={P}, d={d}, n0={n0}"
        )
    if q == 3:
        delta = Fraction(klassen[1] - klassen[2], 2)
        closed = Fraction(1) + Fraction(12) * delta * delta \
            * Fraction(1, (m - 3) ** 2)
        konstanten.update({
            "delta": delta,
            "delta_sq": delta * delta,
            "closed_form": closed,
        })
    else:
        sigma2 = (Fraction(num) - Fraction(den, q - 1)) / q
        closed = Fraction(1) + Fraction(20) * sigma2 \
            * Fraction(1, (m - 5) ** 2)
        konstanten.update({
            "sigma2": sigma2,
            "closed_form": closed,
        })
    if q in (3, 5):
        identitaet = closed == konstanten["ratio_true"]
        if not identitaet:
            raise ValueError(
                f"geschlossene Form != ratio_true (exakt) bei P={P}, q={q}"
            )
        konstanten["closed_form_identitaet_exakt"] = True
    else:
        konstanten["closed_form_identitaet_exakt"] = False
    return konstanten


def quote_exakt(
    counts: Dict[str, int],
    konstanten: Dict[str, object],
    shots: int = SHOTS,
) -> Dict[str, object]:
    """Exakte Spiegel der gefrorenen counts-Kette (ratio_from_counts).

    counts = Dict{Bitstring: Count-Zaehlung} (Summe == shots). Kette:
      1. Labels: int(bits, 2) -> n_full (Laenge 2^nq).
      2. Wraparound-Fold auf d Klassen (falte_restklassen = fold_d-Spiegel).
      3. n_hat = m * C / shots als Fraction — EXakt (Zweierpotenz-Nenner).
      4. N_hut = mod-q-Falt der d n_hat-Klassen (fractions).
      5. share = (q * sum N_hut^2 - m_hut^2) / (d * m)  — Parseval-SUMME,
         niemals per-Bin (reelle Teilkoerper-GAP).
      6. quote = share / model_share_reg (Fraction-Division: das float
         model_share_reg ist ein exakt darstellbarer dyadischer Bruch).
    Rueckgabe enthaelt neben den Fraction-Groessen die bit-genauen
    Float-Schatten (anteil_flt_falt = float(anteil_falt) — EINE Rundung,
    bit-identisch zur Bestands-Faltform; nur Diagnostik, nie Quelle).
    """
    P, d, q = konstanten["P"], konstanten["d"], konstanten["q"]
    m = int(konstanten["m"])
    if d % q != 0:
        raise ValueError(
            f"Quote-Identitaet verlangt d Vielfaches von q (Bins j*d/q "
            f"treffen alle Nicht-DC-Klassen): d={d}, q={q}"
        )
    if shots <= 0:
        raise ValueError(f"shots muss >= 1 sein, erhalten {shots}")
    _, breite = register_breite(d)
    n_full = [0] * breite
    for bits, masse in counts.items():
        label = int(bits.replace(" ", ""), 2)
        if not 0 <= label < breite:
            raise ValueError(f"label {label} ausserhalb 0..{breite - 1}")
        n_full[label] += int(masse)
    gesamt = sum(n_full)
    if gesamt != shots:
        raise ValueError(
            f"Counts-Summe {gesamt} != shots {shots}"
        )
    klassen_counts = falte_restklassen(n_full, d)
    n_hut_klassen = [Fraction(m * c, shots) for c in klassen_counts]
    N_hut = falte_q_fraction(n_hut_klassen, d, q)
    m_hut_skaliert = sum(N_hut)                      # == m exakt (t6)
    if m_hut_skaliert != m:
        raise ValueError(
            f"Massenerhaltung verletzt: sum N_hut = {m_hut_skaliert} != m {m}"
        )
    quadrat = sum(w * w for w in N_hut)
    ziffer = q * quadrat - m_hut_skaliert * m_hut_skaliert
    anteil_falt = ziffer / (Fraction(d) * m)
    modell = Fraction(konstanten["model_share_reg"])
    quote = anteil_falt / modell
    return {
        "n_hut_klassen": n_hut_klassen,
        "N_hut": N_hut,
        "m_hat": m_hut_skaliert,
        "q_sum_N_sq_minus_m2": ziffer,
        "anteil_falt": anteil_falt,
        "anteil_modell": modell,
        "quote": quote,
        # Float-Schatten (ABGELEITET-View, nie Quelle):
        "anteil_flt_falt": float(anteil_falt),
        "quote_flt": float(quote),
    }


def ring_dft(vektor: Sequence[int], q: int) -> List[Tuple[int, ...]]:
    """DFT Laenge q IM Ring Z[omega_q] (exakt im Ring, nicht in Q).

    X_hut_j = sum_{a=0}^{q-1} v_a * omega^{-ja}, j = 0..q-1 — Elemente des
    Zyklotomie-Rings (Basistupel 1..omega^{q-2}). Die Richtungsform
    omega^{-ja} folgt der DFT-Hauskonvention des Bestandsmoduls; die
    Exponenten werden in der Ring-Ebene via cyc_omega(q, (-j*a) % q)
    reduziert.
    """
    if any(int(v) != v for v in vektor):
        raise ValueError("ring_dft verlangt einen int-Vektor")
    skaliert = [int(v) for v in vektor]
    ergebnis: List[Tuple[int, ...]] = []
    for j in range(q):
        summe = _cyc.cyc_zero(q)
        for a, v in enumerate(skaliert):
            if v != 0:
                potenz = _cyc.cyc_omega(q, (-j * a) % q)
                summe = _cyc.cyc_add(summe,
                                     _cyc.cyc_mul(_cyc.cyc_from_int(v, q),
                                                  potenz, q))
        ergebnis.append(tuple(summe))
    return ergebnis


def quad_magnitude(element: Tuple[int, ...], q: int) -> Tuple[int, ...]:
    """|X|^2 = X * conj(X) IM Ring — Element der Realteilkoerpers.

    WICHTIG: dieses Produkt ist i.A. KEINE rationale Groesse (reeller
    Teilkoerper, V4-Grube) — fuer rationale Aussagen nur die Galois-Norm
    norm_galois oder Parseval-SUMMEN ueber j benutzen.
    """
    return tuple(_cyc.cyc_mul(element, _cyc.cyc_conj(element, q), q))


def galois_konjugiert(
    element: Tuple[int, ...], q: int, k: int
) -> Tuple[int, ...]:
    """Automorphismus sigma_k: omega^a ↦ omega^{ak}, angewandt auf Element.

    Die Substitution ist NICHT die Ring-Multiplikation mit omega^k (das
    verschiebt Exponenten, a ↦ a + k) — sigma_k ersetzt die Potenz
    omega^a durch omega^{ak}. In Koeffizienten-Sicht: sigma_k(e) =
    sum_a v_a * omega^{a*k mod q}. Fuer k mit q | k ist sigma die
    Identitaet-Reduktion des Rings; k in 1..q-1 sind die echten
    Automorphismen.
    """
    wert = _cyc.cyc_zero(q)
    for a, v in enumerate(element):
        if v:
            potenz = _cyc.cyc_omega(q, (a * k) % q)
            wert = _cyc.cyc_add(wert,
                                _cyc.cyc_mul(_cyc.cyc_from_int(v, q), potenz, q))
    return tuple(wert)


def norm_galois(element: Tuple[int, ...], q: int) -> Fraction:
    """Galois-Norm N(X) = Produkt ueber alle Konjugierten (exakt ganzrational).

    N(sigma_k(X)) = N(X) fuer alle k — das Produkt ist unter ALLEN
    Automorphismen fixiert -> Element von Q -> als reduziertes Ring-Element
    konstanter Koeffizient. Als Fraction rueckgegeben. Anker-Pin:
    N(1 - omega) = q fuer jede Primzahl q.
    """
    if q < 2:
        raise ValueError(f"q muss >= 2 sein, erhalten {q}")
    produkt = _cyc.cyc_from_int(1, q)
    for k in range(1, q):
        produkt = _cyc.cyc_mul(produkt, galois_konjugiert(element, q, k), q)
    if any(x != 0 for x in produkt[1:]):
        raise ValueError(
            f"Galois-Norm ergab kein rationales Element: Basis {produkt}"
        )
    return Fraction(produkt[0])


def ramanujan_summe(q: int, n: int) -> int:
    """c_q(n) = q-1 falls q | n sonst -1 (Primzahl-q-Form, 034-Konvention).

    Herleitung: c_q(n) = sum_{k=1}^{q-1} omega^{kn} = (sum_{k=0}^{q-1}
    omega^{kn}) - 1 = (q falls q|n sonst 0) - 1. Ring-Anker in tests/.
    """
    if q <= 1:
        raise ValueError(f"q muss Primzahl >= 2 sein, erhalten {q}")
    return q - 1 if n % q == 0 else -1