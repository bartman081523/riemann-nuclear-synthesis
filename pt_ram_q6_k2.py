# -*- coding: utf-8 -*-
"""EXPERIMENT 051 (H-RAM-Q-6 Leg D2/D3) — frische-P-Vorzeichen-Programm
(Kingston-K2-Session, TOKEN2; Fez bleibt hinter 046).

Registeriert (0 QPU, VOR jeder Messung):
  * Run-4-Rotationsregel: die Run-3-Verdict-P werden Run-4-Kalibrier-P;
    Run-4-Verdict-P = h3.new_points_run3(Run-3-Verdict-Listen, ERWEITERTE
    Union aller 30 gemessenen P) — strikt kleinste Primzahl > letzter+30.
  * Frischer 26-Punkte-Grid (13 Verdict + 13 Kalibrier), d-Invarianz
    ueber die (d=q^2, q^3)-Familie, cP-Freeze via h3.coh_sens.
  * Zugtabelle (Train) aus den DREI COMMITTIerten Sessions des 26-Punkte-
    Grids (S1 = 11d, S2 = 047, K = Kingston-D1): Session eligible iff
    |res_v3| >= ELIGIBLE_ABS_MIN, Pool-Mitglied iff >= 2 eligible UND
    Mehrheit vorhanden (2-1-Splits zaehlen fuer die Mehrheit; 1-eligible
    und 2-eligible-Gleichstand fallen weg).
  * D2 ex-ante-Familie — SECHS arithmetische Merkmale (M0 = Arm-Mehrheit
    ist Nullmodell-Vergleich und GEHOERT NICHT zur Bonferroni-Familie):
      L3 = P mod 3 in {1,2}; L5 = Legendre (P/5) in {+1,-1};
      L3L5 = Paar-Klasse; chi4 = (P mod 4 == 1 -> +1 sonst -1);
      chi8 = (P mod 8 in {1,3} -> +1 sonst -1); P10 = P mod 10.
    alpha' = 0.05/6; gepoolt n<=13 -> Merkmal benoetigt >= 12/13 Treffer.
    Vorzeichen-Transfer gilt ex ante als REFUTED-erwartet (467-Flip und
    Geister-Probe der Phase 11d: Vorzeichen KEINE P-Funktion — jede
    Bestaetigung waere die Headline, die Prereg macht Bestaetigung schwer
    und Verwerfung leicht).
  * D3 In-Arm-Vorzeichen-Gesetz: 1-NN-in-P-Transfer (im Arm, Pool-Zeichen
    des naechsten Mitglieds; Gleichstand -> Punkt faellt weg), exakt
    einseitige Binomial gegen 0.5, alpha 0.05.
  * K2-Verdict-Combiner: DEGENERAT (geerbte Kontrollen t3-t6) ->
    VOID_KAPPA (geerbtes Verdict VOID_CALIBRATION) -> VOID_NOISE
    (eligible gesamt < 8) -> Komposit "D2:..|D3:..".
"""
import hashlib
import json
import os

import pt_ram_q_hardware as hw
import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_eval as h3e
import pt_ram_q6_kingston as k6

EXPERIMENT = "051-ram-q6-kingston-fresh-sign"
HYPOTHESIS = "H-RAM-Q-6"
LEG = "D2-D3-FRISCH-SIGN"
PREREG_STATUS = "REGISTERED_NOT_MEASURED"
PREREG_PATH = "pt_ram_q6_k2_prereg.json"
PREREG_MD5 = "ef7029764f0c192d69712674bd161822"  # Freeze vor Messung (2026-10-02)
BACKEND_NAME = k6.BACKEND_NAME
STAGE3_PATH = "pt_ram_q6_k2_stage3.json"
ISA_GATE_PATH = "pt_ram_q6_k2_isa_gate.json"
JOB_ID_PATH = "pt_ram_q6_k2_job_id.txt"
RAW_PATH = "pt_ram_q6_k2_raw.json"
INHERITED_EVAL_PATH = "pt_ram_q6_k2_inherited_eval.json"
EVAL_PATH = "pt_ram_q6_k2_eval.json"

# ---------------------------------------------------------------- Grid ---
S1_EVAL_PATH = "pt_ram_q_hardware3_eval.json"           # Session 1 (11d)
S2_EVAL_PATH = "pt_ram_q_hardware3_eval_rep.json"       # Session 2 (047)
K1_INH_PATH = "pt_ram_q6_kingston_inherited_eval.json"  # Session 3 (D1)
FROZEN_INPUTS = [
    S1_EVAL_PATH,
    S2_EVAL_PATH,
    K1_INH_PATH,
]

ARMS = ("q3_d3", "q5_d5")
NQ_BY_ARM = {"q3_d3": h3.NQ3, "q5_d5": h3.NQ5}
D_BY_ARM = {"q3_d3": h3.D3_MIN, "q5_d5": h3.D5_MIN}
Q_BY_ARM = {"q3_d3": 3, "q5_d5": 5}
D_MIN_BY_ARM = {"q3_d3": h3.D3_MIN, "q5_d5": h3.D5_MIN}
D_FAM_BY_ARM = {"q3_d3": (h3.D3_WIDE, 27), "q5_d5": (h3.D5_WIDE, 125)}

RUN3_VERDICT = {"q3_d3": list(h3.NEW_Q3_POINTS),
                "q5_d5": list(h3.NEW_Q5_POINTS)}
LADDER_ANCHORS = {"q3_d3": h3.LADDER_ANCHORS["q3"],  # UNVERAENDERT 181
                  "q5_d5": h3.LADDER_ANCHORS["q5"]}  # UNVERAENDERT 467

# ------------------------------------------------- D2/D3 Konstanten ------
ELIGIBLE_ABS_MIN = k6.ELIGIBLE_ABS_MIN           # 0.01 (§Z.29-Lesart)
D2_FAMILY = ("L3", "L5", "L3L5", "chi4", "chi8", "P10")
ALPHA_FAMILY2 = 0.05 / len(D2_FAMILY)            # 0.008333...
D3_ALPHA = 0.05
D3_N_ELIG_FLOOR = 8
K2_N_ELIG_FLOOR = 8
D2_MEMBER_N_MIN = 2

V_DEGENERAT = "K2_DEGENERAT"
V_VOID_KAPPA = "K2_VOID_KAPPA"
V_VOID_NOISE = "K2_VOID_NOISE"
V_D2_CONFIRMED = "K2_D2_CONFIRMED_ARITHMETIC_TRANSFER"
V_D2_PARTIAL = "K2_D2_PARTIAL_UEBER_ALPHA_NICHT_UEBER_M0"
V_D2_REFUTED = "K2_D2_REFUTED_KEIN_TRANSFER"
V_D3_CONFIRMED = "K2_D3_CONFIRMED_IN_ARM_SIGN_LAW"
V_D3_REFUTED = "K2_D3_REFUTED_SIGN_KEIN_FUNKTION_VON_P"
V_D3_VOID_FILTER = "K2_D3_VOID_NOISE_NACH_PREDICTION_FILTER"


def extended_union():
    """Alle 30 P, die vor K2 schon ein Messbein hatten (Run-1-Grids +
    Run-2-Kalibrier + Run-3-Verdict/Kalibrier)."""
    return (set(hw.Q3_POINTS) | set(hw.Q5_POINTS)
            | set(h3.CAL_Q3_POINTS) | set(h3.CAL_Q5_POINTS)
            | set(h3.NEW_Q3_POINTS) | set(h3.NEW_Q5_POINTS))


def run4_grid():
    """Run-4-Rotation: Kalibrier = Run-3-Verdict; Verdict = frisch nach
    der Phase-10b-Regel über der ERWEITERTEN Union.  Deren Listen sind
    deterministisch (committete h3-Regeln); die Assertions machen die
    Disjunktheit zur Invariante."""
    union4 = extended_union()
    # Run-3-Verdict-P sind VOR Run-4 schon je ein Messbein (drei Sessions,
    # ab K2 vier) — sie koennen NUR als Kalibrier wiederverwendet werden.
    ext = set(union4) | set(h3.NEW_Q3_POINTS) | set(h3.NEW_Q5_POINTS)
    assert len(ext) == len(union4), \
        "Run-3-Verdict-P muessen in der Union liegen (30-P-Invariante)"
    new3 = h3.new_points_run3(h3.NEW_Q3_POINTS, ext)
    new5 = h3.new_points_run3(h3.NEW_Q5_POINTS, ext)
    assert not (set(new3) & ext) and not (set(new5) & ext)
    # Kreuz-arm-P-Ueberschneidungen sind DESIGN (Run-3-Praezedenz 044:
    # {467, 613, 691} lagen in BEIDEN Run-3-Verdict-Listen) — die Punkte
    # sind per (arm, P) Schluessel getrennt, d-Register unterscheidet sie.
    return {"q3_d3": {"cal": list(h3.NEW_Q3_POINTS), "verdict": new3},
            "q5_d5": {"cal": list(h3.NEW_Q5_POINTS), "verdict": new5}}


def arm_records(arm, plist, with_d_invariance=True):
    """Punkt-Records wie im 044-Prereg (h3.arm_point, d = D_MIN_BY_ARM);
    d-Invarianz ueber die (d=q^2, q^3)-Familie (tol 1e-12, wie
    verify_anchors_run3)."""
    d = D_MIN_BY_ARM[arm]
    q = Q_BY_ARM[arm]
    fam = D_FAM_BY_ARM[arm]
    out = {}
    for P in plist:
        pt = h3.arm_point(P, d, q)
        if with_d_invariance:
            for dd in fam:
                other = h3.arm_point(P, dd, q)
                if abs(other["ratio_true"] - pt["ratio_true"]) > 1e-12:
                    raise ValueError(
                        "Run-4-d-Invarianz verletzt: P=%d d=%d/%d"
                        % (P, d, dd))
        out[(arm, P)] = pt
    return out


def fresh_points():
    """Frisches Grid: verdict = Run-4-NEU; cal = Run-3-Verdict.  Die
    Kalibrier-Records muessen den Run-3-Verdict-Records des committeten
    044-Prereg BIT-EXAKT gleichen (Rotations-Wiederverwendung, keine
    Recompute-Drift)."""
    grid = run4_grid()
    pts, cal = {}, {}
    src_prereg = h3.load_frozen_prereg()
    for arm in ARMS:
        pts.update(arm_records(arm, grid[arm]["verdict"]))
        cal_pts = arm_records(arm, grid[arm]["cal"])
        old = src_prereg["prediction_freeze"]["points"][arm]
        old_by_p = {r["P"]: r for r in old}
        for (a, P), rec in cal_pts.items():
            old_rec = old_by_p[P]
            if json.dumps(rec, sort_keys=True) != json.dumps(old_rec,
                                                             sort_keys=True):
                raise ValueError(
                    "Run-4-Kalibrier-Record != Run-3-Verdict-Record (P=%d, "
                    "%s) — Rotationsregel verletzt" % (P, a))
        cal.update(cal_pts)
    return pts, cal


def all_fresh():
    pts, cal = fresh_points()
    combined = dict(pts)
    combined.update(cal)
    return combined


def cP_freeze_fresh(pts, cal):
    """cP für ALLE 26 frischen Punkte (set|arm|P-Konvention), coh_sens
    im Verhältnis-Massstab; die Kalibrier-Einträge müssen mit den
    committeten 044-Verdict-cP bit-genau gleich sein (Rotationsregel)."""
    old_cP = h3.load_frozen_prereg()["prediction_freeze"]["cP_freeze"]
    out = {}
    for key, pt in pts.items():
        out["verdict|%s|%d" % key] = float(h3.coh_sens(pt))
    for key, pt in cal.items():
        k = "cal|%s|%d" % key
        out[k] = float(h3.coh_sens(pt))
        old_k = "verdict|%s|%d" % key
        if abs(out[k] - float(old_cP[old_k])) > 1e-12:
            raise ValueError("cP-Rotation: frischer cal-cP != committeter "
                             "verdict-cP fuer %s" % old_k)
    return out


# ---------------------------------------------------------- D2-Merkmale --
def legendre_mod5(P):
    """Legendre-Symbol (P/5) für P != 5 (Primzahlen > 5): +1/−1 —
    quadratisches Reziprozitaet-Muss: Zyklotomie-Feld, NICHT ein
    eingebautes Bauteil der Riemann-Struktur."""
    return 1 if P % 5 in (1, 4) else -1


def feats(P):
    """Die SECHS registrierten ex-ante-Merkmale (nur P-Funktionen)."""
    l5 = legendre_mod5(P)
    return {"L3": P % 3,
            "L5": l5,
            "L3L5": (P % 3, l5),
            "chi4": 1 if P % 4 == 1 else -1,
            "chi8": 1 if P % 8 in (1, 3) else -1,
            "P10": P % 10}


def majority(list_signs):
    """Mehrheit; None bei Gleichstand ODER leer."""
    s = [v for v in list_signs if v is not None]
    pos = sum(1 for v in s if v > 0)
    neg = len(s) - pos
    if pos > neg:
        return 1.0
    if neg > pos:
        return -1.0
    return None


# ----------------------------------------------------- Zugtabelle -------
def res_map_all(eval_doc):
    """|res_v3| über ALLE 26 Punkte des Grids (Verdict + Kalibrier),
    Key-Konvention set|arm|P — anders als k6.holdout_residuen (nur
    Verdict-P, 13)."""
    out = {}
    for pkey, row in eval_doc["punkte"].items():
        res = row.get("res_v3")
        if res is not None:
            out[pkey] = float(res)
    return out


def build_train_table(evals, abs_min=None):
    """ex-ante-Zugtabelle aus den COMMITTETEN Session-Auswertungen:
    Session-Mitglied (pool) iff >= 2 Sessions eligible UND Mehrheit.
    (1-eligible: zu wenig Votum; 2-eligible bei Gleichstand: kein
    Vorzeichen — 'majority_tie'.)"""
    abs_min = ELIGIBLE_ABS_MIN if abs_min is None else abs_min
    per_key = {}
    for path, doc in evals:
        for pkey, res in res_map_all(doc).items():
            per_key.setdefault(pkey, {})[path] = res
    pool, excluded = {}, {}
    for pkey, by_src in sorted(per_key.items()):
        elig = [v for v in by_src.values() if abs(v) >= abs_min]
        if len(elig) >= 2:
            sign = majority(elig)
        else:
            sign = None
        if sign is None:
            reason = ("majority_tie" if len(elig) >= 2
                      else "weniger als 2 eligible Sessions")
            excluded[pkey] = {"res": by_src, "reason": reason}
            continue
        pool[pkey] = {"res": by_src, "sign": sign,
                      "n_eligible": len(elig)}
    return {"eligible_abs_min": abs_min, "pool": pool, "excluded": excluded,
            "n_pool": len(pool), "n_excluded": len(excluded)}


def source_md5s(paths=FROZEN_INPUTS, base=None):
    """md5 der COMMITTETEN Zugquellen (Konsistenz-Gate im Eval)."""
    base = os.getcwd() if base is None else base
    out = []
    for p in paths:
        with open(os.path.join(base, p), "rb") as fh:
            out.append({"path": p, "md5": hashlib.md5(fh.read())
                        .hexdigest()})
    return out


def d2_predictions(train, fresh_pts, family=D2_FAMILY):
    """Ex-ante-Tabellen für ALLE Member: frische Sign, geschaut auf
    Klasse mit Pool-Empfehlung.  None = keine Regel (Klasse unbesetzt
    ODER Mehrheitstiefe)."""
    by_arm = {}
    for pkey, row in train["pool"].items():
        set_, arm, P = pkey.split("|")
        by_arm.setdefault(arm, {})[int(P)] = row["sign"]
    out = {}
    for arm in ARMS:
        fp = {P for (a, P) in fresh_pts if a == arm}
        out[arm] = {}
        for f in family:
            cls = {}
            for Po, sign in by_arm[arm].items():
                c = json.dumps(feats(Po)[f])
                cls.setdefault(c, []).append(sign)
            pred = {}
            for P in sorted(fp):
                v = majority(cls.get(json.dumps(feats(P)[f]), []))
                pred[str(P)] = v
            out[arm][f] = pred
    return {"prediction": out}


def d3_predictions(train, fresh_pts):
    """1-NN-in-P im Arm; Gleichstand -> None (Punkt faellt weg)."""
    by_arm = {}
    for pkey, row in train["pool"].items():
        set_, arm, P = pkey.split("|")
        by_arm.setdefault(arm, {})[int(P)] = row["sign"]
    out = {}
    for arm in ARMS:
        pool = by_arm[arm]
        fp = sorted(P for (a, P) in fresh_pts if a == arm)
        pred = {}
        for P in fp:
            dists = sorted((abs(P - Po), Po) for Po in pool)
            if not dists:
                pred[str(P)] = None
                continue
            if len(dists) > 1 and dists[0][0] == dists[1][0]:
                pred[str(P)] = None
                continue
            pred[str(P)] = pool[dists[0][1]]
        out[arm] = pred
    return {"prediction": out}


# ------------------------------------------------- Scoring (rein) -------
def binom_sf_one_sided(k, n):
    """Exakte einseitige p-Wert: P(X >= k) bei p = 0.5 (k, n int,
    k <= n).  Identisch zu k6.binom_sf_one_sided (keine Kopie — delegiert)."""
    return k6.binom_sf_one_sided(k, n)


def score_d2(res_fresh, preds, m0_signs, abs_min=ELIGIBLE_ABS_MIN,
             alpha_family=ALPHA_FAMILY2):
    """D2-Score über die SECHS-Merkmale-Familie (gepoolt über beide Arme,
    weil die Merkmale arm-agnostisch sind — ABER: die Vorzeichen-Regel
    ist im Arm gelernt, also ist die Tabelle per Arm gefroren und nur der
    Test gepoolt).  Jeder Punkt trägt einmal pro Member; n_variiert bei
    None-Meldungen.  M0-Einsatz: derselbe Satz eligible-Punkte DES
    Members, dieselbe gefrorene Arm-Meldung — KEINE Re-Fit."""
    per_member = {}
    for f in D2_FAMILY:
        rows = []
        hits = m0_hits = 0
        n = m0_n = 0
        m0_comparable = True
        for arm in ARMS:
            tbl = preds["prediction"][arm][f]
            for P_s, sign in tbl.items():
                res = res_fresh.get("verdict|%s|%s" % (arm, P_s))
                if res is None or abs(res) < abs_min:
                    continue
                n += 1
                r_sign = 1.0 if res > 0 else -1.0
                if sign is not None and r_sign == sign:
                    hits += 1
                rows.append({"arm": arm, "P": int(P_s), "res": res,
                             "pred": sign, "hit": (sign is not None
                                                   and r_sign == sign)})
                m0_sign = m0_signs[arm]
                m0_n += 1
                if m0_sign is not None and m0_sign * r_sign > 0:
                    m0_hits += 1
        p_f = binom_sf_one_sided(hits, n) if n else 1.0
        p_m0 = binom_sf_one_sided(m0_hits, m0_n) if m0_n else 1.0
        m0_comparable = all(v is not None for v in m0_signs.values())
        beats = (n >= D2_MEMBER_N_MIN and m0_comparable
                 and p_f <= alpha_family and p_f < p_m0 and hits > m0_hits)
        per_member[f] = {"n": n, "hits": hits, "p": p_f,
                         "m0": {"n": m0_n, "hits": m0_hits, "p": p_m0},
                         "m0_comparable": m0_comparable,
                         "ueber_alpha": bool(n >= D2_MEMBER_N_MIN
                                             and p_f <= alpha_family),
                         "beats_m0": beats,
                         "rows": rows}
    passing = sorted(f for f, r in per_member.items() if r["beats_m0"])
    over_only = sorted(f for f, r in per_member.items()
                       if r["ueber_alpha"] and not r["beats_m0"])
    return {"members": per_member, "passing": passing,
            "ueber_alpha_only": over_only,
            "alpha_family": alpha_family,
            "verdict": (V_D2_CONFIRMED if passing
                        else (V_D2_PARTIAL if over_only else V_D2_REFUTED))}


def score_d3(res_fresh, preds, abs_min=ELIGIBLE_ABS_MIN,
             alpha=D3_ALPHA):
    """D3-1-NN-Transfer, gepoolt über beide Arme, exakt einseitiges
    binomial.  Punkte ohne Meldung (Gleichstand) fallen weg."""
    rows, hits, n = [], 0, 0
    for arm in ARMS:
        for P_s, sign in preds["prediction"][arm].items():
            res = res_fresh.get("verdict|%s|%s" % (arm, P_s))
            if res is None or abs(res) < abs_min:
                continue
            if sign is None:
                # registrierte Regel: ohne Meldung (Gleichstand) faellt
                # der Punkt WEG — er zaehlt weder in n noch in hits.
                rows.append({"arm": arm, "P": int(P_s), "res": res,
                             "pred": None, "hit": False,
                             "dropped_ohne_meldung": True})
                continue
            n += 1
            r_sign = 1.0 if res > 0 else -1.0
            hit = r_sign == sign
            hits += 1 if hit else 0
            rows.append({"arm": arm, "P": int(P_s), "res": res,
                         "pred": sign, "hit": hit})
    per_arm = {}
    for arm in ARMS:
        sub = [r for r in rows if r["arm"] == arm]
        per_arm[arm] = {"n": len(sub), "hits": sum(1 for r in sub
                                                   if r["hit"]),
                        "nicht_verdict_tragend": True}
    n_dropped = sum(1 for r in rows if r.get("dropped_ohne_meldung"))
    return {"n": n, "n_dropped_ohne_meldung": n_dropped, "hits": hits,
            "p": (binom_sf_one_sided(hits, n) if n else 1.0),
            "rows": rows, "per_arm_nicht_verdict_tragend": per_arm,
            "alpha": alpha,
            "verdict": (V_D3_CONFIRMED
                        if (n and n >= D3_N_ELIG_FLOOR
                            and binom_sf_one_sided(hits, n) <= alpha)
                        else (V_D3_VOID_FILTER
                              if n < D3_N_ELIG_FLOOR else V_D3_REFUTED))}


def decide_k2(degenerat_failed, inherited_verdict, n_elig_total,
              d2_res, d3_res, void_kappa=h3e.V_VOID):
    """Gefrorene K2-Kombinations-Reihenfolge:
    DEGENERAT -> VOID_KAPPA -> VOID_NOISE -> Komposit "D2:|D3:"."""
    if degenerat_failed:
        return V_DEGENERAT
    if inherited_verdict == void_kappa:
        return V_VOID_KAPPA
    if n_elig_total < K2_N_ELIG_FLOOR:
        return V_VOID_NOISE
    return "D2:%s|D3:%s" % (d2_res["verdict"], d3_res["verdict"])


# ------------------------------------------------------- Prereg-Freeze --
def build_k2_prereg():
    """Komplettes 051-Prereg (VOR Messung, 0 QPU): frisches Grid +
    Zugtabelle + ex-ante-Meldungen + geerbtes Gesetz/Kontrolle."""
    pts, cal = fresh_points()
    cP = cP_freeze_fresh(pts, cal)
    train = build_train_table(
        [(p, _load_json(p)) for p in FROZEN_INPUTS])
    src_md5s = source_md5s()
    d2_pred = d2_predictions(train, pts)
    d3_pred = d3_predictions(train, pts)
    old = h3.load_frozen_prereg()
    grid = run4_grid()

    def pt_records(dct):
        out = {}
        for arm in ARMS:
            recs = [dct[(arm, P)] for (a, P) in sorted(dct) if a == arm]
            out[arm] = recs
        return out

    assert len(pts) == 13 and len(cal) == 13, (len(pts), len(cal))
    assert len(set(P for (a, P) in pts) & extended_union()) == 0

    doc = {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "leg": LEG,
        "status": PREREG_STATUS,
        "substrat": {
            "backend": BACKEND_NAME,
            "token": "TOKEN2 (Kingston, via pt_v5_kingston.load_token; "
                     "TOKEN1 wird NIE gelesen)",
            "fez_disziplin": "Fez-046-Job dauassrojkfs738rrcsg QUEUED — "
                             "EIN-Fez-Job-Regel; K2 laeuft auf dem "
                             "KINGSTON-Bein (Session K2, 4. Session der "
                             "Serie)",
            "session_kontext": "S1 = 11d (Fez), S2 = 047 (Fez), K = "
                               "Kingston-D1 (051-Vorlaeufer), K2 = "
                               "dieser Job",
        },
        "frozen_inputs": {
            "sources": src_md5s,
            "law": "044-v3b-Gesetz md5 "
                   "baaca1f6772e07b0847fe436da7e16da UNVERAENDERT "
                   "geerbt (kein Gesetzes-Fork)",
        },
        "grid": {
            "rotationsregel": "Run-3-Verdict-P -> Run-4-Kalibrier-P; "
                              "Run-4-Verdict-P = kleinste Primzahl "
                              "> letzte+30 (strikte Lesart: Primzahl-"
                              "Argument wird UBERSPRUNGEN), Union = "
                              "alle bis dato gemessenen P",
            "extended_union_size": len(extended_union()),
            "extended_union_sorted": sorted(extended_union()),
            "run4": {arm: {k: rec
                           for k, rec in grid[arm].items()} for arm in
                     ARMS},
        },
        "prediction_freeze": {
            "points": pt_records(pts),
            "cP_freeze": cP,
            "registered_expectation_nicht_verdict_tragend": (
                "Ex-ante-Erwartung beider Legs REFUTED (467-Flip, "
                "Geister-Probe 'Vorzeichen KEINE P-Funktion', "
                "'neue Arithmetik' Grade E/F) — Bestaetigung muß "
                "SCHWERER als Verwerfung sein"),
        },
        "kalibrier_bein": {"points": pt_records(cal),
                           "note": "Run-3-Verdict-P als Run-4-"
                                   "Kalibrier (Rotation); Records "
                                   "bit-exakt vom committeten 044-"
                                   "Prereg vererbbar"},
        "zugtabelle": {
            "train": train,
            "m0_predictions": {
                "q3_d3": majority([row["sign"] for pk, row in
                                   train["pool"].items()
                                   if pkey_arm(pk) == "q3_d3"]),
                "q5_d5": majority([row["sign"] for pk, row in
                                   train["pool"].items()
                                   if pkey_arm(pk) == "q5_d5"]),
                "rule": "Arm-Mehrheit der Pool-Zeichen, ex ante "
                        "gefloren; NULL-MODELL (nicht in der "
                        "Bonferroni-Familie)",
            },
        },
        "d2_leg": {
            "family": list(D2_FAMILY),
            "family_size": len(D2_FAMILY),
            "m0_in_family": False,
            "alpha_family": ALPHA_FAMILY2,
            "pooled_threshold_note": "gepoolt n=13: Member benotigt "
                                     ">= 12/13 Treffer (12/13 p=%.6g "
                                     "<= alpha'; 11/13 p=%.6g > alpha'; "
                                     "q5-allein 5/5 p=%.6g > alpha' — "
                                     "registrierte Konsequenz)"
                                     % (k6.binom_sf_one_sided(12, 13),
                                        k6.binom_sf_one_sided(11, 13),
                                        k6.binom_sf_one_sided(5, 5)),
            "m0_vergleich": "dieselbe eligible-Punktmenge des Members, "
                            "dieselbe GEFRORENE Arm-Meldung — M0 wird "
                            "NIE auf der Menge neu gefittet; M0-"
                            "Gleichstand -> Member nicht CONFIRMED-"
                            "faehig (nicht vergleichbarer Nullmodell)",
            "predictions": d2_pred,
            "entscheidungs_notiz": "Punkte ohne Member-Meldung "
                                   "(unbesetzte Klasse ODER Tiefe) "
                                   "bleiben in der Menge und zaehlen "
                                   "als Nicht-Treffer (konservativ)",
            "decision": "CONFIRMED iff mindestens EIN Member p <= alpha' "
                        "UND p < p_M0 UND hits > hits_M0 (auf seiner "
                        "Menge); PARTIAL iff alpha' aber nicht M0; "
                        "sonst REFUTED",
            "registered_expectation": "REFUTED",
        },
        "d3_leg": {
            "nearest_rule": "1-NN in P, im Arm, Pool-Zeichen des "
                            "naechsten Mitglieds; Abstands-Gleichstand "
                            "-> Punkt faellt weg (zaehlt weder in n "
                            "noch in hits)",
            "alpha": D3_ALPHA,
            "n_elig_floor": D3_N_ELIG_FLOOR,
            "predictions": d3_pred,
            "decision": "CONFIRMED iff n >= n_elig_floor UND "
                        "p_one_sided <= alpha; sonst REFUTED",
            "registered_expectation": "REFUTED",
        },
        "diagnostik_nicht_verdict_tragend": {
            "zeichen_stabilitaet_kalibrier": "K2 re-misst die Run-3-"
                                             "Verdict-P (4. Session) — "
                                             "Zeichen-Abgleich gegen "
                                             "S1/S2/K an diesen 13 "
                                             "Punkten",
            "echo_leiter": "wie 044: kappa_block-Fit an den Ankern "
                           "181/467, NICHT verdict-tragend",
        },
        "hardware_parameters": {
            "run_config": old["hardware_parameters"]["run_config"],
            "circuit_budget": 116,
            "shots_per_circuit": h3.SHOTS,
            "k_repeats": h3.K_REPEATS,
            "isa_ceilings": dict(k6.ISA_CEILINGS),
        },
        "punktemenge_vertraege": {
            "n_verdict": len(pts), "n_kalibrier": len(cal),
            "verdict_p_disjunkt_extended_union": len(
                set(P for (a, P) in pts) & extended_union()) == 0,
            "kalibrier_p_equals_run3_verdict": True,
        },
        "k2_verdict_map": {
            "K2_DEGENERAT": "geerbte Kontrollen (t3/t4/t5/t6) verletzt "
                            "-> keine Auswertung",
            "K2_VOID_KAPPA": "geerbtes 044-Verdict VOID_CALIBRATION -> "
                             "keine Auswertung",
            "K2_VOID_NOISE": "eligible gesamt < %d von 13 -> keine "
                             "Auswertung" % K2_N_ELIG_FLOOR,
            "sonst": "Komposit D2:<...>|D3:<...>",
        },
        "ladder_anchors": dict(LADDER_ANCHORS),
        "ladder_note": "Echo-Leiter + Negativ-Kontrollen bleiben an den "
                       "UNVERAENDERTEN Session-Ankern 181/467 (Vertrag); "
                       "die Anker liegen im frischen Grid als Kalibrier",
        "inherited_from_044": {
            "controls": old["controls"],
            "hardware_run_config": old["hardware_parameters"]["run_config"],
            "verdict_map": old["verdict_map"],
            "circuit_budget": old["hardware_parameters"].get("circuit_budget",
                                                             116),
        },
    }
    return doc


def pkey_arm(pkey):
    """set|arm|P -> arm."""
    return pkey.split("|")[1]


def freeze_prereg(path=PREREG_PATH):
    doc = build_k2_prereg()
    _, md5 = k6.freeze_prereg(doc, path)
    return md5


def load_frozen_prereg(path=PREREG_PATH):
    doc = _load_json(path)
    got = k6.self_md5(path)
    if PREREG_MD5 and got != PREREG_MD5:
        raise AssertionError("K2-Prereg-CONSTANTE %s != Datei %s"
                             % (PREREG_MD5, got))
    if doc.get("status") != PREREG_STATUS:
        raise AssertionError("K2-Prereg-Status verletzt: %r"
                             % doc.get("status"))
    return doc


def _load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


if __name__ == "__main__":
    md5 = freeze_prereg()
    print("K2-Prereg gefroren:", PREREG_PATH, "md5:", md5)