# -*- coding: utf-8 -*-
"""Tests fuer pt_ram_q_prio48_qpu.py — EXPERIMENT 055 (LEG FP48-COMBINED),
QPU-Treiber, 0 QPU / 0 Token (getestet wird der Driver-Flow mit Fakes,
nicht die Hardware).

Erste Driver-Coverage ueberhaupt (Driver-Realignment II, 2026-10-03, nach
dem 04:31-Spurious-Resume-Abort am ISA-Gate-Stale x 2->4 bei KONSTANTER
2q-Spalte): gepinnt wird, dass der Resume-Zweig den Job ueber die
Job-ID-Datei wiederaufnimmt (KEIN neuer Job, 046/053-Praezedenz), OHNE
frischen Re-Transpile (die ISA eines eingereichten Jobs ist auf IBM
gefroren), dass seine fetch-Totals byte-frozen aus dem committeten
ISA-Gate rekonstruiert werden (bit-identisch zum Submit-Lauf, weil der
Submit-Pfad totals == totals_gate assertet), dass existierendes Raw
kontaktfrei zurueckgegeben wird, dass die Submission den Gate-Crosscheck
VOR dem QPU-Kontakt ausfuehrt (K2-Praezedenz bleibt im Submit-Zweig) und
dass der committete Gate-Artefakt-Kreis (830/84/160, Prereg-Pin) die
Resume-Quelle ist.
"""
import json

import pt_ram_q_prio48 as p48
import pt_ram_q_prio48_qpu as pqr
import pytest

PREREG_MD5 = "b7afc42c62a6da75b2e43dd3674f8965"


# ------------------------------------------------------------------ Fakes

class _Counts:
    def __init__(self, counts):
        self._counts = counts

    def get_counts(self):
        return self._counts


class _Data:
    def __init__(self, counts):
        self.c = _Counts(counts)


class _Entry:
    def __init__(self, counts):
        self.data = _Data(counts)


class FakeResult:
    """job.result()-Stellvertreter: indexierbar wie ein SamplerV2-Primitive."""

    def __init__(self, n_circuits, shots=8192):
        self._entries = [_Entry({"00": shots}) for _ in range(n_circuits)]

    def __getitem__(self, i):
        return self._entries[i]

    def __len__(self):
        return len(self._entries)


class FakeJob:
    def status(self):
        return "JobStatus.DONE"

    def result(self):
        return FakeResult(p48.N_CIRCUITS)


class FakeService:
    """service.job(id) wird genau einmal erwartet (Resume-Vertrag)."""

    def __init__(self):
        self.jobs = []

    def job(self, job_id):
        self.jobs.append(job_id)
        return FakeJob()


class FakeBackend:
    name = "ibm_fez"


def _patch_backend(monkeypatch, backend=FakeBackend()):
    monkeypatch.setattr(pqr, "get_backend", lambda service: backend)
    return backend


# ------------------------------------------------------- Resume-Vertrag II

class TestResumeBranchRealignmentII:
    def test_resume_fetches_job_without_retranspile(self, tmp_path,
                                                    monkeypatch):
        # Job-ID-Datei vorhanden, Raw fehlt -> Resume, KEIN neuer Job und
        # KEIN frischer Re-Transpile (die ISA des Jobs ist auf IBM gefroren;
        # Praezedenz 04:31: Target-Refresh wuerde hier sonst spurios aborten).
        monkeypatch.setattr(
            pqr, "transpile_forced",
            lambda *a, **k: pytest.fail("Re-Transpile auf Resume"))
        _patch_backend(monkeypatch)
        service = FakeService()
        jid = tmp_path / "job_id.txt"
        jid.write_text("fakejobid123")
        raw = tmp_path / "raw.json"
        assert not raw.exists()

        doc = pqr.run_qpu_job(service_getter=lambda: service,
                              results_path=str(raw), job_id_path=str(jid))

        assert doc["status"] == "QPU_RAW_FETCHED"
        assert service.jobs == ["fakejobid123"]      # genau 1 Fetch, 0 Submit
        assert doc["job_meta"] == {"job_id": "fakejobid123",
                                   "backend": "ibm_fez"}
        assert doc["n_circuits"] == p48.N_CIRCUITS == 160
        assert doc["backend"] == "ibm_fez"
        assert all(e["shots_actual"] == 8192 for e in doc["counts"])
        assert doc["counts_md5"] == pqr.counts_md5(
            [e["counts"] for e in doc["counts"]])
        assert raw.exists()                          # Raw persistiert
        # banned_from_raw bleibt abwesend (Raw-Disziplin):
        for banned in ("kappa", "ratio", "gamma", "band", "verdict",
                       "res_v3", "center", "delta_cal"):
            assert banned not in doc

    def test_resume_totals_byte_frozen_from_committed_gate(self, tmp_path,
                                                           monkeypatch):
        # Der Totals-Ersatz auf Resume kommt aus dem committeten Gate-File —
        # exakt das totals_gate-Dikt des Submit-Laufs (der Submit-Pfad
        # assertet totals == totals_gate, also ist die Rekonstruktion
        # bit-identisch zu doc["transpile"] des Submit-Zweigs).
        monkeypatch.setattr(
            pqr, "transpile_forced",
            lambda *a, **k: pytest.fail("Re-Transpile auf Resume"))
        _patch_backend(monkeypatch)
        with open(p48.ISA_GATE_PATH, encoding="utf-8") as fh:
            gate = json.load(fh)
        jid = tmp_path / "job_id.txt"
        jid.write_text("fakejobid123")

        doc = pqr.run_qpu_job(service_getter=lambda: FakeService(),
                              results_path=str(tmp_path / "raw.json"),
                              job_id_path=str(jid))

        assert doc["transpile"] == {
            "optimization_level": int(gate["optimization_level"]),
            "seed_transpiler": int(gate["transpile_seed"]),
            "isa_2q_total": int(gate["total_two_q"]),
            "isa_2q_max": int(gate["max_two_q"])}

    def test_resume_requires_service(self, tmp_path):
        # backend_getter gesetzt => service None => Resume-Pflicht-Assert
        # (die Job-ID-Datei allein genuegt NICHT zum QPU-Kontakt).
        jid = tmp_path / "job_id.txt"
        jid.write_text("fakejobid123")
        with pytest.raises(AssertionError, match="Resume braucht"):
            pqr.run_qpu_job(backend_getter=lambda: FakeBackend(),
                            results_path=str(tmp_path / "raw.json"),
                            job_id_path=str(jid))

    def test_existing_raw_short_circuits_without_contact(self, tmp_path,
                                                         monkeypatch):
        # Raw existiert: geschieht NICHTS — kein Service, kein Gate.
        def _boom():
            pytest.fail("QPU-Kontakt trotz existierendem Raw")
        monkeypatch.setattr(pqr, "get_service", _boom)
        raw = tmp_path / "raw.json"
        raw.write_text(json.dumps({"status": "QPU_RAW_FETCHED",
                                   "marker": "alt"}))
        doc = pqr.run_qpu_job(service_getter=_boom,
                              results_path=str(raw),
                              job_id_path=str(tmp_path / "job_id.txt"))
        assert doc == {"status": "QPU_RAW_FETCHED", "marker": "alt"}


# ------------------------------------------------------ Submission-Zweig

class TestSubmissionBranchStillGatechecks:
    def test_gate_check_runs_before_submission(self, tmp_path, monkeypatch):
        # K2-Praezedenz bleibt im Submit-Zweig: Gate-stale -> Abbruch VOR
        # jedem QPU-Kontakt (SamplerV2/service.job werden nie erreicht).
        service = FakeService()

        def _stale(backend, circuits, isa_gate=pqr.ISA_GATE_PATH):
            raise AssertionError("ISA-Gate-Stale-Fake")
        monkeypatch.setattr(pqr, "_isa_verified_for_submit", _stale)
        _patch_backend(monkeypatch)
        with pytest.raises(AssertionError, match="ISA-Gate-Stale-Fake"):
            pqr.run_qpu_job(
                service_getter=lambda: service,
                results_path=str(tmp_path / "raw.json"),
                job_id_path=str(tmp_path / "job_id.txt"))
        assert service.jobs == []


# ------------------------------------------------ committete Gate-Quelle

class TestCommittedGateFileIsResumeSource:
    def test_gate_artifact_pinned(self):
        # committetes ISA-Gate c9ccaea: K2-Schema + EXTRA prereg_md5; der
        # resume-Totals-Ersatz liest genau dieses Artefakt.
        with open(p48.ISA_GATE_PATH, encoding="utf-8") as fh:
            gate = json.load(fh)
        assert gate["total_two_q"] == 830
        assert gate["max_two_q"] == 84
        assert gate["optimization_level"] == 3
        assert gate["transpile_seed"] == 7
        assert gate["prereg_md5"] == PREREG_MD5
        assert len(gate["per_circuit_two_q"]) == p48.N_CIRCUITS == 160