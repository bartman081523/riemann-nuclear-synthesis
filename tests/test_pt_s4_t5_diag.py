# -*- coding: utf-8 -*-
"""Tests fuer pt_s4_t5_diag.py — 045-T5-Diagnose (Phase 12e), 0 QPU.

Die Diagnose ist NICHT verdict-tragend (Praezedenz gamma_arm, Phase
11d): das committete Frozen-Run-Verdict H_S4_CLOSURE_DEVIATION_FOUND
aus 045 bleibt unangetastet, hier wird nur die Herkunft der EINZIGEN
Verletzung (r_median, max_within 1.026e-08 > SUM_TOL) gepinnt.

Gepinnt werden offline aus dem committeten 045-Artefakt: die Zerlegung
von max_within je Groesse (Mittelung gruen auf 2.7e-10, r_median rot)
und die Bahn-Gruppen; gegen das committete Diagnose-Artefakt
(skipif): probe_a Multiset-Permutation, probe_b Kausalkette
(3.55e-15 -> 2.8e-13 -> 2.0e-09 -> 1.1e-08) und die t_H-Quellen.
"""
import json
import os

import pytest

import pt_s4_closure_theorem as s4
import pt_s4_t5_diag as s4d

RESULTS_045 = "pt_s4_closure_theorem_results.json"
DIAG_RESULTS = "pt_s4_t5_diag_results.json"

# 045-Anker
L3_MAX_DEV = 3.554447978966673e-15
MAX_WITHIN_045 = 1.0260516436488842e-08
R6_045 = 1.9147852243778032          # per_pattern["6"]["r_median"]
R0_045 = 1.9147852141172867          # per_pattern["0"]["r_median"] = ref
ADJ_IDX = [0, 1, 2, 3, 5, 6, 8, 10, 11, 12, 13, 14]
DIS_IDX = [4, 7, 9]


# ------------------------------------------------------------------ Konstanten

class TestFrozenConstants:
    def test_pfade_und_spiegel(self):
        assert s4d.RESULTS_045_PATH == RESULTS_045
        assert s4d.DIAG_RESULTS_PATH == DIAG_RESULTS
        assert s4d.SUM_TOL == 1e-9 == s4.SUM_TOL

    def test_groessen_und_bahnen(self):
        assert s4d.QUANTITIES == ("k1_mean", "k2_mean", "R", "r_median")
        assert s4d.MEAN_BASED == ("k1_mean", "k2_mean", "R")
        assert s4d.BAHNEN == {"adjacent": (6, 10), "disjoint": (4, 7)}
        assert s4d.PROBE_CFG_INDEX == 0

    def test_entry_delta_ist_l3_max_dev(self):
        assert s4d.ENTRY_DELTA == L3_MAX_DEV
        assert s4d.DELTAS == (L3_MAX_DEV, 1e-14, 1e-13)

    def test_docstring_nicht_verdict_tragend(self):
        assert "NICHT verdict-tragend" in s4d.__doc__
        assert "keine Toleranz-Erhoehung" in s4d.__doc__


# --------------------------------------------- Zerlegung offline aus 045-JSON

@pytest.mark.skipif(not os.path.exists(RESULTS_045),
                    reason="045-Resultate noch nicht committed")
class TestDekompositionOffline:
    @pytest.fixture(scope="class")
    def deko(self):
        with open(RESULTS_045, encoding="utf-8") as fh:
            return s4d.decompose_max_within(json.load(fh))

    def test_bahngruppen(self, deko):
        groessen = {"k1_mean", "k2_mean", "R", "r_median"}
        assert set(deko["adjacent"]) == groessen
        assert set(deko["disjoint"]) == groessen

    def test_mittelung_gruen_beide_bahnen(self, deko):
        assert deko["mean_based_max_within"] == pytest.approx(
            2.730e-10, rel=1e-2)
        assert deko["mean_based_max_within"] < s4d.SUM_TOL
        assert deko["mean_based_unter_sum_tol"] is True

    def test_mittelung_unabhaengig_nachgerechnet(self, deko):
        with open(RESULTS_045, encoding="utf-8") as fh:
            per = json.load(fh)["t5_t6_familien_summen"]["per_pattern"]
        ref_a, ref_d = per["0"], per["4"]
        neu = max(max(abs(per[str(i)][q] - ref_a[q]) for i in ADJ_IDX)
                  for q in s4d.MEAN_BASED)
        neu = max(neu, max(abs(per[str(i)][q] - ref_d[q]) for i in DIS_IDX
                           for q in s4d.MEAN_BASED))
        assert deko["mean_based_max_within"] == neu

    def test_r_median_max_ist_045_max_within(self, deko):
        assert deko["r_median_max"] == MAX_WITHIN_045
        assert deko["reproduziert_045_max_within"] is True

    def test_r_median_einzige_verletzung(self, deko):
        assert deko["r_median_einzige_verletzung"] is True

    def test_r_median_adj_exakt(self, deko):
        assert deko["adjacent"]["r_median"] == MAX_WITHIN_045
        # Differenz der Extremmuster 6 vs 10 (Ketten-Reproduktion):
        assert R6_045 - R0_045 == pytest.approx(MAX_WITHIN_045, rel=1e-6)

    def test_r_median_dis_auch_ueber_tol(self, deko):
        # dis 3.203e-09 > SUM_TOL, aber unter dem adj-Maximum —
        # beide r_median-Verletzungen, eine max_within-Verletzung.
        assert deko["disjoint"]["r_median"] == pytest.approx(
            3.203e-09, rel=1e-2)
        assert deko["disjoint"]["r_median"] < deko["r_median_max"]

    def test_mittelung_pro_groesse(self, deko):
        assert deko["adjacent"]["k1_mean"] < s4d.SUM_TOL
        assert deko["adjacent"]["k2_mean"] < s4d.SUM_TOL
        assert deko["adjacent"]["R"] < s4d.SUM_TOL
        assert deko["disjoint"]["k1_mean"] < s4d.SUM_TOL
        assert deko["disjoint"]["k2_mean"] < s4d.SUM_TOL
        assert deko["disjoint"]["R"] < s4d.SUM_TOL


# --------------------------------------------------- committetes Diagnose-Doc

@pytest.mark.skipif(not os.path.exists(DIAG_RESULTS),
                    reason="Diagnose-Resultate noch nicht committed")
class TestCommittedDiag:
    @pytest.fixture(scope="class")
    def doc(self):
        with open(DIAG_RESULTS, encoding="utf-8") as fh:
            return json.load(fh)

    def test_status_und_basis(self, doc):
        assert doc["verdict_tragend"] is False
        assert doc["qpu"] == 0
        assert doc["basis"] == RESULTS_045
        assert doc["beobachtet_max_within_045"] == MAX_WITHIN_045

    def test_conclusions(self, doc):
        c = doc["conclusions"]
        assert c["struktur_auf_gemittelten_groessen_gruen"] is True
        assert c["r_median_einzige_verletzung"] is True
        assert c["verdict_045_unveraendert"] == "H_S4_CLOSURE_DEVIATION_FOUND"
        assert c["keine_toleranz_erhoehung"] is True

    def test_decomposition_im_doc(self, doc):
        d = doc["decomposition"]
        assert d["mean_based_unter_sum_tol"] is True
        assert d["r_median_einzige_verletzung"] is True
        assert d["reproduziert_045_max_within"] is True
        assert d["r_median_max"] == MAX_WITHIN_045

    def test_probe_a_multiset_permutation(self, doc):
        vs = doc["probe_a_multiset"]["vergleiche"]
        assert [(v["p"], v["q"]) for v in vs] == [(6, 10), (4, 7)]
        for v in vs:
            assert v["multiset_gleich_lang"] is True
            assert v["n_a"] == v["n_b"] == 78
            # sortierte Multisets elementweise im Rundungs-Korridor
            # (Median ~2-4e-9, Maximum am r~26-Ende ~1.1e-7/4.1e-7):
            assert v["sorted_elementwise_max"] < 1e-6

    def test_probe_a_elementweise_bit_exakt(self, doc):
        # deterministic re-compuation: die elementweisen Sortier-Diffs
        # sind gefrorene Werte (adj 4.08e-07 / dis 1.13e-07).
        v6, v4 = doc["probe_a_multiset"]["vergleiche"]
        assert v6["sorted_elementwise_max"] == 4.081764615193606e-07
        assert v6["sorted_elementwise_median"] == pytest.approx(
            4.2028880237188204e-09)
        assert v4["sorted_elementwise_max"] == 1.125693209758083e-07
        assert v4["sorted_elementwise_median"] == pytest.approx(
            2.40900860370985e-09)

    def test_probe_a_r_median_gleicht_045(self, doc):
        with open(RESULTS_045, encoding="utf-8") as fh:
            per = json.load(fh)["t5_t6_familien_summen"]["per_pattern"]
        vs = {(v["p"], v["q"]): v
              for v in doc["probe_a_multiset"]["vergleiche"]}
        # Median ueber die volle 78er-Familie == 045-per_pattern-Wert
        # (deterministische Re-Komputation desselben Code-Pfads, ALLE
        # vier bit-exakt).
        for p, q in [(6, 10), (4, 7)]:
            assert vs[(p, q)]["r_median_p"] == per[str(p)]["r_median"]
            assert vs[(p, q)]["r_median_q"] == per[str(q)]["r_median"]
        # Und die 6-vs-10-Streuung der Mediane IST die 045-Verletzung:
        assert vs[(6, 10)]["r_median_diff"] == (
            R6_045 - per["10"]["r_median"])
        assert vs[(6, 10)]["r_median_diff"] == pytest.approx(
            1.1384355902421817e-08)

    def test_probe_b_kette_reproduziert_beobachtung(self, doc):
        kette = doc["probe_b_kette"]["kette"]
        assert doc["probe_b_kette"]["cfg_index"] == 0
        k0 = kette[0]
        assert k0["delta"] == L3_MAX_DEV
        # Kettenglieder in den gemessenen Baendern:
        assert 1e-13 < k0["d_eig"] < 1e-12
        assert 5e-10 < k0["d_t_h"] < 1e-8
        assert 5e-9 < k0["d_r"] < 1e-7
        # dr trifft die beobachtete 6-vs-10-Differenz auf ~0.1 %
        assert k0["d_r"] == pytest.approx(
            R6_045 - 1.9147852129934473, rel=5e-3)

    def test_probe_b_r_basen(self, doc):
        pb = doc["probe_b_kette"]
        assert pb["r_basis"] == pytest.approx(1.8090388695, abs=1e-9)
        assert pb["t_h_basis"] == pytest.approx(386.0809733633, rel=1e-9)

    def test_probe_b_monoton(self, doc):
        drs = [abs(k["d_r"]) for k in doc["probe_b_kette"]["kette"]]
        assert drs[0] < drs[1] < drs[2]

    def test_t_h_quellen_asymmetrie(self, doc):
        q = doc["t_h_quellen"]
        assert q["t_h_unfold_cache"] == pytest.approx(3096.9296372343,
                                                      rel=1e-9)
        assert q["t_h_eigvals"] == pytest.approx(386.0809733633, rel=1e-9)
        assert 7 < q["quotient"] < 9
        assert q["n_pos_gaps"] == 504
        assert q["n_exkl_luecken"] == 120
        assert q["median_pos_gap"] == pytest.approx(1.627427e-02, rel=1e-3)
        assert q["r_am_eigen_t_h"] == pytest.approx(1.8090388695, abs=1e-9)
        assert q["r_am_cache_t_h"] == pytest.approx(1.9605550701, abs=1e-9)
        assert -0.2 < q["r_quell_diff"] < -0.1