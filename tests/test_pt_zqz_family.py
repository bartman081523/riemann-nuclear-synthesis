"""EXPERIMENT 053 (H-ZQZ): Tests zur geschlossenen Z/qZ-Restklassen-Familie.

Kritik1-Umsetzung Punkte (4)/(5): geschlossene Z/qZ-Statevector-Familie der
MOCS-Observablen + drittes-unabhaengiges-Observable-Gate (Renyi-3, GUE-<r>-Proxy).
Alle Tests 0 QPU, reine Statevector-Arithmetik (G1 EXAKT-STATEVECTOR).
"""
import json
import math

import numpy as np
import pytest

import pt_zqz_family as zqz
from pt_prime_state import sieve_primes, construct_P_N, measure_entropy


# ---------- Prereg / Freeze-Kette ----------

def test_prereg_exists_and_md5_matches_constant():
    with open(zqz.PREREG_PATH) as f:
        prereg = json.load(f)
    assert zqz.PREREG_MD5 != "PLACEHOLDER_REPLACE_BEFORE_FREEZE"
    assert zqz.payload_md5(prereg) == zqz.PREREG_MD5


def test_prereg_carries_quantor_coverage_required_field():
    # Kritik-Punkt (3): Quantor-Abdeckung als Prereg-Pflichtfeld.
    with open(zqz.PREREG_PATH) as f:
        prereg = json.load(f)
    qc = prereg["quantor_coverage"]
    for key in ("universe", "mode", "modulus", "classes", "n_max",
                "ex_ante", "grid_rule", "disclosure"):
        assert key in qc
    assert qc["mode"] == "closed"
    assert qc["ex_ante"] is True
    assert qc["modulus"] == [3, 5, 7]
    assert sorted(qc["classes"].keys()) == ["3", "5", "7"]
    assert qc["classes"]["3"] == [1, 2]
    assert qc["classes"]["5"] == [1, 2, 3, 4]
    assert qc["classes"]["7"] == [1, 2, 3, 4, 5, 6]


def test_verdict_ids_unique():
    ids = list(zqz.VERDICT_IDS.values())
    assert len(ids) == len(set(ids))
    assert all(ids)


# ---------- Klassen-Arithmetik (L1-Basis) ----------

def test_class_counts_index_zero_is_a_one():
    primes = sieve_primes(50)
    counts = zqz.class_counts(primes, 5)
    # Index 0 -> a=1: 11, 31, 41 ≡ 1 mod 5
    assert counts[0] == 3
    # Index 1 -> a=2: 2, 7, 17, 37, 47 ≡ 2 mod 5 (p=2 zaehlt mit!)
    assert counts[1] == 5


def test_counting_identity_full_union_for_all_q():
    # Zaehlidentitaet: sum_a pi_a + [q <= N] == pi(N) exakt (alle q).
    for N in (63, 127, 255, 1023):
        primes = sieve_primes(N)
        pi_N = len(primes)
        for q in zqz.Q_LIST:
            counts = zqz.class_counts(primes, q)
            s = sum(counts) + (1 if N >= q else 0)
            assert s == pi_N, (N, q)


def test_union_vector_exact_including_p_equals_q_term():
    # a=0 deckt p=q ab: ohne diesen Term waere die Union um 1.0 abweichend.
    for N in (15, 63, 127, 255):
        P_N, acc, scale = zqz.union_vector(N)
        dev = float(np.max(np.abs(acc - scale * P_N)))
        assert dev == 0.0, (N, dev)


# ---------- Entropie-Familie (L2-Basis) ----------

def test_schmidt_spectrum_reproduces_measure_entropy():
    for N in (127, 255, 1023):
        P_N, dim, _ = construct_P_N(N)
        s_sq, n_A, n_B = zqz.schmidt_spectrum(P_N)
        S_ref, _, nA2, nB2 = measure_entropy(P_N)
        assert (n_A, n_B) == (nA2, nB2)
        assert 1.0 - float(np.sum(s_sq)) < 1e-13
        dev = abs(zqz.s_vn_from_spectrum(s_sq) - S_ref)
        assert dev == 0.0, (N, dev)


def test_renyi_monotonicity_S3_le_S2_le_SvN():
    # Renyi-Entropie faellt monoton in alpha (natuerliche Log-Konvention).
    rng = np.random.default_rng(53)
    for _ in range(40):
        sq = rng.random(12)
        sq = np.sort(sq / sq.sum())[::-1]
        S1 = zqz.s_vn_from_spectrum(sq)
        S2 = zqz.renyi_natural(sq, 2.0)
        S3 = zqz.renyi_natural(sq, 3.0)
        assert S3 <= S2 + 1e-12, (S2, S3)
        assert S2 <= S1 + 1e-12, (S1, S2)


def test_saturation_row_N63_q5_a1_exact():
    # Ex-ante-Fund (VOR dem Freeze, im Prereg vermerkt): q=5, a=1, N=63 ->
    # vier Primzahlen (11, 31, 41, 61) perfekt diagonal im 8x8-Reshape ->
    # maximal entflochten, S = ln 4 EXAKT, R_a = 1.0 exakt (Latorre-Saettigung
    # der registrierten Obergrenze, KEINE Verletzung).
    P_N, dim, _ = construct_P_N(63)
    assert dim == 64
    vec = zqz.raw_class_vector(63, dim, 5, 1)
    assert sorted(np.nonzero(vec)[0].tolist()) == [11, 31, 41, 61]
    v = vec / math.sqrt(4.0)          # pi_a = 4 -> normalisierter Klassen-State
    s_sq, n_A, n_B = zqz.schmidt_spectrum(v)
    assert (n_A, n_B) == (8, 8)
    assert len(s_sq) == 4
    assert abs(float(np.sum(s_sq)) - 1.0) < 1e-13
    S_c = zqz.s_vn_from_spectrum(s_sq)
    assert abs(S_c - math.log(4.0)) < 1e-12
    assert abs(S_c / math.log(4.0) - 1.0) < 1e-12   # R_a = 1 exakt


# ---------- Spektral-Proxy (L3-Basis) ----------

def test_r_statistic_hand_example_is_half():
    # Luecken [1, 2, 1, 2] (aus Eigenwerten [0,1,3,4,6]) -> alle r = 1/2.
    assert abs(zqz.r_distinct_from_gaps([1.0, 2.0, 1.0, 2.0]) - 0.5) < 1e-15


def test_r_statistic_matches_reference_on_prime_spectrum():
    primes = sieve_primes(255)
    eigs = zqz.proxy_eigs_tridiag(primes)
    r_raw, r_unf, M = zqz.spacing_stats(eigs)
    assert M == len(primes) - 1
    # spacing_stats ruft r_distinct_from_gaps auf np.diff(sortiert) — gleicher Pfad
    assert abs(zqz.r_distinct_from_gaps(np.diff(np.sort(eigs))) - r_raw) == 0.0
    # Referenz: r_statistic aus pt_ququint_gue (V3-Basis) auf demselben Spektrum
    from pt_ququint_gue import r_statistic
    assert abs(r_statistic(eigs) - r_raw) < 1e-15
    assert 0.0 < r_unf < 1.0


def test_unfold_gaps_deterministic():
    d = [1.0, 3.0, 2.0, 5.0, 4.0, 1.5, 2.5, 6.0, 3.5, 2.0, 4.5]
    g1 = zqz.unfold_gaps(d)
    g2 = zqz.unfold_gaps(d)
    assert np.array_equal(g1, g2)
    assert 0.25 < float(g1.mean()) < 4.0   # Luecken nach Unfolding O(1)


def test_tridiag_matches_dense_eigvalsh_small_N():
    primes = sieve_primes(127)
    eigs_t = np.sort(zqz.proxy_eigs_tridiag(primes))
    pf = np.asarray(primes, dtype=float)
    A = np.diag(pf) + np.diag(np.abs(np.diff(pf)), 1) + \
        np.diag(np.abs(np.diff(pf)), -1)
    eigs_d = np.linalg.eigvalsh(A)
    assert np.max(np.abs(eigs_t - eigs_d)) < zqz.TRIDIAG_TOL


# ---------- Raw / Results-Kette ----------

def test_raw_has_no_verdict_keys_and_carries_frozen_chain():
    with open(zqz.RAW_PATH) as f:
        raw = json.load(f)
    with open(zqz.PREREG_PATH) as f:
        prereg = json.load(f)
    assert raw["prereg_md5"] == zqz.PREREG_MD5
    assert raw["quantor_coverage"] == prereg["quantor_coverage"]
    for key in ("verdict", "verdicts", "decide", "results"):
        assert key not in raw
    assert raw["n_sweep"] == zqz.N_SWEEP
    assert len(raw["union_rows"]) == len(zqz.N_SWEEP)
    assert len(raw["class_rows"]) == 168


def test_results_verdicts_in_frozen_allowed_set():
    with open(zqz.RESULTS_PATH) as f:
        results = json.load(f)
    allowed = set(zqz.VERDICT_IDS.values())
    assert set(results["verdicts"]) == {"l1", "l2", "l3"}
    for leg, verdict in results["verdicts"].items():
        assert verdict in allowed, (leg, verdict)
    assert results["prereg_md5"] == zqz.PREREG_MD5


def test_results_pins_union_alpha_exact():
    with open(zqz.RESULTS_PATH) as f:
        r = json.load(f)
    assert r["pins"]["pins_ok"] is True
    assert r["pins"]["max_pin_dev_S"] == 0.0
    assert r["pins"]["max_pin_dev_R"] == 0.0
    assert r["pins"]["union_vec_max_dev"] == 0.0
    assert r["pins"]["closure_ok"] is True
    assert r["class_stats"]["R_all_within_bound"] is True
    assert r["class_stats"]["n_R_at_saturation"] == 22
    assert r["alpha_combined_dev"] == 0.0
    assert repr(r["alpha_combined_recomputed"]) == repr(0.2103550767898247)


# ---------- decide()-Verdict-Zweige (synthetische Reihen) ----------

def _synthetic_raw(r_unf=None, flip_r=False):
    """Minimal-Raw (6 Union-Zeilen) mit gesteuerter <r>_unf-Serie.

    r_unf-Default [0.60, 0.55, 0.62, 0.53, 0.61, 0.66] korreliert nur
    maessig mit der steigenden R_N-Serie (rho = +0.4857 < 0.85 ->
    Kandidaten-Fall). flip_r=True macht die r-Serie monoton gegen die
    steigende R_N-Serie -> rho = +1 (Abhaengigkeits-Fall). Pins schlagen
    auf die echten 023-EXT-Werte fehl, d.h. L1 faellt in diesen Tests —
    unangetastet ist nur die L2/L3-Zweiglogik.
    """
    N_SW = [7, 15, 31, 63, 127, 255]
    r_series = r_unf if list(r_unf or []) else None
    if r_series is None and not flip_r:
        r_series = [0.60, 0.55, 0.62, 0.53, 0.61, 0.66]
    if flip_r:
        r_series = [0.55, 0.58, 0.60, 0.62, 0.64, 0.66]
    elif r_series is None:
        r_series = [None] * 6
    union = []
    for i, (N, S) in enumerate(zip(N_SW, [0.5, 0.8, 1.1, 1.4, 1.7, 2.0])):
        union.append({"N": N, "S_vN": S, "S3": S - 0.1,
                      "R_N": 0.40 + 0.06 * i, "r_raw": r_series[i],
                      "r_unf": r_series[i], "m_gaps": 10})
    classes = [{"N": N, "q": q, "a": a, "pi_a": 4, "included": True,
                "S_vN": S - 0.05, "S2": S - 0.08, "S3": S - 0.10,
                "R_a": 0.9}
               for S, N in zip([0.5, 0.8, 1.1, 1.4, 1.7, 2.0], N_SW)
               for (q, a) in ((3, 1), (5, 1))]
    return {
        "prereg_md5": zqz.PREREG_MD5, "n_sweep": N_SW,
        "union_rows": union, "class_rows": classes,
        "closure_matrix": [{"N": N, "identity_exact": True} for N in N_SW],
        "crosschecks": {"union_vec_max_dev": [0.0]},
        "constants": {"poisson_r": zqz.POISSON_R, "goe_r": zqz.GOE_R,
                      "gue_r": zqz.GUE_R, "unfold_window": zqz.UNFOLD_WINDOW},
    }


def test_decide_l3_in_band_independent_gives_candidate(tmp_path, monkeypatch):
    prereg, md5 = zqz.load_frozen(expected_md5=zqz.PREREG_MD5)
    monkeypatch.setattr(zqz, "RESULTS_PATH", str(tmp_path / "synth_results.json"))
    out = zqz.decide(_synthetic_raw(), prereg, md5)
    assert out["verdicts"]["l3"] == zqz.VERDICT_IDS["l3_candidate"]
    # Hand-Rangrechnung: r-Ranks [3,2,5,1,4,6] vs R-Ranks [1..6] -> rho=+0.4857
    assert abs(out["l3"]["rho_r_vs_R"] - 0.48571428571428577) < 1e-12


def test_decide_l3_below_band_gives_refused_out_of_band(tmp_path, monkeypatch):
    prereg, md5 = zqz.load_frozen(expected_md5=zqz.PREREG_MD5)
    monkeypatch.setattr(zqz, "RESULTS_PATH", str(tmp_path / "synth_results.json"))
    out = zqz.decide(_synthetic_raw(r_unf=[0.30] * 6), prereg, md5)
    assert out["verdicts"]["l3"] == zqz.VERDICT_IDS["l3_out_of_band"]


def test_decide_l3_monotone_correlated_gives_refused_dependent(tmp_path, monkeypatch):
    # r_unf-Serie monoton steigend gegen R_N-Serie (beide steigend) -> rho=+1.
    prereg, md5 = zqz.load_frozen(expected_md5=zqz.PREREG_MD5)
    monkeypatch.setattr(zqz, "RESULTS_PATH", str(tmp_path / "synth_results.json"))
    out = zqz.decide(_synthetic_raw(flip_r=True), prereg, md5)
    assert out["verdicts"]["l3"] == zqz.VERDICT_IDS["l3_dependent"]


def test_decide_l2_monotone_transform_is_redundant(tmp_path, monkeypatch):
    prereg, md5 = zqz.load_frozen(expected_md5=zqz.PREREG_MD5)
    monkeypatch.setattr(zqz, "RESULTS_PATH", str(tmp_path / "synth_results.json"))
    out = zqz.decide(_synthetic_raw(), prereg, md5)
    # S3 = S_vN - 0.1 ist monotone Transformation; Pools mit Float-Ties ->
    # rho = 0.9906 (nahe, nicht exakt 1) — ueber rho_cand_max = 0.85.
    assert out["l2"]["rho_S3_vs_SvN_pool"] >= out["l2"]["rho_cand_max"]
    assert out["verdicts"]["l2"] == zqz.VERDICT_IDS["l2_redundant"]


def test_decide_missing_gap_series_gives_undetermined(tmp_path, monkeypatch):
    prereg, md5 = zqz.load_frozen(expected_md5=zqz.PREREG_MD5)
    monkeypatch.setattr(zqz, "RESULTS_PATH", str(tmp_path / "synth_results.json"))
    out = zqz.decide(_synthetic_raw(r_unf=[None] * 6), prereg, md5)
    assert out["verdicts"]["l3"] == zqz.VERDICT_IDS["l3_undetermined"]


def test_decide_chain_break_aborts_with_mismatch(tmp_path, monkeypatch):
    prereg, _ = zqz.load_frozen(expected_md5=zqz.PREREG_MD5)
    monkeypatch.setattr(zqz, "RESULTS_PATH", str(tmp_path / "synth_results.json"))
    raw = _synthetic_raw()
    raw["prereg_md5"] = "0" * 32
    with pytest.raises(AssertionError, match="RAW-PREREG-MISMATCH"):
        zqz.decide(raw, prereg, zqz.PREREG_MD5)