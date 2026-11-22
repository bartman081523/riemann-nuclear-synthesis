import math, time, json
import numpy as np
from scipy.linalg import eigh_tridiagonal
import sys
sys.path.insert(0, "/run/media/julian/ML4/riemann")
from pt_prime_state import sieve_primes

N_SWEEP = [7, 15, 31, 63, 127, 255, 511, 1023, 2047, 4095, 8191, 16383, 32767, 65535]

# --- dense vs tridiag deviation at v1 points ---
def cv_dense(primes):
    n = len(primes); A = np.zeros((n, n))
    for i in range(n):
        A[i, i] = primes[i]
        if i + 1 < n:
            A[i, i+1] = abs(primes[i+1]-primes[i]); A[i+1, i] = A[i, i+1]
    eigs = np.linalg.eigvalsh(A)
    return float(np.var(eigs))/(eigs[-1]-eigs[0])**2

def cv_trid(seq):
    d = np.asarray(seq, float); e = np.abs(np.diff(d))
    w = eigh_tridiagonal(d, e, eigvals_only=True)
    return float(np.var(w))/(w[-1]-w[0])**2

committed = json.load(open("/run/media/julian/ML4/riemann/pt_rh_multi_observable_results.json"))
by_N = {r["N"]: r["cv_spread_A"] for r in committed["rows"]}
print("v1-reproduction (dense, same path as v1):")
maxdev = 0.0
for N in N_SWEEP[:8]:
    cv = cv_dense(sieve_primes(N))
    dev = abs(cv - by_N[N])
    maxdev = max(maxdev, dev)
    print(f"  N={N:5d} dense={cv!r} committed={by_N[N]!r} dev={dev:.3e}")
print(f"max dev dense-vs-committed: {maxdev:.3e}")

t0 = time.time(); cvd = cv_dense(sieve_primes(65535)); t1 = time.time()
print(f"dense N=65535: {t1-t0:.1f}s cv={cvd:.9f} | tridiag cv={cv_trid(sieve_primes(65535)):.9f}")

# --- corrected witnesses ---
def alpha_of(S, Ns):
    return float(np.polyfit(np.log(np.asarray(Ns, float)), np.log(np.asarray(S, float)), 1)[0])

for name, coef, exp in [("W1", 1.0, 0.4), ("W2", 0.01, 0.55)]:
    S = [coef * N**exp for N in N_SWEEP]
    a = alpha_of(S, N_SWEEP)
    R = [S_/math.log(len(sieve_primes(N))) for S_, N in zip(S, N_SWEEP)]
    print(f"{name}: alpha={a!r} (target {exp}, dev {abs(a-exp):.2e}) | R range [{min(R):.4f}, {max(R):.4f}] | all>1={all(r>1 for r in R)} all<1={all(r<1 for r in R)}")
