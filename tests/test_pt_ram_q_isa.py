# -*- coding: utf-8 -*-
"""Tests fuer pt_ram_q_isa.py — ISA-Report-Logik OFFLINE (FakeFez).

KEIN Netzwerk, KEIN QPU-Job: die Transpilation laeuft gegen das FakeFez-
Target (gleiche 1q/2q-Basis wie ibm_fez). Die ECHTE ibm_fez-Transpilation
ist der Script-Run (pt_ram_q_isa.py __main__, Freeze-B-Voraussetzung);
dieser Test pinnnt die Report-Struktur, die Ceiling-Logik und die
TOKEN1-Disziplin (kein TOKEN2-Import im Modul).
"""
import json

import pytest

import pt_ram_q_hardware as hw
import pt_ram_q_isa as isa_mod


@pytest.fixture(scope="module")
def fez_report():
    from qiskit_ibm_runtime.fake_provider import FakeFez
    _isa, report = isa_mod.isa_report(FakeFez())
    return report


class TestIsaReport:
    def test_all_58_circuits_present(self, fez_report):
        assert fez_report["n_circuits"] == 58
        assert len(fez_report["circuit_names"]) == 58
        assert len(fez_report["per_circuit"]) == 58

    def test_names_match_circuit_set(self, fez_report):
        import pt_ram_q_hardware_aer as aer
        names_expected = [c["name"] for c in aer.build_hardware_circuit_set()]
        assert fez_report["circuit_names"] == names_expected

    def test_total_is_sum_of_per_circuit(self, fez_report):
        s = sum(e["two_q"] for e in fez_report["per_circuit"].values())
        assert fez_report["total_two_q"] == s

    def test_max_is_max_of_per_circuit(self, fez_report):
        m = max(e["two_q"] for e in fez_report["per_circuit"].values())
        assert fez_report["max_two_q"] == m

    def test_loschmidt_and_struct_kinds_recorded(self, fez_report):
        kinds = {e["kind"] for e in fez_report["per_circuit"].values()}
        assert kinds == {"structure", "loschmidt", "negative_control",
                         "readout_cal"}


class TestCeilingCheck:
    def test_fakesez_passes(self, fez_report):
        check = isa_mod.ceiling_check(fez_report)
        assert check["ok"] is True
        assert check["violations"] == []
        assert check["per_circuit_max"] == hw.ISA_2Q_PER_CIRCUIT_MAX == 120
        assert check["total_max"] == hw.ISA_2Q_TOTAL_MAX == 6000

    def test_per_circuit_violation_detected(self):
        report = {"per_circuit": {"a": {"two_q": 121}, "b": {"two_q": 5}},
                  "total_two_q": 126}
        check = isa_mod.ceiling_check(report)
        assert check["ok"] is False
        assert check["violations"] == [{"name": "a", "two_q": 121,
                                        "ceiling": 120}]

    def test_total_violation_detected(self):
        report = {"per_circuit": {"a": {"two_q": 5}},
                  "total_two_q": 6001}
        check = isa_mod.ceiling_check(report)
        assert check["ok"] is False
        assert {"name": "__total__", "two_q": 6001,
                "ceiling": 6000} in check["violations"]


class TestRunIsaReport:
    def test_document_structure_and_verdict(self):
        from qiskit_ibm_runtime.fake_provider import FakeFez
        doc = isa_mod.run_isa_report(backend_getter=FakeFez,
                                     results_path=None)
        assert doc["verdict"] == "ISA_OK"
        assert doc["backend"] == "fake_fez"
        assert doc["optimization_level"] == 3
        assert doc["transpile_seed"] == 7
        assert doc["n_circuits"] == 58
        assert doc["isa_ceilings"] == {"per_circuit_2q_max": 120,
                                       "total_2q_max": 6000}
        assert doc["run_config_frozen"]["md5"] == \
            hw.load_frozen_prereg()["md5"]

    def test_results_file_written(self, tmp_path):
        from qiskit_ibm_runtime.fake_provider import FakeFez
        path = tmp_path / "isa.json"
        doc = isa_mod.run_isa_report(backend_getter=FakeFez,
                                     results_path=str(path))
        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert loaded == doc
        assert loaded["verdict"] == "ISA_OK"


class TestGuards:
    def test_no_token2_in_module(self):
        src = open(isa_mod.__file__, encoding="utf-8").read()
        assert "IBMQ_TOKEN2" not in src
        assert "TOKEN2" not in src.replace("TOKEN2 wird NIE gelesen", "")

    def test_no_sampler_import(self):
        # Auth-only-Modul: kein QPU-Job hier (SamplerV2 gehoert zum
        # Fez-Job-Runner nach Freeze B).
        src = open(isa_mod.__file__, encoding="utf-8").read()
        assert "SamplerV2" not in src
        assert "sampler.run" not in src