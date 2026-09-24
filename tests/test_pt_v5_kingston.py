"""EXPERIMENT 035 — V5 Kingston-Drift-Test (H-V5): Tests.

OFFLINE (FakeFez + Aer lokal, kein Provider/Token-Wert — Guard). Prereg
(pt_v5_kingston_prereg.json, md5) wird VOR dem Job gefroren; Baender,
Schwellen und Verdict-Tabelle stammen aus dem Plan (VOR der Messung
fixiert) und sind im Payload committet.
"""

import json
import math
import os
import re
import sys
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_v5_kingston as vk


# === Theorem-Identitaet (C1) ===

def test_operators_theorem_identity():
    ops = vk.build_operators()
    # Re(H_PT) ≡ H_diag exakt (Matrix- und Pauli-Ebene)
    assert np.array_equal(ops["H_real"], ops["H_diag"])
    assert ops["ops_real"].simplify() == ops["ops_diag"].simplify()
    terms = [(str(p), round(float(np.real(c)), 9)) for p, c in
             zip(ops["ops_real"].paulis, ops["ops_real"].coeffs)]
    assert len(terms) == 4
    assert terms == [("II", 3.341205737), ("IZ", -0.499276914),
                     ("ZI", -0.994632147), ("ZZ", 0.152703324)]
    # Noiseless bias exakt 0 (Konsequenz der Identitaet)
    nl = vk.noiseless_observables_at(vk.FEZ_PARAMS)
    assert nl["bias"] == 0.0


# === Noiseless-Anker + Spektrum-Trennung (C2/C3) ===

def test_noiseless_anchors_and_spectrum_split():
    nl = vk.noiseless_observables_at(vk.FEZ_PARAMS)
    assert abs(nl["re"] - vk.NOISELESS_RE) <= 1e-9
    assert nl["hd"] == nl["re"]  # Theorem-Identitaet
    assert abs(nl["im"] - vk.NOISELESS_IM) <= 1e-9
    # Boden von Re(H_PT) = H_diag: exakt min(E_DIAG) = 2.0
    assert vk.noiseless_ground_energy() == vk.NOISELESS_E0_DIAG == 2.0
    # H1-Modellziel (min Re(spec(H_PT)), nicht-hermitisch) committet
    assert abs(vk.noiseless_e0_h1() - vk.NOISELESS_E0_H1) <= 1e-9
    assert vk.NOISELESS_E0_H1 == 2.0018501462716807


# === Fez-Anker (param-matched Referenz) ===

def test_fez_anchors_committed():
    assert vk.FEZ_RUN1["job_id"] == "d9fidihhtsac739fg3n0"
    assert vk.FEZ_RUN1["re"] == 2.145828476862593
    assert vk.FEZ_RUN1["hd"] == 2.1577507852679036
    assert vk.FEZ_RUN1["im"] == 0.009395361635620568
    assert vk.FEZ_RUN1["bias"] == -0.011922308405310833
    assert vk.FEZ_RUN1["e0_loop"] == 2.1398203106629032
    assert vk.FEZ_RUN2["job_id"] == "d9fjbraneu4c739pmaqg"
    assert vk.FEZ_RUN2["re"] == 2.17247246569962
    # Spread (param-mismatched, konservativ)
    assert math.isclose(vk.FEZ_SPREAD["re"], 0.026643988837027, rel_tol=1e-9)
    assert math.isclose(vk.FEZ_SPREAD["hd"], 0.023245434777046, rel_tol=1e-9)
    assert math.isclose(vk.FEZ_SPREAD["im"], 0.020637380492818, rel_tol=1e-9)
    # VQE-Loop-Wert ist NICHT der 3-Pub-Re-Wert (registrierte Trennung)
    assert vk.FEZ_RUN1["e0_loop"] != vk.FEZ_RUN1["re"]


# === ISA (FakeFez-Anker gefroren, Online-Akzeptanz) ===

def test_isa_counts_frozen_and_acceptance():
    cnt = vk.isa_gate_counts(vk.isa_ansatz_fakefez())
    assert cnt == {"two_q": 1, "one_q": 18, "names": ["cz"], "depth": 11}
    assert vk.isa_accept_online(cnt) is True
    # Online-Varianten: ecr/cx akzeptiert, Verletzungen abgelehnt
    assert vk.isa_accept_online({"two_q": 1, "names": ["ecr"],
                                 "depth": 11}) is True
    assert vk.isa_accept_online({"two_q": 2, "names": ["cz"],
                                 "depth": 11}) is False
    assert vk.isa_accept_online({"two_q": 1, "names": ["cz"],
                                 "depth": 50}) is False
    assert vk.isa_accept_online({"two_q": 1, "names": ["rz"],
                                 "depth": 11}) is False


# === STRESS-Baseline (C5) ===

def test_stress_baseline_frozen():
    base = vk.stress_baseline()
    assert abs(base["shift"]["re"] - vk.STRESS_SHIFT_RE) <= 1e-6
    assert abs(base["shift"]["hd"] - vk.STRESS_SHIFT_RE) <= 1e-6
    assert abs(base["shift"]["im"] - vk.STRESS_SHIFT_IM) <= 1e-6
    assert base["shift"]["bias"] == 0.0  # identische Operatoren
    assert abs(base["noiseless"]["re"] - vk.NOISELESS_RE) <= 1e-6
    assert abs(base["stress"]["re"] - 2.145755961322) <= 1e-6
    # STRESS-Shift reproduziert den Fez-Re-Drift (+0.008048) fast exakt
    fez_re_drift = vk.FEZ_RUN1["re"] - vk.NOISELESS_RE
    assert abs(base["shift"]["re"] - fez_re_drift) <= 1e-3


# === Shot-SE (exakte Varianz aus der STRESS-Dichtematrix) ===

def test_shot_se_analytic_exact_and_deterministic():
    se = vk.shot_se()
    assert set(se) == {"re", "hd", "im", "bias"}
    assert se == vk.shot_se()  # deterministisch + exakt (kein sd-Schaetzer)
    # Frozen-Konstanten exakt reproduziert (C6-Kern)
    f = vk.shot_se_frozen()
    assert f == {"re": vk.SE_RE, "hd": vk.SE_HD,
                 "im": vk.SE_IM, "bias": vk.SE_BIAS}
    assert se == f
    # Struktur: re/hd identische Operatoren (C1) -> SE identisch;
    # bias-Kontrast hypot (zwei unabhaengige Pubs)
    assert vk.SE_RE == vk.SE_HD
    assert vk.SE_BIAS == math.hypot(vk.SE_RE, vk.SE_HD)
    # Groessenordnung: Var(Re)=0.156 -> SE ~ 4.4e-3; Im ~ 3.2e-4
    assert 0.001 < vk.SE_RE < 0.05
    assert 0.0001 < vk.SE_IM < 0.001
    # Formel aus der Dichtematrix reproduziert (rel 1e-12)
    rho = vk.noisy_density_matrix_stress()
    ops = vk.build_operators()
    O = ops["ops_real"].to_matrix()
    exp = float(np.real(np.trace(rho @ O)))
    var = float(np.real(np.trace(rho @ O @ O)) - exp * exp)
    assert math.isclose(math.sqrt(var) / math.sqrt(vk.SHOTS), vk.SE_RE,
                        rel_tol=1e-12)
    # Cross-Check Full-Path: reduziertes <Re> trifft den STRESS-Anker
    assert abs(exp - (vk.NOISELESS_RE + vk.STRESS_SHIFT_RE)) <= 1e-9


# === Baender (registrierte Ableitungsformel) ===

def test_bands_derivation_formula():
    b = vk.bands()
    for key, anchor in (("re", vk.FEZ_RUN1["re"]),
                        ("hd", vk.FEZ_RUN1["hd"]),
                        ("im", vk.FEZ_RUN1["im"])):
        m = max(abs(vk.STRESS_SHIFT_RE if key != "im" else vk.STRESS_SHIFT_IM)
                + vk.SHOT_SIGMA_FACTOR * vk.shot_se_frozen()[key],
                vk.FEZ_SPREAD[key])
        assert math.isclose((b[key][0] + b[key][1]) / 2, anchor, rel_tol=1e-12)
        assert math.isclose((b[key][1] - b[key][0]) / 2, m, rel_tol=1e-12)
        # mit den exakten SE sind ALLE drei Baender Fez-Spread-dominiert:
        # die Baender sind genau die Spanne der beiden Fez-Runs
        assert m == vk.FEZ_SPREAD[key]
        assert math.isclose(b[key][1], vk.FEZ_RUN2[key], rel_tol=1e-12)
    # numerische Spot-Checks (Spread-dominierte Baender)
    assert math.isclose(b["re"][0], 2.119184488025566, rel_tol=1e-7)
    assert math.isclose(b["re"][1], 2.172472465699620, rel_tol=1e-7)
    assert math.isclose(b["hd"][0], 2.134505350490858, rel_tol=1e-7)
    assert math.isclose(b["im"][0], -0.011242018857197, rel_tol=1e-7)
    # untere Im-Kante unter 0 (registriert, dokumentiert)
    assert b["im"][0] < 0.0
    # Sanity: noiseless-Anker und BEIDE Fez-Runs liegen in den Baendern
    # (Run 2 exakt an der oberen Kante — inclusive, s. evaluate)
    for key, vals in (("re", (vk.NOISELESS_RE, vk.FEZ_RUN1["re"],
                              vk.FEZ_RUN2["re"])),
                      ("hd", (vk.NOISELESS_RE, vk.FEZ_RUN1["hd"],
                              vk.FEZ_RUN2["hd"])),
                      ("im", (vk.NOISELESS_IM, vk.FEZ_RUN1["im"],
                              vk.FEZ_RUN2["im"]))):
        for v in vals:
            assert b[key][0] <= v <= b[key][1]


# === Verdict (registrierte Entscheidungstabelle, synthetisch) ===

def _anchor_meas():
    return {"re": vk.FEZ_RUN1["re"], "hd": vk.FEZ_RUN1["hd"],
            "im": vk.FEZ_RUN1["im"], "bias": vk.FEZ_RUN1["bias"]}


def test_evaluate_synthetic_verdicts():
    bands = vk.bands()
    # CONFIRMED: alle drei im Band (Anker ist Zentrum), |bias| < 0.05
    v, d = vk.evaluate(_anchor_meas(), bands, controls_ok=True)
    assert v == vk.VERDICT_MAP["CONFIRMED"]
    assert d["n_out"] == 0 and d["bias_class"] == "ok"
    # BIAS_MITTEL: in-band, 0.05 <= |bias| < 0.15
    v, d = vk.evaluate(dict(_anchor_meas(), bias=0.08), bands, True)
    assert v == vk.VERDICT_MAP["BIAS_MITTEL"] and d["bias_class"] == "mittel"
    # MITTEL: genau 1 Observable aussen, bias ok
    v, d = vk.evaluate(dict(_anchor_meas(), re=bands["re"][1] + 0.05),
                       bands, True)
    assert v == vk.VERDICT_MAP["MITTEL"] and d["n_out"] == 1
    # REFUTED: 2 Observablen aussen
    m = dict(_anchor_meas(), re=bands["re"][1] + 0.05,
             hd=bands["hd"][0] - 0.05)
    assert vk.evaluate(m, bands, True)[0] == vk.VERDICT_MAP["REFUTED"]
    # REFUTED: 1 aussen + bias >= 0.05 (zwei Rand-Signale)
    m = dict(_anchor_meas(), re=bands["re"][1] + 0.05, bias=0.06)
    assert vk.evaluate(m, bands, True)[0] == vk.VERDICT_MAP["REFUTED"]
    # REFUTED: |bias| >= 0.15 allein, alle Observablen in-band
    assert vk.evaluate(dict(_anchor_meas(), bias=0.2), bands, True)[0] == \
        vk.VERDICT_MAP["REFUTED"]
    # Bandgrenzen: strikt (< 0.05 -> ok, 0.05 -> mittel, 0.15 -> hoch)
    assert vk.evaluate(dict(_anchor_meas(), bias=0.05), bands, True)[1]\
        ["bias_class"] == "mittel"
    assert vk.evaluate(dict(_anchor_meas(), bias=0.15), bands, True)[1]\
        ["bias_class"] == "hoch"
    # Inclusive-Bandkante: ein Wert exakt an der oberen Kante (Fez Run 2)
    # ist IM Band (Spread-Baender haben Run 2 an der Kante)
    edge = dict(_anchor_meas(), re=bands["re"][1], hd=bands["hd"][1],
                im=bands["im"][1])
    assert vk.evaluate(edge, bands, True)[0] == vk.VERDICT_MAP["CONFIRMED"]
    # INVALID dominiert alles
    v, d = vk.evaluate(_anchor_meas(), bands, controls_ok=False)
    assert v == vk.VERDICT_MAP["INVALID"] and d["flags"] is None


# === Prereg ===

def test_prereg_payload_fields():
    p = vk.build_prereg_payload()
    assert p["experiment"] == "035-ququint-v5-kingston-drift"
    assert p["hypothesis"] == "H-V5"
    assert "Bias-Regime" in p["steelman"]
    rb = p["registered_before"]
    assert "EIN Job erzwingt Param-Transfer" in rb["param_transfer"]
    assert "identischer Observablen" in rb["theorem_identity"]
    assert "2026-06-08" in rb["threshold_reuse"]
    assert "COBYLA-Lokalminima" in rb["vqd_honest_re_registration"]
    assert "Faktor" in rb["im_bias_descriptive"]
    assert "VQE-Loop-Wert" in rb["e0_definition"]
    assert "2.0018501462716807" in rb["spectrum_split"]
    assert "min(E_DIAG) = 2.0" in rb["spectrum_split"]
    assert "Anker-relativ" in rb["spectrum_split"]
    assert "M_obs" in rb["band_derivation"]
    assert "N(exakt, precision)-Gauss-Noise" in rb["band_derivation"]
    assert "Fez-Spread-dominiert" in rb["shot_se_analytic"]
    assert "A- Kandidat, NICHT A" in rb["grade_expectation"]
    a = p["anchors"]
    assert a["fez_run1"]["job_id"] == "d9fidihhtsac739fg3n0"
    assert a["fez_run1"]["re"] == 2.145828476862593
    assert a["noiseless"]["e0_h1"] == 2.0018501462716807
    assert a["shot_se"]["re"] == vk.SE_RE
    t = p["thresholds"]
    assert t["bias_confirmed"] == 0.05 and t["bias_refuted"] == 0.15
    assert t["shots"] == 8192 and t["band_shot_sigma"] == 2.0
    assert t["stress"] == {"p1": 3e-4, "ro": 1e-2, "ratio": 10.0}
    assert "n_se_seeds" not in t
    assert p["bands"] == vk.bands()
    c = p["controls"]
    assert "C1_theorem_identity" in c and "C5_stress_baseline" in c
    assert "2.145755961322" in c["C6_reduction_exact"]
    assert c["gate"] == "Kontrollfehler -> EVALUATION_INVALID"
    assert len(p["verdict_map"]) == 5
    assert len(p["decision_table"]) == 5
    assert p["protocol"]["resilience_level"] == 1
    assert p["protocol"]["dynamical_decoupling"] == "XX"
    assert p["protocol"]["one_job"] is True
    assert len(p["protocol"]["pubs"]) == 3
    assert p["qpu"]["backend"] == "ibm_kingston"
    assert "NIEMALS" in p["qpu"]["token"]
    assert p["qpu"]["quota_check_first"] is True
    assert p["seeds"] == {"transpiler": 7}


def test_prereg_md5_freeze_verify_tamper(tmp_path):
    payload = vk.build_prereg_payload()
    doc = vk.freeze_prereg(payload, path=str(tmp_path / "prereg.json"))
    assert vk.verify_prereg_md5(doc)
    tampered = dict(doc)
    tampered["thresholds"] = dict(tampered["thresholds"])
    tampered["thresholds"]["bias_confirmed"] = 0.5  # Schwellen-Manipulation
    assert not vk.verify_prereg_md5(tampered)
    path = str(tmp_path / "prereg.json")
    reloaded = vk.load_frozen_prereg(path)
    assert reloaded["md5"] == doc["md5"]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(tampered, fh)
    try:
        vk.load_frozen_prereg(path)
        raise AssertionError("manipulierter Prereg wurde akzeptiert")
    except ValueError:
        pass


# === Quota-Pruefung (kein Token-Echo) ===

class _FakeBackend:
    def __init__(self, status="online", operational=True, pending=0):
        self._status = SimpleNamespace(status=status, operational=operational,
                                       pending_jobs=pending)

    def status(self):
        return self._status


class _FakeJob:
    def __init__(self, state):
        self._state = state

    def status(self):
        return self._state


class _FakeService:
    def __init__(self, token=None, instance=None, channel=None):
        self.captured = {"token": token, "instance": instance,
                         "channel": channel}

    def backend(self, name):
        assert name == "ibm_kingston"
        return _FakeBackend()

    def jobs(self, backend_name=None, limit=None):
        return [_FakeJob("DONE"), _FakeJob("RUNNING")]


def test_quota_check_structure_and_no_token_echo(monkeypatch):
    monkeypatch.setattr(vk, "load_token", lambda name: "GEHEIM-TOKEN")
    monkeypatch.setattr(vk, "QiskitRuntimeService", _FakeService)
    info = vk.run_quota_check()
    assert info["backend"] == "ibm_kingston"
    assert info["operational"] is True and info["status"] == "online"
    assert info["pending_jobs"] == 0
    assert info["recent_jobs"] == 2 and info["active_recent"] == 1
    dumped = json.dumps(info)
    assert "GEHEIM-TOKEN" not in dumped
    # Service-Fabrik reicht den Token NUR an den Service durch
    vk.run_quota_check(service=None)
    # (gezaehlt im naechsten Test via capturer)


def test_service_factory_passes_token_only_to_service(monkeypatch):
    captured = {}

    class _SpyService(_FakeService):
        def __init__(self, token=None, instance=None, channel=None):
            captured["token"] = token
            captured["instance"] = instance
            captured["channel"] = channel

    monkeypatch.setattr(vk, "load_token", lambda name: "GEHEIM-TOKEN")
    monkeypatch.setattr(vk, "QiskitRuntimeService", _SpyService)
    vk.run_quota_check()
    assert captured == {"token": "GEHEIM-TOKEN",
                        "instance": "open-instance",
                        "channel": "ibm_quantum_platform"}


# === EIN Job (Fake-Estimator) ===

class _FakePubResult:
    def __init__(self, evs):
        self.data = SimpleNamespace(evs=evs)


class _FakeResult(list):
    pass


class _FakeRuntimeJob:
    def __init__(self, evs):
        self._res = _FakeResult([_FakePubResult(e) for e in evs])

    def result(self):
        return self._res

    def job_id(self):
        return "fake-job-v5-1"


class _FakeEstimator:
    calls = []

    def __init__(self, mode=None):
        self.mode = mode
        self.options = SimpleNamespace(
            resilience_level=None,
            dynamical_decoupling=SimpleNamespace(enable=None,
                                                 sequence_type=None),
            default_shots=None)
        _FakeEstimator.calls.append(self)

    def run(self, pubs):
        _FakeEstimator.calls[-1].pubs = pubs
        return _FakeRuntimeJob([2.150, 2.160, 0.010])


def test_run_kingston_job_one_run_three_pubs(monkeypatch):
    _FakeEstimator.calls = []
    monkeypatch.setattr(vk, "Estimator", _FakeEstimator)
    # FakeBackend hat kein Transpile-Target -> ISA offline (FakeFez-Anker)
    monkeypatch.setattr(vk, "isa_ansatz_for",
                        lambda backend: vk.isa_ansatz_fakefez())
    run = vk.run_kingston_job(service=_FakeService())
    # EIN Aufruf, EIN Job, drei Pubs
    assert len(_FakeEstimator.calls) == 1
    est = _FakeEstimator.calls[0]
    assert len(est.pubs) == 3
    assert est.options.resilience_level == 1
    assert est.options.dynamical_decoupling.enable is True
    assert est.options.dynamical_decoupling.sequence_type == "XX"
    assert est.options.default_shots == vk.SHOTS
    assert run["job_id"] == "fake-job-v5-1"
    assert run["meas"] == {"re": 2.150, "hd": 2.160, "im": 0.010,
                           "bias": 2.150 - 2.160}
    assert run["isa"]["two_q"] == 1
    assert run["isa_accept"] is True
    # Pubs sind (bound_circuit, operator)-Paare mit gebundenen Parametern
    for circ, op in est.pubs:
        assert circ.num_parameters == 0


# === Offline-Guard (kein Token-Wert im Quelltext) ===

def test_offline_guard_no_token_value():
    src = open(vk.__file__, encoding="utf-8").read()
    # Nur der Token-NAME (IBMQ_TOKEN2) ist registriert — jedes Vorkommen
    # von "IBMQ_TOKEN" ist der TOKEN2-Name (kein TOKEN1 im Kingston-Pfad);
    # ein Token-WERT niemals
    assert src.count("IBMQ_TOKEN2") == 2  # TOKEN_NAME + Prereg-QPU-Text
    assert src.count("IBMQ_TOKEN") == src.count("IBMQ_TOKEN2")
    assert vk.TOKEN_NAME == "IBMQ_TOKEN2"
    assert "load_token" in src
    assert re.search(r"\b[0-9a-fA-F]{40,}\b", src) is None
    assert "apikey" not in src.lower()