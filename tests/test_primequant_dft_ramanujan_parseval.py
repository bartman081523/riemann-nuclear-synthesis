"""
Anker-Tests: Ring-DFT, Parseval (041-Theorem) und Ramanujan-Summen —
exakt im generischen zyklotomischen Ring Z[x]/(Phi_q(x)), q in {2,3,5,7,11}.

Angehoben an die gefrorene 055b-Form:
  - Parseval-Vollform:  Sum_j conj(Ch_hat_j) * Ch_hat_j = q * Sum_l N_l^2
    (Ch_hat_j = Sum_l N_l omega^{jl}) — links im Ring ausgewertet, rechts
    reine Integer-Arithmetik.
  - Nicht-DC-Quote / Float-Faltform: Sum_{j=1}^{q-1} conj(Ch_hat_j)*Ch_hat_j =
    q*Sum N_l^2 - m^2  mit m = DC-Bin (= Sum N_l). Die exakte Quote
    (q*Sum N_l^2 - m^2)/(d*m) tritt im 055b-Pfad als geschlossene Float-
    Form auf (gemessen 2026-10-06: Delta = 0.0 bit-identisch).
  - Konstante q-Klasse: Ch_hat_j = 0 (Ring-Null) fuer alle j != 0 — die
    exakte Form des Negative-Control-Notes (uniform/composite) im Prereg.
  - ABSOLUT-Querschnitt: ein ABGELEITET-Pfad (komplexe float-Summe, nur im
    TEST, nicht im Modul) trifft die exakte Integer-Groesse bis 2 ULP.

Ramanujan-Summe (Primzahl q): c_q(n) = q-1 falls q | n sonst -1 — im Ring
als Sum_{j=1}^{q-1} omega^{jn} ausgewertet (alle j teilerfremd zu q fuer
Primzahl q); das Ergebnis ist ein reines Integer-Element.
"""
import math
import os
import sys

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

try:
    import primequant as pq
except ImportError:  # editable install fehlt: src-Fallback
    sys.path.insert(0, os.path.join(_REPO, "src"))
    import primequant as pq

try:
    import numpy as _np  # ABGELEITET-Kreuzpruefung im Test (Float-Schatten)
except ImportError:
    _np = None

PRIMES = (2, 3, 5, 7, 11)


def ring_dft(N, q):
    """Ch_hat_j = Sum_l N_l * omega^{jl} im Ring (EXAKT), j = 0..q-1."""
    out = []
    for j in range(q):
        s = pq.cyc_zero(q)
        for l, nl in enumerate(N):
            if nl:
                s = pq.cyc_add(s, pq.cyc_mul(pq.cyc_from_int(nl, q),
                                             pq.cyc_omega(q, j * l % q), q))
        out.append(s)
    return out


def integer_wert(elem):
    """Ring-Element mit nur konstantem Term -> int; sonst (None, rest)."""
    if any(k != 0 for k in elem[1:]):
        return None, elem
    return elem[0], None


@pytest.mark.parametrize("q", PRIMES)
def test_dft_orthogonalitaet_exakt(q):
    omega = pq.cyc_omega(q, 1)
    for j in range(q):
        for l in range(q):
            s = pq.cyc_zero(q)
            for k in range(q):
                term = pq.cyc_mul(pq.cyc_pow(omega, k * j, q),
                                  pq.cyc_conj(pq.cyc_pow(omega, k * l, q), q), q)
                s = pq.cyc_add(s, term)
            soll = pq.cyc_from_int(q if j == l else 0, q)
            assert pq.cyc_eq(s, soll), (q, j, l, s)


@pytest.mark.parametrize("q", PRIMES)
def test_parseval_ring_exakt(q):
    """Sum_j conj(Ch_hat_j)*Ch_hat_j == q * Sum_l N_l^2 — voll (inkl. DC-Bin).

    Integrität ist eine SUMMEN-Aussage: die einzelnen Bin-Größen
    conj(Ĉ_j)·Ĉ_j leben im total-reellen Realteilkörper und sind für q >= 3
    generell NICHT ganzzahlig (gemessen z. B. q=5, N=1..5, Bin 1 =
    10 - 5*omega^2 - 5*omega^3); erst die Summe über j kippt nach Q/Z."""
    basis = (3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5)
    N_muster = [list(range(1, q + 1)), basis[:q], [0] * q, [7] * q]
    for N in N_muster:
        Ch = ring_dft(N, q)
        links = pq.cyc_zero(q)
        for C in Ch:
            links = pq.cyc_add(links, pq.cyc_mul(pq.cyc_conj(C, q), C, q))
        val, rest = integer_wert(links)
        assert val is not None, (q, N, rest)
        rechts = q * sum(n * n for n in N)
        assert val == rechts, (q, N, val, rechts)


@pytest.mark.parametrize("q", PRIMES)
def test_quote_nicht_dc_faltform_exakt(q):
    """Sum_{j=1}^{q-1} conj(Ch)*Ch == q*Sum N^2 - m^2 (Float-Faltform-Anker)."""
    basis = (3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5)
    N_muster = [
        basis[:q],
        [2 * n + 1 for n in basis[:q]],
        [7] * q,
        [0] + list(basis[: q - 1]),
    ]
    for N in N_muster:
        Ch = ring_dft(N, q)
        m = sum(N)
        nicht_dc = pq.cyc_zero(q)
        for C in Ch[1:]:
            nicht_dc = pq.cyc_add(nicht_dc, pq.cyc_mul(pq.cyc_conj(C, q), C, q))
        val, rest = integer_wert(nicht_dc)
        assert val is not None, (q, N, rest)
        assert val == q * sum(n * n for n in N) - m * m, (q, N, val)


@pytest.mark.parametrize("q", PRIMES)
def test_konstante_q_klasse_dc_only(q):
    """Negative-Control-Anker (uniform): konstante Verteilung -> Ring-Null
    auf allen Nicht-DC-Frequenzen."""
    N = [3] * q
    Ch = ring_dft(N, q)
    assert pq.cyc_eq(Ch[0], pq.cyc_from_int(3 * q, q)), q
    for j in range(1, q):
        assert pq.cyc_eq(Ch[j], pq.cyc_zero(q)), (q, j, Ch[j])


@pytest.mark.parametrize("q", PRIMES)
def test_ramanujan_formel_exakt(q):
    """c_q(n) = Sum_{j, gcd(j,q)=1} omega^{jn} = q-1 falls q|n sonst -1."""
    for n in range(0, 3 * q + 1):
        s = pq.cyc_zero(q)
        for j in range(1, q + 1):
            if math.gcd(j, q) == 1:
                s = pq.cyc_add(s, pq.cyc_pow(pq.cyc_omega(q, 1), j * n, q))
        soll = q - 1 if n % q == 0 else -1
        assert pq.cyc_eq(s, pq.cyc_from_int(soll, q)), (q, n, s)


@pytest.mark.skipif(_np is None, reason="numpy fehlt (ABGELEITET-Kreuzpruefung)")
def test_absolut_float_schatten_2_ulp():
    """ABGELEITET-Kreuzpruefung im Test (nie Quelle): komplexe Float-Summe
    trifft die exakte Integer-Groesse bis 2 ULP — synthetischer Fall
    d = q^2 (Klassen auf q Residuen gefaltet, q = 2 -> d = 4),
    Spiegel des 055b-t3-Ankers."""
    q = 2
    N_voll = (7, 11, 5, 3)  # d = q*q = 4 Klassen
    m = sum(N_voll)
    d = len(N_voll)
    # Faltung auf q Residuen-Klassen (exakt, hier von Hand)
    gefaltet = [sum(N_voll[l] for l in range(d) if l % q == r) for r in range(q)]
    # EXAKT: Ring-DFT + nicht-DC Parseval
    Ch = ring_dft(gefaltet, q)
    nicht_dc = pq.cyc_zero(q)
    for C in Ch[1:]:
        nicht_dc = pq.cyc_add(nicht_dc, pq.cyc_mul(pq.cyc_conj(C, q), C, q))
    exakt, rest = integer_wert(nicht_dc)
    assert exakt is not None
    assert exakt == q * sum(n * n for n in gefaltet) - m * m

    # ABGELEITET: komplexe Float-Summe omega = exp(2 pi i / q); Float-Quote
    # gegen die exakte Quote der geschlossenen Faltform
    w = complex(math.cos(2 * math.pi / q), math.sin(2 * math.pi / q))
    schatz = 0.0
    for j in range(1, q):
        C = sum(float(n) * w ** (j * l) for l, n in enumerate(gefaltet))
        schatz += abs(C) ** 2
    assert abs(float(exakt) - schatz) <= 2 * math.ulp(float(exakt)), (exakt, schatz)
    quote_exakt = (q * sum(n * n for n in gefaltet) - m * m) / (d * m)
    schatz_quote = schatz / (d * m)
    assert abs(quote_exakt - schatz_quote) <= 2 * math.ulp(quote_exakt), (
        quote_exakt, schatz_quote)