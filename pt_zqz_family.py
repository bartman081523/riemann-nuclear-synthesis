"""
EXPERIMENT 053 — H-ZQZ: geschlossene Z/qZ-Restklassen-Familie der
MOCS-Observablen (Statevector, 0 QPU).

Auslöser: kritik1.txt Punkt 1/4 (Stichproben-Karussell -> all-Quantor)
und die ChatGPT-Angebot-Formulierung: reine Statevector-Analyse der
MOCS-Observablen (alpha_vN, R(N), c_v) auf einer GESCHLOSSENEN
Restklassen-Familie. Erster Lauf nach dem Messverbund-Flow-Diagramm
(RIEMANN §10.36, Regel R1/R5) mit dem Prereg-Pflichtfeld
quantor_coverage (§10.37).

GLIEDERUNG (drei Leg-Verdicts, ex ante gefroren):
  L1  Klassen-Hold:  alpha_vN, R(N), c_v auf Klassen a = 1..q-1 fuer
      q in {3,5,7}; Zählidentität Sigma_a pi_a + [q<=N] == pi(N) EXAKT;
      Raw-Union-Vektor == |P_N> bit-exakt; S_vN/R_N(Union) gegen die
      committeten 023-EXT-Rows (md5-gepinnt, Toleranz 1e-12).
  L2  Rényi-3-Unabhängigkeits-Gate (§X.3-Kandidat: Entropie-Familie):
      Kandidat QUALIFIZIERT nur wenn |rho(S3, S_vN)| < RHO_CAND_MAX
      (erwartungsoffen registriert; mechanisch redundant moeglich).
  L3  GUE-<r>-Gate (§X.3-Kandidat: Eigenwerte des Hilbert-Pólya-
      Proxys, NICHT die gefaltete V3-Hamilton-Familie): unfolded-frei
      <r>_raw (V3-komparabel) UND lokal-entfaltet <r>_unf gegen die
      korrigierte GUE-Konstante 0.5996 (Atas et al., arXiv:1212.5611;
      Poisson 0.3863, GOE 0.5307); Qualifikation nur im GUE-Band UND
      unabhängig von R_N UND außerhalb des V3-DEGENERAT-Bands.

SUPPORT-LEG (prime-quant auf ibm_fez): im Prereg REGISTRIERT
(REGISTERED_NOT_SUBMITTED), Ausfuehrung erst nach L1-Auswertung und
separater Freigabe — protokoll-treu zu pt_prime_state_qpu_singleshot
(psi' = (U_A^dagger ⊗ I)|P_N>, Statevector.from_instruction als
Verifikations-Gate). KEIN neues Rauschgesetz am Bein (R4).

Ketten-Muster (Haus-Stil all-in-one, wie pt_ramanujan_replication /
pt_ram_q_asymptotik):
  --freeze  Prereg canonical + md5-Pin committet VOR Messung
  --run     Messung -> RAW JSON (KEINE Verdicts)
  --eval    Roh-Commit VOR Auswertung; Auswertung mit decide ex ante
"""
import argparse
import hashlib
import json
import math
import subprocess
import sys

import numpy as np
from scipy.linalg import eigh_tridiagonal
from scipy.stats import spearmanr

from pt_prime_state import sieve_primes, construct_P_N, measure_entropy
from pt_rh_multi_observable import (
    alpha_vN_scaling,
    latorre_ratio,
    evaluate_alpha,
    evaluate_latorre_ratio,
    jacobi_matrix_for_primes,
)
from pt_ququint_gue import r_statistic

# ---------- Artefakte ----------
PREREG_PATH = "pt_zqz_family_prereg.json"
RAW_PATH = "pt_zqz_family_raw.json"
RESULTS_PATH = "pt_zqz_family_results.json"
EXT_RESULTS_PATH = "pt_rh_multi_observable_ext_results.json"

PREREG_MD5 = "53c801d8f1d3ecc755a89fec87c213c7"   # gefroren 2026-10-02, VOR jeder Messung

# ---------- Gitter (quantor_coverage: mode=closed) ----------
N_SWEEP = [7, 15, 31, 63, 127, 255, 511, 1023,
           2047, 4095, 8191, 16383, 32767, 65535]
Q_LIST = [3, 5, 7]                       # Moduli; Klassen a = 1..q-1

# ---------- gefrorene Schwellen (ex ante, KEINE Toleranz-Erhoehung) ----------
ALPHA_MAX = 0.5          # v1-frozen (023)
R_TO_1 = 1.0             # v1-frozen (023)
UNION_TOL = 0.0          # Raw-Union-Vektor: EXAKT (IEEE-Addition von 0/1)
R_BOUND_ARITH = 1e-12    # R_a <= 1 + dies (Sättigung durch perfekte
                         # Entfleckung erlaubt — ex ante Grenzfall q=5,a=1,N=63)
PIN_TOL = 1e-12          # S_vN/R_N(Union) gegen committete 023-EXT-Rows
SPECTRUM_TOL = 1e-15     # eigene Schmidt-Spektrum-Rueckrechnung vs measure_entropy
TRIDIAG_TOL = 1e-10      # dense-vs-tridiagonal Jacobi-Spektrum Kreuzcheck
RHO_CAND_MAX = 0.85      # L2/L3-Unabhängigkeits-Gate (I2-Familie, konservativ)
GUE_BAND = (0.52, 0.68)  # korrigierte GUE-Konstante 0.5996 ± 0.08 (finite size)
POISSON_SEP = 0.05       # Mindestabstand der Bandunterkante zu Poisson+Drift
V3_BAND = (0.19, 0.23)   # V3-DEGENERAT (d25 0.2059 / d625 0.2199)
V3_SEP = 0.10            # Mindestabstand des Bands zum V3-Band

# Referenzkonstanten (Primärliteratur, prüfpflichtig)
POISSON_R = 0.3863
GOE_R = 0.5307
GUE_R = 0.5996           # Atas et al. 2013 (arXiv:1212.5611); vormals
                         # GOE-Surmise 0.5359 = 4 - 2 sqrt(3) — korrigiert
UNFOLD_WINDOW = 5        # lokales Unfolding: Fenster ±5 benachbarte Lücken

VERDICT_IDS = {
    "l1_held": "H_ZQZ_L1_HELD",
    "l1_refuted": "H_ZQZ_L1_REFUTED",
    "l2_candidate": "H_ZQZ_L2_CANDIDATE_QUALIFIED",
    "l2_redundant": "H_ZQZ_L2_REDUNDANT_WITH_S_VN",
    "l3_candidate": "H_ZQZ_L3_GUE_CANDIDATE_QUALIFIED",
    "l3_out_of_band": "H_ZQZ_L3_REFUSED_OUT_OF_BAND",
    "l3_dependent": "H_ZQZ_L3_REFUSED_DEPENDENT",
    "l3_undetermined": "H_ZQZ_L3_UNDETERMINED_SMALL_M",
}


# ---------- Schmidt-Spektrum (maschinengleich zu measure_entropy) ----------

def schmidt_spectrum(psi):
    """Schmidt-Wahrscheinlichkeiten s_i^2, maschinengleich zu
    pt_prime_state.measure_entropy (dieselbe n_A-Regel, dieselbe
    reshape-Konvention, derselbe 1e-12-Cut).

    Returns: (s_sq, n_A, n_B)
    """
    dim = len(psi)
    n_A = int(math.sqrt(dim))
    while dim % n_A != 0 and n_A > 1:
        n_A -= 1
    n_B = dim // n_A
    psi_matrix = psi.reshape(n_A, n_B)
    _, S, _ = np.linalg.svd(psi_matrix)
    s_sq = S ** 2
    s_sq = s_sq[s_sq > 1e-12]
    return s_sq, n_A, n_B


def s_vn_from_spectrum(s_sq):
    """S_vN in natuerlichem Log (maschinengleich zu measure_entropy)."""
    return -float(np.sum(s_sq * np.log(s_sq)))


def renyi_natural(s_sq, alpha):
    """Rényi-Entropie in natuerlichem Log: S_alpha = log(sum s_sq^alpha)/(1-alpha).

    alpha in (0, 1) u. (1, inf); alpha=1 ist der Grenzfall vN (nicht hier).
    Reihenfolge-Cut: wie schmidt_spectrum (s_sq > 0 nach dem 1e-12-Cut).
    """
    s_sq = np.asarray(s_sq, dtype=float)
    s_sq = s_sq[s_sq > 0]
    return float(np.log(np.sum(s_sq ** alpha)) / (1.0 - alpha))


# ---------- Klassen-Arithmetik (mode=closed) ----------

def class_counts(primes, q):
    """pi_a fuer a = 1..q-1 (Liste, Index 0 -> a=1)."""
    pi = [0] * (q - 1)
    for p in primes:
        a = p % q
        if a >= 1:
            pi[a - 1] += 1
    return pi


def raw_class_vector(N, dim, q, a):
    """UNnormierter Klassenvektor u_a = Summe_{p<=N, p=a mod q} |p>.

    a=0 deckt p=q ab (einzige Primzahl ≡ 0 mod q)."""
    u = np.zeros(dim, dtype=complex)
    for p in sieve_primes(N):
        if p % q == a:
            u[p] = 1.0
    return u


def union_vector(N):
    """Raw-Union ALLER Klassenvektoren (a = 0..q-1, q=5-Repraesentant)
    == sqrt(pi(N)) * P_N — EXAKT in float64."""
    P_N, dim, _ = construct_P_N(N)
    primes = sieve_primes(N)
    q = 5  # Repraesentant; Identitaet gilt fuer alle q (Zählidentität separat)
    acc = np.zeros(dim, dtype=complex)
    for a in range(0, q):
        acc = acc + raw_class_vector(N, dim, q, a)
    return P_N, acc, math.sqrt(len(primes))


# ---------- Jacobi-Spektrum (Proxy) ----------

def proxy_eigs_tridiag(primes):
    """Eigenwerte des Jacobi-Proxys via eigh_tridiagonal (O(n^2), stabil).

    d = Diagonale (p_k), e = Nebendiagonale (|p_{k+1} - p_k|) — exakt die
    dense-Matrix aus pt_rh_multi_observable.jacobi_matrix_for_primes.
    """
    d = np.asarray([float(p) for p in primes])
    if d.size < 2:
        return np.array([])
    e = np.abs(np.diff(d))
    return eigh_tridiagonal(d, e, eigvals_only=True)


def unfold_local(eigs, window=UNFOLD_WINDOW):
    """Lokales Unfolding auf dem SPEKTRUM (Referenz-Variante; in der
    Praxis laeuft das Unfolding auf den Luecken via unfold_gaps)."""
    return unfold_gaps(np.diff(np.sort(np.asarray(eigs, dtype=float))),
                       window=window)


# ---------- Prereg-Kette ----------

def current_branch():
    out = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


def build_prereg_payload():
    """Canonical Prereg (ohne md5-Feld)."""
    return {
        "experiment": "EXPERIMENT 053",
        "hypothesis": "H-ZQZ-1",
        "title": ("Geschlossene Z/qZ-Restklassen-Familie der MOCS-Observablen "
                  "(Statevector, 0 QPU) + Kandidaten-Gates fuer ein drittes "
                  "unabhaengiges Observable"),
        "date_locked": "2026-10-02",
        "branch": current_branch(),
        "methodology": {
            "device": "G1 EXAKT-STATEVECTOR (0 QPU); G3/G4 Support-Bein "
                      "REGISTRIERT, nicht eingereicht (§10.36 R1-R5)",
            "elements": "E1 Primbasis (pt_prime_state.construct_P_N/measure_entropy), "
                        "E6 Spektral-Proxy (jacobi_matrix_for_primes), "
                        "Statisitk-Kern pt_ququint_gue.r_statistic",
            "schmidt_split": "maschinengleich zu measure_entropy (natuerlicher Log)",
            "renyi_convention": "natuerlicher Log, S_alpha = log(sum s^alpha)/(1-alpha)",
            "unfolding": f"lokal, Fenster ±{UNFOLD_WINDOW} benachbarte Luecken",
            "committeter_anker": f"023-EXT Rows ({EXT_RESULTS_PATH}) S_vN/R_N",
        },
        "quantor_coverage": {
            "universe": "primes p <= N, N im 14-Punkte-Gitter 7..65535",
            "mode": "closed",
            "modulus": Q_LIST,
            "classes": {str(q): list(range(1, q)) for q in Q_LIST},
            "n_max": 65535,
            "ex_ante": True,
            "grid_rule": None,
            "disclosure": (
                "Klassenvektor |P_N^(q,a)> = (1/sqrt(pi_a)) Summe ueber "
                "p<=N, p=a mod q; a=0 entfaellt (p=q selbst gezaehlt via "
                "[q<=N]); Zählidentitaet Sigma_a pi_a + [q<=N] == pi(N) "
                "exakt; R_a nur fuer pi_a >= 2 (latorre_ratio-Grenzfall); "
                "Bipartition pro (N) identisch zum vollen P_N (n_A-Regel "
                "sqrt-Dekrement); pi_a je Zeile publiziert"
            ),
        },
        "grid": {"n_sweep": N_SWEEP, "q_list": Q_LIST,
                 "classes": {str(q): list(range(1, q)) for q in Q_LIST}},
        "thresholds": {
            "alpha_max": ALPHA_MAX,
            "r_to_1": R_TO_1,
            "r_bound_arith": R_BOUND_ARITH,
            "union_tol": UNION_TOL,
            "pin_tol": PIN_TOL,
            "spectrum_tol": SPECTRUM_TOL,
            "tridiag_tol": TRIDIAG_TOL,
            "rho_cand_max": RHO_CAND_MAX,
            "gue_band": list(GUE_BAND),
            "poisson_sep": POISSON_SEP,
            "v3_band": list(V3_BAND),
            "v3_sep": V3_SEP,
        },
        "constants": {"poisson_r": POISSON_R, "goe_r": GOE_R,
                      "gue_r": GUE_R, "gue_ref": "Atas et al. 2013, arXiv:1212.5611"},
        "verdict_map": {
            "l1": ("HELD iff closure EXAKT fuer alle (N,q) UND union_vec_max_dev "
                   "== 0.0 UND S_vN/R_N(Union) Pins <= 1e-12 UND alpha_a < 0.5 "
                   "fuer alle fitfaehigen Klassen UND R_a <= 1 + 1e-12 fuer "
                   "alle inkludierten (q,a,N); sonst REFUTED. "
                   "Begruendung der Grenz-Regel: perfekt entflochtene "
                   "Klassen saturieren die Latorre-Konstante EXAKT "
                   "(R_a = 1, ex ante bekannt: q=5, a=1, N=63 — vier "
                   "Primzahlen in perfekter Zeilen/Spalten-Abdeckung); "
                   "das ist Sattigung, keine Verletzung; R_a > 1 + 1e-12 "
                   "refutiert weiterhin (super-logarithmische Klasse)."),
            "l2": ("CANDIDATE_QUALIFIED iff |rho(S3_pool, S_vN_pool)| < 0.85; "
                   "sonst REDUNDANT_WITH_S_VN (erwartungsoffen: Entropie-"
                   "Familie teilt das Schmidt-Spektrum mechanisch)"),
            "l3": ("GUE_CANDIDATE_QUALIFIED iff <r>_unf(Union, N=65535) in "
                   "[0.52, 0.68] UND |rho(<r>_unf-Serie(14 Unions), "
                   "R_N-Serie)| < 0.85 UND Bandabstaende respektiert "
                   "(Bandsunterkante - Poisson 0.3863 >= 0.05, "
                   "Bandsunterkante - V3-Oberkante 0.23 >= 0.10); sonst "
                   "REFUSED_OUT_OF_BAND / REFUSED_DEPENDENT; "
                   "UNDETERMINED_SMALL_M falls M < 2 Luecken"),
        },
        "verdict_ids": VERDICT_IDS,
        "commit_rules": [
            "Prereg-Freeze VOR jeder Messung (REGISTERED_NOT_MEASURED)",
            "Roh-Commit VOR Auswertung (RAW enthaelt KEINE Verdicts)",
            "Auswertung mit decide() ex ante gegen gefrorene Schwellen",
            "KEINE Toleranz-Erhoehung; Einstufung statt stillem Re-Decide",
        ],
        "support_leg": {
            "status": "REGISTERED_NOT_SUBMITTED",
            "backend": "ibm_fez (TOKEN1)",
            "trigger": ("NUR nach L1-Auswertung HELD und separater Freigabe "
                        "(R3: ein Job, job-id-File, Kalibrier-Bein)"),
            "protocol": ("pt_prime_state_qpu_singleshot-Muster: "
                         "psi' = (U_A^dagger ⊗ I)|P_N^(q,a)>, "
                         "Statevector.from_instruction als Verifikations-Gate, "
                         "8192 Shots"),
            "target": ("Klassenstatus |P_N^(q=3, a=1)> bei N=31; gemessen: "
                       "Schmidt-Spektren-Verteilung; Vergl. S_vN_QPU vs "
                       "S_vN_SV (Bias gemeldet, KEIN Rauschgesetz-Fit)"),
            "no_new_noise_law": True,
        },
        "numpy_build": np.__version__,
    }


def payload_md5(payload):
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)
    return hashlib.md5(blob.encode("utf-8")).hexdigest()


def write_prereg(path=PREREG_PATH):
    payload = build_prereg_payload()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, sort_keys=True, separators=(",", ":"),
                  ensure_ascii=False)
    return payload_md5(payload)


def load_frozen(path=PREREG_PATH, expected_md5=None):
    """Freeze-Loader: md5 KANONISCH (ueber den geparsten Inhalt, payload_md5)
    — identisch zur Freeze-Anzeige; Byte-md5 des indent-Files weicht ab
    (Repair 2026-10-02: raw-Prereg-Feld war e31d89... (Byte-md5 des
    indent-1-Files), kanonischer Freeze-MD5 53c801d8... — identisches
    gefrorenes CONTENT, nur Serialisierung anders; siehe Doku §10.38)."""
    with open(path, "rb") as f:
        raw = f.read()
    md5 = payload_md5(json.loads(raw.decode("utf-8")))
    if expected_md5 is not None and md5 != expected_md5:
        raise SystemExit(
            f"PREREG-MISMATCH: {path} md5 {md5} != {expected_md5} "
            "- Freeze gebrochen, Abbruch.")
    return json.loads(raw.decode("utf-8")), md5


def freeze_prereg(path=PREREG_PATH):
    """Freeze: schreibe Prereg und returniere den MD5 (einziger Ort,
    an dem PREREG_MD5 gesetzt wird — danach manuell in die Konstante
    uebernehmen und committen)."""
    payload = build_prereg_payload()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, sort_keys=True, separators=(",", ":"),
                  ensure_ascii=False, indent=1)
    md5 = payload_md5(payload)
    print(f"PREREG_FROZEN md5={md5}")
    return md5


# ---------- Messung (RAW: keine Verdicts) ----------

def run_measurement():
    import os
    if os.path.exists(RAW_PATH):
        raise SystemExit(
            f"RAW-EXISTIERT-BEREITS: {RAW_PATH} — kein stiller Re-Run "
            "(Raw-Commit-Disziplin). Loeschen ist ein expliziter Akt.")
    # GEFRORENES Prereg (Quantor-Feld + md5 aus dem Freeze, kein Rebuild)
    prereg, prereg_md5 = load_frozen(expected_md5=PREREG_MD5)
    rows_union = []
    rows_class = []
    closure_matrix = []
    crosschecks = {}

    for N in N_SWEEP:
        P_N, dim, n_qubits = construct_P_N(N)
        primes = sieve_primes(N)
        pi_N = len(primes)
        s_full, n_A, n_B = schmidt_spectrum(P_N)
        # Selbstcheck: eigene Rueckrechnung == measure_entropy
        S_me, S_max, nA2, nB2 = measure_entropy(P_N)
        assert (nA2, nB2) == (n_A, n_B), f"Bipartition-Divergenz bei N={N}"
        S_self = s_vn_from_spectrum(s_full)
        dev_s = abs(S_self - S_me)
        assert dev_s <= SPECTRUM_TOL, f"Spektrum-Rueckrechnung N={N}: {dev_s}"

        # Union-Zeile (alle drei Klassensysteme gleichzeitig)
        u_rows = {}
        for q in Q_LIST:
            pi_a = class_counts(primes, q)
            # Zählidentität: Sigma pi_a + [q <= N] == pi(N)
            ident = (sum(pi_a) + (1 if q <= N else 0)) == pi_N
            if not ident:
                raise SystemExit(f"ZAEHLIDENTITAET VERLETZT N={N} q={q}")
            # Raw-Union-Vektor (a = 0..q-1, p=q via a=0) == sqrt(pi) * P_N (EXAKT)
            acc = np.zeros(dim, dtype=complex)
            for a in range(0, q):
                u_a = raw_class_vector(N, dim, q, a)
                if a >= 1 and pi_a[a - 1] > 0:
                    v_a = u_a / math.sqrt(pi_a[a - 1])
                    u_rows[(q, a)] = v_a
                acc = acc + u_a
            dev_un = float(np.max(np.abs(acc - math.sqrt(pi_N) * P_N)))
            assert dev_un == 0.0, f"UNION-VEKTOR N={N} q={q}: {dev_un}"
            crosschecks.setdefault("union_vec_max_dev", []).append(dev_un)
        closure_matrix.append({"N": N, "pi_N": pi_N, "q": Q_LIST,
                               "pi_a": [class_counts(primes, q) for q in Q_LIST],
                               "identity_exact": True})

        # Raw-Klassenvektoren (q=5-Repraesentant) fuer die Union-Bit-Exaktheit
        P_N_ref, acc_ref, scale_ref = union_vector(N)
        assert float(np.max(np.abs(acc_ref - math.sqrt(len(primes)) * P_N))) == 0.0

        # Jacobi-Spektrum (Union = volle Primfolge)
        eigs_u = proxy_eigs_tridiag(primes)
        # Kreuzcheck dense-vs-tridiagonal (nur kleine N, registriert)
        if pi_N <= 1023:
            A = jacobi_matrix_for_primes(primes)
            eigs_d = np.linalg.eigvalsh(A) if A.size else np.array([])
            dd = float(np.max(np.abs(np.sort(eigs_d) - eigs_u))) if eigs_d.size else 0.0
            assert dd <= TRIDIAG_TOL, f"TRIDIAG-CROSSCHECK N={N}: {dd}"
            crosschecks.setdefault("tridiag_max_dev", []).append(dd)

        # Klassen-SVDs (auf derselben Bipartition)
        class_S = {}
        class_R_included = {}
        for q in Q_LIST:
            for a in range(1, q):
                pi_a = class_counts(primes, q)[a - 1]
                if pi_a < 2:
                    rows_class.append({"N": N, "q": q, "a": a, "pi_a": pi_a,
                                       "included": False, "S_vN": None,
                                       "S2": None, "S3": None, "R_a": None})
                    continue
                v = u_rows[(q, a)]
                s_sq, _, _ = schmidt_spectrum(v)
                S_c = s_vn_from_spectrum(s_sq)
                S2 = renyi_natural(s_sq, 2.0)
                S3 = renyi_natural(s_sq, 3.0)
                R_a = latorre_ratio(S_c, pi_a)
                rows_class.append({"N": N, "q": q, "a": a, "pi_a": pi_a,
                                   "included": True,
                                   "S_vN": float(S_c), "S2": float(S2),
                                   "S3": float(S3), "R_a": float(R_a)})
                class_S[(q, a)] = S_c
                class_R_included[(q, a)] = R_a

        # Union-Observable (bit-kompatibel zu 023-EXT: measure_entropy-Pfad)
        S_vN, S_max, _, _ = measure_entropy(P_N)
        R_N = latorre_ratio(S_vN, pi_N)
        S2_u = renyi_natural(s_full, 2.0)
        S3_u = renyi_natural(s_full, 3.0)
        r_raw_N, r_unf_N, m_gaps = spacing_stats(eigs_u)
        rows_union.append({
            "N": N, "pi_N": pi_N, "dim": dim, "n_qubits": n_qubits,
            "n_A": n_A, "n_B": n_B,
            "S_vN": float(S_vN), "S2": float(S2_u), "S3": float(S3_u),
            "R_N": float(R_N),
            "r_raw": r_raw_N, "r_unf": r_unf_N, "m_gaps": m_gaps,
        })

    raw = {
        "prereg_md5": prereg_md5,
        "numpy_build": np.__version__,
        "n_sweep": N_SWEEP,
        "q_list": Q_LIST,
        "quantor_coverage": prereg["quantor_coverage"],
        "union_rows": rows_union,
        "class_rows": rows_class,
        "closure_matrix": closure_matrix,
        "crosschecks": crosschecks,
        "constants": {"poisson_r": POISSON_R, "goe_r": GOE_R, "gue_r": GUE_R,
                      "unfold_window": UNFOLD_WINDOW},
    }
    with open(RAW_PATH, "w", encoding="utf-8") as f:
        json.dump(raw, f, sort_keys=True, indent=1)
    print(f"RAW geschrieben: {RAW_PATH} (union={len(rows_union)}, "
          f"class={len(rows_class)})")
    return raw


def spacing_stats(eigs):
    """(<r>_raw [V3-komparabel, unfolded-frei], <r>_unf [lokal entfaltet],
    M = Anzahl Luecken) — None-wertig bei M < 2 Luecken."""
    eigs = np.sort(np.asarray(eigs, dtype=float))
    d = np.diff(eigs)
    d = d[d > 0]
    if d.size < 2:
        return None, None, int(d.size)
    r_raw = r_distinct_from_gaps(d)
    g = unfold_gaps(d)
    r_unf = r_distinct_from_gaps(g)
    return (float(r_raw), float(r_unf), int(d.size))


def r_distinct_from_gaps(d):
    """Oganesyan-Huse-r direkt aus Luecken (aequivalent zu r_statistic auf
    dem sortierten Spektrum, ohne Kollabier-Rundung)."""
    d = np.asarray(d, dtype=float)
    if d.size < 2:
        return None
    denom = np.maximum(d[:-1], d[1:])
    r = np.minimum(d[:-1], d[1:]) / denom
    return float(r.mean())


def unfold_gaps(d, window=UNFOLD_WINDOW):
    """Lokales Unfolding auf der Luecken-Folge (deterministisch)."""
    d = np.asarray(d, dtype=float)
    m = d.size
    g = np.empty(m)
    for i in range(m):
        lo = max(0, i - window)
        hi = min(m, i + window + 1)
        g[i] = d[i] / float(np.mean(d[lo:hi]))
    return g


# ---------- Auswertung (decide ex ante, Roh VOR Auswertung committed) ----------

def decide(raw, prereg, prereg_md5):
    # Kette RAW -> Prereg (md5-Gleichheit, Freeze-Kette intakt)
    assert raw["prereg_md5"] == prereg_md5, (
        f"RAW-PREREG-MISMATCH: {raw['prereg_md5']} != {prereg_md5}")
    th = prereg["thresholds"]
    union = raw["union_rows"]
    classes = raw["class_rows"]
    N_MAX = raw["n_sweep"][-1]

    # --- Pins gegen committete 023-EXT-Rows ---
    with open(EXT_RESULTS_PATH) as f:
        ext = json.load(f)
    ext_by_N = {r["N"]: r for r in ext["rows"]}
    pin_dev_S = [abs(u["S_vN"] - ext_by_N[u["N"]]["S_vN"]) for u in union]
    pin_dev_R = [abs(u["R_N"] - ext_by_N[u["N"]]["R_N"]) for u in union]
    pins_ok = max(pin_dev_S) <= th["pin_tol"] and max(pin_dev_R) <= th["pin_tol"]

    union_dev = raw["crosschecks"].get("union_vec_max_dev", [0.0])
    union_ok = max(union_dev) == 0.0
    closure_ok = all(c["identity_exact"] for c in raw["closure_matrix"])

    # --- L1: Klassen-Verdicts ---
    alpha_class = {}
    r_ok = True
    alpha_ok = True
    for q in prereg["grid"]["q_list"]:
        for a in prereg["grid"]["classes"][str(q)]:
            pts = [r for r in classes
                   if r["q"] == q and r["a"] == a and r["included"]]
            if len(pts) < 3:
                alpha_class[f"q={q},a={a}"] = None
                continue
            alpha_a, log_a = alpha_vN_scaling([r["N"] for r in pts],
                                              [r["S_vN"] for r in pts])
            alpha_class[f"q={q},a={a}"] = {
                "alpha": float(alpha_a), "log_const": float(log_a),
                "n_pts": len(pts),
                "rh_consistent": bool(evaluate_alpha(alpha_a)),
            }
            if not evaluate_alpha(alpha_a):
                alpha_ok = False
            for p in pts:
                if p["R_a"] is not None and p["R_a"] > 1.0 + th["r_bound_arith"]:
                    r_ok = False
    l1_held = closure_ok and union_ok and pins_ok and alpha_ok and r_ok
    l1_verdict = VERDICT_IDS["l1_held"] if l1_held else VERDICT_IDS["l1_refuted"]

    # --- L2: Rényi-3-Unabhängigkeits-Gate ---
    pool_S = [row["S_vN"] for row in union] + [
        r["S_vN"] for r in classes if r["included"]]
    pool_S3 = [row["S3"] for row in union] + [
        r["S3"] for r in classes if r["included"]]
    rho_S3, _ = spearmanr(pool_S3, pool_S)
    l2_ok = abs(float(rho_S3)) < th["rho_cand_max"]
    l2_verdict = (VERDICT_IDS["l2_candidate"] if l2_ok
                  else VERDICT_IDS["l2_redundant"])

    # --- L3: GUE-<r>-Gate ---
    last_u = next(u for u in union if u["N"] == N_MAX)
    r_unf_last = last_u["r_unf"]
    lo, hi = th["gue_band"]
    in_band = r_unf_last is not None and lo <= r_unf_last <= hi
    # Unabhängigkeit: <r>_unf-Serie (Union, 14 P) vs R_N-Serie
    r_unf_series = [u["r_unf"] for u in union]
    r_series_ok = all(x is not None for x in r_unf_series)
    rho_r = (spearmanr(r_unf_series, [u["R_N"] for u in union])[0]
             if r_series_ok else None)
    sep_poisson = lo - raw["constants"]["poisson_r"]
    sep_v3 = lo - th["v3_band"][1]
    band_ok = (sep_poisson >= th["poisson_sep"] and sep_v3 >= th["v3_sep"])
    if r_unf_last is None or last_u["m_gaps"] < 3:
        l3_verdict = VERDICT_IDS["l3_undetermined"]
    elif not in_band:
        l3_verdict = VERDICT_IDS["l3_out_of_band"]
    elif abs(float(rho_r)) >= th["rho_cand_max"]:
        l3_verdict = VERDICT_IDS["l3_dependent"]
    else:
        l3_verdict = VERDICT_IDS["l3_candidate"]

    results = {
        "prereg_md5": raw["prereg_md5"],
        "raw_path": RAW_PATH,
        "pins": {
            "max_pin_dev_S": float(max(pin_dev_S)),
            "max_pin_dev_R": float(max(pin_dev_R)),
            "pin_tol": th["pin_tol"],
            "pins_ok": bool(pins_ok),
            "union_vec_max_dev": float(max(union_dev)),
            "union_ok": bool(union_ok),
            "closure_ok": bool(closure_ok),
        },
        "alpha_class": alpha_class,
        "alpha_combined_recomputed": float(
            alpha_vN_scaling(raw["n_sweep"], [u["S_vN"] for u in union])[0]),
        "alpha_combined_committed": float(ext["alpha_combined"]),
        "alpha_combined_dev": float(abs(
            alpha_vN_scaling(raw["n_sweep"], [u["S_vN"] for u in union])[0]
            - ext["alpha_combined"])),
        "class_stats": {
            "n_class_rows": len(classes),
            "n_included": sum(1 for r in classes if r["included"]),
            "R_a_max": float(max(r["R_a"] for r in classes if r["included"])),
            "n_R_at_saturation": sum(
                1 for r in classes
                if r["included"] and abs(r["R_a"] - 1.0) <= th["r_bound_arith"]),
            "R_all_within_bound": bool(r_ok),
        },
        "c_profile": c_profile(classes),
        "l2": {
            "rho_S3_vs_SvN_pool": float(rho_S3),
            "rho_cand_max": th["rho_cand_max"],
            "qualified": bool(l2_ok),
            "verdict": l2_verdict,
        },
        "l3": {
            "r_unf_union_Nmax": r_unf_last,
            "r_raw_union_Nmax": last_u["r_raw"],
            "gue_band": list(GUE_BAND),
            "poisson_r": raw["constants"]["poisson_r"],
            "goe_r": raw["constants"]["goe_r"],
            "gue_r": raw["constants"]["gue_r"],
            "v3_band": list(V3_BAND),
            "rho_r_vs_R": (float(rho_r) if rho_r is not None else None),
            "sep_poisson": float(sep_poisson),
            "sep_v3": float(sep_v3),
            "band_ok": bool(band_ok),
            "m_gaps": last_u["m_gaps"],
            "verdict": l3_verdict,
        },
        "verdicts": {"l1": l1_verdict, "l2": l2_verdict, "l3": l3_verdict},
    }
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, sort_keys=True, indent=1)
    print("VERDICTS:", results["verdicts"])
    return results


def c_profile(classes):
    """c_v-Familienprofil: Variationskoeffizient von R_a ueber Klassen je N
    (formel-registriert, Standardabweichung ddof=0, nur N mit >= 3 inkl.)."""
    out = {}
    for N in sorted({r["N"] for r in classes}):
        rs = [r["R_a"] for r in classes
              if r["N"] == N and r["included"] and r["R_a"] is not None]
        if len(rs) < 3:
            continue
        mean = float(np.mean(rs))
        std = float(np.std(rs, ddof=0))
        out[str(N)] = {"n_classes": len(rs), "mean": mean, "std": std,
                       "c_v": (std / mean if mean > 0 else None),
                       "min": float(min(rs)), "max": float(max(rs))}
    return out


# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--eval", action="store_true")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    if args.freeze or args.all:
        freeze_prereg()
    if args.run or args.all:
        run_measurement()
    if args.eval or args.all:
        prereg, md5 = load_frozen(expected_md5=PREREG_MD5)
        with open(RAW_PATH) as f:
            raw = json.load(f)
        decided = decide(raw, prereg, md5)
        print(json.dumps(decided["verdicts"], indent=1))


if __name__ == "__main__":
    main()