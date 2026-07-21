"""
EXPERIMENT 026 - GF(5) Polynom-Ring und DFT (Phase 1 von 3)

Theoretische Fundierung der Ququint-Architektur (Pillar 4). Baut auf
pt_ququint_vqe.py auf, das nur Restklassen-Arithmetik hatte. Hier
implementieren wir:

  - GF5: endlicher Koerper mit 5 Elementen (echte Field-Axiome)
  - Poly: Polynom-Ring GF(5)[x] mit Addition, Multiplikation, Evaluation
  - dft/idft: Diskrete Fourier-Transformation auf Z/5Z

Diese Strukturen sind die Grundlage fuer:
  - Phase 2: pt_ququint_simulator.py (n-dimensionale unitäre Matrizen)
  - Phase 3: pt_ququint_empirical.py (Schmidt-Entropie 2-Qubit vs 1-Ququint)
"""
import math

import numpy as np


# === GF(5) FIELD ELEMENT ===

class GF5:
    """Element des endlichen Koerpers GF(5) = {0, 1, 2, 3, 4}.

    Repräsentiert eine ganze Zahl modulo 5. Addition und Multiplikation
    sind die modularen Operationen.
    """

    __slots__ = ("_value",)

    def __init__(self, value):
        if not isinstance(value, int):
            raise TypeError(f"GF5 requires int, got {type(value).__name__}")
        if value < 0 or value > 4:
            raise ValueError(f"GF5 element must be in {{0,1,2,3,4}}, got {value}")
        self._value = value

    @property
    def value(self):
        return self._value

    def __int__(self):
        return self._value

    def __index__(self):
        return self._value

    def __eq__(self, other):
        if not isinstance(other, GF5):
            return NotImplemented
        return self._value == other._value

    def __hash__(self):
        return hash(self._value)

    def __lt__(self, other):
        if not isinstance(other, GF5):
            return NotImplemented
        return self._value < other._value

    def __le__(self, other):
        if not isinstance(other, GF5):
            return NotImplemented
        return self._value <= other._value

    def __gt__(self, other):
        if not isinstance(other, GF5):
            return NotImplemented
        return self._value > other._value

    def __ge__(self, other):
        if not isinstance(other, GF5):
            return NotImplemented
        return self._value >= other._value

    def __add__(self, other):
        if not isinstance(other, GF5):
            return NotImplemented
        return GF5((self._value + other._value) % 5)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if not isinstance(other, GF5):
            return NotImplemented
        return GF5((self._value - other._value) % 5)

    def __rsub__(self, other):
        return GF5((other - self._value) % 5) if isinstance(other, int) else NotImplemented

    def __neg__(self):
        return GF5((-self._value) % 5)

    def __mul__(self, other):
        if not isinstance(other, GF5):
            return NotImplemented
        return GF5((self._value * other._value) % 5)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __pow__(self, exp):
        if not isinstance(exp, int):
            raise TypeError("Exponent must be int")
        if exp < 0:
            return self.inverse() ** (-exp)
        result = GF5(1)
        for _ in range(exp):
            result = result * self
        return result

    def inverse(self):
        """Multiplikatives Inverses a^{-1} in GF(5)."""
        if self._value == 0:
            raise ZeroDivisionError("0 has no multiplicative inverse in GF(5)")
        for b in range(1, 5):
            if (self._value * b) % 5 == 1:
                return GF5(b)
        raise ValueError(f"No inverse found for {self._value} in GF(5) — should be impossible")

    def __repr__(self):
        return f"GF5({self._value})"

    def __str__(self):
        return str(self._value)


# === POLYNOMIAL RING GF(5)[x] ===

class Poly:
    """Polynom in GF(5)[x] als Liste von GF5-Koeffizienten.

    Repraesentation: [a_0, a_1, ..., a_n] steht fuer a_0 + a_1*x + ... + a_n*x^n.
    Fuehrende Nullen werden automatisch entfernt. Das Nullpolynom hat Grad -1.
    """

    __slots__ = ("_coeffs",)

    def __init__(self, coeffs):
        """coeffs: iterable of ints (will be converted to GF5)."""
        if not hasattr(coeffs, '__iter__'):
            raise TypeError("coeffs must be iterable")
        gf5_coeffs = []
        for c in coeffs:
            if isinstance(c, GF5):
                gf5_coeffs.append(c)
            elif isinstance(c, int):
                gf5_coeffs.append(GF5(c))
            else:
                raise TypeError(f"Polynomial coefficients must be int or GF5, got {type(c).__name__}")
        # Strip leading zeros
        while len(gf5_coeffs) > 1 and gf5_coeffs[-1] == GF5(0):
            gf5_coeffs.pop()
        # Empty list represents zero polynomial
        self._coeffs = gf5_coeffs

    @property
    def coeffs(self):
        return list(self._coeffs)

    def degree(self):
        """Grad des Polynoms (-1 fuer das Nullpolynom)."""
        if not self._coeffs:
            return -1
        return len(self._coeffs) - 1

    def is_zero(self):
        return not self._coeffs

    def __eq__(self, other):
        if not isinstance(other, Poly):
            return NotImplemented
        return self._coeffs == other._coeffs

    def __hash__(self):
        return hash(tuple(self._coeffs))

    def __add__(self, other):
        if not isinstance(other, Poly):
            return NotImplemented
        n = max(len(self._coeffs), len(other._coeffs))
        result = []
        for i in range(n):
            a = self._coeffs[i] if i < len(self._coeffs) else GF5(0)
            b = other._coeffs[i] if i < len(other._coeffs) else GF5(0)
            result.append(a + b)
        return Poly([int(c) for c in result])

    def __sub__(self, other):
        if not isinstance(other, Poly):
            return NotImplemented
        n = max(len(self._coeffs), len(other._coeffs))
        result = []
        for i in range(n):
            a = self._coeffs[i] if i < len(self._coeffs) else GF5(0)
            b = other._coeffs[i] if i < len(other._coeffs) else GF5(0)
            result.append(a - b)
        return Poly([int(c) for c in result])

    def __neg__(self):
        return Poly([int(-c) for c in self._coeffs])

    def __mul__(self, other):
        if not isinstance(other, Poly):
            return NotImplemented
        if not self._coeffs or not other._coeffs:
            return Poly([])
        n_self = len(self._coeffs)
        n_other = len(other._coeffs)
        result = [GF5(0)] * (n_self + n_other - 1)
        for i, a in enumerate(self._coeffs):
            for j, b in enumerate(other._coeffs):
                result[i + j] = result[i + j] + a * b
        return Poly([int(c) for c in result])

    def __rmul__(self, other):
        return self.__mul__(other)

    def scale(self, c):
        """Skaliere das Polynom um c (GF5-Element)."""
        if isinstance(c, int):
            c = GF5(c)
        if not isinstance(c, GF5):
            return NotImplemented
        return Poly([int(c * a) for a in self._coeffs])

    def evaluate(self, x):
        """Werte das Polynom an der Stelle x in GF(5) aus."""
        if isinstance(x, int):
            x = GF5(x)
        if not isinstance(x, GF5):
            return NotImplemented
        if not self._coeffs:
            return GF5(0)
        result = self._coeffs[-1]
        for i in range(len(self._coeffs) - 2, -1, -1):
            result = result * x + self._coeffs[i]
        return result

    def __repr__(self):
        if not self._coeffs:
            return "Poly(0)"
        terms = []
        for i, c in enumerate(self._coeffs):
            if c == GF5(0):
                continue
            if i == 0:
                terms.append(f"{int(c)}")
            elif i == 1:
                if c == GF5(1):
                    terms.append("x")
                else:
                    terms.append(f"{int(c)}*x")
            else:
                if c == GF5(1):
                    terms.append(f"x^{i}")
                else:
                    terms.append(f"{int(c)}*x^{i}")
        return "Poly(" + " + ".join(terms) + ")" if terms else "Poly(0)"

    def __str__(self):
        return self.__repr__()


# === DISCRETE FOURIER TRANSFORM ON Z/5Z ===

def dft(x):
    """Diskrete Fourier-Transformation auf Z/5Z.

    F_k = sum_{j=0}^{4} x_j * omega^{j*k}
    wobei omega = exp(2*pi*i/5) eine primitive 5. Einheitswurzel ist.

    Args:
        x: numpy array der Laenge 5 (oder Liste)

    Returns:
        numpy array der Laenge 5 (komplex)
    """
    x = np.asarray(x, dtype=complex)
    if x.shape != (5,):
        raise ValueError(f"DFT input must have shape (5,), got {x.shape}")
    n = 5
    omega = np.exp(2j * np.pi / n)
    result = np.zeros(n, dtype=complex)
    for k in range(n):
        for j in range(n):
            result[k] += x[j] * omega ** (j * k)
    return result


def idft(X):
    """Inverse DFT auf Z/5Z.

    x_j = (1/5) * sum_{k=0}^{4} X_k * omega^{-j*k}

    Args:
        X: numpy array der Laenge 5 (komplex)

    Returns:
        numpy array der Laenge 5 (komplex)
    """
    X = np.asarray(X, dtype=complex)
    if X.shape != (5,):
        raise ValueError(f"iDFT input must have shape (5,), got {X.shape}")
    n = 5
    omega = np.exp(2j * np.pi / n)
    result = np.zeros(n, dtype=complex)
    for j in range(n):
        for k in range(n):
            result[j] += X[k] * omega ** (-j * k)
    return result / n