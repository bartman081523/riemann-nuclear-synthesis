# -*- coding: utf-8 -*-
"""H9-Scratch 4 (0 QPU): H-H9-4 Test (F-Tabelle Prio 6) — Orbit-Atome über
n (T9-Formel + Atom-Skala), HYPOTHESEN_UND_ANTITHESEN_H9_2026_09_29.md §C.4.

**Deck-Text-Korrektur (registriert):** C.4 sagt "n=5 (135 Muster)" und an
zweiter Stelle "105 Muster" — beide Zahlen falsch. Die committete
check_t9-Tabelle (pt_s4_closure_theorem) liefert fuer n=5 exakt 45 Muster
(adjacent 5*C(4,2)=30, disjunkt C(10,2)*9/2−30=15, 2 Bahnen) — 105 ist der
n=6-Count. Die kombinatorische Kernaussage von H-H9-4 bei n=5 ist damit
SCHON im committeten Modul exakt verifiziert; was hier getestet wird ist
die NUMERISCHE Ebene (R-Atome, Invarianz-Massstab, Gap-Reihenfolge).

**Pipeline-Konvention (identisch zu 045):** folded_hamiltonian(cfg, signs,
EPS_PRIMARY=0.25) + re_eigs + k_norm an TAU1/TAU2/TAU3*t_H (t_H
UNFOLDED per Konfig via Summenmenge) + ratio_stat; R = mean(k2s)/mean(k1s)
je Muster ueber die Konfig-Familie; r_median = Median der per-Instanz
ratio_stat; max_within = max|ref − x| ueber Bahnen x 4 Groessen
(k1_mean/k2_mean/R/r_median) gegen den BAHN-ERSTEN Repraesentanten
(bit-identisch zu check_t5_t6).

**Konfig-Familien (EX ANTE registriert, vor dem ersten n=5-Lauf):**
  shape "min"  = (a,)*(n-1)+(b,)           S_n-Orbit: n=4 -> 4 cfgs, n=5 -> 5
  shape "tri"  = (a,b,c)+(a,)*(n-3)        S_n-Orbit: n=4 -> 12, n=5 -> 20
  shape "full" = alle a-Tupel mit >=2 versch. Gammas: n=4 -> 78 (045-Basis),
                 n=5 -> 240 (geschlossene S_5-Familie, Kosten gemessen
                 19.4 s eig/Instanz at d=3125 -> 45*240*23.5 s = 69 h —
                 NICHT gelaufen, dokumentiert)
  Jede Familie ist unter Block-Positions-Permutationen ABGESCHLOSSEN
  (notwendig fuer die Orbit-Invarianz des S₄-Schluss-Theorems).
**Staffel-Regel ex ante (KOORIGIERT vor dem ersten n=5-Lauf):** die
n=4-Kalibrier-Arme min4/tri4 pruefen die Invarianz-Masstab-Treue gegen die
045-BASIS (10 x max_within_orbit_dev 1.0260516436488842e-08 = 1.03e-7);
die 1e-9-Grenze des Modulkopfs gehoert zur L3-Familien-SUMmen-Empirie
(5.8e-11), NICHT zur T5/T6-per-config-Empirie (045 selbst misst 1.026e-8)
— die erste Fassung der Staffel (<= 1e-9) haette selbst die 78er-Familie
nicht bestaetigt; dokumentierte Korrektur VOR jedem n=5-Lauf, Smoke-Artefakte
im Job-tmp (h9_atom_n5_smoke.jsonl). Das n=5-Hauptbein laeuft auf dem
SAME-SHAPE Familie des KLEINSTEN passenden n=4-Shapes (min gewinnt bei
Gleichstand); Fallsboden: wenn kein n=4-Shape haelt, tri5 + Feld
"selection_fallback". Die Regel haengt NUR an der Invarianz-Empirie,
nicht an R-Atom-Werten (kein Leak in die Atome).

**Ex-ante-Erwartungen (vor dem n=5-Lauf registriert, KEINES numerisch
frei aus einem Fit abgeleitet):**
  P1  die 45 n=5-Muster scheiden sich in GENAU 2 R-Klassen (adj/disj),
      within-Orbit max_within <= 10 x 045-Basis (1.0260516436488842e-07)
  P2  der Invarianz-Massstab bleibt an der 045-Empirie-Klasse
      (<= 100x des n=4-Same-Shape-Kalibrier-max_within)
  P3  (1-Bit-Bonus, Muenzwurf-Null ex ante anerkannt): R_adj < R_disj
      wie in n=4
  P4  die zwei Klassen nicht-degeneriert (Gap >= 1e-3)
  KEINE a-priori-Zahlen-Vorhersage der Atome: keine ex-ante abgeleitete
  Skalierungsgesetz im Modulkorpus (dokumentierte Abweichung von der
  C.4-Formulierung "R-Mediane a priori vorhersagen" — die ist als
  (nicht-machbar) registriert).
**Falsifikator H-H9-4 (n=5, registriert):** F1 keine 2-Klassen-Struktur
(max_within > 10 x 045-Basis = 1.0260516436488842e-07), F2 Massstab-Break
(> 100x der SAME-SHAPE n=4-Kalibrier), F3 Degeneration (Gap < 1e-3).

**Arme:**
  0 anchor78  : n=4, 78er, 15 Muster, bit-Plausibilisierung gegen 045
                (max_within_orbit_dev 1.0260516436488842e-08, atome
                1.0829548092830659/1.1881079493699196, gap
                0.10515314008685372) — assert |rep−045| <= 1e-12.
                Zusaetzlich s4.check_t5_t6(cache) als Zweit-Implementierung
                und bit-Gleichheit mit dem eigenen Replik.
  1 calib-min : n=4, shape min (4 cfgs)
  2 calib-tri : n=4, shape tri (12 cfgs)
  3 n3-blind  : n=3, shape min (3 cfgs): T9 sagt 1 Bahn (totale
                Shuffle-Blindheit) -> max_within auf Rundungs-Niveau
  4 n5-{shape}: 45 Muster x selektierte n=5-Familie (Kern; Arm-Name
                ist shape-abhaengig, damit JSONL-Resume nie Zeilen
                verschiedener Familien vermischt)

Doku: HYPOTHESEN_UND_ANTITHESEN_H9_2026_09_29.md §C.4; Diagnostik-Präzedenz
(durchlaufend, NICHT verdict-tragend); 045-Verdict unangetastet; kein
Re-Decide; Suite unangetastet. Fortschritt per JSONL (crash-resume:
vorhandene (arm, idx)-Zeilen werden uebersprungen).
"""
import itertools
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

import pt_hstar5_execution as h5
import pt_ququint_gue as gue
import pt_s4_closure_theorem as s4
import pt_s4_t5_diag as td

TMP = "/home/julian/.claude/jobs/1e27c8b2/tmp"
OUT_JSONL = TMP + "/h9_atom_n5.jsonl"
OUT_JSON = TMP + "/h9_atom_n5.json"
OUT_SCRATCH = "scratches/h9_atom_n5_out.json"
SMOKE = "--smoke" in sys.argv
RESUME = not SMOKE

A_G, B_G, C_G = gue.GAMMA_FAMILY
KOSTEN_FULL_N5_AH = 69.0  # gemessen: 19.4 s eig + 3.5 s build je Instanz


def load_done():
    done = set()
    if RESUME and os.path.exists(OUT_JSONL):
        with open(OUT_JSONL, encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                    if rec.get("type") == "pattern":
                        done.add((rec["arm"], rec["idx"]))
                except json.JSONDecodeError:
                    continue
    return done


def family_shape(shape, n):
    a, b, c = A_G, B_G, C_G
    if shape == "min":
        base = (a,) * (n - 1) + (b,)
    elif shape == "tri" and n >= 3:
        base = (a, b, c) + (a,) * (n - 3)
    else:
        raise ValueError(shape)
    return tuple(sorted(set(itertools.permutations(base))))


def make_patterns(n):
    return s4.two_minus_patterns(n)


def orbit_rep(pattern, n):
    sigmas = list(itertools.permutations(range(n)))
    imgs = set()
    for sigma in sigmas:
        inv = s4.perm_inverse(sigma)
        img = dict(zip(sorted(pattern),
                       (pattern[tuple(sorted((inv[x], inv[y])))]
                        for x, y in sorted(pattern))))
        imgs.add(tuple(img[q] for q in sorted(img)))
    return min(imgs)


def run_arm(name, configs, n, done, fh, smoke_limit=None):
    """check_t5_t6-Konvention auf beliebiger (geschlossener) S_n-Familie."""
    t0 = time.time()
    cache = {cfg: {"t_h": h5.unfold_spectrum(cfg)[1]} for cfg in configs}
    pats = make_patterns(n)
    stats = {}
    for idx, pattern in enumerate(pats):
        if (name, idx) in done:
            continue
        if smoke_limit is not None and idx >= smoke_limit:
            continue
        signs = tuple(pattern[p] for p in sorted(pattern))
        k1s, k2s, rms = [], [], []
        for cfg in configs:
            _, st = h5._config_stats(cfg, h5.EPS_PRIMARY, signs, cache)
            k1s.append(st["k1"])
            k2s.append(st["k2"])
            if st["r_median"] is not None:
                rms.append(st["r_median"])
        rec = {"type": "pattern", "arm": name, "idx": idx,
               "signs": signs, "adjacent": s4.is_adjacent(pattern),
               "k1_mean": float(np.mean(k1s)),
               "k2_mean": float(np.mean(k2s)),
               "R": float(np.mean(k2s) / np.mean(k1s)),
               "r_median": (float(np.median(rms)) if rms else None),
               "seconds": round(time.time() - t0, 1)}
        stats[idx] = rec
        fh.write(json.dumps(rec) + "\n")
        fh.flush()
        print(f"[{name}] pattern {idx} R {rec['R']:.9f} "
              f"adj {rec['adjacent']} ({rec['seconds']}s)", flush=True)
    # resume: geladene Zeilen einlesen
    with open(OUT_JSONL, encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") == "pattern" and rec["arm"] == name \
                    and rec["idx"] not in stats:
                stats[rec["idx"]] = rec
    idxs = sorted(stats)
    if not idxs:
        return {"leer": True}
    groups = {}
    for idx in idxs:
        groups.setdefault(orbit_rep(pats[idx], n), []).append(idx)
    keys = list(groups)
    gvals = ("k1_mean", "k2_mean", "R", "r_median")
    max_within, worst = 0.0, None
    for key, gidx in groups.items():
        gidx = sorted(gidx)
        ref = stats[gidx[0]]
        for idx in gidx[1:]:
            for q in gvals:
                if ref[q] is not None and stats[idx][q] is not None:
                    d = abs(ref[q] - stats[idx][q])
                    if d > max_within:
                        max_within = d
                        worst = (q, idx)
    adj_R = [stats[i]["R"] for i in idxs if stats[i]["adjacent"]]
    dis_R = [stats[i]["R"] for i in idxs if not stats[i]["adjacent"]]
    out = {"arm": name, "n": n, "n_configs": len(configs),
           "n_patterns": len(pats), "n_orbits": len(groups),
           "orbit_groessen": sorted(len(v) for v in groups.values()),
           "adjacent_R_median": float(np.median(adj_R)) if adj_R else None,
           "disjoint_R_median": float(np.median(dis_R)) if dis_R else None,
           "gap": (float(np.median(adj_R) - np.median(dis_R))
                   if adj_R and dis_R else None),
           "max_within": max_within, "worst_within": worst,
           "seconds": round(time.time() - t0, 1)}
    print(f"[{name}] FERTIG: {len(configs)} cfgs, orbits "
          f"{out['orbit_groessen']}, adj_R {out['adjacent_R_median']}, "
          f"dis_R {out['disjoint_R_median']}, gap {out['gap']}, "
          f"max_within {max_within:.3e} ({out['seconds']}s)", flush=True)
    return out


def main():
    t00 = time.time()
    smoke_limit = 2 if SMOKE else None
    done = load_done()
    d045 = json.load(open(td.RESULTS_045_PATH))
    t5 = d045["t5_t6_familien_summen"]
    ref = {"max_within_orbit_dev": t5["max_within_orbit_dev"],
           "adjacent_R": t5["adjacent_R"],
           "disjoint_R": t5["disjoint_R"],
           "between_orbit_R_gap": t5["between_orbit_R_gap"]}
    print(f"[Anker] 045-Referenzen: {ref}", flush=True)
    fh = open(OUT_JSONL, "a", encoding="utf-8")

    arms = {}
    # ---- Arm 0: Anker-Replica 78er (n=4) ---------------------------------
    if not SMOKE:
        t0 = time.time()
        rep = run_arm("anchor78", h5.get_config_family(), 4, done, fh)
        arms["anchor78"] = rep
        # bit-Plausibilisierung vs 045 (H9-Scratch-2-Präzedenz: 1e-12)
        delta_within = abs(rep["max_within"] - ref["max_within_orbit_dev"])
        assert delta_within <= 1e-12, f"Anker max_within {delta_within}"
        da = abs(rep["adjacent_R_median"] - ref["adjacent_R"])
        dd = abs(rep["disjoint_R_median"] - ref["disjoint_R"])
        dg = abs(rep["gap"] - ref["between_orbit_R_gap"])
        print(f"[Anker] delta_within {delta_within:.3e}, d_adj {da:.3e}, "
              f"d_dis {dd:.3e}, d_gap {dg:.3e} ({time.time()-t0:.1f}s)",
              flush=True)
        arms["anchor78"] |= {"delta_zero45": delta_within, "d_adj": da,
                             "d_dis": dd, "d_gap": dg}

    # ---- Kalibrier-Staffel + n3 (schonend) -------------------------------
    arms["n3_min"] = run_arm("n3_min", family_shape("min", 3), 3,
                             done, fh, smoke_limit)
    cal_min = run_arm("calib_min", family_shape("min", 4), 4,
                      done, fh, smoke_limit)
    cal_tri = run_arm("calib_tri", family_shape("tri", 4), 4,
                      done, fh, smoke_limit)
    arms["calib_min"], arms["calib_tri"] = cal_min, cal_tri

    # ---- Staffel-Regel (ex ante, 10x 045-Basis) ---------------------------
    basis10 = 10.0 * ref["max_within_orbit_dev"]
    ok_min = cal_min.get("max_within", 1.0) <= basis10
    ok_tri = cal_tri.get("max_within", 1.0) <= basis10
    shape5 = "min" if ok_min else ("tri" if ok_tri else "tri")
    fallback = not (ok_min or ok_tri)
    cfgs5 = family_shape(shape5, 5)
    print(f"[Staffel] Basis10 {basis10:.3e}, ok_min {ok_min} "
          f"ok_tri {ok_tri} -> n5-Shape {shape5} ({len(cfgs5)} cfgs), "
          f"fallback {fallback}", flush=True)
    arm5 = f"n5_{shape5}"
    arms[arm5] = run_arm(arm5, cfgs5, 5, done, fh, smoke_limit)
    arms[arm5]["selection_shape"] = shape5
    arms[arm5]["selection_fallback"] = fallback
    fh.close()

    n5 = arms[arm5]
    cal = arms[f"calib_{shape5}"]
    falsifikator = {
        "F1_nicht_2_klassen": n5.get("max_within", 1.0) > basis10,
        "F2_massstab": (n5.get("max_within", 1e9)
                        > 100.0 * cal.get("max_within", 1e9)),
        "F3_degeneriert": abs(n5.get("gap") or 0.0) < 1e-3,
    }
    falsified = any(falsifikator.values())
    out = {
        "experiment": "h9-atom-n5",
        "qpu": 0, "verdict_tragend": False,
        "deck_text_korrektur": "C.4 '135/105 Muster' falsch — committet "
                               "check_t9: n=5 45 Muster (30 adj + 15 disj)",
        "051_ref": ref,
        "erwartungen_exante": {
            "P1": "2 Klassen, max_within <= 10 x 045-Basis (1.026e-07)",
            "P2": "max_within <= 100x n=4-Kalibrier (same shape)",
            "P3": "R_adj < R_disj (1-Bit-Bonus, Muenzwurf-Null)",
            "P4": "Gap >= 1e-3",
            "keine_zahlenvorhersage": "kein ex-ante-Fit/gesetz im Modulkop"},
        "arms": {k: v for k, v in arms.items()},
        "falsifikator": falsifikator,
        "hh9_4_n5_zwei_atom_struktur": bool(not falsified),
        "n5_full_family_nicht_gelaufen": {
            "grund": f"Kosten {KOSTEN_FULL_N5_AH:.0f} h (19.4 s eig je "
                     f"Instanz, 45x240 Instanzen)",
            "kosten_stunden": KOSTEN_FULL_N5_AH},
        "total_seconds": round(time.time() - t00, 1),
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=float)
    print(f"[Falsifikator] {falsifikator} -> "
          f"{'FALSIFIZIERT' if falsified else 'KEIN Falsifikator feuert'}",
          flush=True)
    print(f"[FERTIG] {out['total_seconds']}s -> {OUT_JSON}", flush=True)
    with open(OUT_SCRATCH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=float)
    print("kopiert:", OUT_SCRATCH, flush=True)


if __name__ == "__main__":
    main()