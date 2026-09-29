# -*- coding: utf-8 -*-
"""H9-Scratch 2 (0 QPU): SOURCE-UNIFIED-Test an der EINZIGEN
H_S4_CLOSURE_DEVIATION_FOUND-Verletzung (045, T5 r_median).

Kern der Antithese SA-1 (_config_stats-Asymmetrie): k1/k2/k3 werden am
CACHE-t_h bewertet (unfold_spectrum, konfig-abhaengig, sign-frei),
r_median aber via ratio_stat am PER-INSTANCE-t_h (heisenberg_time der
eigenen Eigenwerte). Test: die Orbit-Invarianz-Medians nochmal, mit r
auf dem EINHEITLICHEN Cache-t_h:

    r_unified(cfg) = K(evs, TAU2*t_cache[cfg]) / K(evs, TAU1*t_cache[cfg])

vs. r_inst(cfg) = ratio_stat(evs)  [Replik-Sanity vs 045].

Entscheidend beidseitig:
  - kippt max_within unter r_unified unter SUM_TOL (1e-9) =>
    die Verletzung ist ein reines Quellen-Artefakt (Antithese haelt).
  - bleibt sie ~1e-8 => die Abweichung traegt auch quellen-einheitlich
    (Antithese kippt — struktureller Rest).

Read-only auf committeten Modulen (pt_hstar5_execution,
pt_s4_closure_theorem, pt_s4_t5_diag); KEIN Verdict-Re-Decide, keine
Toleranz-Aenderung — Diagnostik wie pt_s4_t5_diag (Praezedenz).

ERGEBNIS 2026-09-29 (Full-Run 538.8 s): max_within_inst 1.1384355902421817e-08
vs max_within_unified 6.423892529028308e-10 < SUM_TOL — Kriterium erfuellt
(scratches/h9_s4_source_unified_out.json; Run-Log nur im Job-tmp,
*.run.log ist .gitignore'd; Muster 6 inst_median
1.9147852243778032 bit-gleich 045-Referenz r_median_p(6)). Dokumentiert in
HYPOTHESEN_UND_ANTITHESEN_H9_2026_09_29.md §C.3 (Grade B+, kein Re-Decide).
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

import pt_hstar5_execution as h5
import pt_s4_closure_theorem as s4
import pt_s4_t5_diag as td

OUT_JSONL = "/home/julian/.claude/jobs/1e27c8b2/tmp/h9_s4_unified.jsonl"
OUT_JSON = "/home/julian/.claude/jobs/1e27c8b2/tmp/h9_s4_unified.json"
SUM_TOL = 1e-9


def main(patterns=None):
    t0 = time.time()
    results = json.load(open(td.RESULTS_045_PATH))
    pats = s4.two_minus_patterns()
    if patterns is None:
        patterns = list(range(len(pats)))
    cfgs = list(h5.get_config_family())
    print(f"[h9] cfgs={len(cfgs)} patterns={patterns}", flush=True)

    cache = {}
    for cfg in cfgs:
        _, t_h = h5.unfold_spectrum(cfg)
        cache[cfg] = {"t_h": t_h}
    print(f"[h9] cache build fertig {time.time()-t0:.1f}s", flush=True)

    fh = open(OUT_JSONL, "a", encoding="utf-8")
    per_pattern = {}
    per_pattern_unified = {}
    for p in patterns:
        signs = tuple(pats[p][q] for q in sorted(pats[p]))
        r_inst, r_uni = [], []
        t1 = time.time()
        for cfg in cfgs:
            evs = h5.re_eigs(h5.folded_hamiltonian(cfg, signs, h5.EPS_PRIMARY))
            t_c = cache[cfg]["t_h"]
            ri = h5.ratio_stat(evs)
            if ri is not None:
                r_inst.append(float(ri))
            r_uni.append(float(h5.k_norm(evs, h5.TAU2 * t_c)
                               / h5.k_norm(evs, h5.TAU1 * t_c)))
        per_pattern[p] = r_inst
        per_pattern_unified[p] = r_uni
        rec = {"pattern": int(p), "n": len(r_inst),
               "r_inst_median": float(np.median(r_inst)),
               "r_uni_median": float(np.median(r_uni)),
               "seconds": round(time.time() - t1, 1)}
        fh.write(json.dumps(rec) + "\n")
        fh.flush()
        print(f"[h9] pattern {p}: inst_median {rec['r_inst_median']:.10f} "
              f"uni_median {rec['r_uni_median']:.10f} "
              f"({rec['seconds']}s)", flush=True)

    bahnen = td.BAHNEN
    vergleiche = []
    max_inst = 0.0
    max_uni = 0.0
    for name, (p, q) in bahnen.items():
        if p not in per_pattern or q not in per_pattern:
            continue
        di = abs(float(np.median(per_pattern[p])) - float(np.median(per_pattern[q])))
        du = abs(float(np.median(per_pattern_unified[p]))
                 - float(np.median(per_pattern_unified[q])))
        max_inst = max(max_inst, di)
        max_uni = max(max_uni, du)
        vergleiche.append({"bahn": name, "pair": [p, q],
                           "d_inst": di, "d_unified": du})
        print(f"[h9] {name} ({p},{q}): d_inst={di:.3e} d_unified={du:.3e}",
              flush=True)

    doc = {
        "experiment": "h9-s4-source-unified",
        "basis": td.RESULTS_045_PATH,
        "verdict_tragend": False,
        "qpu": 0,
        "patterns": patterns,
        "vergleiche": vergleiche,
        "max_within_inst": max_inst,
        "max_within_unified": max_uni,
        "beobachtet_045_max_within": results["t5_t6_familien_summen"][
            "max_within_orbit_dev"],
        "sum_tol": SUM_TOL,
        "unified_unter_tol": bool(max_uni < SUM_TOL),
        "inst_reproduziert": bool(
            abs(max_inst - results["t5_t6_familien_summen"][
                "max_within_orbit_dev"]) < 1e-12),
        "per_pattern_inst": {str(k): v for k, v in per_pattern.items()},
        "per_pattern_unified": {str(k): v for k, v in per_pattern_unified.items()},
        "total_seconds": round(time.time() - t0, 1),
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1, default=float)
    print(f"[h9] FERTIG {time.time()-t0:.1f}s -> {OUT_JSON}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main([int(x) for x in sys.argv[1:]])
    else:
        main()