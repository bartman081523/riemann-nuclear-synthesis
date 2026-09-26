# -*- coding: utf-8 -*-
"""Tests Phase 11a — kohärentes Prep-Fehler-Diagnostik-Modul (0 QPU).

Alle Werte sind gegen das COMMITTED Run-2-Raw (pt_ram_q_hardware2_eval.json,
pt_ram_q_stage2b_results.json, counts_md5 16ca44bd...) und die klassisch
EXAKTE Arithmetik gepinnt. Nicht verdict-tragend: das Modul dokumentiert die
Befunde, aus denen das v3-Gesetz des Freeze A" (EXPERIMENT 044) abgeleitet ist.
"""
import json
import math
import os

import numpy as np
import pytest

import pt_ram_q_hardware3_diag as dg


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _results():
    return json.load(open(os.path.join(REPO, "pt_ram_q_hardware3_diag_results.json"),
                          encoding="utf-8"))


# === share_grad: Gradient des exakten ABS-FFT-Shares ===

def test_share_grad_matches_finite_differences():
    pt = dg._load_frozen_prereg_points()["q3_d3"][0]
    n = np.asarray(pt["n_d"], dtype=float)
    g = dg.share_grad(n, pt["q"], pt["d"], pt["m"])
    eps = 1e-6
    for a in range(pt["d"]):
        n_up, n_dn = n.copy(), n.copy()
        n_up[a] += eps
        n_dn[a] -= eps
        s_up = dg.share_abs_fft(n_up, pt["q"], pt["d"], pt["m"])
        s_dn = dg.share_abs_fft(n_dn, pt["q"], pt["d"], pt["m"])
        assert abs((s_up - s_dn) / (2 * eps) - g[a]) < 1e-6


def test_share_grad_zero_for_uniform():
    # Uniformer Vektor: |G_j| = 0 fuer alle j != 0 -> Share 0, Gradient 0.
    g = dg.share_grad([8.0] * 3, 3, 3, 24.0)
    assert float(np.abs(g).max()) == 0.0


# === kohärente Empfindlichkeit cP: exakt, worst >= rms ===

def test_coh_sens_worst_ge_rms_and_positive():
    for arm in ("q3_d3", "q5_d5"):
        for pt in dg._load_frozen_prereg_points()[arm]:
            c_w = dg.coh_sens(pt, "worst")
            c_r = dg.coh_sens(pt, "rms")
            assert c_w > 0 and c_r > 0
            assert abs(c_w - math.sqrt(pt["d"]) * c_r) < 1e-12


def test_coh_sens_pinned_all_26_run2_points():
    res = _results()
    for row in res["punkte"]:
        pt = row["pt"]
        c = dg.coh_sens(pt, "worst")
        assert abs(c - row["cP"]) < 1e-12


# === Run-2-Datenladen: 26 Punkte, konsistent mit dem committeten Eval ===

def test_load_rows_26_points_from_committed_eval():
    rows = dg.load_run2_rows()
    assert len(rows) == 26
    assert sum(1 for r in rows if r["set"] == "new") == 13
    assert sum(1 for r in rows if r["set"] == "old") == 13
    e = json.load(open(os.path.join(REPO, "pt_ram_q_hardware2_eval.json"),
                       encoding="utf-8"))
    for r in rows:
        if r["set"] == "new":
            v = e["punkte"][r["key"]]
            assert abs(r["ratio"] - v["ratio_hw"]) < 1e-12
            assert abs(r["kappa"] - v["kappa_hat"]) < 1e-12
        else:
            v = e["d_invarianz_bein"]["punkte"][r["key"]]
            assert abs(r["ratio"] - v["ratio_run2"]) < 1e-12


# === gamma-Fit (LSQ durch Null) + Transfer auf committeten Daten ===

def test_gamma_lsq_through_origin_exact():
    cp = np.array([4.0, 5.0])
    dc = np.array([0.08, 0.10])
    assert abs(dg.gamma_lsq(cp, dc) - 0.02) < 1e-12
    assert dg.gamma_lsq(np.array([1.0]), np.array([0.0])) == 0.0


def test_transfer_pinned_committed_values():
    res = _results()
    assert res["q3_d3"]["gamma_lsq"] == pytest.approx(0.0101574, abs=5e-7)
    assert res["q5_d5"]["gamma_lsq"] == pytest.approx(0.0071684, abs=5e-7)
    assert res["q3_d3"]["transfer_max_abs_res"] == pytest.approx(0.0152, abs=5e-4)
    assert res["q5_d5"]["transfer_max_abs_res"] == pytest.approx(0.0197, abs=5e-4)
    # Beide Transfer-Maxima unter der committeten Freeze-B'-Bandbreite w_B'
    assert res["q3_d3"]["transfer_max_abs_res"] < res["w_b_ref"]
    assert res["q5_d5"]["transfer_max_abs_res"] < res["w_b_ref"]


def test_transfer_recomputed_from_raw_matches_pinned():
    res = dg.build_results()
    frozen = _results()
    for arm in ("q3_d3", "q5_d5"):
        assert abs(res[arm]["gamma_lsq"] - frozen[arm]["gamma_lsq"]) < 1e-9
        assert abs(res[arm]["transfer_max_abs_res"]
                   - frozen[arm]["transfer_max_abs_res"]) < 1e-9


def test_pure_coherent_v3a_gamma_arm_consistency_across_sets():
    """M2-Befund: delta = gamma*cP hat arm-stabile gamma ueber beide Punktmengen
    (q3: new vs old stimmen innerhalb ~2 std ueberein)."""
    res = _results()
    g_new = res["q3_d3"]["v3a_gamma_new_mean"]
    g_old = res["q3_d3"]["v3a_gamma_old_mean"]
    assert abs(g_new - g_old) < 0.005
    assert g_new == pytest.approx(0.0164, abs=5e-4)
    assert g_old == pytest.approx(0.0158, abs=5e-4)


# === Mechanismus-Befunde, gepinnt ===

def test_kappa_deficit_uncorrelated_with_delta_on_q3():
    """q3: corr(1-kappa_hat, delta) ~ 0 — die Suppression ist NICHT
    kappa-skaliert (Echo-Refokus trennt kappa_hat von der Struktur)."""
    res = _results()
    assert abs(res["q3_d3"]["corr_kdef_delta"]) < 0.15
    assert res["q3_d3"]["corr_kdef_delta"] == pytest.approx(-0.047, abs=1e-2)


def test_v2_residuals_all_negative_and_explained_by_coherent_floor():
    res = _results()
    v2 = [r["res_v2"] for r in res["punkte"] if r["set"] == "new"]
    assert all(x < 0 for x in v2)
    # delta_cal = delta_v2-Komplement: gamma*cP reicht, um res_v2 zu schliessen
    for r in res["punkte"]:
        if r["set"] == "new":
            assert abs(r["delta_cal"] - (-r["res_v2"])) < 0.05


def test_541_anomaly_is_register_specific_not_point_intrinsic():
    """q5|541: run-1 (d=25) res_v1 POSITIV +0.0248, run-2 (d=5) -0.1453 —
    das Anomal ist an das d=5-Register/diese Session gebunden, nicht an P."""
    res = _results()
    row = [r for r in res["d_inv_querkonsistenz"] if r["key"] == "q5_d5|541"][0]
    assert row["res_v1_run1"] > 0
    assert row["res_v1_run2"] < -0.10
    assert row["delta"] < -0.15


def test_run3_calibration_bein_is_consistent_on_run2_evidence():
    """Die Run-3-Kalibrierpunkte (Run-2-Verdict-P) tragen das in-job
    gamma-Arm-Fit: der Fit auf genau diesen Punkten laesst Residuen mit
    ~2x Marge unter w_B' (q3 0.0145 / q5 0.0142 < 0.02787)."""
    res = _results()
    for arm in ("q3_d3", "q5_d5"):
        assert res[arm]["cal_fit_max_abs_res"] < res["w_b_ref"]
        # und gamma_cal_fit stimmt mit dem Detail-Befund ueberein
        assert 0.004 < res[arm]["gamma_cal_fit"] < 0.012


def test_results_json_schema_and_status():
    res = _results()
    assert res["experiment"] == "044-ram-q-coherent-prep-error"
    assert res["hypothesis"] == "H-RAM-Q-4"
    assert res["status"] == "DIAGNOSTIC_ONLY_NOT_VERDICT_TRAGEND"
    assert res["qpu_jobs"] == 0
    for key in ("w_a", "w_b_ref", "kappa_ceiling"):
        assert key in res
    assert res["kappa_ceiling"] == 0.81