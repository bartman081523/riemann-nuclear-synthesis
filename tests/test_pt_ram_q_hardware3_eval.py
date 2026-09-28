# -*- coding: utf-8 -*-
"""Tests fuer pt_ram_q_hardware3_eval.py — gefrorene QPU-Auswertung
(Phase 11d, EXPERIMENT 044, H-RAM-Q-4), 0 QPU.

Gepinnt wird die GEFRORENE Verdict-Logik (Freeze A'', md5 baaca1f6):
Präzedenz DEGENERAT -> INVALID -> VOID (Union) -> AMPL (einseitig,
scharfe Kante) -> REFUTED -> CONFIRMED -> COARSE, das in-job
gamma_arm-Fit (LSQ durch Null, NUR Kalibrier-P), die Aer-Reduktion
center_v3(gamma=0) == center_v2 und die committed-Raw-Pins
(skipif: Raw/Eval noch nicht committed).
"""
import json
import os

import pytest

import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_aer as h3a
import pt_ram_q_hardware3_eval as ev
import pt_ram_q_hardware_aer as aer


# ------------------------------------------------------------------ Konstanten

class TestFrozenConstants:
    def test_verdict_names_from_map(self):
        assert ev.V_CONFIRMED == "H-RAM-Q-4_NOISE_LIFT_CONFIRMED"
        assert ev.V_COARSE == "H-RAM-Q-4_COARSE_HOLD_SHARP_MISS"
        assert ev.V_REFUTED == "H-RAM-Q-4_REFUTED"
        assert ev.V_AMPL == "H-RAM-Q-4_INVALID_AMPLIFICATION"
        assert ev.V_VOID == "H-RAM-Q-4_VOID_CALIBRATION"
        assert ev.V_DEGENERAT == "H-RAM-Q-4_DEGENERAT"
        assert ev.V_INVALID == "EVALUATION_INVALID_CONTROLS_FAILED"
        assert ev.V_UNMATCHED == "VERDICT_MAP_UNMATCHED"

    def test_paths(self):
        assert ev.RAW_PATH == "pt_ram_q_hardware3_raw.json"
        assert ev.STAGE3_PATH == "pt_ram_q_stage3_results.json"
        assert ev.ISA_PATH == "pt_ram_q_isa3_report.json"
        assert ev.EVAL_PATH == "pt_ram_q_hardware3_eval.json"
        assert ev.PREREG_MD5 == "baaca1f6772e07b0847fe436da7e16da"

    def test_delegation_counting_helpers(self):
        # Identische Zaehlfunktionen wie die Phase-10d-Auswertung (keine Kopie).
        assert ev.aer.ratio_from_counts is aer.ratio_from_counts
        assert ev.aer.p0_fraction is aer.p0_fraction
        assert ev.aer.share_hw_folded is aer.share_hw_folded
        assert ev.aer.center_v2 is aer.center_v2


# ------------------------------------------------------------------- decide_verdict

class TestDecideVerdictFrozenOrder:
    @staticmethod
    def _call(**over):
        base = dict(t4_violated=False, t_fail_other=False,
                    n_kappa_low_union=0, n_above_ceiling=0,
                    n_below_sharp=0, n_in_sharp=13,
                    all_in_coarse=True, n_holdout=13)
        base.update(over)
        return ev.decide_verdict(**base)

    def test_confirmed(self):
        assert self._call() == ev.V_CONFIRMED

    def test_t4_degenerat(self):
        assert self._call(t4_violated=True) == ev.V_DEGENERAT

    def test_t_fail_other_invalid(self):
        assert self._call(t_fail_other=True) == ev.V_INVALID

    def test_kappa_floor_union_counts_cal_points(self):
        # >= 2 in der UNION (Verdict-P UND Kalibrier-P) -> VOID; 1 reicht
        # NICHT fuer VOID — schliesst aber CONFIRMED aus (Zweig verlangt
        # n_kappa_low_union == 0 EXAKT) -> ehrliches UNMATCHED.
        assert self._call(n_kappa_low_union=2,
                          n_in_sharp=13) == ev.V_VOID
        assert self._call(n_kappa_low_union=1) == ev.V_UNMATCHED
        # Union-Zaehlung ist nicht auf Holdout beschraenkt:
        assert self._call(n_kappa_low_union=2, n_in_sharp=0) == ev.V_VOID

    def test_amplification_one_sided_sharp_edge(self):
        assert self._call(n_above_ceiling=1) == ev.V_AMPL

    def test_falsifier_two_below_sharp(self):
        assert self._call(n_below_sharp=2) == ev.V_REFUTED
        assert self._call(n_below_sharp=3, n_in_sharp=7) == ev.V_REFUTED

    def test_coarse_hold(self):
        # alle im groben Band, >= 1 ausserhalb scharf -> COARSE.
        assert self._call(n_in_sharp=11, all_in_coarse=True) == ev.V_COARSE

    def test_unmatched_honest_branch(self):
        # 379/467-Muster: nicht alle im scharfen Band, aber keiner darunter,
        # auch nicht alle im groben Band -> ehrlicher Nicht-Treffer.
        assert self._call(n_in_sharp=6, all_in_coarse=False) == ev.V_UNMATCHED


# ------------------------------------------------------------------- gamma-Fit

class TestGammaFit:
    def _pts(self):
        return h3a.all_points()

    def test_identity_constructed_delta(self):
        # delta_cal = ratio_ro_exact + b_P*(kappa-1) - ratio; konstruiere
        # ratio = (ratio_ro_exact + b_P*(kappa-1)) - cP*G  =>  delta = cP*G
        # =>  gamma = G (LSQ durch Null,registrierte Formel).
        pts = self._pts()
        pt = pts[("q3_d3", 149)]
        nq = h3a.NQ_BY_ARM["q3_d3"]
        cp = h3a.cP_of(pt)
        G, b, kappa, ro_hat = 0.02, 0.7, 0.95, 0.012
        base = aer.ratio_ro_exact(pt, ro_hat, nq) + b * (kappa - 1.0)
        rows = [{"c_p": cp, "delta_cal": base - (base - cp * G)}]
        assert ev.fit_gamma_arm(rows) == pytest.approx(G, abs=1e-12)

    def test_two_rows_weighted_lsq(self):
        r1 = {"c_p": 4.0, "delta_cal": 0.08}   # cP*G mit G = 0.02
        r2 = {"c_p": 5.0, "delta_cal": 0.10}
        out = ev.fit_gamma_arm([r1, r2])
        # gamma = (4*0.08 + 5*0.10)/(16 + 25) = 0.82/41
        assert out == pytest.approx(0.82 / 41.0, rel=1e-12)

    def test_empty_rows_none(self):
        assert ev.fit_gamma_arm([]) is None


# -------------------------------------------------------------------- center_v3

class TestCenterV3:
    def test_aer_reduction_gamma_zero_is_center_v2(self):
        # gamma_arm = 0 reduziert center_v3 EXAKT auf das gefrorene
        # center_v2 (Freeze A', Phase-10b-Konvention).
        pts = h3a.all_points()
        for arm, P in (("q3_d3", 181), ("q5_d5", 467), ("q5_d5", 547)):
            pt = pts[(arm, P)]
            nq = h3a.NQ_BY_ARM[arm]
            kappa, ro_hat, b_p = 0.9, 0.01, 0.7
            assert ev.center_v3(kappa, pt, ro_hat, b_p, 0.0,
                                h3a.cP_of(pt), nq) == pytest.approx(
                aer.center_v2(kappa, pt, ro_hat, b_p), rel=1e-12)

    def test_gamma_subtracted_inside_bracket(self):
        # gamma*cP wirkt INNERHALB des (1-1/S)-Klammer: center_v3(g)
        # = center_v3(0) - (1-1/S)*g*cP.
        pts = h3a.all_points()
        pt = pts[("q3_d3", 181)]
        nq = h3a.NQ_BY_ARM["q3_d3"]
        kappa, ro_hat, b_p, cp = 0.9, 0.01, 0.7, h3a.cP_of(pt)
        c0 = ev.center_v3(kappa, pt, ro_hat, b_p, 0.0, cp, nq)
        g = 0.01
        c1 = ev.center_v3(kappa, pt, ro_hat, b_p, g, cp, nq)
        assert c1 == pytest.approx(
            c0 - (1.0 - 1.0 / h3.SHOTS) * g * cp, rel=1e-12)


# ------------------------------------------------- Fold-Identitaet (t3, 2. Weg)

class TestFoldedShare:
    def test_dq_fold_is_identity(self):
        # Shuffle-Inertness-Theorem: bei d = q ist der Fold die Identitaet.
        pts = h3a.all_points()
        for (arm, P), pt in pts.items():
            assert pt["d"] == pt["q"]
        pt = pts[("q3_d3", 181)]
        n_hat = [pt["m"] / pt["d"]] * pt["d"]   # Laenge d, Masse m
        assert ev._folded_share(n_hat, pt) == pytest.approx(
            aer.share_hw_folded(n_hat, pt["q"], pt["d"], pt["m"]), rel=1e-12)


# ------------------------------------------------- Committetes Raw + Eval-Dokument

class TestCommittedEvalDocument:
    """Pins gegen das COMMITTED Raw (9f5f1de) + die geschriebene Auswertung."""

    @pytest.fixture(scope="class")
    def eval_doc(self):
        if not os.path.exists(ev.EVAL_PATH):
            pytest.skip("pt_ram_q_hardware3_eval.json noch nicht geschrieben")
        with open(ev.EVAL_PATH, encoding="utf-8") as fh:
            return json.load(fh)

    @pytest.fixture(scope="class")
    def raw(self):
        if not os.path.exists(ev.RAW_PATH):
            pytest.skip("pt_ram_q_hardware3_raw.json noch nicht committed")
        with open(ev.RAW_PATH, encoding="utf-8") as fh:
            return json.load(fh)

    def test_raw_integrity(self, raw):
        # gefrorene job_integrity: EIN Fez-Job, 116 Circuits, md5 VOR Auswertung
        assert raw["job_meta"]["job_id"] == "dat1o6qhcrkc73dtgo60"
        assert raw["backend"] == "ibm_fez"
        assert raw["n_circuits"] == 116 and len(raw["counts"]) == 116
        assert raw["counts_md5"] == "230098aeeb6e8716d2638e1d5fe3cfeb"
        assert raw["shots_per_circuit"] == h3.SHOTS
        assert raw["transpile"]["isa_2q_total"] == 559
        assert raw["transpile"]["isa_2q_max"] == 84

    def test_eval_schema_and_verdict(self, eval_doc):
        assert eval_doc["experiment"] == h3.EXPERIMENT
        assert eval_doc["hypothesis"] == h3.HYPOTHESIS
        assert eval_doc["status"] == "EVALUATED"
        assert eval_doc["prereg_md5"] == ev.PREREG_MD5
        assert eval_doc["counts_md5_verified"] is True
        assert eval_doc["verdict"] == "H-RAM-Q-4_REFUTED"
        vm = h3.load_frozen_prereg()["verdict_map"]
        assert eval_doc["verdict"] in vm
        assert eval_doc["verdict_map_text"].startswith(">= 2 der 13 Holdout-P")

    def test_verdict_inputs_frozen_edge(self, eval_doc):
        vi = eval_doc["verdict_inputs"]
        assert vi["n_points"] == 26 and vi["n_holdout"] == 13
        assert vi["n_kalibrier"] == 13
        assert vi["n_kappa_low_union"] == 0      # Lift ueberall >= 0.81
        assert vi["n_below_sharp"] == 3          # REFUTED-Triger (>= 2)
        assert vi["n_above_ceiling_sharp"] == 0
        assert vi["all_in_coarse_w_a"] is False  # 613 liegt ueber w_A
        # Kanten-Lesart dokumentiert: grob w_A -> nur 1 darunter, kein REFUTED.
        assert vi["n_below_coarse_w_a"] == 1

    def test_gamma_arms_in_job_fit(self, eval_doc):
        # Fit NUR ueber Kalibrier-P (q3 8, q5 5); Holdout geht in KEINEN Fit.
        g = eval_doc["gamma_arm"]
        assert g["q3_d3"]["n_cal"] == 8 and g["q5_d5"]["n_cal"] == 5
        assert abs(g["q3_d3"]["gamma"]) < 0.02
        assert len(g["q3_d3"]["rows"]) == 8 and len(g["q5_d5"]["rows"]) == 5
        for arm in h3a.ARMS:
            for r in g[arm]["rows"]:
                assert {"c_p", "delta_cal"} <= set(r)

    def test_band_flags_refuted_pattern(self, eval_doc):
        pts = {k: v for k, v in eval_doc["punkte"].items()
               if k.startswith("verdict|")}
        assert len(pts) == 13
        below = [k for k, v in pts.items() if v["below_sharp"]]
        assert len(below) == 3
        assert all(k.startswith("verdict|q5_d5|") for k in below)
        # q3-Bein dicht: ALLE 8 im groben Band
        assert all(v["in_band_coarse"] for k, v in pts.items()
                   if k.startswith("verdict|q3_d3|"))

    def test_t5_controls_green(self, eval_doc):
        k = eval_doc["kontrollen"]
        assert k["t3_identity_two_ways"]["ok"] is True
        assert k["t3_identity_two_ways"]["max_dev"] < 1e-12
        assert k["t4_negative_must_not_fire"]["ok"] is True
        assert all(c["ok"] for c in k["t4_negative_must_not_fire"]["controls"].values())
        assert k["t5_gate_set_frozen"]["ok"] is True
        assert k["t5_gate_set_frozen"]["point_set_ok"] is True
        assert k["t5_gate_set_frozen"]["cal_set_ok"] is True
        assert k["t6_mass_conservation"]["ok"] is True
        assert k["t6_mass_conservation"]["max_mass_dev"] == 0.0

    def test_echo_ladder_diagnostic_not_verdict_relevant(self, eval_doc):
        lad = eval_doc["echo_ladder"]
        for arm in h3a.ARMS:
            assert lad[arm]["P"] == h3a.ladder_anchor(arm)
            assert lad[arm]["repeats"] == list(h3.LADDER_REPEATS)
            assert lad[arm]["r1_shared_with_loschmidt"] is True
            assert lad[arm]["r1_konsistent_mit_kappa_hat_anker"] is True
            assert "NICHT verdict-tragend" in lad[arm]["verdict_role"]
        # Mechanismus-Diagnose: q5 refokussiert nicht vollstaendig.
        assert lad["q5_d5"]["fit_kappa_block"] < h3.KAPPA_CEILING

    def test_alternative_readings_documented(self, eval_doc):
        alt = eval_doc["alternative_lesarten"]
        assert alt["refuted_mit_w_a"]["verdict_waere"] is None
        assert alt["refuted_mit_w_a"]["n_below_coarse_w_a"] == 1
        assert alt["amplification_mit_w_a"]["n_above_ceiling_w_a"] == 0
        assert alt["exklusion"] is None          # n_kappa_low == 0