# -*- coding: utf-8 -*-
"""H-RAM-Q-3 Hardware-Auswertung (EXPERIMENT 042): gefrorene verdict_map.

Liest AUSSCHLIESSLICH das committete Raw-Dokument (pt_ram_q_hardware_raw.json;
Raw-Commit VOR dieser Auswertung — job_integrity: "Job-ID + md5 der Counts
committed VOR der Auswertung") und das gefrorene Prereg (md5 432d43fe).
KEIN QPU-Kontakt, KEINE neuen Register: die Auswertung wendet nur die
gefrorene Estimator-Kette (operational_definitions) auf die committeden
Counts an — identisch zum Aer-Sampled-Bein (pt_ram_q_hardware_aer).

Estimator-Kette:
  n_hat_a = m*c_a/S (rational) -> fold_d (Wraparound) -> ABSOLUT-FFT-Share
  ratio_hw = share/model_share_reg; Punkt-Wert = Mittel ueber die 3 Reps
  kappa_hat = P_L/P_ro_ref (gepaarte Loschmidt-/Readout-Cal-Counts, EIN Job)
  Zentrum (GEFROREN, safeguard band_rule):
    c(kappa_hat) = kappa_hat*(1-1/S)*ratio_true + L_q
  Band: w_B aus pt_ram_q_stage2_results.json (Freeze B, 0.0248574...),
        grob w_A = 0.05 (Freeze A).

Verdikt-Praezedenz (die Map selbst gibt keine Reihenfolge an; dokumentiert
in §Z.24): T4 verletzt -> DEGENERAT; sonstige Kontrollen (T3/T5/T6, md5)
gescheitert -> EVALUATION_INVALID; >= 2 Punkte kappa_hat < 0.81 ->
VOID_CALIBRATION; Punkt ueber Ceiling c(1)+w -> INVALID_AMPLIFICATION;
>= 2 unter c-w -> REFUTED; alle 13 im scharfen Band + alle kappa >= 0.81
-> NOISE_LIFT_CONFIRMED; alle im groben Band, >= 1 ausserhalb w_B ->
COARSE_HOLD_SHARP_MISS; sonst VERDICT_MAP_UNMATCHED (ehrlicher
Nicht-Treffer-Zweig — KEIN erfundener Verdict, die Map kennt keinen).

T1/T2 sind Offline-Kontrollen und laufen im committeten Test-Suite-Bein
(TestCommittedResults / TestAbsolutFFTShare); dieses Modul dokumentiert die
Vererbung, statt sie zu behaupten.

Bekannte Spannung der gefrorenen Texte (in §Z.24 dokumentiert, NICHT
aufgeloest): kappa_floor_void sagt "Punkt EXKLUDIERT" (einzeln), waehrend
die verdict_map fuer CONFIRMED/REFUTED ueber "alle 13" / ">= 2 der 13"
zaehlt.  Primaer gilt die woertliche verdict_map (Anti-Sharpshooter: keine
Interpretations-Latte zur Laufzeit); die Exklusions-Lesart wird als
alternative_lesart_exklusion mitgerechnet und bei Divergenz ausgewiesen.
"""
import json

import numpy as np

import pt_ram_q_hardware as hw
import pt_ram_q_hardware_aer as aer
import pt_ram_q_hardware_qpu as qpu

RAW_PATH = qpu.RAW_PATH
STAGE2_PATH = aer.RESULTS_PATH
ISA_PATH = aer.ISA_PATH
EVAL_PATH = "pt_ram_q_hardware_eval.json"

T3_TOL = 1e-12
T6_MASS_TOL = 1e-9

V_CONFIRMED = "H-RAM-Q-3_NOISE_LIFT_CONFIRMED"
V_COARSE = "H-RAM-Q-3_COARSE_HOLD_SHARP_MISS"
V_REFUTED = "H-RAM-Q-3_REFUTED"
V_AMPL = "H-RAM-Q-3_INVALID_AMPLIFICATION"
V_VOID = "H-RAM-Q-3_VOID_CALIBRATION"
V_DEGENERAT = "H-RAM-Q-3_DEGENERAT"
V_INVALID = "EVALUATION_INVALID_KONTROLLE_GESCHEITERT"
V_UNMATCHED = "VERDICT_MAP_UNMATCHED"


def load_w_b(stage2_path=STAGE2_PATH):
    """w_B aus dem committeten Freeze-B-Stage-2-Resultat (keine Konstante)."""
    with open(stage2_path, encoding="utf-8") as fh:
        return float(json.load(fh)["w_b"])


def decide_verdict(*, t4_violated, t_fail_other, n_kappa_low, n_above_ceiling,
                   n_below_sharp, n_in_sharp, all_in_coarse, n_points):
    """Gefrorene verdict_map mit dokumentierter Praezedenz (§Z.24)."""
    if t4_violated:
        return V_DEGENERAT
    if t_fail_other:
        return V_INVALID
    if n_kappa_low >= 2:
        return V_VOID
    if n_above_ceiling >= 1:
        return V_AMPL
    if n_below_sharp >= 2:
        return V_REFUTED
    if n_in_sharp == n_points and n_kappa_low == 0:
        return V_CONFIRMED
    if all_in_coarse and (n_points - n_in_sharp) >= 1:
        return V_COARSE
    return V_UNMATCHED


def _folded_share(n_hat, pt):
    """Zweiter Weg der t3-Identitaet: gefaltete Form (041-Theorem)."""
    N = hw.fold_mod_q(list(n_hat), pt["d"], pt["q"])
    return aer.share_hw_folded(N, pt["q"], pt["d"], pt["m"])


def evaluate(raw_path=RAW_PATH, stage2_path=STAGE2_PATH, isa_path=ISA_PATH):
    raw = json.load(open(raw_path, encoding="utf-8"))
    with open(stage2_path, encoding="utf-8") as fh:
        stage2 = json.load(fh)
    with open(isa_path, encoding="utf-8") as fh:
        isa = json.load(fh)
    prereg = hw.load_frozen_prereg()
    w_b = load_w_b(stage2_path)
    w_a = aer.W_A
    pts = aer._point_pts()
    cs_by_name = {c["name"]: c for c in aer.build_hardware_circuit_set()}
    raw_by_name = {e["name"]: e for e in raw["counts"]}

    # --- job_integrity: md5 der committeden Counts ---
    md5_ok = (qpu.counts_md5([e["counts"] for e in raw["counts"]])
              == raw["counts_md5"])

    # --- t3 (zwei Wege) + t6 (Shots/Masse) ueber alle State-Circuits ---
    t3_dev = 0.0
    t6_shots_ok = True
    t6_mass_dev = 0.0
    for e in raw["counts"]:
        if e["shots_actual"] != hw.SHOTS:
            t6_shots_ok = False
        if e["kind"] not in ("structure", "negative_control"):
            continue
        pt = pts[(e["arm"], e["P"])]
        rc = aer.ratio_from_counts(e["counts"], pt, aer.NQ_BY_ARM[e["arm"]])
        t3_dev = max(t3_dev, abs(rc["share"] - _folded_share(rc["n_hat"], pt)))
        t6_mass_dev = max(t6_mass_dev, abs(rc["m_hat"] - pt["m"]))
    t3_ok = t3_dev <= T3_TOL
    t6_ok = t6_shots_ok and t6_mass_dev <= T6_MASS_TOL

    # --- t4: Negativ-Kontrollen gegen die registrierte Kante (kappa=1-Maximum,
    #     Freeze-A-Vorab-Registrierung); Exact-kappa_hat-Variante als Diagnostik
    controls = {}
    t4_ok = True
    for name, c in cs_by_name.items():
        if c["kind"] != "negative_control":
            continue
        e = raw_by_name[name]
        pt_ref = pts[(c["arm"], c["P"])]
        nq = aer.NQ_BY_ARM[c["arm"]]
        share = aer.ratio_from_counts(e["counts"], pt_ref, nq)["share"]
        edge = c["lower_prime_band_edge"]
        ok = share < edge
        t4_ok = t4_ok and ok
        controls[name] = {
            "measured_share": share,
            "expected_share": c["expected_share"],
            "lower_prime_band_edge": edge,
            "ok": ok,
        }

    # --- t5: Gate-Set gefroren + Transpile-Record == ISA-Report ---
    point_set_raw = {(e["arm"], e["P"]) for e in raw["counts"]
                     if e["kind"] == "structure"}
    point_set_frozen = {(arm, p["P"]) for arm in ("q3_d9", "q5_d25")
                        for p in prereg["prediction_freeze"]["points"][arm]}
    transpile_ok = (
        raw["transpile"]["optimization_level"] == isa["optimization_level"]
        and raw["transpile"]["seed_transpiler"] == isa["transpile_seed"]
        and raw["transpile"]["isa_2q_total"] == isa["total_two_q"]
        and raw["transpile"]["isa_2q_max"] == isa["max_two_q"]
        and isa["verdict"] == "ISA_OK")
    run_config_ok = (raw["registered_run_config"]
                     == prereg["hardware_parameters"]["run_config"])
    t5_ok = (point_set_raw == point_set_frozen and transpile_ok
             and run_config_ok and raw["n_circuits"] == 58
             and len(raw["counts"]) == 58)

    t_fail_other = not (md5_ok and t3_ok and t5_ok and t6_ok)

    # --- Punkte: 3 Reps -> ratio_hw; kappa_hat = P_L/P_ro_ref ---
    points = {}
    for arm in ("q3_d9", "q5_d25"):
        nq = aer.NQ_BY_ARM[arm]
        cal = raw_by_name.get(f"cal_{nq}q")
        p_ro = aer.p0_fraction(cal["counts"], nq) if cal else 0.0
        for key in sorted(k for k in pts if k[0] == arm):
            pt = pts[key]
            P = pt["P"]
            ratios, missing = [], []
            for r in range(hw.K_REPEATS):
                e = raw_by_name.get(f"struct_{arm}_{P}_r{r}")
                if e is None:
                    missing.append(r)
                    continue
                ratios.append(aer.ratio_from_counts(
                    e["counts"], pt, nq)["ratio"])
            ratio = float(np.mean(ratios)) if ratios else None
            los = raw_by_name.get(f"loschmidt_{arm}_{P}")
            p_l = aer.p0_fraction(los["counts"], nq) if los else 0.0
            kappa = p_l / p_ro if p_ro > 0 else None
            c1 = aer.center_v1(kappa, pt) if kappa is not None else None
            c1max = aer.center_v1(1.0, pt)
            res = ratio - c1 if (ratio is not None and c1 is not None) else None
            kappa_ok = kappa is not None and kappa >= hw.KAPPA_CEILING
            rec = {
                "P": P, "nq": nq, "m": pt["m"],
                "ratio_hw": ratio, "ratio_reps": ratios,
                "ratio_std": (float(np.std(ratios)) if ratios else None),
                "missing_reps": missing,
                "P_L": p_l, "P_ro_ref": p_ro, "kappa_hat": kappa,
                "center_v1": c1, "res_sharp": res,
                "in_band_sharp": (abs(res) <= w_b) if res is not None else None,
                "in_band_coarse": (abs(res) <= w_a) if res is not None else None,
                "below_sharp": (ratio < c1 - w_b)
                if (ratio is not None and c1 is not None) else None,
                "below_coarse": (ratio < c1 - w_a)
                if (ratio is not None and c1 is not None) else None,
                "above_sharp": (ratio > c1 + w_b)
                if (ratio is not None and c1 is not None) else None,
                "ceiling_c1max": c1max,
                "above_ceiling_w_b": (ratio > c1max + w_b)
                if ratio is not None else None,
                "above_ceiling_w_a": (ratio > c1max + w_a)
                if ratio is not None else None,
                "kappa_ok": kappa_ok,
            }
            # Diagnostik (NICHT verdict-tragend): gesetzliche v2-Form mit den
            # committeten Aer-b_P und gemessenem ro_hat.
            bp = stage2["b_p"].get(f"{arm}|{P}")
            ro_hat = 1.0 - p_ro ** (1.0 / nq) if p_ro > 0 else None
            c2 = (aer.center_v2(kappa, pt, ro_hat, bp)
                  if (kappa is not None and bp is not None) else None)
            rec["diagnostisch_v2"] = {
                "nicht_verdict_tragend": True, "b_p_aer": bp,
                "ro_hat": ro_hat, "center_v2": c2,
                "res_v2": (ratio - c2)
                if (ratio is not None and c2 is not None) else None,
            }
            points[f"{arm}|{P}"] = rec

    vals = [v for v in points.values() if v["ratio_hw"] is not None]
    n_kappa_low = sum(1 for v in vals if not v["kappa_ok"])
    n_below_sharp = sum(1 for v in vals if v["below_sharp"])
    n_above_ceiling = sum(1 for v in vals if v["above_ceiling_w_b"])
    n_in_sharp = sum(1 for v in vals if v["in_band_sharp"])
    all_in_coarse = (len(vals) == len(points)
                     and all(v["in_band_coarse"] for v in vals))
    verdict_inputs = {
        "n_points": len(points), "n_evaluated": len(vals),
        "n_kappa_low": n_kappa_low, "n_below_sharp": n_below_sharp,
        "n_above_ceiling_w_b": n_above_ceiling, "n_in_sharp": n_in_sharp,
        "n_outside_sharp": len(vals) - n_in_sharp,
        "all_in_coarse_w_a": all_in_coarse,
        "n_below_coarse_w_a": sum(1 for v in vals if v["below_coarse"]),
    }
    verdict = decide_verdict(
        t4_violated=not t4_ok, t_fail_other=t_fail_other,
        n_kappa_low=n_kappa_low, n_above_ceiling=n_above_ceiling,
        n_below_sharp=n_below_sharp, n_in_sharp=n_in_sharp,
        all_in_coarse=all_in_coarse, n_points=len(points))

    # --- alternative Lesarten (dokumentiert, nicht verdict-ersetzend) ---
    alt = {
        "refuted_mit_w_a": {
            "n_below_coarse_w_a": verdict_inputs["n_below_coarse_w_a"],
            "verdict_waere": V_REFUTED
            if verdict_inputs["n_below_coarse_w_a"] >= 2 else None,
        },
        "amplification_mit_w_a": {
            "n_above_ceiling_w_a": sum(1 for v in vals
                                       if v["above_ceiling_w_a"]),
        },
        "exklusion": None,
    }
    if (verdict not in (V_DEGENERAT, V_INVALID, V_VOID)
            and n_kappa_low == 1 and len(vals) == len(points)):
        # kappa_floor_void-Lesart: der eine Punkt ist EXKLUDIERT; Band-Verdict
        # ueber die 12 verbleibenden Punkte (alle mit kappa >= 0.81).
        inc = [v for v in vals if v["kappa_ok"]]
        alt["exklusion"] = {
            "n_points": len(inc),
            "verdict_waere": decide_verdict(
                t4_violated=False, t_fail_other=False, n_kappa_low=0,
                n_above_ceiling=sum(1 for v in inc if v["above_ceiling_w_b"]),
                n_below_sharp=sum(1 for v in inc if v["below_sharp"]),
                n_in_sharp=sum(1 for v in inc if v["in_band_sharp"]),
                all_in_coarse=all(v["in_band_coarse"] for v in inc),
                n_points=len(inc)),
        }

    vmap = prereg["verdict_map"]
    doc = {
        "experiment": hw.EXPERIMENT,
        "hypothesis": hw.HYPOTHESIS,
        "status": "EVALUATED",
        "raw_backend": raw.get("backend"),
        "raw_job_meta": raw.get("job_meta"),
        "raw_counts_md5": raw.get("counts_md5"),
        "counts_md5_verified": md5_ok,
        "w_b": w_b, "w_a": w_a,
        "w_b_source": {"path": stage2_path,
                       "registered": "Freeze B (Domain-q97.5, unclipped Gate)"},
        "kappa_ceiling": hw.KAPPA_CEILING,
        "kontrollen": {
            "t1_backcompat": "inherited (committetes Offline-Suite-Bein: "
                             "TestCommittedResults)",
            "t2_v2_anchors": "inherited (committetes Offline-Suite-Bein: "
                             "TestCommittedResults/ANCHOR_PIN)",
            "t3_identity_two_ways": {"ok": t3_ok, "max_dev": t3_dev,
                                     "tol": T3_TOL},
            "t4_negative_must_not_fire": {"ok": t4_ok, "controls": controls,
                                          "edge_konvention": "registrierte "
                                          "Freeze-A-Kante (kappa=1-Maximum, "
                                          "konservativ fuer must-not-fire)"},
            "t5_gate_set_frozen": {"ok": t5_ok,
                                   "point_set_ok":
                                       point_set_raw == point_set_frozen,
                                   "transpile_ok": transpile_ok,
                                   "run_config_ok": run_config_ok},
            "t6_mass_conservation": {"ok": t6_ok, "shots_ok": t6_shots_ok,
                                     "max_mass_dev": t6_mass_dev},
        },
        "punkte": points,
        "verdict_inputs": verdict_inputs,
        "verdict": verdict,
        "verdict_map_text": vmap.get(verdict,
                                     "kein Treffer der gefrorenen Map — "
                                     "ehrlicher Nicht-Treffer-Zweig (kein "
                                     "erfundener Verdict)"),
        "alternative_lesarten": alt,
    }
    return doc


def write_eval(doc, path=EVAL_PATH):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    return path


if __name__ == "__main__":
    ev = evaluate()
    write_eval(ev)
    print(f"verdict: {ev['verdict']}")
    vi = ev["verdict_inputs"]
    print(f"inputs: {vi}")
    print(f"kontrollen: t3 {ev['kontrollen']['t3_identity_two_ways']['ok']}, "
          f"t4 {ev['kontrollen']['t4_negative_must_not_fire']['ok']}, "
          f"t5 {ev['kontrollen']['t5_gate_set_frozen']['ok']}, "
          f"t6 {ev['kontrollen']['t6_mass_conservation']['ok']}, "
          f"md5 {ev['counts_md5_verified']}")
    for k, v in ev["punkte"].items():
        print(f"{k}: ratio {v['ratio_hw']:.4f} kappa {v['kappa_hat']:.4f} "
              f"c {v['center_v1']:.4f} res {v['res_sharp']:+.4f} "
              f"sharp {v['in_band_sharp']}")