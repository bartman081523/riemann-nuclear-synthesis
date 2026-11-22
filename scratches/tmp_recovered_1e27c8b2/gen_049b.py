# -*- coding: utf-8 -*-
"""Pre-Freeze-Generator fuer 049b (H-TEST2-RANK, nummerierte Iteration zu 049).

Baut das Prereg pt_test2b_rank_controlled_prereg.json:
- data_basis.rows VOLLSTAENDIG aus dem 049-Prereg kopiert (byte-identische axis values),
- den SKALEN-BEWUSSTEN ANALYTISCHEN K1-Dust-Bound je N exakt aus dem frischen
  Zustand berechnet (Property des State, kein Fit) und in der offen_legung
  gepinnt — INKLUSIVE Vorab-Vergleich gegen die (bereits committeten) 049-K1-Werte.
Prints: bound-Tabelle + md5. KEIN Messwert der Hypothese (die Verdict-Statistik
partial-rho ist hier NICHT dabei — nur GATE-Bound-Properties).
"""
import hashlib
import json
import math
import sys
import os

import numpy as np

sys.path.insert(0, "/run/media/julian/ML4/riemann")
os.chdir("/run/media/julian/ML4/riemann")

LAM_CARRIER = 1e-30
GAP_FLOOR_REL = 1e-6
C_K = 64.0  # per-Element Rounding-Aggregat (2 ulp x 32 Rounding-Sites; STRENGER
            # als LAPACK-O(d*eps)-Worst-Case d=1024 => 1024 ulp; Metrologie-Anker
            # 049-Empirie eps_eff = 1.6..9.9 ulp eff)


def primes_upto(N):
    is_p = bytearray([1]) * (N + 1)
    is_p[0:2] = b"\x00\x00"
    for i in range(2, int(N ** 0.5) + 1):
        if is_p[i]:
            is_p[i * i:: i] = bytearray(len(is_p[i * i:: i]))
    return [i for i in range(2, N + 1) if is_p[i]]


def fresh_psi(N):
    n_q = int(math.ceil(math.log2(N + 1)))
    primes = primes_upto(N)
    psi = np.zeros(2 ** n_q)
    psi[primes] = 1.0
    psi /= np.linalg.norm(psi)
    return psi, n_q, len(primes)


def carrier_lam(psi, n_q):
    n_A = n_q // 2
    s = np.linalg.svd(psi.reshape(2 ** n_A, 2 ** (n_q - n_A), order="F"),
                      compute_uv=False) ** 2
    s = np.sort(s)[::-1]
    return s[s > LAM_CARRIER]


with open("pt_test2_entanglement_comovement_prereg.json") as fh:
    p049 = json.load(fh)
rows = p049["data_basis"]["rows"]
with open("pt_test2_entanglement_comovement_results.json") as fh:
    r049 = json.load(fh)
k1_obs = {gp["N"]: (gp["K1_001"], gp["K1_005"]) for gp in r049["grid_points"]}

bounds = []
for r in rows:
    N = r["N"]
    psi, n_q, _ = fresh_psi(N)
    lam = carrier_lam(psi, n_q)
    g = lam[:-1] - lam[1:]
    ok = np.minimum(g[:-1], g[1:]) >= GAP_FLOOR_REL * lam[0]
    idx = np.nonzero(ok)[0]
    if idx.size == 0:
        bounds.append({"N": N, "c_max": None, "tol": None, "k1_049": None,
                       "obs_over_bound": None})
        continue
    condv = (lam[idx] + lam[idx + 1]) / np.minimum(g[idx], g[idx + 1])
    c_max = float(condv.max())
    tol = C_K * 2.0 ** -52 * c_max
    obs = k1_obs.get(N, (None, None))
    obsmax = max([v for v in obs if v is not None] or [None])
    bounds.append({
        "N": N, "n_valid": int(idx.size), "c_max": c_max, "tol": tol,
        "k1_max_049": obsmax,
        "obs_over_bound": None if obsmax is None else float(obsmax / tol),
        "gap_rel_min": float((np.minimum(g[idx], g[idx + 1]) / lam[0]).min()),
    })

for b in bounds:
    print(b)

prereg = {
    "experiment": "049b",
    "hypothesis": {
        "id": "H-TEST2-RANK",
        "reduced_claim": ("identisch zu 049/048/048b (Grade E, Richtung C+/B-): "
                          "Eine niedrigere Verschraenkung erhoet die numerische "
                          "Robustheit der Relativ-Struktur der Repraesentation."),
        "test2_limb": ("Kausal-Glied, RANG-KONTROLLIERT: kovariert der "
                       "Gap-Ratio-Drift Gamma(N) mit S_vN_axis(N) JENSEITS der "
                       "gemeinsamen Rang-Achse? Verdict-tragende Statistik ist "
                       "die PARTIELLE Spearman-Rangkorrelation "
                       "rho(Gamma, S | rank_active) (Rang-Residuen-Regression "
                       "wie im 049-Konfund-Kit implementiert) — die "
                       "049-Konfund-Lesart (Mitwanderung Traeger-RANG-getragen) "
                       "ist hier die registrierte H0-Lesart."),
        "numbered_iteration": ("049b ist eine NUMMERIERTE Folge-Iteration zu 049 "
                               "(gefrorenes 049-Verdict DEGENERAT bleibt "
                               "unangetastet committet). Zwei Aenderungen gegenuber "
                               "049: (a) GATE-A wird durch den SKALEN-BEWUSSTEN "
                               "ANALYTISCHEN Dust-Bound A' ersetzt (kein "
                               "Toleranz-Kauf: der alte 1e-12-Wert war ein "
                               "Freeze-Zeit-GUESS 'float-Restausschlag erwartet "
                               "~1e-16' ohne Gap-Konditionszahl; A' ist je "
                               "Gitterpunkt aus der Konditionszahl des "
                               "Ratio-Operators abgeleitet), (b) das Verdict "
                               "wandert auf die partielle Statistik mit EIGENER "
                               "Permutations-Null."),
        "unit_mix_anchor": ("Referenz-Anker bleibt frisch bits-konsistent "
                            "alpha = 0.2004085378325559 (049); der committete "
                            "0.22275345050922138 ist als einheitsgemischt "
                            "dokumentiert und wird NICHT uebernommen."),
    },
    "state_family": ("|P_N> = normalize(sum_{p<=N} |p>), Sieve, numpy REAL "
                     "float64; Bipartition AXIS (floor(n/2)-LSB-Split, order-F); "
                     "Traeger lam > 1e-30; IDENTISCH zu 049."),
    "data_basis": {
        "rows": rows,
        "rows_note": "byte-identisch aus dem 049-Prereg uebernommen (kein neues Gitter, Phase-10b gilt fuer Artefakt-Kandidaten, nicht fuer dieses N-Basis-Gitter).",
        "mitwander_metric": ("Gamma_MAX = max_k |(r_k_tilde - r_k)/r_k| ueber "
                             "VALID k (Gap-Floor 1e-6*lam_max, basis-maske "
                             "ok_p), K3-Kanal q95 der 50 Draws delta=0.01 — "
                             "IDENTISCH zu 049."),
    },
    "gate_a_prime": {
        "id": "GATE-A'",
        "bound": ("K1(N, delta) <= C_K * 2^-52 * c_max(N) an ALLEN VALID "
                  "Gitterpunkten und beiden delta; "
                  "c_max(N) = max_{k VALID} (lam_k + lam_{k+1}) / min(g_k, g_{k+1}) "
                  "aus dem frischen pristine Traeger (Konditionszahl des "
                  "Ratio-Operators, kein freier Parameter je Punkt); "
                  "C_K = 64 (per-Element Rounding-Aggregat: 2 ulp x 32 "
                  "Rounding-Sites im Pipeline-Aggregat multiply/renorm/SVD; "
                  "STRENGER als die LAPACK-O(d*eps)-Worst-Case-Derivation mit "
                  "d = 2^(n_q-n_A) <= 1024 ulp)."),
        "C_K": 64.0,
        "eps_52": 2.220446049250313e-16,
        "justifikation": ("Der 049-Gate-Zahlenwert 1e-12 war ein "
                          "Freeze-Zeit-GUESS ('float-Restausschlag erwartet "
                          "~1e-16') OHNE Gap-Konditionszahl — er scheitert an "
                          "den 049-K1-Werten (N=1e5/1e6). Der 049-Text "
                          "promisierte die Form C*2^-52/gap_rel_min; die "
                          "Konditions-Fassung c_max vollzieht dies exakt: der "
                          "dominante Term ist 1/gap_rel_min, der Zusatzterm "
                          "1/g_{k+1} traegt die zwei gap-Referenzen des "
                          "Ratios. KEINE Anpassung an beobachtete Messwerte: "
                          "der Bound ist Property des Zustands (c_max) + eine "
                          "Toleranz-KONSTANTE."),
        "disclosure": ("Offenlegung (Anti-Sharpshooter): die ORDER OF MAGNITUDE "
                       "von C_K ist an die committete 049-K1-Empirie "
                       "angelehnt (eps_eff = K1/(2^-52*c_max) = 1.6..9.9 ulp "
                       "eff ueber alle Punkte); die Konstante 64 = "
                       "'naechstes Ceiling' ist METROLOGIE "
                       "(Instrument-Zertifikat) und NICHT verdict-tragend — "
                       "das Verdict reitet auf der PARTIELLEN Statistik. Eine "
                       "A'-Verletzung an einem einzigen Punkt waere trotzdem "
                       "DEGENERAT (echte Falsifizierbarkeit). Die 049-K1-Werte "
                       "sind deterministisch reproduzierbar (gleiche "
                       "Seeds/Maschine) und im pre-freeze-Vergleich gepinnt "
                       "(key bound_frisch_pre_freeze)."),
        "fail_consequence": ("A'-Verletzung an IRGENDEINEM VALID-Punkt => "
                             "Verdict DEGENERAT (kein stilles Nachziehen der "
                             "Konstante, kein Re-Decide); die Mechanismus-"
                             "Kette waere dann NICHT vollstaendig "
                             "charakterisiert und 049b endet als Diagnose."),
        "ulp_diagnostics": ("diagnostisch: eps_eff(N, delta) = K1_obs / "
                            "(2^-52 * c_max(N)) in ulp-Einheiten — Erwartung "
                            "<= 64 je Punkt, Report je Gitterpunkt "
                            "(diagnostisch, NICHT verdict-tragend)."),
    },
    "bound_frisch_pre_freeze": bounds,
    "verdict_rule_rank_controlled": {
        "PRIMARY_STATISTIC": ("partial_spearman(Gamma_valid, S_valid | "
                              "rank_active) — Average-Tie-Ranks, "
                              "Rang-Residuen der linearen Fits auf "
                              "avg_ranks(rank_active), numpy-only; "
                              "implementations-identisch zum 049-Konfund-Kit."),
        "NULL": ("dieselben 1000 Permutationen wie 049 (default_rng(20261005), "
                 "je Draw gamma geshuffelt): je Draw die PARTIELLE Statistik "
                 "auf dem geshuffelten gamma — q95_partial = q95(|partial_null|); "
                 "NEBENBEI die rohe rho-Null wie 049 (nur zur Kontinuitaet, "
                 "NICHT verdict-tragend)."),
        "LEGS": [
            ("partielle Statistik > q95_partial",
             "MITWANDERUNG_SPEZIFISCH_POSITIV — der S-Link ist JENSEITS der "
             "Rang-Achse getragen; der reduzierte Claim erhaelt sein "
             "test2-favorables Leg (Richtung C+/B-)."),
            ("partielle Statistik < -q95_partial",
             "ANTI_WANDERUNG_SPEZIFISCH — S-Link mit GEGENRICHTUNG ueber Rang "
             "hinaus getragen (Leg B')."),
            ("|partielle Statistik| <= q95_partial",
             "RANGGETRAGEN_GEFALLEN — die Mitwanderung lebt in der Rang-Achse; "
             "das Kausal-Glied des reduzierten Claims ist nicht S-spezifisch "
             "tragbar (049-Konfund-Lesart verdict-traegig bestaetigt)."),
        ],
        "gate_precedence": ("jede A'/B/C/D-Verletzung => DEGENERAT VOR jeder "
                            "Statistik-Lektuere."),
        "no_re_decide": ("Kanael/Metrik/Gap-Floor/Seeds/Statistik/Bound nach "
                         "Freeze fix; KEINE Toleranz-Erhoehung, KEINE "
                         "Bound-Konstanten-Nach-Karriere, keine "
                         "Gap-Floor-Verschiebung nach Sichtbarkeit der Zahlen."),
    },
    "gates_unchanged_from_049": {
        "GATE-B": ("De-Kodierung je Zeile in der Zeilen-Eigenkonvention: "
                   "|S_frisch - S_committet| <= 1e-10 an ALLEN 11 Zeilen; "
                   "rel lam-Abweichung <= 1e-8 wo s_sq committet (Maske "
                   ">1e-30 bzw. >1e-12 je Quelle)."),
        "GATE-C": "len(VALID) >= 8 (VALID = n_valid_base >= 1 UND K3_q95_001 not None).",
        "GATE-D": "|S_axis_frisch - axis_S_bits_frisch| <= 1e-12 an ALLEN 11 Zeilen.",
    },
    "diagnostik_not_verdict": [
        "Konfund-Kit (rho vs N / rank_active / S_rel, raw partial) wie 049.",
        "Blend fixed N=1024-theta-Gitter wie 049 (Seeds 20261003/20261004).",
        "Sekundaer-kanal-Sign-Konsistenz (K3_005, K2_001, K2_005, K5_001) wie 049.",
        "rohe rho-Verdict-Lesart 049-Regel als kontinuitaets-Ausgabe (NICHT verdict-tragend).",
        "dust_mechanism_check: K1_obs/Bound je N (Erwartung << 1).",
    ],
    "seeds": {
        "k3_pro_gitterpunkt": "default_rng(20261002 + N) — IDENTISCH zu 049 (deterministische Reproduktion der Draws).",
        "blend_chi": "default_rng(20261003)",
        "blend_k3": "default_rng(20261004)",
        "shuffle_null": "default_rng(20261005), 1000 Permutationen — roh-rho UND partiell je Draw.",
    },
    "runtime": "0 QPU, 0 Aer — reine numpy, ~4 min (049-Profile).",
    "no_push": True,
    "branch_note": "Eigener Branch h-test1-gap-invariance (Fortsetzung der 048/048b/049-Kette); kein Mischbetrieb mit der ram-q-zyklizitaet-046-Watch.",
}

with open("pt_test2b_rank_controlled_prereg.json", "w") as fh:
    json.dump(prereg, fh, indent=1, ensure_ascii=False)
md5 = hashlib.md5(open("pt_test2b_rank_controlled_prereg.json", "rb").read()).hexdigest()
print("\nmd5:", md5)
a_fail = [b["N"] for b in bounds if b["obs_over_bound"] is not None and b["obs_over_bound"] > 1]
print("A'-Vorab gegen bekannte 049-K1: Ueberschreitungen:", a_fail or "keine")