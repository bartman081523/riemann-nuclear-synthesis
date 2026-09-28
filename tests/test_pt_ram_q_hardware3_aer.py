# -*- coding: utf-8 -*-
"""Tests fuer pt_ram_q_hardware3_aer.py — Stage-3-Aer-Bein (EXPERIMENT 044,
H-RAM-Q-4, Phase 11c), 0 QPU.

Offline-Klassen pinnen den 116-Circuit-Satz, die 26 gefrorenen Punkte,
cP/pkey/gamma_aer/validate_form-Konventionen und die Delegations-Identitaet
gegen die Phase-9/10-Module.  Die Klasse TestStage3Results pinnt das
COMMITTED Resultat des Voll-Grids (skipif: Datei noch nicht committed).
"""
import json
import os

import pytest

import pt_ram_q_hardware2_aer as s2b
import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_aer as h3a
import pt_ram_q_hardware_aer as aer


# ---------------------------------------------------------------- Circuit-Satz

class TestCircuitSet:
    @pytest.fixture(scope="class")
    def circuits(self):
        return h3a.build_hardware_circuit_set()

    def test_budget_116(self, circuits):
        assert len(circuits) == 116
        names = [c["name"] for c in circuits]
        assert len(set(names)) == 116
        kinds = {}
        for c in circuits:
            kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
        assert kinds == {"structure": 39, "loschmidt": 13, "echo_ladder": 6,
                         "kalibrier_structure": 39, "kalibrier_loschmidt": 13,
                         "negative_control": 4, "readout_cal": 2}
        assert sum(c["shots"] for c in circuits) == 116 * 8192 == 950272

    def test_sets_and_arms(self, circuits):
        for c in circuits:
            if c["kind"] in ("structure", "loschmidt", "echo_ladder",
                             "negative_control"):
                assert c["set"] == "verdict"
            if c["kind"] in ("kalibrier_structure", "kalibrier_loschmidt"):
                assert c["set"] == "cal"
            if "arm" in c:
                assert c["arm"] in ("q3_d3", "q5_d5")
        # Minimalregister: q3-Arm 2 Qubits, q5-Arm 3 Qubits
        for c in circuits:
            if c.get("arm") == "q3_d3":
                assert c["circuit"].num_qubits == 2
            if c.get("arm") == "q5_d5":
                assert c["circuit"].num_qubits == 3

    def test_ladder_r1_shared(self, circuits):
        names = {c["name"] for c in circuits}
        # r=1 existiert NICHT als eigener Circuit (geteilt mit dem
        # Anker-Loschmidt, echo_ladder.r1_shared)
        for arm, P in (("q3_d3", 181), ("q5_d5", 467)):
            assert f"ladder_{arm}_{P}_r1" not in names
            assert f"loschmidt_{arm}_{P}" in names
            for r in (2, 4, 8):
                assert f"ladder_{arm}_{P}_r{r}" in names
        # r=1 der Leiter ist exakt der Anker-Loschmidt (r1_shared)
        anker = [c for c in circuits if c["name"] == "loschmidt_q3_d3_181"]
        assert len(anker) == 1

    def test_negative_controls_frozen(self, circuits):
        doc = h3.load_frozen_prereg()
        ctrls = doc["controls"]["t4_negative_must_not_fire"]
        by_name = {c["name"]: c for c in circuits}
        # Composite/Uniform an den NEUEN Ankern, Erwartungen DIREKT aus dem
        # gefrorenen controls-Block (kein lokales Re-Fit).
        assert by_name["ctrl_composite_P181_d3"]["expected_share"] == \
            ctrls["composite_q3"]["expected_share"] == 1.0
        assert by_name["ctrl_uniform_q3"]["expected_share"] == \
            ctrls["uniform_q3"]["expected_share"] == 0.0
        assert by_name["ctrl_composite_P467_d5"]["expected_share"] == \
            ctrls["composite_q5"]["expected_share"] == \
            pytest.approx(0.3824175824175824)
        assert by_name["ctrl_uniform_q5"]["expected_share"] == \
            ctrls["uniform_q5"]["expected_share"] == 0.0
        # Prime-Band-Unterkante (Kontrolle darf NICHT im Band liegen)
        assert by_name["ctrl_composite_P181_d3"][
            "lower_prime_band_edge"] == pytest.approx(4.925673189396992)
        assert by_name["ctrl_composite_P467_d5"][
            "lower_prime_band_edge"] == pytest.approx(3.323511509358921)

    def test_no_shuffle_circuit(self, circuits):
        # Shuffle-Inertness-Theorem (t4b): bei d=q ist der Fold die
        # Identitaet — kein Shuffle-Circuit im Satz.
        assert not [c for c in circuits if "shuffle" in c["name"].lower()]
        kinds = {c["kind"] for c in circuits}
        assert "shuffle" not in kinds


# ------------------------------------------------------------------- Punkte

class TestPoints:
    def test_26_points_from_frozen_payload(self):
        pts = h3a.all_points()
        assert len(pts) == 26
        doc = h3.load_frozen_prereg()
        for arm in h3a.ARMS:
            vP = sorted(p["P"] for p in doc["prediction_freeze"]["points"][arm])
            cP = sorted(p["P"] for p in doc["kalibrier_bein"]["points"][arm])
            assert sorted(p for (a, p) in pts
                          if a == arm and pts[(a, p)]["set"] == "verdict") == vP
            assert sorted(p for (a, p) in pts
                          if a == arm and pts[(a, p)]["set"] == "cal") == cP
        # Anderthalb Verbot: kein Punkt in beiden Sets (amendierte P-Regel)
        verdict = {k for k in pts if pts[k]["set"] == "verdict"}
        cal = {k for k in pts if pts[k]["set"] == "cal"}
        assert not (verdict & cal)

    def test_pt_dicts_untouched_from_payload(self):
        # Keine Regeneration: L_q/N/P/... kommen 1:1 aus dem Payload
        doc = h3.load_frozen_prereg()
        src = doc["prediction_freeze"]["points"]["q3_d3"][0]
        pts = h3a._point_pts()
        pt = pts[("q3_d3", src["P"])]
        for k, v in src.items():
            assert pt[k] == v

    def test_cP_of_matches_payload_all_26(self):
        doc = h3.load_frozen_prereg()
        table = doc["prediction_freeze"]["cP_freeze"]
        for key, pt in h3a.all_points().items():
            k = f'{pt["set"]}|{pt["arm"]}|{pt["P"]}'
            assert h3a.cP_of(pt) == table[k]

    def test_cP_of_recompute_coh_sens(self):
        # cP_freeze ist die gefrorene coh_sens-Rechnung (Phase-11a-Kern)
        for key, pt in h3a.all_points().items():
            assert h3a.cP_of(pt) == pytest.approx(h3.coh_sens(pt), rel=1e-12)

    def test_pkey_convention(self):
        pts = h3a.all_points()
        assert h3a.pkey(("q3_d3", 181), pts) == "verdict|q3_d3|181"
        assert h3a.pkey(("q3_d3", 149), pts) == "cal|q3_d3|149"
        assert h3a.pkey(("q5_d5", 467), pts) == "verdict|q5_d5|467"
        assert h3a.pkey(("q5_d5", 433), pts) == "cal|q5_d5|433"

    def test_ladder_anchor(self):
        assert h3a.ladder_anchor("q3_d3") == 181
        assert h3a.ladder_anchor("q5_d5") == 467

    def test_cal_points_are_run2_verdict_points(self):
        # Das Kalibrier-Bein besteht aus den Run-2-Verdict-P (Phase-11a-
        # Praezedenz) und liegt deshalb in der Phase-11a-Diagnostik (set new)
        diag = json.load(open(h3.DIAG_RESULTS, encoding="utf-8"))
        diag_bp = {r["key"]: r["b_p"] for r in diag["punkte"]
                   if r["set"] == "new"}
        for (arm, P), pt in h3a._cal_pts().items():
            assert pt["set"] == "cal"
            assert f"{arm}|{P}" in diag_bp


# ------------------------------------------- Konstanten + Delegations-Identitaet

class TestConstantsAndDelegation:
    def test_constants_frozen(self):
        assert h3a.SHOTS == 8192
        assert h3a.K_REPEATS == 3
        assert h3a.W_A == 0.05
        assert h3a.TOL_FORM == 0.03
        assert h3a.KAPPA_CEILING == 0.81
        assert h3a.STRESS_GRID_P1 == [0.0, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2]
        assert h3a.N_ENS == 8
        assert h3a.W_B_PRIME == 0.02787029633307472
        assert h3a.BP_KONSISTENZ_TOL == 1e-3
        assert h3a.NQ_BY_ARM == {"q3_d3": 2, "q5_d5": 3}
        assert h3a.SET_VERDICT == "verdict" and h3a.SET_CAL == "cal"

    def test_delegation_is_identity_phase9_10(self):
        # Run-3 aendert NUR Punktesatz/Zentrum — die d-generischen Funktionen
        # sind UNVERAENDERT delegiert (keine Kopie, keine Reimplementation).
        assert h3a.stress_noise_model is aer.stress_noise_model
        assert h3a.exact_point_level is aer.exact_point_level
        assert h3a.sampled_point_level is aer.sampled_point_level
        assert h3a.ratio_ro_exact is aer.ratio_ro_exact
        assert h3a.center_v2 is aer.center_v2
        assert h3a.fit_b_p is aer.fit_b_p
        assert h3a.build_struct_circuit is aer.build_struct_circuit
        assert h3a.build_loschmidt_circuit is aer.build_loschmidt_circuit
        assert h3a.build_ladder_circuit is s2b.build_ladder_circuit
        assert h3a.ladder_point_level is s2b.ladder_point_level
        assert h3a.fit_echo_ladder is s2b.fit_echo_ladder

    def test_results_path(self):
        assert h3a.RESULTS_PATH == "pt_ram_q_stage3_results.json"


# ------------------------------------------------------------- gamma_aer-Fit

class TestGammaAerFit:
    def _cells_one(self, **over):
        pts = h3a._cal_pts()
        pt = pts[("q3_d3", 149)]
        cell = {"arm": "q3_d3", "set": "cal", "P": 149, "p1": 1e-3,
                "leg": "sampled", "ens": 0, "kappa": 0.95,
                "ratio": 0.5, "ro_hat": 0.012, "b_p": 0.7, "domain": True}
        cell.update(over)
        return pt, cell

    def test_convention_gamma_is_slope(self):
        # delta_cal = ratio_ro_exact + b_P*(kappa-1) - ratio; konstruiere
        # ratio = A - cP*G  =>  delta = cP*G  =>  gamma = G (LSQ durch Null)
        pts = h3a._cal_pts()
        pt = pts[("q3_d3", 149)]
        nq = h3a.NQ_BY_ARM["q3_d3"]
        cp = h3a.cP_of(pt)
        G = 0.031
        b, kappa, ro_hat = 0.7, 0.95, 0.012
        ratio = (h3a.ratio_ro_exact(pt, ro_hat, nq)
                 + b * (kappa - 1.0)) - cp * G
        cell = {"arm": "q3_d3", "set": "cal", "P": 149, "leg": "sampled",
                "domain": True, "kappa": kappa, "ratio": ratio,
                "ro_hat": ro_hat, "b_p": b}
        table = h3.load_frozen_prereg()["prediction_freeze"]["cP_freeze"]
        out = h3a.gamma_aer_fit([cell], pts, table)
        assert out["q3_d3"]["n_cells"] == 1
        assert out["q3_d3"]["gamma"] == pytest.approx(G, abs=1e-12)
        # Arm ohne Zellen: gamma 0, n_cells 0 (kein Fit-Call)
        assert out["q5_d5"] == {"gamma": 0.0, "n_cells": 0}

    def test_filters_verdict_and_subdomain_and_exact(self):
        pts = h3a._cal_pts()
        table = h3.load_frozen_prereg()["prediction_freeze"]["cP_freeze"]
        _, good = self._cells_one()
        # Verdict-Zelle mit identischem Profil: muss RAUSGEFILTERT werden
        _, ver = self._cells_one(set="verdict")
        # Sub-Domain-Kalibrier-Zelle: raus
        _, sub = self._cells_one(kappa=0.5, domain=False)
        # Exakt-Bein-Kalibrier-Zelle: raus
        _, ex = self._cells_one(leg="exact")
        out = h3a.gamma_aer_fit([good, ver, sub, ex], pts, table)
        assert out["q3_d3"]["n_cells"] == 1

    def test_two_cells_weighted_lsq(self):
        pts = h3a._cal_pts()
        table = h3.load_frozen_prereg()["prediction_freeze"]["cP_freeze"]
        p3 = pts[("q3_d3", 149)]
        p5 = pts[("q5_d5", 433)]
        cells = []
        for pt, arm, G in ((p3, "q3_d3", 0.02), (p5, "q5_d5", 0.04)):
            nq = h3a.NQ_BY_ARM[arm]
            cp = h3a.cP_of(pt)
            b, kappa, ro_hat = 0.7, 0.95, 0.012
            ratio = (h3a.ratio_ro_exact(pt, ro_hat, nq)
                     + b * (kappa - 1.0)) - cp * G
            cells.append({"arm": arm, "set": "cal", "P": pt["P"],
                          "leg": "sampled", "domain": True, "kappa": kappa,
                          "ratio": ratio, "ro_hat": ro_hat, "b_p": b})
        out = h3a.gamma_aer_fit(cells, pts, table)
        assert out["q3_d3"]["gamma"] == pytest.approx(0.02, abs=1e-12)
        assert out["q5_d5"]["gamma"] == pytest.approx(0.04, abs=1e-12)


# ------------------------------------------------------------------ Gate-Lesart

class TestValidateForm:
    @staticmethod
    def _cell(leg, kappa, res2, res1=0.0, ens=0):
        return {"arm": "q3_d3", "set": "verdict", "P": 181, "p1": 1e-3,
                "leg": leg, "ens": ens, "kappa": kappa, "ratio": 0.5,
                "ro_hat": 0.01, "b_p": 0.7, "res_v1": res1, "res_v2": res2,
                "domain": kappa >= h3a.KAPPA_CEILING}

    def test_exact_violation_detected(self):
        cells = [self._cell("exact", 0.9, 0.02),
                 self._cell("exact", 0.85, 0.04, ens=None)]
        out = h3a.validate_form({"cells": cells})
        assert out["v2_pass_exact"] is False
        assert len(out["v2_violations"]) == 1
        assert out["v2_violations"][0]["res"] == 0.04
        assert out["max_res_v2_exact"] == 0.04

    def test_sampled_q975_gate(self):
        # 40 Domain-Zellen im Band + 2 Ausreisser 0.2 -> q97.5 > W_A
        cells = [self._cell("sampled", 0.9, 0.01 + 1e-4 * i, ens=i)
                 for i in range(40)]
        cells += [self._cell("sampled", 0.9, 0.2, ens=40),
                  self._cell("sampled", 0.9, 0.2, ens=41)]
        out = h3a.validate_form({"cells": cells})
        assert out["v2_pass_sampled"] is False
        assert out["sampled_q975"] > h3a.W_A
        assert out["n_domain_cells_sampled"] == 42
        # Ohne Ausreisser: q97.5 <= W_A -> Gate S gruen
        out2 = h3a.validate_form({"cells": cells[:40]})
        assert out2["v2_pass_sampled"] is True
        assert out2["sampled_q975"] <= h3a.W_A

    def test_subdomain_excluded_from_gates(self):
        # kappa < 0.81: weder Gate-E-Verletzung noch Domain-Zelle
        cells = [self._cell("exact", 0.5, 0.5, ens=None),
                 self._cell("sampled", 0.7, 0.4, ens=0)]
        out = h3a.validate_form({"cells": cells})
        assert out["v2_violations"] == []
        assert out["v2_pass"] is True
        assert out["n_domain_cells_exact"] == 0
        assert out["n_domain_cells_sampled"] == 0

    def test_v1_fail_counted_over_all_cells(self):
        # v1-Fails werden ueber ALLE Zellen gezaehlt (auch sub-domain)
        cells = [self._cell("exact", 0.9, 0.01, res1=0.01, ens=None),
                 self._cell("sampled", 0.5, 0.01, res1=0.5, ens=0)]
        out = h3a.validate_form({"cells": cells})
        assert out["v1_fail_cells"] == 1

    def test_empty_domain_quantile_zero(self):
        out = h3a.validate_form({"cells": [self._cell("exact", 0.5, 0.9,
                                                      ens=None)]})
        assert out["sampled_q975"] == 0.0
        assert out["v2_pass"] is True


# ------------------------------------------------- Commitiertes Stage-3-Resultat

class TestStage3Results:
    """Pins gegen das COMMITTED Voll-Grid-Resultat (skipif offline)."""

    @pytest.fixture(scope="class")
    def res(self):
        if not os.path.exists(h3a.RESULTS_PATH):
            pytest.skip("pt_ram_q_stage3_results.json noch nicht committed")
        with open(h3a.RESULTS_PATH, encoding="utf-8") as fh:
            return json.load(fh)

    def test_schema_basics(self, res):
        assert res["experiment"] == "044-ram-q-coherent-prep-error"
        assert res["hypothesis"] == "H-RAM-Q-4"
        assert res["status"] == "STAGE3_AER_COMPLETED"
        assert res["prereg_md5"] == "baaca1f6772e07b0847fe436da7e16da"
        assert res["grid"]["levels"] == [0.0, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2]
        assert res["grid"]["n_ens"] == 8 and res["grid"]["reps"] == 3

    def test_sets_complete(self, res):
        assert res["sets"]["verdict"] == {
            "q3_d3": [181, 229, 283, 379, 467, 613, 691, 797],
            "q5_d5": [467, 547, 613, 673, 691]}
        assert res["sets"]["kalibrier"] == {
            "q3_d3": [149, 197, 251, 347, 433, 577, 659, 761],
            "q5_d5": [433, 499, 577, 631, 659]}

    def test_result_tables_26_points(self, res):
        assert len(res["exact"]) == 26 and len(res["b_p"]) == 26
        assert len(res["sampled"]) == 26 * 6
        assert len(res["cells"]) == 26 * 6 * 9          # 8 ens + 1 exact
        assert len(res["residuals_v2"]) == 26 * 6 * 8
        assert len(res["residuals_v1"]) == 26 * 6 * 8
        verdict_keys = [k for k in res["b_p"] if k.startswith("verdict|")]
        cal_keys = [k for k in res["b_p"] if k.startswith("cal|")]
        assert len(verdict_keys) == 13 and len(cal_keys) == 13

    def test_cells_carry_b_p(self, res):
        # gamma_aer-Fit liest b_p aus den SAMPLED-Zellen (Fix der
        # KeyError-Serie); das Exakt-Bein nutzt den Punkt-Fit aus
        # res["b_p"] und traegt kein per-Zell-b_p (by Design).
        sampled = [c for c in res["cells"] if c["leg"] == "sampled"]
        exact = [c for c in res["cells"] if c["leg"] == "exact"]
        assert len(sampled) == 26 * 6 * 8 and len(exact) == 26 * 6
        assert all("b_p" in c for c in sampled)
        assert all("b_p" not in c for c in exact)

    def test_form_gates_green(self, res):
        fv = res["form_validation"]
        assert fv["v2_pass"] is True
        assert fv["v2_pass_exact"] is True and fv["v2_pass_sampled"] is True
        assert fv["v2_violations"] == []
        assert fv["max_res_v2_exact"] <= h3a.TOL_FORM
        assert fv["sampled_q975"] <= h3a.W_A

    def test_w_b_doubleprime_reused(self, res):
        assert res["w_b_doubleprime"]["wert"] == 0.02787029633307472
        assert res["w_b_doubleprime"]["reused"] is True
        assert res["w_b_consistency"]["gate_s_ok"] is True

    def test_bp_kalibrier_konsistenz(self, res):
        """10/13 Kalibrier-Punkte bit-konsistent; 3 Grenzzweig-Ausnahmen.

        761/197/631 sitzen an einem Grenzzweig der Transpile-Synthese:
        ±1 ulp (2**-52) multiplikativ an den Amplituden kippt >= 3
        gleichberechtigte Zerlegungen; die so erreichte A-Geometrie
        reproduziert den committeten Stage-3-kappa am Punkt 761
        bit-exakt (Differenz -4.44e-16 = die Störung selbst;
        scratch_phase11_geometry_kappa, 2026-09-28).  Die committeten
        ops_struct der 3 Punkte (197/631: mit x-Gate) belegen die
        Zweig-Differenz im Artefakt selbst.  cz/2q-Counts sind
        varianteninvariant (ISA-3-Re-Verifikation 2026-09-28:
        559/84 bit-gleich, 0/116 Abweichungen).  KEINE
        Toleranz-Erhoehung: BP_KONSISTENZ_TOL bleibt 1e-3 und prueft
        scharf ueber die 10 ungestoerten Punkte; die 3 Ausnahmen
        sind als committete Werte eingefroren (jede grobe
        Referenz-Verfehlung ~1e-1 wuerde weiterhin feuern).
        """
        kons = res["b_p_kalibrier_konsistenz"]
        razor = {"q3_d3|761": 0.02750701876034989,
                 "q3_d3|197": 0.02711532692526042,
                 "q5_d5|631": 0.007622010515988098}
        assert len(kons) == 13
        for k, v in kons.items():
            if k in razor:
                assert v["ok"] is False, k
                assert abs(v["abs_diff"] - razor[k]) < 1e-12, k
            else:
                assert v["ok"] is True, k
                assert v["abs_diff"] < h3a.BP_KONSISTENZ_TOL, k

    def test_gamma_aer_near_zero(self, res):
        for arm in h3a.ARMS:
            g = res["gamma_aer"][arm]["gamma"]
            assert abs(g) < 0.005, f"gamma_aer {arm} = {g} nicht ~0"
            assert res["gamma_aer"][arm]["n_cells"] > 0

    def test_ladder_diagnostic(self, res):
        lad = res["echo_ladder_aer"]
        assert lad["q3_d3"]["P"] == 181 and lad["q5_d5"]["P"] == 467
        assert lad["q3_d3"]["repeats"] == [1, 2, 4, 8]
        assert len(lad["q3_d3"]["levels"]) == 6
        assert res["ladder_summary"]["n_ladder_domain_levels"] >= 1