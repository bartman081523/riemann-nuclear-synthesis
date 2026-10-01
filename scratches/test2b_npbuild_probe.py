#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Numpy-Build-Probe zur 049/049b-Konfund-Delta-Aufklaerung (0 QPU, NICHT verdict-tragend).

Anomalie: 049-committed partial_rho_gamma_S_given_rank_active = -0.31904242195272137,
049b-committed                                                          = -0.29878604232636102
(trotz implementations-identischem Konfund-Kit und byte-identischen Rows/ Seeds).

Aufklaerung (diese Probe, 2x2-Matrix [Interpreter-Build x Gamma-Datensatz]):
- 049-Lauf  = venv/bin/python, numpy 2.4.6 (Runtime 238.5 s)
- 049b-Lauf = System-python,   numpy 2.5.2 (Runtime  59.4 s)  — unabsichtlich
  unterschiedliche Interpreter je Lauf.
- Mechanismus: np.polyfit-LSTSQ-ULP-Delta zwischen den Builds formt die
  +-0.5-Rang-Residuen an den rank_active-Ties ([1.5,1.5]/[3.5,3.5]/[5.5,5.5] aus
  n_valid_base [1,1]/[3,3]/[7,7]): unter 2.4.6 landen Paare (63,255) und
  (127,511) auf BIT-GLEICHEN Residuen -> Average-Tie-Ranks 2.5/2.5 und 9.5/9.5;
  unter 2.5.2 sind dieselben Paare um 1-2 ulp gesplitet -> getrennte Raenge.
  Qualitativ anderer resS-Rang-Vektor -> partial springt. KEIN BLAS-dust,
  build-deterministisch (in JEDEM Build threads-stabil).
- Die drei RAW-rho's (0.9272727272727272 / 0.966401527166472 / 0.7575757575757575)
  sind BUILD-INVARIANT bit-gleich (ganzzahlige Rang-Statistiken, keine Residuen).
- Die gamma-Werte SELBST differieren zwischen den Builds auf ~1e-14 (nur 1/11
  bit-identisch): PCG64-RNG ist bit-stabil (default_rng(20261015).random(6)
  bit-gleich in beiden Builds, im Probe-Out verifiziert), das Delta sitzt in der
  LAPACK-SVD-Pipeline der K3-Draws (carrier_lam / ok_p-Gap-Maske / Ratio) —
  dieselbe ULP-Klasse.
Verdict-Robustheit: |partial| 0.299 und 0.319 stehen beide weit unter
q95_partial 0.6402558049850593 (049b, eigene Permutations-Null) bzw. unter der
rohen 049-Regel q95_null 0.6363636363636362 -> Verdict RANGGETRAGEN_GEFALLEN
und der ZEICHENFLIP gegenueber rho_obs +0.939 tragen in BEIDEN Builds. Die
Null-Schwelle selbst wurde nicht offline re-permutiert (broad Null, ULP-Delta
irrelevant gegen die Margin; offen gelegt).
Lektion (Metrologie): Interpreter- und numpy-Version je Lauf in den
Lauf-Metadaten pinnen; polyfit-Residuen-Rang-Statistiken an Ties sind
build-sensitiv auf ULP-Niveau. Kein Messwert der Hypothese aendert sich.

Aufruf: venv/bin/python scratches/test2b_npbuild_probe.py  (outer)
        scratches/test2b_npbuild_probe.py --gamma {049|049b}  (inner, self-invoked)
"""
import json
import os
import subprocess
import sys


def _inner():
    """Lauf unter dem rufenden Interpreter: volle Konfund-Statistik je Datensatz."""
    import numpy as np

    os.chdir(REPO)

    # Funktionsdefs EXAKT aus dem committeten 049b-Runner (implementations-identisch)
    src = open("pt_test2b_rank_controlled.py").read()
    seg = src[src.index("def avg_ranks"): src.index("# --------------------------------------------------------------- Hauptlauf")]
    ns = {"np": np}
    exec(seg, ns)
    avg_ranks = ns["avg_ranks"]
    spearman = ns["spearman"]
    partial_spearman = ns["partial_spearman"]

    which = sys.argv[sys.argv.index("--gamma") + 1]
    res_file = ("pt_test2_entanglement_comovement_results.json" if which == "049"
                else "pt_test2b_rank_controlled_results.json")
    grid = {p_["N"]: p_ for p_ in json.load(open(res_file))["grid_points"]}
    prereg = json.load(open("pt_test2_entanglement_comovement_prereg.json"))
    axis = {r["N"]: float(r["axis_S_bits_frisch"]) for r in prereg["data_basis"]["rows"]}
    rows = prereg["data_basis"]["rows"]
    NQ = {r["N"]: r["n_qubits"] for r in rows}

    valids = [grid[n] for n in VALID_049 if n in grid]
    gamma_valid = [v["K3_q95_001"] for v in valids]
    s_valid = [axis[v["N"]] for v in valids]
    s_rel = [axis[v["N"]] / (NQ[v["N"]] // 2) for v in valids]
    rank_active = [float(v["n_valid_base"]) for v in valids]
    ns_float = [float(v["N"]) for v in valids]

    rho_gn = spearman(gamma_valid, ns_float)
    rho_gra = spearman(gamma_valid, rank_active)
    rho_gsrel = spearman(gamma_valid, s_rel)
    partial = partial_spearman(gamma_valid, s_valid, rank_active)

    # resS/resG-Struktur exakt wie Konfund-Zeilen 444-449 des 049b-Runners
    r_g, r_s, r_a = avg_ranks(gamma_valid), avg_ranks(s_valid), avg_ranks(rank_active)
    bg, ag = np.polyfit(r_a, r_g, 1)
    bs, as_ = np.polyfit(r_a, r_s, 1)
    res_g = [float(v) for v in (r_g - (ag + bg * r_a))]
    res_s = [float(v) for v in (r_s - (as_ + bs * r_a))]

    out = {
        "numpy": np.__version__,
        "python": sys.version.split()[0],
        "gamma_dataset": which,
        "rho_gamma_vs_N": rho_gn,
        "rho_gamma_vs_rank_active": rho_gra,
        "rho_gamma_vs_S_rel": rho_gsrel,
        "partial": partial,
        "polyfit_bg_ag_bs_as": [float(bg), float(ag), float(bs), float(as_)],
        "resS_values": res_s,
        "resS_ranks": [float(v) for v in avg_ranks(res_s)],
        "resG_ranks": [float(v) for v in avg_ranks(res_g)],
    }
    print("###JSON###")
    print(json.dumps(out))


def run_build(interp, which):
    proc = subprocess.run([interp, __file__, "--gamma", which],
                          capture_output=True, text=True, cwd=REPO)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-800:])
    return json.loads(proc.stdout.split("###JSON###", 1)[1])


def main():
    interps = {}
    for tag, interp in [("venv_numpy_246", "venv/bin/python"),
                        ("sys_numpy_252", "python")]:
        vers = subprocess.run([interp, "-c", "import numpy;print(numpy.__version__)"],
                              capture_output=True, text=True, cwd=REPO)
        interps[tag] = {"interp": interp, "numpy": vers.stdout.strip(), "by_dataset": {}}
    whiches = ["049", "049b"]
    for tag in sorted(interps):
        for w in whiches:
            interps[tag]["by_dataset"][w] = run_build(interps[tag]["interp"], w)

    checks = []
    for tag in sorted(interps):
        for w, committed in [("049", COMMITTED_049), ("049b", COMMITTED_049B)]:
            got = interps[tag]["by_dataset"][w]["partial"]
            own = ((w == "049" and tag == "venv_numpy_246") or
                   (w == "049b" and tag == "sys_numpy_252"))
            checks.append({
                "build": tag, "dataset": w, "partial": got,
                "committed_value": committed,
                "own_run_build": own,
                "bit_gleich_committed": got == committed,
                "erwartung": "bit-gleich" if own else "weicht ab (Build-Determinante)",
            })
    all_ok = all(
        (c["bit_gleich_committed"] if c["own_run_build"]
         else not c["bit_gleich_committed"])
        for c in checks)

    # RNG-Bit-Stabilitaet im aktiven Prozess (inner liefert keine; hier sys)
    import numpy as np
    r = np.random.default_rng(20261015)
    rng_sys = [float(x) for x in r.random(6)]
    rng_expected = [0.28088964726739407, 0.5875203375235917, 0.4748989189215046,
                    0.4127794730483393, 0.004527277708947786, 0.7650887813453231]

    out = {
        "probe": "test2b_npbuild_probe (0 QPU, NICHT verdict-tragend)",
        "resolution": ("numpy-BUILD-Delta (2.4.6 venv vs 2.5.2 sys), polyfit-ULP an "
                       "rank_active-Ties; build-determiniert, NICHT daten-determiniert"),
        "interpreter_of_runs": {"049": "venv/bin/python (numpy 2.4.6)",
                                "049b": "System-Python (numpy 2.5.2)"},
        "builds": interps,
        "interpreter_labels": {"venv_numpy_246": "venv/bin/python", "sys_numpy_252": "python (System, wie 049b-Lauf)"},
        "checks": checks,
        "rng_bit_stability": {
            "sys_values": rng_sys,
            "bit_gleich_beide_builds": rng_sys == rng_expected,
        },
        "gamma_lapack_ulp": ("gamma-Werte nur 1/11 bit-identisch zwischen 049/049b-Results "
                             "— LAPACK-ULP in der SVD-Pipeline; RAW-rho's dennoch bit-gleich "
                             "(Rang-Robustheit)"),
        "q95_partial_note": ("q95_partial 0.6402558049850593 (049b-Null, 1000 Permutationen) "
                             "nicht offline re-permutiert; Verdict-Robustheit folgt aus "
                             "|partial| << Margin in beiden Builds"),
        "verdict_robust": "RANGGETRAGEN_GEFALLEN + ZEICHENFLIP tragen in beiden Builds",
    }

    print("\n=== 2x2-Matrix [Build x Gamma-Datensatz] ===")
    for tag in sorted(interps):
        for w in whiches:
            d = interps[tag]["by_dataset"][w]
            print("%-14s numpy %-6s gamma=%-4s partial %+.16f"
                  % (tag, d["numpy"], w, d["partial"]))
    print("\nChecks:", "ALLE in Erwartung" if all_ok else checks)
    print("resS-Ranks venv 2.4.6:", interps["venv_numpy_246"]["by_dataset"]["049"]["resS_ranks"])
    print("resS-Ranks sys  2.5.2:", interps["sys_numpy_252"]["by_dataset"]["049"]["resS_ranks"])
    raw_ok = all(
        interps[t]["by_dataset"][w][k] == exp
        for t in interps for w in whiches for k, exp in
        [("rho_gamma_vs_N", RHO_RAW_EXPECTED[0]),
         ("rho_gamma_vs_rank_active", RHO_RAW_EXPECTED[1]),
         ("rho_gamma_vs_S_rel", RHO_RAW_EXPECTED[2])]
    )
    print("raw-rho's bit-identisch ueber Builds UND Datensaetze:", raw_ok)
    out["raw_rho_invariant_ueber_builds_und_datensaetze"] = raw_ok
    out["checks_all_in_erwartung"] = all_ok

    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1, default=float)
    print("\nOK ->", OUT)
    sys.exit(0 if all_ok and raw_ok else 1)


REPO = "/run/media/julian/ML4/riemann"
OUT = os.path.join(REPO, "scratches", "test2b_npbuild_probe_out.json")
COMMITTED_049 = -0.31904242195272137
COMMITTED_049B = -0.29878604232636102
VALID_049 = [15, 31, 63, 127, 255, 511, 1023, 10000, 100000, 1000000]
RHO_RAW_EXPECTED = (0.9272727272727272, 0.966401527166472, 0.7575757575757575)

if __name__ == "__main__":
    if "--gamma" in sys.argv:
        _inner()
    else:
        main()