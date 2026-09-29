# -*- coding: utf-8 -*-
"""Tests fuer EXPERIMENT 045 (S₄-Schluss-Theorem) gegen das committete
Frozen-Run-Artefakt pt_s4_closure_theorem_results.json — 0 QPU, keine
Wiederholung der schweren Läufe (T4/T5 ~85 min) in den Tests.

Gepinnt werden: die ex-ante-Toleranzen des Modulkopfs, die Lemma-Ebene
(l1/l2/l3), die T4-H-Identität, die T5-Verletzung EXAKT (Verdict
H_S4_CLOSURE_DEVIATION_FOUND), die Atome (Rundungs-Invarianz auf
ATOM_DECIMALS), T7/T8/T9/D-Strukturen und die Kreuzprobe — plus die
reine Orbit-Kombinatorik (15 Muster, 12/3-Split, T9-Formeln) direkt
aus den Musterlisten.
"""
import json
import os

import pytest

import pt_s4_closure_theorem as s4

RESULTS_PATH = "pt_s4_closure_theorem_results.json"

# 045-l2_l3 l3_max_dev — die gemessene Konjugations-Rundungs-Differenz
L3_MAX_DEV = 3.554447978966673e-15
MAX_WITHIN_045 = 1.0260516436488842e-08
ADJACENT_R = 1.0829548092830659
DISJOINT_R = 1.1881079493699196
ATOM_ADJ = 1.082954809
ATOM_DIS = 1.188107949


# ------------------------------------------------------------------ Konstanten

class TestFrozenConstants:
    def test_toleranzen_gefroren(self):
        assert s4.CONJ_TOL == 1e-10
        assert s4.SPEC_TOL == 1e-9
        assert s4.SUM_TOL == 1e-9

    def test_gammas_und_pfade(self):
        assert s4.GAMMAS == (0.002, 0.02, 0.2)
        assert s4.RESULTS_PATH == RESULTS_PATH
        assert s4.ATOM_DECIMALS == 9

    def test_praedikat_umfasst_r_median(self):
        # Dokumentierter Scope: max_within laeuft ueber VIER Groessen
        # inkl. der Rang-Statistik r_median (Quelle der 045-Verletzung;
        # Diagnose: pt_s4_t5_diag.py, NICHT verdict-tragend).
        import inspect
        src = inspect.getsource(s4.check_t5_t6)
        assert '"k1_mean", "k2_mean", "R", "r_median"' in src


# ------------------------------------------------------- Muster-Kombinatorik

class TestMusterKombinatorik:
    def test_15_muster_zwei_minus(self):
        pats = s4.two_minus_patterns()
        assert len(pats) == 15
        for p in pats:
            assert sum(1 for v in p.values() if v == -1) == 2

    def test_adjacent_split_12_3(self):
        pats = s4.two_minus_patterns()
        adjacent = sum(1 for p in pats if s4.is_adjacent(p))
        assert adjacent == 12
        assert 15 - adjacent == 3

    @pytest.mark.parametrize("n,adj,dis", [(3, 3, 0), (4, 12, 3),
                                           (5, 30, 15), (6, 60, 45)])
    def test_t9_formeln(self, n, adj, dis):
        # adjacent = n*C(n-1,2), disjunkt = C(n,2)*C(n-2,2)/2
        from math import comb
        assert n * (n - 1) * (n - 2) // 2 == adj
        assert (n * (n - 1) // 2) * ((n - 2) * (n - 3) // 2) // 2 == dis
        pats = s4.two_minus_patterns(n)
        assert len(pats) == adj + dis

    def test_formeln_gesamt(self):
        from math import comb
        for n in (3, 4, 5, 6):
            adj = n * comb(n - 1, 2)
            dis = comb(n, 2) * comb(n - 2, 2) // 2
            assert len(s4.two_minus_patterns(n)) == adj + dis


# --------------------------------------------------- committete 045-Resultate

@pytest.mark.skipif(not os.path.exists(RESULTS_PATH),
                    reason="045-Resultate noch nicht committed")
class TestCommittedResults:
    @pytest.fixture(scope="class")
    def res(self):
        with open(RESULTS_PATH, encoding="utf-8") as fh:
            return json.load(fh)

    def test_metadaten_0_qpu(self, res):
        assert res["experiment"] == "045-s4-closure-theorem"
        assert res["qpu"] == 0
        assert res["eps"] == 0.25
        assert res["family_size"] == 78

    def test_verdict_class_gefroren(self, res):
        assert res["verdict_class"] == "H_S4_CLOSURE_DEVIATION_FOUND"

    def test_l1_bit_gleich(self, res):
        l1 = res["l1_A_uniformitaet"]
        assert l1["bit_equal"] is True
        assert l1["max_abs_dev"] == 0.0
        assert l1["lemma_ok"] is True

    def test_l2_l3_konjugation(self, res):
        l23 = res["l2_l3_konjugation"]
        assert l23["l2_max_dev"] == 0.0
        assert l23["l3_max_dev"] == L3_MAX_DEV
        assert l23["l3_max_dev"] < s4.CONJ_TOL
        assert l23["lemma_ok"] is True

    def test_t4_h_identitaet_gruen(self, res):
        t4 = res["t4_h_identitaet"]
        assert t4["max_h_dev"] < s4.CONJ_TOL
        assert t4["max_spec_dev"] < s4.SPEC_TOL
        assert t4["max_k_dev"] < s4.SPEC_TOL
        assert t4["theorem_ok"] is True

    def test_t5_bahnstruktur(self, res):
        t5 = res["t5_t6_familien_summen"]
        assert t5["n_patterns"] == 15
        assert t5["orbit_count"] == 2
        assert t5["orbit_sizes"] == [12, 3]
        assert t5["adjacent_counts"] == [12, 0]
        assert t5["tuple_dict_konsistenz_ok"] is True

    def test_t5_verletzung_exakt_gefroren(self, res):
        t5 = res["t5_t6_familien_summen"]
        assert t5["max_within_orbit_dev"] == MAX_WITHIN_045
        assert t5["max_within_orbit_dev"] >= s4.SUM_TOL
        assert t5["theorem_ok"] is False

    def test_t5_struktur_elemente_gruen(self, res):
        t5 = res["t5_t6_familien_summen"]
        assert t5["between_orbit_R_gap"] > 1e-6
        assert t5["prime_adjacent"] is True
        assert t5["composite_adjacent"] is True
        assert t5["prime_composite_same_orbit"] is True
        assert t5["prime_composite_sum_dev"] < s4.SUM_TOL

    def test_t5_atome_rundungs_invariant(self, res):
        t5 = res["t5_t6_familien_summen"]
        assert round(t5["adjacent_R"], 9) == ATOM_ADJ
        assert round(t5["disjoint_R"], 9) == ATOM_DIS
        assert t5["adjacent_R"] == ADJACENT_R
        assert t5["disjoint_R"] == DISJOINT_R

    def test_t7_v1_atom_korrespondenz(self, res):
        t7 = res["t7_v1_atom_korrespondenz"]
        assert t7["n_records"] == 132
        assert t7["n_adjacent"] == 110
        assert t7["n_disjoint"] == 22
        assert t7["expected_ratio_adjacent"] == 0.8
        assert t7["observed_ratio_adjacent"] == 110 / 132
        assert t7["derived_atoms"] == {"adjacent": ATOM_ADJ,
                                       "disjoint": ATOM_DIS}
        assert t7["n_distinct_atoms_per_class"] == {"adjacent": 1,
                                                    "disjoint": 1}
        assert t7["max_R_dev_within_class"] < s4.SUM_TOL
        assert t7["rounding_invariance_ok"] is True
        assert t7["theorem_ok"] is True

    def test_t8_s3_gegenprobe(self, res):
        t8 = res["t8_s3_gegenprobe"]
        assert t8["n_orbits_s3"] == 4
        assert t8["orbit_sizes_s3"] == [6, 3, 3, 3]
        assert t8["n_distinct_sums_s3"] == 2
        assert t8["distinct_sums_s3"] == [ATOM_ADJ, ATOM_DIS]
        assert t8["same_s4_orbit_sum_dev"] < s4.SUM_TOL
        assert t8["counterfactual_ok"] is True

    def test_t9_n_verallgemeinerung(self, res):
        t9 = res["t9_n_verallgemeinerung"]["per_n"]
        assert t9["3"] == {"n_patterns": 3, "n_orbits": 1,
                           "adjacent": 3, "disjoint": 0,
                           "formula_adjacent": 3, "formula_disjoint": 0}
        assert t9["4"]["n_orbits"] == 2
        assert t9["5"] == {"n_patterns": 45, "n_orbits": 2,
                           "adjacent": 30, "disjoint": 15,
                           "formula_adjacent": 30, "formula_disjoint": 15}
        assert t9["6"]["n_patterns"] == 105
        assert t9["6"]["formula_adjacent"] == 60
        assert t9["6"]["formula_disjoint"] == 45
        assert res["t9_n_verallgemeinerung"]["theorem_ok"] is True

    def test_d64_muster_diagnose(self, res):
        d = res["d_64_muster_diagnose"]
        assert d["n_patterns"] == 64
        assert d["n_distinct_k_pairs"] == 30
        assert d["n_orbits_stabilizer_s3"] == 20
        assert d["burnside_orbits_full_s4"] == 11

    def test_kreuzprobe_gruen(self, res):
        cross = res["cross_t5_t7_atom"]
        assert cross["max_atom_dev"] == 3.699196504669544e-10
        assert cross["max_atom_dev"] < 10 ** (-s4.ATOM_DECIMALS) + 5e-10
        assert cross["ok"] is True

    def test_verdict_klasse_aus_einzel_checks_abgeleitet(self, res):
        # Genau EIN Theorem rot (t5), alle uebrigen gruen -> DEVIATION.
        checks = [res["l1_A_uniformitaet"]["lemma_ok"],
                  res["l2_l3_konjugation"]["lemma_ok"],
                  res["t4_h_identitaet"]["theorem_ok"],
                  res["t5_t6_familien_summen"]["theorem_ok"],
                  res["t7_v1_atom_korrespondenz"]["theorem_ok"]]
        assert checks == [True, True, True, False, True]
        assert res["verdict_class"] == "H_S4_CLOSURE_DEVIATION_FOUND"