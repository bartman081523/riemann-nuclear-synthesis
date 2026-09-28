# -*- coding: utf-8 -*-
"""Tests fuer pt_ram_q_hardware3_rep_eval.py — Rep-Klassifikation der
Phase-11d-Wiederholung (Phase 12c, EXPERIMENT 047, H-RAM-Q-5), 0 QPU.

Gepinnt wird die REGISTRIERTE Klassifikations-Logik gegen das Prereg
(md5 be770a1e): die 5 H-RAM-Q-5a-Klassen in der Reihenfolge
INVALID -> VOID_ERNEUT -> SESSIONROBUST -> SESSION_SPEZIFISCH -> Reserve,
die Verdict-Map-Integritaet (Byte-Gleichheit als Gesetz-Nachweis), die
Holdout-kappa_hat-Floor-Union gegen das committete 11d-Band und die
committed-Artefakte (skipif: Eval-Docs noch nicht committed).
"""
import json
import os

import pytest

import pt_ram_q_hardware3_rep_eval as re_


# ------------------------------------------------------------------ Konstanten

class TestFrozenConstants:
    def test_verdict_strings_match_gefrorenem_eval(self):
        assert re_.V_REFUTED == "H-RAM-Q-4_REFUTED"
        assert re_.V_CONFIRMED == "H-RAM-Q-4_NOISE_LIFT_CONFIRMED"
        assert re_.V_COARSE == "H-RAM-Q-4_COARSE_HOLD_SHARP_MISS"
        assert re_.V_VOID == "H-RAM-Q-4_VOID_CALIBRATION"
        assert re_.V_DEGENERAT == "H-RAM-Q-4_DEGENERAT"
        assert re_.V_AMPL == "H-RAM-Q-4_INVALID_AMPLIFICATION"
        assert re_.V_INVALID == "EVALUATION_INVALID_CONTROLS_FAILED"
        assert re_.V_UNMATCHED == "VERDICT_MAP_UNMATCHED"

    def test_klassen_registriert(self):
        assert re_.K_INVALID == "H-RAM-Q-5a_INVALID"
        assert re_.K_VOID_ERNEUT == "H-RAM-Q-5a_VOID_ERNEUT"
        assert re_.K_SESSIONROBUST == "H-RAM-Q-5a_SESSIONROBUST"
        assert re_.K_SESSION_SPEZIFISCH == "H-RAM-Q-5a_SESSION_SPEZIFISCH"
        assert re_.K_RESERVE == "H-RAM-Q-5a_AMPL_ODER_DEGENERAT"

    def test_paths_und_gesetz(self):
        assert re_.EVAL_REP_PATH == "pt_ram_q_hardware3_eval_rep.json"
        assert re_.EVAL_11D_PATH == "pt_ram_q_hardware3_eval.json"
        assert re_.PREREG_PATH == "pt_ram_q_hardware3_rep_prereg.json"
        assert re_.REP_EVAL_PATH == "pt_ram_q_hardware3_rep_eval.json"
        assert re_.FLOOR_KAPPA == 0.81
        assert re_.W_B_DP == 0.02787029633307472


# ------------------------------------------------------------------- Hilfs-Docs

def _punkt(**over):
    base = dict(set="verdict", res_v3=0.0, kappa_hat=0.9,
                below_sharp=False, in_band_sharp=True)
    base.update(over)
    return base


def _doc(**over):
    base = {
        "verdict": re_.V_REFUTED,
        "verdict_inputs": {"n_below_sharp": 2, "n_in_sharp": 7,
                           "n_outside_sharp": 6, "n_kappa_low_union": 0,
                           "n_holdout": 13},
        "kontrollen": {k: {"ok": True} for k in re_.KONTROLLEN},
        "counts_md5_verified": True,
        "verdict_map_text": "MAP-v1",
        "echo_ladder": {"q3_d3": {"fit_kappa_block": 0.991324},
                        "q5_d5": {"fit_kappa_block": 0.727000}},
        "gamma_arm": {"q3_d3": {"gamma": 0.002293},
                      "q5_d5": {"gamma": 0.016039}},
        "punkte": {
            "verdict|q5_d5|467": _punkt(res_v3=-0.0841, below_sharp=True),
            "verdict|q5_d5|547": _punkt(res_v3=-0.0049),
            "verdict|q5_d5|673": _punkt(res_v3=-0.0334, below_sharp=True),
            "verdict|q3_d3|379": _punkt(res_v3=0.0294, kappa_hat=0.95),
            "cal|q5_d5|433": _punkt(set="cal", res_v3=-0.0608,
                                    below_sharp=True),
        },
        "raw_job_meta": {"job_id": "dat3gpqhcrkc73dtjmt0"},
        "raw_backend": "ibm_fez",
        "raw_counts_md5": "f1b214c961878d23a4ca6c257e5ee378",
    }
    base.update(over)
    return base


# ------------------------------------------------------------------- Integritaet

class TestKontrollenOk:
    def test_gruen(self):
        assert re_.kontrollen_ok(_doc()) is True

    def test_counts_md5_fehlt(self):
        assert re_.kontrollen_ok(_doc(counts_md5_verified=False)) is False

    @pytest.mark.parametrize("k", list(re_.KONTROLLEN))
    def test_jede_kontrolle_kippt(self, k):
        d = _doc()
        d["kontrollen"][k] = {"ok": False}
        assert re_.kontrollen_ok(d) is False

    def test_kontrolle_fehlt_ganz(self):
        d = _doc()
        del d["kontrollen"]["t6_mass_conservation"]
        assert re_.kontrollen_ok(d) is False

    def test_verdict_map_gleich(self):
        assert re_.verdict_map_gleich(_doc(), _doc()) is True
        assert re_.verdict_map_gleich(_doc(),
                                      _doc(verdict_map_text="MAP-v2")) \
            is False


# ------------------------------------------------------------------- classify_5a

class TestClassify5aRegistrierteReihenfolge:
    def test_sessionrobust(self):
        klasse, _ = re_.classify_5a(_doc(), _doc())
        assert klasse == re_.K_SESSIONROBUST

    def test_invalid_schlaegt_alles(self):
        d = _doc(verdict=re_.V_VOID)
        d["kontrollen"]["t4_negative_must_not_fire"] = {"ok": False}
        klasse, begr = re_.classify_5a(d, _doc())
        assert klasse == re_.K_INVALID
        assert "Kontrollen" in begr

    def test_invalid_verdict_map_geaendert(self):
        alt = _doc(verdict_map_text="MAP-alt")
        klasse, _ = re_.classify_5a(_doc(verdict=re_.V_CONFIRMED), alt)
        assert klasse == re_.K_INVALID

    def test_void_erneut(self):
        klasse, begr = re_.classify_5a(_doc(verdict=re_.V_VOID), _doc())
        assert klasse == re_.K_VOID_ERNEUT
        assert "0/26" in begr

    def test_session_spezifisch_confirmed(self):
        klasse, begr = re_.classify_5a(_doc(verdict=re_.V_CONFIRMED),
                                       _doc())
        assert klasse == re_.K_SESSION_SPEZIFISCH
        assert "NICHT stillschweigend" in begr

    def test_session_spezifisch_coarse(self):
        klasse, _ = re_.classify_5a(_doc(verdict=re_.V_COARSE), _doc())
        assert klasse == re_.K_SESSION_SPEZIFISCH

    def test_reserve_unmatched(self):
        klasse, begr = re_.classify_5a(_doc(verdict=re_.V_UNMATCHED),
                                       _doc())
        assert klasse == re_.K_RESERVE
        assert "VERDICT_MAP_UNMATCHED" in begr

    def test_reserve_ampl(self):
        klasse, _ = re_.classify_5a(_doc(verdict=re_.V_AMPL), _doc())
        assert klasse == re_.K_RESERVE

    def test_sessionrobust_begr_nennt_n_below_sharp(self):
        _, begr = re_.classify_5a(_doc(), _doc())
        assert "n_below_sharp >= 2" in begr


# ------------------------------------------------------------------- eval_5b

class TestEval5b:
    def test_echo_leiter_session_robust_q5(self):
        out = re_.eval_5b(_doc(), _doc(
            echo_ladder={"q3_d3": {"fit_kappa_block": 0.992660},
                         "q5_d5": {"fit_kappa_block": 0.731435}}))
        assert out["q5_d5"]["unter_floor_081"] is True
        assert out["q5_d5"]["session_robust_unter_floor"] is True
        assert out["q3_d3"]["unter_floor_081"] is False
        assert out["q3_d3"]["session_robust_unter_floor"] is False

    def test_union_im_band_11d(self):
        out = re_.eval_5b(_doc(), _doc(punkte={
            "verdict|a": _punkt(kappa_hat=0.8245),
            "verdict|b": _punkt(kappa_hat=0.9725)}))
        assert out["floor_union_11d"] == [0.8245, 0.9725]
        assert out["union_im_band_11d"] is True

    def test_union_unter_floor_kippt_band(self):
        out = re_.eval_5b(_doc(punkte={
            "verdict|a": _punkt(kappa_hat=0.8000),
            "verdict|b": _punkt(kappa_hat=0.9725)}), _doc())
        assert out["floor_union_11d"] == [0.9, 0.95]
        assert out["union_im_band_11d"] is False

    def test_floor_shift(self):
        out = re_.eval_5b(_doc(punkte={
            "verdict|a": _punkt(kappa_hat=0.9),
            "verdict|b": _punkt(kappa_hat=0.9)}), _doc(punkte={
            "verdict|a": _punkt(kappa_hat=0.8245),
            "verdict|b": _punkt(kappa_hat=0.9725)}))
        assert out["floor_union_neu"] == [0.9, 0.9]
        assert out["floor_union_11d"] == [0.8245, 0.9725]
        assert out["floor_shift_vs_11d"] == pytest.approx(0.9 - 0.8245)

    def test_gamma_arm_delta(self):
        out = re_.eval_5b(_doc(), _doc(
            gamma_arm={"q3_d3": {"gamma": 0.009106},
                       "q5_d5": {"gamma": 0.038129}}))
        assert out["gamma_arm"]["q3_d3"]["delta"] == pytest.approx(
            0.002293 - 0.009106)
        assert out["interpretationsguard"].startswith("Die Echo-Leiter")


# --------------------------------------------------- falsifikator / diff-Tabelle

class TestFalsifikatorUndTabelle:
    ALT = _doc(punkte={
        "verdict|q5_d5|467": _punkt(res_v3=-0.0318, below_sharp=True),
        "verdict|q5_d5|547": _punkt(res_v3=-0.0437, below_sharp=True),
        "verdict|q5_d5|673": _punkt(res_v3=-0.0548, below_sharp=True),
        "verdict|q3_d3|379": _punkt(res_v3=0.0289, kappa_hat=0.95),
        "cal|q5_d5|433": _punkt(set="cal", res_v3=-0.0367,
                                below_sharp=True),
    })

    def test_schnitt_und_nur_mengen(self):
        out = re_.falsifikator_vergleich(_doc(), self.ALT)
        assert out["below_sharp_neu"] == ["verdict|q5_d5|467",
                                          "verdict|q5_d5|673"]
        assert out["below_sharp_11d"] == ["verdict|q5_d5|467",
                                          "verdict|q5_d5|547",
                                          "verdict|q5_d5|673"]
        assert out["schnitt"] == ["verdict|q5_d5|467",
                                  "verdict|q5_d5|673"]
        assert out["nur_11d"] == ["verdict|q5_d5|547"]
        assert out["nur_neu"] == []
        assert out["set_identisch"] is False

    def test_kalibrier_p_zaehlt_nicht(self):
        # cal|q5_d5|433 below in BEIDEN — taucht in keinem Falsifikator auf
        # (lows() filtert auf set == "verdict"); auch nicht in den Residuen.
        out = re_.falsifikator_vergleich(_doc(), self.ALT)
        assert "cal|q5_d5|433" not in out["below_sharp_neu"]
        assert "cal|q5_d5|433" not in out["below_sharp_11d"]
        assert "cal|q5_d5|433" not in out["residuen"]

    def test_set_identisch(self):
        out = re_.falsifikator_vergleich(self.ALT, self.ALT)
        assert out["set_identisch"] is True
        assert out["schnitt"] == ["verdict|q5_d5|467",
                                  "verdict|q5_d5|547",
                                  "verdict|q5_d5|673"]

    def test_diff_tabelle_felder(self):
        rows = re_.diff_tabelle(_doc(), self.ALT)
        r = rows["verdict|q5_d5|673"]
        assert r["res_v3_delta"] == pytest.approx(-0.0334 - (-0.0548))
        assert r["below_sharp_neu"] is True
        assert r["below_sharp_11d"] is True
        c = rows["cal|q5_d5|433"]
        assert c["kappa_hat_delta"] == 0.0

    def test_diff_tabelle_467(self):
        rows = re_.diff_tabelle(_doc(), self.ALT)
        r = rows["verdict|q5_d5|467"]
        assert r["res_v3_neu"] == pytest.approx(-0.0841)
        assert r["res_v3_11d"] == pytest.approx(-0.0318)
        assert r["below_sharp_neu"] is True
        assert r["below_sharp_11d"] is True


# ------------------------------------------------------- committete Artefakte

REP_EVAL = "pt_ram_q_hardware3_rep_eval.json"
EVAL_REP = "pt_ram_q_hardware3_eval_rep.json"
EVAL_11D = "pt_ram_q_hardware3_eval.json"


@pytest.mark.skipif(not os.path.exists(REP_EVAL),
                    reason="Rep-Eval noch nicht committed")
class TestCommittedRepEval:
    @pytest.fixture(scope="class")
    def doc(self):
        with open(REP_EVAL, encoding="utf-8") as fh:
            return json.load(fh)

    def test_klassifikation_sessionrobust(self, doc):
        assert doc["h_ram_q_5a"]["klassifikation"] == "H-RAM-Q-5a_SESSIONROBUST"
        assert doc["h_ram_q_5a"]["verdict_tragend"] is True

    def test_verdict_neu_refuted(self, doc):
        assert doc["h_ram_q_5a"]["verdict_neu"] == "H-RAM-Q-4_REFUTED"
        assert doc["h_ram_q_5a"]["verdict_inputs_neu"]["n_below_sharp"] >= 2

    def test_integritaet_gruen(self, doc):
        assert doc["integritaet"]["kontrollen_ok"] is True
        assert doc["integritaet"]["verdict_map_gleich"] is True
        assert doc["integritaet"]["counts_md5_verified"] is True

    def test_prereg_md5_gepinnt(self, doc):
        assert doc["prereg_md5_file"] == "be770a1ec904cb392d7c70e2bfa364d3"

    def test_5b_diagnostik_nicht_verdict_tragend(self, doc):
        assert "NICHT Teil der gefrorenen" in \
            doc["h_ram_q_5b"]["interpretationsguard"]
        assert doc["h_ram_q_5b"]["q5_d5"]["session_robust_unter_floor"] \
            is True

    def test_falsifikator_schnitt(self, doc):
        f = doc["falsifikator_vergleich"]
        assert f["schnitt"] == ["verdict|q5_d5|467", "verdict|q5_d5|673"]
        assert f["nur_11d"] == ["verdict|q5_d5|547"]

    def test_governance_kein_re_decide(self, doc):
        t = doc["verdict_governance"]["kein_stilles_re_decide"]
        assert "bleibt als committetes Session-1-Verdict" in t
        assert "DEMSELBEN gefrorenen Gesetz" in t

    def test_sessions_tabelle_26_punkte(self, doc):
        with open(EVAL_REP, encoding="utf-8") as fh:
            n = len(json.load(fh)["punkte"])
        assert len(doc["sessions_differenz_tabelle"]) == n


@pytest.mark.skipif(not (os.path.exists(EVAL_REP)
                         and os.path.exists(EVAL_11D)),
                    reason="Eval-Docs noch nicht committed")
class TestGegenCommittedDocsRekonstruierbar:
    def test_klassifikation_aus_docs_reproduzierbar(self):
        doc_neu = json.load(open(EVAL_REP, encoding="utf-8"))
        doc_alt = json.load(open(EVAL_11D, encoding="utf-8"))
        klasse, _ = re_.classify_5a(doc_neu, doc_alt)
        assert klasse == "H-RAM-Q-5a_SESSIONROBUST"

    def test_verdict_map_byte_gleich_beide_sessions(self):
        doc_neu = json.load(open(EVAL_REP, encoding="utf-8"))
        doc_alt = json.load(open(EVAL_11D, encoding="utf-8"))
        assert doc_neu["verdict_map_text"] == doc_alt["verdict_map_text"]