"""GF(q) und der Polynomring GF(q)[x] fuer Primzahlen q — EXAKT (int-only, stdlib).

Körper-Arithmetik generell über alle Primzahlen q; kein Träger wird bevorzugt
oder hartkodiert. Elemente von GF(q) sind ints in [0, q). Polynome sind
Tupel von Koeffizienten niedrigster Ordnung zuerst (coefficient[0] = A(0)).

Externer Anker (Gödel-Regel): die Körperaxiome werden als volle Tabellen
(q^2 bzw. q^3 Tupel, enumeriert — kein Zieh-Meister) gegen die Identitaet
(x - 1)^{q-1} == Phi_q(x)  (mod q)  geprueft, und gegen die Korselt-/Carmichael-
Verwendung der pt_hshor1-Schicht, die die Inversibilitaet von GF(q) nutzt.
"""

from __future__ import annotations

from typing import Sequence, Tuple


def ist_primzahl(q: int) -> bool:
    if not isinstance(q, int) or isinstance(q, bool) or q < 2:
        return False
    if q == 2:
        return True
    d = 2
    while d * d <= q:
        if q % d == 0:
            return False
        d += 1
    return True


def _pruefe_prim(q: int) -> None:
    if not ist_primzahl(q):
        raise ValueError(f"q muss eine Primzahl >= 2 sein, erhalten {q!r}")


# ---------------------------------------------------------------------------
# Koerper GF(q)
# ---------------------------------------------------------------------------

def gfq_norm(q: int, a: int) -> int:
    """Repraesentation eines Koerperelements (int in [0,q))."""
    _pruefe_prim(q)
    return a % q


def gfq_add(q: int, a: int, b: int) -> int:
    return (a + b) % q


def gfq_sub(q: int, a: int, b: int) -> int:
    return (a - b) % q


def gfq_mul(q: int, a: int, b: int) -> int:
    return (a * b) % q


def gfq_inv(q: int, a: int) -> int:
    """Multiplikatives Inverses in GF(q) via kleinem Fermat (EXAKT)."""
    _pruefe_prim(q)
    a = a % q
    if a == 0:
        raise ZeroDivisionError("0 ist in GF(q) nicht invertierbar")
    return pow(a, q - 2, q)


def gfq_div(q: int, a: int, b: int) -> int:
    return (a % q) * gfq_inv(q, b) % q


# ---------------------------------------------------------------------------
# Polynomring GF(q)[x]; Tupel niedrigster Ordnung zuerst
# ---------------------------------------------------------------------------

def poly_norm(q: int, f: Sequence[int]) -> Tuple[int, ...]:
    """Normiert: Koeffizienten mod q, fuehrende Nullen getrimmt (0-Polynom = ())."""
    _pruefe_prim(q)
    k = list(int(c) % q for c in f)
    while k and k[-1] == 0:
        k.pop()
    return tuple(k)


def poly_add(q: int, f: Sequence[int], g: Sequence[int]) -> Tuple[int, ...]:
    la, lb = len(f), len(g)
    n = max(la, lb)
    return poly_norm(q, tuple((f[i] if i < la else 0) + (g[i] if i < lb else 0) for i in range(n)))


def poly_sub(q: int, f: Sequence[int], g: Sequence[int]) -> Tuple[int, ...]:
    la, lb = len(f), len(g)
    n = max(la, lb)
    return poly_norm(q, tuple((f[i] if i < la else 0) - (g[i] if i < lb else 0) for i in range(n)))


def poly_mul(q: int, f: Sequence[int], g: Sequence[int]) -> Tuple[int, ...]:
    if not f or not g:
        return ()
    erg = [0] * (len(f) + len(g) - 1)
    for i, fi in enumerate(f):
        if fi == 0:
            continue
        for j, gj in enumerate(g):
            if gj:
                erg[i + j] += fi * gj
    return poly_norm(q, erg)


def poly_pow(q: int, f: Sequence[int], k: int) -> Tuple[int, ...]:
    """Binare Potenz (EXAKT; k >= 0)."""
    if k < 0:
        raise ValueError("poly_pow nur fuer k >= 0 definiert")
    erg: Tuple[int, ...] = (1,)
    basis = poly_norm(q, f)
    while k:
        if k & 1:
            erg = poly_mul(q, erg, basis)
        basis = poly_mul(q, basis, basis)
        k >>= 1
    return erg


def poly_eval(q: int, f: Sequence[int], x: int) -> int:
    """Horner-Schema in GF(q)."""
    erg = 0
    for c in reversed(list(f)):
        erg = (erg * int(x) + int(c)) % q
    return erg % q


def poly_grad(q: int, f: Sequence[int]) -> Tuple[int, ...]:
    if len(f) <= 1:
        return ()
    return poly_norm(q, tuple((i % q) * f[i] for i in range(1, len(f))))


def poly_divmod(q: int, f: Sequence[int], g: Sequence[int]) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    """Euclidische Division in GF(q)[x]: f = d*g + r, deg r < deg g. EXAKT."""
    g = poly_norm(q, g)
    if not g:
        raise ZeroDivisionError("Division durch das Nullpolynom")
    rest = list(poly_norm(q, f))
    grad_g = len(g) - 1
    fuehrend_inv = gfq_inv(q, g[-1])
    grad_f = len(rest) - 1
    d: list = [0] * max(0, grad_f - grad_g + 1)
    while len(rest) - 1 >= grad_g and rest:
        grad_r = len(rest) - 1
        faktor = (rest[-1] * fuehrend_inv) % q
        pos = grad_r - grad_g
        d[pos] = faktor
        for i in range(grad_g + 1):
            rest[pos + i] = (rest[pos + i] - faktor * g[i]) % q
        while rest and rest[-1] == 0:
            rest.pop()
    return poly_norm(q, d), poly_norm(q, rest)


def poly_gcd(q: int, f: Sequence[int], g: Sequence[int]) -> Tuple[int, ...]:
    """Normalisierter Euclid-GCD in GF(q)[x]."""
    f2, g2 = poly_norm(q, f), poly_norm(q, g)
    while g2:
        _, rest = poly_divmod(q, f2, g2)
        f2, g2 = g2, rest
    if not f2:
        return ()
    return poly_norm(q, tuple(c * gfq_inv(q, f2[-1]) for c in f2))


def phi_q_koeffs(q: int) -> Tuple[int, ...]:
    """Phi_q(x) = 1 + x + ... + x^{q-1} fuer Primzahl q (Koeffs. niedrigst zuerst).
    Grad phi(q) = q-1, also genau q Einser-Koeffizienten."""
    _pruefe_prim(q)
    return (1,) * q


def poly_from_int_koeffs(q: int, koeffs: Sequence[int]) -> Tuple[int, ...]:
    """Int-Koeffizienten (auch negativ) -> normiertes GF(q)-Polynom."""
    return poly_norm(q, koeffs)