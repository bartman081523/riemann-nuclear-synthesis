"""Kanal-Schicht — Kraus-Float-Darstellung + exakter Wahrscheinlichkeits-Zweig.

Dieses Modul traegt bewusst ZWEI Arithmetik-Schichten (Arithmetik-Achse) und
ist deshalb NICHT in der EXAKT-Modul-Liste der Hygiene-Pruefung:

* **Float-Schicht** (ABGELEITET-Werkzeug): Kraus-Operatoren als numpy-
  Matrizen fuer Dichtematrix-Pfade. Jeder Parameter kommt herkunft-
  etikettiert herein (``Param``) — kalibriert+<UTC> / abgeleitet /
  geschätzt:…; die Schicht ist niemals Quelle einer exakten Aussage.
* **Exakter Zweig** (EXAKT, ganzrational): Kanaele auf Wahrscheinlichkeits-
  Vektoren (Fractions). Grundlage ist das **Diagonal-Abschluss-Theorem**:
  Depolarisieren, Abklingen (Amplituden-Daempfung), Dephasieren und der
  Auslese-Verwirrungs-Kanal bilden diagonale Dichtematrizen in sich ab —
  fuer die Prep -> Messung-Familie (055/055b/055c) ist die Torzahl-
  Noise-Modellierung auf Wahrscheinlichkeits-Ebene also exakt rational,
  sobald die Kanal-Parameter ganzrational sind. Der Test bestätigt die
  Theorem-Aussage in BEIDEN Schichten (im Float-Pfad sogar bitweise:
  die Kohärenz-Eintraege bleiben EXAKT 0.0).

Qubit-Bit-Konvention (wie in Qiskit-Counts-Darstellung und in den
geflorenen Label-Ketten): Label-int bit i == Qubit i (LSB = Qubit 0);
Bitstring-Anzeige mit hoehstem Qubit links int(bits, 2) konsistent.

Torzahl-Komposition (ISA-Op-Counts, V12): ``ChannelModel.aus_op_counts``
liest die Op-COUNTS-Dicts des committeten ISA-Reports (sx/x -> 1q,
cz/cx/ecr -> 2q, rz -> virtuell = kein Gate-Fehler, measure -> Auslese)
und komponiert p_eff(k, p) = 1 - (1 - p)^k als EXAKTE Fraction-Form
(ganzzahlige Potenzen,Division bleibt ganzrational). KEIN Transpile,
keine seed_transpiler-Fahndung, keine ISA_CELL_DRIFT-Exposure.

Verkettungs-Schutz: jede komponierte Groesse traegt ihr Garantie-Etikett
via ``pruefe_verkettung`` — die Ausgabeklasse liegt nie UEBER der
schwaechsten Eingabeklasse (EXAKT nie aus GESAMPFELT; geschätzt-Parameter
tragen GESAMPFELT und koennen nicht durch Etikett umgedeutet werden).

Bekannte Gaps (siehe KNOWN_GAPS.md): thermische Relaxation nur als
Affin-Karte auf Populations-Ebene + Kohaerenzfaktor im FLOAT-Pfad — der
volle Kraus-Satz fuer T2 > T1 ist NICHT implementiert (GAP, keine
aus-dem-Gedaechtnis-Konstruktion); ro = p0^(1/nq) ist fuer p0 nicht in
{0, 1} transzendent -> Auslese bleibt im Float-Pfad (ABGELEITET).
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from ._guarantees import (
    AnchorViolation,
    Garantiert,
    Guarantee,
    pruefe_verkettung,
)
from ._guarantees import klasse_rang

# --- Param-Etikett ----------------------------------------------------------


@dataclass(frozen=True)
class Param:
    """Ein Kanal-Parameter mit Herkunfts-Etikett (Teil der Schnittstelle).

    wert: Fraction fuer ganzrationale Parameter, float fuer transzendente
    Darstellungen (nie Quelle einer EXAKT-Aussage). herkunft folgt den
    _guarantees-Praefixen: "kalibriert+<UTC>" (Geraete-Datum), "abgeleitet"
    (definierte Transformation einer benannten Quelle), "geschätzt:<…>"
    (markierte Hypothese).
    """

    name: str
    wert: object
    herkunft: str
    quelle: Optional[str] = None

    def __post_init__(self) -> None:
        if isinstance(self.wert, int) and not isinstance(self.wert, bool):
            object.__setattr__(self, "wert", Fraction(self.wert))
        if isinstance(self.wert, Fraction):
            pass
        elif isinstance(self.wert, float):
            if self.wert != self.wert or self.wert in (
                float("inf"), float("-inf")
            ):
                raise ValueError(
                    f"Param {self.name}: wert nicht-endlich ({self.wert})"
                )
        else:
            raise ValueError(
                f"Param {self.name}: wert must Fraction, int oder float sein, "
                f"erhalten {type(self.wert).__name__}"
            )
        if not self.name:
            raise ValueError("Param verlangt einen nicht-leeren Namen")
        # herkunft-Vorformat wird von der Garantie-Konstruktion geprueft.

    def garantie(self) -> Guarantee:
        """Arithmetik-Klasse aus der Herkunfts-Klasse des Parameters.

        geschätzt:… -> GESAMPFELT (schwaechste Klasse — Hypothesen
        koennen nicht durch Etikett umgedeutet werden); kalibriert+ und
        abgeleitet -> ABGELEITET (kalibrierte Geraete-Werte duerfen nie
        EXAKT tragen). grenze: arithmetische Darstellungs-Schranke des
        Float-Wertes (Fraction traegt None — ganzrational exakt).
        """
        if self.herkunft.startswith("geschätzt:"):
            klasse = "GESAMPFELT"
        elif self.herkunft == "exakt-definiert":
            klasse = "EXAKT"          # benannte exakte Identitaet, kein Geraet
        elif self.herkunft.startswith("kalibriert+") or self.herkunft == "abgeleitet":
            klasse = "ABGELEITET"
        else:
            raise ValueError(
                f"Param {self.name}: herkunft braucht kalibriert+/abgeleitet/"
                f"geschätzt:-Praefix, erhalten {self.herkunft!r}"
            )
        grenze = None if isinstance(self.wert, Fraction) else \
            f"float-Darstellungschranke (ULP-Skala) fuer Param {self.name}"
        return Guarantee(
            klasse=klasse,
            herkunft=self.herkunft,
            grenze=grenze,
            quelle=self.quelle,
        )


# --- EXAKTER Wahrscheinlichkeits-Zweig --------------------------------------


def _probvektor_normieren(p_vektor: Sequence[object]) -> List[Fraction]:
    """int -> Fraction; float-Eintraege verweigert (EXAKT-Zweig-Pflicht)."""
    fracs: List[Fraction] = []
    for p in p_vektor:
        if isinstance(p, float):
            raise ValueError(
                "float-Eintrag im EXAKT-Zweig — Wahrscheinlichkeits-Vektoren "
                "müssen als Fraction hereinkommen"
            )
        fracs.append(Fraction(p))
    summe = sum(fracs)
    if summe != 1:
        raise ValueError(f"Probvektor-Summe {summe} != 1")
    return fracs


def _basis_zwei(breite: int) -> int:
    if breite <= 0 or breite & (breite - 1):
        raise ValueError(f"breite muss Zweierpotenz sein, erhalten {breite}")
    return breite.bit_length() - 1


def depolarisiert_probs(
    p_vektor: Sequence[object],
    lambda_frac: object,
    breite: int,
    qubits: Optional[Sequence[int]] = None,
) -> List[Fraction]:
    """Depolarisierender Kanal auf Wahrscheinlichkeits-Ebene EXAKT.

    E(rho) = (1-lambda)*rho + lambda * (I_paar/d_paar) (x) tr_paar(rho):
    auf den Labels new[a] = (1-lambda)*p[a] + (lambda/4^r) * p_rest[a]
    mit p_rest = Summe ueber Labels, deren Nicht-Kanal-Bits gleich sind.
    qubits=None depolarisiert das GESAMTE Register (Rest leer).
    """
    vec = _probvektor_normieren(p_vektor)
    lam = Fraction(lambda_frac)
    if not 0 <= lam <= 1:
        raise ValueError(f"lambda ausserhalb [0,1]: {lam}")
    n_qubits = _basis_zwei(breite)
    if len(vec) != breite:
        raise ValueError(
            f"Probvektor-Länge {len(vec)} != breite {breite}"
        )
    if qubits is None:
        qubits_l = list(range(n_qubits))
    else:
        qubits_l = list(int(q) for q in qubits)
        if len(set(qubits_l)) != len(qubits_l):
            raise ValueError(f"doppelte Qubits: {qubits_l}")
        if not all(0 <= q < n_qubits for q in qubits_l):
            raise ValueError(
                f"Qubits {qubits_l} ausserhalb 0..{n_qubits - 1}"
            )
    maske_kanal = 0
    for q in qubits_l:
        maske_kanal |= 1 << q
    maske_rest = ~maske_kanal & (breite - 1)
    n_paar = 1 << len(qubits_l)
    p_rest: Dict[int, Fraction] = {}
    for label, masse in enumerate(vec):
        rest_label = label & maske_rest
        p_rest[rest_label] = p_rest.get(rest_label, Fraction(0)) + masse
    ergebnis: List[Fraction] = []
    for label, masse in enumerate(vec):
        rest_label = label & maske_rest
        ergebnis.append(
            (1 - lam) * masse
            + lam * Fraction(1, n_paar) * p_rest[rest_label]
        )
    return ergebnis


def abklingen_probs(
    p_vektor: Sequence[object],
    gamma_frac: object,
    breite: int,
    qubits: Optional[Sequence[int]] = None,
) -> List[Fraction]:
    """Amplituden-Daempfung auf Wahrscheinlichkeits-Ebene EXAKT.

    Pro Kanal-Qubit: Anregung 1 -> 0 mit Wahrscheinlichkeit gamma
    (Abklingen; 0 -> 1 ist VERBOTEN im Modell). new[b] = sum_a p[a] *
    gamma^(#a&~b auf qubits) * (1-gamma)^(#a&b auf qubits), dabei muessen
    alle Nicht-Kanal-Bits von a und b UEBEREINSTIMMEN (Identitaet am Rest).
    """
    vec = _probvektor_normieren(p_vektor)
    gam = Fraction(gamma_frac)
    if not 0 <= gam <= 1:
        raise ValueError(f"gamma ausserhalb [0,1]: {gam}")
    n_qubits = _basis_zwei(breite)
    if len(vec) != breite:
        raise ValueError(f"Probvektor-Länge {len(vec)} != breite {breite}")
    if qubits is None:
        qubits_l = list(range(n_qubits))
    else:
        qubits_l = list(int(q) for q in qubits)
        if len(set(qubits_l)) != len(qubits_l):
            raise ValueError(f"doppelte Qubits: {qubits_l}")
        if not all(0 <= q < n_qubits for q in qubits_l):
            raise ValueError(
                f"Qubits {qubits_l} ausserhalb 0..{n_qubits - 1}"
            )
    maske_kanal = 0
    for q in qubits_l:
        maske_kanal |= 1 << q
    maske_rest = ~maske_kanal & (breite - 1)
    ergebnis = [Fraction(0)] * breite
    for label_a, masse in enumerate(vec):
        if masse == 0:
            continue
        bits_a_kanal = label_a & maske_kanal
        rest = label_a & maske_rest
        anregungen = bits_a_kanal.bit_count()
        # alle Muster der 1->0-Erosion durchlaufen:
        for eroeriert in range(1 << anregungen):
            # eroeriert waehlt, WELCHE Anregungen abklingen (Bit i <-> i-te
            # gesetzte Bit-Position in bits_a_kanal, LSB-zu-LSB-Reihenfolge)
            verlust = 0
            gesetzt = bits_a_kanal
            positionen = [i for i in range(n_qubits)
                          if (gesetzt >> i) & 1]
            for j, pos_i in enumerate(positionen):
                if (eroeriert >> j) & 1:
                    verlust |= 1 << pos_i
            b_kanal = bits_a_kanal & ~verlust
            b_label = rest | b_kanal
            abgeklungen = (bits_a_kanal & ~verlust).bit_count()
            gewicht = gam ** (anregungen - abgeklungen) \
                * (1 - gam) ** abgeklungen
            err = ergebnis[b_label]
            ergebnis[b_label] = err + masse * gewicht
    return ergebnis


def dephasieren_probs(
    p_vektor: Sequence[object],
    gamma_frac: object,
    breite: Optional[int] = None,
) -> List[Fraction]:
    """Dephasieren auf Wahrscheinlichkeits-Ebene EXAKT = IDENTITAET.

    Der Dephasierungskanal wirkt nur auf den Kohaerenzen (Off-Diagonalen);
    auf einer diagonalen Dichtematrix (Wahrscheinlichkeits-Vektor) ist er
    die Identitaet — das ist die registrierte Aussage dieses Kanals (gamma
    wird nur auf [0,1] validiert, um die Signatur-Symmetrie zu halten).
    """
    vec = _probvektor_normieren(p_vektor)
    gam = Fraction(gamma_frac)
    if not 0 <= gam <= 1:
        raise ValueError(f"gamma_phi ausserhalb [0,1]: {gam}")
    if breite is None:
        breite = len(vec)
    if len(vec) != int(breite):
        raise ValueError(f"Probvektor-Länge {len(vec)} != breite {breite}")
    return list(vec)


def auslese_probs(
    p_vektor: Sequence[object], ro_frac: object, breite: int
) -> List[Fraction]:
    """Auslese-Verwirrung EXAKT (symmetrisch, unabhaengig pro Qubit, alle).

    new[b] = sum_a p[a] * ro^(Hamming(a, b)) * (1-ro)^(nq - Hamming(a, b)).
    Qubits sind IMMER alle Register-Qubits (Auslese wir global gemessen);
    ro kann float sein — dann wirft der Zweig (Fraction-Pflicht).
    """
    vec = _probvektor_normieren(p_vektor)
    ro = Fraction(ro_frac)
    if not 0 <= ro <= 1:
        raise ValueError(f"ro ausserhalb [0,1]: {ro}")
    n_qubits = _basis_zwei(breite)
    if len(vec) != breite:
        raise ValueError(f"Probvektor-Länge {len(vec)} != breite {breite}")
    ergebnis: List[Fraction] = []
    for b_label in range(breite):
        masse = Fraction(0)
        for a_label, a_masse in enumerate(vec):
            if a_masse == 0:
                continue
            h = (a_label ^ b_label).bit_count()
            masse += a_masse * ro ** h * (1 - ro) ** (n_qubits - h)
        ergebnis.append(masse)
    return ergebnis


@dataclass(frozen=True)
class Kanal:
    """Ein deklarierter Kanal: Typ + Qubits + Param-Etikett.

    typ zulaessig: "depolarisiert" | "abklingen" | "dephasieren" |
    "auslese". auslese verlangt qubits=None (wirkt auf alle Qubits).
    """

    typ: str
    param: Param
    qubits: Optional[Tuple[int, ...]] = None

    def __post_init__(self) -> None:
        if self.typ not in ("depolarisiert", "abklingen", "dephasieren",
                            "auslese"):
            raise ValueError(
                f"unbekannter Kanal-Typ {self.typ!r}; zulaessig: "
                "depolarisiert | abklingen | dephasieren | auslese"
            )
        if self.typ == "auslese" and self.qubits is not None:
            raise ValueError(
                "auslese wirkt auf alle Register-Qubits; qubits=None setzen"
            )
        if self.typ in ("depolarisiert", "abklingen") and \
                self.qubits is not None:
            if len(self.qubits) == 0:
                raise ValueError(f"{self.typ} verlangt.qubits nicht-leer")


def apply_to_probs_diag(
    p_vektor: Sequence[object], kanal: Kanal, breite: int
) -> List[Fraction]:
    """EXAKTER Diagonal-Zweig: Kanal auf Wahrscheinlichkeits-Vektor anwenden.

    Fraction-Pflicht auf BEIDEN Seiten (Vektor UND Parameter) — ein
    float-Param wirft hier bewusst (der Float-Schicht-Pfad ist der
    abgeleite Weg, nicht dieser).
    """
    if not isinstance(kanal.param.wert, Fraction):
        raise ValueError(
            f"float-Param {kanal.param.name!r} im EXAKT-Zweig — "
            "ganzrationalen Parameter übergeben oder den Float-Pfad benutzen"
        )
    if kanal.typ == "depolarisiert":
        return depolarisiert_probs(p_vektor, kanal.param.wert, breite,
                                   kanal.qubits)
    if kanal.typ == "abklingen":
        return abklingen_probs(p_vektor, kanal.param.wert, breite,
                               kanal.qubits)
    if kanal.typ == "dephasieren":
        return dephasieren_probs(p_vektor, kanal.param.wert, breite)
    return auslese_probs(p_vektor, kanal.param.wert, breite)


def verkette_diag(
    p_vektor: Sequence[object],
    kanaele: Sequence[Kanal],
    breite: int,
) -> List[Fraction]:
    """Kette von Kanälen auf dem Wahrscheinlichkeits-Vektor (linksauffasend).

    Initiale Konvertierung läuft über _probvektor_normieren (Fraction-Pflicht
    + Summe-1-Waechter) — kein stiller Fraction(float)-Durchlass.
    """
    vec: List[Fraction] = _probvektor_normieren(p_vektor)
    for k in kanaele:
        vec = apply_to_probs_diag(vec, k, breite)
    return vec


# --- Float-Schicht (Kraus-Darstellung; ABGELEITET-Werkzeug) -----------------

_PAULIS_1Q = {
    "I": np.array([[1, 0], [0, 1]], dtype=complex),
    "X": np.array([[0, 1], [1, 0]], dtype=complex),
    "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
    "Z": np.array([[1, 0], [0, -1]], dtype=complex),
}


def kraus_depolarisiert(
    lambda_wert: float, anzahl_qubits: int
) -> List[np.ndarray]:
    """Depolarisierender Kanal als Pauli-Kraus-Satz.

    E(rho) = (1-lambda)*rho + lambda*I/2^n:
    K_I = sqrt(1 - lambda*(1 - 4^-n)) * I;  K_P = sqrt(lambda)/2^n * P.
    (Ableitung: sum_P P rho P^dagger = d*I fuer die Pauli-Strings des
    Raums, also (lambda/d^2)*sum_{P!=I} = (lambda/d^2)*(d*I - rho).)

    lambda ist der KANAL-Parameter (Gewicht der vollstaendigen Vermischung),
    nicht der Pauli-Stichproben-Anteil — beide Lesarten treffen sich hier
    exakt in der Formel.
    """
    if not 0.0 <= lambda_wert <= 1.0:
        raise ValueError(f"lambda ausserhalb [0,1]: {lambda_wert}")
    if anzahl_qubits < 1:
        raise ValueError(f"anzahl_qubits muss >= 1 sein, erhalten {anzahl_qubits}")
    dim = 1 << anzahl_qubits
    c_i = 1.0 - lambda_wert * (1.0 - 1.0 / (dim * dim))
    kraus_ops: List[np.ndarray] = [np.sqrt(c_i) * np.eye(dim, dtype=complex)]
    for symbole in itertools.product("IXYZ", repeat=anzahl_qubits):
        if all(s == "I" for s in symbole):
            continue
        kraus_ops.append(np.sqrt(lambda_wert) / dim
                         * _pauli_string(symbole))
    return kraus_ops


def _pauli_string(symbole: Sequence[str]) -> np.ndarray:
    """Pauli-String-Matrix elementweise: lokal bit k <-> symbole[k].

    M[a, b] = Produkt_k P_k[a_k, b_k] — dieselbe Bit-Konvention wie die
    Qubit-Platzierung in apply_kraus (lokal bit k laeuft auf dem k-ten
    Qubit der Kanal-Liste); kein np.kron-Ordungs-Stolpern.
    """
    dim_r = 1 << len(symbole)
    matrix = np.zeros((dim_r, dim_r), dtype=complex)
    for a in range(dim_r):
        for b in range(dim_r):
            eintrag = 1.0 + 0j
            for k, s in enumerate(symbole):
                p_mat = _PAULIS_1Q[s]
                eintrag = eintrag * p_mat[(a >> k) & 1, (b >> k) & 1]
            matrix[a, b] = eintrag
    return matrix


def kraus_abklingen(gamma_wert: float) -> List[np.ndarray]:
    """Amplituden-Daempfung 1q: K0 = diag(1, sqrt(1-gamma)); K1 = [[0, sqrt(gamma)], [0, 0]]."""
    if not 0.0 <= gamma_wert <= 1.0:
        raise ValueError(f"gamma ausserhalb [0,1]: {gamma_wert}")
    k0 = np.array([[1.0 + 0j, 0], [0, np.sqrt(1.0 - gamma_wert) + 0j]])
    k1 = np.array([[0, np.sqrt(gamma_wert) + 0j], [0, 0]])
    return [k0, k1]


def kraus_dephasieren(gamma_phi_wert: float) -> List[np.ndarray]:
    """Reine Dephasierung 1q: K0 = sqrt(1-gamma_phi)*I; K1 = sqrt(gamma_phi)*Z.

    Off-Diagonale werden mit (1 - 2*gamma_phi) multipliziert; Diagonale bleibt
    EXAKT unangetastet (Diagonal-Abschluss-Theorem, Float-Pfad bitweise).
    """
    if not 0.0 <= gamma_phi_wert <= 1.0:
        raise ValueError(f"gamma_phi ausserhalb [0,1]: {gamma_phi_wert}")
    k0 = np.sqrt(1.0 - gamma_phi_wert) * _PAULIS_1Q["I"]
    k1 = np.sqrt(gamma_phi_wert) * _PAULIS_1Q["Z"]
    return [k0, k1]


def relaxation_wahrscheinlichkeiten(
    t1: float, t2: float, t_dauer: float, gleichgewicht_p1: float = 0.0
) -> Tuple[float, float, float]:
    """Populations-Affine + Kohaerenzfaktor der thermischen Relaxation.

    p1(t) = e^(-t/T1) * p1(0) + (1 - e^(-t/T1)) * gleichgewicht_p1;
    Kohaerenzfaktor = e^(-t/T2). Rueckgabe (a_dd, offset, kohaerenzfaktor)
    mit new_p1 = a_dd * p1 + offset. NUR Float-Pfad (transzendente
    Exponential-Auswertung); der volle Kraus-Satz fuer T2 > T1 ist
    NICHT implementiert (KNOWN_GAP). T2 > 2*T1 verletzt die
    Vollstaendigkeits-Bedingung (CP-Grenze) und wird verweigert.
    """
    if t1 <= 0 or t2 <= 0 or t_dauer < 0:
        raise ValueError(
            f"T1/T2 muessen > 0 sein, t_dauer >= 0 (erhalten "
            f"T1={t1}, T2={t2}, t={t_dauer})"
        )
    if t2 > 2.0 * t1:
        raise ValueError(
            f"T2 > 2*T1 verletzt die CP-Grenze (erhalten T2={t2}, T1={t1})"
        )
    a_dd = math.exp(-t_dauer / t1)
    koh = math.exp(-t_dauer / t2)
    offset = (1.0 - a_dd) * gleichgewicht_p1
    return a_dd, offset, koh


def auslese_verwirrung(ro_wert: float, nq: int) -> np.ndarray:
    """Auslese-Verwirrungsmatrix 2^nq x 2^nq (klassisch, symmetrisch 1q).

    M[a, b] = ro^Hamming(a, b) * (1 - ro)^(nq - Hamming(a, b));
    Zeilen-Summen 1. Label-Konvention wie ueberall: bit i == Qubit i.
    """
    if not 0.0 <= ro_wert <= 1.0:
        raise ValueError(f"ro ausserhalb [0,1]: {ro_wert}")
    nq = int(nq)
    if nq < 1:
        raise ValueError(f"nq muss >= 1 sein, erhalten {nq}")
    dim = 1 << nq
    matrix = np.zeros((dim, dim))
    for a_label in range(dim):
        for b_label in range(dim):
            h = (a_label ^ b_label).bit_count()
            matrix[a_label, b_label] = (
                ro_wert ** h * (1.0 - ro_wert) ** (nq - h)
            )
    return matrix


def rho_diag(p_vektor: Sequence[float]) -> np.ndarray:
    """Diagonale Dichtematrix aus Wahrscheinlichkeits-Vektor (float)."""
    arr = np.asarray(list(p_vektor), dtype=complex)
    if np.abs(arr.imag).max() > 0:
        raise ValueError("rho_diag verlangt reellen Wahrscheinlichkeits-Vektor")
    matrix = np.zeros((arr.size, arr.size), dtype=complex)
    matrix[np.arange(arr.size), np.arange(arr.size)] = arr.real
    return matrix


def kohärenz_max(rho: np.ndarray) -> float:
    """Maximaler Betrag der Nicht-Diagonal-Eintraege (Theorem-Diagnostik)."""
    matrix = np.asarray(rho)
    n = matrix.shape[0]
    maske = ~np.eye(n, dtype=bool)
    return float(np.abs(matrix[maske]).max())


def _platz_bits(i: int, qubits_l: Sequence[int]) -> int:
    """Lokaler Kanal-Index i (bit k) -> globale Bits an Qubits q[k]."""
    anteil = 0
    for k, q in enumerate(qubits_l):
        if (i >> k) & 1:
            anteil |= 1 << q
    return anteil


def apply_kraus(
    rho: np.ndarray,
    kraus_ops: Sequence[np.ndarray],
    qubits: Sequence[int],
) -> np.ndarray:
    """Anwendung eines Kraus-Satzes auf die genannten Qubits von rho.

    rho' = sum_k (K_k (x) I_rest) rho (K_k (x) I_rest)^dagger.
    Bit-Konvention: Label bit i == Qubit i (LSB = Qubit 0, wie in den
    Count-Labels); lokal bit k des Kraus-Operators laeuft auf Qubit
    q[k] der Kanal-Liste. Implementierung via Label-Loop ueber
    (Rest-Label, Kanal-Label) — N <= 6 bewusst gewaehlt, Klarheit vor
    Geschwindigkeit.
    """
    matrix = np.asarray(rho, dtype=complex)
    dim = matrix.shape[0]
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError("rho muss quadratisch sein")
    n_qubits_gesamt = _basis_zwei(dim)
    kanal_qubits = [int(q) for q in qubits]
    if len(kanal_qubits) != len(set(kanal_qubits)):
        raise ValueError(f"doppelte Qubits: {kanal_qubits}")
    if not all(0 <= q < n_qubits_gesamt for q in kanal_qubits):
        raise ValueError(
            f"Qubits {kanal_qubits} ausserhalb 0..{n_qubits_gesamt - 1}"
        )
    dim_r = 1 << len(kanal_qubits)
    for op in kraus_ops:
        op_arr = np.asarray(op, dtype=complex)
        if op_arr.shape != (dim_r, dim_r):
            raise ValueError(
                f"Kraus-Operator hat Form {op_arr.shape}, "
                f"verlangt ({dim_r}, {dim_r}) fuer Qubits {kanal_qubits}"
            )
    maske_kanal = 0
    for q in kanal_qubits:
        maske_kanal |= 1 << q
    rest_qubits = [q for q in range(n_qubits_gesamt) if q not in kanal_qubits]
    platzierung = [_platz_bits(i, kanal_qubits) for i in range(dim_r)]
    platzierung_rest = [
        _platz_bits(i, rest_qubits) for i in range(dim >> len(kanal_qubits))
    ]
    ergebnis = np.zeros_like(matrix)
    sub = np.zeros((dim_r, dim_r), dtype=complex)
    for k_op in kraus_ops:
        for rest_label in range(dim >> len(kanal_qubits)):
            rest_basis = platzierung_rest[rest_label]
            # sub[i, j] = rho[rest | platzierung(i), rest | platzierung(j)]
            for i in range(dim_r):
                a_label = rest_basis | platzierung[i]
                for j in range(dim_r):
                    b_label = rest_basis | platzierung[j]
                    sub[i, j] = matrix[a_label, b_label]
            transformed = k_op @ sub @ k_op.conj().T
            for i in range(dim_r):
                a_label = rest_basis | platzierung[i]
                for j in range(dim_r):
                    b_label = rest_basis | platzierung[j]
                    ergebnis[a_label, b_label] += transformed[i, j]
    return ergebnis


# --- ChannelModel aus ISA-Op-Counts (V12) -----------------------------------

_TOR_FAMILIEN: Dict[str, str] = {
    "rz": "virtuell",
    "sx": "1q", "x": "1q", "y": "1q", "z": "1q", "h": "1q",
    "s": "1q", "sdg": "1q", "t": "1q", "tdg": "1q", "id": "1q",
    "rzx": "2q", "cz": "2q", "cx": "2q", "ecr": "2q", "swap": "2q",
    "measure": "auslese",
    "barrier": "keins",
}


def herkunft_vererbt(quellen: Sequence[Param], ausdruck: str) -> str:
    """Herkunfts-Etikett eines abgeleiteten Werts = SCHWAECHESTE Eingabe.

    Eine geschätzt-Eingabe macht den abgeleiteten Wert zu einer markierten
    Hypothese (Klasse GESAMPFELT); nur kalibriert+/abgeleitet-Eingaben
    liefern "abgeleitet" (ABGELEITET). EXAKT-Eingaben erben auf diesem
    Pfad KEINE EXAKT-Klasse — kein stiller Aufwaerts-Schritt; die EXAKT-
    Klasse des Op-COUNTS-Modells deklariert sich separat (alle Params
    exakt-definiert -> Modell EXAKT).
    """
    if any(p.herkunft.startswith("geschätzt:") for p in quellen):
        return f"geschätzt:{ausdruck} — Klasse der schwaechsten Eingabe"
    return "abgeleitet"


def _p_eff(k: int, p: Fraction) -> Fraction:
    """Effektive Fehler-Wahrscheinlichkeit von k unabhaengigen Anwendungen:
    p_eff = 1 - (1-p)^k — ganzrational EXAKT (ganzzahlige Potenzen)."""
    if k < 0:
        raise ValueError(f"k muss >= 0 sein, erhalten {k}")
    if not 0 <= p <= 1:
        raise ValueError(f"p ausserhalb [0,1]: {p}")
    return 1 - (1 - p) ** k


@dataclass(frozen=True)
class ChannelModel:
    """Komposition der ISA-Op-COUNTS zu effektiven Kanal-Werten (EXAKT-Form).

    p_1q_eff = 1-(1-p_1q)^(#1q), p_2q_eff = 1-(1-p_2q)^(#2q) als Fraction;
    p_2q kann direkt als Param kommen oder via p_1q*ratio_2q (dann mit
    Verkettungs-Schutz: Klasse = min der beiden Param-Klassen).
    """

    ops: Dict[str, int]
    fam_zuehler: Dict[str, int]
    p_1q_eff: Fraction
    p_2q_eff: Fraction
    params: Dict[str, Param]

    def garantie(self) -> Guarantee:
        """Mindest-Klassen-Etikett der Komposition (keine Aufwaerts-Wanderung).

        Die Klasse des komponierten Wertes ist die SCHWAECHESTE Param-Klasse
        (geschätzt -> GESAMPFELT; sonst kalibriert/abgeleitet -> ABGELEITET;
        nur alle-EXAKT heisst EXAKT + herkunft "exakt-definiert" — die
        Op-COUNTS sind registrierte Struktur, keine Geraete-Eichung).
        pruefe_verkettung läuft danach als Guard: jede künftige
        Klassen-Herbung knallt hier, nicht still.
        """
        eingaben = [p.garantie() for p in self.params.values()]
        rang_min = min(klasse_rang(g.klasse) for g in eingaben)
        quelle = "ISA-Op-Counts + Params " + ";".join(sorted(self.params))
        if rang_min >= klasse_rang("EXAKT"):
            ausgabe = Guarantee(
                klasse="EXAKT", herkunft="exakt-definiert", grenze=None,
                quelle=quelle,
            )
        else:
            name_klasse = next(
                name for name in ("GESAMPFELT", "ABGELEITET")
                if klasse_rang(name) == rang_min
            )
            ausgabe = Guarantee(
                klasse=name_klasse, herkunft="abgeleitet", grenze=None,
                quelle=quelle,
            )
        pruefe_verkettung(ausgabe, eingaben)
        return ausgabe

    def als_json(self) -> dict:
        return {
            "ops": dict(self.ops),
            "fam_zuehler": dict(self.fam_zuehler),
            "p_1q_eff": f"{self.p_1q_eff}",
            "p_2q_eff": f"{self.p_2q_eff}",
            "params": {
                name: {
                    "wert": f"{p.wert}" if isinstance(p.wert, Fraction)
                    else repr(p.wert),
                    "herkunft": p.herkunft,
                    "quelle": p.quelle,
                }
                for name, p in sorted(self.params.items())
            },
            "garantie": self.garantie().als_json(),
        }

    @classmethod
    def aus_op_counts(
        cls,
        ops: Mapping[str, int],
        params: Mapping[str, Param],
    ) -> "ChannelModel":
        """Op-COUNTS-Dict des committeten ISA-Reports -> Modell (V12).

        Unbekannte Op-Namen werfen ValueError (deklarierte Registrierung,
        kein stiller Fall-Durchlass). rz/measure/barrier tragen keinen
        Gate-Fehler; 1q/2q-Zaehler treiben p_eff.
        """
        ops_neu = {name: int(wert) for name, wert in ops.items()}
        for name, wert in ops_neu.items():
            if name not in _TOR_FAMILIEN:
                raise ValueError(
                    f"unbekannter ISA-Op-Name {name!r} — Registrierung in "
                    "_TOR_FAMILIEN nötig, kein stiller Durchlass"
                )
            if wert < 0:
                raise ValueError(f"negativer Op-Count {name}={wert}")
        fam_zuehler: Dict[str, int] = {}
        for name, wert in ops_neu.items():
            fam = _TOR_FAMILIEN[name]
            fam_zuehler[fam] = fam_zuehler.get(fam, 0) + wert
        n_1q = fam_zuehler.get("1q", 0)
        n_2q = fam_zuehler.get("2q", 0)

        p_1q_param = params.get("p_1q")
        if p_1q_param is None:
            raise ValueError("params verlangt p_1q (1q-Gate-Fehler-Rate)")
        if n_1q == 0:
            raise ValueError(
                "ISA-Report ohne 1q-Tore: p_1q_eff undefiniert — Modell "
                "ohne 1q-Anteil nicht konstruierbar (Ops: " + repr(dict(ops)) + ")"
            )
        if isinstance(p_1q_param.wert, Fraction) is False:
            raise ValueError(
                "p_1q muss ganzrational sein (EXAKT-Zweig) — float-Params "
                "gehören in die ABGELEITET-Schicht mit eigenem Etikett"
            )
        p_1q_eff = _p_eff(n_1q, p_1q_param.wert)

        if "p_2q" in params:
            p_2q_param = params["p_2q"]
            if not isinstance(p_2q_param.wert, Fraction):
                raise ValueError(
                    "p_2q muss ganzrational sein (EXAKT-Zweig)"
                )
            anteil_2q = p_2q_param
        elif "p_1q" in params and "ratio_2q" in params:
            ratio_param = params["ratio_2q"]
            if not isinstance(ratio_param.wert, Fraction):
                raise ValueError("ratio_2q muss ganzrational sein (EXAKT-Zweig)")
            anteil_2q = Param(
                name="p_2q_abgeleitet",
                wert=p_1q_param.wert * ratio_param.wert,
                herkunft=herkunft_vererbt(
                    (p_1q_param, ratio_param), "p_1q*ratio_2q"),
                quelle=(f"p_1q({p_1q_param.herkunft}) * "
                        f"ratio_2q({ratio_param.herkunft})"),
            )
            # Verkettungs-Schutz: Klasse p_2q nie ueber min der beiden:
            pruefe_verkettung(
                anteil_2q.garantie(),
                [p_1q_param.garantie(), ratio_param.garantie()],
            )
        else:
            raise ValueError(
                "params verlangt p_2q ODER (p_1q + ratio_2q) für 2q-Komposition"
            )
        p_2q_eff = _p_eff(n_2q, anteil_2q.wert)

        benutzt = {"p_1q": p_1q_param, "p_2q": anteil_2q}
        for zusatz in ("ratio_2q", "ro"):
            if zusatz in params:
                benutzt[zusatz] = params[zusatz]
        return cls(
            ops=ops_neu,
            fam_zuehler=fam_zuehler,
            p_1q_eff=p_1q_eff,
            p_2q_eff=p_2q_eff,
            params=benutzt,
        )