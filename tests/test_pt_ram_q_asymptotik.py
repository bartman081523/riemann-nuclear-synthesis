"""EXPERIMENT 041 — RAM-Q Asymptotik (H-RAM-Q-2): Tests.

OFFLINE (reine numpy-Arithmetik, kein qiskit — Guard). Die Suite prueft die
q-universelle EXAKTidentitaet (Baustein B2) in beiden Formen, die q=3-Bruecke
zur gefrorenen 040-Identitaet, die q=5-034-Rueckkompatibilitaet inkl. des
Race-Term-Ankers, Strukturkorollar, Sieb- und FFT-Pfade, d-Invarianz und das
Prereg-Skelett.

Anti-Peeking: Die Suite berechnet VOR dem Freeze-Commit KEINE q=7-DFT-Profile
und KEINE Prime-DFT-Profile in den Wraparound-Regimen — alle Identitaets- und
Invarianz-Tests laufen auf SYNTHETISCHEN Residuen-Counts
(rq.synthetic_support / share_star_from_counts) bzw. reiner Algebra. Registrierte
Sieb-Counts im Prereg sind deterministische Arithmetik (wie 040). Der q=5-Anker
bindet gegen die bereits committeten 034-Konstanten
(V2_SHARE_STAR_PRIME_COMMITTED) — Rueckkopplung wie 040 T1/T2.
"""

import functools
import json
import math
import os
import sys
import tempfile

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_prime_state as ps
import pt_ququint_multin as mn
import pt_ramanujan_replication as rr
import pt_ram_q_asymptotik as ra
import pt_ram_q_zyklizitaet as rq


# === B2: Zwei Formen, eine Identitaet ===

def _random_counts(rng, q, total):
    """Zufaellige ganzzahlige Counts (n0 >= 0, Rest > 0) mit Summe total."""
    while True:
        cuts = sorted(rng.integers(0, total + 1, size=q - 1))
        parts = np.diff(np.concatenate(([0], cuts, [total])))
        if parts.min() >= 0 and parts.sum() == total:
            return [int(x) for x in parts]


def test_two_forms_identity_random_counts():
    """Geschlossene Expansion ≡ Modell+Dispersion (EXAKT, keine Naeherung)."""
    rng = np.random.default_rng(41)
    for q in (3, 5, 7, 11):
        for total in (q + 2, 50, 500):
            counts = _random_counts(rng, q, total)
            for d in (q ** 2, q ** 4):
                a = ra.unified_identity_share(counts, d)
                b = ra.unified_identity_share_closed(counts, d)
                assert abs(a - b) <= 1e-12 * max(1.0, abs(a))
                # Dekomposition: Rennen + Dispersion nicht-negativ
                m = total
                model = (m - q * counts[0]) ** 2 / ((q - 1) * d * m)
                race = q * ra.class_dispersion(counts) / (d * m)
                assert a >= model - 1e-15
                assert abs(a - (model + race)) <= 1e-15


def test_q3_delta_bridge_synthetic():
    """B2 ≡ gefrorene 040-Zweiklassen-Identitaet (sigma^2 = 2 delta^2)."""
    rng = np.random.default_rng(42)
    for _ in range(200):
        n1, n2 = int(rng.integers(0, 80)), int(rng.integers(0, 80))
        counts = [1, n1, n2]
        d = 729
        assert abs(ra.unified_identity_share(counts, d)
                   - rq.delta_identity_analytic(n1, n2, d)) <= 1e-15
    # Bei n0 != 1 bleibt B2 exakt; die delta-Form ist an n0 = 1 gebunden
    counts = [2, 3, 5]
    b2 = ra.unified_identity_share(counts, 81)
    manual = ((10 - 6) ** 2 / (2 * 81 * 10)
              + 3 * ra.class_dispersion(counts) / (81 * 10))
    assert abs(b2 - manual) <= 1e-15


def test_frozen_q3_prereg_bridge():
    """B2 ≡ delta_identity_analytic auf den GEFRORENEN 040-Counts (Algebra)."""
    doc = rq.load_frozen_prereg()
    assert doc["md5"] == ra.Q3_PREREG_MD5
    for pt in doc["prime_points"]:
        counts = pt["residue_counts_mod3"]
        b2 = ra.unified_identity_share(counts, pt["d"])
        delta = rq.delta_identity_analytic(counts[1], counts[2], pt["d"])
        assert abs(b2 - delta) <= 1e-15 * max(1.0, abs(delta))


def test_q5_equipartition_and_034_formula():
    """sigma^2 = 0 -> (m-5)^2/(4dm) — die gefrorene 034-Modellformel.

    Bei realen kleinen P gilt die Aequipartition NICHT (Race-Term):
    counts mod 5 bei P=97 sind [1,5,7,7,5] — das Modell (m-5)^2/(4dm)
    ist die sigma^2=0-Idealisierung, B2 = Modell + Race-Term.
    """
    counts_eq = [1, 28, 28, 28, 28]
    assert ra.class_dispersion(counts_eq) == 0.0
    m = sum(counts_eq)
    d = 625
    expected = (m - 5) ** 2 / (4 * d * m)
    assert abs(ra.unified_identity_share(counts_eq, d) - expected) <= 1e-18
    # Modell-Formel von rq (P-basiert) trifft die Aequipartitionsformel,
    # wenn die realen Counts equipartitioniert sind — hier synthetisch:
    assert abs(rq.model_share_star_q(97, d, 5)
               - rr.model_share_star(97, d)) <= 1e-18
    # realer Fall P=97: Aequipartition verletzt -> B2 > Modell
    _, counts97 = ra.counts_mod(97, 5)
    assert counts97 == [1, 5, 7, 7, 5]
    assert ra.class_dispersion(counts97) > 0
    assert (ra.unified_identity_share(counts97, d)
            > rq.model_share_star_q(97, d, 5))


def test_q5_anchor_tie_034_race_term():
    """Der q=5-Race-Term erklaert die 034-Ratio 1.0248 EXAKT (T1-Anker)."""
    m, counts5 = ra.counts_mod(625, 5)
    assert m == len(ps.sieve_primes(625))
    assert counts5[0] == 1  # p = 5 einziger Prime ≡ 0 mod 5
    ratio_b2 = ra.unified_ratio(counts5)
    anchor = rr.V2_SHARE_STAR_PRIME_COMMITTED / rr.model_share_star(625, 625)
    assert math.isclose(ratio_b2, anchor, rel_tol=ra.ANCHOR_TOL)
    # und direkt in Share-Space gegen die committete 034-Konstante
    d = 625
    share_b2 = ra.unified_identity_share(counts5, d)
    assert abs(share_b2 - rr.V2_SHARE_STAR_PRIME_COMMITTED) <= 1e-15


def test_ratio_ge_1_structural():
    """Strukturkorollar: ratio >= 1 IMMER; None bei m <= q (Modell-Null).

    Prime-Fall n0 = 1 (registrierte Form (m-q)^2); allgemeines n0 mit
    (m-q*n0)^2-Nenner; Modell-Null (m = q*n0 oder m <= q) -> None.
    """
    rng = np.random.default_rng(43)
    for q in (3, 5, 7):
        for _ in range(100):
            rest = _random_counts(rng, q - 1, int(rng.integers(q, 400)))
            counts = [1] + rest  # Prime-Konvention n0 = 1, m > q
            r = ra.unified_ratio(counts)
            assert r is not None and r >= 1.0
            # Registrierte Form trifft die allgemeine (n0=1)
            sigma2 = ra.class_dispersion(counts)
            assert abs(r - (1.0 + q * (q - 1) * sigma2
                            / (sum(counts) - q) ** 2)) <= 1e-15
        # Modell-Null: m = q (nur n0 und eine Klasse)
        assert ra.unified_ratio([1] + [0] * (q - 2) + [1]) is None
    # allgemeines n0: Nenner (m - q*n0)^2
    counts = [2, 3, 5]  # q=3, m=10, q*n0=6
    sigma2 = ra.class_dispersion(counts)
    assert abs(ra.unified_ratio(counts)
               - (1.0 + 3 * 2 * sigma2 / (10 - 6) ** 2)) <= 1e-15
    assert ra.unified_ratio([3, 1, 1]) is None  # m = 5 <= q*n0 = 9


def test_numpy_sieve_bit_exact():
    """numpy-Sieb ≡ pt_prime_state.sieve_primes bit-exakt."""
    for N in (10 ** 3, 10 ** 5):
        assert list(ra.numpy_primes(N)) == ps.sieve_primes(N)
    m, _ = ra.counts_mod(625, 5)
    assert m == 114


def test_fft_profile_matches_direct_sum_and_mn():
    """FFT-Pfad ≡ direkter Doppelsummen-G ≡ mn-Pfad (distincte Positionen).

    Konvention: ABSOLUT |G|^2/(dm). Bei distincten Positionen mod d
    (synthetic_support: p = r + q*t < d) ist mn's Renormalisierung ein
    No-op — beide Pfade muessen uebereinstimmen; B2 trifft das Profil.
    """
    for q, d, counts in ((3, 81, [1, 2, 1]),
                         (5, 625, [1, 3, 0, 2, 4]),
                         (7, 49, [1, 0, 3, 1, 2, 1, 1])):
        support = rq.synthetic_support(counts, d)
        # mn-Pfad (distincte Positionen -> Renormalisierung No-op)
        prof_mn = mn.single_register_profile(support, d)
        # FFT-Pfad aus Count-Vektor mod d
        cnt_d = np.bincount(np.array(support) % d, minlength=d)
        prof_fft = ra.profile_from_count_vector(cnt_d, d)
        assert np.allclose(prof_mn, prof_fft, rtol=1e-12, atol=1e-15)
        # direkte Doppelsumme (unabhaengige Konstruktion von G)
        m = len(support)
        a = np.arange(d)
        G = np.exp(2j * np.pi * np.outer(a, support) / d).sum(axis=1)
        prof_direct = np.abs(G) ** 2 / (d * m)
        assert np.allclose(prof_direct, prof_fft, rtol=1e-12, atol=1e-15)
        # share ueber alle drei Pfade identisch
        s_mn = rq.share_star_q(prof_mn, d, q)
        s_fft = rq.share_star_q(prof_fft, d, q)
        s_dir = rq.share_star_q(prof_direct, d, q)
        assert abs(s_mn - s_fft) <= 1e-14 and abs(s_dir - s_fft) <= 1e-14
        # und B2 trifft das synthetische Profil EXAKT (Identitaet gilt
        # fuer ALLE Counts)
        assert abs(s_fft - ra.unified_identity_share(counts, d)) <= 1e-14


def test_fft_profile_with_wraparound_counts():
    """Wraparound-Multiplizitaet: B2 bleibt EXAKT unter ABSOLUT-Konvention.

    Positionen p = r + t*d (t = 0..n_r-1) kollidieren mod d — der
    Count-Vektor mod d bekommt Multiplizitaet (sum_r n_r^2 > m), die
    mn-Renormalisierung ist KEIN No-op mehr (direkt gemessener Befund an
    (211,81): Residual 6.5e-2 unter mn-Pfad). Der FFT-Pfad misst ABSOLUT
    und B2 trifft ihn trotzdem — gebunden gegen die Doppelsumme.
    """
    q, d = 7, 49
    counts = [1, 3, 0, 5, 2, 4, 1]
    support = []
    for r, n in enumerate(counts):
        start = r if r else q
        support.extend([start + t * d for t in range(n)])  # Kollision mod d
    m = len(support)
    a = np.arange(d)
    G = np.exp(2j * np.pi * np.outer(a, support) / d).sum(axis=1)
    prof_direct = np.abs(G) ** 2 / (d * m)
    cnt_d = np.bincount(np.array(support) % d, minlength=d)
    prof_fft = ra.profile_from_count_vector(cnt_d, d)
    assert np.allclose(prof_direct, prof_fft, rtol=1e-12, atol=1e-15)
    # Multiplizitaet wirklich vorhanden: sum cnt^2 > m
    assert int((cnt_d.astype(np.int64) ** 2).sum()) > m
    s = rq.share_star_q(prof_fft, d, q)
    assert abs(s - ra.unified_identity_share(counts, d)) <= 1e-13
    # mn-Pfad (renormalisiert) misst die MASSE-FRAKTION, nicht absolut —
    # dokumentiertes Konvention-Verhalten:
    prof_mn = mn.single_register_profile(support, d)
    assert abs(prof_mn.sum() - 1.0) <= 1e-12
    assert prof_fft.sum() > 1.0 + 1e-9  # sum_r n_r^2/m > 1
    s_mn = rq.share_star_q(prof_mn, d, q)
    assert abs(s_mn - s) > 1e-6


def test_d_invariance_exact():
    """d-Invarianz-Theorem: d*share*|G-Masse| haengt nur von Counts mod q ab."""
    rng = np.random.default_rng(45)
    for q, d_grid in ((3, (9, 81, 729)), (5, (25, 625)), (7, (49, 343, 2401))):
        counts = _random_counts(rng, q, 60)
        counts[0] = 1
        vals = [d * ra.unified_identity_share(counts, d) * sum(counts)
                for d in d_grid]
        ref = vals[-1]
        for v in vals:
            assert abs(v - ref) <= 1e-9 * max(1.0, abs(ref))
    # analytisch: die Groesse IST die geschlossene Summe (unabhaengig von d)
    # q=3, counts [1,2,5]: (q-1)n0^2 - 2n0*A + q*sum(n_r^2) - A^2,
    # A = m - n0 = 7 -> 2 - 14 + 3*29 - 49 = 26
    counts = [1, 2, 5]
    m = sum(counts)
    closed = 2 * 1 - 2 * 1 * 7 + 3 * (4 + 25) - 7 ** 2
    assert closed == 26
    assert abs(729 * ra.unified_identity_share(counts, 729) * m - closed) <= 1e-9
    assert abs(9 * ra.unified_identity_share(counts, 9) * m - closed) <= 1e-9


def test_null_model_m_equal_q():
    """m = q: Race-Term IST die gesamte Masse — q*sigma^2/(dm) EXAKT.

    Reine Algebra auf den registrierten Counts (P=17, mod 7 und P=5, mod 3);
    die DFT-Messung dieser Punkte erfolgt erst nach dem Freeze-Commit.
    """
    counts7 = [1, 0, 1, 2, 1, 1, 1]  # Primes <= 17 mod 7 (Sieb-Arithmetik)
    m = sum(counts7)
    assert m == 7
    assert abs(ra.unified_identity_share(counts7, 49)
               - ra.race_only_share(counts7, 49)) <= 1e-18
    assert abs(ra.race_only_share(counts7, 49) - 2.0 / 49.0) <= 1e-15
    counts3 = [1, 0, 2]  # Primes <= 5 mod 3
    assert abs(ra.race_only_share(counts3, 9) - 2.0 / 9.0) <= 1e-15
    assert abs(ra.unified_identity_share(counts3, 9)
               - rq.delta_identity_analytic(0, 2, 9)) <= 1e-18


def test_loglog_slope_helper():
    """Slope-Helfer: exaktes Potenzgesetz -> -1; ratio <= 1 -> ValueError."""
    rows = [{"P": float(10 ** k), "ratio": 1.0 + 7.0 / 10 ** k}
            for k in (3, 4, 5, 6, 7)]
    assert abs(ra.loglog_slope(rows) + 1.0) <= 1e-9
    with pytest.raises(ValueError):
        ra.loglog_slope([{"P": 100.0, "ratio": 1.0}, {"P": 1000.0, "ratio": 1.2}])


def test_prereg_structure_no_measured_fields():
    """Prereg-Skelett: registrierte Arithmetik, KEINE gemessenen Felder."""
    payload = ra.build_prereg_payload()
    forbidden = {"share_measured", "ratio_measured", "measured", "in_band",
                 "residual", "residuals", "d_inv_residual", "results"}
    def _walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                assert k not in forbidden, f"gemessenes Feld registriert: {k}"
                _walk(v)
        elif isinstance(node, list):
            for v in node:
                _walk(v)
    _walk(payload)
    # Punkte-Struktur: (17,49) null-deskriptiv + 4 Band-Punkte auf 2401
    pts = payload["prime_points"]
    assert [(p["P"], p["d"], p["role"]) for p in pts] == [
        (17, 49, "null_deskriptiv"),
        (10 ** 4, 2401, "band"), (10 ** 5, 2401, "band"),
        (10 ** 6, 2401, "band"), (10 ** 7, 2401, "band"),
    ]
    assert payload["gated_points"] == [[10 ** k, 2401] for k in (4, 5, 6, 7)]
    # registrierte Counts sind deterministische Sieb-Arithmetik
    # (unabhaengig ueber pt_prime_state nachgerechnet)
    for pt in pts:
        primes = ps.sieve_primes(pt["P"])
        expect = [0] * 7
        for p in primes:
            expect[p % 7] += 1
        assert pt["residue_counts_mod7"] == expect
        assert pt["pi"] == len(primes)
        # B2-Vorhersagen konsistent mit den registrierten Counts
        assert abs(pt["b2_share_exact"]
                   - ra.unified_identity_share(expect, pt["d"])) <= 1e-15
        assert abs(pt["sigma2"] - ra.class_dispersion(expect)) <= 1e-15
    # Band-Schwellen in Share-Space, Gate nur auf d=2401
    for pt in pts:
        if pt["role"] == "band":
            assert pt["gated"] is True
            assert abs(pt["band_lo"] - ra.BAND_LO * pt["model"]) <= 1e-15
            assert abs(pt["band_hi"] - ra.BAND_HI * pt["model"]) <= 1e-15
            assert pt["model"] == (pt["pi"] - 7) ** 2 / (6.0 * pt["d"] * pt["pi"])
        else:
            assert pt["gated"] is False
            assert pt["band_lo"] is None and pt["band_hi"] is None
    # Verdict-Map und Kontrollfamilie vollstaendig registriert
    for key in ("t1_q5_anchor", "t2_q3_bridge", "t3_d_invariance_q3",
                "t4_ratio_ge_1_structural", "t5_gate_set_frozen",
                "t6_null_points_exact"):
        assert key in payload["controls"]
    assert set(payload["verdict_map"]) == {
        ra.VERDICT_CONFIRMED, ra.VERDICT_PARTIAL, ra.VERDICT_REFUTED,
        ra.VERDICT_INVALID}
    assert payload["qpu"] == ("0 QPU — reine Arithmetik (numpy-Sieb + FFT), "
                              "offline, kein Quanten-SDK")


def test_freeze_roundtrip_and_tamper():
    """Freeze -> md5 -> verify -> load; Tamper wird erkannt."""
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "prereg.json")
        doc = ra.freeze_prereg(path=path)
        assert ra.verify_prereg_md5(doc)
        loaded = ra.load_frozen_prereg(path)
        assert loaded["md5"] == doc["md5"]
        with open(path, encoding="utf-8") as fh:
            tampered = json.load(fh)
        tampered["prime_points"][0]["b2_share_exact"] *= 2.0
        assert not ra.verify_prereg_md5(tampered)
        bad = os.path.join(td, "bad.json")
        with open(bad, "w", encoding="utf-8") as fh:
            json.dump(tampered, fh)
        with pytest.raises(ValueError, match="MISMATCH"):
            ra.load_frozen_prereg(bad)


def test_offline_guard():
    src = open("pt_ram_q_asymptotik.py", encoding="utf-8").read()
    for banned in ("qiskit", "IBMQ_TOKEN", "os.environ"):
        assert banned not in src

# === Post-Freeze-Pinning (analog Phase 7): die committete Results-Datei
# bindet Verdict, Kontrollen, Wraparound-Identitaet und Scan-Erwartungen;
# ein leichter Live-Recompute belegt, dass sie aus DEMSELBEN Code-Pfad
# stammt wie das aktuelle Modul (42s-Auswertung selbst NICHT doppelt). ===

RESULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "pt_ram_q_asymptotik_results.json")


@functools.lru_cache(maxsize=1)
def _results():
    with open(RESULTS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def test_evaluation_results_pinned():
    """Verdict, Kontrollen, md5, Residuals + Wraparound-Identitaet gepinnt."""
    res = _results()
    assert res["verdict"] == ra.VERDICT_CONFIRMED
    assert res["gated_total"] == 4 and res["gated_outside"] == 0
    assert res["prereg_md5"] == "704916f946beedf49c51ab6bc9bf37bd"
    for key in ("t1_q5_anchor", "t2_q3_bridge", "t3_d_invariance_q3",
                "t4_ratio_ge_1_structural", "t5_gate_set_frozen",
                "t6_null_points_exact"):
        assert res["controls"][key] is True, f"Kontrolle {key} nicht True"
    # Identitaets-Residual auf Fließkomma-Rauschen (gemessen 1.8e-15)
    assert res["max_residual"] < 1e-10
    # d-Invarianz bei Wraparound (P=1e7 >> d=2401) — die scharfste
    # neue Pruefung: gemessen 1.4e-16
    assert res["max_d_inv_residual"] < 1e-10
    # Null-Punkt (17,49): gemessen = 2/49 EXAKT (Race-Term IST die Masse)
    null_row = next(r for r in res["q7_rows"] if r["P"] == 17)
    assert null_row["gated"] is False and null_row["in_band"] is None
    assert null_row["ratio_measured"] is None
    assert abs(null_row["share_measured"] - 2.0 / 49.0) <= 1e-15
    assert null_row["share_measured"] == null_row["b2_share_exact"]
    assert null_row["residual"] == 0.0
    # Band-Punkte: ratio_measured trifft ratio_pred_exact, alle im Band
    gated_rows = [r for r in res["q7_rows"] if r["gated"]]
    assert [r["P"] for r in gated_rows] == [10 ** k for k in (4, 5, 6, 7)]
    for r in gated_rows:
        assert r["in_band"] is True
        assert math.isclose(r["ratio_measured"], r["ratio_pred_exact"],
                            rel_tol=1e-12), f"P={r['P']}"
        assert r["residual"] < 1e-10


def test_d_invariance_wraparound_pinned():
    """d-Invarianz bei Wraparound: d*share*m identisch ueber {49,2401},
    share skaliert exakt 1/d; Live-Recompute bei P=1e4 aus DEMSELBEN Pfad."""
    res = _results()
    m = 1229  # pi(1e4), registriert
    for row in res["d_invariance"]:
        d1, d2 = row["d_pair"]
        # Invariante d*share*m ueber beide d identisch
        v1, v2 = d1 * row["share_d49"] * m, d2 * row["share_d2401"] * m
        assert abs(v1 - v2) <= 1e-8 * max(1.0, abs(v1))
        # Skalierung share ~ 1/d exakt (49 = d1/d2-Faktor)
        assert abs(row["share_d49"] / row["share_d2401"] - 49.0) <= 1e-9
    # Live-Recompute (P=1e4, beide d) aus measure_share trifft die Datei
    s49, _, _ = ra.measure_share(10 ** 4, 49, 7)
    s2401, _, _ = ra.measure_share(10 ** 4, 2401, 7)
    row = res["d_invariance"][0]
    assert abs(s49 - row["share_d49"]) <= 1e-12
    assert abs(s2401 - row["share_d2401"]) <= 1e-12
    assert abs(s49 / s2401 - 49.0) <= 1e-9


def test_pinned_fft_matches_mn_small_p():
    """Kleines P < d (kein Wraparound): FFT-Pfad ≡ mn-Pfad (Renormalisierung
    No-op) — Bindung an die 040-Konvention, hier am q=5-Punkt (97, 625)."""
    s_fft, counts, m = ra.measure_share(97, 625, 5)
    primes = ps.sieve_primes(97)
    assert m == len(primes) == 25
    prof_mn = mn.single_register_profile(primes, 625)
    s_mn = rq.share_star_q(prof_mn, 625, 5)
    assert abs(s_fft - s_mn) <= 1e-12
    # und B2 trifft den kleinen Prime-Punkt exakt (Race-Term sichtbar)
    assert abs(s_fft - ra.unified_identity_share(counts, 625)) <= 1e-14
    assert ra.unified_ratio(counts) > 1.0  # counts [1,5,7,7,5]: sigma2 > 0


def test_pinned_scans_and_extension():
    """Skans q in {3,5}: Slope im registrierten Band, C_max unter Schranke,
    1e8-Erweiterung deskriptiv (ratio >= 1, C_p klein, Envelope fallend)."""
    res = _results()
    for q, d in (("3", 729), ("5", 625)):
        sc = res["scans"][q]
        assert sc["slope_in_registered_band"] is True
        assert ra.SLOPE_BAND[0] <= sc["slope"] <= ra.SLOPE_BAND[1]
        assert sc["c_max_ok"] is True
        assert sc["envelope_decreasing"] is True
        ext = sc["extension_row_deskriptiv"]
        assert ext["d"] == d and ext["pi"] == 5761455
        assert ext["ratio"] >= 1.0
        assert ext["c_p"] <= ra.C_MAX
        # ratio trifft die B2-Identitaet aus den registrierten Counts
        b2 = ra.unified_identity_share(ext["residue_counts"], ext["d"])
        assert abs(ext["share_b2"] - b2) <= 1e-9 * max(1.0, b2)
        assert abs(ext["ratio"] - b2 / ext["model"]) <= 1e-12
