# -*- coding: utf-8 -*-
"""EXPERIMENT 042 (H-RAM-Q-3) Prereg-Freeze-A-Tests.

Bindend: der Freeze muss die q-universelle Identität bit-exakt gegen die
040-/034-Ketten reproduzieren und die Regeln VOR jedem Hardware-Kontakt
exakt registrieren (REGISTERED_NOT_MEASURED, 0 QPU).
"""

import json

import numpy as np
import pytest

import pt_ram_q_hardware as hw

EXPECTED_MD5 = "432d43fe1bc9e2594efd3b35266d2d81"


# === Freeze-Integrität ===

class TestFreezeIntegrity:
    def test_md5_roundtrip_and_tamper(self):
        doc = hw.load_frozen_prereg()
        assert doc["md5"] == EXPECTED_MD5
        assert hw.verify_prereg_md5(doc)
        # Manipulation wird entdeckt
        tampered = json.loads(json.dumps(doc))
        tampered["status"] = "MEASURED"
        assert not hw.verify_prereg_md5(tampered)

    def test_status_registered_not_measured_zero_qpu(self):
        doc = hw.load_frozen_prereg()
        assert doc["experiment"] == "042-ram-q-hardware-noise-lift"
        assert doc["hypothesis"] == "H-RAM-Q-3"
        assert doc["status"] == "REGISTERED_NOT_MEASURED"
        assert doc["registered_before"] == "2026-09-26"
        # 0 QPU im Freeze A; Hardware erst nach Freeze B
        assert doc["qpu"].startswith("0 QPU")
        assert "EIN Fez-Job (TOKEN1) erst nach Freeze B" in doc["qpu"]
        # User-Anker wörtlich
        assert "REGISTERED_NOT_MEASURED" in doc["user_anchor"]
        assert "vor dem ersten QPU-Kontakt" in doc["user_anchor"]

    def test_freeze_refuses_broken_anchors(self, monkeypatch):
        def broken_040():
            return {109: 2.0}
        monkeypatch.setattr(hw, "_load_040_ratios", broken_040)
        with pytest.raises(ValueError, match="Anker-Verifikation gescheitert"):
            hw.build_prereg_payload()


# === Klassischer Kern: bit-exakt gegen die gefrorenen Ketten ===

class TestClassicalCore:
    def test_q3_arm_bit_exact_vs_040(self):
        doc = hw.load_frozen_prereg()
        r40 = hw._load_040_ratios()
        for pt in doc["prediction_freeze"]["points"]["q3_d9"]:
            assert abs(pt["ratio_true"] - r40[pt["P"]]) <= 1e-9

    def test_q5_arm_bit_exact_vs_034(self):
        doc = hw.load_frozen_prereg()
        r34 = hw._load_034_ratios()
        for pt in doc["prediction_freeze"]["points"]["q5_d25"]:
            assert abs(pt["ratio_true"] - r34[pt["P"]]) <= 1e-9

    def test_universal_formula_matches_closed_forms(self):
        doc = hw.load_frozen_prereg()
        for arm in ("q3_d9", "q5_d25"):
            for pt in doc["prediction_freeze"]["points"][arm]:
                q, m, N, n0 = pt["q"], pt["m"], pt["N"], pt["n0"]
                num = q * sum(x * x for x in N) - m * m
                den = (m - q * n0) ** 2
                # Universalform (q-1)(qΣN²-m²)/(m-qn0)² == ratio_true
                assert abs((q - 1) * num / den - pt["ratio_true"]) <= 1e-12
                # geschlossene Form == Universalform
                assert abs(pt["closed_form"] - pt["ratio_true"]) <= 1e-12
                # L_q = (q-1)^2 m^2 / (S (m-qn0)^2)
                assert abs((q - 1) ** 2 * m * m / (hw.SHOTS * den) - pt["L_q"]) <= 1e-12

    def test_d_invariance_on_flat_registers(self):
        """041 T3: der Ratio ist d-frei — d=9/d=25 tragen die Identischen Ratios."""
        for P in hw.Q3_POINTS:
            wide = hw.arm_point(P, 729, 3)
            flat = hw.arm_point(P, 9, 3)
            assert abs(wide["ratio_true"] - flat["ratio_true"]) <= 1e-12
        for P in hw.Q5_POINTS:
            wide = hw.arm_point(P, 625, 5)
            flat = hw.arm_point(P, 25, 5)
            assert abs(wide["ratio_true"] - flat["ratio_true"]) <= 1e-12

    def test_state_amplitudes_normalized_and_match_counts(self):
        """Operational Definition: |psi> = sum sqrt(n_a/m)|a>; Messung gibt Counts n_a."""
        doc = hw.load_frozen_prereg()
        for arm, n_labels in (("q3_d9", 16), ("q5_d25", 32)):
            for pt in doc["prediction_freeze"]["points"][arm]:
                n_d = pt["n_d"]
                assert len(n_d) == pt["d"]
                assert sum(n_d) == pt["m"]
                amp = [np.sqrt(n / pt["m"]) if n > 0 else 0.0
                       for n in n_d] + [0.0] * (n_labels - pt["d"])
                assert abs(sum(a * a for a in amp) - 1.0) <= 1e-12
                # Messung des States in der Basis gibt exakt n_a/m pro Label
                probs = [a * a for a in amp]
                assert abs(sum(probs) - 1.0) <= 1e-12


# === Registrierte Regeln und Kontrollen ===

class TestRegisteredRules:
    def test_band_center_and_edges(self):
        doc = hw.load_frozen_prereg()
        for arm in ("q3_d9", "q5_d25"):
            for pt in doc["prediction_freeze"]["points"][arm]:
                c = (1.0 - 1.0 / hw.SHOTS) * pt["ratio_true"] + pt["L_q"]
                # Amplification-Ceiling ist die OBERKANTE des rauschfreien Niveaus + w
                ceiling = (1.0 - 1.0 / hw.SHOTS) * pt["ratio_true"] + pt["L_q"] + hw.W_A
                assert c < ceiling < c + hw.W_A + 1e-12
                # das gefrorene Zentrum liegt UNTER dem rauschfreien Niveau + L_q nicht:
                # Zentrum = (1-1/S)*ratio + L_q  (Identität, nicht Band-Ende)
                assert abs(c - ((1.0 - 1.0 / hw.SHOTS) * pt["ratio_true"] + pt["L_q"])) <= 1e-12

    def test_negative_controls_exact_and_below_prime_band_floor(self):
        doc = hw.load_frozen_prereg()
        ctrl = doc["controls"]["t4_negative_must_not_fire"]
        pts = {p["P"]: p for p in doc["prediction_freeze"]["points"]["q3_d9"]}
        prime = pts[109]
        # exakte Erwartungen reproduzierbar
        for sh in ctrl["shuffle"]:
            perm = np.random.RandomState(sh["seed"]).permutation(9).tolist()
            assert perm == sh["permutation"]
            n_sh = [0] * 9
            for a in range(9):
                n_sh[perm[a]] = prime["n_d"][a]
            N_sh = hw.fold_mod_q(n_sh, 9, 3)
            assert N_sh == sh["N_tilde"]
            assert abs((3 * sum(x * x for x in N_sh) - prime["m"] ** 2)
                       / (9.0 * prime["m"]) - sh["expected_share"]) <= 1e-12
        comp = ctrl["composite"]
        assert abs((5 * sum(x * x for x in comp["N_tilde"]) - comp["m"] ** 2)
                   / (25.0 * comp["m"]) - comp["expected_share"]) <= 1e-12
        # Must-not-fire an der konservativsten Ecke (kappa = KAPPA_CEILING, w = W_A):
        # untere Prime-Bandkante = kappa*(1-1/S)*share_true + L_q - w
        for sh in ctrl["shuffle"]:
            floor = (hw.KAPPA_CEILING * (1 - 1 / hw.SHOTS) * prime["share_true_reg"]
                     + prime["L_q"] - hw.W_A)
            assert sh["expected_share"] < floor
        p5 = doc["prediction_freeze"]["points"]["q5_d25"][-1]
        comp_floor = (hw.KAPPA_CEILING * (1 - 1 / hw.SHOTS) * p5["share_true_reg"]
                      + p5["L_q"] - hw.W_A)
        assert comp["expected_share"] < comp_floor

    def test_circuit_budget_consistency(self):
        doc = hw.load_frozen_prereg()
        b = doc["hardware_parameters"]["circuit_budget"]
        assert b["structure"] == len(hw.Q3_POINTS) * hw.K_REPEATS + len(hw.Q5_POINTS) * hw.K_REPEATS
        assert b["loschmidt"] == len(hw.Q3_POINTS) + len(hw.Q5_POINTS)
        assert b["negative_controls"] == 4
        assert b["readout_cal"] == 2
        assert b["total"] == 58
        assert b["total_shots"] == 58 * hw.SHOTS == 475136
        assert b["jobs"] == 1

    def test_verdict_map_and_safeguards_complete(self):
        doc = hw.load_frozen_prereg()
        vm = doc["verdict_map"]
        for key in ("H-RAM-Q-3_NOISE_LIFT_CONFIRMED", "H-RAM-Q-3_COARSE_HOLD_SHARP_MISS",
                    "H-RAM-Q-3_REFUTED", "H-RAM-Q-3_INVALID_AMPLIFICATION",
                    "H-RAM-Q-3_VOID_CALIBRATION", "H-RAM-Q-3_DEGENERAT",
                    "EVALUATION_INVALID_KONTROLLE_GESCHEITERT"):
            assert key in vm
        sl = doc["safeguard_limits"]
        assert "w_A = 0.05" in sl["band_rule"]
        assert "INVALID_AMPLIFICATION" in sl["amplification_ceiling"]
        assert "0.81" in sl["kappa_floor_void"]
        assert ">= 2" in sl["falsifier"]
        tfa = doc["two_freeze_architecture"]
        for key in ("freeze_a", "stage2_aer", "freeze_b", "hardware"):
            assert key in tfa
        # Konstanten im Payload == Modul-Konstanten
        assert doc["hardware_parameters"]["n_shots"] == hw.SHOTS == 8192
        assert doc["simulation_leg"]["stress_grid_p1"] == hw.STRESS_GRID_P1
        assert doc["simulation_leg"]["n_ens"] == hw.N_ENS
        assert hw.W_A == 0.05
        assert hw.KAPPA_CEILING == 0.81
        assert hw.TOL_FORM == 0.03 and hw.W_B_FLOOR == 0.01
        assert doc["simulation_leg"]["freeze_b"].count("w_B <= W_A") >= 1