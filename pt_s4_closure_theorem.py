# -*- coding: utf-8 -*-
"""pt_s4_closure_theorem.py — EXPERIMENT 045 (H-S4-CLOSURE):
Numerische Verifikation + Formalisierung des S₄-Schluss-Theorems
(SYNTHESIS §Z.20.2 / RIEMANN §10.21, bewiesen 2026-09-25 im
H-STAR-5-v1-Abbruch). 0 QPU, NICHT verdict-tragend (das Phase-6a-REFUTED
steht unangetastet; dieses Experiment prueft das THEOREM, das dem
v2-Design-Zwang zugrunde liegt).

Das Theorem (verifizierte Praezisionsform; Konvention = np.kron-Reihenfolge,
Position 0 signifikantester Faktor):
  Die 78er-Familie (alle nicht-konstanten 4-Tupel ueber
  (0.002, 0.02, 0.2)) ist unter Block-Positions-Permutationen
  sigma ∈ S₄ abgeschlossen. Fuer den gefalteten Hamiltonian gilt
  H(sigma·cfg, sigma·s) = U† H(cfg, s) U  mit der PULL-FORWARD-Paarung
  (sigma·cfg)_j = cfg_{sigma(j)}, (sigma·s)_(jk) = s_(sigma(j),sigma(k))
  und der Positions-Permutations-Unitary U (U†(B⊗_i)U = B⊗_{sigma^-1(i)});
  Spektren stimmen bis Rundung (~1e-13·||H||), NICHT bit-exakt.
  Aequivalent: k(cfg∘sigma, s∘sigma) = k(cfg, s) — und da die 78er-
  Familie permutations-abgeschlossen ist, folgt durch Reindexierung die
  Konventions- und Aktionsrichtung-UNABHAENGIGE Familien-Invarianz:
  JEDE Familiensumme (mean k1, mean k2, Median der per-config-r) ist
  konstant auf den Bahn-MENGEN der Zeichen-Muster. Die 15 Zwei-Minus-
  Muster fallen in genau 2 S₄-Orbits: benachbart (12, −1-Paare teilen
  einen Vertex) und disjunkt (3, perfekte Matchings). Prime- UND
  Composite-Zeichen liegen beide im benachbarten Orbit → die
  Composite-Kontrolle ist (auf der 78er-Familie) zahnlos.

Ex-ante-Pruefgrenzen (registriert im Skript-Kopf, VOR dem Lauf):
  - Term-/H-Konjugation: ||·||_max < 1e-10 (d = 625)
  - Spektrum/k-Gleichheit: < 1e-9
  - Familien-Summen-Invarianz innerhalb eines Orbits: < 1e-9
    (dokumentierte Empirie: 5.8e-11 — die Invarianz ist EXAKT als
    unitäre Äquivalenz; die Floating-Point-Realisierung ist
    rundungs-beschränkt, NICHT bit-exakt — die 9-Dezimalstellen-Atome
    des v1-Laufs sind Rundungs-identisch)
  - Orbit-Struktur: 15 Zwei-Minus-Muster → genau 2 Orbits (12/3)
  - v1-Atom-Korrespondenz: R-Werte auf 9 Dezimalstellen

Lemmata:
  L1 A-Uniformität: A = H_PT_ququint(gamma)[1] ist bit-identisch ueber
     die drei Familien-gamma (damit ist die cfg[0]-Indizierung in
     folded_hamiltonian wirkungslos — A ist ein globaler Operator).
  L2 Paar-Term-Konjugation: U† T_(a,b) U = T_(sigma^-1(a), sigma^-1(b)).
  L3 Kron-Summen-Konjugation: U† kron_sum(blocks(cfg)) U =
     kron_sum(blocks(sigma·cfg)).
Theorem (T):
  T4  U† H(cfg, s) U = H(sigma·cfg, sigma·s) (Spektren + k-Werte;
      PULL-FORWARD-Paarung, siehe Kopf).
  T5  Familien-Summen (mean k1, mean k2, R, r_median) ueber die
      78er-Familie sind konstant auf S₄-Orbits von s (gemessen ueber
      ALLE 15 Zwei-Minus-Muster); benachbart ≠ disjunkt.
  T6  composite_signs(4) und prime_signs(4) liegen beide im
      benachbarten Orbit → Familien-Summe(composite) ≈ Familien-Summe
      (prime) auf Rundungsniveau (zahnlose Kontrolle, v1-Praezedenz).
  T7  v1-Atom-Korrespondenz: die 132 archivierten Shuffle-Instanzen
      (pt_hstar5_phase6a_v1_degenerate.shuffle.jsonl) zerfallen exakt
      nach der Orbit-Klasse ihrer Zeichen-Zuordnung (110 benachbart /
      22 disjunkt); die beiden Atome werden AUS DEN ARCHIVIERTEN
      R-Werten selbst abgeleitet (9 Dezimalstellen, Vorlauf-Messung:
      Spread 2.7e-10 benachbart / 1.6e-11 disjunkt — alle R innerhalb
      einer Klasse bei 9 Dezimalstellen identisch, Klassen-Abstand
      0.105). Die Dokumentations-Atome 1.082955/1.188108 sind
      6-Dezimal-Kuerzungen der abgeleiteten Atome.
  T8  S₃-Gegenprobe: unter dem Stabilisator S₃ (fixiert Position 3)
      zerfallen die 15 Muster in 4 Bahnen (Groessen 6/3/3/3) — unter
      S₃ allein waeren bis zu 4 Familien-Summen zu erwarten, gemessen
      werden genau die 2 S₄-Werte (S₃-Bahnen im selben S₄-Orbit haben
      nach Reindexierung GLEICHE Summen) — die gemessenen 2 Atome
      waehlen volles S₄.
  T9  n-Verallgemeinerung: n=3 → 1 Bahn (totale Shuffle-Blindheit),
      n=4 → 2 (12/3), n=5 → 2 (30/15), n=6 → 2 (60/45); adjacent =
      n·C(n−1,2), disjunkt = C(n,2)·C(n−2,2)/2.
Diagnose (D):
  64-Muster-Enumeration am dokumentierten Beispiel-cfg
  (0.002, 0.002, 0.02, 0.002): per-config k1/k2 ueber alle 2^6
  Zeichen-Vektoren; Bahn-Zerlegung unter dem cfg-Stabilisator (S₃,
  Ordnung 6) → 20 Bahnen (Burnside-Verifikation per expliziter
  Enumeration). Der dokumentierte Befund "23 distinkte R,
  Multiplizitäten = S₃-Orbit-Größen" ist in den Artefakten NICHT
  archiviert; die Re-Diagnose liefert die exakte Bahn-Struktur und
  die per-config-k-Koinzidenzen.
"""
import itertools
import json
import time

import numpy as np

import pt_hstar5_execution as h5
from pt_ququint_gue import H_PT_ququint

EXPERIMENT = "045-s4-closure-theorem"
HYPOTHESIS = "H-S4-CLOSURE"
RESULTS_PATH = "pt_s4_closure_theorem_results.json"

GAMMAS = (0.002, 0.02, 0.2)
CONJ_TOL = 1e-10
SPEC_TOL = 1e-9
SUM_TOL = 1e-9
ATOM_DECIMALS = 9


# === Konventionen ===

def perm_inverse(sigma):
    """sigma als Bild-Tupel (sigma(0),...,sigma(n-1)) -> Inverse."""
    inv = [0] * len(sigma)
    for i, s in enumerate(sigma):
        inv[s] = i
    return tuple(inv)


def apply_sigma_config(sigma, cfg):
    """(sigma·cfg)_i = cfg_{sigma(i)} — PULL-FORWARD, konsistent mit der
    Konjugationsrichtung U† kron_sum(blocks(cfg)) U =
    kron_sum(blocks(cfg∘sigma)): der Block an Position j ist der alte
    Block an Position sigma(j) (denn U†(B⊗_i)U = B⊗_{sigma^-1(i)})."""
    return tuple(cfg[sigma[i]] for i in range(len(cfg)))


def perm_unitary(sigma, n, d_block=5):
    """Positions-Permutations-Unitary, Konvention = kron_sum_c/np.kron:
    Position 0 ist der SIGNIFIKANTESTe Faktor (Digit 5^(n-1)).
    U |i_0 i_1 .. i_{n-1}> = |i_{inv(0)} i_{inv(1)} ..> mit inv = sigma^-1
    — der Inhalt von Position k wird der alte Inhalt von Position
    sigma^-1(k). Konvention numerisch gegen L2/L3 validiert."""
    inv = perm_inverse(sigma)
    d = d_block ** n
    U = np.zeros((d, d))
    for idx in range(d):
        pos = []
        x = idx
        for p in range(n - 1, -1, -1):  # Position 0 zuerst (big-endian)
            pos.append(x // d_block ** p % d_block)
        new_idx = 0
        for k in range(n):              # big-endian Aufbau
            new_idx = new_idx * d_block + pos[inv[k]]
        U[new_idx, idx] = 1.0
    return U


def sigma_signs(sigma, signs):
    """(sigma·s)_(a,b) = s_(sigma(a), sigma(b)) (sortiert), a<b — die
    PULL-FORWARD-Konvention, konsistent mit apply_sigma_config (cfg∘sigma)
    in der H-Identitaet T4: U† Σ_{a<b} s_ab (A⊗A)_{ab} U =
    Σ_{j<k} s_(sigma(j),sigma(k)) (A⊗A)_{jk}. signs: Tupel/Liste in
    Paar-Reihenfolge ODER Dict mit (a,b)-Schluesseln; Rueckgabe Tupel in
    Paar-Reihenfolge. (Die Bahn-MENGE {sigma·s} ist konventions- und
    Aktionsrichtungs-unabhaengig, da sigma die ganze Gruppe durchlaeuft
    — Orbit-Struktur, Groessen und adjacent/disjoint-Zahlung sind davon
    unberuehrt.)"""
    pairs = list(itertools.combinations(range(len(sigma)), 2))
    sdict = signs if isinstance(signs, dict) else dict(zip(pairs, signs))
    out = []
    for a, b in pairs:
        aa, bb = sorted((sigma[a], sigma[b]))
        out.append(sdict[(aa, bb)])
    return tuple(out)


def pair_term(a, b, n, A):
    """(A (x) A) auf Positionen (a, b), dim 5^n."""
    ops = ["I"] * n
    ops[a] = "A"
    ops[b] = "A"
    term = np.array([[1.0 + 0j]])
    for op in ops:
        term = np.kron(term, A if op == "A" else np.eye(5))
    return term


# === L1: A-Uniformität ===

def check_l1():
    mats = {g: H_PT_ququint(gamma=g)[1] for g in GAMMAS}
    base = mats[GAMMAS[0]]
    bit_equal = all(np.array_equal(base, m) for m in mats.values())
    max_dev = max(float(np.max(np.abs(base - m))) for m in mats.values())
    return {"bit_equal": bool(bit_equal), "max_abs_dev": max_dev,
            "lemma_ok": bool(bit_equal)}


# === L2/L3: Term- und Kron-Summen-Konjugation ===

def check_l2_l3():
    n = 4
    A = H_PT_ququint(gamma=GAMMAS[0])[1]
    pairs = list(itertools.combinations(range(n), 2))
    sigmas = list(itertools.permutations(range(n)))
    l2_max = 0.0
    for sigma in sigmas:
        U = perm_unitary(sigma, n)
        Ut = U.T
        for (a, b) in pairs:
            t_ab = pair_term(a, b, n, A)
            ia, ib = sorted((perm_inverse(sigma)[a],
                             perm_inverse(sigma)[b]))
            t_tgt = pair_term(ia, ib, n, A)
            dev = float(np.max(np.abs(Ut @ t_ab @ U - t_tgt)))
            l2_max = max(l2_max, dev)
    l3_max = 0.0
    rng = np.random.default_rng(20260928)
    for _ in range(3):
        blocks = [h5.pt_block(g) for g in
                  rng.choice(GAMMAS, size=n, replace=True)]
        ks = h5.kron_sum_c(blocks)
        for sigma in sigmas:
            U = perm_unitary(sigma, n)
            target = h5.kron_sum_c(
                [blocks[sigma[i]] for i in range(n)])
            dev = float(np.max(np.abs(U.T @ ks @ U - target)))
            l3_max = max(l3_max, dev)
    return {"l2_max_dev": l2_max, "l3_max_dev": l3_max,
            "lemma_ok": bool(l2_max < CONJ_TOL and l3_max < CONJ_TOL)}


# === T4: H-Identität ===

def check_t4(cache, n_sample=5, seed=20260928):
    rng = np.random.default_rng(seed)
    configs = h5.get_config_family()
    max_h = 0.0
    max_spec = 0.0
    max_k = 0.0
    for _ in range(n_sample):
        cfg = configs[int(rng.integers(len(configs)))]
        signs = tuple(int(x) for x in
                      rng.choice((-1, 1), size=6, replace=True))
        H = h5.folded_hamiltonian(cfg, signs, h5.EPS_PRIMARY)
        evs_ref, st_ref = h5._config_stats(cfg, h5.EPS_PRIMARY, signs,
                                           cache)
        for sigma in itertools.permutations(range(4)):
            U = perm_unitary(sigma, 4)
            lhs = U.T @ H @ U
            rhs = h5.folded_hamiltonian(apply_sigma_config(sigma, cfg),
                                        sigma_signs(sigma, signs),
                                        h5.EPS_PRIMARY)
            max_h = max(max_h, float(np.max(np.abs(lhs - rhs))))
            evs_rhs = h5.re_eigs(rhs)
            max_spec = max(max_spec, float(np.max(np.abs(evs_ref
                                                         - evs_rhs))))
            for key, tau in (("k1", h5.TAU1), ("k2", h5.TAU2)):
                k_rhs = h5.k_norm(evs_rhs, tau * cache[cfg]["t_h"])
                max_k = max(max_k, abs(st_ref[key] - k_rhs))
    return {"max_h_dev": max_h, "max_spec_dev": max_spec,
            "max_k_dev": max_k,
            "theorem_ok": bool(max_h < CONJ_TOL and max_spec < SPEC_TOL
                               and max_k < SPEC_TOL)}


# === T5: Familien-Summen ueber alle 15 Zwei-Minus-Muster ===

def two_minus_patterns(n=4):
    """Alle Zeichen-Vektoren mit genau zwei Minus (C(6,2) = 15)."""
    pairs = list(itertools.combinations(range(n), 2))
    out = []
    for combo in itertools.combinations(range(len(pairs)), 2):
        s = [1] * len(pairs)
        s[combo[0]] = -1
        s[combo[1]] = -1
        out.append(dict(zip(pairs, s)))
    return out


def is_adjacent(pattern):
    minus_pairs = [p for p, v in pattern.items() if v == -1]
    (a1, b1), (a2, b2) = minus_pairs
    return bool({a1, b1} & {a2, b2})


def orbit_of(pattern, sigmas):
    """Kanonischer Schluessel der Bahn eines Musters (sigma_signs liefert
    Tupel in Paar-Reihenfolge; die Bahn-MENGE ist aktionsrichtungs-
    unabhaengig, siehe sigma_signs-Docstring)."""
    return min(tuple(sigma_signs(sigma, pattern)) for sigma in sigmas)


def check_t5_t6(cache):
    """Familien-Summen je Zwei-Minus-Muster ueber die 78er-Familie."""
    configs = h5.get_config_family()
    eps = h5.EPS_PRIMARY
    stats = {}
    for idx, pattern in enumerate(two_minus_patterns()):
        signs = tuple(pattern[p] for p in sorted(pattern))
        k1s, k2s, rms = [], [], []
        for cfg in configs:
            _, st = h5._config_stats(cfg, eps, signs, cache)
            k1s.append(st["k1"])
            k2s.append(st["k2"])
            if st["r_median"] is not None:
                rms.append(st["r_median"])
        stats[idx] = {"signs": signs,
                      "adjacent": is_adjacent(pattern),
                      "k1_mean": float(np.mean(k1s)),
                      "k2_mean": float(np.mean(k2s)),
                      "R": float(np.mean(k2s) / np.mean(k1s)),
                      "r_median": (float(np.median(rms))
                                   if rms else None)}
    sigmas = list(itertools.permutations(range(4)))
    orbits = {}
    for idx, pattern in enumerate(two_minus_patterns()):
        orbits[idx] = orbit_of(pattern, sigmas)
    orbit_groups = {}
    for idx, key in orbits.items():
        orbit_groups.setdefault(key, []).append(idx)
    # Invarianz innerhalb, Trennung zwischen den Orbits
    max_within = 0.0
    for key, idxs in orbit_groups.items():
        ref = stats[idxs[0]]
        for idx in idxs[1:]:
            for q in ("k1_mean", "k2_mean", "R", "r_median"):
                if ref[q] is not None and stats[idx][q] is not None:
                    max_within = max(max_within,
                                     abs(ref[q] - stats[idx][q]))
    keys = list(orbit_groups)
    between_gap = (abs(stats[orbit_groups[keys[0]][0]]["R"]
                       - stats[orbit_groups[keys[1]][0]]["R"])
                   if len(keys) == 2 else None)
    # T6: prime/composite im benachbarten Orbit, Summen gleich auf Rundung
    s_prime = h5.prime_signs(4)
    s_comp = h5.composite_signs(4)
    prime_idx = [idx for idx, p in
                 enumerate(two_minus_patterns())
                 if tuple(p[q] for q in sorted(p)) == s_prime]
    comp_idx = [idx for idx, p in
                enumerate(two_minus_patterns())
                if tuple(p[q] for q in sorted(p)) == s_comp]
    prime_orbit = orbits[prime_idx[0]] if prime_idx else None
    comp_orbit = orbits[comp_idx[0]] if comp_idx else None
    # Repraesentant je Orbit (erster Index der Bahn-Liste) entscheidet
    # adjacent/disjoint — KEINE Iteration ueber Bahn-Keys in stats.
    adj_orbit_key = None
    dis_orbit_key = None
    for key, idxs in orbit_groups.items():
        if stats[idxs[0]]["adjacent"]:
            adj_orbit_key = key
        else:
            dis_orbit_key = key
    prime_adjacent = (prime_idx and is_adjacent(
        two_minus_patterns()[prime_idx[0]]))
    comp_adjacent = (comp_idx and is_adjacent(
        two_minus_patterns()[comp_idx[0]]))
    same_orbit = prime_orbit == comp_orbit if (prime_orbit
                                               and comp_orbit) else None
    sum_dev_pc = None
    if prime_idx and comp_idx:
        sum_dev_pc = abs(stats[prime_idx[0]]["k1_mean"]
                         - stats[comp_idx[0]]["k1_mean"])
        sum_dev_pc = max(sum_dev_pc, abs(stats[prime_idx[0]]["k2_mean"]
                                         - stats[comp_idx[0]]["k2_mean"]))
    # Tupel/Dict-Konsistenz der Aktion (frei, keine eigs): orbit_of nutzt
    # den Dict-Pfad, die Familien-Summen den Tupel-Pfad — identische
    # Bilder fuer alle 15 Muster x alle 24 sigma schliessen einen Pfad-
    # Sprung zwischen Bahn-Schluesselung und Summen-Berechnung aus.
    td_ok = True
    for pattern in two_minus_patterns():
        signs_t = tuple(pattern[p] for p in sorted(pattern))
        for sigma in sigmas:
            if sigma_signs(sigma, pattern) != sigma_signs(sigma, signs_t):
                td_ok = False
    return {"n_patterns": len(stats),
            "orbit_count": len(orbit_groups),
            "orbit_sizes": sorted((len(v) for v in orbit_groups.values()),
                                  reverse=True),
            "adjacent_counts": sorted(
                (sum(1 for i in v if stats[i]["adjacent"])
                 for v in orbit_groups.values()), reverse=True),
            "max_within_orbit_dev": max_within,
            "between_orbit_R_gap": between_gap,
            "prime_signs": list(s_prime), "composite_signs": list(s_comp),
            "prime_adjacent": bool(prime_adjacent),
            "composite_adjacent": bool(comp_adjacent),
            "prime_composite_same_orbit": same_orbit,
            "prime_composite_sum_dev": sum_dev_pc,
            "tuple_dict_konsistenz_ok": bool(td_ok),
            "adjacent_R": (float(stats[orbit_groups[adj_orbit_key][0]]
                                 ["R"])
                           if adj_orbit_key is not None else None),
            "disjoint_R": (float(stats[orbit_groups[dis_orbit_key][0]]
                                 ["R"])
                           if dis_orbit_key is not None else None),
            "per_pattern": {str(i): stats[i] for i in stats},
            "theorem_ok": bool(len(orbit_groups) == 2
                               and max_within < SUM_TOL
                               and between_gap is not None
                               and between_gap > 1e-6
                               and prime_adjacent and comp_adjacent
                               and same_orbit
                               and (sum_dev_pc is not None
                                    and sum_dev_pc < SUM_TOL)
                               and td_ok)}


# === T7: v1-Atom-Korrespondenz ===

def check_t7():
    """Die Atome werden AUS DEN ARCHIVIERTEN R-Werten selbst abgeleitet
    (9 Dezimalstellen): alle R innerhalb einer Orbit-Klasse muessen auf
    ATOM_DECIMALS identisch sein (Rundungs-Invarianz der
    Familien-Summen, gemessener Spread 2.7e-10 / 1.6e-11); die
    Dokumentations-Atome 1.082955/1.188108 muessen 6-Dezimal-Kuerzungen
    der abgeleiteten Atome sein (Vorlauf-Empirie: Deviation 1.9e-7 =
    reine Truncation)."""
    with open("pt_hstar5_phase6a_v1_degenerate.shuffle.jsonl",
              encoding="utf-8") as fh:
        recs = [json.loads(line) for line in fh if line.strip()]
    base = h5.prime_signs(4)
    perms = list(h5.shuffle_null_signs(base, n_perm=200,
                                       seed=h5.NULL_SEED))[:len(recs)]
    n_adj = n_dis = 0
    class_R = {"adjacent": [], "disjoint": []}
    for rec, perm in zip(recs, perms):
        # perm ist ein Tupel ueber die Paar-Reihenfolge (0,1)..(2,3)
        minus_pairs = [(a, b) for (a, b), v in
                       zip(itertools.combinations(range(4), 2), perm)
                       if v == -1]
        (a1, b1), (a2, b2) = minus_pairs
        adjacent = bool({a1, b1} & {a2, b2})
        if adjacent:
            n_adj += 1
            class_R["adjacent"].append(rec["R"])
        else:
            n_dis += 1
            class_R["disjoint"].append(rec["R"])
    # Atome aus den Daten: jeder Klasse genau EIN Wert bei 9 Dezimalen
    atoms = {}
    max_dev_within = 0.0
    for cls, xs in class_R.items():
        rounded = {round(x, ATOM_DECIMALS) for x in xs}
        atoms[cls] = rounded
        atom = sorted(rounded)[0]
        max_dev_within = max(max_dev_within,
                             max(abs(x - atom) for x in xs))
    n_atoms_total = sum(len(v) for v in atoms.values())
    # Dokumentations-Atome als 6-Dezimal-Kuerzungen verifizieren
    doc_atoms = {"adjacent": 1.082955, "disjoint": 1.188108}
    doc_ok = all(
        len(v) == 1
        and round(sorted(v)[0], 6) == doc_atoms[cls]
        for cls, v in atoms.items())
    return {"n_records": len(recs), "n_adjacent": n_adj,
            "n_disjoint": n_dis,
            "expected_ratio_adjacent": 12 / 15,
            "observed_ratio_adjacent": n_adj / len(recs),
            "derived_atoms": {k: sorted(v)[0] for k, v in atoms.items()},
            "n_distinct_atoms_per_class": {k: len(v)
                                           for k, v in atoms.items()},
            "n_atoms_total": n_atoms_total,
            "max_R_dev_within_class": max_dev_within,
            "rounding_invariance_ok": bool(max_dev_within <= 5e-10),
            "doc_atoms_truncation_ok": bool(doc_ok),
            "theorem_ok": bool(len(recs) == 132
                               and n_adj == 110 and n_dis == 22
                               and n_atoms_total == 2
                               and max_dev_within <= 5e-10
                               and doc_ok)}


# === T8: S₃-Gegenprobe ===

def check_t8(t5_result):
    """Stabilisator S₃ = {sigma : sigma(3) = 3}. Bahnen der 15 Muster
    unter S₃: 4 Bahnen (Groessen 6/3/3/3) — unter S₃ ALLEIN waeren bis
    zu 4 Familien-Summen (Atome) zu erwarten, gemessen werden genau die
    2 S₄-Werte (die 3 benachbarten S₃-Bahnen liegen im selben S₄-Orbit
    und haben nach T5/Reindexierung GLEICHE Summen). Die 2 Atome waehlen
    also volles S₄, nicht den Stabilisator. Familien-Summen werden aus
    T5 per_pattern WIEDERVERWENDET (keine eigenen eigs — der volle
    15x78-Grid steht bereits in T5)."""
    sig3 = [s for s in itertools.permutations(range(4)) if s[3] == 3]
    patterns = two_minus_patterns()
    orbits3 = {}
    for idx, pattern in enumerate(patterns):
        orbits3[idx] = min(tuple(sigma_signs(sigma, pattern))
                           for sigma in sig3)
    groups3 = {}
    for idx, key in orbits3.items():
        groups3.setdefault(key, []).append(idx)
    per_pattern = t5_result["per_pattern"]
    sums3 = {key: per_pattern[str(idxs[0])]["R"]
             for key, idxs in groups3.items()}
    distinct = sorted({round(v, 9) for v in sums3.values()})
    # S₃-Bahnen im selben S₄-Orbit muessen gleiche Summen haben (T5);
    # S₃-Bahnen in VERSCHIEDENEN S₄-Orbits: genau die 2 Klassen.
    same_s4 = {}
    for key, idxs in groups3.items():
        cls = "adjacent" if per_pattern[str(idxs[0])]["adjacent"] \
            else "disjoint"
        same_s4.setdefault(cls, []).append(key)
    cross_orbit_dev = 0.0
    for cls, keys in same_s4.items():
        if len(keys) > 1:
            ref = sums3[keys[0]]
            for k2 in keys[1:]:
                cross_orbit_dev = max(cross_orbit_dev, abs(ref - sums3[k2]))
    return {"n_orbits_s3": len(groups3),
            "orbit_sizes_s3": sorted((len(v) for v in groups3.values()),
                                     reverse=True),
            "n_distinct_sums_s3": len(distinct),
            "distinct_sums_s3": distinct,
            "same_s4_orbit_sum_dev": cross_orbit_dev,
            "expected_sizes_s3": [6, 3, 3, 3],
            "counterfactual_ok": bool(len(groups3) == 4
                                      and sorted(
                                          (len(v) for v in
                                           groups3.values()),
                                          reverse=True) == [6, 3, 3, 3]
                                      and len(distinct) == 2
                                      and cross_orbit_dev < SUM_TOL)}


# === T9: n-Verallgemeinerung (rein kombinatorisch) ===

def check_t9():
    out = {}
    for n in (3, 4, 5, 6):
        pairs = list(itertools.combinations(range(n), 2))
        pats = []
        for combo in itertools.combinations(range(len(pairs)), 2):
            s = dict(zip(pairs, [1] * len(pairs)))
            s[pairs[combo[0]]] = -1
            s[pairs[combo[1]]] = -1
            pats.append(s)
        sigmas = list(itertools.permutations(range(n)))
        seen = set()
        adj_n = dis_n = 0
        for p in pats:
            imgs = set()
            for sigma in sigmas:
                inv = perm_inverse(sigma)
                img = dict(zip(sorted(p),
                               (p[tuple(sorted((inv[a], inv[b])))]
                                for a, b in sorted(p))))
                imgs.add(tuple(img[q] for q in sorted(img)))
            seen.add(min(imgs))
            minus = [q for q, v in p.items() if v == -1]
            (a1, b1), (a2, b2) = minus
            if {a1, b1} & {a2, b2}:
                adj_n += 1
            else:
                dis_n += 1
        out[n] = {"n_patterns": len(pats),
                  "n_orbits": len(seen),
                  "adjacent": adj_n, "disjoint": dis_n,
                  "formula_adjacent": n * len(
                      list(itertools.combinations(range(n - 1), 2))),
                  "formula_disjoint": len(pairs) * (len(pairs) - 1) // 2
                  - n * len(list(itertools.combinations(range(n - 1), 2)))}
    return {"per_n": {str(k): v for k, v in out.items()},
            "theorem_ok": bool(
                out[3]["n_orbits"] == 1
                and out[4]["n_orbits"] == 2
                and out[4]["adjacent"] == 12 and out[4]["disjoint"] == 3
                and out[5]["n_orbits"] == 2 and out[5]["adjacent"] == 30
                and out[5]["disjoint"] == 15
                and out[6]["n_orbits"] == 2 and out[6]["adjacent"] == 60
                and out[6]["disjoint"] == 45
                and all(out[n]["adjacent"] == out[n]["formula_adjacent"]
                        for n in out))}


# === D: 64-Muster-Diagnose am dokumentierten Beispiel-cfg ===

def check_d(cache):
    cfg = (0.002, 0.002, 0.02, 0.002)
    eps = h5.EPS_PRIMARY
    pairs = list(itertools.combinations(range(4), 2))
    vals = []
    for bits in itertools.product((-1, 1), repeat=6):
        signs = bits
        _, st = h5._config_stats(cfg, eps, signs, cache)
        vals.append({"signs": list(signs), "k1": st["k1"],
                     "k2": st["k2"]})
    distinct = {}
    for v in vals:
        key = (round(v["k1"], 9), round(v["k2"], 9))
        distinct[key] = distinct.get(key, 0) + 1
    # Bahn-Zerlegung der 64 unter dem cfg-Stabilisator (Positionen mit
    # gleichem gamma: {0,1,3}; Position 2 einzigartig) -> S₃, Ordnung 6
    sig3 = [s for s in itertools.permutations(range(4)) if s[3] == 3]
    n_orbits_stab = 0
    seen = set()
    for bits in itertools.product((-1, 1), repeat=6):
        s = dict(zip(pairs, bits))
        imgs = {tuple(sigma_signs(sigma, s)) for sigma in sig3}
        seen.add(min(imgs))
    n_orbits_stab = len(seen)
    return {"cfg": list(cfg), "n_patterns": len(vals),
            "n_distinct_k_pairs": len(distinct),
            "multiplicities": sorted(distinct.values(), reverse=True),
            "n_orbits_stabilizer_s3": n_orbits_stab,
            "burnside_orbits_full_s4": 11,
            "doc_claim": "23 distinkte R, Multiplizitaeten = "
                         "S3-Orbit-Groessen 1/2/3/5/6 (nicht "
                         "archiviert; Re-Diagnose liefert die exakte "
                         "Bahn-Struktur)"}


# === Haupt ===

def main():
    t0 = time.time()
    configs_o2 = h5.get_config_family()
    cache = {}
    for cfg in configs_o2:
        _, t_h = h5.unfold_spectrum(cfg)
        cache[cfg] = {"t_h": t_h}
    print(f"cache: {len(cache)} cfgs ({time.time() - t0:.0f} s)",
          flush=True)

    results = {"experiment": EXPERIMENT, "hypothesis": HYPOTHESIS,
               "qpu": 0, "eps": h5.EPS_PRIMARY,
               "family_size": len(configs_o2)}
    for name, fn in (("l1_A_uniformitaet", check_l1),
                     ("l2_l3_konjugation", check_l2_l3),
                     ("t4_h_identitaet", lambda: check_t4(cache)),
                     ("t5_t6_familien_summen",
                      lambda: check_t5_t6(cache)),
                     ("t7_v1_atom_korrespondenz", check_t7),
                     ("t8_s3_gegenprobe",
                      lambda: check_t8(results["t5_t6_familien_summen"])),
                     ("t9_n_verallgemeinerung", check_t9),
                     ("d_64_muster_diagnose", lambda: check_d(cache))):
        t1 = time.time()
        results[name] = fn()
        results[name]["seconds"] = round(time.time() - t1, 1)
        print(f"{name}: ok={results[name].get('theorem_ok', results[name].get('lemma_ok'))} "
              f"({results[name]['seconds']} s)", flush=True)
    results["total_seconds"] = round(time.time() - t0, 1)
    # Kreuzprobe T5 <-> T7 (staerkster Abschluss): die aus Scratch
    # neu berechneten Familien-Summen-R muessen die aus dem v1-Archiv
    # abgeleiteten Atome auf ATOM_DECIMALS reproduzieren.
    t5_R = results["t5_t6_familien_summen"]
    t7_atoms = results["t7_v1_atom_korrespondenz"]["derived_atoms"]
    atom_dev = {
        "adjacent": abs(t5_R["adjacent_R"] - t7_atoms["adjacent"]),
        "disjoint": abs(t5_R["disjoint_R"] - t7_atoms["disjoint"]),
    }
    results["cross_t5_t7_atom"] = {
        "max_atom_dev": max(atom_dev.values()),
        "atom_dev": atom_dev,
        "ok": bool(all(v < 10 ** (-ATOM_DECIMALS) + 5e-10
                       for v in atom_dev.values())),
    }
    print(f"cross_t5_t7_atom: ok={results['cross_t5_t7_atom']['ok']} "
          f"(max dev {results['cross_t5_t7_atom']['max_atom_dev']:.2e})",
          flush=True)
    results["verdict_class"] = (
        "H_S4_CLOSURE_VERIFIED" if all(
            results[k].get("theorem_ok", results[k].get("lemma_ok",
                                                         True))
            for k in ("l1_A_uniformitaet", "l2_l3_konjugation",
                      "t4_h_identitaet", "t5_t6_familien_summen",
                      "t7_v1_atom_korrespondenz", "t8_s3_gegenprobe",
                      "t9_n_verallgemeinerung"))
        and results["cross_t5_t7_atom"]["ok"]
        else "H_S4_CLOSURE_DEVIATION_FOUND")
    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1)
    print(f"verdict_class: {results['verdict_class']} "
          f"({results['total_seconds']} s total)")
    return results


if __name__ == "__main__":
    main()