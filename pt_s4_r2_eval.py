# -*- coding: utf-8 -*-
"""EXPERIMENT 052, gefrorene Auswertung: die offizielle EINSTUFUNG
der einzigen 045-T5-Verletzung (H-S4CLOSURE-R2).

Liest NUR committete Artefakte (gefruenes Prereg, gefrorene Roh-Messung
pt_s4_r2_results.json, 045-Erste-Messung, committeter Scratch) und
schreibt pt_s4_r2_eval.json — die entscheidende Funktion decide() ist
die ex-ante-Registrierung des Preregs (kein Bedingungs-Re-Write im
Licht der Messung).  Kein Re-Decide: das committete 045-Verdict
H_S4_CLOSURE_DEVIATION_FOUND bleibt unberührt; diese Datei ist die
EINSTUFUNGS-Tabelle, nicht ein Verdict-Ersatz.

Vertrags-Gate: das Roh darf KEINE Verdict-/Einstufungs-Felder tragen;
die Konsistenz re-derivier die Medians/Maxima bit-exakt aus den
Roh-Arrays (Integrität), Bit-Pins gegen 045/Scratch sind DISKLOSURE
(049b-Lektion — cross-build ULP-Delta, NICHT Gate).
"""
import hashlib
import json
import platform
import time

import numpy as np

import pt_s4_r2_recompute as rc

VERDICT_DEGENERAT = "DEGENERAT"
VERDICT_RECOMPUTE_UNABLE = "RECOMPUTE_UNABLE"
VERDICT_QUELLEN_ARTEFAKT = "H_S4CLOSURE_R2_QUELLEN_ARTEFAKT"
VERDICT_STRUKTURELL_REST = "H_S4CLOSURE_R2_STRUKTURELL_REST"

RAW_FORBIDDEN_KEYS = ("verdict", "verdict_class", "einstufung",
                      "einstufung_045", "unified_unter_tol",
                      "inst_reproduziert")


def decide(crit, sum_tol):
    """Zentrale ex-ante-Bedingung (registriert im Prereg verdict_map).

    crit: structural_ok, basis_ok, konsistenz_ok (bool); l1_native_max,
    l1_class_r_median_adjacent, l2_full_adj, l2_full_dis, l2_bahn_adj,
    l2_bahn_dis (float).  Boundary strikt: '>'-Seite faellt bei
    Gleichheit, '<'-Seite faellt bei Gleichheit (Prereg
    boundary_semantics)."""
    if not (crit["structural_ok"] and crit["basis_ok"]
            and crit["konsistenz_ok"]):
        return VERDICT_DEGENERAT
    l1_ok = (crit["l1_native_max"] > sum_tol
             and crit["l1_class_r_median_adjacent"] > sum_tol)
    if not l1_ok:
        return VERDICT_RECOMPUTE_UNABLE
    l2_bad = (crit["l2_full_adj"] >= sum_tol
              or crit["l2_full_dis"] >= sum_tol
              or crit["l2_bahn_adj"] >= sum_tol
              or crit["l2_bahn_dis"] >= sum_tol)
    return VERDICT_STRUKTURELL_REST if l2_bad else VERDICT_QUELLEN_ARTEFAKT


def bitpin(label, a, b):
    """Disclosure-Eintrag: Delta + Bit-Gleichheit (kein Gate)."""
    d = abs(float(a) - float(b))
    return {"was": label, "delta": d, "bit_gleich": bool(d == 0.0)}


def konsistenz_pruefen(raw, prereg):
    """Re-Derivation der Medians/Maxima aus den Roh-Arrays (Integrität)."""
    classes = rc.adjacency_classes()
    fails = []
    for arm, key in (("inst", "per_pattern_inst"),
                     ("unified", "per_pattern_unified")):
        med = {int(k): float(np.median([float(x) for x in v]))
               for k, v in raw[key].items()}
        fw = rc.full_within_maximum(med, classes)
        for cls in ("adjacent", "disjoint"):
            got = raw["full_within"][arm][cls]["max"]
            if fw[cls]["max"] != got:
                fails.append("%s.%s re-der %r != raw %r"
                             % (arm, cls, fw[cls]["max"], got))
            wp_re = fw[cls]["worst_pair"]
            wp_raw = raw["full_within"][arm][cls]["worst_pair"]
            if ((wp_re is None) != (wp_raw is None)) or (
                    wp_re is not None and list(wp_re) != list(wp_raw)):
                fails.append("%s.%s worst_pair re-der %s != raw %s"
                             % (arm, cls, wp_re, wp_raw))
        for v in raw["vergleiche"]:
            a, b = v["pair"]
            d = abs(med[a] - med[b])
            ref = v["d_inst" if arm == "inst" else "d_unified"]
            if d != ref:
                fails.append("bahn %s/%s re-der %r != raw %r"
                             % (arm, v["bahn"], d, ref))
    structural_native = raw["native_t5_t6"]
    for key, want in prereg["criteria"]["l1_reproduktion"][
            "structural"].items():
        if key == "k_class_sizes":     # Prereg-Konstante (live classes),
            continue                   # kein natives Roh-Feld
        got = structural_native.get(key)
        if got != want:
            fails.append("native structural %s = %r != Prereg %r"
                         % (key, got, want))
    return {"ok": not fails, "fails": fails}


def make_disclosure(raw, prereg, crit):
    """Bit-Pins gegen die committeten Basis-Artefakte (kein Gate)."""
    res045 = rc.load_json_dict(prereg["basis"]["results_045"]["path"])
    scr = rc.load_json_dict(prereg["basis"]["scratch_unified"]["path"])
    t5 = res045["t5_t6_familien_summen"]
    pp = {int(k): v for k, v in t5["per_pattern"].items()}
    native = raw["native_t5_t6"]
    classes = rc.adjacency_classes()

    def med_of(source):
        return {int(k): float(np.median(v)) for k, v in source.items()}

    full_uni = rc.full_within_maximum(
        med_of(raw["per_pattern_unified"]), classes)
    full_inst = rc.full_within_maximum(
        med_of(raw["per_pattern_inst"]), classes)
    scr_full_uni = rc.full_within_maximum(
        med_of(scr["per_pattern_unified"]), classes)
    scr_full_inst = rc.full_within_maximum(
        med_of(scr["per_pattern_inst"]), classes)
    return {
        "native_vs_045": [
            bitpin("max_within_orbit_dev",
                   native["max_within_orbit_dev"],
                   t5["max_within_orbit_dev"]),
            bitpin("between_orbit_R_gap",
                   native["between_orbit_R_gap"],
                   t5["between_orbit_R_gap"]),
        ] + [bitpin("r_median p%d" % i,
                    native["per_pattern"][str(i)]["r_median"],
                    pp[i]["r_median"]) for i in (0, 6, 10)],
        "unified_vs_scratch": [
            bitpin("full_within adj", full_uni["adjacent"]["max"],
                   scr_full_uni["adjacent"]["max"]),
            bitpin("bahn d_uni adj", crit["l2_bahn_adj"],
                   next(float(v["d_unified"]) for v in scr["vergleiche"]
                        if v["bahn"] == "adjacent")),
            bitpin("inst full_within adj", full_inst["adjacent"]["max"],
                   scr_full_inst["adjacent"]["max"]),
        ],
        "build_caveat": (
            "049b-Lektion: Bit-Pins sind DISKLOSURE, nicht Gate — "
            "cross-build ULP-Delta moeglich; interpreter/numpy je "
            "Raw-Metadaten aufgezeichnet"),
    }


def main(results_path=None, eval_path=None, verbose=True):
    t0 = time.time()
    prereg = rc.load_frozen_prereg()
    results_path = results_path or rc.RESULTS_PATH
    eval_path = eval_path or rc.EVAL_PATH
    sum_tol = prereg["konstanten"]["sum_tol"]
    assert sum_tol == rc.SUM_TOL == 1e-9

    raw = json.load(open(results_path, encoding="utf-8"))
    bad = [k for k in raw if k in RAW_FORBIDDEN_KEYS]
    basis_fails, kons_fails = [], []
    if bad:
        basis_fails.append("Roh-Vertrag verletzt: %s" % bad)
    else:
        if raw.get("experiment") != rc.EXPERIMENT:
            basis_fails.append("Roh-experiment %r != %r"
                               % (raw.get("experiment"), rc.EXPERIMENT))
        if raw.get("prereg_md5") != rc.self_md5():
            basis_fails.append("Roh-prereg_md5 != gefrorenes Prereg")
        # Basis-md5s (045-Erste-Messung + committeter Scratch + Code)
        for key in ("results_045", "scratch_unified"):
            entry = prereg["basis"][key]
            got = rc.md5_of(entry["path"])
            if got != entry["md5"]:
                basis_fails.append("Basis-md5 %s: %s != %s"
                                   % (key, got, entry["md5"]))
        for path, want in prereg["basis"]["code"].items():
            got = rc.md5_of(path)
            if got != want:
                basis_fails.append("Code-md5 %s: %s != %s"
                                   % (path, got, want))
    basis_ok = not basis_fails
    if basis_ok:
        try:
            kons_check = konsistenz_pruefen(raw, prereg)
            kons_fails = kons_check["fails"]
        except Exception as exc:                       # noqa: BLE001
            kons_fails.append("Re-Derivation fehlgeschlagen: %r" % (exc,))
    kons = {"ok": not kons_fails, "fails": kons_fails}

    crit, verdict = None, None
    star = None
    try:
        if not basis_ok or not kons["ok"]:
            raise ValueError("Basis/Konsistenz verletzt — DEGENERAT-Pfad")
        native = raw["native_t5_t6"]
        star = rc.native_star_arm_maxima(
            {int(k): v for k, v in native["per_pattern"].items()})
        classes = rc.adjacency_classes()
        struct = prereg["criteria"]["l1_reproduktion"]["structural"]
        structural_ok = (
            all(native.get(k) == v for k, v in struct.items()
                if k not in ("k_class_sizes",))
            and {c: len(idxs) for c, idxs in classes.items()}
            == struct["k_class_sizes"])
        crit = {
            "structural_ok": bool(structural_ok),
            "basis_ok": True,
            "konsistenz_ok": True,
            "l1_native_max": float(native["max_within_orbit_dev"]),
            "l1_class_r_median_adjacent": float(
                star["adjacent"]["star_max"]["r_median"]["max"]),
            "l2_full_adj": float(raw["full_within"]["unified"]["adjacent"]
                                 ["max"]),
            "l2_full_dis": float(raw["full_within"]["unified"]["disjoint"]
                                 ["max"]),
            "l2_bahn_adj": float(next(v["d_unified"] for v in
                                      raw["vergleiche"]
                                      if v["bahn"] == "adjacent")),
            "l2_bahn_dis": float(next(v["d_unified"] for v in
                                      raw["vergleiche"]
                                      if v["bahn"] == "disjoint")),
        }
        verdict = decide(crit, sum_tol)
    except Exception as exc:                     # noqa: BLE001
        kons["fails"].append("Kriterien-Extraktion %r" % (exc,))
        crit = {
            "structural_ok": False, "basis_ok": bool(basis_ok),
            "konsistenz_ok": bool(kons["ok"]),
            "l1_native_max": float("nan"), "l1_class_r_median_adjacent":
            float("nan"), "l2_full_adj": float("nan"),
            "l2_full_dis": float("nan"), "l2_bahn_adj": float("nan"),
            "l2_bahn_dis": float("nan"),
        }
        verdict = decide(crit, sum_tol)
    vmap = {v["name"]: v for v in prereg["verdict_map"]}
    einstufung = vmap[verdict]["einstufung_045"]

    if crit["structural_ok"] and crit["konsistenz_ok"]:
        disclosure = make_disclosure(raw, prereg, crit)
    else:
        disclosure = {"note": "DEGENERAT-Pfad — Disclosure nicht aufgebaut"}

    doc = {
        "experiment": rc.EXPERIMENT,
        "hypothesis": rc.HYPOTHESIS,
        "qpu": 0,
        "prereg_md5": prereg["md5"],
        "verdict": verdict,
        "einstufung_045": einstufung,
        "verdict_ort": "pt_s4_r2_eval.json (Roh ohne Verdict-Felder — "
                       "Committ 045 UNBERÜHRT)",
        "criteria": crit,
        "sum_tol": sum_tol,
        "margin_ratios": {
            "l1_native_over_tol": crit["l1_native_max"] / sum_tol,
            "l2_full_adj_under_tol": sum_tol / crit["l2_full_adj"],
            "l2_full_dis_under_tol": sum_tol / crit["l2_full_dis"],
        },
        "star_arm_maxima": star,
        "konsistenz": kons,
        "disclosure": disclosure,
        "governance": {
            "kein_re_decide": True,
            "committed_045_verdict": prereg["governance"][
                "committed_045_verdict"],
            "toleranz": prereg["governance"]["toleranz"],
        },
        "raw_metadata": raw.get("metadata", {}),
        "eval_env": {"python": platform.python_version(),
                     "numpy": np.__version__,
                     "platform": platform.platform()},
        "seconds": round(time.time() - t0, 1),
    }
    if verbose:
        print("verdict: %s" % verdict)
        print("einstufung_045: %s" % einstufung)
        for k, v in crit.items():
            print("  %-28s %r" % (k, v))
        for b in disclosure["native_vs_045"] + disclosure["unified_vs_scratch"]:
            print("  pin %-22s bit_gleich=%s delta=%.3e"
                  % (b["was"], b["bit_gleich"], b["delta"]))
    with open(eval_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, default=float, ensure_ascii=False)
    return doc


if __name__ == "__main__":
    main()