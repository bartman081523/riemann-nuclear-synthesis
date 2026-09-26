# -*- coding: utf-8 -*-
"""Stage-2 Aer-Bein (EXPERIMENT 042, H-RAM-Q-3) — Tests pinnen die gefrorene Semantik.

Freeze-A-Prereg (md5 432d43fe1bc9e2594efd3b35266d2d81): simulation_leg
stress_model / form_validation / freeze_b.  Die Tests hier sind HERMETISCH
(kein Netzwerk, kein QPU): sie pinnen die Estimator-Kette, die gesetzliche
v2-Form (per-Punkt-Anker + per-Punkt-Steigung), die KORRIGIERTE Inversion,
die ABSOLUT-FFT-Share-Konvention (t3 Zwei-Wege-Identitaet) und den
58-Circuit-Builder (struktur 39 + loschmidt 13 + kontrollen 4 + kalibrierung 2).
"""
import json
import os

import numpy as np
import pytest

import pt_ram_q_hardware as hw
import pt_ram_q_hardware_aer as aer

RESULTS_PATH = aer.RESULTS_PATH

DOC = hw.load_frozen_prereg()
PTS = {}
for arm in ("q3_d9", "q5_d25"):
    for p in DOC["prediction_freeze"]["points"][arm]:
        PTS[(arm, p["P"])] = p

# Aus der Exakt-Diagnose (scratch_stage2_exact.py, Commits-Vorlauf, 0 QPU):
# kappa=1-Intercepts der Domain-Linien == ratio_ro-Anker (zwei unabhaengige
# Herleitungen: LSQ-Intercept der exakten Stresskurve UND direkte T_ro-
# Arithmetik auf den gefrorenen n_d) — muessen uebereinstimmen.
ANCHOR_PIN = {
    ("q3_d9", 109): 0.867205,
    ("q3_d9", 307): 0.870167,
    ("q5_d25", 625): 0.893225,
    ("q5_d25", 401): 0.923583,
}
# Kreuzcheck (Exakt-Diagnose, LSQ-Intercepts der Domain-Linien):
# 0.867231 / 0.870202 / 0.893516 / 0.923868 — Abstand <= 2.9e-4 (Fit-Rest).


class TestStressModel:
    def test_readout_only_at_p1_zero(self):
        nm = aer.stress_noise_model(0.0)
        types = [e["type"] for e in nm.to_dict()["errors"]]
        assert types == ["roerror"]  # kein Quantenfehler, nur Readout

    def test_cz_adaption_ratio_10(self):
        # Gefrorene Adaption (ibm_fez nativ cz statt cx): 2q-Fehler = ratio*p1.
        prob = aer.two_qubit_depolarizing_param(1e-4)
        assert prob == pytest.approx(1e-3, rel=1e-12)

    def test_two_qubit_cap_at_one(self):
        assert aer.two_qubit_depolarizing_param(0.2) == 1.0

    def test_quantum_error_on_cz_at_p1_positive(self):
        nm = aer.stress_noise_model(1e-4)
        d = nm.to_dict()["errors"]
        qerr = [e for e in d if e["type"] == "qerror"]
        assert any("cz" in e.get("operations", []) for e in qerr)

    def test_ro_default_is_1e2(self):
        nm = aer.stress_noise_model(0.0)
        ro_entry = [e for e in nm.to_dict()["errors"]
                    if e["type"] == "roerror"][0]
        assert ro_entry["probabilities"][0][1] == pytest.approx(0.01)

    def test_readout_behavioral_cal(self):
        # Verhaltens-Check: Kalibrier-Circuit |0^n> liefert P(0) = (1-ro)^nq.
        from qiskit_aer import AerSimulator
        nm = aer.stress_noise_model(0.0, ro=0.01)
        qc = aer.build_cal_circuit(4)
        sim = AerSimulator(method="density_matrix", noise_model=nm,
                           seed_simulator=1)
        p0 = aer.p0_fraction(sim.run(qc, shots=20000).result().get_counts(), 4)
        assert p0 == pytest.approx(0.99 ** 4, abs=0.01)


class TestAbsolutFFTShare:
    def test_hand_computed_dft(self):
        # n = [1,0,2,0], d=4, q=2, m=3: G[2] = n0 - n1 + n2 - n3 = 3,
        # js = [int(1*4/2)] = [2]  =>  share = |G[2]|^2/(d*m) = 9/12 = 0.75.
        assert aer.share_hw_fft([1, 0, 2, 0], q=2, d=4, m=3) == pytest.approx(
            0.75, abs=1e-12)

    def test_two_way_identity_t3(self):
        # Gefrorene Kontrolle t3: ABSOLUT-FFT bei j*d/q vs gefaltete Formel
        # (q*sum N_hat^2 - m_hat^2)/(d*m) — exakt 1e-12 (041-Theorem).
        rng = np.random.default_rng(421)
        for _ in range(20):
            d, q = 25, 5
            n_full = rng.integers(0, 5, size=d).astype(float)
            n_d = n_full  # Wraparound-frei halten: n_full ist bereits d-lang
            N = hw.fold_mod_q(n_d, d, q)
            m = float(n_d.sum())
            s_fft = aer.share_hw_fft(n_d, q, d, m)
            s_fold = aer.share_hw_folded(N, q, d, m)
            assert abs(s_fft - s_fold) <= 1e-12

    def test_parseval_sanity(self):
        # Summe ueber ALLE Fourier-Koeffizienten = d * sum(n^2).
        n = np.array([2.0, 1.0, 0.0, 3.0, 1.0, 1.0, 0.0, 0.0])
        G = np.fft.fft(n)
        assert np.isclose(np.sum(np.abs(G) ** 2), len(n) * np.sum(n ** 2))

    def test_convention_differs_from_class_mass(self):
        # DOKUMENTIERTER Konventionsbefund (Phase 8): share_star_q (pt_ram_q_
        # zyklizitaet) ist KLASSEN-MASSEN (sum prof an Klassenpositionen),
        # NICHT die gefrorene ABSOLUT-FFT-Konvention der Hardware-Leg.
        n = [1.0, 0.0, 2.0, 0.0]
        s_fft = aer.share_hw_fft(n, q=2, d=4, m=3)
        s_class = 2.0 / 3.0  # Klassenmasse bei Position 2, normiert auf m
        assert s_fft != pytest.approx(s_class, abs=1e-9)


class TestRatioRoAnchor:
    @pytest.mark.parametrize("arm,P", [("q3_d9", 109), ("q3_d9", 307),
                                       ("q5_d25", 625), ("q5_d25", 401)])
    def test_anchor_at_ro_zero_is_ratio_true(self, arm, P):
        pt = PTS[(arm, P)]
        nq = 4 if arm == "q3_d9" else 5
        assert aer.ratio_ro_exact(pt, ro=0.0, nq=nq) == pytest.approx(
            pt["ratio_true"], abs=1e-12)

    @pytest.mark.parametrize("arm,P", [("q3_d9", 109), ("q3_d9", 307),
                                       ("q5_d25", 625), ("q5_d25", 401)])
    def test_anchor_pinned_values(self, arm, P):
        pt = PTS[(arm, P)]
        nq = 4 if arm == "q3_d9" else 5
        assert aer.ratio_ro_exact(pt, ro=0.01, nq=nq) == pytest.approx(
            ANCHOR_PIN[(arm, P)], abs=1e-6)

    def test_monotone_decreasing_in_ro(self):
        pt = PTS[("q3_d9", 109)]
        vals = [aer.ratio_ro_exact(pt, ro=r, nq=4)
                for r in (0.0, 0.005, 0.01, 0.02)]
        assert all(a > b for a, b in zip(vals, vals[1:]))

    def test_anchor_independent_recompute(self):
        # Unabhaengige Implementierung: volle T_ro-Matrix via Kronecker-
        # Produkt statt Tensor-Kontraktion — muss auf 1e-9 uebereinstimmen.
        pt = PTS[("q5_d25", 625)]
        nq, ro = 5, 0.01
        T1 = np.array([[1 - ro, ro], [ro, 1 - ro]])
        T_full = np.array([[1.0]])
        for _ in range(nq):
            T_full = np.kron(T_full, T1)
        n_labels = 2 ** nq
        n_full = np.zeros(n_labels)
        n_full[:pt["d"]] = pt["n_d"]
        p_ro = T_full @ n_full
        n_d_ro = np.array([sum(p_ro[a::pt["d"]]) for a in range(pt["d"])])
        m = pt["m"]
        s = aer.share_hw_fft(n_d_ro, pt["q"], pt["d"], m)
        indep = s / pt["model_share_reg"]
        assert aer.ratio_ro_exact(pt, ro, nq) == pytest.approx(indep, abs=1e-9)


class TestCenterLaws:
    def test_center_v1_anchor_value(self):
        pt = PTS[("q3_d9", 109)]
        S = hw.SHOTS
        assert aer.center_v1(1.0, pt) == pytest.approx(
            (1.0 - 1.0 / S) * pt["ratio_true"] + pt["L_q"], abs=1e-12)

    def test_center_v2_anchor_value(self):
        pt = PTS[("q3_d9", 109)]
        S = hw.SHOTS
        b = 0.898257  # per-Punkt-Steigung aus der Exakt-Diagnose
        c = aer.center_v2(1.0, pt, ro_hat=0.01, b_p=b)
        assert c == pytest.approx(
            (1.0 - 1.0 / S) * ANCHOR_PIN[("q3_d9", 109)] + pt["L_q"], abs=1e-4)

    def test_center_v2_slope(self):
        pt = PTS[("q3_d9", 109)]
        S = hw.SHOTS
        b = 0.898257
        d1 = aer.center_v2(0.95, pt, 0.01, b) - aer.center_v2(0.93, pt, 0.01, b)
        assert d1 == pytest.approx((1.0 - 1.0 / S) * b * 0.02, abs=1e-12)

    def test_center_v2_ro_hat_shifts_anchor(self):
        # ro_hat > ro_stress verschiebt den Anker (ratio_ro ist ro-abhaengig):
        pt = PTS[("q5_d25", 625)]
        c1 = aer.center_v2(1.0, pt, 0.01, 0.672516)
        c2 = aer.center_v2(1.0, pt, 0.02, 0.672516)
        assert c2 < c1


class TestInversion:
    def test_correct_inversion(self):
        # KORRIGIERTE Inversion (dokumentiert): W = (kappa-u)/(1-u) = alpha^2
        # => alpha = sqrt((kappa-u)/(1-u)).  W=0.64, u=0.03 =>
        # kappa = 0.03 + 0.97*0.64 = 0.6508, alpha = 0.8.
        kappa = 0.03 + 0.97 * 0.64
        assert aer.alpha_from_kappa(kappa, u=0.03) == pytest.approx(
            0.8, abs=1e-12)

    def test_old_buggy_formula_differs(self):
        # Die verworfene Formel sqrt(1+(1-kappa)/(1-u))-1 (Spot-Check-Z.87)
        # liefert an derselben Stelle 0.1591 — der Test pinnt den Fix.
        kappa, u = 0.03 + 0.97 * 0.64, 0.03
        buggy = np.sqrt(1.0 + (1.0 - kappa) / (1.0 - u)) - 1.0
        assert buggy != pytest.approx(0.8, abs=1e-3)
        assert aer.alpha_from_kappa(kappa, u) != pytest.approx(buggy, abs=1e-9)

    def test_clamped_at_zero(self):
        assert aer.alpha_from_kappa(0.0, u=0.03) == 0.0


class TestCircuitBuilders:
    def test_struct_statevector_matches_frozen_profile(self):
        from qiskit.quantum_info import Statevector
        pt = PTS[("q3_d9", 109)]
        qc = aer.build_struct_circuit(pt, nq=4, measure=False)
        sv = np.asarray(Statevector.from_instruction(qc).data).real ** 2
        assert sv[:pt["d"]] == pytest.approx(
            np.array(pt["n_d"]) / pt["m"], abs=1e-9)
        assert sv[pt["d"]:] == pytest.approx(0.0, abs=1e-9)

    def test_loschmidt_returns_to_zero(self):
        # Kern-Eigenschaft: Prep + exakte Inverse = Identitaet auf |0^n>
        # (der Barrier verhindert das Kompilier-Wegkuerzen im Transpiler).
        from qiskit.quantum_info import Statevector
        pt = PTS[("q5_d25", 625)]
        qc = aer.build_loschmidt_circuit(pt, nq=5)
        sv = np.asarray(Statevector.from_instruction(qc).data)
        assert abs(sv[0]) == pytest.approx(1.0, abs=1e-9)
        assert np.abs(sv[1:]).max() <= 1e-9

    def test_cal_circuit_shape(self):
        qc = aer.build_cal_circuit(5)
        assert qc.num_qubits == 5
        assert qc.num_clbits == 5

    def test_struct_has_measurement(self):
        qc = aer.build_struct_circuit(PTS[("q3_d9", 109)], nq=4, measure=True)
        assert qc.num_clbits == 4


class TestHardwareCircuitSet:
    def test_58_circuits(self):
        cs = aer.build_hardware_circuit_set()
        assert len(cs) == 58

    def test_budget_split(self):
        cs = aer.build_hardware_circuit_set()
        kinds = {}
        for c in cs:
            kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
        assert kinds == {"structure": 39, "loschmidt": 13,
                         "negative_control": 4, "readout_cal": 2}

    def test_four_negative_controls_with_frozen_expectations(self):
        cs = aer.build_hardware_circuit_set()
        ctrls = [c for c in cs if c["kind"] == "negative_control"]
        expect = {c["name"]: c["expected_share"] for c in ctrls}
        # Gefrorene t4-Erwartungen (Freeze A, md5 432d43fe):
        assert expect["ctrl_shuffle_421_P109_d9"] == pytest.approx(
            0.09961685823754789, abs=1e-12)
        assert expect["ctrl_shuffle_422_P109_d9"] == pytest.approx(
            0.6973180076628352, abs=1e-12)
        assert expect["ctrl_composite_P625_d25"] == pytest.approx(
            0.08912280701754385, abs=1e-12)
        # 4. Negativ-Kontrolle (Freeze-B-Registrierung): shuffle@625 seed 421.
        assert expect["ctrl_shuffle_421_P625_d25"] == pytest.approx(
            0.18385964912280703, abs=1e-12)
        # Must-not-fire: alle vier unter der unteren Prime-Bandkante.
        for c in ctrls:
            assert c["expected_share"] < c["lower_prime_band_edge"]

    def test_names_unique(self):
        cs = aer.build_hardware_circuit_set()
        names = [c["name"] for c in cs]
        assert len(names) == len(set(names))

    def test_all_have_8192_shots_metadata(self):
        cs = aer.build_hardware_circuit_set()
        assert all(c["shots"] == hw.SHOTS for c in cs)


class TestSeeds:
    def test_deterministic(self):
        assert aer.stage2_seed("q3_d9", 109, 1e-3, 0) == \
            aer.stage2_seed("q3_d9", 109, 1e-3, 0)

    def test_distinct_inputs_distinct_seeds(self):
        seeds = {aer.stage2_seed("q3_d9", 109, p, e)
                 for p in (0.0, 1e-4, 3e-4) for e in range(8)}
        assert len(seeds) == 24


class TestSampledLegSmoke:
    def test_smoke_kappa_and_ratio_plausible(self):
        pt = PTS[("q3_d9", 109)]
        out = aer.sampled_point_level(pt, nq=4, p1=1e-3, n_ens=2, reps=1)
        assert 0.3 <= out["kappa_mean"] <= 1.05
        assert 0.3 <= out["ratio_mean"] <= 1.2
        assert len(out["kappa_ens"]) == 2
        assert len(out["ratio_ens"]) == 2

    def test_deterministic_rerun(self):
        pt = PTS[("q3_d9", 109)]
        a = aer.sampled_point_level(pt, nq=4, p1=1e-3, n_ens=2, reps=1)
        b = aer.sampled_point_level(pt, nq=4, p1=1e-3, n_ens=2, reps=1)
        assert a["ratio_ens"] == b["ratio_ens"]
        assert a["kappa_ens"] == b["kappa_ens"]


class TestFormValidation:
    def _synth(self, v2_res, v1_res):
        return {"cells": [
            {"arm": "q3_d9", "P": 109, "p1": lv, "ratio": r, "kappa": 0.95,
             "res_v2": rv, "res_v1": rv1}
            for lv, r, rv, rv1 in zip((0.0, 1e-4, 3e-4), (1.0, 0.98, 0.95),
                                      v2_res, v1_res)]}

    def test_pass_and_fail(self):
        ok = aer.validate_form(self._synth([0.01, -0.01, 0.02],
                                           [0.0, -0.04, 0.01]))
        assert ok["v2_pass"] is True
        bad = aer.validate_form(self._synth([0.01, 0.05, -0.02],
                                            [0.0, 0.0, 0.0]))
        assert bad["v2_pass"] is False
        assert bad["v2_violations"][0]["p1"] == 1e-4

    def test_w_b_q97_5(self):
        # 2 Ausreisser unter 40 Werten (5%) => q97.5 trifft das obere Quantil.
        cells = [{"leg": "sampled", "domain": True, "res_v2": r}
                 for r in [0.01] * 38 + [0.05] * 2]
        w = aer.compute_w_b({"cells": cells})
        assert aer.W_B_FLOOR <= w <= aer.W_A
        assert w == pytest.approx(0.05, abs=1e-9)

    def test_w_b_sub_domain_and_exact_excluded(self):
        # REGRESSION (Stage-2-Run 2): w_B las ueber ALLE Ensemble-Residuen —
        # der Sub-Domain-Schwanz (Residuen bis ~0.25, strukturimmanent, das
        # Gesetz ist domain-restriktiv) drueckte q97.5 auf 0.230 -> w_B
        # saettigte an W_A=0.05.  Gefroren ist KAPPA_CEILING=0.81 (Freeze A,
        # 0 QPU, vor jedem Stress-Kontakt): w_B wird NUR ueber Domain-Zellen
        # kalibriert; Sub-Domain- und Exact-Beine sind Diagnostik.
        cells = [{"leg": "sampled", "domain": True, "res_v2": 0.01}
                 for _ in range(40)]
        cells += [{"leg": "sampled", "domain": False, "res_v2": 0.25}
                  for _ in range(100)]
        cells += [{"leg": "exact", "domain": True, "res_v2": 0.25}]
        res = {"cells": cells}
        w = aer.compute_w_b(res)
        assert w == pytest.approx(0.01, abs=1e-12)  # Floor, NICHT 0.25
        # Gate-Beleg: roher q97.5 (0.01) <= W_A
        assert res["w_b_gate_ok"] is True
        assert res["w_b_raw_q975"] == pytest.approx(0.01, abs=1e-12)


class TestRunStage2Serializable:
    def test_json_dump_contract(self, monkeypatch, tmp_path):
        # REGRESSION (Stage-2-Run 1): 'intercepts' trug Tupel-Keys ->
        # json.dump crashte NACH der vollen Rechenzeit (Run verwarf).
        # Pinnt: alle Top-Level-Dicts sind String-keyed ("arm|P") und das
        # Dokument ist vollstaendig json-serialisierbar.
        def fake_exact(pt, nq, p1):
            return {"p1": p1, "pl_bare": 0.99, "kappa": 0.99, "u": 0.06,
                    "alpha": 0.97, "share": 0.5, "ratio": 0.9,
                    "res_v1": 0.01, "ops_struct": {"rz": 3}}

        def fake_sampled(pt, nq, p1, n_ens=2, reps=2, level_tag=None):
            return {"kappa_ens": [0.99] * n_ens, "ratio_ens": [0.9] * n_ens,
                    "ro_hat_ens": [0.01] * n_ens, "kappa_mean": 0.99,
                    "ratio_mean": 0.9}

        monkeypatch.setattr(aer, "exact_point_level", fake_exact)
        monkeypatch.setattr(aer, "sampled_point_level", fake_sampled)
        path = tmp_path / "s2.json"
        r = aer.run_stage2(n_ens=1, reps=1, results_path=str(path))
        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert loaded["status"] == "STAGE2_AER_COMPLETED"
        for top in ("b_p", "b_p_fit", "ratio_ro", "intercepts"):
            assert all("|" in k for k in loaded[top]), top
        assert loaded["form_validation"] is not None
        assert loaded["w_b"] is not None
        assert len(loaded["cells"]) == 13 * 6 * 2  # sampled + exact je Zelle
        assert len(loaded["residuals_v2"]) == 13 * 6


@pytest.mark.skipif(not os.path.exists(RESULTS_PATH),
                    reason="Stage-2-Full-Grid-Results noch nicht committed")
class TestCommittedResults:
    @pytest.fixture(scope="class")
    def results(self):
        with open(RESULTS_PATH) as fh:
            return json.load(fh)

    def test_v2_form_passes_domain(self, results):
        assert results["form_validation"]["v2_pass"] is True

    def test_v1_documented_fail(self, results):
        assert results["form_validation"]["v1_fail_cells"] >= 2

    def test_w_b_within_band(self, results):
        assert aer.W_B_FLOOR <= results["w_b"] <= aer.W_A

    def test_b_p_within_registered_arm_ranges(self, results):
        # JSON-Keys sind Strings "arm|P" (Serialize-Regression des Runs 1).
        for k, b in results["b_p"].items():
            arm = k.split("|")[0]
            if arm == "q3_d9":
                assert 0.80 <= b <= 0.95
            else:
                assert 0.60 <= b <= 0.78

    def test_ratio_ro_anchors_committed(self, results):
        # ANCHOR_PIN bei 1e-4 — die gefrorenen T_ro-Anker der Exakt-Diagnose
        # pinnen 4 der 13 Punkte (109/307 q3, 625/401 q5); die uebrigen
        # 9 Punkte liegen ausserhalb des Exakt-Diagnose-Pins.
        for k, v in results["ratio_ro"].items():
            arm, P = k.split("|")
            if (arm, int(P)) in ANCHOR_PIN:
                assert v == pytest.approx(ANCHOR_PIN[(arm, int(P))], abs=1e-4)

    def test_w_b_gate_unclipped(self, results):
        # Freeze-B-Gate gegen den UNGECLIPPTEN Wert (Prereg-Text: "w_B <=
        # W_A = 0.05, sonst Re-Freeze"); Domain-Lesart: w_B == clip(raw),
        # raw > Floor -> bit-identisch.
        assert results["w_b_gate_ok"] is True
        assert results["w_b_raw_q975"] <= aer.W_A
        assert results["w_b"] == pytest.approx(
            results["w_b_raw_q975"], abs=1e-12)