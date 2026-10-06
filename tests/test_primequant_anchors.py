"""Anker-Schicht (Phase B): Payload-Hash-Pins, Rohdokument-Verifizierung.

Alle Pins aus den live-erprobten Probe-Laeufen (scratches/
probe_anchor_shapes.py -> probe2_out.txt, scratches/probe_lese_guards.py,
2026-10-06): SHA-256 ueber kanonisches Counts-Payload der drei
committeten Rohdokumente, counts_md5-Re-Verifizierung, Struktur-Familien-
Zensus (111 Reihen / 37 Punkte), 45 Delta-Reihen TV==0, Negative-Control-
TV-Pins, exakte Quote der ersten Struktur-Reihe, Kalibrier-Abzweig
(Fez/Kingston, Pfad-basiert) und die Guard-Texte des Lesekanals.
"""
import functools
import os
import sys
from fractions import Fraction as F

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)
try:
    import primequant as pq
except ImportError:  # editable install fehlt: src-Fallback
    sys.path.insert(0, os.path.join(_REPO, "src"))
    import primequant as pq

# Rohtexte liegen im Repo-Root; die Suite laeuft per Konvention mit cwd
# = Repo-Root (= Rootdir des claims-Pins).
SV = "pt_ram_q_prio48_sv_raw.json"
HW3 = "pt_ram_q_hardware3_raw.json"
KS = "pt_ram_q6_kingston_raw.json"

# counts_md5 = MD5 ueber counts_payload(counts): re-verifiziert je Laden.
MD5_PINS = {
    SV: "a126430cd770325e1dd8009ad84d66d9",
    HW3: "230098aeeb6e8716d2638e1d5fe3cfeb",
    KS: "f4da706dd542c306a96cba2001e1a6b9",
}
# Neue Pin-Achse (SHA-256-Regel 2026-10-05) ueber dasselbe Payload.
SHA_PINS = {
    SV: "289f1f4e6c48eada9a15f1735af9739a68b2a630addc91efda5c9e31f76359a2",
    HW3: "4c1da04939041eea5743eac0d62f6252a87bff43c6a2a4694063b96f7d6b68b5",
    KS: "6a896e53232dadfc1c696d2e0ba8fa602ee4df02b5c39be46c4d435a3b9b56ce",
}
BACKEND_PINS = {
    SV: ("AER_STATEVECTOR_LOCAL", None),
    HW3: ("ibm_fez", "2026-09-28T07:54:54.444730+00:00"),
    KS: ("ibm_kingston", "2026-10-01T23:49:08.483868+00:00"),
}

# kinds-Zensus der 160 sv-Reihen (live, Probe D).
TALLY = {
    "structure": 39,
    "loschmidt": 13,
    "echo_ladder": 6,
    "kalibrier_structure": 72,
    "kalibrier_loschmidt": 24,
    "negative_control": 4,
    "readout_cal": 2,
}
ROW_KEYS = {"P", "arm", "counts", "kind", "name", "r", "rep", "set",
            "shots_actual"}

Q3_P = [149, 181, 197, 229, 251, 283, 347, 379, 433, 467, 577, 613, 659,
        691, 761, 797]
Q5_P = [433, 467, 479, 499, 521, 547, 557, 563, 577, 593, 613, 617, 631,
        653, 659, 673, 677, 691, 701, 719, 733]


@functools.lru_cache(maxsize=None)
def _roh(name):
    """Dok des committeten Rohs, je Testlauf einmal.

    lies_committed_counts gibt (dok, rekomputierter-MD5) zurueck und
    verifiziert counts_md5 bereits beim Laden; hier zusaetzlich gegen
    den Pin geprueft.
    """
    dok, md5 = pq.lies_committed_counts(name)
    assert md5 == MD5_PINS[name]
    return dok


def test_counts_payload_kanonisch():
    assert pq.counts_payload([{"0": 1}]) == b'[{"0":1}]'
    # Reihen-Reihenfolge bleibt, Keys werden je Reihe sortiert
    assert pq.counts_payload([{"1": 2}, {"0": 1}]) == \
        b'[{"1":2},{"0":1}]'
    assert pq.counts_payload([{"01": 2, "00": 1}]) == b'[{"00":1,"01":2}]'
    assert pq.payload_sha256(b"abc") == \
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    with pytest.raises(ValueError,
                       match="payload_sha256 verlangt bytes oder bytearray"):
        pq.payload_sha256("abc")


def test_fehlende_dateien():
    with pytest.raises(FileNotFoundError, match="Datei fehlt:"):
        pq.datei_sha256("scratches/kein_dokument_lala.json")
    with pytest.raises(FileNotFoundError, match="Rohdokument fehlt:"):
        pq.lies_rohdokument("scratches/kein_dokument_lala.json")


def test_rohs_backend_fetched_und_payload_pins():
    for name in (SV, HW3, KS):
        dok = _roh(name)
        backend, fetched = BACKEND_PINS[name]
        assert dok["backend"] == backend
        assert dok["fetched_at_utc"] == fetched
        # counts_md5 wird beim Laden re-verifiziert; der Rueckgabe-Wert ist
        # der rekomputierte MD5 == der committete Pin
        assert pq.versichere_counts_md5(dok) == MD5_PINS[name]
        assert dok["counts_md5"] == MD5_PINS[name]
        assert pq.payload_sha256(pq.counts_payload(dok["counts"])) == \
            SHA_PINS[name]


def test_versichere_counts_md5_guards():
    dok = _roh(SV)
    falsch = dict(dok)
    falsch["counts_md5"] = "0" * 32
    with pytest.raises(pq.AnchorViolation,
                       match="counts_md5 divergiert: rekomputiert "
                             "a126430cd770325e1dd8009ad84d66d9, "
                             "committet 00000000000000000000000000000000"):
        pq.versichere_counts_md5(falsch)
    ohne = {k: v for k, v in dok.items() if k != "counts_md5"}
    with pytest.raises(pq.AnchorViolation,
                       match="Rohdokument ohne counts oder counts_md5"):
        pq.versichere_counts_md5(ohne)


def test_sv_reihen_schema_und_kinds_zensus():
    reihen = _roh(SV)["counts"]
    assert len(reihen) == 160
    tally = {}
    for r in reihen:
        tally[r["kind"]] = tally.get(r["kind"], 0) + 1
        assert frozenset(r.keys()) == ROW_KEYS
    assert tally == TALLY
    erste = reihen[0]
    assert {k: v for k, v in erste.items() if k != "counts"} == \
        {"P": 181, "arm": "q3_d3", "kind": "structure",
         "name": "struct_q3_d3_181_r0", "r": None, "rep": 0,
         "set": "verdict", "shots_actual": 8192}


def test_struktur_familie_zensus():
    reihen = _roh(SV)["counts"]
    familie = [r for r in reihen if r["kind"] in pq.STRUKTUR_REIHENARTEN]
    assert len(familie) == 111
    paar_z = {}
    for r in familie:
        assert r["shots_actual"] == 8192
        paar_z[(r["arm"], r["P"])] = paar_z.get((r["arm"], r["P"]), 0) + 1
    assert len(paar_z) == 37
    assert set(paar_z.values()) == {3}
    for arm, p_liste in (("q3_d3", Q3_P), ("q5_d5", Q5_P)):
        punkte = sorted(p for (a, p) in paar_z if a == arm)
        assert punkte == p_liste


def test_45_delta_reihen_tv_null():
    reihen = _roh(SV)["counts"]
    delta_reihe = [r for r in reihen if r["kind"] in pq.DELTA_REIHENARTEN]
    assert len(delta_reihe) == 45
    for r in delta_reihe:
        nq = max(len(label) for label in r["counts"])
        modell = pq.modell_fuer_art(r["kind"], nq)
        assert pq.tv_exakt(r["counts"], modell) == 0


def test_negative_control_tv_pins():
    # n_d/m der Composite-Kontrollen kommen aus dem committeten Prereg
    # (055b); Uniform: Modell = 1/q auf den Labeln 0..q-1.
    reihen = _roh(SV)["counts"]
    by_name = {r["name"]: r for r in reihen
               if r["kind"] == "negative_control"}
    assert sorted(by_name) == ["ctrl_composite_P181_d3",
                               "ctrl_composite_P467_d5",
                               "ctrl_uniform_q3", "ctrl_uniform_q5"]
    modell_181 = pq.fuele_modell(
        pq.exakter_probvektor([19, 13, 10], 42), 4)
    modell_467 = pq.fuele_modell(
        pq.exakter_probvektor([23, 18, 17, 15, 18], 91), 8)
    erwartungen = {
        "ctrl_composite_P181_d3": (modell_181, F(551, 86016)),
        "ctrl_uniform_q3": (pq.modell_fuer_art("negative_control", 2, q=3),
                            F(79, 24576)),
        "ctrl_composite_P467_d5": (modell_467, F(835, 106496)),
        "ctrl_uniform_q5": (pq.modell_fuer_art("negative_control", 3, q=5),
                            F(31, 2560)),
    }
    for name, (modell, tv_pin) in sorted(erwartungen.items()):
        zeile = by_name[name]
        assert pq.tv_exakt(zeile["counts"], modell) == tv_pin


def test_erste_struktur_quote_exakt():
    reihen = _roh(SV)["counts"]
    konst = pq.punkt_konstanten(181, 3, 3)
    res = pq.quote_exakt(reihen[0]["counts"], konst)
    n_hut = [F(3969, 4096), F(19761, 1024), F(89019, 4096)]
    assert res["N_hut"] == res["n_hut_klassen"] == n_hut
    assert res["m_hat"] == 42
    assert res["q_sum_N_sq_minus_m2"] == F(6484629375, 8388608)
    assert res["anteil_falt"] == F(102930625, 16777216)
    assert res["anteil_modell"] == F(169, 28)
    assert res["anteil_flt_falt"] == 6.135143339633942
    assert res["quote"] == F(720514375, 708837376)
    assert res["quote_flt"] == 1.0164734527204164


def test_kalibriere_dokument_fez():
    kal = pq.kalibriere_dokument(HW3)
    assert set(kal.keys()) == {"backend", "counts_md5_rekomputiert",
                               "fetched_at_utc", "garantie", "herkunft",
                               "pfad", "reihen"}
    assert kal["backend"] == "ibm_fez"
    assert kal["fetched_at_utc"] == "2026-09-28T07:54:54.444730+00:00"
    assert kal["herkunft"] == "kalibriert+2026-09-28T07:54:54.444730+00:00"
    assert kal["counts_md5_rekomputiert"] == \
        "230098aeeb6e8716d2638e1d5fe3cfeb"
    assert set(kal["reihen"].keys()) == {"cal_2q", "cal_3q"}
    g_kal = kal["garantie"]
    assert g_kal.klasse == "ABGELEITET"
    assert g_kal.herkunft == kal["herkunft"]
    assert g_kal.grenze == \
        "Kalibrierung nur aus committeten Reihen mit verifiziertem Pin"
    assert g_kal.quelle == \
        "pt_ram_q_hardware3_raw.json (counts_md5 230098aeeb6e8716d2638e1d5fe3cfeb)"
    # cal_2q: Randflips je Qubit exakt als Fraction
    q2 = kal["reihen"]["cal_2q"]
    assert q2["nq"] == 2
    assert q2["ro_rand_qubits"] == {0: F(3, 4096), 1: F(5, 4096)}
    iv2 = q2["ro_intervall"]
    assert iv2["name"] == "cal_2q" and iv2["nq"] == 2 and iv2["shots"] == 8192
    assert iv2["k0"] == 8176
    assert iv2["p0"] == F(511, 512)
    assert iv2["ro_lo"] == F(1, 1024)
    assert iv2["ro_hi"] == F(9, 8192)
    assert iv2["breite"] == F(1, 8192)
    assert iv2["uniform_ro_exakt"] is False
    assert q2["garantie"].klasse == "ABGELEITET"
    assert q2["garantie"].grenze.startswith("Randflips exakt je Qubit")
    # cal_3q
    q3 = kal["reihen"]["cal_3q"]
    assert q3["nq"] == 3
    assert q3["ro_rand_qubits"] == {0: F(3, 8192), 1: F(1, 4096),
                                    2: F(3, 4096)}
    iv3 = q3["ro_intervall"]
    assert iv3["k0"] == 8181
    assert iv3["p0"] == F(8181, 8192)
    assert iv3["ro_lo"] == F(3, 8192)
    assert iv3["ro_hi"] == F(1, 2048)
    assert iv3["breite"] == F(1, 8192)
    assert iv3["uniform_ro_exakt"] is False


def test_kalibriere_dokument_kingston():
    kal = pq.kalibriere_dokument(KS)
    assert kal["backend"] == "ibm_kingston"
    assert kal["fetched_at_utc"] == "2026-10-01T23:49:08.483868+00:00"
    assert kal["herkunft"] == "kalibriert+2026-10-01T23:49:08.483868+00:00"
    assert kal["counts_md5_rekomputiert"] == \
        "f4da706dd542c306a96cba2001e1a6b9"
    assert set(kal["reihen"].keys()) == {"cal_2q", "cal_3q"}
    g_kal = kal["garantie"]
    assert g_kal.klasse == "ABGELEITET"
    assert g_kal.grenze == \
        "Kalibrierung nur aus committeten Reihen mit verifiziertem Pin"
    assert g_kal.quelle == \
        "pt_ram_q6_kingston_raw.json (counts_md5 f4da706dd542c306a96cba2001e1a6b9)"
    q2 = kal["reihen"]["cal_2q"]
    assert q2["nq"] == 2
    assert q2["ro_rand_qubits"] == {0: F(13, 8192), 1: F(7, 4096)}
    iv2 = q2["ro_intervall"]
    assert iv2["k0"] == 8165
    assert iv2["p0"] == F(8165, 8192)
    assert iv2["ro_lo"] == F(13, 8192)
    assert iv2["ro_hi"] == F(7, 4096)
    assert iv2["breite"] == F(1, 8192)
    assert iv2["uniform_ro_exakt"] is False
    q3 = kal["reihen"]["cal_3q"]
    assert q3["nq"] == 3
    assert q3["ro_rand_qubits"] == {0: F(27, 8192), 1: F(9, 8192),
                                    2: F(17, 8192)}
    iv3 = q3["ro_intervall"]
    assert iv3["k0"] == 8140
    assert iv3["p0"] == F(2035, 2048)
    assert iv3["ro_lo"] == F(17, 8192)
    assert iv3["ro_hi"] == F(9, 4096)
    assert iv3["breite"] == F(1, 8192)
    assert iv3["uniform_ro_exakt"] is False
    assert q3["garantie"].klasse == "ABGELEITET"


def test_kalibriere_verweigert_sv_ohne_fetched():
    with pytest.raises(pq.AnchorViolation,
                       match="Rohdokument ohne fetched_at_utc"):
        pq.kalibriere_dokument(SV)


def test_ro_intervall_synth_und_ganzzahl_wurzel():
    synth = pq.ro_intervall({"name": "synth_7938", "kind": "readout_cal",
                             "shots_actual": 8192,
                             "counts": {"00": 7938, "01": 254}})
    assert synth["k0"] == 7938
    assert synth["p0"] == F(3969, 4096)
    assert synth["ro_lo"] == synth["ro_hi"] == F(1, 64)
    assert synth["breite"] == 0
    assert synth["uniform_ro_exakt"] is True
    voll = pq.ro_intervall({"name": "synth_voll", "kind": "readout_cal",
                            "shots_actual": 8192, "counts": {"00": 8192}})
    assert voll["k0"] == 8192 and voll["p0"] == 1
    assert voll["ro_lo"] == 0 and voll["ro_hi"] == 0
    assert voll["breite"] == 0 and voll["uniform_ro_exakt"] is True
    assert pq.ganzzahl_wurzel(0, 5) == 0
    assert pq.ganzzahl_wurzel(1, 3) == 1
    assert pq.ganzzahl_wurzel(8, 3) == 2
    assert pq.ganzzahl_wurzel(9, 3) == 2
    assert pq.ganzzahl_wurzel(8064 ** 2, 2) == 8064
    assert pq.ganzzahl_wurzel(8064 ** 2 + 1, 2) == 8064


def test_lese_readout_cal_reihen_guards_und_pins():
    # Guard-Reihenfolge (live): kein counts-Array (auch leer), kein
    # readout_cal, Label-Laengen, shots<=0, Summe, nicht-ganze Masse
    with pytest.raises(pq.AnchorViolation, match="kein counts-Array"):
        pq.lese_readout_cal_reihen({"x": 1})
    with pytest.raises(pq.AnchorViolation, match="kein counts-Array"):
        pq.lese_readout_cal_reihen({"counts": []})
    with pytest.raises(pq.AnchorViolation, match="kein readout_cal-Reihe"):
        pq.lese_readout_cal_reihen(
            {"counts": [{"kind": "structure", "counts": {"00": 1}}]})
    with pytest.raises(pq.AnchorViolation,
                       match=r"Label-Laengen uneinheitlich .* \{1, 2\}"):
        pq.lese_readout_cal_reihen(
            {"counts": [{"kind": "readout_cal", "name": "g",
                         "counts": {"0": 4, "00": 4}, "shots_actual": 8}]})
    with pytest.raises(pq.AnchorViolation, match="shots_actual <= 0"):
        pq.lese_readout_cal_reihen(
            {"counts": [{"kind": "readout_cal", "name": "g",
                         "counts": {"00": 8}, "shots_actual": 0}]})
    with pytest.raises(pq.AnchorViolation,
                       match="Counts-Summe 7 != shots 8"):
        pq.lese_readout_cal_reihen(
            {"counts": [{"kind": "readout_cal", "name": "g",
                         "counts": {"00": 7}, "shots_actual": 8}]})
    with pytest.raises(pq.AnchorViolation, match="Masse 4.5 nicht ganz"):
        pq.lese_readout_cal_reihen(
            {"counts": [{"kind": "readout_cal", "name": "g",
                         "counts": {"01": 4.5, "00": 3.5},
                         "shots_actual": 8}]})
    # Realer Lesekanal: hw3-Reihen kommen wortgetreu zurueck
    dok = _roh(HW3)
    cal = pq.lese_readout_cal_reihen(dok)
    assert len(cal) == 2
    assert [r["name"] for r in cal] == ["cal_2q", "cal_3q"]
    assert cal[0] == {"name": "cal_2q", "kind": "readout_cal", "arm": None,
                      "set": None, "P": None, "rep": None, "r": None,
                      "shots_actual": 8192,
                      "counts": {"00": 8176, "10": 10, "01": 6}}
    # Randflip-Anteile (little-endian: Label-Char rechts = Qubit 0)
    rf1 = pq.rand_flip_anteile(cal[0])
    assert rf1 == {0: F(3, 4096), 1: F(5, 4096)}
    assert pq.rand_flip_anteile(cal[1]) == \
        {0: F(3, 8192), 1: F(1, 4096), 2: F(3, 4096)}
    dok_k = _roh(KS)
    cal_k = pq.lese_readout_cal_reihen(dok_k)
    assert len(cal_k) == 2
    rf = pq.rand_flip_anteile(cal_k[0])
    assert rf == {0: F(13, 8192), 1: F(7, 4096)}
    assert pq.rand_flip_anteile(cal_k[1]) == \
        {0: F(27, 8192), 1: F(9, 8192), 2: F(17, 8192)}
    dok_sv = _roh(SV)
    cal_sv = pq.lese_readout_cal_reihen(dok_sv)
    assert len(cal_sv) == 2
    # gesaettigte Kalibrier-Reihen des SV-Spiegels: Randflip 0 exakt
    assert pq.rand_flip_anteile(cal_sv[0]) == {0: 0, 1: 0}
    assert pq.rand_flip_anteile(cal_sv[1]) == {0: 0, 1: 0, 2: 0}