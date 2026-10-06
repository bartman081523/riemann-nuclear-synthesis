#!/usr/bin/env python3
"""EXPERIMENT 055c (H-055C, G2-EXAKT) Tests — primequant Phase-C-Anker.

Bindet die gefrorene Kette: Prereg R0 REGISTERED_NOT_MEASURED (kanonische
Serialisierung, Freeze-Commit 0a66007), Roh-Commit 4c6cc57 VOR Auswertung,
Gefrorene eval (zweiter Pfad, kein Runner-/primequant-Import) und deren
Verdicts H-055C-1..4 (drei HELD; T2 REFUTED = ehrlicher Negativbefund am
ex-ante-2-ULP-Band, genau EINE Zeile von 111: calstruct_q5_d5_433_r0,
mechanisch Binaden-ULP-Effekt).  Kein Test schreibt Projekt-Artefakte
(053-Lektion) und keiner ruft die eval main() auf — die Verdict-Kette
wird AUS dem committeten eval gelesen und Feld fuer Feld gegen die
committeten Rohs nachgerechnet.
"""
import hashlib
import json
import math
from collections import Counter
from fractions import Fraction
from pathlib import Path

import pytest

import pt_ram_q_prio48_exakt_eval as EV

REPO = Path(__file__).resolve().parents[1]
PREREG_P = "pt_ram_q_prio48_exakt_prereg.json"
ROH_P = "pt_ram_q_prio48_exakt_raw.json"
SV_P = "pt_ram_q_prio48_sv_raw.json"
EVAL_P = "pt_ram_q_prio48_exakt_eval.json"
ISA_P = "pt_ram_q_prio48_sv_isa_report.json"

DELTA_ARTEN = ("loschmidt", "kalibrier_loschmidt", "echo_ladder",
               "readout_cal")
STRUKT_ARTEN = ("structure", "kalibrier_structure")


def _load(path):
    with open(REPO / path, encoding="utf-8") as f:
        return json.load(f)


def _ev():
    return _load(EVAL_P)


def _prereg():
    return _load(PREREG_P)


def _raw_reihen():
    return _load(ROH_P)["reihen"]


def _sv_reihen():
    return _load(SV_P)["counts"]


def _raw_by_name():
    return {z["name"]: z for z in _raw_reihen()}


# --------------------------------------------------------------------------
# Prereg + Source-Pins (Freeze-Kette)
# --------------------------------------------------------------------------

def test_prereg_frozen_kanonisch():
    roh = (REPO / PREREG_P).read_bytes()
    payload = json.loads(roh.decode("utf-8"))
    kanon = json.dumps(payload, sort_keys=True, indent=1,
                       ensure_ascii=False).encode("utf-8")
    assert roh == kanon                       # freeze_discipline 1
    assert payload["status"] == "REGISTERED_NOT_MEASURED"
    assert payload["version_regie"] == "R0"
    assert payload["hypothesis"] == "H-055C"
    assert payload["g_typ"] == "G2-EXAKT"
    ev = _ev()
    kompakt = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode("utf-8")).hexdigest()
    datei = hashlib.sha256(roh).hexdigest()
    e0 = ev["verification"]["E0_freeze_rahmen"]
    e1 = ev["verification"]["E1_prereg"]
    assert datei == e0["prereg_file_sha256"]
    assert kompakt == e0["prereg_payload_sha256"]
    assert ev["verification"]["E1_prereg"]["status"] == \
        payload["status"]
    assert hashlib.sha256(json.dumps(
        payload["schwellwerte"], sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode("utf-8")).hexdigest() == \
        e1["schwellwerte_payload_sha256"]
    assert hashlib.sha256(json.dumps(
        payload["hypotheses"], sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode("utf-8")).hexdigest() == \
        e1["hypotheses_payload_sha256"]
    assert set(payload["hypotheses"]) == {"H-055C-1", "H-055C-2",
                                          "H-055C-3", "H-055C-4"}


def test_raw_counts_source_pin():
    """Dual-Pin-Kette: MD5 ueber Counts-only-Liste, SHA-256 ueber die
    VOLLEN Reihenliste (anchors-Konvention) + SV-Prereg-Pin-Kette mit
    disclosed 63-Zeichen-Sourcepin (nicht abortierend)."""
    pins = _prereg()["source_pins"]
    roh = _load(ROH_P)
    dok = _load(SV_P)
    sv_reihen = dok["counts"]

    p_md5 = json.dumps([z["counts"] for z in sv_reihen], sort_keys=True,
                       separators=(",", ":")).encode("utf-8")
    p_sha = json.dumps(sv_reihen, sort_keys=True,
                       separators=(",", ":")).encode("utf-8")
    assert hashlib.md5(p_md5).hexdigest() == pins["sv_counts_md5"]
    assert hashlib.sha256(p_sha).hexdigest() == \
        pins["sv_counts_payload_sha256"]
    assert dok["backend"] == pins["sv_backend"]
    assert dok["fetched_at_utc"] is None
    assert dok["n_circuits"] == 160
    cs = roh["counts_md5_source"]
    assert cs["pfad"] == SV_P
    assert cs["counts_md5"] == pins["sv_counts_md5"]
    assert cs["counts_payload_sha256"] == pins["sv_counts_payload_sha256"]
    assert cs["backend"] == pins["sv_backend"]
    assert cs["fetched_at_utc"] is None

    # SV-Prereg-Pin-Kette: eigener Rekompute == sv-dok == Runner-Konstante,
    # alle 64 Zeichen; der Prereg-Sourcepin bleibt der disclosed 63-Zeichen-
    # Registrierungs-Typo (bindende Kette intakt, Prereg NICHT editiert).
    pr5 = _load("pt_ram_q_prio48_sv_prereg.json")
    sha5 = hashlib.sha256(json.dumps(
        pr5, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode("utf-8")).hexdigest()
    runner_pin = EV.eigen_runner_pin("SV_PREREG_SHA256")
    assert len(runner_pin) == 64
    assert sha5 == runner_pin == dok["prereg_sha256"] == \
        roh["counts_md5_source"]["dok_prereg_sha256"]
    assert len(pins["sv_dok_prereg_sha256"]) == 63


# --------------------------------------------------------------------------
# E5-Feld-Anker: erste Struktur-Reihe (K4-Pins, transkribiert gefroren)
# --------------------------------------------------------------------------

def test_row_0_statistik_gepinnt():
    erste = EV.ERSTE
    raw = _raw_by_name()
    r = raw[erste["name"]]
    assert r["kind"] == "structure" and r["P"] == 181
    assert r["n_hut_klassen"] == erste["n_hut"]
    assert r["N_hut"] == erste["n_hut"]          # d == q-Identitaet
    assert r["m_hat"] == erste["m_hat"] == "42"
    assert r["q_sum_N_sq_minus_m2"] == erste["q_sum"]
    assert r["anteil_falt"] == erste["anteil_falt"]
    assert r["anteil_modell"] == erste["anteil_modell"]
    assert r["quote"] == erste["quote"]
    assert float(r["anteil_flt_falt"]) == erste["anteil_flt_falt"]
    assert float(r["quote_flt"]) == erste["quote_flt"]
    assert float(r["faltform_float"]) == erste["anteil_flt_falt"]
    # Quote-Kette exakt nachgerechnet (zweiter Pfad)
    konst = EV.eigen_punkt_konstanten(181, 3, 3, 8192)
    assert konst["n0"] == 1
    sv_by_name = {z["name"]: z for z in _sv_reihen()}
    res = EV.eigen_quote_exakt(sv_by_name[erste["name"]]["counts"], konst,
                               8192)
    assert str(res["anteil_falt"]) == erste["anteil_falt"]
    assert str(res["quote"]) == erste["quote"]
    assert res["anteil_flt_falt"] == erste["anteil_flt_falt"]


# --------------------------------------------------------------------------
# Schwellen T1-T4 (Verdict-Kette, aus dem committeten eval + Roh nachgerechnet)
# --------------------------------------------------------------------------

def test_t1_delta_tv_exakt_null():
    ev = _ev()
    t1 = ev["schwellen"]["T1"]
    assert t1["verdict"] == "HELD" and t1["n"] == 45
    assert t1["verletzt_bei"] == []
    reihen = _raw_reihen()
    assert Counter(z["kind"] for z in reihen) == Counter(EV.TALLY)
    delta = [z for z in reihen if z["kind"] in DELTA_ARTEN]
    assert len(delta) == 45
    for z in delta:
        assert z["tv"] == "0"                   # Fraction(0) als String
        assert Fraction(z["tv"]) == Fraction(0)
        assert z["modell"][0] == "1"            # Delta auf 0^n exakt
        assert z["massa_label0"] == "1"
    # Quelle: die 45 sv-Reihen tragen die Counts (nicht das Raw)
    sv_by_name = {z["name"]: z for z in _sv_reihen()}
    for z in delta:
        assert z["name"] in sv_by_name
        assert sv_by_name[z["name"]]["shots_actual"] == 8192


def test_t2_fft_ulp_band():
    """Ehrlicher Negativbefund: Band ex ante 2 ULP (V6 mass 1 ULP), auf
    der VOLLEN 111-Reihe-Sweep genau EINE Verletzung (4.0 ULP) — Verdict
    bleibt REFUTED, kein Toleranz-Raise."""
    ev = _ev()
    t2 = ev["schwellen"]["T2"]
    assert t2["verdict"] == "REFUTED"
    assert t2["verletzt_bei"] == "calstruct_q5_d5_433_r0"
    assert t2["max_delta_fft_ulp"] == 4.0
    roh_rows = [z for z in _raw_reihen() if z["kind"] in STRUKT_ARTEN]
    assert len(roh_rows) == 111
    over = [z["name"] for z in roh_rows
            if float(z["delta_fft"]) >
            2.0 * math.ulp(float(z["anteil_flt_falt"]))]
    assert over == ["calstruct_q5_d5_433_r0"]
    verteilung = Counter(float(z["delta_fft_ulp"]) for z in roh_rows)
    assert verteilung == {0.0: 56, 1.0: 42, 2.0: 12, 4.0: 1}
    q3 = [z for z in roh_rows if z["arm"] == "q3_d3"]
    q5 = [z for z in roh_rows if z["arm"] == "q5_d5"]
    assert len(q3) == 48 and len(q5) == 63
    assert max(float(z["delta_fft_ulp"]) for z in q3) == 2.0
    assert max(float(z["delta_fft_ulp"]) for z in q5) == 4.0
    # Mechanismus: gleicher absoluter Rest 2^-49, kleineres ulp am
    # Binadenrand [2, 4) der verletzten Zeile
    viol = _raw_by_name()["calstruct_q5_d5_433_r0"]
    assert float(viol["delta_fft"]) == 2.0 ** -49
    assert float(viol["delta_fft_ulp"]) == 4.0
    flt = float(viol["anteil_flt_falt"])
    assert math.ulp(flt) == 2.0 ** -51


def test_t3_negative_controls_band():
    ev = _ev()
    t3 = ev["schwellen"]["T3"]
    assert t3["verdict"] == "HELD" and t3["n"] == 4
    assert t3["verletzt_bei"] is None
    raw = _raw_by_name()
    detail = {d["name"]: d for d in t3["detail"]}
    assert set(detail) == set(EV.NC_N_D)
    for name, dekl in EV.NC_TV_PINS.items():
        z = raw[name]
        tv = Fraction(z["tv"])
        assert tv == dekl                       # TV-Pin exakt
        assert tv <= EV.T3_TV                   # tv-Band
        alpha_frac = EV.T3_ALPHA[z["arm"]]
        assert Fraction(detail[name]["alpha"]) == alpha_frac
        assert detail[name]["min_p"] == "PIN:" + detail[name]["min_p_pin"]
        assert detail[name]["name"] == name
        assert TV_LABEL_MIN.get(name) is not None  # min_p_label gefroren
        assert detail[name]["min_p_label"] == TV_LABEL_MIN[name]


def test_t4_faltform_bit_identisch():
    ev = _ev()
    t4 = ev["schwellen"]["T4"]
    assert t4["verdict"] == "HELD" and t4["n"] == 111
    assert t4["bit_identisch"] == 111
    assert t4["verletzt_bei"] is None
    roh_rows = [z for z in _raw_reihen() if z["kind"] in STRUKT_ARTEN]
    assert all(float(z["faltform_float"]) == float(z["anteil_flt_falt"])
               for z in roh_rows)
    assert sum(1 for z in roh_rows
               if float(z["faltform_float"]) ==
               float(z["anteil_flt_falt"])) == 111


# --------------------------------------------------------------------------
# Bestands-Pfad + Raw-Disziplin + Verdict-Kette
# --------------------------------------------------------------------------

def test_isa_meta_wohlgeformt():
    pins = _prereg()["source_pins"]
    isa_bytes = (REPO / ISA_P).read_bytes()
    sha = hashlib.sha256(isa_bytes).hexdigest()
    assert sha == pins["isa_sha256"]
    isa = _load(ISA_P)
    assert len(isa["per_circuit"]) == 160
    roh_isa = _load(ROH_P)["isa_report"]["meta_pro_arm"]
    assert set(roh_isa) == {"q3_d3", "q5_d5", "ohne_arm:readout_cal"}
    for arm, meta in roh_isa.items():
        assert meta["p_1q_eff_herkunft"].startswith("geschätzt:Hypothese")
        assert meta["p_eff_formel"].startswith("1-(1-p_1q_eff)^")
        for op, k in meta["ops_gesamt"].items():
            assert isinstance(op, str) and isinstance(k, int) and k >= 0
            assert not isinstance(k, bool)
        assert isinstance(meta["2q_tore"], int)
        assert isinstance(meta["tiefe_max"], int)
    circuits = 0
    for _c, e in isa["per_circuit"].items():
        assert isinstance(e["ops"], dict)
        assert all(isinstance(k, int) and not isinstance(k, bool)
                   and k >= 0 for k in e["ops"].values())
        assert isinstance(e["n_2q"], int) and isinstance(e["depth"], int)
        circuits += 1
    assert circuits == 160


def test_raw_ohne_verdict_felder():
    """banned_from_raw auf Feld/Key-Ebene BINDEND (0 Verletzungen) +
    Value-Disclosure: genau 63 Substring-Vorkommen von 'verdict' = 62
    frozen set-Designations-Strings der committeten 055b-Quelle +
    1 ISA-Garantie-String, der Verdict-Status explizit VERNEINT."""
    banned = tuple(_prereg()["banned_from_raw"])
    roh = _load(ROH_P)
    keys = []

    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                sk = k if isinstance(k, str) else str(k)
                for w in banned:
                    assert w not in sk, (w, sk)
                keys.append(sk)
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
    walk(roh)
    werte = {"verdict": 0}

    def walk2(obj, pfad):
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk2(v, pfad + [k])
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk2(v, pfad + [str(i)])
        elif isinstance(obj, str):
            for w in banned:
                if w in obj:
                    werte[w] = werte.get(w, 0) + 1
    walk2(roh, [])
    assert werte == {"verdict": 63}
    # Set-Vokabular: bit-identisch zur committeten 055b-Quelle getragen
    roh_sets = Counter((z.get("set") if isinstance(z.get("set"), str)
                        else (None if z.get("set") is None
                              else "?" + str(z.get("set"))))
                       for z in roh["reihen"])
    assert roh_sets == {None: 2, "cal": 96, "verdict": 62}
    sv_by_name = {z["name"]: z for z in _sv_reihen()}
    assert all(sv_by_name[z["name"]]["set"] == z["set"]
               for z in roh["reihen"])
    # ISA-Garantie-String verneint Verdict-Status explizit
    garantie = roh["isa_report"]["meta_pro_arm"]["q3_d3"]["p_eff_formel"]
    assert garantie.startswith("1-(1-p_1q_eff)^")


def test_eval_verdict_kette():
    ev = _ev()
    assert ev["experiment"] == "055c-primequant-exakt"
    assert ev["hypothesis"] == "H-055C" and ev["g_typ"] == "G2-EXAKT"
    assert ev["eval_status"] == "GEFRORENE_AUSWERTUNG (nur committete " \
        "Artefakte)"
    assert "kein primequant-Import" in ev["second_path"]
    assert ev["primequant_importiert"] is False
    assert ev["qiskit_importiert"] is False
    assert ev["verdicts"] == {"H-055C-1": "HELD", "H-055C-2": "REFUTED",
                              "H-055C-3": "HELD", "H-055C-4": "HELD"}
    assert ev["kern_verdict"] == {"verdict": "H-055C_KERN_MIXED",
                                  "grade_hinweis": "B+"}
    nach = {z["schwelle"]: z for z in ev["nachtabelle"]}
    assert set(nach) == {"T1", "T2", "T3", "T4"}
    for t in ("T1", "T2", "T3", "T4"):
        assert nach[t]["verdict"] == ev["schwellen"][t]["verdict"]
        assert nach[t]["n"] == ev["schwellen"][t]["n"]
    assert nach["T1"]["verdict"] == "HELD"
    assert nach["T3"]["verdict"] == "HELD"
    assert nach["T4"]["verdict"] == "HELD"


def test_frak_hash_kreuz_pin():
    """Dritter Pfad gegen die Pins: je NC-Reihe wird der min-p-Wert am
    min_p_label mit dem EIGENEN Walk des gefrorenen evals exakt
    nachgerechnet und dreifach verketted (eval-detail == raw-p_werte_pin ==
    Rekompute)."""
    ev = _ev()
    raw = _raw_by_name()
    detail = {d["name"]: d for d in ev["schwellen"]["T3"]["detail"]}
    nc = {z["name"]: z for z in _sv_reihen()
          if z["kind"] == "negative_control"}
    assert set(nc) == set(detail)
    for name, d in detail.items():
        breite = 1 << int(raw[name]["nq"])
        modell = EV.eigen_nc_modell(name, breite)
        zaehl = EV.eigen_zaehlung_auf_labels(nc[name]["counts"], breite)
        idx = d["min_p_label"]
        p = EV.eigen_p_wert_zweiseitig(zaehl[idx], 8192, modell[idx])
        pin = EV.eigen_frak_pin(p)
        assert pin == d["min_p_pin"]
        assert raw[name]["p_werte_pin"][str(idx)] == pin
        if p < 1:                        # informativer Fall: 1 bleibt 1
            assert Fraction(0) < p <= Fraction(1)


TV_LABEL_MIN = {
    "ctrl_composite_P181_d3": 2,
    "ctrl_uniform_q3": 1,
    "ctrl_composite_P467_d5": 4,
    "ctrl_uniform_q5": 1,
}