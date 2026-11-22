# -*- coding: utf-8 -*-
"""Pre-Freeze-Check 2 EXPERIMENT 049: Woher kommen die committeten S_vN?

(1) S_vN direkt aus dem committeten s_sq-Array (quellenagnostisch) vs. Zeilen-S_vN.
(2) Full-Split-Sweep (alle Bipartitionen, F und C) fuer N=255/10000 — findet die
    Konvention, die die committeten Werte exakt trifft.
(3) Kandidaten-Zustandskonstruktionen (uniform prime, prime-INDEX, inkl. 1,
    interleaved Split).
"""
import sys
sys.path.insert(0, "/run/media/julian/ML4/riemann")
import json

import numpy as np


def sieve(n):
    is_p = bytearray([1]) * (n + 1)
    is_p[0:2] = b"\x00\x00"
    for i in range(2, int(n ** 0.5) + 1):
        if is_p[i]:
            is_p[i * i:: i] = bytearray(len(is_p[i * i:: i]))
    return [i for i in range(2, n + 1) if is_p[i]]


def sv_nats(lam):
    lam = np.asarray(lam, float)
    lam = lam[lam > 0]
    return float(-(lam * np.log(lam)).sum())


def split_sv(psi, d_A, d_B, order):
    A = psi.reshape(d_A, d_B, order=order)
    s = np.linalg.svd(A, compute_uv=False)
    lam = s ** 2
    lam = lam[lam > 0]
    return -(lam * np.log(lam)).sum()


def interleaved_sv(psi, n_q, n_A):
    """A-Seite = die n_A LSB-Positionen im Bit-Shuffle (even/odd-Stil)."""
    dim = 2 ** n_q
    idx = np.arange(dim)
    # A-Bits = geradzahlig nummerierte Qubits (q0,q2,...) -> d_A = 2^n_A
    a_bits = [(idx >> q) & 1 for q in range(0, n_q, 2 if n_A * 2 >= n_q else 1)]
    # einfache Variante: A = q0,q2,q4,... (die ersten n_A gerade Positionen)
    a_positions = list(range(0, n_q, 2))[: n_A]
    b_positions = [q for q in range(n_q) if q not in a_positions]
    a_idx = np.zeros(dim, dtype=np.int64)
    b_idx = np.zeros(dim, dtype=np.int64)
    for k, q in enumerate(a_positions):
        a_idx |= ((idx >> q) & 1) << k
    for k, q in enumerate(b_positions):
        b_idx |= ((idx >> q) & 1) << k
    A = np.zeros((2 ** len(a_positions), 2 ** len(b_positions)))
    np.add.at(A, (a_idx, b_idx), psi)
    s = np.linalg.svd(A, compute_uv=False)
    lam = s ** 2
    lam = lam[lam > 0]
    return -(lam * np.log(lam)).sum()


# ---------- (1) committete s_sq-Arrays direkt auswerten --------------------
print("=== (1) S_vN(committetes s_sq) vs. Zeilen-S_vN ===")
with open("/run/media/julian/ML4/riemann/pt_prime_state_qpu_singleshot_results.json") as fh:
    single = json.load(fh)["results"]
for row in single:
    S_ary = sv_nats(row["s_sq_classical"])
    print("N=%-6d S_vN(Zeile)=%.16f S_vN(s_sq)=%.16f d=%+.2e"
          % (row["N"], row["S_vN_classical"], S_ary,
             abs(S_ary - row["S_vN_classical"])))
with open("/run/media/julian/ML4/riemann/pt_prime_state_N255_results.json") as fh:
    n255 = json.load(fh)["new_data_points"]
for row in n255:
    S_ary = sv_nats(row["s_sq"])
    print("N=%-6d S_vN(Zeile)=%.16f S_vN(s_sq)=%.16f d=%+.2e"
          % (row["N"], row["S_vN"], S_ary, abs(S_ary - row["S_vN"])))


# ---------- (2) Full-Split-Sweep N=255 und N=10000 -------------------------
print("")
print("=== (2) Split-Sweep (alle Bipartitionen, F/C) ===")
for label, N, n_q, target in [("N=255", 255, 8, 2.3140371226085792),
                              ("N=10000", 10000, 14, 4.6722418304796660)]:
    primes = [p for p in sieve(N) if p < 2 ** n_q]
    psi = np.zeros(2 ** n_q)
    psi[primes] = 1.0
    psi /= np.linalg.norm(psi)
    print("--- %s (n=%d, pi=%d) target %.16f, uniform-prime-Zustand"
          % (label, n_q, len(primes), target))
    hits = []
    for n_A in range(1, n_q):
        d_A = 2 ** n_A
        d_B = 2 ** (n_q - n_A)
        for order in ("F", "C"):
            S = split_sv(psi, d_A, d_B, order)
            mark = ""
            if abs(S - target) < 1e-10:
                hits.append((n_A, order, "low"))
                mark = "  <== EXAKT"
            if abs(S - target) < 1e-4:
                mark += "  (nah)"
            print("   n_A=%2d %s S=%.16f%s" % (n_A, order, S, mark))
    print("   EXAKT-Treffer:", hits if hits else "KEINE")


# ---------- (3) Kandidaten-Zustaende bei N=255 -----------------------------
print("")
print("=== (3) Kandidaten-Zustaende N=255 (target %.16f) ===" % 2.3140371226085792)
n_q, N = 8, 255
primes = [p for p in sieve(N) if p < 2 ** n_q]


def report_state(label, psi):
    nrm = np.linalg.norm(psi)
    psi_n = psi / nrm
    row = []
    for n_A in range(1, n_q):
        S_f = split_sv(psi_n, 2 ** n_A, 2 ** (n_q - n_A), "F")
        row.append("f%d %.4f" % (n_A, S_f))
    # best-hit vs target
    best = None
    for n_A in range(1, n_q):
        for order in ("F", "C"):
            S = split_sv(psi_n, 2 ** n_A, 2 ** (n_q - n_A), order)
            if best is None or abs(S - 2.3140371226085792) < best[0]:
                best = (abs(S - 2.3140371226085792), n_A, order, S)
    print("%-28s best: n_A=%d %s S=%.16f d=%.2e" % (label, best[1], best[2],
                                                    best[3], best[0]))
    # interleaved
    for n_A in (4,):
        S_it = interleaved_sv(psi_n, n_q, n_A)
        print("     interleaved n_A=%d: S=%.16f d=%.2e" % (n_A, S_it,
                                                           abs(S_it - 2.3140371226085792)))


psi_u = np.zeros(2 ** n_q)
psi_u[primes] = 1.0
report_state("uniform primes <= N", psi_u)

# inkl. 1 als "Prime"
psi_1 = np.zeros(2 ** n_q)
psi_1[[1] + primes] = 1.0
report_state("uniform inkl. 1", psi_1)

# Prime-INDEX-Zustand: psi[k]=1 an Position der k-ten Primzahl (1-basiert ab 1)
psi_idx = np.zeros(2 ** n_q)
for k, p in enumerate(primes + [2]):
    psi_idx[k] = 1.0
report_state("prime-INDEX", psi_idx)

# Gewichtung 1/sqrt(p), 1/p, sqrt(p)
psi_w = np.zeros(2 ** n_q)
for p in primes:
    psi_w[p] = 1.0 / np.sqrt(p)
report_state("Gewicht 1/sqrt(p)", psi_w)

psi_w2 = np.zeros(2 ** n_q)
for p in primes:
    psi_w2[p] = 1.0 / p
report_state("Gewicht 1/p", psi_w2)