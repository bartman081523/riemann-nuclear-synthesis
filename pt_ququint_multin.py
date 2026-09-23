"""EXPERIMENT 032 - Ququint V2 (H-STAR-1): V_N-Skalierung vs. 0.55-Anchor.

Frage: Skaliert der Ququint-Witness V(φ_N) mit der multiplikativen Struktur
von Z/NZ — wie der S_vN-Anchor der Primzustände (S_vN/log(N): 0.28 -> 0.55,
§X.1)? Oder ist der Witness ein reines Verschränkungs-Zertifikat, dessen
Wert von der Prime-Struktur des Supports unabhängig ist?

Anti-Sharpshooter: Prereg (Vorhersagen + Schwellen) VOR der Kurven-
berechnung gefroren (pt_multin_prereg_v2.json, md5). Alles pure numpy,
kein qiskit.

Geometrie:
  |phi_P> = (1/sqrt(pi(P))) sum_{p <= P} |p>_A |p>_B — Prime-Paar-Zustand
  auf zwei d-dim Registern (d = 5^k, Encoding: Prime p -> Basis-Index p,
  injektiv fuer P < d). Zeugnis-Objekt ist die Generalisierung von
  histogram_dft (pt_ququint_ibmq): V = Summe der Diagonal-Masse von
  (F_d (x) F_d^dagger) psi. Schranke WITNESS_BOUND = 1/d (rho_sep).

Analytische Kern-Erkenntnis (VOR der Messung abgeleitet, Prereg-Teil 1):
  (F_d |p>)_a = omega_d^{ap}/sqrt(d);  (F_d^dagger |p>)_a = omega_d^{-ap}/sqrt(d)
  -> <a,a| U |phi_P> = (1/sqrt(pi)) * pi * (1/d)  fuer JEDES a (Phasen heben
  sich auf) -> V_N = pi(P)/d EXAKT — unabhaengig WELCHE Diagonal-Positionen
  belegt sind. Der Paar-Witness ist blind gegen die multiplikative Struktur
  des Supports: H-STAR-1 ist analytisch falsifizierbar, die Controls
  (Composite-/Random-Support gleichen Rangs) muessen IDENTISCHES V liefern.

Die multiplikative Primstruktur lebt stattdessen im EINZELREGISTER-DFT:
  G(a) = sum_{p<=P} omega_d^{ap},  p(a) = |G(a)|^2/(d*pi).
  a = 0 ist TRIVIAL (G(0) = m fuer JEDEN Support -> p(0) = m/d, derselbe
  Zeuge-Wert wie V). Das nicht-triviale Objekt ist die Klasse
  S* = {a ≡ 0 mod 5^{k-1}, a ≠ 0}: dort ist omega_d^{a·p} = omega_5^{j·p},
  d.h. S* misst die PRIMZAHl-Residuen mod 5. Primzahlen meiden Residue 0
  (nur p=5) und sind gleichverteilt auf {1,2,3,4} ->
  G(125j) ≈ 1 - (pi-1)/4 ≈ -27 (d=625, m=114), |G|^2 ≈ 743 vs. generisch
  E|G|^2 = m = 114 -> share(S*) ≈ 0.045 vs. generisch 0.0064 (Faktor ~7).
  Kontrolle: Composite-Support (Residue-0 reich, Vielfache von 5) -> kein
  Lift; Random-Support -> kein Lift. d=25 (m=9) ist FLUKTUIUNGSBEHERRSCHT
  (Ramanujan-Modell: |G(5j)|^2 ≈ (pi/phi(d))^2 |c_25(5j)|^2 ≈ 5.06 < m=9)
  -> nur deskriptiv, KEIN Gate.
"""

import hashlib
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pt_prime_state import sieve_primes

PREREG_PATH = "pt_multin_prereg_v2.json"
EXPERIMENT = "032-ququint-v2-vn-scaling"
DECISION_RULE = "t1_rank_trivial AND t2_controls_invariant"

NU_TOLERANCE = 0.05              # nu_N = (V - 1/d) / (pi/d - 1/d) konstant?
RAMANUJAN_SHARE_STAR_MIN = 0.025  # d=625, S* = {a≡0 mod 125, a≠0};
                                  # Modell ≈ 0.045, generisch 0.0064
CONTROL_SHARE_STAR_MAX = 0.02     # Random-/Composite-Support: kein Lift

V2_SWEEP = [  # (P, d): 2 Punkte d=25 (pi=5,9), 4 Punkte d=625 (pi=25..114)
    (11, 25), (23, 25),
    (97, 625), (211, 625), (463, 625), (625, 625),
]
RANDOM_SEED = 20260923


# === Zustaende ===

def diagonal_pair_state(support, d):
    """Sigma|p,p> uniform über die Support-Indizes (Diagonale A=B)."""
    psi = np.zeros((d, d), dtype=complex)
    for x in support:
        psi[int(x), int(x)] = 1.0
    return (psi / np.sqrt(len(support))).reshape(d * d)


def phi_prime_pair(P, d):
    """Prime-Paar-Zustand: Support = Primzahlen <= P."""
    return diagonal_pair_state(sieve_primes(P), d)


def separable_pair(P, d):
    """rho_sep = (1/pi) sum |pp><pp| — die Konfund-Kontrolle (diag)."""
    rho = np.zeros((d * d, d * d), dtype=complex)
    for p in sieve_primes(P):
        rho[p * d + p, p * d + p] = 1.0
    return rho / len(sieve_primes(P))


def composite_support(P):
    """Die ersten pi(P) zusammengesetzten Zahlen <= P (Rang-matched Kontrolle)."""
    primes = set(sieve_primes(P))
    m = len(sieve_primes(P))
    out = []
    for n in range(4, P + 1):
        if n in primes:
            continue
        if any(n % f == 0 for f in range(2, int(n ** 0.5) + 1)):
            out.append(n)
            if len(out) == m:
                return out
    raise ValueError("nicht genug Composites")


def random_diagonal_support(m, d, seed):
    rng = np.random.default_rng(seed)
    return sorted(rng.choice(d, size=m, replace=False).tolist())


# === Witness ===

def _dft_matrix(d):
    n = np.arange(d)
    return np.exp(2j * np.pi * np.outer(n, n) / d) / np.sqrt(d)


def witness_value(obj, d):
    """V = Summe der Diagonal-Masse von (F (x) F^dagger) angewandt auf
    Zustand (Vektor oder Dichte-Matrix) — Generalisierung von histogram_dft.

    Tensor-Struktur statt dichtem kron (d=625: U waere 390625^2 dense):
      (F (x) F^dagger) vec(M) = vec(F M F.conj())   (F ist symmetrisch)
    Vektor:   V = sum_a |(F M F.conj())[a,a]|^2
    Dichte:   V = Tr(rho)/d fuer DIAGONALE rho (jedes |s,s> traegt
              sum_a |F[a,s] F^dagger[s,a]|^2 = 1/d) — exakt, kein denses rho.
    """
    F = _dft_matrix(d)
    obj = np.asarray(obj, dtype=complex)
    if obj.ndim == 1:
        W = F @ obj.reshape(d, d) @ F.conj()
        return float((np.abs(np.diag(W)) ** 2).sum())
    diag_rho = np.diag(obj)
    if np.abs(obj - np.diag(diag_rho)).max() > 1e-12:
        raise ValueError("witness_value: nur diagonale Dichte-Matrix "
                         "unterstuetzt (V = Tr(rho)/d exakt); nicht-"
                         "diagonale rho als Eigenvektor-Zerlegung geben")
    return float(np.real(np.sum(diag_rho)) / d)


def svn_pair(psi, d):
    """S_vN der Bipartition A|B (reshape d x d, SVD) + max-Entropie."""
    m = np.asarray(psi, dtype=complex).reshape(d, d)
    _, S, _ = np.linalg.svd(m)
    s2 = S ** 2
    s2 = s2[s2 > 1e-12]
    return float(-np.sum(s2 * np.log(s2))), float(math.log(d))


# === Einzelpregister-Ramanujan-Profil ===

def single_register_profile(support, d):
    """p(a) = |G(a)|^2/(d*pi) mit G(a) = sum_{x in support} omega_d^{ax}."""
    idx = np.asarray(support, dtype=float)
    n = np.arange(d)
    G = np.exp(2j * np.pi * np.outer(n, idx) / d).sum(axis=1)
    prof = np.abs(G) ** 2 / (d * len(idx))
    return prof / prof.sum()


def dft_profile(P, d):
    return single_register_profile(sieve_primes(P), d)


def share_star(prof, d):
    """Masse der Klasse S* = {a ≡ 0 mod d/5, a ≠ 0} — die NICHT-triviale
    mod-5^{k-1}-Klasse (a=0 ist trivial: G(0) = m fuer jeden Support)."""
    step = d // 5
    return float(sum(prof[a] for a in range(step, d, step)))


# === Prereg ===

def build_prereg_payload():
    return {
        "experiment": EXPERIMENT,
        "registered_before": (
            "Analytische Vorarbeit: V_N = pi/d fuer Diagonal-Support ist VOR "
            "diesem Freeze abgeleitet (Phasen-Hebung omega^{ap} omega^{-ap} = 1). "
            "Die numerische Kurve wurde vor dem Freeze NICHT berechnet; das "
            "Prereg fixiert die Schwellen beider moeglichen Ausgaenge."
        ),
        "hypothesis": (
            "H-STAR-1: V(φ_N) skaliert mit der multiplikativen Struktur von "
            "Z/NZ wie S_vN/log(N) -> 0.55 — der Witness als Primzahl-"
            "Zertifikat. Steelman: Witness konstant in N (Encodierungs-"
            "Artefakt, rank-trivial)."
        ),
        "anchor": "S_vN/log(N) der |P_N>-Zustaende: 0.28 (N=127) -> 0.55 "
                  "(N=1e6), sub-logarithmisch (§X.1, A-)",
        "decision_rule": DECISION_RULE,
        "sweep": [[P, d] for P, d in V2_SWEEP],
        "predictions": {"t1_rank_trivial": True, "t2_controls_invariant": True},
        "thresholds": {
            "nu_tolerance": NU_TOLERANCE,
            "control_tolerance": 1e-9,
            "ramanujan_share_star_min": RAMANUJAN_SHARE_STAR_MIN,
            "control_share_star_max": CONTROL_SHARE_STAR_MAX,
        },
        "ramanujan_statistic": {
            "definition": "share_star = Masse der Klasse S* = {a ≡ 0 mod "
                          "d/5, a ≠ 0} im Einzelregister-DFT-Profil",
            "why_nontrivial": "a=0 ist trivial (G(0) = m fuer JEDEN Support, "
                              "p(0) = m/d = V). S* ohne a=0 misst die "
                              "Primzahl-Residuen mod 5: omega^{125j·p} = "
                              "omega_5^{j·p}. Primzahlen meiden Residue 0 "
                              "(nur p=5) -> G(125j) ≈ 1 - (pi-1)/4 ≈ -27 "
                              "(d=625), |G|^2 ≈ 743 vs. generisch m = 114.",
            "model_share_star_d625": 0.045,
            "generic_baseline_d625": 4 / 625,
            "d25_status": "deskriptiv (m=9 fluktuationsbeherrscht; "
                          "Ramanujan-Modell sagt KEINEN Lift: "
                          "|G(5j)|^2 ≈ 5.06 < m = 9)",
        },
        "verdict_map": {
            "H-STAR-1_REFUTED_WITNESS_RANK_TRIVIAL": "t1 AND t2",
            "H-STAR-1_SURVIVES": "NOT t1",
            "RAMANUJAN_FINGERPRINT": "share_star(prim, d625) >= 0.025 AND "
                                     "share_star(rand) < 0.02 AND "
                                     "share_star(comp) < 0.02",
        },
    }


def canonical_payload_json(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def payload_md5(payload):
    return hashlib.md5(canonical_payload_json(payload).encode("utf-8")).hexdigest()


def freeze_prereg(payload=None):
    if payload is None:
        payload = build_prereg_payload()
    doc = dict(payload)
    doc["md5"] = payload_md5(payload)
    return doc


def verify_prereg_md5(doc):
    stripped = {k: v for k, v in doc.items() if k != "md5"}
    return payload_md5(stripped) == doc["md5"]


def load_frozen_prereg(path=PREREG_PATH):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if not verify_prereg_md5(doc):
        raise ValueError(f"Prereg-md5-MISMATCH in {path}")
    return doc


# === Verdict ===

def verdict(t1, t2, t3):
    h1 = ("H-STAR-1_REFUTED_WITNESS_RANK_TRIVIAL"
          if (t1 and t2) else "H-STAR-1_SURVIVES")
    tag = " + RAMANUJAN_FINGERPRINT" if t3 else ""
    return h1 + tag


# === Evaluation ===

def run_v2():
    """Volle V2-Evaluation (deterministisch, seeded)."""
    rows = []
    nus = []
    controls = []
    for P, d in V2_SWEEP:
        primes = sieve_primes(P)
        pi = len(primes)
        psi = phi_prime_pair(P, d)
        v = witness_value(psi, d)
        nu = (v - 1 / d) / (pi / d - 1 / d)
        nus.append(nu)
        row = {"P": P, "d": d, "pi": pi, "V": v, "bound": 1 / d,
               "ideal": pi / d, "nu": nu,
               "svn": svn_pair(psi, d)[0],
               "log_P_over": math.log(pi) / math.log(P)}
        # Controls (Rang-match)
        v_rand = witness_value(
            diagonal_pair_state(random_diagonal_support(pi, d, RANDOM_SEED), d), d)
        try:
            v_comp = witness_value(
                diagonal_pair_state(composite_support(P), d), d)
        except ValueError:
            v_comp = None
        row["V_random"] = v_rand
        row["V_composite"] = v_comp
        row["dV_random"] = abs(v - v_rand)
        row["dV_composite"] = None if v_comp is None else abs(v - v_comp)
        rows.append(row)

    t1 = max(abs(nu - 1.0) for nu in nus) <= NU_TOLERANCE
    t2 = all(r["dV_random"] <= 1e-9 and
             (r["dV_composite"] is None or r["dV_composite"] <= 1e-9)
             for r in rows)

    # Ramanujan-Fingerprint: S* = {a ≡ 0 mod d/5, a ≠ 0} (a=0 trivial)
    prof625 = dft_profile(625, 625)
    share_star_prime = share_star(prof625, 625)
    prof_rand = single_register_profile(
        random_diagonal_support(114, 625, RANDOM_SEED), 625)
    share_star_rand = share_star(prof_rand, 625)
    prof_comp = single_register_profile(composite_support(625), 625)
    share_star_comp = share_star(prof_comp, 625)
    t3 = (share_star_prime >= RAMANUJAN_SHARE_STAR_MIN
          and share_star_rand < CONTROL_SHARE_STAR_MAX
          and share_star_comp < CONTROL_SHARE_STAR_MAX)

    return {
        "experiment": EXPERIMENT,
        "prereg_path": PREREG_PATH,
        "rows": rows,
        "t1_rank_trivial": bool(t1),
        "t2_controls_invariant": bool(t2),
        "t3_ramanujan": bool(t3),
        "ramanujan": {
            "share_star_prime_d625": share_star_prime,
            "share_star_random_d625": share_star_rand,
            "share_star_composite_d625": share_star_comp,
            "generic_baseline_d625": 4 / 625,
            "p0_trivial_d625": float(prof625[0]),
            "d25_descriptive": {
                "share_star_d25": share_star(dft_profile(23, 25), 25),
                "p0_trivial_d25": float(dft_profile(23, 25)[0]),
                "generic_baseline_d25": 4 / 25,
                "note": "deskriptiv, kein Gate (m=9 fluktuationsbeherrscht)",
            },
        },
        "decision_rule": DECISION_RULE,
        "verdict": verdict(t1, t2, t3),
    }


def main():
    res = run_v2()
    with open("pt_multin_v2_results.json", "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    print("VERDICT:", res["verdict"])
    for r in res["rows"]:
        dvc = r["dV_composite"]
        dvc_txt = "-" if dvc is None else f"{dvc:.2e}"
        print(f"P={r['P']:4d} d={r['d']:4d} pi={r['pi']:3d} "
              f"V={r['V']:.6f} ideal={r['ideal']:.6f} nu={r['nu']:.2e} "
              f"dV_rand={r['dV_random']:.2e} dV_comp={dvc_txt}")
    r = res["ramanujan"]
    print(f"Ramanujan share* (d625, S* ohne a=0): prim={r['share_star_prime_d625']:.4f} "
          f"rand={r['share_star_random_d625']:.4f} "
          f"comp={r['share_star_composite_d625']:.4f} "
          f"(generic {r['generic_baseline_d625']:.4f}) | "
          f"p0 trivial: d625={r['p0_trivial_d625']:.4f} "
          f"d25={r['d25_descriptive']['p0_trivial_d25']:.4f} "
          f"share*_d25={r['d25_descriptive']['share_star_d25']:.4f}")


if __name__ == "__main__":
    main()