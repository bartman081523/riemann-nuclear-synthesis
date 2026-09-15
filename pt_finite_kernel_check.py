"""
EXPERIMENT 028 - PATTERN C: FINITE KERNEL CHECK (decide-analogue)

Python-Translation der LawN256-Struktur aus anthropics/zeta-23-lean
(zeta-23-lean-review/, Zeta23/PairCeiling/LawN256.lean): dort werden 256
ganzzahlige Enclosures extern per Intervall-Arithmetik erzeugt und in Lean
nur noch per `decide` im Kernel nachgeprueft. Hier dieselbe epistemische
Zweiteilung in Python:

  UNTRUSTED GENERATOR  (Sektion nach '=== UNTRUSTED GENERATOR ===')
      Berechnet Claims mit float-Simulator und Projektcode
      (pt_ququint_gf5.GF5, pt_ququint_simulator.pauli_x_5/pauli_z_5),
      serialisiert exakte Daten (Ganzzahlen, Brueche, Enclosures)
      nach pt_finite_kernel_claims.json.

  TRUSTED KERNEL  (alles vor der Generator-Sektion, stdlib-only)
      Re-deriviert JEDE Aussage aus den aufgezeichneten exakten Daten mit
      eigener Arithmetik: rohe Ganzzahl-Operatoren mod 5 (unabhaengig von
      der GF5-Klasse), zyklotomischer Ring Z[omega] = Z[x]/(Phi_5(x)),
      komplexe rationale Zahlen (Fraction-Paare). Kein float, keine
      externen Pakete, kein Projektimport — das Kernel-Checken ist ein
      unabhaengiger Code-Pfad, exakt wie Leans `decide` die Berechnung
      im Kernel wiederholt.

Verifizierte Aussagegruppen (28 Verdicts, 25 CONFIRMED erwartet, 3
dokumentierte REFUTED-Funde):

  gf5_axioms (10)
      Abschluss, Kommutativitaet, Assoziativitaet, Distributivitaet,
      Identitaeten, Inverse — Kernel prueft die aufgezeichneten Tabellen
      gegen rohe int-Arithmetik UND tabellen-intern. Ein bughaftes GF5.__add__
      wuerde closure_add REFUTED setzen (Mutationstests belegen das).

  ququint_displacement (5)
      X^5 = I, Z^5 = I, X^dagger X = I, Z^dagger Z = I, Z X = omega X Z —
      exakt in Z[omega] ueber die aufgezeichneten ganzzahligen Matrizen.

  exactness_enclosures (3)
      X5-Float-Eintraege exakt ganzzahlig (0.0/1.0), Z5-Nebendiagonale exakt
      Null, Z5-Diagonale in aufgezeichneten rationalen Enclosures.
      EnclOK-Analogon: das Kernel prueft die Mitgliedschaft exakt
      (Fraction(float) ist exakt in Python); die Schachrheit der Enclosures
      gegen die wahren 5. Einheitswurzeln ist displayed hypothesis
      (externes Interval-Arithmetik-Analogon), NICHT kernel-verifiziert.

  dft (1)
      sum_k omega^{k(j-l)} = 5*delta_jl fuer alle (j,l) in Z_5^2 — das
      exakte mathematische Fundament von dft∘idft = id in pt_ququint_gf5;
      das Kernel berechnet alle 25 Summen selbst im Z[omega]-Ring.

  pt_algebra (9)
      P^2 = I; Kriterium P·H·P == conj(H) ([H, PT] = 0 mit T = komplexe
      Konjugation) und Hermitizitaet H^dagger == H fuer drei exakt
      rationale Form-Exemplare; dazu die Real-/Imaginaerteil-Zerlegung
      P·H·P - conj(H) == (P·D·P - D) + i*gamma*(P·A·P + A) fuer die beiden
      D+i*gamma*A-Formen.

Dokumentierte Funde (keine Fehler, sondern exaktifizierte Befunde):
  - dimer_canonical_hermitian REFUTED: der kanonische PT-Dimer
    [[E+i*gamma, s], [s, E-i*gamma]] ist nicht-Hermitisch (per Design).
  - project_form_pt_symmetric REFUTED: die generische Projektform
    H = D + i*gamma*A mit reell-symmetrischem A erfuellt das strenge
    Kriterium [H, PT] = 0 NICHT (Reellteil: [D,P] = 0, Imaginaerteil:
    {A,P} = 0 — fuer symmetrisches A mit Reversal-P unmoeglich). Die
    Projektterminologie "PT-symmetrische Extension" ist PT-TYP
    (Hermitian/anti-Hermitian-Split als Observablen), nicht strenge
    PT-Symmetrie. Exaktifizierung der eigenen Randnotiz im
    Forschungsdokument (Konstruktionsfehler-Korrektur, A hermitesch).
  - project_form_hermitian REFUTED: nicht-Hermitisch (per Design).

Verwendung:
    python pt_finite_kernel_check.py            # generate + verify + Result-JSON
    python pt_finite_kernel_check.py generate   # nur Claims schreiben
    python pt_finite_kernel_check.py verify     # Claims laden + verifizieren
"""
import hashlib
import json
import sys
from fractions import Fraction

CLAIMS_PATH = "pt_finite_kernel_claims.json"
RESULT_PATH = "pt_finite_kernel_check_result.json"

VERDICT_CONFIRMED = "CONFIRMED"
VERDICT_REFUTED = "REFUTED"


# =========================================================================
# TRUSTED KERNEL CORE — exakte Arithmetik, stdlib-only
# =========================================================================

# --- Zyklotomischer Ring Z[omega] = Z[x]/(Phi_5(x)), Phi_5 = 1+x+x^2+x^3+x^4 ---
# ECHTER zyklotomischer Ring (Rang 4, Basis 1, omega, omega^2, omega^3 mit
# omega^4 = -1-omega-omega^2-omega^3), NICHT der Gruppenring Z[x]/(x^5-1)
# (Rang 5): im Gruppenring ist 1+omega+...+omega^4 = Phi_5(omega) != 0, die
# DFT-Orthogonalitaet sum_k omega^{k(j-l)} = 5*delta_jl gilt daher NUR im
# echten Ring. Element = 4-Tupel int-Koeffizienten (c0..c3).

_PHI5_OMEGA4 = (-1, -1, -1, -1)  # omega^4 = -(1 + omega + omega^2 + omega^3)


def cyc_zero():
    return (0, 0, 0, 0)


def cyc_one():
    return (1, 0, 0, 0)


def cyc_omega(k):
    """omega^k, k beliebig (int); Exponent wird exakt reduziert via
    omega^5 = 1 und omega^4 = -(1+omega+omega^2+omega^3)."""
    k = k % 5
    if k < 4:
        coeffs = [0, 0, 0, 0]
        coeffs[k] = 1
        return tuple(coeffs)
    return _PHI5_OMEGA4


def cyc_add(a, b):
    return tuple((x + y) for x, y in zip(a, b))


def cyc_mul(a, b):
    """Multiplikation mit Reduktion mod Phi_5: Grade 4..6 werden exakt
    abgebaut via omega^6 = omega (omega^5 = 1 mod Phi_5), omega^5 = 1,
    omega^4 = -(1+omega+omega^2+omega^3)."""
    raw = [0] * 7
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                if bj:
                    raw[i + j] += ai * bj
    out = list(raw[:4])
    out[1] += raw[6]  # omega^6 = omega (denn omega^5 = 1)
    out[0] += raw[5]  # omega^5 = 1
    if raw[4]:
        for idx, coeff in enumerate(_PHI5_OMEGA4):
            out[idx] += raw[4] * coeff  # omega^4 = -(1+omega+omega^2+omega^3)
    return tuple(out)


def cyc_conj(a):
    """Komplexe Konjugation im Rang-4-Ring: conj(sum c_k omega^k)
    = c0 + c1*omega^4 + c2*omega^3 + c3*omega^2
    = (c0-c1) + (-c1)*omega + (c3-c1)*omega^2 + (c2-c1)*omega^3.
    Check: conj(omega^4) = omega (denn |omega^4|^2 = 1)."""
    c0, c1, c2, c3 = a
    return (c0 - c1, -c1, -c1 + c3, -c1 + c2)


def cyc_eq(a, b):
    return a == b


def cyc_from_json(lst):
    return tuple(int(c) for c in lst)


# --- Matrizen ueber Z[omega] ---

def cyc_one_mat(n):
    return [[cyc_one() if i == j else cyc_zero() for j in range(n)]
            for i in range(n)]


def cyc_mat_mul(A, B):
    n = len(A)
    m = len(B[0])
    p = len(B)
    out = [[cyc_zero() for _ in range(m)] for _ in range(n)]
    for i in range(n):
        for k in range(p):
            a = A[i][k]
            if a == cyc_zero():
                continue
            for j in range(m):
                out[i][j] = cyc_add(out[i][j], cyc_mul(a, B[k][j]))
    return out


def cyc_mat_adj(A):
    """Adjungierte: Transponieren + komplexe Konjugation jedes Eintrags."""
    n = len(A)
    m = len(A[0])
    return [[cyc_conj(A[j][i]) for j in range(n)] for i in range(m)]


def cyc_mat_scalar_mul(c, A):
    return [[cyc_mul(c, a) for a in row] for row in A]


def cyc_mat_eq(A, B):
    return A == B


def cyc_mat_pow(A, p):
    result = cyc_one_mat(len(A))
    base = [list(row) for row in A]
    for _ in range(p):
        result = cyc_mat_mul(result, base)
    return result


def canonical_Z5_cyc():
    """Exakte Z5 = diag(1, omega, ..., omega^4) aus der Theorie (kernel-seitig,
    fuer Tests/Dokumentation; die Verifizierer nutzen die AUFGZEICHNETEN
    Matrizen aus den Claims, nicht diese kanonische Konstruktion)."""
    n = 5
    return [[cyc_omega(k) if i == j == k else cyc_zero() for j in range(n)]
            for i, k in enumerate(range(n))]


# --- Exakte komplexe rationale Zahlen: QC = (Fraction re, Fraction im) ---

def qc(re, im):
    return (Fraction(re), Fraction(im))


def qc_add(x, y):
    return (x[0] + y[0], x[1] + y[1])


def qc_sub(x, y):
    return (x[0] - y[0], x[1] - y[1])


def qc_mul(x, y):
    return (x[0] * y[0] - x[1] * y[1], x[0] * y[1] + x[1] * y[0])


def qc_conj(x):
    return (x[0], -x[1])


def qc_eq(x, y):
    return x == y


def qc_from_json(lst):
    re_n, re_d, im_n, im_d = lst
    return (Fraction(int(re_n), int(re_d)), Fraction(int(im_n), int(im_d)))


def qc_from_int(v):
    return (Fraction(v), Fraction(0))


def qc_mat_from_json(M):
    return [[qc_from_json(e) for e in row] for row in M]


def qc_mat_from_int(M):
    return [[qc_from_int(v) for v in row] for row in M]


def qc_mat_mul(A, B):
    n = len(A)
    m = len(B[0])
    p = len(B)
    out = [[qc(Fraction(0), Fraction(0)) for _ in range(m)] for _ in range(n)]
    for i in range(n):
        for k in range(p):
            for j in range(m):
                out[i][j] = qc_add(out[i][j], qc_mul(A[i][k], B[k][j]))
    return out


def qc_mat_add(A, B):
    return [[qc_add(a, b) for a, b in zip(ra, rb)] for ra, rb in zip(A, B)]


def qc_mat_sub(A, B):
    return [[qc_sub(a, b) for a, b in zip(ra, rb)] for ra, rb in zip(A, B)]


def qc_mat_adj(A):
    """Hermitisch-konjugierte: Transponieren + konjugieren."""
    n = len(A)
    m = len(A[0])
    return [[qc_conj(A[j][i]) for j in range(n)] for i in range(m)]


def qc_mat_scalar_mul(c, A):
    return [[qc_mul(c, a) for a in row] for row in A]


def qc_mat_eq(A, B):
    return A == B


def frac_from_json(lst):
    n, d = lst
    return Fraction(int(n), int(d))


# --- Ganzzahl-Matrizen (Permutationen etc.) ---

def int_mat_mul(A, B):
    n = len(A)
    m = len(B[0])
    p = len(B)
    out = [[0 for _ in range(m)] for _ in range(n)]
    for i in range(n):
        for k in range(p):
            a = A[i][k]
            if a:
                for j in range(m):
                    out[i][j] += a * B[k][j]
    return out


def int_mat_eq(A, B):
    return A == B


# --- Verdict-Helfer ---

def _verdict(group, name, ok, detail):
    return {
        "group": group,
        "name": name,
        "verdict": VERDICT_CONFIRMED if ok else VERDICT_REFUTED,
        "detail": detail,
    }


# =========================================================================
# VERIFIZIERER (kernel-seitig; alles exakt aus aufgezeichneten Daten)
# =========================================================================

def verify_gf5_tables(claims):
    """GF(5)-Axiome: rohe int-Arithmetik mod 5 gegen die aufgezeichneten
    Tabellen (unabhaengig von der GF5-Klasse) plus tabellen-interne Checks.
    Erzeugt 10 Verdicts."""
    tables = claims["groups"]["gf5_tables"]
    add = [[int(v) for v in row] for row in tables["add_table"]]
    mul = [[int(v) for v in row] for row in tables["mul_table"]]
    inv = [int(v) for v in tables["inverses"]]
    group = "gf5_axioms"
    out = []

    def in_range(t):
        return all(0 <= v <= 4 for row in t for v in row)

    # Abschluss + Konsistenz mit roher mod-5-Arithmetik (zwei Code-Pfade:
    # aufgezeichnet via GF5-Klasse, verifiziert via rohe int-Ops).
    out.append(_verdict(group, "closure_add",
                        in_range(add) and all(add[a][b] == (a + b) % 5
                                              for a in range(5) for b in range(5)),
                        "add_table == (a+b) mod 5, rohe Ganzzahloperator-Arithmetik"))
    out.append(_verdict(group, "closure_mul",
                        in_range(mul) and all(mul[a][b] == (a * b) % 5
                                              for a in range(5) for b in range(5)),
                        "mul_table == (a*b) mod 5, rohe Ganzzahloperator-Arithmetik"))

    # Tabelle-interne Eigenschaften (unabhaengig von roher Arithmetik).
    out.append(_verdict(group, "commutativity_add",
                        all(add[a][b] == add[b][a]
                            for a in range(5) for b in range(5)),
                        "add_table[a][b] == add_table[b][a], alle 25 Paare"))
    out.append(_verdict(group, "commutativity_mul",
                        all(mul[a][b] == mul[b][a]
                            for a in range(5) for b in range(5)),
                        "mul_table[a][b] == mul_table[b][a], alle 25 Paare"))
    out.append(_verdict(group, "associativity_add",
                        all(add[add[a][b]][c] == add[a][add[b][c]]
                            for a in range(5) for b in range(5) for c in range(5)),
                        "125 Tripel, rein tabellen-intern"))
    out.append(_verdict(group, "associativity_mul",
                        all(mul[mul[a][b]][c] == mul[a][mul[b][c]]
                            for a in range(5) for b in range(5) for c in range(5)),
                        "125 Tripel, rein tabellen-intern"))
    out.append(_verdict(group, "distributivity",
                        all(mul[a][add[b][c]] == add[mul[a][b]][mul[a][c]]
                            for a in range(5) for b in range(5) for c in range(5)),
                        "125 Tripel a*(b+c) == a*b + a*c, tabellen-intern"))
    out.append(_verdict(group, "additive_identity",
                        all(add[0][a] == a and add[a][0] == a for a in range(5)),
                        "0 als additives Identitaetselement"))
    out.append(_verdict(group, "multiplicative_identity",
                        all(mul[1][a] == a and mul[a][1] == a for a in range(5)),
                        "1 als multiplikatives Identitaetselement"))
    out.append(_verdict(group, "multiplicative_inverses",
                        all(1 <= inv[a] <= 4 and mul[a][inv[a]] == 1
                            for a in range(1, 5)),
                        "a * a^{-1} == 1 mod 5 fuer alle a != 0"))
    return out


def verify_displacement_algebra(claims):
    """Ququint-Verschiebungsoperatoren X5, Z5: exakte Identitaeten in Z[omega]
    = Z[x]/(Phi_5(x)), gerechnet mit Kernel-Arithmetik ueber die
    AUFGEZEICHNETEN Matrizen. Erzeugt 5 Verdicts."""
    group = "ququint_displacement"
    disp = claims["groups"]["displacement"]
    # X5 wird als int-Matrix aufgezeichnet; in Z[omega]-Eintraege (Rang 4)
    # ueberfuehren: ganzzahlige Skalare sind konstante Polynome (e,0,0,0).
    X = [[(int(e), 0, 0, 0) for e in row] for row in disp["X5"]]
    Z = [[cyc_from_json(e) for e in row] for row in disp["Z5_cyc"]]
    I5 = cyc_one_mat(5)
    omega = cyc_omega(1)
    out = []

    out.append(_verdict(group, "x_pow5_is_identity",
                        cyc_mat_eq(cyc_mat_pow(X, 5), I5),
                        "X^5 == I, exakt in Z[omega] (zyklische Verschiebung)"))
    out.append(_verdict(group, "z_pow5_is_identity",
                        cyc_mat_eq(cyc_mat_pow(Z, 5), I5),
                        "Z^5 == I, exakt in Z[omega] (omega^{5k} = 1)"))
    out.append(_verdict(group, "x_is_unitary",
                        cyc_mat_eq(cyc_mat_mul(cyc_mat_adj(X), X), I5)
                        and cyc_mat_eq(cyc_mat_mul(X, cyc_mat_adj(X)), I5),
                        "X^dagger X == X X^dagger == I, exakt (Permutationsmatrix)"))
    out.append(_verdict(group, "z_is_unitary",
                        cyc_mat_eq(cyc_mat_mul(cyc_mat_adj(Z), Z), I5)
                        and cyc_mat_eq(cyc_mat_mul(Z, cyc_mat_adj(Z)), I5),
                        "Z^dagger Z == Z Z^dagger == I, exakt (|omega^k|^2 = 1 in Z[omega])"))
    # Z X == omega X Z: beide Seiten kernel-seitig multipliziert.
    zx = cyc_mat_mul(Z, X)
    xz_scaled = cyc_mat_scalar_mul(omega, cyc_mat_mul(X, Z))
    out.append(_verdict(group, "z_commutation_relation",
                        cyc_mat_eq(zx, xz_scaled),
                        "Z X == omega X Z, exakt in Z[omega] (Weyl-Relation mod 5)"))
    return out


def verify_exactness_and_enclosures(claims):
    """Exaktheits- und Enclosure-Claims (EnclOK-Analogon). Die Mitgliedschaft
    float in rationalem Enclosure ist exakt pruefbar: Fraction(float) ist die
    exakte Binaerdarstellung, der Vergleich mit Fraction-Grenzen verliert
    nichts. Erzeugt 3 Verdicts."""
    group = "exactness_enclosures"
    disp = claims["groups"]["displacement"]
    out = []

    # X5: Float-Eintraege muessen exakt 0.0/1.0 (reell, Imaginaerteil exakt 0)
    # sein und der aufgezeichneten int-Matrix exakt entsprechen.
    x_exact = disp["X5"]
    x_float = disp["X5_float"]
    ok = all(float(x_float[i][j][1]) == 0.0
             and float(x_float[i][j][0]) == float(x_exact[i][j])
             for i in range(5) for j in range(5))
    out.append(_verdict(group, "x5_entries_exact",
                        ok, "X5-Float-Eintraege exakt 0.0/1.0 (reell), gleich der int-Matrix"))

    # Z5: Nebendiagonale exakt Null (Float-Vergleich mit 0.0 ist exakt).
    z_float = disp["Z5_float"]
    ok = all(float(z_float[i][j][0]) == 0.0 and float(z_float[i][j][1]) == 0.0
             for i in range(5) for j in range(5) if i != j)
    out.append(_verdict(group, "z5_offdiagonal_exact_zero",
                        ok, "Z5-Nebendiagonaleinträge exakt 0+0j"))

    # Z5-Diagonale in rationalen Enclosures (EnclOK-Analogon).
    ok = True
    for k in range(5):
        box = disp["Z5_enclosures"][k]
        for comp in (0, 1):
            lo = frac_from_json(box[comp][0:2])
            hi = frac_from_json(box[comp][2:4])
            val = Fraction(float(z_float[k][k][comp]))
            if not (lo <= val <= hi):
                ok = False
    out.append(_verdict(group, "z5_diagonal_in_enclosures",
                        ok,
                        "Z5-Diagonale in rationalen Enclosures (Fraction(float) exakt); "
                        "Verschaerftheit gegen wahre Einheitswurzeln = displayed hypothesis"))
    return out


def verify_dft_orthogonality(claims):
    """sum_k omega^{k(j-l)} = 5*delta_jl fuer alle (j,l): das Kernel berechnet
    alle 25 Summen selbst im Z[omega]-Ring (decide-Analogon: die Berechnung
    laeuft im Kernel, nicht beim Generator). Erzeugt 1 Verdict."""
    all_ok = True
    checked = 0
    for j in range(5):
        for l in range(5):
            acc = cyc_zero()
            for k in range(5):
                acc = cyc_add(acc, cyc_omega((k * (j - l)) % 5))
            if j == l:
                # 5 * 1: als Summe fuenfmal 1 aufgebaut (Z[omega] reduziert
                # Koeffizienten NICHT mod 5 — Verdoppeln gaebe 8, nicht 5).
                expected = cyc_zero()
                for _ in range(5):
                    expected = cyc_add(expected, cyc_one())
            else:
                expected = cyc_zero()
            if not cyc_eq(acc, expected):
                all_ok = False
            checked += 1
    return [_verdict("dft", "dft_orthogonality_5delta", all_ok,
                     f"{checked} Identitaeten sum_k omega^(k(j-l)) == 5*delta_jl, "
                     "kernel-seitig in Z[omega] berechnet")]


def verify_pt_algebra(claims):
    """PT-Operatorenalgebra ueber exakt rationalen Exemplaren. Kriterium:
    [H, PT] = 0 mit T = komplexe Konjugation <=> P H P == conj(H).
    Erzeugt 9 Verdicts."""
    group = "pt_algebra"
    pt = claims["groups"]["pt"]
    P = qc_mat_from_int(pt["P"])
    P_int = [[int(v) for v in row] for row in pt["P"]]
    I2 = [[1, 0], [0, 1]]
    out = []

    out.append(_verdict(group, "p_square_is_identity",
                        int_mat_eq(int_mat_mul(P_int, P_int), I2),
                        "P^2 == I, exakt (Reversal-Permutation)"))

    ex = pt["exemplars"]

    def check_exemplar(name, H):
        php = qc_mat_mul(qc_mat_mul(P, H), P)
        ch = [[qc_conj(e) for e in row] for row in H]
        pt_ok = qc_mat_eq(php, ch)
        herm_ok = qc_mat_eq(qc_mat_adj(H), H)
        return [
            _verdict(group, f"{name}_pt_symmetric", pt_ok,
                     "P H P == conj(H) (<=> [H, PT] = 0), exakt rational"),
            _verdict(group, f"{name}_hermitian", herm_ok,
                     "H^dagger == H, exakt rational"),
        ]

    out += check_exemplar("dimer_canonical", qc_mat_from_json(ex["dimer_canonical"]["H"]))
    out += check_exemplar("project_form", qc_mat_from_json(ex["project_form"]["H"]))
    out += check_exemplar("anticommuted_form", qc_mat_from_json(ex["anticommuted_form"]["H"]))

    # Real-/Imaginaerteil-Zerlegung des Kriteriums fuer D + i*gamma*A-Formen:
    # P H P - conj(H) == (P D P - D) + i*gamma*(P A P + A).
    for name in ("project_form", "anticommuted_form"):
        spec = ex[name]
        D = qc_mat_from_int(spec["D"])
        A = qc_mat_from_int(spec["A"])
        gamma = frac_from_json(spec["gamma"])
        H = qc_mat_from_json(spec["H"])
        lhs = qc_mat_sub(qc_mat_mul(qc_mat_mul(P, H), P),
                         [[qc_conj(e) for e in row] for row in H])
        pdp = qc_mat_sub(qc_mat_mul(qc_mat_mul(P, D), P), D)
        pap_plus = qc_mat_add(qc_mat_mul(qc_mat_mul(P, A), P), A)
        igamma = qc(Fraction(0), gamma)
        rhs = qc_mat_add(pdp, qc_mat_scalar_mul(igamma, pap_plus))
        out.append(_verdict(group, f"{name}_criterion_split",
                            qc_mat_eq(lhs, rhs),
                            "P H P - conj(H) == (P D P - D) + i*gamma*(P A P + A), exakt"))
    return out


def verify_claims(claims):
    """Vollstaendige Kernel-Verifikation: alle Gruppen, Fingerprint, Totals."""
    verdicts = []
    verdicts += verify_gf5_tables(claims)
    verdicts += verify_displacement_algebra(claims)
    verdicts += verify_exactness_and_enclosures(claims)
    verdicts += verify_dft_orthogonality(claims)
    verdicts += verify_pt_algebra(claims)
    confirmed = sum(1 for v in verdicts if v["verdict"] == VERDICT_CONFIRMED)
    refuted = sum(1 for v in verdicts if v["verdict"] == VERDICT_REFUTED)
    return {
        "pattern": "C (finite kernel check, decide-analogue, zeta-23-lean LawN256 structure)",
        "generator": claims.get("generator", "unknown"),
        "verdicts": verdicts,
        "claims_total": len(verdicts),
        "confirmed": confirmed,
        "refuted": refuted,
        "claims_sha256": claims_sha256(claims),
    }


def claims_sha256(claims):
    payload = json.dumps(claims, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# =========================================================================
# === UNTRUSTED GENERATOR ===
# (lazy heavy imports; darf float und Projektcode nutzen — das Kernel
#  teilt keinen Code-Pfad mit dieser Sektion)
# =========================================================================

def generate_claims():
    """Berechnet die Claims mit Projektcode (UNTRUSTED). Alle Daten werden
    exakt serialisiert: int-Tabellen via GF5-Klasse, int-Matrizen exakt
    gesnappt (0.0/1.0), Float-Phasen mit rationalen Enclosures versehen,
    PT-Exemplare als kanonische rationale Form-Daten."""
    import numpy as np

    from pt_ququint_gf5 import GF5
    from pt_ququint_simulator import pauli_x_5, pauli_z_5

    # --- GF(5)-Tabellen via GF5-Klasse (untrusted Code-Pfad) ---
    add_table = [[int(GF5(a) + GF5(b)) for b in range(5)] for a in range(5)]
    mul_table = [[int(GF5(a) * GF5(b)) for b in range(5)] for a in range(5)]
    inverses = [int(GF5(a).inverse()) if a else 0 for a in range(5)]

    # --- X5 aus dem Simulator: Permutation, exakt ganzzahlig ---
    X_float = pauli_x_5()
    X_exact = [[int(X_float[i, j].real) for j in range(5)] for i in range(5)]
    for i in range(5):
        for j in range(5):
            re_v, im_v = float(X_float[i, j].real), float(X_float[i, j].imag)
            if im_v != 0.0 or re_v not in (0.0, 1.0):
                raise ValueError(
                    f"X5[{i},{j}] = {re_v!r}{im_v:+}j ist nicht exakt 0.0/1.0 "
                    "(reell) — Snap unzulaessig")

    # --- Z5 aus dem Simulator: Float-Diagonale + rationale Enclosures ---
    Z_float = pauli_z_5()
    Z_float_rec = [[[float(Z_float[i, j].real), float(Z_float[i, j].imag)]
                    for j in range(5)] for i in range(5)]
    Z_cyc = [[cyc_omega(k) if i == j == k else cyc_zero() for j in range(5)]
             for i, k in enumerate(range(5))]
    half_width = Fraction(1, 10 ** 12)
    enclosures = []
    for k in range(5):
        c_re = Fraction(float(Z_float[k, k].real))
        c_im = Fraction(float(Z_float[k, k].imag))
        lo_re, hi_re = c_re - half_width, c_re + half_width
        lo_im, hi_im = c_im - half_width, c_im + half_width
        enclosures.append([
            [int(lo_re.numerator), int(lo_re.denominator),
             int(hi_re.numerator), int(hi_re.denominator)],
            [int(lo_im.numerator), int(lo_im.denominator),
             int(hi_im.numerator), int(hi_im.denominator)],
        ])

    # --- PT-Exemplare: kanonische rationale Form-Daten (exakt) ---
    # Reversal-Paritaet auf 2 Leveln.
    P = [[0, 1], [1, 0]]
    # Kanonischer PT-Dimer: E=1, gamma=1/2, s=3/2.
    dimer_H = [
        [[1, 1, 1, 2], [3, 1, 0, 1]],   # 1 + i/2 , 3/2
        [[3, 1, 0, 1], [1, 1, -1, 2]],  # 3/2    , 1 - i/2
    ]
    # Projektform: D = diag(1,2), A = [[0,1],[1,0]] (reell-symmetrisch), gamma=1/2.
    proj_D = [[1, 0], [0, 2]]
    proj_A = [[0, 1], [1, 0]]
    proj_H = [
        [[1, 1, 0, 1], [0, 1, 1, 2]],   # 1 , i/2
        [[0, 1, 1, 2], [2, 1, 0, 1]],   # i/2 , 2
    ]
    # Antikommutierte Form: A = [[0,1],[-1,0]] (anticommutiert mit P), gamma=1/2.
    anti_D = [[1, 0], [0, 1]]
    anti_A = [[0, 1], [-1, 0]]
    anti_H = [
        [[1, 1, 0, 1], [0, 1, 1, 2]],   # 1 , i/2
        [[0, 1, -1, 2], [1, 1, 0, 1]],  # -i/2 , 1
    ]

    return {
        "generator": "pt_finite_kernel_check.generate_claims",
        "provenance": {
            "pattern": "C (decide-analogue, zeta-23-lean LawN256 structure)",
            "generator_trust": (
                "UNTRUSTED: Tabellen via pt_ququint_gf5.GF5-Klasse, Matrizen via "
                "pt_ququint_simulator (float); das Kernel teilt keinen Code-Pfad "
                "und re-deriviert alles aus den aufgezeichneten exakten Daten"),
            "enclosure_semantics": (
                "EnclOK-Analogon: rationale Enclosures (Halbbreite 1e-12) um die "
                "Float-Z5-Diagonale werden vom Generator aufgezeichnet; das Kernel "
                "prueft die Mitgliedschaft exakt (Fraction(float) ist exakt), die "
                "Verschaerftheit gegen die wahren 5. Einheitswurzeln ist displayed "
                "hypothesis wie die externen Intervall-Enclosures in LawN256.lean"),
            "pt_exemplars": (
                "kanonische rationale FORM-Exemplare (Dimer, Projektform "
                "D+i*gamma*A mit reell-symmetrischem A, antikommutiertes A): "
                "klassen-level exakte Aussagen, keine Float-Matrizen"),
        },
        "groups": {
            "gf5_tables": {
                "add_table": add_table,
                "mul_table": mul_table,
                "inverses": inverses,
            },
            "displacement": {
                "X5": X_exact,
                "X5_float": [[[float(X_float[i, j].real), float(X_float[i, j].imag)]
                              for j in range(5)] for i in range(5)],
                "Z5_cyc": [[list(e) for e in row] for row in Z_cyc],
                "Z5_float": Z_float_rec,
                "Z5_enclosures": enclosures,
            },
            "pt": {
                "P": P,
                "exemplars": {
                    "dimer_canonical": {"H": dimer_H},
                    "project_form": {"D": proj_D, "A": proj_A,
                                     "gamma": [1, 2], "H": proj_H},
                    "anticommuted_form": {"D": anti_D, "A": anti_A,
                                          "gamma": [1, 2], "H": anti_H},
                },
            },
        },
    }


def write_claims(claims, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(claims, fh, sort_keys=True, indent=2)
        fh.write("\n")


# =========================================================================
# CLI
# =========================================================================

def _print_result(result):
    print("=" * 75)
    print("PATTERN C: FINITE KERNEL CHECK (decide-analogue)")
    print("=" * 75)
    print(f"generator       : {result['generator']}")
    print(f"claims_sha256   : {result['claims_sha256']}")
    print(f"claims_total    : {result['claims_total']}")
    print(f"confirmed       : {result['confirmed']}")
    print(f"refuted         : {result['refuted']}")
    print("-" * 75)
    for v in result["verdicts"]:
        print(f"  [{v['verdict']:9s}] {v['group']}/{v['name']}")
    print("-" * 75)
    for v in result["verdicts"]:
        if v["verdict"] == VERDICT_REFUTED:
            print(f"  REFUTED-Fund: {v['name']} — {v['detail']}")
    print("=" * 75)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    mode = argv[0] if argv else "all"
    if mode in ("generate", "all"):
        claims = generate_claims()
        write_claims(claims, CLAIMS_PATH)
        print(f"Claims geschrieben: {CLAIMS_PATH} "
              f"(sha256 {claims_sha256(claims)[:16]}...)")
    if mode in ("verify", "all"):
        with open(CLAIMS_PATH, encoding="utf-8") as fh:
            claims = json.load(fh)
        result = verify_claims(claims)
        _print_result(result)
        with open(RESULT_PATH, "w", encoding="utf-8") as fh:
            json.dump(result, fh, sort_keys=True, indent=2)
            fh.write("\n")
        print(f"Result geschrieben: {RESULT_PATH}")


if __name__ == "__main__":
    main()