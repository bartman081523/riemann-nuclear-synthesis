# -*- coding: utf-8 -*-
"""EXPERIMENT 055 (H-H9 FPrio 4+8) — Stage-3-Aer EXACT-ONLY fuer das
055-Grid (0 QPU): b_P fuer ALLE 37 Reihen des Combined-Beins.

Mirror des K2-Stage-3-Beins (pt_ram_q6_k2_stage3aer.py, 051): das 055-Eval
konsumiert ausschliesslich stage3["b_p"]/["prereg_md5"]/["status"] via das
GEFRORENE 044-Gesetz (pt_ram_q_hardware3_eval.py) — kein Gate liest
cells/sampled.  Gegenueber h3a.run_stage3 (committet 044, Voll-Grid mit
sampled/gamma_aer/Echo-Leiter/w_B''-Gate-S) weggekuerzt:

  * Sampled-Bein, gamma_aer, Echo-Leiter, form_validation: 044-Diagnostik,
    kein Auswertungs-Vertrag.
  * Echo-Leiter ist RAW-abhaengig im Eval (r1 vs kappa_hat) und braucht
    kein Stage-3-Artefakt.

Registriert hier (Vertrag):
  * b_P fuer ALLE 37 Punkte: 13 verdict (Run-3-Verdict-P), 13 cal-old
    (Run-2-Verdict-P) und 11 Ladder-P (WOERTLICHE Phase-11b-Regel, FRISCH
    — kein 044-Praezedenz) via fit_b_p ueber die EXAKTEN Level-Kurven
    (STRESS_GRID_P1, density_matrix, RO_STRESS), Keys 'set|arm|P' via
    h3a.pkey auf den GESTEMPELTEN Records (p48.eval_grid).
  * b_P-KONSISTENZ der 26 Legacy-Keys DIREKT gegen das committete
    044-Stage-3 (h3a.RESULTS_PATH): die 13 055-verdict-Reihen SIND die
    044-verdict-Zeilen (Keys 'verdict|arm|P') und die 13 055-cal-old-
    Reihen SIND die 044-cal-Zeilen (Keys 'cal|arm|P') — KEIN Remapping,
    dieselbe Belegkonvention, derselbe Codepfad (exact_point_level +
    fit_b_p).  Die 11 Ladder-Keys sind FRISCH (keine 044-Quelle).
  * DEGENERAT-Pflicht: fit_b_p braucht >= 2 Domain-Nodes (kappa >= 0.81);
    jeder Fit-Fehler wird REGISTRIERT (b_p_fit_failed), NICHT absorbiert
    — fehlende b_p-Keys lassen das Eval fuer die Reihe delta_cal/res_v3
    = None rechnen (registriert, kein Gate-Verstoss).
  * Prereg-Binding: prereg_md5 = doc['md5'] des GEFRORENEN 055-Payloads
    (pt_ram_q_prio48_prereg.json, REGISTERED_NOT_MEASURED, VOR jeder
    Messung) — Payload-Content-md5, NICHT die Byte-MD5 (indent-Spaltung,
    053-Praezedenz).
Token-DISZIPLIN: 0 QPU, kein Fez/Kingston-Kontakt, kein Token.
"""
import json

import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_aer as h3a
import pt_ram_q_prio48 as p48

RESULTS_PATH = "pt_ram_q_prio48_stage3_results.json"
STATUS_OK = "STAGE3_AER_EXACT_ONLY_COMPLETED"
STATUS_DEGENERAT = "STAGE3_AER_EXACT_ONLY_DEGENERAT"
N_EXPECTED_POINTS = 37        # 13 verdict + 13 cal-old + 11 Ladder
N_EXPECTED_LEGACY = 26        # davon mit 044-Konsistenz-Quelle


def frozen_prereg_md5():
    """doc['md5'] des gefrorenen 055-Payloads (Payload-Content-md5, nicht
    die Byte-MD5 des Files — indent-Spaltung, 053-Praezedenz)."""
    with open(p48.PREREG_PATH, encoding="utf-8") as fh:
        return json.load(fh)["md5"]


def run_stage3(results_path=RESULTS_PATH, pts=None, cal=None):
    """Exakte b_P-Kurven fuer ALLE 37 Punkte; Dokument-Schema analog
    h3a.run_stage3 (ohne sampled/gamma/ladder), Keys 'set|arm|P'."""
    if pts is None and cal is None:
        pts, cal, ladder = p48.eval_grid()
    else:
        ladder = []
    all_pts = {**pts, **cal}
    assert len(all_pts) == N_EXPECTED_POINTS, len(all_pts)
    levels = list(h3a.STRESS_GRID_P1)

    exact_curves = {}
    for key in sorted(all_pts):
        pt = all_pts[key]
        nq = h3a.NQ_BY_ARM[pt["arm"]]
        exact_curves[key] = [h3a.exact_point_level(pt, nq, p1)
                             for p1 in levels]

    b_p, b_p_fit, ratio_ro, intercepts, fit_failed = {}, {}, {}, {}, {}
    for key, curve in exact_curves.items():
        pt = all_pts[key]
        k = h3a.pkey(key, all_pts)
        nq = h3a.NQ_BY_ARM[pt["arm"]]
        try:
            fit = h3a.fit_b_p([c["kappa"] for c in curve],
                              [c["ratio"] for c in curve])
        except ValueError as exc:
            fit_failed[k] = str(exc)
            continue  # Key FAELLT WEG: eval-`b_p.get` -> delta_cal None
        b_p[k] = fit["b_p"]
        b_p_fit[k] = fit
        ratio_ro[k] = h3a.ratio_ro_exact(pt, h3a.RO_STRESS, nq)
        intercepts[k] = fit["intercept"] + fit["b_p"]

    # b_P-Konsistenz der Legacy-Keys DIREKT gegen das committete 044-
    # Stage-3.  Ladder-P (cal|q5_d5|P mit P nicht in CAL_OLD_P) sind
    # FRISCH und fallen unter die "fresh"-Lesart (keine 044-Quelle).
    with open(h3a.RESULTS_PATH, encoding="utf-8") as fh:
        old_s3 = json.load(fh)["b_p"]
    bp_kons, n_ladder_fresh = {}, 0
    for k, bp in b_p.items():
        _set, arm, ps = k.split("|")
        P = int(ps)
        if (arm, P) in pts:
            key044 = k                       # 'verdict|arm|P'
        elif _set == "cal" and P in p48.CAL_OLD_P[arm]:
            key044 = k                       # 'cal|arm|P'
        else:
            n_ladder_fresh += 1              # Ladder-P: FRISCH
            continue
        if key044 not in old_s3:
            raise KeyError("044-Stage-3-Quelle fehlt fuer Legacy-Key %s"
                           % key044)
        diff = abs(bp - old_s3[key044])
        bp_kons[k] = {"stage3_grid": bp, "stage3_044": old_s3[key044],
                      "abs_diff": diff, "ok": diff < h3a.BP_KONSISTENZ_TOL}
    kons_bad = [k for k, v in bp_kons.items() if not v["ok"]]

    results = {
        "experiment": p48.EXPERIMENT, "hypothesis": p48.HYPOTHESIS,
        "leg": p48.LEG,
        "status": (STATUS_DEGENERAT if fit_failed else STATUS_OK),
        "prereg_md5": frozen_prereg_md5(),
        "grid": {"levels": levels,
                 "n_points_verdict": 13, "n_points_kalibrier": 24,
                 "n_cal_old": 13, "n_ladder_new": p48.N_NEW_CAL_Q5,
                 "n_cal_q5_total": p48.N_CAL_Q5_TARGET,
                 "n_points_verdict_expected": 13,
                 "domain_rule": "kappa >= KAPPA_CEILING = 0.81 per Zelle "
                                "(fit_b_p: >= 2 Domain-Nodes, sonst "
                                "registriert DEGENERAT)",
                 "mode": "exact_only"},
        "sets": {"verdict": {arm: sorted(p for (a, p) in pts
                                         if a == arm) for arm in p48.ARMS},
                 "kalibrier": {arm: sorted(p for (a, p) in cal
                                           if a == arm) for arm in p48.ARMS}},
        "ladder_ps": list(ladder),
        "exact": {h3a.pkey(kk, all_pts): [
            {"p1": c["p1"], "kappa": c["kappa"], "ratio": c["ratio"],
             "res_v1": c["res_v1"], "alpha": c["alpha"],
             "ops_struct": c["ops_struct"]} for c in v]
            for kk, v in exact_curves.items()},
        "b_p": b_p, "b_p_fit": b_p_fit,
        "ratio_ro": ratio_ro, "intercepts": intercepts,
        "b_p_fit_failed": fit_failed,
        "b_p_konsistenz": bp_kons,
        "b_p_konsistenz_zusammenfassung": {
            "n_legacy_checked": len(bp_kons),
            "n_expected_legacy": N_EXPECTED_LEGACY,
            "n_ladder_fresh": n_ladder_fresh,
            "n_abweichungen": len(kons_bad),
            "tol": h3a.BP_KONSISTENZ_TOL,
            "divergente_keys": kons_bad,
            "lesung": "DIREKT (kein Remapping) — die 055-verdict-Reihen "
                      "SIND die 044-verdict-Zeilen und die 055-cal-old-"
                      "Reihen die 044-cal-Zeilen.",
            "klasse": ("±1-ulp-Transpile-Zweig (Phase-11c-Praezedenz: "
                       ">= 3 gleichrangige Zerlegungen, ops_struct mit/ohne "
                       "x-Gate; KEINE Toleranz-Erhoehung, registriert und "
                       "b_P aus dem HEUTigen Zweig weitergerechnet)")
                      if kons_bad else "alle im BLAS-Rauschen"},
        "weggekuerzt": {"sampled": "notwendig_los",
                        "gamma_aer": "044-Diagnostik, kein Eval-Vertrag",
                        "echo_ladder": "RAW-abhaengig im Eval (r1 vs "
                                       "kappa_hat), kein Stage-3-Vertrag",
                        "form_validation": "braucht Sampled-Bein"},
        "prereg_reference": {"path": p48.PREREG_PATH,
                             "md5_doc": frozen_prereg_md5(),
                             "status": "REGISTERED_NOT_MEASURED (gefaehrt "
                                       "VOR jeder Messung)"},
        "w_b_doubleprime": {
            "wert": h3a.W_B_PRIME, "reused": True,
            "note": "w_B'' ist die gefrorene 044-Konstante (kommt IM Eval "
                    "aus pt_ram_q_stage2b_results.json via load_w_b()) — "
                    "das Stage-3-Artefakt aendert sie NICHT; die Gate-S-"
                    "Konsistenz (sampled q97.5) ist im exact-only-Modus "
                    "nicht berechenbar und 044-Diagnostik."},
    }
    if results_path:
        with open(results_path, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=1, sort_keys=True)
    return results


if __name__ == "__main__":
    res = run_stage3()
    bad = [k for k, v in res["b_p_konsistenz"].items() if not v["ok"]]
    print(f"b_P: {len(res['b_p'])}/{N_EXPECTED_POINTS} Reihen "
          f"| fit_failed {len(res['b_p_fit_failed'])} | status {res['status']}")
    print(f"Legacy-Konsistenz (044, DIREKT): "
          f"{res['b_p_konsistenz_zusammenfassung']['n_legacy_checked']} "
          f"Keys, {len(bad)} Abweichungen {bad if bad else ''} | "
          f"Ladder fresh "
          f"{res['b_p_konsistenz_zusammenfassung']['n_ladder_fresh']}")
    for arm in p48.ARMS:
        ks = sorted(k for k in res["b_p"] if k.split("|")[1] == arm)
        print(f"{arm}: b_P-Bereich "
              f"[{min(res['b_p'][k] for k in ks):+.4f}, "
              f"{max(res['b_p'][k] for k in ks):+.4f}]")