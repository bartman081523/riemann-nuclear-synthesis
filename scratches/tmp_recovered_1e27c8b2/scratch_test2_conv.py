# -*- coding: utf-8 -*-
"""Pre-Freeze-Konventionscheck EXPERIMENT 049: reshape order F vs C je Quelle.

Verifiziert, welche Bipartitions-/Reshape-Konvention die committeten S_vN-Werte
reproduziert, BEVOR der Runner gefroren wird (GATE-B <= 1e-10 haengt daran).
"""
import sys
sys.path.insert(0, "/run/media/julian/ML4/riemann")

import numpy as np


def sieve(n):
    is_p = bytearray([1]) * (n + 1)
    is_p[0:2] = b"\x00\x00"
    for i in range(2, int(n ** 0.5) + 1):
        if is_p[i]:
            is_p[i * i:: i] = bytearray(len(is_p[i * i:: i]))
    return [i for i in range(2, n + 1) if is_p[i]]


def s_vn(psi, n_A, order):
    d_A = 2 ** n_A
    A = psi.reshape(d_A, -1, order=order)
    s = np.linalg.svd(A, compute_uv=False)
    lam = s ** 2
    lam = lam[lam > 0]
    return float(-(lam * np.log(lam)).sum())


def state(N, n_qubits):
    primes = [p for p in sieve(N) if p < 2 ** n_qubits]
    psi = np.zeros(2 ** n_qubits)
    psi[primes] = 1.0
    return psi / np.linalg.norm(psi)


# singleshot: N=15 (n=4, n_A_field=4 als DIM), committet 0.836065555629091
# N255-File: N=255 (n=8, n_A=4 als COUNT), committet 2.314037122608579
# N1e6-File: N=10000 (n=14, n_A=7 als COUNT), committet 4.672241830479666
CASES = [
    ("singleshot N=15",   15,     4, 2, 0.836065555629091),
    ("singleshot N=127",  127,    7, 3, 1.356183805881178),
    ("N255-File N=255",   255,    8, 4, 2.314037122608579),
    ("N255-File N=1023",  1023,  10, 5, 3.1900293627988274),
    ("N1e6-File N=10000", 10000, 14, 7, 4.672241830479666),
]

for label, N, n_q, n_A, committed in CASES:
    psi = state(N, n_q)
    f = s_vn(psi, n_A, "F")
    c = s_vn(psi, n_A, "C")
    print("%-18s committet %.16f" % (label, committed))
    print("   order=F  %.16f   d=%+.2e" % (f, abs(f - committed)))
    print("   order=C  %.16f   d=%+.2e" % (c, abs(c - committed)))
    # zusaetzlich: Split-Variante n_A_hi = n_q - n_A_count (hohe Qubits als A)
    f_hi = s_vn(psi, n_q - n_A, "F")
    c_hi = s_vn(psi, n_q - n_A, "C")
    print("   hi-Split F %.16f (d=%+.2e) | C %.16f (d=%+.2e)"
          % (f_hi, abs(f_hi - committed), c_hi, abs(c_hi - committed)))