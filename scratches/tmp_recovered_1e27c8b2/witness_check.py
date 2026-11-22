import math
import numpy as np
from pt_prime_state import sieve_primes

N_SWEEP = [7, 15, 31, 63, 127, 255, 511, 1023, 2047, 4095, 8191, 16383, 32767, 65535]

def alpha_of(S_values, N_values):
    log_N = np.log(np.asarray(N_values, dtype=float))
    log_S = np.log(np.asarray(S_values, dtype=float))
    alpha, c = np.polyfit(log_N, log_S, 1)
    return float(alpha)

for N in N_SWEEP:
    pi_N = len(sieve_primes(N))
    # witness 1: a TRUE / b FALSE  (alpha = 0.4 exact, R > 1 everywhere?)
    S1 = [0.4 * N**0.4 for N in N_SWEEP]
    # witness 2: a FALSE / b TRUE  (alpha = 0.6 exact, R < 1 everywhere?)
    S2 = [0.05 * N**0.6 for N in N_SWEEP]

a1 = alpha_of([0.4 * N**0.4 for N in N_SWEEP], N_SWEEP)
a2 = alpha_of([0.05 * N**0.6 for N in N_SWEEP], N_SWEEP)
R1 = [(0.4 * N**0.4) / math.log(len(sieve_primes(N))) for N in N_SWEEP]
R2 = [(0.05 * N**0.6) / math.log(len(sieve_primes(N))) for N in N_SWEEP]
print("witness1 alpha =", a1, " (expect ~0.4, a TRUE);  R range:", min(R1), max(R1), " all>1:", all(r > 1 for r in R1))
print("witness2 alpha =", a2, " (expect ~0.6, a FALSE); R range:", min(R2), max(R2), " all<1:", all(r < 1 for r in R2))
# also on the v1-only 8 points (witness must work on both domains)
N8 = N_SWEEP[:8]
a1b = alpha_of([0.4 * N**0.4 for N in N8], N8)
a2b = alpha_of([0.05 * N**0.6 for N in N8], N8)
R1b = [(0.4 * N**0.4) / math.log(len(sieve_primes(N))) for N in N8]
R2b = [(0.05 * N**0.6) / math.log(len(sieve_primes(N))) for N in N8]
print("v1-only: w1 alpha", a1b, "allR>1", all(r>1 for r in R1b), "| w2 alpha", a2b, "allR<1", all(r<1 for r in R2b))
# timing probe: jacobi eigvalsh at N=65535
import time
primes = sieve_primes(65535)
print("pi(65535) =", len(primes))
t0 = time.time()
n = len(primes)
A = np.zeros((n, n))
for i in range(n):
    A[i, i] = primes[i]
    if i + 1 < n:
        A[i, i+1] = abs(primes[i+1] - primes[i])
        A[i+1, i] = A[i, i+1]
t1 = time.time()
eigs = np.linalg.eigvalsh(A)
t2 = time.time()
spread = eigs[-1] - eigs[0]
cv = float(np.var(eigs)) / spread**2
print(f"build {t1-t0:.1f}s, eigvalsh {t2-t1:.1f}s, cv_spread = {cv:.6f}")
# null-A: odd integers, null-B: powers of two, at N=65535
odd = [x for x in range(3, 65536, 2)]
n = len(odd)
Ao = np.zeros((n, n))
for i in range(n):
    Ao[i, i] = odd[i]
    if i + 1 < n:
        Ao[i, i+1] = odd[i+1] - odd[i]
        Ao[i+1, i] = 2.0
eo = np.linalg.eigvalsh(Ao)
cvo = float(np.var(eo)) / (eo[-1]-eo[0])**2
pw = [2**k for k in range(1, 17)]
n = len(pw)
Ap = np.zeros((n, n))
for i in range(n):
    Ap[i, i] = pw[i]
    if i + 1 < n:
        Ap[i, i+1] = pw[i+1] - pw[i]
        Ap[i+1, i] = Ap[i, i+1]
ep = np.linalg.eigvalsh(Ap)
cvp = float(np.var(ep)) / (ep[-1]-ep[0])**2
print(f"null-A (odd) cv = {cvo:.6f} | null-B (pow2) cv = {cvp:.6f} | primes cv = {cv:.6f}")
