"""EXPERIMENT 033 — α-Trennungstest (H-ALPHA): Tests.

OFFLINE (FakeFez + Aer lokal, kein Provider/Token — Guard). Prereg
(pt_alpha_prereg.json, md5) wird VOR der Auswertung gefroren; die Bänder
stammen aus dem Plan (VOR dem Smoke fixiert) und sind im Payload committet.
"""

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_alpha_separation as al
import pt_ququint_crossover as cx
import pt_ququint_ibmq_aer as aq


# === ISA-Transpilation (FakeFez, deterministisch seed 7) ===

def test_isa_batch_counts_frozen():
    _isa, report = al.isa_transpiled_batch()
    assert len(_isa) == 12
    assert tuple(report["per_circuit"].keys()) == al.CIRCUIT_ORDER
    c = report["phi_d_two_q"]
    # Registrierte Akzeptanz um den echten Fez-Wert 81 (Phase 3c)
    assert al.ISA_COUNT_ACCEPT[0] <= c <= al.ISA_COUNT_ACCEPT[1]
    assert c == 79  # frozen (seed_transpiler=7, deterministisch)
    assert report["two_q_gate_names"] == ("cz",)
    assert report["total_two_q"] == sum(
        r["two_q"] for r in report["per_circuit"].values())
    # sep_C: Praep ohne 2q-Gates (wie Phase 2/3)
    for k in ("sep_C_0", "sep_C_1", "sep_C_2", "sep_C_3", "sep_C_4"):
        assert report["per_circuit"][k]["two_q"] == 0
    # Reduktion: alle Circuits auf 6 aktive Qubits, 6 Clbits
    for r in report["per_circuit"].values():
        assert len(r["active"]) == 6
        assert r["n_clbits"] == 6


def test_reduce_to_active_preserves_structure():
    isa, _rep = al.isa_transpiled_batch()
    phi_d = isa[1]
    red = al.reduce_to_active(phi_d)
    assert red.num_qubits == 6
    assert red.num_clbits == phi_d.num_clbits
    ops_orig = {}
    ops_red = {}
    for inst in phi_d.data:
        if inst.operation.name != "barrier":
            ops_orig[inst.operation.name] = ops_orig.get(inst.operation.name, 0) + 1
    for inst in red.data:
        ops_red[inst.operation.name] = ops_red.get(inst.operation.name, 0) + 1
    assert ops_red == ops_orig  # keine Barriers im ISA-Output uebrig


def test_reduce_to_active_keeps_measure_mapping():
    # Noiseless-Anker: das reduzierte phi_D liefert exakt V = 1 -> das
    # (Qubit, Clbit)-Mess-Mapping ist intakt, 64-Bin-Semantik unveraendert.
    isa, _rep = al.isa_transpiled_batch()
    red = al.reduce_to_active(isa[1])
    sim = aq.AerSimulator(method="density_matrix")
    result = sim.run(red, shots=4096, seed_simulator=7).result()
    vec = aq._counts64_to_vec(result.get_counts(0))
    w = aq.witness_from_counts(vec, n_boot=200, seed=9871)
    assert w["v_hat"] >= 0.995
    assert w["margin"] >= 0.0


# === STRESS-Noise-Modell (ISA-Konvention: cz statt cx) ===

def test_build_isa_noise_model_conventions():
    nm = al.build_isa_noise_model(3e-4, ro=1e-2, ratio=10.0)
    assert "cz" in nm.basis_gates and "cx" in nm.basis_gates
    # p1=0 -> Readout-only (keine Quantenfehler)
    nm0 = al.build_isa_noise_model(0.0, ro=1e-2)
    q0 = [e for e in nm0.to_dict().get("errors", []) if e["type"] == "qerror"]
    assert q0 == []
    q = [e for e in nm.to_dict().get("errors", []) if e["type"] == "qerror"]
    ops = {tuple(e.get("operations", [])) for e in q}
    assert ("rz",) in ops and ("sx",) in ops and ("x",) in ops
    # 2q-Fehler haengt am cz-Operator (ratio*p1 = 3e-3, 16-Elementige
    # Depolarizing-Verteilung = 2q-Kanal)
    cz_errs = [e for e in q if e.get("operations") == ["cz"]]
    assert len(cz_errs) == 1
    assert len(cz_errs[0]["probabilities"]) == 16
    # Aer-Konvention: depolarizing_error(lam, 2) -> p_max = 1 - lam*15/16
    assert math.isclose(max(cz_errs[0]["probabilities"]),
                        1.0 - 3e-3 * 15 / 16, rel_tol=1e-9)
    for bad in (-1e-3,):
        try:
            al.build_isa_noise_model(bad)
            raise AssertionError("negatives p1 akzeptiert")
        except ValueError:
            pass
    try:
        al.build_isa_noise_model(0.0, ro=0.6)
        raise AssertionError("ro > 0.5 akzeptiert")
    except ValueError:
        pass


def test_run_isa_batch_stress_smoke():
    res = al.run_isa_batch(3e-4)
    assert res["p1"] == 3e-4 and res["ro"] == 1e-2 and res["ratio"] == 10.0
    assert res["n_shots"] == 8192 and res["seed"] == 42
    # STRESS-Level: deutlich unter noiseless (0.8), klar ueber Uniform-Boden
    assert 0.3 < res["phi"]["margin"] < 0.65
    assert 0.6 < res["phi"]["v_hat"] < 0.85
    assert res["phi"]["se"] < 0.05
    assert res["confound_max_diff"] <= al.CONFOUND_LIMIT
    # Registrierte sep-Kontrolle (STRESS-Level): Witness-Null-Trennung.
    # sep_D v_hat faellt unter den 0.2-Boden (58 cz) -> sep margin > 0 ist
    # NICHT registrierbar (Smoke vor Freeze; QPU-Gate der Phase 3).
    assert res["phi"]["v_hat"] > res["sep"]["v_hat"] + 0.1
    # Determinismus: identische Seeds -> identisches v_hat
    res2 = al.run_isa_batch(3e-4)
    assert abs(res2["phi"]["v_hat"] - res["phi"]["v_hat"]) <= 1e-12


# === alpha / kappa_eff / Verdict ===

def test_alpha_from_kappa_arithmetic():
    # V4-Anker: kappa*=62.26124 auf c=45 -> alpha ≈ 1.7987 ≈ 81/45
    assert math.isclose(
        al.alpha_from_kappa(al.V4_KAPPA_STAR_COMMITTED, 45), 1.7987,
        rel_tol=1e-3)
    # Punktvorhersagen: kappa_eff = 10c/13 -> alpha exakt 1; 18c/13 -> 1.8
    assert math.isclose(al.alpha_from_kappa(10.0 * 79 / 13.0, 79), 1.0,
                        rel_tol=1e-12)
    assert math.isclose(al.alpha_from_kappa(18.0 * 79 / 13.0, 79), 1.8,
                        rel_tol=1e-12)
    pts = al.kappa_eff_points(79)
    assert math.isclose(pts["H-A"], 10.0 * 79 / 13.0, rel_tol=1e-12)
    assert math.isclose(pts["H-B"], 18.0 * 79 / 13.0, rel_tol=1e-12)


def test_verdict_alpha_and_kappa_bands():
    ha = al.kappa_eff_band(79, "H-A")
    hb = al.kappa_eff_band(79, "H-B")
    assert math.isclose(ha[0], 0.9 * 10.0 * 79 / 13.0, rel_tol=1e-12)
    assert math.isclose(ha[1], 1.1 * 10.0 * 79 / 13.0, rel_tol=1e-12)
    assert math.isclose(hb[0], 0.9 * 18.0 * 79 / 13.0, rel_tol=1e-12)
    assert math.isclose(hb[1], 1.1 * 18.0 * 79 / 13.0, rel_tol=1e-12)
    va = al.verdict_alpha
    assert va(1.0) == al.VERDICT_MAP["H-ALPHA-A"]
    assert va(0.9) == al.VERDICT_MAP["H-ALPHA-A"]
    assert va(1.1) == al.VERDICT_MAP["H-ALPHA-A"]
    assert va(0.89) == al.VERDICT_MAP["H-ALPHA-INKONKLUSIV"]
    assert va(1.8) == al.VERDICT_MAP["H-ALPHA-B"]
    assert va(1.62) == al.VERDICT_MAP["H-ALPHA-B"]
    assert va(1.98) == al.VERDICT_MAP["H-ALPHA-B"]
    assert va(None) == al.VERDICT_MAP["H-ALPHA-INKONKLUSIV"]
    # Smoke-Interpolationslage (~93.5 -> alpha ~1.54): zwischen den Baendern
    assert va(1.54) == al.VERDICT_MAP["H-ALPHA-INKONKLUSIV"]
    # Zaune sind Sanity-only: 93.5 liegt IN der H-B-Zaune [90,140] (Flag
    # True), aber AUSSERHALB beider alpha-Baender -> Verdikt INKONKLUSIV.
    # Genau die Smoke-Lage: Zaune-Flag und Verdikt fallen auseinander.
    flags = al.fence_flags(93.5, 79)
    assert flags == {"H-A": False, "H-B": True}
    assert al.fence_flags(60.77, 79)["H-A"] is True
    assert al.fence_flags(109.4, 79)["H-B"] is True
    assert al.fence_flags(None, 79) == {"H-A": False, "H-B": False}


# === Prereg ===

def test_prereg_payload_fields():
    p = al.build_prereg_payload()
    assert p["experiment"] == "033-ququint-alpha-separation"
    assert p["hypothesis"] == "H-ALPHA"
    arch = p["architectures"]["A_isa"]
    assert arch["phi_d_two_q_frozen"] == 79
    assert arch["acceptance"] == [76, 86]
    assert arch["real_fez_reference"] == 81
    assert arch["two_q_gate_names"] == ["cz"]
    t = p["thresholds"]
    assert t["p1_primary"] == 3e-4 and t["ro"] == 1e-2 and t["ratio"] == 10.0
    assert t["n_shots"] == 8192 and t["n_boot"] == 1000
    assert t["band_tol_rel"] == 0.10
    assert math.isclose(t["alpha_band_H-A"][0], 0.9, rel_tol=1e-12)
    assert math.isclose(t["alpha_band_H-A"][1], 1.1, rel_tol=1e-12)
    assert math.isclose(t["alpha_band_H-B"][0], 1.62, rel_tol=1e-12)
    assert math.isclose(t["alpha_band_H-B"][1], 1.98, rel_tol=1e-12)
    assert t["isa_count_accept"] == [76, 86]
    assert t["confound_limit"] == 0.05
    pts = p["predictions"]["kappa_eff_points"]
    assert math.isclose(pts["H-A"], 10.0 * 79 / 13.0, rel_tol=1e-12)
    assert math.isclose(pts["H-B"], 18.0 * 79 / 13.0, rel_tol=1e-12)
    assert math.isclose(p["bands_kappa_eff"]["H-B"][0], 0.9 * 18.0 * 79 / 13.0,
                        rel_tol=1e-12)
    assert len(p["grids"]["kappa_grid"]) == 12
    assert p["grids"]["kappa_grid"] == list(cx.KAPPA_GRID)
    assert "BEKANNT" in p["registered_before"]["smoke_disclosure"]
    assert "sanity-only" in p["fences_kappa_eff"]["role"]
    assert p["controls"]["gate"] == "Kontrollfehler -> EVALUATION_INVALID"
    assert len(p["verdict_map"]) == 4
    assert "SCHWACH" in p["weak_assumption"]
    assert "INKONKLUSIV" in p["post_hoc_analysis_pre_registered"]
    assert "0 QPU" in p["qpu"]
    assert p["seeds"]["aer"] == 42 and p["seeds"]["transpile"] == 7


def test_prereg_md5_freeze_verify_tamper(tmp_path):
    payload = al.build_prereg_payload()
    doc = al.freeze_prereg(payload)
    assert al.verify_prereg_md5(doc)
    tampered = dict(doc)
    tampered["thresholds"] = dict(tampered["thresholds"])
    tampered["thresholds"]["band_tol_rel"] = 0.5  # Band-Manipulation
    assert not al.verify_prereg_md5(tampered)
    path = tmp_path / "prereg.json"
    path.write_text(json.dumps(doc))
    reloaded = al.load_frozen_prereg(str(path))
    assert reloaded["md5"] == doc["md5"]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(tampered, fh)
    try:
        al.load_frozen_prereg(str(path))
        raise AssertionError("manipulierter Prereg wurde akzeptiert")
    except ValueError:
        pass


# === Evaluation (Smoke mit vollem kappa-Gitter: C-V4-Anker erfordert es) ===

def test_run_alpha_smoke_reduced_grid():
    res = al.run_alpha(p1_grid=(0.0, 3e-4, 1e-3))
    assert res["controls_ok"] is True
    assert all(res["controls"].values())
    assert res["verdict"] in {
        al.VERDICT_MAP["H-ALPHA-A"], al.VERDICT_MAP["H-ALPHA-B"],
        al.VERDICT_MAP["H-ALPHA-INKONKLUSIV"],
        al.VERDICT_MAP["EVALUATION_INVALID"]}
    assert res["phi_d_two_q_frozen"] == 79
    kei = res["kappa_eff_isa"]["kappa_star"]
    assert kei is not None and 1.0 < kei < 800.0
    assert abs(res["kappa_eff_45"]["kappa_star"]
               - al.V4_KAPPA_STAR_COMMITTED) <= al.V4_TOL_REL * al.V4_KAPPA_STAR_COMMITTED
    assert res["measurement"]["margin_isa"] < 0.8  # unter noiseless
    assert res["curve_isa_descriptive"]["0.0"] is None
    assert set(k for k in res["curve_isa_descriptive"]) >= {"0.0003", "0.001"}
    # Deskriptive alpha_45 am Primärpunkt reproduziert die V4-Implikation
    assert math.isclose(res["curve_45_descriptive"]["0.0003"]["kappa_eff"],
                        al.V4_KAPPA_STAR_COMMITTED, rel_tol=al.V4_TOL_REL)


# === Offline-Guard ===

def test_offline_guard_no_runtime_service_no_token():
    src = open(al.__file__, encoding="utf-8").read()
    assert "QiskitRuntimeService" not in src
    assert "IBMQ_TOKEN" not in src
    assert "service.backend(" not in src
    # Die EINZIGE qiskit_ibm-Benutzung ist der offline fake_provider-Import
    assert src.count("from qiskit_ibm") == 1
    assert "fake_provider" in src