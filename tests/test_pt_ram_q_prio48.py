# -*- coding: utf-8 -*-
"""Tests fuer pt_ram_q_prio48.py — EXPERIMENT 055 (H-H9 FPrio-4 + FPrio-8,
LEG FP48-COMBINED), 0 QPU.

Gepinnt wird das GEFRORENE Prereg (md5 b7afc42c…), das Grid (13 Verdict-P
+ 24 Kal-P, davon 11 Ladder-Iteration), die registrierten Anker
(recompute_anchors: S1->S2-Rho-Q5 0.5-Klasse / Rho-Q3 0.8095-Klasse /
pooled 13/13, q95-exakt sekundaer, D.5-SE-Provenanz), die Einstellungs-
Konventionen (slot_assignment start=1, forced_row_order, layout_slots)
und die committeten S1/S2-Eval- + Stage-3-Pins.
"""
import json
import os

import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_aer as h3a
import pt_ram_q_prio48 as p48
import pytest

LADDER_PS = [479, 557, 617, 677, 701, 521, 593, 653, 719, 733, 563]
PREREG_MD5 = "b7afc42c62a6da75b2e43dd3674f8965"


# ------------------------------------------------------------------ Konstanten

class TestFrozenConstants:
    def test_experiment_identity(self):
        assert p48.EXPERIMENT == "EXPERIMENT 055"
        assert p48.LEG == "FP48-COMBINED"
        assert p48.HYPOTHESIS == ("H-H9 FPrio-4 (C.1/D.7 Session-P-Bindung)"
                                  " + FPrio-8 (D.5 n_cal>=16)")

    def test_circuit_budget_composition(self):
        # 148 FORCED (37 Reihen x 4) + 12 UNFORCED = 160; Budget 160 x 8192.
        order = p48.forced_row_order()
        n_rows = sum(len(rows) for rows in order.values())
        assert n_rows == 37
        assert 37 * 4 + 12 == p48.N_CIRCUITS == 160
        assert p48.SHOTS == 8192 and p48.TOTAL_SHOTS == 1310720
        assert p48.TRANSPILE_SEED == h3a.TRANSPILE_SEED == 7

    def test_grid_ps(self):
        assert p48.VERDICT_P == {"q3_d3": [181, 229, 283, 379, 467, 613,
                                           691, 797],
                                 "q5_d5": [467, 547, 613, 673, 691]}
        assert p48.CAL_OLD_P == {"q3_d3": [149, 197, 251, 347, 433,
                                           577, 659, 761],
                                 "q5_d5": [433, 499, 577, 631, 659]}
        assert p48.VERDICT_P["q3_d3"] == sorted(p48.VERDICT_P["q3_d3"])
        assert p48.VERDICT_P["q5_d5"] == sorted(p48.VERDICT_P["q5_d5"])
        assert sum(len(v) for v in p48.VERDICT_P.values()) == 13
        # Kal: q3 8 + q5 (5 alt + 11 Ladder) = 24; Ladder-Nachtrag wörtlich
        # die Generierungs-Reihenfolge (nicht sortiert).
        assert sum(len(v) for v in p48.CAL_OLD_P.values()) == 13
        assert p48.N_NEW_CAL_Q5 == 11 and p48.N_CAL_Q5_TARGET == 16
        assert p48.KAPPA_CEILING == 0.81 and p48.KAPPA_S1_Q5_CAL_MIN == \
            0.8115144847818115

    def test_arm_grid_meta(self):
        assert p48.ARMS == ("q3_d3", "q5_d5")
        assert p48.Q_BY_ARM == {"q3_d3": 3, "q5_d5": 5}
        assert p48.NQ_BY_ARM == {"q3_d3": 2, "q5_d5": 3}
        assert p48.D_MIN_BY_ARM == {"q3_d3": 3, "q5_d5": 5}
        assert p48.FAM_BY_ARM == {"q3_d3": (3, 9, 27), "q5_d5": (5, 25, 125)}
        assert p48.D_FAM_BY_ARM == {"q3_d3": (9, 27), "q5_d5": (25, 125)}
        assert p48.D_TOL == 1e-12 and p48.CP_TOL == 1e-12

    def test_session_weight_and_band_pins(self):
        assert p48.W_A == 0.05
        assert p48.W_B_DP == 0.02787029633307472
        assert p48.SE_NO_INT_S1_Q5_CAL == 0.0025335578768332333
        assert p48.SE_C_MEAN_S1 == 0.01197607825720734
        assert p48.SQRT_EXPECT_N16 == 0.0014163019093822874

    def test_paths(self):
        assert p48.PREREG_PATH == "pt_ram_q_prio48_prereg.json"
        assert p48.RAW_PATH == "pt_ram_q_prio48_raw.json"
        assert p48.EVAL_PATH == "pt_ram_q_prio48_eval.json"
        assert p48.ISA_REPORT_PATH == "pt_ram_q_prio48_isa_report.json"
        assert p48.ISA_GATE_PATH == "pt_ram_q_prio48_isa_gate.json"
        assert p48.H3_EVAL_S1 == "pt_ram_q_hardware3_eval.json"
        assert p48.H3_EVAL_S2 == "pt_ram_q_hardware3_eval_rep.json"
        # p48-H3-Prereg (relativ) und h3-Prereg (absolut vom Modul-Import)
        # muessen DENSELBEN Freeze referenzieren (recompute_anchors nutzt
        # h3.load_frozen_prereg() default, verify_frozen p48.load_...).
        assert os.path.abspath(p48.H3_PREREG) == h3.PREREG_PATH
        assert p48.K2_PREREG == "pt_ram_q6_k2_prereg.json"
        assert p48.K2_EVAL == "pt_ram_q6_k2_eval.json"
        assert p48.JOB046_ID == "dauassrojkfs738rrcsg"
        assert p48.JOB_ID_PATH == "pt_ram_q_prio48_fez_job_id.txt"
        assert p48.SESSIONS_OUT == "scratches/h9_ramq_sessions_out.json"
        assert p48.FEZ_BACKLOG == ("QUQUINT-F4 daua5hahcrkc73dv9eh0"
                                   " -> 046 dauassrojkfs738rrcsg -> 055")

    def test_isa_ceilings_inherited(self):
        assert p48.ISA_2Q_PER_CIRCUIT_MAX == 120
        assert p48.ISA_2Q_TOTAL_MAX == 6000

    def test_c_vorprobe_consts_match_prereg(self):
        assert p48.RHO_C_VORPROBE_Q5 == 0.1879
        assert p48.RHO_C_VORPROBE_Q3 == -0.4441
        pr = p48.load_frozen_prereg()
        committed = pr["c1_c_vorprobe"]["committed_rho_S1"]
        assert committed["q5"] == p48.RHO_C_VORPROBE_Q5
        assert committed["q3"] == p48.RHO_C_VORPROBE_Q3


# -------------------------------------------------------------------- Prereg

class TestFrozenPrereg:
    def test_prereg_md5_pin(self):
        # DREI-Hash-Unterscheidung (h3/053-Lektion, hier sauber): doc["md5"]
        # = Payload-Content-md5 (canonical sort_keys+compact, OHNE md5-Feld),
        # NICHT die Byte-MD5 des indent-1-Files. load_frozen_prereg erzwingt
        # den Freeze-Vergleich (ValueError bei MISMATCH).
        doc = p48.load_frozen_prereg()
        assert doc["md5"] == PREREG_MD5
        assert p48.verify_prereg_md5(doc) is True
        stripped = {k: v for k, v in doc.items() if k != "md5"}
        assert p48.payload_md5(stripped) == PREREG_MD5

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_verify_frozen_shape(self):
        out = p48.verify_frozen()
        assert sorted(out) == ["anchors", "ladder", "md5_ok", "n_cP",
                               "n_cal_rows", "n_verdict_rows", "prereg_md5"]
        assert out["md5_ok"] is True
        assert out["prereg_md5"] == PREREG_MD5
        assert out["ladder"] == LADDER_PS
        assert out["n_verdict_rows"] == 13
        assert out["n_cal_rows"] == 24  # q3 8 + q5 (5 alt + 11 Ladder)
        assert out["n_cP"] == 37

    def test_verify_frozen_matches_prereg(self):
        pr = p48.load_frozen_prereg()
        pr_md5 = pr["md5"]
        assert pr_md5 == PREREG_MD5

    def test_verdict_map_texts(self):
        pr = p48.load_frozen_prereg()
        vm = pr["verdict_map"]
        assert sorted(vm) == ["GEOMETRYBOUND_D7", "MIXED_PARTIAL",
                              "P_BOUND_TRANSFER_HELD", "UNDETERMINED"]
        assert vm["P_BOUND_TRANSFER_HELD"] == (
            "C1 beide Arme >= S1->S2-Anker UND C2 UND kein C3-Feuer "
            "(rho(Delta-res, Delta-c) < q95-exakt je Arm)")
        assert vm["GEOMETRYBOUND_D7"] == (
            "C1 q5 unter Anchor UND C3 q5 feuert (>= q95-exakt) — D.7 "
            "gewinnt die Runde, auf Session-3-Ebene dokumentiert; "
            "H-RAM-Q-4 bleibt REFUTED")

    def test_safeguard_limits_verbatim(self):
        pr = p48.load_frozen_prereg()
        assert pr["safeguard_limits"] == {
            "kappa_ceiling": 0.81,
            "void": ("REFIT_INVALID_KAPPA: kappa_hat < 0.81 an >= 2 der "
                     "Union-Reihen -> gamma-Refit invalid (descriptiv-void; "
                     "kein kritisches Verdict-Ableiten)"),
            "kontrolle_void": "EVALUATION_INVALID_KONTROLLE_GESCHEITERT",
            "w_band": 0.02787029633307472,
            "w_a": 0.05,
        }
        assert pr["status"] == "REGISTERED_NOT_MEASURED"
        assert pr["integritaet"] == {"qpu_jobs_now": 0,
                                     "verdict_re_decide": False,
                                     "prereg_freezes_beruehrt": False,
                                     "toleranz_erhoehung": False}


# ------------------------------------------------------------- Ladder + Grid

class TestLadderAndGrid:
    def test_ladder_ps_wortlich(self):
        out, log = p48.ladder_ps()
        assert out == LADDER_PS
        assert out != sorted(out)  # Generierungs-Reihenfolge, nicht sortiert
        pr = p48.load_frozen_prereg()
        assert log == pr["kalibrier_bein"]["ladder_generations"]
        assert pr["kalibrier_bein"]["ladder_generations"] == [
            {"generation": 1, "P_alt": [433, 499, 577, 631, 659],
             "candidates": [479, 557, 617, 677, 701]},
            {"generation": 2, "P_alt": [479, 557, 617, 677, 701],
             "candidates": [521, 593, 653, 719, 733]},
            {"generation": 3, "P_alt": [521, 593, 653, 719, 733],
             "candidates": [563, 641, 739, 751, 769]},
        ]

    def test_ladder_naked_form_and_disjoint(self):
        assert p48.ladder_ps(with_log=False) == LADDER_PS
        assert not (set(LADDER_PS) & set(p48.union40()))

    def test_forced_row_order(self):
        order = p48.forced_row_order()
        q3 = order["q3_d3"]
        q5 = order["q5_d5"]
        assert q3 == ([("verdict", P) for P in sorted(p48.VERDICT_P["q3_d3"])]
                      + [("cal", P) for P in sorted(p48.CAL_OLD_P["q3_d3"])])
        # q5: verdict 5 + cal-alt 5 + Ladder 11 in Generierungs-Reihenfolge.
        assert q5 == ([("verdict", P) for P in sorted(p48.VERDICT_P["q5_d5"])]
                      + [("cal", P) for P in p48.CAL_OLD_P["q5_d5"]]
                      + [("cal", P) for P in LADDER_PS])
        assert len(q3) == 16 and len(q5) == 21

    def test_eval_grid_stamps(self):
        pts_e, cal_e, ladder = p48.eval_grid()
        assert ladder == LADDER_PS
        assert sorted(pts_e)[:1] == [("q3_d3", 181)]
        k = ("q3_d3", 181)
        assert pts_e[k]["set"] == h3a.SET_VERDICT == "verdict"
        assert pts_e[k]["arm"] == "q3_d3"
        assert pts_e[k]["P"] == 181
        ck = ("q3_d3", 149)
        assert cal_e[ck]["set"] == h3a.SET_CAL == "cal"
        assert h3a.pkey(k, pts_e) == "verdict|q3_d3|181"
        assert h3a.pkey(ck, cal_e) == "cal|q3_d3|149"
        assert len(pts_e) == 13 and len(cal_e) == 24

    def test_cP_freeze_fresh_bit_equal(self):
        pr = p48.load_frozen_prereg()
        pts_e, cal_e, _ladder = p48.eval_grid()
        cP = p48.cP_freeze_fresh(pts_e, cal_e)
        assert len(cP) == 37 == len(pr["prediction_freeze"]["cP_freeze"])
        got = pr["prediction_freeze"]["cP_freeze"]
        for key in cP:
            assert abs(cP[key] - got[key]) <= p48.CP_TOL
        assert cP["verdict|q5_d5|467"] == 4.883399773945637
        assert cP["cal|q5_d5|433"] == 4.895198651036044
        assert cP["cal|q3_d3|149"] == 5.003660769251847


# ------------------------------------------------------------------- Anker

class TestAnchorMaths:
    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_recompute_anchors_pins(self):
        a = p48.recompute_anchors()
        assert abs(a["rho_q5"] - 0.49999999999999994) <= 1e-12
        assert abs(a["rho_q3"] - 0.8095238095238096) <= 1e-12
        assert abs(a["rho_pooled"] - 0.8956043956043955) <= 1e-12
        assert abs(a["q95_q5"] - 0.7999999999999999) <= 1e-12
        assert a["n_perm_q5"] == 120
        assert abs(a["q95_q3"] - 0.6190476190476191) <= 1e-12
        assert a["n_perm_q3"] == 40320
        assert abs(a["se_no_int"] - 0.0025335578768332333) <= 1e-12
        assert abs(a["mean_c"] - 4.726980333354999) <= 1e-12
        assert abs(a["se_times_mean_c"] - 0.01197607825720734) <= 1e-12
        assert abs(a["sqrt_skalierung_n16"] - 0.0014163019093822874) <= 1e-12
        assert a["c_p_identisch_s1_s2"] is True

    def test_spearman_units(self):
        assert p48.spearman([1, 2, 3], [1, 2, 3]) == 1.0
        assert p48.spearman([1, 2, 3], [3, 2, 1]) == -1.0

    def test_q95_exact_perm_units(self):
        q95, npm = p48.q95_exact_perm([0.0, 1.0, 2.0], [0.0, 1.0, 2.0])
        assert npm == 6
        assert q95 == 1.0  # Identitaet liegt in der Nullmenge -> q95 = max

    def test_slot_assignment_start_rule(self):
        assert p48.slot_assignment(5, 3) == [1, 2, 0, 1, 2]
        assert p48.slot_assignment(1, 3) == [1]      # erste Zeile nie Slot 0
        assert p48.slot_assignment(0, 4) == []
        assert p48.slot_assignment(3, 3) == [1, 2, 0]

    def test_layout_slots_units(self):
        line = [(0, 1), (1, 2), (2, 3)]
        assert p48.layout_slots(2, line) == [(0, 1), (1, 2), (2, 3)]
        assert p48.layout_slots(3, line) == [(0, 1, 2), (1, 2, 3)]
        disc = [(0, 1), (2, 3)]
        assert p48.layout_slots(2, disc) == [(0, 1), (2, 3)]
        assert p48.layout_slots(3, disc) == []


class TestS1S2Anchors:
    def test_s1_s2_below_sets(self):
        s1 = p48.arm_rows(p48.H3_EVAL_S1, "q5_d5")
        s2 = p48.arm_rows(p48.H3_EVAL_S2, "q5_d5")
        s1q3 = p48.arm_rows(p48.H3_EVAL_S1, "q3_d3")
        s2q3 = p48.arm_rows(p48.H3_EVAL_S2, "q3_d3")
        assert s1["verdict"]["P"] == [467, 547, 613, 673, 691]
        assert s1["verdict"]["below_sharp"] == [467, 547, 673]
        assert s2["verdict"]["below_sharp"] == [467, 673]
        assert s1q3["verdict"]["below_sharp"] == []
        assert s2q3["verdict"]["below_sharp"] == []
        assert s1["verdict"]["c_p"] == s2["verdict"]["c_p"]
        assert s1q3["verdict"]["c_p"] == \
            s2q3["verdict"]["c_p"]

    def test_s1_s2_kappa_pins(self):
        s1 = p48.arm_rows(p48.H3_EVAL_S1, "q5_d5")["verdict"]
        s2 = p48.arm_rows(p48.H3_EVAL_S2, "q5_d5")["verdict"]
        assert s1["kappa"][0] == 0.8274049627184941   # P=467
        assert s2["kappa"][0] == 0.868557336621455
        assert min(s1["kappa"]) == 0.8244713360224911      # Union-Minimum

    def test_session_anchor_constants(self):
        assert p48.ANCHOR_RHO_Q5 == 0.49999999999999994
        assert p48.ANCHOR_RHO_Q3 == 0.8095238095238096
        assert p48.ANCHOR_RHO_POOLED == 0.8956043956043955
        assert p48.Q95_PERM_Q5 == 0.7999999999999999
        assert p48.Q95_PERM_Q3 == 0.6190476190476191

    def test_s1_s2_verdicts_and_gamma(self):
        d1 = h3e_eval()
        d2 = json.load(open(p48.H3_EVAL_S2, encoding="utf-8"))
        assert d1["verdict"] == d2["verdict"] == "H-RAM-Q-4_REFUTED"
        g5 = d1["gamma_arm"]["q5_d5"]
        g3 = d1["gamma_arm"]["q3_d3"]
        assert g5["gamma"] == 0.038128743451453374
        assert g3["gamma"] == 0.009105648402709013
        assert len(g5["rows"]) == 5 and len(g3["rows"]) == 8
        assert g5["n_cal"] == 5 and g3["n_cal"] == 8

    def test_echo_ladder_pins(self):
        d1 = h3e_eval()
        d2 = json.load(open(p48.H3_EVAL_S2, encoding="utf-8"))
        for tag, d in (("S1", d1), ("S2", d2)):
            lad5 = d["echo_ladder"]["q5_d5"]
            lad3 = d["echo_ladder"]["q3_d3"]
            assert lad5["P"] == 467 and lad3["P"] == 181
            assert lad5["repeats"] == lad3["repeats"] == [1, 2, 4, 8]
            assert lad5["r1_konsistent_mit_kappa_hat_anker"] is True
            assert lad5["r1_shared_with_loschmidt"] is True
            assert lad5["verdict_role"] == "NICHT verdict-tragend (Diagnostik)"
        lad5 = d1["echo_ladder"]["q5_d5"]
        lad3 = d1["echo_ladder"]["q3_d3"]
        assert lad5["kappa_r"]["r8"] == 0.09815425987043148
        assert lad3["kappa_r"]["r8"] == 0.9118150684931506
        assert lad5["kappa_r"]["r1"] == 0.8274049627184941
        assert lad5["fit_kappa_block"] == 0.7314347776025595
        assert lad3["fit_kappa_block"] == 0.9926602234735433


def h3e_eval():
    with open(p48.H3_EVAL_S1, encoding="utf-8") as fh:
        d = json.load(fh)
    return d


class TestStage3Pins:
    def _s3(self):
        with open("pt_ram_q_prio48_stage3_results.json",
                  encoding="utf-8") as fh:
            return json.load(fh)

    def test_stage3_shape(self):
        s3 = self._s3()
        assert s3["status"] == "STAGE3_AER_EXACT_ONLY_COMPLETED"
        assert len(s3["b_p"]) == 37
        assert s3["b_p_fit_failed"] == {}
        assert s3["ladder_ps"] == LADDER_PS

    def test_stage3_divergence_verbatim(self):
        s3 = self._s3()
        zz = s3["b_p_konsistenz_zusammenfassung"]
        assert zz["divergente_keys"] == ["cal|q3_d3|197", "verdict|q3_d3|613",
                                         "cal|q3_d3|761", "verdict|q5_d5|613",
                                         "cal|q5_d5|631"]

    def test_stage3_b_p_value_pins(self):
        s3 = self._s3()
        assert s3["b_p"]["verdict|q3_d3|613"] == 1.7294524538402756
        assert s3["b_p"]["verdict|q5_d5|613"] == 1.0354122149223435
        assert s3["b_p"]["verdict|q5_d5|467"] == 1.045997528061458
        assert s3["b_p"]["cal|q5_d5|479"] == 1.061631848619412
        assert s3["intercepts"]["verdict|q3_d3|613"] == 0.8896416028270498
        assert s3["intercepts"]["verdict|q5_d5|613"] == 0.906404201733523

    def test_ladder_rows_are_cal_rows(self):
        s3 = self._s3()
        assert all("cal|q5_d5|%d" % P in s3["b_p"] for P in LADDER_PS)