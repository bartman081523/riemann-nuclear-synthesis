"""Garantie-Deklarationen fuer primequant — EXAKT / ABGELEITET / GESAMPFELT.

Zwei unabhaengige Achsen, bewusst NICHT miteinander vermischt:

* Arithmetik-Achse (``klasse``): EXAKT (nur int/Fraction auf dem Wertepfad),
  ABGELEITET (definierte Transformation einer exakten Quelle, z. B. float-
  Schatten mit Schranke), GESAMPFELT (gezogene Stichprobe — nur als
  nicht-bewertungsrelevante Kreuzpruefung oder Re-Play-Kontrolle zulaessig).
* Herkunfts-Achse (``herkunft``): "kalibriert+<UTC-ISO>" (Geraete-Datum mit
  Zeitstempel), "abgeleitet" (aus einer benannten Identitaet), "geschätzt:…"
  (markierte Hypothese, niemals Physik-Assert).

Regel der Verkettung (Goe del-Regel der Paketschicht — das Rechenwerk
zertifiziert sich nicht selbst): eine Klasse kann auf dem Datenfluss nur
ABWAERTS wandern (EXAKT -> ABGELEITET -> GESAMPFELT), niemals aufwaerts. Ein
Wert, der als EXAKT ausgegeben wird, wo der Eingangsschleier GESAMPFELT war,
ist eine Anker-Verletzung, kein Upgrade. Und: kalibrierte Geraete-Werte sind
empirisch — sie duerfen niemals die Klasse EXAKT tragen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

Klassen = ("GESAMPFELT", "ABGELEITET", "EXAKT")
_RANG = {k: i for i, k in enumerate(Klassen)}

GUARANTEE_SCHEMA = "primequant.garantie/1"

_HERKUNFT_PREFIXE = ("kalibriert+", "abgeleitet", "geschätzt:")


class AnchorViolation(Exception):
    """Verletzung einer Garantie-Deklaration (falsche Klasse, Aufwaerts-Wanderung,
    kalibriert-als-EXAKT, fehlender externer Anker)."""


@dataclass(frozen=True)
class Guarantee:
    """Garantie-Etikett eines Wertes/Ergebnisses — Teil der Schnittstelle,
    nicht der Doku nachtraeglich."""

    klasse: str
    herkunft: str = "abgeleitet"
    grenze: Optional[str] = None
    quelle: Optional[str] = None

    def __post_init__(self) -> None:
        if self.klasse not in _RANG:
            raise ValueError(
                f"unbekannte Garantieklasse {self.klasse!r}; zulaessig: {Klassen}"
            )
        if not any(
            self.herkunft.startswith(p) for p in _HERKUNFT_PREFIXE
        ) and self.herkunft != "exakt-definiert":
            raise ValueError(
                "herkunft muss mit 'kalibriert+' beginnen oder 'abgeleitet'/"
                f"'geschätzt:…'/'exakt-definiert' sein, erhalten {self.herkunft!r}"
            )
        if self.klasse == "EXAKT" and self.herkunft != "exakt-definiert":
            raise AnchorViolation(
                f"EXAKT verlangt herkunft 'exakt-definiert' (aus einer benannten "
                f"Identitaet), erhalten {self.herkunft!r} — kalibrierte Geraete-Werte "
                "sind empirisch und 'geschätzt:…' ist eine markierte Hypothese; "
                "beide duerfen niemals die Klasse EXAKT tragen"
            )
        if self.klasse == "EXAKT" and self.grenze is not None:
            raise AnchorViolation(
                "EXAKT traegt die Schranke 'keine' (None); eine Schranke gehoert "
                "zu ABGELEITET/GESAMPFELT"
            )

    def als_json(self) -> dict:
        return {
            "schema": GUARANTEE_SCHEMA,
            "klasse": self.klasse,
            "herkunft": self.herkunft,
            "grenze": self.grenze,
            "quelle": self.quelle,
        }

    @classmethod
    def aus_json(cls, daten: dict) -> "Guarantee":
        if daten.get("schema") != GUARANTEE_SCHEMA:
            raise AnchorViolation(
                f"Garantie-Payload ohne Schema {GUARANTEE_SCHEMA!r}"
            )
        return cls(
            klasse=daten["klasse"],
            herkunft=daten.get("herkunft", "abgeleitet"),
            grenze=daten.get("grenze"),
            quelle=daten.get("quelle"),
        )


@dataclass(frozen=True)
class Garantiert:
    """Wert mit seinem unloesbaren Garantie-Etikett."""

    wert: object
    garantie: Guarantee

    def als_json(self) -> dict:
        return {"wert": self.wert, "garantie": self.garantie.als_json()}


def garantiere(
    wert: object,
    klasse: str,
    herkunft: str = "abgeleitet",
    grenze: Optional[str] = None,
    quelle: Optional[str] = None,
) -> Garantiert:
    return Garantiert(wert=wert, garantie=Guarantee(klasse, herkunft, grenze, quelle))


def klasse_rang(klasse: str) -> int:
    if klasse not in _RANG:
        raise ValueError(f"unbekannte Garantieklasse {klasse!r}")
    return _RANG[klasse]


def forder_garantie(garantie: Guarantee, mindestens: str) -> None:
    """Hebt, wenn die Klasse unter der geforderten Mindestklasse liegt."""
    if klasse_rang(garantie.klasse) < klasse_rang(mindestens):
        raise AnchorViolation(
            f"Garantie {garantie.klasse} erfuellt Mindestklasse {mindestens} nicht"
        )


def pruefe_verkettung(ausgabe: Guarantee, eingaben: Iterable[object]) -> None:
    """Ausgabeklasse darf nie OVER der schwächsten Eingabeklasse liegen
    (keine Aufwaerts-Laundering: EXAKT nie aus GESAMPFELT, ABGELEITET nie aus
    GESAMPFELT+EXAKT-Mischung heraus hochgestuft)."""
    rang_min = None
    for ein in eingaben:
        g = ein.garantie if isinstance(ein, Garantiert) else ein
        if not isinstance(g, Guarantee):
            raise ValueError("Eingabe ohne Guarantee; Deklaration ist Schnittstelle")
        r = klasse_rang(g.klasse)
        rang_min = r if rang_min is None else min(rang_min, r)
    if rang_min is None:
        raise AnchorViolation(
            "Verkettung ohne Eingaben deklariert — mindestens ein Eingabe-Etikett nötig"
        )
    if klasse_rang(ausgabe.klasse) > rang_min:
        raise AnchorViolation(
            f"Ausgabe {ausgabe.klasse} ueber schwaechster Eingabe "
            f"{Klassen[rang_min]} — Aufwaerts-Wanderung verboten"
        )