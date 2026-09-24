"""EXPERIMENT 034 - QUQUINT Paket 2: Ramanujan-Fingerprint-Replikation
(H-RAM-2), 0 QPU, Prereg-gebunden.

Frage (Plan: riemann-phase-post-z16-alpha-ramanujan-kingston-gue.md,
Paket 2): Der V2-Nebenfund (§Z.16, Vektor RAMANUJAN_DFT_FINGERPRINT B) ist
EINMAL gemessen (d=625, P=625, EIN P-Set): share*(prime) = 0.0427 vs
random 0.0099 vs composite 0.0036. Repliziert der mod-5-Fingerprint über
das volle (P, d)-Gitter, oder war er eine Fluktuation des Einzelpunkts?

Exakte Modell-Arithmetik (VOR dem Freeze im Modul hergeleitet und gegen
die V2-Anker verifiziert — Prereg-Lektion: Referenzkonstanten gegen die
Primär-Herleitung prüfen, nicht aus dem Plan übernehmen):

  Für a in S* = {a ≡ 0 mod d/5, a ≠ 0} ist omega_d^{a·p} = omega_5^{j·(p mod 5)}
  -> G(a) = sum_p omega_5^{j·p} = n_0 + sum_{r=1}^{4} n_r·omega_5^{j·r}
     mit n_r = #{p <= P : p ≡ r mod 5}; n_0 = 1 (nur p=5, für P >= 5).
  Uniform-Modell (Ramanujan-Äquipartition mod 5): n_r = (m-1)/4 ->
     G(a) = 1 - (m-1)/4 = (5-m)/4  (unabhängig von j, denn
     sum_{r=1..4} omega_5^{jr} = -1)
  -> share*_model(P, d) = 4·((m-5)/4)^2/(d·m) = (m-5)^2/(4·d·m),  m = pi(P).

  Verifikation gegen V2 (pt_multin_v2_results.json):
    - Exaktes Modell @ (625,625): 0.041688; V2-prereg führte das CRUDE
      Modell m/(4d) = 0.045 (Referenz-Korrektur dokumentiert, GUE-Lektion);
      V2 gemessen 0.04272280701754398 -> ratio 1.0248, im Band [0.8, 1.25].
    - Transition EXAKT bei m=25: (m-5)^2 = 16m -> share*_model = 4/d =
      generische Baseline -> bei P=97 sagt das Modell KEINE Trennung
      (registrierte NEGATIV-Vorhersage, deskriptiver Punkt).
    - m=16 (P=53): Modell UNTER der generischen Baseline (Unterdrückung).
    - m=5 (P=11, d=25): exakte Null (G_j = 0).

  Gated-Set (Fluktuations-Begründung VOR dem Freeze, vom V2-Anker
  kalibriert): die V2-Abweichung (2.5% bei m=114) skaliert als 1/m
  (Residuen-Counts sind O(1)-deviant, nicht O(sqrt(m))) -> Band ±25% fair
  für m >= ~40; ZWEITES Kriterium: Random-Null-Overlap-Sicherheit —
  share*_random ~ 4/d mit relativer Streuung O(1) (V2: 0.0099 = 1.54×
  generisch) verlangt band_lo >= ~3× generisch -> (m-5)^2/m >= 50 ->
  m >= 62; registrierte Marge -> GATE_MIN_PI = 79.
  Gated: pi(P) >= 79 -> genau 5 Punkte (401, 463, 541, 599, 625) — das
  Plan-Falsifikator-Format ">= 2 von >= 5" ist erfüllt.
  Deskriptiv: alle Punkte mit pi < 79 (inkl. d25, m=5/9 — V2-Lektion)
  MIT Modell-Vorhersage im Report (inkl. Transition-Punkt m=25).

Falsifikator (registriert VOR der Auswertung):
  >= 2 von 5 gated Prim-Punkten außerhalb [0.8, 1.25]·model  ODER
  Kontroll-Overlap (share*_random >= band_lo an einem gated Punkt ODER
  share*_composite >= band_lo des kleinsten gated Punkts (401)).
  Genau 1 Punkt außerhalb, kein Overlap -> PARTIAL (registrierte
  Mittelklasse, Fluktuationstoleranz — DEGENERAT-Lektion: die Klassen
  zwischen REPLICATED und REFUTED müssen explizit registriert sein).

Determinismus: share* ist REINE ARITHMETIK des Supports (DFT-Profil ohne
Shots/Noise) — V2-Anker sind bit-genau reproduzierbar (Tol 1e-9).

Offline-Guard: reine numpy-Arithmetik, kein Quantum-Stack-Import, kein
Provider, kein Token. 0 QPU.
"""

from __future__ import annotations

import argparse
import hashlib
import json

from pt_prime_state import sieve_primes
import pt_ququint_multin as mn

EXPERIMENT = "034-ququint-ramanujan-replication"
PREREG_PATH = "pt_ramanujan_prereg.json"
RESULTS_PATH = "pt_ramanujan_results.json"

HYPOTHESIS = (
    "H-RAM-2: Der mod-5-Fingerprint (Primes meiden Residuenset S* = "
    "{a ≡ 0 mod d/5, a ≠ 0} im DFT-Diagonalraum; share* ≈ (pi-5)^2/(4·d·pi) "
    "aus der Uniform-Residuen-Arithmetik) repliziert über das (P, d)-Gitter "
    "mit Trennung zu random- UND composite-Kontrolle in ALLEN gated Punkten.")
STEELMAN = (
    "Antithese: Der V2-Treffer war eine Fluktuation des Einzelpunkts "
    "(d625, EIN P-Set); über das Gitter kollabiert share*(prime) auf die "
    "Random-/Composite-Baseline (generisch 4/d).")

# === Registrierte Konstanten (Prereg, VOR Messung) ===

D_GRID = (25, 625)

# (P, d) Prime-Punkte: die 6 V2-Punkte (Replikation) + 5 neue (Plan:
# "z. B. 7, 53, 199, 401" + 541/599 zur Verstaerkung des gated-Satzes).
PRIME_POINTS = (
    (11, 25), (23, 25),                     # d25: deskriptiv (m=5, 9)
    (7, 625), (53, 625), (97, 625),         # m=4, 16, 25: deskriptiv
    (199, 625), (211, 625),                 # m=46, 47: deskriptiv
    (401, 625), (463, 625), (541, 625),     # GATED (pi >= 79)
    (599, 625), (625, 625),                 # GATED
)
COMPOSITE_POINTS = ((15, 625), (121, 625), (341, 625), (625, 625))

GATE_MIN_PI = 79          # gated <=> pi(P) >= 79 (5 Punkte)
BAND_LO = 0.8             # Band [0.8·model, 1.25·model] (Plan)
BAND_HI = 1.25
FALSIFIER_MIN_OUTSIDE = 2  # Plan: >= 2 von >= 5 ausserhalb -> REFUTED

RANDOM_SEED_BASE = 20260924        # pro Punkt: base + Index in PRIME_POINTS
V2_RANDOM_SEED = 20260923          # V2-Anker-Reproduktion (pt_ququint_multin)

# V2-Anker (pt_multin_v2_results.json, prereg_md5 d9da292c7863810840b86ae2f0):
V2_SHARE_STAR_PRIME_COMMITTED = 0.04272280701754398
V2_SHARE_STAR_RANDOM_COMMITTED = 0.009880701754386056
V2_SHARE_STAR_COMPOSITE_COMMITTED = 0.0035649122807017617
V2_SHARE_STAR_TOL = 1e-9   # deterministische Arithmetik -> bit-genau

# Referenz-Korrektur (GUE-Lektion): V2-prereg fuehrte das CRUDE Modell
# m/(4d) = 0.045; das exakte Uniform-Modell ist (m-5)^2/(4dm).
V2_CRUDE_MODEL_D625 = 0.045
EXACT_MODEL_625_625 = 109.0 ** 2 / (4.0 * 625.0 * 114.0)  # 0.041688...

GENERIC_BASELINE = {25: 4 / 25, 625: 4 / 625}

TRANSITION_M = 25  # (m-5)^2 = 16m  <=>  m = 25: Modell = generisch (kein Lift)

VERDICT_MAP = {
    "REPLICATED": "H-RAM-2_REPLICATED_FINGERPRINT",
    "PARTIAL": "H-RAM-2_PARTIAL_EIN_PUNKT_AUSSEN",
    "REFUTED": "H-RAM-2_REFUTED_FINGERPRINT_KOLLABIERT",
    "INVALID": "EVALUATION_INVALID_KONTROLLE_GESCHEITERT",
}


# === Modell (exakte Uniform-Residuen-Arithmetik) ===

def model_share_star(P, d):
    """share*_model = (pi-5)^2/(4·d·pi) — exakte Uniform-Arithmetik.

    Herleitung (Docstring): G(a) = (5-m)/4 für alle 4 S*-Klassen bei
    Äquipartition der Nicht-5-Primes auf {1,2,3,4}; share* = Summe der
    4 Klassen-Massen = 4·((m-5)/4)^2/(d·m).
    """
    m = len(sieve_primes(P))
    return (m - 5) ** 2 / (4.0 * float(d) * m)


def generic_baseline(d):
    """Generische Baseline (random-Level): 4/d."""
    return 4.0 / float(d)


def lift_factor(P):
    """Lift über generisch: (m-5)^2/(16m); <1 = Unterdrückung, =1 Transition."""
    m = len(sieve_primes(P))
    return (m - 5) ** 2 / (16.0 * m)


def is_gated(P, d):
    return d == 625 and len(sieve_primes(P)) >= GATE_MIN_PI


def composite_rank_matched(m):
    """Erste m Composites (4, 6, 8, 9, 10, 12, ...).

    Fuer kleine P kann mn.composite_support(P) nicht genug Elemente <= P
    liefern (z. B. P=7: nur [4, 6]); rank-matched heisst: gleiche Macht m
    = pi(P), Grenze dann notfalls hoeher. Fuer m = pi(625) = 114 identisch
    mit mn.composite_support(625) (T3-Anker).
    """
    out = []
    n = 4
    while len(out) < m:
        if not all(n % p for p in sieve_primes(int(n ** 0.5) + 1)):
            out.append(n)  # teilbar durch ein Prime <= sqrt(n) -> composite
        n += 1
    return out


# === Punkt-Messung (reine Arithmetik) ===

def run_point(P, d, seed):
    """share*(prime/random) an einem (P, d)-Punkt + Modell + Band.

    Random-Null: Support gleicher Macht m (pi(P)), Seed base+Index
    (registriert). Composite: rank-matched Kontrolle (erste m Composites).
    """
    primes = sieve_primes(P)
    m = len(primes)
    prof_prime = mn.single_register_profile(primes, d)
    share_prime = mn.share_star(prof_prime, d)
    rand_support = mn.random_diagonal_support(m, d, seed)
    share_random = mn.share_star(
        mn.single_register_profile(rand_support, d), d)
    try:
        comp_support = mn.composite_support(P)
    except ValueError:
        comp_support = composite_rank_matched(m)
    share_composite = mn.share_star(
        mn.single_register_profile(comp_support, d), d)
    model = model_share_star(P, d)
    return {
        "P": P, "d": d, "m": m,
        "share_prime": share_prime,
        "share_random": share_random,
        "share_composite": share_composite,
        "model": model,
        "generic": generic_baseline(d),
        "lift_model": lift_factor(P),
        "gated": is_gated(P, d),
        "seed": seed,
    }


def band(model):
    return [BAND_LO * model, BAND_HI * model]


def composite_limit():
    """Overlap-Schwelle für die Composite-Kontrolle: band_lo des kleinsten
    gated Punkts (401, 625) — registriert."""
    return BAND_LO * model_share_star(401, 625)


# === Verdict ===

def point_flags(row, comp_limit):
    """Gates an einem Punkt (nur gated-Punkte zählen für den Falsifikator)."""
    if not row["gated"]:
        return {"band": None, "random_overlap": None,
                "composite_overlap": None, "outside": None}
    lo, hi = band(row["model"])
    in_band = lo <= row["share_prime"] <= hi
    return {
        "band": in_band,
        "random_overlap": row["share_random"] >= lo,
        "composite_overlap": row["share_composite"] >= comp_limit,
        "outside": not in_band,
    }


# === Prereg (Freeze VOR Auswertung) ===

def build_prereg_payload():
    pi_by_point = {f"{P},{d}": len(sieve_primes(P))
                   for P, d in PRIME_POINTS}
    models = {f"{P},{d}": model_share_star(P, d) for P, d in PRIME_POINTS}
    gated = [f"{P},{d}" for P, d in PRIME_POINTS if is_gated(P, d)]
    return {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "steelman": STEELMAN,
        "registered_before": {
            "plan": ("~/.claude/plans/riemann-phase-post-z16-alpha-ramanujan-"
                     "kingston-gue.md, Paket 2"),
            "plan_date": "2026-09-24",
            "model_derivation": (
                "Exakte Uniform-Residuen-Arithmetik im Modul hergeleitet "
                "UND gegen die V2-Anker verifiziert VOR diesem Freeze "
                "(Prereg-Lektion): share*_model = (pi-5)^2/(4·d·pi); "
                "G(a) = (5-m)/4 für alle 4 S*-Klassen."),
            "reference_correction": (
                "V2-prereg fuehrte das CRUDE Modell m/(4d) = 0.045 (d=625); "
                "das exakte Uniform-Modell liefert 0.041688. V2 gemessen "
                "0.04272280701754398 -> ratio 1.0248, im registrierten Band "
                "[0.8, 1.25] — die Korrektur ändert das V2-Urteil NICHT "
                "(GUE-Lektion-Muster: Korrektur VOR dem Freeze dokumentiert)."),
            "gate_set_justification": (
                "GATE_MIN_PI = 79 aus zwei VOR dem Freeze abgeleiteten "
                "Kriterien: (1) Prim-Band-Fluktuation skaliert als 1/m vom "
                "V2-Anker (2.5% bei m=114; Residuen-Counts O(1)-deviant) "
                "-> ±25%-Band fair für m >= ~40; (2) Random-Overlap-Sicherheit: "
                "share*_random ~ 4/d mit O(1)-relativer Streuung (V2: "
                "1.54× generisch) verlangt band_lo >= ~3× generisch -> "
                "m >= 62; registrierte Marge -> pi >= 79. Gated: genau 5 "
                "Punkte (401, 463, 541, 599, 625) — Plan-Format "
                "\">= 2 von >= 5\" erfüllt."),
            "transition_prediction": (
                "Registrierte NEGATIV-Vorhersage: bei m=25 (P=97, d=625) ist "
                "(m-5)^2 = 16m exakt -> share*_model = 4/d = generisch: das "
                "Modell sagt KEINE Prime-Trennung am Transition-Punkt "
                "(deskriptiv, kein Gate). Bei m=16 (P=53) sagt das Modell "
                "share* UNTER der generischen Baseline (Unterdrückung); "
                "bei m=5 (P=11, d=25) die exakte Null."),
            "descriptive_policy": (
                "Alle Punkte mit pi(P) < 79 sind deskriptiv (Modell-Vorhersage "
                "wird berichtet, kein Gate) — d25 vollständig deskriptiv "
                "(V2-Lektion: m=9 fluktuationsbeherrscht)."),
        },
        "prime_points": [[P, d] for P, d in PRIME_POINTS],
        "composite_points": [[P, d] for P, d in COMPOSITE_POINTS],
        "d_grid": list(D_GRID),
        "pi_by_point": pi_by_point,
        "model_share_star": models,
        "gated_points": gated,
        "thresholds": {
            "band": [BAND_LO, BAND_HI],
            "gate_min_pi": GATE_MIN_PI,
            "falsifier_min_outside": FALSIFIER_MIN_OUTSIDE,
            "composite_overlap_limit": composite_limit(),
            "v2_share_star_tol": V2_SHARE_STAR_TOL,
        },
        "seeds": {
            "random_base": RANDOM_SEED_BASE,
            "seed_rule": "RANDOM_SEED_BASE + Index in PRIME_POINTS",
            "v2_anchor_seed": V2_RANDOM_SEED,
        },
        "v2_anchors": {
            "share_star_prime_d625": V2_SHARE_STAR_PRIME_COMMITTED,
            "share_star_random_d625": V2_SHARE_STAR_RANDOM_COMMITTED,
            "share_star_composite_d625": V2_SHARE_STAR_COMPOSITE_COMMITTED,
            "crude_model_d625": V2_CRUDE_MODEL_D625,
            "exact_model_d625": EXACT_MODEL_625_625,
            "prereg_md5": "d9da292c7863810840b86ae2f069a365",
        },
        "controls": {
            "T1_v2_anchor_prime": (
                "share*(prime, 625, 625) == V2-kommittiert "
                f"({V2_SHARE_STAR_PRIME_COMMITTED:.14f}) innerhalb "
                f"{V2_SHARE_STAR_TOL:.0e} (bit-genau, reine Arithmetik)"),
            "T2_v2_anchor_random": (
                "share*(random, 625, 625, seed 20260923) == V2-kommittiert "
                f"({V2_SHARE_STAR_RANDOM_COMMITTED:.14f})"),
            "T3_v2_anchor_composite": (
                "share*(composite, 625, 625) == V2-kommittiert "
                f"({V2_SHARE_STAR_COMPOSITE_COMMITTED:.14f})"),
            "T4_model_exact": (
                "model(625,625) == 109^2/(4·625·114) exakt (1e-12) und "
                "model(97,625) == 4/625 exakt (Transition)"),
            "T5_gate_set": (
                "gated Punkte == [401, 463, 541, 599, 625] auf d=625, "
                "alle pi >= 79; d25 ausschließlich deskriptiv"),
            "gate": "Kontrollfehler -> EVALUATION_INVALID",
        },
        "falsifier": {
            "rule": (">= 2 von 5 gated Prim-Punkten außerhalb [0.8, 1.25]·model "
                     "ODER Kontroll-Overlap (random >= band_lo an einem gated "
                     "Punkt ODER composite >= band_lo(401))"),
            "partial_class": (
                "GENAU 1 Punkt außerhalb, kein Overlap -> PARTIAL "
                "(registrierte Mittelklasse, Fluktuationstoleranz — "
                "DEGENERAT-Lektion: Klassen zwischen REPLICATED und "
                "REFUTED explizit registriert)"),
        },
        "verdict_map": VERDICT_MAP,
        "qpu": "0 QPU (reine numpy-Arithmetik, kein Quantum-Stack-Import)",
        "plan": "~/.claude/plans/riemann-phase-post-z16-alpha-ramanujan-kingston-gue.md",
    }


def canonical_payload_json(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def payload_md5(payload):
    return hashlib.md5(
        canonical_payload_json(payload).encode("utf-8")).hexdigest()


def freeze_prereg(payload=None):
    if payload is None:
        payload = build_prereg_payload()
    doc = dict(payload)
    doc["md5"] = payload_md5(payload)
    return doc


def verify_prereg_md5(doc):
    stripped = {k: v for k, v in doc.items() if k != "md5"}
    return payload_md5(stripped) == doc["md5"]


def load_frozen_prereg(path=PREREG_PATH):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if not verify_prereg_md5(doc):
        raise ValueError(f"Prereg-md5-MISMATCH in {path}")
    return doc


# === Kontrollen ===

def run_controls():
    c = {}
    prof_prime = mn.dft_profile(625, 625)
    c["T1_v2_anchor_prime"] = (
        abs(mn.share_star(prof_prime, 625) - V2_SHARE_STAR_PRIME_COMMITTED)
        <= V2_SHARE_STAR_TOL)
    prof_rand = mn.single_register_profile(
        mn.random_diagonal_support(114, 625, V2_RANDOM_SEED), 625)
    c["T2_v2_anchor_random"] = (
        abs(mn.share_star(prof_rand, 625) - V2_SHARE_STAR_RANDOM_COMMITTED)
        <= V2_SHARE_STAR_TOL)
    prof_comp = mn.single_register_profile(mn.composite_support(625), 625)
    c["T3_v2_anchor_composite"] = (
        abs(mn.share_star(prof_comp, 625) - V2_SHARE_STAR_COMPOSITE_COMMITTED)
        <= V2_SHARE_STAR_TOL)
    c["T4_model_exact"] = (
        abs(model_share_star(625, 625) - EXACT_MODEL_625_625) <= 1e-12
        and abs(model_share_star(97, 625) - 4 / 625) <= 1e-12)
    expected_gated = ["401,625", "463,625", "541,625", "599,625", "625,625"]
    got_gated = [f"{P},{d}" for P, d in PRIME_POINTS if is_gated(P, d)]
    c["T5_gate_set"] = (got_gated == expected_gated
                        and not is_gated(97, 625)   # Transition-Punkt m=25
                        and not is_gated(625, 25))  # d25 stets deskriptiv
    return c


# === Evaluation ===

def run_replication():
    """Kontrollen zuerst, dann das (P, d)-Gitter, dann der registrierte
    Falsifikator."""
    controls = run_controls()
    controls_ok = all(bool(v) for v in controls.values())

    comp_limit = composite_limit()
    rows = []
    for idx, (P, d) in enumerate(PRIME_POINTS):
        row = run_point(P, d, RANDOM_SEED_BASE + idx)
        row["kind"] = "prime"
        row["flags"] = point_flags(row, comp_limit)
        rows.append(row)
    comp_rows = []
    for c_idx, (P, d) in enumerate(COMPOSITE_POINTS):
        row = run_point(P, d, RANDOM_SEED_BASE + 1000 + c_idx)
        row["kind"] = "composite_control"
        row["flags"] = None
        comp_rows.append(row)

    verdict = verdict_replication(rows, comp_rows, comp_limit, controls_ok)

    return {
        "experiment": EXPERIMENT,
        "prereg_path": PREREG_PATH,
        "controls": controls,
        "controls_ok": controls_ok,
        "rows": rows,
        "composite_rows": comp_rows,
        "composite_overlap_limit": comp_limit,
        "verdict": verdict,
    }


def verdict_replication(rows, comp_rows, comp_limit, controls_ok):
    if not controls_ok:
        return VERDICT_MAP["INVALID"]
    gated = [r for r in rows if r["gated"]]
    outside = sum(1 for r in gated if r["flags"]["outside"])
    overlap = any(r["flags"]["random_overlap"] for r in gated)
    overlap = overlap or any(
        r["share_composite"] >= comp_limit for r in comp_rows)
    if overlap or outside >= FALSIFIER_MIN_OUTSIDE:
        return VERDICT_MAP["REFUTED"]
    if outside == 1:
        return VERDICT_MAP["PARTIAL"]
    return VERDICT_MAP["REPLICATED"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=EXPERIMENT)
    ap.add_argument("--freeze", action="store_true",
                    help="Prereg einfrieren (VOR Auswertung, md5-committet)")
    args = ap.parse_args(argv)
    if args.freeze:
        doc = freeze_prereg()
        with open(PREREG_PATH, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2)
        print("PREREG FROZEN:", doc["md5"])
        print("gated Punkte:", doc["gated_points"])
        print("Composite-Overlap-Limit:",
              f"{doc['thresholds']['composite_overlap_limit']:.6f}")
        return

    doc = load_frozen_prereg()
    res = run_replication()
    res["prereg_md5"] = doc["md5"]
    res["post_hoc_note"] = (
        "Gitter nach dem Freeze (md5 %s) berechnet; Kontrollen zuerst; "
        "reine Arithmetik (deterministisch), 0 QPU." % doc["md5"])
    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)

    print("VERDICT:", res["verdict"])
    print("Kontrollen ok:", res["controls_ok"])
    for k, v in res["controls"].items():
        print(f"  {k}: {v}")
    print(f"{'P':>5} {'d':>5} {'m':>4} {'share*':>8} {'model':>8} "
          f"{'rand':>8} {'comp':>8} {'ratio':>7} gated")
    for r in res["rows"]:
        ratio = (r["share_prime"] / r["model"]
                 if r["model"] and r["model"] > 0 else float("nan"))
        print(f"{r['P']:5d} {r['d']:5d} {r['m']:4d} {r['share_prime']:8.4f} "
              f"{r['model']:8.4f} {r['share_random']:8.4f} "
              f"{r['share_composite']:8.4f} {ratio:7.3f} "
              f"{str(r['gated']):>5}")
    for r in res["composite_rows"]:
        print(f"COMP {r['P']:5d} {r['d']:5d} {r['m']:4d} "
              f"share*={r['share_composite']:.4f} "
              f"(Limit {res['composite_overlap_limit']:.4f})")


if __name__ == "__main__":
    main()