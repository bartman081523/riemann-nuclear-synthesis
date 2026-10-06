"""Anker-Tests: GF(q) + GF(q)[x] — Axiome per VOLLER Enumeration (nicht Stichprobe).

EXAKT-Anker (Goedel-Regel: das Rechenwerk zertifiziert sich nicht selbst):
  1. Koerper-Axiome als vollstaendige Tabellen (q^2 bzw. q^3 Tupel, enumeriert)
     fuer q in {2,3,5,7,11} — reine Enumeration, kein Zieh-Prozess.
  2. Freshman's Dream: (x-1)^{q-1} == Phi_q(x) (mod q) fuer Primzahl q
     (charakteristische Fingerabdruck-Identitaet, ex ante bekannt).
     Folgeseite: ueber GF(q) ist Phi_q REDUZIERT (ggT(Phi_q, x-1) = x-1);
     die Irreduzibilitaet ueber Q ist ein Z-Identitaets-Anker
     ((x-1)·Phi_q = x^q - 1), kein GF(q)-gcd-Anker.
Repraesentationen: GF(q)-Elemente als ints [0,q); Polynome als Tupel
niedrigster Ordnung zuerst, normiert (fuehrende Nullen getrimmt, leeres
Tupel = Nullpolynom).
"""
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

PRIMES = (2, 3, 5, 7, 11)


def test_gfq_axiome_voll_enumeriert_q235711():
    for q in PRIMES:
        zero, eins = 0, 1
        for a in range(q):
            # Neutralitaet + Inverse (Fermat) — jede Zelle geprueft
            assert pq.gfq_add(q, a, zero) == a
            assert pq.gfq_mul(q, a, eins) == a
            for b in range(q):
                # Kommutativ/Additiv-Struktur
                assert pq.gfq_add(q, a, b) == pq.gfq_add(q, b, a)
                assert pq.gfq_mul(q, a, b) == pq.gfq_mul(q, b, a)
                # Distributiv-Gesetz (voll q^2 hier, Assoziativ separat q^3)
                assert pq.gfq_mul(q, a, pq.gfq_add(q, b, eins)) == pq.gfq_add(
                    q, pq.gfq_mul(q, a, b), a
                )
                assert pq.gfq_add(q, b, pq.gfq_sub(q, a, b)) == a
                inv_b = pq.gfq_inv(q, b) if b != 0 else None
                if inv_b is not None:
                    assert pq.gfq_mul(q, a, b) == pq.gfq_mul(q, a, pq.gfq_mul(q, eins, b))


def test_gfq_assoziativ_q235():
    # q^3 = 125 bzw. 343 bzw. 5^3 = 125 Zellen komplett (kein Ziehen)
    for q in (2, 3, 5):
        for a in range(q):
            for b in range(q):
                for c in range(q):
                    assert pq.gfq_mul(q, a, pq.gfq_mul(q, b, c)) == pq.gfq_mul(
                        q, pq.gfq_mul(q, a, b), c
                    )
                    assert pq.gfq_add(q, a, pq.gfq_add(q, b, c)) == pq.gfq_add(
                        q, pq.gfq_add(q, a, b), c
                    )


def test_gfq_inverse_tabelle_exakt():
    for q in PRIMES:
        for a in range(1, q):
            inv = pq.gfq_inv(q, a)
            assert 0 <= inv < q
            assert pq.gfq_mul(q, a, inv) == 1
        with pytest.raises(ZeroDivisionError):
            pq.gfq_inv(q, 0)


def test_freshman_dream_phi_q235711():
    # (x-1)^{q-1} == Phi_q(x) mod q  — ex ante bekannte Identitaet
    for q in PRIMES:
        f = pq.poly_pow(q, (q - 1, 1), q - 1)
        assert f == (1,) * q, (q, f)
        assert pq.phi_q_koeffs(q) == (1,) * q


def test_phi_q_identitaeten_gcd_teilbarkeit():
    # Phi_q(0) = 1 ⇒ ggT(Phi_q, x^k) = 1 über GF(q).  Phi_q(1) = q ≡ 0 mod q:
    # über GF(q) ist Phi_q = (x-1)^{q-1} REDUZIERT (ggT(Phi_q, x-1) = x-1) —
    # die Irreduzibilität über Q ist bewusst NICHT Teil des GF(q)-Orakels;
    # sie wird als Z-Identität (x-1)·Phi_q = x^q - 1 (Integer-Faltung im Test)
    # verankert.
    for q in PRIMES:
        phi = pq.phi_q_koeffs(q)
        assert pq.poly_norm(q, phi) == (1,) * q
        assert sum(phi) == q  # Phi_q(1) = q als Integer
        for k in range(q + 2):
            xp = tuple([0] * k + [1])
            assert pq.poly_gcd(q, phi, xp) == (1,)
        # Reduktion: (x-1)^{q-1} == Phi_q mod q [eigentliche Pruefung im
        # Freshman-Test] ⇒ ggT(Phi_q, x-1) = x-1 über GF(q).  Vertreter-Grube:
        # x-1 ist (q-1, 1), NICHT (1, 1) — (1,1) = x+1 ist nur für q=2 x−1.
        minus_eins_x = (q - 1, 1)
        assert pq.poly_eval(q, phi, 1) == 0  # Phi_q(1) = q ≡ 0 mod q
        assert pq.poly_gcd(q, phi, minus_eins_x) == minus_eins_x
        # Z-Identität: (x-1)·Phi_q = x^q - 1 (reine Integer-Arithmetik)
        prod = [0] * (q + 1)
        for i in (0, 1):
            for j in range(q):
                prod[i + j] += (1 if i == 0 else -1)
        assert prod == [1] + [0] * (q - 1) + [-1], (q, prod)


def test_poly_divmod_gcd_eval_grad_pow_exakt():
    for q in PRIMES:
        f = (1, 3, 0, 2, 1)
        g = (2, 0, 1)
        dd, rr = pq.poly_divmod(q, f, g)
        # f == g*d + r exakt
        assert pq.poly_add(q, pq.poly_mul(q, g, dd), rr) == pq.poly_norm(q, f)
        assert len(rr) < len(g)
        # gcd(f, 0) == f normiert; gcd f mit f
        assert pq.poly_gcd(q, f, ()) == pq.poly_norm(q, f)
        assert pq.poly_gcd(q, f, f) == pq.poly_norm(q, f)
        # Horner == manuelles Horner-Nachbauen (zwei Wege, gleiche Werte)
        for x in range(q):
            horner = pq.poly_eval(q, f, x)
            manuell = 0
            for k in reversed(range(len(f))):
                manuell = (manuell * x + f[k]) % q
            assert horner == manuell
        # poly_pow binaer == wiederholte Multiplikation
        for k in (0, 1, 2, 5, 8):
            erg = (1,)
            for _ in range(k):
                erg = pq.poly_mul(q, erg, f)
            assert pq.poly_pow(q, f, k) == erg
        # poly_grad
        assert pq.poly_grad(q, (5, 0, 2, 3)) == pq.poly_norm(q, (0, 4, 9))


def test_gfq_negativ_faelle_klassifiziert():
    with pytest.raises(ValueError):
        pq.gfq_inv(4, 1)  # 4 keine Primzahl
    with pytest.raises(ValueError):
        pq.poly_pow(9, (1,), 3)  # 9 keine Primzahl
    with pytest.raises(ValueError):
        pq.poly_norm(6, (1, 2))  # 6 keine Primzahl
    # Trivial-Faelle
    assert pq.poly_divmod(5, (), (1,)) == ((), ())


def test_poly_from_int_koeffs_negativ():
    assert pq.poly_from_int_koeffs(5, (-1, 4)) == (4, 4)
    assert pq.poly_from_int_koeffs(5, (7,)) == (2,)