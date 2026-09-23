"""EXPERIMENT 032 - Ququint V4 (H-STAR-4): Margin(p1)-Crossover.

Frage (Plan §Z.15, Y.4-QUQUINT_FIDELITY_ADVANTAGE als falsifizierbare
Schwelle §Z.15.3): Existiert eine kritische Gate-Degradation kappa*, ab
der die NATIVE-Ququint-Architektur (2 echte Ququints, d=5) einen hoeheren
Witness-Margin liefert als die ENCODIERTE Architektur (6 Qubits, 3-Qubit-
Emulation, 81 2q) — am IDENTISCHEN logischen Task?

Anti-Sharpshooter: das Prereg (kappa-Gitter, Baender, Seeds, Schwellen,
Architektur-Instantiierung) wird VOR der Kurven-Berechnung gefroren (md5,
Commit vor dem Lauf). Simulator only, 0 QPU (QPU-Anker nur nach neuem
Freeze, §Z.13.5-Muster).

Identischer logischer Task (beide Architekturen, Voll-Task):
  Bereite |phi> = (1/sqrt(5)) sum_k |k,k> aus dem Reset-Zustand her und
  messe den DFT-Diagonalgewichts-Witness V = sum_a p~(a,a) mit
  margin = v_hat - 4*SE - 1/5 (Phase-2/3-Konvention: n_shots 8192,
  parametrischer Bootstrap 1000, Seeds fest).
  SCHWACHE ANNAHME (registriert, Plan-Pflicht): "margin >= 0" ist ein
  NOTWENDIGER, aber nicht hinreichender Proxy fuer logische Korrektheit.
  Der Crossover betrifft den Margin als Reporting-Groesse, nicht die
  logische Fehlerrate selbst.

Architektur A (encodiert, "Qubit-Baseline" = die Fez-Realitaet §Z.13/§Z.14):
  6 Qubits, volles phi_D-Circuit (Praeparation + DFT-Rotation; ISA-Budget
  81 2q vs Prereg-Soll 45), STRESS-Noise-Modell wie Phase 2 (Depolarizing
  p1 auf 1q, ratio*p1 auf cx mit ratio 10, Readout ro = 1e-2, nicht
  kalibriert). AerSimulator density_matrix, 12-Circuit-Batch (run_witness),
  margin aus witness_from_counts — exakt die Phase-2/3-Engine.

Architektur B (native-qudit F5-Baseline, 25-dim, pure numpy):
  2 echte Ququints. 4 native Gates (Voll-Task, beide Seiten zahlen Praep):
    1. F5 auf A   (Praep 1: |0> -> uniform, 1-Qudit, eps = kappa*p1)
    2. SUM-Gate   (2-Qudit,  eps = kappa*ratio*p1 — NEUTRAL: dieselbe
       2q-Ratio-Struktur wie Architektur A, keine native Schonung)
    3. F5 auf A   (Witness-Rotation, 1-Qudit)
    4. F5+ auf B  (Witness-Rotation, 1-Qudit)
  Depolarizing pro Gate: rho -> (1-eps)*U rho U+ + eps*I_25/25.
  Readout: 5-Level-Konfusion pro Qudit (1-ro richtig, ro/4 uniform auf
  die 4 falschen Level) — Readout-RATE ro identisch zu Architektur A.
  Die Plan-Formulierung "2 Gates x kappa-Degradation" = die 2 nativen
  Witness-Rotations-Gates; der Voll-Task addiert die 2 Praep-Gates.
  SUM-Gate: Permutation (k,0) <-> (k,k) (unitarisch); im Protokoll wirkt
  nur (k,0) -> |k,k> auf der uniformen Superposition.

Kritische Ratio (registrierte Definition):
  kappa* = kappa mit margin_native(kappa, p1) = margin_encoded(p1) am
  Fez-typischen STRESS-Punkt p1 = 3e-4. Bisektion auf log-kappa im
  registrierten Gitter, rel. Genauigkeit 1%. kappa* ist die Degradation,
  die native Gates maximal haben duerfen, damit die native Architektur
  den encodierten Margin noch schlaegt.

Rough-Modell VOR der Messung (registrierte Vorhersage, falsifikator-first):
  Encodiertes 2q-Fehlergewicht 81*ratio*p1 = 810*p1; nativ
  (3*1 + 1*10)*kappa*p1 = 13*kappa*p1 -> kappa*_rough ≈ 810/13 ≈ 62
  (SE-, Readout- und Depolarizing-Boden vernachlaessigt; der kleine
  Hilbert-Raum gibt der nativen Seite zusaetzlichen Boden-Vorteil:
  V-Boden nativ 5/25 = 0.2 vs encodiert 5/64 ≈ 0.078).
  Vorhersage-Band kappa* in [10, 500]; Falsifikator-Erwartung
  t_kappa_star_ge_10 = True.

Verdict-Baender (Prereg, VOR der Berechnung):
  kappa* < 1       -> H-STAR-4_REFUTED_KEIN_CROSSOVER
                      (native Gates muessten BESSER als Qubit-Gates sein,
                      um nur gleichzuziehen — Y.4-Advantage im Simulator-
                      Spiegel tot)
  1 <= kappa* < 10 -> H-STAR-4_SCHWACH_CROSSOVER
  kappa* >= 10     -> H-STAR-4_CONFIRMED_CROSSOVER
                      (ueberlebt die standard Qudit-Gate-Degradations-Bind)
  kein Crossover im Gitter -> H-STAR-4_INKONKLUSIV

Kontroll-Gates (VOR dem Verdict, sonst EVALUATION_INVALID):
  T1 Task-Identitaet nativ:  bei Null-Noise (kappa=0, p1=0, ro=0) ist
      v_exact = 1.0 exakt ((F (x) F+)|phi> = |phi>, Phase-1-Pin).
  T2 Task-Identitaet encodiert: Aer phi_D bei p1=0, ro=0 liefert
      |v_hat - 1| <= 0.02 (8192 Shots, 2 sigma).
  M  Monotonie: margin_native ist monoton fallend in kappa (analytisches
      V ueber das Gitter strikt fallend).
"""

import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pt_ququint_ibmq import D5, WITNESS_BOUND
from pt_ququint_ibmq_aer import (
    NOISE_GRID_DEFAULT,
    dft_rotation_circuit,
    error_budget,
    phi_prep_circuit,
    run_witness,
    transpiled_counts,
)

PREREG_PATH = "pt_crossover_prereg_v4.json"
RESULTS_PATH = "pt_crossover_v4_results.json"
EXPERIMENT = "032-ququint-v4-margin-crossover"
DECISION_RULE = ("kappa_star >= 10 -> CONFIRMED; kappa_star < 1 -> REFUTED; "
                 "sonst SCHWACH; kein Crossover -> INKONKLUSIV "
                 "(nach Kontroll-Gates T1/T2/M)")

P1_PRIMARY = 3e-4          # Fez-naher STRESS-Punkt (Phase-2 prereg_draft)
RO_DEFAULT = 1e-2          # Readout-Rate, GLEICH auf beiden Seiten
RATIO_DEFAULT = 10.0       # 2q/1q-Fehlerratio, §Z.13-Konvention
N_SHOTS = 8192
N_BOOT = 1000
SEED_AER = 42              # Phase-2-Konvention (seed_simulator)
SEED_SHOTS_NATIVE = 20260924
SEED_BOOT_NATIVE = 9871    # Phase-2-Konvention (witness_from_counts)

KAPPA_GRID = (0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0,
              100.0, 200.0, 400.0, 800.0)
KAPPA_REFUTED_MAX = 1.0
KAPPA_CONFIRMED_MIN = 10.0
KAPPA_TOL_REL = 0.01       # Bisektions-Genauigkeit (relativ)
KAPPA_MAX_ITER = 60

KAPPA_SWEEP_CURVES = (1.0, 10.0, 100.0)   # deskriptiv: native margin(p1)

CONTROL_IDENTITY_TOL = 0.02  # T2 (8192 Shots ~ 2 sigma)
PHI_D_CX_SOLL = 45           # Prereg-Soll §Z.14 (Beobachtung: 81, ISA)


# === Native-Qudit-Primitiven (25-dim, pure numpy) ===

def f5_matrix():
    """DFT-5: F[j,k] = omega^{jk}/sqrt(5)."""
    w = np.exp(2j * np.pi / D5)
    j = np.arange(D5)
    return w ** np.outer(j, j) / np.sqrt(D5)


def phi_ququint():
    """|phi> = (1/sqrt(5)) sum_k |k,k>, 25-dim (Index k*5 + l)."""
    psi = np.zeros(D5 * D5, dtype=complex)
    for k in range(D5):
        psi[k * D5 + k] = 1.0
    return psi / np.sqrt(D5)


def sum_gate():
    """Native 2-Qudit-SUM-Gate als Permutation (k,0) <-> (k,k), 25x25.

    Unitarisch (Produkt von 4 Transpositionen + Fixpunkt k=0); im
    Protokoll wirkt nur der Zweig (k,0) -> (k,k) auf der uniformen
    (k,0)-Superposition. Das ist das Qudit-Analogon des COPY/CNOT-Gates —
    EIN natives 2-Qudit-Gate statt 1+ CX-Kette (Y.4-Claim-Klasse).
    """
    perm = np.arange(D5 * D5)
    for k in range(D5):
        a, b = k * D5 + 0, k * D5 + k
        perm[a], perm[b] = perm[b], perm[a]
    return np.eye(D5 * D5, dtype=complex)[:, perm]


def depolarize(rho, eps):
    """Qudit-Depolarizing: rho -> (1-eps)*rho + eps*I/dim (dim = 25)."""
    if eps == 0.0:
        return rho
    dim = rho.shape[0]
    return (1.0 - eps) * rho + eps * np.eye(dim, dtype=complex) / dim


def readout_confusion_25(ro):
    """5-Level-Readout-Konfusion pro Qudit, gekroent (25x25).

    P(gemessen = richtig) = 1-ro, Fehler uniform auf die 4 falschen Level.
    Die Readout-RATE ro ist identisch zur encodierten Seite (ro pro Qubit;
    die encodierte Seite hat 6 Qubits, nativ 2 Qudits — dieser strukturelle
    Unterschied ist Teil des Vergleichs, nicht eine Modellwahl).
    """
    c = np.full((D5, D5), ro / (D5 - 1))
    np.fill_diagonal(c, 1.0 - ro)
    return np.kron(c, c)


def native_gate_plan(kappa, p1, ratio=RATIO_DEFAULT):
    """Die 4 nativen Gates: (name, arity, eps). 1-Qudit: kappa*p1,
    2-Qudit: kappa*ratio*p1 — neutral, dieselbe Ratio-Struktur wie A."""
    return [
        ("F5_A_prep", 1, kappa * p1),
        ("SUM_2q", 2, kappa * ratio * p1),
        ("F5_A_rot", 1, kappa * p1),
        ("F5dag_B_rot", 1, kappa * p1),
    ]


def native_protocol(kappa, p1, ro=RO_DEFAULT, ratio=RATIO_DEFAULT):
    """Volle native Kette: 4 Gates mit Depolarizing, dann Readout-Konfusion.

    Liefert probs (25-dim Wahrscheinlichkeiten, Analogon des Aer-Histogramms
    vor dem Shot-Sampling), v_exact (Witness der exakten probs) und den
    Gate-Plan.
    """
    F = f5_matrix()
    f_a = np.kron(F, np.eye(D5))
    f_dag_b = np.kron(np.eye(D5), F.conj().T)
    s = sum_gate()

    psi0 = np.zeros(D5 * D5, dtype=complex)
    psi0[0] = 1.0
    rho = np.outer(psi0, psi0)
    plan = native_gate_plan(kappa, p1, ratio)
    gates = {"F5_A_prep": f_a, "SUM_2q": s,
             "F5_A_rot": f_a, "F5dag_B_rot": f_dag_b}
    for name, _arity, eps in plan:
        rho = gates[name] @ rho @ gates[name].conj().T
        rho = depolarize(rho, eps)

    probs = np.real(np.diag(rho)).copy()
    probs = np.clip(probs, 0.0, None)
    probs /= probs.sum()
    confused = readout_confusion_25(ro) @ probs

    return {"probs": probs, "probs_readout": confused,
            "v_exact": float(_diag_weight(probs, D5, D5)),
            "v_exact_readout": float(_diag_weight(confused, D5, D5)),
            "gate_plan": plan}


def _diag_weight(probs, d, diag_size):
    """V = Summe der ersten diag_size Diagonal-Eintraege von probs (d x d).

    Fuer d=8, diag_size=5 identisch zu dft_diagonal_weight (Phase-1);
    fuer d=5 (nativ) dieselbe Arithmetik auf dem 5x5-Quadrat.
    """
    mat = np.asarray(probs, dtype=float).reshape(d, d)
    return float(np.einsum("ii->i", mat[:diag_size, :diag_size]).sum())


# === Margin-Schaetzer (identische Struktur wie witness_from_counts) ===

def native_witness_from_probs(probs, n_shots=N_SHOTS, n_boot=N_BOOT,
                              seed_shots=SEED_SHOTS_NATIVE,
                              seed_boot=SEED_BOOT_NATIVE):
    """Shot-Sampling (Analogon Aer) + parametrischer Bootstrap um das
    beobachtete Histogramm — dieselbe Pipeline wie witness_from_counts,
    nur auf 25 Bins (d=5 statt 8) und V ueber die 5 Diagonal-Bins.
    margin = v_hat - 4*SE - WITNESS_BOUND."""
    probs = np.asarray(probs, dtype=float)
    probs = probs / probs.sum()
    rng = np.random.default_rng(seed_shots)
    counts = rng.multinomial(int(n_shots), probs)
    p_hat = counts / float(n_shots)
    v_hat = _diag_weight(p_hat, D5, D5)
    rng_boot = np.random.default_rng(seed_boot)
    boot = rng_boot.multinomial(int(n_shots), p_hat, size=int(n_boot)) \
        / float(n_shots)
    boot = boot.reshape(int(n_boot), D5, D5)
    v_boot = np.einsum("nii->n", boot)
    se = float(np.std(v_boot, ddof=1))
    return {
        "v_exact": float(_diag_weight(probs, D5, D5)),
        "v_hat": float(v_hat),
        "se": se,
        "bound": float(WITNESS_BOUND),
        "margin": float(v_hat - 4.0 * se - WITNESS_BOUND),
        "n_shots": int(n_shots),
        "n_boot": int(n_boot),
    }


def native_margin(kappa, p1, ro=RO_DEFAULT, ratio=RATIO_DEFAULT,
                  n_shots=N_SHOTS, n_boot=N_BOOT):
    """margin_native(kappa, p1) — Voll-Task mit Readout."""
    proto = native_protocol(kappa, p1, ro=ro, ratio=ratio)
    out = native_witness_from_probs(proto["probs_readout"],
                                    n_shots=n_shots, n_boot=n_boot)
    out["kappa"] = float(kappa)
    out["p1"] = float(p1)
    out["gate_plan"] = [(n, a, e) for n, a, e in proto["gate_plan"]]
    return out


def find_kappa_star(margin_enc, p1, kappa_grid=KAPPA_GRID, ro=RO_DEFAULT,
                    ratio=RATIO_DEFAULT, n_shots=N_SHOTS, n_boot=N_BOOT,
                    tol_rel=KAPPA_TOL_REL, max_iter=KAPPA_MAX_ITER):
    """kappa*: margin_native(kappa, p1) = margin_enc (Bisektion auf log2).

    Bracket-Suche im registrierten Gitter; kein Vorzeichenwechsel im
    Gitter -> None (kein Crossover im Gitter).
    """
    def delta(kappa):
        return native_margin(kappa, p1, ro=ro, ratio=ratio,
                             n_shots=n_shots, n_boot=n_boot)["margin"] - margin_enc

    dvals = [delta(k) for k in kappa_grid]
    bracket = None
    for i in range(len(kappa_grid) - 1):
        if dvals[i] > 0.0 >= dvals[i + 1]:
            bracket = (float(kappa_grid[i]), float(kappa_grid[i + 1]))
            break
    if bracket is None:
        return None
    lo, hi = bracket
    d_lo = delta(lo)
    for _ in range(int(max_iter)):
        mid = (lo * hi) ** 0.5  # geometrische Mitte (log-kappa)
        if hi / lo - 1.0 <= tol_rel:
            break
        d_mid = delta(mid)
        if d_mid > 0.0:
            lo, d_lo = mid, d_mid
        else:
            hi = mid
    return {"kappa_star": float((lo * hi) ** 0.5), "bracket": [lo, hi],
            "p1": float(p1), "margin_enc": float(margin_enc),
            "delta_at_bracket": [float(d_lo), float(delta(hi))],
            "grid_deltas": [float(d) for d in dvals]}


# === Verdict ===

def verdict(kappa_star):
    """Verdict nach den registrierten Baendern (None -> kein Crossover)."""
    if kappa_star is None:
        return "H-STAR-4_INKONKLUSIV"
    if kappa_star < KAPPA_REFUTED_MAX:
        return "H-STAR-4_REFUTED_KEIN_CROSSOVER"
    if kappa_star < KAPPA_CONFIRMED_MIN:
        return "H-STAR-4_SCHWACH_CROSSOVER"
    return "H-STAR-4_CONFIRMED_CROSSOVER"


# === Prereg ===

def build_prereg_payload():
    """Deterministischer Prereg-Payload (KEIN Timestamp im gehashten Inhalt)."""
    return {
        "experiment": EXPERIMENT,
        "registered_before": (
            "Vorwissen: die Phase-2-Aer-Kurve (§Z.13) liefert den encodierten "
            "phi-Margin am Fez-Punkt p1=3e-4 (v_hat ca. 0.62-0.66) — die "
            "ENCODIERTE Seite ist Prior, nicht Resultat dieses Experiments. "
            "Die NATIVE margin-Kurve und kappa* wurden vor diesem Freeze "
            "NICHT berechnet. Rough-Modell (nur Fehlergewichte): encodiert "
            "81*ratio*p1 = 810*p1, nativ (3*1+1*10)*kappa*p1 = 13*kappa*p1 "
            "-> kappa*_rough ≈ 62; Vorhersage-Band [10, 500]."
        ),
        "hypothesis": (
            "H-STAR-4: Es existiert p* bzw. kappa*, ab dem der Ququint-"
            "Witness-Margin den Qubit-Baseline-Margin schlaegt (Threshold-"
            "Crossover, Y.4 QUQUINT_FIDELITY_ADVANTAGE als falsifizierbare "
            "Schwelle)."
        ),
        "weak_assumption": (
            "SCHWACH (Plan-Pflicht): margin >= 0 ist ein notwendiger, nicht "
            "hinreichender Proxy fuer logische Korrektheit. Der Crossover "
            "betrifft den Margin als Reporting-Groesse, nicht die logische "
            "Fehlerrate selbst."
        ),
        "steelman": (
            "Kein Crossover: die native Margin-Kurve faellt so schnell wie "
            "die encodierte (margin_ququint ≡ margin_qubit) — kappa* < 1, "
            "native Gates muessten besser als Qubit-Gates sein, um "
            "gleichzuziehen."
        ),
        "decision_rule": DECISION_RULE,
        "architectures": {
            "A_encoded": (
                "6 Qubits, volles phi_D-Circuit (Praep + DFT-Rotation), "
                "STRESS-Noise wie Phase 2: Depolarizing p1 (1q) / ratio*p1 "
                "(cx, ratio 10), Readout ro=1e-2; AerSimulator "
                "density_matrix, 12-Circuit-Batch, witness_from_counts. "
                "ISA-Budget phi_D 81 2q (Beobachtung §Z.14) vs Prereg-Soll "
                "45; der V4-Lauf re-transpiliert deterministisch und "
                "BERICHTET den Count."
            ),
            "B_native": (
                "2 Ququints (d=5), 25-dim numpy density matrix; 4 native "
                "Gates: F5_A (Praep, kappa*p1), SUM (2-Qudit, "
                "kappa*ratio*p1 — dieselbe Ratio wie A), F5_A (Rotation), "
                "F5+_B (Rotation); Readout 5-Level-Konfusion pro Qudit mit "
                "Rate ro (GLEICH zu A). Depolarizing pro Gate "
                "(1-eps)*U rho U+ + eps*I_25/25."
            ),
            "plan_formulation_note": (
                "'2 Gates x kappa-Degradation' (Plan) = die 2 nativen "
                "Witness-Rotations-Gates; der registrierte Voll-Task addiert "
                "2 Praep-Gates auf BEIDEN Seiten (keine Seite bekommt "
                "noiseless Input — Anti-Sharpshooter)."
            ),
            "fairness": [
                "Readout-Rate ro identisch (1e-2 pro Qubit/Qudit-Level).",
                "2-Qudit-Gate erhaelt dieselbe Ratio-Penalty (10) wie die "
                "encodierte Seite — KEINE native Schonung.",
                "Praeparation auf beiden Seiten im Budget (Voll-Task).",
                "Depolarizing-Ziel I/d: nativ I_25/25 (V-Boden 0.2), "
                "encodiert I_64/64 (V-Boden 5/64) — struktureller Vorteil "
                "des kleineren Hilbert-Raums, Teil des Vergleichs.",
            ],
        },
        "kappa_star_definition": (
            "kappa* mit margin_native(kappa, p1=3e-4) = margin_encoded(p1=3e-4); "
            "Bisektion auf log-kappa, rel. Genauigkeit 1%, Bracket-Suche im "
            "registrierten Gitter; kein Bracket -> INKONKLUSIV."
        ),
        "predictions": {"t_kappa_star_ge_10": True},
        "thresholds": {
            "kappa_refuted_max": KAPPA_REFUTED_MAX,
            "kappa_confirmed_min": KAPPA_CONFIRMED_MIN,
            "kappa_tol_rel": KAPPA_TOL_REL,
            "prediction_band": [10.0, 500.0],
            "control_identity_tol": CONTROL_IDENTITY_TOL,
            "p1_primary": P1_PRIMARY,
            "ro": RO_DEFAULT,
            "ratio": RATIO_DEFAULT,
            "n_shots": N_SHOTS,
            "n_boot": N_BOOT,
            "phi_d_cx_soll": PHI_D_CX_SOLL,
        },
        "grids": {
            "kappa_grid": list(KAPPA_GRID),
            "p1_grid_descriptive": list(NOISE_GRID_DEFAULT),
            "kappa_sweep_curves_descriptive": list(KAPPA_SWEEP_CURVES),
        },
        "seeds": {
            "seed_aer": SEED_AER,
            "seed_shots_native": SEED_SHOTS_NATIVE,
            "seed_boot_native": SEED_BOOT_NATIVE,
        },
        "controls": {
            "T1_native_identity": (
                "kappa=0, p1=0, ro=0 -> v_exact = 1.0 (Tol 1e-9) — "
                "(F (x) F+)|phi> = |phi> (Phase-1-Pin)"),
            "T2_encoded_identity": (
                "Aer phi_D bei p1=0, ro=0 -> |v_hat - 1| <= 0.02 (2 sigma, "
                "8192 Shots)"),
            "M_monotonicity": (
                "Analytisches V(kappa) ueber das Gitter strikt fallend"),
            "gate": "Kontrollfehler -> EVALUATION_INVALID",
        },
        "verdict_map": {
            "H-STAR-4_REFUTED_KEIN_CROSSOVER": "kappa* < 1",
            "H-STAR-4_SCHWACH_CROSSOVER": "1 <= kappa* < 10",
            "H-STAR-4_CONFIRMED_CROSSOVER": "kappa* >= 10",
            "H-STAR-4_INKONKLUSIV": "kein Crossover im Gitter",
        },
        "qpu": "0 QPU (Simulator only); QPU-Anker nur nach neuem Freeze "
               "(§Z.13.5-Muster).",
    }


def canonical_payload_json(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def payload_md5(payload):
    return hashlib.md5(canonical_payload_json(payload).encode("utf-8")).hexdigest()


def freeze_prereg(payload=None):
    if payload is None:
        payload = build_prereg_payload()
    doc = dict(payload)
    doc["md5"] = payload_md5(payload)
    return doc


def verify_prereg_md5(doc):
    stripped = {k: v for k, v in doc.items() if k != "md5"}
    return payload_md5(stripped) == doc["md5"]


def load_frozen_prereg(path=PREREG_PATH):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if not verify_prereg_md5(doc):
        raise ValueError(f"Prereg-md5-MISMATCH in {path}")
    return doc


# === Evaluation ===

def _kappa_star_report(result):
    if result is None:
        return {"kappa_star": None, "note": "kein Crossover im Gitter"}
    return result


def run_v4(n_shots=N_SHOTS, kappa_grid=KAPPA_GRID,
           p1_grid=NOISE_GRID_DEFAULT, kappa_sweep=KAPPA_SWEEP_CURVES,
           control_identity_tol=CONTROL_IDENTITY_TOL, ro=RO_DEFAULT,
           ratio=RATIO_DEFAULT):
    """Volle V4-Evaluation (deterministisch, seeded; Aer nur fuer Architektur A).

    Kontroll-Gates zuerst, dann kappa*-Bisektion am Fez-Punkt, dann
    deskriptive Kurven. 0 QPU.
    """
    p1_grid = tuple(float(p) for p in p1_grid)

    # --- Architektur A (encodiert, Aer) ---
    encoded_curve = [run_witness(p1, n_shots=n_shots, seed=SEED_AER,
                                 ro=ro, ratio=ratio) for p1 in p1_grid]
    encoded_by_p1 = {pt["p1"]: pt for pt in encoded_curve}
    encoded_primary = encoded_by_p1[P1_PRIMARY]
    # T2: Noiseless-Kontrolle (p1=0 UND ro=0)
    encoded_noiseless = run_witness(0.0, n_shots=n_shots, seed=SEED_AER,
                                    ro=0.0, ratio=ratio)

    # --- Gate-Counts + Error-Budget (Bericht, Struktur) ---
    dft_circ = dft_rotation_circuit()
    full_tc = transpiled_counts(phi_prep_circuit().compose(dft_circ))
    budget = error_budget(full_tc["cx"], P1_PRIMARY, ratio)

    # --- Architektur B (nativ, numpy) ---
    proto_noiseless = native_protocol(0.0, 0.0, ro=0.0)
    native_exact_curve = [native_protocol(k, P1_PRIMARY, ro=0.0)["v_exact"]
                          for k in kappa_grid]
    native_curve_primary = [native_margin(k, P1_PRIMARY, ro=ro, ratio=ratio,
                                          n_shots=n_shots) for k in kappa_grid]

    # --- Kontroll-Gates ---
    controls = {
        "T1_native_identity": abs(proto_noiseless["v_exact"] - 1.0) <= 1e-9,
        "T2_encoded_identity": abs(encoded_noiseless["phi"]["v_hat"] - 1.0) \
            <= control_identity_tol,
        "M_monotonicity": all(
            native_exact_curve[i + 1] < native_exact_curve[i]
            for i in range(len(native_exact_curve) - 1)),
    }
    controls_ok = all(controls.values())

    # --- kappa* am Fez-Punkt (nur nach den Gates) ---
    if controls_ok:
        xs = find_kappa_star(encoded_primary["phi"]["margin"], P1_PRIMARY,
                             kappa_grid=kappa_grid, ro=ro, ratio=ratio,
                             n_shots=n_shots)
        kappa_star = None if xs is None else xs["kappa_star"]
        kappa_star_report = _kappa_star_report(xs)
    else:
        xs = None
        kappa_star = None
        kappa_star_report = {"kappa_star": None, "note": "Gates fehlgeschlagen"}

    # --- Deskriptiv: native p1-Kurven bei fixem kappa + kappa*(p1) ---
    native_p1_curves = {
        str(k): [native_margin(k, p1, ro=ro, ratio=ratio, n_shots=n_shots)
                 for p1 in p1_grid]
        for k in kappa_sweep
    }
    kappa_star_per_p1 = {}
    if controls_ok:
        for p1 in p1_grid:
            r = find_kappa_star(encoded_by_p1[p1]["phi"]["margin"], p1,
                                kappa_grid=kappa_grid, ro=ro, ratio=ratio,
                                n_shots=n_shots)
            kappa_star_per_p1[repr(p1)] = None if r is None else r["kappa_star"]

    return {
        "experiment": EXPERIMENT,
        "prereg_path": PREREG_PATH,
        "controls": controls,
        "controls_ok": bool(controls_ok),
        "encoded": {
            "primary_p1": P1_PRIMARY,
            "phi_primary": encoded_primary["phi"],
            "phi_noiseless": encoded_noiseless["phi"],
            "sep_primary": encoded_primary["sep"],
            "confound_max_diff_primary": encoded_primary["confound_max_diff"],
            "curve": [{"p1": pt["p1"], "phi": pt["phi"],
                       "confound_max_diff": pt["confound_max_diff"]}
                      for pt in encoded_curve],
            "gate_counts_phi_D": full_tc,
            "error_budget_2q_p1_3e4": budget,
        },
        "native": {
            "noiseless_v_exact": proto_noiseless["v_exact"],
            "v_exact_curve": [float(v) for v in native_exact_curve],
            "margin_curve_primary": native_curve_primary,
            "p1_curves_descriptive": native_p1_curves,
        },
        "kappa_star": kappa_star_report,
        "kappa_star_per_p1_descriptive": kappa_star_per_p1,
        "decision_rule": DECISION_RULE,
        "verdict": (verdict(kappa_star) if controls_ok
                    else "EVALUATION_INVALID_KONTROLLEN_FEHLEN"),
    }


def main():
    res = run_v4()
    doc = load_frozen_prereg()
    res["prereg_md5"] = doc["md5"]
    res["post_hoc_note"] = (
        "Kurven nach dem Freeze (md5 %s) berechnet; Kontroll-Gates zuerst "
        "geprueft; Simulator only, 0 QPU." % doc["md5"]
    )
    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    print("VERDICT:", res["verdict"])
    print(f"Kontrollen ok: {res['controls_ok']} | "
          f"T1={res['controls']['T1_native_identity']} "
          f"T2={res['controls']['T2_encoded_identity']} "
          f"M={res['controls']['M_monotonicity']}")
    ks = res["kappa_star"]["kappa_star"]
    ks_txt = "-" if ks is None else f"{ks:.2f}"
    print(f"kappa* = {ks_txt}  (Band: <1 REFUTED | 1-10 SCHWACH | >=10 CONFIRMED; "
          f"Vorhersage ~62, Band [10, 500])")
    enc = res["encoded"]["phi_primary"]
    print(f"Encoded phi_D (Aer, p1=3e-4): V={enc['v_hat']:.4f} "
          f"SE={enc['se']:.4f} margin={enc['margin']:.4f} | "
          f"phi_D 2q = {res['encoded']['gate_counts_phi_D']['cx']} "
          f"(Soll {PHI_D_CX_SOLL}), Budget 2q = "
          f"{res['encoded']['error_budget_2q_p1_3e4']:.4f}")
    mc = res["native"]["margin_curve_primary"]
    sel = [m for m in mc if m["kappa"] in (1.0, 10.0, 100.0)]
    print("Native margin(kappa, p1=3e-4): "
          + " | ".join(f"k={m['kappa']:g}: V={m['v_hat']:.4f} m={m['margin']:.4f}"
                       for m in sel))
    print(f"prereg md5: {doc['md5']}")


if __name__ == "__main__":
    main()