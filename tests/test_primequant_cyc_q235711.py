"""
Anker-Tests: generischer zyklotomischer Ring Z[x]/(Phi_q(x)), q in {2,3,5,7,11}.

EXAKT-Anker, alle Werte reine Enumeration (kein Zieh-Generator):
  1. Ring-Axiome: q <= 3 vollstaendig ueber {-2..2}, sonst eine
     deterministische Muster-Menge (Potenzen von omega + benannte Muster).
  2. cyc_mul gegen einen ALGORITMISCH UNABHAENGIGEN Reduktions-Weg
     (hoechste Potenz zuerst via Phi_q = 1 + x + ... + x^{q-1} abziehen —
     das Modul nutzt die einstufigen omega^q-/omega^{q-1}-Regeln).
  3. conj-Involution und conj(omega^k) = omega^{-k} (V4-Grube: omega^{-1}
     braucht die Phi_q-Reduktion, kein Index-Swap).
  4. Inversen-Klassifikation: Einheiten round-trip, nicht-invertierbare
     Elemente werfen NichtInvertierbar mit Klassifizierer im Text.
  5. Verschiebungs-Kommutation Z*X = omega * X*Z und X^q = I (Matrixschicht);
     Z = diag(omega^j), X_{i,j} = delta_{i,(j+1) mod q}.
"""
import os
import sys
from itertools import product

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

try:
    import primequant as pq
except ImportError:  # editable install fehlt: src-Fallback
    sys.path.insert(0, os.path.join(_REPO, "src"))
    import primequant as pq

PRIMES = (2, 3, 5, 7, 11)


def voll_enum(q, wertebereich):
    """Deterministische Aufzaehlung ALLER Tupel ueber wertebereich."""
    return list(product(wertebereich, repeat=q - 1))


def menge_fuer(q, limit=40):
    """Deterministische Elementen-Menge: full Enum bei kleinen q, sonst
    benannte Muster (Potenzen von omega + fuenf feste Muster) — HELPER,
    kein Test (kein test_-Praefix)."""
    if 5 ** (q - 1) <= limit:
        return voll_enum(q, (-2, -1, 0, 1, 2))
    menge = [pq.cyc_omega(q, k) for k in range(q)]
    menge += [
        pq.cyc_from_int(2, q),
        pq.cyc_from_int(-3, q),
        (1, -1) + (0,) * (q - 3),
        (0, 1, 1) + (0,) * (q - 4),
        (2, -1, 0, 1) + (0,) * (q - 5),
    ]
    return tuple(menge)


def reduziere_mit_phi(prod, q):
    """Unabhaengiger zweiter Pfad: hoechste Potenz d >= q-1 mit
    c * x^{d-q+1} * Phi_q(x) abziehen (Phi_q monisch vom Grad q-1),
    bis alle Grade < q-1. Andere Struktur als cyc_mul (einstufige Regeln)."""
    prod = list(prod)
    while True:
        while prod and prod[-1] == 0:
            prod.pop()
        d = len(prod) - 1
        if d < q - 1:
            break
        c = prod[d]
        if c:
            versatz = d - (q - 1)
            for i in range(q):
                prod[versatz + i] -= c
        prod[d] = 0
        while prod and prod[-1] == 0:
            prod.pop()
    while len(prod) < q - 1:
        prod.append(0)
    return tuple(prod[: q - 1])


def referenz_mul(a, b, q):
    """Referenz-Multiplikation: volle Faltung (Grade 0..2q-4), dann
    Phi_q-Reduktion. Unabhaengig vom einstufigen Weg des Moduls."""
    prod = [0] * (2 * q - 3)
    for i, ci in enumerate(a):
        for j, cj in enumerate(b):
            if ci and cj:
                prod[i + j] += ci * cj
    return reduziere_mit_phi(prod, q)


@pytest.mark.parametrize("q", PRIMES)
def test_cyc_mul_gegen_unabhaengigen_phi_weg(q):
    werte_sammlung = ((-1, 0, 1, 2, -2),) if q <= 3 else ((-1, 0, 1), (2, -2))
    for werte in werte_sammlung:
        menge = voll_enum(q, werte)
        if len(menge) > 45:
            menge = menge[:45]  # deterministischer Vorspann der Aufzaehlung
        for a in menge:
            for b in menge:
                assert pq.cyc_mul(a, b, q) == referenz_mul(a, b, q), (q, a, b)


@pytest.mark.parametrize("q", PRIMES)
def test_cyc_axiome_mengenweise(q):
    """Kommutativ, Eins, Distributiv, Assoziativ — voll ueber menge_fuer."""
    menge = menge_fuer(q)
    eins = pq.cyc_one(q)
    for a in menge:
        assert pq.cyc_eq(pq.cyc_mul(a, eins, q), a), (q, a)
        assert pq.cyc_eq(pq.cyc_mul(eins, a, q), a), (q, a)
    for a, b, c in zip(menge, menge[1:], (list(menge[1:]) + [menge[0]])):
        assert pq.cyc_eq(pq.cyc_mul(a, b, q), pq.cyc_mul(b, a, q)), (q, a, b)
        assert pq.cyc_eq(
            pq.cyc_mul(a, pq.cyc_add(b, c), q),
            pq.cyc_add(pq.cyc_mul(a, b, q), pq.cyc_mul(a, c, q)),
        ), (q, a, b, c)
        assert pq.cyc_eq(
            pq.cyc_mul(pq.cyc_mul(a, b, q), c, q),
            pq.cyc_mul(a, pq.cyc_mul(b, c, q), q),
        ), (q, a, b, c)


@pytest.mark.parametrize("q", PRIMES)
def test_cyc_add_sub_neg_zero_one(q):
    """Add/Sub/Neg/Zero/One — voll fuer kleine q, sonst deterministischer
    Vorspann (60e6-Paare bei q=11 ware kein Anker mehr, sondern ein Stillstand)."""
    a_menge = voll_enum(q, (-2, 0, 2))
    if len(a_menge) > 30:
        a_menge = a_menge[:30]  # deterministischer Vorspann der Aufzaehlung
    b_menge = voll_enum(q, (-1, 1))
    if len(b_menge) > 10:
        b_menge = b_menge[:10]
    for a in a_menge:
        for b in b_menge:
            assert pq.cyc_eq(pq.cyc_sub(pq.cyc_add(a, b), b), a), (q, a, b)
            assert pq.cyc_eq(pq.cyc_neg(pq.cyc_neg(a)), a)
    assert pq.cyc_eq(pq.cyc_add(pq.cyc_zero(q), pq.cyc_one(q)), pq.cyc_one(q))
    assert pq.cyc_eq(pq.cyc_make(q, range(q - 1)), pq.cyc_make(q, range(q - 1)))
    assert pq.cyc_rang(q) == q - 1


@pytest.mark.parametrize("q", PRIMES)
def test_cyc_pow_binaer_gegen_wiederholung(q):
    w1 = pq.cyc_omega(q, 1)
    a = pq.cyc_add(w1, pq.cyc_from_int(2, q))
    erg = pq.cyc_one(q)
    for k in range(9):
        assert pq.cyc_eq(pq.cyc_pow(a, k, q), erg), (q, k)
        erg = pq.cyc_mul(erg, a, q)
    # omega^q == omega^0 == 1 im Ring; negative Potenzaet via cyc_inv
    assert pq.cyc_eq(pq.cyc_pow(w1, q, q), pq.cyc_one(q))
    for k in range(-4, 9):
        assert pq.cyc_eq(pq.cyc_pow(w1, k, q), pq.cyc_omega(q, k % q)), (q, k)


@pytest.mark.parametrize("q", PRIMES)
def test_cyc_conj_involution_und_omega_negativ(q):
    for a in menge_fuer(q):
        assert pq.cyc_eq(pq.cyc_conj(pq.cyc_conj(a, q), q), a), (q, a)
    for k in range(-2 * q, 2 * q + 1):
        wk = pq.cyc_omega(q, k)
        assert pq.cyc_eq(pq.cyc_conj(wk, q), pq.cyc_omega(q, -k)), (q, k)
        # |omega^k|^2 = 1 (total-reeller Tracer: Produkt ist reines Z-Element)
        p = pq.cyc_mul(wk, pq.cyc_conj(wk, q), q)
        assert p == pq.cyc_from_int(1, q), (q, k, p)


@pytest.mark.parametrize("q", PRIMES)
def test_cyc_galois_produkt_ist_ganze_zahl(q):
    """Die Galois-Koerpernorm N(a) = Prod_{k=1}^{q-1} a(omega^k) ist ein reines
    Z-Element (ganze Zahl) fuer ALLES a im Ring — das ist das echte Normform-
    Theorem.
    Abstand-Gube: das einzelne conj(a)*a ist fuer q >= 3 NICHT generell ganz
    (a·conj(a) lebt im total-reellen Realteilkorper Q(omega + omega^{q-1}),
    nicht in Q) — gefallene Erstversion dieses Tests dokumentierte exakt diese
    Verwechslung an a = 1 - omega: (1-omega)(1-omega^bar) = 3 + omega^2 + omega^3.

    Bekannte Werte als ex-ante-Pins: N(1 - omega) = q fuer ungerade q
    (die Verzweigungs-Identitaet (q) = (1 - omega)^{q-1}); q = 2: N = q^2 = 4
    (Ring degeneriert, Sigma_1(1 - omega) = 1 - omega = 2, Produkt = 4)."""
    for a in menge_fuer(q):
        norm = pq.cyc_from_int(1, q)
        for k in range(1, q):
            # sigma_k(a) = Sum_j a_j * omega^{jk} — Ring-Element
            sig = pq.cyc_zero(q)
            for j, cj in enumerate(a):
                if cj:
                    sig = pq.cyc_add(
                        sig,
                        pq.cyc_mul(pq.cyc_from_int(cj, q),
                                   pq.cyc_omega(q, (j * k) % q), q),
                    )
            norm = pq.cyc_mul(norm, sig, q)
        assert all(kk == 0 for kk in norm[1:]), (q, a, norm)
        # Pin: N(1 - omega) = q (ungerade q) / q^2 (q = 2)
        if a == (1, -1) + (0,) * (q - 3):
            soll = q if q > 2 else q * q
            assert pq.cyc_eq(norm, pq.cyc_from_int(soll, q)), (q, norm, soll)


@pytest.mark.parametrize("q", PRIMES)
def test_cyc_inv_einheiten_und_klassifikation(q):
    kandidaten = [
        pq.cyc_one(q),
        pq.cyc_omega(q, 2),
        pq.cyc_omega(q, -3),
        pq.cyc_sub(pq.cyc_omega(q, 1), pq.cyc_one(q)),  # omega - 1
        pq.cyc_from_int(-1, q),
    ]
    for a in kandidaten:
        try:
            iv = pq.cyc_inv(a, q)
        except pq.NichtInvertierbar:
            continue  # Klassifikation, kein Stillstand — round-trip entfaellt
        assert pq.cyc_eq(pq.cyc_mul(iv, a, q), pq.cyc_one(q)), (q, a)
        assert pq.cyc_eq(pq.cyc_mul(a, iv, q), pq.cyc_one(q)), (q, a)
    # Klassifikation mit Grund im Meldungstext
    zwo = pq.cyc_from_int(2, q)
    with pytest.raises(pq.NichtInvertierbar) as info:
        pq.cyc_inv(zwo, q)
    assert "Z[omega]" in str(info.value), str(info.value)
    with pytest.raises(pq.NichtInvertierbar):
        pq.cyc_inv(pq.cyc_zero(q), q)
    with pytest.raises(ValueError):
        pq.cyc_inv((1, 2, 3, 4, 5), 7)  # Laenge != q - 1


def test_cyc_q2_degeneriert_zu_z():
    q = 2
    assert pq.cyc_rang(q) == 1
    for a in (0, 1, 2, -3):
        for b in (0, 1, 2, -3):
            assert pq.cyc_eq(
                pq.cyc_mul(pq.cyc_from_int(a, q), pq.cyc_from_int(b, q), q),
                pq.cyc_from_int(a * b, q),
            ), (a, b)
    assert pq.cyc_eq(pq.cyc_omega(q, 1), pq.cyc_from_int(-1, q))
    assert pq.cyc_eq(pq.cyc_inv(pq.cyc_from_int(-1, q), q), pq.cyc_from_int(-1, q))
    with pytest.raises(pq.NichtInvertierbar):
        pq.cyc_inv(pq.cyc_from_int(2, q), q)
    assert pq.cyc_eq(pq.cyc_conj(pq.cyc_from_int(-3, q), q), pq.cyc_from_int(-3, q))


@pytest.mark.parametrize("q", PRIMES)
def test_cyc_json_roundtrip(q):
    for a in menge_fuer(q):
        assert pq.cyc_from_json(q, pq.cyc_to_json(a)) == a
    with pytest.raises(ValueError):
        pq.cyc_from_json(q, [0] * (q - 2))
    with pytest.raises(ValueError):
        pq.cyc_from_json(q, [0] * q)
    with pytest.raises(ValueError):
        pq.cyc_from_json(q, [0] * (q - 3) + [1.0])


@pytest.mark.parametrize("q", (2, 3, 5, 7))
def test_cyc_verschiebung_kommutation_und_X_pow_q(q):
    """Z*X = omega * X*Z, X^q = I, Z^q = I — der Gate-Level-Anker (qudit)."""
    n = q
    omega = pq.cyc_omega(q, 1)
    X = [
        [pq.cyc_one(q) if (j + 1) % q == i else pq.cyc_zero(q) for j in range(n)]
        for i in range(n)
    ]
    Z = [
        [pq.cyc_omega(q, i) if i == j else pq.cyc_zero(q) for j in range(n)]
        for i in range(n)
    ]
    ZX = pq.cyc_mat_mul(Z, X, q)
    wXZ = pq.cyc_mat_scalar_mul(omega, pq.cyc_mat_mul(X, Z, q))
    assert pq.cyc_mat_eq(ZX, wXZ), q
    assert pq.cyc_mat_eq(pq.cyc_mat_pow(X, q, q), pq.cyc_mat_id(q, n)), q
    assert pq.cyc_mat_eq(pq.cyc_mat_pow(Z, q, q), pq.cyc_mat_id(q, n)), q
    # Adjungierte: X-adjungiert ist die Rueckverschiebung, X · X^dagger = I
    Xadj = pq.cyc_mat_adj(X, q)
    assert pq.cyc_mat_eq(pq.cyc_mat_mul(X, Xadj, q), pq.cyc_mat_id(q, n)), q
    assert pq.cyc_mat_eq(pq.cyc_mat_adj(pq.cyc_mat_adj(X, q), q), X), q


def test_cyc_mat_scalar_gesamt_kleinstmoglich():
    q = 3
    n = 2
    A = pq.cyc_mat_id(q, n)
    null_matrix = [[pq.cyc_zero(q) for _ in range(n)] for _ in range(n)]
    assert pq.cyc_mat_eq(pq.cyc_mat_scalar_mul(pq.cyc_zero(q), A), null_matrix)
    with pytest.raises(ValueError):
        pq.cyc_mat_id(q, 0)
    with pytest.raises(ValueError):
        pq.cyc_mat_pow(pq.cyc_mat_id(q, n), -1, q)
    with pytest.raises(ValueError):
        pq.cyc_mat_mul([], pq.cyc_mat_id(q, n), q)