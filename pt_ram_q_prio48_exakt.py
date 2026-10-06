#!/usr/bin/env python3
"""EXPERIMENT 055c — pt_ram_q_prio48_exakt (G2-EXAKT Reanalyse der committeten 055b-Reihen).

Spiegel der 055b-Runner-Struktur (pt_ram_q_prio48_sv.py), aber:

 - KEIN Simulator, KEIN Transpile, KEIN Seed, KEIN qiskit, KEIN Token-Kontakt
   (der QPU-Rohdokument wird nur GELESEN, nie neu erzeugt).
 - Quelle: das committete pt_ram_q_prio48_sv_raw.json (160 Reihen, counts_md5
   a126430cd770325e1dd8009ad84d66d9, counts_payload-SHA 289f1f4e...) plus
   committeter ISA-Report (Op-COUNTS, V12).
 - Statistik: primequant EXAKT-Schicht (int/Fraction, seed-frei); Float
   ausschliesslich als ABGELEITED-Kreuz-Schatten (FFT-/Faltform-Spiegel der
   gefrorenen Bestands-Konvention share_hw_fft / share_hw_folded), nie Quelle.
 - Kontrollen FIRST: Abbruch VOR jeder Statistik.
 - KEINE Verdict-Felder im Raw (banned_from_raw, siehe Prereg).

Die gefrorenen Schwellen (T1-T4) stehen im Prereg
pt_ram_q_prio48_exakt_prereg.json; dieser Runner berechnet nur Groessen.
Die gefrorene Auswertung pt_ram_q_prio48_exakt_eval.py applied die Schwellen
und traegt die Verdicts H-055C-1..4.
"""

import datetime
import hashlib
import json
import math
import platform
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

import primequant as pq          # EXAKT-Schicht (int/Fraction, seed-frei)
import numpy                     # ABGELEITED-Float-Schicht (FFT-Mirror only)


REPO = Path(__file__).resolve().parent
PREREG_P = "pt_ram_q_prio48_exakt_prereg.json"
SV_RAW_NAME = "pt_ram_q_prio48_sv_raw.json"
ISA_P = "pt_ram_q_prio48_sv_isa_report.json"
ROH_P = "pt_ram_q_prio48_exakt_raw.json"

# ---- Gefrorene Source-Pins (Anchor-Schicht, tests/test_primequant_anchors.py) ----
SV_COUNTS_MD5 = "a126430cd770325e1dd8009ad84d66d9"
SV_PAYLOAD_SHA256 = ("289f1f4e6c48eada9a15f1735af9739a68b2a630addc91ef"
                     "da5c9e31f76359a2")
SV_BACKEND = "AER_STATEVECTOR_LOCAL"
SV_FETCHED = None                 # sv-Roh hat kein fetched_at_utc (kalibriere-Guard)
SV_PREREG_SHA256 = ("c708d9054a325381914a1436dadaa0a2bf4d33eefe79cb2cde73"
                    "274dc0a43b2f")          # 055b R1-Prereg (Herkunfts-Kette)
ISA_SHA256 = "5b0d17a75b708d5bb9f20bc76a1e389e790dd5d4575217db161d7f0b2503dcd1"

# kinds-Tally des committeten SV-Rohs (V9)
TALLY = {
    "structure": 39, "loschmidt": 13, "echo_ladder": 6,
    "kalibrier_structure": 72, "kalibrier_loschmidt": 24,
    "negative_control": 4, "readout_cal": 2,
}
ROW_KEYS = {"P", "arm", "counts", "kind", "name", "r", "rep", "set",
            "shots_actual"}

# Erste-Struktur-Reihe Quote-Kette (Pins aus test_erste_struktur_quote_exakt,
# live verifiziert 2026-10-06 vor dem Freeze)
ERSTE = {"name": "struct_q3_d3_181_r0",
         "n_hut": ["3969/4096", "19761/1024", "89019/4096"],
         "m_hat": "42", "q_sum": "6484629375/8388608",
         "anteil_falt": "102930625/16777216", "anteil_modell": "169/28",
         "quote": "720514375/708837376",
         "anteil_flt_falt": 6.135143339633942,
         "quote_flt": 1.0164734527204164}

# Negative-Control-Modell-Deklarationen (Pins aus test_negative_control_tv_pins):
# die Composite-Kontrollen lesen n_d/m aus dem DEKLARIERTEN 055b-Prereg-Modell
# (NICHT die Mod-q-Klassen-Zahl der Primzahlen <= P).
NC_MODELL_BAUER = {
    "ctrl_composite_P181_d3":
        lambda: pq.fuele_modell(pq.exakter_probvektor([19, 13, 10], 42), 4),
    "ctrl_uniform_q3":
        lambda: pq.modell_fuer_art("negative_control", 2, q=3),
    "ctrl_composite_P467_d5":
        lambda: pq.fuele_modell(pq.exakter_probvektor(
            [23, 18, 17, 15, 18], 91), 8),
    "ctrl_uniform_q5":
        lambda: pq.modell_fuer_art("negative_control", 3, q=5),
}
NC_TV_PINS = {
    "ctrl_composite_P181_d3": Fraction(551, 86016),
    "ctrl_uniform_q3": Fraction(79, 24576),
    "ctrl_composite_P467_d5": Fraction(835, 106496),
    "ctrl_uniform_q5": Fraction(31, 2560),
}


class LaufAbbruch(RuntimeError):
    """Kontrolle gefeuert — Abbruch VOR jeder Statistik."""


def _kanon_payload_sha256(payload):
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _kanon_datei(payload):
    return json.dumps(payload, sort_keys=True, indent=1,
                      ensure_ascii=False).encode("utf-8")


def fstr(f):
    """Fraction -> kanonischer String (round-trip exakt via Fraction(str))."""
    return str(f)


def flot(x):
    """Float -> repr-String (round-trip bit-exakt)."""
    return repr(x)


def frak_pin(f):
    """SHA-256-Pin ueber kanonische Fraction-Bytes.  p-Werte gegen p_a = n_a/m
    tragen Denaenome ~42^8192 — die Decimal-Stringform stoesst an die
    int-str-Limit (4300 Ziffern), die Pin-Form bleibt verifizierbar ohne
    Expansion: num.to_bytes + b':' + den.to_bytes (Vorzeichenbyte first).

    Format: sign(0x2B/0x2D) : num : den  (big-endian, kein Overhead).
    """
    n, d = f.numerator, f.denominator
    vorz = b"-" if n < 0 else b"+"
    n = -n if n < 0 else n
    nb = n.to_bytes(max(1, (n.bit_length() + 7) // 8), "big")
    db = d.to_bytes(max(1, (d.bit_length() + 7) // 8), "big")
    return hashlib.sha256(vorz + b":" + nb + b":" + db).hexdigest()


def lade_prereg():
    """Freeze-Vergleich ERZWUNGEN am Lauf (053-Lektion): die Prereg-Datei
    auf Disk muss exakt die kanonische Serialisierung ihres Payloads sein
    und den Freeze-Status tragen."""
    pfad = REPO / PREREG_P
    roh = pfad.read_bytes()
    payload = json.loads(roh.decode("utf-8"))
    kanon = _kanon_datei(payload)
    if roh != kanon:
        raise LaufAbbruch(
            "Prereg-Datei nicht kanonisch registriert (K1-Prereg-Form "
            "verfehlt): " + PREREG_P)
    if payload.get("status") != "REGISTERED_NOT_MEASURED":
        raise LaufAbbruch(
            "Prereg-Status nicht REGISTERED_NOT_MEASURED (kein Freeze vor "
            "dem Lauf): " + str(payload.get("status")))
    return payload, _kanon_payload_sha256(payload)


def arm_zerlegen(arm):
    """'q3_d3' -> (q=3, d=3); 'q5_d5' -> (5, 5)."""
    a, b = arm.split("_")
    q = int(a[1:])
    d = int(b[1:])
    if d % q != 0:
        raise LaufAbbruch("Arm " + arm + " verletzt d %% q == 0")
    return q, d


def nq_von_arm(arm):
    q, d = arm_zerlegen(arm)
    return pq.register_breite(d)[0]


def kontrollen(prereg):
    """K1-K5: Abbruch VOR jeder Statistik.  Rueckgabe (dok, isameta, sha)."""
    # K1a: Prereg-Identitaet gegen Runner-Konstanten
    if (prereg.get("experiment") != "055c-primequant-exakt"
            or prereg.get("hypothesis") != "H-055C"
            or prereg.get("g_typ") != "G2-EXAKT"):
        raise LaufAbbruch(
            "Prereg-Identitaet divergiert von Runner-Konstanten "
            "(experiment/hypothesis/g_typ)")

    # K1b: committetes SV-Roh dualen Pin-Verifikation (Anker-Schicht)
    dok, md5 = pq.lies_committed_counts(SV_RAW_NAME)
    if md5 != SV_COUNTS_MD5:
        raise LaufAbbruch("SV-Roh counts_md5 divergiert von Pin: " + md5)
    sha = pq.payload_sha256(pq.counts_payload(dok["counts"]))
    if sha != SV_PAYLOAD_SHA256:
        raise LaufAbbruch(
            "SV-Roh counts_payload_sha256 divergiert von Pin: " + sha)
    if (dok.get("backend") != SV_BACKEND
            or dok.get("fetched_at_utc") != SV_FETCHED
            or dok.get("prereg_sha256") != SV_PREREG_SHA256):
        raise LaufAbbruch(
            "SV-Roh Backend/fetched_at_utc/prereg_sha256 divergiert von Pin")

    # K2: Reihen-Schema (V9)
    reihen = dok["counts"]
    if len(reihen) != 160:
        raise LaufAbbruch("SV-Roh Reihenzahl " + str(len(reihen)) +
                          " != 160")
    for i, r in enumerate(reihen):
        if set(r.keys()) != ROW_KEYS:
            raise LaufAbbruch(
                "Reihe " + str(i) + " (" + r["name"] +
                ") Keys divergieren von ROW_KEYS")
        if r["shots_actual"] != pq.SHOTS:
            raise LaufAbbruch(
                "Reihe " + str(i) + " (" + r["name"] +
                ") shots_actual != 8192 == pq.SHOTS")
        c = r["counts"]
        if not isinstance(c, dict) or any(
                (not isinstance(k, str))
                or (not isinstance(v, int)) or v < 0
                for k, v in c.items()):
            raise LaufAbbruch(
                "Reihe " + str(i) + " (" + r["name"] +
                ") Counts-Dict nicht wohlgeformt (str-Keys, int >= 0)")
        if sum(c.values()) != pq.SHOTS:
            raise LaufAbbruch(
                "Reihe " + str(i) + " (" + r["name"] + ") Counts-Masse != "
                "8192")
    tally = Counter(r["kind"] for r in reihen)
    if tally != Counter(TALLY):
        raise LaufAbbruch("kinds-Tally divergiert: " +
                          json.dumps(dict(tally), sort_keys=True))

    # K3: ISA-Report sha-Pin + Struktur
    isa = pq.lies_rohdokument(ISA_P)
    isa_sha = pq.datei_sha256(ISA_P)
    if isa_sha != ISA_SHA256:
        raise LaufAbbruch("ISA-Report sha256 divergiert von Pin: " + isa_sha)
    if len(isa.get("per_circuit", {})) != 160:
        raise LaufAbbruch("ISA-Report per_circuit != 160 Circuits")
    isameta = isa_aggregat(isa)

    # K4: Erste-Struktur-Reihe Quote-Kette (Phase-B-Pins, integrity)
    erste = next(r for r in reihen if r["name"] == ERSTE["name"])
    res0 = pq.quote_exakt(erste["counts"],
                          pq.punkt_konstanten(erste["P"], 3, 3))
    if [fstr(v) for v in res0["n_hut_klassen"]] != ERSTE["n_hut"]:
        raise LaufAbbruch("Erste-Reihe n_hut_klassen Pin verfehlt")
    if [fstr(v) for v in res0["N_hut"]] != ERSTE["n_hut"]:
        raise LaufAbbruch("Erste-Reihe N_hut Pin verfehlt")
    for feld, ziel in (("m_hat", ERSTE["m_hat"]),
                       ("q_sum_N_sq_minus_m2", ERSTE["q_sum"]),
                       ("anteil_falt", ERSTE["anteil_falt"]),
                       ("anteil_modell", ERSTE["anteil_modell"]),
                       ("quote", ERSTE["quote"])):
        if fstr(res0[feld]) != ziel:
            raise LaufAbbruch(
                "Erste-Reihe " + feld + " Pin verfehlt (erwartet " + ziel +
                ", erhalten " + fstr(res0[feld]) + ")")
    for feld, ziel in (("anteil_flt_falt", ERSTE["anteil_flt_falt"]),
                       ("quote_flt", ERSTE["quote_flt"])):
        if res0[feld] != ziel:
            raise LaufAbbruch(
                "Erste-Reihe " + feld + " Float-Pin verfehlt (erwartet " +
                repr(ziel) + ", erhalten " + repr(res0[feld]) + ")")

    # K5: Negative-Control-Modelle + TV-Pins (integrity)
    nc_namen = {r["name"] for r in reihen if r["kind"] == "negative_control"}
    if nc_namen != set(NC_MODELL_BAUER):
        raise LaufAbbruch(
            "Negative-Control-Namen divergieren von Modell-Deklarationen")
    for r in reihen:
        if r["kind"] != "negative_control":
            continue
        tv = pq.tv_exakt(r["counts"], NC_MODELL_BAUER[r["name"]]())
        if tv != NC_TV_PINS[r["name"]]:
            raise LaufAbbruch(
                "Negative-Control TV-Pin verfehlt fuer " + r["name"] +
                ": rekomputiert " + fstr(tv))

    return dok, isameta, isa_sha


def isa_aggregat(isa):
    """ISA-Op-COUNTS per Arm aggregieren (NON-verdict-Meta, V12)."""
    pro = {}
    for name, eintrag in isa["per_circuit"].items():
        arm = eintrag.get("arm")
        if arm is None:
            # Die zwei readout_cal-Circuits (cal_2q) trägt der ISA-Report
            # OHNE Arm (Kalibrier-Gerüst ausserhalb der Arm-Slots).
            arm = "ohne_arm:" + str(eintrag.get("kind"))
        pro.setdefault(arm, {"ops_gesamt": {}, "2q_tore": 0, "tiefe_max": 0,
                             "circuits": 0})
        e = pro[arm]
        e["circuits"] += 1
        for op, k in eintrag["ops"].items():
            e["ops_gesamt"][op] = e["ops_gesamt"].get(op, 0) + k
        e["2q_tore"] += int(eintrag["n_2q"])
        e["tiefe_max"] = max(e["tiefe_max"], int(eintrag["depth"]))
    for arm, e in pro.items():
        k1q = e["ops_gesamt"].get("sx", 0) + e["ops_gesamt"].get("x", 0)
        e["1q_tore"] = k1q
        # p_1q_eff hat keine on-disk Kalibrierquelle -> geschäft:Hypothese;
        # p_eff nur als EXAKTE Formel verankert, KEIN erfundener Wert.
        e["p_eff_formel"] = "1-(1-p_1q_eff)^" + str(k1q)
        e["p_1q_eff_herkunft"] = ("geschätzt:Hypothese (keine on-disk "
                                  "Kalibrierquelle, KNOWN_GAPS)")
    return pro


def statistics(dok):
    """Alle Reihen-Spiegel: EXAKT-Kette + ABGELEITED-Float-Schatten."""
    reihen = dok["counts"]
    aus = []
    konst_cache = {}

    Q = "committete 055b-Counts (" + SV_COUNTS_MD5 + ")"
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
        "quelle": Q,
    }
    GAR_DELTA = {
        "klasse": "EXAKT",
        "exakt": ["tv", "modell", "massa_label0"],
        "abgeleitet": [],
        "grenze": "T1-Schwelle nur in der gefrorenen Auswertung",
        "quelle": Q,
    }
    GAR_KONTR = {
        "klasse": "EXAKT",
        "exakt": ["tv", "modell", "p_werte_pin"],
        "abgeleitet": [],
        "grenze": "T3-Schwelle nur in der gefrorenen Auswertung",
        "quelle": Q,
    }
    GAR_KAL = {
        "klasse": "EXAKT",
        "exakt": ["tv", "modell", "rand_flip_anteile"],
        "abgeleitet": [],
        "grenze": "T1-Reihe (readout_cal ist DELTA_REIHENART)",
        "quelle": Q,
    }

    for r in reihen:
        kind = r["kind"]
        zeile = {"name": r["name"], "kind": kind, "arm": r["arm"],
                 "set": r["set"], "P": r["P"], "rep": r["rep"], "r": r["r"],
                 "shots_actual": r["shots_actual"]}

        if kind in ("structure", "kalibrier_structure"):
            q, d = arm_zerlegen(r["arm"])
            if (r["P"], d, q) not in konst_cache:
                konst_cache[(r["P"], d, q)] = pq.punkt_konstanten(
                    r["P"], d, q)
            konst = konst_cache[(r["P"], d, q)]
            res = pq.quote_exakt(r["counts"], konst)
            zeile["n_hut_klassen"] = [fstr(v) for v in res["n_hut_klassen"]]
            zeile["N_hut"] = [fstr(v) for v in res["N_hut"]]
            zeile["m_hat"] = fstr(res["m_hat"])
            zeile["q_sum_N_sq_minus_m2"] = fstr(
                res["q_sum_N_sq_minus_m2"])
            zeile["anteil_falt"] = fstr(res["anteil_falt"])
            zeile["anteil_flt_falt"] = flot(res["anteil_flt_falt"])
            zeile["anteil_modell"] = fstr(res["anteil_modell"])
            zeile["quote"] = fstr(res["quote"])
            zeile["quote_flt"] = flot(res["quote_flt"])
            m = int(res["m_hat"])
            # ABGELEITED Spiegel der gefrorenen Bestands-Konvention:
            # Input = D-Klassen-n_hat (m-scaled); bei d==q ist N_hut
            # identisch mit n_hut_klassen (falt_auf_q-Identitaet).
            n_hat_floats = [float(v) for v in res["n_hut_klassen"]]
            fft_share = share_hw_fft_mirror(n_hat_floats, q, d, m)
            fft_quote = fft_share / float(res["anteil_modell"])
            faltform = share_hw_folded_mirror(n_hat_floats, q, d, m)
            zeile["fft_share_float"] = flot(fft_share)
            zeile["fft_quote_float"] = flot(fft_quote)
            zeile["faltform_float"] = flot(faltform)
            d_fft = abs(res["anteil_flt_falt"] - fft_share)
            d_quo = abs(res["quote_flt"] - fft_quote)
            zeile["delta_fft"] = flot(d_fft)
            zeile["delta_fft_ulp"] = flot(d_fft / math.ulp(
                res["anteil_flt_falt"]))
            zeile["delta_quote"] = flot(d_quo)
            zeile["delta_quote_ulp"] = flot(d_quo / math.ulp(
                res["quote_flt"]))
            zeile["garantie"] = GAR_STRUKTUR

        elif kind in ("loschmidt", "kalibrier_loschmidt", "echo_ladder",
                      "readout_cal"):
            nq = max(len(k) for k in r["counts"])
            modell = pq.modell_fuer_art(kind, nq)
            tv = pq.tv_exakt(r["counts"], modell)
            massa = pq.exakte_masse_am_label(r["counts"], 0)
            zeile["nq"] = nq
            zeile["tv"] = fstr(tv)
            zeile["modell"] = [fstr(v) for v in modell]
            zeile["massa_label0"] = str(Fraction(massa, pq.SHOTS))
            if kind == "readout_cal":
                flips = pq.rand_flip_anteile(r)
                zeile["rand_flip_anteile"] = {str(a): str(v)
                                              for a, v in flips.items()}
                zeile["garantie"] = GAR_KAL
            else:
                zeile["garantie"] = GAR_DELTA

        elif kind == "negative_control":
            q, d = arm_zerlegen(r["arm"])
            nq, breite = pq.register_breite(d)
            modell = NC_MODELL_BAUER[r["name"]]()
            tv = pq.tv_exakt(r["counts"], modell)
            zaehl = pq.zaehlung_auf_labels(r["counts"], breite)
            # p-Werte EXAKT werden NICHT als Decimal-Strings serialisiert
            # (Denominator ~42^8192, int-str-Limit) — als SHA-256-Pins
            # ueber kanonische Fraction-Bytes; die gefrorene Auswertung
            # rekomputiert exakt, hasht gleicher Form und vergleicht.
            p_werte_pin = {}
            for a in range(len(modell)):
                p_a = modell[a]
                beob = zaehl[a] if a < len(zaehl) else 0
                p_werte_pin[str(a)] = frak_pin(pq.p_wert_zweiseitig(
                    beob, pq.SHOTS, p_a))
            zeile["nq"] = nq
            zeile["tv"] = fstr(tv)
            zeile["modell"] = [fstr(v) for v in modell]
            zeile["p_werte_pin"] = p_werte_pin
            zeile["garantie"] = GAR_KONTR

        else:
            raise LaufAbbruch("Unbekannte art: " + kind)

        aus.append(zeile)

    return aus


def share_hw_fft_mirror(n_d, q, d, m):
    """ABSOLUT-FFT-Konvention (pt_ram_q_hardware_aer.py::share_hw_fft —
    Spiegel, NICHT Import): sum_{j=1}^{q-1} |DFT_d(n_hat)[j*d/q]|^2/(d*m).
    ABGELEITED-Float-Schatten, nie Quelle."""
    g = numpy.fft.fft(numpy.asarray(n_d, dtype=float))
    js = [int(j * d / q) for j in range(1, q)]
    return float(sum(abs(g[j]) ** 2 for j in js) / (d * m))


def share_hw_folded_mirror(N, q, d, m):
    """Faltform (041-Theorem, pt_ram_q_hardware_aer.py::share_hw_folded —
    Spiegel, NICHT Import): (q*sum N^2 - m^2)/(d*m).  EXAKT bis zur letzten
    Division (dyadisch-exakter Zaehler), daher genau EINE Rundung."""
    N = numpy.asarray(N, dtype=float)
    return float((q * numpy.sum(N ** 2) - m * m) / (d * m))


def main():
    prereg, prereg_sha = lade_prereg()
    print("[055c] Prereg geladen, kanonisch + REGISTERED_NOT_MEASURED "
          "verifiziert; sha256 = " + prereg_sha)

    dok, isameta, isa_sha = kontrollen(prereg)
    print("[055c] Kontrollen K1-K5 PASS (Abbruchpunkt vor Statistik)")

    reihen = statistics(dok)
    tally = Counter(z["kind"] for z in reihen)

    roh = {
        "experiment": "055c-primequant-exakt",
        "hypothesis": "H-055C",
        "g_typ": "G2-EXAKT",
        "leg": prereg.get("leg", ""),
        "status": "G2EXAKT_RAW_COMPUTED",
        "backend": "PRIMEQUANT_EXAKT_LOCAL",
        "branch": "h-test1-gap-invariance",
        "n_circuits": 160,
        "fetched_at_utc": None,
        "computed_at_utc": datetime.datetime.now(
            datetime.timezone.utc).isoformat(),
        "prereg": {"pfad": PREREG_P, "status": prereg["status"],
                   "sha256": prereg_sha,
                   "file_sha256": hashlib.sha256(
                       (REPO / PREREG_P).read_bytes()).hexdigest()},
        "counts_md5_source": {"pfad": SV_RAW_NAME,
                              "counts_md5": SV_COUNTS_MD5,
                              "counts_payload_sha256": SV_PAYLOAD_SHA256,
                              "backend": SV_BACKEND, "fetched_at_utc": None,
                              "dok_prereg_sha256": dok.get(
                                  "prereg_sha256")},
        "isa_report": {"pfad": ISA_P, "sha256": isa_sha,
                       "meta_pro_arm": isameta,
                       "garantie": "NON-verdict-Meta: Torzahl-Komposition "
                                   "aus committetem ISA-Report (V12); "
                                   "p_1q_eff geschätzt:Hypothese"},
        "numpy_build": numpy.__version__,
        "python_build": platform.python_version(),
        "primequant_version": pq.__version__,
        "qiskit_build": None,
        "seed": None,
        "kontrollen": {"K1": "prereg-identitaet + sv-source-pins",
                       "K2": "reihen-schema (160, ROW_KEYS, TALLY, shots)",
                       "K3": "isa-sha + per_circuit-Struktur",
                       "K4": "erste-struktur-quote-pins",
                       "K5": "negative-control-modell- + tv-pins"},
        "garantie_katalog": {
            "struktur": "EXAKT (Fraction-Kette via quote_exakt/"
                        "punkt_konstanten); Float-Schatten ABGELEITED "
                        "(FFT-/Faltform-Spiegel), nie Quelle",
            "delta": "EXAKT (tv_exakt gegen modell_fuer_art; "
                     "Delta-Saettigung erwartet, V8)",
            "negative_control": "EXAKT (tv + exakte zweiseitige p-Werte)",
            "readout_cal": "EXAKT (tv + rand_flip_anteile via "
                           "calibrations-Schicht)",
            "float_schatten": "ABGELEITED — bestands-Konvention als Spiegel; "
                              "Schranke nur in der gefrorenen Auswertung",
        },
        "reihen": reihen,
    }

    try:
        blob = json.dumps(roh, sort_keys=True, indent=1,
                          ensure_ascii=False)
    except TypeError as fehler:
        raise LaufAbbruch("Raw-Payload nicht serialisierbar: "
                          + str(fehler))

    (REPO / ROH_P).write_bytes(blob.encode("utf-8"))

    struct = tally.get("structure", 0) + tally.get("kalibrier_structure", 0)
    delta = (tally.get("loschmidt", 0) + tally.get("kalibrier_loschmidt", 0)
             + tally.get("echo_ladder", 0) + tally.get("readout_cal", 0))
    print("[055c] Reihen: " + str(len(reihen)) + " (" +
          ", ".join(k + " " + str(v) for k, v in sorted(tally.items())) +
          ")")
    print("[055c] struct " + str(struct) + " | delta " + str(delta) +
          " | negative_control " + str(tally.get("negative_control", 0)))
    print("[055c] Raw geschrieben: " + ROH_P + " (kanonisch, sort_keys, "
          "indent=1) — keine Verdict-Felder")


if __name__ == "__main__":
    try:
        main()
    except LaufAbbruch as ab:
        print("[055c] LAUF-ABBRUCH: " + str(ab), file=sys.stderr)
        sys.exit(2)