"""EXPERIMENT 037 — Shor-Oracle auf der Ququint/GF(5)-Architektur.

Branch: shor-ququint-oracle. Engineering-Layer des Plans
(~/.claude/plans/parallel-zooming-nova.md, Denkmodus:
QuantumHypothesisEngineerMind v1.0_20260924_qhe-mix — Simulations-Leiter:
Statevector zuerst, 0 QPU in dieser Phase).

Inhalt:
  * Ququint-Digit-Encoding (Basis 5, little-endian) + DFT ueber Z_{5^n}
    (direkt UND ziffern-faktorisiert — die Ququint-QFT als einstellige
    DFT_5 + Ziffern-Paar-Phasen).
  * Permutations-Unitary U_{a,N}: |x> -> |a*x mod N> mit Idle-Subraum
    x >= N (Register-Axiom: die Modulus-Aktion gilt nur auf dem
    encodierten Traeger {0..N-1}).
  * Zyklus-/Order-Utilities: Tr U^t EXAKT aus Zyklen (Ganzzahl-Spur,
    keine Matrix-Potenzen) — funktioniert auch fuer N=561 (Karmichael).
  * Volle Statevector-QPE (Zaehlregister n_count Ququints, Q = 5^n_count
    >= N^2; x-Register n_x Ququints, 5^n_x >= N) mit ziffernweiser
    kontrollierter U-Evolution (Schaltungs-Spiegel) + inverse DFT +
    Kettenbruch-Rekonstruktion -> Ordnung r.
  * Voller Shor-Wrapper shor_factor: gcd-Shortcut, Ordnungsfindung via
    QPE, Faktor-Extraktion gcd(a^{r/2} +- 1, N), Retry-Logik.
  * CRT-Identitaeten (strukturelle Null fuer EXPERIMENT 038 / H-SHOR-1,
    formaler Zwillingsbruder der H-STAR-5 Tensor-Summen-Identitaet):
      C U_{a,pq} C^T = U_{a,p} (x) U_{a,q},   Tr U_{a,pq}^t = Tr U_{a,p}^t * Tr U_{a,q}^t
  * Fermat-Grid-Statistik: Anteil der a mit ord_a(N) NICHT teiler von
    N-1. REGISTRIERTE BLINDHEIT (Korselt): fuer Karmichael-Zahlen gilt
    Korselt <=> lambda(N) | N-1 <=> ALLE Orders teilen N-1 — die
    Grid-Rate ist auf genau dieser Klasse exakt 0 (z.B. 561: lambda=80
    teilt 560). Schaerferes Kriterium: max_order(N) == N-1 <=> prim
    (zyklische Gruppe / primitive Wurzel).

Alle Identitaeten sind TDD-verifiziert (tests/test_pt_shor_ququint.py),
VOR der Registrierung in EXPERIMENT 038.
"""

from fractions import Fraction
from math import gcd, sqrt

import numpy as np

EXPERIMENT = "EXPERIMENT_037_SHOR_QUQUINT_ORACLE"
BRANCH = "shor-ququint-oracle"

# Toleranzen (H-STAR-5-Pattern)
TOL_IDENTITY = 1e-9          # CRT-/Trace-Identitaeten
DFT_TOL = 1e-12              # direkte vs. ziffern-faktorisierte DFT
TS_CHECK = (1, 2, 3, 4, 5, 6, 7)   # Trace-Identitaets-Fenster

# Register-Axiome (simulation_first_ladder: Budget vor der Ausfuehrung)
QPE_COUNT_QUQUINTS = 4       # Q = 5^4 = 625 >= N^2 fuer N <= 25
QPE_X_QUQUINTS = 2           # XD = 25 >= N fuer N <= 25
QPE_PEAK_REL = 0.05          # Peak-Schwelle relativ zum Maximum


# === Register-Utilities: Ququint-Digits (Basis 5, little-endian) ===

def encode_digits(x, n):
    """x in [0, 5^n) -> tuple von n Ziffern, little-endian (Digit 0 = LSB)."""
    if not 0 <= x < 5 ** n:
        raise ValueError("x ausserhalb des Registers: %d" % x)
    return tuple((x // 5 ** i) % 5 for i in range(n))


def decode_digits(digits):
    """tuple Ziffern (little-endian) -> int."""
    return sum(d * 5 ** i for i, d in enumerate(digits))


# === DFT ueber Z_{5^n} ===

def dft_5n(n):
    """Direkte DFT-Matrix F[k,j] = omega_Q^{kj}/sqrt(Q), Q = 5^n."""
    Q = 5 ** n
    idx = np.arange(Q)
    E = np.outer(idx, idx)
    return np.exp(2j * np.pi * E / Q) / sqrt(Q)


def iqft_5n(n):
    """Inverse DFT (QFT-dagger) ueber Z_{5^n}."""
    return dft_5n(n).conj().T


def dft_5n_factored(n):
    """Ziffern-faktorisierte Form: F[k,j] = exp(2*pi*i * E/Q)/sqrt(Q) mit
    E = sum_{i+l<n} k_i j_l 5^{i+l} — NUR Ziffern-Groessen (kleine Expo-
    nenten), keine kj-Produkte. Terme mit i+l >= n tragen ganzzahlige
    Vielfache von Q und fallen als Phase weg. Das ist die Schaltungs-
    zerlegung: einstellige DFT_5 pro Ququint + Ziffern-Paar-Phasen."""
    Q = 5 ** n
    kd = np.array([encode_digits(k, n) for k in range(Q)])
    jd = np.array([encode_digits(j, n) for j in range(Q)])
    E = np.zeros((Q, Q))
    for i in range(n):
        for l in range(n):
            if i + l < n:
                E += 5 ** (i + l) * np.outer(kd[:, i], jd[:, l])
    return np.exp(2j * np.pi * E / Q) / sqrt(Q)


# === Permutations-Unitary U_{a,N} ===

def U_an(a, N, dim):
    """|x> -> |a*x mod N> fuer x < N, Idle (Identitaet) fuer x >= N.
    Erfordert gcd(a, N) = 1 (sonst keine Permutation)."""
    if gcd(a, N) != 1:
        raise ValueError("gcd(a, N) = %d > 1: kein Permutations-Unitary" % gcd(a, N))
    if dim < N:
        raise ValueError("dim < N: Register zu klein")
    U = np.zeros((dim, dim))
    for x in range(dim):
        y = (a * x) % N if x < N else x
        U[y, x] = 1.0
    return U


def perm_map(a, N):
    """Klassische Permutationstabelle y[x] = a*x mod N auf {0..N-1}."""
    return [(a * x) % N for x in range(N)]


def perm_cycles(a, N):
    """Zykellaengen (aufsteigend sortiert) der Permutation x -> a*x mod N
    auf {0..N-1}; Fixpunkte als Laenge 1."""
    m = perm_map(a, N)
    seen = [False] * N
    out = []
    for x in range(N):
        if seen[x]:
            continue
        length = 0
        y = x
        while not seen[y]:
            seen[y] = True
            y = m[y]
            length += 1
        out.append(length)
    return sorted(out)


def trace_power_from_cycles(cycles, t):
    """Tr U^t EXAKT (Ganzzahl) aus Zyklen: jede Zyklen-Laenge L traegt
    L falls L | t, sonst 0. Keine Matrix-Potenzen."""
    return sum(L for L in cycles if t % L == 0)


# === Ordnungs-Arithmetik ===

def order_mod(a, N):
    """Multiplikative Ordnung ord_a(N) (klassische Enumeration)."""
    if gcd(a, N) != 1:
        raise ValueError("gcd(a, N) > 1: Ordnung nicht definiert")
    r = 1
    y = a % N
    while y != 1:
        y = (y * a) % N
        r += 1
        if r > N:
            raise RuntimeError("Ordnungs-Enumeration lief: a=%d, N=%d" % (a, N))
    return r


def coprime_units(N, min_a=2):
    """Coprime a in [min_a, N-1]."""
    return [x for x in range(min_a, N) if gcd(x, N) == 1]


def max_order(N):
    """Maximale Ordnung ueber alle Coprime-a. Fuer primes p ist die
    Gruppe zyklisch: max_order(p) = p-1 (primitive Wurzel). Fuer
    Karmichael-Zahlen gilt max_order = lambda(N) < N-1 (Korselt)."""
    return max(order_mod(a, N) for a in coprime_units_all(N))


def coprime_units_all(N):
    """Alle Coprime a in [1, N-1]."""
    return [x for x in range(1, N) if gcd(x, N) == 1]


def grid_violation_rate(N, units=None):
    """O1-Statistik: Anteil der a mit ord_a(N) NICHT teiler von N-1.
    Fuer primes p: identisch 0 (Fermat, Theorem). Fuer typische
    Composites > 0. REGISTRIERTE BLINDHEIT: Korselt-Klasse
    (Karmichael, lambda(N) | N-1) -> Rate 0 wie bei Primes."""
    if units is None:
        units = coprime_units(N)
    if not units:
        raise ValueError("keine Coprime-a im Fenster")
    viol = [(N - 1) % order_mod(a, N) != 0 for a in units]
    return sum(1 for v in viol if v) / len(units)


# === CRT-Identitaeten (strukturelle Null) ===

def crt_matrix(p, q):
    """CRT-Isomorphie als Permutationsmatrix: x <-> (x mod p, x mod q),
    Zeilenindex y = (x mod p)*q + (x mod q). C ist orthogonale
    Permutationsmatrix (C C^T = I)."""
    dim = p * q
    C = np.zeros((dim, dim))
    for x in range(dim):
        y = (x % p) * q + (x % q)
        C[y, x] = 1.0
    return C


def crt_factorization_dev(a, p, q):
    """max |C U_{a,pq} C^T - U_{a,p} (x) U_{a,q}| — exakt 0 in exakter
    Arithmetik (Theorem, CRT-Ring-Isomorphie)."""
    N = p * q
    C = crt_matrix(p, q)
    left = C @ U_an(a, N, N) @ C.T
    right = np.kron(U_an(a, p, p), U_an(a, q, q))
    return float(np.max(np.abs(left - right)))


def trace_product_dev(a, p, q, ts=TS_CHECK):
    """max_t |Tr U_{a,pq}^t - Tr U_{a,p}^t * Tr U_{a,q}^t| ueber das
    Fenster ts — formaler Zwillingsbruder der H-STAR-5 Tensor-Summen-
    Identitaet (Tr e^{-iHt} = Prod_p Tr e^{-iH_p t})."""
    cyc_N = perm_cycles(a, p * q)
    cyc_p = perm_cycles(a, p)
    cyc_q = perm_cycles(a, q)
    dev = 0.0
    for t in ts:
        lhs = trace_power_from_cycles(cyc_N, t)
        rhs = trace_power_from_cycles(cyc_p, t) * trace_power_from_cycles(cyc_q, t)
        dev = max(dev, abs(lhs - rhs))
    return float(dev)


# === Statevector-QPE (Ordnungsfindung) ===

def qpe_order(a, N, n_count=QPE_COUNT_QUQUINTS, n_x=QPE_X_QUQUINTS):
    """Volle Statevector-QPE auf Ququint-Registern.

    Zaehlregister: n_count Ququints, Q = 5^n_count (Gleichsuperposition),
    x-Register: n_x Ququints, XD = 5^n_x, Start |1>. Ziffernweise
    kontrollierte U-Evolution (Schaltungs-Spiegel: Digit k steuert
    U^{5^k}), dann inverse DFT auf dem Zaehlregister.

    Rueckgabe: dict mit probs (Laenge Q), peaks, denominators, r
    (verifiziert: a^r = 1 mod N) oder r=None.
    """
    Q = 5 ** n_count
    XD = 5 ** n_x
    if XD < N:
        raise ValueError("5^n_x < N: x-Register zu klein")
    if Q < N * N:
        raise ValueError("5^n_count < N^2: Zaehlregister zu klein")
    if gcd(a, N) != 1:
        raise ValueError("gcd(a, N) > 1")

    # Schritt 1: Zaehlregister in Gleichsuperposition, x-Register |1>.
    psi = np.zeros(Q * XD, dtype=complex)
    inv_sqrt_q = 1.0 / sqrt(Q)
    for c in range(Q):
        psi[c * XD + (1 % N)] = inv_sqrt_q

    # Schritt 2: ziffernweise kontrollierte Evolution (Spiegel der
    # Schaltung: Digit k von c steuert U^{5^k}; Permutations-Komposition,
    # KEINE Matrix-Potenzen, KEIN Shortcut).
    for k in range(n_count):
        step = 5 ** k
        e_k = pow(a, step, N)          # U^{5^k} = Mult. mit e_k mod N
        for c in range(Q):
            d = (c // step) % 5
            if d == 0:
                continue
            m = pow(e_k, d, N)         # U^{5^k * d}
            block = psi[c * XD:(c + 1) * XD].copy()
            new = block.copy()         # Idle-Subraum x >= N unberuehrt
            for x in range(N):
                new[(m * x) % N] = block[x]
            psi[c * XD:(c + 1) * XD] = new

    # Schritt 3: inverse DFT auf dem Zaehlregister.
    psi3 = (iqft_5n(n_count) @ psi.reshape(Q, XD)).reshape(-1)
    probs = np.abs(psi3.reshape(Q, XD)) ** 2
    probs = probs.sum(axis=1)

    # Schritt 4: Peaks + Kettenbruch-Rekonstruktion.
    max_p = float(probs.max())
    peaks = [(k, float(probs[k])) for k in range(Q)
             if probs[k] > QPE_PEAK_REL * max_p]
    denominators = sorted({Fraction(k, Q).limit_denominator(N).denominator
                           for k, _ in peaks if k > 0})
    r = _resolve_order(denominators, a, N)
    return {"a": a, "N": N, "Q": Q, "XD": XD, "probs": probs,
            "peaks": peaks, "denominators": denominators, "r": r}


def _resolve_order(denominators, a, N):
    """r aus Kettenbruch-Nennern: LCM, fallback Paar-/Einzelkandidaten;
    jede Kandidatin wird verifiziert (a^r = 1 mod N) und auf die
    EXAKTE Ordnung reduziert."""
    if not denominators:
        return None

    def lcm_list(xs):
        out = 1
        for x in xs:
            out = out * x // gcd(out, x)
        return out

    candidates = [lcm_list(denominators)]
    candidates += list(denominators)
    candidates += [lcm_list([denominators[i], denominators[j]])
                   for i in range(len(denominators))
                   for j in range(i + 1, len(denominators))]
    for r in candidates:
        if r > 1 and pow(a, r, N) == 1:
            return _reduce_order(r, a, N)
    return None


def _reduce_order(r, a, N):
    """Reduziere ein Vielfaches der Ordnung auf die exakte Ordnung."""
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23):
        while r % p == 0 and pow(a, r // p, N) == 1:
            r //= p
    return r


# === Voller Shor-Wrapper ===

def shor_factor(N, n_count=QPE_COUNT_QUQUINTS, n_x=QPE_X_QUQUINTS,
                max_attempts=8, a_list=None):
    """Faktorisiere N ueber QPE-Ordnungsfindung auf dem Ququint-Register.

    Fuer primes p: a^{r/2} = +-1 (Koerper, x^2 = 1 hat nur +-1 als
    Loesung) -> der Weg liefert NIE einen nichttrivialen Faktor ->
    None nach max_attempts (Theorem-Niveau-Positive-Control).
    Fuer Composites: nichttrivialer Faktor mit Wahrscheinlichkeit >= 1/2
    pro Coprime-a (given even r) -> Retry schliesst das Fenster.

    Rueckgabe: (f1, f2) mit 1 < f1 <= f2 < N, oder None.
    """
    if N < 4:
        raise ValueError("N < 4: nichts zu faktorisieren")
    if N % 2 == 0:
        return (2, N // 2)
    if a_list is None:
        a_list = coprime_units(N)
    for a in a_list[:max_attempts]:
        g = gcd(a, N)
        if 1 < g < N:                       # gcd-Shortcut
            other = N // g
            return (min(g, other), max(g, other))
        res = qpe_order(a, N, n_count, n_x)
        r = res["r"]
        if r is None or r % 2 != 0:
            continue
        y = pow(a, r // 2, N)
        if y == N - 1:                      # a^{r/2} = -1: trivial
            continue
        for cand in (gcd(y - 1, N), gcd(y + 1, N)):
            if 1 < cand < N:
                other = N // cand
                return (min(cand, other), max(cand, other))
    return None


# === Ensemble-SFF aus Zyklen (exakt, ohne Matrizen) ===

def sff_ensemble(N, a_list=None, ts=TS_CHECK):
    """K(t) = |Tr U_{a,N}^t|^2 pro a (EXAKT aus Zyklen, Ganzzahl-Spur),
    ensemble-gemittelt ueber die Coprime-a. Sekundaer-Observable
    (SFF-Schiene) fuer EXPERIMENT 038."""
    if a_list is None:
        a_list = coprime_units(N)
    out = {}
    for t in ts:
        ks = [trace_power_from_cycles(perm_cycles(a, N), t) ** 2
              for a in a_list]
        out[t] = float(np.mean(ks))
    return out