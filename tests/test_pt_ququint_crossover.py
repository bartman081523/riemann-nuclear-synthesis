"""V4 (H-STAR-4): Margin(p1)-Crossover encoded vs native-qudit.

Tests OFFLINE; nur Architektur A nutzt AerSimulator (lokal, kein IBM-
Provider — Guard). Prereg (kappa-Gitter, Baender, Seeds, Schwellen) wird
VOR der Kurven-Berechnung gefroren (pt_crossover_prereg_v4.json, md5).

Kernidentitaet beider Architekturen (registriert): identischer logischer
Task (Voll-Task mit Praep, Readout-Rate ro gleich, 2q-Ratio-Penalty auch
nativ), kappa* = margin_native(kappa) = margin_encoded am Fez-Punkt
p1 = 3e-4. Schwaecher Proxy (margin >= 0) ist im Prereg markiert.
"""

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_ququint_crossover as cx
from pt_ququint_ibmq import D5, WITNESS_BOUND
from pt_ququint_ibmq_aer import dft_diagonal_weight, error_budget, witness_from_counts


# === Native-Primitiven ===

def test_f5_matrix_unitary_and_uniform():
    F = cx.f5_matrix()
    assert np.allclose(F @ F.conj().T, np.eye(D5), atol=1e-12)
    col0 = F[:, 0]
    assert np.allclose(np.abs(col0) ** 2, np.full(D5, 1 / D5), atol=1e-12)


def test_phi_ququint_dft_eigenstate():
    # Phase-1-Pin: (F (x) F+) |phi> = |phi> -> V = 1 exakt
    F = cx.f5_matrix()
    U = np.kron(F, F.conj().T)
    psi = cx.phi_ququint()
    assert np.allclose(U @ psi, psi, atol=1e-12)
    probs = np.abs(psi) ** 2
    assert math.isclose(cx._diag_weight(probs, D5, D5), 1.0, rel_tol=1e-12)


def test_sum_gate_unitary_and_copy_action():
    S = cx.sum_gate()
    assert np.allclose(S @ S.conj().T, np.eye(25), atol=1e-12)
    assert np.allclose(S @ S, np.eye(25), atol=1e-12)  # Permutation (Swap)
    for k in range(D5):
        e = np.zeros(25, dtype=complex)
        e[k * D5 + 0] = 1.0
        target = np.zeros(25, dtype=complex)
        target[k * D5 + k] = 1.0
        assert np.allclose(S @ e, target, atol=1e-12)


def test_depolarize_arithmetic():
    rho = np.zeros((25, 25), dtype=complex)
    rho[0, 0] = 1.0
    assert cx.depolarize(rho, 0.0) is rho  # eps=0 exakt no-op
    out = cx.depolarize(rho, 0.25)
    assert math.isclose(float(np.trace(out).real), 1.0, rel_tol=1e-12)
    expected = 0.75 * rho + 0.25 * np.eye(25, dtype=complex) / 25
    assert np.allclose(out, expected, atol=1e-14)
    full = cx.depolarize(rho, 1.0)
    assert np.allclose(full, np.eye(25, dtype=complex) / 25)


def test_readout_confusion_rows_and_v_loss():
    C = cx.readout_confusion_25(0.01)
    assert np.allclose(C.sum(axis=0), 1.0, atol=1e-12)
    # Kron-Struktur: der Top-Left-5x5-Block ist c[:,0] (x) c[:,0] -> (1-ro)^2
    assert math.isclose(C[0, 0], 0.99 ** 2, rel_tol=1e-12)
    # true (0,0) -> gemessen (0,1): A richtig (0.99) x B falsch (ro/4)
    assert math.isclose(C[0 * D5 + 1, 0 * D5 + 0], 0.99 * 0.0025, rel_tol=1e-12)
    # V=1-Zustand (uniform auf der Diagonale) verliert Masse:
    probs = np.zeros(25)
    for k in range(D5):
        probs[k * D5 + k] = 0.2
    v = cx._diag_weight(C @ probs, D5, D5)
    assert v < 1.0 and v > 1.0 - 2 * 0.01


def test_native_gate_plan_arities_and_eps():
    plan = cx.native_gate_plan(2.0, 3e-4)
    assert [a for _n, a, _e in plan] == [1, 2, 1, 1]
    assert math.isclose(plan[0][2], 2.0 * 3e-4, rel_tol=1e-12)
    assert math.isclose(plan[1][2], 2.0 * 10.0 * 3e-4, rel_tol=1e-12)
    assert math.isclose(plan[2][2], 2.0 * 3e-4, rel_tol=1e-12)
    assert math.isclose(plan[3][2], 2.0 * 3e-4, rel_tol=1e-12)
    assert [n for n, _a, _e in plan] == [
        "F5_A_prep", "SUM_2q", "F5_A_rot", "F5dag_B_rot"]


def test_native_noiseless_chain_v_exact_one():
    proto = cx.native_protocol(0.0, 0.0, ro=0.0)
    assert abs(proto["v_exact"] - 1.0) <= 1e-12
    # Nach Praep (Gates 1+2) ist der Zustand bereits phi; die Rotation
    # bildet phi auf sich ab -> Diagonale uniform 1/5:
    diag = [proto["probs"][k * D5 + k] for k in range(D5)]
    assert np.allclose(diag, np.full(D5, 0.2), atol=1e-12)
    assert proto["v_exact_readout"] == proto["v_exact"]  # ro=0


def test_native_noiseless_margin_band():
    w = cx.native_witness_from_probs(
        cx.native_protocol(0.0, 0.0, ro=0.0)["probs_readout"])
    # Noiseless lebt die Verteilung KOMPLETT auf der Witness-Diagonale ->
    # V ist deterministisch: v_hat = 1 exakt UND SE = 0 exakt (keine
    # Off-Diagonal-Masse, kein Bootstrap-Variationsanteil in V) ->
    # margin = 1 - 0 - 0.2 = 0.8 exakt. (Der 4*SE-Penalty verschwindet
    # nur im noiseless-Grenzfall; mit ro > 0 oder Gate-Fehlern kehren
    # Off-Diagonal-Masse und SE zurueck.)
    assert abs(w["v_hat"] - 1.0) <= 1e-12
    assert w["se"] == 0.0
    assert abs(w["margin"] - 0.8) <= 1e-12


def test_native_margin_monotone_in_kappa():
    kgrid = cx.KAPPA_GRID
    vs = [cx.native_protocol(k, cx.P1_PRIMARY, ro=0.0)["v_exact"] for k in kgrid]
    assert all(vs[i + 1] < vs[i] for i in range(len(vs) - 1))
    ms = [cx.native_margin(k, cx.P1_PRIMARY, n_shots=8192)["margin"]
          for k in kgrid]
    # Bootstrap-Fluktuation erlaubt 1e-3 Wackern, Trend muss fallen
    assert ms[-1] < ms[0]
    assert all(ms[i + 1] <= ms[i] + 1e-3 for i in range(len(ms) - 1))


def test_native_uniform_margin_below_bound():
    probs = np.full(25, 1 / 25)
    w = cx.native_witness_from_probs(probs)
    assert math.isclose(w["v_exact"], 0.2, rel_tol=1e-12)
    assert w["margin"] < 0.0  # V-Boden 0.2 == Bound, SE zieht darunter


def test_diag_weight_matches_phase1_convention():
    # d=8, diag_size=5 ist identisch zu dft_diagonal_weight (Phase-1)
    rng = np.random.default_rng(7)
    probs64 = rng.dirichlet(np.ones(64))
    assert abs(cx._diag_weight(probs64, 8, 5) - dft_diagonal_weight(probs64)) < 1e-12


def test_native_estimator_parity_with_phase2_witness_from_counts():
    # Struktur-Paritaet: derselbe beobachtete Histogramm-Ausschnitt + dieselbe
    # Bootstrap-Sequenz (seed 9871) -> identisches v_hat/se/margin.
    probs25 = np.zeros(25)
    probs25[:D5 * D5] = 1.0 / (D5 * D5)  # uniform
    probs25 /= probs25.sum()
    rng = np.random.default_rng(cx.SEED_SHOTS_NATIVE)
    counts25 = rng.multinomial(8192, probs25)
    probs64 = np.zeros(64)
    for a in range(D5):
        for b in range(D5):
            probs64[a * 8 + b] = probs25[a * D5 + b]
    counts64 = np.zeros(64)
    for a in range(D5):
        for b in range(D5):
            counts64[a * 8 + b] = counts25[a * D5 + b]
    mine = cx.native_witness_from_probs(probs25, n_shots=8192)
    phase2 = witness_from_counts(counts64, seed=9871)
    # v_hat bit-identisch (dieselben beobachteten Diagonal-Counts).
    assert abs(mine["v_hat"] - phase2["v_hat"]) <= 1e-12
    # SE nur innerhalb statistischer Toleranz: numpy.multinomial bestimmt
    # die LETZTE Kategorie als Restbestimmung (kein RNG-Zug). Im 25-Bin-
    # Vektor faellt der Rest auf Diagonal-Bin 24 (deterministisch), im
    # 64-Bin-Vektor auf das Null-Bin 63, waehrend Bin 24 dort als
    # Binomialzug gezogen wird -> die Bootstrap-Sequenz divergiert leicht.
    # Struktur-Paritaet (dieselbe Pipeline) haelt; Bit-Paritaet ist nicht
    # erreichbar. Gemessene Differenz: 1.2e-4 (beide um 0.0044-0.0045).
    assert abs(mine["se"] - phase2["se"]) <= 2e-4
    assert abs(mine["margin"] - phase2["margin"]) <= 1e-3
    assert mine["bound"] == WITNESS_BOUND


# === kappa*-Bisektion + Verdict ===

def test_find_kappa_star_bracket_synthetic():
    res = cx.find_kappa_star(0.4, cx.P1_PRIMARY, n_shots=8192)
    assert res is not None
    lo, hi = res["bracket"]
    assert lo <= res["kappa_star"] <= hi
    assert res["kappa_star"] > 1.0
    assert res["delta_at_bracket"][0] > 0.0 >= res["delta_at_bracket"][1]
    assert res["grid_deltas"][0] > 0.0  # kleinste kappa: native deutlich besser
    assert res["grid_deltas"][-1] < 0.0


def test_find_kappa_star_no_bracket_when_enc_too_strong():
    # margin_enc = 0.9 liegt ueber dem noiseless nativen Margin (~0.76)
    assert cx.find_kappa_star(0.9, cx.P1_PRIMARY) is None


def test_verdict_bands():
    assert cx.verdict(0.5) == "H-STAR-4_REFUTED_KEIN_CROSSOVER"
    assert cx.verdict(1.0) == "H-STAR-4_SCHWACH_CROSSOVER"
    assert cx.verdict(9.9) == "H-STAR-4_SCHWACH_CROSSOVER"
    assert cx.verdict(10.0) == "H-STAR-4_CONFIRMED_CROSSOVER"
    assert cx.verdict(62.0) == "H-STAR-4_CONFIRMED_CROSSOVER"
    assert cx.verdict(None) == "H-STAR-4_INKONKLUSIV"


# === Encodierte Seite (Aer) ===

def test_error_budget_encoded_side():
    # 81 cx * ratio 10 * p1 3e-4 = 0.243 (§Z.13-Konvention)
    assert math.isclose(error_budget(81, 3e-4), 0.243, rel_tol=1e-12)


def test_run_v4_smoke_small_settings():
    # Test-Artifact: kleine Shots + groessere Identitaets-Toleranz (deterministisch
    # via Seeds); die Produktion nutzt die Prereg-Defaults (8192, Tol 0.02).
    res = cx.run_v4(n_shots=2048,
                    kappa_grid=(0.25, 1.0, 10.0, 100.0, 800.0),
                    p1_grid=(0.0, 3e-4, 1e-3),
                    control_identity_tol=0.08)
    assert res["controls_ok"] is True
    assert all(res["controls"].values())
    assert res["verdict"] in {
        "H-STAR-4_REFUTED_KEIN_CROSSOVER", "H-STAR-4_SCHWACH_CROSSOVER",
        "H-STAR-4_CONFIRMED_CROSSOVER", "H-STAR-4_INKONKLUSIV"}
    ks = res["kappa_star"]["kappa_star"]
    assert ks is not None and 1.0 < ks < 800.0
    assert res["encoded"]["phi_noiseless"]["v_hat"] > 0.9
    # Normalisierungsrundung (1.0000000000000002) -> Toleranz wie Gate T1
    assert abs(res["native"]["noiseless_v_exact"] - 1.0) <= 1e-12
    # Deskriptive Kurven vorhanden
    assert len(res["native"]["margin_curve_primary"]) == 5
    assert set(res["kappa_star_per_p1_descriptive"]) == {"0.0", "0.0003", "0.001"}
    assert res["kappa_star_per_p1_descriptive"]["0.0"] is None  # p1=0: kein
    # Gate-Crossover (native margin konstant in kappa bei p1=0, readout-only)
    assert res["encoded"]["gate_counts_phi_D"]["cx"] > 0
    assert "cx" in res["encoded"]["gate_counts_phi_D"]


# === Prereg ===

def test_prereg_payload_fields():
    p = cx.build_prereg_payload()
    assert p["experiment"] == "032-ququint-v4-margin-crossover"
    assert p["predictions"]["t_kappa_star_ge_10"] is True
    t = p["thresholds"]
    assert t["kappa_refuted_max"] == 1.0
    assert t["kappa_confirmed_min"] == 10.0
    assert t["kappa_tol_rel"] == 0.01
    assert t["prediction_band"] == [10.0, 500.0]
    assert t["p1_primary"] == 3e-4
    assert t["ro"] == 1e-2 and t["ratio"] == 10.0
    assert t["n_shots"] == 8192 and t["n_boot"] == 1000
    assert t["phi_d_cx_soll"] == 45
    assert len(p["grids"]["kappa_grid"]) == 12
    # Schwaecher Proxy ist MARKIERT (Plan-Pflicht H-STAR-4)
    assert "SCHWACH" in p["weak_assumption"]
    assert "Proxy" in p["weak_assumption"]
    # Instantiierung: "2 Gates x kappa-Degradation" = 2 Rotations-Gates,
    # Voll-Task addiert Praep auf BEIDEN Seiten
    assert "2 Praep-Gates" in p["architectures"]["plan_formulation_note"]
    assert "kappa*ratio*p1" in p["architectures"]["B_native"]
    assert "81 2q" in p["architectures"]["A_encoded"]
    assert len(p["architectures"]["fairness"]) == 4
    assert p["controls"]["gate"] == "Kontrollfehler -> EVALUATION_INVALID"
    assert "0 QPU" in p["qpu"]
    assert len(p["verdict_map"]) == 4


def test_prereg_md5_freeze_verify_tamper(tmp_path):
    payload = cx.build_prereg_payload()
    doc = cx.freeze_prereg(payload)
    assert cx.verify_prereg_md5(doc)
    tampered = dict(doc)
    tampered["thresholds"] = dict(tampered["thresholds"])
    tampered["thresholds"]["kappa_confirmed_min"] = 1.0  # Band-Manipulation
    assert not cx.verify_prereg_md5(tampered)
    path = tmp_path / "prereg.json"
    path.write_text(json.dumps(doc))
    reloaded = cx.load_frozen_prereg(str(path))
    assert reloaded["md5"] == doc["md5"]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(tampered, fh)
    try:
        cx.load_frozen_prereg(str(path))
        raise AssertionError("manipulierter Prereg wurde akzeptiert")
    except ValueError:
        pass


# === Offline-Guard ===

def test_offline_module_no_qiskit_ibm_import():
    src = open(cx.__file__, encoding="utf-8").read()
    assert "qiskit_ibm" not in src
    assert "QiskitRuntimeService" not in src
    assert "IBMQ_TOKEN" not in src