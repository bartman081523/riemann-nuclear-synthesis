"""
Anker-Tests: Seed-Bann, Abhaengigkeits-Bann und Token-Bann — erzwungen,
nicht nur dokumentiert.

  1. EXAKT-Module (__init__, _cyc, _gfq, _guarantees, + Phase B) importieren
     KEINE Wurf-Quelle: AST-Scan verbietet numpy/scipy/sympy/random-Imports;
     Text-Scan verbietet Zieh-API-Muster (randint/randn/shuffle/default_rng/...)
     und "np."-Notation.
  2. Das gesamte Paket (alle .py unter src/primequant) importiert kein
     qiskit / qiskit_ibm_runtime / dotenv und liest kein Token (IBMQ/_TOKEN/
     get_service/QISKIT_IBM) — Kalibrier-Werte kommen nur als committete
     Artefakte in die Schicht (Phase B: calibrations.py liest Dateien).
  3. Version-Abgleich: __version__ == pyproject.toml-version.
"""
import ast
import os
import sys
import tomllib

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

try:
    import primequant as pq
except ImportError:  # editable install fehlt: src-Fallback
    sys.path.insert(0, os.path.join(_REPO, "src"))
    import primequant as pq

PAKET_ORDNER = os.path.join(_REPO, "src", "primequant")

EXAKT_MODULES = ("__init__.py", "_guarantees.py", "_cyc.py", "_gfq.py")

VERBOTENE_IMPORT_ROOTS = {"numpy", "scipy", "sympy", "random", "secrets"}

VERBOTENE_TOKEN = (
    "random",
    "default_rng",
    "RandomState",
    "randint",
    "randn",
    "shuffle",
    "choice(",
    "sampl",
    "np.",
)

VERBOTENE_TOKEN_PAKETWEIT = (
    "qiskit",
    "QiskitRuntimeService",
    "get_service",
    "IBMQ",
    "_TOKEN",
    ".env",
    "dotenv",
)


def _quelltexte(dateien):
    for name in dateien:
        pfad = os.path.join(PAKET_ORDNER, name)
        assert os.path.exists(pfad), f"EXAKT-Modul fehlt: {pfad}"
        with open(pfad, "r", encoding="utf-8") as d:
            yield name, pfad, d.read()


def _import_roots(quelltext):
    baum = ast.parse(quelltext)
    roots = set()
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Import):
            for alias in knoten.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(knoten, ast.ImportFrom):
            if knoten.level == 0 and knoten.module:
                roots.add(knoten.module.split(".")[0])
    return roots


def test_exakt_modules_importieren_keine_wurfquelle():
    for name, _pfad, text in _quelltexte(EXAKT_MODULES):
        roots = _import_roots(text)
        verboten = roots & VERBOTENE_IMPORT_ROOTS
        assert not verboten, f"{name} importiert verboten: {verboten}"


def test_exakt_modules_ohne_zieh_api_token():
    for name, _pfad, text in _quelltexte(EXAKT_MODULES):
        for token in VERBOTENE_TOKEN:
            assert token not in text, f"{name} enthaelt verboten Token {token!r}"


def test_paketweit_kein_qiskit_kein_token():
    alle = sorted(n for n in os.listdir(PAKET_ORDNER) if n.endswith(".py"))
    assert alle, "Paketordner unveraendert: src/primequant/*.py erwartet"
    for name, _pfad, text in _quelltexte(alle):
        for token in VERBOTENE_TOKEN_PAKETWEIT:
            assert token not in text, f"{name} enthaelt verboten Token {token!r}"


def test_version_gleicht_pyproject():
    mit_pyproject = os.path.join(_REPO, "pyproject.toml")
    assert os.path.exists(mit_pyproject)
    with open(mit_pyproject, "rb") as d:
        daten = tomllib.load(d)
    assert daten["project"]["name"] == "primequant"
    assert pq.__version__ == daten["project"]["version"]