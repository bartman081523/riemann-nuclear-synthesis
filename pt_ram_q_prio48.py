# -*- coding: utf-8 -*-
"""pt_ram_q_prio48.py — EXPERIMENT 055 (H-H9 FPrio 4+8): Prereg-Modul.

EIN kombiniertes Fez-TOKEN1-Job-Hinter-046 (Backlog:
QUQUINT-F4 daua5hahcrkc73dv9eh0 -> 046 dauassrojkfs738rrcsg -> 055),
das ZWEI Deck-Falsifikatoren in einem Messverbund entlaedt:

  F-Prio 4 (C.1/D.7): Session-P-Bindung vs Geometrie-Bindung auf den
      13 verdict-Reihen. Die Qubit-Zuordnung wird pro Circuit zyklisch
      FORCED verschoben (per-Circuit initial_layout, transpiler seed 7
      UNVERAENDERT); die P-Vektoren bleiben WAHR. Kriterien:
        C1 ANKER-PARITAET: rho(res'_arm, res_S1_arm) >= Anchor S1->S2
           je Arm (q5: 0.49999999999999994-Klasse, q3: 0.8095238-Klasse;
           gepoolt 0.8956044 bit-gepinnt).
        C2: q5-Kern S2-below {467,673} BOTH (2/2) + Zweitstufe
           S1-Klasse {467,547,673} >= 2/3; q3 klassenleer n/a.
        C3 GEOMETRIE-COUNTER: exact-perm Spearman(Delta-res, Delta-c)
           mit Delta-c = c_prime - c_S1 aus dem VOR Messung committeten
           ISA-Report (c' ist ex ante-Nachricht, c_S1 committet).
      n=5-LEKTION registriert: eine TRUE-Session-Replication erreicht
      beim exakten Permutations-Null nur rho 0.5 (80-Perzentil-Klasse;
      120 Permutationen) — ein q95-Massstab (0.8) wuerde sogar die
      reine S2-Replication FAILEN lassen. Registrierter Massstab ist
      deshalb die Paritaet zum S1->S2-Anker; q95 bleibt sekundaerer
      Deskriptiv-Benchmark.

  F-Prio 8 (D.5): n_cal(q5) 5 -> 16 via 11 neue Kalibrier-P unter der
      WOERTLICHEN Phase-11b-P-Regel (iterative Generationen,
      new_points_run3-Iteration mit wachsender Union). Refit gamma'_q5
      (no-intercept LSQ <c,Delta>/<c,c>, law-konsistent) + DECOMPOSITION
      (OLS-mit-Achsenabschnitt, resid_sd ddof=2) an n=16. D.5-SE-Pro-
      venance bit-geloest: SE_no_int * c̄ (S1,q5,cal) =
      0.0025335578768332333 * c̄ = 0.01197607825720734 ~ Deck
      "SE(gamma)*c_p ~ 0.011" — die D.5-Zahl ist die Durch-Null-LSQ-SE,
      NICHT die (F)-OLS-SE 0.1254448714861779. LITERAL Deck-F-Zeile-8-
      Falsifikatorlinie: resid_sd(q5, OLS-mit-Achsenabschnitt, ddof=2,
      n=16) < 0.01 — sonst BLEIBT SA-H9-5 (Kalibrier-Streuung =
      Band-Groesse).

DISZIPLIN: Das Freeze (REGISTERED_NOT_MEASURED) entsteht VOR jeder
Messung. Das QPU-Modul (pt_ram_q_prio48_qpu.py) traegt NUR counts;
kein kappa, kein ratio, kein gamma-Fit, kein Band. Die gefrorene
Auswertung (pt_ram_q_prio48_eval.py) laeuft erst NACH dem Raw-Commit.

Alle Kandidaten werden aus committeten Grids abgeleitet (Anti-
Sharpshooter: die Ableitung benutzt nur Messungs-MEMBERSHIP, keine
Messwerte). Design-Skript: scratches/h9_fprio48_design.py.
"""
import hashlib
import itertools
import json

import numpy as np

import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_aer as h3a

# ------------------------------------------------------------------ Pfade --
PREREG_PATH = "pt_ram_q_prio48_prereg.json"
ISA_REPORT_PATH = "pt_ram_q_prio48_isa_report.json"
ISA_GATE_PATH = "pt_ram_q_prio48_isa_gate.json"
RAW_PATH = "pt_ram_q_prio48_raw.json"
EVAL_PATH = "pt_ram_q_prio48_eval.json"
JOB_ID_PATH = "pt_ram_q_prio48_fez_job_id.txt"

H3_PREREG = "pt_ram_q_hardware3_prereg.json"          # Freeze 11b (baaca1f6)
H3_EVAL_S1 = "pt_ram_q_hardware3_eval.json"           # Session 1 (11d, 044)
H3_EVAL_S2 = "pt_ram_q_hardware3_eval_rep.json"       # Session 2 (047, fez)
K2_PREREG = "pt_ram_q6_k2_prereg.json"                # 051 Freeze (Kingston)
K2_EVAL = "pt_ram_q6_k2_eval.json"                    # 051 Auswertung
SESSIONS_OUT = "scratches/h9_ramq_sessions_out.json"

# ----------------------------------------------------------- Konstanten ---
EXPERIMENT = "EXPERIMENT 055"
HYPOTHESIS = "H-H9 FPrio-4 (C.1/D.7 Session-P-Bindung) + FPrio-8 (D.5 n_cal>=16)"
LEG = "FP48-COMBINED"

W_B_DP = 0.02787029633307472      # w_B'' = w_B' (committet)
W_A = 0.05                        # r1-Mitwanderung (Echo-Leiter)
KAPPA_CEILING = 0.81
SHOTS = int(h3.SHOTS)             # 8192
TRANSPILE_SEED = 7                # s3a.TRANSPILE_SEED (VERAENDERT NICHT)
N_CIRCUITS = 160
TOTAL_SHOTS = N_CIRCUITS * SHOTS  # 1,310,720
ISA_2Q_PER_CIRCUIT_MAX = 120      # hw.ISA_2Q_PER_CIRCUIT_MAX (geerbt)
ISA_2Q_TOTAL_MAX = 6000           # hw.ISA_2Q_TOTAL_MAX (geerbt)
NQ3, NQ5 = 2, 3                   # Minimalregister (geerbt 042)

N_NEW_CAL_Q5 = 11
N_CAL_Q5_TARGET = 5 + N_NEW_CAL_Q5          # 16 (Deck D.5)
D_TOL = 1e-12
CP_TOL = 1e-12

# Verdict-/Kal-P-Vektoren (Run-2/Run-3 committet, 042/043/044)
VERDICT_P = {"q3_d3": list(h3.NEW_Q3_POINTS),      # [181,229,283,379,467,613,691,797]
             "q5_d5": list(h3.NEW_Q5_POINTS)}      # [467,547,613,673,691]
CAL_OLD_P = {"q3_d3": list(h3.CAL_Q3_POINTS),      # [149,197,251,347,433,577,659,761]
             "q5_d5": list(h3.CAL_Q5_POINTS)}      # [433,499,577,631,659]

ARMS = ("q3_d3", "q5_d5")
Q_BY_ARM = {"q3_d3": 3, "q5_d5": 5}
D_MIN_BY_ARM = {"q3_d3": 3, "q5_d5": 5}
D_FAM_BY_ARM = {"q3_d3": (9, 27), "q5_d5": (25, 125)}   # k2-Lesart
FAM_BY_ARM = {"q3_d3": (3, 9, 27), "q5_d5": (5, 25, 125)}  # inkl. d_min (Ref)
NQ_BY_ARM = {"q3_d3": NQ3, "q5_d5": NQ5}

# Gepinnte ex-ante-Anker (design_out verifiziert; --verify rechnen sie frisch
# gegen die committeten Evals nach und MUSS bit-gleich treffen)
ANCHOR_RHO_Q5 = 0.49999999999999994     # S1->S2 observed, verdict q5 (n=5)
ANCHOR_RHO_Q3 = 0.8095238095238096      # S1->S2 observed, verdict q3 (n=8)
ANCHOR_RHO_POOLED = 0.8956043956043955  # 13 gepoolte Reihen (bit-pin Deck)
Q95_PERM_Q5 = 0.7999999999999999        # sekundaer (n_perm 120, n=5-LEKTION)
Q95_PERM_Q3 = 0.6190476190476191        # sekundaer (n_perm 40320)
SE_NO_INT_S1_Q5_CAL = 0.0025335578768332333   # D.5-SE-Provenance (no-int LSQ)
SE_C_MEAN_S1 = 0.01197607825720734            # SE·c̄ ~ Deck "0.011"
SQRT_EXPECT_N16 = 0.0014163019093822874       # SE·sqrt(5/16)
KAPPA_S1_Q5_CAL_MIN = 0.8115144847818115      # Void-Gate ex ante (knapp)
RHO_C_VORPROBE_Q5 = 0.1879                    # (F)-Kontext, Runde (descriptiv)
RHO_C_VORPROBE_Q3 = -0.4441                   # (F)-Kontext, Runde (descriptiv)

FEZ_BACKLOG = ("QUQUINT-F4 daua5hahcrkc73dv9eh0 -> 046 "
               "dauassrojkfs738rrcsg -> 055")
JOB046_ID = "dauassrojkfs738rrcsg"


# ------------------------------------------------------------- Helfer -----
def spearman(a, b):
    """§Z.31-Konvention: argsort-argsort-Raenge + Pearson."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def q95_exact_perm(v_anchor, v_other):
    """q95 der exakten Permutations-Null (deterministisch, kein RNG).

    rho(v_anchor, P(v)) fuer ALLE n!-Permutationen; q95 = kleinster Wert
    >= 95 % der Nullmenge (int(ceil(0.95*n)) - 1 nach Sortierung).
    """
    v_anchor = np.asarray(v_anchor, dtype=float)
    v_other = np.asarray(v_other, dtype=float)
    rhos = [spearman(v_anchor, v_other[list(p)])
            for p in itertools.permutations(range(len(v_anchor)))]
    rhos = np.sort(np.asarray(rhos))
    return float(rhos[int(np.ceil(0.95 * len(rhos))) - 1]), len(rhos)


def arm_rows(path, arm):
    """Verdict-/Kal-Zeilen eines Arms aus einem Eval-Artefakt (Design-Scratch)."""
    d = json.load(open(path, encoding="utf-8"))
    rows = {}
    for key, row in d["punkte"].items():
        setname, armname, _ps = key.split("|")
        if armname != arm:
            continue
        rows.setdefault(setname, {})[row["P"]] = row
    out = {}
    for setname, byP in rows.items():
        Ps = sorted(byP)
        out[setname] = {
            "P": Ps,
            "res": [float(byP[p]["res_v3"]) for p in Ps],
            "c_p": [float(byP[p]["c_p"]) for p in Ps],
            "below_sharp": [p for p in Ps if byP[p]["below_sharp"]],
            "kappa": [float(byP[p]["kappa_hat"]) for p in Ps],
        }
    return out


def _fmd5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


# ------------------------------------------------------- Punkte-Ableitung --
def union40():
    """Messungs-Vereinigung nach 051: K2-extended_union (30) U Run-4-verdict.

    Nur Messungs-MEMBERSHIP (committete Grids) — keine Messwerte.
    """
    k2 = json.load(open(K2_PREREG, encoding="utf-8"))
    grid = k2["grid"]
    union30 = set(grid["extended_union_sorted"])
    r4 = grid["run4"]
    verdict_new = set(r4["q3_d3"]["verdict"]) | set(r4["q5_d5"]["verdict"])
    u = sorted(union30 | verdict_new)
    if not set(h3.MEASURED_UNION) <= set(u):
        raise ValueError("union40 enthaelt den 11b-MEASURED_UNION nicht")
    return u


def ladder_ps(with_log=True):
    """Die 11 neuen Kalibrier-P: WOERTLICHE new_points_run3-Iteration.

    Generationen: Gen1 (aus den 5 Run-2-Kal-P), Gen2 (aus Gen1), Gen3 —
    die Union WAECHST dabei um jede GENOMMENE Kandidat (Kollisionsskip
    inkl. eigener frueherer Kandidaten). Code-Lesart ist registriert
    (smallest_prime_above = strikt > x; Hand-Notat des Design-Fensters
    [479,557,607,...] ist WIDERRUFEN — siehe design_out-Belege).
    """
    u = set(union40())
    gen_in = list(h3.CAL_Q5_POINTS)            # 433,499,577,631,659
    out, log, used = [], [], set()
    gen = 0
    while len(out) < N_NEW_CAL_Q5 and gen < 10:
        gen += 1
        cand = h3.new_points_run3(gen_in, u)
        for p in cand:
            if len(out) >= N_NEW_CAL_Q5:
                break
            out.append(p)
            u.add(p)
            used.add(p)
        if with_log:
            log.append({"generation": gen, "P_alt": list(gen_in),
                        "candidates": list(cand)})
        gen_in = list(cand)
    if len(out) != N_NEW_CAL_Q5:
        raise ValueError("Ladder ergab %d statt %d P"
                         % (len(out), N_NEW_CAL_Q5))
    if set(out) & set(union40()):
        raise ValueError("Ladder kollidiert mit der Union-40")
    return (out, log) if with_log else out


def arm_records(arm, plist):
    """arm_point-Records eines Arms (k2-Mirror) mit d-Invarianz ueber die
    REGISTER-Familie FAM_BY_ARM (Ref = d_min, 1e-12)."""
    d = D_MIN_BY_ARM[arm]
    q = Q_BY_ARM[arm]
    out = {}
    for P in sorted(plist):
        pt = h3.arm_point(P, d, q)
        ref = pt["ratio_true"]
        for dv in FAM_BY_ARM[arm]:
            r2 = h3.arm_point(P, dv, q)["ratio_true"]
            if abs(r2 - ref) > D_TOL:
                raise ValueError("d-Invarianz verletzt (P=%d, d=%d, arm=%s)"
                                 % (P, dv, arm))
        out[(arm, P)] = pt
    return out


def _records_by_P(rows):
    return {rec["P"]: rec for rec in rows}


def fresh_points():
    """Punkt-Records fuer 055 mit BIT-CHECKS gegen das gefrorene 11b-Prereg:

      - 13 verdict-Records bit-gleich prediction_freeze.points[arm]
        (044-Freeze; K2 hat dieselben als ITS Run-4-cal bereits bit-gecheckt);
      - 13 cal-old-Records bit-gleich kalibrier_bein.points[arm]
        (11b-Kalibrier-Bein = Run-2-verdict-P — die kalibrier_bein-Ziele
        sind hier DIE BIT-CHECK-Quelle, nicht prediction_freeze);
      - 11 Ladder-Records frisch via arm_point (d-Invarianz 1e-12).
    """
    with open(H3_PREREG, encoding="utf-8") as fh:
        pr = json.load(fh)
    pts, cal_old = {}, {}
    for arm in ARMS:
        recs = arm_records(arm, VERDICT_P[arm])
        old_v = _records_by_P(pr["prediction_freeze"]["points"][arm])
        for (_arm, P), rec in recs.items():
            if json.dumps(rec, sort_keys=True) != json.dumps(old_v[P],
                                                             sort_keys=True):
                raise ValueError("Verdict-Record != 11b-Prereg (P=%d, %s)"
                                 % (P, arm))
        pts.update(recs)
        recs_c = arm_records(arm, CAL_OLD_P[arm])
        old_c = _records_by_P(pr["kalibrier_bein"]["points"][arm])
        for (_arm, P), rec in recs_c.items():
            if json.dumps(rec, sort_keys=True) != json.dumps(old_c[P],
                                                             sort_keys=True):
                raise ValueError("Kal-Record != 11b-Kalibrier-Bein (P=%d, %s)"
                                 % (P, arm))
        cal_old.update(recs_c)
    ladder, log = ladder_ps()
    cal_new = arm_records("q5_d5", ladder)
    return pts, cal_old, cal_new, ladder, log


def eval_grid():
    """Gestempelte Grids für build_hardware_circuit_set (k2-Mirror)."""
    pts, cal_old, cal_new, ladder, log = fresh_points()
    pts_e = {k: {**r, "arm": k[0], "set": h3a.SET_VERDICT}
             for k, r in sorted(pts.items())}
    cal_e = {k: {**r, "arm": k[0], "set": h3a.SET_CAL}
             for k, r in sorted(cal_old.items())}
    cal_e.update({k: {**r, "arm": k[0], "set": h3a.SET_CAL}
                  for k, r in sorted(cal_new.items())})
    return pts_e, cal_e, ladder


def cP_freeze_fresh(pts_e, cal_e):
    """cP-Registry (k2-Lesart, set|arm|P) mit Bit-Checks:

      - alle verdict-Eintraege BIT-GLEICH dem committeten 044-cP_freeze;
      - die 26 cal-old-Eintraege BIT-GLEICH dem committeten 044-cP_freeze
        (selbe Kal-Zeilen-Konvention — deterministische same-transpile);
      - die 11 Ladder-Eintraege sind FRISCH (kein 044-Praedezessor).
    """
    pr44 = h3.load_frozen_prereg()
    legacy = pr44["prediction_freeze"]["cP_freeze"]
    out = {}
    for _k, pt in sorted(pts_e.items()):
        key = "verdict|%s|%d" % (pt["arm"], pt["P"])
        out[key] = float(h3.coh_sens(pt))
        if abs(out[key] - float(legacy[key])) > CP_TOL:
            raise ValueError("cP-Verdict != committet (044) fuer %s" % key)
    for _k, pt in sorted(cal_e.items()):
        key = "cal|%s|%d" % (pt["arm"], pt["P"])
        out[key] = float(h3.coh_sens(pt))
        if key in legacy and abs(out[key] - float(legacy[key])) > CP_TOL:
            raise ValueError("cP-Cal-old != committet (044) fuer %s" % key)
    return out


# ------------------------------------------------------ Layout-Perturbation --
def layout_slots(nq, edges):
    """Alle verbundenen induzierten Subgraphen der Kopplungsmap (Groesse nq),
    als sortierte Tuples, LEXIKOGRAPHISCH. Heavy-hex ohne Dreiecke:
    Groesse 3 == 3-Knoten-Pfade. Fast-Path: jede verbundene nq-Menge hat
    >= nq-1 interne Kanten (notwendig), dann BFS-Check."""
    edges = [(int(a), int(b)) for a, b in edges]
    nodes = sorted({x for e in edges for x in e})
    adj = {x: set() for x in nodes}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    nset = set(nodes)
    slots = []
    for comb in itertools.combinations(nodes, nq):
        s = set(comb)
        deg = sum(1 for a, b in edges if a in s and b in s)
        if deg < nq - 1:
            continue
        seen = {comb[0]}
        front = [comb[0]]
        while front:
            x = front.pop()
            for y in adj[x] & nset & s:
                if y not in seen:
                    seen.add(y)
                    front.append(y)
        if len(seen) == nq:
            slots.append(comb)
    slots.sort()
    return slots


def forced_row_order():
    """FORCED-Reihen je Arm: verdict aufsteigend, dann cal-old aufsteigend,
    dann Ladder in Generierungs-Reihenfolge (q5). Gibt {(arm): [row_keys]}.

    Reparatur 2026-10-03 (latenter Bug, Feuerpunkt nur in forced_row_order —
    der Freeze-Pfad ruft diese Funktion nicht; Payload-md5 unberuehrt):
    ladder_ps(with_log=False) liefert die NAKKE Liste (kein (out, log)-Paar)
    — der zweistellige Unpack war ein ValueError 'too many values'."""
    ladder = ladder_ps(with_log=False)
    order = {}
    for arm in ARMS:
        rows = [("verdict", P) for P in sorted(VERDICT_P[arm])]
        rows += [("cal", P) for P in sorted(CAL_OLD_P[arm])]
        if arm == "q5_d5":
            rows += [("cal", P) for P in ladder]
        order[arm] = rows
    return order


def slot_assignment(n_rows, n_slots, start=1):
    """Zyklischer Shift (Reihe i -> Slot (start + i) mod n_slots), start=1
    (die Einstellungs-Regel: NIEMALS Slot 0 = 'Freeze-Geometrie' fuer die
    erste Zeile)."""
    return [(start + i) % n_slots for i in range(n_rows)]


# ------------------------------------------------------------- Anchor-Lesung --
def _sess_rows():
    b = json.load(open(SESSIONS_OUT, encoding="utf-8"))["b_session_residuen"]
    return (list(b["q5_rows"]), list(b["q3_rows"]))


def recompute_anchors():
    """Alle registrierten Anker FRISCH aus den committeten Artefakten
    rechnen (S1/S2-Evals + h9_sessions-Scratch) und bit gegen die
    Konstanten pruefen — wird von --verify UND vom Freeze-Builder benutzt."""
    s1q5 = arm_rows(H3_EVAL_S1, "q5_d5")
    s2q5 = arm_rows(H3_EVAL_S2, "q5_d5")
    s1q3 = arm_rows(H3_EVAL_S1, "q3_d3")
    s2q3 = arm_rows(H3_EVAL_S2, "q3_d3")
    if s1q5["verdict"]["P"] != s2q5["verdict"]["P"]:
        raise ValueError("S1/S2-verdict-P-Vektoren differieren (q5)")
    if s1q5["verdict"]["c_p"] != s2q5["verdict"]["c_p"] or \
            s1q3["verdict"]["c_p"] != s2q3["verdict"]["c_p"]:
        raise ValueError("c_p S1 != S2 (deterministische same-transpile "
                         "verletzt — C3/C.1-Grundlage faellt weg)")
    rho5 = spearman(s1q5["verdict"]["res"], s2q5["verdict"]["res"])
    rho3 = spearman(s1q3["verdict"]["res"], s2q3["verdict"]["res"])
    q5_rows, q3_rows = _sess_rows()
    brows = q5_rows + q3_rows
    rho_pool = spearman([r["s1"] for r in brows], [r["s2"] for r in brows])
    q95_5, npm5 = q95_exact_perm(s1q5["verdict"]["res"],
                                 s2q5["verdict"]["res"])
    q95_3, npm3 = q95_exact_perm(s1q3["verdict"]["res"],
                                 s2q3["verdict"]["res"])
    checks = {
        "anchor_rho_q5": (rho5, ANCHOR_RHO_Q5),
        "anchor_rho_q3": (rho3, ANCHOR_RHO_Q3),
        "anchor_rho_pooled": (rho_pool, ANCHOR_RHO_POOLED),
        "q95_exact_perm_q5": (q95_5, Q95_PERM_Q5),
        "q95_exact_perm_q3": (q95_3, Q95_PERM_Q3),
    }
    diverging = [k for k, (got, pin) in checks.items()
                 if abs(got - pin) > 1e-12]
    if diverging:
        raise ValueError("Anker-Rechnung trifft Pin nicht: %s" % diverging)
    # D.5-SE (no-intercept LSQ) an den S1-q5-Cal-Reihen:
    s1gamma = json.load(open(H3_EVAL_S1, encoding="utf-8"))["gamma_arm"]["q5_d5"]
    crows = s1gamma["rows"]
    cps = np.array([r["c_p"] for r in crows])
    dls = np.array([r["delta_cal"] for r in crows])
    gam = float(cps @ dls) / float(cps @ cps)
    scatter = dls - gam * cps
    se = float(np.sqrt(float(scatter @ scatter) / (len(cps) - 1)
                       / float(cps @ cps)))
    mean_c = float(np.mean(cps))
    if abs(se - SE_NO_INT_S1_Q5_CAL) > 1e-12:
        raise ValueError("SE-no-int-Anker trifft Pin nicht")
    if abs(se * mean_c - SE_C_MEAN_S1) > 1e-12:
        raise ValueError("SE·c̄-Provenance trifft Pin nicht")
    return {
        "rho_q5": rho5, "rho_q3": rho3, "rho_pooled": rho_pool,
        "q95_q5": q95_5, "n_perm_q5": npm5,
        "q95_q3": q95_3, "n_perm_q3": npm3,
        "se_no_int": se, "mean_c": mean_c,
        "se_times_mean_c": se * mean_c,
        "sqrt_skalierung_n16": se * np.sqrt(5.0 / 16.0),
        "c_p_identisch_s1_s2": True,
    }


# ------------------------------------------------------------- Payload -----
def _inherit(key):
    """11b-Freeze-Block WORDGLICH uebernehmen (kein Hand-Typing-Drift)."""
    pr = h3.load_frozen_prereg(H3_PREREG)
    return pr[key]


def build_prereg_payload():
    """Der 055-Prereg-Payload (REGISTERED_NOT_MEASURED)."""
    pts_e, cal_e, ladder = eval_grid()
    cP = cP_freeze_fresh(pts_e, cal_e)
    pts, cal_old, cal_new, _ladder, log = fresh_points()
    anchors = recompute_anchors()

    rec_points = {a: [{**(pts[(a, P)])} for P in sorted(VERDICT_P[a])]
                  for a in ARMS}
    # Unstamped Records BITGLEICH 11b (frisch_points gecheckt — 044-shape).
    cal_rows = {a: [{**(cal_old[(a, P)])} for P in sorted(CAL_OLD_P[a])]
                for a in ARMS}
    cal_rows["q5_d5"] += [{**(cal_new[("q5_d5", P)])} for P in ladder]

    payload = {
        # ---------------------------- Registry-Rahmen ---------------------
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "leg": LEG,
        "status": "REGISTERED_NOT_MEASURED",
        "registered_before": "2026-10-03 (vor jeder Messung dieses Jobs; kein "
                             "Messwert dieser Registrierung zugefuehrt)",
        "registered_by": "Claude (autonom, Task #83) — User-Anker "
                         "'mache weiter mit tasks'",
        "user_directive": "EIN Fez-Job hinter 046 (Backlog %s); kein Push, "
                          "kein Re-Decide." % FEZ_BACKLOG,

        # ------------------------- Verkettung (prior chain) ---------------
        "prior_chain": {
            **_inherit("prior_chain"),
            "EXPERIMENT_047_EVAL_REP_MD5": _fmd5(H3_EVAL_S2),
            "EXPERIMENT_051_K2_PREREG_MD5": _fmd5(K2_PREREG),
            "EXPERIMENT_051_K2_KINGSTON_EVAL_MD5": _fmd5(K2_EVAL),
            "EXPERIMENT_053_MD5_HINWEIS": "Kette siehe §Z.35 (053, H-ZQZ) — "
                                          "kein Messinput für 055",
        },

        # ---------------------- Schichttrennung (unveraendert) ------------
        "layer_separation": _inherit("layer_separation"),
        "frozen_theorems": _inherit("frozen_theorems"),
        "phase10_verdict_context": _inherit("phase10_verdict_context"),
        "operational_definitions": _inherit("operational_definitions"),
        "design_decision": {
            **_inherit("design_decision"),
            "fprio4_8_design": "EIN combined Job fuer F-Prio 4 UND 8; "
                               "Layout-Perturbation ist der EINZIGE "
                               "registrierte Transpilation-Delta (seed 7 "
                               "unveraendert); die C1-Massstabs-Entscheidung "
                               "(ANKER-PARITAET statt q95) folgt der n=5-"
                               "LEKTION — belegt im Design-Scratch "
                               "(h9_fprio48_design_out.json).",
        },
        "fallback_lesart_b_inherited": _inherit("fallback_lesart_b"),
        "inherited_freeze_note": "Freeze-A'/B''/C''-Budget (044/047) und die "
                                 "044-verdict-Freezes bleiben UNANGETASTET; "
                                 "055 erweitert das Kalibrier-Bein (n=16) und "
                                 "shiftet die Geometrie (C1/C3).",

        # ---------------------------- Klassik-Kern ------------------------
        "classical_core": _inherit("prediction_freeze")["classical_core"],
        "echo_ladder": {
            **_inherit("echo_ladder"),
            "fprio5_lesart_b_status": "descriptiv auf DIESEM Job via die 12 "
                                      "unforced Auto-Layout-Circuits — "
                                      "gleiche Geometrie wie S1/S2; NICHT "
                                      "verdict-tragend.",
            "w_a_r1": W_A,
        },

        # ------------------- prediction freeze (044-Mirror) ---------------
        "prediction_freeze": {
            "classical_core": _inherit("prediction_freeze")["classical_core"],
            "p_rule": _inherit("prediction_freeze")["p_rule"],
            "noise_law": _inherit("prediction_freeze")["noise_law"],
            "points": rec_points,
            "calibration_points": cal_rows,
            "cP_freeze": cP,
            "anchor_verification": {
                "run1_regression": "verify_anchors_run3 (tol 1e-9) "
                                   "geerbt 042/044 — in --verify "
                                   "frisch ausgefuehrt",
                "d_invariance_register_fam": "1e-12 je Row "
                                             "(FAM_BY_ARM inkl. d_min)",
                "c_p_identische_s1_s2": anchors["c_p_identisch_s1_s2"],
            },
        },

        # -------------------------- Kalibrier-Bein ------------------------
        "kalibrier_bein": {
            "purpose": "GAMMA-FIT-Bein (kein Verdict) + F-Prio-8-Refit "
                       "(n_cal(q5) = 16); die 13 al Kal-Zeilen sind BITGLEICH "
                       "dem 11b-Kalibrier-Bein (Run-2-verdict-P); die 11 "
                       "neuen P sind die wörtliche Phase-11b-Regel-Iteration.",
            "points": cal_rows,
            "reps": 3,
            "loschmidt_gepaart": True,
            "gamma_fit_rule": _inherit("kalibrier_bein")["gamma_fit_rule"],
            "verdict_role": "kein Verdict; nur Fit/Refit + Void-Gate "
                            "(kappa ceiling 0.81).",
            "leckage_dokumentiert": _inherit("kalibrier_bein")[
                "leckage_dokumentiert"],
            "n_new_cal_q5": N_NEW_CAL_Q5,
            "ladder_generations": log,
        },

        # -------------------------- Hardware-Parameters -------------------
        "hardware_parameters": {
            "circuit_budget": N_CIRCUITS,
            "shots_per_circuit": SHOTS,
            "total_shots": TOTAL_SHOTS,
            "backend": "ibm_fez",
            "one_job": True,
            "fez_backlog": FEZ_BACKLOG,
            "job046_id": JOB046_ID,
            "isa_ceilings": {
                "per_circuit_2q_max": ISA_2Q_PER_CIRCUIT_MAX,
                "total_2q_max": ISA_2Q_TOTAL_MAX,
                "inherited": "hw-Konstanten (geerbt 042/044)",
            },
            "run_config": _inherit("hardware_parameters")["run_config"],
        },

        "layout_perturbation": {
            "purpose": "F-Prio 4: die Geometrie-Zuordnung verschiebt sich "
                       "pro Zeile zyklisch, die P-Vektoren bleiben unveraendert "
                       "(C1-Test: P-Bindung); Delta-c testet die Geometrie-"
                       "Bindung (D.7-C3).",
            "rule": "FORCED initial_layout je Circuit (KEIN Seed-Wechsel, "
                    "transpiler seed 7 UNVERAENDERT); Reihen pro Arm nach "
                    "(set, P) sortiert [verdict aufsteigend, dann cal-old "
                    "aufsteigend, dann Ladder-Reihenfolge], Slots = lexiko- "
                    "graphische Enumeration verbundener induzierter Subgraphen "
                    "der LIVE-Kopplungsmap (Groesse 2 = Kanten/q3, Groesse 3 "
                    "= 3-Knoten-Pfade/q5), Zuordnung = zyklischer Shift "
                    "(Reihe i -> Slot i+1 mod n_rows_arm); Fallback bei "
                    "ISA-Ceiling: skip-forward, im Report dokumentiert.",
            "seed": TRANSPILE_SEED,
            "optimization_level": 3,
            "transpiler_delta": "NUR initial_layout",
            "cP_perturbation_source": "Delta-c = c_prime - c_S1; c_prime aus "
                                      "pt_ram_q_prio48_isa_report.json "
                                      "(VOR Submission committet), c_S1 aus "
                                      "pt_ram_q_hardware3_eval.json "
                                      "[committet S1]; c_S1 == c_S2 "
                                      "bit-verified (deterministische "
                                      "same-transpile),",
            "unforced_subset": "Echo-Leiter (6) + negative Kontrollen (4) + "
                               "readout_cal (2) = 12 Circuits unter Auto-"
                               "Layout seed 7 — per-Circuit-2q bitgleich "
                               "gegen pt_ram_q_isa3_report.json (Gate-"
                               "Assertion); fez-scoped FPrio-5-Lesart (b) "
                               "dadurch MESSBAR.",
        },

        # ------------------------------ Kriterien -------------------------
        "session_anchors": {
            "c1_massstab": "ANKER-PARITAET (>= beobachtet S1->S2 je Arm); "
                           "q95-exakt bleibt SEKUNDAERER Deskriptiv-Benchmark "
                           "(n=5-LEKTION: TRUE-Replication erreicht nur rho "
                           "0.5 = 80-Perzentil-Klasse bei 120 Permutationen).",
            "rho_S1_S2_q5_verdict_pin": ANCHOR_RHO_Q5,
            "rho_S1_S2_q3_verdict_pin": ANCHOR_RHO_Q3,
            "rho_S1_S2_pooled_13_pin": ANCHOR_RHO_POOLED,
            "q95_exact_perm_q5_sekundaer_pin": Q95_PERM_Q5,
            "n_perm_q5": 120,
            "q95_exact_perm_q3_sekundaer_pin": Q95_PERM_Q3,
            "n_perm_q3": 40320,
            "kriterium_C1_q5": "rho(res'_q5-verdict, res_S1_q5-verdict) >= "
                               "Anchor S1->S2 (0.5-Klasse)",
            "kriterium_C1_q3": "rho(res'_q3-verdict, res_S1_q3-verdict) >= "
                               "Anchor S1->S2 (0.8095-Klasse)",
            "frisch_getestet_in_verify": anchors,
        },
        "c2_criteria": {
            "q5_kern": "S2-below {467, 673} BOTH transfer (2/2)",
            "q5_zweitstufe_S1": "{467, 547, 673} mindest 2/3 (547 "
                                "session-spezifisch)",
            "q3": "klassenleer in S1/S2 — n/a",
            "sharpness": "committete 0.01-|res|-Konvention, Band w_B'' "
                         "(below_sharp = res_v3 < center - w_B'')",
            "w_b_doubleprime_pin": W_B_DP,
        },
        "c3_geometry_counter": {
            "statistic": "exact-perm Spearman(Delta-res, Delta-c) je Arm",
            "delta_res": "res' (Session 3) - res_S1 (committet) je Verdict-"
                         "Reihe (n=5/q5, n=8/q3)",
            "delta_c": "c_prime - c_S1 aus dem VOR Messung committeten "
                       "ISA-Report",
            "feuer_kriterium": "rho(Delta-res, Delta-c) >= q95-exakt je Arm "
                               "(q5: 0.7999…-Klasse, q3: 0.6190…-Klasse)",
            "verdict_role": "NEIN-Feuern ist die C3-null-Voraussetzung der "
                            "C1-Verdicts",
            "descriptiv_role": "feuernde/unterscheide C3 ist der D.7-Beweis.",
        },
        "c1_c_vorprobe": {
            "role": "DESKRIPTIV registriert (KEIN Verdict-Kriterium); Design "
                    "unabhaengig vom Ausgang",
            "committed_rho_S1": {"q5": RHO_C_VORPROBE_Q5,
                                 "q3": RHO_C_VORPROBE_Q3},
            "null": "exakt-perm (design_out)",
        },

        # ------------------------------ FPrio-8 ---------------------------
        "fprio8_refit": {
            "gamma_refit_q5": "no-intercept LSQ gamma' = <c,Delta>/<c,c> "
                              "ueber 16 Kal-Reihen (law-konsistent, "
                              "fit_gamma_arm-Konvention)",
            "decomposition_F": "OLS-mit-Achsenabschnitt X = [ones, c_p], "
                               "se = sqrt(s2*XtXi[1,1]), resid_std ddof=2",
            "d5_se_provenance": "SE_no_int * c̄ (S1,q5,cal) %r ~ Deck "
                                "'SE(gamma)*c_p ~ 0.011' — die D.5-Zahl ist "
                                "die Durch-Null-LSQ-SE, NICHT die (F)-OLS-SE "
                                "0.1254448714861779."
                                % SE_C_MEAN_S1,
            "se_no_int_S1_pin": SE_NO_INT_S1_Q5_CAL,
            "se_times_mean_c_S1_pin": SE_C_MEAN_S1,
            "sqrt_skalierung_n16_pin": SQRT_EXPECT_N16,
            "kappa_S1_q5_cal_min_pin": KAPPA_S1_Q5_CAL_MIN,
            "falsifikatorlinie_F_zeile_8": "resid_sd(q5, OLS-mit-Achsen-"
                                           "abschnitt, ddof=2, n=16 Kal-"
                                           "Reihen) < 0.01 -> SA-H9-5 kippt "
                                           "(Kalibrier-Streuung ist NICHT "
                                           "Band-Groesse); sonst BLEIBT "
                                           "SA-H9-5.",
            "committed_F_anchors": {
                "q5": {"gamma_committed": 0.038128743451453374,
                       "gamma_ols": 0.21586104749721277,
                       "se_gamma": 0.1254448714861779,
                       "resid_sd": 0.023936865145634485,
                       "r2": 0.4967312299110952, "n": 5},
                "q3": {"gamma_committed": 0.009105648402709013,
                       "se_gamma": 0.012189383635140131,
                       "resid_sd": 0.009138844281032127,
                       "r2": 0.6525102051324765, "n": 8},
            },
        },

        # ------------------------------ Kontrollen ------------------------
        "controls": _inherit("controls"),

        # ---------------------------- safeguard ---------------------------
        "safeguard_limits": {
            "kappa_ceiling": KAPPA_CEILING,
            "void": "REFIT_INVALID_KAPPA: kappa_hat < 0.81 an >= 2 der "
                    "Union-Reihen -> gamma-Refit invalid (descriptiv-void; "
                    "kein kritisches Verdict-Ableiten)",
            "kontrolle_void": "EVALUATION_INVALID_KONTROLLE_GESCHEITERT",
            "w_band": W_B_DP,
            "w_a": W_A,
        },

        # ------------------------------ Verdict ---------------------------
        "verdict_map": {
            "P_BOUND_TRANSFER_HELD": "C1 beide Arme >= S1->S2-Anker UND C2 "
                                     "UND kein C3-Feuer (rho(Delta-res, "
                                     "Delta-c) < q95-exakt je Arm)",
            "GEOMETRYBOUND_D7": "C1 q5 unter Anchor UND C3 q5 feuert "
                                "(>= q95-exakt) — D.7 gewinnt die Runde, "
                                "auf Session-3-Ebene dokumentiert; "
                                "H-RAM-Q-4 bleibt REFUTED",
            "MIXED_PARTIAL": "Teilweise (mind. ein Transfer-Arm gehalten, "
                             "keine klare Konstellation)",
            "UNDETERMINED": "Datenlage unklar (keine der Konstellationen)",
        },
        "banned_from_raw": ["kappa", "ratio", "gamma", "band", "verdict",
                            "res_v3", "center", "delta_cal"],

        # ------------------------- Governance/Grammatik -------------------
        "qpu": {
            "backend": "ibm_fez",
            "token_discipline": "NUR TOKEN1 (IBMQ_TOKEN aus .env via "
                                "pt_ququint_fez); TOKEN2 wird NIE gelesen; "
                                "kein Sampler-V2-Local-Pfad.",
            "sampler": "SamplerV2 (raw counts, resilience none), "
                       "default_shots 8192, DD XX (Prereg run_config), "
                       "ALLE 160 Circuits in EINEM Job (circuit_budget).",
            "transpile": {"optimization_level": 3,
                          "seed_transpiler": TRANSPILE_SEED,
                          "initial_layout": "FORCED (layout_perturbation)"},
            "job_id_file": JOB_ID_PATH,
            "raw_path": RAW_PATH,
            "raw_discipline": "raw.json traegt NUR counts (+ job_meta/"
                              "transpile/run_config) — KEIN kappa/ratio/"
                              "gamma/band/verdict; Roh-Commit VOR Auswertung.",
            "resume_vertrag": "Existiert raw.json: geschieht NICHTS. Existiert "
                              "die Job-ID-Datei: Resume via service.job(id) "
                              "(KEIN neuer Job — 046-/053-Praezedenz).",
        },
        "anti_sharpshooter": "Alle Kandidaten werden aus committeten Grids "
                             "abgeleitet (NUR Messungs-MEMBERSHIP); die 11 "
                             "P entstammen der wörtlichen registrierten "
                             "Phase-11b-P-Regel (new_points_run3-Iteration); "
                             "kein ex-post-Fit, keine Toleranz-Erhoehnung, "
                             "kein Re-Decide.",
        "suite_state": {
            "basis_tests": 1342,
            "prio48_tests_geplant": ">= 15 (Modul-Statik + Points/CP/Anker/"
                                    "Layout-Statik + Runner-ISA-Fallback)",
            "suite_command": "QISKIT_PARALLEL=FALSE venv/bin/python "
                             "-m pytest tests/ -q",
        },
        "future_phase_numbering": {
            "experiment": "055",
            "reserved_054": "GOE-Angebot (angeboten, NICHT ausgeführt)",
            "note": "Nummerierung 048..053 belegt; 055 das kombinierte "
                    "F-Prio-4+8-Experiment.",
        },
        "integritaet": {
            "qpu_jobs_now": 0,
            "verdict_re_decide": False,
            "prereg_freezes_beruehrt": False,
            "toleranz_erhoehung": False,
        },
    }
    return payload


# ------------------------------------------------- Freeze / Verifizierung --
def canonical_payload_json(payload):
    """HOUSKONVENTION (h3/053): sort_keys + compact separators —
    Payload-Content-md5, NICHT die Byte-MD5 des Files (indent-Spaltung)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def payload_md5(payload):
    return hashlib.md5(canonical_payload_json(payload).encode("utf-8")
                       ).hexdigest()


def freeze_prereg(path=PREREG_PATH):
    payload = build_prereg_payload()
    doc = dict(payload)
    doc["md5"] = payload_md5(payload)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    return doc


def verify_prereg_md5(doc):
    stripped = {k: v for k, v in doc.items() if k != "md5"}
    return payload_md5(stripped) == doc["md5"]


def load_frozen_prereg(path=PREREG_PATH):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if not verify_prereg_md5(doc):
        raise ValueError("055-Prereg-md5-MISMATCH in %s" % path)
    return doc


def verify_frozen(path=PREREG_PATH):
    """Alle BIT-CHECKS am gefrorenen 055-Prereg (Verify/Regression)."""
    doc = load_frozen_prereg(path)
    pts_e, cal_e, ladder = eval_grid()
    cP = cP_freeze_fresh(pts_e, cal_e)
    got = doc["prediction_freeze"]["cP_freeze"]
    diverging = [k for k in cP if k in got and
                 abs(cP[k] - float(got[k])) > CP_TOL]
    missing = [k for k in cP if k not in got]
    if diverging or missing:
        raise ValueError("cP-Divergenz (diverging=%s, missing=%s)"
                         % (diverging, missing))
    # Ladder-Determinismus: die 11 neuen q5-Kal-Reihen des Preregs muessen
    # exakt die frisch abgeleitete Ladder-Reihenfolge sein (Gen-Reihenfolge).
    kb_q5 = doc["kalibrier_bein"]["points"]["q5_d5"]
    kb_ladder = [rec["P"] for rec in kb_q5][len(CAL_OLD_P["q5_d5"]):]
    if kb_ladder != ladder:
        raise ValueError("Prereg-Ladder != frische Iteration (%s vs %s)"
                         % (kb_ladder, ladder))
    # Anker frisch gegen die Pins (recompute_anchors asserted intern)
    anchors = recompute_anchors()
    h3.verify_anchors_run3(tol=1e-9)
    n_verdict = sum(len(r) for r in doc["prediction_freeze"]["points"].values())
    n_cal = sum(len(r) for r in doc["kalibrier_bein"]["points"].values())
    return {"md5_ok": True, "prereg_md5": doc["md5"],
            "ladder": kb_ladder, "n_verdict_rows": n_verdict,
            "n_cal_rows": n_cal, "n_cP": len(cP), "anchors": anchors}


# --------------------------------------------------------------- CLI ------
def main(argv=None):
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--freeze" in argv:
        doc = freeze_prereg()
        print("frozen:", PREREG_PATH)
        print("md5:", doc["md5"])
        print("n_cP:", len(doc["prediction_freeze"]["cP_freeze"]))
        return 0
    if "--verify" in argv:
        st = verify_frozen()
        print(json.dumps(st, indent=1, sort_keys=True))
        return 0
    # Standard: Selbst-Test ohne Schreiben
    ladder, log = ladder_ps()
    pts_e, cal_e, _l = eval_grid()
    print("== EXPERIMENT 055 (FPrio 4+8) Selbstdiagnose ==")
    print("ladder:", ladder)
    print("rows: verdict", len(pts_e), "| cal", len(cal_e),
          "| total", len(pts_e) + len(cal_e))
    print("budget:", N_CIRCUITS, "x", SHOTS, "=", TOTAL_SHOTS, "shots")
    print("layout slots q3/q5 (Beispiel-Kopplung fehlt offline) — "
          "Enumeration laeuft im Runner/Gate")
    print("anchors:")
    print(json.dumps(recompute_anchors(), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())