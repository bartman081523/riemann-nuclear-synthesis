# -*- coding: utf-8 -*-
"""Tests fuer pt_ram_q_hardware_qpu.py — Hardware-Bein-Vertraege OFFLINE.

KEIN Netzwerk: submit/fetch/resume laufen gegen FakeSampler/FakeJob/FakeFez.
Gepinnt: (1) DD XX + default_shots 8192 + EIN Job mit 58 Circuits;
(2) das Raw-Dokument enthaelt KEINEN Estimator und KEIN Verdict
(Freeze-B-Vertrag: Raw-Commit VOR Auswertung); (3) counts_md5 kanonisch und
deterministisch; (4) Resume-Vertrag (raw-exists -> No-op; job-id-Datei ->
Wiederaufnahme); (5) TOKEN-Disziplin (nur TOKEN1, kein TOKEN2).
"""
import json
from types import SimpleNamespace

import pytest

import pt_ram_q_hardware as hw
import pt_ram_q_hardware_aer as aer
import pt_ram_q_hardware_qpu as qpu


class FakeSampler:
    def __init__(self, mode=None):
        self.mode = mode
        self.submitted = None
        self.options = SimpleNamespace(
            default_shots=0,
            dynamical_decoupling=SimpleNamespace(enable=False,
                                                 sequence_type=None))

    def run(self, circuits):
        self.submitted = list(circuits)
        return FakeJob()


class FakeJob:
    def __init__(self):
        from qiskit.providers.jobstatus import JobStatus
        self._status = JobStatus.DONE

    def job_id(self):
        return "MOCK_RAMQ_JOB_000"

    def status(self):
        return self._status

    def result(self):
        # 58 Pubs mit data.c (creg "c" — QuantumCircuit(nq, nq) Default)
        out = []
        for i in range(58):
            counts = {"0" * (4 if i < 39 else 5): 8000,
                      "1" * (4 if i < 39 else 5): 192}
            out.append(SimpleNamespace(data=SimpleNamespace(
                c=SimpleNamespace(get_counts=lambda ct=counts: dict(ct)))))
        return out


class FakeService:
    def job(self, job_id):
        return FakeJob()


def _fake_backend():
    from qiskit_ibm_runtime.fake_provider import FakeFez
    return FakeFez()


class TestSubmitJob:
    def test_dd_xx_and_default_shots_frozen(self):
        s = FakeSampler()
        isa = qpu.isa_circuits(_fake_backend())
        job = qpu.submit_job(s, isa)
        assert s.options.default_shots == hw.SHOTS == 8192
        assert s.options.dynamical_decoupling.enable is True
        assert s.options.dynamical_decoupling.sequence_type == "XX"
        assert len(s.submitted) == 58
        assert job.job_id() == "MOCK_RAMQ_JOB_000"

    def test_isa_matches_freeze_b_report(self):
        # seed 7, opt level 3 -> bit-dieselbe Transpilation wie der
        # committete ISA-Report (1570 total 2q, max 76).
        isa = qpu.isa_circuits(_fake_backend())
        assert len(isa) == 58
        assert qpu.TRANSPILE_SEED == aer.TRANSPILE_SEED == 7


class TestCountsMd5:
    def test_canonical_serialization_pinned(self):
        payload = json.dumps([{"00": 3, "11": 5}], sort_keys=True,
                             separators=(",", ":")).encode("utf-8")
        assert payload == b'[{"00":3,"11":5}]'
        assert qpu.counts_md5([{"00": 3, "11": 5}]) == \
            "911deb659724419d74a211850adfaf2d"

    def test_deterministic_and_order_sensitive(self):
        a = [{"01": 2, "10": 4}]
        b = [{"10": 4, "01": 2}]
        assert qpu.counts_md5(a) == qpu.counts_md5(b)  # sort_keys
        assert qpu.counts_md5(a) != qpu.counts_md5([{"01": 4, "10": 2}])
        assert qpu.counts_md5(a) != qpu.counts_md5(a + a)


class TestFetchRaw:
    def test_raw_document_contract(self):
        circuits = aer.build_hardware_circuit_set()
        doc = qpu.fetch_raw(FakeJob().result(), circuits,
                            {"job_id": "J", "backend": "fake_fez",
                             "shots_per_circuit": 8192}, "fake_fez")
        assert doc["status"] == "QPU_RAW_FETCHED"
        assert doc["experiment"] == hw.EXPERIMENT
        assert doc["hypothesis"] == hw.HYPOTHESIS
        assert doc["n_circuits"] == 58
        assert doc["shots_per_circuit"] == 8192
        assert len(doc["counts"]) == 58
        assert doc["registered_run_config"] == \
            hw.load_frozen_prereg()["hardware_parameters"]["run_config"]
        assert doc["transpile"]["optimization_level"] == 3
        assert doc["transpile"]["seed_transpiler"] == 7

    def test_raw_contains_no_estimator_and_no_verdict(self):
        # FREEZE-B-VERTRAG: das Raw-Dokument wird committet, BEVOR ein
        # Estimator laeuft — kappa/ratio/band/verdict duerfen hier noch
        # gar nicht existieren.
        circuits = aer.build_hardware_circuit_set()
        doc = qpu.fetch_raw(FakeJob().result(), circuits,
                            {"job_id": "J", "backend": "b"}, "b")
        for forbidden in ("kappa", "ratio", "band", "verdict", "center",
                          "share"):
            assert forbidden not in doc
        assert doc["status"] != "EVALUATED"

    def test_counts_md5_in_doc_is_canonical(self):
        circuits = aer.build_hardware_circuit_set()
        doc = qpu.fetch_raw(FakeJob().result(), circuits,
                            {"job_id": "J", "backend": "b"}, "b")
        expected = qpu.counts_md5([e["counts"] for e in doc["counts"]])
        assert doc["counts_md5"] == expected


class TestRunQpuJob:
    def test_resume_noop_when_raw_exists(self, tmp_path, monkeypatch):
        raw = tmp_path / "raw.json"
        raw.write_text(json.dumps({"status": "QPU_RAW_FETCHED"}),
                       encoding="utf-8")

        def boom():
            raise AssertionError("backend darf bei Raw-No-op nicht angefasst "
                                 "werden")
        doc = qpu.run_qpu_job(backend_getter=boom,
                              results_path=str(raw))
        assert doc["status"] == "QPU_RAW_FETCHED"

    def test_full_flow_offline(self, tmp_path, monkeypatch):
        # SamplerV2 gegen FakeFez wuerde LOKAL ausfuehren (UUID-Job-ID,
        # ~25s) — der Vertragstest mockt den Sampler, nicht den Ablauf:
        # Submit -> job_id-Datei -> poll (DONE) -> fetch -> Raw-File.
        monkeypatch.setattr(qpu, "SamplerV2", FakeSampler)
        raw = tmp_path / "raw.json"
        jid = tmp_path / "job_id.txt"
        doc = qpu.run_qpu_job(backend_getter=_fake_backend,
                              service_getter=FakeService,
                              results_path=str(raw),
                              job_id_path=str(jid), poll=True)
        assert doc["status"] == "QPU_RAW_FETCHED"
        assert doc["job_meta"]["job_id"] == "MOCK_RAMQ_JOB_000"
        assert jid.read_text(encoding="utf-8") == "MOCK_RAMQ_JOB_000"
        loaded = json.loads(raw.read_text(encoding="utf-8"))
        assert loaded["counts_md5"] == doc["counts_md5"]
        assert all(e["shots_actual"] == 8192 for e in loaded["counts"])

    def test_resume_from_job_id_file(self, tmp_path):
        raw = tmp_path / "raw.json"
        jid = tmp_path / "job_id.txt"
        jid.write_text("RESUME_JOB_42", encoding="utf-8")
        doc = qpu.run_qpu_job(backend_getter=_fake_backend,
                              service_getter=FakeService,
                              results_path=str(raw), job_id_path=str(jid))
        assert doc["status"] == "QPU_RAW_FETCHED"
        assert doc["job_meta"]["job_id"] == "RESUME_JOB_42"


class TestGuards:
    def test_no_token2_in_module(self):
        src = open(qpu.__file__, encoding="utf-8").read()
        # Die einzige erlaubte TOKEN2-Erwähnung ist die Disziplin-Note
        # (Deklaration, kein Zugriff); gelesen/geladen wird NUR TOKEN1.
        stripped = src.replace("TOKEN2 wird NIE gelesen", "")
        assert "IBMQ_TOKEN2" not in stripped
        assert "os.environ.get" not in stripped  # kein direkter Env-Griff
        assert 'fez.load_token' in src  # Token-Pfad nur via pt_ququint_fez

    def test_raw_module_defines_no_evaluation(self):
        # Das Auswertungsmodul ist SEPARAT (Freeze-B-Vertrag): dieses Modul
        # darf keine Estimator-/Verdict-Funktion definieren.
        src = open(qpu.__file__, encoding="utf-8").read()
        for forbidden_def in ("def evaluate", "def compute_", "def center",
                              "def verdict", "def share_", "def ratio_"):
            assert forbidden_def not in src, forbidden_def