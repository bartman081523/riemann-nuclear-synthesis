#!/usr/bin/env python3
"""EXPERIMENT 046b (H-V5RB) Tests — Statevector-Identitaet, 0 QPU.

Bindet die gefrorene Kette: Prereg-Pin (SHA-256), Raw ohne Verdicts,
Eval-Verdicts ex ante, Mechanik bit-pin gegen die 035-Konstanten.
Kein Test schreibt Projekt-Artefakte (053-Lektion: monkeypatch-
Redirects nur auf tmp_path).
"""
import json

import pytest

import pt_v5_sv as s


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_prereg_pin_holds():
    prereg, dig = s.load_frozen(expected_sha256=s.PREREG_SHA256)
    assert dig == s.PREREG_SHA256
    assert prereg["status"] == "REGISTERED_NOT_MEASURED"
    assert prereg["hypothesis"] == "H-V5RB"


def test_load_frozen_rejects_foreign_pin():
    with pytest.raises(SystemExit):
        s.load_frozen(expected_sha256="00" * 32)


def test_raw_has_no_verdict_fields():
    raw = _load(s.RAW_PATH)
    for banned in ("verdict", "kern", "classification", "band_platzierung"):
        assert banned not in raw
    assert raw["status"] == "SV_RAW_FETCHED"
    assert raw["prereg_sha256"] == s.PREREG_SHA256
    assert all(isinstance(v, bool) for v in raw["controls"].values())


def test_raw_prereg_binding():
    raw = _load(s.RAW_PATH)
    _, dig = s.load_frozen(expected_sha256=s.PREREG_SHA256)
    assert raw["prereg_sha256"] == dig


def test_logical_statevector_bit_pin():
    """Die logical-Leg neu rechnen (deterministisch) und gegen Raw
    bit-pin (Statevector exakt, kein Sampling)."""
    raw = _load(s.RAW_PATH)
    import numpy as np
    from qiskit.quantum_info import Statevector

    ops = s.v5.build_operators()
    bound = s.v5.ansatz_logical().assign_parameters(s.v5.FEZ_PARAMS)
    sv = Statevector(bound)
    re_log = float(np.real(sv.expectation_value(ops["ops_real"])))
    hd_log = float(np.real(sv.expectation_value(ops["ops_diag"])))
    lg = raw["legs"]["logical"]
    assert lg["re"] == re_log
    assert lg["hd"] == hd_log
    assert lg["bias"] == re_log - hd_log


def test_fakefez_isa_reproduces_frozen_c2_anchor():
    """Die fakefez_isa-Leg trifft die GEFRORENEN 035-Noiseless-Anker
    (C2-Mechanik verbatim) — der H-V5RB-1-Mechanismus selbst."""
    raw = _load(s.RAW_PATH)
    ff = s.v5.noiseless_observables_at(s.v5.FEZ_PARAMS)
    assert abs(ff["re"] - s.v5.NOISELESS_RE) <= s.TOL_ANCHOR
    assert abs(ff["hd"] - s.v5.NOISELESS_RE) <= s.TOL_ANCHOR
    assert abs(ff["im"] - s.v5.NOISELESS_IM) <= s.TOL_ANCHOR
    assert ff["bias"] == 0.0
    lg = raw["legs"]["fakefez_isa"]
    assert abs(ff["re"] - lg["re"]) <= 1e-9
    assert abs(ff["im"] - lg["im"]) <= 1e-9


def test_logical_vs_fakefez_isa_identity():
    """H-V5RB-2-Mechanik: logische ISA-Invarianz unter der 1e-9-Route."""
    raw = _load(s.RAW_PATH)
    lg = raw["legs"]["logical"]
    ff = raw["legs"]["fakefez_isa"]
    assert abs(lg["re"] - ff["re"]) <= s.TOL_ISA_ID
    assert abs(lg["hd"] - ff["hd"]) <= s.TOL_ISA_ID
    assert abs(lg["im"] - ff["im"]) <= s.TOL_ISA_ID
    assert abs(lg["bias"]) <= s.TOL_BIAS
    assert ff["bias"] == 0.0


def test_eval_kern_verdicts_ex_ante():
    e = _load(s.EVAL_PATH)
    assert e["verdicts"]["H-V5RB-1"] == s.V_L1_HELD
    assert e["verdicts"]["H-V5RB-2"] == s.V_L2_HELD
    assert e["verdicts"]["kern"] == s.KERN_HELD
    assert e["controls_ok"] is True
    assert all(e["checks_l1"].values())
    assert all(e["checks_l2"].values())
    for v in e["deviations_logical_vs_fakefez"].values():
        assert v <= s.TOL_ISA_ID


def test_eval_band_platzierung_035():
    """Descriptiver Mirror: die Exakt-Werte liegen IN allen 035-Baendern
    (CONFIRMED-Platzierung, kein Verdict-Erlass)."""
    e = _load(s.EVAL_PATH)
    for leg in ("fakefez_isa", "logical"):
        m = e["qpu_law_mirror"][leg]
        assert m["verdict_qpu_law_mirror"] == \
            "H-V5_CONFIRMED_KINGSTON_NEUTRAL_BAND"
        assert m["detail"]["n_out"] == 0
        assert m["detail"]["bias_class"] == "ok"
        bp = m["band_platzierung"]
        assert all(bp[k]["in_band"] for k in ("re", "hd", "im"))
        assert abs(bp["hd_marge_zur_unkante"] - 0.00327549) < 1e-6


def test_eval_kontext_046_unangetastet():
    e = _load(s.EVAL_PATH)
    assert e["context"]["046_fez_job_id"] == "dauassrojkfs738rrcsg"
    assert "QUEUED" in e["context"]["046_fez_job_status"]


def test_prereg_referenzkonstanten_gefroren_am_payload():
    """Kein ex-post-Zugriff: die 035-Konstanten stehen AM gefrorenen
    Payload und stimmen mit den Modul-Konstanten ueberein."""
    prereg, _ = s.load_frozen(expected_sha256=s.PREREG_SHA256)
    ref = prereg["referenzkonstanten_035"]
    assert ref["noiseless_re"] == s.v5.NOISELESS_RE
    assert ref["noiseless_im"] == s.v5.NOISELESS_IM
    assert ref["fez_params"] == list(s.v5.FEZ_PARAMS)