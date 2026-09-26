# -*- coding: utf-8 -*-
"""EXPERIMENT 043 (H-RAM-Q-3b) Prereg-Freeze-A'-Tests — Minimalregister + Echo-Leiter.

Bindend: der Freeze muss
  (1) die 13 alten Punkte am Minimalregister d=q bit-exakt gegen 040/034 tragen,
  (2) die 13 NEUEN P nach registrierter Regel deterministisch ableiten (d-frei),
  (3) die unverändert gefrorene Garantie kappa_hat >= 0.81 registrieren,
  (4) Option B nur als nachgelagerte Fallback-Lesart dokumentieren,
  (5) VOR jedem QPU-Kontakt mit md5 gefroren sein (REGISTERED_NOT_MEASURED, 0 QPU).
"""

import json
import os

import numpy as np
import pytest

import pt_ram_q_hardware as hw
import pt_ram_q_hardware2 as hw2

EXPECTED_MD5 = "5b91119b925ae365bcd0618a2a15fa30"


def _is_prime(n):
    """Unabhängige Primzahl-Prüfung (Probeteilung, nicht der Modul-Sieb)."""
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def _smallest_prime_above_independent(x):
    y = x + 1
    while not _is_prime(y):
        y += 1
    return y


# === Freeze-Integrität ===

class TestFreezeIntegrity:
    def test_md5_roundtrip_and_tamper(self):
        doc = hw2.load_frozen_prereg()
        assert doc["md5"] == EXPECTED_MD5
        assert hw2.verify_prereg_md5(doc)
        # Manipulation wird entdeckt
        tampered = json.loads(json.dumps(doc))
        tampered["status"] = "MEASURED"
        assert not hw2.verify_prereg_md5(tampered)

    def test_status_registered_not_measured_zero_qpu(self):
        doc = hw2.load_frozen_prereg()
        assert doc["experiment"] == "043-ram-q-minimal-register-echo"
        assert doc["hypothesis"] == "H-RAM-Q-3b"
        assert doc["status"] == "REGISTERED_NOT_MEASURED"
        assert doc["registered_before"] == "2026-09-26"
        # 0 QPU im Freeze A'; Hardware erst nach Freeze B'
        assert doc["qpu"].startswith("0 QPU")
        assert "EIN Fez-Job (TOKEN1) erst nach" in doc["qpu"]
        # User-Anker wörtlich (Direktive Schritt 2)
        assert "REGISTERED_NOT_MEASURED" in doc["user_anchor"]
        assert "minimalen Repräsentanten" in doc["user_anchor"]
        assert "0.81" in doc["user_anchor"]
        assert "nachgelagerte Fallback-Lesart" in doc["user_anchor"]
        assert "Echo-Tiefen-Leiter" in doc["user_anchor"]

    def test_freeze_refuses_broken_040_anchors(self, monkeypatch):
        monkeypatch.setattr(hw, "_load_040_ratios", lambda: {109: 2.0})
        with pytest.raises(ValueError, match="Anker-Verifikation gescheitert"):
            hw2.build_prereg_payload()

    def test_freeze_refuses_broken_034_anchors(self, monkeypatch):
        monkeypatch.setattr(hw, "_load_034_ratios", lambda: {625: 2.0})
        with pytest.raises(ValueError, match="Anker-Verifikation gescheitert"):
            hw2.build_prereg_payload()

    def test_freeze_refuses_d_invariance_violation(self, monkeypatch):
        """d-Invarianz-Check (b) feuert, wenn ein Register der q^k-Familie abweicht."""
        real = hw.arm_point

        def corrupted(P, d, q):
            pt = dict(real(P, d, q))
            if P == 149 and d == 9:
                pt["ratio_true"] = pt["ratio_true"] + 1e-6
            return pt

        monkeypatch.setattr(hw, "arm_point", corrupted)
        diag3 = [real(P, hw2.D3_MIN, 3) for P in hw2.OLD_Q3_POINTS]
        diag5 = [real(P, hw2.D5_MIN, 5) for P in hw2.OLD_Q5_POINTS]
        with pytest.raises(ValueError, match="d-Invarianz q3 P=149"):
            hw2.verify_anchors_minimal(diag3, diag5)


# === Klassischer Kern: bit-exakt gegen die gefrorenen Ketten ===

class TestClassicalCore:
    def test_old_q3_arm_bit_exact_vs_040_at_d3(self):
        """Die 8 alten P tragen am MINIMALREGISTER d=3 die 040-Ratios bit-exakt."""
        r40 = hw2._load_040_ratios()
        for P in hw2.OLD_Q3_POINTS:
            pt = hw2.arm_point(P, hw2.D3_MIN, 3)
            assert abs(pt["ratio_true"] - r40[P]) <= 1e-9

    def test_old_q5_arm_bit_exact_vs_034_at_d5(self):
        """Die 5 alten P tragen am MINIMALREGISTER d=5 die 034-Ratios bit-exakt."""
        r34 = hw2._load_034_ratios()
        for P in hw2.OLD_Q5_POINTS:
            pt = hw2.arm_point(P, hw2.D5_MIN, 5)
            assert abs(pt["ratio_true"] - r34[P]) <= 1e-9

    def test_p_rule_independent_and_pinned(self):
        """Registrierte P-Regel gegen eine UNABHÄNGIGE Implementierung (Probeteilung)."""
        expected_q3 = [149, 197, 251, 347, 433, 577, 659, 761]
        expected_q5 = [433, 499, 577, 631, 659]
        assert hw2.NEW_Q3_POINTS == expected_q3
        assert hw2.NEW_Q5_POINTS == expected_q5
        for old, new in zip(hw2.OLD_Q3_POINTS, hw2.NEW_Q3_POINTS):
            assert _is_prime(new)
            assert new > old + 30
            assert new == _smallest_prime_above_independent(old + 30)
        for old, new in zip(hw2.OLD_Q5_POINTS, hw2.NEW_Q5_POINTS):
            assert _is_prime(new)
            assert new > old + 30
            assert new == _smallest_prime_above_independent(old + 30)
        # Regel auch im Payload registriert und identisch
        doc = hw2.load_frozen_prereg()
        rule = doc["prediction_freeze"]["p_rule"]
        assert rule["new_q3"] == expected_q3
        assert rule["new_q5"] == expected_q5
        assert rule["old_q3"] == list(hw.Q3_POINTS)
        assert rule["old_q5"] == list(hw.Q5_POINTS)
        # LADDER_ANCHORS = erste neue Punkte
        assert hw2.LADDER_ANCHORS == {"q3": 149, "q5": 433}

    def test_new_points_d_invariance_q_pow_k_and_dP_outside_family(self):
        """041 T3 (k=1 eingeschlossen): d=q == d=q^2 == d=q^3 (1e-12).
        d=P liegt AUSSERHALB der Familie (q | d noetig) — arm_point verweigert
        dort via closed_form-Guard, weil P im Label P mod P = 0 landet."""
        for P in hw2.NEW_Q3_POINTS:
            ref = hw2.arm_point(P, hw2.D3_MIN, 3)["ratio_true"]
            for d in (9, 27):
                assert abs(hw2.arm_point(P, d, 3)["ratio_true"] - ref) <= 1e-12
            with pytest.raises(ValueError, match="closed_form != ratio_true"):
                hw2.arm_point(P, P, 3)
        for P in hw2.NEW_Q5_POINTS:
            ref = hw2.arm_point(P, hw2.D5_MIN, 5)["ratio_true"]
            for d in (25, 125):
                assert abs(hw2.arm_point(P, d, 5)["ratio_true"] - ref) <= 1e-12
            with pytest.raises(ValueError, match="closed_form != ratio_true"):
                hw2.arm_point(P, P, 5)

    def test_universal_formula_Lq_and_strict_ratio_gt_1(self):
        doc = hw2.load_frozen_prereg()
        for arm in ("q3_d3", "q5_d5"):
            for pt in doc["prediction_freeze"]["points"][arm]:
                q, m, N, n0 = pt["q"], pt["m"], pt["N"], pt["n0"]
                num = q * sum(x * x for x in N) - m * m
                den = (m - q * n0) ** 2
                # Universalform == ratio_true == closed_form
                assert abs((q - 1) * num / den - pt["ratio_true"]) <= 1e-12
                assert abs(pt["closed_form"] - pt["ratio_true"]) <= 1e-12
                # L_q = (q-1)^2 m^2 / (S (m-qn0)^2)
                assert abs((q - 1) ** 2 * m * m / (hw2.SHOTS * den) - pt["L_q"]) <= 1e-12
                # Strukturkorollar (041): ratio > 1 streng
                assert pt["ratio_true"] > 1.0

    def test_state_amplitudes_minimal_register(self):
        """|psi> = sum sqrt(n_a/m)|a>; d=q: 3 reale Labels von 4 (2 Qubits, q3)
        bzw. 5 von 8 (3 Qubits, q5)."""
        doc = hw2.load_frozen_prereg()
        for arm, n_qubits, real in (("q3_d3", 2, 3), ("q5_d5", 3, 5)):
            n_labels = 2 ** n_qubits
            for pt in doc["prediction_freeze"]["points"][arm]:
                assert pt["d"] == pt["q"]            # Minimalrepraesenant
                n_d = pt["n_d"]
                assert len(n_d) == pt["d"]
                assert sum(n_d) == pt["m"]
                amp = [np.sqrt(n / pt["m"]) if n > 0 else 0.0
                       for n in n_d] + [0.0] * (n_labels - pt["d"])
                assert abs(sum(a * a for a in amp) - 1.0) <= 1e-12
                # idle Labels ideal leer
                assert all(n == 0 for n in n_d[real:])
        topo = doc["hardware_parameters"]["register_topology"]
        assert topo["q3_d3"]["d"] == 3 and topo["q3_d3"]["n_qubits"] == 2
        assert topo["q3_d3"]["labels"] == 4
        assert topo["q3_d3"]["real_labels"] == 3
        assert topo["q3_d3"]["idle_labels"] == 1
        assert topo["q5_d5"]["labels"] == 8
        assert topo["q5_d5"]["real_labels"] == 5
        assert topo["q5_d5"]["idle_labels"] == 3
        # idle == labels - real (Arithmetik-Konsistenz beider Arme)
        for spec in topo.values():
            assert spec["idle_labels"] == spec["labels"] - spec["real_labels"]

    def test_wraparound_fold_at_minimal_register(self):
        """Operational Definition: n_d[a] = sum n_full[a::d]; Idle-Label-Masse
        faellt via a mod d in echte Klassen (Label 3 -> Klasse 0 bei q3;
        Labels 5..7 -> Klassen 0..2 bei q5)."""
        from pt_ram_q_hardware_aer import fold_d
        assert list(fold_d([10, 20, 30, 5], 3)) == [15, 20, 30]
        assert list(fold_d([10, 20, 30, 40, 50, 1, 2, 3], 5)) == [11, 22, 33, 40, 50]
        # Masse bleibt exakt erhalten
        assert sum(fold_d([10, 20, 30, 5], 3)) == sum([10, 20, 30, 5])
        assert sum(fold_d([10, 20, 30, 40, 50, 1, 2, 3], 5)) == 156


# === Registrierte Regeln und Kontrollen ===

class TestRegisteredRules:
    def test_band_center_and_edges(self):
        doc = hw2.load_frozen_prereg()
        for arm in ("q3_d3", "q5_d5"):
            for pt in doc["prediction_freeze"]["points"][arm]:
                # Zentrum c(kappa_hat) = kappa_hat*(1-1/S)*ratio_true + L_q (gefroren)
                c = (1.0 - 1.0 / hw2.SHOTS) * pt["ratio_true"] + pt["L_q"]
                ceiling = c + hw2.W_A
                assert abs(ceiling - c - hw2.W_A) <= 1e-12
                # Amplification-Ceiling liegt oberhalb des rauschfreien Niveaus + w
                assert ceiling > c

    def test_composite_controls_exact_and_below_floor_both_arms(self):
        doc = hw2.load_frozen_prereg()
        ctrl = doc["controls"]["t4_negative_must_not_fire"]
        # exakte Erwartungen aus N_tilde reproduzierbar (034-Konvention, jetzt d=q)
        for key, arm, d, q in (("composite_q3", "q3_d3", 3, 3),
                               ("composite_q5", "q5_d5", 5, 5)):
            comp = ctrl[key]
            prime = doc["prediction_freeze"]["points"][arm][0]
            exp = (q * sum(x * x for x in comp["N_tilde"]) - comp["m"] ** 2) / (d * comp["m"])
            assert abs(exp - comp["expected_share"]) <= 1e-12
            # Must-not-fire an der konservativsten Ecke (kappa = 0.81, w = W_A):
            # untere Prime-Bandkante
            floor = (hw2.KAPPA_CEILING * (1 - 1 / hw2.SHOTS) * prime["share_true_reg"]
                     + prime["L_q"] - hw2.W_A)
            assert comp["expected_share"] < floor
            # Composite-State liegt massgeblich unter dem Prime-Level
            assert comp["expected_share"] < prime["share_true_reg"]
        assert ctrl["rule"].count("KAPPA_CEILING") == 1
        assert "H-RAM-Q-3b_DEGENERAT" in ctrl["rule"]

    def test_uniform_controls_zero_and_below_floor(self):
        doc = hw2.load_frozen_prereg()
        ctrl = doc["controls"]["t4_negative_must_not_fire"]
        pts = {("q3_d3"): doc["prediction_freeze"]["points"]["q3_d3"][0],
               ("q5_d5"): doc["prediction_freeze"]["points"]["q5_d5"][0]}
        for key, arm in (("uniform_q3", "q3_d3"), ("uniform_q5", "q5_d5")):
            unif = ctrl[key]
            assert unif["expected_share"] == 0.0
            assert unif["n_classes"] == (3 if key == "uniform_q3" else 5)
            prime = pts[arm]
            floor = (hw2.KAPPA_CEILING * (1 - 1 / hw2.SHOTS) * prime["share_true_reg"]
                     + prime["L_q"] - hw2.W_A)
            assert unif["expected_share"] < floor

    def test_shuffle_inert_theorem_delta_zero_and_inside_band(self):
        """Theorem (frozen_theorems.shuffle_inertness_at_dq): bei d=q ist der Fold
        die Identitaet => expected_share == share_true_reg EXAKT. Die Kontrolle
        laege IM Prime-Band (ueber der unteren Bandkante) und kann nicht
        must-not-fire — deshalb Composite + Uniform als Ersatz."""
        doc = hw2.load_frozen_prereg()
        t4b = doc["controls"]["t4b_shuffle_inert_theorem"]
        for key, arm in (("q3_seed421", "q3_d3"), ("q5_seed421", "q5_d5")):
            inert = t4b[key]
            prime = doc["prediction_freeze"]["points"][arm][0]
            assert inert["delta"] == 0.0                      # EXAKT, nicht < tol
            assert inert["expected_share"] == prime["share_true_reg"]
            floor = (hw2.KAPPA_CEILING * (1 - 1 / hw2.SHOTS) * prime["share_true_reg"]
                     + prime["L_q"] - hw2.W_A)
            # wuerde IM Band liegen (ueber der unteren Prime-Bandkante)
            assert inert["expected_share"] > floor
        # kein Shuffle-Circuit im Budget
        assert doc["hardware_parameters"]["circuit_budget"].get("shuffle", 0) in (0, None)
        assert "strukturell inert" in doc["frozen_theorems"]["shuffle_inertness_at_dq"]

    def test_circuit_budget_consistency(self):
        doc = hw2.load_frozen_prereg()
        b = doc["hardware_parameters"]["circuit_budget"]
        assert b["structure"] == (len(hw2.NEW_Q3_POINTS) + len(hw2.NEW_Q5_POINTS)) * hw2.K_REPEATS
        assert b["structure"] == 39
        assert b["loschmidt"] == len(hw2.NEW_Q3_POINTS) + len(hw2.NEW_Q5_POINTS) == 13
        assert b["echo_ladder"] == (len(hw2.LADDER_REPEATS) - 1) * 2 == 6
        assert b["diagnostik_structure"] == len(hw2.OLD_Q3_POINTS) + len(hw2.OLD_Q5_POINTS) == 13
        assert b["diagnostik_loschmidt"] == 13
        assert b["negative_controls"] == 4
        assert b["readout_cal"] == 2
        assert b["total"] == 90
        assert b["total_shots"] == 90 * hw2.SHOTS == 737280
        assert b["jobs"] == 1

    def test_echo_ladder_specification(self):
        doc = hw2.load_frozen_prereg()
        lad = doc["echo_ladder"]
        assert lad["repeats"] == [1, 2, 4, 8]
        assert lad["anchors"] == {"q3": 149, "q5": 433}
        # r=1 geteilt mit dem gepaarten Loschmidt-Circuit des Ankerpunkts
        assert "geteilt" in lad["r1_shared"]
        assert "kappa_ladder(r=1)" in lad["r1_shared"]
        assert "Barrier" in lad["barriers"]
        assert "NICHT verdict-tragend" in lad["erwartungsbereich_diagnostisch"]
        assert "Kalibrier-Diagnostik" in lad["verdict_role"]
        assert "Daempfungsgesetz" in lad["purpose"]
        # Modul-Konstanten identisch
        assert hw2.LADDER_REPEATS == (1, 2, 4, 8)

    def test_diagnostik_bein_rules_and_w_cross(self):
        doc = hw2.load_frozen_prereg()
        diag = doc["diagnostik_bein"]
        assert diag["reps"] == 1
        assert diag["loschmidt_gepaart"] is True
        assert diag["verdict_role"] == "NICHT verdict-tragend; Re-Freeze-Trigger-Analyse nur."
        assert "HARDWARE-D_INVARIANZ_KONSISTENT" in diag["rule"]
        assert "HARDWARE-D_INVARIANZ_VERLETZT" in diag["rule"]
        # Diagnostik-Punkte = die 13 ALTEN P (bit-exakt gegen 040/034)
        r40 = hw2._load_040_ratios()
        r34 = hw2._load_034_ratios()
        for P, pt in zip(hw2.OLD_Q3_POINTS, diag["points"]["q3_d3"]):
            assert pt["P"] == P and abs(pt["ratio_true"] - r40[P]) <= 1e-9
        for P, pt in zip(hw2.OLD_Q5_POINTS, diag["points"]["q5_d5"]):
            assert pt["P"] == P and abs(pt["ratio_true"] - r34[P]) <= 1e-9
        # w_cross-Eichung gegen committed run-1-Residuen (unabhaengig rechnerisch)
        eval_doc = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               os.pardir, hw2.RUN1_EVAL)))
        res = np.array([rec["ratio_hw"] - rec["center_v1"]
                        for rec in eval_doc["punkte"].values()])
        assert res.size == 13
        stats = diag["w_cross_derivation"]
        assert stats["n"] == 13
        assert abs(stats["max_abs"] - np.abs(res).max()) <= 1e-12
        assert abs(stats["std"] - res.std()) <= 1e-12
        assert abs(stats["two_sqrt2_std"] - 2.0 * np.sqrt(2.0) * res.std()) <= 1e-12
        assert stats["two_sqrt2_std"] == pytest.approx(0.0825, abs=5e-5)
        assert hw2.W_CROSS == 0.09
        assert hw2.W_CROSS >= stats["two_sqrt2_std"]
        assert str(hw2.W_CROSS) in stats["w_cross_rule"]
        # Leckage dokumentiert: Verdict nutzt ausschliesslich die NEUEN P
        assert "ausschliesslich" in diag["leckage_dokumentiert"]
        assert "13 NEUEN P" in diag["leckage_dokumentiert"]

    def test_verdict_map_safeguards_and_fallback(self):
        doc = hw2.load_frozen_prereg()
        vm = doc["verdict_map"]
        for key in ("H-RAM-Q-3b_NOISE_LIFT_CONFIRMED", "H-RAM-Q-3b_COARSE_HOLD_SHARP_MISS",
                    "H-RAM-Q-3b_REFUTED", "H-RAM-Q-3b_INVALID_AMPLIFICATION",
                    "H-RAM-Q-3b_VOID_CALIBRATION", "H-RAM-Q-3b_DEGENERAT",
                    "EVALUATION_INVALID_KONTROLLE_GESCHEITERT"):
            assert key in vm
        sl = doc["safeguard_limits"]
        assert "w_A = 0.05" in sl["band_rule"]
        assert "VERENGEN (w_B <= w_A)" in sl["band_rule"]
        assert "INVALID_AMPLIFICATION" in sl["amplification_ceiling"]
        assert "0.81" in sl["kappa_floor_void"]
        assert "UNVERAENDERT" in sl["kappa_floor_void"]
        assert "nicht metrisch aufgeweicht" in sl["kappa_floor_void"]
        assert ">= 2" in sl["falsifier"]
        assert "EIN Fez-Job (TOKEN1)" in sl["job_integrity"]
        assert "90 Circuits" in sl["job_integrity"]
        tfa = doc["two_freeze_architecture"]
        for key in ("freeze_a", "stage2_aer", "freeze_b", "hardware"):
            assert key in tfa
        fb = doc["fallback_lesart_b"]
        assert "NUR-NACHGELAGERT, NIE stiller Patch" in fb["status"]
        assert "kappa_hat" in fb["trigger"] and ">= 2 Punkten" in fb["trigger"]
        assert "Separat gefrorenes NEUES Prereg" in fb["mechanism"]
        assert "UNVERÄNDERT" in fb["primär_pfad"]

    def test_constants_unchanged_from_phase9_and_isa_ceilings(self):
        """Die gefrorenen Konstanten sind UNVERAENDERT aus Freeze A/042 (md5 432d43fe)."""
        assert hw2.SHOTS == hw.SHOTS == 8192
        assert hw2.K_REPEATS == hw.K_REPEATS == 3
        assert hw2.W_A == hw.W_A == 0.05
        assert hw2.KAPPA_CEILING == hw.KAPPA_CEILING == 0.81
        assert hw2.TOL_FORM == hw.TOL_FORM == 0.03
        assert hw2.W_B_FLOOR == hw.W_B_FLOOR == 0.01
        assert hw2.ISA_2Q_PER_CIRCUIT_MAX == hw.ISA_2Q_PER_CIRCUIT_MAX == 120
        assert hw2.ISA_2Q_TOTAL_MAX == hw.ISA_2Q_TOTAL_MAX == 6000
        assert hw2.STRESS_GRID_P1 == hw.STRESS_GRID_P1
        assert hw2.N_ENS == hw.N_ENS
        doc = hw2.load_frozen_prereg()
        ic = doc["hardware_parameters"]["isa_ceilings"]
        assert ic["per_circuit_2q_max"] == 120
        assert ic["total_2q_max"] == 6000
        assert "Re-Freeze" in ic["abort"]
        assert hw2.RUN1_COUNTS_MD5 == hw2.RUN1_COUNTS_MD5_KEY == "d19f4a563d88e0cf3ffd4b187a10ca73"
        assert hw2.RUN1_JOB == "darq1stvr3kc73ej96ig"

    def test_prior_chain_and_phase9_context(self):
        doc = hw2.load_frozen_prereg()
        pc = doc["prior_chain"]
        assert "432d43fe1bc9e2594efd3b35266d2d81" in pc
        assert "d19f4a563d88e0cf3ffd4b187a10ca73" in pc
        assert len(pc) == 6
        ctx = doc["phase9_verdict_context"]
        assert ctx["verdict"] == "H-RAM-Q-3_VOID_CALIBRATION"
        assert "30 2q" in ctx["echo_tiefen"] and "76 2q" in ctx["echo_tiefen"]
        assert "0.6608" in ctx["befund"] and "0.8080" in ctx["befund"]
        assert "§10.25" in ctx["korrektur"]

    def test_anchor_report_and_misc_pins(self):
        doc = hw2.load_frozen_prereg()
        av = doc["prediction_freeze"]["anchor_verification"]
        assert av["old_P_at_dq_vs_040"] == "8/8 bit-exakt (tol 1e-9)"
        assert av["old_P_at_dq_vs_034"] == "5/5 bit-exakt (tol 1e-9)"
        assert av["new_P_d_invariance"] == "13/13 identisch (d=q, d=q^2, d=q^3; tol 1e-12)"
        ls = doc["layer_separation"]
        assert "1025/348/879/5683" in ls["encoding_verbot"]
        assert doc["suite_state"] == 831
        assert doc["future_phase_numbering"]["synthesis"] == "§Z.25 (SYNTHESIS)"
        assert "§10.26 (RIEMANN)" in doc["future_phase_numbering"]["log"]
        assert "§Z.23/§10.24 Gematria-Layer" in doc["future_phase_numbering"]["log"]
        assert doc["hardware_parameters"]["backend"] == "ibm_fez"
        assert "TOKEN2 unberuehrt" in doc["hardware_parameters"]["token"]

    def test_design_decision_and_theorems(self):
        doc = hw2.load_frozen_prereg()
        dd = doc["design_decision"]
        assert "INSTRUMENT, nicht die Hypothese" in dd["option_a_gewaehlt"]
        assert "nicht metrisch aufgeweicht" in dd["garantie_unveraendert"]
        assert "Fallback-Lesart" in dd["why_not_option_b_primaer"]
        ft = doc["frozen_theorems"]
        assert "shuffle_inertness_at_dq" in ft
        assert "d_invariance" in ft and "B2_q_universal_identity" in ft
        # noise law unverändert
        nl = doc["prediction_freeze"]["noise_law"]
        assert "UNVERAENDERT" in nl["ratio_hw"]
        assert "(q-1)^2*m^2/(S*(m-q*n0)^2)" in nl["L_q"]
        # anti-sharpshooter
        asc = doc["anti_sharpshooter"]
        assert "kleinste Primzahl > P_alt + 30" in asc["no_ex_post_fit"]
        assert "Echo-Leiter MISST das Gesetz" in asc["registered_alternative_models"]
        # Kontrolle T3/T5/T6 Texte
        ctrl = doc["controls"]
        assert "1e-12" in ctrl["t3_identity_two_ways"]
        assert "keine nachträglichen Ergänzungen" in ctrl["t5_gate_set_frozen"]
        assert "EVALUATION_INVALID" in ctrl["t6_mass_conservation"]