"""Kanal-Schicht (Phase B): EXAKTER Diagonal-Zweig + ABGELEITET-Kraus.

EXAKT-Zweig: Fraction-Pflicht auf Vektor UND Parameter mit exakten
Guard-Texten; ABGELEITET-Schicht: float-Kraus-Saetze nur als Kreuz-Anker
mit absoluten Toleranzen (numpy), nie Quelle einer EXAKT-Zeile.
Herkunfts-Achse: geschätzt -> GESAMPFELT, kalibriert+/abgeleitet ->
ABGELEITET, exakt-definiert -> EXAKT (Param.garantie-Routing); die
Kanal-Typen depolarisiert/abklingen/dephasieren/auslese tragen ihre
Qubits-Pflichten ex ante.
"""
import os
import sys
from fractions import Fraction as F

import numpy as np
import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)
try:
    import primequant as pq
    import primequant.channels as ch
except ImportError:  # editable install fehlt: src-Fallback
    sys.path.insert(0, os.path.join(_REPO, "src"))
    import primequant as pq
    import primequant.channels as ch


def _exakt_param(name: str, wert: F) -> "ch.Param":
    return ch.Param(name, wert, "exakt-definiert")


def test_param_garantie_routings():
    gesch = ch.Param("p1", F(1, 2), "geschätzt:Hypothese").garantie()
    assert gesch.klasse == "GESAMPFELT"
    assert gesch.herkunft == "geschätzt:Hypothese"
    assert gesch.grenze is None
    kalib = ch.Param("ro", F(1, 64),
                     "kalibriert+2026-09-28T07:54:54+00:00").garantie()
    assert kalib.klasse == "ABGELEITET"
    assert kalib.herkunft.startswith("kalibriert+")
    abgl = ch.Param("x", F(1, 3), "abgeleitet").garantie()
    assert abgl.klasse == "ABGELEITET"
    assert abgl.herkunft == "abgeleitet"
    exakt = ch.Param("l", F(1, 2), "exakt-definiert").garantie()
    assert exakt.klasse == "EXAKT"
    assert exakt.grenze is None
    with pytest.raises(ValueError,
                       match=r"herkunft braucht kalibriert\+"):
        ch.Param("x", F(1, 2), "kalibriert").garantie()
    # int wird Fraction; bool bleibt bool (Verweigerung)
    assert ch.Param("n", 2, "exakt-definiert").wert == F(2)
    with pytest.raises(ValueError, match="erhalten bool"):
        ch.Param("b", True, "exakt-definiert")
    with pytest.raises(ValueError, match="erhalten str"):
        ch.Param("s", "x", "exakt-definiert")
    with pytest.raises(ValueError, match="nicht-endlich"):
        ch.Param("x", float("inf"), "geschätzt:B")
    with pytest.raises(ValueError, match="nicht-leeren Namen"):
        ch.Param("", F(1), "exakt-definiert")
    float_etikett = ch.Param("f", 0.5, "geschätzt:B").garantie()
    assert float_etikett.grenze is not None
    assert "ULP" in float_etikett.grenze


def test_depolarisiert_probs_pins():
    assert ch.depolarisiert_probs(pq.delta_vektor(2), F(1, 2), 4,
                                  qubits=[0]) == [F(3, 4), F(1, 4), 0, 0]
    # dieselbe Misch-Formel bei breite 2 (qubits=None -> Qubit 0)
    assert ch.depolarisiert_probs(pq.delta_vektor(1), F(1, 2), 2) == \
        [F(3, 4), F(1, 4)]
    with pytest.raises(ValueError, match=r"lambda ausserhalb \[0,1\]"):
        ch.depolarisiert_probs(pq.delta_vektor(2), F(3, 2), 4, qubits=[0])
    with pytest.raises(ValueError, match="Probvektor-Länge 8 != breite 4"):
        ch.depolarisiert_probs(pq.delta_vektor(3), F(1, 2), 4, qubits=[0])
    with pytest.raises(ValueError, match=r"doppelte Qubits: \[0, 0\]"):
        ch.depolarisiert_probs(pq.delta_vektor(2), F(1, 2), 4, qubits=[0, 0])
    with pytest.raises(ValueError, match=r"ausserhalb 0..1"):
        ch.depolarisiert_probs(pq.delta_vektor(2), F(1, 2), 4, qubits=[3])
    with pytest.raises(ValueError, match="float-Eintrag im EXAKT-Zweig"):
        ch.depolarisiert_probs([0.5, 0.5], F(1, 2), 2)


def test_abklingen_probs_pins():
    assert ch.abklingen_probs(pq.delta_vektor(2, 3), F(1, 2), 4) == \
        [F(1, 4)] * 4
    assert ch.abklingen_probs(pq.delta_vektor(2, 2), F(1, 2), 4) == \
        [F(1, 2), 0, F(1, 2), 0]
    with pytest.raises(ValueError, match=r"gamma ausserhalb \[0,1\]"):
        ch.abklingen_probs(pq.delta_vektor(2), F(3, 2), 4)
    with pytest.raises(ValueError, match="Probvektor-Länge 2 != breite 4"):
        ch.abklingen_probs(pq.delta_vektor(1), F(1, 2), 4)
    with pytest.raises(ValueError, match=r"doppelte Qubits: \[1, 1\]"):
        ch.abklingen_probs(pq.delta_vektor(2), F(1, 2), 4, qubits=[1, 1])


def test_dephasieren_auslese_pins():
    # Dephasieren ist auf der Diagonale die Identitaet
    assert ch.dephasieren_probs([F(1, 4), F(3, 4)], F(1, 4), 2) == \
        [F(1, 4), F(3, 4)]
    assert ch.dephasieren_probs(pq.delta_vektor(2), F(1, 2), 4) == \
        [1, 0, 0, 0]
    with pytest.raises(ValueError, match=r"gamma_phi ausserhalb \[0,1\]"):
        ch.dephasieren_probs(pq.delta_vektor(2), F(3, 2), 4)
    assert ch.auslese_probs(pq.delta_vektor(1), F(1, 4), 2) == \
        [F(3, 4), F(1, 4)]
    assert ch.auslese_probs(pq.delta_vektor(2, 3), F(1, 4), 4) == [
        F(1, 16), F(3, 16), F(3, 16), F(9, 16)]
    with pytest.raises(ValueError, match=r"ro ausserhalb \[0,1\]"):
        ch.auslese_probs(pq.delta_vektor(1), F(3, 2), 2)
    with pytest.raises(ValueError, match="Probvektor-Länge 2 != breite 4"):
        ch.auslese_probs(pq.delta_vektor(1), F(1, 4), 4)


def test_apply_diag_und_verkette():
    dep0 = ch.Kanal("depolarisiert",
                    _exakt_param("lam", F(1, 2)), qubits=(0,))
    out = ch.apply_to_probs_diag(pq.delta_vektor(2), dep0, 4)
    assert out == [F(3, 4), F(1, 4), 0, 0]
    # dephasieren danach: Diagonale bleibt, Ergebnis identisch
    dek = ch.Kanal("dephasieren", _exakt_param("gphi", F(1, 4)))
    assert ch.apply_to_probs_diag(out, dek, 4) == out
    assert ch.verkette_diag(pq.delta_vektor(2), [dep0, dek], 4) == out
    # float-Param verweigert im EXAKT-Zweig
    f_kanal = ch.Kanal("depolarisiert",
                       ch.Param("lam", 0.5, "geschätzt:Hypothese"),
                       qubits=(0,))
    with pytest.raises(ValueError, match="float-Param 'lam' im EXAKT-Zweig"):
        ch.apply_to_probs_diag(pq.delta_vektor(2), f_kanal, 4)
    with pytest.raises(ValueError, match="float-Eintrag im EXAKT-Zweig"):
        ch.verkette_diag([0.5, 0.5], [], 2)
    with pytest.raises(ValueError, match="Probvektor-Summe 2/3 != 1"):
        ch.verkette_diag([F(1, 3), F(1, 3)], [], 2)


def test_kanal_guards():
    with pytest.raises(ValueError,
                       match="unbekannter Kanal-Typ 'quantenkanal'"):
        ch.Kanal("quantenkanal", _exakt_param("p", F(1, 2)), qubits=(0,))
    with pytest.raises(ValueError,
                       match="auslese wirkt auf alle Register-Qubits"):
        ch.Kanal("auslese", _exakt_param("ro", F(1, 8)), qubits=(0,))
    with pytest.raises(ValueError,
                       match="depolarisiert verlangt.qubits nicht-leer"):
        ch.Kanal("depolarisiert", _exakt_param("lam", F(1, 2)), qubits=())
    with pytest.raises(ValueError,
                       match="abklingen verlangt.qubits nicht-leer"):
        ch.Kanal("abklingen", _exakt_param("g", F(1, 4)), qubits=())


def test_kraus_depolarisiert_pins():
    ops = ch.kraus_depolarisiert(0.5, 1)
    assert len(ops) == 4
    assert ops[0][0, 0].real == pytest.approx(0.7905694150420949, abs=1e-15)
    assert ops[0][1, 1].real == pytest.approx(0.7905694150420949, abs=1e-15)
    # ops[1] ist X (real belegt); Y haette hier Imaginaerteil
    assert ops[1][0, 1].real == pytest.approx(0.3535533905932738, abs=1e-15)
    assert ops[1][0, 1].imag == pytest.approx(0.0, abs=1e-15)
    with pytest.raises(ValueError, match=r"lambda ausserhalb \[0,1\]"):
        ch.kraus_depolarisiert(1.5, 1)
    with pytest.raises(ValueError, match="anzahl_qubits muss >= 1"):
        ch.kraus_depolarisiert(0.5, 0)


def test_kraus_abklingen_dephasieren_pins():
    ops_a = ch.kraus_abklingen(0.5)
    assert len(ops_a) == 2
    assert ops_a[0][0, 0].real == pytest.approx(1.0, abs=1e-15)
    assert ops_a[0][1, 1].real == pytest.approx(0.7071067811865476, abs=1e-15)
    # A1 = sqrt(gamma) * |0><1| tritt denselben Decay-Wert aus
    assert ops_a[1][0, 1].real == pytest.approx(0.7071067811865476, abs=1e-15)
    ops_d = ch.kraus_dephasieren(0.25)
    assert ops_d[0][0, 0].real == pytest.approx(0.8660254037844386, abs=1e-15)
    assert ops_d[1][0, 0].real == pytest.approx(0.5, abs=1e-15)
    with pytest.raises(ValueError, match=r"gamma ausserhalb \[0,1\]"):
        ch.kraus_abklingen(1.5)
    with pytest.raises(ValueError, match=r"gamma_phi ausserhalb \[0,1\]"):
        ch.kraus_dephasieren(1.5)


def test_relaxation_und_verwirrung():
    a_dd, offset, koh = ch.relaxation_wahrscheinlichkeiten(100.0, 80.0, 20.0)
    assert a_dd == pytest.approx(0.8187307530779818, abs=1e-15)
    assert offset == pytest.approx(0.0, abs=1e-15)
    assert koh == pytest.approx(0.7788007830714049, abs=1e-15)
    with pytest.raises(ValueError, match="T1/T2 muessen > 0"):
        ch.relaxation_wahrscheinlichkeiten(0.0, 80.0, 20.0)
    with pytest.raises(ValueError, match="CP-Grenze"):
        ch.relaxation_wahrscheinlichkeiten(100.0, 300.0, 20.0)
    mat = ch.auslese_verwirrung(0.25, 2)
    assert list(mat[0]) == pytest.approx([0.5625, 0.1875, 0.1875, 0.0625],
                                         abs=1e-12)
    assert np.allclose(mat.diagonal(), 0.5625)
    assert list(mat.sum(axis=1)) == pytest.approx([1.0] * 4, abs=1e-12)
    with pytest.raises(ValueError, match=r"ro ausserhalb \[0,1\]"):
        ch.auslese_verwirrung(1.5, 2)
    with pytest.raises(ValueError, match="nq muss >= 1 sein"):
        ch.auslese_verwirrung(0.25, 0)


def test_apply_kraus_anker():
    rho = ch.rho_diag([1.0, 0.0, 0.0, 0.0])
    ops_dep = ch.kraus_depolarisiert(0.5, 1)
    out = ch.apply_kraus(rho, ops_dep, [0])
    assert np.allclose(out, np.diag([0.75, 0.25, 0.0, 0.0]), atol=1e-12)
    assert ch.kohärenz_max(out) == pytest.approx(0.0, abs=1e-12)
    with pytest.raises(ValueError, match="rho muss quadratisch sein"):
        ch.apply_kraus(np.zeros((2, 3)), ops_dep, [0])
    with pytest.raises(ValueError, match=r"doppelte Qubits: \[0, 0\]"):
        ch.apply_kraus(rho, ops_dep, [0, 0])
    with pytest.raises(ValueError, match=r"ausserhalb 0..1"):
        ch.apply_kraus(rho, ops_dep, [3])
    with pytest.raises(ValueError, match=r"Kraus-Operator hat Form \(1, 2\)"):
        ch.apply_kraus(rho, [np.zeros((1, 2))], [0])


def test_channel_model_direkt_path():
    ops = {"sx": 6, "rz": 5, "measure": 2, "cz": 1, "x": 1}
    modell = ch.ChannelModel.aus_op_counts(ops, {
        "p_1q": ch.Param("p_1q", F(1, 64), "geschätzt:Hypothese"),
        "p_2q": ch.Param("p_2q", F(1, 16), "geschätzt:Hypothese")})
    assert modell.fam_zuehler == {"1q": 7, "virtuell": 5, "auslese": 2,
                                  "2q": 1}
    # p_eff = 1 - (1-p)^k ganzrational exakt
    assert modell.p_1q_eff == F(459065871937, 4398046511104)  # 1-(63/64)^7
    assert modell.p_2q_eff == F(1, 16)
    garantie = modell.garantie()
    assert garantie.klasse == "GESAMPFELT"
    assert garantie.herkunft == "abgeleitet"
    assert garantie.grenze is None
    assert garantie.quelle == "ISA-Op-Counts + Params p_1q;p_2q"
    als_json = modell.als_json()
    assert als_json["p_2q_eff"] == "1/16"
    assert als_json["p_1q_eff"] == str(F(459065871937, 4398046511104))
    assert set(als_json["params"]) == {"p_1q", "p_2q"}


def test_channel_model_ratio_path():
    ops = {"sx": 6, "rz": 5, "measure": 2, "cz": 1, "x": 1}
    modell = ch.ChannelModel.aus_op_counts(ops, {
        "p_1q": ch.Param("p_1q", F(1, 64), "geschätzt:Hypothese"),
        "ratio_2q": ch.Param("ratio_2q", 4, "geschätzt:Hypothese")})
    assert sorted(modell.params.keys()) == ["p_1q", "p_2q", "ratio_2q"]
    abgeleitet = modell.params["p_2q"]
    # Dict-Schluessel "p_2q", Param-Name "p_2q_abgeleitet"
    assert abgeleitet.name == "p_2q_abgeleitet"
    assert abgeleitet.wert == F(1, 16)
    assert abgeleitet.herkunft == \
        "geschätzt:p_1q*ratio_2q — Klasse der schwaechsten Eingabe"
    assert "ratio_2q" in modell.params          # Eingabe bleibt registriert
    assert modell.garantie().klasse == "GESAMPFELT"
    als_json = modell.als_json()
    assert als_json["params"]["p_2q"]["herkunft"] == abgeleitet.herkunft


def test_channel_model_exakt_garantie():
    ops = {"sx": 6, "rz": 5, "measure": 2, "cz": 1, "x": 1}
    modell = ch.ChannelModel.aus_op_counts(ops, {
        "p_1q": ch.Param("p_1q", F(1, 64), "exakt-definiert"),
        "p_2q": ch.Param("p_2q", F(1, 16), "exakt-definiert")})
    garantie = modell.garantie()
    assert garantie.klasse == "EXAKT"
    assert garantie.herkunft == "exakt-definiert"
    assert garantie.grenze is None
    assert garantie.quelle == "ISA-Op-Counts + Params p_1q;p_2q"


def test_channel_model_guards():
    ops = {"sx": 6, "rz": 5, "measure": 2, "cz": 1, "x": 1}
    exakt_1q = ch.Param("p_1q", F(1, 64), "exakt-definiert")
    exakt_2q = ch.Param("p_2q", F(1, 16), "exakt-definiert")
    with pytest.raises(ValueError, match="unbekannter ISA-Op-Name 'gate_zzz'"):
        ch.ChannelModel.aus_op_counts({"gate_zzz": 1},
                                      {"p_1q": exakt_1q, "p_2q": exakt_2q})
    with pytest.raises(ValueError, match="negativer Op-Count x=-1"):
        ch.ChannelModel.aus_op_counts({"x": -1},
                                      {"p_1q": exakt_1q, "p_2q": exakt_2q})
    with pytest.raises(ValueError, match=r"params verlangt p_1q"):
        ch.ChannelModel.aus_op_counts(ops, {"p_2q": exakt_2q})
    with pytest.raises(ValueError, match="ISA-Report ohne 1q-Tore"):
        ch.ChannelModel.aus_op_counts({"measure": 2},
                                      {"p_1q": exakt_1q, "p_2q": exakt_2q})
    with pytest.raises(ValueError, match="p_1q muss ganzrational sein"):
        ch.ChannelModel.aus_op_counts(ops, {
            "p_1q": ch.Param("p_1q", 0.01, "geschätzt:B"),
            "p_2q": exakt_2q})
    with pytest.raises(ValueError, match="p_2q muss ganzrational sein"):
        ch.ChannelModel.aus_op_counts(ops, {
            "p_1q": exakt_1q,
            "p_2q": ch.Param("p_2q", 0.05, "geschätzt:B")})
    with pytest.raises(ValueError, match="ratio_2q muss ganzrational sein"):
        ch.ChannelModel.aus_op_counts(ops, {
            "p_1q": exakt_1q,
            "ratio_2q": ch.Param("ratio_2q", 4.0, "geschätzt:B")})
    with pytest.raises(ValueError,
                       match=r"params verlangt p_2q ODER \(p_1q \+ ratio_2q\)"):
        ch.ChannelModel.aus_op_counts(ops, {"p_1q": exakt_1q})


def test_herkunft_vererbt():
    gemischt = ch.herkunft_vererbt(
        [ch.Param("a", F(1), "geschätzt:B"),
         ch.Param("b", F(1), "abgeleitet")], "x*y")
    assert gemischt == "geschätzt:x*y — Klasse der schwaechsten Eingabe"
    sauber = ch.herkunft_vererbt(
        [ch.Param("a", F(1), "abgeleitet"),
         ch.Param("b", F(1), "kalibriert+2026-09-28T07:54:54+00:00")], "x+y")
    assert sauber == "abgeleitet"