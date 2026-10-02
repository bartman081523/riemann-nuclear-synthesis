# -*- coding: utf-8 -*-
"""EXPERIMENT 052 Tests: Re-Rechnungs-Artefakt / EINSTUFUNG der
einzigen 045-T5-Verletzung (H-S4CLOSURE-R2, 0 QPU).

Vertrags-Tests (Kanonik, md5, Basis-Pins, Toleranz-Identität,
Stuktur-Konstanten), Zweig-Tests der ex-ante-Verdict-Map an synthetischen
Dokumenten und Helper-Tests (vollständiges Paar-Grid, Star-Arme,
Konsistenz-Gate).  KEIN Live-Lauf im Suite-Weg — der gefrorene Lauf
schreibt sein Raw separat vor der Auswertung.
"""
import itertools
import json

import pytest

import pt_hstar5_execution as h5
import pt_s4_closure_theorem as s4
import pt_s4_t5_diag as td
import pt_s4_r2_recompute as rc
import pt_s4_r2_eval as ev


# --- Prereg-Kanonik ---

def test_prereg_konstante_und_datei_gleich():
    doc = rc.load_frozen_prereg()
    assert doc["experiment"] == rc.EXPERIMENT
    assert doc["hypothesis"] == "H-S4CLOSURE-R2"
    assert doc["status"] == "REGISTERED_NOT_MEASURED"
    assert doc["qpu"] == 0
    assert doc["branch"] == "h-test1-gap-invariance"


def test_prereg_regeneriert_bit_identisch():
    doc = rc.load_frozen_prereg()
    rebuilt = rc.build_prereg()
    canon = lambda d: json.dumps(d, sort_keys=True, separators=(",", ":"))
    assert canon({k: v for k, v in doc.items() if k != "md5"}) == canon(rebuilt)
    assert rc.self_md5() == doc["md5"]


def test_prereg_tamper_faellt(tmp_path):
    doc = rc.load_frozen_prereg()
    doc["sum_tol_falsch"] = 1e-7
    path = tmp_path / "tampered.json"
    path.write_text(rc.canonical(doc), encoding="utf-8")
    with pytest.raises(AssertionError):
        rc.load_frozen_prereg(str(path))


def test_toleranz_identitaet_keine_erhoehung():
    assert rc.SUM_TOL == td.SUM_TOL == s4.SUM_TOL == 1e-9
    assert rc.load_frozen_prereg()["konstanten"]["sum_tol"] == 1e-9


def test_s4_konstanten_gespiegelt():
    assert rc.EPS == h5.EPS_PRIMARY == 0.25
    assert (rc.TAU1, rc.TAU2, rc.TAU3) == (h5.TAU1, h5.TAU2, h5.TAU3)
    assert rc.BAHNEN == td.BAHNEN
    assert rc.BAHNEN == {"adjacent": (6, 10), "disjoint": (4, 7)}


def test_basis_pins_gleich_committeten_artefakten():
    res045 = json.load(open("pt_s4_closure_theorem_results.json"))
    scr = json.load(open("scratches/h9_s4_source_unified_out.json"))
    pr = rc.load_frozen_prereg()["basis"]
    assert pr["beobachtet_045_max_within"] == \
        res045["t5_t6_familien_summen"]["max_within_orbit_dev"]
    assert pr["beobachtet_045_between_gap"] == \
        res045["t5_t6_familien_summen"]["between_orbit_R_gap"]
    assert pr["beobachtet_045_r_median"]["6"] == 1.9147852243778032
    assert pr["beobachtet_045_r_median"]["10"] == 1.9147852129934473
    assert pr["adjacent_R_repr_atom"] == \
        res045["t5_t6_familien_summen"]["adjacent_R"]
    assert pr["disjoint_R_repr_atom"] == \
        res045["t5_t6_familien_summen"]["disjoint_R"]
    assert pr["scratch_max_within_unified"] == scr["max_within_unified"]
    assert pr["scratch_max_within_inst"] == scr["max_within_inst"]


def test_bekannte_scratch_lesarten_exakt_verankert():
    pr = rc.load_frozen_prereg()["basis"]["bekannte_scratch_lesarten"]
    fu = pr["scratch_full_within_unified"]["adjacent"]
    assert fu["max"] == 8.393228334568903e-10
    assert fu["worst_pair"] == [3, 12]
    assert pr["scratch_full_within_unified"]["disjoint"]["max"] == \
        2.679068078492719e-11
    fi = pr["scratch_full_within_inst"]["adjacent"]
    assert fi["max"] == 1.1384355902421817e-08
    assert fi["worst_pair"] == [6, 10]
    star = pr["star_anker_045"]["adjacent"]["star_max"]["r_median"]
    assert star["max"] == 1.0260516436488842e-08
    assert star["worst_pair"] == [0, 6]
    assert pr["star_anker_045"]["adjacent"]["repr"] == 0
    assert pr["star_anker_045"]["disjoint"]["repr"] == 4


# --- Struktur-Helfer ---

def test_adjacency_klassen_matchen_orbitstruktur():
    classes = rc.adjacency_classes()
    assert (len(classes["adjacent"]), len(classes["disjoint"])) == (12, 3)
    sigmas = list(itertools.permutations(range(4)))
    pats = s4.two_minus_patterns()
    orbits = {i: s4.orbit_of(pat, sigmas) for i, pat in enumerate(pats)}
    groups = {}
    for i, key in orbits.items():
        groups.setdefault(key, []).append(i)
    assert sorted(map(sorted, groups.values())) == \
        sorted(map(sorted, classes.values()))


def test_full_within_maximum_synthetic():
    med = {i: float(i) for i in range(6)}
    classes = {"adjacent": [0, 1, 2, 3], "disjoint": [4, 5]}
    out = rc.full_within_maximum(med, classes)
    assert out["adjacent"]["max"] == 3.0
    assert out["adjacent"]["worst_pair"] == [0, 3]
    assert out["disjoint"]["max"] == 1.0
    assert out["disjoint"]["worst_pair"] == [4, 5]


def test_full_within_maximum_klasse_size_muss_zutreffen():
    classes = rc.adjacency_classes()
    out = rc.full_within_maximum(
        {i: 1.0 for i in classes["adjacent"] + classes["disjoint"]}, classes)
    assert out["adjacent"]["max"] == 0.0
    assert out["adjacent"]["n_members"] == 12
    assert out["disjoint"]["n_members"] == 3


# --- Verdict-Zweige (ex ante, synthetisch) ---

TOL = 1e-9


def crit(**over):
    base = {"structural_ok": True, "basis_ok": True, "konsistenz_ok": True,
            "l1_native_max": 1.1e-9,
            "l1_class_r_median_adjacent": 1.02e-8,
            "l2_full_adj": 8.4e-10, "l2_full_dis": 2.7e-11,
            "l2_bahn_adj": 6.5e-10, "l2_bahn_dis": 2.7e-11}
    base.update(over)
    return base


def test_verdict_bahn_ok_und_full_ok_oder_artifact():
    assert ev.decide(crit(), TOL) == ev.VERDICT_QUELLEN_ARTEFAKT


def test_verdict_degenerat_falls_struktur_fehlt():
    assert ev.decide(crit(structural_ok=False), TOL) == ev.VERDICT_DEGENERAT
    assert ev.decide(crit(basis_ok=False), TOL) == ev.VERDICT_DEGENERAT
    assert ev.decide(crit(konsistenz_ok=False), TOL) == ev.VERDICT_DEGENERAT


def test_verdict_recompute_unable():
    assert ev.decide(crit(l1_native_max=8.5e-10), TOL) == \
        ev.VERDICT_RECOMPUTE_UNABLE
    assert ev.decide(crit(l1_class_r_median_adjacent=9.9e-10), TOL) == \
        ev.VERDICT_RECOMPUTE_UNABLE


def test_verdict_struktureller_rest_bei_l2_flip():
    assert ev.decide(crit(l2_full_adj=1.01e-9), TOL) == \
        ev.VERDICT_STRUKTURELL_REST
    assert ev.decide(crit(l2_full_dis=1.0e-9), TOL) == \
        ev.VERDICT_STRUKTURELL_REST
    assert ev.decide(crit(l2_bahn_adj=1.0e-9), TOL) == \
        ev.VERDICT_STRUKTURELL_REST


def test_boundary_semantik_strikt():
    # exakt gleich = kippt (l1-Gleichheit unter Kante, l2-Gleichheit ueber)
    assert ev.decide(crit(l1_native_max=TOL), TOL) == ev.VERDICT_RECOMPUTE_UNABLE
    assert ev.decide(crit(l2_full_adj=TOL), TOL) == ev.VERDICT_STRUKTURELL_REST


def test_decide_ignoriert_klassengrenze_nicht():
    # l1-native max ueber TOL und Klasse under TOL => unable (arm-attribution)
    assert ev.decide(crit(l1_class_r_median_adjacent=5e-10), TOL) == \
        ev.VERDICT_RECOMPUTE_UNABLE


# --- Governance ---

def test_verdict_map_struktur_und_kein_re_decide():
    pr = rc.load_frozen_prereg()
    names = [v["name"] for v in pr["verdict_map"]]
    assert names == ["DEGENERAT", "RECOMPUTE_UNABLE",
                     "H_S4CLOSURE_R2_QUELLEN_ARTEFAKT",
                     "H_S4CLOSURE_R2_STRUKTURELL_REST"]
    assert pr["governance"]["kein_re_decide"] is True
    assert pr["governance"]["committed_045_verdict"] == \
        "H_S4_CLOSURE_DEVIATION_FOUND"
    assert pr["governance"]["eval_reads_only_committed"] is True


def test_committed_045_verdict_file_unveraendert():
    doc = json.load(open("pt_s4_closure_theorem_results.json"))
    assert doc["verdict_class"] == "H_S4_CLOSURE_DEVIATION_FOUND"
    assert doc["experiment"] == "045-s4-closure-theorem"


def test_roh_vertrag_felder_verboten():
    banned = set(ev.RAW_FORBIDDEN_KEYS)
    assert {"verdict", "verdict_class", "einstufung", "einstufung_045",
            "unified_unter_tol", "inst_reproduziert"} == banned


def synthetic_raw(adj_val=1.0, dis_val=2.0, tamper=None):
    """Synthetisches Konsistenz-Beispiel über der REALen 15er-Struktur."""
    classes = rc.adjacency_classes()
    arrays = {}
    for i in range(15):
        arrays[str(i)] = [adj_val if i in classes["adjacent"] else dis_val]
    med = {i: (adj_val if i in classes["adjacent"] else dis_val)
           for i in range(15)}
    fw = {arm: rc.full_within_maximum(med, classes) for arm in ("inst", "unified")}
    raw = {"per_pattern_inst": dict(arrays),
           "per_pattern_unified": {k: list(v) for k, v in arrays.items()},
           "full_within": {arm: {cls: {"max": fw[arm][cls]["max"],
                                       "worst_pair": fw[arm][cls]["worst_pair"]}
                                 for cls in ("adjacent", "disjoint")}
                           for arm in ("inst", "unified")},
           "vergleiche": [{"bahn": b, "pair": list(p),
                           "d_inst": abs(med[p[0]] - med[p[1]]),
                           "d_unified": abs(med[p[0]] - med[p[1]])}
                          for b, p in td.BAHNEN.items()],
           "native_t5_t6": {"n_patterns": 15, "orbit_count": 2,
                            "orbit_sizes": [12, 3],
                            "adjacent_counts": [12, 0]}}
    if tamper:
        raw["full_within"]["unified"]["adjacent"]["max"] = tamper
    return raw


PR_REG = {"criteria": {"l1_reproduktion": {"structural": {
    "n_patterns": 15, "orbit_count": 2, "orbit_sizes": [12, 3],
    "adjacent_counts": [12, 0],
    "k_class_sizes": {"adjacent": 12, "disjoint": 3}}}}}


def test_konsistenz_pruefen_bit_equal_ok():
    out = ev.konsistenz_pruefen(synthetic_raw(), PR_REG)
    assert out["ok"] is True, out["fails"]


def test_konsistenz_pruefen_tamper_faellt():
    out = ev.konsistenz_pruefen(synthetic_raw(tamper=0.5), PR_REG)
    assert out["ok"] is False
    assert any("re-der" in f or "worst_pair" in f for f in out["fails"])


def test_konsistenz_pruefen_struktur_abweichung():
    raw = synthetic_raw()
    raw["native_t5_t6"]["orbit_sizes"] = [11, 4]
    out = ev.konsistenz_pruefen(raw, PR_REG)
    assert out["ok"] is False
    assert any("orbit_sizes" in f for f in out["fails"])