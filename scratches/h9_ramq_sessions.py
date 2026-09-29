# -*- coding: utf-8 -*-
"""H9-Scratch 1 (0 QPU, read-only auf committeten Artefakten):
Session-Struktur der RAM-Q-Residuen und Kandidaten-Steelman-Antithesen.

Fragen (alles aus committeten JSONs, KEINE neue Messung, KEIN Verdict):
  S1/S2 = 11d (pt_ram_q_hardware3_eval.json)
        / 047 (pt_ram_q_hardware3_eval_rep.json)

  (A) Antithese "Falsifikator = kappa-Tail": sind die below_sharp-Punkte
      die kappa-niedrigsten ihrer Bahn? (S1: ja-ish 0.8274/0.8309/0.8311,
      S2: NEIN — 467 hat kappa 0.8686 = 4. von 5 bei groesstem Residuum.)
      -> Spearman(res, kappa) pro Bahn/Session.
  (B) Session-Stabilitaet der Residuen an gleichem P: res_S1(P) vs
      res_S2(P) ueber alle 26 Holdout-Punkte — Spearman/Pearson,
      Vorzeichen-Übereinstimmung. Stabil => P-Struktur-Komponente.
  (C) res vs c_p (P-Struktur) gepoolt ueber Sessions (session-zentriert).
  (D) Hypergeometrische Wahrscheinlichkeit der Falsifikator-Schnittmenge
      {467,673} bei |S1|=3, |S2|=2 aus 13.
  (E) Multiple-Comparison-Arithmetik fuer den 046 Kingston -2.22sigma
      Event unter der Null (4 Sessions, 2sigma-Regel).
  (F) gamma_arm-Kalibrier-Kraft: OLS-SE von gamma auf den committeten
      cal-Zeilen vs Band w_B'' 0.02787.
  (G) Echo-Leiter-Gesetzesform: B^r vs f+(1-f)B^r pro Bein/Session
      (Floor-Frage: q5 r8 0.0982/0.0980 session-identisch?).
"""
import json
import math

import numpy as np

H = "pt_ram_q_hardware3_eval.json"
R = "pt_ram_q_hardware3_eval_rep.json"


def load_punkte(path):
    d = json.load(open(path))
    return d, d["punkte"]


def spearman(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def hypergeom_p(n_pop, size_b, overlap, at_least):
    """P(X >= at_least) mit X ~ Hypergeo(overlap| n_pop, size_b, overlap)."""
    from math import comb
    tot = 0
    for k in range(at_least, min(size_b, overlap) + 1):
        tot += comb(overlap, k) * comb(n_pop - overlap, size_b - k)
    return tot / comb(n_pop, size_b)


def main():
    d1, p1 = load_punkte(H)
    d2, p2 = load_punkte(R)
    w_b = d1["w_b_doubleprime"]
    out = {"w_b_doubleprime": w_b, "kappa_ceiling": d1["kappa_ceiling"]}

    # ---- (A) kappa-Tail-Antithese pro Session/q5-Verdict --------------
    print("== (A) Spearman(res_v3, kappa_hat) und kappa-Raenge ==")
    a_rows = {}
    for name, punkte in (("S1_11d", p1), ("S2_047", p2)):
        for leg in ("q5_d5", "q3_d3"):
            kp = [(P, v) for k, v in punkte.items()
                  for P in [k.split("|")[-1]] if leg in k and v["set"] == "verdict"]
            kp.sort()
            res = [v["res_v3"] for _, v in kp]
            kap = [v["kappa_hat"] for _, v in kp]
            rs = spearman(res, kap)
            order = sorted(kp, key=lambda t: t[1]["kappa_hat"])
            ranks = {P: i + 1 for i, (P, _) in enumerate(order)}
            below = [P for P, v in kp if v["below_sharp"]]
            a_rows[f"{name}/{leg}"] = {
                "spearman_res_kappa": rs,
                "kappa_ranks_below": {P: ranks[P] for P in below},
                "n": len(kp),
            }
            print(f"  {name}/{leg}: spearman(res,kappa)={rs:+.3f} "
                  f"n={len(kp)} below={below} "
                  f"kappa-Raenge={dict((P, ranks[P]) for P in below)}")
    out["a_kappa_tail"] = a_rows

    # ---- (B) Session-Stabilitaet res_S1(P) vs res_S2(P) ---------------
    print("== (B) Residuen-Konsistenz ueber Sessions (nur Holdout) ==")
    rows = {}
    for k, v in p1.items():
        if v["set"] != "verdict":
            continue
        leg, P = k.split("|")[1], int(k.split("|")[2])
        rows[(leg, P)] = [v["res_v3"], None]
    for k, v in p2.items():
        if v["set"] != "verdict":
            continue
        leg, P = k.split("|")[1], int(k.split("|")[2])
        rows[(leg, P)][1] = v["res_v3"]
    pairs = [(leg, P, r1, r2) for (leg, P), (r1, r2) in sorted(rows.items())
             if r2 is not None]
    r1s = [p[2] for p in pairs]
    r2s = [p[3] for p in pairs]
    sp = spearman(r1s, r2s)
    pe = float(np.corrcoef(r1s, r2s)[0, 1])
    same_sign = sum(1 for p in pairs if (p[2] > 0) == (p[3] > 0))
    print(f"  n={len(pairs)} spearman={sp:+.3f} pearson={pe:+.3f} "
          f"vorzeichen-gleich {same_sign}/{len(pairs)}")
    out["b_session_residuen"] = {
        "n": len(pairs), "spearman": sp, "pearson": pe,
        "vorzeichen_gleich": same_sign,
        "q5_rows": [{"leg": l, "P": P, "s1": a, "s2": b}
                    for l, P, a, b in pairs if l == "q5_d5"],
        "q3_rows": [{"leg": l, "P": P, "s1": a, "s2": b}
                    for l, P, a, b in pairs if l == "q3_d3"],
    }

    # ---- (C) res vs c_p gepoolt (session-zentriert) --------------------
    print("== (C) res vs c_p (gepoolt, session-zentriert) ==")
    cp_rows = []
    for name, punkte in (("S1", p1), ("S2", p2)):
        for k, v in punkte.items():
            if v["set"] != "verdict":
                continue
            leg, P = k.split("|")[1], int(k.split("|")[2])
            cp_rows.append({"s": name, "leg": leg, "P": P,
                            "c_p": v["c_p"], "res": v["res_v3"],
                            "kappa": v["kappa_hat"]})
    for leg in ("q5_d5", "q3_d3"):
        rl = [r for r in cp_rows if r["leg"] == leg]
        for s in ("S1", "S2"):
            ss = [r for r in rl if r["s"] == s]
            mu = float(np.mean([r["res"] for r in ss]))
            for r in ss:
                r["res_c"] = r["res"] - mu
        pool = [(r["res_c"], r["c_p"]) for r in rl]
        xs = [c for _, c in pool]
        ys = [y for y, _ in pool]
        rho = spearman(ys, xs)
        rpe = float(np.corrcoef(ys, xs)[0, 1]) if len(set(xs)) > 1 else float("nan")
        print(f"  {leg}: n={len(pool)} spearman(res_c, c_p)={rho:+.3f} "
              f"pearson={rpe:+.3f}")
        out.setdefault("c_res_cp", {})[leg] = {
            "n": len(pool), "spearman": rho, "pearson": rpe}

    # ---- (D) Hypergeometrie der Schnittmenge ---------------------------
    # |S1|=3 (Falsifikatoren 467/547/673), |S2|=2 (467/673), N=13.
    # (Erster Lauf hatte hier overlap=2 statt 3 -> 1/78; vor Commit
    # korrigiert, siehe Schwach-6 im H9-Dokument.)
    p_d = hypergeom_p(13, 2, 3, 2)
    print(f"== (D) P(Schnitt>=2 | |S1|=3, |S2|=2, N=13) = C(3,2)/C(13,2)"
          f" = {p_d:.6f}")
    out["d_hypergeom"] = p_d

    # ---- (E) Multiple-Comparison fuer -2.22sigma ------------------------
    from math import erf, sqrt
    p_2pt_22 = 1 - erf(2.22 / sqrt(2.0))  # zweiseitig
    joint4 = 1 - (1 - p_2pt_22) ** 4
    print(f"== (E) P(|z|>=2.22)={p_2pt_22:.6f}, "
          f"P(>=1 von 4 Sessions)={joint4:.6f}")
    out["e_multiple_comparison"] = {
        "p_event": p_2pt_22, "p_event_in_4_sessions": joint4}

    # ---- (F) gamma_arm-Kalibrier-Kraft (OLS-SE) ------------------------
    print("== (F) gamma_arm: OLS-Steigung +- SE an den cal-Zeilen ==")
    g_out = {}
    for leg, g in d1["gamma_arm"].items():
        cps = np.array([row["c_p"] for row in g["rows"]], float)
        dls = np.array([row["delta_cal"] for row in g["rows"]], float)
        n = len(cps)
        X = np.column_stack([np.ones(n), cps])
        beta, *_ = np.linalg.lstsq(X, dls, rcond=None)
        pred = X @ beta
        resid = dls - pred
        s2 = float(resid @ resid) / max(n - 2, 1)
        XtXi = np.linalg.inv(X.T @ X)
        se = math.sqrt(s2 * XtXi[1, 1])
        r2 = 1 - (resid @ resid) / float(((dls - dls.mean()) ** 2).sum()
                                         or 1e-30)
        g_out[leg] = {
            "gamma_committed": g["gamma"], "gamma_ols": float(beta[1]),
            "se_gamma": se, "resid_sd": float(resid.std(ddof=2)),
            "r2": float(r2), "n": n,
            "t_gamma_committed": g["gamma"] / se,
        }
        print(f"  {leg}: committed {g['gamma']:.6f} vs OLS {beta[0+1]:+.4f}"
              f" +- {se:.4f}  (n={n}, R2={r2:.3f}, "
              f"resid-SD {resid.std(ddof=2):.4f} vs w_B'' {w_b:.4f})")
    out["f_gamma_power"] = g_out

    # ---- (G) Echo-Leiter-Gesetzesform ----------------------------------
    print("== (G) Echo-Leiter: B^r vs f+(1-f)B^r ==")
    g_out = {}
    for name, src in (("S1", d1), ("S2", d2)):
        for leg, el in src["echo_ladder"].items():
            kr = el["kappa_r"]
            rs = np.array([1, 2, 4, 8], float)
            ks = np.array([kr["r1"], kr["r2"], kr["r4"], kr["r8"]], float)
            # (i) rein B^r: OLS log k vs r durch Ursprung? Freie Achse:
            slope_i = float(np.dot(rs, np.log(ks)) / np.dot(rs, rs))
            B_i = float(math.exp(slope_i))
            res_i = ks - np.exp(slope_i * rs)
            # (ii) f + (1-f)B^r, fit via Groesse f = k(r8)-Asymptote-Frei:
            best = None
            for f in np.linspace(0.0, 0.097, 98):
                y = ks - f
                if (y <= 0).any():
                    continue
                sl = float(np.dot(rs, np.log(y)) / np.dot(rs, rs))
                resid = ks - (f + np.exp(sl * rs))
                sse = float(resid @ resid)
                if best is None or sse < best[0]:
                    best = (sse, float(f), float(math.exp(sl)))
            sse_i = float(res_i @ res_i)
            g_out[f"{name}/{leg}"] = {
                "kappa_r": kr, "fit_kappa_block_committed": el["fit_kappa_block"],
                "B_ganz_ohne_floor_ols": B_i, "sse_B^r": sse_i,
                "floor_fit": {"f": best[1], "B": best[2], "sse": best[0]},
            }
            print(f"  {name}/{leg}: r8={kr['r8']:.6f}  "
                  f"B^r-SSE={sse_i:.4f}  floor-Fit f={best[1]:.4f} "
                  f"B={best[2]:.4f} SSE={best[0]:.5f}  "
                  f"(committed fit {el['fit_kappa_block']:.4f})")
    out["g_echo_law"] = g_out

    with open("scratches/h9_ramq_sessions_out.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
    print("geschrieben: scratches/h9_ramq_sessions_out.json")


if __name__ == "__main__":
    main()