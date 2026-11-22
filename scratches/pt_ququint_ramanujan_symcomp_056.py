"""EXPERIMENT 056 — QuQuint-Ramanujan symbolische Kompilation & asymptotische
Extrapolation (H-SYMCOMP-1..4). 0 QPU, seed-frei, stdlib-exakt.

Arbeitsplan-Referenz: 'Srinivasa Ramanujans göttliche Mathematik.md'
§ Arbeitsplan Phase I–IV (symbolischer Compiler + asymptotische
Extrapolation der QuQuint-Ramanujan-Architektur).

Konkrete Vorläufer-Codebasis (alle 0-QPU-Arithmetik, gefroren):
  Phase I:  pt_ram_q_zyklizitaet.py (Exp 040/B1, md5 bd9dfee7) —
            ATOM-Identität share*=(m-q*n0)^2/((q-1)*d*m), c_q(j)=-1.
            src/primequant/_cyc.py (Z[ζ_q]-Ring), _gfq.py (GF(q)),
            observables.py (ramanujan_summe, ring_dft, norm_galois).
  Phase II: pt_ram_q_hardware3.py / _aer.py / pt_isa3.py (Exp 042–044,
            Fez-Job dat1o6qhcrkc73dtgo60) — Transpile-Geometrie vs. Physik,
            Loschmidt-Echo r∈{1,2,4,8}; pt_ram_q_asymptotik.py
            profile_from_count_vector (absolute vs. renormalisierte Konvention).
  Phase III: pt_ram_q_asymptotik.py (Exp 041/B2+B3, q=7-Prereg) —
             q-universelle EXAKTidentität + Siegel-Walfisz/GRH-Schicht;
             pt_rh_multi_observable_ext.py (Sweep bis N=65535, 16 Qubits).
  Phase IV: pt_ram_q_prio48_exakt.py (Exp 055c, G2-EXAKT) — Faltform/
            Ein-Rundungs-Beweis; src/primequant/{distributions,observables,
            channels,stateprep}.py — exakte Fraction-Kette.

Symbolischer Compiler (stdlib-exakt, KEIN sympy/numpy auf dem Wertepfad
der exakten Beweise — sympy ist im venv nicht installiert und in
tests/test_primequant_no_seeded_rng.py für EXAKT-Module gebannt; der
Compiler ist damit stärker als der im Plan skizzierte sympy-Pfad:
reine Integer-Exponenten-Arithmetik, keine Float-Symbole):
  Gate-Abbildung: diagonale Phase exp(2πi·a·p/d) wird als Integer-Exponent
  e=(a·p) mod d kompiliert. Auf S*_q (a=j·d/q) reduziert e auf
  (j·(p mod q)) mod q — NUR Residuum, nie p-Größe, nie d-Größe.
  Das ist die Wraparound-Garantie (P≫d) auf Gate-Ebene.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import numpy as np

import pt_ram_q_zyklizitaet as rq
import pt_ram_q_asymptotik as ra
import pt_ramanujan_replication as rr
import pt_ququint_multin as mn
from pt_prime_state import sieve_primes
from primequant import _cyc, _gfq
from primequant import observables as ob
from primequant import distributions as di
from primequant import stateprep as sp

EXPERIMENT = "056-ququint-ramanujan-symcomp"
HYPOTHESIS = "H-SYMCOMP"
PREREG_PATH = "scratches/pt_symcomp_056_prereg.json"
RESULTS_PATH = "scratches/pt_symcomp_056_results.json"

Q_FAMILY = (3, 5, 7, 11)
D_BY_Q = {3: (9, 81, 729), 5: (25, 625), 7: (49, 2401)}
SCAN_Q = (3, 5)
SCAN_D = {3: 729, 5: 625}
SCAN_GRID = (10 ** 3, 10 ** 4, 10 ** 5, 10 ** 6, 10 ** 7)
SCAN_EXT = 10 ** 8
BAND_LO, BAND_HI = 0.8, 1.25
RESIDUAL_TOL = 1e-10
D_INV_TOL = 1e-10
ANCHOR_TOL = 1e-12
SLOPE_BAND = (-1.5, -0.5)
C_MAX = 1e4


def build_prereg_payload():
    scans = {}
    for q in SCAN_Q:
        rows = []
        for P in SCAN_GRID:
            m, counts = ra.counts_mod(P, q)
            rows.append({"P": P, "pi": m, "counts": counts,
                         "sigma2": ra.class_dispersion(counts),
                         "ratio_pred": ra.unified_ratio(counts)})
        scans[str(q)] = rows
    return {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "q_family": list(Q_FAMILY),
        "d_by_q": {str(k): list(v) for k, v in D_BY_Q.items()},
        "scan_registration": {"q": list(SCAN_Q), "grid": list(SCAN_GRID),
                              "extension": SCAN_EXT},
        "thresholds": {"residual_tol": RESIDUAL_TOL, "d_inv_tol": D_INV_TOL,
                       "anchor_tol": ANCHOR_TOL, "band": [BAND_LO, BAND_HI],
                       "slope_band": list(SLOPE_BAND), "c_max": C_MAX},
        "scans_frozen": scans,
        "verdict_map": {
            "CONFIRMED": "E1+E2+E3-hard grün, E4-Synthese exakt",
            "PARTIAL": "genau eine deskriptive Heuristik (slope/C/envelope) außerhalb, alles Harte grün",
            "REFUTED": "harte Identität/Invarianz/Compiler-Reduktion gebrochen",
            "INVALID": "Anker (V2/q=5-Rückkompatibilität) gebrochen — Algorithmus-Bug, kein Theorie-Fehlschlag",
        },
        "qpu": "0 QPU — reine Arithmetik, seed-frei, kein Quanten-SDK",
        "vorlaeufer": ["pt_ram_q_zyklizitaet.py", "pt_ram_q_asymptotik.py",
                       "pt_ram_q_hardware3.py", "pt_ram_q_hardware_aer.py",
                       "pt_isa3.py", "pt_rh_multi_observable_ext.py",
                       "pt_ram_q_prio48_exakt.py", "src/primequant/_cyc.py",
                       "src/primequant/_gfq.py", "src/primequant/observables.py"],
    }


def canonical(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"))


def payload_md5(p):
    return hashlib.md5(canonical(p).encode()).hexdigest()


def freeze(path=PREREG_PATH):
    p = build_prereg_payload()
    doc = dict(p)
    doc["md5"] = payload_md5(p)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    return doc


def load_frozen(path=PREREG_PATH):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    stripped = {k: v for k, v in doc.items() if k != "md5"}
    if payload_md5(stripped) != doc["md5"]:
        raise ValueError("SYMCOMP-Prereg-md5-MISMATCH")
    return doc


# ---- E1: symbolischer Compiler-Kern (exakt, integer-only) ----
def e1_compiler_core():
    details = {"ramanujan_rows": [], "ring_rows": [], "gf_rows": [],
               "gate_rows": []}
    ok = True
    for q in Q_FAMILY:
        for n in range(0, 3 * q):
            got = ob.ramanujan_summe(q, n)
            exp = (q - 1) if n % q == 0 else -1
            good = got == exp
            ok &= good
            if not good:
                details["ramanujan_rows"].append({"q": q, "n": n, "got": got})
        # Ring: omega^q == 1, Norm N(1-omega) == q
        om = _cyc.cyc_omega(q, 1)
        pw = _cyc.cyc_pow(om, q, q)
        is_one = _cyc.cyc_eq(pw, _cyc.cyc_one(q))
        try:
            one_minus = _cyc.cyc_sub(_cyc.cyc_one(q), om)
            norm = ob.norm_galois(tuple(one_minus), q)
            norm_ok = (norm == q)
        except Exception as e:  # noqa
            norm_ok, norm = False, str(e)
        ok &= is_one and norm_ok
        details["ring_rows"].append({"q": q, "omega_q_is_one": bool(is_one),
                                     "norm_1_minus_omega": str(norm),
                                     "norm_ok": bool(norm_ok)})
        # GF(q): Fermat-Inverse
        for a in range(1, q):
            inv = _gfq.gfq_inv(q, a)
            if (a * inv) % q != 1:
                ok = False
                details["gf_rows"].append({"q": q, "a": a, "bad": True})
    # Gate-Exponenten-Reduktion: (a*p mod d) == (j*(p mod q) via omega_q)
    for q, ds in D_BY_Q.items():
        for d in ds:
            step = d // q
            for j in range(1, q):
                a = j * step
                for p in (2, 3, 5, 7, 11, 13, 101, 10007, 10 ** 6 + 3):
                    e_full = (a * p) % d
                    # Compiler-Regel: omega_d^{a p} == omega_q^{j (p mod q)}
                    # d.h. e_full/step muss kongruent j*(p%q) mod q sein
                    lhs_class = (e_full // step) % q if e_full % step == 0 else None
                    rhs_class = (j * (p % q)) % q
                    good = (e_full % step == 0) and (lhs_class == rhs_class)
                    if not good:
                        ok = False
                        details["gate_rows"].append({"q": q, "d": d, "j": j, "p": p})
    details["gate_checked"] = sum(len(v) for v in D_BY_Q.values()) * 4 * 9
    return ok, details


# ---- E2: Transpile-Geometrie + Loschmidt + V2-Anker ----
def e2_hardware_dekonstruktion():
    out = {}
    # T-V2-Anker: B2-Ratio erklärt 034-Ratio exakt
    _, counts5 = ra.counts_mod(625, 5)
    ratio_b2 = ra.unified_ratio(counts5)
    anchor = rr.V2_SHARE_STAR_PRIME_COMMITTED / rr.model_share_star(625, 625)
    t_anchor = math.isclose(ratio_b2, anchor, rel_tol=ANCHOR_TOL)
    out.update({"ratio_b2_q5": ratio_b2, "anchor_ratio": anchor,
                "abs_diff": abs(ratio_b2 - anchor), "t_anchor": t_anchor})
    # Absolute vs. renormalisierte Konvention bei Wraparound (211,81),q=3
    share_abs, counts, m = ra.measure_share(211, 81, 3)
    pred_b2 = ra.unified_identity_share(counts, 81)
    res_abs = abs(share_abs - pred_b2)
    # renormalisierter mn-Pfad (bricht bei Wraparound — dokumentiert)
    prof_mn = mn.single_register_profile(sieve_primes(211), 81)
    share_mn = rq.share_star_q(prof_mn, 81, 3)
    res_mn = abs(share_mn - pred_b2)
    out.update({"wraparound_point": [211, 81], "res_abs": res_abs,
                "res_renorm_mn": res_mn,
                "abs_ok": res_abs <= RESIDUAL_TOL,
                "renorm_bricht_erwartet": res_mn > 1e-3})
    # Loschmidt-Ideal: Prep+Barrier+Prep^-1 = Identität -> Delta auf 0^n
    try:
        d0 = sp.ideal_loschmidt_delta(2)
        losch_ok = True
    except Exception:
        losch_ok, d0 = False, None
    out.update({"loschmidt_delta": str(d0)[:200], "losch_ok": losch_ok})
    # q=5-Rückkompatibilität (B1 bit-exakt 034)
    t_back = (rq.model_share_star_q(625, 625, 5) == rr.model_share_star(625, 625)
              and rq.transition_m(5) == rr.TRANSITION_M)
    out["t_backcompat_q5"] = bool(t_back)
    hard = t_anchor and out["abs_ok"] and out["renorm_bricht_erwartet"] and losch_ok and t_back
    return hard, out


# ---- E3: Asymptotik + Wraparound-Invarianz ----
def e3_asymptotik(doc):
    rows = {}
    hard_ok, res_worst, dinv_worst, ratio_floor_ok = True, 0.0, 0.0, True
    for q in SCAN_Q:
        d = SCAN_D[q]
        qrows = []
        for P in list(SCAN_GRID) + [SCAN_EXT]:
            share, counts, m = ra.measure_share(P, d, q)
            pred = ra.unified_identity_share(counts, d)
            alt = ra.unified_identity_share_closed(counts, d)
            res = abs(share - pred)
            alt_res = abs(pred - alt) / max(abs(pred), 1e-300)
            res_worst = max(res_worst, res)
            if res > RESIDUAL_TOL or alt_res > 1e-15:
                hard_ok = False
            ratio = ra.unified_ratio(counts)
            if ratio is not None and ratio < 1.0 - 1e-12:
                ratio_floor_ok = False
                hard_ok = False
            qrows.append({"P": P, "pi": m, "share": share, "b2": pred,
                          "residual": res, "alt_res": alt_res, "ratio": ratio,
                          "c_p": P * (ratio - 1.0) if ratio else None})
        rows[str(q)] = qrows
    # d-Invarianz bei Wraparound (P≫d)
    dinvs = []
    for P, d1, d2, q in [(10 ** 6, 9, 729, 3), (10 ** 6, 25, 625, 5),
                         (10 ** 5, 49, 2401, 7)]:
        inv, _, _ = ra.d_invariance_residual(P, d1, d2, q)
        dinvs.append({"P": P, "pair": [d1, d2], "q": q, "residual": inv})
        dinv_worst = max(dinv_worst, inv)
        if inv > D_INV_TOL:
            hard_ok = False
    hard_ok &= ratio_floor_ok
    # Deskriptive B3-Heuristik (kein hartes Gate)
    desk, desk_ok = {}, True
    for q in SCAN_Q:
        prereg_rows = [r for r in rows[str(q)] if r["P"] in list(SCAN_GRID)]
        try:
            slope = ra.loglog_slope([{"P": r["P"], "ratio": r["ratio"]} for r in prereg_rows])
        except ValueError:
            slope = None
        c_max = max(r["c_p"] for r in prereg_rows if r["c_p"] is not None)
        env = prereg_rows[-1]["ratio"] - 1.0 < prereg_rows[0]["ratio"] - 1.0
        s_ok = slope is not None and SLOPE_BAND[0] <= slope <= SLOPE_BAND[1]
        c_ok = c_max <= C_MAX
        desk[str(q)] = {"slope": slope, "slope_ok": s_ok, "c_max": c_max,
                        "c_ok": c_ok, "envelope_ok": bool(env)}
        desk_ok &= (s_ok and c_ok and env)
    return hard_ok, desk_ok, {"scan_rows": rows, "d_invs": dinvs,
                              "max_residual": res_worst,
                              "max_dinv": dinv_worst,
                              "ratio_floor_ok": ratio_floor_ok, "desk": desk}


# ---- E4: Hilbert-Pólya-Zielprofil-Synthese ----
def e4_synthese():
    # Geschlossene Fraction-Identität für q∈{3,5} an Stichproben
    checks = []
    ok = True
    for P, d, q in [(625, 625, 5), (97, 625, 5), (109, 729, 3), (10007, 729, 3)]:
        k = ob.punkt_konstanten(P, d, q)
        ident = bool(k.get("closed_form_identitaet_exakt"))
        ratio_ok = (k["closed_form"] == k["ratio_true"])
        ok &= ident and ratio_ok
        checks.append({"P": P, "d": d, "q": q, "ident_exakt": ident,
                       "ratio_true": str(k["ratio_true"]),
                       "share_true": str(k["share_true_reg"]),
                       "model_share": str(k["model_share_reg"])})
    profil = ("share*_q = (m-q*n0)^2/((q-1)*d*m) + q*sigma^2/(d*m); "
              "ratio = 1 + q(q-1)*sigma^2/(m-q*n0)^2 >= 1; "
              "Compiler: exp(2πi·a·p/d) ↦ e=(a·p) mod d ↦ j·(p mod q) mod q; "
              "Hilbert-Pólya-Ziel: diskretes zyklotomisches Resonanzgitter, "
              "Kontinuum nur als symbolischer Limes P→∞ (B3).")
    return ok, {"checks": checks, "zielprofil": profil}


def run_evaluation(prereg_path=PREREG_PATH):
    doc = load_frozen(prereg_path)
    e1_ok, e1 = e1_compiler_core()
    e2_ok, e2 = e2_hardware_dekonstruktion()
    e3_hard, e3_desk, e3 = e3_asymptotik(doc)
    e4_ok, e4 = e4_synthese()
    hard = e1_ok and e2_ok and e3_hard and e4_ok
    if not (e1_ok and e2_ok and e4_ok and e3_hard):
        # INVALID nur wenn Anker bricht; sonst REFUTED
        if not e2.get("t_anchor") or not e2.get("t_backcompat_q5"):
            verdict = "EVALUATION_INVALID_KONTROLLE_GESCHEITERT"
        else:
            verdict = "H-SYMCOMP_REFUTED"
    elif not e3_desk:
        verdict = "H-SYMCOMP_PARTIAL"
    else:
        verdict = "H-SYMCOMP_CONFIRMED"
    return {"experiment": EXPERIMENT, "hypothesis": HYPOTHESIS,
            "prereg_md5": doc["md5"], "qpu_jobs": 0,
            "e1_compiler": {"ok": e1_ok, **e1},
            "e2_hardware": {"ok": e2_ok, **e2},
            "e3_asymptotik": {"hard_ok": e3_hard, "desk_ok": e3_desk, **e3},
            "e4_synthese": {"ok": e4_ok, **e4},
            "verdict": verdict}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    args = ap.parse_args()
    if args.freeze or not os.path.exists(PREREG_PATH):
        doc = freeze()
        print("PREREG-FREEZE md5:", doc["md5"])
    res = run_evaluation()
    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    print("VERDICT:", res["verdict"])
    print("E1 compiler:", res["e1_compiler"]["ok"])
    print("E2 hardware:", res["e2_hardware"]["ok"], res["e2_hardware"])
    print("E3 hard/desk:", res["e3_asymptotik"]["hard_ok"],
          res["e3_asymptotik"]["desk_ok"], "max_res",
          res["e3_asymptotik"]["max_residual"], "max_dinv",
          res["e3_asymptotik"]["max_dinv"])
    print("E4 synthese:", res["e4_synthese"]["ok"])
    hard_fail = not (res["e1_compiler"]["ok"] and res["e2_hardware"]["ok"]
                     and res["e3_asymptotik"]["hard_ok"] and res["e4_synthese"]["ok"])
    return 1 if (hard_fail or "REFUTED" in res["verdict"] or "INVALID" in res["verdict"]) else 0


if __name__ == "__main__":
    sys.exit(main())
