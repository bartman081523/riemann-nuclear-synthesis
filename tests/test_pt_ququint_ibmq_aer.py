"""
Tests for pt_ququint_ibmq_aer.py — EXPERIMENT 031, Phase 2 (Aer + Transpilation).

Ququint auf IBMQ, Phase 2: die Phase-1-encodierten Zustände/Messungen werden
zu qiskit-Circuits übersetzt; AerSimulator (density_matrix) liefert Noise-
Stress (Readout + Depolarizing), Transpilation liefert Gate-Counts.
KEINE QPU-Kosten, KEIN echter Backend-Zugriff.

Abgedeckt:
  - exakte 6-Qubit-Präparations-Circuits: |phi> (statevector-verifiziert
    gegen phi_max_encoded aus Phase 1) und die 5 Basiszustands-Circuits,
    deren Gleichgewichts-Mischung EXAKT rho_sep ist (nur X-Gates — die
    Präparations-Asymmetrie ist das ehrliche Verschränkungs-Kosten-Signal)
  - DFT-Messrotation U = F (x) F† via UnitaryGate, verifiziert gegen das
    Phase-1-Histogramm histogram_dft(|phi>)
  - QPU-Job-Layout (12 Circuits: phi_C, phi_D, sep_C x5, sep_D x5) — genau
    die Batch-Struktur, die Phase 3 als EINEN Job einreicht
  - transpilierte Gate-Counts auf der Phase-2-Basis (rz/sx/x/cx): nur
    strukturelle Pins (Transpiler-Output ist versionsabhängig und wird nie
    exakt gepinnt); sep_C braucht 0 Zwei-Qubit-Gates nach Transpilation
  - Error-Budget-Arithmetik (Eingabe für die Phase-3-Prereg-Predictions)
  - Witness-Kurve unter dem STRESS-Noise-Modell: V(|phi>) über der 1/5-
    Schranke ohne 1q-Fehler, monoton degradierend; V(rho_sep) nie fälschlich
    über der Schranke (kein False Positive); depolarisiertes Limit V = 5/64
  - das §Z.11-Konfund (identische Computational-Populationen) in jeder Run
    auf Aer-Level geprüft
  - Phase-2-Guard: Aer only — kein qiskit_ibm-Import, kein echter
    Backend-Zugriff
"""
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TWO_DIM = 64
BASIS = {"rz", "sx", "x", "cx"}
DIAG = [k * 8 + k for k in range(5)]


def counts_to_probs(counts):
    total = int(sum(counts.values()))
    p = np.zeros(TWO_DIM)
    for key, c in counts.items():
        p[int(key, 2)] = c / total
    return p


def count_two_qubit_ops(circ):
    return int(sum(1 for inst in circ.data if inst.operation.num_qubits == 2))


def count_unitary_ops(circ):
    return int(sum(1 for inst in circ.data if inst.operation.name == "unitary"))


# === EXAKTE PRÄPARATION (statevector-verifiziert gegen Phase 1) ===


class TestExactPreparation:
    def test_phi_prep_circuit_matches_phi_statevector(self):
        import pt_ququint_ibmq as qi
        import pt_ququint_ibmq_aer as qa
        from qiskit.quantum_info import Statevector
        sv = np.asarray(Statevector.from_instruction(qa.phi_prep_circuit()).data)
        assert np.allclose(sv, qi.phi_max_encoded(), atol=1e-10)

    def test_sep_circuits_are_basis_states_kk(self):
        import pt_ququint_ibmq_aer as qa
        from qiskit.quantum_info import Statevector
        seps = qa.sep_prep_circuits()
        assert len(seps) == 5
        for k in range(5):
            sv = np.asarray(Statevector.from_instruction(seps[k]).data)
            assert np.linalg.norm(sv) == pytest.approx(1.0)
            assert sv[k * 8 + k] == pytest.approx(1.0, abs=1e-12)
            off = [i for i in range(TWO_DIM) if i != k * 8 + k]
            assert np.allclose(sv[off], 0.0, atol=1e-12)

    def test_sep_mixture_histogram_equals_separable(self):
        # equal-weight average of the 5 basis-state histograms IS rho_sep
        import pt_ququint_ibmq as qi
        import pt_ququint_ibmq_aer as qa
        from qiskit.quantum_info import Statevector
        avg = np.zeros(TWO_DIM)
        for circ in qa.sep_prep_circuits():
            sv = np.asarray(Statevector.from_instruction(circ).data)
            avg += np.real(sv * sv.conj())
        avg /= 5.0
        expected = np.real(np.diag(qi.separable_dephased_encoded()))
        assert np.allclose(avg, expected, atol=1e-15)

    def test_sep_prep_has_no_two_qubit_gates(self):
        # the confound control needs NO entangling gates — the honest
        # preparation asymmetry against the |phi> preparation
        import pt_ququint_ibmq_aer as qa
        for circ in qa.sep_prep_circuits():
            assert count_two_qubit_ops(circ) == 0

    def test_dft_rotation_maps_phi_to_phase1_histogram(self):
        # prep + F (x) F† must reproduce the Phase-1 DFT histogram exactly —
        # this test catches any qubit-ordering / kron-ordering error
        import pt_ququint_ibmq as qi
        import pt_ququint_ibmq_aer as qa
        from qiskit.quantum_info import Statevector
        full = qa.phi_prep_circuit().compose(qa.dft_rotation_circuit())
        sv = np.asarray(Statevector.from_instruction(full).data)
        p = np.real(sv * sv.conj())
        assert np.allclose(p, qi.histogram_dft(qi.phi_max_encoded()), atol=1e-9)


# === QPU-JOB-LAYOUT (12 Circuits = Phase-3-Batch) ===


class TestJobLayout:
    def test_layout_has_twelve_circuits_in_phase3_structure(self):
        import pt_ququint_ibmq_aer as qa
        layout = qa.witness_job_layout()
        assert set(layout) == {"phi_C", "phi_D", "sep_C", "sep_D"}
        assert len(layout["sep_C"]) == 5
        assert len(layout["sep_D"]) == 5
        total = 2 + len(layout["sep_C"]) + len(layout["sep_D"])
        assert total == 12

    def test_all_layout_circuits_measure_six_qubits(self):
        import pt_ququint_ibmq_aer as qa
        layout = qa.witness_job_layout()
        for circ in [layout["phi_C"], layout["phi_D"]] + layout["sep_C"] + layout["sep_D"]:
            assert circ.num_qubits == 6
            assert circ.num_clbits == 6
            assert circ.count_ops().get("measure", 0) == 6

    def test_dft_gates_only_in_d_settings(self):
        import pt_ququint_ibmq_aer as qa
        layout = qa.witness_job_layout()
        assert count_unitary_ops(layout["phi_C"]) == 0
        assert count_unitary_ops(layout["phi_D"]) == 2  # F on A, F† on B
        for circ in layout["sep_C"]:
            assert count_unitary_ops(circ) == 0
        for circ in layout["sep_D"]:
            assert count_unitary_ops(circ) == 2


# === TRANSPIlATION UND GATE-COUNTS (nur strukturelle Pins) ===


class TestTranspilation:
    def test_sep_c_transpiles_with_zero_two_qubit_gates(self):
        import pt_ququint_ibmq_aer as qa
        for circ in qa.sep_prep_circuits():
            tc = qa.transpiled_counts(circ)
            assert tc["cx"] == 0
            assert set(tc["counts"]) <= BASIS

    def test_phi_prep_needs_entangling_gates(self):
        import pt_ququint_ibmq_aer as qa
        tc = qa.transpiled_counts(qa.phi_prep_circuit())
        assert tc["cx"] >= 1
        assert set(tc["counts"]) <= BASIS

    def test_dft_rotation_adds_entangling_cost(self):
        import pt_ququint_ibmq_aer as qa
        tc_phi = qa.transpiled_counts(qa.phi_prep_circuit())
        tc_full = qa.transpiled_counts(
            qa.phi_prep_circuit().compose(qa.dft_rotation_circuit())
        )
        assert tc_full["cx"] > tc_phi["cx"]
        assert set(tc_full["counts"]) <= BASIS

    def test_transpiled_counts_structure_and_error_budget_arithmetic(self):
        import pt_ququint_ibmq_aer as qa
        tc = qa.transpiled_counts(qa.phi_prep_circuit())
        assert tc["depth"] > 0
        assert tc["num_qubits"] == 6
        # pure arithmetic feeding the Phase-3 prereg predictions:
        assert qa.error_budget(7, 3e-3, ratio=10.0) == pytest.approx(7 * 0.03)
        assert qa.error_budget(0, 1e-3) == 0.0


# === NOISE-MODELL (STRESS, nicht kalibriert) ===


class TestNoiseModel:
    def test_noise_model_contains_1q_2q_and_readout(self):
        import pt_ququint_ibmq_aer as qa
        nm = qa.build_noise_model(1e-3, 1e-2, ratio=10.0)
        entries = nm.to_dict()["errors"]
        qops = [e.get("operations", []) for e in entries if e["type"] == "qerror"]
        assert any("cx" in ops for ops in qops)
        assert any(set(ops) & {"rz", "sx", "x"} for ops in qops)
        assert any(e["type"] == "roerror" for e in entries)

    def test_zero_p1_keeps_readout_only(self):
        import pt_ququint_ibmq_aer as qa
        nm = qa.build_noise_model(0.0, 1e-2)
        entries = nm.to_dict()["errors"]
        assert any(e["type"] == "roerror" for e in entries)
        assert not any(e["type"] == "qerror" for e in entries)

    def test_noise_model_rejects_invalid_params(self):
        import pt_ququint_ibmq_aer as qa
        with pytest.raises(ValueError):
            qa.build_noise_model(-1e-3)
        with pytest.raises(ValueError):
            qa.build_noise_model(1e-3, ro=0.6)


# === WITNESS AUS COUNTS (parametrischer Bootstrap um die beobachteten
#     Histogramme — exakt das, was Hardware-Daten liefern) ===


class TestWitnessFromCounts:
    def test_ideal_phi_histogram_gives_margin_above_bound(self):
        import pt_ququint_ibmq as qi
        import pt_ququint_ibmq_aer as qa
        p = qi.histogram_dft(qi.phi_max_encoded())
        counts = qi.sample_shots_from_probs(p, 8192, seed=3)
        out = qa.witness_from_counts(counts)
        assert out["v_hat"] > 0.9
        assert out["margin"] > 0.0

    def test_ideal_separable_histogram_stays_at_bound(self):
        import pt_ququint_ibmq as qi
        import pt_ququint_ibmq_aer as qa
        p = qi.histogram_dft(qi.separable_dephased_encoded())
        counts = qi.sample_shots_from_probs(p, 8192, seed=5)
        out = qa.witness_from_counts(counts)
        assert abs(out["v_hat"] - qa.WITNESS_BOUND) <= 4.0 * out["se"] + 1e-12
        assert out["margin"] < 0.0

    def test_fully_depolarized_limit_below_bound(self):
        # depolarisiertes Limit: uniform 1/64 -> V = 5/64 < 1/5 — extreme
        # Noise erzeugt KEIN False Positive
        import pt_ququint_ibmq_aer as qa
        p = np.full(TWO_DIM, 1.0 / 64.0)
        v = qa.dft_diagonal_weight(p)
        assert v == pytest.approx(5.0 / 64.0)
        assert v < qa.WITNESS_BOUND


# === NOISELESS RUN (Readout 1e-2, kein 1q-Fehler) ===


class TestNoiselessRun:
    def test_phi_above_bound_and_confound_verified(self):
        import pt_ququint_ibmq_aer as qa
        out = qa.run_witness(p1=0.0, n_shots=8192, seed=42)
        assert out["phi"]["v_hat"] > 0.5
        assert out["phi"]["margin"] > 0.0
        assert out["confound_max_diff"] <= 0.05

    def test_separable_never_flagged_noiseless(self):
        import pt_ququint_ibmq_aer as qa
        out = qa.run_witness(p1=0.0, n_shots=8192, seed=42)
        assert abs(out["sep"]["v_hat"] - qa.WITNESS_BOUND) <= 0.03
        assert out["sep"]["margin"] < 0.0


# === NOISE-SWEEP (STRESS-Kurve) ===


class TestNoiseSweep:
    def test_phi_witness_degrades_monotonically(self):
        import pt_ququint_ibmq_aer as qa
        curve = qa.witness_curve([0.0, 3e-4, 3e-3], n_shots=8192, seed=7)
        vs = [pt["phi"]["v_hat"] for pt in curve["points"]]
        assert vs[0] > vs[1] + 0.02
        assert vs[1] > vs[2] + 0.02
        assert curve["points"][0]["phi"]["margin"] > 0.0
        assert curve["points"][1]["phi"]["margin"] > 0.0

    def test_separable_never_falsely_flagged_at_any_noise(self):
        import pt_ququint_ibmq_aer as qa
        curve = qa.witness_curve([0.0, 3e-4, 3e-3], n_shots=8192, seed=7)
        for pt in curve["points"]:
            assert pt["sep"]["margin"] < 0.0
            assert pt["sep"]["v_hat"] <= qa.WITNESS_BOUND + 0.05
            assert pt["confound_max_diff"] <= 0.05


# === PHASE-2-REPORT (Prereg-Feeding) ===


class TestPhase2Report:
    def test_report_structure_feeds_phase3_prereg(self):
        import pt_ququint_ibmq_aer as qa
        rep = qa.phase2_report(n_shots=2048, seed=11)
        assert "gate_counts" in rep and "curve" in rep and "prereg_draft" in rep
        assert "phi_prep" in rep["gate_counts"] and "dft_rotation" in rep["gate_counts"]
        draft = rep["prereg_draft"]
        assert draft["decision_rule_candidate"] == "v_hat - 4*SE > 1/5"
        assert "phi" in draft and "sep" in draft and "confound_max_diff" in draft


# === PHASE-2-GUARDS ===


class TestPhase2Guards:
    def test_no_real_backend_access_in_source(self):
        import pt_ququint_ibmq_aer as qa
        src = open(qa.__file__, encoding="utf-8").read()
        assert "qiskit_ibm" not in src

    def test_stress_model_caveat_documented(self):
        import pt_ququint_ibmq_aer as qa
        src = open(qa.__file__, encoding="utf-8").read().lower()
        assert "stress" in src
        assert "not a calibrated" in src

    def test_ccz_thesis_out_of_scope_documented(self):
        # Verfeinerung ggü. §Z.12.6: die CCZ-Fidelity-These braucht natives
        # Qudit-Hardware-CCZ — in der 3-Qubit-Emulation (CX-basiert) ist sie
        # nicht testbar. Das Modul muss diese Ausgrenzung dokumentieren.
        import pt_ququint_ibmq_aer as qa
        src = open(qa.__file__, encoding="utf-8").read().lower()
        assert "not testable in emulation" in src