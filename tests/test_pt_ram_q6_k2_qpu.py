# -*- coding: utf-8 -*-
"""EXPERIMENT 051 (H-RAM-Q-6 Leg D2/D3) — K2-QPU-Modul-Beweise (0 QPU).

Ohne Netz/QPU-Kontakt werden bewiesen: Konstanten-Binding (TOKEN2-only-
Pfad, K2-Pfade, K2-Binding im Raw-Doc), Gate-Versorgung (der committete
K2-Gate deckt ALLE frischen Builder-Namen ab — Kreuzcheck-Precondition),
Kreuzcheck-Mechanik (Gate-ops-Loop greift, Stale-Gate bricht ab,
Totals-Block exakt das h3e.t5-Schema), Raw-Doc-Kontrakt (t5-Felder,
registered_run_config, counts_md5-Kanonik, ABWESEND-Liste) und der
Resume-Vertrag.
"""
import hashlib
import json

import pytest

import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_aer as h3a
import pt_ram_q6_k2 as k2
import pt_ram_q6_k2_qpu as k2q
import pt_ram_q6_kingston as k6
import pt_ram_q6_kingston_isa_stage as stage6
import pt_ram_q6_kingston_qpu as k6q


def _fresh_circuits():
    return h3a.build_hardware_circuit_set(*k2.eval_grid())


def _gate():
    with open(k2q.ISA_GATE_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def test_constants_binding():
    assert k2q.BACKEND_NAME == k2.BACKEND_NAME == k6.BACKEND_NAME == \
        "ibm_kingston"
    assert k2q.TRANSPILE_SEED == h3a.TRANSPILE_SEED == 7
    assert k2q.JOB_ID_PATH == k2.JOB_ID_PATH
    assert k2q.RAW_PATH == k2.RAW_PATH
    assert k2q.ISA_GATE_PATH == k2.ISA_GATE_PATH
    # count_2q ist DIE committete D1-Funktion (keine Kopie)
    assert k2q.count_2q is stage6.count_2q


def test_gate_names_cover_fresh_builder():
    """Kreuzcheck-Precondition: jeder frische Circuit-Name hat einen
    Gate-Eintrag (sonst KeyError im isa_circuits)."""
    gate = _gate()
    assert k6.validate_isa_gate(gate) is True
    names = {c["name"] for c in _fresh_circuits()}
    assert names == set(gate["per_circuit_two_q"])
    # Das K2-Gate ist nicht das D1-Gate (anderes Experiment-Binding)
    assert gate["experiment"] == k2.EXPERIMENT
    assert gate["prereg_md5"] == k2.PREREG_MD5
    assert gate["verdict"] == "ISA_OK"


def _fake_pm_factory(gate, names, diverge_at=None):
    """Passmanager-Stellvertreter: transpiliert Zelle-fuer-Zelle die
    Gate-ops nach (oder divergiert ab Index diverge_at).  pm.run erhaelt
    NACKTE QuantumCircuits in Builder-Reihenfolge — Namen ueber `names`
    (gleiche Ordnung)."""
    class _FakeTC:
        def __init__(self, ops):
            self._ops = ops

        def count_ops(self):
            return dict(self._ops)

    class _FakePM:
        def run(self, qcs):
            out = []
            for i, _qc in enumerate(qcs):
                ops = dict(gate["per_circuit_two_q"][names[i]]["ops"])
                if diverge_at is not None and i == diverge_at:
                    ops["rz"] = ops.get("rz", 0) + 1
                out.append(_FakeTC(ops))
            return out
    return _FakePM


def test_isa_circuits_kreuzcheck_greift_und_totals_t5_schema(monkeypatch):
    gate = json.loads(json.dumps(_gate()))
    import pt_ram_q6_k2_qpu as mod
    circuits = _fresh_circuits()
    names = [c["name"] for c in circuits]
    monkeypatch.setattr(
        mod, "generate_preset_pass_manager",
        lambda backend, **kw: _fake_pm_factory(gate, names)())
    tci, totals = mod.isa_circuits(None, circuits)
    assert totals == {"optimization_level": 3, "seed_transpiler": 7,
                      "isa_2q_total": gate["total_two_q"],
                      "isa_2q_max": gate["max_two_q"]}
    assert len(tci) == 116
    # t5-Kontrakt-Shape: genau diese 4 Schluessel
    assert set(totals) == {"optimization_level", "seed_transpiler",
                           "isa_2q_total", "isa_2q_max"}


def test_isa_circuits_abbrechen_bei_stale_gate(monkeypatch, tmp_path):
    """Ein manipulated Gate (n_2q um 1 erhoeht) muss den Kreuzcheck VOR
    QPU-Kontakt brechen."""
    gate = json.loads(json.dumps(_gate()))
    first_name = sorted(gate["per_circuit_two_q"])[0]
    gate["per_circuit_two_q"][first_name]["n_2q"] += 1
    broken = tmp_path / "stale_gate.json"
    broken.write_text(json.dumps(gate), encoding="utf-8")
    import pt_ram_q6_k2_qpu as mod
    circuits = _fresh_circuits()
    names = [c["name"] for c in circuits]
    # Der lokale Transpile reproduziert das UNTAMPERTE Gate; das
    # manipulierte Gate-Dokument muss dann am n_2q-Vergleich kippen.
    monkeypatch.setattr(
        mod, "generate_preset_pass_manager",
        lambda backend, **kw: _fake_pm_factory(
            json.loads(json.dumps(_gate())), names)())
    with pytest.raises(AssertionError, match="n_2q divergiert"):
        mod.isa_circuits(None, _fresh_circuits(), isa_gate=str(broken))


class _FakeDatum:
    def get_counts(self):
        return {"00": 8191, "11": 1}


class _FakeSlice:
    def __init__(self):
        self.c = _FakeDatum()


class _FakeResult:
    def __getitem__(self, i):
        e = type("E", (), {})()
        e.data = _FakeSlice()
        return e


def test_fetch_raw_contract():
    circuits = _fresh_circuits()
    totals = {"optimization_level": 3, "seed_transpiler": 7,
              "isa_2q_total": 559, "isa_2q_max": 84}
    doc = k2q.fetch_raw(_FakeResult(), circuits,
                        {"job_id": "testjob", "backend": "ibm_kingston",
                         "shots_per_circuit": int(h3.SHOTS)},
                        "ibm_kingston", totals)
    # Bindung an K2
    assert doc["experiment"] == k2.EXPERIMENT
    assert doc["hypothesis"] == k2.HYPOTHESIS
    assert doc["leg"] == k2.LEG
    assert doc["status"] == "QPU_RAW_FETCHED"
    assert doc["n_circuits"] == 116
    assert doc["registered_run_config"] == \
        k2.load_frozen_prereg()["hardware_parameters"]["run_config"]
    assert set(doc["registered_run_config"]) >= {
        "dynamical_decoupling", "optimization_level", "resilience"}
    # t5-Schema: transpile-Block EXAKT aus totals
    assert doc["transpile"] == totals
    # Zeilen: name/kind/arm/set/P/rep/r + counts
    row = doc["counts"][0]
    assert {"name", "kind", "arm", "set", "P", "rep", "r", "shots_actual",
            "counts"} <= set(row)
    assert row["shots_actual"] == 8192
    assert all(e["shots_actual"] == 8192 for e in doc["counts"])
    kinds = {e["kind"] for e in doc["counts"]}
    assert {"structure", "kalibrier_structure", "loschmidt",
            "kalibrier_loschmidt"} <= kinds
    # counts_md5 = md5 ueber kanonisch serialisierte Counts-Liste
    payload = json.dumps([e["counts"] for e in doc["counts"]],
                         sort_keys=True, separators=(",", ":")).encode()
    assert doc["counts_md5"] == hashlib.md5(payload).hexdigest()
    assert k2q.counts_md5([e["counts"] for e in doc["counts"]]) == \
        doc["counts_md5"]
    # ABSICHTLICH ABWESEND (kein Verdict-Kanal vor dem Freeze-Auswertung):
    for banned in ("kappa", "ratio", "gamma", "verdict", "band",
                   "kappa_hat", "res_v3"):
        assert banned not in doc
    # counts_md5-Impl identisch zur D1-Implementierung
    assert k2q.counts_md5([{"00": 3, "11": 2}]) == \
        k6q.counts_md5([{"00": 3, "11": 2}])


def test_resume_vertrag_raw_vorhanden(tmp_path):
    """Existiert das Raw, geschieht NICHTS — kein Backend, kein Submit."""
    fake_raw = {"status": "QPU_RAW_FETCHED", "experiment": k2.EXPERIMENT}
    path = tmp_path / "raw.json"
    path.write_text(json.dumps(fake_raw), encoding="utf-8")
    # Beweis: ohne Backend-Getter darf der Resume-Pfad nicht touchieren:
    doc2 = k2q.run_qpu_job(results_path=str(path),
                           backend_getter=lambda: pytest.fail(
                               "Backend darf im Resume-Pfad nicht gebaut "
                               "werden"))
    assert doc2 == fake_raw


def test_counts_md5_kanonische_serialisierung():
    payload = json.dumps([{"00": 8191, "11": 1}], sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    assert k2q.counts_md5([{"00": 8191, "11": 1}]) == \
        hashlib.md5(payload).hexdigest()