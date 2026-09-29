# -*- coding: utf-8 -*-
"""045-T5-Diagnose: Herkunft der EINZIGEN Verletzung in
H_S4_CLOSURE_DEVIATION_FOUND (EXPERIMENT 045, 0 QPU).

STATUS: NICHT verdict-tragend (Praezedenz gamma_arm, Phase 11d). Das
committete Frozen-Run-Verdict H_S4_CLOSURE_DEVIATION_FOUND aus
pt_s4_closure_theorem_results.json bleibt unangetastet — dieses Modul
erklaert die Abweichung, es re-decided nichts (keine Toleranz-Erhoehung,
keine Praedikat-Aenderung).

BEFUND (Familien-Summen, T5): max_within_orbit_dev 1.0260516436488842e-08
> SUM_TOL 1e-9, und die Abweichung traegt zu 100 % an r_median (adj
1.026e-08, disj 3.203e-09); alle drei GEMITTELten Groessen (k1_mean,
k2_mean, R) halten beide Bahnen bei <= 2.73e-10 (Faktor 3.7 unter
SUM_TOL) — die Orbit-Struktur-Elemente des T5-Praedikats (2 Bahnen
12/3, adjacent_counts [12,0], between_gap 0.105 > 1e-6,
prime/composite in einer Bahn, sum_dev_pc 5.95e-11, td_ok) und alle
uebrigen Theoreme (T4/T7/T8/T9, Kreuzprobe) sind gruen.

MECHANISMUS (gemessen, vier Kettenglieder):
  1. H-Entry-Level: unter Konjugation sind H-Eintraege bit-verschieden
     um l3_max_dev = 3.554447978966673e-15 (045-l2_l3) — in exakter
     Arithmetik identisch.
  2. Eigenwert-Level: der allgemeine (nicht-Hermitesche) 625x625-Solver
     (re_eigs via np.linalg.eigvals) hat einen Rundungs-Boden
     ~2.8e-13 pro Eintrags-Stoerung (045-t4: max_spec_dev 5.0e-13).
  3. t_H-Ampifikation: ratio_stat leitet t_H INTERN pro Instanz ab
     (heisenberg_time(evs) = 2*pi/Median der positiven Luecken,
     Schwelle 1e-12) — der inverse Median-Gap traegt die
     Eigenwert-Noise: 3.55e-15 am Eintrag -> dt_H ~ 2.0e-09.
  4. r-Level: r = K(tau2*t_H)/K(tau1*t_H) an diesem pro-instanz t_H
     -> dr ~ 1.1e-8. Die beobachtete r_median-Abweichung der
     Extremmuster 6/10 (1.138e-08) wird durch die Eintrags-Perturbation
     auf exakt dem l3-Level auf 0.1 % reproduziert.

ASYMMETRIE-KONSTRUKTIONSFAKT (erklaert, warum NUR r_median kippt):
  _config_stats bewertet k1/k2/k3 am CACHE-t_H (unfold_spectrum:
  exakte Summenmenge, nur cfg-abhaengig — unter Bahn-Reindexing
  stabil), aber r_median via ratio_stat am per-Instanz-Eigenwert-t_H.
  Die Orbit-Invarianz ist eine Reindexing-Identitaet ueber die
  permutations-abgeschlossene 78er-Familie: Mittelung ueberlebt sie
  (Noise-Mittelung auf ~1e-10), die Rang-Statistik Median ist zwar
  permutations-invariant (in exakter Arithmetik exakt), traegt aber
  den elementweisen per-record-Noise (~1e-8) in den mittleren
  Ordnungsstatistiken weiter.

MULTISET-PROBE (probe_a, Voll-Familie): sortierte r-Multisets zweier
Bahn-Mitglieder stimmen elementweise auf ~1e-8 ueberein — die
Orbit-Invarianz haelt als Multiset-Identitaet (Permutation exakt,
Rundung elementweise); der Median erbt genau dieses Mass.

Die registrierte Empirie-Basis des Modulkopfs (5.8e-11) war auf die
gemittelten Groessen/Atome kalibriert; r_median lief im selben
Toleranz-Band mit — die Diagnose dokumentiert das, aendert es nicht.
"""
from __future__ import annotations

import json
import time

import numpy as np

import pt_hstar5_execution as h5
import pt_s4_closure_theorem as s4

RESULTS_045_PATH = "pt_s4_closure_theorem_results.json"
DIAG_RESULTS_PATH = "pt_s4_t5_diag_results.json"

SUM_TOL = 1e-9          # Spiegel des 045-Moduls (KEINE Erhoehung)
QUANTITIES = ("k1_mean", "k2_mean", "R", "r_median")
MEAN_BASED = ("k1_mean", "k2_mean", "R")
BAHNEN = {"adjacent": (6, 10), "disjoint": (4, 7)}
ENTRY_DELTA = 3.554447978966673e-15   # 045-l2_l3 l3_max_dev
DELTAS = (ENTRY_DELTA, 1e-14, 1e-13)
PROBE_CFG_INDEX = 0


def _orbit_groups(results):
    """Bahn-Mitglieder aus den committeten 045-per_pattern-Daten."""
    per = results["t5_t6_familien_summen"]["per_pattern"]
    groups = {}
    for key, st in per.items():
        groups.setdefault(st["adjacent"], []).append(int(key))
    return {("adjacent" if adj else "disjoint"): sorted(v)
            for adj, v in groups.items()}


def decompose_max_within(results):
    """max_within je Groesse aus den committeten per_pattern-Daten —
    identische Referenzwahl wie check_t5_t6 (erstes idx je Bahn)."""
    per = results["t5_t6_familien_summen"]["per_pattern"]
    groups = _orbit_groups(results)
    out = {}
    for name, idxs in groups.items():
        ref = per[str(idxs[0])]
        out[name] = {q: max(abs(per[str(i)][q] - ref[q]) for i in idxs)
                     for q in QUANTITIES}
    mean_based = max(out[n][q] for n in groups for q in MEAN_BASED)
    out["mean_based_max_within"] = mean_based
    out["mean_based_unter_sum_tol"] = bool(mean_based < SUM_TOL)
    r_max = max(out[n]["r_median"] for n in groups)
    out["r_median_max"] = r_max
    out["r_median_einzige_verletzung"] = bool(
        r_max >= SUM_TOL and out["mean_based_max_within"] < SUM_TOL)
    out["reproduziert_045_max_within"] = bool(
        abs(r_max
            - results["t5_t6_familien_summen"]["max_within_orbit_dev"])
        == 0.0)
    return out


def _r_familie(patterns, cache):
    """Pro Muster: Liste (cfg-weise) r = ratio_stat(evs), None
    durchgereicht, ueber die volle 78er-Familie."""
    pats = s4.two_minus_patterns()
    familien = {}
    for p in patterns:
        signs = tuple(pats[p][q] for q in sorted(pats[p]))
        rows = []
        for cfg in h5.get_config_family():
            _, st = h5._config_stats(cfg, h5.EPS_PRIMARY, signs, cache)
            rows.append(st["r_median"])
        familien[p] = rows
    return familien


def _multiset_vergleich(familien, p, q):
    """Sortierte elementweise Differenz zweier Bahn-r-Multisets."""
    a = sorted(v for v in familien[p] if v is not None)
    b = sorted(v for v in familien[q] if v is not None)
    out = {"p": p, "q": q, "n_a": len(a), "n_b": len(b),
           "multiset_gleich_lang": len(a) == len(b)}
    if len(a) == len(b) and a:
        diffs = np.abs(np.asarray(a) - np.asarray(b))
        out["sorted_elementwise_max"] = float(diffs.max())
        out["sorted_elementwise_median"] = float(np.median(diffs))
        out["r_median_p"] = float(np.median(a))
        out["r_median_q"] = float(np.median(b))
        out["r_median_diff"] = float(out["r_median_p"] - out["r_median_q"])
    return out


def probe_a_multiset(cache):
    """Voll-Familien-Multiset-Probe: r ueber 78 Configs fuer die
    Extremmuster 6/10 (adjacent) und 4/7 (disjunkt)."""
    t0 = time.time()
    familien = _r_familie(tuple(p for pa in BAHNEN.values()
                                for p in pa), cache)
    vergleiche = [_multiset_vergleich(familien, p, q)
                  for p, q in BAHNEN.values()]
    return {"vergleiche": vergleiche, "seconds": round(time.time() - t0, 1)}


def probe_b_kette():
    """Eintrags-Perturbation am l3-Level -> Kette dEig/dt_H/dr."""
    cfg = h5.get_config_family()[PROBE_CFG_INDEX]
    pats = s4.two_minus_patterns()
    signs = tuple(pats[6][q] for q in sorted(pats[6]))
    H0 = h5.folded_hamiltonian(cfg, signs, h5.EPS_PRIMARY)
    evs0 = h5.re_eigs(H0)
    r0 = h5.ratio_stat(evs0)
    t0 = h5.heisenberg_time(evs0)
    kette = []
    for delta in DELTAS:
        H1 = H0.copy()
        H1[0, 0] += delta
        evs1 = h5.re_eigs(H1)
        r1 = h5.ratio_stat(evs1)
        kette.append({"delta": delta,
                      "d_eig": float(np.max(np.abs(evs1 - evs0))),
                      "d_t_h": float(h5.heisenberg_time(evs1) - t0),
                      "d_r": float(r1 - r0)})
    return {"cfg_index": PROBE_CFG_INDEX, "kette": kette,
            "r_basis": float(r0), "t_h_basis": float(t0)}


def t_h_quellen(cache):
    """Asymmetrie der t_H-Quellen an der Probe-Config: Cache (unfold,
    exakte Summenmenge) vs. per-Instanz-Eigenwerte (ratio_stat)."""
    cfg = h5.get_config_family()[PROBE_CFG_INDEX]
    t_cache = cache[cfg]["t_h"]
    pats = s4.two_minus_patterns()
    signs = tuple(pats[6][q] for q in sorted(pats[6]))
    evs0 = h5.re_eigs(h5.folded_hamiltonian(cfg, signs, h5.EPS_PRIMARY))
    t_eig = h5.heisenberg_time(evs0)
    r_eig = h5.ratio_stat(evs0)
    r_cache = (h5.k_norm(evs0, h5.TAU2 * t_cache)
               / h5.k_norm(evs0, h5.TAU1 * t_cache))
    ev = np.sort(evs0)
    gaps = np.diff(ev)
    pos = gaps[gaps > 1e-12]
    return {"t_h_unfold_cache": float(t_cache),
            "t_h_eigvals": float(t_eig),
            "quotient": float(t_cache / t_eig),
            "median_pos_gap": float(np.median(pos)),
            "n_pos_gaps": int(pos.size),
            "n_exkl_luecken": int(gaps.size - pos.size),
            "r_am_eigen_t_h": float(r_eig),
            "r_am_cache_t_h": float(r_cache),
            "r_quell_diff": float(r_eig - r_cache)}


def main():
    t_start = time.time()
    with open(RESULTS_045_PATH, encoding="utf-8") as fh:
        results = json.load(fh)
    deko = decompose_max_within(results)
    cache = {}
    for cfg in h5.get_config_family():
        _, t_h = h5.unfold_spectrum(cfg)
        cache[cfg] = {"t_h": t_h}
    probe_a = probe_a_multiset(cache)
    probe_b = probe_b_kette()
    quellen = t_h_quellen(cache)
    dev_045 = results["t5_t6_familien_summen"]["max_within_orbit_dev"]
    doc = {
        "experiment": "045-s4-t5-diagnose",
        "basis": RESULTS_045_PATH,
        "verdict_tragend": False,
        "qpu": 0,
        "decomposition": deko,
        "probe_a_multiset": probe_a,
        "probe_b_kette": probe_b,
        "t_h_quellen": quellen,
        "beobachtet_max_within_045": dev_045,
        "mechanismus": ("H-Entry 3.55e-15 -> dEig ~2.8e-13 -> "
                        "dt_H ~2e-9 (t_H = 2pi/Median-Luecke) -> "
                        "dr ~1.1e-8; Mittelung hebelt die Noise, die "
                        "Rang-Statistik r_median traegt sie"),
        "conclusions": {
            "struktur_auf_gemittelten_groessen_gruen":
                deko["mean_based_unter_sum_tol"],
            "r_median_einzige_verletzung":
                deko["r_median_einzige_verletzung"],
            "verdict_045_unveraendert":
                results["verdict_class"],
            "keine_toleranz_erhoehung": True,
        },
        "total_seconds": round(time.time() - t_start, 1),
    }
    with open(DIAG_RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
    print(f"verdict_class 045 (unveraendert): {results['verdict_class']}")
    print(f"mean_based_max_within: "
          f"{deko['mean_based_max_within']:.4e} "
          f"(< SUM_TOL: {deko['mean_based_unter_sum_tol']})")
    for v in probe_a["vergleiche"]:
        print(f"Multiset {v['p']} vs {v['q']}: n {v['n_a']}/{v['n_b']} "
              f"sorted_elementwise_max "
              f"{v.get('sorted_elementwise_max', float('nan')):.3e}"
              f"  r_median_diff {v.get('r_median_diff', float('nan')):+.4e}")
    k = probe_b["kette"][0]
    print(f"Kette (delta {k['delta']:.3e}): dEig {k['d_eig']:.3e} "
          f"dt_H {k['d_t_h']:+.3e} dr {k['d_r']:+.4e}")
    print(f"total_seconds: {doc['total_seconds']}")
    return doc


if __name__ == "__main__":
    main()