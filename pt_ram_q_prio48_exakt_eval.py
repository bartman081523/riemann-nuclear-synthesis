#!/usr/bin/env python3
"""Gefrorene Auswertung EXPERIMENT 055c — pt_ram_q_prio48_exakt_eval.py.

Wendet NUR die im Prereg pt_ram_q_prio48_exakt_prereg.json (SHA-256-Freeze,
REGISTERED_NOT_MEASURED, Freeze-Commit 0a66007) deklarierten Schwellen
T1-T4 an und traegt die Verdicts H-055C-1..4.  Liest ausschliesslich
committete Artefakte:

 - pt_ram_q_prio48_sv_raw.json        (055b-Quelle, dual gepinnt)
 - pt_ram_q_prio48_sv_isa_report.json (Op-COUNTS, NON-verdict-Meta)
 - pt_ram_q_prio48_exakt_raw.json     (Roh-Commit 4c6cc57 VOR Auswertung)
 - pt_ram_q_prio48_exakt.py           (NUR als Daten-Artefakt: Blob-Sha
   gegen den Freeze-Commit verifiziert, damit die hier transkribierten
   NC-Modell-Konstanten genau die gefrorenen sind — kein Import, kein
   Aufruf des Runners).

Second-Path-Disziplin: alle Statistik-Funktionen (Sieb, Restklassen,
Label-Parse, mod-d/mod-q-Folds, TV, Quote-Kette, Punkt-Konstanten,
Binomial-Walk, frak_pin, FFT/Faltform-Spiegel) sind HIER eigen
implementiert — kein primequant-Import, kein Runner-Import; Identitaet
zum committeten Raw wird Feld fuer Feld BIT-EXAKT verglichen. numpy nur
ABGELEITED-FFT-Schatten, nie Quelle.  Kein Seed, kein qiskit, kein
Token, keine QPU-Anbindung.
"""

import hashlib
import json
import math
import platform
import re
import subprocess
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

import numpy                    # ABGELEITED-FFT/Faltform-Schatten only

REPO = Path(__file__).resolve().parent

PREREG_P = "pt_ram_q_prio48_exakt_prereg.json"
SV_RAW_NAME = "pt_ram_q_prio48_sv_raw.json"
SV_PREREG_NAME = "pt_ram_q_prio48_sv_prereg.json"
ISA_P = "pt_ram_q_prio48_sv_isa_report.json"
ROH_P = "pt_ram_q_prio48_exakt_raw.json"
EVAL_P = "pt_ram_q_prio48_exakt_eval.json"
RUNNER_P = "pt_ram_q_prio48_exakt.py"

FREEZE_COMMIT = "0a66007"
RAW_COMMIT = "4c6cc57"

# ---- Gefrorene Schwellen T1-T4 (verbatim aus dem Prereg) ----
T1_TEXT = ("fuer alle 45 Delta-Reihen tv == '0' exakt (Fraction(0)) — "
           "Delta-Saettigung erwartet, V8")
T2_TEXT = ("fuer alle 111 struct-rows: |anteil_flt_falt − fft_share_float| "
           "≤ 2·math.ulp(anteil_flt_falt) — ABS-FFT rundet je Term "
           "(komplexes Summen-Netz), V6 mass 1 ULP")
T3_P_TEXT = ("p_wert_zweiseitig ≥ 1/240 (q3-Bein) beziehungsweise ≥ 1/400 "
             "(q5-Bein) je Label, zweiseitig gegen p_a = n_a/m")
T3_TV_TEXT = "tv ≤ 1/50 pro negative Kontrolle"
T4_TEXT = ("fuer alle 111 struct-rows: faltform_float == anteil_flt_falt "
           "bit-identisch — dyadisch-exakter Zaehler, genau EINE Rundung "
           "⇒ IEEE einzig-korrekt-gerundet")

T3_TV = Fraction(1, 50)
T3_ALPHA = {"q3_d3": Fraction(1, 240), "q5_d5": Fraction(1, 400)}

TALLY = {
    "structure": 39, "loschmidt": 13, "echo_ladder": 6,
    "kalibrier_structure": 72, "kalibrier_loschmidt": 24,
    "negative_control": 4, "readout_cal": 2,
}
ROW_KEYS = {"P", "arm", "counts", "kind", "name", "r", "rep", "set",
            "shots_actual"}
BASE_KEYS = ("name", "kind", "arm", "set", "P", "rep", "r", "shots_actual")
DELTA_ARTEN = ("loschmidt", "kalibrier_loschmidt", "echo_ladder",
               "readout_cal")
STRUKT_ARTEN = ("structure", "kalibrier_structure")

# ---- Garantie-Kataloge (verbatim aus dem gefrorenen Runner; die eval
# prueft die Raw-Kopie STRICT auf Gleichheit; quelle wird je Lauf aus dem
# Prereg-Pin eingesetzt) ----
GAR_STRUKTUR = {
    "klasse": "EXAKT",
    "exakt": ["n_hut_klassen", "N_hut", "m_hat",
              "q_sum_N_sq_minus_m2", "anteil_falt", "anteil_modell",
              "quote"],
    "abgeleitet": ["anteil_flt_falt", "quote_flt", "fft_share_float",
                   "fft_quote_float", "delta_fft", "delta_fft_ulp",
                   "delta_quote", "delta_quote_ulp", "faltform_float"],
    "grenze": "T1-T4-Schwellen nur in der gefrorenen Auswertung "
              "(pt_ram_q_prio48_exakt_eval.py)",
    "quelle": None,
}
GAR_DELTA = {
    "klasse": "EXAKT",
    "exakt": ["tv", "modell", "massa_label0"],
    "abgeleitet": [],
    "grenze": "T1-Schwelle nur in der gefrorenen Auswertung",
    "quelle": None,
}
GAR_KONTR = {
    "klasse": "EXAKT",
    "exakt": ["tv", "modell", "p_werte_pin"],
    "abgeleitet": [],
    "grenze": "T3-Schwelle nur in der gefrorenen Auswertung",
    "quelle": None,
}
GAR_KAL = {
    "klasse": "EXAKT",
    "exakt": ["tv", "modell", "rand_flip_anteile"],
    "abgeleitet": [],
    "grenze": "T1-Reihe (readout_cal ist DELTA_REIHENART)",
    "quelle": None,
}

# ---- NC-Modell-Deklarationen (transkribiert aus dem gefrorenen Runner,
# Zeile 75-91 @ FREEZE_COMMIT; E0 beweist die Byte-Identitaet mit dem
# Freeze-Commit, die TV-/p-Pin-Vergleiche fangen jede Transkriptions-
# Divergenz bit-exakt.  Composite = deklarierte n_d/m; uniform = Klassen-
# Ebene [1/q] mit Auffuellung auf Registerbreite.) ----
NC_N_D = {
    "ctrl_composite_P181_d3": ((19, 13, 10), 42),
    "ctrl_uniform_q3": None,
    "ctrl_composite_P467_d5": ((23, 18, 17, 15, 18), 91),
    "ctrl_uniform_q5": None,
}
NC_TV_PINS = {
    "ctrl_composite_P181_d3": Fraction(551, 86016),
    "ctrl_uniform_q3": Fraction(79, 24576),
    "ctrl_composite_P467_d5": Fraction(835, 106496),
    "ctrl_uniform_q5": Fraction(31, 2560),
}

# ---- Erste-Struktur-Reihe Quote-Pins (verbatim gefrorener Runner,
# Zeile 64-70: live verifiziert 2026-10-06 vor dem Freeze) ----
ERSTE = {"name": "struct_q3_d3_181_r0",
         "n_hut": ["3969/4096", "19761/1024", "89019/4096"],
         "m_hat": "42", "q_sum": "6484629375/8388608",
         "anteil_falt": "102930625/16777216", "anteil_modell": "169/28",
         "quote": "720514375/708837376",
         "anteil_flt_falt": 6.135143339633942,
         "quote_flt": 1.0164734527204164}


class EvalAbbruch(RuntimeError):
    """Verifikation-Schritt divergiert — Auswertung bricht ab (kein Verdict)."""


# =================================================================
# EIGENE Second-Path-Implementierungen (kein primequant/Runner-Import)
# =================================================================

def eigen_sieb(n: int):
    """Eratosthenes: alle p mit 2 <= p <= n, aufsteigend (exakt)."""
    if n < 2:
        return []
    ist = [True] * (n + 1)
    ist[0] = ist[1] = False
    p = 2
    while p * p <= n:
        if ist[p]:
            for v in range(p * p, n + 1, p):
                ist[v] = False
        p += 1
    return [i for i, ok in enumerate(ist) if ok]


def eigen_restklassen(P: int, d: int):
    """n_r = #{p <= P: p ≡ r (mod d)}, r = 0..d-1 (exakte Zaehlung)."""
    z = [0] * d
    for p in eigen_sieb(P):
        z[p % d] += 1
    return z


def eigen_register_breite(d: int):
    """(nq, 2^nq) — kleinste Potenz von zwei >= d (exakt)."""
    nq, breite = 0, 1
    while breite < d:
        breite *= 2
        nq += 1
    return nq, breite


def eigen_label_int(bits: str) -> int:
    """Kanonischer Label-Parse: int(bits.replace(' ', ''), 2)."""
    return int(bits.replace(" ", ""), 2)


def eigen_zaehlung_auf_labels(counts, breite):
    """Counts-Dict -> voller Label-Vektor ueber 0..breite-1 (exakt)."""
    vek = [0] * breite
    for bits, masse in counts.items():
        label = eigen_label_int(bits)
        if not 0 <= label < breite:
            raise EvalAbbruch(
                "label %r ausserhalb Breite %d" % (bits, breite))
        if isinstance(masse, bool) or int(masse) != masse or masse < 0:
            raise EvalAbbruch("Count-Masse %r ungueltig" % (masse,))
        vek[label] += int(masse)
    return vek


def eigen_exakte_masse_am_label(counts, label):
    """Beobachtete Masse EXAKT am Label-Int (Identitaet-Bitordnung)."""
    gesamt = 0
    for bits, masse in counts.items():
        if eigen_label_int(bits) == label:
            gesamt += int(masse)
    return gesamt


def eigen_tv(counts, modell):
    """TV = (1/(2S))·Σ_a |c_a − S·p_a| — exakt (Fraction), eigene Guards."""
    modell_vek = [Fraction(p) for p in modell]
    if sum(modell_vek) != 1:
        raise EvalAbbruch("Modell-Summe != 1")
    S = sum(int(v) for v in counts.values())
    if S <= 0:
        raise EvalAbbruch("Counts-Summe <= 0")
    max_label = -1
    massen = {}
    for bits, masse in counts.items():
        if isinstance(masse, bool) or int(masse) != masse or masse < 0:
            raise EvalAbbruch("Count-Masse ungueltig bei %r" % (bits,))
        label = eigen_label_int(bits)
        max_label = max(max_label, label)
        massen[label] = massen.get(label, 0) + int(masse)
    breite = max(len(modell_vek), max_label + 1)
    if max_label >= breite:
        raise EvalAbbruch("Max-Label jenseits Modell-Breite")
    num = Fraction(0)
    for a in range(breite):
        masse = massen.get(a, 0)
        p = modell_vek[a] if a < len(modell_vek) else Fraction(0)
        num += abs(Fraction(masse) - Fraction(S) * p)
    return num / (2 * S)


def eigen_punkt_konstanten(P, d, q, shots):
    """Exakte Punkt-Konstanten (eigener Spiegel von punkt_konstanten).

    klassen = falt(n_d, mod q); n0 = klassen[0] MUSS 1 sein (q-Atom)."""
    prim = eigen_sieb(P)
    m = len(prim)
    if m <= 0:
        raise EvalAbbruch("keine Primzahlen <= P=%d" % P)
    n_d = eigen_restklassen(P, d)
    if sum(n_d) != m:
        raise EvalAbbruch("Restklassen-Summe %d != m %d" % (sum(n_d), m))
    klassen = []
    for r in range(q):
        klassen.append(sum(n_d[a] for a in range(r, d, q)))
    n0 = klassen[0]
    if n0 != 1:
        raise EvalAbbruch(
            "Klasse-0-Atom erwartet n0 == 1: P=%d, d=%d, n0=%d" % (P, d, n0))
    quadrat = sum(x * x for x in klassen)
    num = q * quadrat - m * m
    den = (m - q * n0) ** 2
    if den <= 0:
        raise EvalAbbruch("Nenner entartet (m == q·n0): P=%d, d=%d" % (P, d))
    # Geschlossene Form q == 3 (exakte Kreuz-Anker-Identitaet,
    # hand-verifiziert: ratio_true == 1 + 12·Δ²/(m−3)², Δ = (k1−k2)/2);
    # fuer q == 5 gibt es diese eingipflige Form nicht.
    if q == 3:
        delta_t = klassen[1] - klassen[2]
        geschlossen = Fraction(1) + Fraction(3 * delta_t * delta_t,
                                             (m - 3) ** 2)
        if geschlossen != Fraction((q - 1) * num, den):
            raise EvalAbbruch(
                "geschlossene q=3-Form != ratio_true: P=%d, d=%d, %s != %s"
                % (P, d, fstr(geschlossen),
                   fstr(Fraction((q - 1) * num, den))))
    return {
        "P": P, "d": d, "q": q, "m": m, "n_d": n_d, "N": klassen,
        "n0": n0, "num": num, "den": den,
        "ratio_true": Fraction((q - 1) * num, den),
        "share_true_reg": Fraction(num, d * m),
        "model_share_reg": Fraction(den, (q - 1) * d * m),
        "L_q": Fraction((q - 1) ** 2 * m * m, shots * den),
    }


def eigen_quote_exakt(counts, konst, shots):
    """Exakte Quote-Kette (eigener Spiegel von quote_exakt).

    labels -> n_full (Registerbreite) -> fold mod d -> n_hut = m·c/S
    -> N_hut = fold mod q -> m_hat == m Guard -> ziffer = q·ΣN² − m_hat²
    -> anteil_falt = ziffer/(d·m) -> quote = anteil_falt/anteil_modell.
    Floats nur ABGELEITED-Kreuz-Schatten (eine IEEE-Rundung)."""
    d, q, m = int(konst["d"]), int(konst["q"]), int(konst["m"])
    if d % q != 0:
        raise EvalAbbruch("Quote-Identitaet verlangt d % q == 0")
    if shots <= 0:
        raise EvalAbbruch("shots <= 0")
    _, breite = eigen_register_breite(d)
    n_full = eigen_zaehlung_auf_labels(counts, breite)
    if sum(n_full) != shots:
        raise EvalAbbruch("Counts-Summe %d != shots %d" % (sum(n_full),
                                                           shots))
    klassen_counts = [0] * d
    for label, masse in enumerate(n_full):
        klassen_counts[label % d] += masse
    n_hut = [Fraction(m * c, shots) for c in klassen_counts]
    N_hut = [sum(n_hut[a] for a in range(r, d, q)) for r in range(q)]
    m_hat = sum(N_hut)
    if m_hat != m:
        raise EvalAbbruch("Massenerhaltung: m_hat %s != m %d" % (
            fstr(m_hat), m))
    quadrat = sum(w * w for w in N_hut)
    ziffer = q * quadrat - m_hat * m_hat
    anteil_falt = Fraction(ziffer, Fraction(d) * m)
    modell = konst["model_share_reg"]
    quote = anteil_falt / modell
    return {
        "n_hut_klassen": n_hut, "N_hut": N_hut, "m_hat": m_hat,
        "ziffer": ziffer, "anteil_falt": anteil_falt,
        "anteil_modell": modell, "quote": quote,
        "anteil_flt_falt": float(anteil_falt),
        "quote_flt": float(quote),
    }


def eigen_delta_vektor(breite, label=0):
    """Delta-Modell auf vollem Register (eigenes delta_vektor)."""
    vek = [Fraction(0)] * breite
    vek[label] = Fraction(1)
    return vek


def eigen_modell_fuer_art(kind, nq):
    """Delta-Reihen-Arten -> Delta auf 0^nq (committete Konvention V8:
    alle Delta-Reihen gesaettigt auf 0^n — das Modell ist die ideale
    Verteilung, gegen die tv == 0 verlangt wird)."""
    if kind not in DELTA_ARTEN:
        raise EvalAbbruch("eigen_modell_fuer_art: keine Delta-Art " + kind)
    return eigen_delta_vektor(1 << nq, 0)


def eigen_nc_modell(name, breite):
    """Negative-Control-Modell EXAKT (deklarierte Konstanten)."""
    dekl = NC_N_D[name]
    if dekl is None:
        q = 3 if name.endswith("q3") else 5
        basis = [Fraction(1, q)] * q
    else:
        n_d, m_d = dekl
        if sum(n_d) != m_d:
            raise EvalAbbruch("deklarierter n_d widerspricht m: " + name)
        basis = [Fraction(w, m_d) for w in n_d]
    if breite < len(basis):
        raise EvalAbbruch("Modell breiter als Registerbreite %d bei %s" %
                          (breite, name))
    return basis + [Fraction(0)] * (breite - len(basis))


def eigen_frak_pin(f):
    """SHA-256-Pin ueber kanonische Fraction-Bytes — BIT-EXAKTER Spiegel
    der committed frak_pin-Konvention (Vorzeichenbyte b'+'/'-', dann b':' +
    num.to_bytes + b':' + den.to_bytes; big-endian, minimale Laenge)."""
    n, d = f.numerator, f.denominator
    vorz = b"-" if n < 0 else b"+"
    n_abs = -n if n < 0 else n
    nb = n_abs.to_bytes(max(1, (n_abs.bit_length() + 7) // 8), "big")
    db = d.to_bytes(max(1, (d.bit_length() + 7) // 8), "big")
    return hashlib.sha256(vorz + b":" + nb + b":" + db).hexdigest()


def eigen_binom_zweig(p):
    p = Fraction(p)
    if not 0 <= p <= 1:
        raise EvalAbbruch("p ausserhalb [0,1]")
    return p.numerator, p.denominator


def eigen_binom_cdf_walk(k, S, a, m):
    """Σ_{j=0..k} C(S,j)·a^j·(m−a)^(S−j) EXAKT in Zaehlerraum — Integer-
    Term-Walk mit Teilbarkeits-Assert (eigener Spiegel der committed
    binom_cdf_exakt-Regel; V7: 480× schneller als der Fraction-Walk).

    Randregeln der committed Konvention: k < 0 -> 0; k >= S -> m**S;
    a == 0 -> m**S (X identisch 0, CDF identisch 1); a == m -> 0
    (X identisch S, CDF identisch 0 fuer k < S)."""
    if k < 0:
        return 0
    if k >= S:
        return m ** S
    if a == 0:
        return m ** S
    if a == m:
        return 0
    term = (m - a) ** S
    summe = term
    for j in range(1, k + 1):
        term = term * (S - j + 1) * a
        divisor = j * (m - a)
        quotient, rest = divmod(term, divisor)
        if rest != 0:
            raise EvalAbbruch("Term-Walk Teilbarkeit verletzt bei j=%d" % j)
        term = quotient
        summe += term
    return summe


def eigen_p_wert_zweiseitig(k, S, p):
    """min(1, 2·min(P(X≤k), P(X≥k))) — registrierte zweiseitige Doppel-
    Schwanz-Konvention inklusive Grenzterme; rechter Schwanz als Spiegel
    cdf(S−k) unter Binomial(S, 1−p) exakt mit eigenem Walk."""
    k, S = int(k), int(S)
    a, m = eigen_binom_zweig(p)
    links = Fraction(eigen_binom_cdf_walk(k, S, a, m), m ** S)
    if k <= 0:
        rechts = Fraction(1)
    elif k > S:
        rechts = Fraction(0)
    else:
        spiegel = eigen_binom_cdf_walk(S - k, S, m - a, m)
        rechts = Fraction(spiegel, m ** S)
    kleiner = links if links <= rechts else rechts
    wert = 2 * kleiner
    return wert if wert < 1 else Fraction(1)


def eigen_share_hw_fft_mirror(n_d, q, d, m):
    """ABSOLUT-FFT-Konvention (Spiegel der frozen share_hw_fft — NICHT
    Import): Σ_{j=1}^{q−1} |DFT_d(n_hat)[j·d/q]|²/(d·m).  ABGELEITED-Float-
    Schatten, nie Quelle; bit-genau der Run-Ausdruck: np.fft.fft, js =
    [int(j·d/q)], Summe durch (d·m)."""
    g = numpy.fft.fft(numpy.asarray(n_d, dtype=float))
    js = [int(j * d / q) for j in range(1, q)]
    return float(sum(abs(g[j]) ** 2 for j in js) / (d * m))


def eigen_share_hw_folded_mirror(n_d, q, d, m):
    """Faltform 041-Theorem (Spiegel der frozen share_hw_folded — NICHT
    Import): (q·Σ N² − m²)/(d·m), numpy.sum BIT-IDENTISCH (keine Python-
    Sum-Assoziativitaet), EXAKT bis zur letzten Division ⇒ genau EINE
    IEEE-Rundung (T4)."""
    N = numpy.asarray(n_d, dtype=float)
    return float((q * numpy.sum(N ** 2) - m * m) / (d * m))


# =================================================================
# Serialisierungshilfen (bit-exakter Spiegel der Runner-Konvention)
# =================================================================

def fstr(f):
    """Fraction -> kanonischer String (round-trip exakt)."""
    return str(f)


def flot(x):
    """Float -> repr-String (round-trip bit-exakt)."""
    return repr(x)


def frak_sicher(f):
    """Fraction-String mit int-str-Limit-Schutz (Lektion (a) des Freeze-
    Commits — hier im eval LIVE erneut demonstriert): kleine Denoms als
    str; Denoms ab ~4300 Stellen als SHA-256-Pin ueber die kanonischen
    Fraction-Bytes."""
    try:
        s = fstr(f)
    except ValueError:
        return "PIN:" + eigen_frak_pin(f)
    if f.numerator.bit_length() + f.denominator.bit_length() > 12000:
        return "PIN:" + eigen_frak_pin(f)
    return s


def eigen_counts_payload(counts_list):
    """Bestands-Konvention anchors: json.dumps(counts_list, sort_keys=True,
    separators=(",", ":")) mit DEFAULT-ensure_ascii (Keys = Bitstrings)."""
    return json.dumps(counts_list, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def eigen_datei_sha256(pfad):
    return hashlib.sha256((REPO / pfad).read_bytes()).hexdigest()


def eigen_git_blob_sha(commit, pfad):
    """Bytes aus dem genannten Commit ziehen (git show) und hashen —
    beweist, dass die Werktree-Bytes exakt die committeten sind."""
    roh = subprocess.run(
        ["git", "show", "%s:%s" % (commit, pfad)], cwd=str(REPO),
        capture_output=True, check=True)
    return hashlib.sha256(roh.stdout).hexdigest()


def eigen_runner_pin(name):
    """Hex-Konstanten-Zuweisung aus dem FROZENEN Runner lesen (String-
    Concat moeglich); Hex-Formen werden NIEMALS transkribiert."""
    text = (REPO / RUNNER_P).read_text(encoding="utf-8")
    m = re.search(r"%s\s*=\s*(\(.+?\)|\"[^\"]+\")\n" % name, text,
                  re.DOTALL)
    teile = re.findall(r'"([0-9a-fA-F]+)"', m.group(1))
    pin = "".join(teile)
    if not 32 <= len(pin) <= 64:
        raise EvalAbbruch("Runner-Pin %s nicht lesbar" % name)
    return pin


# =================================================================
# Verifikations-Schritte (E1-E7)
# =================================================================

def schritt_prereg():
    """E1: Prereg-Bytes kanonisch + Status + beide Pins vs Freeze-Blob."""
    roh = (REPO / PREREG_P).read_bytes()
    payload = json.loads(roh.decode("utf-8"))
    kanon = json.dumps(payload, sort_keys=True, indent=1,
                       ensure_ascii=False).encode("utf-8")
    if roh != kanon:
        raise EvalAbbruch("Prereg nicht kanonisch (freeze_discipline 1)")
    if payload.get("status") != "REGISTERED_NOT_MEASURED":
        raise EvalAbbruch("Prereg-Status nicht REGISTERED_NOT_MEASURED")
    kompakt = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode("utf-8")).hexdigest()
    datei = hashlib.sha256(roh).hexdigest()
    freeze_file = eigen_git_blob_sha(FREEZE_COMMIT, PREREG_P)
    if datei != freeze_file:
        raise EvalAbbruch(
            "Prereg-Werktree-Bytes != Freeze-Blob " + FREEZE_COMMIT)
    return payload, kompakt, datei


def lade_raw_und_binde_prereg(prereg, kompakt_sha, datei_sha):
    """E0b: committetes Roh laden + Prereg-Bindung + 160-Reihen-Feld."""
    raw = json.loads((REPO / ROH_P).read_bytes().decode("utf-8"))
    raw_sha = eigen_datei_sha256(ROH_P)
    if raw_sha != eigen_git_blob_sha(RAW_COMMIT, ROH_P):
        raise EvalAbbruch("Raw-Werktree-Bytes != Roh-Commit " + RAW_COMMIT)
    bnd = raw.get("prereg", {})
    if (bnd.get("pfad") != PREREG_P
            or bnd.get("status") != "REGISTERED_NOT_MEASURED"
            or bnd.get("sha256") != kompakt_sha
            or bnd.get("file_sha256") != datei_sha):
        raise EvalAbbruch("raw['prereg']-Bindung divergiert von den "
                          "eigenen Prereg-Pins")
    kandid = [k for k, v in raw.items()
              if isinstance(v, list) and v
              and all(isinstance(x, dict) for x in v)]
    treffer = [k for k in kandid if len(raw[k]) == 160
               and all(isinstance(x.get("name"), str) and "kind" in x
                       for x in raw[k])]
    if len(treffer) != 1:
        raise EvalAbbruch("Reihen-Feld im Raw zweideutig: %r" % (treffer,))
    return raw, treffer[0]


def schritt_sv_source(prereg):
    """E2: committetes SV-Roh dual gepinnt (eigene Pfade) + Prereg-Quell-
    Pin-Kette (Rekompute == sv-dok == runner; der Prereg-Sourcepin geht
    SEPARAT als Disclosure, NICHT abortierend)."""
    pins = prereg["source_pins"]
    dok_bytes = (REPO / SV_RAW_NAME).read_bytes()
    dok = json.loads(dok_bytes.decode("utf-8"))
    if hashlib.sha256(dok_bytes).hexdigest() != \
            eigen_git_blob_sha("HEAD", SV_RAW_NAME):
        raise EvalAbbruch("SV-Roh-Werktree != committeter HEAD-Blob")
    reihen = dok["counts"]
    if (dok.get("backend") != pins["sv_backend"]
            or dok.get("fetched_at_utc") is not None
            or dok.get("n_circuits") != 160):
        raise EvalAbbruch("SV backend/fetched_at_utc/n_circuits divergiert")
    payload_md5 = eigen_counts_payload([z["counts"] for z in reihen])
    payload_sha = eigen_counts_payload(reihen)
    md5 = hashlib.md5(payload_md5).hexdigest()
    sha = hashlib.sha256(payload_sha).hexdigest()
    if md5 != pins["sv_counts_md5"]:
        raise EvalAbbruch("SV counts_md5 divergiert: " + md5)
    if sha != pins["sv_counts_payload_sha256"]:
        raise EvalAbbruch("SV counts_payload_sha256 divergiert: " + sha)

    pr5 = json.loads((REPO / SV_PREREG_NAME).read_bytes().decode("utf-8"))
    sha5 = hashlib.sha256(json.dumps(
        pr5, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode("utf-8")).hexdigest()
    runner_p5 = eigen_runner_pin("SV_PREREG_SHA256")
    kette = {"eigenrekompute": sha5, "sv_dok_top":
             dok.get("prereg_sha256"), "runner_konstante": runner_p5,
             "raw_counts_md5_source": None,
             "prereg_source_pins": pins["sv_dok_prereg_sha256"]}
    if not (len(runner_p5) == 64 and runner_p5 == sha5
            and dok.get("prereg_sha256") == sha5):
        raise EvalAbbruch("prereg-quell-pin-kette divergiert: "
                          "rekompute %s | runner %s | dok %s" %
                          (sha5[:16], runner_p5, str(
                              dok.get("prereg_sha256"))))
    typo = pins["sv_dok_prereg_sha256"] != sha5
    return reihen, kette, typo


def schritt_isa(prereg):
    """E3: ISA sha + Struktur + eigene Aggregation (ohne_arm-Bucket)."""
    pins = prereg["source_pins"]
    isa_bytes = (REPO / ISA_P).read_bytes()
    if hashlib.sha256(isa_bytes).hexdigest() != \
            eigen_git_blob_sha("HEAD", ISA_P):
        raise EvalAbbruch("ISA-Werktree != committeter HEAD-Blob")
    isa = json.loads(isa_bytes.decode("utf-8"))
    sha = hashlib.sha256(isa_bytes).hexdigest()
    if sha != pins["isa_sha256"]:
        raise EvalAbbruch("ISA-Report sha divergiert vom Pin: " + sha)
    if len(isa.get("per_circuit", {})) != 160:
        raise EvalAbbruch("ISA per_circuit != 160")
    pro = {}
    for _c, e in isa["per_circuit"].items():
        arm = e.get("arm") or "ohne_arm:" + str(e.get("kind"))
        b = pro.setdefault(arm, {"ops_gesamt": {}, "2q_tore": 0,
                                 "tiefe_max": 0, "circuits": 0})
        b["circuits"] += 1
        for op, k in e["ops"].items():
            b["ops_gesamt"][op] = b["ops_gesamt"].get(op, 0) + k
        b["2q_tore"] += int(e["n_2q"])
        b["tiefe_max"] = max(b["tiefe_max"], int(e["depth"]))
    k1q_s = {}
    for arm in pro:
        k1q = pro[arm]["ops_gesamt"].get("sx", 0) + \
            pro[arm]["ops_gesamt"].get("x", 0)
        k1q_s[arm] = k1q
    for arm in pro:
        k1q = k1q_s[arm]
        pro[arm]["1q_tore"] = k1q
        pro[arm]["p_eff_formel"] = "1-(1-p_1q_eff)^" + str(k1q)
        pro[arm]["p_1q_eff_herkunft"] = ("geschätzt:Hypothese (keine "
                                         "on-disk Kalibrierquelle, "
                                         "KNOWN_GAPS)")
    return isa, pro


def schritt_reihen_schema(reihen):
    """E4: 160 Reihen, ROW_KEYS, TALLY, shots 8192, Counts wohlgeformt."""
    if len(reihen) != 160:
        raise EvalAbbruch("Reihenzahl %d != 160" % len(reihen))
    for i, r in enumerate(reihen):
        if set(r.keys()) != ROW_KEYS:
            raise EvalAbbruch(
                "Reihe %d (%s) Keys divergieren" % (i, r.get("name")))
        if r["shots_actual"] != 8192:
            raise EvalAbbruch("Reihe %d shots_actual != 8192" % i)
        c = r["counts"]
        if not c or sum(int(v) for v in c.values()) != 8192:
            raise EvalAbbruch("Reihe %d Counts-Masse != 8192" % i)
    tally = Counter(r["kind"] for r in reihen)
    if tally != Counter(TALLY):
        raise EvalAbbruch("kinds-Tally divergiert: " +
                          json.dumps(dict(tally), sort_keys=True))


def pruefe_reihen_felder(reihen, raw_by_name):
    """E5: Feld-fuer-Feld-Rekomputation aller 160 Reihen (EIGENER zweiter
    Pfad) + bit-exakte Vergleiche gegen das committete Raw + ERSTE + NC-
    Pins + Garantie-Kataloge STRICT."""
    prot = {"gepruefte_reihen": 0, "gepruefte_felder": 0, "brueche": [],
            "erste:": None}
    konst_cache = {}
    aus = {"delta_tv": {}, "struct_detail": [], "nc_detail": []}

    def bruch(z, art, eigen, roh):
        prot["brueche"].append((z, art, str(eigen)[:160],
                                str(roh)[:160]))

    for r in reihen:
        art = r["kind"]
        name = r["name"]
        raw_z = raw_by_name[name]
        # Base-Felder laeuft der Runner direkt von der Quelle ueber
        for feld in BASE_KEYS:
            prot["gepruefte_felder"] += 1
            if raw_z.get(feld) != r.get(feld):
                bruch(name, "base:" + feld, r.get(feld), raw_z.get(feld))
        bruch0 = len(prot["brueche"])
        felder = {}

        if art in STRUKT_ARTEN:
            arm_q, arm_d = r["arm"].split("_")
            q, d = int(arm_q[1:]), int(arm_d[1:])
            if d % q != 0:
                raise EvalAbbruch("Arm %s verletzt d %% q == 0" % r["arm"])
            key = (r["P"], d, q)
            if key not in konst_cache:
                konst_cache[key] = eigen_punkt_konstanten(
                    r["P"], d, q, r["shots_actual"])
            konst = konst_cache[key]
            res = eigen_quote_exakt(r["counts"], konst, r["shots_actual"])
            m_int = int(res["m_hat"])
            n_hat_floats = [float(v) for v in res["n_hut_klassen"]]
            fft_share = eigen_share_hw_fft_mirror(n_hat_floats, q, d,
                                                  m_int)
            fft_quote = fft_share / float(res["anteil_modell"])
            faltform = eigen_share_hw_folded_mirror(n_hat_floats, q, d,
                                                    m_int)
            d_fft = abs(res["anteil_flt_falt"] - fft_share)
            d_quo = abs(res["quote_flt"] - fft_quote)
            felder = {
                "n_hut_klassen": [fstr(v) for v in res["n_hut_klassen"]],
                "N_hut": [fstr(v) for v in res["N_hut"]],
                "m_hat": fstr(res["m_hat"]),
                "q_sum_N_sq_minus_m2": fstr(res["ziffer"]),
                "anteil_falt": fstr(res["anteil_falt"]),
                "anteil_modell": fstr(res["anteil_modell"]),
                "quote": fstr(res["quote"]),
                "anteil_flt_falt": flot(res["anteil_flt_falt"]),
                "quote_flt": flot(res["quote_flt"]),
                "fft_share_float": flot(fft_share),
                "fft_quote_float": flot(fft_quote),
                "faltform_float": flot(faltform),
                "delta_fft": flot(d_fft),
                "delta_fft_ulp": flot(d_fft / math.ulp(
                    res["anteil_flt_falt"])),
                "delta_quote": flot(d_quo),
                "delta_quote_ulp": flot(d_quo / math.ulp(
                    res["quote_flt"])),
            }
            aus["struct_detail"].append({
                "name": name, "arm": r["arm"], "P": r["P"],
                "delta_fft_ulp": d_fft / math.ulp(res["anteil_flt_falt"]),
                "delta_quote_ulp": d_quo / math.ulp(res["quote_flt"]),
                "bit_identisch_faltform": faltform ==
                    res["anteil_flt_falt"]})
            if art == "structure" and name == ERSTE["name"] and \
                    prot["erste:"] is None:
                prot["erste:"] = True
                for ziel_key, feld in (
                        ("n_hut", "n_hut_klassen"), ("n_hut", "N_hut"),
                        ("m_hat", "m_hat"),
                        ("q_sum", "q_sum_N_sq_minus_m2"),
                        ("anteil_falt", "anteil_falt"),
                        ("anteil_modell", "anteil_modell"),
                        ("quote", "quote")):
                    if felder[feld] != ERSTE[ziel_key]:
                        raise EvalAbbruch(
                            "ERSTE-Pin divergiert (%s): eigen %s | pin %s"
                            % (feld, felder[feld], ERSTE[ziel_key]))
                if res["anteil_flt_falt"] != ERSTE["anteil_flt_falt"] or \
                        res["quote_flt"] != ERSTE["quote_flt"]:
                    raise EvalAbbruch("ERSTE-Float-Pin divergiert")
        elif art in DELTA_ARTEN:
            nq = max(len(k) for k in r["counts"])
            modell = eigen_modell_fuer_art(art, nq)
            tv = eigen_tv(r["counts"], modell)
            massa = eigen_exakte_masse_am_label(r["counts"], 0)
            felder = {"nq": nq, "tv": fstr(tv),
                      "modell": [fstr(v) for v in modell],
                      "massa_label0": str(Fraction(massa, 8192))}
            aus["delta_tv"][name] = tv
            if art == "readout_cal":
                flips = {}
                for i in range(nq):
                    s = 0
                    for bits, masse in r["counts"].items():
                        if (eigen_label_int(bits) >> i) & 1:
                            s += int(masse)
                    flips[str(i)] = fstr(Fraction(s, 8192))
                felder["rand_flip_anteile"] = dict(flips)
        elif art == "negative_control":
            nq, breite = eigen_register_breite(
                int(r["arm"].split("_")[1][1:]))
            modell = eigen_nc_modell(name, breite)
            tv = eigen_tv(r["counts"], modell)
            if tv != NC_TV_PINS[name]:
                raise EvalAbbruch("NC-TV-Pin divergiert bei %s: eigen %s"
                                  % (name, fstr(tv)))
            zaehl = eigen_zaehlung_auf_labels(r["counts"], breite)
            pins = {}
            for idx in range(len(modell)):
                beob = zaehl[idx] if idx < len(zaehl) else 0
                pw = eigen_p_wert_zweiseitig(beob, 8192, modell[idx])
                pins[str(idx)] = eigen_frak_pin(pw)
            felder = {"nq": nq, "tv": fstr(tv),
                      "modell": [fstr(v) for v in modell],
                      "p_werte_pin": pins}
            aus["nc_detail"].append({"name": name, "tv": fstr(tv),
                                     "p_pins": pins})
        else:
            raise EvalAbbruch("Unbekannte art: " + art)

        # Garantie-Katalog STRICT (Raw-Kopie == eval-Katalog)
        basis = {"structure": GAR_STRUKTUR,
                 "kalibrier_structure": GAR_STRUKTUR,
                 "readout_cal": GAR_KAL,
                 "negative_control": GAR_KONTR}.get(art, GAR_DELTA)
        erwat = dict(basis)
        erwat["quelle"] = ("committete 055b-Counts (%s)" %
                           SV_PIN["sv_counts_md5"])
        if json.dumps(raw_z.get("garantie"), sort_keys=True) != \
                json.dumps(erwat, sort_keys=True):
            bruch(name, "garantie", "EIGEN_KATALOG",
                  json.dumps(raw_z.get("garantie"), sort_keys=True)[:160])

        # alle eigenerzeugten Felder bit-exakt gegen das Raw
        for feld, eig in felder.items():
            prot["gepruefte_felder"] += 1
            roh = raw_z.get(feld)
            if feld not in raw_z:
                bruch(name, feld, "FEHLT_IM_RAW", "-")
                continue
            if isinstance(eig, list):
                if json.dumps(eig, sort_keys=True) != \
                        json.dumps(roh, sort_keys=True):
                    bruch(name, feld, eig, roh)
            elif isinstance(eig, dict):
                if json.dumps(eig, sort_keys=True) != \
                        json.dumps(roh, sort_keys=True):
                    bruch(name, feld, eig, roh)
            elif eig != roh:
                bruch(name, feld, eig, roh)
        if len(prot["brueche"]) == bruch0:
            prot["gepruefte_reihen"] += 1
    return prot, aus


def schritt_banned(raw):
    """E6: banned_from_raw auf Feld/Key-Ebene (alle Keys rekursiv, bindend)
    + Value-Vorkommen (disclosed, nicht verdict-tragend)."""
    worte = tuple(BANNED_WORDS)
    erg = {"key_brueche": [], "wert_vorkommen": {}}

    def walk(obj, pfad):
        if isinstance(obj, dict):
            for k, v in obj.items():
                sk = k if isinstance(k, str) else str(k)
                for w in worte:
                    if w in sk:
                        erg["key_brueche"].append(
                            ".".join(pfad + [sk]))
                walk(v, pfad + [sk])
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, pfad + [str(i)])
        elif isinstance(obj, str):
            for w in worte:
                if w in obj:
                    erg["wert_vorkommen"].setdefault(w, []).append({
                        "pfad": ".".join(pfad), "ausschnitt": obj[:100]})

    walk(raw, [])
    return erg


def schwellen(reihen, raw_by_name, aus_e5):
    """E7: T1-T4 — NUR die im Prereg deklarierten Schwellen."""
    erg = {}

    # T1: alle 45 Delta-Reihen (incl. readout_cal) tv == 0 exakt
    delta_zeilen = [(r["name"], aus_e5["delta_tv"].get(r["name"]))
                    for r in reihen if r["kind"] in DELTA_ARTEN]
    verletzt = [n for n, tv in delta_zeilen if tv != Fraction(0)]
    erg["T1"] = {"text": T1_TEXT, "n": len(delta_zeilen),
                 "verletzt_bei": verletzt,
                 "verdict": "REFUTED" if verletzt else "HELD"}

    # T2/T4: alle 111 struct-rows — gegen die BIT-verifizierten Raw-Felder
    zeilen = [r for r in reihen if r["kind"] in STRUKT_ARTEN]
    max_ulp = 0.0
    verletzt2 = None
    verletzt4 = None
    bit_ident = 0
    for r in zeilen:
        rw = raw_by_name[r["name"]]
        flt = float(rw["anteil_flt_falt"])
        d_ulp = float(rw["delta_fft_ulp"])
        if d_ulp > max_ulp:
            max_ulp = d_ulp
        if float(rw["delta_fft"]) > 2 * math.ulp(flt) and verletzt2 is None:
            verletzt2 = r["name"]
        if float(rw["faltform_float"]) != flt and verletzt4 is None:
            verletzt4 = r["name"]
        if float(rw["faltform_float"]) == flt:
            bit_ident += 1
    erg["T2"] = {"text": T2_TEXT, "n": len(zeilen),
                 "max_delta_fft_ulp": max_ulp,
                 "verletzt_bei": verletzt2,
                 "verdict": "REFUTED" if verletzt2 else "HELD"}
    erg["T4"] = {"text": T4_TEXT, "n": len(zeilen),
                 "bit_identisch": bit_ident,
                 "verletzt_bei": verletzt4,
                 "verdict": "REFUTED" if verletzt4 else "HELD"}

    # T3: je NC-Row tv ≤ 1/50 UND jeder Label-p ≥ alpha — SIMULTAN (V11)
    detail = []
    verletzt3 = None
    for r in reihen:
        if r["kind"] != "negative_control":
            continue
        rw = raw_by_name[r["name"]]
        alpha = T3_ALPHA[r["arm"]]
        tv_frac = Fraction(str(rw["tv"]))
        breite = 1 << int(rw["nq"])
        modell = eigen_nc_modell(r["name"], breite)
        zaehl = eigen_zaehlung_auf_labels(r["counts"], breite)
        min_p = None
        min_p_label = None
        for idx in range(breite):
            beob = zaehl[idx] if idx < len(zaehl) else 0
            p = eigen_p_wert_zweiseitig(beob, 8192, modell[idx])
            if eigen_frak_pin(p) != rw["p_werte_pin"][str(idx)]:
                raise EvalAbbruch("NC p-Pin divergiert %s/%d" % (
                    r["name"], idx))
            if min_p is None or p < min_p:
                min_p, min_p_label = p, idx
            if p < alpha and verletzt3 is None:
                verletzt3 = "%s/label %d (p %s < alpha %s)" % (
                    r["name"], idx, frak_sicher(p), fstr(alpha))
        if tv_frac > T3_TV and verletzt3 is None:
            verletzt3 = "%s (tv %s > 1/50)" % (r["name"], fstr(tv_frac))
        detail.append({"name": r["name"], "arm": r["arm"],
                       "tv": fstr(tv_frac), "min_p_label": min_p_label,
                       "min_p": frak_sicher(min_p),
                       "min_p_pin": eigen_frak_pin(min_p),
                       "alpha": fstr(alpha)})
    erg["T3"] = {"text": T3_P_TEXT + " | " + T3_TV_TEXT, "n": len(detail),
                 "verletzt_bei": verletzt3, "detail": detail,
                 "verdict": "REFUTED" if verletzt3 else "HELD"}
    return erg


def main():
    global BANNED_WORDS, SV_PIN
    aus = {"experiment": "055c-primequant-exakt", "hypothesis": "H-055C",
           "g_typ": "G2-EXAKT",
           "eval_status": "GEFRORENE_AUSWERTUNG (nur committete Artefakte)",
           "second_path": "kein Runner-Import, kein primequant-Import — "
                          "eigene Implementierungen; Feld-fuer-Feld "
                          "BIT-Vergleiche",
           "python_build": platform.python_version(),
           "numpy_build": numpy.__version__,
           "primequant_importiert": False,
           "qiskit_importiert": False}

    runner_sha = eigen_datei_sha256(RUNNER_P)
    if runner_sha != eigen_git_blob_sha(FREEZE_COMMIT, RUNNER_P):
        raise EvalAbbruch("Runner-Werktree-Bytes != Freeze-Blob "
                          + FREEZE_COMMIT)
    raw = json.loads((REPO / ROH_P).read_bytes().decode("utf-8"))

    prereg, kompakt_sha, datei_sha = schritt_prereg()
    raw, reihen_feld = lade_raw_und_binde_prereg(prereg, kompakt_sha,
                                                 datei_sha)
    SV_PIN = prereg["source_pins"]
    BANNED_WORDS = tuple(prereg["banned_from_raw"])
    roh_zeilen_by_name = {z["name"]: z for z in raw[reihen_feld]}

    sv_reihen, pin_kette, pin_typo = schritt_sv_source(prereg)

    cs = raw.get("counts_md5_source", {})
    cs_erg = {"pfad": cs.get("pfad") == SV_RAW_NAME,
              "counts_md5":
                  cs.get("counts_md5") == SV_PIN["sv_counts_md5"],
              "counts_payload_sha256":
                  cs.get("counts_payload_sha256") ==
                  SV_PIN["sv_counts_payload_sha256"],
              "backend": cs.get("backend") == SV_PIN["sv_backend"],
              "fetched_at_utc": cs.get("fetched_at_utc") is None,
              "dok_prereg_sha256": cs.get("dok_prereg_sha256") ==
              pin_kette["eigenrekompute"]}
    if not all(cs_erg.values()):
        raise EvalAbbruch("counts_md5_source divergiert: " +
                          json.dumps(cs_erg, sort_keys=True))
    pin_kette["raw_counts_md5_source"] = cs.get("dok_prereg_sha256")
    if pin_typo:
        aus["disclosures"] = [{
            "typ": "prereg_source_pins_prereg_laenge",
            "feld": "source_pins.sv_dok_prereg_sha256",
            "befund": ("63 Zeichen statt 64 — ein 'e' fehlt "
                       "(...33eef79... statt ...33eefe79...); "
                       "Registrierungs-Artefakt; die bindende Kette "
                       "Rekompute == sv-dok == raw-Block == Runner-Konstante"
                       " ist intakt (64-Zeichen), gefrorenes Prereg "
                       "NICHT editiert (Praezedenz Plan §9.6)")}]
    isa, eigen_aggr = schritt_isa(prereg)
    raw_isa = raw.get("isa_report", {}).get("meta_pro_arm", {})
    if json.dumps(eigen_aggr, sort_keys=True) != \
            json.dumps(raw_isa, sort_keys=True):
        raise EvalAbbruch("ISA-Aggregation eigen != raw: eigen %s | raw %s"
                          % (json.dumps(eigen_aggr, sort_keys=True)[:300],
                             json.dumps(raw_isa, sort_keys=True)[:300]))

    schritt_reihen_schema(sv_reihen)
    prot5, aus_e5 = pruefe_reihen_felder(sv_reihen, roh_zeilen_by_name)
    if prot5["brueche"] or prot5["erste:"] is not True:
        raise EvalAbbruch(
            "E5-Divergenzen: %d | erste = %r" % (len(prot5["brueche"]),
                                                 prot5["erste:"]))
    if not aus_e5["struct_detail"]:
        raise EvalAbbruch("struct_detail leer")

    e5 = {"reihen": prot5["gepruefte_reihen"],
          "felder": prot5["gepruefte_felder"], "brueche": 0,
          "erste_pin_verifiziert": True,
          "erste_reihe": ERSTE["name"],
          "max_delta_fft_ulp": max(d["delta_fft_ulp"] for d in
                                   aus_e5["struct_detail"]),
          "max_delta_quote_ulp": max(d["delta_quote_ulp"] for d in
                                     aus_e5["struct_detail"]),
          "faltform_bit_identisch": sum(1 for d in aus_e5["struct_detail"]
                                        if d["bit_identisch_faltform"])}
    aus["verification"] = {
        "E0_freeze_rahmen": {
            "freeze_commit": FREEZE_COMMIT,
            "raw_commit": RAW_COMMIT,
            "runner_blob_sha256": runner_sha,
            "prereg_file_sha256": datei_sha,
            "prereg_payload_sha256": kompakt_sha,
            "raw_sha256": eigen_datei_sha256(ROH_P),
            "sv_raw_sha256_Head": eigen_git_blob_sha("HEAD", SV_RAW_NAME),
        },
        "E1_prereg": {"status": prereg["status"],
                      "registration_utc": prereg["registration_utc"],
                      "version_regie": prereg["version_regie"],
                      "schwellwerte_payload_sha256": hashlib.sha256(
                          json.dumps(
                              prereg["schwellwerte"], sort_keys=True,
                              separators=(",", ":"),
                              ensure_ascii=False).encode(
                                  "utf-8")).hexdigest(),
                      "hypotheses_payload_sha256": hashlib.sha256(
                          json.dumps(
                              prereg["hypotheses"], sort_keys=True,
                              separators=(",", ":"),
                              ensure_ascii=False).encode(
                                  "utf-8")).hexdigest()},
        "E2_sv_source": {"pins": SV_PIN,
                         "pin_kette": pin_kette,
                         "counts_md5_source_block": cs_erg},
        "E3_isa": {"sha256": SV_PIN["isa_sha256"],
                   "per_circuit": 160,
                   "eigen_aggregation == raw": True},
        "E5_second_path": e5}

    banned = schritt_banned(raw)
    if banned["key_brueche"]:
        raise EvalAbbruch("banned_from_raw KEY-Ban verletzt: " +
                          json.dumps(banned["key_brueche"][:10]))
    aus["e6_banned"] = {"key_brueche": 0,
                        "wert_vorkommen": {w: len(v) for w, v in
                                           banned["wert_vorkommen"].items()},
                        "wert_vorkommen_detail": banned["wert_vorkommen"]}

    sch = schwellen(sv_reihen, roh_zeilen_by_name, aus_e5)
    aus["schwellen"] = sch

    verdicts = {"H-055C-1": sch["T1"]["verdict"],
                "H-055C-2": sch["T2"]["verdict"],
                "H-055C-3": sch["T3"]["verdict"],
                "H-055C-4": sch["T4"]["verdict"]}
    alle = list(verdicts.values())
    if all(v == "HELD" for v in alle):
        kern = "H-055C_KERN_ALLE_GEHALTEN"
        grace = "A-"
    elif alle.count("HELD") >= 2:
        kern = "H-055C_KERN_MIXED"
        grace = "B+"
    else:
        kern = "H-055C_KERN_NIEDERLAGE"
        grace = "C"
    aus["verdicts"] = verdicts
    aus["kern_verdict"] = {"verdict": kern, "grade_hinweis": grace}
    aus["nachtabelle"] = [{"schwelle": k, "n": v["n"],
                           "verletzt_bei": v.get("verletzt_bei"),
                           "verdict": v["verdict"]}
                          for k, v in sch.items()]
    aus["nc_detail"] = aus_e5["nc_detail"]
    (REPO / EVAL_P).write_text(json.dumps(aus, sort_keys=True, indent=1,
                                          ensure_ascii=False) + "\n",
                               encoding="utf-8")
    print("[055c-eval] OK " + json.dumps({
        "verdicts": verdicts, "kern": kern, "grade": grace,
        "T2_max_ulp": sch["T2"]["max_delta_fft_ulp"],
        "E5_reihen": e5["reihen"], "E5_felder": e5["felder"],
        "banned_werte": aus["e6_banned"]["wert_vorkommen"]},
        sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except EvalAbbruch as ab:
        print("[055c-eval] ABBRUCH: " + str(ab), file=sys.stderr)
        sys.exit(3)