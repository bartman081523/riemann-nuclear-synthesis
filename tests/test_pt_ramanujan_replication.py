"""EXPERIMENT 034 — Ramanujan-Fingerprint-Replikation (H-RAM-2): Tests.

OFFLINE (reine numpy-Arithmetik, kein qiskit — Guard). Prereg
(pt_ramanujan_prereg.json, md5) wird VOR der Auswertung gefroren; Modell,
Bänder, Gate-Set und Falsifikator stammen aus dem Plan (VOR der Messung
fixiert) und sind im Payload committet.
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_ramanujan_replication as rr
import pt_ququint_multin as mn
import pt_prime_state as ps


# === Exakte Modell-Arithmetik (Uniform-Residuen) ===

def test_model_derivation_anchors():
    # (625, 625): m=114 -> (114-5)^2/(4*625*114) = 109^2/285000
    exact = 109.0 ** 2 / (4.0 * 625.0 * 114.0)
    assert math.isclose(rr.model_share_star(625, 625), exact, rel_tol=1e-12)
    assert exact == 11881 / 285000  # exakter Bruch, 0.0416877...
    assert math.isclose(exact, 0.041688, rel_tol=1e-5)
    # Transition EXAKT bei m=25 (P=97): (m-5)^2 = 16m -> Modell = 4/d =
    # generische Baseline (registrierte NEGATIV-Vorhersage am Punkt)
    assert math.isclose(rr.model_share_star(97, 625), 4 / 625, rel_tol=1e-12)
    assert math.isclose(rr.lift_factor(97), 1.0, rel_tol=1e-12)
    # Unterdrückung bei m=16 (P=53): Modell UNTER generisch
    assert rr.model_share_star(53, 625) < 4 / 625
    assert rr.lift_factor(53) < 1.0
    # m=5 (P=11): exakte Null (G_j = 0)
    assert rr.model_share_star(11, 25) == 0.0
    assert rr.model_share_star(11, 625) == 0.0
    # Gated Punkte: Modellwerte aus der einen Formel
    assert math.isclose(rr.model_share_star(401, 625),
                        (79 - 5) ** 2 / (4.0 * 625.0 * 79.0), rel_tol=1e-12)
    # Generische Baseline 4/d
    assert math.isclose(rr.generic_baseline(625), 4 / 625, rel_tol=1e-12)
    assert math.isclose(rr.generic_baseline(25), 4 / 25, rel_tol=1e-12)


def test_v2_reference_correction():
    # V2 gemessen 0.04272280... vs exaktes Modell 0.041688: ratio 1.0248,
    # im registrierten Band [0.8, 1.25] — die CRUDE-Modell-Korrektur
    # (0.045 -> 0.041688) ändert das V2-Urteil NICHT.
    ratio = rr.V2_SHARE_STAR_PRIME_COMMITTED / rr.EXACT_MODEL_625_625
    assert math.isclose(ratio, 1.0248, rel_tol=1e-3)
    assert 0.8 <= ratio <= 1.25
    # CRUDE-Modell (V2-prereg) ist dokumentiert, nicht benutzt
    assert math.isclose(rr.V2_CRUDE_MODEL_D625, 0.045, rel_tol=1e-12)


# === V2-Anker (deterministische Arithmetik, bit-genau) ===

def test_t1_t2_t3_anchors_reproduce_v2():
    c = rr.run_controls()
    assert c["T1_v2_anchor_prime"] is True
    assert c["T2_v2_anchor_random"] is True
    assert c["T3_v2_anchor_composite"] is True
    # Unmittelbar: der Prime-Anker ist exakt der V2-kommittierte Wert
    prof = mn.dft_profile(625, 625)
    assert mn.share_star(prof, 625) == rr.V2_SHARE_STAR_PRIME_COMMITTED


def test_t4_t5_controls():
    c = rr.run_controls()
    assert c["T4_model_exact"] is True
    assert c["T5_gate_set"] is True


# === Gate-Set (registriert: pi >= 79 auf d=625 -> genau 5 Punkte) ===

def test_gate_set_frozen():
    gated = [(P, d) for P, d in rr.PRIME_POINTS if rr.is_gated(P, d)]
    assert gated == [(401, 625), (463, 625), (541, 625), (599, 625),
                     (625, 625)]
    # alle deskriptiven Punkte unter der Gate-Schwelle oder d25
    for P, d in rr.PRIME_POINTS:
        if (P, d) not in gated:
            assert not rr.is_gated(P, d)
    # d25 ist IMMER deskriptiv (V2-Lektion: m=9 fluktuationsbeherrscht)
    assert rr.is_gated(625, 25) is False
    # Transition-Punkt (97, 625, m=25) ist deskriptiv
    assert rr.is_gated(97, 625) is False
    # 401 ist der kleinste gated Punkt: pi(401) = 79 = GATE_MIN_PI
    assert len(ps.sieve_primes(401)) == 79 == rr.GATE_MIN_PI
    assert len(ps.sieve_primes(463)) == 90
    assert len(ps.sieve_primes(541)) == 100
    assert len(ps.sieve_primes(599)) == 109


# === Band- und Flag-Logik ===

def test_band_and_point_flags_logic():
    lo, hi = rr.band(0.04)
    assert math.isclose(lo, 0.032, rel_tol=1e-12)
    assert math.isclose(hi, 0.05, rel_tol=1e-12)
    row_in = {"gated": True, "model": 0.04, "share_prime": 0.041,
              "share_random": 0.01, "share_composite": 0.003}
    f = rr.point_flags(row_in, rr.composite_limit())
    assert f == {"band": True, "random_overlap": False,
                 "composite_overlap": False, "outside": False}
    # Random-Overlap: random >= band_lo -> Falsifikator
    row_ov = dict(row_in, share_random=0.033)
    assert rr.point_flags(row_ov, rr.composite_limit())["random_overlap"] is True
    # Ausserhalb des Bands (oben und unten)
    lim = rr.composite_limit()
    assert rr.point_flags(
        dict(row_in, share_prime=0.051), lim)["outside"] is True
    assert rr.point_flags(
        dict(row_in, share_prime=0.031), lim)["outside"] is True
    # Deskriptiver Punkt: alle Flags None (kein Gate)
    row_desc = dict(row_in, gated=False)
    assert rr.point_flags(row_desc, rr.composite_limit()) == {
        "band": None, "random_overlap": None,
        "composite_overlap": None, "outside": None}
    # Composite-Limit = band_lo des kleinsten gated Punkts (401)
    assert math.isclose(rr.composite_limit(),
                        0.8 * rr.model_share_star(401, 625), rel_tol=1e-12)


# === Punkt-Messung (Struktur) ===

def test_run_point_structure():
    row = rr.run_point(401, 625, rr.RANDOM_SEED_BASE + 7)
    assert row["P"] == 401 and row["d"] == 625
    assert row["m"] == 79 and row["gated"] is True
    assert row["seed"] == rr.RANDOM_SEED_BASE + 7
    for k in ("share_prime", "share_random", "share_composite", "model",
              "generic", "lift_model"):
        assert isinstance(row[k], float)
    # Modellwert im Row stimmt mit der Formel überein
    assert row["model"] == rr.model_share_star(401, 625)
    # Determinismus: gleicher Seed -> gleicher Random-Wert
    row2 = rr.run_point(401, 625, rr.RANDOM_SEED_BASE + 7)
    assert row2["share_random"] == row["share_random"]


def test_composite_controls_rank_matched():
    # Composite-Support ist rank-matched (erste m Composites <= P)
    sup = mn.composite_support(15)
    assert len(sup) == 6  # pi(15) = 6
    assert all(p not in sup for p in (2, 3, 5, 7, 11, 13))
    assert list(sup) == [4, 6, 8, 9, 10, 12]
    # Der (625,625)-Composite-Wert ist der V2-Anker (deterministisch)
    prof = mn.single_register_profile(mn.composite_support(625), 625)
    assert math.isclose(mn.share_star(prof, 625),
                        rr.V2_SHARE_STAR_COMPOSITE_COMMITTED, abs_tol=1e-12)


# === Verdict (registrierter Falsifikator, synthetische Faelle) ===

def _gated_row(outside=False, random_overlap=False):
    row = {"gated": True, "model": 0.04, "share_prime": 0.041,
           "share_random": 0.01, "share_composite": 0.003,
           "P": 401, "d": 625}
    row["flags"] = rr.point_flags(row, rr.composite_limit())
    if outside:
        row["share_prime"] = 0.06
        row["flags"] = rr.point_flags(row, rr.composite_limit())
    if random_overlap:
        row["share_random"] = 0.05
        row["flags"] = rr.point_flags(row, rr.composite_limit())
    return row


def _desc_row():
    row = {"gated": False, "model": 0.0064, "share_prime": 0.05,
           "share_random": 0.01, "share_composite": 0.003,
           "P": 97, "d": 625}
    row["flags"] = rr.point_flags(row, rr.composite_limit())
    return row


def test_verdict_map_synthetic():
    comp_rows = [{"share_composite": 0.003, "P": 15, "d": 625},
                 {"share_composite": 0.003, "P": 121, "d": 625},
                 {"share_composite": 0.003, "P": 341, "d": 625},
                 {"share_composite": 0.003, "P": 625, "d": 625}]
    limit = rr.composite_limit()
    desc = [_desc_row() for _ in range(7)]

    # REPLICATED: 0 ausserhalb, kein Overlap
    rows = [_gated_row() for _ in range(5)] + desc
    assert rr.verdict_replication(rows, comp_rows, limit, True) == \
        rr.VERDICT_MAP["REPLICATED"]
    # REFUTED: 2 von 5 ausserhalb
    rows = [_gated_row() for _ in range(3)] + \
        [_gated_row(outside=True) for _ in range(2)] + desc
    assert rr.verdict_replication(rows, comp_rows, limit, True) == \
        rr.VERDICT_MAP["REFUTED"]
    # REFUTED via Random-Overlap (auch bei 0 ausserhalb)
    rows = [_gated_row() for _ in range(4)] + \
        [_gated_row(random_overlap=True)] + desc
    assert rr.verdict_replication(rows, comp_rows, limit, True) == \
        rr.VERDICT_MAP["REFUTED"]
    # REFUTED via Composite-Overlap
    hot_comp = [dict(r, share_composite=limit + 1e-3) for r in comp_rows]
    rows = [_gated_row() for _ in range(5)] + desc
    assert rr.verdict_replication(rows, hot_comp, limit, True) == \
        rr.VERDICT_MAP["REFUTED"]
    # PARTIAL: GENAU 1 ausserhalb, kein Overlap (registrierte Mittelklasse)
    rows = [_gated_row() for _ in range(4)] + [_gated_row(outside=True)] + desc
    assert rr.verdict_replication(rows, comp_rows, limit, True) == \
        rr.VERDICT_MAP["PARTIAL"]
    # INVALID: Kontrollfehler dominiert alles
    assert rr.verdict_replication(rows, comp_rows, limit, False) == \
        rr.VERDICT_MAP["INVALID"]
    # Deskriptive Punkte veraendern das Verdikt NICHT (auch wenn wild
    # ausserhalb — sie tragen kein Gate)
    wild_desc = _desc_row()
    wild_desc["share_prime"] = 0.5
    wild_desc["flags"] = rr.point_flags(wild_desc, limit)
    rows = [_gated_row() for _ in range(5)] + desc + [wild_desc]
    assert rr.verdict_replication(rows, comp_rows, limit, True) == \
        rr.VERDICT_MAP["REPLICATED"]


# === Prereg ===

def test_prereg_payload_fields():
    p = rr.build_prereg_payload()
    assert p["experiment"] == "034-ququint-ramanujan-replication"
    assert p["hypothesis"].startswith("H-RAM-2")
    assert "Fluktuation" in p["steelman"]
    rb = p["registered_before"]
    assert "V2-Anker" in rb["model_derivation"]
    assert "0.045" in rb["reference_correction"]       # CRUDE-Modell benannt
    assert "1.0248" in rb["reference_correction"]
    assert "GATE_MIN_PI = 79" in rb["gate_set_justification"]
    assert "m >= 62" in rb["gate_set_justification"]   # Random-Overlap-Kriterium
    assert "KEINE Prime-Trennung" in rb["transition_prediction"]
    assert "m=25" in rb["transition_prediction"]
    assert "Unterdrückung" in rb["transition_prediction"]
    assert "fluktuationsbeherrscht" in rb["descriptive_policy"]
    t = p["thresholds"]
    assert t["band"] == [0.8, 1.25]
    assert t["gate_min_pi"] == 79
    assert t["falsifier_min_outside"] == 2
    assert math.isclose(t["composite_overlap_limit"],
                        0.8 * rr.model_share_star(401, 625), rel_tol=1e-12)
    assert p["gated_points"] == ["401,625", "463,625", "541,625",
                                 "599,625", "625,625"]
    assert len(p["prime_points"]) == 12
    assert p["pi_by_point"]["625,625"] == 114
    assert p["pi_by_point"]["401,625"] == 79
    assert math.isclose(p["model_share_star"]["625,625"],
                        rr.EXACT_MODEL_625_625, rel_tol=1e-12)
    va = p["v2_anchors"]
    assert va["share_star_prime_d625"] == rr.V2_SHARE_STAR_PRIME_COMMITTED
    assert va["crude_model_d625"] == 0.045
    assert va["prereg_md5"] == "d9da292c7863810840b86ae2f069a365"
    assert p["seeds"]["random_base"] == 20260924
    assert p["seeds"]["v2_anchor_seed"] == 20260923
    assert "Index in PRIME_POINTS" in p["seeds"]["seed_rule"]
    c = p["controls"]
    assert "bit-genau" in c["T1_v2_anchor_prime"]
    assert "20260923" in c["T2_v2_anchor_random"]
    assert "Transition" in c["T4_model_exact"]
    assert c["gate"] == "Kontrollfehler -> EVALUATION_INVALID"
    assert "PARTIAL" in p["falsifier"]["partial_class"]
    assert "DEGENERAT-Lektion" in p["falsifier"]["partial_class"]
    assert len(p["verdict_map"]) == 4
    assert "0 QPU" in p["qpu"]


def test_prereg_md5_freeze_verify_tamper(tmp_path):
    payload = rr.build_prereg_payload()
    doc = rr.freeze_prereg(payload)
    assert rr.verify_prereg_md5(doc)
    tampered = dict(doc)
    tampered["thresholds"] = dict(tampered["thresholds"])
    tampered["thresholds"]["band"] = [0.99, 1.01]  # Band-Manipulation
    assert not rr.verify_prereg_md5(tampered)
    path = tmp_path / "prereg.json"
    path.write_text(json.dumps(doc))
    reloaded = rr.load_frozen_prereg(str(path))
    assert reloaded["md5"] == doc["md5"]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(tampered, fh)
    try:
        rr.load_frozen_prereg(str(path))
        raise AssertionError("manipulierter Prereg wurde akzeptiert")
    except ValueError:
        pass


# === Evaluation (Smoke: reine Arithmetik, voller Gitterlauf) ===

def test_run_replication_smoke():
    res = rr.run_replication()
    assert res["controls_ok"] is True
    assert all(res["controls"].values())
    assert res["verdict"] in set(rr.VERDICT_MAP.values())
    assert len(res["rows"]) == 12
    assert len(res["composite_rows"]) == 4
    gated = [r for r in res["rows"] if r["gated"]]
    assert len(gated) == 5
    for r in gated:
        assert r["flags"]["band"] in (True, False)
        assert r["flags"]["outside"] is (not r["flags"]["band"])
    for r in res["rows"]:
        if not r["gated"]:
            assert r["flags"] == {"band": None, "random_overlap": None,
                                  "composite_overlap": None, "outside": None}
    # Composite-Anker-Zeile (625, 625) reproduziert V2 bit-genau
    anchor = [r for r in res["composite_rows"] if r["P"] == 625][0]
    assert math.isclose(anchor["share_composite"],
                        rr.V2_SHARE_STAR_COMPOSITE_COMMITTED, abs_tol=1e-12)
    # Determinismus: zweiter Lauf identisch
    res2 = rr.run_replication()
    assert res2["verdict"] == res["verdict"]
    assert [r["share_prime"] for r in res2["rows"]] == \
        [r["share_prime"] for r in res["rows"]]


# === Offline-Guard ===

def test_offline_guard_no_qiskit_no_token():
    src = open(rr.__file__, encoding="utf-8").read()
    assert "qiskit" not in src.lower()
    assert "IBMQ_TOKEN" not in src
    assert "QiskitRuntimeService" not in src
    assert "SamplerV2" not in src and "EstimatorV2" not in src