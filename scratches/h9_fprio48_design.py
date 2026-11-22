# -*- coding: utf-8 -*-
"""h9_fprio48_design.py — Deck F-Prio 4+8: Kombiniertes P-Shuffle + Kalibrier-Refit.

0 QPU, READ-ONLY auf committeten Artefakten. Design-Scratch für EXPERIMENT 055
(054 bleibt für das GOE-Angebot reserviert): EIN Fez-TOKEN1-Job hinter 046
(Backlog: QUQUINT-F4 daua5hahcrkc73dv9eh0 -> 046 dauassrojkfs738rrcsg -> 055).

Zwei Deck-Falsifikatoren in EINEM Job:
  F-Prio 4 (C.1/D.7): session-stabile P-Bindung KIPPT, wenn Rank-/Klassen-
          Transfer über die S2-P-Vektoren fällt UND die Residuen die
          Geometrie-(c_p-)Schiebung verfolgen (C3).
  F-Prio 8 (D.5): n_cal(q5) >= 16 durch 11 frische Kalibrier-P unter der
          registrierten Phase-11b-P-Regel — die Zerlegung (SE(γ') vs
          per-P-Anatomie) entscheidet wörtlich über SA-H9-5 (F-Zeile 8).

Alle Kandidaten werden aus committeten Grids abgeleitet (Anti-Sharpshooter:
die Ableitung benutzt nur Messungs-MEMBERSHIP, keine Messwerte).
"""
import json
import itertools
import os
import sys
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)          # Workdir-Root (Module + Artefakte)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

OUT = "scratches/h9_fprio48_design_out.json"

S1 = "pt_ram_q_hardware3_eval.json"          # 11d (044), fez, TOKEN1
S2 = "pt_ram_q_hardware3_eval_rep.json"      # 047 rep, fez, TOKEN1
K2_PREREG = "pt_ram_q6_k2_prereg.json"       # 051 Freeze (committete Grids)
SESSIONS_OUT = "scratches/h9_ramq_sessions_out.json"

W_B_DP = 0.02787029633307472   # w_B'' = w_B' (committet)
W_A = 0.05
KAPPA_CEILING = 0.81           # kappa_floor_void-Grenze (geerbt)
S_SHOTS = 8192
REP_5TH = 0.95

# §Z.31-Konvention (h9_ramq_sessions): argsort-argsort-Ränge


def spearman(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def q95_exact_perm(v_anchor, v_other):
    """q95 der exakten Permutations-Null: rho(res_S1, Permutationen von v).

    Deterministisch (kein RNG): alle n! Permutationen, rho jeder Permutation
    gegen den Anker, q95 = kleinster Wert >= 95 % der Nullmenge.
    """
    v_anchor = np.asarray(v_anchor, dtype=float)
    v_other = np.asarray(v_other, dtype=float)
    n = len(v_anchor)
    n_perm = 0
    rhos = []
    for perm in itertools.permutations(range(n)):
        rhos.append(spearman(v_anchor, v_other[list(perm)]))
        n_perm += 1
    rhos = np.sort(np.asarray(rhos))
    idx = int(np.ceil(REP_5TH * n_perm)) - 1
    return float(rhos[idx]), n_perm


def arm_rows(path, arm):
    """Verdict-/Kal-Zeilen eines Arms aus einem Eval-Artefakt."""
    d = json.load(open(path))
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


def main():
    import pt_ram_q_hardware3 as h3

    out = {"experiment": "055-design (F-Prio 4+8 kombiniert, 0 QPU)",
           "hypothesis": "H-H9 C.1/D.7 + D.5 (F-Prio 4 + F-Prio 8)",
           "module_planned": "pt_ram_q_prio48.py / pt_ram_q_prio48_qpu.py"}

    # ---------------------------------------------------------------
    # 1) Messungs-Vereinigung aus K2-Prereg (committet, 051)
    # ---------------------------------------------------------------
    k2 = json.load(open(K2_PREREG))
    grid = k2["grid"]
    union30 = list(grid["extended_union_sorted"])
    r4 = grid["run4"]
    verdict_new = set(r4["q3_d3"]["verdict"]) | set(r4["q5_d5"]["verdict"])
    union40 = sorted(set(union30) | verdict_new)
    out["union"] = {
        "k2_extended_union_size": len(union30),
        "run4_verdict_added": sorted(verdict_new),
        "union_size": len(union40),
        "union_sorted": union40,
        # Kreuzchecks gegen den 11b-Kern:
        "subset_11b_MEASURED_UNION": set(h3.MEASURED_UNION) <= set(union40),
        "size_11b_MEASURED_UNION": len(set(h3.MEASURED_UNION)),
    }

    # ---------------------------------------------------------------
    # 2) Die 11 neuen Kalibrier-P unter der WÖRTLICHEN Phase-11b-Regel
    #    (iterative Generationen; Kollisionsskip gegen Union inkl. der
    #    eigenen früheren Kandidaten)
    # ---------------------------------------------------------------
    union_live = set(union40)
    ladder = []
    ladder_log = []
    gen_in = list(h3.CAL_Q5_POINTS)   # 433,499,577,631,659
    for gen in range(3):
        if len(ladder) >= 11:
            break
        cand = h3.new_points_run3(gen_in, union_live)
        for p in cand:
            if len(ladder) >= 11:
                break
            # Herkunft mitloggen (per Hand-Rechnung prüfbar)
            ladder.append(p)
            union_live.add(p)
        ladder_log.append({
            "generation": gen + 1,
            "P_alt": list(gen_in),
            "candidates": list(cand),
        })
        gen_in = list(cand)
    out["ladder"] = {
        "candidates_ordered": ladder,
        "n_new": len(ladder),
        "n_cal_q5_total": 5 + len(ladder),
        "generations": ladder_log,
        # Hand-Notat (Design-Fenster) zum Audit-Ablauf: [479,557,607,677,701,
        # 509,593,641,719,733,563] — WIDERRUFEN durch den Code-Mirror:
        # smallest_prime_above(x) = kleinste Primzahl STRICTLY > x; die Hand-
        # Notat liess x selbst zu (Fehlerklasse sp_above-Staerke) — Korrektur-
        # belege: sp_above(607) = 613 (prim, Union-Skip -> 617),
        # sp_above(509) = 521, P_alt 617 -> 647 (Union) -> 653.
        # Die Code-Lesart ist registriert (Anti-Sharpshooter: Ableitung nur
        # aus Messungs-Membership).
        "hand_note_widerrufen": True,
        "collides_with_union": [p for p in ladder if p in union40],
    }
    out["ladder"]["n_cal_q5_target_16"] = out["ladder"]["n_cal_q5_total"] == 16

    # ---------------------------------------------------------------
    # 3) Anatomien der 11 neuen P (arm_point-Kern, 042) + d-Invarianz
    # ---------------------------------------------------------------
    anatomy = {}
    d_inv_ok = True
    for P in ladder:
        pt5 = h3.arm_point(P, 5, 5)
        r_ref = pt5["ratio_true"]
        r_variants = {d: h3.arm_point(P, d, 5)["ratio_true"]
                      for d in (5, 25, 125)}
        if any(abs(v - r_ref) > 1e-12 for v in r_variants.values()):
            d_inv_ok = False
        anatomy[str(P)] = {
            "m": pt5["m"],
            "n_d": pt5["n_d"],
            "N": pt5["N"],
            "n0": pt5["n0"],
            "ratio_true": pt5["ratio_true"],
            "L_q": pt5["L_q"],
            "share_true_reg": pt5["share_true_reg"],
            "model_share_reg": pt5["model_share_reg"],
            "sigma2": pt5.get("sigma2"),
        }
    out["anatomy_new_cal"] = anatomy
    out["anatomy_d_invariance_d5_d25_d125_all_1e_12"] = d_inv_ok

    # ---------------------------------------------------------------
    # 4) Budget-Proof: 160 Circuits x 8192 = 1 Job
    # ---------------------------------------------------------------
    rows = {"q3": {"verdict": 8, "cal_old": 8, "cal_new": 0},
            "q5": {"verdict": 5, "cal_old": 5, "cal_new": len(ladder)}}
    per_row_circuits = 4          # 3 struct-Reps + 1 Loschmidt
    forced = (rows["q3"]["verdict"] + rows["q3"]["cal_old"]
              + rows["q5"]["verdict"] + rows["q5"]["cal_old"]
              + rows["q5"]["cal_new"]) * per_row_circuits
    ladder_circuits = 6           # r2/r4/r8 x Anker 181/467 (r1 geteilt)
    controls = 4
    readout_cal = 2
    total = forced + ladder_circuits + controls + readout_cal
    out["budget"] = {
        "rows": rows,
        "per_row_circuits": per_row_circuits,
        "forced_circuits": forced,
        "ladder_circuits": ladder_circuits,
        "controls": controls,
        "readout_cal": readout_cal,
        "total_circuits": total,
        "shots_per_circuit": S_SHOTS,
        "total_shots": total * S_SHOTS,
        "isa_ceilings_frozen": {"per_circuit_2q_max": 120,
                                "total_2q_max": 6000},
        "budget_ok_1_job": total == 160,
    }

    # ---------------------------------------------------------------
    # 5) Ex-ante-Anker aus committeten Evals (S1/S2) + C1-Schwellen
    # ---------------------------------------------------------------
    s1 = arm_rows(S1, "q5_d5")
    s2v = arm_rows(S2, "q5_d5")
    s1q3 = arm_rows(S1, "q3_d3")
    s2q3 = arm_rows(S2, "q3_d3")

    same_P = s1["verdict"]["P"] == s2v["verdict"]["P"]
    c_ident = (s1["verdict"]["c_p"] == s2v["verdict"]["c_p"]
               and s1q3["verdict"]["c_p"] == s2q3["verdict"]["c_p"])

    rho_q5_s1s2 = spearman(s1["verdict"]["res"], s2v["verdict"]["res"])
    rho_q3_s1s2 = spearman(s1q3["verdict"]["res"], s2q3["verdict"]["res"])
    q95_q5, nperm5 = q95_exact_perm(s1["verdict"]["res"], s2v["verdict"]["res"])
    q95_q3, nperm8 = q95_exact_perm(s1q3["verdict"]["res"],
                                    s2q3["verdict"]["res"])

    sess = json.load(open(SESSIONS_OUT))
    brows = list(sess["b_session_residuen"]["q5_rows"]) \
        + list(sess["b_session_residuen"]["q3_rows"])
    rho_pooled = spearman([r["s1"] for r in brows], [r["s2"] for r in brows])

    out["c1_criteria"] = {
        "P_gleich_beiden_sessions": same_P,
        "c_p_identisch_s1_s2": c_ident,
        "rho_S1_S2_q5_verdict": rho_q5_s1s2,
        "rho_S1_S2_q3_verdict": rho_q3_s1s2,
        "rho_S1_S2_pooled_13": rho_pooled,
        "pooled_pin_0.8956_bit": abs(rho_pooled
                                     - 0.8956043956043955) < 1e-12,
        # n=5-SCHWAECHE registriert: eine TRUE-Session-Replication erreicht
        # nur rho 0.5 (80-Perzentil-Klasse beim Permutations-Null) — ein
        # q95-Massstab (0.8) wuerde sogar die reine S2-Replication FAILEN
        # lassen. Registrierter C1-Massstab = ANKER-PARITAET (>= beobachtet
        # S1→S2); der q95-exakte Null bleibt SEKUNDAERER Deskriptiv-Benchmark.
        "q95_exact_perm_q5_sekundaer": q95_q5,
        "n_perm_q5": nperm5,
        "q95_exact_perm_q3_sekundaer": q95_q3,
        "n_perm_q3": nperm8,
        "kriterium_C1_q5": "rho(res'_q5-verdict, res_S1_q5-verdict) >= Anchor "
                           "S1→S2 (0.5-Klasse)",
        "kriterium_C1_q3": "rho(res'_q3-verdict, res_S1_q3-verdict) >= Anchor "
                           "S1→S2 (0.8095-Klasse)",
    }

    out["c2_criteria"] = {
        "q5_core_S2": s2v["verdict"]["below_sharp"],
        "kriterium_q5_core": "BOTH {467,673} unter Session 5 (2/2)",
        "q5_second_S1": s1["verdict"]["below_sharp"],
        "kriterium_q5_second": "mindestens 2/3 von {467,547,673}",
        "q3_classes": [],
        "kriterium_q3": "n/a (beide Sessions klassenleer)",
        "w_band": W_B_DP,
    }

    out["s1_anchors"] = {
        "q5_verdict": s1["verdict"], "q3_verdict": s1q3["verdict"],
        "q5_cal_kappa": s1["cal"]["kappa"], "q5_cal_c_p": s1["cal"]["c_p"],
    }
    out["s2_anchors"] = {
        "q5_verdict": s2v["verdict"], "q3_verdict": s2q3["verdict"],
    }

    # ---------------------------------------------------------------
    # 6) D.5-Preview: zwei SE-Konventionen an den committeten Reihen
    # ---------------------------------------------------------------
    # (a) committete (F)-Konvention OLS-mit-Achsenabschnitt (gepinnt);
    f_q5 = sess["f_gamma_power"]["q5_d5"]
    f_q3 = sess["f_gamma_power"]["q3_d3"]
    # (b) no-intercept-SE gamma = <c,Delta>/<c,c>, SE = sqrt(s^2/Summen c^2)
    s1gamma = json.load(open(S1))["gamma_arm"]["q5_d5"]
    rows_cal = s1gamma["rows"]
    cps = np.array([r["c_p"] for r in rows_cal])
    dls = np.array([r["delta_cal"] for r in rows_cal])
    gam = float(cps @ dls) / float(cps @ cps)
    res_scatter = dls - gam * cps
    s2_res = float(res_scatter @ res_scatter) / (len(cps) - 1)
    se_no_int = float(np.sqrt(s2_res / float(cps @ cps)))

    d5_preview = {
        "F_OLS_q5_committed": {k: f_q5.get(k) for k in
                               ("gamma_committed", "gamma_ols", "se_gamma",
                                "resid_sd", "n")},
        "F_OLS_q3_committed": {k: f_q3.get(k) for k in
                               ("gamma_committed", "gamma_ols", "se_gamma",
                                "resid_sd", "n")},
        "no_intercept_gamma_S1_q5_cal": gam,
        "no_intercept_se_gamma_S1_q5": se_no_int,
        "se_gamma_times_mean_c_p_S1": se_no_int * float(np.mean(cps)),
        # PROVENANCE: SE_no_int * c̄ = 0.011976 ≈ Deck "SE(γ)*c_p ≈ 0.011" —
        # die D.5-Zahl ist die Durch-Null-LSQ-SE (nicht die (F)-OLS-SE 0.1254)
        "provenance_0.011": "D.5-SE = no-intercept-LSQ-SE * c̄",
        "kappa_S1_q5_cal_min": min(s1["cal"]["kappa"]),
        "void_gate_ex_ante_kappa_ok": min(s1["cal"]["kappa"]) >= KAPPA_CEILING,
        # Registrierte Erwartung fuer den Refit an n=16 (5 + 11):
        "erwartung_sqrt_skalierung": se_no_int * float(np.sqrt(5.0 / 16.0)),
        # Literale Deck-F-Zeile-8-Falsifikatorlinie (resid_sd < 0.01):
        "falsifikatorlinie": "resid_sd(q5, OLS-mit-Achsenabschnitt, ddof=2, "
                             "n=16 Kalibrier-Reihen) < 0.01, sonst BLEIBT "
                             "SA-H9-5 (Kalibrier-Streuung = Band-Groesse)",
        "expected_decomposition": "wenn SE sqrt(n)-schrumpft: SE(γ')*c_p "
                                  "= 0.011-Klasse/√16 -> ~0.006",
    }
    out["d5_preview"] = d5_preview

    # ---------------------------------------------------------------
    # 7) C.1-C-Vorprobe OFFLINE (descriptiv, KEIN Verdict-Role)
    # ---------------------------------------------------------------
    def perm_null_vs_c(res_vec, c_vec):
        q95, npm = q95_exact_perm(res_vec, c_vec)
        rho_obs = spearman(res_vec, c_vec)
        return {"rho_obs": rho_obs, "q95_null": q95, "n_perm": npm,
                "obs_le_q95": rho_obs <= q95}

    c_probe = {
        "q5": perm_null_vs_c(s1["verdict"]["res"], s1["verdict"]["c_p"]),
        "q5_pool_S1S2": None,   # registriert am gepoolten, session-zentrierten
        "q3": perm_null_vs_c(s1q3["verdict"]["res"], s1q3["verdict"]["c_p"]),
        "rolle": "DESKRIPTIV registriert — kein Verdict-Kriterium",
    }
    out["c1_c_vorprobe"] = c_probe

    # ---------------------------------------------------------------
    # 8) Perturbations-/Gate-Regeln (Text-Registrierung)
    # ---------------------------------------------------------------
    out["registratur"] = {
        "perturbation": "FORCED initial_layout je Circuit (KEIN Seed-Wechsel, "
                        "transpiler seed 7 UNVERAENDERT); Reihen pro Arm nach "
                        "(set, P) sortiert [verdict aufsteigend, dann cal-alt, "
                        "dann Ladder-Reihenfolge], Slots = lexicographische "
                        "Enumeration verbundener induzierter Subgraphen der "
                        "LIVE-Kopplungsmap (Groesse 2 = Kanten/q3, Groesse 3 = "
                        "3-Knoten-Pfade/q5), Zuordnung = zyklischer Shift "
                        "(Reihe i -> Slot i+1 mod n_rows_arm); Fall-Back bei "
                        "Ceiling: Skip-forward, im Report dokumentiert; c' aus "
                        "dem VOR Messung committeten ISA-Report (C3 unberührt).",
        "unforced_subset": "Echo-Leiter (6) + negative Kontrollen (4) + "
                           "readout_cal (2) = 12 Circuits unter Auto-Layout "
                           "seed 7 — per-Circuit-2q BITGLEICH gegen "
                           "pt_ram_q_isa3_report.json (Gate-Assertion). "
                           "Damit ist die fez-scoped FPrio-5-Lesart (b) "
                           "MESSBAR (gleiche Geometrie wie S1/S2).",
        "gate_form": "PTZ-Gate ohne bit-Vorgänger (K2-Präzedenz: "
                     "per_circuit_two_q + isa_ceiling + ceiling_check-Verdict)",
        "echo_ladder": "identisch 11b/047 (Anker 181/467, repeats [1,2,4,8], "
                       "r1 geteilt, Barriers) — NICHT verdict-tragend; "
                       "FPrio-5-Lesart (b) auf DIESEM Job = DESCRIPTIV.",
        "voids": {
            "REFIT_INVALID_KAPPA": "kappa_hat < 0.81 an >= 2 der Union-Reihen "
                                   "-> gamma-Refit invalid (descriptiv-void)",
            "EVALUATION_INVALID_KONTROLLE_GESCHEITERT": "geerbte Kontrollen "
                                                        "verletzt",
        },
        "verdict_map": {
            "P_BOUND_TRANSFER_HELD": "C1 beide Arme >= S1→S2-Anchor UND C2 "
                                     "UND kein C3-Feuer (rho(Delta-res, "
                                     "Delta-c) < q95-exakt je Arm)",
            "GEOMETRYBOUND_D7": "C1 q5 unter Anchor UND C3 q5 feuert "
                                "(>= q95-exakt) — D.7 gewinnt die Runde, "
                                "auf Session-3-Ebene dokumentiert; "
                                "H-RAM-Q-4 bleibt REFUTED",
            "MIXED_PARTIAL": "Teilweise (mindestens ein Transfer-Arm gehalten, "
                             "keine klare Konstellation)",
            "UNDETERMINED": "Datenlage unklar (keine der Konstellationen)",
        },
        "f_prio_4": "P-Vektor-Transfer C.1: die Rang-/Klassen-Struktur der "
                    "S1-Falsifikatoren folgt dem Session-P-Vektor, NICHT "
                    "einer Geometrie-Neuordnung.",
        "f_prio_8": "n_cal(q5) >= 16 via 11 neuer P (Phase-11b-Regel); "
                    "Refit gamma'_q5 law-konsistent; DECOMPOSITION entscheidet "
                    "SA-H9-5 über die Deck-F-Zeile-8-Grenze.",
        "experiment_nummer": 55,
        "reserved": "EXPERIMENT 054 = GOE-Angebot (angeboten, NICHT ausgeführt)",
        "integritaet": {"qpu_jobs_now": 0, "verdict_re_decide": False,
                        "prereg_freezes_beruehrt": False},
    }

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)

    print("== FPrio-4+8 Design (EXP 055, 0 QPU) ==")
    print("Union:", len(union40), "| subset-11b ok:",
          out["union"]["subset_11b_MEASURED_UNION"])
    print("Ladder:", ladder, "| n_cal_q5:", out["ladder"]["n_cal_q5_total"])
    print("d-Invarianz:", d_inv_ok)
    print("Budget:", total, "circuits =", total * S_SHOTS, "shots")
    print("rho S1S2 q5/q3:", rho_q5_s1s2, rho_q3_s1s2)
    print("q95 exact-perm q5/q3:", q95_q5, "(", nperm5, ")",
          q95_q3, "(", nperm8, ")")
    print("SE no-int (S1 q5 cal):", se_no_int, "| SE*c:", d5_preview[
        "se_gamma_times_mean_c_p_S1"])
    print("sqrt-Erwartung n=16:", d5_preview["erwartung_sqrt_skalierung"])
    print("geschrieben:", OUT)


if __name__ == "__main__":
    main()