# -*- coding: utf-8 -*-
"""EXPERIMENT 051 (H-RAM-Q-6 Leg D2/D3) — Stage-3-Aer-EXACT-ONLY-Beweise.

Das committete Artefakt pt_ram_q6_k2_stage3.json wird GEPINNT (alle 26
b_P-Werte exakt, Konsistenz-Befund mit den beiden ±1-ulp-Divergenzen),
der DEGENERAT-Pfad wird mit synthetischen Kurven (monkeypatch) geprueft,
und der set/arm-Stempel-Vertrag (k2.eval_grid) wird gegen die
Rohrecords bit-exakt bewiesen (h3a.pkey + Builder-Vertraeglichkeit).
"""
import json

import pytest

import pt_ram_q_hardware3_aer as h3a
import pt_ram_q6_k2 as k2
import pt_ram_q6_k2_stage3aer as s3
import tests.test_pt_ram_q6_k2_refactor_proof as rp

RUN4_Q3 = rp.RUN4_Q3
RUN4_Q5 = rp.RUN4_Q5

# GEFRORNER Artefakt-Pin (Run vor jedem Commit, 0 QPU):
B_P_FROZEN = {
    "cal|q3_d3|181": 1.7442935197170375, "cal|q3_d3|229": 1.7250416525115768,
    "cal|q3_d3|283": 1.753156955127673, "cal|q3_d3|379": 1.7049577901057635,
    "cal|q3_d3|467": 1.7056256126820026,
    "cal|q3_d3|613": 1.7294524538402756,
    "cal|q3_d3|691": 1.7015557841443723,
    "cal|q3_d3|797": 1.7217504920995026,
    "cal|q5_d5|467": 1.045997528061458,
    "cal|q5_d5|547": 1.034590166857484,
    "cal|q5_d5|613": 1.0354122149223435,
    "cal|q5_d5|673": 1.0229941628941568,
    "cal|q5_d5|691": 1.013831398761439,
    "verdict|q3_d3|223": 1.8203480434235375,
    "verdict|q3_d3|263": 1.771118723354747,
    "verdict|q3_d3|317": 1.756409390879936,
    "verdict|q3_d3|419": 1.7377107136237289,
    "verdict|q3_d3|503": 1.7077028923817752,
    "verdict|q3_d3|647": 1.700413865693905,
    "verdict|q3_d3|727": 1.7278904945344489,
    "verdict|q3_d3|829": 1.720948680610007,
    "verdict|q5_d5|503": 1.0529011572184694,
    "verdict|q5_d5|587": 1.023214564924435,
    "verdict|q5_d5|647": 1.0080755033923725,
    "verdict|q5_d5|709": 1.0082032179259717,
    "verdict|q5_d5|727": 1.0153110138074182,
}
DIV_Q3_613 = 0.027415245450614467
DIV_Q5_613 = 0.006954972219534339


def _doc():
    return json.load(open(s3.RESULTS_PATH, encoding="utf-8"))


def test_artefakt_binding_und_status():
    doc = _doc()
    assert doc["status"] == s3.STATUS_OK
    assert doc["prereg_md5"] == k2.PREREG_MD5
    assert doc["experiment"] == k2.EXPERIMENT
    assert doc["leg"] == k2.LEG
    assert doc["prereg_reference"]["md5"] == k2.PREREG_MD5
    assert doc["grid"]["n_points_verdict"] == 13
    assert doc["grid"]["n_points_kalibrier"] == 13
    assert doc["grid"]["mode"] == "exact_only"
    assert len(doc["b_p"]) == len(doc["exact"]) == 26


def test_b_p_frozen_pin_vollstaendig():
    doc = _doc()
    for k, v in B_P_FROZEN.items():
        assert doc["b_p"][k] == v, k
    # b_p == fit["b_p"], intercept + b_p == intercepts (Artefakt-intern)
    for k, v in doc["b_p_fit"].items():
        assert doc["b_p"][k] == v["b_p"], k
        assert doc["intercepts"][k] == v["intercept"] + v["b_p"], k


def test_b_p_keys_decken_cP_freeze_und_trotzdem_kein_silent_none():
    """Eval-Vertrag: `stage3["b_p"].get(pkey)` muss fuer JEDE cP-Schluessel
    einen Wert liefern (kein stiller None-Kanal)."""
    b_p = _doc()["b_p"]
    cP = k2.load_frozen_prereg()["prediction_freeze"]["cP_freeze"]
    assert set(b_p) == set(cP)


def test_konsistenz_pin_und_11c_klasse():
    doc = _doc()
    kons = doc["b_p_kalibrier_konsistenz"]
    assert len(kons) == 13
    assert len(doc["b_p_fit_failed"]) == 0
    zs = doc["b_p_konsistenz_zusammenfassung"]
    assert zs["n_kalibrier"] == 13 and zs["tol"] == h3a.BP_KONSISTENZ_TOL
    # Divergenzen GENAU an P=613 (beide Arme) — ±1-ulp-Zweig-Klasse:
    assert zs["divergente_keys"] == ["cal|q3_d3|613", "cal|q5_d5|613"]
    assert kons["cal|q3_d3|613"]["abs_diff"] > h3a.BP_KONSISTENZ_TOL
    for k in zs["divergente_keys"]:
        assert not kons[k]["ok"]
    # Dritte Werte exakt gepinnt (11c-Praezedenz: ops-Unterschied im
    # x-Gate, alle Dritt-Werte aus dem committeten 044-Artefakt)
    assert kons["cal|q3_d3|613"]["abs_diff"] == DIV_Q3_613
    assert kons["cal|q5_d5|613"]["abs_diff"] == DIV_Q5_613
    assert kons["cal|q3_d3|613"]["stage3_grid"] == \
        B_P_FROZEN["cal|q3_d3|613"]
    # 11/13 im BLAS-Rauschen (dokumentiert ~1e-5, weit unter 1e-3)
    ok = [r["abs_diff"] for r in kons.values() if r["ok"]]
    assert len(ok) == 11 and max(ok) < h3a.BP_KONSISTENZ_TOL


def test_sets_block_und_exact_levels():
    doc = _doc()
    assert doc["sets"]["verdict"] == \
        {"q3_d3": sorted(RUN4_Q3), "q5_d5": sorted(RUN4_Q5)}
    assert doc["sets"]["kalibrier"] == \
        {"q3_d3": [181, 229, 283, 379, 467, 613, 691, 797],
         "q5_d5": [467, 547, 613, 673, 691]}
    for k, curve in doc["exact"].items():
        assert [c["p1"] for c in curve] == list(h3a.STRESS_GRID_P1), k
        assert all("ops_struct" in c for c in curve)


def _fake_exact(pt, nq, p1):
    """Synthetische exakte Kurve (schnell, deterministisch): kappa
    steigt ueber die Levels, ratio = 1 + 0.05 (kappa - 1) — Steigung
    0.05 ueber ALLER 6 Nodes."""
    i = list(h3a.STRESS_GRID_P1).index(p1)
    k = [0.82, 0.85, 0.88, 0.91, 0.94, 0.97][i]
    return {"p1": p1, "kappa": k, "ratio": 1.0 + 0.05 * (k - 1.0),
            "res_v1": 0.0, "alpha": 0.0, "ops_struct": {"cz": 1}}


def test_synthetic_kurven_sl_0_05(monkeypatch):
    """Pfad-Test ohne Sim: slope 0.05 ueber 6 Nodes == b_P 0.05 exakt."""
    monkeypatch.setattr(h3a, "exact_point_level", _fake_exact)
    res = s3.run_stage3(results_path=None)
    assert res["status"] == s3.STATUS_OK
    assert len(res["b_p"]) == 26 and not res["b_p_fit_failed"]
    assert len(res["b_p_kalibrier_konsistenz"]) == 13
    for fit in res["b_p_fit"].values():
        assert fit["b_p"] == pytest.approx(0.05, abs=1e-9)
        assert fit["n_nodes"] == 6


def test_degenerat_pfad_registriert_fitfail(monkeypatch):
    """fit_b_p < 2 Domain-Nodes -> ValueError wird REGISTRIERT (b_p_fit_
    failed), Keys fallen WEG (eval: .get -> None), Status kippt."""
    def fail(kappas, ratios, ceiling=h3a.KAPPA_CEILING):
        raise ValueError("weniger als 2 Domain-Nodes — b_P nicht "
                         "identifizierbar")
    monkeypatch.setattr(h3a, "exact_point_level", _fake_exact)
    monkeypatch.setattr(h3a, "fit_b_p", fail)
    res = s3.run_stage3(results_path=None)
    assert res["status"] == s3.STATUS_DEGENERAT
    assert len(res["b_p_fit_failed"]) == 26
    assert res["b_p"] == {}
    assert res["b_p_kalibrier_konsistenz"] == {}


def test_degenerat_keine_auswirkung_auf_ro_werte(monkeypatch):
    """Ohne fit bleiben ratio_ro/intercepts leer (keine Teilergebnisse)."""
    def fail(kappas, ratios, ceiling=h3a.KAPPA_CEILING):
        raise ValueError("keine Nodes")
    monkeypatch.setattr(h3a, "exact_point_level", _fake_exact)
    monkeypatch.setattr(h3a, "fit_b_p", fail)
    res = s3.run_stage3(results_path=None)
    assert res["ratio_ro"] == {} and res["intercepts"] == {}


def test_eval_grid_stempel_bit_exakt():
    """Stempel Veraendert NUR set/arm (Rohrecord bleibt bit-exakt)."""
    pts0, cal0 = k2.fresh_points()
    pts, cal = k2.eval_grid()
    for (a, P), raw in pts0.items():
        st = pts[(a, P)]
        assert st["set"] == h3a.SET_VERDICT and st["arm"] == a
        clean = {kk: vv for kk, vv in st.items() if kk not in ("set", "arm")}
        assert json.dumps(clean, sort_keys=True) == \
            json.dumps(raw, sort_keys=True), (a, P)
    for (a, P), raw in cal0.items():
        st = cal[(a, P)]
        assert st["set"] == h3a.SET_CAL and st["arm"] == a
        clean = {kk: vv for kk, vv in st.items() if kk not in ("set", "arm")}
        assert json.dumps(clean, sort_keys=True) == \
            json.dumps(raw, sort_keys=True), (a, P)


def test_eval_grid_pkey_konvention_wie_prereg():
    """h3a.pkey auf gestempelten Records == cP_freeze-Schluessel."""
    pts, cal = k2.eval_grid()
    cP = k2.load_frozen_prereg()["prediction_freeze"]["cP_freeze"]
    for key in pts:
        assert h3a.pkey(key, pts) in cP
    for key in cal:
        assert h3a.pkey(key, cal) in cP


def test_builder_vertraegt_stempel_frisch_identisch():
    """Der Builder liest die Stempel nicht — gestempeltes und rohes
    frisches Grid muessen denselben Circuit-Namen/Circuit-Hash liefern."""
    raw = h3a.build_hardware_circuit_set(*k2.fresh_points())
    st = h3a.build_hardware_circuit_set(*k2.eval_grid())
    assert rp._circuit_tups(raw) == rp._circuit_tups(st)
    assert len(st) == 116


def test_binomial_eine_seite_wie_gemeldet():
    """Konsistenz zur 044-Testpin: 12/13 <= alpha' < 11/13 < 5/5."""
    a = k2.ALPHA_FAMILY2
    assert k2.binom_sf_one_sided(12, 13) <= a < k2.binom_sf_one_sided(11, 13)
    assert k2.binom_sf_one_sided(5, 5) > a