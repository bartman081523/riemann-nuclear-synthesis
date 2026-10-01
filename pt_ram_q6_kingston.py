# -*- coding: utf-8 -*-
"""EXPERIMENT 050 (Prereg-Modul, H-RAM-Q-6 Leg D1 Substrat-Uni): Kingston.

D1 Substrat-Uni (Freigabe "mache alles was noch offen ist, auch alle auf
statevector und qpu", sub-constraint "kein Freeze des QPU-Beins ohne
Prereg-Commits"): dasselbe 26-(P,arm)-Grid des GEFRORENEN Phase-11b-
Payloads (baaca1f6), EIN Kingston-Job (TOKEN2), ISA-Gate first.  Die 26
Punkte werden NICHT neu gerechnet — sie kommen bit-identisch aus
pt_ram_q_hardware3_aer.all_points().

Die ex-ante-Legs dieses Moduls (L1/L2/L3) sind im Freeze
pt_ram_q6_kingston_prereg.json registriert.  Das GEERBTE Verdict (die
044-v3b-Gesetzes-Auswertung ueber das Kingston-Raw via
pt_ram_q_hardware3_eval.evaluate) ist REGISTERTE Sekundaer-Lesart — es
re-decidiert NICHTS (S1/S2 bleiben committet).

TOKEN-DISZIPLIN: dieses Bein liest NUR TOKEN2 (IBMQ_TOKEN2 via
pt_v5_kingston.load_token).  TOKEN1 wird NIE gelesen.  Kein Docker.
"""
import hashlib
import json
import os

import numpy as np

import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_aer as h3a
import pt_ram_q_hardware3_eval as h3e

EXPERIMENT = "050-ram-q6-kingston-substrat"
HYPOTHESIS = "H-RAM-Q-6"
LEG = "D1-SUBSTRAT-UNIVERSITAET"
# Re-Freeze-Präzedenz Phase 10b R1: Branch-Feld korrigiert auf den REAL
# getragenen Branch (h-test1-gap-invariance, descended von ram-q f0fdd4c;
# Task-Text sagte ram-q-zyklizitaet) VOR jedem QPU-Kontakt — kein Messwert.
BRANCH = "h-test1-gap-invariance"

PREREG_PATH = "pt_ram_q6_kingston_prereg.json"
PREREG_MD5 = "768bffb829114f2482f42382e0763b60"
PREREG_STATUS = "REGISTERED_NOT_MEASURED"

S1_EVAL_PATH = "pt_ram_q_hardware3_eval.json"        # Session 1 (11d)
S2_EVAL_PATH = "pt_ram_q_hardware3_eval_rep.json"    # Session 2 (047)
INHERITED_EVAL_PATH = "pt_ram_q6_kingston_inherited_eval.json"
EVAL_PATH = "pt_ram_q6_kingston_eval.json"

ISA_GATE_PATH = "pt_ram_q6_kingston_isa_gate.json"
JOB_ID_PATH = "pt_ram_q6_kingston_job_id.txt"
RAW_PATH = "pt_ram_q6_kingston_raw.json"

BACKEND_NAME = "ibm_kingston"

# --- Leg-Konstanten ex ante ---
SEED_L1_S1 = 20261006
SEED_L1_S2 = 20261007
N_PERM = 2000
N_HOLDOUT = 13
ELIGIBLE_ABS_MIN = 0.01          # §Z.29-Lesart |res| >= 0.01
BINOM_ALPHA = 0.05               # L2 einseitig exakt
KAPPA_CEILING = h3.KAPPA_CEILING  # 0.81 — identisch zum gefrorenen Verdict
ISA_CEILINGS = {"per_circuit_2q_max": 120, "total_2q_max": 6000}


def canonical(doc):
    """House-Konvention (identisch zu h3.canonical_payload_json)."""
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


def self_md5(path=PREREG_PATH):
    """md5 des canonical-DOCS ohne md5-Feld (= der gefrorene Vertragswert)."""
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    doc.pop("md5", None)
    return hashlib.md5(canonical(doc).encode("utf-8")).hexdigest()


# --- Leg-Mathematik (ex ante) ---

def _avg_tie_ranks(values):
    order = np.argsort(values, kind="stable")
    ranks = np.empty(len(values), dtype=float)
    vals = np.asarray(values, dtype=float)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return ranks


def pearson(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    x = x - x.mean()
    y = y - y.mean()
    denom = np.sqrt((x * x).sum() * (y * y).sum())
    if denom == 0.0:
        return 0.0
    return float((x * y).sum() / denom)


def spearman(x, y):
    return pearson(_avg_tie_ranks(x), _avg_tie_ranks(y))


def permutation_null_rho(x, y, n_perm, seed):
    """Null: |rho(x, perm(y)); Schwelle q95 der absoluten Null."""
    rng = np.random.default_rng(int(seed))
    y = np.asarray(y, dtype=float)
    stats = np.sort(np.asarray(
        [abs(spearman(x, rng.permutation(y))) for _ in range(int(n_perm))]))
    return {"n_perm": int(n_perm), "seed": int(seed),
            "q95_abs": float(stats[int(np.floor(0.95 * (len(stats) - 1)))]),
            "null_mean": float(np.mean(stats)),
            "null_max": float(stats[-1]),
            "null_q05_abs": float(stats[int(np.floor(0.05 * (len(stats) - 1)))])}


def leg_l1(res_session, res_kingston, seed, n_perm=N_PERM):
    rho = spearman(res_session, res_kingston)
    null = permutation_null_rho(res_session, res_kingston, n_perm, seed)
    return {"rho_obs": rho, "n": len(res_session), "null": null,
            "pass": bool(rho > null["q95_abs"]),
            "seed": int(seed), "n_perm": int(n_perm)}


def sign_agreement(res_a, res_b, abs_min=None):
    a = np.asarray(res_a, dtype=float)
    b = np.asarray(res_b, dtype=float)
    if abs_min is None:
        mask = np.ones(len(a), dtype=bool)
    else:
        mask = np.abs(a) >= abs_min
    k = int(np.sum(np.sign(a[mask]) == np.sign(b[mask])))
    return {"n": int(mask.sum()), "agree": k, "disagree": int(mask.sum()) - k}


def binom_sf_one_sided(k, n):
    """P(X >= k) unter Binomial(n, 0.5), exakt (Kombinatorik)."""
    from math import comb
    if n == 0:
        return 1.0
    return sum(comb(n, i) for i in range(int(k), n + 1)) / 2 ** n


def leg_l2(res_session, res_kingston, abs_min=ELIGIBLE_ABS_MIN):
    raw = sign_agreement(res_session, res_kingston)
    raw["p_one_sided"] = binom_sf_one_sided(raw["agree"], raw["n"])
    raw["pass"] = bool(raw["p_one_sided"] <= BINOM_ALPHA)
    out = {"lesart_roh": raw, "abs_min": abs_min}
    el = sign_agreement(res_session, res_kingston, abs_min)
    el["p_one_sided"] = binom_sf_one_sided(el["agree"], el["n"])
    out["lesart_eligible"] = el
    return out


def holdout_residuen(eval_doc):
    """res_v3 der 13 Holdout-(P,arm)-Felder aus einem Session-Eval-Dok."""
    out = {}
    for k, p in (eval_doc.get("punkte") or {}).items():
        if k.startswith("verdict|"):
            out[k] = p.get("res_v3")
    if len(out) != N_HOLDOUT:
        raise AssertionError("Holdout-Anzahl %d != %d" % (len(out), N_HOLDOUT))
    return out


def kappa_map(eval_doc):
    return {k: p.get("kappa_hat")
            for k, p in (eval_doc.get("punkte") or {}).items()}


# --- ISA-Gate-Schema (GEFRORENE Eval kompatibel) ---

ISA_GATE_SCHEMA_KEYS = {
    "experiment", "backend", "optimization_level", "transpile_seed",
    "total_two_q", "max_two_q", "isa_ceiling", "per_circuit_two_q",
    "verdict", "generated_at_utc", "n_circuits",
}


def validate_isa_gate(doc, n_circuits=116):
    missing = ISA_GATE_SCHEMA_KEYS - set(doc)
    if missing:
        raise AssertionError("ISA-Gate-Schluessel fehlen: %s" % sorted(missing))
    if doc["verdict"] != "ISA_OK":
        raise AssertionError("ISA-Gate verdict: %s" % doc["verdict"])
    if int(doc["n_circuits"]) != int(n_circuits):
        raise AssertionError(
            "ISA-Gate n_circuits %d != %d" % (doc["n_circuits"], n_circuits))
    if doc["transpile_seed"] != h3a.TRANSPILE_SEED:
        raise AssertionError("transpile_seed abweichend")
    if doc["optimization_level"] != 3:
        raise AssertionError("optimization_level abweichend")
    if doc["max_two_q"] > ISA_CEILINGS["per_circuit_2q_max"]:
        raise AssertionError("per-circuit 2q Ceiling verletzt: %d"
                             % doc["max_two_q"])
    if doc["total_two_q"] > ISA_CEILINGS["total_2q_max"]:
        raise AssertionError("total-2q Ceiling verletzt: %d" % doc["total_two_q"])
    return True


def build_prereg_doc():
    """Freigabe-Dokument (einmalig beim Freeze; ohne Messwerte)."""
    pts = h3a.all_points()
    holdout_ks = sorted(k for k, v in pts.items() if v["set"] == "verdict")
    cal_ks = sorted(k for k, v in pts.items() if v["set"] == "cal")
    assert len(holdout_ks) == N_HOLDOUT and len(cal_ks) == N_HOLDOUT
    return {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "leg": LEG,
        "branch": BRANCH,
        "grid_points": {"verdict": [(a, P) for (a, P) in holdout_ks],
                        "kalibrier": [(a, P) for (a, P) in cal_ks]},
        "status": PREREG_STATUS,
        "frozen_inputs": {
            "law_prereg": {"path": "pt_ram_q_hardware3_prereg.json",
                           "md5": "baaca1f6772e07b0847fe436da7e16da"},
            "s1_eval": S1_EVAL_PATH, "s2_eval": S2_EVAL_PATH,
            "s1_job": "dat1o6qhcrkc73dtgo60", "s2_job": "dat3gpqhcrkc73ejcrgg",
            "points_source": "h3a.all_points() aus dem GEFRORENEN Payload "
                             "(13 Verdict + 13 Kalibrier; NICHT neu gerechnet)",
            "b_p_source": "pt_ram_q_hardware3_stage3.json (identisch zum "
                          "044-Eval-Kommit)",
        },
        "grid": {"n_verdict": N_HOLDOUT, "n_calibration": N_HOLDOUT,
                 "n_total": 2 * N_HOLDOUT},
        "hardware_parameters": {
            "backend": BACKEND_NAME,
            "token_discipline": "NUR TOKEN2 (pt_v5_kingston.load_token), "
                                'instance "open-instance"; TOKEN1 NIE gelesen',
            "shots_per_circuit": int(h3.SHOTS),
            "circuit_budget": {"verdict_structure": 39, "verdict_loschmidt": 13,
                               "echo_ladder": 6, "kalibrier_structure": 39,
                               "kalibrier_loschmidt": 13,
                               "negative_controls": 4, "readout_cal": 2,
                               "total": 116},
            "total_shots": 116 * int(h3.SHOTS),
            "run_config": {"optimization_level": 3,
                           "dynamical_decoupling": "XX",
                           "resilience": "none (raw SamplerV2 counts)"},
            "isa_ceilings": ISA_CEILINGS,
        },
        "legs": {
            "L1_Substrat_Kohaerenz": {
                "rule": "Spearman rho(res_Sx, res_K) ueber die 13 Holdout-P; "
                        "Null = Permutation der res_K (N_PERM draws, seed je "
                        "Session registriert), Schwelle = q95 der |rho|-Null; "
                        "BEIDE Legs muessen ueber der Schwelle liegen.",
                "seeds": {"S1": SEED_L1_S1, "S2": SEED_L1_S2},
                "n_perm": N_PERM,
                "sources": {"res_S1": S1_EVAL_PATH, "res_S2": S2_EVAL_PATH,
                            "res_K": RAW_PATH + " -> h3e.evaluate"},
                "verdict_role": "tragscheidend (mit L2)",
            },
            "L2_VorzeichenStabilitaet": {
                "rule": "Vorzeichen-Gleichheit sign(res_Sx) == sign(res_K) "
                        "ueber ALLE 13 roh; exakt einseitiger Binomial-p "
                        "(H0: gleiche Chance) <= 0.05 je Leg (d.h. >= 10/13)."
                        " Zweit-Lesare: eligible bei |res| >= 0.01 (je "
                        "Session, Praezedenz §Z.29) und Vereinigung.",
                "alpha": BINOM_ALPHA,
                "verdict_role": "tragscheidend (mit L1)",
            },
            "L3_KappaFloorUnion": {
                "rule": "kappa_ok je Punkt = kappa_hat >= 0.81 (Union ueber "
                        "Verdict UND Kalibrier der 26); n_kappa_low_union "
                        ">= 2 -> VOID_SUBSTRAT (Kalibrier-Floor nicht "
                        "uebertragbar). DIAGNOSTIK Spearman(kappa_K, kappa_S1) "
                        "ueber 26 — NICHT verdict-tragend.",
                "kappa_ceiling": KAPPA_CEILING,
                "verdict_role": "VOID-Kriterium",
            },
        },
        "verdict_map": {
            "order": ["DEGENERAT", "VOID_SUBSTRAT", "D1_REFUTED_SUBSTRAT_"
                      "SPEZIFISCH", "D1_PARTIAL", "D1_CONFIRMED_SUBSTRAT_"
                      "UNIVERSAL"],
            "DEGENERAT": "eine Kontrolle des geerbten Eval (t3-t6) verletzt "
                         "oder n_circuits != 116",
            "VOID_SUBSTRAT": "n_kappa_low_union >= 2 auf Kingston",
            "D1_REFUTED_SUBSTRAT_SPEZIFISCH": "KEINDER L1-Leg-Bestand und "
                                              "KEINER L2-Leg-Bestand",
            "D1_PARTIAL": "mindestens ein L1-Leg und das zugehoerige L2-Leg "
                          "bestehen",
            "D1_CONFIRMED_SUBSTRAT_UNIVERSAL": "BEIDE L1-Legs und BEIDE "
                                               "L2-Legs (roh) bestehen",
        },
        "inherited_verdict": {
            "rule": "pt_ram_q_hardware3_eval.evaluate(raw_path=KINGSTON_raw, "
                    "stage3=identisch, isa=KINGSTON_gate) — die 044-v3b-"
                    "Lesart auf dem SUBSTRAT Kingston (REGISTERTE Sekundaer-"
                    "Lesart, kein Re-Decide von S1/S2).",
            "prereg_md5_of_law": "baaca1f6772e07b0847fe436da7e16da",
        },
        "registered_expectations_nicht_verdict_tragend": {
            "s1_s2_praezedenz_rho": 0.8956043956043955,
            "s1_s2_praezedenz_vorzeichen_gleich": 11,
            "s1_s2_praezedenz_eligible_9/9": "bei |res| >= 0.01 (§Z.29)",
            "ghost_kanal_prior": "Echo-Kanal-Dominanz (res~delta_cal ~ "
                                 "-0.985 beide Arme, §10.31) — ein drittes "
                                 "Substrat spiegelt denselben Kanal.",
        },
        "submission_contract": {
            "job_id": JOB_ID_PATH + " (sofort nach Submission persistiert)",
            "raw": RAW_PATH + " (counts_md5; Commit VOR Auswertung)",
            "raw_absent_fields": ["kappa", "ratio", "gamma", "band",
                                  "residuen", "verdict"],
            "isa_gate_first": "gate-Artefakt committed VOR Submission; "
                              "transpile-Totals im Raw aus dem Gate gelesen, "
                              "NIE hartkodiert (Fez-559/84 NIE hier).",
        },
        "anti_sharpshooter": {
            "no_ex_post_fit": "Legs und Schwellen EX ANTE registriert; keine "
                              "Schwelle wird nach der Auswertung angepasst; "
                              "keine Toleranz-Erhebung.",
            "fallback_lesart": "L2-VereinigungsLesare (nur nachtraeglich "
                               "DOKUMENTIERT, nie stiller Patch).",
        },
    }


if __name__ == "__main__":
    p, m = freeze_prereg(build_prereg_doc())
    print("freeze:", p, m)