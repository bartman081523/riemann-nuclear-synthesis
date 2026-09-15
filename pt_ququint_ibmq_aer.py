"""
EXPERIMENT 031 - Ququint auf IBMQ, Phase 2: Aer-Noise + Transpilation.

Fortsetzung von EXPERIMENT 030 (Phase 1, pt_ququint_ibmq): die encodierten
Zustände/Messungen werden zu qiskit-Circuits übersetzt. Diese Phase läuft
KOMPLETT auf AerSimulator (density_matrix, 64x64, seeded reproduzierbar) —
KEINE QPU-Kosten, KEIN echter Backend-Zugriff (Guard: kein IBM-Provider-Import).

Was Phase 2 leistet:
  1. EXAKTE Präparation: |phi> = (1/sqrt(5)) sum_k |k,k> in 6 Qubits via
     RY/CRY + CX-Kopie; die 5 rho_sep-Komponenten |kk> via reine X-Gates
     (0 Zwei-Qubit-Gates — die Präparations-Asymmetrie ist das ehrliche
     Verschränkungs-Kosten-Signal).
  2. DFT-Messrotation U = F (x) F† via UnitaryGate (Phase-1-Konvention:
     qiskit little-endian Index k + 8*l == logical_index(a, b) = a*8+b).
  3. QPU-Job-Layout: 12 Circuits (phi_C, phi_D, sep_C x5, sep_D x5) — genau
     die Batch-Struktur, die Phase 3 als EINEN Fez-Job einreicht.
  4. Transpilation auf die Phase-2-Basis (rz/sx/x/cx): GATE-COUNTS als
     Struktur-Ausgabe. Transpiler-Output ist versionsabhängig — die Tests
     pinnen nur strukturelle Fakten (sep_C braucht 0 cx; phi/DFT brauchen
     cx), niemals exakte Counts.
  5. STRESS-Noise-Modell: Readout 1e-2 (Fez-typische Wahl) + Depolarizing
     p1 auf 1q-Gates, ratio*p1 auf cx. STRESS heißt: nicht kalibriert,
     bewusst konservativ (rz ist virtuell, wird hier aber mitgezählt).
     Nicht ein Fez-Kalibrierteil — Vorhersagen bleiben Bänder, keine
     exakten Werte.
  6. Witness-Kurve V(p1) mit parametrischem Bootstrap um die beobachteten
     Histogramme (exakt das, was Hardware-Daten liefern würden).

CCZ-These — OUT OF SCOPE (Verfeinerung ggü. §Z.12.6): die native-CCZ-
Fidelity-These (CCZ-Diagonalphase direkt in Hardware vs. 7-CX-Zerlegung)
ist in der 3-Qubit-Emulation NOT testable in emulation — die Emulation
transpiliert zu CX, es gibt nie ein natives CCZ-Gate. Phase 2 testet nur
die Synthese-Overhead-Seite (Gate-Counts + Error-Budget). Die These selbst
braucht natives Qudit-Hardware-CCZ und bleibt hypothetisch.

Anti-Sharpshooter: die Phase-2-Ergebnisse (Gate-Counts, Noise-Kurve) gehen
als PREREG-DRAFT in Phase 3 ein — die Phase-3-Predictions müssen aus
Phase 2 kommen, nicht post-hoc aus Hardware-Daten.
"""

import os
import sys
from functools import lru_cache

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import UnitaryGate
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error

from pt_ququint_ibmq import (
    D5,
    ENC_DIM,
    TWO_DIM,
    WITNESS_BOUND,
    dft5_encoded,
    dft_diagonal_weight,
    separable_dephased_encoded,
)

QISKIT_BASIS = ("rz", "sx", "x", "cx")
N_SHOTS_DEFAULT = 8192
NOISE_GRID_DEFAULT = (0.0, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2)
READOUT_ERROR_DEFAULT = 1e-2   # Fez-typische STRESS-Wahl, nicht kalibriert
TWO_Q_RATIO_DEFAULT = 10.0
_BOOT = 1000

# RY nutzt HALBWINKEL: P(q2=0) = cos^2(theta/2) = 4/5 verlangt
# cos(theta/2) = 2/sqrt(5) -> theta = 2 arccos(2/sqrt(5)) (nicht arccos!).
_THETA = float(2.0 * np.arccos(2.0 / np.sqrt(5.0)))


# === PRÄPARATIONS-CIRCUITS (exakt gegen Phase 1 verifiziert) ===


def phi_prep_circuit():
    """|phi> = (1/sqrt(5)) sum_k |k,k> auf 6 Qubits, exakt (statevector-getestet).

    Qubit-Layout: A = (q0,q1,q2), k = q0 + 2*q1 + 4*q2; B = (q3,q4,q5).
    qiskit little-endian 64-dim Index = k + 8*l = logical_index(l, k):
    ggü. Phase 1 A<->B GETAUSCHT — für die in Phase 2/3 verwendeten
    Zustände (|phi>, rho_sep) unmaterial, da beide unter A<->B invariant
    sind (Support auf der Diagonalen). Für asymmetrische Zustände (z.B.
    Weyl-Bell) müsste die Abbildung explizit gemacht werden.
    """
    qc = QuantumCircuit(6)
    qc.ry(_THETA, 2)          # cos = 2/sqrt(5) auf q2=0-Zweig (4 uniforme k)
    qc.x(2)
    qc.cry(np.pi / 2, 2, 0)   # q2=1-Zweig -> q0 gleichverteilt
    qc.cry(np.pi / 2, 2, 1)
    qc.x(2)
    qc.cx(0, 3)               # Kopie nach B: |k,k>
    qc.cx(1, 4)
    qc.cx(2, 5)
    return qc


def sep_prep_circuits():
    """Die 5 rho_sep-Komponenten |kk> als reine X-Gate-Circuits (0 cx).

    Jede Komponente ist ein Basiszustand; die Gleichgewichts-Mischung ist
    exakt separable_dephased_encoded. Das ist die Konfund-Kontrolle OHNE
    verschränkende Gates — die Präparations-Asymmetrie (0 vs ~7 cx) ist
    der ehrliche Kosten-Signal für die Verschränkungserzeugung.
    """
    circuits = []
    for k in range(D5):
        qc = QuantumCircuit(6)
        for bit in range(3):
            if (k >> bit) & 1:
                qc.x(bit)        # Register A
                qc.x(3 + bit)    # Register B
        circuits.append(qc)
    return circuits


def dft_rotation_circuit():
    """Messung D: U = F (x) F† als UnitaryGate auf den beiden Registern.

    qargs [0,1,2] für F auf A (Gate-Qubit 0 = kleinstes Bit = Phase-1-
    Konvention), [3,4,5] für F† auf B.
    """
    F = dft5_encoded()
    qc = QuantumCircuit(6)
    qc.append(UnitaryGate(F, label="F5_A"), [0, 1, 2])
    qc.append(UnitaryGate(F.conj().T, label="F5dag_B"), [3, 4, 5])
    return qc


# === QPU-JOB-LAYOUT (12 Circuits = Phase-3-Batch) ===


def witness_job_layout():
    """Die 12 Circuits des Phase-3-Fez-Jobs (alle mit measure_all).

    phi_C/phi_D: |phi> in Messung C (computational) bzw. D (DFT-Basis).
    sep_C/sep_D: die 5 rho_sep-Komponenten in beiden Messungen (auf der
    QPU wird die Mischung durch Job-Batching über die 5 Circuits erzeugt —
    identische Statistik zur Gleichgewichts-Mischung).
    """
    dft = dft_rotation_circuit()
    phi = phi_prep_circuit()
    layout = {
        "phi_C": phi.copy(),
        "phi_D": phi.compose(dft),
        "sep_C": sep_prep_circuits(),
        "sep_D": [s.compose(dft) for s in sep_prep_circuits()],
    }
    for circ in [layout["phi_C"], layout["phi_D"]]:
        circ.measure_all()
    for group in (layout["sep_C"], layout["sep_D"]):
        for circ in group:
            circ.measure_all()
    return layout


# === TRANSPIlATION (Gate-Counts auf der Phase-2-Basis) ===


def transpiled_counts(circ, optimization_level=2):
    """Transpiliert einen PRE-Measure-Circuit auf QISKIT_BASIS und zählt.

    Liefert counts (op-name -> Anzahl), depth, cx, num_qubits. Nur für
    Struktur-/Gate-Count-Ausgaben; Transpiler-Output ist versionsabhängig.
    """
    tqc = transpile(
        circ,
        basis_gates=list(QISKIT_BASIS),
        optimization_level=optimization_level,
        seed_transpiler=7,
    )
    ops = tqc.count_ops()
    return {
        "counts": {str(k): int(v) for k, v in ops.items()},
        "depth": int(tqc.depth()),
        "cx": int(ops.get("cx", 0)),
        "num_qubits": int(tqc.num_qubits),
    }


def error_budget(cx_count, p1, ratio=TWO_Q_RATIO_DEFAULT):
    """Erwartete cx-Fehlerwahrscheinlichkeit pro Shot-Ablauf: cx * ratio * p1.

    Pure Arithmetik — Eingabe für die Phase-3-Prereg-Predictions.
    """
    return float(cx_count) * float(ratio) * float(p1)


@lru_cache(maxsize=1)
def _transpiled_job():
    """Die 12 Layout-Circuits EINMAL transpiliert (gecacht).

    Reihenfolge: [phi_C, phi_D] + sep_C x5 + sep_D x5 — dieselbe Reihenfolge
    wie die Aer-Counts-Auswertung in run_witness.
    """
    layout = witness_job_layout()
    circuits = [layout["phi_C"], layout["phi_D"]] + layout["sep_C"] + layout["sep_D"]
    return [
        transpile(
            circ,
            basis_gates=list(QISKIT_BASIS),
            optimization_level=2,
            seed_transpiler=7,
        )
        for circ in circuits
    ]


# === STRESS-NOISE-MODELL (nicht kalibriert!) ===


def build_noise_model(p1, ro=READOUT_ERROR_DEFAULT, ratio=TWO_Q_RATIO_DEFAULT):
    """STRESS-Noise-Modell: Depolarizing p1 (1q) / ratio*p1 (cx) + Readout ro.

    p1 = 0 -> Readout-only. Kein kalibriertes Fez-Modell; konservativ
    (rz ist auf Hardware virtuell, wird hier aber als 1q-Fehler gezählt).
    """
    p1 = float(p1)
    ro = float(ro)
    ratio = float(ratio)
    if p1 < 0.0:
        raise ValueError(f"p1 muss >= 0 sein, erhalten: {p1}")
    if not 0.0 <= ro <= 0.5:
        raise ValueError(f"ro muss in [0, 0.5] liegen, erhalten: {ro}")
    nm = NoiseModel(basis_gates=list(QISKIT_BASIS))
    if p1 > 0.0:
        nm.add_all_qubit_quantum_error(
            depolarizing_error(p1, 1), ["rz", "sx", "x"]
        )
        nm.add_all_qubit_quantum_error(
            depolarizing_error(ratio * p1, 2), ["cx"]
        )
    nm.add_all_qubit_readout_error(ReadoutError([[1.0 - ro, ro], [ro, 1.0 - ro]]))
    return nm


# === WITNESS AUS COUNTS (Hardware-Äquivalent) ===


def _counts64_to_vec(counts_dict):
    """Aer-Counts (Bitstring-Keys) -> 64-dim COUNTS-Vektor (nicht normiert!).

    int(key, 2) ist der qiskit little-endian Index == Phase-1 logical_index.
    Die Normalisierung machen witness_from_counts/sep_witness_from_counts
    selbst (dort ist die Eingabe ein Counts-Vektor mit Summe = n_shots).
    """
    vec = np.zeros(TWO_DIM)
    for key, c in counts_dict.items():
        vec[int(key, 2)] = float(c)
    return vec


def witness_from_counts(counts_vec, n_boot=_BOOT, seed=9871):
    """v_hat/se/margin aus einem beobachteten DFT-Histogramm (64 Bins).

    Parametrischer Bootstrap um die beobachteten Häufigkeiten (nicht um die
    exakte Verteilung) — exakt das, was Hardware-Daten liefern würden.
    margin = v_hat - 4*SE - WITNESS_BOUND (ENTSCHEIDUNG bleibt dem Prereg
    vorbehalten; margin ist nur eine Reporting-Größe).
    """
    counts_vec = np.asarray(counts_vec, dtype=float)
    n_shots = int(round(counts_vec.sum()))
    p_hat = counts_vec / float(n_shots)
    v_hat = dft_diagonal_weight(p_hat)
    rng = np.random.default_rng(seed)
    boot = rng.multinomial(n_shots, p_hat, size=int(n_boot)) / float(n_shots)
    boot = boot.reshape(int(n_boot), ENC_DIM, ENC_DIM)
    v_boot = np.einsum("nii->n", boot[:, :D5, :D5])
    se = float(np.std(v_boot, ddof=1))
    return {
        "v_hat": float(v_hat),
        "se": se,
        "bound": float(WITNESS_BOUND),
        "margin": float(v_hat - 4.0 * se - WITNESS_BOUND),
        "n_shots": n_shots,
        "n_boot": int(n_boot),
    }


def sep_witness_from_counts(sep_counts_list, n_boot=_BOOT, seed=9872):
    """Witness über die 5 separaten sep-Circuits, EHRlich resampelt.

    Die 5 Komponenten-Histogramme werden als 5 UNABHÄNGige Multinomials
    resampelt und dann gepoolt (nicht: ein Multinomial um das Pooled-
    Histogramm — das würde die Segmentierung der QPU-Statistik fälschlich
    glätten).
    """
    n_list = [int(round(np.asarray(c, dtype=float).sum())) for c in sep_counts_list]
    p_hats = [np.asarray(c, dtype=float) / float(n) for c, n in zip(sep_counts_list, n_list)]
    v_hat = dft_diagonal_weight(sum(p_hats) / float(len(p_hats)))
    rng = np.random.default_rng(seed)
    acc = np.zeros((int(n_boot), TWO_DIM))
    total = 0.0
    for p_hat, n in zip(p_hats, n_list):
        acc += rng.multinomial(n, p_hat, size=int(n_boot))
        total += float(n)
    boot = acc / total
    boot = boot.reshape(int(n_boot), ENC_DIM, ENC_DIM)
    v_boot = np.einsum("nii->n", boot[:, :D5, :D5])
    se = float(np.std(v_boot, ddof=1))
    return {
        "v_hat": float(v_hat),
        "se": se,
        "bound": float(WITNESS_BOUND),
        "margin": float(v_hat - 4.0 * se - WITNESS_BOUND),
        "n_shots": int(total),
        "n_boot": int(n_boot),
    }


# === AER-RUNS ===


def run_witness(p1, n_shots=N_SHOTS_DEFAULT, seed=42,
                ro=READOUT_ERROR_DEFAULT, ratio=TWO_Q_RATIO_DEFAULT):
    """EIN Batch: 12 transpilierte Circuits auf AerSimulator (density_matrix).

    Liefert phi-Witness, sep-Witness und confound_max_diff (max |phi_C/n -
    mean(sep_C)/n| über die 64 Bins) — die §Z.11-Konfund-Kontrolle auf
    Aer-Level, in jeder Run mitgeliefert.
    """
    circuits = _transpiled_job()
    sim = AerSimulator(
        method="density_matrix",
        noise_model=build_noise_model(p1, ro=ro, ratio=ratio),
    )
    result = sim.run(circuits, shots=int(n_shots), seed_simulator=int(seed)).result()
    counts = [result.get_counts(i) for i in range(len(circuits))]
    phi_d = _counts64_to_vec(counts[1])
    sep_c = [_counts64_to_vec(c) for c in counts[2:7]]
    sep_d = [_counts64_to_vec(c) for c in counts[7:12]]
    phi_c = _counts64_to_vec(counts[0])
    # Konfund-Kontrolle auf Wahrscheinlichkeiten: phi_C-Histogramm gegen das
    # Mittel der 5 sep_C-Histogramme (jeweils n_shots Shots, identisch hier).
    p_phi_c = phi_c / float(n_shots)
    p_sep_c = sum(c / float(n_shots) for c in sep_c) / float(len(sep_c))
    return {
        "p1": float(p1),
        "ro": float(ro),
        "ratio": float(ratio),
        "n_shots": int(n_shots),
        "seed": int(seed),
        "phi": witness_from_counts(phi_d),
        "sep": sep_witness_from_counts(sep_d),
        "confound_max_diff": float(np.max(np.abs(p_phi_c - p_sep_c))),
    }


def witness_curve(grid=NOISE_GRID_DEFAULT, n_shots=N_SHOTS_DEFAULT, seed=42,
                  ro=READOUT_ERROR_DEFAULT, ratio=TWO_Q_RATIO_DEFAULT):
    """V über dem p1-Grid (STRESS-Kurve, nicht kalibriert)."""
    grid = tuple(float(p) for p in grid)
    points = [run_witness(p1, n_shots=n_shots, seed=seed, ro=ro, ratio=ratio)
              for p1 in grid]
    return {
        "grid": grid,
        "points": points,
        "model": {
            "type": "stress (not a calibrated Fez model)",
            "readout": float(ro),
            "two_q_ratio": float(ratio),
        },
        "n_shots": int(n_shots),
        "seed": int(seed),
    }


def phase2_report(n_shots=N_SHOTS_DEFAULT, seed=42,
                  grid=NOISE_GRID_DEFAULT, ro=READOUT_ERROR_DEFAULT,
                  ratio=TWO_Q_RATIO_DEFAULT):
    """Gate-Counts + Witness-Kurve + PREREG-DRAFT für Phase 3.

    prereg_draft enthält den Fez-nahen STRESS-Punkt (p1 = 3e-4) als
    Predictions-Grundlage — die Phase-3-Predictions müssen aus Phase 2
    kommen (Anti-Sharpshooter), nicht post-hoc aus Hardware-Daten.
    """
    phi_tc = transpiled_counts(phi_prep_circuit())
    dft_circ = dft_rotation_circuit()
    dft_tc = transpiled_counts(dft_circ)
    full_tc = transpiled_counts(phi_prep_circuit().compose(dft_circ))
    sep_cx = max(transpiled_counts(s)["cx"] for s in sep_prep_circuits())
    curve = witness_curve(grid, n_shots=n_shots, seed=seed, ro=ro, ratio=ratio)
    fez_point = next(pt for pt in curve["points"] if pt["p1"] == 3e-4)
    return {
        "gate_counts": {
            "phi_prep": phi_tc,
            "dft_rotation": dft_tc,
            "phi_D_total": full_tc,
            "sep_C_max_cx": int(sep_cx),
        },
        "curve": curve,
        "prereg_draft": {
            "p1": float(fez_point["p1"]),
            "phi": fez_point["phi"],
            "sep": fez_point["sep"],
            "confound_max_diff": float(fez_point["confound_max_diff"]),
            "decision_rule_candidate": "v_hat - 4*SE > 1/5",
        },
    }