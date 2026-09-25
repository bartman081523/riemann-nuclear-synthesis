"""EXPERIMENT 036 Phase 6a — H-STAR-5 Ausfuehrungs-Prereg + Runner (TDD).

Diese Tests fixieren VOR jeder Prime-vs-Null-Auswertung:
  - das Ausfuehrungs-Prereg (numerische Fenster, Ensemble-Groesse,
    Quantil-Schwellen, Kontroll-Gates) mit eigenem md5-Freeze,
  - die registrierte Faltungs-Konstruktion (deterministisch, primes,
    Re-Spektrum-Konvention),
  - die strukturelle Null (Re-Konvention, PT-Bloecke),
  - die Kontrollfamilie (GUE-Positivkontrolle muss den analytischen
    GUE-Ramp zeigen, Poisson-Negativkontrolle darf nicht zünden),
  - die Verdict-Logik (5 Klassen, Kontrollen-zuerst-Regel).

Reine numpy-Mathematik, kein qiskit, 0 QPU.
"""

import hashlib
import json
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_hstar5_execution as ex


# === Prereg (Fenster/Thresholds frozen VOR der ersten Messung) ===

def test_execution_prereg_payload_complete():
    p = ex.build_execution_prereg()
    for key in ("experiment", "hypothesis", "status", "qpu", "scope",
                "skeleton_md5", "construction", "observables", "thresholds",
                "verdict_logic", "compute_calibration", "instantiierungs_noten",
                "version", "supersedes", "deviation_reason", "s4_closure_note",
                "family_o1", "family_o2"):
        assert key in p, key
    # Skeleton-MD5 fix verankert (nicht veraenderbar)
    assert p["skeleton_md5"] == ex.SKELETON_MD5
    assert ex.SKELETON_MD5 == "f915729ef5fb9943c68ec6feeb9a300b"
    assert p["version"] == 2
    # v1-Prereg (degeneriert, nie zu Verdict ausgewertet) ist verankert
    assert p["supersedes"]["md5"] == "aa8e77cc3bbd88a0307f3a9f44ccd0c0"
    # Konstruktion eingefroren (unveraendert gegen v1)
    c = p["construction"]
    assert c["eps_primary"] == 0.25
    assert c["prime_set_4"] == (2, 3, 5, 7)
    assert c["composite_set_4"] == (4, 6, 8, 9)
    assert c["spectrum_convention"].startswith("Re")
    # Fenster (Tau-Grid) eingefroren
    assert c["tau_grid"] == (0.1, 0.5, 2.0)
    # Ensemble/Schwellen eingefroren
    t = p["thresholds"]
    assert t["n_shuffle"] == 200
    assert t["null_seed"] == 20260923
    assert t["q_upper"] == 0.975
    assert t["q_lower"] == 0.025
    assert t["n_controls"] == 100
    assert t["gue_gate"] == (3.5, 6.5)
    assert t["poisson_gate"] == (0.2, 1.8)
    assert t["o2_mechanism_threshold"] == 1e-6
    assert t["identity_tol"] == 1e-9
    # Familien: O1 kanonisch (12), O2 voll (78)
    assert p["family_o1"]["kind"] == "canonical"
    assert p["family_o1"]["n"] == 12
    assert p["family_o2"]["kind"] == "full"
    assert p["family_o2"]["n"] == 78


def test_execution_prereg_freeze_verify_tamper(tmp_path):
    path = tmp_path / "prereg.json"
    ex.freeze_execution_prereg(path=str(path))
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    assert ex.verify_execution_prereg_md5(doc)
    body = {k: v for k, v in doc.items() if k != "md5"}
    assert doc["md5"] == ex.payload_md5(body)
    # Tamper -> Verifikation failt
    doc["thresholds"]["q_upper"] = 0.5
    assert not ex.verify_execution_prereg_md5(doc)


# === Zeichen-Regel (Prim-Residuen) ===

def test_legendre_sign_rule_known_values():
    # QRs: mod 2 {0,1}; mod 3 {0,1}; mod 5 {0,1,4}; mod 7 {0,1,2,4}
    assert ex.legendre_sign_rule(2, 3) == +1   # 3 mod 2 = 1 (QR)
    assert ex.legendre_sign_rule(3, 5) == -1   # 5 mod 3 = 2 (nicht QR)
    assert ex.legendre_sign_rule(3, 7) == +1   # 7 mod 3 = 1 (QR)
    assert ex.legendre_sign_rule(5, 7) == -1   # 7 mod 5 = 2 (nicht QR)


def test_prime_signs_4_blocks_pattern():
    signs = ex.prime_signs(4)
    assert signs == (+1, +1, +1, -1, +1, -1)  # (2,3),(2,5),(2,7),(3,5),(3,7),(5,7)


def test_composite_signs_rank_matched():
    primes = ex.prime_signs(4)
    comps = ex.composite_signs(4)
    assert len(comps) == len(primes) == 6
    # gleiche Paar-Anzahl wie der Prime-Fold, deterministisch
    # Paare (4,6),(4,8),(4,9),(6,8),(6,9),(8,9):
    #   6%4=2 -> -1; 8%4=0 -> +1; 9%4=1 -> +1;
    #   8%6=2 -> -1; 9%6=3 -> +1; 9%8=1 -> +1
    assert comps == (-1, +1, +1, -1, +1, +1)
    # deterministisch bei wiederholtem Aufruf
    assert ex.composite_signs(4) == comps


def test_shuffle_null_preserves_multiset_and_seed():
    base = ex.prime_signs(4)
    perms_a = list(ex.shuffle_null_signs(base, n_perm=5, seed=ex.NULL_SEED))
    perms_b = list(ex.shuffle_null_signs(base, n_perm=5, seed=ex.NULL_SEED))
    assert perms_a == perms_b  # Stream deterministisch
    for perm in perms_a:
        assert sorted(perm) == sorted(base)  # Multimenge erhalten
        assert perm != base or True  # Permutationen koennen trivial sein (multimenge)


# === Konstruktion: gefalteter Hamiltonian ===

def _config(n):
    return (0.02,) * n


def test_folded_hamiltonian_zero_coupling_is_kron_sum():
    cfg = (0.02, 0.02)
    eps = 0.0
    H = ex.folded_hamiltonian(cfg, ex.prime_signs(2), eps)
    blocks = [ex.pt_block(g) for g in cfg]
    Hk = ex.kron_sum_c(blocks)
    assert np.allclose(H, Hk)


def test_folded_hamiltonian_deterministic():
    # Nicht-palindromische Konfiguration: (0.02, 0.2, 0.02) haette via
    # Block-Swap-Symmetrie (0<->2) die Zeichen (+1,+1,-1) -> (-1,+1,+1)
    # unitaer-realisiert — Spektren waren identisch (kein Bug, Symmetrie).
    cfg = (0.002, 0.02, 0.2)
    s1 = ex.prime_signs(3)          # (+1, +1, -1)
    s2 = (-1, +1, +1)               # explizit anderes Zeichen-Muster
    assert s1 != s2
    ev1 = np.sort(np.linalg.eigvals(ex.folded_hamiltonian(cfg, s1, 0.25)).real)
    ev2 = np.sort(np.linalg.eigvals(ex.folded_hamiltonian(cfg, s1, 0.25)).real)
    assert np.array_equal(ev1, ev2)  # deterministisch (kein RNG in der Faltung)
    ev3 = np.sort(np.linalg.eigvals(ex.folded_hamiltonian(cfg, s2, 0.25)).real)
    # anderes Zeichen-Muster -> i.a. anderes Spektrum (nicht bit-identisch)
    assert not np.allclose(ev1, ev3)


def test_pt_block_is_pt_symmetric_not_hermitian():
    H = ex.pt_block(0.02)
    assert not np.allclose(H, H.conj().T)
    # Hermitischer Teil = H_diag (A_5 real-symmetrisch)
    Hd = (H + H.conj().T) / 2.0
    assert np.allclose(Hd, Hd.conj().T)


# === Strukturelle Null (Re-Konvention, PT-Bloecke) ===

def test_structural_identity_re_convention_exact():
    """Tr e^{-iHt} = Prod_p Tr e^{-iH_p t} am Re-Spektrum, exakt (tol 1e-9)."""
    cfg = (0.002, 0.02, 0.2)
    blocks = [ex.pt_block(g) for g in cfg]
    Hk = ex.kron_sum_c(blocks)
    for t in ex.TS_CHECK_EXECUTION:
        lhs = ex.trace_exp_re(ex.re_eigs(Hk), t)
        rhs = np.prod([ex.trace_exp_re(ex.re_eigs(B), t) for B in blocks])
        assert abs(lhs - rhs) <= 1e-9, t


def test_o2_residual_zero_unfolded_nonzero_folded():
    """R2 = log K - Sum log K_p: exakt 0 ungefaltet; gefaltet echt > 0."""
    cfg = (0.002, 0.02)
    blocks = [ex.pt_block(g) for g in cfg]
    Hk = ex.kron_sum_c(blocks)
    ev_u = ex.re_eigs(Hk)
    block_evs = [ex.re_eigs(B) for B in blocks]
    r2u = ex.o2_residual(ev_u, block_evs)
    assert abs(r2u) <= 1e-9
    # gefaltet (eps=0.25): Faktorisierung gebrochen
    Hf = ex.folded_hamiltonian(cfg, ex.prime_signs(2), 0.25)
    ev_f = ex.re_eigs(Hf)
    r2f = ex.o2_residual(ev_f, block_evs)
    assert abs(r2f) > 1e-6  # echte Brechung, nicht numerisches Rauschen


# === SFF-Utilities ===

def test_re_eigs_keeps_multiplicities_no_collapse():
    H = np.diag([1.0 + 0j, 1.0 + 0j, 2.0 + 1j])
    ev = ex.re_eigs(H)
    assert ev[0] == ev[1] == 1.0  # Kein Kollaps (SFF sieht Multiplizitaeten)
    assert ev[2] == 2.0


def test_heisenberg_ruler_median_spacing():
    ev = np.array([0.0, 1.0, 2.1, 3.0, 10.0])  # Ausreisser-Luecke im Ende
    gaps = np.diff(ev)
    assert ex.heisenberg_time(ev) == pytest.approx(2 * np.pi / np.median(gaps))


def test_heisenberg_ruler_ignores_exact_degeneracies():
    """Identische Bloecke -> exakt doppelte Eigenwerte -> Luecken exakt 0.
    Die Regel nutzt die positiven Luecken; die K-Summen sehen die
    Multiplizitaeten weiterhin (kein Kollaps)."""
    ev = np.array([0.0, 0.0, 0.0, 1.0, 2.1, 3.0])  # 3 exakte Doppelter
    pos = np.diff(ev)[np.diff(ev) > 1e-12]         # [1, 1.1, 0.9]
    assert ex.heisenberg_time(ev) == pytest.approx(2 * np.pi / np.median(pos))


def test_k_norm_harmonic_spectrum_flat_phase_sum():
    ev = np.arange(10, dtype=float)
    k0 = ex.k_norm(ev, 0.0)
    assert k0 == pytest.approx(10.0)  # K(0) = d
    kt = ex.k_norm(ev, 0.1237)
    assert 0.0 <= kt <= 10.0


def test_ratio_stat_direction_and_tau_convention():
    # iid-uniformes (Poisson-artiges) Spektrum: kein Ramp -> r < 1
    rng = np.random.default_rng(7)
    ev = np.sort(rng.uniform(0.0, 50.0, size=50))
    r = ex.ratio_stat(ev)
    assert r is not None and r < 1.0
    assert r == pytest.approx(
        ex.k_norm(ev, 0.5 * ex.heisenberg_time(ev))
        / ex.k_norm(ev, 0.1 * ex.heisenberg_time(ev)))


def test_ratio_stat_discards_exact_harmonic_reference_point():
    # Exakt-harmonisches Spektrum: K(tau1*t_H) ~ 1e-29 (destruktive
    # Interferenz, Float-Reste) -> unter der registrierten
    # Verwerfungs-Schwelle 1e-12 -> Instanz verworfen (None)
    ev = np.linspace(0.0, 1.0, 50)
    k1 = ex.k_norm(ev, 0.1 * ex.heisenberg_time(ev))
    assert k1 < 1e-12
    assert ex.ratio_stat(ev) is None


# === Kontroll-Gates (kleine Live-Groesse, grosse im Runner) ===

def test_gue_poisson_controls_small_scale():
    """Positivkontrolle GUE zeigt Ramp (R ~ 5), Poisson nicht (R ~ < 2)."""
    r_gue = ex.control_ratio_stat(ex.gue_eigs, d=125, n=30)
    r_pois = ex.control_ratio_stat(ex.poisson_eigs, d=125, n=30)
    assert 3.0 <= r_gue <= 7.0   # analytisch 5.0 (GUE-Ramp)
    assert 0.2 <= r_pois <= 1.8  # kein Ramp


# === Verdict-Logik (5 Klassen, Kontrollen zuerst) ===

def _controls_ok():
    return {"structural_ok": True, "gue_ok": True, "poisson_ok": True,
            "composite_in_band": True}


def test_verdict_confirmed_requires_all():
    v = ex.verdict(r_prime=10.0, shuffle_ratios=np.array([1.0] * 200),
                   controls=_controls_ok(), o2_ok=True)
    assert v["verdict"] == "CONFIRMED"
    assert v["verdict_class"] == "H-STAR5_CONFIRMED_PRIME_SFF_SEPARATION"


def test_verdict_refuted_inside_band():
    shuffle = np.array([1.0, 2.0] * 100)
    v = ex.verdict(r_prime=1.5, shuffle_ratios=shuffle,
                   controls=_controls_ok(), o2_ok=False)
    assert v["verdict"] == "REFUTED"
    assert v["verdict_class"] == "H-STAR5_REFUTED_INTEGRABLE_IN_ALL_PROBES"


def test_verdict_degenerat_below_band():
    shuffle = np.array([1.0] * 200)
    v = ex.verdict(r_prime=0.1, shuffle_ratios=shuffle,
                   controls=_controls_ok(), o2_ok=False)
    assert v["verdict"] == "DEGENERAT"
    assert v["verdict_class"] == "H-STAR5_REFUTED_UNTER_NULL_DEGENERAT"


def test_verdict_void_when_positive_control_fails():
    controls = _controls_ok()
    controls["gue_ok"] = False
    v = ex.verdict(r_prime=10.0, shuffle_ratios=np.array([1.0] * 200),
                   controls=controls, o2_ok=True)
    assert v["verdict"] == "VOID"
    assert v["verdict_class"] == "H-STAR5_VOID_POSITIVKONTROLLE_ZUENDET_NICHT"


def test_verdict_invalid_when_negative_control_fires():
    controls = _controls_ok()
    controls["composite_in_band"] = False
    v = ex.verdict(r_prime=10.0, shuffle_ratios=np.array([1.0] * 200),
                   controls=controls, o2_ok=True)
    assert v["verdict"] == "INVALID"
    assert v["verdict_class"] == "H-STAR5_INVALID_KONTROLLE_GESCHEITERT"
    controls["poisson_ok"] = False
    v = ex.verdict(r_prime=10.0, shuffle_ratios=np.array([1.0] * 200),
                   controls=controls, o2_ok=True)
    assert v["verdict"] == "INVALID"


def test_verdict_confirmed_requires_o2():
    v = ex.verdict(r_prime=10.0, shuffle_ratios=np.array([1.0] * 200),
                   controls=_controls_ok(), o2_ok=False)
    assert v["verdict"] == "REFUTED"


# === Kanonische Familie (v2) ===

def test_canonical_family_configs_structure():
    """12 sortierte 4-Tupel, ein Repraesentant je gamma-Multimenge,
    nicht-konstant, deterministisch, Teilmenge der vollen 78er-Familie."""
    fam = ex.canonical_family_configs()
    full = ex.get_config_family()
    assert len(fam) == 12
    assert len(set(fam)) == 12
    for cfg in fam:
        assert cfg == tuple(sorted(cfg))
        assert len(set(cfg)) > 1
        assert cfg in full
    assert fam == ex.canonical_family_configs()  # deterministisch


def test_s4_closure_miniature_theorem():
    """S₄-Schluss-Theorem im Miniaturmassstab: ueber einer unter
    Positions-Permutationen abgeschlossenen Familie ist jede
    Familiensumme Orbit-invariant im Zeichen-Muster — 2-minus-Muster
    desselben S₃-Orbits geben identisches Ensemble-R (tol 1e-9)."""
    # Mini-Familie: alle 6 nicht-konstanten 3-Tupel ueber 2 gamma-Werte,
    # abgeschlossen unter S₃ (Block-Positionen).
    fam = [(0.02, 0.02, 0.2), (0.02, 0.2, 0.02), (0.2, 0.02, 0.02),
           (0.02, 0.2, 0.2), (0.2, 0.02, 0.2), (0.2, 0.2, 0.02)]

    def ens_r(signs):
        k1s, k2s = [], []
        for cfg in fam:
            _, t_h = ex.unfold_spectrum(cfg)
            ev = ex.re_eigs(ex.folded_hamiltonian(cfg, signs, 0.25))
            k1s.append(ex.k_norm(ev, ex.TAU1 * t_h))
            k2s.append(ex.k_norm(ev, ex.TAU2 * t_h))
        return np.mean(k2s) / np.mean(k1s)

    # Drei 2-minus-Muster am Dreieck — alle Paare benachbart (1 Orbit).
    rs = [ens_r(s) for s in ((-1, -1, +1), (-1, +1, -1), (+1, -1, -1))]
    assert abs(rs[0] - rs[1]) <= 1e-9
    assert abs(rs[1] - rs[2]) <= 1e-9


def test_canonical_family_breaks_s4_closure_miniature():
    """Gegenstueck: auf der kanonischen Familie (ein Repraesentant je
    Multimenge) sind dieselben Muster i.a. verschieden — keine
    Orbit-Invarianz mehr."""
    canon = [(0.02, 0.02, 0.2), (0.2, 0.2, 0.02)]  # sortierte Repraesentanten

    def ens_r(signs):
        k1s, k2s = [], []
        for cfg in canon:
            _, t_h = ex.unfold_spectrum(cfg)
            ev = ex.re_eigs(ex.folded_hamiltonian(cfg, signs, 0.25))
            k1s.append(ex.k_norm(ev, ex.TAU1 * t_h))
            k2s.append(ex.k_norm(ev, ex.TAU2 * t_h))
        return np.mean(k2s) / np.mean(k1s)

    rs = {s: ens_r(s) for s in ((-1, -1, +1), (-1, +1, -1), (+1, -1, -1))}
    assert len(set(round(r, 6) for r in rs.values())) >= 2


# === Results-Vertrag (kleine Live-Groesse, 0 QPU) ===

def test_run_phase6a_results_contract(tmp_path, monkeypatch):
    monkeypatch.setattr(ex, "CONFIG_FAMILY",
                        [(0.02, 0.02, 0.2), (0.2, 0.2, 0.02)])
    monkeypatch.setattr(ex, "CANONICAL_FAMILY", [(0.02, 0.02, 0.2)])
    out = tmp_path / "res.json"
    res = ex.run_phase6a(out_path=str(out), n_shuffle=4, n_controls=10,
                         verbose=False)
    for key in ("experiment", "hypothesis", "o1_prime", "shuffle_null",
                "composite_o1", "o2", "controls", "verdict", "verdict_class",
                "qpu", "prereg_mode", "family_o1", "family_o2",
                "s4_closure_v1_note"):
        assert key in res, key
    assert res["qpu"] == 0
    assert res["verdict"] in {"CONFIRMED", "REFUTED", "DEGENERAT", "VOID",
                              "INVALID"}
    assert res["family_o1"]["n"] == 1
    assert res["family_o2"]["n"] == 2
    assert res["prereg_mode"] in {"frozen_v2", "live"}
    with open(out, encoding="utf-8") as fh:
        assert json.load(fh)["hypothesis"] == "H-STAR-5"


# === Offline-Guard ===

def test_offline_guard_no_qiskit_no_token_no_qpu():
    src = open(ex.__file__, encoding="utf-8").read()
    assert "qiskit" not in src.lower()
    assert "IBMQ_TOKEN" not in src
    assert "load_account" not in src
    assert "getenv" not in src