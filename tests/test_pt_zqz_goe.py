"""EXPERIMENT 054 (pt_zqz_goe) — Tests.

Fokus: SHA-256-Freeze-Kette (kanonischer Payload-Hash, an beiden
Call-Sites erzwungen — 053-Lektion), Sampler-Validierung (Determinismus,
Klassenordnung GOE/GUE/Poisson), L0/L1/L2/L3-Verdict-Logik synthetisch
(monkeypatch, keine echten Artefakt-Writes; RESULTS_PATH immer nach
tmp_path umgelenkt — Clobber-Lektion aus 053).
"""
import json

import numpy as np
import pytest

import pt_zqz_family as fam
import pt_zqz_goe as m
from pt_prime_state import sieve_primes


# ---------- Prereg-Pin-Politik (SHA-256, User-Direktive) ----------

def test_prereg_pin_sha256_format():
    assert m.PREREG_SHA256 is not None
    assert len(m.PREREG_SHA256) == 64
    int(m.PREREG_SHA256, 16)  # hex-decodierbar (kein MD5-Format)


def test_committed_prereg_matches_frozen_checksum():
    payload, dig = m.load_frozen(m.PREREG_PATH,
                                 expected_sha256=m.PREREG_SHA256)
    assert dig == m.PREREG_SHA256
    assert payload["experiment"] == "EXPERIMENT 054"
    assert payload["date_locked"] == "2026-10-05"
    assert payload["branch"] == "h-test1-gap-invariance"


def test_source_anchor_sha256():
    """Eingang ist die COMMITTETE 053-Messseite, gepinnt via SHA-256."""
    p, _ = m.load_frozen(m.PREREG_PATH)
    assert p["input_scope"]["source_path"] == "pt_zqz_family_raw.json"
    assert p["input_scope"]["source_sha256"] == \
        m.sha256_file(m.SOURCE_RAW_PATH)


def test_canonical_hash_serialization_independent(tmp_path):
    """053-Lektion als Regression: indent-1-File und Compact-
    Serialisierung muessen denselben KANONISCHEN SHA-256 ergeben."""
    payload = m.build_prereg_payload()
    dig = m.payload_sha256(payload)
    a = tmp_path / "indent.json"
    b = tmp_path / "compact.json"
    with open(a, "w", encoding="utf-8") as f:
        json.dump(payload, f, sort_keys=True, separators=(",", ":"),
                  ensure_ascii=False, indent=1)
    with open(b, "w", encoding="utf-8") as f:
        json.dump(payload, f, sort_keys=True, separators=(",", ":"),
                  ensure_ascii=False)
    _, dig_a = m.load_frozen(str(a), expected_sha256=dig)
    _, dig_b = m.load_frozen(str(b), expected_sha256=dig)
    assert dig_a == dig_b == dig


def test_load_frozen_rejects_broken_chain(tmp_path):
    payload = m.build_prereg_payload()
    p = tmp_path / "p.json"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, sort_keys=True, indent=1)
    with pytest.raises(SystemExit):
        m.load_frozen(str(p), expected_sha256="0" * 64)


def test_prereg_thresholds_and_audit_frozen_exact():
    p, _ = m.load_frozen(m.PREREG_PATH)
    assert p["thresholds"] == {
        "z_band_k": 2.0, "l0_k": 4.0, "l3_rho_max": 0.5,
        "l0_dim": 256, "l0_n": 512,
        "poisson_sanity_dim": 512, "band_sigma_min": 1e-9,
    }
    assert p["methodology"]["n_mc"] == 1024
    assert p["methodology"]["chunk"] == 128
    assert "sharpshooter_audit" in p
    assert "gefroren" in p["sharpshooter_audit"]
    assert p["inherited_verdicts"]["exp_053_l3"] == \
        "H_ZQZ_L3_REFUSED_OUT_OF_BAND (unverändert)"


def test_verdict_ids_complete_and_unique():
    slugs = list(m.build_prereg_payload()["verdict_ids"].values())
    assert len(slugs) == len(set(slugs))
    assert all(s.startswith("H_ZQZ_GOE_") for s in slugs)
    for needed in ("H_ZQZ_GOE_L1_GOE_BAND_GEHALTEN",
                   "H_ZQZ_GOE_L1_GOE_BAND_VERFEHLT",
                   "H_ZQZ_GOE_L2_KLASSE_GOE_DOMINANT",
                   "H_ZQZ_GOE_L3_RESIDUEN_OHNE_TREND"):
        assert needed in slugs


# ---------- Konventions-Share + Design-Identität mit 053 ----------

def test_statistics_convention_shared_with_053():
    """Statistik-Kern ist IMPORT (Funktionsobjekt-Identität), nicht Kopie."""
    assert m.spacing_stats is fam.spacing_stats
    assert m.r_distinct_from_gaps is fam.r_distinct_from_gaps
    assert m.unfold_gaps is fam.unfold_gaps
    assert m.UNFOLD_WINDOW == fam.UNFOLD_WINDOW
    assert m.N_SWEEP == fam.N_SWEEP
    assert (m.POISSON_R, m.GOE_R, m.GUE_R) == \
        (fam.POISSON_R, fam.GOE_R, fam.GUE_R)


def test_d_match_rule_matches_source_pi_N():
    src = json.load(open(m.SOURCE_RAW_PATH))
    for row in src["union_rows"]:
        assert row["pi_N"] == len(sieve_primes(row["N"]))
        assert row["m_gaps"] == row["pi_N"] - 1


# ---------- Sampler: β-Hermite-Referenzen ----------

def test_cell_seed_deterministic_and_distinct():
    s1 = m.cell_seed("goe_tridiag", 6542)
    assert s1 == m.BASE_SEED + 1 * m.SEED_STRIDE + 6542
    assert s1 == m.cell_seed("goe_tridiag", 6542)
    codes = {m.cell_seed(k, 257)
             for k in ("goe_tridiag", "gue_tridiag", "poisson")}
    assert len(codes) == 3


def test_class_stats_deterministic_and_scale_invariant():
    a = m.class_stats(16, "goe_tridiag", 24)
    b = m.class_stats(16, "goe_tridiag", 24)
    assert a["r_unf_mean"] == b["r_unf_mean"]
    assert a["r_unf_std"] == b["r_unf_std"]
    rng = np.random.default_rng(7)
    eigs = np.sort(rng.uniform(0.0, 10.0, size=40))
    r1_raw, r1_unf, _ = m.spacing_stats(eigs)
    r2_raw, r2_unf, _ = m.spacing_stats(eigs * 1e6)
    assert abs(r1_raw - r2_raw) < 1e-12
    assert abs(r1_unf - r2_unf) < 1e-12


def test_beta_hermite_deterministic_matrix_shape():
    rng1 = np.random.default_rng(11)
    rng2 = np.random.default_rng(11)
    e1 = m.beta_hermite_eigs_chunk(6, 2, 3, rng1)
    e2 = m.beta_hermite_eigs_chunk(6, 2, 3, rng2)
    assert e1.shape == (3, 6)
    assert np.array_equal(e1, e2)
    assert np.all(np.diff(e1, axis=1) >= -1e-14)  # sortiert


def test_class_order_goegue_poisson_direction():
    """Robuste Ordnung bei kleinem d: GUE > GOE > Poisson (Richtung,
    kein Band-Gate — Referenzdesign-Basis)."""
    goe = m.class_stats(64, "goe_tridiag", 64)
    gue = m.class_stats(64, "gue_tridiag", 64)
    poi = m.class_stats(64, "poisson", 64)
    assert gue["r_unf_mean"] > goe["r_unf_mean"]
    assert goe["r_unf_mean"] > poi["r_unf_mean"]


# ---------- L0-/L1-Lauf-Gate-Logik ----------

def test_two_sample_gate():
    dev, k, ok = m._two_sample_k(0.5308, 0.03, 512,
                                 0.5309, 0.03, 512, 4.0)
    assert ok and dev < k
    _, _, ok2 = m._two_sample_k(0.5300, 0.03, 512,
                                0.5320, 0.03, 512, 0.5)
    assert not ok2


def test_run_measurement_guard_blocks_silent_rerun(tmp_path, monkeypatch):
    raw = tmp_path / "raw.json"
    raw.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(m, "RAW_PATH", str(raw))
    with pytest.raises(SystemExit):
        m.run_measurement()


def test_source_mismatch_breaks_chain(tmp_path, monkeypatch):
    fake = tmp_path / "src.json"
    fake.write_text('{"union_rows": []}', encoding="utf-8")
    monkeypatch.setattr(m, "SOURCE_RAW_PATH", str(fake))
    payload = m.build_prereg_payload()
    dig = m.payload_sha256(payload)
    raw = {"prereg_sha256": dig,
           "source": {"sha256": "a" * 64},
           "mc_rows": [], "d_match": {}, "constants": {},
           "validation": {}}
    monkeypatch.setattr(m, "RESULTS_PATH", str(tmp_path / "res.json"))
    # decide() bricht an der Eingangs-Pin-Pruefung mit AssertionError
    # (SystemExit ist der Fall am LAUF in run_measurement)
    with pytest.raises(AssertionError):
        m.decide(raw, payload, dig)


# ---------- decide() end-to-end synthetisch ----------

def make_synthetic(monkeypatch, rows, r_unf_of, tmp_path,
                   source_rewrite=None):
    """rows: [(N, d)]; r_unf_of(N, d, stats) -> r_unf. Quelle wird VOR
    dem Prereg-Pin finalisiert (sonst SHA-Mismatch); RESULTS_PATH nach
    tmp_path umgelenkt. Rueckgabe (raw, payload, dig, stats_by_key)."""
    stats_by_key = {}
    union = []
    d_match = {}
    mc_rows = []
    for N, d in rows:
        d_match[str(N)] = d
        for key in ("goe_tridiag", "gue_tridiag", "poisson"):
            st = m.class_stats(d, key, 16)
            stats_by_key[(key, d)] = st
            mc_rows.append(dict(st))
    union = []
    for (N, d) in rows:
        union.append({"N": N, "r_unf": r_unf_of(N, d, stats_by_key),
                      "r_raw": None, "m_gaps": d - 1, "pi_N": d,
                      "R_N": 0.0, "S_vN": 0.0, "S2": 0.0, "S3": 0.0})
    for u in union:
        u["r_raw"] = u["r_unf"]
    src = tmp_path / "src.json"
    src.write_text(json.dumps({"union_rows": union}), encoding="utf-8")
    monkeypatch.setattr(m, "SOURCE_RAW_PATH", str(src))
    monkeypatch.setattr(m, "RESULTS_PATH", str(tmp_path / "res.json"))
    payload = m.build_prereg_payload()
    payload["grid"]["n_sweep"] = [N for N, _ in rows]
    dig = m.payload_sha256(payload)
    raw = {
        "prereg_sha256": dig,
        "numpy_build": np.__version__,
        "source": {"path": m.SOURCE_RAW_PATH,
                   "sha256": payload["input_scope"]["source_sha256"]},
        "n_sweep": payload["grid"]["n_sweep"],
        "d_match": d_match,
        "mc_rows": mc_rows,
        "validation": {
            # Schluessel heißen wie die Produktions-Zellen; fuer die
            # Tests reichen kleine Dimensionen (deterministisch,
            # kein Artefakt-Write).
            "goe_tridiag_d256": m.class_stats(64, "goe_tridiag", 32),
            "goe_dense_d256": m.class_stats(64, "goe_dense", 32),
            "gue_tridiag_d256": m.class_stats(64, "gue_tridiag", 32),
            "gue_dense_d256": m.class_stats(64, "gue_dense", 32),
            "poisson_d512": m.class_stats(64, "poisson", 32),
        },
        "constants": {"poisson_r": m.POISSON_R, "goe_r": m.GOE_R,
                      "gue_r": m.GUE_R, "unfold_window": m.UNFOLD_WINDOW},
    }
    return raw, payload, dig, stats_by_key


def test_decide_end_to_end_nearest_class(tmp_path, monkeypatch):
    """Drei Punkte exakt auf den jeweiligen Klassenmitteln: nearest z
    muss DIE Klasse erkennen; POISSON-Endpunkt weit unter dem GOE-Band.

    GUE-Mittel bei d=54 liegt ~2.3sigma UEber dem GOE-Mittel -> sauber
    ausserhalb des ±2sigma-L1-Bands -> VERFEHLT ist die korrekte L1-
    Physik (die Klassen-Erkennung wird ueber nearest geprueft)."""
    rows = [(7, 4), (31, 11), (255, 54)]
    nearest = {"goe_tridiag": "GOE", "gue_tridiag": "GUE",
               "poisson": "Poisson"}
    for target, expected_l1 in (
            ("goe_tridiag", "H_ZQZ_GOE_L1_GOE_BAND_GEHALTEN"),
            ("gue_tridiag", "H_ZQZ_GOE_L1_GOE_BAND_VERFEHLT"),
            ("poisson", "H_ZQZ_GOE_L1_GOE_BAND_VERFEHLT")):
        def r_of(N, d, stats, _t=target):
            return stats[(_t, d)]["r_unf_mean"]

        raw, payload, dig, _ = make_synthetic(monkeypatch, rows, r_of,
                                              tmp_path)
        res = m.decide(raw, payload, dig)
        assert res["verdicts"]["l0"] == \
            "H_ZQZ_GOE_L0_VALIDIERUNG_GEHALTEN", res["verdicts"]
        assert res["verdicts"]["l1"] == expected_l1
        # End-to-end-Kern: die parameterfreie nearest-z-Klassifikation
        # erkennt die platzierte Klasse am Endpunkt.
        assert res["series_table"][-1]["nearest"] == nearest[target]
        assert res["class_counts"]["n_tie"] == 0
        assert res["l1"]["z_goe"] is not None


def test_decide_l1_band_in_out(tmp_path, monkeypatch):
    rows = [(7, 4), (31, 11), (255, 54)]

    def band_series(N, d, stats):
        return stats[("goe_tridiag", d)]["r_unf_mean"]

    raw, payload, dig, _ = make_synthetic(monkeypatch, rows, band_series,
                                          tmp_path)
    res = m.decide(raw, payload, dig)
    assert res["verdicts"]["l1"] == "H_ZQZ_GOE_L1_GOE_BAND_GEHALTEN"
    assert res["l1"]["band_goe"] is not None

    def far_series(N, d, stats):
        g = stats[("goe_tridiag", d)]
        return g["r_unf_mean"] - 10 * g["r_unf_std"] - 1e-12

    raw2, payload2, dig2, _ = make_synthetic(monkeypatch, rows, far_series,
                                             tmp_path)
    res2 = m.decide(raw2, payload2, dig2)
    assert res2["verdicts"]["l1"] == "H_ZQZ_GOE_L1_GOE_BAND_VERFEHLT"


def test_decide_l2_dominanz_und_entschieden(tmp_path, monkeypatch):
    """Parameterfreie Dominanz (Endpunkt im 4er-Synthetik-Gitter)."""
    rows = [(7, 4), (31, 11), (255, 54), (1023, 172)]

    def goe_lead(N, d, stats):
        if N == 31:
            return stats[("poisson", d)]["r_unf_mean"]
        return stats[("goe_tridiag", d)]["r_unf_mean"]

    raw, payload, dig, _ = make_synthetic(monkeypatch, rows, goe_lead,
                                          tmp_path)
    res = m.decide(raw, payload, dig)
    cc = res["class_counts"]
    assert cc["n_goe"] == 3 and cc["n_poisson"] == 1
    assert res["verdicts"]["l2"] == "H_ZQZ_GOE_L2_KLASSE_GOE_DOMINANT"

    def other(N, d, stats):
        if N == 7:
            return stats[("gue_tridiag", d)]["r_unf_mean"]
        if N == 31:
            return stats[("gue_tridiag", d)]["r_unf_mean"]
        return stats[("poisson", d)]["r_unf_mean"]

    raw2, payload2, dig2, _ = make_synthetic(monkeypatch, rows, other,
                                             tmp_path)
    res2 = m.decide(raw2, payload2, dig2)
    cc2 = res2["class_counts"]
    assert cc2["n_goe"] == 0 and cc2["n_gue"] == 2 and cc2["n_poisson"] == 2
    assert res2["verdicts"]["l2"] == "H_ZQZ_GOE_L2_KLASSE_ANDERE_DOMINANT"


def test_decide_l2_tie_fallback_unentschieden(tmp_path, monkeypatch):
    """GOE unter den Count-Leadern, aber geteilt -> UNENTSCHIEDEN."""
    rows = [(7, 4), (31, 11), (255, 54), (1023, 172)]

    def split(N, d, stats):
        return (stats[("goe_tridiag", d)] if N in (7, 31)
                else stats[("poisson", d)])["r_unf_mean"]

    raw, payload, dig, _ = make_synthetic(monkeypatch, rows, split,
                                          tmp_path)
    res = m.decide(raw, payload, dig)
    cc = res["class_counts"]
    assert cc["n_goe"] == 2 and cc["n_poisson"] == 2
    assert res["verdicts"]["l2"] == "H_ZQZ_GOE_L2_UNENTSCHIEDEN"


def test_decide_l3_trend_vs_flat(tmp_path, monkeypatch):
    rows = [(7, 4), (31, 11), (255, 54), (1023, 172)]

    def trend(N, d, stats):
        return stats[("goe_tridiag", d)]["r_unf_mean"] + \
            {"7": 0.03, "31": 0.02, "255": 0.01, "1023": 0.0}[str(N)]

    raw, payload, dig, _ = make_synthetic(monkeypatch, rows, trend,
                                          tmp_path)
    res = m.decide(raw, payload, dig)
    assert res["l3"]["rho_residual_logN"] == pytest.approx(-1.0,
                                                           abs=1e-12)
    assert res["verdicts"]["l3"] == "H_ZQZ_GOE_L3_RESIDUEN_TREND_AN"

    def flat(N, d, stats):
        return stats[("goe_tridiag", d)]["r_unf_mean"] + \
            {"7": 0.02, "31": -0.01, "255": 0.04, "1023": -0.015}[str(N)]

    raw2, payload2, dig2, _ = make_synthetic(monkeypatch, rows, flat,
                                             tmp_path)
    res2 = m.decide(raw2, payload2, dig2)
    assert abs(res2["l3"]["rho_residual_logN"]) < 0.5
    assert res2["verdicts"]["l3"] == "H_ZQZ_GOE_L3_RESIDUEN_OHNE_TREND"


def test_decide_d_match_violation_asserts(tmp_path, monkeypatch):
    rows = [(7, 4), (31, 11), (255, 54)]

    def ok(N, d, stats):
        return stats[("goe_tridiag", d)]["r_unf_mean"]

    raw, payload, dig, _ = make_synthetic(monkeypatch, rows, ok, tmp_path)
    src = json.load(open(m.SOURCE_RAW_PATH))
    src["union_rows"][0]["pi_N"] = src["union_rows"][0]["pi_N"] + 1
    # Pins nachziehen, damit decide() bis zum pi_N-Assert durchlaeuft
    with open(m.SOURCE_RAW_PATH, "w", encoding="utf-8") as f:
        json.dump(src, f)
    payload["input_scope"]["source_sha256"] = m.sha256_file(
        m.SOURCE_RAW_PATH)
    raw["source"]["sha256"] = payload["input_scope"]["source_sha256"]
    with pytest.raises(AssertionError):
        m.decide(raw, payload, dig)


def _keys_deep(obj):
    """Alle Keys einer (verschachtelten) json-faehigen Struktur."""
    out = set()

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                out.add(k)
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(obj)
    return out


def test_results_no_mc_rows_leak(tmp_path, monkeypatch):
    """Results tragen KEINEN Key 'mc_rows' (Rohwerte bleiben in der
    pt_zqz_goe_raw.json); Key-Check rekursiv statt Substring im Blob —
    res spiegelt source_path (tmp-dir-Name leitet sich vom Testnamen
    ab und wuerde sonst sich selbst matchen)."""
    rows = [(7, 4), (31, 11), (255, 54)]

    def ok(N, d, stats):
        return stats[("goe_tridiag", d)]["r_unf_mean"]

    raw, payload, dig, _ = make_synthetic(monkeypatch, rows, ok, tmp_path)
    res = m.decide(raw, payload, dig)
    assert "mc_rows" not in _keys_deep(res)
    assert res["verdicts"]["l2"] in (
        "H_ZQZ_GOE_L2_KLASSE_GOE_DOMINANT",
        "H_ZQZ_GOE_L2_KLASSE_ANDERE_DOMINANT",
        "H_ZQZ_GOE_L2_UNENTSCHIEDEN")
    assert res["class_counts"]["n_points"] == 3