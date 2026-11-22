# -*- coding: utf-8 -*-
"""Tests fuer pt_ram_q_isa3.py — ISA-Report-Logik OFFLINE (FakeFez).

KEIN Netzwerk, KEIN QPU-Job: die Transpilation laeuft gegen das FakeFez-
Target (gleiche 1q/2q-Basis wie ibm_fez).  Die ECHTE ibm_fez-Transpilation
ist der Script-Run (pt_ram_q_isa3.py __main__, Freeze-B''-Voraussetzung);
dieser Test pinnt die Report-Struktur, die Ceiling-Logik, die Set-/Anker-
Struktur des 116-Circuit-Satzes und die TOKEN1-Disziplin.
"""
import json

import pytest

import pt_ram_q_hardware3 as h3
import pt_ram_q_isa3 as isa_mod


@pytest.fixture(scope="module")
def fez_report():
    from qiskit_ibm_runtime.fake_provider import FakeFez
    _isa, report = isa_mod.isa_report(FakeFez())
    return report


class TestIsaReport:
    def test_all_116_circuits_present(self, fez_report):
        assert fez_report["n_circuits"] == 116
        assert len(fez_report["circuit_names"]) == 116
        assert len(fez_report["per_circuit"]) == 116

    def test_names_match_circuit_set(self, fez_report):
        import pt_ram_q_hardware3_aer as s3a
        names_expected = [c["name"] for c in s3a.build_hardware_circuit_set()]
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
                         "kalibrier_structure", "kalibrier_loschmidt",
                         "negative_control", "readout_cal"}

    def test_set_field_recorded(self, fez_report):
        # NEU gegenueber ISA-2: Set-Zugehoerigkeit pro Circuit mitreportiert
        pc = fez_report["per_circuit"]
        sets = {e.get("set") for e in pc.values()}
        assert sets <= {"verdict", "cal", None}
        assert {"verdict", "cal"} <= sets
        for name in ("struct_q3_d3_181_r0", "loschmidt_q5_d5_467",
                     "ladder_q3_d3_181_r4"):
            assert pc[name]["set"] == "verdict"
        for name in ("calstruct_q3_d3_149_r0", "calloschmidt_q5_d5_433"):
            assert pc[name]["set"] == "cal"

    def test_ladder_cz_linear_at_anchor(self, fez_report):
        # Echo-Leiter am NEUEN Anker: r Bloecke Prep+inv -> cz linear
        # (q3 Anker 181, q5 Anker 467; r=1 ist der geteilte Anker-Loschmidt).
        ops = fez_report["per_circuit"]
        q3 = [ops[f"ladder_q3_d3_181_r{r}"]["two_q"] for r in (2, 4, 8)]
        q5 = [ops[f"ladder_q5_d5_467_r{r}"]["two_q"] for r in (2, 4, 8)]
        assert q3 == sorted(q3) and len(set(q3)) == 3
        assert q5 == sorted(q5) and len(set(q5)) == 3
        assert "ladder_q3_d3_181_r1" not in ops


class TestCeilingCheck:
    def test_fakesez_passes(self, fez_report):
        check = isa_mod.ceiling_check(fez_report)
        assert check["ok"] is True
        assert check["violations"] == []
        assert (check["per_circuit_max"]
                == h3.ISA_2Q_PER_CIRCUIT_MAX == 120)
        assert check["total_max"] == h3.ISA_2Q_TOTAL_MAX == 6000

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
        assert doc["experiment"] == "044-ram-q-coherent-prep-error"
        assert doc["hypothesis"] == "H-RAM-Q-4"
        assert doc["optimization_level"] == 3
        assert doc["transpile_seed"] == 7
        assert doc["n_circuits"] == 116
        assert doc["isa_ceilings"] == {"per_circuit_2q_max": 120,
                                       "total_2q_max": 6000}
        assert doc["run_config_frozen"]["md5"] == \
            h3.load_frozen_prereg()["md5"]

    def test_results_file_written(self, tmp_path):
        from qiskit_ibm_runtime.fake_provider import FakeFez
        path = tmp_path / "isa3.json"
        doc = isa_mod.run_isa_report(backend_getter=FakeFez,
                                     results_path=str(path))
        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert loaded == doc
        assert loaded["verdict"] == "ISA_OK"


class TestCommittedIsa3:
    """Pins gegen den ECHTEN ibm_fez-ISA-Report (skipif, offline)."""

    @pytest.fixture(scope="class")
    def doc(self):
        import os
        if not os.path.exists(isa_mod.ISA_PATH3):
            pytest.skip("pt_ram_q_isa3_report.json noch nicht committed")
        with open(isa_mod.ISA_PATH3, encoding="utf-8") as fh:
            return json.load(fh)

    def test_verdict_and_budget(self, doc):
        assert doc["backend"] == "ibm_fez"
        assert doc["verdict"] == "ISA_OK"
        assert doc["ceiling_check"]["ok"] is True
        assert doc["n_circuits"] == 116
        # Echtes Target (gemessen 2026-09-26): 559 2q total, max 84
        # (Leiter r8 q5) — identisch zur FakeFez-Prognose und im
        # Payload-Prognose-Band (max ~84-96, total ~600-700; total sogar
        # darunter).  Phase-10-Praezedenz: 493 2q / max 84 ueber 90
        # Circuits.
        assert doc["total_two_q"] == 559
        assert doc["max_two_q"] == 84
        assert doc["max_two_q"] <= h3.ISA_2Q_PER_CIRCUIT_MAX
        assert doc["total_two_q"] <= h3.ISA_2Q_TOTAL_MAX

    def test_frozen_md5_and_anchor_depths(self, doc):
        assert doc["run_config_frozen"]["md5"] == \
            "baaca1f6772e07b0847fe436da7e16da"
        pc = doc["per_circuit"]
        # Anker-Tiefen auf dem echten Target: q3 Loschmidt 2 (identisch zur
        # Aer-Basis), q5 14 (Routing), Leiter cz-linear — identisch zur
        # Phase-10-Tiefe trotz neuer Anker (181/467 statt 149/433).
        assert pc["loschmidt_q3_d3_181"]["two_q"] == 2
        assert pc["loschmidt_q5_d5_467"]["two_q"] == 14
        assert [pc[f"ladder_q3_d3_181_r{r}"]["two_q"] for r in (2, 4, 8)] \
            == [4, 8, 16]
        assert [pc[f"ladder_q5_d5_467_r{r}"]["two_q"] for r in (2, 4, 8)] \
            == [24, 44, 84]
        assert pc["ladder_q5_d5_467_r8"]["depth"] == 418

    def test_no_token2_in_module(self):
        src = open(isa_mod.__file__, encoding="utf-8").read()
        assert "IBMQ_TOKEN2" not in src
        assert "TOKEN2" not in src.replace("TOKEN2 wird NIE gelesen", "")

    def test_no_sampler_import(self):
        # Auth-only-Modul: kein QPU-Job hier (der Fez-Job folgt erst nach
        # Freeze B'').
        src = open(isa_mod.__file__, encoding="utf-8").read()
        assert "SamplerV2" not in src
        assert "sampler.run" not in src