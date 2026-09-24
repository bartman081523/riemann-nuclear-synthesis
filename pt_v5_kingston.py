"""EXPERIMENT 035 — V5 Kingston-Drift-Test (H-V5): EIN Kingston-Job.

These H-V5 (X.4/X.6): ibm_kingston ist das neutralste Backend (kleinste
EV-Drift gegenueber Fez). Ein param-Transfer-Job (EstimatorV2, 3 Pubs:
Re(H_PT) / H_diag / Im(H_PT) an den committeten Fez-Run-1-Optimum-Params)
muss alle drei Observablen in die Drift-Baender um die Fez-Anker bringen;
sonst REFUTED.

Registrierte Ehrlichkeit VOR der Messung:
- Re(H_PT) ≡ H_diag als Operatoren (Theorem-Identitaet, C1) — der
  gemessene bias_PT_re ist der Shot-Kontrast identischer Observablen
  (Fez: -0.0119 Run 1, -0.0085 Run 2), NICHT ein Operator-Effekt.
- Schwellen 0.05/0.15 aus dem committeten Prereg (2026-06-08)
  wiederverwendet, nicht neu erfunden (Anti-Sharpshooter).
- Hardware-VQD scheitert dokumentiert (COBYLA-Lokalminima,
  pt_vqe_vqd.py) — statt eines Schein-"VQD-Gap" wird der bias_PT_re-
  Kontrast als Diskriminator registriert (Fez-Protokoll leitete Delta
  deterministisch aus H_diag her).
- Im-Bias ist deskriptiv (X.5: Session-Variabilitaet Faktor 200;
  Run 1 -0.0205, Run 2 +0.0001), kein Gate.
- Param-Transfer statt Online-VQE: EIN Job erzwingt es (ein
  COBYLA-Loop waeren ~11 sequenzielle Jobs). Fez-E0_meas (2.139820)
  ist der VQE-Loop-Wert, nicht param-identisch mit dem 3-Pub-Re-
  Messwert (2.145828); registriert wird E0 := Re-Pub an den Fez-Params.
- Spektrum-Trennung: min Re(spec(H_PT)) = 2.0018501462716807 (H1-
  Modellziel, committet) ist NICHT der Boden von Re(H_PT) = H_diag
  (exakt min(E_DIAG) = 2.0, Folgerung aus C1). Der Ansatz erreicht
  noiseless 2.13778 (Ansatz-Lokaloptimum) — der Drift-Test ist
  Anker-relativ, nicht Boden-relativ.
- Bandbreite M_obs = max(|shift_STRESS| + 2*sigma_shot, |Fez run2 -
  run1|); alle drei Komponenten sind gefrorene Offline-Groessen
  (Fez-Spread param-mismatched -> konservativ). sigma_shot ist die
  EXAKTE Shot-Varianz aus der STRESS-Dichtematrix (reduzierter
  2-Qubit-Circuit; Aer reduziert die 156-Qubit-ISA intern auf aktive
  Qubits, uniform Noise macht die Reduktion statistisch exakt —
  Cross-Check C6 gegen den Full-Path 1e-9), NICHT die Aer-Precision-
  Semantik (precision>0 injiziert N(exakt, precision)-Gauss-Noise,
  kein binomiales Shot-Sampling).
- EIN Kingston-Job (TOKEN2, NIEMALS echo/committen; TOKEN1 bleibt
  Fez-Pfad). Quota-Pruefung VOR Freeze und VOR Job.
"""

import argparse
import hashlib
import json
import math
import re

import numpy as np

from qiskit import QuantumCircuit
from qiskit.circuit.library import n_local as n_local_fn
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import EstimatorV2 as AerEstimator
from qiskit_ibm_runtime import EstimatorV2 as Estimator
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime.fake_provider import FakeFez

import pt_alpha_separation as al
from pt_structural import jacobi_A, E_DIAG
from pt_token_diagnose import load_token

EXPERIMENT = "035-ququint-v5-kingston-drift"
PREREG_PATH = "pt_v5_kingston_prereg.json"
RESULTS_PATH = "pt_v5_kingston_results.json"
HYPOTHESIS = "H-V5"
STEELMAN = ("Backend-Drift verschiebt Energie/Gap ausserhalb der "
            "Prereg-Baender: Kingston misst nicht die Fez-Anker, "
            "sondern ein backend-eigenes Bias-Regime (EV-Tabelle X.4: "
            "Kingston 2.67 vs Fez 2.97 vs Marrakesh 3.12).")

BACKEND_NAME = "ibm_kingston"
TOKEN_NAME = "IBMQ_TOKEN2"  # NUR Kingston-Pfad; TOKEN1 bleibt Fez-Pfad
INSTANCE = "open-instance"
GAMMA = 0.02
SHOTS = 8192
TRANSPILE_SEED = 7

# Fez-Anker (param-matched Referenz, pt_vqe_vqd_results.json / _run2.json)
FEZ_PARAMS = [-0.10039260373380426, 0.31547161200836626,
              -0.7794084485021391, -0.09555937796511249]
FEZ_RUN1 = {
    "job_id": "d9fidihhtsac739fg3n0",
    "re": 2.145828476862593,
    "hd": 2.1577507852679036,
    "im": 0.009395361635620568,
    "bias": -0.011922308405310833,
    "e0_loop": 2.1398203106629032,  # VQE-Loop-Wert, nicht 3-Pub-Re
}
FEZ_RUN2 = {
    "job_id": "d9fjbraneu4c739pmaqg",
    "re": 2.17247246569962,
    "hd": 2.1809962200449498,
    "im": 0.03003274212843888,
    "bias": -0.008523754345329593,
}
FEZ_SPREAD = {k: abs(FEZ_RUN2[k] - FEZ_RUN1[k])
              for k in ("re", "hd", "im", "bias")}

# Noiseless-Referenzen (FakeFez-ISA, density_matrix exakt, gefroren)
NOISELESS_RE = 2.137780842080
NOISELESS_IM = 0.008960976233
NOISELESS_E0_H1 = 2.0018501462716807  # min Re(spec(H_PT)), committet
NOISELESS_E0_DIAG = 2.0               # min(E_DIAG), exakt (C1-Folgerung)

# STRESS-Baseline (p1=3e-4, ro=1e-2, ratio=10, §Z.13-Konvention)
STRESS = {"p1": 3e-4, "ro": 1e-2, "ratio": 10.0}
STRESS_SHIFT_RE = 0.007975119242
STRESS_SHIFT_IM = 0.000111359004

# Shot-SE: EXAKTE Varianz aus der STRESS-Dichtematrix des reduzierten
# 2-Qubit-Circuits (phys 23->0, phys 22->1; uniform Noise -> statistisch
# exakt, C6 cross-checkt gegen den Full-Path 1e-9). SE = sqrt(Var)/sqrt(
# SHOTS); bias = hypot(SE_re, SE_hd) (re/hd identische Operatoren,
# unabhaengige Pubs). Bewusst NICHT die AerEstimator-Precision-Semantik:
# precision>0 injiziert N(exakt, precision)-Gauss-Noise, kein binomiales
# Shot-Sampling. Deterministisch und exakt, kein sd-Schaetzer.
SE_RE = 0.004367920539504277
SE_HD = 0.004367920539504277
SE_IM = 0.00032217563103976147
SE_BIAS = 0.006177172466334955
SHOT_SIGMA_FACTOR = 2.0

# Committete Schwellen (pt_vqe_vqd-Prereg, 2026-06-08) — wiederverwendet
THRESH_BIAS_CONFIRMED = 0.05
THRESH_BIAS_REFUTED = 0.15

# ISA-Akzeptanz (offline FakeFez-Anker gefroren; online Kingston-Soll)
ISA_TWO_Q_FROZEN = 1
ISA_ONE_Q_FROZEN = 18
ISA_DEPTH_FROZEN = 11
ISA_NAMES_FROZEN = ("cz",)
ONLINE_2Q_NAMES = ("cz", "ecr", "cx")
ONLINE_DEPTH_MAX = 40

VERDICT_MAP = {
    "CONFIRMED": "H-V5_CONFIRMED_KINGSTON_NEUTRAL_BAND",
    "BIAS_MITTEL": "H-V5_INNERHALB_BAENDER_BIAS_MITTELKLASSE",
    "MITTEL": "H-V5_MITTEL_EIN_OBSERVABLE_AUSSEN",
    "REFUTED": "H-V5_REFUTED_DRIFT",
    "INVALID": "EVALUATION_INVALID_KONTROLLE_GESCHEITERT",
}

OBS_KEYS = ("re", "hd", "im")


# === Operatoren (Theorem-Identitaet) ===

def build_operators():
    """A, H_diag, H_PT und die drei SparsePauliOps (logisch, ohne Layout)."""
    A = jacobi_A(E_DIAG, y=1.0)
    H_diag = np.diag(E_DIAG).astype(complex)
    H_PT = H_diag + 1j * GAMMA * A
    H_real = (H_PT + H_PT.conj().T) / 2
    H_imag = (H_PT - H_PT.conj().T) / (2j)
    return {
        "A": A, "H_diag": H_diag, "H_PT": H_PT,
        "H_real": H_real, "H_imag": H_imag,
        "ops_real": SparsePauliOp.from_operator(H_real),
        "ops_diag": SparsePauliOp.from_operator(H_diag),
        "ops_imag": SparsePauliOp.from_operator(H_imag),
    }


def _laid_out(ops, isa):
    """Operator auf das ISA-Layout heben (apply_layout, wie Fez-Protokoll)."""
    return ops.apply_layout(isa.layout)


def noiseless_ground_energy():
    """Boden von Re(H_PT) = H_diag: exakt min(E_DIAG) (C1-Folgerung)."""
    ops = build_operators()
    return float(np.linalg.eigvalsh(ops["H_real"])[0])


def noiseless_e0_h1():
    """min Re(spec(H_PT)) — das committete H1-Modellziel (nicht-hermitisch)."""
    ops = build_operators()
    eigs = sorted(np.linalg.eigvals(ops["H_PT"]), key=lambda z: z.real)
    return float(eigs[0].real)


# === ISA (FakeFez offline, Backend online) ===

def ansatz_logical():
    return n_local_fn(2, ["ry"], "cx", "linear", reps=1)


def isa_ansatz_fakefez():
    pm = generate_preset_pass_manager(
        optimization_level=3, backend=FakeFez(), seed_transpiler=TRANSPILE_SEED)
    return pm.run(ansatz_logical())


def isa_ansatz_for(backend):
    pm = generate_preset_pass_manager(
        optimization_level=3, backend=backend, seed_transpiler=TRANSPILE_SEED)
    return pm.run(ansatz_logical())


def isa_gate_counts(isa):
    two_q = sum(1 for inst in isa.data
                if len(inst.qubits) == 2 and inst.operation.name != "barrier")
    one_q = sum(1 for inst in isa.data
                if len(inst.qubits) == 1 and inst.operation.name != "barrier")
    names = sorted({inst.operation.name for inst in isa.data
                    if len(inst.qubits) == 2 and inst.operation.name != "barrier"})
    return {"two_q": two_q, "one_q": one_q, "names": names,
            "depth": int(isa.depth())}


def isa_accept_online(counts):
    """Registrierte Online-Akzeptanz: GENAU 1 2q-Gate aus cz/ecr/cx, flach."""
    return (counts["two_q"] == ISA_TWO_Q_FROZEN
            and all(n in ONLINE_2Q_NAMES for n in counts["names"])
            and counts["depth"] <= ONLINE_DEPTH_MAX)


# === Offline-Referenzen (FakeFez-ISA + Aer) ===

def _aer_estimator(precision, noise_model=None):
    options = {"default_precision": precision,
               "backend_options": {"method": "density_matrix"}}
    if noise_model is not None:
        options["backend_options"]["noise_model"] = noise_model
    return AerEstimator(options=options)


def _three_observables(bound_isa, precision, noise_model=None):
    ops = build_operators()
    pubs = [(bound_isa, _laid_out(ops["ops_real"], bound_isa)),
            (bound_isa, _laid_out(ops["ops_diag"], bound_isa)),
            (bound_isa, _laid_out(ops["ops_imag"], bound_isa))]
    est = _aer_estimator(precision, noise_model)
    vals = est.run(pubs).result()
    return [float(vals[i].data.evs) for i in range(3)]


def noiseless_observables_at(params):
    """Noiseless-Anker an den Fez-Params (ISA inklusive, exakt)."""
    isa = isa_ansatz_fakefez()
    re, hd, im = _three_observables(isa.assign_parameters(params), 0.0)
    return {"re": re, "hd": hd, "im": im, "bias": re - hd}


def stress_baseline():
    """STRESS-Shift vs noiseless (gefehrene Offline-Grossen)."""
    isa = isa_ansatz_fakefez()
    bound = isa.assign_parameters(FEZ_PARAMS)
    nm = al.build_isa_noise_model(STRESS["p1"], ro=STRESS["ro"],
                                  ratio=STRESS["ratio"])
    r0, d0, i0 = _three_observables(bound, 0.0)
    r1, d1, i1 = _three_observables(bound, 0.0, noise_model=nm)
    return {
        "noiseless": {"re": r0, "hd": d0, "im": i0, "bias": r0 - d0},
        "stress": {"re": r1, "hd": d1, "im": i1, "bias": r1 - d1},
        "shift": {"re": r1 - r0, "hd": d1 - d0, "im": i1 - i0,
                  "bias": (r1 - d1) - (r0 - d0)},
    }


def _reduced_bound_isa():
    """Bound-ISA auf die 2 aktiven Qubits reduziert (Layout-abgeleitet).

    Aer reduziert die 156-Qubit-ISA intern auf aktive Qubits; das
    Noise-Modell (build_isa_noise_model) ist UNIFORM ueber alle Qubits
    (qerror ohne gate_qubits -> alle, roerror nur bei measure), daher
    ist die Reduktion statistisch exakt (Cross-Check C6 gegen Full-Path).
    """
    isa = isa_ansatz_fakefez()
    bound = isa.assign_parameters(FEZ_PARAMS)
    virt = isa.layout.initial_layout.get_virtual_bits()
    qregs = [r for r in isa.layout.initial_layout.get_registers()
             if r.size == 2]
    qreg = qregs[0]
    pmap = {virt[qreg[0]]: 0, virt[qreg[1]]: 1}  # logisch 0/1 -> phys
    red = QuantumCircuit(2)
    for inst in bound.data:
        qidx = [bound.find_bit(q).index for q in inst.qubits]
        if qidx and all(i in pmap for i in qidx):
            red.append(inst.operation, [pmap[i] for i in qidx])
    return red


def noisy_density_matrix_stress():
    """Exakte STRESS-Dichtematrix (4x4) des reduzierten bound-ISA."""
    nm = al.build_isa_noise_model(STRESS["p1"], ro=STRESS["ro"],
                                  ratio=STRESS["ratio"])
    sim = AerSimulator(method="density_matrix", noise_model=nm)
    circ = _reduced_bound_isa()
    circ.save_density_matrix()
    return np.asarray(sim.run(circ).result().data(0)["density_matrix"])


def shot_se():
    """Exakte Shot-SE pro Observable: sqrt(Var(O))/sqrt(SHOTS).

    Var(O) = Tr(rho O^2) - <O>^2 aus der STRESS-Dichtematrix. bias-Kontrast
    hypot(SE_re, SE_hd) — re/hd sind identische Operatoren (C1) in zwei
    unabhaengigen Pubs. Deterministisch und exakt (kein sd-Schaetzer).
    """
    rho = noisy_density_matrix_stress()
    ops = build_operators()
    se = {}
    for key, name in (("ops_real", "re"), ("ops_diag", "hd"),
                      ("ops_imag", "im")):
        O = ops[key].to_matrix()
        exp = float(np.real(np.trace(rho @ O)))
        var = float(np.real(np.trace(rho @ O @ O)) - exp * exp)
        se[name] = math.sqrt(max(var, 0.0)) / math.sqrt(SHOTS)
    se["bias"] = math.hypot(se["re"], se["hd"])
    return se


def shot_se_frozen():
    return {"re": SE_RE, "hd": SE_HD, "im": SE_IM, "bias": SE_BIAS}


# === Baender (registrierte Ableitung) ===

def band_half_width(key):
    m = max(abs(STRESS_SHIFT_RE if key != "im" else STRESS_SHIFT_IM)
            + SHOT_SIGMA_FACTOR * shot_se_frozen()[key], FEZ_SPREAD[key])
    return m


def bands():
    anchors = {"re": FEZ_RUN1["re"], "hd": FEZ_RUN1["hd"],
               "im": FEZ_RUN1["im"]}
    return {k: [anchors[k] - band_half_width(k),
                anchors[k] + band_half_width(k)] for k in anchors}


# === Kontrolle ===

def run_controls():
    c = {}
    ops = build_operators()
    # C1 Theorem-Identitaet: Re(H_PT) ≡ H_diag (Matrix UND Pauli-Ebene)
    c["C1_theorem_identity"] = bool(
        np.array_equal(ops["H_real"], ops["H_diag"])
        and ops["ops_real"].simplify() == ops["ops_diag"].simplify())
    # C2 Noiseless-Anker an den Fez-Params (inkl. ISA)
    nl = noiseless_observables_at(FEZ_PARAMS)
    c["C2_noiseless_anchors"] = bool(
        abs(nl["re"] - NOISELESS_RE) <= 1e-6
        and abs(nl["hd"] - NOISELESS_RE) <= 1e-6
        and abs(nl["im"] - NOISELESS_IM) <= 1e-6
        and nl["bias"] == 0.0)
    # C3 Spektrum: Boden(H_real) = min(E_DIAG) exakt; H1-Ziel committet
    c["C3_spectrum_split"] = bool(
        noiseless_ground_energy() == NOISELESS_E0_DIAG
        and abs(noiseless_e0_h1() - NOISELESS_E0_H1) <= 1e-9)
    # C4 ISA-Akzeptanz offline (FakeFez-Anker gefroren)
    cnt = isa_gate_counts(isa_ansatz_fakefez())
    c["C4_isa_offline_anchor"] = bool(
        cnt["two_q"] == ISA_TWO_Q_FROZEN and cnt["one_q"] == ISA_ONE_Q_FROZEN
        and tuple(cnt["names"]) == ISA_NAMES_FROZEN
        and cnt["depth"] == ISA_DEPTH_FROZEN)
    # C5 STRESS-Baseline reproduziert die gefrorenen Shifts
    base = stress_baseline()
    c["C5_stress_baseline"] = bool(
        abs(base["shift"]["re"] - STRESS_SHIFT_RE) <= 1e-6
        and abs(base["shift"]["hd"] - STRESS_SHIFT_RE) <= 1e-6
        and abs(base["shift"]["im"] - STRESS_SHIFT_IM) <= 1e-6
        and base["shift"]["bias"] == 0.0)
    # C6 Reduktions-Exaktheit: reduzierter 2-Qubit-Pfad ≡ Full-Path
    rho = noisy_density_matrix_stress()
    O = ops["ops_real"].to_matrix()
    re_red = float(np.real(np.trace(rho @ O)))
    c["C6_reduction_exact"] = bool(
        abs(re_red - (NOISELESS_RE + STRESS_SHIFT_RE)) <= 1e-9
        and shot_se()["re"] == SE_RE
        and shot_se()["hd"] == SE_HD
        and shot_se()["im"] == SE_IM)
    return c


# === Prereg ===

def build_prereg_payload():
    return {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "steelman": STEELMAN,
        "registered_before": {
            "param_transfer": (
                "EIN Job erzwingt Param-Transfer statt Online-VQE (ein "
                "COBYLA-Loop waeren ~11 sequenzielle Jobs): die drei Pubs "
                "werden an den committeten Fez-Run-1-Optimum-Params "
                f"{FEZ_PARAMS} gemessen (Job d9fidihhtsac739fg3n0)."),
            "theorem_identity": (
                "Re(H_PT) ≡ H_diag als Operatoren (C1, Matrix- und "
                "Pauli-Ebene) — der gemessene bias_PT_re ist der Shot-"
                "Kontrast identischer Observablen (Fez Run 1 -0.0119, "
                "Run 2 -0.0085), kein Operator-Effekt."),
            "threshold_reuse": (
                "Schwellen 0.05/0.15 aus dem committeten Prereg vom "
                "2026-06-08 WIEDERVERWENDET, nicht neu erfunden "
                "(Anti-Sharpshooter)."),
            "vqd_honest_re_registration": (
                "Hardware-VQD scheitert dokumentiert (COBYLA-Lokalminima, "
                "pt_vqe_vqd.py-Docstring); statt eines Schein-VQD-Gap "
                "wird bias_PT_re als Diskriminator registriert — das "
                "Fez-Protokoll leitete Delta deterministisch aus H_diag her."),
            "im_bias_descriptive": (
                "Im-Bias ist KEIN Gate (X.5: Session-Variabilitaet Faktor "
                "200; Fez Run 1 -0.0205, Run 2 +0.0001); nur deskriptiv."),
            "e0_definition": (
                "E0 := Re-Pub an den Fez-Params (param-transfer). "
                "Fez-E0_meas 2.139820 ist der VQE-Loop-Wert und nicht "
                "param-identisch mit dem 3-Pub-Re-Messwert 2.145828."),
            "spectrum_split": (
                "min Re(spec(H_PT)) = 2.0018501462716807 (H1-Modellziel, "
                "committet) ist NICHT der Boden von Re(H_PT) = H_diag "
                "(exakt min(E_DIAG) = 2.0); der Ansatz erreicht noiseless "
                "2.13778 — der Drift-Test ist Anker-relativ, nicht "
                "Boden-relativ."),
            "band_derivation": (
                "M_obs = max(|shift_STRESS| + 2*sigma_shot, |Fez run2 - "
                "run1|); Fez-Spread param-mismatched, konservativ. Alle "
                "drei Komponenten gefroren: STRESS-Shift (ISA + Noise "
                "p1=3e-4, ro=1e-2, ratio=10), Shot-SE exakt aus der "
                "STRESS-Dichtematrix (reduzierter 2-Qubit-Circuit, "
                "Var = Tr(rho O^2) - <O>^2, SE = sqrt(Var)/sqrt(8192); "
                "Aer reduziert die 156-Qubit-ISA intern auf aktive "
                "Qubits, uniform Noise macht die Reduktion statistisch "
                "exakt, C6 cross-checkt 1e-9). Bewusst NICHT die "
                "AerEstimator-Precision-Semantik: precision>0 injiziert "
                "N(exakt, precision)-Gauss-Noise, kein binomiales "
                "Shot-Sampling."),
            "shot_se_analytic": (
                "sigma_shot ist die exakte Varianz aus der STRESS-"
                "Dichtematrix, nicht ein sd-Schaetzer ueber Seeds; "
                "Ergebnis: alle drei Baender sind Fez-Spread-dominiert "
                "(2*sigma_shot + |shift| < Spread fuer re/hd/im), d.h. "
                "die Baender sind genau die Spanne der beiden Fez-Runs "
                "(obere Kante = Fez Run 2)."),
            "grade_expectation": (
                "Ein-Job-Bestaetigung ist ein A- Kandidat, NICHT A "
                "(eine Session, keine Cross-Session-Replikation)."),
        },
        "anchors": {
            "fez_run1": FEZ_RUN1,
            "fez_run2": FEZ_RUN2,
            "fez_spread": FEZ_SPREAD,
            "noiseless": {"re": NOISELESS_RE, "im": NOISELESS_IM,
                          "e0_h1": NOISELESS_E0_H1,
                          "e0_diag": NOISELESS_E0_DIAG},
            "stress_shift": {"re": STRESS_SHIFT_RE, "im": STRESS_SHIFT_IM},
            "shot_se": shot_se_frozen(),
        },
        "thresholds": {
            "bias_confirmed": THRESH_BIAS_CONFIRMED,
            "bias_refuted": THRESH_BIAS_REFUTED,
            "shots": SHOTS,
            "band_shot_sigma": SHOT_SIGMA_FACTOR,
            "stress": STRESS,
            "online_depth_max": ONLINE_DEPTH_MAX,
            "online_2q_names": list(ONLINE_2Q_NAMES),
        },
        "bands": bands(),
        "isa_acceptance": {
            "offline_frozen": {"two_q": ISA_TWO_Q_FROZEN,
                               "one_q": ISA_ONE_Q_FROZEN,
                               "names": list(ISA_NAMES_FROZEN),
                               "depth": ISA_DEPTH_FROZEN},
            "online": {"two_q": ISA_TWO_Q_FROZEN,
                       "names": list(ONLINE_2Q_NAMES),
                       "depth_max": ONLINE_DEPTH_MAX},
        },
        "controls": {
            "C1_theorem_identity":
                "Re(H_PT) ≡ H_diag exakt (Matrix + Pauli) — sonst INVALID",
            "C2_noiseless_anchors":
                "noiseless an Fez-Params: Re=H_diag=2.137780842080, "
                "Im=0.008960976233, bias exakt 0",
            "C3_spectrum_split":
                "Boden(H_real) = 2.0 exakt UND H1-Ziel 2.0018501462716807 "
                "reproduziert (Trennung der beiden Groessen)",
            "C4_isa_offline_anchor":
                "FakeFez-ISA gefroren: 1 cz, 18 1q, Tiefe 11 (seed 7)",
            "C5_stress_baseline":
                "STRESS-Shift reproduziert gefroren (+0.007975119242 Re, "
                "+0.000111359004 Im, bias exakt 0)",
            "C6_reduction_exact":
                "Reduzierter 2-Qubit-Pfad ≡ Full-Path: <Re> aus der "
                "STRESS-Dichtematrix trifft 2.145755961322 (1e-9) und "
                "shot_se() trifft die gefrorenen SE-Konstanten exakt",
            "gate": "Kontrollfehler -> EVALUATION_INVALID",
        },
        "verdict_map": dict(VERDICT_MAP),
        "decision_table": [
            "Kontrollen fail -> EVALUATION_INVALID",
            "0 Observablen aussen & |bias| < 0.05 -> CONFIRMED",
            "0 Observablen aussen & 0.05 <= |bias| < 0.15 -> BIAS_MITTEL",
            "genau 1 Observable aussen & |bias| < 0.05 -> MITTEL",
            "sonst (>=2 aussen ODER 1 aussen + bias >= 0.05 ODER "
            "|bias| >= 0.15) -> REFUTED_DRIFT",
        ],
        "protocol": {
            "estimator": "EstimatorV2 (mode=backend)",
            "pubs": ["Re(H_PT)", "H_diag", "Im(H_PT)"],
            "resilience_level": 1,
            "dynamical_decoupling": "XX",
            "one_job": True,
        },
        "qpu": {
            "backend": BACKEND_NAME,
            "token": "IBMQ_TOKEN2 (NIEMALS echo/committen; TOKEN1 bleibt "
                     "Fez-Pfad)",
            "quota_check_first": True,
            "one_job": True,
        },
        "seeds": {"transpiler": TRANSPILE_SEED},
    }


def canonical_payload_json(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def payload_md5(payload):
    return hashlib.md5(canonical_payload_json(payload).encode("utf-8")).hexdigest()


def freeze_prereg(payload, path=PREREG_PATH):
    doc = dict(payload)
    doc["md5"] = payload_md5(payload)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    return doc


def verify_prereg_md5(doc):
    body = {k: v for k, v in doc.items() if k != "md5"}
    return payload_md5(body) == doc.get("md5")


def load_frozen_prereg(path=PREREG_PATH):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if not verify_prereg_md5(doc):
        raise ValueError("Prereg-MD5 verletzt: " + path)
    return doc


# === Quota-Pruefung (VOR Freeze und VOR Job) ===

def _make_service():
    token = load_token(TOKEN_NAME)
    return QiskitRuntimeService(channel="ibm_quantum_platform",
                                token=token, instance=INSTANCE)


def run_quota_check(service=None):
    if service is None:
        service = _make_service()
    backend = service.backend(BACKEND_NAME)
    status = backend.status()
    info = {
        "backend": BACKEND_NAME,
        "status": str(getattr(status, "status", None)
                      or getattr(status, "status_msg", "")),
        "operational": bool(status.operational),
        "pending_jobs": int(status.pending_jobs),
        "recent_jobs": None,
        "active_recent": None,
    }
    try:
        jobs = service.jobs(backend_name=BACKEND_NAME, limit=20)
        info["recent_jobs"] = len(jobs)
        info["active_recent"] = sum(
            1 for j in jobs if "DONE" not in str(j.status())
            and "ERROR" not in str(j.status())
            and "CANCELLED" not in str(j.status()))
    except Exception as exc:  # Historie ist optional, Blockade ist Status
        info["recent_jobs_error"] = type(exc).__name__
    return info


# === EIN Kingston-Job ===

def run_kingston_job(service=None):
    if service is None:
        service = _make_service()
    backend = service.backend(BACKEND_NAME)
    ops = build_operators()
    isa = isa_ansatz_for(backend)
    counts = isa_gate_counts(isa)
    bound = isa.assign_parameters(FEZ_PARAMS)
    pubs = [(bound, _laid_out(ops["ops_real"], isa)),
            (bound, _laid_out(ops["ops_diag"], isa)),
            (bound, _laid_out(ops["ops_imag"], isa))]
    est = Estimator(mode=backend)
    est.options.resilience_level = 1
    est.options.dynamical_decoupling.enable = True
    est.options.dynamical_decoupling.sequence_type = "XX"
    est.options.default_shots = SHOTS
    job = est.run(pubs)  # EIN Aufruf, drei Pubs
    result = job.result()
    re, hd, im = (float(result[i].data.evs) for i in range(3))
    return {
        "job_id": job.job_id(),
        "backend": BACKEND_NAME,
        "isa": counts,
        "isa_accept": isa_accept_online(counts),
        "meas": {"re": re, "hd": hd, "im": im, "bias": re - hd},
    }


# === Auswertung ===

def evaluate(meas, bands_doc, controls_ok=True):
    if not controls_ok:
        return VERDICT_MAP["INVALID"], {"n_out": None, "flags": None,
                                        "bias": meas.get("bias"),
                                        "bias_class": None}
    flags = {}
    n_out = 0
    for key in ("re", "hd", "im"):
        lo, hi = bands_doc[key]
        inside = bool(lo <= meas[key] <= hi)
        flags[key] = {"value": meas[key], "band": [lo, hi], "in_band": inside}
        if not inside:
            n_out += 1
    bias = meas["bias"]
    ab = abs(bias)
    bias_class = ("ok" if ab < THRESH_BIAS_CONFIRMED
                  else "mittel" if ab < THRESH_BIAS_REFUTED else "hoch")
    if n_out == 0 and bias_class == "ok":
        verdict = VERDICT_MAP["CONFIRMED"]
    elif n_out == 0 and bias_class == "mittel":
        verdict = VERDICT_MAP["BIAS_MITTEL"]
    elif n_out == 1 and bias_class == "ok":
        verdict = VERDICT_MAP["MITTEL"]
    else:
        verdict = VERDICT_MAP["REFUTED"]
    return verdict, {"n_out": n_out, "flags": flags,
                     "bias": bias, "bias_class": bias_class}


# === CLI ===

def main(argv=None):
    parser = argparse.ArgumentParser(description=EXPERIMENT)
    parser.add_argument("--quota", action="store_true",
                        help="TOKEN2-Quota-Pruefung (VOR Freeze/Job)")
    parser.add_argument("--freeze", action="store_true",
                        help="Prereg einfrieren (VOR Job)")
    parser.add_argument("--run", action="store_true",
                        help="EIN Kingston-Job + Auswertung")
    args = parser.parse_args(argv)

    if args.quota:
        info = run_quota_check()
        print(json.dumps(info, indent=2))
        return 0 if info["operational"] else 1

    if args.freeze:
        controls = run_controls()
        if not all(controls.values()):
            print("KONTROLLEN FEHLGESCHLAGEN — kein Freeze:", controls)
            return 2
        # Freeze-Guard: Shot-SE ist exakt deterministisch -> bit-genau
        se_live = shot_se()
        se_frozen = shot_se_frozen()
        for k in ("re", "hd", "im", "bias"):
            if se_live[k] != se_frozen[k]:
                print("SE-GUARD FEHLGESCHLAGEN (%s): live %.12f vs frozen "
                      "%.12f" % (k, se_live[k], se_frozen[k]))
                return 2
        doc = freeze_prereg(build_prereg_payload())
        print("PREREG FROZEN:", doc["md5"])
        print("Baender:", json.dumps(doc["bands"], indent=2))
        return 0

    if args.run:
        prereg = load_frozen_prereg()
        controls = run_controls()
        quota = run_quota_check()
        print("Quota:", json.dumps(quota))
        if not quota["operational"]:
            print("BLOCKADE: Backend nicht operational — dokumentierte "
                  "Zurueckstellung, kein zweiter Versuch.")
            return 3
        if not all(controls.values()):
            print("KONTROLLEN FEHLGESCHLAGEN VOR JOB:", controls)
            return 2
        run = run_kingston_job()
        online_ok = run["isa_accept"]
        verdict, detail = evaluate(run["meas"], prereg["bands"],
                                   controls_ok=all(controls.values())
                                   and online_ok)
        results = {
            "experiment": EXPERIMENT,
            "prereg_md5": prereg["md5"],
            "quota": quota,
            "controls": controls,
            "online_isa": run["isa"],
            "isa_accept": online_ok,
            "job_id": run["job_id"],
            "meas": run["meas"],
            "detail": detail,
            "verdict": verdict,
            "post_hoc_note": "Auswertung ausschliesslich gegen die "
                             "gefrorenen Baender/Schwellen (md5 "
                             + prereg["md5"] + ").",
        }
        with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)
        print("JOB:", run["job_id"], "| ISA:", run["isa"])
        print("MEAS:", json.dumps(run["meas"], indent=2))
        print("VERDICT:", verdict)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())