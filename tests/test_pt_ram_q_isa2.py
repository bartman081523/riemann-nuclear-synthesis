# -*- coding: utf-8 -*-
"""Tests fuer pt_ram_q_isa2.py — ISA-Report-Logik OFFLINE (FakeFez).

KEIN Netzwerk, KEIN QPU-Job: die Transpilation laeuft gegen das FakeFez-
Target (gleiche 1q/2q-Basis wie ibm_fez). Die ECHTE ibm_fez-Transpilation
ist der Script-Run (pt_ram_q_isa2.py __main__, Freeze-B'-Voraussetzung);
dieser Test pinnnt die Report-Struktur, die Ceiling-Logik und die
TOKEN1-Disziplin (kein TOKEN2-Import im Modul).
"""
import json

import pytest

import pt_ram_q_hardware2 as hw2
import pt_ram_q_isa2 as isa_mod


@pytest.fixture(scope="module")
def fez_report():
    from qiskit_ibm_runtime.fake_provider import FakeFez
    _isa, report = isa_mod.isa_report(FakeFez())
    return report


class TestIsaReport:
    def test_all_90_circuits_present(self, fez_report):
        assert fez_report["n_circuits"] == 90
        assert len(fez_report["circuit_names"]) == 90
        assert len(fez_report["per_circuit"]) == 90

    def test_names_match_circuit_set(self, fez_report):
        import pt_ram_q_hardware2_aer as s2b
        names_expected = [c["name"] for c in s2b.build_hardware_circuit_set()]
        assert fez_report["circuit_names"] == names_expected

    def test_total_is_sum_of_per_circuit(self, fez_report):
        s = sum(e["two_q"] for e in fez_report["per_circuit"].values())
        assert fez_report["total_two_q"] == s

    def test_max_is_max_of_per_circuit(self, fez_report):
        m = max(e["two_q"] for e in fez_report["per_circuit"].values())
        assert fez_report["max_two_q"] == m

    def test_all_kinds_recorded(self, fez_report):
        kinds = {e["kind"] for e in fez_report["per_circuit"].values()}
        assert kinds == {"structure", "loschmidt", "echo_ladder",
                         "diagnostik_structure", "diagnostik_loschmidt",
                         "negative_control", "readout_cal"}

    def test_ladder_cz_linear_at_anchor(self, fez_report):
        # Echo-Leiter am Anker: r Bloecke Prep+inv -> cz linear
        # (q3 Anker 149: r in {2,4,8}; r=1 ist der geteilte Anker-Loschmidt).
        ops = fez_report["per_circuit"]
        q3 = [ops[f"ladder_q3_d3_149_r{r}"]["two_q"] for r in (2, 4, 8)]
        q5 = [ops[f"ladder_q5_d5_433_r{r}"]["two_q"] for r in (2, 4, 8)]
        assert q3 == sorted(q3) and len(set(q3)) == 3
        assert q5 == sorted(q5) and len(set(q5)) == 3
        # r1 existiert NICHT als eigener Circuit (geteilt mit loschmidt)
        assert "ladder_q3_d3_149_r1" not in ops


class TestCeilingCheck:
    def test_fakesez_passes(self, fez_report):
        check = isa_mod.ceiling_check(fez_report)
        assert check["ok"] is True
        assert check["violations"] == []
        assert (check["per_circuit_max"]
                == hw2.ISA_2Q_PER_CIRCUIT_MAX == 120)
        assert check["total_max"] == hw2.ISA_2Q_TOTAL_MAX == 6000

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
        assert doc["experiment"] == "043-ram-q-minimal-register-echo"
        assert doc["hypothesis"] == "H-RAM-Q-3b"
        assert doc["optimization_level"] == 3
        assert doc["transpile_seed"] == 7
        assert doc["n_circuits"] == 90
        assert doc["isa_ceilings"] == {"per_circuit_2q_max": 120,
                                       "total_2q_max": 6000}
        assert doc["run_config_frozen"]["md5"] == \
            hw2.load_frozen_prereg()["md5"]

    def test_results_file_written(self, tmp_path):
        from qiskit_ibm_runtime.fake_provider import FakeFez
        path = tmp_path / "isa2.json"
        doc = isa_mod.run_isa_report(backend_getter=FakeFez,
                                     results_path=str(path))
        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert loaded == doc
        assert loaded["verdict"] == "ISA_OK"


class TestCommittedIsa2:
    """Pins gegen den ECHTEN ibm_fez-ISA-Report (skipif, offline)."""

    @pytest.fixture(scope="class")
    def doc(self):
        import os
        if not os.path.exists(isa_mod.ISA_PATH2):
            pytest.skip("pt_ram_q_isa2_report.json noch nicht committed")
        with open(isa_mod.ISA_PATH2, encoding="utf-8") as fh:
            return json.load(fh)

    def test_verdict_and_budget(self, doc):
        assert doc["backend"] == "ibm_fez"
        assert doc["verdict"] == "ISA_OK"
        assert doc["ceiling_check"]["ok"] is True
        assert doc["n_circuits"] == 90
        # Echtes Target (gemessen 2026-09-26): 493 2q total, max 84
        # (Leiter r8 q5) — Routing-Surplus gegenueber der Aer-Basis
        # (q5-Loschmidt 14 statt 8, q3 unveraendert 2).
        assert doc["total_two_q"] == 493
        assert doc["max_two_q"] == 84
        assert doc["max_two_q"] <= hw2.ISA_2Q_PER_CIRCUIT_MAX
        assert doc["total_two_q"] <= hw2.ISA_2Q_TOTAL_MAX

    def test_frozen_md5_and_anchor_depths(self, doc):
        assert doc["run_config_frozen"]["md5"] == \
            "0b9c9968dc5e99a3cc22962a8b760e44"
        pc = doc["per_circuit"]
        # Anker-Tiefen auf dem echten Target: q3 Loschmidt 2 (identisch
        # zur Aer-Basis), q5 14 (Routing), Leiter cz-linear.
        assert pc["loschmidt_q3_d3_149"]["two_q"] == 2
        assert pc["loschmidt_q5_d5_433"]["two_q"] == 14
        assert [pc[f"ladder_q3_d3_149_r{r}"]["two_q"] for r in (2, 4, 8)] \
            == [4, 8, 16]
        assert [pc[f"ladder_q5_d5_433_r{r}"]["two_q"] for r in (2, 4, 8)] \
            == [24, 44, 84]
    def test_no_token2_in_module(self):
        src = open(isa_mod.__file__, encoding="utf-8").read()
        assert "IBMQ_TOKEN2" not in src
        assert "TOKEN2" not in src.replace("TOKEN2 wird NIE gelesen", "")

    def test_no_sampler_import(self):
        # Auth-only-Modul: kein QPU-Job hier (SamplerV2 gehoert zum
        # Fez-Job-Runner nach Freeze B').
        src = open(isa_mod.__file__, encoding="utf-8").read()
        assert "SamplerV2" not in src
        assert "sampler.run" not in src