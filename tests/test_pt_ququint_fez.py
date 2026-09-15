"""
Tests for pt_ququint_fez.py — EXPERIMENT 032, Phase 3b (Fez-Runner).

Der QPU-Runner. ALLE Tests sind OFFLINE (kein Token, keine Submission):
  - Token-Parsing nur ueber eine Temp-Datei (niemals die echte .env)
  - V2-Result-Parsing gegen SimpleNamespace-Mocks (exakt der
    result[i].data.meas.get_counts()-Kontrakt)
  - Evaluation auf Counts aus der Phase-1-Histogramm-Sampling
  - ISA-Batch auf GenericBackendV2 (offline, kein Fez-Zugriff)
  - EIN lokaler SamplerV2-End-to-End gegen AerSimulator (statevector) —
    der echte V2-API-Pfad, ohne QPU-Kosten
  - run_phase3 komplett gemockt (monkeypatch) — Beweis, dass die
    Orchestrierung ohne Netz funktioniert
  - Guards: SamplerV2-Instantiierung nur in run_phase3; nur TOKEN1
    (IBMQ_TOKEN), TOKEN2 unberuehrt; Backend-Name ibm_fez
"""
import json
import os
import sys
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ORDER = (["phi_C", "phi_D"] + [f"sep_C_{k}" for k in range(5)]
         + [f"sep_D_{k}" for k in range(5)])


def counts_from_vec(vec, n_bits=6):
    """64-dim Counts-Vektor -> SamplerV2-Counts-Dict (Bitstring-Keys)."""
    return {format(i, f"0{n_bits}b"): int(c) for i, c in enumerate(vec) if int(c) > 0}


def fake_v2_result(counts_list):
    """Ein V2-Result-Mock: result[i].data.meas.get_counts()."""
    pubs = []
    for counts in counts_list:
        pubs.append(SimpleNamespace(data=SimpleNamespace(
            meas=SimpleNamespace(get_counts=lambda c=counts: dict(c)))))
    return list(pubs)


def canned_counts(n_shots=8192, seed=17, phi_only_ideal=False):
    """Counts-Batch in CIRCUIT_ORDER aus den Phase-1-Histogrammen."""
    import pt_ququint_ibmq as qi
    rng_seed = 11
    phi_c = qi.histogram_computational(qi.phi_max_encoded())
    phi_d = qi.histogram_dft(qi.phi_max_encoded())
    sep_c = qi.histogram_computational(qi.separable_dephased_encoded())
    sep_d = qi.histogram_dft(qi.separable_dephased_encoded())
    out = []
    out.append(qi.sample_shots_from_probs(phi_c, n_shots, seed=rng_seed))
    out.append(qi.sample_shots_from_probs(phi_d, n_shots, seed=rng_seed + 1))
    for k in range(5):
        comp = qi.histogram_computational(qi.product_encoded(k, k))
        out.append(qi.sample_shots_from_probs(comp, n_shots, seed=rng_seed + 2 + k))
    for k in range(5):
        comp = qi.histogram_computational(qi.product_encoded(k, k))
        out.append(qi.sample_shots_from_probs(
            qi.histogram_dft(qi.product_encoded(k, k)), n_shots, seed=rng_seed + 7 + k))
    return [counts_from_vec(np.asarray(v)) for v in out]


# === TOKEN (nur Temp-Dateien — niemals die echte .env) ===


class TestToken:
    def test_load_token_reads_only_token1(self, tmp_path):
        import pt_ququint_fez as pf
        env = tmp_path / ".env"
        env.write_text("IBMQ_TOKEN2=token_zwei\nIBMQ_TOKEN=token_eins\n")
        assert pf.load_token(str(env)) == "token_eins"

    def test_load_token_raises_when_missing(self, tmp_path):
        import pt_ququint_fez as pf
        env = tmp_path / ".env"
        env.write_text("OTHER_KEY=x\n")
        with pytest.raises(RuntimeError):
            pf.load_token(str(env))


# === V2-RESULT-PARSING ===


class TestCountsParsing:
    def test_counts_to_vec_is_raw_and_indexed(self):
        import pt_ququint_fez as pf
        counts = {"000000": 3, "010101": 5}
        vec = pf.counts_to_vec(counts)
        assert vec[0] == 3.0
        assert vec[21] == 5.0  # int('010101', 2) = 21
        assert vec.sum() == 8.0  # RAW counts, nicht normiert

    def test_collect_counts_reads_v2_contract(self):
        import pt_ququint_fez as pf
        canned = canned_counts(n_shots=512)
        result = fake_v2_result(canned)
        out = pf.collect_counts(result, 12)
        assert len(out) == 12
        assert out[0] == canned[0]
        assert out[1] == canned[1]

    def test_batch_order_preserved(self):
        # Ideal-Daten-Struktur: phi_C UND phi_D tragen die 5 Diagonal-Bins
        # (|phi> ist DFT-invariant!), sep_C gepoolt ebenfalls (Konfund),
        # sep_D gepoolt ist uniform ueber die 25 logischen Bins (diag ~ 1/5)
        import pt_ququint_fez as pf
        canned = canned_counts(n_shots=512)
        out = pf.collect_counts(fake_v2_result(canned), 12)
        diag = [k * 8 + k for k in range(5)]
        logical = [a * 8 + b for a in range(5) for b in range(5)]

        def pooled_vec(indices):
            vs = [pf.counts_to_vec(out[i]) for i in indices]
            total = sum(v.sum() for v in vs)
            return sum(vs) / total

        v_c = pf.counts_to_vec(out[0])
        v_d = pf.counts_to_vec(out[1])
        assert v_c[diag].sum() > 0.9 * v_c.sum()
        assert v_d[diag].sum() > 0.9 * v_d.sum()
        p_sc = pooled_vec(range(2, 7))
        assert p_sc[diag].sum() > 0.9
        p_sd = pooled_vec(range(7, 12))
        assert p_sd[logical].sum() > 0.9
        assert p_sd[diag].sum() < 0.35  # uniform 25: Diagonal-Anteil ~ 1/5


# === EVALUATION (pure Funktion, keine Hardware) ===


class TestEvaluate:
    def test_ideal_counts_pass_rule(self, tmp_path):
        import pt_ququint_prereg as pr
        import pt_ququint_fez as pf
        payload = pr.build_prereg_payload()
        out = pf.evaluate(canned_counts(n_shots=8192), payload)
        assert out["phi_margin_pass"] is True
        assert out["sep_margin_pass"] is True
        assert out["confound_pass"] is True
        assert out["rule_holds"] is True
        assert out["decision_rule"] == payload["decision_rule"]

    def test_false_positive_on_sep_is_caught(self):
        # Kontroll-Verletzung: sep-D-Histogramme durch phi-DFT ersetzt
        import pt_ququint_ibmq as qi
        import pt_ququint_prereg as pr
        import pt_ququint_fez as pf
        payload = pr.build_prereg_payload()
        counts = canned_counts(n_shots=8192)
        phi_d = counts_from_vec(qi.histogram_dft(qi.phi_max_encoded()) * 8192)
        for i in range(7, 12):
            counts[i] = phi_d
        out = pf.evaluate(counts, payload)
        assert out["sep_margin_pass"] is False
        assert out["rule_holds"] is False

    def test_confound_violation_detected(self):
        # phi_C wird auf einen anderen Basiszustand verschoben -> Konfund bricht
        import pt_ququint_ibmq as qi
        import pt_ququint_prereg as pr
        import pt_ququint_fez as pf
        payload = pr.build_prereg_payload()
        counts = canned_counts(n_shots=8192)
        counts[0] = counts_from_vec(qi.histogram_computational(qi.product_encoded(1, 1)) * 8192)
        out = pf.evaluate(counts, payload)
        assert out["confound_pass"] is False
        assert out["rule_holds"] is False

    def test_result_carries_all_prereg_keys_and_leakage(self):
        import pt_ququint_prereg as pr
        import pt_ququint_fez as pf
        payload = pr.build_prereg_payload()
        out = pf.evaluate(canned_counts(n_shots=8192), payload)
        for key in payload["predictions"]:
            assert key in out
        assert "leakage_rate_phi_C" in out and "leakage_rate_sep_C" in out
        assert "phi_v_hat" in out and "sep_v_hat" in out
        # Ideal-Daten sind SAUBERER als das Fez-STRESS-Band annimmt:
        # phi-Margin ueber dem Band (weniger Noise als modelliert),
        # sep-Margin naeher an der Schranke, Konfund unter dem Band.
        # Alle drei Bänder verfehlt, Regel trotzdem erfuellt — das Band ist
        # die sekundaere Modell-Treue-Meldung, nicht die Entscheidung.
        assert out["bands_hold"] == {"phi_margin": False, "sep_margin": False,
                                     "confound_max_diff": False}
        assert out["rule_holds"] is True

    def test_bands_hold_on_stress_point(self):
        # auf dem Phase-2-STRESS-Punkt (3e-4) muessen ALLE drei Bänder
        # halten — das ist die Kalibrierung der Band-Pruefung selbst
        import pt_ququint_prereg as pr
        import pt_ququint_fez as pf
        payload = pr.build_prereg_payload()
        emu = pr.build_emulated_result()
        bands = pf._check_bands(result=None, margins={
            "phi_margin": emu["phi_margin"],
            "sep_margin": emu["sep_margin"],
            "confound_max_diff": emu["confound_max_diff"],
        }, prereg=payload)
        assert bands == {"phi_margin": True, "sep_margin": True,
                         "confound_max_diff": True}


# === ISA-BATCH (offline, GenericBackendV2 — KEIN Fez-Zugriff) ===


class TestIsaBatch:
    def test_isa_batch_structure_on_generic_backend(self):
        import pt_ququint_fez as pf
        from qiskit.providers.fake_provider import GenericBackendV2
        backend = GenericBackendV2(num_qubits=27, basis_gates=["rz", "sx", "x", "ecr"])
        isa, report = pf.isa_batch(backend)
        assert len(isa) == 12
        assert report["circuit_names"] == list(ORDER)
        assert all(c.num_qubits >= 6 for c in isa)
        for name, circ in zip(ORDER, isa):
            ops = circ.count_ops()
            two_q = sum(v for k, v in ops.items() if k not in ("rz", "sx", "x", "measure", "barrier", "delay", "id"))
            if name.startswith("sep_C"):
                assert two_q == 0, f"{name} darf keine 2q-Gates haben"
            if name.startswith("sep_D"):
                assert two_q > 0
        assert report["total_two_q"] > 0

    def test_isa_batch_matches_phase2_cost_structure(self):
        # die Phase-2-Struktur muss überleben: phi_D ~ 45 2q-Gates
        # (ohne SWAP-Blowup auf einem 27-Qubit-Target)
        import pt_ququint_fez as pf
        from qiskit.providers.fake_provider import GenericBackendV2
        backend = GenericBackendV2(num_qubits=27, basis_gates=["rz", "sx", "x", "ecr"])
        isa, report = pf.isa_batch(backend)
        idx = {n: i for i, n in enumerate(ORDER)}
        ops_phi_d = isa[idx["phi_D"]].count_ops()
        two_q_phi_d = sum(v for k, v in ops_phi_d.items()
                          if k not in ("rz", "sx", "x", "measure", "barrier", "delay"))
        assert 40 <= two_q_phi_d <= 60
        assert report["per_circuit"]["phi_D"]["two_q"] == two_q_phi_d


# === LOKALER END-TO-END (SamplerV2 gegen Aer, statevector) ===


class TestLocalEndToEnd:
    def test_sampler_v2_local_then_evaluate(self, tmp_path):
        import pt_ququint_prereg as pr
        import pt_ququint_fez as pf
        from qiskit_aer import AerSimulator
        from qiskit_ibm_runtime import SamplerV2
        import pt_ququint_ibmq_aer as qa
        layout = qa.witness_job_layout()
        circuits = [layout["phi_C"], layout["phi_D"]] + layout["sep_C"] + layout["sep_D"]
        sampler = SamplerV2(mode=AerSimulator(method="statevector"))
        sampler.options.default_shots = 1024
        result = sampler.run(circuits).result()
        counts = pf.collect_counts(result, 12)
        payload = pr.build_prereg_payload()
        out = pf.evaluate(counts, payload)
        assert out["phi_margin_pass"] is True
        assert out["sep_margin_pass"] is True
        assert out["rule_holds"] is True


# === RUN_PHASE3 (komplett gemockt — beweist: Orchestrierung ohne Netz) ===


class TestRunPhase3Mocked:
    def test_run_phase3_orchestration_with_mocks(self, tmp_path, monkeypatch):
        import pt_ququint_fez as pf
        from qiskit_aer import AerSimulator
        from qiskit_ibm_runtime import SamplerV2

        # das echte gefrorene Prereg (md5-verifiziert) nach tmp kopieren
        repo_prereg = os.path.join(os.path.dirname(pf.__file__),
                                   "pt_ququint_fez_prereg.json")
        prereg_path = tmp_path / "prereg.json"
        prereg_path.write_text(open(repo_prereg, encoding="utf-8").read(),
                               encoding="utf-8")

        class FakeSampler:
            def __init__(self, mode=None):
                self.mode = mode
                self.options = SimpleNamespace(
                    default_shots=0,
                    dynamical_decoupling=SimpleNamespace(
                        enable=False, sequence_type=None),
                )
            def run(self, circuits):
                real = SamplerV2(mode=AerSimulator(method="statevector"))
                real.options.default_shots = 512
                res = real.run(circuits).result()
                return SimpleNamespace(
                    job_id=lambda: "MOCK_JOB_ID_000",
                    result=lambda: res,
                )

        monkeypatch.setattr(pf, "load_token", lambda *a, **kw: "MOCK_TOKEN")
        monkeypatch.setattr(pf, "get_service", lambda token: "MOCK_SERVICE")
        monkeypatch.setattr(pf, "get_backend", lambda service: "MOCK_BACKEND")
        monkeypatch.setattr(pf, "SamplerV2", FakeSampler)

        # PassManager-Vertrag: Objekt mit .run(circuits) — wie StagedPassManager
        class FakePassManager:
            def run(self, circuits):
                return list(circuits)

        monkeypatch.setattr(pf, "generate_preset_pass_manager",
                            lambda **kw: FakePassManager())

        out_path = tmp_path / "results.json"
        audit_path = tmp_path / "audit.json"
        result = pf.run_phase3(prereg_path=str(prereg_path),
                               results_path=str(out_path),
                               audit_path=str(audit_path),
                               shots=512)
        assert result["job_id"] == "MOCK_JOB_ID_000"
        assert result["rule_holds"] is True
        written = json.loads(out_path.read_text())
        assert written["job_id"] == "MOCK_JOB_ID_000"
        assert written["emulated"] is False
        assert audit_path.exists()
        assert json.loads(audit_path.read_text())["status"] == "CONFIRMED"


# === GUARDS ===


class TestFezGuards:
    def test_sampler_v2_instantiated_only_in_run_phase3(self):
        # die Submission darf nur in run_phase3 passieren — KEIN Testpfad
        # instantiiert einen Sampler (Quelle: strukturelle Prüfung)
        import pt_ququint_fez as pf
        src = open(pf.__file__, encoding="utf-8").read()
        assert src.count("SamplerV2(") == 1
        run_pos = src.index("def run_phase3")
        inst_pos = src.index("SamplerV2(")
        assert inst_pos > run_pos

    def test_backend_is_ibm_fez_and_token1_only(self):
        import pt_ququint_fez as pf
        assert pf.BACKEND_NAME == "ibm_fez"
        src = open(pf.__file__, encoding="utf-8").read()
        assert "IBMQ_TOKEN2" not in src  # TOKEN2 unberuehrt
        assert "IBMQ_TOKEN=" in src      # TOKEN1

    def test_prereg_verified_before_submission(self):
        # run_phase3 muss das gefrorene Prereg via load_frozen_prereg laden
        # (md5-Verifikation ist Teil des Pfads) und NACH dem Freeze die
        # Submission anstossen
        import pt_ququint_fez as pf
        src = open(pf.__file__, encoding="utf-8").read()
        assert "load_frozen_prereg" in src
        run_pos = src.index("def run_phase3")
        load_pos = src.index("load_frozen_prereg(", run_pos)
        submit_pos = src.index("pf.submit(", run_pos) if "pf.submit(" in src \
            else src.index("submit(", run_pos)
        assert load_pos < submit_pos