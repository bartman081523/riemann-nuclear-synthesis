"""
EXPERIMENT 054 — H-ZQZ-GOE: GOE-fokussiertes Band fuer das Dritte-
Observable-Gate des Union-<r>-Signals (0 QPU, Einstufungs-Experiment).

Ausloeser: das in EXPERIMENT 053 dokumentierte Angebot ("Ein
nachfolgendes Prereg mit explizit GOE-fokussiertem Band (H-ZQZ-GOE,
"054") ist ANGEBOTEN und NICHT ausgefuehrt", RIEMANN
§10.38 / SYNTHESIS §Z.35) plus die User-Aufgabe 2026-10-05
("mache alle noch offenen Tasks aus dem Plan INVESTIGATION_PLAN.md").

MESSSEITE (praexistiert, committet): die 14-Punkte-Union-<r>-Serie
(r_raw/r_unf je N) aus pt_zqz_family_raw.json (EXPERIMENT 053,
Kette 245f115; SHA-256-Eingangspin). Der Endpunkt
r_unf_union(N=65535) = 0.5141345707251959 liegt 0.0059 unter der
053er GUE-Band-Unterkante 0.52; naechstliegende Referenzkonstante
GOE 0.5307 (Abstand 0.0166). Das 053er L3-Verdict
H_ZQZ_L3_REFUSED_OUT_OF_BAND BLEIBT UNVERAENDERT (Einstufung statt
Re-Decide); dieses Prereg klassifiziert das committete Signal nur
NEU — gegen Referenzverteilungen der DREI Standardklassen bei
MATCHED Dimension d = pi(N).

REFERENZSEITE (ex ante gefroren VOR jeder MC-Berechnung):
  L0  Validierungs-Gate: β-Hermite-Tridiagonal-Sampler (Dumitriu-
      Edelman) gegen dense GOE/GUE-Sampler bei d=256 (2-Stichproben-
      Mean-Konsistenz, 4·SE-Regel auf <r>_unf) und Poisson-Kontrolle
      gegen die Literaturkonstante 0.3863 bei d=512 auf <r>_RAW
      (paarweise Gap-Ratios — unfolding-frei, daher definitions-
      identisch mit der Konstante); Scheitern -> alle Verdicts
      UNDETERMINED (kein Band aus einem unvalidierten Sampler).
  L1  Endpunkt-Band: r_unf_union(65535) innerhalb des GOE-Bands
      [mu_GOE(6542) - 2 sigma, mu_GOE(6542) + 2 sigma] (Realisierungs-
      Verteilung bei matched d, n_mc=1024, ddof=1).
  L2  Klassen-Dominanz: naechstliegende Klasse (z-Distanz
      |r_unf - mu|/sigma) je N ueber die 14-Punkte-Serie; GOE_DOMINANT
      iff GOE beide anderen Klassen an Stimmen uebertrifft
      (parameterfrei, Tie -> UNENTSCHIEDEN).
  L3  Residuen-Trend: Spearman rho(Δ_N, log N) mit Δ_N = r_unf(N) -
      mu_GOE(d(N)); |rho| < 0.5 -> OHNE_TREND, sonst TREND_AN.

ANTI-SHARPSHOOTER-AUDIT: alle Band-/Regel-Konstanten (z=2.0, k=4.0,
rho=0.5, seeds, n_mc, Fenster) sind im Prereg gefroren VOR der ersten
MC-Berechnung; die Referenzseite hatte bis zum Freeze keinerlei
Kontakt mit den Messwerten. Die Messseite praexistiert natuerlich
(committetes 053-Roh-Artefakt) — daher ist dies ein Einstufungs-/
Klassifikations-Experiment, kein praediktiver Ersttest.

Ketten-Muster (Haus-Stil all-in-one, wie pt_zqz_family):
  --freeze  Prereg canonical + SHA-256-Pin VOR jeder Rechnung
  --run     MC-Referenzen -> RAW JSON (KEINE Verdicts)
  --eval    Roh-Commit VOR Auswertung; decide() ex ante.

Hash-Politik 2026-10-05 (User-Direktive): NEUE Pins als SHA-256
(hex, 64 Zeichen) — hier durchgehend angewendet; Legacy-MD5-Pins
committeter Artefakte (053: 53c801d8...) bleiben unangetastet.
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

from pt_prime_state import sieve_primes
from pt_zqz_family import (
    N_SWEEP,
    UNFOLD_WINDOW,
    POISSON_R,
    GOE_R,
    GUE_R,
    spacing_stats,
    r_distinct_from_gaps,
    unfold_gaps,
)

# ---------- Artefakte ----------
PREREG_PATH = "pt_zqz_goe_prereg.json"
RAW_PATH = "pt_zqz_goe_raw.json"
RESULTS_PATH = "pt_zqz_goe_results.json"
SOURCE_RAW_PATH = "pt_zqz_family_raw.json"   # committete 053-Messseite

PREREG_SHA256 = "235bd79b5cf1c0de5738f29d9326da04a95914a660ebb7ea686f28b476120ea0"
# Gefroren 2026-10-05, VOR jeder MC-Berechnung (Freeze-Ausgabe
# PREREG_FROZEN oben); load_frozen erzwingt ihn am Lauf UND an der
# Auswertung (053-Lektion: expected an BEIDEN Call-Sites).

# ---------- gefrorenes Referenz-Design (ex ante) ----------
N_MC = 1024              # Realisierungen je (Klasse, d)
CHUNK = 128              # Batch-Groesse der Tridiagonal-Samples
BASE_SEED = 20261005     # Seed-Stamm; Zellformel siehe cell_seed()
SEED_STRIDE = 1000003    # Primzahl-Stride je Klasse
CLASS_CODE = {
    "goe_tridiag": 1,
    "gue_tridiag": 2,
    "poisson": 3,
    "goe_dense": 11,
    "gue_dense": 12,
}

# gefrorene Schwellen (KEINE Toleranz-Erhoehung)
Z_BAND_K = 2.0           # Band [mu - 2 sigma, mu + 2 sigma], zweiseitig
L0_K = 4.0               # Mean-Konsistenz in kombinierten SE-Einheiten
L3_RHO_MAX = 0.5         # |rho(Residuum, log N)| Schranke
L0_DIM = 256             # dense-vs-tridiagonal Validierungsdimension
L0_N = 512               # Realisierungen je Validierungsarm
POISSON_SANITY_DIM = 512
GAP_FLOOR = 0.0          # Luecken > 0 (identisch zu spacing_stats)

BAND_SIGMA_MIN = 1e-9    # sigma-Guard (leere Bandwaende -> UNDETERMINED)


def cell_seed(class_key, d):
    """Gefrorene Zellformel: BASE_SEED + Klasse*SEED_STRIDE + d."""
    return BASE_SEED + CLASS_CODE[class_key] * SEED_STRIDE + int(d)


# ---------- β-Hermite-Referenz-Sampler (Dumitriu–Edelman) ----------

def beta_hermite_eigs_chunk(d, beta, n_chunk, rng):
    """Eigenwerte von n_chunk β-Hermite-Tridiagonalmatrizen der
    Dimension d (Dumitriu-Edelman): a_i ~ N(0, 2/beta),
    b_j ~ chi(beta*(d-1-j)) / sqrt(beta)  (j = 0..d-2, 0-basiert).
    Skaleninvarianz der r-Statistik macht die Normierung wirkungslos;
    L0 validiert die Konstruktion empirisch gegen dense-Samples."""
    a = rng.standard_normal((n_chunk, d)) * math.sqrt(2.0 / beta)
    b = np.empty((n_chunk, d - 1))
    for j in range(d - 1):
        k = beta * (d - 1 - j)
        v = rng.standard_normal((n_chunk, k))
        b[:, j] = np.sqrt((v * v).sum(axis=1)) / math.sqrt(beta)
    out = np.empty((n_chunk, d))
    for i in range(n_chunk):
        out[i] = np.sort(
            eigh_tridiagonal(a[i], b[i], eigvals_only=True))
    return out


def dense_hermite_eigs_chunk(d, beta, n_chunk, rng):
    """Dense-Referenz (gleiche Klasse, gleiche Pipeline): GOE
    (G+G^T)/2 bzw. GUE (G+G^dagger)/2 mit G komplex-gaussisch."""
    out = np.empty((n_chunk, d))
    for i in range(n_chunk):
        if beta == 1:
            g = rng.standard_normal((d, d))
            h = (g + g.T) / 2.0
        else:
            g = (rng.standard_normal((d, d))
                 + 1j * rng.standard_normal((d, d))) / math.sqrt(2.0)
            h = (g + g.conj().T) / 2.0
        out[i] = np.sort(np.linalg.eigvalsh(h))
    return out


def poisson_eigs_chunk(d, n_chunk, rng):
    """Poisson-Null: iid-uniform sortierte Punkte auf [0, d] (Konvention
    wie pt_ququint_gue.poisson_control, aber durch dieselbe
    spacing_stats-Pipeline)."""
    pts = rng.uniform(0.0, float(d), size=(n_chunk, d))
    return np.sort(pts, axis=1)


def class_stats(d, class_key, n_mc):
    """Realisierungs-Verteilung von (<r>_raw, <r>_unf) bei matched d —
    durch DIESELBE Pipeline wie die Messseite (spacing_stats)."""
    rng = np.random.default_rng(cell_seed(class_key, d))
    rr = []
    ru = []
    for lo in range(0, n_mc, CHUNK):
        hi = min(lo + CHUNK, n_mc)
        if class_key == "goe_tridiag":
            eigs = beta_hermite_eigs_chunk(d, 1, hi - lo, rng)
        elif class_key == "gue_tridiag":
            eigs = beta_hermite_eigs_chunk(d, 2, hi - lo, rng)
        elif class_key == "goe_dense":
            eigs = dense_hermite_eigs_chunk(d, 1, hi - lo, rng)
        elif class_key == "gue_dense":
            eigs = dense_hermite_eigs_chunk(d, 2, hi - lo, rng)
        elif class_key == "poisson":
            eigs = poisson_eigs_chunk(d, hi - lo, rng)
        else:
            raise SystemExit(f"UNBEKANNTE KLASSE: {class_key}")
        for row in eigs:
            r_raw, r_unf, _ = spacing_stats(row)
            if r_raw is None:
                continue
            rr.append(r_raw)
            ru.append(r_unf if r_unf is not None else float("nan"))
    rr = np.asarray(rr, dtype=float)
    ru = np.asarray(ru, dtype=float)
    ru_finite = ru[np.isfinite(ru)]
    beta_map = {"goe_tridiag": 1, "gue_tridiag": 2}
    return {
        "class": class_key, "d": int(d), "n_mc": int(n_mc),
        "n_finite": int(ru_finite.size),
        "r_raw_mean": float(rr.mean()),
        "r_raw_std": float(rr.std(ddof=1)),
        "r_unf_mean": float(ru_finite.mean()),
        "r_unf_std": float(ru_finite.std(ddof=1)),
        "r_unf_q025": float(np.quantile(ru_finite, 0.025)),
        "r_unf_q500": float(np.quantile(ru_finite, 0.500)),
        "r_unf_q975": float(np.quantile(ru_finite, 0.975)),
        "beta": beta_map.get(class_key),
        "seed": cell_seed(class_key, d),
    }


# ---------- Prereg-Kette (SHA-256, Policy 2026-10-05) ----------

def current_branch():
    out = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def build_prereg_payload():
    """Canonical Prereg (ohne sha256-Feld). Messwerte werden NICHT
    kopiert: die Messseite ist nur ueber ihren Hash geankert."""
    return {
        "experiment": "EXPERIMENT 054",
        "hypothesis": "H-ZQZ-GOE-1..3",
        "title": ("GOE-fokussiertes Band fuer das Dritte-Observable-Gate "
                  "(Klassifikation des committeten Union-<r>-Signals "
                  "gegen Poisson/GOE/GUE bei matched d = pi(N), 0 QPU)"),
        "date_locked": "2026-10-05",
        "branch": current_branch(),
        "experiment_class": ("EINSTUFUNGS-/KLASSIFIKATIONS-Experiment: "
                             "Messseite praexistiert (committetes 053-Roh-"
                             "Artefakt); Referenzseite (MC-Baender) ex ante "
                             "gefroren vor erster Berechnung"),
        "methodology": {
            "device": ("G0 KLASSISCH (0 QPU, keine Statevector-"
                       "Neuberechnung; Eingang = committete 053-Artefakte)"),
            "elements": ("E6 Spektral-Proxy (Jacobi-Tridiagonal, wie 053); "
                         "Statistik-Kern pt_zqz_family.spacing_stats/"
                         "r_distinct_from_gaps/unfold_gaps IDENTISCH "
                         "importiert (Konventions-Share); Referenz-Sampler "
                         "β-Hermite-Tridiagonal nach Dumitriu-Edelman"),
            "sampler": {
                "goe_tridiag": ("a_i ~ N(0, 2/beta), b_j ~ chi(beta*(d-1-j))"
                                "/sqrt(beta), beta=1; eigh_tridiagonal"),
                "gue_tridiag": "denselbe Konstruktion, beta=2",
                "poisson": ("iid-uniform sortierte Punkte auf [0, d], "
                            "Konvention wie pt_ququint_gue.poisson_control"),
                "dense_goe": "(G+G^T)/2, G ~ N(0,1) iid, eigvalsh",
                "dense_gue": "(G+G^dagger)/2, G = (Re + i*Im)/sqrt(2), eigvalsh",
                "scale_note": ("<r> ist skaleninvariant; die exakte "
                               "Normalisierung ist wirkungslos; L0 "
                               "validiert die Konstruktion empirisch"),
            },
            "matched_dimension": "d = pi(N) je Gitterpunkt (sieve_primes); "
                                 "Gap-Anzahl je Realisierung = d - 1 == "
                                 "m_gaps der Messseite",
            "n_mc": N_MC,
            "chunk": CHUNK,
            "seed_rule": ("BASE_SEED + CLASS_CODE[class]*SEED_STRIDE + d; "
                          "np.random.default_rngPCG64-Stream; CHUNK=128 "
                          "gepinnt (Stream-Reihenfolge)"),
            "unfolding": f"lokal, Fenster ±{UNFOLD_WINDOW} benachbarte "
                         "Luecken (IDENTISCH zur Messseite via Import)",
        },
        "input_scope": {
            "universe": ("Union-<r>_raw/_unf-Serie ueber das 14-Punkte-"
                         "Gitter N = 7..65535 aus EXPERIMENT 053"),
            "source_path": SOURCE_RAW_PATH,
            "source_sha256": sha256_file(SOURCE_RAW_PATH),
            "mode": "closed",
            "n_max": 65535,
        },
        "grid": {"n_sweep": list(N_SWEEP),
                 "d_match_rule": "d = len(sieve_primes(N))"},
        "thresholds": {
            "z_band_k": Z_BAND_K,
            "l0_k": L0_K,
            "l3_rho_max": L3_RHO_MAX,
            "l0_dim": L0_DIM,
            "l0_n": L0_N,
            "poisson_sanity_dim": POISSON_SANITY_DIM,
            "band_sigma_min": BAND_SIGMA_MIN,
        },
        "constants": {"poisson_r": POISSON_R, "goe_r": GOE_R,
                      "gue_r": GUE_R,
                      "gue_ref": "Atas et al. 2013, arXiv:1212.5611"},
        "verdict_map": {
            "l0": ("GEHALTEN iff (a) tridiag-GOE vs dense-GOE bei d=256: "
                   "|mu_diff| <= 4*sqrt(s1^2/n1 + s2^2/n2) auf <r>_unf, "
                   "(b) tridiag-GUE vs dense-GUE analog, (c) Poisson bei "
                   "d=512 auf <r>_RAW (paarweise Gap-Ratios, "
                   "unfolding-frei — definitionsidentisch mit der "
                   "Konstante): |mu_P_raw - 0.3863| <= "
                   "4*sigma_P_raw/sqrt(n). "
                   "Gescheitert -> L1/L2/L3 = UNDETERMINED_L0."),
            "l1": ("GOE_BAND_GEHALTEN iff r_unf_union(N=65535) in "
                   "[mu_GOE(6542) - 2*sigma, mu_GOE(6542) + 2*sigma] "
                   "(Realisierungs-Verteilung bei matched d, ddof=1); "
                   "sonst GOE_BAND_VERFEHLT (Seite Unterskante/Oberskante "
                   "dokumentiert). Aendert KEIN 053er-Verdict."),
            "l2": ("Je N: naechstliegende Klasse nach z-Distanz "
                   "|r_unf - mu_Klasse(d)|/sigma_Klasse(d) unter "
                   "{Poisson, GOE, GUE}; exakte Tie (float) -> Punkt "
                   "TIE und unbesetzt. GOE_DOMINANT iff n_GOE > n_GUE "
                   "UND n_GOE > n_Poisson; UNENTSCHIEDEN iff GOE in den "
                   "Max-Teilmengen; sonst ANDERE_DOMINANT (Breakdown "
                   "publiziert)."),
            "l3": ("Δ_N = r_unf(N) - mu_GOE(d(N)) ueber die 14 Punkte; "
                   "|spearman(Δ_N, log N)| < 0.5 -> RESIDUEN_OHNE_TREND, "
                   "sonst RESIDUEN_TREND_AN (Rest-Struktur dokumentiert)."),
        },
        "verdict_ids": {
            "l0_held": "H_ZQZ_GOE_L0_VALIDIERUNG_GEHALTEN",
            "l0_failed": "H_ZQZ_GOE_L0_VALIDIERUNG_GESCHEITERT",
            "l1_goe": "H_ZQZ_GOE_L1_GOE_BAND_GEHALTEN",
            "l1_miss": "H_ZQZ_GOE_L1_GOE_BAND_VERFEHLT",
            "l2_goe": "H_ZQZ_GOE_L2_KLASSE_GOE_DOMINANT",
            "l2_other": "H_ZQZ_GOE_L2_KLASSE_ANDERE_DOMINANT",
            "l2_undecided": "H_ZQZ_GOE_L2_UNENTSCHIEDEN",
            "l3_flat": "H_ZQZ_GOE_L3_RESIDUEN_OHNE_TREND",
            "l3_trend": "H_ZQZ_GOE_L3_RESIDUEN_TREND_AN",
            "undetermined_l0": "H_ZQZ_GOE_UNDETERMINED_L0",
            "undetermined_small_m": "H_ZQZ_GOE_UNDETERMINED_SMALL_M",
        },
        "commit_rules": [
            "Prereg-Freeze (SHA-256) VOR jeder MC-Berechnung "
            "(REGISTERED_NOT_MEASURED)",
            "Roh-Commit VOR Auswertung (RAW enthaelt KEINE Verdicts)",
            "Auswertung mit decide() ex ante gegen die gefrorenen "
            "Schwellen; Freeze-Vergleich an Lauf UND Auswertung "
            "erzwungen (053-Lektion)",
            "KEINE Toleranz-Erhoehung; Einstufung statt stillem "
            "Re-Decide; 053er-Verdicts unangetastet",
        ],
        "sharpshooter_audit": ("Band-/Regelkonstanten (z=2.0, k=4.0, "
                               "rho=0.5), seeds, n_mc=1024 und die "
                               "Sampler-Formeln sind VOR der ersten "
                               "MC-Berechnung gefroren; keine Regel "
                               "beruehrt die committeten Messwerte "
                               "(z. B. 0.5141345707251959). Die Messseite "
                               "praexistiert — daher Einstufungs-"
                               "Experiment, kein praediktiver Ersttest."),
        "inherited_verdicts": {
            "exp_053_l1": "H_ZQZ_L1_HELD (unverändert)",
            "exp_053_l2": "H_ZQZ_L2_REDUNDANT_WITH_S_VN (unverändert)",
            "exp_053_l3": "H_ZQZ_L3_REFUSED_OUT_OF_BAND (unverändert)",
        },
        "numpy_build": np.__version__,
    }


def payload_sha256(payload):
    """Kanonischer Payload-Hash (SHA-256, Policy 2026-10-05)."""
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def load_frozen(path=PREREG_PATH, expected_sha256=None):
    """Freeze-Loader: SHA-256 KANONISCH ueber den geparsten Inhalt —
    erzwungen am Lauf UND an der Auswertung (053-Lektion)."""
    with open(path, "rb") as f:
        raw_bytes = f.read()
    dig = payload_sha256(json.loads(raw_bytes.decode("utf-8")))
    if expected_sha256 is not None and dig != expected_sha256:
        raise SystemExit(
            f"PREREG-MISMATCH: {path} sha256 {dig} != {expected_sha256} "
            "- Freeze gebrochen, Abbruch.")
    return json.loads(raw_bytes.decode("utf-8")), dig


def freeze_prereg(path=PREREG_PATH):
    """Freeze: schreibe Prereg und returniere den SHA-256 (einziger
    Ort, an dem PREREG_SHA256 gesetzt wird — danach manuell in die
    Konstante uebernehmen und committen)."""
    payload = build_prereg_payload()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, sort_keys=True, separators=(",", ":"),
                  ensure_ascii=False, indent=1)
    dig = payload_sha256(payload)
    print(f"PREREG_FROZEN sha256={dig}")
    return dig


# ---------- Messung (RAW: keine Verdicts) ----------

def run_measurement():
    import os
    if os.path.exists(RAW_PATH):
        raise SystemExit(
            f"RAW-EXISTIERT-BEREITS: {RAW_PATH} — kein stiller Re-Run "
            "(Raw-Commit-Disziplin). Loeschen ist ein expliziter Akt.")
    # GEFRORENES Prereg (Freeze-Vergleich am Lauf ERZWUNGEN)
    prereg, dig = load_frozen(expected_sha256=PREREG_SHA256)
    source_sha = sha256_file(SOURCE_RAW_PATH)
    if source_sha != prereg["input_scope"]["source_sha256"]:
        raise SystemExit(
            "SOURCE-MISMATCH: pt_zqz_family_raw.json sha256 "
            f"{source_sha} != Prereg-Pin "
            f"{prereg['input_scope']['source_sha256']} — Eingang geaendert.")

    dims = {int(N): len(sieve_primes(int(N))) for N in prereg["grid"]["n_sweep"]}
    rows = []
    for N in sorted(dims):
        d = dims[N]
        for key in ("goe_tridiag", "gue_tridiag", "poisson"):
            st = class_stats(d, key, N_MC)
            assert st["n_finite"] == N_MC, (
                f"MC-DEGENERAT N={N} d={d} {key}: n_finite={st['n_finite']}")
            rows.append(st)

    # --- L0-Validierungsarme (geliche Formeln, eigene Seede-Zellen) ---
    goe_tri = class_stats(L0_DIM, "goe_tridiag", L0_N)
    goe_den = class_stats(L0_DIM, "goe_dense", L0_N)
    gue_tri = class_stats(L0_DIM, "gue_tridiag", L0_N)
    gue_den = class_stats(L0_DIM, "gue_dense", L0_N)
    poi_sanity = class_stats(POISSON_SANITY_DIM, "poisson", N_MC)

    raw = {
        "prereg_sha256": dig,
        "numpy_build": np.__version__,
        "source": {"path": SOURCE_RAW_PATH,
                   "sha256": prereg["input_scope"]["source_sha256"]},
        "n_sweep": list(N_SWEEP),
        "d_match": {str(N): dims[N] for N in sorted(dims)},
        "mc_rows": rows,
        "validation": {
            "goe_tridiag_d256": goe_tri,
            "goe_dense_d256": goe_den,
            "gue_tridiag_d256": gue_tri,
            "gue_dense_d256": gue_den,
            "poisson_d512": poi_sanity,
        },
        "constants": {"poisson_r": POISSON_R, "goe_r": GOE_R,
                      "gue_r": GUE_R, "unfold_window": UNFOLD_WINDOW},
    }
    with open(RAW_PATH, "w", encoding="utf-8") as f:
        json.dump(raw, f, sort_keys=True, indent=1)
    print(f"RAW geschrieben: {RAW_PATH} (mc={len(rows)}, "
          f"validation=5)")
    return raw


# ---------- Auswertung (decide ex ante, Roh VOR Auswertung committed) ----------

def _two_sample_k(mu1, s1, n1, mu2, s2, n2, k):
    se = math.sqrt(s1 * s1 / n1 + s2 * s2 / n2)
    dev = abs(mu1 - mu2)
    return dev, k * se, dev <= k * se


def decide(raw, prereg, prereg_sha256):
    # Kette RAW -> Prereg (SHA-Gleichheit, Freeze-Kette intakt)
    assert raw["prereg_sha256"] == prereg_sha256, (
        f"RAW-PREREG-MISMATCH: {raw['prereg_sha256']} != {prereg_sha256}")
    th = prereg["thresholds"]
    vids = prereg["verdict_ids"]
    constants = raw["constants"]

    # Eingang erneut verifizieren (Auswertung liest committete Artefakte)
    src_sha = sha256_file(SOURCE_RAW_PATH)
    assert src_sha == raw["source"]["sha256"] == \
        prereg["input_scope"]["source_sha256"], "SOURCE-PIN-VERLETZUNG"
    with open(SOURCE_RAW_PATH) as f:
        src = json.load(f)
    union = src["union_rows"]
    by_N = {u["N"]: u for u in union}

    stats = {(r["class"], r["d"]): r for r in raw["mc_rows"]}
    d_match = raw["d_match"]

    def band_of(cls, d):
        st = stats[(cls, d)]
        sig = st["r_unf_std"]
        mu = st["r_unf_mean"]
        return st, (mu - th["z_band_k"] * sig,
                    mu + th["z_band_k"] * sig) if sig > th["band_sigma_min"] \
            else (None, None)

    # --- L0: Validierungs-Gate ---
    v = raw["validation"]
    dev_go, k_go, ok_go = _two_sample_k(
        v["goe_tridiag_d256"]["r_unf_mean"],
        v["goe_tridiag_d256"]["r_unf_std"], v["goe_tridiag_d256"]["n_finite"],
        v["goe_dense_d256"]["r_unf_mean"],
        v["goe_dense_d256"]["r_unf_std"], v["goe_dense_d256"]["n_finite"],
        th["l0_k"])
    dev_gu, k_gu, ok_gu = _two_sample_k(
        v["gue_tridiag_d256"]["r_unf_mean"],
        v["gue_tridiag_d256"]["r_unf_std"], v["gue_tridiag_d256"]["n_finite"],
        v["gue_dense_d256"]["r_unf_mean"],
        v["gue_dense_d256"]["r_unf_std"], v["gue_dense_d256"]["n_finite"],
        th["l0_k"])
    p_st = v["poisson_d512"]
    # Poisson-Anchor auf <r>_RAW: paarweise Gap-Ratios sind
    # unfolding-frei und definitionsidentisch mit 0.3863 (die lokale
    # Fenster-Mittel-Fluktuation wuerde <r>_unf systematisch veraendern).
    dev_p = abs(p_st["r_raw_mean"] - constants["poisson_r"])
    se_p = p_st["r_raw_std"] / math.sqrt(p_st["n_finite"])
    ok_p = dev_p <= th["l0_k"] * se_p
    l0_ok = bool(ok_go and ok_gu and ok_p)
    l0_verdict = (vids["l0_held"] if l0_ok else vids["l0_failed"])

    # --- Series-Aufbereitung (z-Distanzen je Klasse) ---
    series = []
    z_ok = True
    for u in union:
        N = u["N"]
        d = d_match[str(N)]
        assert u["pi_N"] == d, f"D-MATCH-VERLETZUNG N={N}: {u['pi_N']} != {d}"
        r_unf = u["r_unf"]
        zrow = {"N": N, "d": d, "r_unf": r_unf, "r_raw": u["r_raw"],
                "m_gaps": u["m_gaps"], "pi_N": u["pi_N"]}
        if r_unf is None:
            z_ok = False
            zrow["nearest"] = None
            series.append(zrow)
            continue
        g_st, g_band = band_of("goe_tridiag", d)
        q_st, _ = band_of("gue_tridiag", d)
        p_st2, _ = band_of("poisson", d)
        if any(s["r_unf_std"] <= th["band_sigma_min"]
               for s in (g_st, q_st, p_st2)):
            z_ok = False
            zrow["nearest"] = None
            series.append(zrow)
            continue
        z_goe = (r_unf - g_st["r_unf_mean"]) / g_st["r_unf_std"]
        z_gue = (r_unf - q_st["r_unf_mean"]) / q_st["r_unf_std"]
        z_poi = (r_unf - p_st2["r_unf_mean"]) / p_st2["r_unf_std"]
        zrow.update({
            "z_goe": float(z_goe), "z_gue": float(z_gue),
            "z_poisson": float(z_poi),
            "mu_goe": g_st["r_unf_mean"], "sig_goe": g_st["r_unf_std"],
            "mu_gue": q_st["r_unf_mean"], "sig_gue": q_st["r_unf_std"],
            "mu_poisson": p_st2["r_unf_mean"],
            "sig_poisson": p_st2["r_unf_std"],
            "goe_band": [float(g_band[0]), float(g_band[1])],
            "in_goe_band": bool(g_band[0] <= r_unf <= g_band[1]),
        })
        zmin = min(abs(zrow["z_goe"]), abs(zrow["z_gue"]),
                   abs(zrow["z_poisson"]))
        if zmin == abs(zrow["z_goe"]):
            zrow["nearest"] = "GOE"
        elif zmin == abs(zrow["z_gue"]):
            zrow["nearest"] = "GUE"
        elif zmin == abs(zrow["z_poisson"]):
            zrow["nearest"] = "Poisson"
        # exakte Mehrfach-Tie -> TIE (unbesetzt)
        zvals = [abs(zrow["z_goe"]), abs(zrow["z_gue"]),
                 abs(zrow["z_poisson"])]
        if zvals.count(zmin) > 1:
            zrow["nearest"] = "TIE"
        series.append(zrow)

    # --- L1: Endpunkt-Band ---
    last = by_N[prereg["grid"]["n_sweep"][-1]]
    l1_row = next(r for r in series if r["N"] == last["N"])
    if not z_ok:
        l1_verdict = (vids["undetermined_l0"] if not l0_ok
                      else vids["undetermined_small_m"])
    elif l1_row["in_goe_band"]:
        l1_verdict = vids["l1_goe"]
    else:
        l1_verdict = vids["l1_miss"]

    # --- L2: Klassen-Dominanz (parameterfrei) ---
    counted = [r for r in series
               if r["nearest"] in ("GOE", "GUE", "Poisson")]
    n_goe = sum(1 for r in counted if r["nearest"] == "GOE")
    n_gue = sum(1 for r in counted if r["nearest"] == "GUE")
    n_poi = sum(1 for r in counted if r["nearest"] == "Poisson")
    n_tie = len(series) - len(counted)
    tops = max(n_goe, n_gue, n_poi)
    winners = {name for name, cnt in
               (("GOE", n_goe), ("GUE", n_gue), ("Poisson", n_poi))
               if cnt == tops}
    if not z_ok:
        l2_verdict = vids["undetermined_l0"] if not l0_ok \
            else vids["undetermined_small_m"]
    elif winners == {"GOE"}:
        l2_verdict = vids["l2_goe"]
    elif "GOE" in winners:
        l2_verdict = vids["l2_undecided"]
    else:
        l2_verdict = vids["l2_other"]

    # --- L3: Residuen-Trend ---
    deltas = []
    xs_used = []
    for r in series:
        if r["nearest"] is None or r["mu_goe"] is None:
            continue
        deltas.append(r["r_unf"] - r["mu_goe"])
        xs_used.append(math.log(r["N"]))
    if len(deltas) < 3:
        l3_verdict = vids["undetermined_small_m"]
        rho_val = None
        rho_degen = False
    else:
        rho_t, _ = spearmanr(deltas, xs_used)
        rho_t = float(rho_t)
        rho_degen = not math.isfinite(rho_t)
        # Gefrorene Regel buchstabengetreu: |rho| < 0.5 -> OHNE_TREND,
        # sonst TREND_AN. NaN (konstante Deltas) faellt in den sonst-
        # Zweig und wird als degenerat dokumentiert.
        l3_flat = abs(rho_t) < th["l3_rho_max"]
        l3_verdict = vids["l3_flat"] if l3_flat else vids["l3_trend"]
        rho_val = None if rho_degen else rho_t

    results = {
        "prereg_sha256": raw["prereg_sha256"],
        "prereg_path": PREREG_PATH,
        "raw_path": RAW_PATH,
        "source_path": SOURCE_RAW_PATH,
        "source_sha256": raw["source"]["sha256"],
        "input": {u["N"]: {"r_unf": u["r_unf"], "r_raw": u["r_raw"],
                           "m_gaps": u["m_gaps"], "pi_N": u["pi_N"]}
                  for u in union},
        "validation": {
            "goe_tridiag_vs_dense_d256": {
                "mu_tridiag": v["goe_tridiag_d256"]["r_unf_mean"],
                "mu_dense": v["goe_dense_d256"]["r_unf_mean"],
                "dev": float(dev_go), "k_max": float(k_go),
                "passed": bool(ok_go)},
            "gue_tridiag_vs_dense_d256": {
                "mu_tridiag": v["gue_tridiag_d256"]["r_unf_mean"],
                "mu_dense": v["gue_dense_d256"]["r_unf_mean"],
                "dev": float(dev_gu), "k_max": float(k_gu),
                "passed": bool(ok_gu)},
            "poisson_anchor_d512": {
                "statistic": "r_raw (unfolding-frei)",
                "mu_poisson": v["poisson_d512"]["r_raw_mean"],
                "anchor": constants["poisson_r"],
                "dev": float(dev_p), "k_max": float(th["l0_k"] * se_p),
                "passed": bool(ok_p)},
            "verdict": l0_verdict,
        },
        "series_table": series,
        "class_counts": {"n_goe": n_goe, "n_gue": n_gue,
                         "n_poisson": n_poi, "n_tie": n_tie,
                         "n_points": len(series)},
        "l1": {
            "N": last["N"], "d": d_match[str(last["N"])],
            "r_unf": last["r_unf"], "r_raw": last["r_raw"],
            "band_goe": [float(b) for b in l1_row["goe_band"]]
            if "goe_band" in l1_row else None,
            "z_goe": l1_row.get("z_goe"),
            "goe_r_const": constants["goe_r"],
            "gue_r_const": constants["gue_r"],
            "verdict": l1_verdict,
        },
        "l2": {
            "counts": results_counts(n_goe, n_gue, n_poi, n_tie),
            "winners": sorted(winners),
            "verdict": l2_verdict,
        },
        "l3": {
            "rho_residual_logN": rho_val,
            "rho_max": th["l3_rho_max"],
            "rho_degenerate_constant_deltas": rho_degen,
            "n_residual_points": len(deltas),
            "verdict": l3_verdict,
        },
        "inherited_verdicts": prereg["inherited_verdicts"],
        "verdicts": {"l0": l0_verdict, "l1": l1_verdict,
                     "l2": l2_verdict, "l3": l3_verdict},
    }
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, sort_keys=True, indent=1)
    print("VERDICTS:", results["verdicts"])
    return results


def results_counts(n_goe, n_gue, n_poi, n_tie):
    return {"GOE": n_goe, "GUE": n_gue, "Poisson": n_poi, "TIE": n_tie}


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
        prereg, dig = load_frozen(expected_sha256=PREREG_SHA256)
        with open(RAW_PATH) as f:
            raw = json.load(f)
        decided = decide(raw, prereg, dig)
        print(json.dumps(decided["verdicts"], indent=1))


if __name__ == "__main__":
    main()