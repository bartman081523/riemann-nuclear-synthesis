"""EXPERIMENT 059 — Ramanujan-Einklang I: Partitionskongruenzen + q=2-Statevector
(H-REM59). 0 QPU, seed-frei. Erste Anwendung des RamanujanEinklangMind.

E1 (Kongruenz-first, THEOREM-Checks als Integritäts-Reproduktion):
  p(5n+4) ≡ 0 (5), p(7n+5) ≡ 0 (7), p(11n+6) ≡ 0 (11) — exakte
  Euler-Rekurrenz (stdlib big-int), kein Float.
E2 (Tau-Kongruenz, Stichprobe): τ(n) ≡ σ_11(n) (mod 691), 1 ≤ n ≤ 100 —
  Δ-Reihe exakt aus ∏(1−x^n)^24 trunkiert, σ_11 per Teiler.
E3 (Statevector-Leiter, NEU — q=2-Familie, erstmals vermessen):
  P=100, d=64=2^6, q=2. Brücke (ex ante benannt): Counts → Amplituden
  trägt die Norm Σn²; das SV-Observable ist um den exakten Faktor m/Σn²
  skaliert: share_SV = share*_B2 · m/Σn². DFT als explizite 64×64-Unitary
  (konventionsfrei; Gate-QFT-Decomposition gehört der QPU-Phase).
  Vorhersage ex ante aus Counts: G(32) = n0−n1 = −23 → 529/2496.

QPU-Phase (V.3) ist registriert, NICHT submittiert: derselbe Circuit mit
QFT-Decomposition + Readout-Mitigation nach Freigabe.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import numpy as np

import pt_ram_q_asymptotik as ra

EXPERIMENT = "059-ramanujan-einklang-1"
HYPOTHESIS = "H-REM59"
PREREG_PATH = "scratches/pt_rem59_059_prereg.json"
RESULTS_PATH = "scratches/pt_rem59_059_results.json"

PMAX_PART = 2000
N_TAU = 100
P_Q2, D_Q2, Q_Q2 = 100, 64, 2
SV_TOL = 1e-12


def partition_numbers(n_max):
    """p(n) exakt via Euler-Pentagonal-Rekurrenz (big-int, stdlib-only)."""
    p = [0] * (n_max + 1)
    p[0] = 1
    for n in range(1, n_max + 1):
        total = 0
        k = 1
        while True:
            g1 = k * (3 * k - 1) // 2
            if g1 > n:
                break
            s = -1 if k % 2 == 0 else 1
            total += s * p[n - g1]
            g2 = k * (3 * k + 1) // 2
            if g2 <= n:
                total += s * p[n - g2]
            k += 1
        p[n] = total
    return p


def tau_numbers(n_max):
    """τ(n) exakt: Koeffizienten von x·∏(1−x^n)^24, trunkiert (int-Arithmetik)."""
    from math import comb
    poly = [0] * (n_max + 1)
    poly[0] = 1
    for n in range(1, n_max + 1):
        factor = [0] * (n_max + 1)
        for k in range(25):
            e = n * k
            if e > n_max:
                break
            factor[e] = ((-1) ** k) * comb(24, k)
        new = [0] * (n_max + 1)
        for i in range(n_max + 1):
            if poly[i]:
                for j in range(n_max + 1 - i):
                    if factor[j]:
                        new[i + j] += poly[i] * factor[j]
        poly = new
    return [0] + poly[:n_max]  # τ(n) = Koeffizient von x^n


def sigma_11(n):
    return sum(d ** 11 for d in range(1, n + 1) if n % d == 0)


def build_prereg():
    primes = ra.numpy_primes(P_Q2)
    m = int(primes.size)
    cnt = [0] * D_Q2
    for pp in primes:
        cnt[int(pp) % D_Q2] += 1
    n0 = sum(1 for pp in primes if int(pp) % 2 == 0)
    sumn2 = sum(c * c for c in cnt)
    b2 = (m - Q_Q2 * n0) ** 2 / ((Q_Q2 - 1) * float(D_Q2) * m)
    sv_pred = (m - Q_Q2 * n0) ** 2 / (float(D_Q2) * sumn2)
    return {
        "experiment": EXPERIMENT, "hypothesis": HYPOTHESIS,
        "e1": {"familien": ["5n+4 mod 5", "7n+5 mod 7", "11n+6 mod 11"],
               "pmax": PMAX_PART, "vorhergesagt": "alle Reste 0 (THEOREM)"},
        "e2": {"n_max": N_TAU, "vorhergesagt": "alle (τ−σ11) mod 691 == 0 (THEOREM)"},
        "e3": {"P": P_Q2, "d": D_Q2, "q": Q_Q2, "m": m, "n0": n0,
               "sum_n2": sumn2, "b2_share": b2, "sv_share_pred": sv_pred,
               "g32": n0 - (m - n0),
               "bruecke": "Counts→Amplituden trägt Σn²; share_SV = share_B2·m/Σn²",
               "tol": SV_TOL},
        "qpu_phase": "REGISTRIERT, NICHT SUBMITTIERT — Freigabe + Budget nötig",
        "qpu": "0 QPU in dieser Phase",
    }


def canonical(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"))


def md5(p):
    return hashlib.md5(canonical(p).encode()).hexdigest()


def freeze(path=PREREG_PATH):
    p = build_prereg()
    doc = dict(p)
    doc["md5"] = md5(p)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    return doc


def load_frozen(path=PREREG_PATH):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if md5({k: v for k, v in doc.items() if k != "md5"}) != doc["md5"]:
        raise ValueError("059-Prereg-md5-MISMATCH")
    return doc


def e1_partitionen(doc):
    p = partition_numbers(doc["e1"]["pmax"])
    fams = [(5, 4, 5), (7, 5, 7), (11, 6, 11)]
    out, ok = [], True
    for mod, rest, m_ in fams:
        bad = [n for n in range(mod * 400 + rest + 1)
               if n % mod == rest and n <= PMAX_PART and p[n] % m_ != 0]
        checked = sum(1 for n in range(mod * 400 + rest + 1)
                      if n % mod == rest and n <= PMAX_PART)
        ok &= not bad
        out.append({"fam": f"{mod}n+{rest} mod {m_}", "geprueft": checked,
                    "verletzungen": bad[:5], "ok": not bad})
    return bool(ok), out


def e2_tau(doc):
    tau = tau_numbers(doc["e2"]["n_max"])
    bad, ok = [], True
    for n in range(1, doc["e2"]["n_max"] + 1):
        if (tau[n] - sigma_11(n)) % 691 != 0:
            bad.append(n)
            ok = False
    return bool(ok), {"n_max": doc["e2"]["n_max"], "verletzungen": bad[:5],
                      "ok": bool(ok)}


def e3_statevector(doc):
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    from qiskit.quantum_info import Statevector
    e = doc["e3"]
    primes = ra.numpy_primes(e["P"])
    cnt = np.zeros(e["d"])
    for pp in primes:
        cnt[int(pp) % e["d"]] += 1.0
    norm = float((cnt ** 2).sum())
    assert norm == e["sum_n2"]
    psi0 = cnt / math.sqrt(norm)
    omega = np.exp(2j * np.pi / e["d"])
    a = np.arange(e["d"])
    U = omega ** np.outer(a, a) / math.sqrt(e["d"])
    qc = QuantumCircuit(6)
    qc.initialize(psi0, range(6))
    qc.unitary(U, range(6))
    qc.save_statevector()
    sim = AerSimulator(method="statevector")
    sv = Statevector(sim.run(qc).result().get_statevector())
    probs = np.abs(np.asarray(sv)) ** 2
    measured = float(probs[e["d"] // e["q"]])
    pred = e["sv_share_pred"]
    res = abs(measured - pred)
    # Kreuz-Check: klassischer Count-Vektor-Pfad (041) reproduziert B2
    share_cls, _, _ = ra.measure_share(e["P"], e["d"], e["q"])
    return (res <= e["tol"]
            and abs(share_cls - e["b2_share"]) <= 1e-12), {
        "gemessen": measured, "vorhergesagt": pred, "residual": res,
        "klassisch_share": share_cls, "b2": e["b2_share"]}


def run_evaluation():
    doc = load_frozen()
    e1_ok, e1 = e1_partitionen(doc)
    e2_ok, e2 = e2_tau(doc)
    e3_ok, e3 = e3_statevector(doc)
    ok = e1_ok and e2_ok and e3_ok
    verdict = "H-REM59_CONFIRMED" if ok else "H-REM59_REFUTED"
    if not (e1_ok and e2_ok):
        verdict = "EVALUATION_INVALID_THEOREMCHECK_GESCHEITERT"
    return {"experiment": EXPERIMENT, "hypothesis": HYPOTHESIS,
            "prereg_md5": doc["md5"], "qpu_jobs": 0,
            "e1": {"ok": e1_ok, "familien": e1},
            "e2": {"ok": e2_ok, **e2}, "e3": {"ok": e3_ok, **e3},
            "verdict": verdict}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    args = ap.parse_args()
    if args.freeze or not os.path.exists(PREREG_PATH):
        d = freeze()
        print("PREREG-FREEZE md5:", d["md5"])
    res = run_evaluation()
    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    print("VERDICT:", res["verdict"])
    print("E1:", [(f["fam"], f["geprueft"], f["ok"]) for f in res["e1"]["familien"]])
    print("E2:", res["e2"])
    print("E3:", res["e3"])
    return 0 if res["verdict"] == "H-REM59_CONFIRMED" else 1


if __name__ == "__main__":
    sys.exit(main())
