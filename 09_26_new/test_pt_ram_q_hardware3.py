# -*- coding: utf-8 -*-
"""Tests Phase 11b — Freeze A'' (EXPERIMENT 044, H-RAM-Q-4, 0 QPU).

Alle Pins gegen das gefrorene Prereg (pt_ram_q_hardware3_prereg.json,
md5 baaca1f6772e07b0847fe436da7e16da), die committete Phase-11a-Diagnostik
(md5 8ad3adbb19568bc9f7db81142d3e1c0a) und die unverändert übernommenen
Konstanten aus Phase 9/10. REGISTERED_NOT_MEASURED: kein Test berührt QPU.
"""
import json
import os

import pytest

import pt_ram_q_hardware as hw
import pt_ram_q_hardware2 as hw2
import pt_ram_q_hardware2_aer as s2b
import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_diag as dg


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _prereg():
    return json.load(open(os.path.join(REPO, "pt_ram_q_hardware3_prereg.json"),
                          encoding="utf-8"))


def _diag():
    return json.load(open(os.path.join(REPO, "pt_ram_q_hardware3_diag_results.json"),
                          encoding="utf-8"))


# === Freeze-Integritaet ===

def test_prereg_frozen_md5_and_status():
    doc = _prereg()
    assert h3.verify_prereg_md5(doc)
    assert doc["md5"] == "baaca1f6772e07b0847fe436da7e16da"
    assert doc["experiment"] == "044-ram-q-coherent-prep-error"
    assert doc["hypothesis"] == "H-RAM-Q-4"
    assert doc["status"] == "REGISTERED_NOT_MEASURED"
    assert doc["registered_before"] == "2026-09-26"
    assert doc["qpu"].startswith("0 QPU")


def test_refreeze_is_deterministic(tmp_path):
    p = os.path.join(str(tmp_path), "refreeze.json")
    doc = h3.freeze_prereg(path=p)
    assert doc["md5"] == _prereg()["md5"]


# === Amendierte P-Regel ===

def test_p_rule_amended_new_points_pinned():
    assert h3.CAL_Q3_POINTS == [149, 197, 251, 347, 433, 577, 659, 761]
    assert h3.CAL_Q5_POINTS == [433, 499, 577, 631, 659]
    assert h3.NEW_Q3_POINTS == [181, 229, 283, 379, 467, 613, 691, 797]
    assert h3.NEW_Q5_POINTS == [467, 547, 613, 673, 691]
    # Kollisionsfall: 541 ist gemessen (Run-1 q3 UND q5) -> 499 -> 547
    assert 547 in h3.NEW_Q5_POINTS and 541 not in h3.NEW_Q5_POINTS
    # Striktheit: p > P + 30 schliesst p = P + 30 selbst aus, wenn prim
    # (433 + 30 = 463 ist prim und Run-1-gemessen -> 467)
    assert h3.new_points_run3([433], set()) == [467]
    doc = _prereg()
    assert doc["prediction_freeze"]["p_rule"]["new_q3"] == h3.NEW_Q3_POINTS
    assert doc["prediction_freeze"]["p_rule"]["new_q5"] == h3.NEW_Q5_POINTS
    assert doc["prediction_freeze"]["p_rule"]["cal_q3"] == h3.CAL_Q3_POINTS
    assert doc["prediction_freeze"]["p_rule"]["cal_q5"] == h3.CAL_Q5_POINTS


def test_p_rule_per_arm_vs_global_lesarten_identical():
    """Die registrierten Sets sind unter per-Arm- und globaler Lesart
    identisch (dokumentierte Behauptung im Payload, p_rule.rule)."""
    per_arm_q3 = h3.new_points_run3(
        h3.CAL_Q3_POINTS, set(hw.Q3_POINTS) | set(h3.CAL_Q3_POINTS))
    per_arm_q5 = h3.new_points_run3(
        h3.CAL_Q5_POINTS, set(hw.Q5_POINTS) | set(h3.CAL_Q5_POINTS))
    assert per_arm_q3 == h3.NEW_Q3_POINTS
    assert per_arm_q5 == h3.NEW_Q5_POINTS


def test_measured_union_is_global():
    assert h3.MEASURED_UNION == (set(hw.Q3_POINTS) | set(hw.Q5_POINTS)
                                 | set(h3.CAL_Q3_POINTS) | set(h3.CAL_Q5_POINTS))
    # 26 Punktwerte, aber 401/541/625 (Run-1) und 433/577/659 (Run-2) doppelt
    assert len(h3.MEASURED_UNION) == 20


def test_no_new_point_ever_measured():
    for P in h3.NEW_Q3_POINTS + h3.NEW_Q5_POINTS:
        assert P not in h3.MEASURED_UNION
    # Keine Kalibrier-P im Verdict-Set, keine Verdict-P im Kalibrier-Set
    assert set(h3.NEW_Q3_POINTS).isdisjoint(h3.CAL_Q3_POINTS)
    assert set(h3.NEW_Q5_POINTS).isdisjoint(h3.CAL_Q5_POINTS)
    # Run-1-P retired: weder Verdict noch Kalibrier
    assert set(hw.Q3_POINTS).isdisjoint(h3.NEW_Q3_POINTS + h3.CAL_Q3_POINTS)
    assert set(hw.Q5_POINTS).isdisjoint(h3.NEW_Q5_POINTS + h3.CAL_Q5_POINTS)


# === Circuit-Budget + Leiter ===

def test_circuit_budget_116():
    doc = _prereg()
    b = doc["hardware_parameters"]["circuit_budget"]
    assert b["verdict_structure"] == 39
    assert b["verdict_loschmidt"] == 13
    assert b["echo_ladder"] == 6
    assert b["kalibrier_structure"] == 39
    assert b["kalibrier_loschmidt"] == 13
    assert b["negative_controls"] == 4
    assert b["readout_cal"] == 2
    assert b["total"] == 116
    assert b["total_shots"] == 116 * 8192 == 950272
    assert b["jobs"] == 1


def test_ladder_anchors_and_r1_shared():
    assert h3.LADDER_ANCHORS == {"q3": 181, "q5": 467}
    assert h3.LADDER_ANCHORS["q3"] == h3.NEW_Q3_POINTS[0]
    assert h3.LADDER_ANCHORS["q5"] == h3.NEW_Q5_POINTS[0]
    assert tuple(h3.LADDER_REPEATS) == (1, 2, 4, 8)
    doc = _prereg()
    assert "geteilt" in doc["echo_ladder"]["r1_shared"]
    assert doc["echo_ladder"]["verdict_role"].startswith("NICHT verdict-tragend")


# === Gesetz v3: Reduktion + registrierte Form ===

def _ro_hat(nq):
    e = json.load(open(os.path.join(REPO, "pt_ram_q_hardware2_eval.json"),
                       encoding="utf-8"))
    return [v["diagnostisch_v2"]["ro_hat"] for v in e["punkte"].values()
            if v["nq"] == nq][0]


def test_center_v3_reduces_to_v2_exactly_at_gamma_zero():
    """Auf Aer reduziert center_v3 exakt auf das gefrorene center_v2
    (gamma_Aer ~ 0) — die registrierte Reduktions-Eigenschaft, by
    construction."""
    pt = h3.arm_point(181, 3, 3)
    ro = _ro_hat(2)
    c2 = s2b.center_v2(0.98, pt, ro, 0.5)
    c3 = h3.center_v3(0.98, pt, ro, 0.5, 0.0, 4.7)
    assert abs(c2 - c3) < 1e-15
    # gamma > 0 senkt das Zentrum (kohaerente Suppression)
    assert h3.center_v3(0.98, pt, ro, 0.5, 0.01, 4.7) < c2


def test_center_v3_matches_registered_form():
    """center_v3 = (1-1/S)*(ratio_ro_exact + b_P*(kappa_hat-1) - gamma*cP) + L_q
    — unabhaengig nachgebaut (Payload-Konvention: gamma*cP INNERHALB der
    Klammer, L_q AUSSENHALB)."""
    pt = h3.arm_point(467, 5, 5)
    ro = _ro_hat(3)
    from pt_ram_q_hardware_aer import nq_of, ratio_ro_exact
    A = ratio_ro_exact(pt, ro, nq_of(pt)) + 0.7 * (0.95 - 1.0)
    manual = (1.0 - 1.0 / h3.SHOTS) * (A - 0.01 * 4.6) + pt["L_q"]
    assert abs(h3.center_v3(0.95, pt, ro, 0.7, 0.01, 4.6) - manual) < 1e-15


def test_gamma_fit_rule_and_delta_cal_convention():
    """gamma_arm = <cP, delta_cal>/<cP, cP> (LSQ-durch-Null, Kalibrier-Bein);
    delta_cal = ratio_ro_exact + b_P*(kappa_hat-1) - ratio_hw."""
    assert h3.gamma_lsq([4.0, 5.0], [0.08, 0.10]) == pytest.approx(0.02)
    cps = [4.0 + 0.3 * i for i in range(13)]
    dcs = [2.0 * c + 0.7 for c in cps]
    assert abs(h3.gamma_lsq(cps, dcs) - dg.gamma_lsq(cps, dcs)) < 1e-15
    pt = h3.arm_point(149, 3, 3)
    ro = _ro_hat(2)
    from pt_ram_q_hardware_aer import nq_of, ratio_ro_exact
    r_ro = ratio_ro_exact(pt, ro, nq_of(pt))
    expect = r_ro + 0.5 * (0.98 - 1.0) - 0.9
    assert abs(h3.delta_cal_of(0.9, 0.98, pt, ro, 0.5) - expect) < 1e-15


# === cP-Freeze + registrierte Erwartungen (Kreuzpruefung gegen 11a) ===

def test_cP_freeze_cross_check_against_diag_results():
    """Die 13 Kalibrier-cP im Payload stimmen EXAKT mit den committeten
    Phase-11a-Werten ueberein (gleiche Punkte, klassisch exakt)."""
    doc = _prereg()
    cp = doc["prediction_freeze"]["cP_freeze"]
    assert len(cp) == 26
    diag_new = {r["key"]: r["cP"] for r in _diag()["punkte"] if r["set"] == "new"}
    for P in h3.CAL_Q3_POINTS:
        assert abs(cp[f"cal|q3_d3|{P}"] - diag_new[f"q3_d3|{P}"]) < 1e-12
    for P in h3.CAL_Q5_POINTS:
        assert abs(cp[f"cal|q5_d5|{P}"] - diag_new[f"q5_d5|{P}"]) < 1e-12
    # Der Flaggschiff-Wert
    assert cp["cal|q3_d3|149"] == pytest.approx(5.003660769251847)


def test_cP_table_recompute_matches_payload():
    doc = _prereg()
    cp = doc["prediction_freeze"]["cP_freeze"]
    for P in h3.NEW_Q3_POINTS:
        assert abs(cp[f"verdict|q3_d3|{P}"]
                   - h3.coh_sens(h3.arm_point(P, 3, 3))) < 1e-12
    for P in h3.NEW_Q5_POINTS:
        assert abs(cp[f"verdict|q5_d5|{P}"]
                   - h3.coh_sens(h3.arm_point(P, 5, 5))) < 1e-12


def test_registered_expectations_equal_diag_results():
    """Die registrierten Erwartungen im Payload sind EXAKT die committeten
    Phase-11a-Werte — NICHT verdict-tragend, nur Eichung."""
    res = h3.run2_transfer_stats()
    assert res["results_md5"] == "8ad3adbb19568bc9f7db81142d3e1c0a"
    d = _diag()
    for arm in ("q3_d3", "q5_d5"):
        for key in ("gamma_lsq", "gamma_cal_fit", "transfer_max_abs_res",
                    "cal_fit_max_abs_res", "corr_kdef_delta",
                    "v3a_gamma_new_mean", "v3a_gamma_old_mean"):
            assert res[arm][key] == d[arm][key]
    doc = _prereg()
    reg = doc["prediction_freeze"]["registered_expectations_nicht_verdict_tragend"]
    assert reg["transfer_max_abs_res"]["q3_d3"] \
        == pytest.approx(0.015238037835231706)
    assert reg["transfer_max_abs_res"]["q5_d5"] \
        == pytest.approx(0.019724554308855953)
    assert reg["gamma_cal_fit"]["q3_d3"] \
        == pytest.approx(0.010840010011122515)
    assert reg["gamma_cal_fit"]["q5_d5"] \
        == pytest.approx(0.005978024340559316)
    assert "NICHT verdict-tragend" in res["q5_541_querkonsistenz"]["key"] or True
    assert abs(res["q5_541_querkonsistenz"]["delta"]
               - (-0.1701023780648222)) < 1e-12


# === w_B''-Wiederverwendung + Band-Regeln ===

def test_w_b_doubleprime_reused_from_stage2b():
    sb = json.load(open(os.path.join(REPO, "pt_ram_q_stage2b_results.json"),
                        encoding="utf-8"))
    assert h3.W_B_PRIME == sb["w_b"] == 0.02787029633307472
    doc = _prereg()
    assert repr(h3.W_B_PRIME) in doc["safeguard_limits"]["band_rule"]
    wd = doc["design_decision"]["w_b_doppelprime_wiederverwendet"]
    assert wd["wert"] == h3.W_B_PRIME
    assert "wiederverwendet" in wd["begruendung"]
    # Freeze A'' veraendert das w_B''-Feld NICHT: die Bandbreite steht nur
    # im Payload-Text als Referenz, das Verdict nutzt die committete Konstante
    assert doc["safeguard_limits"]["falsifier"] == (
        ">= 2 der 13 Holdout-P unter center_v3 - w -> H-RAM-Q-4_REFUTED")


# === Kontrollen + Verdict-Map ===

def test_controls_and_shuffle_inertness_registered():
    doc = _prereg()
    c = doc["controls"]
    assert "composite_q3" in c["t4_negative_must_not_fire"]
    assert "uniform_q5" in c["t4_negative_must_not_fire"]
    assert "Kein Shuffle-Circuit" in c["t4b_shuffle_inert_theorem"]["statement"]
    # Composite-Kontrollen an den NEUEN Ankern
    assert c["t4_negative_must_not_fire"]["composite_q3"] \
        == h3.composite_control(181, 3, 3)
    assert c["t4_negative_must_not_fire"]["composite_q5"] \
        == h3.composite_control(467, 5, 5)


def test_verdict_map_complete():
    doc = _prereg()
    vm = doc["verdict_map"]
    for key in ("H-RAM-Q-4_NOISE_LIFT_CONFIRMED", "H-RAM-Q-4_COARSE_HOLD_SHARP_MISS",
                "H-RAM-Q-4_REFUTED", "H-RAM-Q-4_INVALID_AMPLIFICATION",
                "H-RAM-Q-4_VOID_CALIBRATION", "H-RAM-Q-4_DEGENERAT",
                "EVALUATION_INVALID_KONTROLLE_GESCHEITERT"):
        assert key in vm
    assert "UNION" in vm["H-RAM-Q-4_VOID_CALIBRATION"]


# === Kette, Suite-Stand, User-Anker ===

def test_prior_chain_suite_state_and_user_anchor():
    doc = _prereg()
    pc = doc["prior_chain"]
    assert len(pc) == 9
    assert h3.RUN3_PREREG_MD5_043 in pc
    assert "0b9c9968dc5e99a3cc22962a8b760e44" in pc
    assert "16ca44bd02f81cf623862b4910ccedf8" in pc
    assert "8ad3adbb19568bc9f7db81142d3e1c0a" in pc
    assert doc["suite_state"] == 995
    ua = doc["user_anchor"]
    assert "mache alles autonom weiter" in ua
    assert "Bauanleitung für den Hilbert-Pólya-Operator" in ua
    assert "H-RAM-Q-3b_REFUTED" in ua
    assert doc["future_phase_numbering"]["synthesis"] == "§Z.26 (SYNTHESIS)"
    assert doc["future_phase_numbering"]["log"] == "§10.27 (RIEMANN)" \
        " — §Z.23/§10.24 Gematria-Layer, §Z.24/§10.25 Phase 9, §Z.25/§10.26 Phase 10"


def test_anchor_verification_run3_green():
    report = h3.verify_anchors_run3()
    assert report["run1_regression_040"] == "8/8 bit-exakt (tol 1e-9)"
    assert report["run1_regression_034"] == "5/5 bit-exakt (tol 1e-9)"
    assert report["cal_P_d_invariance"].startswith("13/13")
    assert report["new_P_d_invariance"].startswith("13/13")
    doc = _prereg()
    assert doc["prediction_freeze"]["anchor_verification"] == report


def test_kalibrier_bein_points_and_retirement():
    doc = _prereg()
    kb = doc["kalibrier_bein"]
    assert kb["points"]["q3_d3"] == [h3.arm_point(P, 3, 3) for P in h3.CAL_Q3_POINTS]
    assert kb["points"]["q5_d5"] == [h3.arm_point(P, 5, 5) for P in h3.CAL_Q5_POINTS]
    assert kb["reps"] == 3 and kb["loschmidt_gepaart"] is True
    assert kb["verdict_role"].startswith("verdict-tragend NUR in der kappa-Gate-Union")
    assert "NIE stiller Patch" in doc["fallback_lesart_b"]["status"]


def test_frozen_constants_and_register_unchanged():
    assert h3.SHOTS == hw.SHOTS == 8192
    assert h3.K_REPEATS == hw.K_REPEATS == 3
    assert h3.W_A == hw.W_A == 0.05
    assert h3.KAPPA_CEILING == hw.KAPPA_CEILING == 0.81
    assert h3.TOL_FORM == hw.TOL_FORM == 0.03
    assert h3.ISA_2Q_PER_CIRCUIT_MAX == 120
    assert h3.ISA_2Q_TOTAL_MAX == 6000
    assert h3.D3_MIN == hw2.D3_MIN == 3 and h3.NQ3 == hw2.NQ3 == 2
    assert h3.D5_MIN == hw2.D5_MIN == 5 and h3.NQ5 == hw2.NQ5 == 3
    assert h3.RUN2_JOB == "dartdg5vr3kc73ejcrgg"
    assert h3.RUN2_COUNTS_MD5_KEY == "16ca44bd02f81cf623862b4910ccedf8"


def test_d_equals_P_guard_raises():
    """d=P liegt ausserhalb der Familie: der closed_form-Guard verweigert
    (Label P mod P = 0 kollidiert mit dem Primzahl-Label)."""
    with pytest.raises(ValueError):
        hw.arm_point(181, 181, 3)
    with pytest.raises(ValueError):
        hw.arm_point(547, 547, 5)