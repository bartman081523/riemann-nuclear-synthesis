"""
Anker-Tests: Garantie-Deklaration (EXAKT / ABGELEITET / GESAMPFELT)
und die Verkettungsregel (Klasse wandert im Datenfluss nur ABWAERTS).

Anker sind strukturell: Konstruktions-Verstoesse (kalibriert-als-EXAKT,
EXAKT-mit-Schranke), Schema-Pflicht in JSON, Rang-Ordnung und die
Verkettungs-Matrix (EXAKT nie aus GESAMPFELT, Leer-Deklaration verweigert).
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

from primequant import _guarantees as g


def test_rang_ordnung_strikt():
    assert g.klasse_rang("GESAMPFELT") < g.klasse_rang("ABGELEITET")
    assert g.klasse_rang("ABGELEITET") < g.klasse_rang("EXAKT")
    with pytest.raises(ValueError):
        g.klasse_rang("EXAKT+")  # unbekannte Klasse


def test_exakt_baukonventionen():
    gu = g.Guarantee("EXAKT", herkunft="exakt-definiert", quelle="Phi_q-Reduktion")
    assert gu.grenze is None
    # EXAKT + kalibriert -> Anker-Verletzung
    with pytest.raises(g.AnchorViolation):
        g.Guarantee("EXAKT", herkunft="kalibriert+2026-10-06T00:00:00Z")
    # EXAKT + Schranke -> Anker-Verletzung
    with pytest.raises(g.AnchorViolation):
        g.Guarantee("EXAKT", grenze="< 1e-9")
    # ABGELEITET mit Schranke ist OK (Schranke gehoert hierher)
    ab = g.Guarantee("ABGELEITET", herkunft="abgeleitet", grenze="≤ 2 ULP")
    assert ab.grenze == "≤ 2 ULP"
    # geschätzt:... ist eine markierte Hypothese, darf nicht EXAKT laufen
    with pytest.raises(g.AnchorViolation):
        g.Guarantee("EXAKT", herkunft="geschätzt:Hypothese")  # Praefix check


def test_herkunft_praefix_zwang():
    with pytest.raises(ValueError):
        g.Guarantee("ABGELEITET", herkunft="wunderbar gerechnet")
    assert g.Guarantee("ABGELEITET", herkunft="kalibriert+2026-10-05T12:00:00Z")
    assert g.Guarantee("GESAMPFELT", herkunft="geschätzt:p1-Hypothese")


def test_json_roundtrip_und_schema_zwang():
    for klasse, herkunft, grenze in (
        ("EXAKT", "exakt-definiert", None),
        ("ABGELEITET", "kalibriert+2026-10-06T09:00:00Z", "≤ 1e-3"),
        ("GESAMPFELT", "geschätzt:Hypothese", "< 0.02"),
    ):
        daten = g.Guarantee(klasse, herkunft, grenze).als_json()
        assert daten["schema"] == g.GUARANTEE_SCHEMA == "primequant.garantie/1"
        rueck = g.Guarantee.aus_json(daten)
        assert rueck == g.Guarantee(klasse, herkunft, grenze)
    ohne_schema = {"klasse": "EXAKT", "herkunft": "exakt-definiert"}
    with pytest.raises(g.AnchorViolation):
        g.Guarantee.aus_json(ohne_schema)


def test_garantiere_und_garantiert_json():
    wert = g.garantiere(42, "EXAKT", herkunft="exakt-definiert", quelle="test")
    assert isinstance(wert, g.Garantiert)
    assert wert.wert == 42
    daten = wert.als_json()
    assert daten["wert"] == 42
    assert daten["garantie"]["klasse"] == "EXAKT"
    wert2 = g.garantiere(0.5, "ABGELEITET", grenze="≤ 2 ULP")
    g.forder_garantie(wert2.garantie, "ABGELEITET")
    g.forder_garantie(wert2.garantie, "GESAMPFELT")
    with pytest.raises(g.AnchorViolation):
        g.forder_garantie(wert2.garantie, "EXAKT")


def test_verkettung_matrix():
    e = g.Guarantee("EXAKT", herkunft="exakt-definiert")
    a = g.Guarantee("ABGELEITET")
    s = g.Guarantee("GESAMPFELT", herkunft="geschätzt:Hypothese")

    # abwaerts erlaubt
    g.pruefe_verkettung(e, [e])
    g.pruefe_verkettung(a, [e])
    g.pruefe_verkettung(s, [e, a, s])
    g.pruefe_verkettung(a, [e, a])  # min = ABGELEITET
    # Aufwaerts verboten
    with pytest.raises(g.AnchorViolation):
        g.pruefe_verkettung(e, [a])
    with pytest.raises(g.AnchorViolation):
        g.pruefe_verkettung(e, [s])
    with pytest.raises(g.AnchorViolation):
        g.pruefe_verkettung(a, [s])
    with pytest.raises(g.AnchorViolation):
        g.pruefe_verkettung(e, [e, s])  # Mischung: min = GESAMPFELT
    # Garantierte als Eingabe akzeptiert
    g.pruefe_verkettung(a, [g.garantiere(1, "EXAKT", herkunft="exakt-definiert")])
    # Leer-Deklaration verweigert
    with pytest.raises(g.AnchorViolation):
        g.pruefe_verkettung(e, [])
    # Nicht-Garantie-Eingabe -> ValueError (Deklaration ist Schnittstelle)
    with pytest.raises(ValueError):
        g.pruefe_verkettung(e, [42])