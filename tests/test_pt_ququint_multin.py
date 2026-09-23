"""V2 (H-STAR-1): V_N-Skalierung mit Primzahlstruktur vs. 0.55-Anchor.

Alle Tests OFFLINE (pure numpy, kein qiskit). Prereg VOR der Kurven-
berechnung gefroren (pt_multin_prereg_v2.json, md5).

Geometrie: Prime-Paar-Zustand |phi_P> = (1/sqrt(pi)) sum_{p<=P} |p>_A |p>_B
auf zwei d-dim Registern (d = 5^k: 5, 25, 625); Witness V = DFT-Diagonal-
gewicht unter F_d (x) F_d^dagger (Generalisierung von histogram_dft).
"""

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_ququint_multin as mn


# === Encoding ===

def test_phi_prime_pair_shape_and_norm():
    psi = mn.phi_prime_pair(23, 25)
    assert psi.shape == (625,)
    assert math.isclose(float(np.sum(np.abs(psi) ** 2)), 1.0, rel_tol=1e-12)
    primes = mn.sieve_primes(23)
    assert len(primes) == 9
    for p in primes:
        assert abs(psi[p * 25 + p]) > 0  # Diagonal-Support |p,p>


def test_separable_pair_bound():
    rho = mn.separable_pair(23, 25)
    v = mn.witness_value(rho, 25)
    assert math.isclose(v, 1 / 25, rel_tol=1e-12)  # WITNESS_BOUND = 1/d


# === Die analytische Kern-Vorhersage (Falsifikator von H-STAR-1) ===

def test_v_n_equals_pi_over_d_primes():
    # Kohaerente Zustands-Witness: V = pi/d EXAKT (unabhaengig von Primstruktur)
    for P, d in [(11, 25), (23, 25), (97, 625)]:
        psi = mn.phi_prime_pair(P, d)
        v = mn.witness_value(psi, d)
        assert math.isclose(v, len(mn.sieve_primes(P)) / d, rel_tol=1e-9), (P, d, v)


def test_control_composite_same_witness():
    # STEELMAN-Kontrolle: gleichrangiger Composite-Support -> identisches V
    P = 97
    d = 625
    primes = mn.sieve_primes(P)
    comps = [n for n in range(4, P + 1)
             if any(n % f == 0 for f in range(2, int(n ** 0.5) + 1))]
    support = comps[: len(primes)]
    assert len(support) == len(primes)
    v_prime = mn.witness_value(mn.diagonal_pair_state(primes, d), d)
    v_comp = mn.witness_value(mn.diagonal_pair_state(support, d), d)
    assert abs(v_prime - v_comp) < 1e-10


def test_control_random_support_same_witness():
    rng_support = mn.random_diagonal_support(9, 25, seed=12345)
    v_rand = mn.witness_value(mn.diagonal_pair_state(rng_support, 25), 25)
    v_prime = mn.witness_value(mn.phi_prime_pair(23, 25), 25)
    assert abs(v_prime - v_rand) < 1e-10


def test_svn_pair_uniform_schmidt():
    # S_vN der Paar-Zustands-Bipartition A|B = log(pi) exakt
    psi = mn.phi_prime_pair(97, 625)
    s, s_max = mn.svn_pair(psi, 625)
    assert math.isclose(s, math.log(25), rel_tol=1e-9)
    assert math.isclose(s_max, math.log(625), rel_tol=1e-9)


# === Ramanujan-Fingerprint (das nicht-triviale Prime-DFT-Objekt) ===
# Statistik: S* = {a ≡ 0 mod d/5, a ≠ 0}. a=0 ist TRIVIAL (G(0) = m fuer
# jeden Support — derselbe Wert wie V). S* ohne a=0 misst die Primzahl-
# Residuen mod 5: omega^{125j·p} = omega_5^{j·p}; Primes meiden Residue 0.

def test_dft_profile_p0_trivial_and_normalized():
    # a=0: G(0) = m -> p(0) = m/d fuer JEDEN Support (trivial, wie V)
    prof = mn.dft_profile(23, 25)
    assert math.isclose(prof.sum(), 1.0, rel_tol=1e-12)
    assert math.isclose(prof[0], 9 / 25, rel_tol=1e-9)
    prof625 = mn.dft_profile(625, 625)
    assert math.isclose(prof625[0], 114 / 625, rel_tol=1e-9)


def test_dft_profile_share_star_d625_lift():
    # Vorhersage (Residuen-Arithmetik): G(125j) ≈ 1 - (pi-1)/4 ≈ -27,
    # |G|^2 ≈ 743 vs. generisch m=114 -> share(S*) ≈ 0.045 vs. 0.0064
    prof = mn.dft_profile(625, 625)
    share = mn.share_star(prof, 625)
    assert share >= mn.RAMANUJAN_SHARE_STAR_MIN


def test_composite_support_profile_no_lift():
    # Kontrolle: Composites enthalten Vielfache von 5 -> Residue-0 reich
    # -> G(125j) ≈ 0 -> KEIN Lift (das mod-5-Verhalten ist prime-spezifisch)
    prof = mn.single_register_profile(mn.composite_support(625), 625)
    assert mn.share_star(prof, 625) < mn.CONTROL_SHARE_STAR_MAX


def test_random_support_profile_no_lift():
    # Kontrolle: Random-Support (m=114, seeded) -> Residuen mod 5
    # gleichverteilt inkl. 0 -> G(125j) ≈ 0 -> KEIN Lift
    rng_support = mn.random_diagonal_support(114, 625, seed=777)
    prof = mn.single_register_profile(rng_support, 625)
    assert mn.share_star(prof, 625) < mn.CONTROL_SHARE_STAR_MAX


# === Prereg ===

def test_prereg_payload_and_md5(tmp_path):
    p = mn.build_prereg_payload()
    assert p["experiment"] == "032-ququint-v2-vn-scaling"
    assert p["decision_rule"] == "t1_rank_trivial AND t2_controls_invariant"
    assert p["predictions"]["t1_rank_trivial"] is True
    assert math.isclose(p["thresholds"]["nu_tolerance"], 0.05)
    assert p["thresholds"]["ramanujan_share_star_min"] == 0.025
    assert p["thresholds"]["control_share_star_max"] == 0.02
    # a=0-Bin als trivial dokumentiert (Anti-Sharpshooter: die Statistik
    # EXKLUDIERT den trivialen Bin)
    assert "a=0 ist trivial" in p["ramanujan_statistic"]["why_nontrivial"]
    doc = mn.freeze_prereg(p)
    assert mn.verify_prereg_md5(doc)
    path = tmp_path / "prereg.json"
    path.write_text(json.dumps(doc))
    assert mn.load_frozen_prereg(str(path))["md5"] == doc["md5"]
    tampered = dict(doc, thresholds={"nu_tolerance": 0.5})
    assert not mn.verify_prereg_md5(tampered)


def test_verdict():
    assert mn.verdict(True, True, True) == (
        "H-STAR-1_REFUTED_WITNESS_RANK_TRIVIAL + RAMANUJAN_FINGERPRINT")
    assert mn.verdict(True, True, False) == "H-STAR-1_REFUTED_WITNESS_RANK_TRIVIAL"
    assert mn.verdict(False, True, True) == "H-STAR-1_SURVIVES + RAMANUJAN_FINGERPRINT"
    assert mn.verdict(False, False, False) == "H-STAR-1_SURVIVES"


def test_offline_module_no_qiskit_ibm_import():
    src = open(mn.__file__, encoding="utf-8").read()
    assert "qiskit_ibm" not in src
    assert "QiskitRuntimeService" not in src