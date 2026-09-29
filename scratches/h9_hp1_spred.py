# -*- coding: utf-8 -*-
"""H9-Scratch 3 (0 QPU, read-only auf committeten Artefakten):
H-H9-1 Test (A) — s(P)-Fit an den CAL-Zeilen beider Sessions, Praediktion
der Verdict-P (HYPOTHESEN_UND_ANTITHESEN_H9_2026_09_29.md §C.1 / F-Tabelle
Prio 3).

**Modell-Registry EX ANTE** (fixiert VOR der ersten Auswertung; keine
Nachwahl nach Sichte der Praediktionsfehler):
  M0  s = 0                        (nur Kalibrier-Offset — Referenz)
  M1  s(P) = a + b*P               (linear in P, Session-gepoolt)
  M2  s(P) = a + b*P + c*P^2       (quadratisch, gepoolt)
  M3  s(P) = beta*c_p               (Rest-Fit der Kalibrierrichtung)
  M4  s(P) = Mittel der 2 naechsten CAL-P von P (lokal, nicht-parametrisch)

Daten/Konventionen: training NUR auf den CAL-Zeilen (13 je Session, beide
Beine), Zielgroesse res_v3 session-zentriert (resc = res − Mittel der CAL-
Zeilen derselben Session/Beins, kein Leck); Praediktion fuer ein Verdict-
(session,P) ist mu(session,arm) + s_fam(P), so dass e_full = res − mu −
s_fam = resc − s_fam.
**Metrik (ex ante, KORRIGIERT):** die verdict-tragende Verletzungsklasse des
geflorenen Designs ist EINSEITIG — unten_sharp == (res_v3 < −w_B''); die
Probe auf den committeten Artefakten bestaetigt die Flag-Gleichheit exakt
(5 q5-/Punkte S1+S2, 0 q3). Der ERSTE Lauf dieses Scratchs verwendete
zusaetzlich zweiseitig |e| > w_B'' (7/10 bzw. 5/16) — das ist NICHT die
committete Klasse (obere Ueberlaeufe wie q5 613 +0.0615/+0.0768 und q3
379/467 sind registrierte NICHT-verdict-tragende Zwischenklasse, kein
Falsifikator) — beide Metriken werden zum Vergleich ausgewiesen, die Tuer
haengt NUR an der one-sided-Klasse. Assert: unzentrierte one-sided-Klasse
== below_sharp-Flags.
**Tuer (ex ante registriert):** Familie m ist Traeger der P-Struktur-
Komponente ggue. M0 (nur Offset), wenn q5-one-sided-Verletzungssumme ueber
beide Sessions von 5 auf <= 1 faellt UND q3 M0 (0) nicht ueberschreitet.
**Multiplicity ehrlich:** 5 Familien x 2 Beine — Konsistenz-Befund, kein
konfirmatorischer Test; blinde Pruefung = Test (B) Session 3.
Honesty: verdict-residuen committet und dem Analysten bekannt -> Test (A)
kann das Verdict nicht neu entscheiden (kein Re-Decide, keine
Toleranz-Aenderung); 0 QPU, nicht verdict-tragend.
"""
import json

import numpy as np

H = "pt_ram_q_hardware3_eval.json"       # S1 = 11d
R = "pt_ram_q_hardware3_eval_rep.json"   # S2 = 047
OUT = "scratches/h9_hp1_spred.json"
REGISTRY = ("M0", "M1", "M2", "M3", "M4")


def spearman(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ra, rb = np.argsort(np.argsort(a)).astype(float), \
        np.argsort(np.argsort(b)).astype(float)
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def load_rows(path):
    rows = []
    d = json.load(open(path))
    for k, v in d["punkte"].items():
        leg, P = k.split("|")[1], int(k.split("|")[2])
        rows.append({"leg": leg, "P": P, "set": v["set"],
                     "res": float(v["res_v3"]), "c_p": float(v["c_p"]),
                     "kappa": float(v["kappa_hat"]),
                     "below_sharp": bool(v["below_sharp"])})
    return rows


def make_fits(train, evals):
    Ps = [r["P"] for r in train]
    ys = [r["resc"] for r in train]
    cps = [r["c_p"] for r in train]

    fits = {}
    fits["M0"] = {(r["session"], r["P"]): 0.0 for r in evals}
    for deg, key in ((1, "M1"), (2, "M2")):
        cols = [np.ones(len(Ps))] + [np.array([float(p) ** d for p in Ps])
                                     for d in range(1, deg + 1)]
        X = np.column_stack(cols)
        beta = np.linalg.lstsq(X, np.array(ys), rcond=None)[0]

        def ev(P, c_p, _b=beta, _d=deg):
            xs = np.array([P ** d for d in range(_d + 1)], float)
            return float(_b @ xs)

        fits[key] = {(r["session"], r["P"]): ev(r["P"], r["c_p"])
                     for r in evals}
    denom = float(sum(c * c for c in cps))
    b3 = float(sum(c * y for c, y in zip(cps, ys)) / denom) if denom > 0 else 0.0
    fits["M3"] = {(r["session"], r["P"]): b3 * r["c_p"] for r in evals}
    m4 = {}
    for r in evals:
        near = sorted(zip(Ps, ys), key=lambda t: abs(t[0] - r["P"]))[:2]
        m4[(r["session"], r["P"])] = float(sum(y for _, y in near) / 2.0)
    fits["M4"] = m4
    return fits


def main():
    d1, d2 = json.load(open(H)), json.load(open(R))
    w_b = float(d1["w_b_doubleprime"])
    assert d1["w_b_doubleprime"] == d2["w_b_doubleprime"]
    s1, s2 = load_rows(H), load_rows(R)
    out = {"w_b_doubleprime": w_b, "registry": list(REGISTRY),
           "leakage_note": "verdict-residuen committet und dem Analysten "
                           "bekannt -> Konsistenz-Check (Extrapolation aus "
                           "cal), blind = Session 3",
           "metric_note": "Tuer an one-sided (below_sharp-Klasse res < -w_B'')"
                          " geknuepft; zweiseitige Klasse (|res| > w_B'', "
                          "in_band_sharp=False) nur zur Transparenz"}
    # ---- Anker: committete below_sharp-Flags = one-sided-Klasse --------
    anchor = {}
    for name, rows in (("S1", s1), ("S2", s2)):
        for leg in ("q5_d5", "q3_d3"):
            vs = [r["P"] for r in rows
                  if r["leg"] == leg and r["set"] == "verdict"
                  and (r["below_sharp"] != (r["res"] < -w_b))]
            assert not vs, f"Anker verletzt {name}/{leg}: {vs}"
            anchor[f"{name}/{leg}"] = [r["P"] for r in rows
                                       if r["leg"] == leg
                                       and r["set"] == "verdict"
                                       and r["below_sharp"]]
    out["anchor_committed_below_sharp"] = anchor
    print(f"[Anker] below_sharp committet: "
          f"{ {k: v for k, v in anchor.items()} }")

    summary = {}
    for leg in ("q5_d5", "q3_d3"):
        train, evals = [], []
        for name, rows in (("S1", s1), ("S2", s2)):
            rl = [r for r in rows if r["leg"] == leg]
            cal = [r for r in rl if r["set"] == "cal"]
            mu = float(sum(r["res"] for r in cal) / len(cal))
            train.extend({**r, "session": name, "resc": r["res"] - mu}
                         for r in cal)
            evals.extend({**r, "session": name, "resc": r["res"] - mu,
                          "mu": mu}
                         for r in rl if r["set"] == "verdict")
        fits = make_fits(train, evals)
        per_model = {}
        for m in REGISTRY:
            preds = fits[m]
            errs = [(r["session"], r["P"],
                     r["resc"] - preds[(r["session"], r["P"])]) for r in evals]
            viol_low = [(s, p, e) for s, p, e in errs if e < -w_b]
            viol_high = [(s, p, e) for s, p, e in errs if e > w_b]
            viol_two = [(s, p) for s, p, e in errs if abs(e) > w_b]
            per_model[m] = {
                "band_verletzungen_tief": len(viol_low),
                "band_verletzungen_hoch": len(viol_high),
                "band_verletzungen_zweiseitig": len(viol_two),
                "max_abs_e": max(abs(e) for _, _, e in errs),
                "mae": float(sum(abs(e) for _, _, e in errs) / len(errs)),
                "spearman_pred_res": spearman(
                    [preds[(r["session"], r["P"])] for r in evals],
                    [r["resc"] for r in evals]),
                "viol_tief": [{"session": s, "P": p, "e": e}
                              for s, p, e in viol_low],
            }
        m0v = per_model["M0"]["band_verletzungen_tief"]
        best = min(REGISTRY,
                   key=lambda m: (per_model[m]["band_verletzungen_tief"],
                                  REGISTRY.index(m)))
        summary[leg] = {"n_eval": len(evals), "per_model": per_model,
                        "m0_violationen_tief": m0v, "best": best,
                        "best_violationen_tief":
                            per_model[best]["band_verletzungen_tief"]}
        print(f"[Test A / {leg}] n_eval={len(evals)} w_B''={w_b:.4f}")
        for m in REGISTRY:
            pm = per_model[m]
            print(f"  {m}: tief {pm['band_verletzungen_tief']}/{len(evals)} "
                  f"hoch {pm['band_verletzungen_hoch']} "
                  f"zwei {pm['band_verletzungen_zweiseitig']} "
                  f"mae {pm['mae']:.4f} max|e| {pm['max_abs_e']:.4f} "
                  f"rho {pm['spearman_pred_res']:+.3f} "
                  f"viol-P {[v['P'] for v in pm['viol_tief']]}")
        print(f"  beste Familie (tiefe Klasse): {best} "
              f"({per_model[best]['band_verletzungen_tief']} von "
              f"{len(evals)} vs M0 {m0v})")

    # ---- Tuer (one-sided) ------------------------------------------------
    q5, q3 = summary["q5_d5"], summary["q3_d3"]
    traeger = [m for m in REGISTRY
               if q5["per_model"][m]["band_verletzungen_tief"] <= 1
               and q3["per_model"][m]["band_verletzungen_tief"]
               <= q3["m0_violationen_tief"]]
    out["summary"] = summary
    out["traeger_familien"] = traeger
    out["hh9_1_test_a_support"] = bool(traeger)
    out["ergebnis_text"] = (
        f"q5 M0-tief {q5['m0_violationen_tief']} Verletzungen; Familien mit "
        f"q5-tief<=1 und q3-M0-Hebung: "
        f"{traeger if traeger else 'KEINE'} -> H-H9-1 Test A "
        f"{'UNTERSTUETZT (Konsistenz-Level, nicht blind)' if traeger else 'FAELLT als Unterstuetzung weg'}")
    print("[Tuer]", out["ergebnis_text"])
    # ---- Bonus (Z): Sign-Stabilitaet unter der Vorzeichen-Null ----------
    from math import comb
    p_11_13 = sum(comb(13, k) for k in range(11, 14)) / 2 ** 13
    p_9_9 = 0.5 ** 9
    out["z_sign_null"] = {"p_11_13_vorzeichen": p_11_13,
                          "p_9_9_stabil": p_9_9}
    print(f"[Z] P(>=11/13 Vorzeichen gleich) = {p_11_13:.6f}, "
          f"P(9/9 stabil bei |res_S1|>=0.01) = {p_9_9:.6f} "
          "(reine Vorzeichen-Null)")
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
    print("geschrieben:", OUT)


if __name__ == "__main__":
    main()