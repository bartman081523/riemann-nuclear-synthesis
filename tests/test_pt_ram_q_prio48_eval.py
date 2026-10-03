# -*- coding: utf-8 -*-
"""Tests fuer pt_ram_q_prio48_eval.py — gefrorene 055-Auswertung, 0 QPU.

PRE-RUN-Praezedenz (044-Verdraengung): hier wird NUR Modul-Statik gepinnt —
Delegationen ins h3-Eval-Fundament, die frozen Verdict-Maschine
(entscheide_verdict_055: Kontrolle-Void > Refit-Void > D.7 > P-Transfer >
Mixed > UNDETERMINED), die geschlossen rechenbaren OLS-/D.5-Formeln, die
committed_F-Anker (Re-Identifikation an den S1-gamma_arm-Reihen)und die
registrierten Verbatim-Register des Preregs. Der echte Fez-Job ist noch
NICHT gelaufen: KEINE Raw-/Eval-Artefakt-Fixtures (die kommen nach dem
Roh-Commit, h3e-Praezedenz test_eval_schema_and_verdict).
"""
import json
import math

import pytest

import pt_ram_q_hardware2_eval as e2
import pt_ram_q_hardware_aer as aer
import pt_ram_q_hardware3_eval as h3e
import pt_ram_q_prio48 as p48
import pt_ram_q_prio48_eval as ev
import pt_ram_q_prio48_stage3aer as s3a

KONTROLLE_VOID = "EVALUATION_INVALID_KONTROLLE_GESCHEITERT"


# ------------------------------------------------------------- Delegationen

class TestDelegation:
    def test_module_identities(self):
        assert ev.aer is aer
        assert ev.h3e is h3e
        assert ev.e2 is e2
        assert ev.s3a is s3a
        assert ev.p48.__name__ == "pt_ram_q_prio48"

    def test_foundation_functions_identity(self):
        # Die Formeln sind EINE Quelle: h3e-Fundament, eval-055 delegiert.
        assert ev._folded_share is h3e._folded_share
        assert ev.fit_gamma_arm is h3e.fit_gamma_arm
        assert ev.center_v3 is h3e.center_v3
        assert ev.anchor_r1_name is h3e.anchor_r1_name

    def test_path_aliases(self):
        assert ev.RAW_PATH == p48.RAW_PATH
        assert ev.EVAL_PATH == p48.EVAL_PATH
        assert ev.ISA_PATH == p48.ISA_REPORT_PATH
        assert ev.GATE_PATH == p48.ISA_GATE_PATH
        assert ev.STAGE3_PATH == s3a.RESULTS_PATH
        assert ev.PREREG_MD5 == "b7afc42c62a6da75b2e43dd3674f8965"
        # Live-Kreuzpin: ev-Freeze-Md5 == committetes Prereg-doc["md5"]
        assert ev.PREREG_MD5 == p48.load_frozen_prereg()["md5"]


# -------------------------------------------------------------- Konstanten

class TestFrozenVerdictMachine:
    def test_verdict_strings(self):
        assert ev.V_PHELD == "P_BOUND_TRANSFER_HELD"
        assert ev.V_D7 == "GEOMETRYBOUND_D7"
        assert ev.V_MIXED == "MIXED_PARTIAL"
        assert ev.V_UNDET == "UNDETERMINED"
        assert ev.REFIT_INVALID == "REFIT_INVALID_KAPPA"
        assert ev.F8_KIPPT == "SA-H9-5 KIPPT"
        assert ev.F8_BLEIBT == "SA-H9-5 BLEIBT"

    def test_verdict_map_crosslinks(self):
        pr = p48.load_frozen_prereg()
        assert set(pr["verdict_map"]) == {ev.V_PHELD, ev.V_D7,
                                          ev.V_MIXED, ev.V_UNDET}
        assert pr["safeguard_limits"]["kontrolle_void"] == KONTROLLE_VOID
        assert pr["safeguard_limits"]["void"].startswith(ev.REFIT_INVALID)


class TestDecideMatrix:
    @staticmethod
    def _call(**over):
        base = dict(t_fail_other=False, refit_invalid=False,
                    c1_q5=True, c1_q3=True, c2=True,
                    c3_fire_q5=False, c3_fire_q3=False)
        base.update(over)
        return ev.decide_verdict_055(**base)

    def test_all_clean_held(self):
        assert self._call() == ev.V_PHELD

    def test_kontrolle_void_primacy(self):
        # Kontrolle-Void schlaegt ALLES (Refit-Void, D.7, Fires, C1/C2).
        assert self._call(t_fail_other=True) == KONTROLLE_VOID
        assert self._call(t_fail_other=True, refit_invalid=True) \
            == KONTROLLE_VOID
        assert self._call(t_fail_other=True, refit_invalid=True,
                          c1_q5=False, c3_fire_q5=True) == KONTROLLE_VOID

    def test_refit_void_primacy(self):
        # Refit-Void schlaegt D.7 und PHELD (descriptiv-void, kein Verdict).
        assert self._call(refit_invalid=True) == ev.V_UNDET
        assert self._call(refit_invalid=True, c1_q5=False,
                          c3_fire_q5=True) == ev.V_UNDET
        assert self._call(refit_invalid=True, c1_q3=False) == ev.V_UNDET

    def test_d7_q5_branch(self):
        assert self._call(c1_q5=False, c3_fire_q5=True) == ev.V_D7
        assert self._call(c1_q5=False, c3_fire_q5=True, c1_q3=False,
                          c3_fire_q3=True) == ev.V_D7
        assert self._call(c1_q5=False, c3_fire_q5=True, c2=False) == ev.V_D7

    def test_q3_fire_alone_never_d7(self):
        # C3-Asymmetrie: q3-Feuer allein gibt KEIN D7 (D.7 braucht q5-Feuer).
        assert self._call(c1_q5=False, c1_q3=True, c3_fire_q3=True) \
            == ev.V_MIXED
        assert self._call(c1_q5=True, c1_q3=True, c2=True,
                          c3_fire_q3=True) == ev.V_MIXED

    def test_pheld_blocked_by_any_fire_or_c2(self):
        assert self._call(c3_fire_q3=True) == ev.V_MIXED
        assert self._call(c3_fire_q5=True, c1_q5=True) == ev.V_MIXED
        assert self._call(c2=False) == ev.V_MIXED
        assert self._call(c1_q3=False) == ev.V_MIXED
        assert self._call(c1_q5=False, c3_fire_q3=True) == ev.V_MIXED

    def test_undetermined_when_nothing_holds(self):
        assert self._call(c1_q5=False, c1_q3=False) == ev.V_UNDET
        assert self._call(c1_q5=True, c1_q3=False, c2=False,
                          c3_fire_q5=False) == ev.V_MIXED


# ------------------------------------------------------------------ Formeln

class TestFormulas:
    def test_ols_decomp_closed_form_n4(self):
        # (1,0),(2,1),(3,0),(4,2): beta=(−0.5, 0.5) exakt; ssres 3/2,
        # s2 3/4, sstot 11/4 -> r2 = 5/11; XtXi[1,1] = 1/5 -> se² = 3/20.
        f = ev._ols_decomp([1, 2, 3, 4], [0, 1, 0, 2])
        assert abs(f["intercept"] + 0.5) < 1e-9
        assert abs(f["gamma_ols"] - 0.5) < 1e-9
        assert abs(f["se_gamma"] - math.sqrt(0.15)) < 1e-9
        assert abs(f["resid_sd_ddof2"] - math.sqrt(0.75)) < 1e-9
        assert abs(f["r2"] - 5.0 / 11.0) < 1e-9
        assert f["n"] == 4

    def test_ols_decomp_degenerate_two_rows(self):
        # n=2 (ddof=2 -> Division 0/0 als Python-Float): Registrierter
        # Schutzbereich ist n>=5 (q5) / n>=8 (q3); n=2 CRASHT deterministisch.
        with pytest.raises(ZeroDivisionError):
            ev._ols_decomp([1.0, 2.0], [1.0, 1.0])

    def test_se_no_int_closed_form(self):
        cps = [1, 2, 3]
        dls = [6, 5, 1]
        gam, se = ev._se_no_int(cps, dls)
        assert abs(gam - 19.0 / 14.0) < 1e-9
        # scatter = [65,32,-43]/14 -> |scatter|^2 = 7098/196; se^2 =
        # 7098/(196*2*14) = 7098/5488.
        assert abs(se - math.sqrt(7098.0 / 5488.0)) < 1e-9


class TestSEProvenanceS1:
    @staticmethod
    def _rows():
        with open(p48.H3_EVAL_S1, encoding="utf-8") as fh:
            d = json.load(fh)
        rows = d["gamma_arm"]["q5_d5"]["rows"]
        cps = [r["c_p"] for r in rows]
        dls = [r["delta_cal"] for r in rows]
        return cps, dls

    def test_d5_se_law_consistent(self):
        cps, dls = self._rows()
        gam, se = ev._se_no_int(cps, dls)
        assert abs(se - p48.SE_NO_INT_S1_Q5_CAL) <= 1e-12
        mean_c = float(sum(cps) / len(cps))
        assert abs(mean_c - 4.726980333354999) <= 1e-12
        assert abs(se * mean_c - p48.SE_C_MEAN_S1) <= 1e-12
        assert abs(se * math.sqrt(5.0 / 16.0)
                   - p48.SQRT_EXPECT_N16) <= 1e-12
        # law-konsistent: gam == gamma_arm["q5_d5"]["gamma"]
        d = json.load(open(p48.H3_EVAL_S1, encoding="utf-8"))
        assert abs(gam - d["gamma_arm"]["q5_d5"]["gamma"]) <= 1e-12


# ---------------------------------------------------- committed_F-Anker (F)

class TestCommittedFAnchors:
    @staticmethod
    def _gamma_rows(arm):
        with open(p48.H3_EVAL_S1, encoding="utf-8") as fh:
            d = json.load(fh)
        rows = d["gamma_arm"][arm]["rows"]
        cps = [r["c_p"] for r in rows]
        dls = [r["delta_cal"] for r in rows]
        return cps, dls

    def test_q5_anchors_reidentified(self):
        pr = p48.load_frozen_prereg()
        anc = pr["fprio8_refit"]["committed_F_anchors"]["q5"]
        assert anc["n"] == 5
        assert anc["gamma_ols"] == 0.21586104749721277
        assert anc["se_gamma"] == 0.1254448714861779
        assert anc["resid_sd"] == 0.023936865145634485
        assert anc["r2"] == 0.4967312299110952
        cps, dls = self._gamma_rows("q5_d5")
        f = ev._ols_decomp(cps, dls)
        assert abs(f["gamma_ols"] - anc["gamma_ols"]) <= 1e-9
        assert abs(f["se_gamma"] - anc["se_gamma"]) <= 1e-9
        assert abs(f["resid_sd_ddof2"] - anc["resid_sd"]) <= 1e-9
        assert abs(f["r2"] - anc["r2"]) <= 1e-9

    def test_q3_anchors_reidentified_structural_omission(self):
        # q3-Anker ohne gamma_ols-Feld (strukturelle Auslassung im Freeze) —
        # die drei registrierten Stats treffen trotzdem bit-nahe.
        pr = p48.load_frozen_prereg()
        anc = pr["fprio8_refit"]["committed_F_anchors"]["q3"]
        assert "gamma_ols" not in anc
        assert anc["n"] == 8
        assert anc["se_gamma"] == 0.012189383635140131
        assert anc["resid_sd"] == 0.009138844281032127
        assert anc["r2"] == 0.6525102051324765
        cps, dls = self._gamma_rows("q3_d3")
        f = ev._ols_decomp(cps, dls)
        assert abs(f["gamma_ols"] - 0.040914759036) <= 1e-6
        assert abs(f["se_gamma"] - anc["se_gamma"]) <= 1e-9
        assert abs(f["resid_sd_ddof2"] - anc["resid_sd"]) <= 1e-9
        assert abs(f["r2"] - anc["r2"]) <= 1e-9

    def test_gamma_committed_is_law_gamma(self):
        pr = p48.load_frozen_prereg()
        anc = pr["fprio8_refit"]["committed_F_anchors"]
        assert anc["q5"]["gamma_committed"] == 0.038128743451453374
        assert anc["q3"]["gamma_committed"] == 0.009105648402709013


# ---------------------------------------------------------- Verbatim-Register

class TestPreregRegistries:
    def test_fprio8_refit_verbatim(self):
        pr = p48.load_frozen_prereg()
        fr = pr["fprio8_refit"]
        assert fr["gamma_refit_q5"] == ("no-intercept LSQ gamma' = "
                                        "<c,Delta>/<c,c> ueber 16 Kal-Reihen "
                                        "(law-konsistent, fit_gamma_arm-"
                                        "Konvention)")
        assert fr["decomposition_F"] == ("OLS-mit-Achsenabschnitt X = "
                                         "[ones, c_p], se = sqrt(s2*XtXi[1,1]),"
                                         " resid_std ddof=2")
        prov = fr["d5_se_provenance"]
        assert "0.01197607825720734" in prov
        assert "0.1254448714861779" in prov
        assert "NICHT die (F)-OLS-SE" in prov
        f8 = fr["falsifikatorlinie_F_zeile_8"]
        assert "< 0.01" in f8
        assert "SA-H9-5 kippt" in f8 and "BLEIBT" in f8

    def test_c2_c3_criteria(self):
        pr = p48.load_frozen_prereg()
        c2 = pr["c2_criteria"]
        assert c2["q5_kern"] == "S2-below {467, 673} BOTH transfer (2/2)"
        assert c2["q5_zweitstufe_S1"] == ("{467, 547, 673} mindest 2/3 "
                                          "(547 session-spezifisch)")
        assert c2["q3"] == "klassenleer in S1/S2 — n/a"
        assert c2["w_b_doubleprime_pin"] == p48.W_B_DP
        c3 = pr["c3_geometry_counter"]
        assert c3["feuer_kriterium"] == ("rho(Delta-res, Delta-c) >= "
                                         "q95-exakt je Arm (q5: 0.7999…-Klasse,"
                                         " q3: 0.6190…-Klasse)")
        assert c3["verdict_role"] == ("NEIN-Feuern ist die C3-null-"
                                      "Voraussetzung der C1-Verdicts")

    def test_banned_and_vorprobe(self):
        pr = p48.load_frozen_prereg()
        assert pr["banned_from_raw"] == ["kappa", "ratio", "gamma", "band",
                                         "verdict", "res_v3", "center",
                                         "delta_cal"]
        cb = pr["c1_c_vorprobe"]
        assert cb["role"] == ("DESKRIPTIV registriert (KEIN Verdict-"
                              "Kriterium); Design unabhaengig vom Ausgang")
        assert cb["null"] == "exakt-perm (design_out)"


# ------------------------------------------------------------- Zeilen-Helfer

class TestArmRows:
    def test_arm_rows_synthetic_guards(self):
        pts = {
            "verdict|q3_d3|181": {"P": 229, "res_v3": None, "c_p": 4.5,
                                  "below_sharp": False, "kappa_hat": None},
            "verdict|q3_d3|0": {"P": 181, "res_v3": 0.25, "c_p": 4.0,
                                "below_sharp": True, "kappa_hat": 0.9},
            "cal|q3_d3|433": {"P": 433, "res_v3": 1.0, "c_p": 5.0,
                              "below_sharp": False, "kappa_hat": 0.85},
            "verdict|q5_d5|467": {"P": 467, "res_v3": -0.5, "c_p": 4.9,
                                  "below_sharp": True, "kappa_hat": 0.82},
        }
        rows = ev.arm_rows(pts, "q3_d3")
        assert sorted(rows) == ["cal", "verdict"]
        v = rows["verdict"]
        assert v["P"] == [181, 229]
        assert v["res"] == [0.25, None]
        assert v["c_p"] == [4.0, 4.5]
        assert v["below_sharp"] == [181]
        assert v["kappa"] == [0.9, None]
        q5 = ev.arm_rows(pts, "q5_d5")["verdict"]
        assert q5["P"] == [467] and q5["res"] == [-0.5]
        assert ev.arm_rows(pts, "q9_d9") == {}

    def test_arm_rows_matches_p48_on_files(self):
        for path, arm in ((p48.H3_EVAL_S1, "q5_d5"),
                          (p48.H3_EVAL_S1, "q3_d3"),
                          (p48.H3_EVAL_S2, "q5_d5"),
                          (p48.H3_EVAL_S2, "q3_d3")):
            with open(path, encoding="utf-8") as fh:
                d = json.load(fh)
            assert ev.arm_rows(d["punkte"], arm) == p48.arm_rows(path, arm)


class TestEchoFromEval:
    def test_echo_subdicts_pins(self):
        e1 = ev._echo_from_eval(p48.H3_EVAL_S1, "q5_d5")
        assert list(e1) == sorted(e1) == ["P", "fit_kappa_block",
                                          "fit_max_res_log", "kappa_r",
                                          "r1_konsistent_mit_kappa_hat_anker",
                                          "r1_shared_with_loschmidt",
                                          "repeats", "verdict_role"]
        assert e1["P"] == 467
        assert e1["repeats"] == [1, 2, 4, 8]
        e3 = ev._echo_from_eval(p48.H3_EVAL_S2, "q3_d3")
        assert e3["P"] == 181
        assert abs(e3["fit_kappa_block"] - 0.9913237988399535) <= 1e-12

    def test_echo_r1_is_verdict_kappa(self):
        # r1_shared_with_loschmidt: kappa_r[r1] == kappa_hat der Anker-Zeile.
        for path, arm, P in ((p48.H3_EVAL_S1, "q5_d5", 467),
                             (p48.H3_EVAL_S1, "q3_d3", 181),
                             (p48.H3_EVAL_S2, "q5_d5", 467),
                             (p48.H3_EVAL_S2, "q3_d3", 181)):
            lad = ev._echo_from_eval(path, arm)
            if not lad.get("r1_shared_with_loschmidt"):
                continue
            vk = p48.arm_rows(path, arm)["verdict"]
            assert abs(lad["kappa_r"]["r1"] - vk["kappa"][vk["P"].index(P)]) \
                <= 1e-12