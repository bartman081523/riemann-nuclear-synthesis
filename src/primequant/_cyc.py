"""primequant._cyc — generischer zyklotomischer Ring Z[x]/(Phi_q(x)) fuer Primzahlen q.

EXAKT (stdlib-only, int-only): Elemente sind int-Tupel (c_0, ..., c_{q-2}) fuer
sum_k c_k omega^k ueber die Basis (1, omega, omega^2, ..., omega^{q-2}) mit
Phi_q(omega) = 0, d.h.

    omega^q = 1   und   omega^{q-1} = -(1 + omega + ... + omega^{q-2}).

Bewusst NICHT der Gruppenring Z[x]/(x^q - 1) (Rang q): nur im echten
zyklotomischen Ring (Rang q-1) ist die DFT-Orthogonalitaet
    sum_k omega^{k(j-l)} = q * delta_{jl}
ring-identisch wahr (Modul-Abschluss, SYNTHESIS §Z.10.3).

Implementations-Grube (im Plan als V4 verifiziert): conj ist KEINE reine
Koeffizienten-Permutation. omega^{-k} = omega^{q-k} legt fuer k >= 2 ein
Basiselement fest, aber omega^{-1} = omega^{q-1} muss ueber Phi_q reduziert
werden — sonst bricht die conj-Involution fuer alle q >= 3.

q = 2 degeneriert auf Rang 1 (Phi_2 = 1 + x, omega = -1): der Ring ist Z,
alle Theoreme bleiben wahr — der saubere Degenerationsfall.

cyc_inv nutzt die Regular Representation: Multiplikation mit a ist eine
(q-1)x(q-1)-int-Matrix; das Inverse loest M x = e1 exakt (Fraction-Gauss).
Nicht-integral loesbare oder singulaere Systeme werden klassifiziert
(NichtInvertierbar), nicht still gerundet.

Garantie: EXAKT (nur int/Fraction auf dem Wertepfad), Herkunft:
exakt-definiert aus der Phi_q-Reduktion. Externe Anker (Goedel-Regel):
(1) Identitaets-Suite in tests/ (DFT-Orthogonalitaet, Parseval, Ramanujan-
formel, Verschiebungs-Kommutation), (2) SymPy-Orakel (optional, nur in
tests/, wird vom Kern nie importiert), (3) Kreuz-Check gegen den
bestehenden q=5-Kern (pt_finite_kernel_check) — vergleichen, nie importieren.
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Sequence, Tuple

from ._gfq import ist_primzahl

Element = Tuple[int, ...]
Matrix = List[List[Element]]


class NichtInvertierbar(Exception):
    """Das Element ist im Ring Z[omega] (oder schon in Q(omega)) nicht invertierbar."""


def _pruefe(q: int, element: Sequence[int]) -> None:
    if not ist_primzahl(q):
        raise ValueError(f"q muss eine Primzahl >= 2 sein, erhalten {q!r}")
    if len(element) != q - 1:
        raise ValueError(
            f"Element-Tupel hat Laenge {len(element)}, erwartet q-1 = {q - 1} (q={q})"
        )
    for c in element:
        if not isinstance(c, int) or isinstance(c, bool):
            raise ValueError(f"Koeffizienten muessen int sein, erhalten {element!r}")


# ---------------------------------------------------------------------------
# Konstruktoren
# ---------------------------------------------------------------------------

def cyc_rang(q: int) -> int:
    """Rang des Rings ueber Z (= q - 1)."""
    if not ist_primzahl(q):
        raise ValueError(f"q muss eine Primzahl >= 2 sein, erhalten {q!r}")
    return q - 1


def cyc_make(q: int, koeffs: Sequence[int]) -> Element:
    ele = tuple(int(c) for c in koeffs)
    _pruefe(q, ele)
    return ele


def cyc_zero(q: int) -> Element:
    return (0,) * (q - 1)


def cyc_one(q: int) -> Element:
    return (1,) + (0,) * (q - 2)


def cyc_omega(q: int, k: int) -> Element:
    """omega^k, kanonisch reduziert (k beliebig ganzzahlig)."""
    if not ist_primzahl(q):
        raise ValueError(f"q muss eine Primzahl >= 2 sein, erhalten {q!r}")
    k = k % q
    ele = [0] * (q - 1)
    if k == q - 1:
        # omega^{q-1} = -(1 + omega + ... + omega^{q-2})  [Phi_q-Reduktion]
        return (-1,) * (q - 1)
    ele[k] = 1
    return tuple(ele)


def cyc_from_int(wert: int, q: int) -> Element:
    if not ist_primzahl(q):
        raise ValueError(f"q muss eine Primzahl >= 2 sein, erhalten {q!r}")
    return (int(wert),) + (0,) * (q - 2)


# ---------------------------------------------------------------------------
# Ring-Arithmetik
# ---------------------------------------------------------------------------

def cyc_add(a: Element, b: Element) -> Element:
    if len(a) != len(b):
        raise ValueError("Elemente unterschiedlichen Rangs")
    return tuple(x + y for x, y in zip(a, b))


def cyc_neg(a: Element) -> Element:
    return tuple(-c for c in a)


def cyc_sub(a: Element, b: Element) -> Element:
    return cyc_add(a, cyc_neg(b))


def cyc_eq(a: Element, b: Element) -> bool:
    return len(a) == len(b) and all(x == y for x, y in zip(a, b))


def cyc_mul(a: Element, b: Element, q: int) -> Element:
    """O(q^2) int-ops: Faltung (Grade 0..2q-4), dann EIN Abwaerts-Reduce:
    omega^d = omega^{d-q} fuer d >= q; omega^{q-1} = -sum_{k<q-1} omega^k.
    Keine Kaskade: d-q <= q-4 < q-1 bleibt unter der Reduce-Front."""
    _pruefe(q, a)
    _pruefe(q, b)
    r = q - 1
    prod = [0] * (2 * r - 1)
    for i, ci in enumerate(a):
        if ci:
            for j, cj in enumerate(b):
                if cj:
                    prod[i + j] += ci * cj
    for d in range(2 * r - 2, r - 1, -1):
        c = prod[d]
        if c:
            prod[d] = 0
            if d == q - 1:
                for k in range(r):
                    prod[k] -= c
            else:
                prod[d - q] += c
    return tuple(prod[:r])


def cyc_pow(a: Element, k: int, q: int) -> Element:
    """Binaere Potenz, EXAKT; k < 0 ueber cyc_inv."""
    if k < 0:
        return cyc_pow(cyc_inv(a, q), -k, q)
    erg = cyc_one(q)
    basis = tuple(a)
    _pruefe(q, basis)
    while k:
        if k & 1:
            erg = cyc_mul(erg, basis, q)
        if k > 1:
            basis = cyc_mul(basis, basis, q)
        k >>= 1
    return erg


def cyc_conj(a: Element, q: int) -> Element:
    """conj(c_0 + sum_{k>=1} c_k omega^k) = c_0 + sum_{k>=1} c_k omega^{-k}
    mit omega^{-k} = omega^{q-k}: fuer k >= 2 ein Basiselement (Index q-k),
    fuer k = 1 die Phi_q-Reduktion omega^{-1} = -(1 + ... + omega^{q-2})."""
    _pruefe(q, a)
    r = q - 1
    out = [0] * r
    out[0] = a[0]
    if r >= 2:
        c1 = a[1]
        if c1:
            for j in range(r):
                out[j] -= c1
        for k in range(2, r):
            c = a[k]
            if c:
                out[q - k] += c
    return tuple(out)


def cyc_inv(a: Element, q: int) -> Element:
    """Inverses in Z[omega]: Regular Representation M (Spalte j = coeffs(a*omega^j)),
    Loese M x = e1 exakt (Fraction-Gauss). Singulaer -> NichtInvertierbar
    (auch ueber Q nicht invertierbar); nicht-integral -> NichtInvertierbar
    (in Q(omega) invertierbar, nicht in Z[omega]) mit rationaler Loese im Text.
    Abschluss: exakter Roundtrip a * inv == 1."""
    _pruefe(q, a)
    r = q - 1
    m: List[List[Fraction]] = []
    for zeile in range(r):
        m.append([Fraction(0)] * r)
    for spalte in range(r):
        sp = cyc_mul(a, cyc_omega(q, spalte), q)
        for zeile in range(r):
            m[zeile][spalte] = Fraction(sp[zeile])

    # Gauss mit Teilpivot; rechts e1
    rechts = [Fraction(1) if i == 0 else Fraction(0) for i in range(r)]
    for spalte in range(r):
        pivot = None
        for zeile in range(spalte, r):
            if m[zeile][spalte] != 0:
                pivot = zeile
                break
        if pivot is None:
            raise NichtInvertierbar(
                f"Element ist auch ueber Q nicht invertierbar (Regular-"
                f"Matrix singulaer): a={a!r}, q={q}"
            )
        if pivot != spalte:
            m[spalte], m[pivot] = m[pivot], m[spalte]
            rechts[spalte], rechts[pivot] = rechts[pivot], rechts[spalte]
        inv_p = m[spalte][spalte]
        for sp2 in range(r):
            m[spalte][sp2] /= inv_p
        rechts[spalte] /= inv_p
        for zeile in range(r):
            if zeile == spalte:
                continue
            fak = m[zeile][spalte]
            if fak == 0:
                continue
            for sp2 in range(r):
                m[zeile][sp2] -= fak * m[spalte][sp2]
            rechts[zeile] -= fak * rechts[spalte]

    for x in rechts:
        if x.denominator != 1:
            raise NichtInvertierbar(
                f"Element ist in Q(omega) invertierbar, aber nicht in Z[omega]: "
                f"Inverses {tuple(rechts)!r} nicht-ganzzahlig (a={a!r}, q={q})"
            )
    inv = tuple(int(x) for x in rechts)
    if not cyc_eq(cyc_mul(inv, tuple(a), q), cyc_one(q)):
        raise RuntimeError("cyc_inv Roundtrip fehlgeschlagen (interner Fehler)")
    return inv


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def cyc_to_json(a: Element) -> list:
    return list(a)


def cyc_from_json(q: int, daten: Sequence[int]) -> Element:
    if not ist_primzahl(q):
        raise ValueError(f"q muss eine Primzahl >= 2 sein, erhalten {q!r}")
    if not isinstance(daten, (list, tuple)) or len(daten) != q - 1:
        raise ValueError(
            f"JSON-Element braucht {q - 1} int-Koeffizienten (q={q}), "
            f"erhalten {daten!r}"
        )
    for c in daten:
        if not isinstance(c, int) or isinstance(c, bool):
            raise ValueError(f"JSON-Koeffizienten muessen int sein: {daten!r}")
    return tuple(daten)


# ---------------------------------------------------------------------------
# Matrixschicht (Eintraege = Ring-Elemente; z. B. X/Verschiebung und Z/diag)
# ---------------------------------------------------------------------------

def cyc_mat_id(q: int, n: int) -> Matrix:
    if n < 1:
        raise ValueError(f"Matrixdimension n >= 1 erwartet, erhalten {n!r}")
    eins = cyc_one(q)
    return [[eins if i == j else cyc_zero(q) for j in range(n)] for i in range(n)]


def cyc_mat_mul(A: Matrix, B: Matrix, q: int) -> Matrix:
    if not A or not B or len(A[0]) != len(B):
        raise ValueError("Matrixformen unvertraeglich")
    n, m, p = len(A), len(B), len(B[0])
    for reihe in A:
        if len(reihe) != m:
            raise ValueError("Matrixformen unvertraeglich (A)")
    for reihe in B:
        if len(reihe) != p:
            raise ValueError("Matrixformen unvertraeglich (B)")
    out: Matrix = []
    for i in range(n):
        zeile: List[Element] = []
        for j in range(p):
            s = cyc_zero(q)
            for k in range(m):
                term = cyc_mul(A[i][k], B[k][j], q)
                s = cyc_add(s, term)
            zeile.append(s)
        out.append(zeile)
    return out


def cyc_mat_adj(A: Matrix, q: int) -> Matrix:
    """Adjungierte = Transposition + konjugierte Eintraege (Element-Konjunktion)."""
    n = len(A)
    if n == 0:
        raise ValueError("leere Matrix")
    m = len(A[0])
    for reihe in A:
        if len(reihe) != m:
            raise ValueError("unebene Zeilenlaengen")
    return [[cyc_conj(A[j][i], q) for j in range(n)] for i in range(m)]


def cyc_mat_scalar_mul(c: Element, A: Matrix) -> Matrix:
    return [[cyc_mul(c, eintrag, len(eintrag) + 1) for eintrag in reihe] for reihe in A]


def cyc_mat_pow(A: Matrix, k: int, q: int) -> Matrix:
    """Binaere Matrix-Potenz; k >= 0."""
    if k < 0:
        raise ValueError("cyc_mat_pow nur fuer k >= 0")
    n = len(A)
    erg = cyc_mat_id(q, n)
    basis = [list(reihe) for reihe in A]
    while k:
        if k & 1:
            erg = cyc_mat_mul(erg, basis, q)
        if k > 1:
            basis = cyc_mat_mul(basis, basis, q)
        k >>= 1
    return erg


def cyc_mat_eq(A: Matrix, B: Matrix) -> bool:
    if len(A) != len(B):
        return False
    for reihe_a, reihe_b in zip(A, B):
        if len(reihe_a) != len(reihe_b):
            return False
        for x, y in zip(reihe_a, reihe_b):
            if not cyc_eq(x, y):
                return False
    return True