# -*- coding: utf-8 -*-
"""EXPERIMENT 050 (H-RAM-Q-6 Leg D1 Kingston) — Offline-Tests (0 QPU)."""
import json
import os

import pytest

import pt_ram_q6_kingston as k6
import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_aer as h3a

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pt_ram_q6_kingston_isa_stage as stage6  # noqa: E402
import pt_ram_q6_kingston_qpu as q6  # noqa: E402


# --- Prereg-Freeze ---

def test_prereg_frozen_ladt_mit_md5():
    doc = k6.load_frozen_prereg()
    assert doc["md5"] == k6.PREREG_MD5
    assert doc["status"] == k6.PREREG_STATUS
    assert doc["experiment"] == k6.EXPERIMENT
    assert doc["hypothesis"] == "H-RAM-Q-6"
    assert sorted(doc["legs"]) == ["L1_Substrat_Kohaerenz",
                                   "L2_VorzeichenStabilitaet",
                                   "L3_KappaFloorUnion"]
    assert doc["verdict_map"]["order"][0] == "DEGENERAT"


def test_prereg_verweist_gefrorenes_gesetz_bitgenau():
    prereg = k6.load_frozen_prereg()
    law = prereg["inherited_verdict"]["prereg_md5_of_law"]
    h3p = json.load(open("pt_ram_q_hardware3_prereg.json", encoding="utf-8"))
    assert law == h3p["md5"] == "baaca1f6772e07b0847fe436da7e16da"
    h3.load_frozen_prereg()  # self-md5 des Gesetzes-Payloads (raises on drift)


def test_prereg_grid_aus_gefrorenem_payload():
    prereg = k6.load_frozen_prereg()
    pts = h3a.all_points()
    verdict = {(a, P) for (a, P) in prereg["grid_points"]["verdict"]}
    kalib = {(a, P) for (a, P) in prereg["grid_points"]["kalibrier"]}
    assert verdict == {k for k, p in pts.items() if p["set"] == "verdict"}
    assert kalib == {k for k, p in pts.items() if p["set"] == "cal"}
    assert not (verdict & kalib)
    assert len(verdict) == 13 and len(kalib) == 13


# --- Leg-Mathematik ---

def test_spearman_perfect_and_antikorreliert():
    assert k6.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert k6.spearman([1, 2, 3, 4], [40, 30, 20, 10]) == pytest.approx(-1.0)


def test_spearman_ties_stabil():
    x = [1, 1, 2, 3]
    y = [5, 6, 7, 8]
    rho = k6.spearman(x, y)
    assert -1.0 <= rho <= 1.0
    assert k6.spearman(x, y) == rho  # deterministisch


def test_binom_sf_exakt():
    assert k6.binom_sf_one_sided(13, 13) == pytest.approx(1 / 8192)
    assert k6.binom_sf_one_sided(10, 13) == pytest.approx(378 / 8192)
    assert k6.binom_sf_one_sided(11, 13) == pytest.approx(92 / 8192)
    assert k6.binom_sf_one_sided(9, 13) == pytest.approx(1093 / 8192)
    assert k6.binom_sf_one_sided(13, 0) == 1.0
    assert k6.binom_sf_one_sided(0, 13) == pytest.approx(1.0)


def test_sign_agreement_roh_und_eligible():
    a = [0.02, -0.02, 0.005, -0.03]
    b = [0.03, 0.05, 0.004, -0.06]
    raw = k6.sign_agreement(a, b)
    assert raw["n"] == 4 and raw["agree"] == 3
    el = k6.sign_agreement(a, b, 0.01)
    assert el["n"] == 3 and el["agree"] == 2


def test_l1_perl_null_deterministisch():
    x = [0.01, -0.05, 0.03, -0.02, 0.04]
    y = [0.02, -0.04, 0.05, -0.01, 0.03]
    r1 = k6.leg_l1(x, y, 20261006, n_perm=120)
    r2 = k6.leg_l1(x, y, 20261006, n_perm=120)
    assert r1["rho_obs"] == r2["rho_obs"]
    assert r1["null"]["q95_abs"] == r2["null"]["q95_abs"]
    assert r1["seed"] == 20261006
    assert r1["pass"] == (r1["rho_obs"] > r1["null"]["q95_abs"])


def test_l2_gegrenzt_an_exakte_binomiale():
    """13/13 Uebereinstimmung -> p 1/8192 pass; 9/13 -> p 407/8192 fail."""
    a = [((i % 2) * 2 - 1) * 0.03 for i in range(13)]
    b = list(a)
    got = k6.leg_l2(a, b)
    assert got["lesart_roh"]["agree"] == 13
    assert got["lesart_roh"]["pass"]
    flipped = [-v for v in b[:4]] + b[4:]
    got2 = k6.leg_l2(a, flipped)
    assert got2["lesart_roh"]["agree"] == 9
    assert not got2["lesart_roh"]["pass"]
    assert got2["lesart_roh"]["p_one_sided"] == pytest.approx(1093 / 8192)


def test_holdout_residuen_vor_s1_bitidentisch():
    """S1-committed res_v3 der 13 Holdout-Felder (Format-Vertrag)."""
    s1 = json.load(open(k6.S1_EVAL_PATH, encoding="utf-8"))
    res = k6.holdout_residuen(s1)
    assert len(res) == 13
    assert "verdict|q5_d5|467" in res
    assert res["verdict|q5_d5|467"] == pytest.approx(-0.031777729460608306)


def test_kappa_map_26_entries():
    s1 = json.load(open(k6.S1_EVAL_PATH, encoding="utf-8"))
    km = k6.kappa_map(s1)
    assert len(km) == 26
    assert all(v is not None for v in km.values())


# --- ISA-Gate-Schema ---

def _gate_doc(**over):
    base = {
        "experiment": k6.EXPERIMENT, "backend": k6.BACKEND_NAME,
        "optimization_level": 3, "transpile_seed": 7, "n_circuits": 116,
        "total_two_q": 559, "max_two_q": 84,
        "isa_ceiling": dict(k6.ISA_CEILINGS),
        "per_circuit_two_q": {"struct_q3_d3_181_r1": {"ops": {"rz": 5},
                                                     "n_2q": 0}},
        "verdict": "ISA_OK", "generated_at_utc": "2026-10-02T00:00:00",
    }
    base.update(over)
    return base


def test_isa_gate_validiert_ok():
    assert k6.validate_isa_gate(_gate_doc()) is True


def test_isa_gate_fehlender_schluessel_raises():
    doc = _gate_doc()
    doc.pop("total_two_q")
    with pytest.raises(AssertionError):
        k6.validate_isa_gate(doc)


def test_isa_gate_ceiling_verletzt_raises():
    with pytest.raises(AssertionError):
        k6.validate_isa_gate(_gate_doc(max_two_q=121))
    with pytest.raises(AssertionError):
        k6.validate_isa_gate(_gate_doc(total_two_q=6001))
    with pytest.raises(AssertionError):
        k6.validate_isa_gate(_gate_doc(verdict="ISA_BUDGET_FAIL"))


def test_count_2q_whitelist():
    assert stage6.count_2q({"cz": 5, "rz": 10, "sx": 6}) == 5
    assert stage6.count_2q({"ecr": 3, "measure": 20}) == 3
    with pytest.raises(ValueError):
        stage6.count_2q({"mystery_gate": 2})


# --- Circuit-Set aus dem GEFRORENEN Payload ---

def test_circuit_set_116_und_namen_unique():
    circuits = h3a.build_hardware_circuit_set()
    assert len(circuits) == 116
    names = [c["name"] for c in circuits]
    assert len(set(names)) == 116
    kinds = {}
    for c in circuits:
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
    assert kinds == {"structure": 39, "kalibrier_structure": 39,
                     "loschmidt": 13, "kalibrier_loschmidt": 13,
                     "echo_ladder": 6, "negative_control": 4,
                     "readout_cal": 2}


def test_circuit_set_namen_aus_gefrorenem_grid():
    prereg = k6.load_frozen_prereg()
    verdict = {(a, P) for (a, P) in prereg["grid_points"]["verdict"]}
    kalib = {(a, P) for (a, P) in prereg["grid_points"]["kalibrier"]}
    circuits = h3a.build_hardware_circuit_set()
    assert not (verdict & kalib)
    for c in circuits:
        if c["kind"] in ("structure", "loschmidt"):
            assert (c["arm"], c["P"]) in verdict, c["name"]
        elif c["kind"] == "echo_ladder":
            P = c["P"]
            assert (c["arm"], P) in verdict and P in (181, 467), c["name"]
            assert c["r"] in (2, 4, 8) and "rep" not in c
        elif c["kind"] in ("kalibrier_structure", "kalibrier_loschmidt"):
            assert (c["arm"], c["P"]) in kalib, c["name"]


def test_counts_md5_kanonisch_stabil():
    """Identisch zum 11d-Fez-Format (Canonical JSON, sort_keys)."""
    got1 = q6.counts_md5([{"00": 5, "11": 3}])
    got2 = q6.counts_md5([{"11": 3, "00": 5}])
    assert got1 == got2
    assert got1 != q6.counts_md5([{"00": 6, "11": 2}])


# --- Raw-Vertrag (KEIN verdict-Feld) ---

class _FakeCounts:
    def get_counts(self):
        return {"00": 8190, "11": 2}


def _fake_job_result():
    from types import SimpleNamespace
    return SimpleNamespace(data=SimpleNamespace(c=_FakeCounts()))


def test_raw_doc_hat_keine_verdict_felder():
    """fetch_raw-Kontrakt am echten Funktionsaufruf (kein verdict-Feld)."""
    from types import SimpleNamespace
    circuits = h3a.build_hardware_circuit_set()
    for c in circuits:
        c.setdefault("arm", None)
        c.setdefault("set", None)
        c.setdefault("P", None)
        c.setdefault("rep", None)
        c.setdefault("r", None)
        c["kind"] = c["kind"]
    results = [_fake_job_result() for _ in circuits]
    totals = {"optimization_level": 3, "seed_transpiler": 7,
              "isa_2q_total": 999, "isa_2q_max": 77}
    doc = q6.fetch_raw(results, circuits,
                       {"job_id": "fake"}, k6.BACKEND_NAME, totals)
    banned = {"kappa_hat", "residuen", "gamma_used", "verdict", "band",
              "P_L", "P_ro_ref", "ratio_hw", "delta_cal", "center_v3",
              "in_band_sharp"}
    inter = banned & set(doc)
    assert not inter, inter
    assert doc["transpile"] == totals
    assert doc["n_circuits"] == 116
    assert all(e["shots_actual"] == 8192 for e in doc["counts"])
    assert doc["counts_md5"]
    assert "kappa" not in doc and "verdict" not in doc
    assert "ABSICHTLICH ABWESEND" in open(
        q6.__file__, encoding="utf-8").read()


def test_transpile_totals_commen_aus_gate_nicht_11d():
    """Das Kingston-Raw liest isa_2q_* aus dem GATE — kein 559/84-Literal."""
    import ast
    tree = ast.parse(open(q6.__file__, encoding="utf-8").read())
    numbers = {node.value for node in ast.walk(tree)
               if isinstance(node, ast.Constant)
               and isinstance(node.value, int)}
    assert 559 not in numbers and 84 not in numbers
    src_text = open(q6.__file__, encoding="utf-8").read()
    for needle in ('int(gate["total_two_q"])', 'int(gate["max_two_q"])',
                   "gate_entry", "ISA-Gate-Stale"):
        assert needle in src_text


# --- D1-Verdict-Ordnung abstrakt ---

def test_decide_d1_ordnung():
    def l1s(passes):
        return {s: {"pass": p} for s, p in passes.items()}

    def l2s(passes):
        return {s: {"lesart_roh": {"pass": p}} for s, p in passes.items()}

    both = {"S1": True, "S2": True}
    assert k6 is not None
    from pt_ram_q6_kingston_eval import decide_d1
    assert decide_d1(["t5"], 0, l1s(both), l2s(both)) == "DEGENERAT"
    assert decide_d1([], 2, l1s(both), l2s(both)) == "VOID_SUBSTRAT"
    assert decide_d1([], 0, l1s(both), l2s(both)
                     ) == "D1_CONFIRMED_SUBSTRAT_UNIVERSAL"
    assert decide_d1([], 0, l1s({"S1": True, "S2": False}),
                     l2s({"S1": True, "S2": False})) == "D1_PARTIAL"
    assert decide_d1([], 0, l1s({"S1": True, "S2": False}),
                     l2s({"S1": True, "S2": True})) == "D1_PARTIAL"
    assert decide_d1([], 0, l1s({"S1": False, "S2": False}),
                     l2s({"S1": False, "S2": False})
                     ) == "D1_REFUTED_SUBSTRAT_SPEZIFISCH"
    assert decide_d1([], 0, l1s({"S1": True, "S2": False}),
                     l2s({"S1": False, "S2": False})
                     ) == "D1_REFUTED_SUBSTRAT_SPEZIFISCH"
    assert decide_d1([], 0, l1s({"S1": False, "S2": False}),
                     l2s({"S1": True, "S2": True})
                     ) == "D1_REFUTED_SUBSTRAT_SPEZIFISCH"