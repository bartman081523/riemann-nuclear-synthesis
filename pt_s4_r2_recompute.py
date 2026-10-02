# -*- coding: utf-8 -*-
"""EXPERIMENT 052 (0 QPU, Re-Rechnungs-Artefakt): die offizielle
EINSTUFUNG der einzigen H_S4_CLOSURE_DEVIATION_FOUND-Verletzung aus
045 (T5 max_within_orbit_dev 1.0260516436488842e-08 > SUM_TOL 1e-9).

Das H9-Deck (HYPOTHESES_UND_ANTITHESES_H9_2026_09_29.md, F-Zeile 2)
fordert: "gefruenes Re-Rechnungs-Artefakt (0 QPU) fuer die offizielle
045-Einstufung — KEIN stilles Re-Decide".  Dieses Modul IS das
gefrueneste Artefakt dafuer:

  L1 (native Reproduktion): s4.check_t5_t6(cache) wörtlich neu mit dem
     leichten Cache s4.main (cache[cfg] = {"t_h": unfold_spectrum(cfg)[1]})
     — dieselbe Maschinerie, dieselbe Re-Quelle, derselbe Code.
  L2 (Quellen-Einheit): der unified-Arm des committeten Scratches
     (scratches/h9_s4_source_unified.py) — r_unified(cfg) =
     k_norm(evs, TAU2*t_cache[cfg]) / k_norm(evs, TAU1*t_cache[cfg]) auf
     den Muster-gefoldeten Eigenwerten; r_inst als Replik-Sanity.
  L2-SCHÄRFUNG ex ante (kein Bahn-Beschnitt): das Kriterium läuft auf
  dem VOLLSTÄNDIGEN within-Klassen-Paar-Grid (12er adjacent / 3er
  disjoint) statt nur der beiden registrierten BAHNEN-Paare — keine
  versteckten Ausnahmen im Einheits-Gesetz.  Aus den committeten
  Scratch-Medians ist bekannt (disclosed): full-adj 8.393228334568903e-10
  (Faktor ~1.19 unter TOL, worst pair (3,12) — KEIN BAHNEN-Paar), bahn
  6.423892529028308e-10; die schmalste Kante dieser Kette ist disclosed
  und ex ante vor-klassifiziert (Bedingungs-Flip = STRUKTURELL_REST).

NEU gegenüber dem Scratch (analytischer Zuwachs, aus committeten Daten
abgeleitet und im Prereg verankert): der Scratch-Flag
"inst_reproduziert: false" (Delta 1.12e-9 gegen 045) ist KEIN
Mess-Rauschen — es ist PAARUNGS-STRUKTUR: 045s native max_within ist
REPRÄSENTATIV-VERANKERt (repr der Orbit-Gruppe, hier Index 0) — worst
pair (0,6) auf r_median 1.026e-8; die vollständige Paarbildung liefert
(6,10) 1.1384355902421817e-08.  Beide > TOL (margins 10.3x / 11.4x).

GOVERNANCE: das committete 045-Verdict H_S4_CLOSURE_DEVIATION_FOUND
BLEIBT UNVERÄNDERT (historisch korrekt für seine Quell-Lesart).  Die
EINSTUFUNG ist ein SEPARATER registrierter Record; SUM_TOL 1e-9
UNVERÄNDERT; das Raw (pt_s4_r2_results.json) trägt KEINE Verdict-/
Einstufungs-Felder — die Auswertung (pt_s4_r2_eval.py) liest NUR
committete Artefakte und schreibt pt_s4_r2_eval.json.

INTERPRETER-PINNING (049b-Lektion: cross-build ULP-Delta): Build und
Lauf unter dem SELBEN venv (Python + numpy Version im Prereg-Embed);
Bit-Pins gegen die 045-Erste-Messung sind DISKLOSURE (nicht Gate) — die
Kriterien sind funktional (TOL-Seite, Klassen-Attribution).

0 QPU — kein Qiskit, kein Docker.
"""
import hashlib
import itertools
import json
import platform
import time

import numpy as np

import pt_hstar5_execution as h5
import pt_s4_closure_theorem as s4
import pt_s4_t5_diag as td

EXPERIMENT = "052-s4-r2-recompute"
HYPOTHESIS = "H-S4CLOSURE-R2"
BRANCH = "h-test1-gap-invariance"   # REAL getragener Branch (Re-Freeze-Lesart 050)

PREREG_PATH = "pt_s4_r2_prereg.json"
PREREG_STATUS = "REGISTERED_NOT_MEASURED"
PREREG_MD5 = "51d5f255259d443a35f68fe5e771a208"   # Freeze vor Messung (2026-10-02)
RESULTS_PATH = "pt_s4_r2_results.json"
EVAL_PATH = "pt_s4_r2_eval.json"

# Konstanten spiegelnd (Schreibgeschützt — Identität wird getestet)
SUM_TOL = td.SUM_TOL                 # 1e-9, unverändert
EPS = h5.EPS_PRIMARY                 # 0.25
TAU1, TAU2, TAU3 = h5.TAU1, h5.TAU2, h5.TAU3
BAHNEN = td.BAHNEN                   # {"adjacent": (6, 10), "disjoint": (4, 7)}

CODE_BASIS = ("pt_hstar5_execution.py", "pt_s4_closure_theorem.py",
              "pt_s4_t5_diag.py")
DATA_BASIS = ("pt_s4_closure_theorem_results.json",
              "scratches/h9_s4_source_unified_out.json")


def canonical(doc):
    """House-Konvention (identisch zu pt_ram_q6_kingston.canonical)."""
    return json.dumps(doc, sort_keys=True, separators=(",", ":"))


def md5_of(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def freeze_prereg(doc, path=PREREG_PATH):
    """Canonical JSON mit md5-Feld schreiben (einmalig beim Freeze)."""
    doc = dict(doc)
    doc.pop("md5", None)
    doc["md5"] = hashlib.md5(canonical(doc).encode("utf-8")).hexdigest()
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(canonical(doc))
    return path, doc["md5"]


def load_frozen_prereg(path=PREREG_PATH):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    got = doc.get("md5")
    check = doc.copy()
    check.pop("md5", None)
    want = hashlib.md5(canonical(check).encode("utf-8")).hexdigest()
    if got != want:
        raise AssertionError("Prereg-md5-MISMATCH %s != %s" % (got, want))
    if PREREG_MD5 and got != PREREG_MD5:
        raise AssertionError(
            "Prereg-md5-CONSTANTE %s != Datei %s" % (PREREG_MD5, got))
    if doc.get("status") != PREREG_STATUS:
        raise AssertionError("Prereg-Status verletzt: %s" % doc.get("status"))
    return doc


def load_json_dict(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def self_md5(path=PREREG_PATH):
    """md5 des canonical-DOCS ohne md5-Feld (= gefrorener Vertragswert)."""
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    doc.pop("md5", None)
    return hashlib.md5(canonical(doc).encode("utf-8")).hexdigest()


# === Bahn-Klassen und das vollständige Paar-Grid ===

def adjacency_classes(patterns=None):
    """Idx der adjacent-/disjoint-Klasse (045: Orbit-Struktur = Klasse,
    orbit_sizes [12, 3], adjacent_counts [12, 0] — committet)."""
    if patterns is None:
        patterns = s4.two_minus_patterns()
    adj = [i for i, pat in enumerate(patterns) if s4.is_adjacent(pat)]
    dis = [i for i, pat in enumerate(patterns) if not s4.is_adjacent(pat)]
    return {"adjacent": adj, "disjoint": dis}


def full_within_maximum(medians, classes=None):
    """Max |median(p) − median(q)| über ALLEN klassen-internen Paaren
    (nicht repr-verankert, kein Bahn-Beschnitt).  medians: idx -> Wert."""
    if classes is None:
        classes = adjacency_classes()
    out = {}
    for cls, idxs in classes.items():
        m, worst = 0.0, None
        for a, b in itertools.combinations(sorted(idxs), 2):
            d = abs(float(medians[a]) - float(medians[b]))
            if d > m:
                m, worst = d, [int(a), int(b)]
        out[cls] = {"max": m, "worst_pair": worst,
                    "n_members": len(idxs)}
    return out


def native_star_arm_maxima(per_pattern, classes=None):
    """045-native Star-Struktur: repr = erstes idx je Orbit-Gruppe
    (Insertion-Reihenfolge der 045-Schleife), max |ref(q) − member(q)|
    je Quantität je Klasse (re-abgeleitet aus den committeten/neuen
    per_pattern-Zeilen — kein neuer eigs-Aufruf)."""
    if classes is None:
        classes = adjacency_classes()
    patterns = s4.two_minus_patterns()
    sigmas = list(itertools.permutations(range(4)))
    reprs = {}
    for cls in ("adjacent", "disjoint"):
        idxs = sorted(classes[cls])
        reprs[cls] = idxs[0]
    out = {}
    for cls, ref_idx in reprs.items():
        ref = per_pattern[ref_idx]
        qs = ("k1_mean", "k2_mean", "R", "r_median")
        vals = {}
        for q in qs:
            if ref[q] is None:
                continue
            m, worst = 0.0, None
            for i in sorted(classes[cls]):
                if i == ref_idx or per_pattern[i][q] is None:
                    continue
                d = abs(float(ref[q]) - float(per_pattern[i][q]))
                if d > m:
                    m, worst = d, [int(ref_idx), int(i)]
            vals[q] = {"max": m, "worst_pair": worst}
        out[cls] = {"repr": int(ref_idx), "star_max": vals}
    return out


# === Prereg-Bau ===

def build_prereg():
    """Deterministischer Prereg-Dokument-Bau aus den COMMITTETEN Artefakten
    (045-Erste-Messung + committeter Scratch); alle embed-Floats exakt
    rückführbar, md5s der Quellen-Files im Doc."""
    res045 = json.load(open("pt_s4_closure_theorem_results.json",
                            encoding="utf-8"))
    t5 = res045["t5_t6_familien_summen"]
    scr = json.load(open("scratches/h9_s4_source_unified_out.json",
                         encoding="utf-8"))
    scr_med_uni = {int(k): float(np.median(v))
                   for k, v in scr["per_pattern_unified"].items()}
    scr_med_inst = {int(k): float(np.median(v))
                    for k, v in scr["per_pattern_inst"].items()}
    classes = adjacency_classes()
    fu_full = full_within_maximum(scr_med_uni, classes)
    fi_full = full_within_maximum(scr_med_inst, classes)

    pp = {int(k): v for k, v in t5["per_pattern"].items()}
    classes_native = native_star_arm_maxima(pp, classes)

    known = {
        "scratch_full_within_unified": {
            cls: fu_full[cls] for cls in ("adjacent", "disjoint")},
        "scratch_full_within_inst": {
            cls: fi_full[cls] for cls in ("adjacent", "disjoint")},
        "scratch_vergleiche": [
            {"bahn": v["bahn"], "pair": list(v["pair"]),
             "d_inst": float(v["d_inst"]),
             "d_unified": float(v["d_unified"])}
            for v in scr["vergleiche"]],
        "star_anker_045": {cls: classes_native[cls]
                           for cls in ("adjacent", "disjoint")},
        "margin_aufklaerung": (
            "Scratch-Flag inst_reproduziert=false (Delta 1.12e-9 vs 045) "
            "ist Paarungs-Struktur, NICHT Mess-Rauschen: 045s native "
            "max_within ist repr-verankert (repr 0, worst (0,6) r_median "
            "1.0260516436488842e-08), die vollständige Paarbildung liefert "
            "(6,10) 1.1384355902421817e-08 — beide > TOL"),
    }
    doc = {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "typ": "re_rechnungs_artefakt_einstufung",
        "status": PREREG_STATUS,
        "qpu": 0,
        "branch": BRANCH,
        "frage": (
            "Die offizielle Einstufung der EINZIGEN "
            "H_S4_CLOSURE_DEVIATION_FOUND-Verletzung (045, T5 "
            "max_within_orbit_dev > SUM_TOL): Quellen-Artefakt der "
            "t_H-Mischung (SA-H9-3), struktureller Rest, oder native "
            "nicht reproduzierbar — als registrierter Record, ohne "
            "stilles Re-Decide des committeten Verdicts"),
        "basis": {
            "results_045": {"path": "pt_s4_closure_theorem_results.json",
                            "md5": md5_of("pt_s4_closure_theorem_results.json")},
            "scratch_unified": {
                "path": "scratches/h9_s4_source_unified_out.json",
                "md5": md5_of("scratches/h9_s4_source_unified_out.json")},
            "code": {p: md5_of(p) for p in CODE_BASIS},
            "beobachtet_045_max_within": t5["max_within_orbit_dev"],
            "beobachtet_045_between_gap": t5["between_orbit_R_gap"],
            "beobachtet_045_r_median": {str(i): pp[i]["r_median"]
                                        for i in (0, 6, 10)},
            "beobachtet_045_R": {str(i): pp[i]["R"] for i in (0, 6, 10, 4, 7)},
            "adjacent_R_repr_atom": t5["adjacent_R"],
            "disjoint_R_repr_atom": t5["disjoint_R"],
            "scratch_max_within_inst": scr["max_within_inst"],
            "scratch_max_within_unified": scr["max_within_unified"],
            "bekannte_scratch_lesarten": known,
        },
        "konstanten": {
            "eps_primary": EPS,
            "tau1": TAU1, "tau2": TAU2, "tau3": TAU3,
            "sum_tol": SUM_TOL,
            "bahnen": {"adjacent": list(BAHNEN["adjacent"]),
                       "disjoint": list(BAHNEN["disjoint"])},
            "n_patterns": 15,
            "family_size": len(h5.get_config_family()),
            "k_class_sizes": {k: len(v) for k, v in classes.items()},
        },
        "gesetze": {
            "r_inst": "h5.ratio_stat(h5.re_eigs(h5.folded_hamiltonian"
                      "(cfg, signs, EPS_PRIMARY))) — wörtlich Scratch/045",
            "r_unified": "h5.k_norm(evs, TAU2*t_cache[cfg]) / "
                         "h5.k_norm(evs, TAU1*t_cache[cfg]) auf Muster-"
                         "gefoldeten Eigenwerten — wörtlich Scratch",
            "native_l1": "s4.check_t5_t6(cache) mit cache[cfg] = "
                         "{'t_h': h5.unfold_spectrum(cfg)[1]} — wörtlich "
                         "s4.main",
            "keine_wege_reduktion":
                "jede Leg rechnet ihre eigenen eigs (native-Feld in "
                "check_t5_t6 intern; L2 im eigenen Loop) — keine "
                "Rekursions-/Cache-Kopplung zwischen den Legs",
        },
        "criteria": {
            "boundary_semantics": (
                "strikt: l1 '> sum_tol' und l2 '< sum_tol'; bei EXAKTER "
                "Gleichheit kippt das zugehörige Kriterium ins "
                "Struktur-Rest-Bündel"),
            "l1_reproduktion": {
                "metric": "native_t5_t6.max_within_orbit_dev (Star-Struktur, wörtlich)",
                "bedingung": "> sum_tol",
                "klassen_attribution": (
                    "within_max der adjacent-Klasse auf dem r_median-Arm "
                    "> sum_tol (aus native per_pattern re-abgeleitet; "
                    "kommutativ-magnitudenbasiert, ordnungs-robust)"),
                "structural": {"n_patterns": 15, "orbit_count": 2,
                               "orbit_sizes": [12, 3],
                               "adjacent_counts": [12, 0],
                               "k_class_sizes": {"adjacent": 12,
                                                 "disjoint": 3}},
                "bit_pins": "DISKLOSURE-only (nicht Gate): r_median p0/6/10 "
                            "+ R-Werte + Atome vs 045-Kommit; ULP-Delta "
                            "ausgeschrieben (049b-Lektion)",
            },
            "l2_einheitsquelle": {
                "metric": "full_within_maximum[adjacent].max (per_pattern_unified Medians)",
                "bedingung": "< sum_tol",
                "secondary_bahn_replik": (
                    "C.3-Replik: d_unified beider BAHNEN-Paare < sum_tol "
                    "(bahn-scoped, klassisch)"),
                "k_class_conditions": {
                    "adjacent": "full_within_maximum adjacent < sum_tol",
                    "disjoint": "full_within_maximum disjoint < sum_tol"},
                "bit_pins_vs_scratch": (
                    "DISKLOSURE-only — der scratch rannte ohnen "
                    "aufgezeichneten Interpreter (Build-Caveat; keine "
                    "Bit-Gates gegen Scratch-Werte)"),
            },
            "konsistenz_gate": (
                "Eval re-deriviert Medians/Maxima aus den Roh-Arrays und "
                "verlangt Bit-Gleichheit zu den Roh-Aggregaten "
                "(Integritaets-Gate); verletzt => DEGENERAT"),
        },
        "verdict_map": [
            {"name": "DEGENERAT",
             "bedingung": (
                 "Basis-Artefakte fehlen oder md5-Delta gegenüber Prereg; "
                 "Struktur-Verletzung (n_patterns != 15, orbit_count != 2, "
                 "orbit_sizes != [12,3], Klassen-Groessen != (12,3), "
                 "Roh-Vertrag oder Konsistenz-Gate verletzt)"),
             "einstufung_045": "UNVERÄNDERT; keine offizielle Einstufung"},
            {"name": "RECOMPUTE_UNABLE",
             "bedingung": (
                 "L1 scheitert (native max_within <= sum_tol ODER carrying "
                 "arm nicht r_median/adjacent) bei intaktem committetem "
                 "045-Basis-Befund"),
             "einstufung_045": (
                 "UNVERÄNDERT; offizielle Einstufung offen (native "
                 "Wiedergabe unter demselben Code nicht erreicht — "
                 "disclosed, kein Re-Decide durch das Fenster)"),
            },
            {"name": "H_S4CLOSURE_R2_QUELLEN_ARTEFAKT",
             "bedingung": "L1 OK UND ALLE L2-Bedingungen OK (primary + bahn)",
             "einstufung_045": (
                 "OFFIZIELL: die T5-Verletzung ist ein Quellen-Artefakt "
                 "der t_H-Mischung (Antithese SA-H9-3 bestätigt als "
                 "Artefaktabklärung); committetes 045-Verdict bleibt "
                 "UNVERÄNDERT, Einstufungs-Tabelle erweitert; "
                 "Margin-Disclosure verpflichtend (Faktor ~1.19 an der "
                 "Kante, bekannt ex ante aus dem committeten Scratch)"),
             },
            {"name": "H_S4CLOSURE_R2_STRUKTURELL_REST",
             "bedingung": "L1 OK UND mindestens EINE L2-Bedingung >= sum_tol",
             "einstufung_045": (
                 "OFFIZIELL: struktureller Rest — die SA-H9-3 "
                 "Quellen-Artefakt-Antithese KIPPT; die Einstufung der "
                 "Verletzung bleibt als echte Abweichung stehen "
                 "(C.3-Lesart wird korrigiert: nur bahn-scoping hielt)")},
        ],
        "governance": {
            "kein_re_decide": True,
            "committed_045_verdict": res045["verdict_class"],
            "toleranz": ("SUM_TOL 1e-9 unverändert (Konstanten-Identität "
                         "s4/td, KEINE Erhöhung, KEINE Weichmachung der "
                         "Klassen-Attribution)"),
            "raw_vertrag": ("pt_s4_r2_results.json trägt KEINE Verdict-/"
                            "Einstufungs-Felder (nur Messungen); Eval "
                            "schreibt pt_s4_r2_eval.json separat"),
            "eval_reads_only_committed": True,
            "margin_risk": (
                "Kante ex ante disclosed: schmalste Kante = unified "
                "full-grid adjacent (Scratch-Lesart 8.393228334568903e-10, "
                "Faktor ~1.19 unter TOL); ein Flip ist möglich und ist "
                "vor-klassifiziert — Bedingungs-Flip = "
                "H_S4CLOSURE_R2_STRUKTURELL_REST"),
            "bit_pin_risk": (
                "049b-Lektion: cross-build ULP — Bit-Pins sind DISKLOSURE, "
                "nicht Gate; interpreter/np-version im Raw-Metadaten"),
            "no_docker": True,
        },
        "deck_anker": {"deck": "HYPOTHESEN_UND_ANTITHESES_H9_2026_09_29.md",
                       "f_zeile": 2,
                       "c3_schnitt": "§C.3 (Grade B+, kein Re-Decide)"},
        "doku_plan": {"section": "§10.35", "synthesis": "§Z.34"},
        "build_env": {"python": platform.python_version(),
                      "numpy": np.__version__,
                      "platform": platform.platform()},
    }
    return doc


# === Der Lauf (L1 + L2, 0 QPU) ===

def run_recompute(results_path=RESULTS_PATH, verbose=True):
    """EIN Durchlauf, ZWEI getrennte Legs (keine Weg-Kopplung):
      L1: native = s4.check_t5_t6(cache) — wörtlich die 045-Maschinerie am
          LEICHTEN Cache (cache[cfg] = {'t_h': ...}, exakt s4.main-Bau).
          Diese Leg berechnet IHRE eigs intern (_config_stats).
      L2: eigener Loop, verbatim scratches/h9_s4_source_unified.py
          (per-config eigs, r_inst = ratio_stat [None-Guard], r_unified =
          k_norm-Quotient am Cache-t_h, kein None-Guard — wörtlich).

    Roh-Vertrag: KEINE Verdict-/Einstufungs-Felder — die Auswertung
    (pt_s4_r2_eval.py) entscheidet aus den registrierten Kriterien."""
    t0 = time.time()
    prereg = load_frozen_prereg()
    cfgs = list(h5.get_config_family())
    pats = s4.two_minus_patterns()

    cache = {}
    for cfg in cfgs:
        _, t_h = h5.unfold_spectrum(cfg)
        cache[cfg] = {"t_h": t_h}
    print("[r2] cache build fertig %.1fs (%d cfgs)"
          % (time.time() - t0, len(cfgs)), flush=verbose)

    # --- L1: native T5/T6 (repr-verankerte Star-Struktur, wörtlich) ---
    native = s4.check_t5_t6(cache)
    print("[r2] L1 check_t5_t6 fertig %.1fs max_within %.6e"
          % (time.time() - t0, native["max_within_orbit_dev"]), flush=verbose)

    # --- L2: unified-Leg (wörtlich Scratch) ---
    per_inst, per_uni = {}, {}
    for p in range(len(pats)):
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
        per_inst[p] = r_inst
        per_uni[p] = r_uni
        print("[r2] pattern %2d n=%2d inst_med %.10f uni_med %.10e (%.1fs)"
              % (p, len(r_inst), float(np.median(r_inst)),
                 float(np.median(r_uni)), time.time() - t1), flush=verbose)

    med_i = {p: float(np.median(v)) for p, v in per_inst.items()}
    med_u = {p: float(np.median(v)) for p, v in per_uni.items()}
    classes = adjacency_classes()
    full = {"inst": full_within_maximum(med_i, classes),
            "unified": full_within_maximum(med_u, classes)}
    vergleiche = []
    for name, (p, q) in td.BAHNEN.items():
        vergleiche.append({"bahn": name, "pair": [int(p), int(q)],
                           "d_inst": abs(med_i[p] - med_i[q]),
                           "d_unified": abs(med_u[p] - med_u[q])})

    doc = {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "qpu": 0,
        "prereg_md5": prereg["md5"],
        "prereg_self_md5": self_md5(),
        "sum_tol": SUM_TOL,
        "native_t5_t6": native,
        "per_pattern_inst": {str(k): v for k, v in per_inst.items()},
        "per_pattern_unified": {str(k): v for k, v in per_uni.items()},
        "full_within": {
            arm: {cls: {"max": v["max"], "worst_pair": v["worst_pair"],
                        "n_members": v["n_members"]}
                  for cls, v in full[arm].items()}
            for arm in ("inst", "unified")},
        "vergleiche": vergleiche,
        "metadata": {"python": platform.python_version(),
                     "numpy": np.__version__,
                     "platform": platform.platform(),
                     "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                     "family_size": len(cfgs),
                     "n_patterns": len(pats)},
        "total_seconds": round(time.time() - t0, 1),
    }
    with open(results_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1, default=float)
    print("[r2] FERTIG %.1fs -> %s" % (time.time() - t0, results_path),
          flush=verbose)
    return doc


if __name__ == "__main__":
    run_recompute()