# -*- coding: utf-8 -*-
"""EXPERIMENT 051 (H-RAM-Q-6 Leg D2/D3) — K2-Eval-Beweise + Artefakt-Pins.

Ohne QPU-Kontakt bewiesen: die Wrapper-Bindings (gegen die committeten
Artefakte Raw + Gate), die Degenerat-Kontroll-Abzweigung (jede t3/t4/t5
/t6-Verletzung), die Eligible-Zaehlung ('8 von 13' — NUR verdict|-P),
der m0-Auszug aus der Zugtabelle (NULL-MODELL, nie re-fit), die
verdict_map-Quelle (Prereg, keine Modul-Kopie), Residuum-Konsistenz
zwischen den beiden Artefakten, und die committeten Pins (inherited
REFUTED bei 0 kappa-low, n_elig 12/13, D2-Kein-Transfer ueber alle 6
Member, D3 4/12, Komposit; registered_expectation REFUTED/REFUTED
GEHOLDEN).
"""
import json
from copy import deepcopy

import pytest

import pt_ram_q_hardware3_aer as h3a
import pt_ram_q6_k2 as k2
import pt_ram_q6_k2_eval as ev

FRESH_P = {
    "q3_d3": [223, 263, 317, 419, 503, 647, 727, 829],
    "q5_d5": [503, 587, 647, 709, 727],
}
FRESH_CAL_P = {
    "q3_d3": [181, 229, 283, 379, 467, 613, 691, 797],
    "q5_d5": [467, 547, 613, 673, 691],
}


def test_check_raw_real_binding():
    rep = ev.check_raw()
    assert rep["raw_binding_ok"] is True and rep["gate_binding_ok"] is True
    assert rep["job_id"] == "davfridj371s73dmqstg"
    assert rep["counts_md5_rekomputiert"] == \
        "72f6729ac9261f50b5bfc9e56c6d7e46"
    assert rep["isa_totals"] == {"optimization_level": 3,
                                 "seed_transpiler": 7,
                                 "isa_2q_total": 559, "isa_2q_max": 84}
    assert rep["banned_abwesend"] == list(ev.BANNED_IN_RAW)
    assert "verdict" in rep["banned_abwesend"]


def test_check_raw_bricht_bei_counts_tamper(tmp_path):
    raw = deepcopy(k2._load_json(k2.RAW_PATH))
    raw["counts_md5"] = "0" * 32
    path = tmp_path / "t_md5.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(AssertionError, match="counts"):
        ev.check_raw(raw_path=str(path))


def test_check_raw_bricht_bei_job_tamper(tmp_path):
    raw = deepcopy(k2._load_json(k2.RAW_PATH))
    raw["job_meta"]["job_id"] = "andererjob123"
    path = tmp_path / "t_job.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(AssertionError):
        ev.check_raw(raw_path=str(path))


def test_check_raw_bricht_bei_leg_tamper(tmp_path):
    raw = deepcopy(k2._load_json(k2.RAW_PATH))
    raw["leg"] = "D1-LEG"
    path = tmp_path / "t_leg.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(AssertionError):
        ev.check_raw(raw_path=str(path))


def test_check_raw_bricht_bei_verdict_kanal(tmp_path):
    raw = deepcopy(k2._load_json(k2.RAW_PATH))
    raw["verdict"] = "K2_CONFIRMED"
    path = tmp_path / "t_banned.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(AssertionError, match="verdict"):
        ev.check_raw(raw_path=str(path))


def test_check_raw_bricht_bei_gate_tamper(tmp_path):
    with open(k2.ISA_GATE_PATH, encoding="utf-8") as fh:
        gate = json.load(fh)
    gate["max_two_q"] = 999
    path = tmp_path / "gate.json"
    path.write_text(json.dumps(gate), encoding="utf-8")
    with pytest.raises(AssertionError):
        ev.check_raw(gate_path=str(path))


def test_degenerat_kontrollen_abzweigung():
    ok_doc = {"kontrollen": {k: {"ok": True} for k in ev.KONTROLLEN_KEYS}}
    failed, flags = ev.degenerat_kontrollen(ok_doc)
    assert failed is False and all(flags.values())
    for violated in ev.KONTROLLEN_KEYS:
        doc = deepcopy(ok_doc)
        doc["kontrollen"][violated]["ok"] = False
        failed2, flags2 = ev.degenerat_kontrollen(doc)
        assert failed2 is True, violated
        assert flags2[violated] is False, violated


def test_eligible_verdict_zaehlt_nur_verdict_p():
    """'8 von 13': 12 eligible + 1 unter der Kante (317, realer Wert);
    Kalibrier-P mit |res| >= Kante zaehlen NICHT."""
    res = {}
    for arm, ps in FRESH_P.items():
        for P in ps:
            val = 0.011 if P != 317 else 0.006208416660086535
            res[f"verdict|{arm}|{P}"] = val
    res["cal|q3_d3|613"] = 1.0
    res["cal|q5_d5|673"] = -1.0
    assert ev.eligible_verdict(res) == 12
    # Grenzfaelle: exakt an der Kante eligible, knapp darunter nie:
    assert ev.eligible_verdict({"verdict|q3_d3|223": 0.01}) == 1
    assert ev.eligible_verdict({"verdict|q3_d3|223": 0.00999}) == 0
    assert ev.eligible_verdict({}) == 0


def test_m0_signs_aus_zugtabelle():
    m0 = ev.m0_signs_from_prereg(k2.load_frozen_prereg())
    assert m0 == {"q3_d3": 1.0, "q5_d5": -1.0}
    assert set(m0) == set(h3a.ARMS)


def test_vmap_aus_prereg_keine_modul_kopie():
    vm = ev.vmap()
    assert vm[k2.V_DEGENERAT] == \
        "geerbte Kontrollen (t3/t4/t5/t6) verletzt -> keine Auswertung"
    assert vm[k2.V_VOID_KAPPA] == \
        "geerbtes 044-Verdict VOID_CALIBRATION -> keine Auswertung"
    assert vm[k2.V_VOID_NOISE] == \
        "eligible gesamt < 8 von 13 -> keine Auswertung"
    assert vm["sonst"] == "Komposit D2:<...>|D3:<...>"
    # Komposit-Verdict greift per .get auf 'sonst':
    assert ev.vmap().get("D2:X|D3:Y", ev.vmap()["sonst"]) == \
        vm["sonst"]
    assert vm["sonst"] == k2.load_frozen_prereg()["k2_verdict_map"]["sonst"]


def test_res_fresh_konsistenz_zwischen_artefakten():
    inh = k2._load_json(k2.INHERITED_EVAL_PATH)
    assert ev.res_fresh_from(inh) == \
        k2._load_json(k2.EVAL_PATH)["res_fresh"]
    assert len(inh["punkte"]) == 26


# ----------------------------- committete Artefakte GEPINNT -------------
def test_inherited_artefakt_gepinnt():
    inh = k2._load_json(k2.INHERITED_EVAL_PATH)
    # Override-Lesart: h3e hasht bei uebergebenem prereg_path die
    # DATEI-BYTES (3926b0c79) — der gefrorene Vertragswert ef702976
    # (canonical ohne md5-Feld) lebt in stage3/gate + bp_md5_ok.
    assert inh["experiment"] == "044-ram-q-coherent-prep-error"
    assert inh["hypothesis"] == "H-RAM-Q-4"
    assert inh["prereg_md5"] == "3926b0c792bbd14ac3050ca540541a63"
    assert inh["raw_counts_md5"] == "72f6729ac9261f50b5bfc9e56c6d7e46"
    assert inh["raw_job_meta"]["job_id"] == "davfridj371s73dmqstg"
    assert inh["counts_md5_verified"] is True
    assert inh["b_p_provenance"]["prereg_md5_ok"] is True
    assert inh["status"] == "EVALUATED"
    assert inh["verdict"] == "H-RAM-Q-4_REFUTED"
    vi = inh["verdict_inputs"]
    assert vi["n_points"] == 26 and vi["n_holdout"] == 13
    assert vi["n_kappa_low_union"] == 0
    assert vi["n_below_sharp"] == 6
    assert vi["n_in_sharp"] == 7
    assert vi["n_above_ceiling_sharp"] == 0
    for key in ev.KONTROLLEN_KEYS:
        assert inh["kontrollen"][key]["ok"] is True, key


def test_k2_artefakt_gepinnt_komposit_refuted():
    doc = k2._load_json(k2.EVAL_PATH)
    assert doc["status"] == ev.STATUS_EVAL
    assert doc["prereg_md5"] == k2.PREREG_MD5
    assert doc["raw_provenance"]["job_id"] == "davfridj371s73dmqstg"
    assert doc["raw_provenance"]["counts_md5"] == \
        "72f6729ac9261f50b5bfc9e56c6d7e46"
    assert doc["n_elig_total"] == 12
    assert doc["verdict"] == \
        "D2:K2_D2_REFUTED_KEIN_TRANSFER|D3:" \
        "K2_D3_REFUTED_SIGN_KEIN_FUNKTION_VON_P"
    assert doc["registered_expectation"] == {"d2": "REFUTED",
                                             "d3": "REFUTED"}
    assert doc["k2_degenerat_kontrollen"]["failed"] is False
    assert sorted(doc["res_fresh"]) == sorted(
        [f"verdict|{a}|{P}" for a, ps in FRESH_P.items() for P in ps] +
        [f"cal|{a}|{P}" for a, ps in FRESH_CAL_P.items() for P in ps])


def test_k2_artefakt_d2_tabelle_gepinnt():
    d2 = k2._load_json(k2.EVAL_PATH)["d2"]
    assert d2["verdict"] == "K2_D2_REFUTED_KEIN_TRANSFER"
    assert d2["passing"] == [] and d2["ueber_alpha_only"] == []
    assert d2["alpha_family"] == pytest.approx(0.05 / 6)
    pins = {"L3": (5, 0.80615234375), "L5": (5, 0.80615234375),
            "L3L5": (6, 0.61279296875), "chi4": (6, 0.61279296875),
            "chi8": (3, 0.980712890625), "P10": (5, 0.80615234375)}
    for member, (hits, p) in pins.items():
        row = d2["members"][member]
        assert row["n"] == 12
        assert row["hits"] == hits, member
        assert row["p"] == p, member
        assert row["m0_comparable"] is True, member
        assert row["beats_m0"] is False, member
        assert row["m0"]["n"] == 12 and row["m0"]["hits"] == 6
        assert row["m0"]["p"] == 0.61279296875


def test_k2_artefakt_d3_tabelle_gepinnt():
    d3 = k2._load_json(k2.EVAL_PATH)["d3"]
    assert d3["verdict"] == "K2_D3_REFUTED_SIGN_KEIN_FUNKTION_VON_P"
    assert d3["n"] == 12 and d3["hits"] == 4
    assert d3["p"] == 0.927001953125
    assert d3["n_dropped_ohne_meldung"] == 0
    assert d3["alpha"] == 0.05
    pa = d3["per_arm_nicht_verdict_tragend"]
    assert pa["q3_d3"] == {"n": 7, "hits": 2, "nicht_verdict_tragend": True}
    assert pa["q5_d5"] == {"n": 5, "hits": 2, "nicht_verdict_tragend": True}
    # Vorzeichen der Residuen stimmen mit den Rows ueberein (hit-Regel):
    doc = k2._load_json(k2.EVAL_PATH)
    for r in d3["rows"]:
        assert r["hit"] == (r["res"] >= 0 and r["pred"] > 0 or
                            r["res"] < 0 and r["pred"] < 0), r


def test_k2_artefakt_res_fresh_punkte_pin():
    """Zwei Randpunkte des frischen Grids bit-exakt (Reproduktion)."""
    res = k2._load_json(k2.EVAL_PATH)["res_fresh"]
    assert res["verdict|q3_d3|317"] == -0.006208416660086535
    assert res["verdict|q5_d5|503"] == pytest.approx(-0.04698043148621178)
    assert res["cal|q3_d3|181"] == pytest.approx(0.029861739016199595)
    assert res["verdict|q5_d5|727"] == pytest.approx(-0.03648703408403353)