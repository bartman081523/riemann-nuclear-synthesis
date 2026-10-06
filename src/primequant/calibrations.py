"""Kalibrierte Parameter — ausschliesslich aus committeten Rohdaten.

Disk-only-Schicht: Kalibrier-Werte kommen von der Platte (committete Roh-
JSONs mit Hash-Pins), niemals aus einer Live-Abfrage — kein Runtime-Import,
kein Token, keine Job-Anbindung. Jeder Wert traegt die Herkunfts-Achse
"kalibriert+<fetched_at_utc des Dokuments>" und die Klasse ABGELEITET
(kalibrierte Geraete-Werte sind empirisch und duerfen niemals die Klasse
EXAKT tragen — Verkettungsregel der Garantien).

Zwei Lesarten pro readout_cal-Reihe (beides ganzrationale Arithmetik):

* Randflips (Primar-Lesart): im per-Qubit-unabhaengigen Auslesemodell ist
  P(Bit i = 1 beim Auslesen von 0^nq) == ro_i EXAKT (Marginalisierung ueber
  die anderen Qubits) — ro_i = Masse auf den Labels mit Bit i == 1 / shots
  als Fraction, ohne Wurzel, ohne Transzendenz.
* Uniform-Lesart (ro_hat): (1 - ro)^nq == p0 am Label 0^nq. Die n-te Wurzel
  ist i.A. algebraisch-irrational, also kein exakter Fraction-Punktwert —
  hier als exaktes Brueckungs-INTERVALL: mit A = k0 * shots^(nq-1) und
  L = floor(A^(1/nq)) gilt  (1-ro) in [L/S, (L+1)/S],  also
  ro in [(S-L-1)/S, (S-L)/S], Breite 1/S (S = shots). Ist A selbst eine
  exakte n-te Potenz (z. B. k0 = S*(63/64)^2 bei nq = 2), kollabiert das
  Intervall auf den exakten Punktwert 1 - (k0/S)^(1/nq) in Fraction.

Die Wurzel selbst wird NICHT ausgewertet (kein float im Pfad); der
Transzendenz-Hinweis fuer den Punktwert steht in KNOWN_GAPS.md.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Tuple

from ._anchors import lies_rohdokument, versichere_counts_md5
from ._guarantees import AnchorViolation, Guarantee


def ganzzahl_wurzel(x: int, n: int) -> int:
    """floor(x^(1/n)) exakt — Bisektion im Ganzzahl-Bereich.

    Nachlauf-Pruefung als Beweis-Zeuge: r**n <= x < (r+1)**n, sonst
    AnchorViolation (Arithmetik-Verstoß, kein stiller Rundungsdurchlass).
    """
    x = int(x)
    n = int(n)
    if x < 0:
        raise ValueError(f"x muss >= 0 sein, erhalten {x}")
    if n <= 0:
        raise ValueError(f"n muss >= 1 sein, erhalten {n}")
    if x < 2:
        return x
    # Sicherer Anfangs-Rahmen: x < 2**bits  =>  x^(1/n) < 2**ceil(bits/n)
    oben = 1 << ((x.bit_length() + n - 1) // n)
    unten = 0
    while unten < oben:
        mitte = (unten + oben + 1) // 2
        if mitte ** n <= x:
            unten = mitte
        else:
            oben = mitte - 1
    r = unten
    if not (r ** n <= x < (r + 1) ** n):
        raise AnchorViolation(
            f"Wurzel-Zeuge verletzt bei x={x}, n={n}: r={r}"
        )
    return r


def _bitstring_laenge(counts: Dict[str, int]) -> int:
    """Einheitliche Label-Breite pruefen und zurueckgeben (nq)."""
    laengen = {len(label.replace(" ", "")) for label in counts}
    if len(laengen) != 1:
        raise AnchorViolation(
            f"Label-Laengen uneinheitlich im readout_cal-Reihe: {laengen}"
        )
    return next(iter(laengen))


def lese_readout_cal_reihen(dokument: dict) -> List[dict]:
    """readout_cal-Reihen aus einem Rohdokument, mit Struktur-Pruefung.

    Verlangt: counts-Array mit Zeilen der Kind 'readout_cal'; jede
    Zeile einheitliche Label-Breite, positives shots_actual und
    Counts-Summe == shots_actual. Ohne readout_cal-Reihe: AnchorViolation
    (Kalibrierung aus diesem Dokument unmoeglich — kein stiller Fallback).
    """
    reihen = dokument.get("counts")
    if not isinstance(reihen, list) or not reihen:
        raise AnchorViolation("kein counts-Array im Rohdokument")
    kalibrier = []
    for zeile in reihen:
        if zeile.get("kind") != "readout_cal":
            continue
        counts = zeile.get("counts")
        name = zeile.get("name") or zeile.get("circuit")
        if not isinstance(counts, dict) or not counts:
            raise AnchorViolation(f"readout_cal {name!r}: counts leer")
        nq = _bitstring_laenge(counts)
        shots = int(zeile.get("shots_actual") or 0)
        if shots <= 0:
            raise AnchorViolation(
                f"readout_cal {name!r}: shots_actual <= 0")
        gesamt = 0
        for label, masse in counts.items():
            int(label.replace(" ", ""), 2)  # Wohlform: nur '0'/'1'
            if int(masse) != masse:
                raise AnchorViolation(
                    f"readout_cal {name!r}: Masse {masse!r} nicht ganz")
            gesamt += int(masse)
        if gesamt != shots:
            raise AnchorViolation(
                f"readout_cal {name!r}: Counts-Summe {gesamt} != shots {shots}"
            )
        kalibrier.append(zeile)
    if not kalibrier:
        raise AnchorViolation("kein readout_cal-Reihe im Rohdokument")
    return kalibrier


def rand_flip_anteile(reihe: dict) -> Dict[int, Fraction]:
    """Per-Qubit-Randflips EXAKT: ro_i = Masse mit Bit i == 1 / shots.

    Identitaet-Bitordnung: label-int Bit i <=> Register-Qubit i (LSB-0),
    wie in der gesamten Paketschicht (distributions/observables/channels).
    """
    counts = reihe["counts"]
    nq = _bitstring_laenge(counts)
    shots = int(reihe["shots_actual"])
    flips = [0] * nq
    for label, masse in counts.items():
        bits = int(label.replace(" ", ""), 2)
        for i in range(nq):
            if (bits >> i) & 1:
                flips[i] += int(masse)
    return {i: Fraction(flips[i], shots) for i in range(nq)}


def ro_intervall(reihe: dict) -> Dict[str, object]:
    """Uniform-Lesart: (1 - ro)^nq == p0 am Label 0^nq -> exaktes Intervall.

    Siehe Modul-Docstring (Herleitung). Rueckgabe mit name/nq/shots/k0/p0,
    ro_lo, ro_hi, breite; k0 == shots entartet auf ro = 0 exakt
    (Intervall kollabiert). 'uniform_ro_exakt' ist True genau dann, wenn
    der Punktwert ganzrational darstellbar ist (ganze n-te Potenz).
    """
    counts = reihe["counts"]
    name = reihe.get("name") or reihe.get("circuit")
    nq = _bitstring_laenge(counts)
    shots = int(reihe["shots_actual"])
    label0 = format(0, "0%db" % nq)
    k0 = int(counts.get(label0, 0))
    if not 0 <= k0 <= shots:
        raise AnchorViolation(f"readout_cal {name!r}: k0 ausserhalb [0, shots]")
    p0 = Fraction(k0, shots)
    if k0 == shots:
        ro = Fraction(0)
        return {
            "name": name, "nq": nq, "shots": shots, "k0": k0, "p0": p0,
            "ro_lo": ro, "ro_hi": ro, "breite": Fraction(0),
            "uniform_ro_exakt": True,
        }
    a = k0 * shots ** (nq - 1)
    L = ganzzahl_wurzel(a, nq)
    if L ** nq == a:  # exakte n-te Potenz -> Punktwert ganzrational
        ro = Fraction(shots - L, shots)
        return {
            "name": name, "nq": nq, "shots": shots, "k0": k0, "p0": p0,
            "ro_lo": ro, "ro_hi": ro, "breite": Fraction(0),
            "uniform_ro_exakt": True,
        }
    ro_lo = Fraction(shots - L - 1, shots)
    ro_hi = Fraction(shots - L, shots)
    return {
        "name": name, "nq": nq, "shots": shots, "k0": k0, "p0": p0,
        "ro_lo": ro_lo, "ro_hi": ro_hi, "breite": Fraction(1, shots),
        "uniform_ro_exakt": False,
    }


def kalibriere_dokument(pfad: str) -> dict:
    """Alle readout_cal-Kalibrierungen eines committeten Rohdokuments.

    Liest die Datei, verifiziert den counts-md5-Pin, nimmt fetched_at_utc
    als Kalibrier-Datum (Herkunfts-Achse) und berechnet je Reihen beide
    Lesarten. Rueckgabe: pfad/backend/fetched_at_utc/counts_md5_rekomputiert/
    herkunft + 'reihen' {name: {ro_rand_qubits, ro_intervall, garantie}} +
    'garantie' (Dokument-Ebene, gleiche Klasse).
    """
    dokument = lies_rohdokument(pfad)
    pin = versichere_counts_md5(dokument)
    fetched = str(dokument.get("fetched_at_utc") or "")
    if not fetched:
        raise AnchorViolation(
            "Rohdokument ohne fetched_at_utc — Kalibrier-Datum unbestimmt")
    herkunft = "kalibriert+" + fetched
    reihen = lese_readout_cal_reihen(dokument)
    erg = {
        "pfad": pfad,
        "backend": dokument.get("backend"),
        "fetched_at_utc": fetched,
        "counts_md5_rekomputiert": pin,
        "herkunft": herkunft,
        "reihen": {},
    }
    for zeile in reihen:
        name = zeile.get("name") or zeile.get("circuit") or "?"
        nq = _bitstring_laenge(zeile["counts"])
        inter = ro_intervall(zeile)
        garantie = Guarantee(
            klasse="ABGELEITET",
            herkunft=herkunft,
            grenze=(
                "Randflips exakt je Qubit (Fraction k_i/"
                f"{zeile['shots_actual']}); Uniform-Lesart ro in "
                f"[{inter['ro_lo']}, {inter['ro_hi']}] "
                f"(Breite {inter['breite']}, S = {inter['shots']})"
            ),
            quelle=(
                f"{pfad} / readout_cal/{name} "
                f"(counts_md5 {pin})"
            ),
        )
        erg["reihen"][name] = {
            "nq": nq,
            "ro_rand_qubits": rand_flip_anteile(zeile),
            "ro_intervall": inter,
            "garantie": garantie,
        }
    erg["garantie"] = Guarantee(
        klasse="ABGELEITET",
        herkunft=herkunft,
        grenze="Kalibrierung nur aus committeten Reihen mit verifiziertem Pin",
        quelle=f"{pfad} (counts_md5 {pin})",
    )
    return erg