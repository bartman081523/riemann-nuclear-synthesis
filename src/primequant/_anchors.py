"""Externe Anker der Paketschicht — Hash-Pins und committete Rohdokumente.

Goedel-Regel (epistemic_rules 4): das Rechenwerk zertifiziert sich nicht
selbst. Ankerung laeuft daher ueber unveraenderliche Artefakte — committete
Roh-JSONs mit Hash-Pins — und ueber ausserhalb der Schicht deklarierte
Schwellen. Diese Datei liefert die Anker-Werkzeuge:

* ``payload_sha256``          — SHA-256 ueber Bytes (Pin-Regel fuer neue
                                Preregs/Raws seit 2026-10-05).
* ``counts_payload``          — kanonische Counts-Serialisierung BIT-GENAU
                                als Spiegel des Bestandsproduzenten
                                (``pt_ram_q_hardware3_qpu.counts_md5``:
                                json.dumps mit sort_keys=True und
                                separators=(",", ":")). Die Bit-Identitaet
                                ist durch den Anker-Test an den committeten
                                Pins belegt; der Produzent selbst wird
                                NICHT importiert (kein Pfad-Zirkel, die
                                Bestandsmodule bleiben gefroren).
* ``counts_md5`` / ``counts_sha256`` — Pins ueber die Counts-Dicts-Liste.
* ``datei_sha256``            — Pin ueber eine ganze Datei (Freeze-Pin).
* ``lies_rohdokument``        — committetes Roh-JSON von der Platte, NUR
                                lesend.
* ``versichere_counts_md5``   — Pin-Re-Verifikation am Dokument:
                                AnchorViolation bei Divergenz.
* ``lies_committed_counts``   — lies + verifiziere in einem Schritt.

EXAKT-Schicht: nur hashlib/json/os auf dem Pfad (Hashes ueber exakten
Bytes sind exakte Identitaeten, keine Naeherung); keine Wurf-Quelle, keine
Job-Anbindung, kein Token-Zugriff.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Dict, List, Optional, Tuple

from ._guarantees import AnchorViolation


def payload_sha256(payload) -> str:
    """SHA-256 ueber Byte-Payload (Pin-Regel fuer neue Pins, 2026-10-05)."""
    if not isinstance(payload, (bytes, bytearray)):
        raise ValueError("payload_sha256 verlangt bytes oder bytearray")
    return hashlib.sha256(bytes(payload)).hexdigest()


def counts_payload(counts_list: List[Dict[str, int]]) -> bytes:
    """Kanonische Counts-Serialisierung — bit-genauer Spiegel der Bestandskette.

    json.dumps(counts_list, sort_keys=True, separators=(",", ":")) als bytes —
    die Identitaet zum Bestandsproduzenten ist durch die Anker-Tests an den
    committeten Pins belegt (hardware3/kingston/prio48_sv); hier bewusst
    als eigene Implementierung, damit die EXAKT-Schicht vom gefrorenen
    Experiment-Baum unabhaengig bleibt.
    """
    return json.dumps(counts_list, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def counts_md5(counts_list: List[Dict[str, int]]) -> str:
    """Legacy-MD5-Pin der Bestandskette (Bestands-Pins bleiben MD5; neue
    Pins werden SHA-256 — die Legacy-Re-Verifikation nutzt dieselbe
    Serialisierung)."""
    return hashlib.md5(counts_payload(counts_list)).hexdigest()


def counts_sha256(counts_list: List[Dict[str, int]]) -> str:
    """SHA-256-Pin ueber dieselbe kanonische Serialisierung."""
    return payload_sha256(counts_payload(counts_list))


def datei_sha256(pfad: str) -> str:
    """SHA-256 ueber den GESAMTEN Byte-Inhalt einer Datei (Freeze-Pin)."""
    if not os.path.exists(pfad):
        raise FileNotFoundError(f"Datei fehlt: {pfad}")
    with open(pfad, "rb") as d:
        return hashlib.sha256(d.read()).hexdigest()


def lies_rohdokument(pfad: str) -> dict:
    """Committetes Roh-JSON von der Platte — nur lesend, kein Schreiben."""
    if not os.path.exists(pfad):
        raise FileNotFoundError(f"Rohdokument fehlt: {pfad}")
    with open(pfad, "rb") as d:
        return json.load(d)


def versichere_counts_md5(dokument: dict) -> str:
    """Pin-Re-Verifikation am Rohdokument (Legacy-MD5).

    Divergenz ist eine AnchorViolation: das committete Artefakt waere
    veraendert oder der Pin falsch — beides zertifikatsunfaehig. Zurueck
    kommt der rekomputierte Pin (fuer Quelle-Eintraege in Garantien).
    """
    if "counts" not in dokument or "counts_md5" not in dokument:
        raise AnchorViolation(
            "Rohdokument ohne counts oder counts_md5 — Pin unverifizierbar"
        )
    liste = [zeile["counts"] for zeile in dokument["counts"]]
    pin = counts_md5(liste)
    if pin != dokument["counts_md5"]:
        raise AnchorViolation(
            f"counts_md5 divergiert: rekomputiert {pin}, "
            f"committet {dokument['counts_md5']}"
        )
    return pin


def lies_committed_counts(pfad: str) -> Tuple[dict, str]:
    """Rohdokument lesen + Pin verifizieren — Standard-Eingang der
    Anker-Familien (b)/(c): danach liest die Auswertung nur committete
    Artefakte mit verifiziertem Hash."""
    dokument = lies_rohdokument(pfad)
    pin = versichere_counts_md5(dokument)
    return dokument, pin