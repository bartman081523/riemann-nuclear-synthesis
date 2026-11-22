import math, time
import numpy as np
from scipy.linalg import eigh_tridiagonal
import sys
sys.path.insert(0, "/run/media/julian/ML4/riemann")
from pt_prime_state import sieve_primes

N_SWEEP = [7, 15, 31, 63, 127, 255, 511, 1023, 2047, 4095, 8191, 16383, 32767, 65535]

def alpha_of(S, Ns):
    return float(np.polyfit(np.log(np.asarray(Ns, float)), np.log(np.asarray(S, float)), 1)[0])

S1 = [0.4 * N**0.4 for N in N_SWEEP]
S2 = [0.05 * N**0.6 for N in N_SWEEP]
R1 = [S / math.log(len(sieve_primes(N))) for S, N in zip(S1, N_SWEEP)]
R2 = [S / math.log(len(sieve_primes(N))) for S, N in zip(S2, N_SWEEP)]
print(f"witness1 alpha={alpha_of(S1, N_SWEEP):.15f} a_TRUE={alpha_of(S1,N_SWEEP)<0.5} Rmin={min(R1):.3f} allR>1={all(r>1 for r in R1)}")
print(f"witness2 alpha={alpha_of(S2, N_SWEEP):.15f} a_FALSE={alpha_of(S2,N_SWEEP)>=0.5} Rmax={max(R2):.3f} allR<1={all(r<1 for r in R2)}")

def cv_tridiag(seq):
    d = np.asarray(seq, dtype=float)
    e = np.abs(np.diff(d))
    w = eigh_tridiagonal(d, e, eigvals_only=True)
    return float(np.var(w)) / (w[-1] - w[0]) ** 2

t0 = time.time()
rows = []
for N in N_SWEEP:
    p = sieve_primes(N)
    cv = cv_tridiag(p)
    rows.append((N, len(p), cv))
    print(f"N={N:6d} pi={len(p):5d} cv_primes={cv:.6f}")
print(f"sweep time {time.time()-t0:.1f}s")
cvs = [r[2] for r in rows]
print(f"cv range [{min(cvs):.6f}, {max(cvs):.6f}] mean {np.mean(cvs):.6f}")

# nulls at every sweep point (same N domain)
print("\nnulls:")
for N in N_SWEEP:
    odd = list(range(3, N + 1, 2))
    pw = [2**k for k in range(1, int(math.log2(N)) + 1)]
    cvo = cv_tridiag(odd)
    cvp = cv_tridiag(pw)
    pcv = cv_tridiag(sieve_primes(N))
    print(f"N={N:6d} primes {pcv:.6f} | odd {cvo:.6f} (d={pcv-cvo:+.6f}) | pow2 {cvp:.6f} (d={pcv-cvp:+.6f}) in_band(p/odd/pow2): {0.05<=pcv<=0.20}/{0.05<=cvo<=0.20}/{0.05<=cvp<=0.20}")
