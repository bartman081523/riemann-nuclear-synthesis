# -*- coding: utf-8 -*-
"""EXPERIMENT 051 (H-RAM-Q-6 Leg D2/D3) — Stage-3-Aer EXACT-ONLY fuer das
FRISCHE Run-4-Grid (0 QPU).

Was gegenueber dem Stamm-Modell (h3a.run_stage3, committet 044) WEGFAELLT —
und warum das kein Vertrag-Verlust ist:
  * Sampled-Bein (n_ens x reps), gamma_aer, Echo-Leiter, w_B''-Gate-S:
    das Eval konsumiert ausschliesslich stage3["b_p"],
    stage3["prereg_md5"], stage3["status"] (h3e-Zeilen 154/265/453) —
    kein Gate liest cells/sampled/form_validation.  Diese Beine sind
    044-Diagnostik (Aer-Rauschen), kein Auswertungs-Vertrag.  Die
    Echo-Leiter im K2-Eval ist RAW-abhaengig (r1-Konsistenz gegen
    kappa_hat des Session-Ankers; anker-tolerant seit Commit 10c88c2) und
    braucht daher KEIN Stage-3-Artefakt.
Registriert hier (Vertrag):
  * b_P fuer ALLE 26 frischen Punkte via fit_b_p ueber die EXAKTEN
    Level-Kurven (STRESS_GRID_P1, density_matrix, RO_STRESS) —
    Key-Konvention 'set|arm|P' via h3a.pkey auf GESTEMPELTEN Records
    (k2.eval_grid).
  * Kalibrier-b_P-Konsistenz (tol h3a.BP_KONSISTENZ_TOL) gegen committetes
    044-Stage-3-Ergebnis (h3a.RESULTS_PATH, Keys 'verdict|arm|P'):
    die frischen Kalibrier-P SIND die Run-3-Verdict-P, deren b_P dort
    auf DEMSELBEN Codepfad (exact_point_level + fit_b_p) gerechnet
    wurde — jede Abweichung > 1e-3 ist Provenienz-Bruch.  Die
    Phase-11a-Diagnostik (h3.DIAG_RESULTS) deckt die Run-3-Verdict-P
    NICHT ab (ihre Sets "new"/"old" sind Run-2-Kalibrier/Run-1) und
    entfaellt daher als Quelle.
  * DEGENERAT-Pflicht: fit_b_p braucht >= 2 Domain-Nodes (kappa >=
    0.81); jeder Fit-Fehler wird REGISTRIERT (b_p_fit_failed), NICHT
    absorbiert — fehlende b_p-Keys lassen das Eval fuer den Punkt
    delta_cal/res_v3 = None rechnen (registriert, kein Gate-Verstoss).
  * Prereg-Binding: prereg_md5 = k2.PREREG_MD5 (der gefrorene D2/D3-
    Freeze, VOR jeder Messung).
Token-DISZIPLIN: 0 QPU, kein Fez/Kingston-Kontakt, kein Token.
"""
import json

import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_aer as h3a
import pt_ram_q6_k2 as k2

RESULTS_PATH = k2.STAGE3_PATH
STATUS_OK = "STAGE3_AER_EXACT_ONLY_COMPLETED"
STATUS_DEGENERAT = "STAGE3_AER_EXACT_ONLY_DEGENERAT"


def run_stage3(results_path=RESULTS_PATH, pts=None, cal=None):
    """Exakte b_P-Kurven fuer ALLE 26 frischen Punkte; Dokument-Schema
    analog h3a.run_stage3 (ohne sampled/gamma/ladder), Keys 'set|arm|P'."""
    if pts is None and cal is None:
        pts, cal = k2.eval_grid()
    all_pts = {**pts, **cal}
    assert len(all_pts) == 26, len(all_pts)
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

    # Kalibrier-b_P-Konsistenz (frisch-cal = Run-3-Verdict) gegen das
    # committete 044-Stage-3 (Keys 'verdict|arm|P', gleicher Codepfad).
    # Die Phase-11a-Diag deckt die Run-3-Verdict-P NICHT ab (siehe Kopf).
    with open(h3a.RESULTS_PATH, encoding="utf-8") as fh:
        old_s3 = json.load(fh)["b_p"]
    bp_kons = {}
    for k, bp in b_p.items():
        if not k.startswith("cal|"):
            continue
        key044 = "verdict|" + k[len("cal|"):]
        if key044 not in old_s3:
            raise KeyError("044-Stage-3-Quelle fehlt fuer frisch-Kalibrier "
                           "%s (%r)" % (k, key044))
        diff = abs(bp - old_s3[key044])
        bp_kons[k] = {"stage3_grid": bp, "stage3_044_verdict": old_s3[key044],
                      "abs_diff": diff, "ok": diff < h3a.BP_KONSISTENZ_TOL}
    kons_bad = [k for k, v in bp_kons.items() if not v["ok"]]

    results = {
        "experiment": k2.EXPERIMENT, "hypothesis": k2.HYPOTHESIS,
        "leg": k2.LEG,
        "status": (STATUS_DEGENERAT if fit_failed else STATUS_OK),
        "prereg_md5": k2.PREREG_MD5,
        "grid": {"levels": levels,
                 "n_points_verdict": 13, "n_points_kalibrier": 13,
                 "domain_rule": "kappa >= KAPPA_CEILING = 0.81 per Zelle "
                                "(fit_b_p: >= 2 Domain-Nodes, sonst "
                                "registriert DEGENERAT)",
                 "mode": "exact_only"},
        "sets": {"verdict": {arm: sorted(p for (a, p) in pts
                                         if a == arm) for arm in k2.ARMS},
                 "kalibrier": {arm: sorted(p for (a, p) in cal
                                           if a == arm) for arm in k2.ARMS}},
        "exact": {h3a.pkey(kk, all_pts): [
            {"p1": c["p1"], "kappa": c["kappa"], "ratio": c["ratio"],
             "res_v1": c["res_v1"], "alpha": c["alpha"],
             "ops_struct": c["ops_struct"]} for c in v]
            for kk, v in exact_curves.items()},
        "b_p": b_p, "b_p_fit": b_p_fit,
        "ratio_ro": ratio_ro, "intercepts": intercepts,
        "b_p_fit_failed": fit_failed,
        "b_p_kalibrier_konsistenz": bp_kons,
        "b_p_konsistenz_zusammenfassung": {
            "n_kalibrier": len(bp_kons),
            "n_abweichungen": len(kons_bad),
            "tol": h3a.BP_KONSISTENZ_TOL,
            "divergente_keys": kons_bad,
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
        "prereg_reference": {"path": k2.PREREG_PATH,
                             "md5": k2.PREREG_MD5,
                             "status": k2.PREREG_STATUS},
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
    bad = [k for k, v in res["b_p_kalibrier_konsistenz"].items()
           if not v["ok"]]
    print(f"b_P: {len(res['b_p'])}/{26 - len(res['b_p_fit_failed'])} "
          f"Punkte | fit_failed {len(res['b_p_fit_failed'])} | "
          f"status {res['status']}")
    print(f"Kalibrier-b_P-Konsistenz (044-Drittquelle): "
          f"{len(res['b_p_kalibrier_konsistenz'])} Punkte, {len(bad)} "
          f"Abweichungen {bad if bad else ''}")
    for arm in k2.ARMS:
        ks = sorted(k for k in res["b_p"] if k.split("|")[1] == arm)
        print(f"{arm}: b_P-Bereich "
              f"[{min(res['b_p'][k] for k in ks):+.4f}, "
              f"{max(res['b_p'][k] for k in ks):+.4f}]")