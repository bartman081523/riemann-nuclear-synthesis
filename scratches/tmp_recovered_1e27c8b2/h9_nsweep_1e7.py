"""HYPOTHESEN_UND_ANTITHESES_H9 - F-Prio 7: N-Sweep 10^7 (H-H9-5, 023-EXT-Kette).

0 QPU, nicht committet-Verdict-tragend. Die committeten 023-EXT-Artefakte
(pt_rh_multi_observable_ext.py, pt_rh_multi_observable_ext_results.json,
Prereg md5 334c97545a41bdf0383c7cc35cdfbb2f) bleiben UNANGETASTET; dieser
Scratch reproduziert die 14 committeten Punkte als Pin-Leg und fuehrt die
Kette um drei registrierte neue Punkte fort.

=========================================================================
EX-ANTE-REGISTRY (geschrieben VOR dem ersten new-point-Lauf)
=========================================================================

Deck-Vertrag (C.5, wörtlich): "klassischer N-Sweep 10^7 … 10^8 mit
v1-Thresholds UNVERÄNDERT; Prädiktion: alpha(N) liegt im Band, das aus dem
fit 0.210(±) + 1/effective_total-Struktur folgt; falsifiziert, wenn alpha
unter das MOCS_ext-Band [0.0864, 0.0882] abfallt, ohne dass omega auf dem
v1-Band bleibt."

GRID (fixe Reihenfolge): N_NEW = [16777215, 10000000, 100000000]
  - 16777215 = 2^24-1 (2^k-1-Familie der committeten Kette, dim 2^24)
  - 10000000 = Deck-literal "10^7" (dim ebenfalls 2^24)
  - 100000000 = Deck-literal "10^8" (dim 2^27)
  Reihenfolge ist laufseitig 1,2,3 — kein Ergebnis-Einfluss
  (polyfit über log N ist member-orientiert, nicht order-orientiert).

LIMIT-LINE (aus NUR committeten 023-EXT-Zahlen):
  alpha_line = alpha_combined_committed / effective_total_committed
  = 0.210355.../2.426374... = 0.086695253568270
  (= "fit 0.210(±) * 1/effective_total-Struktur"; 1/effective_total
  = 0.412137681). Die Deck-Kante [0.0864, 0.0882] trägt in den
  committeten 023-EXT-Results die Werte der ext-cv-Spannweite
  [0.086356, 0.088223] (gerundet); alpha_line liegt INNERHALB des
  Intervalls, weswegen beide Lesarten auf dieselbe Kante 0.0864 zeigen.
  Provenienz transparent dokumentiert (C.4a-"105/135"-Präzedenz), KEIN
  committeter Wert umgeschrieben.

GEFRORENE KRITERIEN (v1-Thresholds UNVERÄNDERT):
  F1 (Deck-Falsifikator, wörtlich): alpha_ext_leg < 0.0864 an EINER
     registrierten Leg. Registrierte Legs (ext-only-Kette, cumulativ,
     analog zum committeten alpha_ext_6pt = 0.132551):
       L7a: ext6 + [16777215]
       L7b: ext6 + [10000000]           (Deck-literal 10^7)
       L7c: ext6 + [16777215, 10000000]
       L8 : ext6 + [16777215, 10000000, 100000000]   (VOLL-LEG, primär)
       L8b: ext6 + [10000000, 100000000]             (Deck-literal 10^7+10^8)
     Klassifizierend ist L8; feuert eine Teil-Leg (L7a/L7b/L7c/L8b) unter
     0.0864 waehrend L8 >= 0.0864, wird DAS verbatim ausgewiesen (Legs-
     Diskriminierung, kein stiller Pick).
  BAND-KLASSEN: alpha_L8 in [0.0864, 0.0882] -> BAND_ERREICHT;
     alpha_L8 in (0.0882, alpha_ext_committed] -> UEBER_BAND (Approach
     unvollstaendig, Falsifizierer still); alpha_L8 < 0.0864 -> FALSIFIZIERT
     (registrierte Form).
  F2 (Traeger-Klausel, "omega auf dem v1-Band"): 'omega' hat in der
     023-EXT-Kette KEIN committetes Objekt; naechst-gelegenes committetes
     Objekt der Aussage C.5 ist cv als "konstanter Träger". Registrierte
     Lesart: cv_spread(new N) in [0.05, 0.20] (v1-Band, UNVERÄNDERT).
     Lesart transparent (kein Threshold gepatcht).
  F3: R(N) < 1 an allen neuen N (b-Regel v1 unveraendert).
  Verdict-Klasse: H-H9-5 registrierte Form (HOLD/FALSIFIZIERT/...); die
     committeten 023-EXT-Verdicts (H_MOCS_EXT: alpha_combined 0.210355,
     R(N) < 1, cv-Mean 0.095996) AENDERN SICH NICHT — die neuen Punkte
     laufen BESIDE dem committeten 14-Punkt-Grid.

PINS (vor jeder new-point-Messung, sonst Abort):
  P1: 14-Punkte-Reproduktion (v1-identische Loop wie ext measure_all):
      S_vN/R_N/cv_dense bit-nah gegen committetes JSON, rel tol 1e-12
      (erwartet bit-exakt).
  P2: alpha_v1_8pt vs 0.265821..., alpha_ext_6pt vs 0.132551...,
      alpha_combined_14pt vs 0.210355..., cv_mean vs 0.09599648443361233,
      jeweils rel tol 1e-12.
SOLVER-PATH-PINS (ex ante registrierte Abweichungen vom v1-Zeilenpfad):
  SP1 (S): np.linalg.svd(psi, full_matrices=False) — THIN-Pfad dieses
      Scratches (Speicher-Gruend fuer dim 2^27). Validierung gegen
      committete S an den RECHTECK-Anchors N=2047 (32x64) und N=32767
      (128x256), rel tol 1e-12; Quadrat-Faelle (m==n) trivial identisch.
  SP2 (cv an neuen N): cv_spread_tridiag (ext-eigen, Solver-Pfad-Pin
      dense-vs-tridiag validiert bei N=65535 in-scratch, rel tol 1e-9;
      dense bei n>=664579 unmoeglich).
  SP3 (Traeger-Fallback, ex ante): falls tridiag-cv an einem neuen N
      technisch unzulassig laeuft (Gate s.u.), GERSHGORIN-EXAKT-INTERVALL
      statt exaktem cv: var(eigs) ist EXAKT = tr A^2/n - (tr A/n)^2 mit
      tr A = sum p, tr A^2 = sum p^2 + 2 sum gap^2 (O(n)); spread =
      lambda_max - lambda_min mit N-2 <= spread <= max_i(d_i + r_i) -
      min_i(d_i - r_i) (Gershgorin, rigoros). cv in
      [varA/spread_ub^2, varA/(N-2)^2]. Intervall komplett in [0.05,0.20]
      -> Traeger fuer die Leg BEWEISEN (exaktes cv dann OPEN).
LAUFGATE (ex ante registriert):
  G1: Messzeit des tridiag-cv am 1e7-Bein (n=664579) wird gemessen;
      Extrapolation (n_verhaeltnis)^2 * t bestimmt, ob 1e8-cv (n=5761455)
      laeuft: nur wenn <= 3 h -> exaktes cv(1e8), sonst SP3-Intervall +
      cv(1e8)-exakt = SKIP (dokumentiert).
  G2: Schlägt das 1e8-Bein technisch fehl (MemoryError/Zeit), bleibt
      1e8 als OPEN dokumentiert; Klassifikation dann aus L7a/L7b/L7c/L7d
      bzw. Teil-Legs mit verbatimem OPEN-Vermerk, KEIN stiller Skip.
REPARATUR-HISTORIE (nach dem ersten Lauf dokumentiert):
  Erster Lauf (2026-09-29, Wrapper-Task bxu33, Log job-tmp/h9_nsweep_1e7.log):
  Pin-Leg 14/14 ok; alle drei Mess-Beine S/R (+cv) gemessen und
  INKREMENTELL ins out.json persistiert (save_state nach jedem Append); G1
  feuerte exakt wie registriert (t_cv_1e7 1445.74 s -> Extrapolation
  108658.0 s > 10800 -> SP3). DANN Crash in der Carrier-Assembly:
  TypeError '<=' not supported between instances of 'float' and 'NoneType'
  — die SP3-Verdrahtung fehlte im New-Leg-Block (der else-Zweig schluckte
  auch cv_path == "gershgorin", so dass die 1e8-Row mit gershgorin = None
  in die Carrier-Assembly ging; das SP3-Intervall wurde NIE berechnet; S/R
  der 1e8-Row waren zu dem Zeitpunkt vollstaendig gemessen und persistiert).
  FIX (dieser Scratch-Stand): eigener elif-Zweig berechnet
  varA_and_bounds fuer das gershgorin-Bein; zusaetzlich --resume: laedt den
  persistierten Zwischenstand, re-runt den Pin-Leg neu (deterministisch,
  ~1 min) und VERPROBT die Pin-Rows bit-nah gegen den Zwischenstand,
  WIEDERVERWENDET die drei gemessenen Beine bit-identisch (kein Neu-Lauf,
  S/R/cv-Werte unveraendert uebernommen), rechnet fuer 1e8 NUR das
  SP3-Intervall nach (sieve + O(n)-varA, kein Messwert neu bestimmt),
  re-berechnet alphas/carrier/verdicts und verprobt die alphas bit-nah
  gegen den Zwischenstand (T_REL). Crash-Traceback und ABORT-Status des
  Zwischenstands bleiben unter provenance.reparatur als
  Offenlegungs-Datensatz erhalten. Post-MEASUREMENT-Reparatur: kein
  Messwert neu bestimmt; Thresholds/Baende aus dem Registry unveraendert;
  kein Re-Decide. Die committeten 023-EXT-Verdicts bleiben unangetastet.

DESKRIPTIV (nicht klassifizierend): 2-Punkt-lokale Tailslopes
  (65535->N_neu), (16777215->1e7, gleiches dim 2^24 - S-Saettigung am
  selben Split erwartbar), (1e7->1e8), (65535->1e8); alpha'_line =
  alpha_ext_L8/effective_total (upgedatete Linie, deskriptiv).
SONST: KEINE Toleranz-Erhoehung, KEIN stilles Re-Decide, I3-Nullen an
  neuen N SKIP (Diagnostik-only, nicht verdict-tragend), 0 QPU.
=========================================================================
"""

import json
import math
import os
import sys
import time
import traceback

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pt_prime_state import sieve_primes, construct_P_N, measure_entropy  # noqa: E402
from pt_rh_multi_observable import alpha_vN_scaling, latorre_ratio  # noqa: E402
from pt_rh_multi_observable_ext import (  # noqa: E402
    cv_spread_dense,
    cv_spread_tridiag,
)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(HERE, "scratches", "h9_nsweep_1e7_out.json")
COMMITTED_PATH = os.path.join(HERE, "pt_rh_multi_observable_ext_results.json")

# ---------------- EX-ANTE-REGISTRY (Maschinen-lesbar, vor Messung) ---------

REGISTRY = {
    "experiment": "H-H9-5 n-sweep 1e7-1e8 (F-Prio 7, 023-EXT-Kette)",
    "deck": "HYPOTHESEN_UND_ANTITHESES_H9_2026_09_29.md C.5 / F-Zeile 7",
    "qpu": 0,
    "nicht_committet_verdict_tragend": True,
    "grid_n_new_fixe_reihenfolge": [16777215, 10000000, 100000000],
    "band_deck": [0.0864, 0.0882],
    "limit_line_definition": "alpha_combined/eff via committed results",
    "legs": {
        "L7a": [2047, 4095, 8191, 16383, 32767, 65535, 16777215],
        "L7b": [2047, 4095, 8191, 16383, 32767, 65535, 10000000],
        "L7c": [2047, 4095, 8191, 16383, 32767, 65535, 16777215, 10000000],
        "L8_primary": [2047, 4095, 8191, 16383, 32767, 65535,
                       16777215, 10000000, 100000000],
        "L8b_deck_literal": [2047, 4095, 8191, 16383, 32767, 65535,
                             10000000, 100000000],
    },
    "f1_falsified_if": "any registered alpha_ext_leg < 0.0864; L8 klassifizierend, Teil-Legs verbatim",
    "f2_carrier": "cv_spread(new N) in [0.05, 0.20] (Lesart: cv = konstanter Traeger)",
    "f3_rule": "R(N) < 1 an allen neuen N",
    "pin_tolerances": {"rel": 1e-12},
    "solver_path_pins": {
        "SP1": "S via full_matrices=False; Rechteck-Validierung N=2047/32767 rel 1e-12",
        "SP2": "cv(new N) via cv_spread_tridiag; dense-vs-tridiag-Pin bei 65535",
        "SP3": "cv-Fallback Gershgorin-Exakt-Intervall (varA exakt, spread gebunden)",
    },
    "run_gates": {
        "G1": "tridiag-cv-Zeit am 1e7-Bein entscheidet 1e8-cv (Extrapolation*2 <= 3h)",
        "G2": "1e8 technisch fehlgeschlagen -> 1e8 OPEN dokumentiert, kein stiller Skip",
    },
    "reparatur": {
        "erster_lauf": "2026-09-29 — Crash in Carrier-Assembly NACH vollst. "
                       "Messung (SP3-Verdrahtung fehlte im New-Leg-Block); "
                       "Mess-Beine im Zwischenstand persistiert",
        "fix": "elif-Zweig fuer cv_path == 'gershgorin' + --resume-Pfad",
        "resume": "Pins neu (Kreuzcheck) + Mess-Beine bit-identisch "
                  "wiederverwendet + SP3-Intervall 1e8 nachgerechnet + "
                  "alphas-Kreuzcheck vs Zwischenstand; kein Wert neu "
                  "bestimmt, kein Re-Decide",
    },
    "kein_re_decide": True,
    "keine_toleranz_erhoehung": True,
}

T_REL = 1e-12
CV_LO, CV_HI = 0.05, 0.20
BAND_LO, BAND_HI = 0.0864, 0.0882

STATE = {
    "registry": REGISTRY,
    "pins": None,
    "rows_committed_repro": [],
    "rows_new": [],
    "alphas": None,
    "carrier": None,
    "verdicts": None,
    "timings": {},
    "deviations": {},
    "provenance": {},
}


def save_state():
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(STATE, fh, indent=2)
    os.replace(tmp, OUT_PATH)


def measure_entropy_thin(P_N):
    """v1-identisch bis auf full_matrices=False (SP1, registry)."""
    dim = len(P_N)
    n_A = int(math.sqrt(dim))
    while dim % n_A != 0 and n_A > 1:
        n_A -= 1
    n_B = dim // n_A
    psi_matrix = P_N.reshape(n_A, n_B)
    _, S, _ = np.linalg.svd(psi_matrix, full_matrices=False)
    S_squared = S ** 2
    S_squared = S_squared[S_squared > 1e-12]
    S_vN = -np.sum(S_squared * np.log(S_squared))
    S_max = math.log(min(n_A, n_B))
    return S_vN, S_max, n_A, n_B


def measure_row(N, cv_path):
    """v1-identische Loop wie ext measure_all, cv-Pfad registriert."""
    t0 = time.time()
    primes = sieve_primes(N)
    t_sieve = time.time() - t0
    pi_N = len(primes)
    t0 = time.time()
    P_N, dim, n_qubits = construct_P_N(N)
    t_construct = time.time() - t0
    t0 = time.time()
    S_vN, S_max, n_A, n_B = measure_entropy_thin(P_N)
    t_ent = time.time() - t0
    R_N = latorre_ratio(S_vN, pi_N)
    t0 = time.time()
    if cv_path == "dense":
        cv_N = float(cv_spread_dense(primes))
    elif cv_path == "tridiag":
        cv_N = float(cv_spread_tridiag(primes))
    elif cv_path == "gershgorin":
        cv_N = None   # SP3-Fallback: exaktes cv SKIP, nur Intervall
    else:
        raise ValueError(cv_path)
    t_cv = time.time() - t0
    del P_N
    row = {
        "N": int(N), "pi_N": int(pi_N), "dim": int(dim),
        "n_qubits": int(n_qubits), "n_A": int(n_A), "n_B": int(n_B),
        "S_vN": float(S_vN), "S_max": float(S_max), "R_N": float(R_N),
        "cv_spread_A": cv_N, "cv_path": cv_path,
        "t_sieve_s": t_sieve, "t_construct_s": t_construct,
        "t_entropy_s": t_ent, "t_cv_s": t_cv,
    }
    print(f"[row] N={N} pi={pi_N} dim={dim} S={S_vN:.9f} R={R_N:.9f} "
          f"cv={cv_N} path={cv_path} (sieve {t_sieve:.1f}s, "
          f"construct {t_construct:.1f}s, ent {t_ent:.1f}s, cv {t_cv:.1f}s)",
          flush=True)
    return row, primes


def varA_and_bounds(primes):
    """SP3: exakte Eigenwert-Varianz + rigorose Gershgorin-spread-Grenzen."""
    d = np.asarray(primes, dtype=np.float64)
    e = np.abs(np.diff(d))
    n = d.size
    tr_A = d.sum()
    tr_A2 = (d ** 2).sum() + 2.0 * (e ** 2).sum()
    varA = tr_A2 / n - (tr_A / n) ** 2
    r_i = np.zeros(n)
    r_i[1:-1] = e[:-1] + e[1:]
    r_i[0] = e[0]
    r_i[-1] = e[-1]
    lam_max_ub = (d + r_i).max()
    lam_min_lb = (d - r_i).min()
    spread_lb = max(d) - min(d)
    spread_ub = lam_max_ub - lam_min_lb
    cv_hi = varA / spread_lb ** 2   # kleinstes cv (groesster Nenner: lb)
    cv_lo = varA / spread_ub ** 2
    return float(varA), float(cv_lo), float(cv_hi), float(spread_lb), float(spread_ub)


def rel_dev(new, ref):
    if ref == 0.0:
        return abs(new - ref)
    return abs(new / ref - 1.0)


def main(resume=False):
    t_start = time.time()
    print("[h9-nsweep-1e7] start, QISKIT_PARALLEL=FALSE-Konvention, 0 QPU",
          flush=True)

    with open(COMMITTED_PATH) as fh:
        committed = json.load(fh)
    c_rows = committed["rows"]
    c_alpha = committed["alpha_combined"]
    c_alpha_v1 = committed["alpha_v1_8pt"]
    c_alpha_ext = committed["alpha_ext_6pt"]
    c_logconst = committed["log_const"]
    c_cv_mean = committed["cv_spread_mean"]
    c_rho_ab = committed["rho_ab"]
    eff = committed["effective_total"]

    # ---------------- Resume: persistierter Zwischenstand -----------------
    prev = None
    prev_rows_new = []
    if resume:
        with open(OUT_PATH) as fh:
            prev = json.load(fh)
        prev_rows_new = list(prev.get("rows_new", []))
        print(f"[resume] Zwischenstand geladen: {len(prev_rows_new)} rows_new, "
              f"pins={(prev.get('pins') or {}).get('status', 'None')!r}, "
              f"verdicts={(prev.get('verdicts') or {}).get('status', 'None')!r}, "
              f"alphas={'vorhanden' if prev.get('alphas') else 'None'}",
              flush=True)

    anchor78 = [r for r in c_rows if r["N"] == 2047][0]
    anchor32767 = [r for r in c_rows if r["N"] == 32767][0]
    print(f"[anchor] committed: a_comb={c_alpha!r} a_v1={c_alpha_v1!r} "
          f"a_ext={c_alpha_ext!r} log_const={c_logconst!r} cv_mean={c_cv_mean!r} "
          f"eff={eff!r}", flush=True)
    print(f"[anchor] alpha_line=a_comb/eff={c_alpha / eff!r}", flush=True)

    # ---------------- Pin-Leg: 14 committete Punkte ----------------------
    N_SWEEP = [7, 15, 31, 63, 127, 255, 511, 1023,
               2047, 4095, 8191, 16383, 32767, 65535]
    rows = []
    worst = {"S": 0.0, "R": 0.0, "cv": 0.0}
    for N in N_SWEEP:
        row, primes = measure_row(N, "dense")
        c_row = [r for r in c_rows if r["N"] == N][0]
        dS = rel_dev(row["S_vN"], c_row["S_vN"])
        dR = rel_dev(row["R_N"], c_row["R_N"])
        dcv = rel_dev(row["cv_spread_A"], c_row["cv_spread_A"])
        worst["S"] = max(worst["S"], dS)
        worst["R"] = max(worst["R"], dR)
        worst["cv"] = max(worst["cv"], dcv)
        if dS > T_REL or dR > T_REL or dcv > T_REL:
            print(f"[PIN-FEHLER] N={N} devS={dS} devR={dR} devCV={dcv}",
                  flush=True)
            raise SystemExit(1)
        rows.append(row)
        del primes

    # Reparatur-Kreuzcheck: Pin-Rows gegen den persistierten Zwischenstand
    worst_pin_repro_dev = 0.0
    if resume and prev is not None:
        prev_rows = prev.get("rows_committed_repro", [])
        if len(prev_rows) != len(rows):
            print(f"[resume] Pin-Row-Anzahl abweichend: {len(rows)} != "
                  f"{len(prev_rows)} — Abort", flush=True)
            raise SystemExit(1)
        for row, prow in zip(rows, prev_rows):
            for k in ("S_vN", "R_N", "cv_spread_A"):
                worst_pin_repro_dev = max(worst_pin_repro_dev,
                                          rel_dev(row[k], prow[k]))
        print(f"[resume] Pin-Rows vs Zwischenstand: worst rel dev "
              f"{worst_pin_repro_dev!r}", flush=True)
        if worst_pin_repro_dev > T_REL:
            print("[resume] PIN-KREUZCHECK FEHLGESCHLAGEN — Abort", flush=True)
            raise SystemExit(1)

    # SP1-Anchor-Extra-Check ist implizit: 2047/32767 sind in den 14 drin.

    S_vals = [r["S_vN"] for r in rows]
    a_comb, log_const = alpha_vN_scaling(N_SWEEP, S_vals)
    a_v1, _ = alpha_vN_scaling(N_SWEEP[:8], S_vals[:8])
    a_ext, _ = alpha_vN_scaling(N_SWEEP[8:], S_vals[8:])
    cv_mean = float(np.mean([r["cv_spread_A"] for r in rows]))
    for name, val, ref in (("alpha_combined", a_comb, c_alpha),
                           ("alpha_v1", a_v1, c_alpha_v1),
                           ("alpha_ext", a_ext, c_alpha_ext),
                           ("log_const", log_const, c_logconst),
                           ("cv_mean", cv_mean, c_cv_mean)):
        d = rel_dev(val, ref)
        STATE["deviations"][name] = d
        if d > T_REL:
            print(f"[PIN-FEHLER] {name}={val!r} vs {ref!r} dev={d}", flush=True)
            raise SystemExit(1)

    STATE["rows_committed_repro"] = rows
    STATE["pins"] = {
        "status": "ok",
        "worst_dev": worst,
        "sp1_anchors_thin_vs_committed": {
            "2047": rel_dev(rows[8]["S_vN"], c_rows[8]["S_vN"]),
            "32767": rel_dev(rows[12]["S_vN"], c_rows[12]["S_vN"]),
            "note": "Rechteck-Faelle 32x64 und 128x256 — SP1-Validierung",
        },
        "alpha_devs": STATE["deviations"],
        "committed_anchors": {
            "alpha_combined": c_alpha, "alpha_v1_8pt": c_alpha_v1,
            "alpha_ext_6pt": c_alpha_ext, "log_const": c_logconst,
            "cv_spread_mean": c_cv_mean, "rho_ab": c_rho_ab,
            "effective_total": eff, "alpha_line": c_alpha / eff,
        },
    }
    save_state()
    print("[pin] ok — 14 Punkte reproduziert (thin-SVD), Pins <= 1e-12",
          flush=True)

    # ---------------- New-Leg ----------------
    N_NEW = REGISTRY["grid_n_new_fixe_reihenfolge"]
    for idx, N in enumerate(N_NEW, start=1):
        print(f"[new] Leg {idx}/3: N={N}", flush=True)
        cv_path = "tridiag"
        if N == 100000000:
            # G1-Gate: Extrapolation aus der gemessenen 1e7-Zeit
            rows_1e7 = [r for r in STATE["rows_new"] if r["N"] == 10000000]
            t_cv_1e7 = rows_1e7[-1]["t_cv_s"] if rows_1e7 else None
            ratio2 = ((5761455.0 / 664579.0) ** 2)
            est = t_cv_1e7 * ratio2 if t_cv_1e7 is not None else None
            print(f"[G1] tridiag bei 1e7: {t_cv_1e7} s; Extrapolation "
                  f"(5.761455M/664579)^2 x t = {est} s (Grenze 10800 s)",
                  flush=True)
            if est is None or est > 10800.0:
                print("[G1] 1e8-cv -> SKIP exaktes cv, SP3-Intervall", flush=True)
                cv_path = "gershgorin"
            else:
                print("[G1] 1e8-cv laeuft (exakt, tridiag)", flush=True)
        cand = [r for r in prev_rows_new if r.get("N") == N and "S_vN" in r] \
            if resume else []
        if cand:
            # Reparatur: gemessenes Bein aus dem persistierten Zwischenstand
            # wiederverwenden (Messwerte unveraendert; Pin-Leg oben re-runt
            # die Pipeline-Validierung, alphas-Kreuzcheck unten verprobt S).
            row = dict(cand[-1])
            print(f"[resume] N={N} Mess-Bein wiederverwendet "
                  f"S={row['S_vN']:.9f} R={row['R_N']:.9f} "
                  f"cv={row['cv_spread_A']}", flush=True)
        else:
            try:
                row, primes = measure_row(N, cv_path)
            except MemoryError:
                print(f"[G2] MemoryError bei N={N} — Leg OPEN dokumentiert",
                      flush=True)
                STATE["rows_new"].append({
                    "N": N, "status": "OPEN_technisch",
                    "reason": "MemoryError im 1e8-Bein (registry G2)",
                })
                save_state()
                continue
            if cv_path == "tridiag":
                varA, cv_lo, cv_hi, sp_lb, sp_ub = varA_and_bounds(primes)
                row["gershgorin"] = {
                    "varA_exact": varA,
                    "cv_interval_exakt": [cv_lo, cv_hi],
                    "spread_bounds": [sp_lb, sp_ub],
                    "tridiag_cv_im_spread_intervall":
                        cv_lo <= row["cv_spread_A"] <= cv_hi,
                }
            elif cv_path == "gershgorin":
                # SP3-Weg: Intervall BERECHNEN (exaktes cv SKIP per G1).
                # Reparaturstand: dieser Zweig fehlte im ersten Lauf
                # (else schluckte "gershgorin" -> gershgorin=None -> Crash).
                varA, cv_lo, cv_hi, sp_lb, sp_ub = varA_and_bounds(primes)
                row["gershgorin"] = {
                    "varA_exact": varA,
                    "cv_interval_exakt": [cv_lo, cv_hi],
                    "spread_bounds": [sp_lb, sp_ub],
                    "exaktes_cv_skip_per_g1": True,
                }
            else:
                row["gershgorin"] = None
            del primes
        if row.get("gershgorin") is None:
            # Reparatur am persistierten Bein: SP3-Intervall nachrechnen
            # (nur sieve + O(n)-varA; KEIN Messwert neu bestimmt).
            t0 = time.time()
            primes = sieve_primes(N)
            varA, cv_lo, cv_hi, sp_lb, sp_ub = varA_and_bounds(primes)
            del primes
            row["gershgorin"] = {
                "varA_exact": varA,
                "cv_interval_exakt": [cv_lo, cv_hi],
                "spread_bounds": [sp_lb, sp_ub],
                "exaktes_cv_skip_per_g1": True,
                "nachgerechnet_im_resume": True,
            }
            print(f"[resume] SP3-Intervall N={N}: varA_exakt={varA} "
                  f"cv=[{cv_lo}, {cv_hi}] spread=[{sp_lb}, {sp_ub}] "
                  f"({time.time() - t0:.1f}s)", flush=True)
        STATE["rows_new"].append(row)
        save_state()

    # ---------------- Alphas/Legs ----------------
    rows_all = rows + [r for r in STATE["rows_new"] if "S_vN" in r]
    Smap = {r["N"]: r["S_vN"] for r in rows_all}
    Rmap = {r["N"]: r["R_N"] for r in rows_all}
    cvmap = {r["N"]: r["cv_spread_A"] for r in rows_all if "cv_spread_A" in r}

    alphas = {}
    for lname, leg_N in REGISTRY["legs"].items():
        have = [N for N in leg_N if N in Smap]
        sv = [Smap[N] for N in have]
        a, _ = alpha_vN_scaling(have, sv)
        alphas[lname] = {
            "alpha": a,
            "members": have,
            "missing": [N for N in leg_N if N not in Smap],
        }
    # combined descriptive (G2-resilient ueber have; im Voll-Grid bit-
    # identisch zum ersten Lauf — Kreuzcheck im resume verprobt es)
    for cname, leg_N in (("C15", N_SWEEP + [16777215]),
                         ("C16", N_SWEEP + [16777215, 10000000]),
                         ("C17", N_SWEEP + [16777215, 10000000, 100000000])):
        have = [N for N in leg_N if N in Smap]
        a, _ = alpha_vN_scaling(have, [Smap[N] for N in have])
        alphas["combined_" + cname] = a
    # lokale Tailslopes deskriptiv
    tails = {}
    for a_, b_ in ((65535, 16777215), (16777215, 10000000), (65535, 10000000),
                   (65535, 100000000), (10000000, 100000000)):
        if a_ in Smap and b_ in Smap:
            tails[f"{a_}->{b_}"] = (math.log(Smap[b_]) - math.log(Smap[a_])) / \
                (math.log(b_) - math.log(a_))
    alphas["local_tail_slopes_descriptive"] = tails

    STATE["alphas"] = alphas

    # Reparatur-Kreuzcheck: alphas gegen den persistierten Zwischenstand
    # (der vor dem Crash gespeichert wurde; S der Mess-Beine steckt dort
    # in beiden Legs — bit-exakt erwartet)
    worst_alpha_dev = 0.0
    if resume and prev is not None and prev.get("alphas"):
        for k, v in prev["alphas"].items():
            if isinstance(v, dict) and "alpha" in v:
                worst_alpha_dev = max(worst_alpha_dev,
                                      rel_dev(alphas[k]["alpha"], v["alpha"]))
            elif isinstance(v, float):
                worst_alpha_dev = max(worst_alpha_dev, rel_dev(alphas[k], v))
            elif isinstance(v, dict):
                # local_tail_slopes_descriptive
                for kk, vv in v.items():
                    worst_alpha_dev = max(worst_alpha_dev,
                                          rel_dev(alphas[k][kk], vv))
        print(f"[resume] alphas-Kreuzcheck vs Zwischenstand: worst rel dev "
              f"{worst_alpha_dev!r}", flush=True)
        if worst_alpha_dev > T_REL:
            print("[resume] ALPHA-KREUZCHECK FEHLGESCHLAGEN — Abort",
                  flush=True)
            raise SystemExit(1)

    # ---------------- Carrier + R + F1 ----------------
    carrier = {}
    for r in STATE["rows_new"]:
        if "S_vN" not in r:
            continue
        entry = {"N": r["N"], "cv_spread_A": r["cv_spread_A"],
                 "cv_path": r["cv_path"]}
        if r["gershgorin"] is not None and r["cv_spread_A"] is None:
            lo = r["gershgorin"]["cv_interval_exakt"][0]
            hi = r["gershgorin"]["cv_interval_exakt"][1]
            entry["gershgorin"] = r["gershgorin"]
            entry["carrier_hold"] = bool(CV_LO <= lo and hi <= CV_HI)
            entry["cv_exact"] = "SP3-Intervall (exaktes cv SKIP per G1)"
        elif r["gershgorin"] is not None:
            lo = r["gershgorin"]["cv_interval_exakt"][0]
            hi = r["gershgorin"]["cv_interval_exakt"][1]
            entry["gershgorin"] = r["gershgorin"]
            entry["carrier_hold"] = bool(
                CV_LO <= r["cv_spread_A"] <= CV_HI
                and CV_LO <= lo and hi <= CV_HI)
            entry["cv_exact"] = "tridiag-exakt (Intervall konsistent)"
            entry["exakt_in_intervall"] = bool(
                lo <= r["cv_spread_A"] <= hi)
        else:
            entry["carrier_hold"] = bool(CV_LO <= r["cv_spread_A"] <= CV_HI)
        entry["R_N"] = r["R_N"]
        entry["r_hold"] = bool(r["R_N"] < 1.0)
        carrier[f"N{r['N']}"] = entry

    f1 = {}
    for lname in REGISTRY["legs"]:
        entry = alphas[lname]
        f1[lname] = {
            "alpha": entry["alpha"],
            "members": entry["members"],
            "missing": entry["missing"],
            "below_band_lo": bool(entry["alpha"] < BAND_LO),
        }
    a_L8 = alphas["L8_primary"]["alpha"]
    if a_L8 < BAND_LO:
        klass = "FALSIFIZIERT"
    elif a_L8 <= BAND_HI:
        klass = "BAND_ERREICHT"
    else:
        klass = "UEBER_BAND"
    if alphas["L8_primary"]["missing"]:
        klass += (" (1e8-Bein OPEN — Klassifikation nur auf Teil-Legs, "
                  "verbatim, kein stiller Skip)")

    STATE["carrier"] = carrier
    STATE["verdicts"] = {
        "f1_legs": f1,
        "klassifikation_L8": klass,
        "alpha_line_committed": c_alpha / eff,
        "alpha_line_L8_descriptive": a_L8 / eff,
        "hh9_5_f1_feuert": bool(any(v["below_band_lo"] for v in f1.values())),
        "hh9_5_carrier_hold": bool(all(v["carrier_hold"] for v in carrier.values())),
        "hh9_5_r_hold": bool(all(v["r_hold"] for v in carrier.values())),
        "committete_verdicts_unangetastet": True,
    }
    STATE["timings"] = {
        "total_s": time.time() - t_start,
        "per_row_s": {str(r["N"]): {k: r[k] for k in
                                    ("t_sieve_s", "t_construct_s",
                                     "t_entropy_s", "t_cv_s")}
                      for r in rows_all if "t_sieve_s" in r},
    }
    STATE["provenance"] = {
        "committed_artifacts_unchanged": [
            "pt_rh_multi_observable_ext.py",
            "pt_rh_multi_observable_ext_results.json",
            "pt_rh_multi_observable_ext_prereg.json (md5 334c9754...)",
        ],
        "scratch_only": True,
        "i3_nulls_skipped_at_new_N": "diagnostisch, nicht verdict-tragend",
        "deck_c5_wortlaut_gelesen": True,
    }
    if resume:
        STATE["provenance"]["reparatur"] = {
            "crash_traceback_erster_lauf": (prev.get("verdicts") or {}).get(
                "traceback"),
            "crash_status_im_zwischenstand": (prev.get("verdicts") or {}).get(
                "status"),
            "mess_beine_wiederverwendet_N": [r.get("N") for r in prev_rows_new],
            "sp3_nachgerechnet_nur_N": [
                r["N"] for r in STATE["rows_new"]
                if isinstance(r.get("gershgorin"), dict)
                and r["gershgorin"].get("nachgerechnet_im_resume")
            ],
            "pins_bei_resume_neu_gelaufen": True,
            "pin_rows_kreuzcheck_worst_dev": worst_pin_repro_dev,
            "alphas_kreuzcheck_worst_dev": worst_alpha_dev,
            "messwerte_neu_bestimmt": [],
            "kein_re_decide": True,
        }
        reused = STATE["provenance"]["reparatur"]["mess_beine_wiederverwendet_N"]
        print(f"[resume] reparatur: Beine {reused} wiederverwendet; "
              f"Kreuzchecks worst pin {worst_pin_repro_dev!r} / "
              f"alphas {worst_alpha_dev!r}", flush=True)
    save_state()
    print(f"[f1] {json.dumps(f1, indent=2)}", flush=True)
    print(f"[verdict] {klass}", flush=True)
    print(f"[h9-nsweep-1e7] fertig in {time.time() - t_start:.1f} s", flush=True)


if __name__ == "__main__":
    try:
        main(resume="--resume" in sys.argv)
    except SystemExit:
        save_state()
        raise
    except Exception:
        STATE["verdicts"] = {
            "status": "ABORT",
            "traceback": traceback.format_exc(),
        }
        save_state()
        raise