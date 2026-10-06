#!/usr/bin/env python3
"""EXPERIMENT 055b (H-055B) Tests — IDEAL-Statevector-Mirror, 0 QPU.

Bindet die gefrorene Kette (R1): Prereg-Pin (SHA-256) + version_regie
(R0 -> R1, kein Metrik-Weakening), Raw ohne Verdict-Felder, R1-
Kontrollen (c_seed Batch-Replay, c_cal_ideal exakt), Eval-Verdicts ex
ante, descriptiver Mirror durch das GEFRORENE 055-Gesetz.
Kein Test schreibt Projekt-Artefakte (053-Lektion).
"""
import json

import pytest

import pt_ram_q_prio48_sv as s

R0_SHA256 = "de15ffb8ff6b5884cac13af2a13567a0" \
            "833c6b2b5c5e459747562c89b4099f84"


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_prereg_pin_holds():
    prereg, dig = s.load_frozen(expected_sha256=s.PREREG_SHA256)
    assert dig == s.PREREG_SHA256
    assert prereg["status"] == "REGISTERED_NOT_MEASURED"
    assert prereg["hypothesis"] == "H-055B"
    assert prereg["experiment"] == "055b-fp48-statevector-ideal"


def test_load_frozen_rejects_foreign_pin():
    with pytest.raises(SystemExit):
        s.load_frozen(expected_sha256="00" * 32)


def test_version_regie_r1_delta():
    prereg, _ = s.load_frozen(expected_sha256=s.PREREG_SHA256)
    vr = prereg["version_regie"]
    assert vr["R0_freeze_sha256"] == R0_SHA256
    assert vr["kein_metrik_weakening"] is True
    assert len(vr["delta_vs_R0"]) == 3
    assert "Sofort-Replay des GESAMTEN Batches" in vr["delta_vs_R0"][0]
    assert "seed_mechanik_lesson" in vr["delta_vs_R0"][1]
    assert "KEINE Veraenderung" in vr["delta_vs_R0"][2]
    assert "NIE evaluiert" in vr["R0_raw_fate"]


def test_prereg_referenzkonstanten_gefroren_am_payload():
    prereg, _ = s.load_frozen(expected_sha256=s.PREREG_SHA256)
    ref = prereg["referenzkonstanten"]
    assert ref["kappa_ceiling"] == 0.81 == s.KAPPA_CEILING
    assert ref["echo_floor_ideal"] == 0.99 == s.ECHO_FLOOR_IDEAL
    assert ref["n_circuits"] == 160
    assert ref["seed_simulator"] == 20261006 == s.SEED_SIMULATOR
    assert ref["arms"] == ["q3_d3", "q5_d5"]
    assert ref["ladder_anchors"] == {"q3": 181, "q5": 467}


def test_raw_has_no_verdict_fields():
    raw = _load(s.RAW_PATH)
    for banned in ("verdict", "kern", "classification", "band_platzierung"):
        assert banned not in raw
    assert raw["status"] == "SV_RAW_FETCHED"
    assert raw["prereg_sha256"] == s.PREREG_SHA256


def test_raw_r1_kontrollen():
    raw = _load(s.RAW_PATH)
    sm = raw["sv_meta"]
    cs = sm["c_seed"]
    assert cs["bit_identisch"] is True
    assert cs["n_diff"] == 0
    assert "batch-replay-im-prozess" in cs["mechanik"]
    ci = sm["c_cal_ideal"]
    assert ci["ok"] is True
    assert ci["cal_2q"] == 1.0 and ci["cal_3q"] == 1.0
    assert sm["active_qubits_max"] == 3


def test_raw_cell_drift_descriptiv():
    raw = _load(s.RAW_PATH)
    cell = raw["sv_meta"]["cell_diagnostik"]
    assert cell["verdict"] in ("ISA_CELL_IDENTICAL", "ISA_CELL_DRIFT")
    assert cell["gate_tally"]["total_two_q_frisch_eq_committed"] is True
    assert cell["gate_tally"]["max_two_q_frisch_eq_committed"] is True
    assert cell["gate_tally"]["total_frisch"] == 830
    assert cell["gate_tally"]["total_committed"] == 830


def test_eval_verdicts_ex_ante():
    e = _load(s.EVAL_PATH)
    assert e["status"] == "SV_EVAL_COMPLETED"
    assert e["prereg_sha256"] == s.PREREG_SHA256
    assert e["verdicts"]["H-055B-1"] == s.V_H1_HELD
    assert e["verdicts"]["H-055B-2"] == s.V_H2_REF
    assert e["verdicts"]["H-055B-3"] == s.V_H3_HELD
    assert e["verdicts"]["H-055B-4"] == s.V_H4_REF
    assert e["verdicts"]["kern"] == s.KERN_MIXED


def test_eval_kontrollen_055b_invalid_praezedenz():
    e = _load(s.EVAL_PATH)
    k = e["kontrollen_055b"]
    assert k["controls_055b_ok"] is True
    assert k["invalid_grund"] is None
    assert k["c_seed"] is True
    assert k["c_cal_ideal"] is True
    assert "INVALID, nicht REFUTED" in k["verdict_rolle"]


def test_eval_law_mirror_descriptiv():
    e = _load(s.EVAL_PATH)
    m = e["mirror_status"]
    assert m["law_verdict"] == "UNDETERMINED"
    assert m["verdict_rolle"].startswith("descriptiv")
    assert m["counts_md5_verified"] is True
    assert m["refit_status"] == "REFIT_OK"
    for t in ("t3_identity_two_ways", "t4_negative_must_not_fire",
              "t5_gate_set_frozen", "t6_mass_conservation"):
        assert m["t_checks"][t] is True


def test_eval_details_zahlen():
    e = _load(s.EVAL_PATH)
    d = e["details"]
    h1 = d["H-055B-1"]
    assert h1["n_kappas"] == 37
    assert h1["kappa_min"] == 1.0
    assert h1["kappa_max"] == 1.0
    assert h1["verdict"] == s.V_H1_HELD
    h3 = d["H-055B-3"]
    assert h3["floor"] == 0.99
    assert h3["kappa_block"]["q3_d3"] == 1.0
    assert h3["kappa_block"]["q5_d5"] == 1.0
    h4 = d["H-055B-4"]
    assert abs(h4["rho_fresh_vs_s1"]["q5_d5"] - 0.09999999999999999) < 1e-12
    assert abs(h4["rho_fresh_vs_s1"]["q3_d3"] - (-0.33333333333333341)) \
        < 1e-12
    assert h4["anchoren"]["q5"] == 0.49999999999999994
    assert h4["anchoren"]["q3"] == 0.8095238095238096


def test_eval_kontext_055_qpu_unangetastet():
    e = _load(s.EVAL_PATH)
    assert e["context"]["055_fez_job_id"] == "db0m71qvog1s73fh15og"
    assert "QUEUED" in e["context"]["055_fez_job_status"]