# -*- coding: utf-8 -*-
"""Phase 10b — Stage-2b Aer-Bein am Minimalregister (EXPERIMENT 043, 0 QPU).

Spiegel der Phase-9-aer-Tests: die Tests pinnen die gefrorene Semantik des
Stage-2b-Moduls — Delegation auf die d-generischen Phase-9-Funktionen, die
Echo-Leiter (r=1 == gepaarter Loschmidt, geometrisches Gesetz), die
kappa-basierte Domain-Regel, das 90-Circuit-Set gegen das gefrorene
circuit_budget und die Kontroll-Referenz-Anker (t4, konservativste Ecke).

Exakt-Diagnose-Pins stammen aus scratch_stage2b_probe.py (0 QPU, VOR dem
Modulbau gelaufen — Anti-Sharpshooter: Zahlen VOR der Implementierung
fixiert).
"""
import json
import os

import numpy as np
import pytest

import pt_ram_q_hardware as hw
import pt_ram_q_hardware_aer as aer
import pt_ram_q_hardware2 as hw2
import pt_ram_q_hardware2_aer as s2b

RESULTS_PATH = s2b.RESULTS_PATH

DOC = hw2.load_frozen_prereg()
PTS = {}
for _arm in ("q3_d3", "q5_d5"):
    for _p in DOC["prediction_freeze"]["points"][_arm]:
        _p = dict(_p)
        _p["arm"] = _arm
        PTS[(_arm, _p["P"])] = _p
DG = {}
for _arm in ("q3_d3", "q5_d5"):
    for _p in DOC["diagnostik_bein"]["points"][_arm]:
        _p = dict(_p)
        _p["arm"] = _arm
        DG[(_arm, _p["P"])] = _p

# --- Exakt-Diagnose-Pins (Probe, 0 QPU) ---
RATIO_RO_PIN = {
    ("q3_d3", 149): 0.926259, ("q5_d5", 433): 0.907401,
}
LADDER_KAPPA_PIN = {  # p1=3e-4, r in (1,2,4,8)
    "q3_d3": (0.9915, 0.9830, 0.9664, 0.9343),
    "q5_d5": (0.9725, 0.9459, 0.8953, 0.8035),
}
LADDER_CZ = {"q3_d3": (2, 4, 8, 16), "q5_d5": (8, 16, 32, 64)}
B_P_RANGES = {"q3_d3": (1.69, 1.80), "q5_d5": (1.01, 1.05)}
ANCHOR = {"q3_d3": 149, "q5_d5": 433}


class TestDelegation:
    """Die d-generischen Funktionen sind DIE Phase-9-Objekte (keine Kopie)."""

    GENERIC = (
        "stress_noise_model", "readout_apply", "share_hw_fft",
        "share_hw_folded", "fold_d", "p0_fraction", "ratio_from_counts",
        "ratio_ro_exact", "alpha_from_kappa", "center_v1", "center_v2",
        "fit_b_p", "stage2_seed", "_amp_vector", "build_struct_circuit",
        "build_loschmidt_circuit", "build_state_circuit",
        "build_cal_circuit", "exact_point_level", "sampled_point_level",
        "compute_w_b", "nq_of",
    )

    def test_generic_functions_are_the_aer_objects(self):
        for name in self.GENERIC:
            assert getattr(s2b, name) is getattr(aer, name), name

    def test_lower_prime_band_edge_ratio_is_phase9_variant(self):
        assert s2b.lower_prime_band_edge_ratio is aer.lower_prime_band_edge

    def test_arms_and_nq(self):
        assert s2b.ARMS == ("q3_d3", "q5_d5")
        assert s2b.NQ_BY_ARM == {"q3_d3": hw2.NQ3, "q5_d5": hw2.NQ5}
        assert s2b.NQ_BY_ARM == {"q3_d3": 2, "q5_d5": 3}

    def test_results_path_and_frozen_constants_unchanged(self):
        assert s2b.RESULTS_PATH == "pt_ram_q_stage2b_results.json"
        assert s2b.SHOTS == 8192 and s2b.K_REPEATS == 3
        assert s2b.W_A == 0.05 and s2b.KAPPA_CEILING == 0.81
        assert s2b.TOL_FORM == 0.03 and s2b.W_B_FLOOR == 0.01
        assert s2b.N_ENS == 8
        assert s2b.STRESS_GRID_P1 == [0.0, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2]

    def test_ladder_anchor(self):
        assert s2b.ladder_anchor("q3_d3") == 149
        assert s2b.ladder_anchor("q5_d5") == 433
        assert s2b.ladder_anchor("q3_d3") == hw2.LADDER_ANCHORS["q3"]
        assert s2b.ladder_anchor("q5_d5") == hw2.LADDER_ANCHORS["q5"]

    def test_point_sets_from_frozen_payload(self):
        assert {k[1] for k in PTS if k[0] == "q3_d3"} == set(hw2.NEW_Q3_POINTS)
        assert {k[1] for k in PTS if k[0] == "q5_d5"} == set(hw2.NEW_Q5_POINTS)
        assert len(PTS) == 13
        # diagnostik = die 13 ALTEN P, disjunkt zu den VERDICT-Punkten (t5)
        assert {k[1] for k in DG if k[0] == "q3_d3"} == set(hw2.OLD_Q3_POINTS)
        assert {k[1] for k in DG if k[0] == "q5_d5"} == set(hw2.OLD_Q5_POINTS)
        assert len(DG) == 13
        assert not ({k[1] for k in PTS} & {k[1] for k in DG})


class TestBandEdge:
    """t4-Bandkante in SHARE-Einheiten, konservativste Ecke kappa=KAPPA_CEILING."""

    def test_edge_formula_bit_exact(self):
        for arm in s2b.ARMS:
            pt = PTS[(arm, ANCHOR[arm])]
            edge = s2b.lower_prime_band_edge(pt)
            manual = (hw.KAPPA_CEILING * (1.0 - 1.0 / hw.SHOTS)
                      * pt["share_true_reg"] + pt["L_q"] - hw.W_A)
            assert edge == manual

    def test_edge_positive_and_above_expected_share(self):
        t4 = DOC["controls"]["t4_negative_must_not_fire"]
        for arm, ctl_key in (("q3_d3", "composite_q3"),
                             ("q5_d5", "composite_q5")):
            pt = PTS[(arm, ANCHOR[arm])]
            edge = s2b.lower_prime_band_edge(pt)
            assert edge > 0.0
            # gefrorene Erwartung liegt WEIT unter der Kante (must-not-fire)
            assert t4[ctl_key]["expected_share"] < edge
            assert t4[ctl_key]["expected_share"] > 0.0

    def test_anchor_edges_match_frozen_derivation(self):
        # Probe-/Freeze-Derivation: 4.085 (q3) / 3.026 (q5) minus W_A
        assert s2b.lower_prime_band_edge(
            PTS[("q3_d3", 149)]) == pytest.approx(4.08493652507237, abs=1e-9)
        assert s2b.lower_prime_band_edge(
            PTS[("q5_d5", 433)]) == pytest.approx(3.0259757753424976, abs=1e-9)

    def test_uniform_controls_expect_zero_below_edge(self):
        for arm in s2b.ARMS:
            pt = PTS[(arm, ANCHOR[arm])]
            assert s2b.lower_prime_band_edge(pt) > 0.0  # 0.0 liegt unter Kante


class TestLadderBuilder:
    ARM, P = "q3_d3", 149
    PT = PTS[("q3_d3", 149)]
    NQ = 2

    def test_r1_is_exactly_the_paired_loschmidt(self):
        for measure in (True, False):
            l1 = s2b.build_ladder_circuit(self.PT, self.NQ, 1, measure=measure)
            lo = s2b.build_loschmidt_circuit(self.PT, self.NQ, measure=measure)
            assert l1 == lo

    def test_invalid_r_raises(self):
        with pytest.raises(ValueError):
            s2b.build_ladder_circuit(self.PT, self.NQ, 3)
        with pytest.raises(ValueError):
            s2b.build_ladder_circuit(self.PT, self.NQ, 0)
        with pytest.raises(ValueError):
            s2b.build_ladder_circuit(self.PT, self.NQ, 16)

    def test_block_and_barrier_structure(self):
        # r Bloecke (Prep+Inverse) + (r-1) Separator-Barriern + r Block-BARRIER
        for r in (2, 4, 8):
            qc = s2b.build_ladder_circuit(self.PT, self.NQ, r, measure=False)
            ops = qc.count_ops()
            assert ops["state_preparation"] == r
            assert ops["state_preparation_dg"] == r
            assert ops["barrier"] == 2 * r - 1

    def test_measure_registers(self):
        qc = s2b.build_ladder_circuit(self.PT, self.NQ, 2, measure=True)
        assert qc.num_qubits == self.NQ and qc.num_clbits == self.NQ
        qnb = s2b.build_ladder_circuit(self.PT, self.NQ, 2, measure=False)
        assert qnb.num_clbits == 0

    @pytest.mark.parametrize("arm, expected_cz", [
        ("q3_d3", LADDER_CZ["q3_d3"]), ("q5_d5", LADDER_CZ["q5_d5"])])
    def test_transpiled_depth_scales_linearly(self, arm, expected_cz):
        pt = PTS[(arm, ANCHOR[arm])]
        nq = s2b.NQ_BY_ARM[arm]
        for r, cz in zip(hw2.LADDER_REPEATS, expected_cz):
            t = s2b.transpile(
                s2b.build_ladder_circuit(pt, nq, r, measure=False),
                basis_gates=s2b.BASIS_GATES, optimization_level=3,
                seed_transpiler=s2b.TRANSPILE_SEED)
            assert t.count_ops().get("cz", 0) == cz, (arm, r)


class TestEchoLadderFit:
    def test_pure_power_law_recovered_exactly(self):
        kb = 0.99
        kappas = [kb ** r for r in (1, 2, 4, 8)]
        fit = s2b.fit_echo_ladder(kappas, [1, 2, 4, 8])
        assert fit["kappa_block"] == pytest.approx(kb, abs=1e-12)
        assert fit["slope"] == pytest.approx(np.log(kb), abs=1e-12)
        assert fit["intercept"] == pytest.approx(0.0, abs=1e-10)
        assert fit["max_res_log"] < 1e-12

    def test_two_points_always_exact(self):
        fit = s2b.fit_echo_ladder([0.98, 0.98 ** 4], [1, 4])
        # 2 Stufen = 2 Parameter -> exakt, Residual 0
        assert fit["max_res_log"] < 1e-12
        assert fit["kappa_block"] == pytest.approx(
            (0.98 ** 4 / 0.98) ** (1.0 / 3.0), abs=1e-12)

    def test_len_mismatch_and_short_raise(self):
        with pytest.raises(ValueError):
            s2b.fit_echo_ladder([0.99, 0.98], [1, 2, 4])
        with pytest.raises(ValueError):
            s2b.fit_echo_ladder([0.99], [1])

    def test_non_power_law_gives_large_residual(self):
        kappas = [0.99, 0.9, 0.8, 0.2]  # kein reines Potenzgesetz
        fit = s2b.fit_echo_ladder(kappas, [1, 2, 4, 8])
        assert fit["max_res_log"] > 0.05


class TestLadderPointLevel:
    """Exakt-Bein der Leiter: p1=0 -> kappa=1.0; 3e-4 -> Probe-Pins;
    cz-Tiefe skaliert linear in r; Gesetz haelt im Domainbereich."""

    def test_p1_zero_gives_unit_kappa_all_r(self):
        for arm in s2b.ARMS:
            pt = PTS[(arm, ANCHOR[arm])]
            nq = s2b.NQ_BY_ARM[arm]
            for r in hw2.LADDER_REPEATS:
                lv = s2b.ladder_point_level(pt, nq, r, 0.0)
                assert lv["kappa_r"] == pytest.approx(1.0, abs=1e-9), (arm, r)

    def test_kappa_pins_at_3e_minus_4(self):
        for arm, pins in LADDER_KAPPA_PIN.items():
            pt = PTS[(arm, ANCHOR[arm])]
            nq = s2b.NQ_BY_ARM[arm]
            for r, pin in zip(hw2.LADDER_REPEATS, pins):
                lv = s2b.ladder_point_level(pt, nq, r, 3e-4)
                assert lv["kappa_r"] == pytest.approx(pin, abs=2e-3), (arm, r)

    def test_kappa_monotone_decreasing_in_r(self):
        for arm in s2b.ARMS:
            pt = PTS[(arm, ANCHOR[arm])]
            nq = s2b.NQ_BY_ARM[arm]
            ks = [s2b.ladder_point_level(pt, nq, r, 3e-4)["kappa_r"]
                  for r in hw2.LADDER_REPEATS]
            assert ks[0] > ks[1] > ks[2] > ks[3], arm

    def test_law_holds_in_domain_breaks_deep_sub_domain(self):
        # Domainbereich (p1=3e-4): max log-Residual klein (Probe ~1e-4/6e-4)
        # vs. deep-sub-domain (p1=1e-2): das Gesetz BRICHT (Probe 0.125/0.324)
        for arm in s2b.ARMS:
            pt = PTS[(arm, ANCHOR[arm])]
            nq = s2b.NQ_BY_ARM[arm]
            dom = [s2b.ladder_point_level(pt, nq, r, 3e-4)["kappa_r"]
                   for r in hw2.LADDER_REPEATS]
            fit_dom = s2b.fit_echo_ladder(dom, list(hw2.LADDER_REPEATS))
            assert fit_dom["max_res_log"] <= 1e-3, arm
            sub = [s2b.ladder_point_level(pt, nq, r, 1e-2)["kappa_r"]
                   for r in hw2.LADDER_REPEATS]
            fit_sub = s2b.fit_echo_ladder(sub, list(hw2.LADDER_REPEATS))
            assert fit_sub["max_res_log"] > 0.05, arm

    def test_cz_counts_scale_linearly(self):
        for arm, czs in LADDER_CZ.items():
            pt = PTS[(arm, ANCHOR[arm])]
            nq = s2b.NQ_BY_ARM[arm]
            for r, cz in zip(hw2.LADDER_REPEATS, czs):
                lv = s2b.ladder_point_level(pt, nq, r, 0.0)
                assert lv["ops_ladder"].get("cz", 0) == cz, (arm, r)


class TestCircuitSet:
    CS = s2b.build_hardware_circuit_set()
    KINDS = {"structure": 39, "loschmidt": 13, "echo_ladder": 6,
             "diagnostik_structure": 13, "diagnostik_loschmidt": 13,
             "negative_control": 4, "readout_cal": 2}

    def test_budget_split_matches_frozen_circuit_budget(self):
        assert len(self.CS) == 90
        counts = {}
        for c in self.CS:
            counts[c["kind"]] = counts.get(c["kind"], 0) + 1
        assert counts == self.KINDS

    def test_unique_names(self):
        names = [c["name"] for c in self.CS]
        assert len(names) == len(set(names))

    def test_all_shots_8192(self):
        assert all(c["shots"] == hw.SHOTS for c in self.CS)

    def test_structure_and_loschmidt_cover_the_13_new_points(self):
        st = [c["P"] for c in self.CS if c["kind"] == "structure"]
        # arm-weise (ARMS-Reihenfolge), je 3 Reps, P aufsteigend pro Arm
        assert st == ([P for P in sorted(hw2.NEW_Q3_POINTS) for _ in range(3)]
                      + [P for P in sorted(hw2.NEW_Q5_POINTS) for _ in range(3)])
        lo = [c["P"] for c in self.CS if c["kind"] == "loschmidt"]
        assert sorted(lo) == sorted(hw2.NEW_Q3_POINTS + hw2.NEW_Q5_POINTS)
        reps = {c["rep"] for c in self.CS if c["kind"] == "structure"}
        assert reps == {0, 1, 2}

    def test_ladder_only_r_ge_2_at_anchors(self):
        lad = [c for c in self.CS if c["kind"] == "echo_ladder"]
        assert {(c["arm"], c["P"], c["r"]) for c in lad} == {
            ("q3_d3", 149, 2), ("q3_d3", 149, 4), ("q3_d3", 149, 8),
            ("q5_d5", 433, 2), ("q5_d5", 433, 4), ("q5_d5", 433, 8)}
        # r=1 ist geteilt (kein eigenes Circuit)
        assert not any(c["r"] == 1 for c in lad)
        assert any(c["name"] == "loschmidt_q3_d3_149" for c in self.CS)
        assert any(c["name"] == "loschmidt_q5_d5_433" for c in self.CS)

    def test_diagnostik_covers_the_13_old_points(self):
        ds = {c["P"] for c in self.CS
              if c["kind"] == "diagnostik_structure"}
        dl = {c["P"] for c in self.CS
              if c["kind"] == "diagnostik_loschmidt"}
        assert ds == {c[1] for c in DG}
        assert dl == ds
        assert all(c["rep"] == 0 for c in self.CS
                   if c["kind"] == "diagnostik_structure")

    def test_controls_match_frozen_payload_bit_exact(self):
        t4 = DOC["controls"]["t4_negative_must_not_fire"]
        by_name = {c["name"]: c for c in self.CS
                   if c["kind"] == "negative_control"}
        assert set(by_name) == {"ctrl_composite_P149_d3",
                                "ctrl_composite_P433_d5",
                                "ctrl_uniform_q3", "ctrl_uniform_q5"}
        for name, key in (("ctrl_composite_P149_d3", "composite_q3"),
                          ("ctrl_composite_P433_d5", "composite_q5"),
                          ("ctrl_uniform_q3", "uniform_q3"),
                          ("ctrl_uniform_q5", "uniform_q5")):
            c = by_name[name]
            assert c["expected_share"] == t4[key]["expected_share"]
            # Kontroll-Referenz = Anker-Punkt des Arms
            assert c["P"] == ANCHOR[c["arm"]]
            # must-not-fire: Erwartung unter der Share-Einheiten-Kante
            assert c["expected_share"] < c["lower_prime_band_edge"]

    def test_cal_circuits(self):
        cals = [c for c in self.CS if c["kind"] == "readout_cal"]
        assert {c["name"] for c in cals} == {"cal_2q", "cal_3q"}

    def test_circuit_qubit_counts(self):
        for c in self.CS:
            nq = c["circuit"].num_qubits
            if c["kind"] in ("structure", "loschmidt", "echo_ladder",
                             "diagnostik_structure", "diagnostik_loschmidt"):
                assert nq == s2b.NQ_BY_ARM[c["arm"]], c["name"]
            elif c["kind"] == "negative_control":
                assert nq == s2b.NQ_BY_ARM[c["arm"]], c["name"]
            else:  # readout_cal
                assert c["name"] == f"cal_{nq}q", c["name"]


class TestSampledLegSmoke:
    ARM, P = "q3_d3", 149
    PT = PTS[("q3_d3", 149)]

    def test_deterministic_rerun(self):
        a = s2b.sampled_point_level(self.PT, 2, 3e-4, n_ens=2, reps=1)
        b = s2b.sampled_point_level(self.PT, 2, 3e-4, n_ens=2, reps=1)
        assert a["kappa_ens"] == b["kappa_ens"]
        assert a["ratio_ens"] == b["ratio_ens"]
        assert a["ro_hat_ens"] == b["ro_hat_ens"]

    def test_plausible_ranges(self):
        sa = s2b.sampled_point_level(self.PT, 2, 3e-4, n_ens=2, reps=1)
        for kap, rat, ro in zip(sa["kappa_ens"], sa["ratio_ens"],
                                sa["ro_hat_ens"]):
            assert 0.9 < kap <= 1.0 + 1e-9
            assert rat > 0.0
            assert ro == pytest.approx(0.01, abs=0.005)


class TestRunStage2bSerializable:
    """Serialize-Contract mit Monkeypatch (Fake-Beine, String-Keys)."""

    @pytest.fixture()
    def results(self, monkeypatch):
        def fake_exact(pt, nq, p1, seed=s2b.SIM_SEED_EXACT):
            return {"p1": p1, "pl_bare": 0.99, "kappa": 0.98, "u": 0.06,
                    "alpha": 0.97, "share": 0.5, "ratio": 0.9,
                    "res_v1": 0.01, "ops_struct": {"rz": 3}}

        def fake_sampled(pt, nq, p1, n_ens=2, reps=1, level_tag=None):
            return {"kappa_ens": [0.98] * n_ens, "ratio_ens": [0.9] * n_ens,
                    "ro_hat_ens": [0.01] * n_ens}

        def fake_ladder(pt, nq, r, p1, seed=s2b.SIM_SEED_EXACT):
            return {"p1": p1, "r": r, "kappa_r": 0.99 ** r,
                    "ops_ladder": {"cz": 2 * r, "barrier": 2 * r - 1}}

        monkeypatch.setattr(s2b, "exact_point_level", fake_exact)
        monkeypatch.setattr(s2b, "sampled_point_level", fake_sampled)
        monkeypatch.setattr(s2b, "ladder_point_level", fake_ladder)
        return s2b.run_stage2b(n_ens=1, reps=1, results_path=None)

    def test_status_and_md5(self, results):
        assert results["status"] == "STAGE2B_AER_COMPLETED"
        assert results["prereg_md5"] == hw2.load_frozen_prereg()["md5"]
        assert results["hypothesis"] == hw2.HYPOTHESIS

    def test_string_keys_everywhere(self, results):
        for k in results["exact"]:
            assert k.split("|")[0] in s2b.ARMS and int(k.split("|")[1]) > 0
        for k in results["b_p"]:
            assert "|" in k
        assert set(results["sampled"]) == {
            f"{arm}|{P}|{p1:g}"
            for arm in s2b.ARMS for P in ({k[1] for k in PTS if k[0] == arm})
            for p1 in s2b.STRESS_GRID_P1}

    def test_cells_shape(self, results):
        # 13 Punkte x 6 Levels x (1 sampled-ens + 1 exact)
        assert len(results["cells"]) == 13 * 6 * 2
        legs = {c["leg"] for c in results["cells"]}
        assert legs == {"sampled", "exact"}
        assert all(c["domain"] == (c["kappa"] >= hw.KAPPA_CEILING)
                   for c in results["cells"])

    def test_res_v2_uses_v2_center(self, results):
        # Residual-Listen tragen nur das SAMPLED-Bein (Phase-9-Spiegel):
        # 13 Punkte x 6 Levels x n_ens=1
        assert len(results["residuals_v2"]) == 13 * 6
        assert len(results["residuals_v1"]) == 13 * 6

    def test_echo_ladder_sections(self, results):
        lad = results["echo_ladder"]
        assert set(lad) == {"q3_d3", "q5_d5"}
        for arm in s2b.ARMS:
            assert lad[arm]["P"] == ANCHOR[arm]
            assert lad[arm]["repeats"] == [1, 2, 4, 8]
            assert len(lad[arm]["levels"]) == 6
            for lv in lad[arm]["levels"]:
                assert set(lv["kappa_by_r"]) == {"r1", "r2", "r4", "r8"}
                assert lv["kappa_by_r"]["r1"] == 0.99
                assert lv["fit"]["kappa_block"] == pytest.approx(0.99,
                                                                 abs=1e-12)
        ops = results["ladder_ops"]
        assert set(ops) == {f"{arm}|r{r}"
                            for arm in s2b.ARMS for r in (1, 2, 4, 8)}

    def test_ladder_summary_domain_rule_uses_r1_kappa(self, results):
        ls = results["ladder_summary"]
        # p1=0 (kappa_1 = 1.0) ist Domain; mit dem Fake bleiben alle kappa_r
        # == 0.99**r > 0.81, also alle 12 Level domain
        assert ls["n_ladder_domain_levels"] == 12
        assert ls["law_max_res_log_domain"] < 1e-12

    def test_form_validation_and_w_b_wired(self, results):
        assert results["form_validation"]["v2_pass"] is True
        # compute_w_b liefert den geclippten Float; raw/gate sind Top-Level
        assert s2b.W_B_FLOOR <= results["w_b"] <= s2b.W_A
        assert results["w_b_gate_ok"] is True
        assert results["w_b"] == results["w_b_raw_q975"]

    def test_json_round_trip(self, results):
        blob = json.dumps(results, sort_keys=True)
        back = json.loads(blob)
        assert back["status"] == "STAGE2B_AER_COMPLETED"
        assert len(back["cells"]) == 13 * 6 * 2


class TestFormValidationWiring:
    """v2-Form/W_B laufen ueber die aer-Funktionen — Spiegel-Regression."""

    def test_w_b_regression_excluded_sub_domain_and_exact(self, monkeypatch):
        # Regression (Phase-9-Praezedenz): nur domain-sampled-Zaellen zaehlen
        # in das q97.5.  Fake-Kurven MIT Steigung 2.0, damit das Zentrum von
        # kappa abhaengt: domain-sampled-Residuum 1e-4, sub-domain-sampled
        # 0.5 -> w_b_raw_q975 == 1e-4 beweist die Exclusion, w_b == Floor
        # beweist das Clipping.
        def fake_exact(pt, nq, p1, seed=s2b.SIM_SEED_EXACT):
            idx = s2b.STRESS_GRID_P1.index(p1)
            kappa = 0.98 - 0.03 * idx
            return {"p1": p1, "pl_bare": 0.99, "kappa": kappa, "u": 0.06,
                    "alpha": 0.97, "share": 0.5,
                    "ratio": 0.90 + 2.0 * (kappa - 0.98),
                    "res_v1": 0.01, "ops_struct": {"rz": 3}}

        def fake_sampled(pt, nq, p1, n_ens=1, reps=1, level_tag=None):
            i = fake_sampled.i
            fake_sampled.i = (i + 1) % 3
            if i == 1:   # sub-domain (kappa < 0.81), grosses Residuum
                kappa, extra = 0.60, 0.5
            else:        # domain, winziges Residuum
                kappa, extra = 0.98, 1e-4
            ratio = s2b.center_v2(kappa, pt, 0.01, 2.0) + extra
            return {"kappa_ens": [kappa], "ratio_ens": [ratio],
                    "ro_hat_ens": [0.01]}

        fake_sampled.i = 0
        monkeypatch.setattr(s2b, "exact_point_level", fake_exact)
        monkeypatch.setattr(s2b, "sampled_point_level", fake_sampled)
        monkeypatch.setattr(s2b, "ladder_point_level", lambda *a, **k: {
            "p1": 0.0, "r": 1, "kappa_r": 1.0, "ops_ladder": {}})
        res = s2b.run_stage2b(n_ens=1, reps=1, results_path=None)
        assert res["w_b"] == pytest.approx(0.01, abs=1e-12)  # Floor greift
        assert res["w_b_gate_ok"] is True
        assert res["w_b_raw_q975"] == pytest.approx(1e-4, abs=1e-6)


class TestValidateFormTwoLegs:
    """Re-Freeze R1: zweistufige Lesart als direkte Gate-Semantik."""

    @staticmethod
    def _cell(leg, kappa, res, arm="q3_d3", P=149, p1=1e-4):
        return {"arm": arm, "P": P, "p1": p1, "leg": leg, "ens": None,
                "kappa": kappa, "res_v2": res, "res_v1": 0.5,
                "domain": kappa >= s2b.KAPPA_CEILING}

    def test_exact_leg_gate_catches_center_violation(self):
        # Zentrum-Verletzung am exact-Bein (sub-domain-Zelle zahlt NICHT ein)
        cells = [self._cell("exact", 0.98, 0.04),
                 self._cell("exact", 0.60, 0.9),
                 self._cell("sampled", 0.98, 1e-4)]
        fv = s2b.validate_form({"cells": cells})
        assert fv["v2_pass"] is False
        assert fv["v2_pass_exact"] is False
        assert fv["v2_pass_sampled"] is True
        assert len(fv["v2_violations"]) == 1
        assert fv["v2_violations"][0] == {"arm": "q3_d3", "P": 149,
                                          "p1": 1e-4, "res": 0.04}
        assert fv["max_res_v2_exact"] == pytest.approx(0.04)
        assert fv["max_res_v2_sampled_diag"] == pytest.approx(1e-4)
        assert fv["n_domain_cells_exact"] == 1
        assert fv["n_domain_cells_sampled"] == 1

    def test_sampled_leg_q975_gate_and_sub_domain_exclusion(self):
        # Gate S: q97.5 der Domain-sampled-Zellen; die sub-domain-Zelle
        # (grosses Residuum) zahlt NICHT ein — mit ihr wuerde q97.5 auf
        # ~0.445 springen, ohne sie bleibt es 1e-4 + 0.9*(0.06-1e-4)
        # ≈ 0.054 > W_A (5 Werte, ein Ausreisser).
        sa = [1e-4] * 4 + [0.06]
        cells = ([self._cell("exact", 0.98, 0.001)]
                 + [self._cell("sampled", 0.98, r) for r in sa]
                 + [self._cell("sampled", 0.60, 0.5)])
        fv = s2b.validate_form({"cells": cells})
        assert fv["v2_pass_exact"] is True
        assert fv["v2_pass_sampled"] is False
        assert fv["v2_pass"] is False
        assert fv["v2_violations"] == []
        assert fv["sampled_q975"] == pytest.approx(0.054, abs=2e-3)
        assert fv["n_domain_cells_sampled"] == 5

    def test_two_legs_green_passes(self):
        cells = ([self._cell("exact", 0.98, 0.001)]
                 + [self._cell("exact", 0.97, 0.002, P=433, arm="q5_d5")]
                 + [self._cell("sampled", 0.98, r) for r in [0.02] * 20]
                 + [self._cell("sampled", 0.60, 0.9)])
        fv = s2b.validate_form({"cells": cells})
        assert fv["v2_pass"] is True
        assert fv["n_cells"] == 23
        assert fv["n_domain_cells_exact"] == 2
        assert fv["n_domain_cells_sampled"] == 20
        assert fv["v1_fail_cells"] == 23


class TestCommittedResults:
    """Pins gegen die committed Stage-2b-Results (skipif)."""

    @pytest.fixture(scope="class")
    def results(self):
        if not os.path.exists(RESULTS_PATH):
            pytest.skip("pt_ram_q_stage2b_results.json noch nicht committed")
        with open(RESULTS_PATH) as fh:
            return json.load(fh)

    def test_status_and_frozen_md5(self, results):
        assert results["status"] == "STAGE2B_AER_COMPLETED"
        # Re-Freeze R1 (Erst-Grid-Form-Verletzung, 0 QPU): neuer md5,
        # alter Freeze 5b91119b925ae365bcd0618a2a15fa30 im Payload
        # (simulation_leg.re_freeze_r1) dokumentiert.
        assert results["prereg_md5"] == "0b9c9968dc5e99a3cc22962a8b760e44"

    def test_v2_pass(self, results):
        fv = results["form_validation"]
        assert fv["v2_pass"] is True
        # Gate E (Zentrum, exact-Bein): max |res_v2| <= TOL_FORM
        assert fv["v2_pass_exact"] is True
        assert fv["max_res_v2_exact"] <= s2b.TOL_FORM
        assert fv["max_res_v2_exact"] == pytest.approx(0.0022, abs=5e-4)
        assert fv["v2_violations"] == []
        # Gate S (Rauschen, sampled-Bein): q97.5 <= W_A; der per-Zell-Max
        # ist Diagnostik (Erst-Grid 0.0396 = 3.4 sigma)
        assert fv["v2_pass_sampled"] is True
        assert fv["sampled_q975"] == pytest.approx(0.0279, abs=5e-4)
        assert fv["max_res_v2_sampled_diag"] <= s2b.W_A
        assert fv["n_domain_cells_exact"] == 60
        assert fv["n_domain_cells_sampled"] == 480

    def test_v1_fails_all_cells(self, results):
        # Probe: res_v1 ~ -0.12 schon bei p1=0 -> ALLE 702 Zellen fail
        assert results["form_validation"]["v1_fail_cells"] == 702
        assert len(results["cells"]) == 702

    def test_domain_counts(self, results):
        dom = [c for c in results["cells"] if c["domain"]]
        # q3: 8 Punkte x 5 Domain-Levels, q5: 5 Punkte x 4 Domain-Levels
        # (exact) -> 60 exakte + 60*8=480 sampled Domain-Zellen
        assert len([c for c in dom if c["leg"] == "exact"]) == 60
        assert len([c for c in dom if c["leg"] == "sampled"]) == 480

    def test_w_b_in_band_unclipped(self, results):
        # compute_w_b liefert den geclippten Float; raw/gate sind Top-Level
        assert s2b.W_B_FLOOR <= results["w_b"] <= s2b.W_A
        assert results["w_b_gate_ok"] is True
        assert results["w_b"] == results["w_b_raw_q975"]

    def test_b_p_arm_ranges(self, results):
        for arm, (lo, hi) in B_P_RANGES.items():
            vals = [v for k, v in results["b_p"].items()
                    if k.startswith(arm + "|")]
            assert len(vals) == {"q3_d3": 8, "q5_d5": 5}[arm]
            assert all(lo <= v <= hi for v in vals), arm

    def test_ratio_ro_anchor_pins(self, results):
        for key, pin in RATIO_RO_PIN.items():
            k = f"{key[0]}|{key[1]}"
            assert results["ratio_ro"][k] == pytest.approx(pin, abs=1e-3), k

    def test_exact_echo_tiefe_pins(self, results):
        # struct cz=1 (q3) / cz=4 (q5) am Anker; Leiter r=1 == Loschmidt
        # cz=2 (q3) / cz=8 (q5)
        ex = results["exact"]["q3_d3|149"]
        assert all(l["ops_struct"].get("cz", 0) == 1 for l in ex)
        ex5 = results["exact"]["q5_d5|433"]
        assert all(l["ops_struct"].get("cz", 0) == 4 for l in ex5)
        ops = results["ladder_ops"]
        assert ops["q3_d3|r1"].get("cz", 0) == 2
        assert ops["q5_d5|r1"].get("cz", 0) == 8

    def test_ladder_law_domain_and_break(self, results):
        ls = results["ladder_summary"]
        assert ls["n_ladder_domain_levels"] == 9
        # Erst-Grid (gemessen 0.01198, q3 bei p1=3e-3): Leiter-Gesetz
        # bleibt innerhalb der Domain kontinuierlich degradierend
        assert ls["law_max_res_log_domain"] <= 0.015
        # deep-sub-domain (p1=1e-2) bricht das Gesetz in beiden Armen
        breaks = [lv["fit"]["max_res_log"]
                  for arm in s2b.ARMS for lv in results["echo_ladder"][arm]["levels"]
                  if lv["kappa_by_r"]["r1"] < hw.KAPPA_CEILING]
        assert breaks and max(breaks) > 0.05

    def test_ladder_kappa_pins(self, results):
        for arm, pins in LADDER_KAPPA_PIN.items():
            lv = [l for l in results["echo_ladder"][arm]["levels"]
                  if l["p1"] == 3e-4][0]
            for r, pin in zip((1, 2, 4, 8), pins):
                assert lv["kappa_by_r"][f"r{r}"] == pytest.approx(
                    pin, abs=2e-3), (arm, r)

    def test_grid_shape(self, results):
        assert len(results["exact"]) == 13
        assert len(results["sampled"]) == 13 * 6
        assert results["grid"]["levels"] == s2b.STRESS_GRID_P1
        assert results["grid"]["n_ens"] == 8 and results["grid"]["reps"] == 3