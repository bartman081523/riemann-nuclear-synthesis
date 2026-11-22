"""Tests für von_mangoldt_exact und von_mangoldt_residue_counts in primequant.stateprep."""

from __future__ import annotations

import math
import pytest
from primequant import von_mangoldt_exact, von_mangoldt_residue_counts


def test_von_mangoldt_exact_small_integers():
    """Prüft von_mangoldt_exact an bekannten Basiszahlen."""
    # n <= 1 -> (0, 0)
    assert von_mangoldt_exact(0) == (0, 0)
    assert von_mangoldt_exact(1) == (0, 0)

    # Primzahlen -> (p, 1)
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
    for p in primes:
        assert von_mangoldt_exact(p) == (p, 1)

    # Primzahlpotenzen p^k -> (p, k)
    assert von_mangoldt_exact(4) == (2, 2)
    assert von_mangoldt_exact(8) == (2, 3)
    assert von_mangoldt_exact(16) == (2, 4)
    assert von_mangoldt_exact(9) == (3, 2)
    assert von_mangoldt_exact(27) == (3, 3)
    assert von_mangoldt_exact(25) == (5, 2)
    assert von_mangoldt_exact(49) == (7, 2)

    # Zusammengesetzte Zahlen mit >= 2 verschiedenen Primteilern -> (0, 0)
    composites = [6, 10, 12, 14, 15, 18, 20, 21, 22, 24, 26, 28, 30]
    for c in composites:
        assert von_mangoldt_exact(c) == (0, 0)


def test_von_mangoldt_residue_counts():
    """Prüft die Zählung von Primzahlpotenzen in Restklassen mod q."""
    # X = 10, q = 3
    # Primzahlpotenzen <= 10:
    # 2 (mod 3 = 2)
    # 3 (mod 3 = 0)
    # 4 = 2^2 (mod 3 = 1)
    # 5 (mod 3 = 2)
    # 7 (mod 3 = 1)
    # 8 = 2^3 (mod 3 = 2)
    # 9 = 3^2 (mod 3 = 0)
    # Erwartet mod 3: 0 -> 2 (3, 9); 1 -> 2 (4, 7); 2 -> 3 (2, 5, 8)
    counts = von_mangoldt_residue_counts(10, 3)
    assert counts == [2, 2, 3]

    # Ungültige Eingaben
    with pytest.raises(ValueError):
        von_mangoldt_residue_counts(-1, 3)
    with pytest.raises(ValueError):
        von_mangoldt_residue_counts(10, 0)
