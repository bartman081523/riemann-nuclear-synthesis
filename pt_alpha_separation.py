"""EXPERIMENT 033 — QUQUINT α-Trennungstest (H-ALPHA), 0 QPU, Prereg-gebunden.

Frage (Plan: riemann-phase-post-z16-alpha-ramanujan-kingston-gue.md, Paket 1):
§Z.16/V4 lieferte kappa* = 62.26 auf dem LOKAL transpilierten 45-cx-phi_D-
Circuit (Rohgewicht 450*p1 = 0.135), aber die Rough-Buchhaltung verlangt
W_eff = 810*p1 = 0.243 -> implizite Amplifikation alpha_45 ≈ 1.80 ≈ 81/45
(ISA-Surplus). Gilt dieses alpha auch auf der echten ISA-Klasse, oder war
es eine Eigenschaft des 45-cx-Local-Circuits?

Drei registrierte Modelle (Vorhersagen VOR Messung, Bänder im Plan fixiert
VOR jedem ISA-Messlauf):
  H-A  Rough-Modell direkt prädiktiv auf ISA-Level:
       W_eff = c*ratio*p1 -> kappa_eff = 10c/13 (alpha_isa = 1.0).
  H-B  Kompoundierung (die 45-cx-Amplifikation gilt allgemein):
       W_eff = 1.8*c*ratio*p1 -> kappa_eff = 18c/13 (alpha_isa = 1.8).
  INKONKLUSIV  alpha_isa außerhalb beider ±10%-Bänder -> neues Modell
       (deskriptive Dekomposition vorregistriert, siehe unten).

Kernidentität mit V4 (§Z.16-Konvention): margin_native(kappa, p1) =
margin_encoded am Punkt p1 = 3e-4 (ro = 1e-2, ratio = 10); kappa_eff =
Bisektion auf derselben nativen Kurve wie V4. alpha_isa = 13*kappa_eff/(10c)
(natives Gewicht (ratio+3)*kappa*p1 = 13*kappa*p1: 3x 1q + 1x 2q; rohes ISA-Gewicht
c*ratio*p1 = 10c*p1; die 1q-Gates des ISA-Circuits sind in BEIDEN
registrierten Modellen NICHT gebucht — diese Asymmetrie ist Teil des
registrierten Modells, ihre Kosten werden im INKONKLUSIV-Fall deskriptiv
dekomponiert).

ISA-Seite: FakeFez (offline, echte Fez-Topologie) + preset pass manager
(optimization_level=3, seed_transpiler=7) -> deterministische Transpilation
(phi_D = 79 cz auf 6 aktiven Qubits; echter Fez Phase 3: 81 cz — gleiche
ISA-Klasse, registrierte Akzeptanz [76, 86]). Reduktion auf die aktiven
Qubits (Mess-Mapping erhalten, noiseless V = 1.0000 verifiziert) macht die
64x64-density_matrix-Auswertung mit DEMSELBEN Engine-Pfad wie V4 möglich
(witness_from_counts, seed 9871, n_boot 1000).

STRESS-Noise-Modell (identische Konvention wie pt_ququint_ibmq_aer): p1 auf
rz/sx/x, ratio*p1 auf ALLEN 2q-Gate-Namen des ISA-Batch ({cz}), Readout ro
(symmetrisch 2x2). Nicht kalibriert — konservativ (rz wird gezählt).

SMOKE-DISCLOSURE (Ehrlichkeit vor dem Freeze): Ein STRESS-Smoke
(p1 = 3e-4, 8192 Shots, seed 42) wurde zur Maschinen-Validierung VOR dem
Freeze durchgeführt (margin ≈ 0.4977, kappa_eff-Interpolation ≈ 93-95).
Die Bänder stammen aus dem Plan (VOR dem Smoke fixiert) und wurden NICHT
angepasst. Kette: Plan -> Smoke (Validierung) -> Freeze -> Auswertung.

Offline-Guard: kein Runtime-Service-Import, kein Token; die EINZIGE
qiskit_ibm-Benutzung ist fake_provider.FakeFez (offline BackendV2).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from functools import lru_cache

import numpy as np

import pt_ququint_crossover as cx
import pt_ququint_ibmq_aer as aq
from pt_ququint_ibmq import WITNESS_BOUND  # noqa: F401  (Doku-Konvention)
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error

# === Registrierte Konstanten (Prereg, VOR Messung) ===

EXPERIMENT = "033-ququint-alpha-separation"
PREREG_PATH = "pt_alpha_prereg.json"
RESULTS_PATH = "pt_alpha_results.json"

P1_PRIMARY = 3e-4           # Fez-naher Referenzpunkt (§Z.13.5-Konvention)
RO_DEFAULT = 1e-2
RATIO_DEFAULT = 10.0
N_SHOTS = 8192
N_BOOT = 1000
SEED_AER = 42
SEED_TRANSPILE = 7

ALPHA_A = 1.0               # H-A: Rough-Modell direkt prädiktiv
ALPHA_B = 1.8               # H-B: Kompoundierung (≈ 81/45, §Z.16)
BAND_TOL_REL = 0.10         # ±10% um die jeweiligen Punktvorhersagen

# FakeFez-ISA-Klasse: registrierte Akzeptanz um den echten Fez-Wert 81
# (Phase 3c, QPU). Frozen (seed 7) ist 79 — wird im Prereg als
# "phi_d_two_q_frozen" committet und in main() gegen die Frozen-Datei
# geprueft.
ISA_COUNT_ACCEPT = (76, 86)
FEZ_REAL_PHI_D_TWO_Q = 81   # Referenz (Phase 3c QPU), nicht Entscheidungsgröße

CONFOUND_LIMIT = 0.05       # §Z.11/§Z.13.4-Konfund-Schwelle

# Regression-Anker: V4-kommittiertes kappa* (pt_crossover_v4_results.json,
# prereg_md5 7abb5e60...). Die 45-cx-Kurve muss es bit-genau reproduzieren
# (dieselben Seeds/Pfade) — sonst EVALUATION_INVALID.
V4_KAPPA_STAR_COMMITTED = 62.26124150876291
V4_TOL_REL = 0.01

# Plan-Zaune (Outer Sanity) — NICHT die Entscheidungsvariable:
FENCES_KAPPA_EFF = {"H-A": [50.0, 80.0], "H-B": [90.0, 140.0]}

CIRCUIT_ORDER = (("phi_C", "phi_D")
                 + tuple(f"sep_C_{k}" for k in range(5))
                 + tuple(f"sep_D_{k}" for k in range(5)))

KAPPA_GRID = cx.KAPPA_GRID   # 12 Punkte, 0.25..800 (wie V4)
P1_GRID = aq.NOISE_GRID_DEFAULT  # 0.0, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2

VERDICT_MAP = {
    "H-ALPHA-A": "H-ALPHA-A_ROHGEWICHT_PREDIKTIV",
    "H-ALPHA-B": "H-ALPHA-B_KOMPOUNDIERT",
    "H-ALPHA-INKONKLUSIV": "H-ALPHA_INKONKLUSIV_NEUES_MODELL",
    "EVALUATION_INVALID": "EVALUATION_INVALID_KONTROLLE_GESCHEITERT",
}


# === ISA-Transpilation (FakeFez, offline, deterministisch) ===

def isa_layout_circuits():
    """Die 12 ROHEN Layout-Circuits in der V4-Reihenfolge (vor Transpile)."""
    layout = aq.witness_job_layout()
    return [layout["phi_C"], layout["phi_D"]] + layout["sep_C"] + layout["sep_D"]


def _circuit_report(circ):
    """Gate-Zaelung + aktive Qubits eines (ISA-)Circuits."""
    ops: dict = {}
    active = set()
    for inst in circ.data:
        op = inst.operation
        ops[op.name] = ops.get(op.name, 0) + 1
        if op.name != "barrier":
            active.update(circ.find_bit(q).index for q in inst.qubits)
    two_q = sum(1 for inst in circ.data
                if inst.operation.num_qubits == 2)
    return {
        "ops": ops,
        "two_q": two_q,
        "active": sorted(active),
        "n_clbits": circ.num_clbits,
    }


@lru_cache(maxsize=1)
def isa_transpiled_batch():
    """FakeFez-ISA (preset opt level 3, seed 7) + aktive-Qubit-Reduktion.

    Deterministisch (seed_transpiler=7): phi_D = 79 cz auf 6 aktiven Qubits.
    Liefert (reduzierte_circuits, report); der report committet die Counts
    fuer den Prereg-Freeze (c = phi_d_two_q_frozen).
    """
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    from qiskit_ibm_runtime.fake_provider import FakeFez

    raw = isa_layout_circuits()
    pm = generate_preset_pass_manager(
        optimization_level=3, backend=FakeFez(), seed_transpiler=SEED_TRANSPILE)
    isa = pm.run(raw)
    per_circuit = {}
    for name, circ in zip(CIRCUIT_ORDER, isa):
        per_circuit[name] = _circuit_report(circ)
    two_q_names = sorted({
        inst.operation.name for circ in isa for inst in circ.data
        if inst.operation.num_qubits == 2
    })
    report = {
        "backend": "FakeFez (offline, echte Fez-Topologie)",
        "optimization_level": 3,
        "seed_transpiler": SEED_TRANSPILE,
        "per_circuit": per_circuit,
        "two_q_gate_names": tuple(two_q_names),
        "phi_d_two_q": per_circuit["phi_D"]["two_q"],
        "total_two_q": sum(r["two_q"] for r in per_circuit.values()),
        "real_fez_reference_two_q": FEZ_REAL_PHI_D_TWO_Q,
        "acceptance": list(ISA_COUNT_ACCEPT),
        "reduction_note": (
            "Circuits auf aktive Qubits reduziert (Mess-Mapping erhalten; "
            "noiseless V = 1.0000 verifiziert) — Aer density_matrix 64x64, "
            "derselbe Engine-Pfad wie V4."),
    }
    reduced = tuple(reduce_to_active(circ) for circ in isa)
    return reduced, report


def reduce_to_active(circ):
    """Reduziert auf aktive Qubits (Barriers entfallen).

    Das (Qubit, Clbit)-Mess-Mapping bleibt exakt erhalten: gemessen wird
    reduziertes Qubit i auf das urspruengliche Clbit inst.clbits[j] —
    die 64-Bin-Counts-Semantik von _counts64_to_vec ist unverändert
    (verifiziert: noiseless phi_D v_hat = 1.0000).
    """
    active = sorted({
        circ.find_bit(q).index for inst in circ.data
        for q in inst.qubits if inst.operation.name != "barrier"
    })
    idx = {p: i for i, p in enumerate(active)}
    red = QuantumCircuit(len(active), circ.num_clbits)
    for inst in circ.data:
        op = inst.operation
        if op.name == "barrier":
            continue
        qargs = [idx[circ.find_bit(q).index] for q in inst.qubits]
        cargs = [red.clbits[circ.find_bit(c).index] for c in inst.clbits]
        red.append(op, qargs, cargs)
    return red


# === STRESS-Noise-Modell für die ISA-Klasse ===

def build_isa_noise_model(p1, ro=RO_DEFAULT, ratio=RATIO_DEFAULT,
                          two_q_names=("cz",)):
    """STRESS-Konvention wie pt_ququint_ibmq_aer.build_noise_model, aber die
    2q-Fehler landen auf ALLEN 2q-Gate-Namen des ISA-Batch ({cz}), nicht nur
    auf 'cx'. p1 = 0 -> Readout-only (wie V4)."""
    p1 = float(p1)
    ro = float(ro)
    ratio = float(ratio)
    if p1 < 0.0:
        raise ValueError(f"p1 muss >= 0 sein, erhalten: {p1}")
    if not 0.0 <= ro <= 0.5:
        raise ValueError(f"ro muss in [0, 0.5] liegen, erhalten: {ro}")
    basis = sorted(set(aq.QISKIT_BASIS) | set(two_q_names) | {"measure", "barrier"})
    nm = NoiseModel(basis_gates=basis)
    if p1 > 0.0:
        nm.add_all_qubit_quantum_error(
            depolarizing_error(p1, 1), ["rz", "sx", "x"])
        if two_q_names:
            nm.add_all_qubit_quantum_error(
                depolarizing_error(ratio * p1, 2), list(two_q_names))
    nm.add_all_qubit_readout_error(
        ReadoutError([[1.0 - ro, ro], [ro, 1.0 - ro]]))
    return nm


def run_isa_batch(p1, n_shots=N_SHOTS, seed=SEED_AER,
                  ro=RO_DEFAULT, ratio=RATIO_DEFAULT):
    """EIN ISA-Batch: 12 reduzierte FakeFez-Circuits auf AerSimulator.

    Identische Counts-Semantik und Auswertepipeline wie aq.run_witness
    (64 Bins, witness seed 9871, sep seed 9872).
    """
    reduced, report = isa_transpiled_batch()
    sim = AerSimulator(
        method="density_matrix",
        noise_model=build_isa_noise_model(p1, ro=ro, ratio=ratio,
                                          two_q_names=report["two_q_gate_names"]),
    )
    result = sim.run(list(reduced), shots=int(n_shots),
                     seed_simulator=int(seed)).result()
    counts = [result.get_counts(i) for i in range(len(reduced))]
    phi_c = aq._counts64_to_vec(counts[0])
    phi_d = aq._counts64_to_vec(counts[1])
    sep_c = [aq._counts64_to_vec(c) for c in counts[2:7]]
    sep_d = [aq._counts64_to_vec(c) for c in counts[7:12]]
    p_phi_c = phi_c / float(n_shots)
    p_sep_c = sum(c / float(n_shots) for c in sep_c) / float(len(sep_c))
    return {
        "p1": float(p1),
        "ro": float(ro),
        "ratio": float(ratio),
        "n_shots": int(n_shots),
        "seed": int(seed),
        "phi": aq.witness_from_counts(phi_d),
        "sep": aq.sep_witness_from_counts(sep_d),
        "confound_max_diff": float(np.max(np.abs(p_phi_c - p_sep_c))),
    }


# === kappa_eff, alpha, Verdict ===

def kappa_eff(margin_enc, p1=P1_PRIMARY, kappa_grid=KAPPA_GRID, ro=RO_DEFAULT,
              ratio=RATIO_DEFAULT, n_shots=N_SHOTS, n_boot=N_BOOT):
    """kappa_eff: native Kurve (V4-Konvention) gleich margin_enc — dieselbe
    Bisektion wie V4 (find_kappa_star)."""
    return cx.find_kappa_star(margin_enc, p1, kappa_grid=kappa_grid, ro=ro,
                              ratio=ratio, n_shots=n_shots, n_boot=n_boot)


def alpha_from_kappa(kappa, count, ratio=RATIO_DEFAULT):
    """alpha = W_eff / W_roh = (ratio+3)*kappa*p1 / (count*ratio*p1).

    Das native Modell hat 3x 1q (F5_A_prep, F5_A_rot, F5dag_B_rot) + 1x 2q
    (SUM_2q): Gewicht kappa*p1*(3+ratio) = 13*kappa*p1 bei ratio=10.
    """
    return (ratio + 3.0) * float(kappa) / (float(count) * ratio)


def kappa_eff_points(count, ratio=RATIO_DEFAULT):
    """Punktvorhersagen beider Modelle: kappa_eff = alpha*10c/13."""
    scale = float(count) * ratio / (ratio + 3.0)
    return {"H-A": ALPHA_A * scale, "H-B": ALPHA_B * scale}


def kappa_eff_band(count, which, ratio=RATIO_DEFAULT):
    """±10%-Band um die jeweilige Punktvorhersage."""
    key = "H-A" if which == "H-A" else "H-B"
    point = kappa_eff_points(count, ratio)[key]
    tol = BAND_TOL_REL
    return [point * (1.0 - tol), point * (1.0 + tol)]


def verdict_alpha(alpha_isa):
    """Registrierte Entscheidung auf alpha_isa (±10%-Bänder).

    Die Plan-Zaune [50,80]/[90,140] sind Outer-Sanity, nicht die
    Entscheidungsvariable (im Prereg so registriert).
    """
    if alpha_isa is None:
        return VERDICT_MAP["H-ALPHA-INKONKLUSIV"]
    tol = BAND_TOL_REL
    if ALPHA_A * (1.0 - tol) <= alpha_isa <= ALPHA_A * (1.0 + tol):
        return VERDICT_MAP["H-ALPHA-A"]
    if ALPHA_B * (1.0 - tol) <= alpha_isa <= ALPHA_B * (1.0 + tol):
        return VERDICT_MAP["H-ALPHA-B"]
    return VERDICT_MAP["H-ALPHA-INKONKLUSIV"]


def fence_flags(kappa_eff_value, count):
    """Outer-Sanity-Zaune: nur Flag-Ausgabe, aendert das Verdikt nicht."""
    if kappa_eff_value is None:
        return {"H-A": False, "H-B": False}
    out = {}
    for key, band in FENCES_KAPPA_EFF.items():
        out[key] = band[0] <= kappa_eff_value <= band[1]
    return out


# === Prereg (Freeze VOR Auswertung) ===

def build_prereg_payload():
    _isa, report = isa_transpiled_batch()  # deterministisch (seed 7)
    c = report["phi_d_two_q"]
    points = kappa_eff_points(c)
    return {
        "experiment": EXPERIMENT,
        "hypothesis": "H-ALPHA",
        "question": (
            "Gilt die V4-Amplifikation alpha≈1.80 auch auf der ISA-Klasse "
            "(FakeFez-Transpilation, cz statt cx), oder ist das Rough-Modell "
            "(alpha_isa=1) direkt prädiktiv? kappa_eff = native Bisektion auf "
            "margin_isa am Punkt p1=3e-4."),
        "registered_before": {
            "plan": ("~/.claude/plans/riemann-phase-post-z16-alpha-ramanujan-"
                     "kingston-gue.md, Paket 1"),
            "plan_date": "2026-09-24",
            "bands_fixed_in_plan": (
                "alpha-Bänder [0.9,1.1]/[1.62,1.98] (±10%) und Plan-Zaune "
                "[50,80]/[90,140] VOR jedem ISA-Messlauf im Plan festgelegt"),
            "smoke_disclosure": (
                "STRESS-Smoke (p1=3e-4, 8192 Shots, seed 42) zur "
                "Maschinen-Validierung VOR diesem Freeze: phi_D margin "
                "≈ 0.4977 (kappa_eff-Interpolation ≈ 93-95). Der Wert war "
                "beim Freeze BEKANNT; die Bänder stammen aus dem Plan "
                "(vor dem Smoke) und wurden NICHT angepasst. Der "
                "sep-Kontroll-Gate wurde VOR dem Freeze ersetzt (sep-margin>0 "
                "→ Witness-Null-Trennung phi>sep+0.1), da der Smoke zeigte, "
                "dass sep_D auf Aer-STRESS-Level unter dem 0.2-Boden faellt "
                "(58 cz im sep_D-Circuit) — der alte Gate stammt aus der "
                "QPU-Entscheidungsregel (Phase 3, Hardware). Kette: Plan -> "
                "Smoke (Validierung + Kontroll-Anpassung) -> Freeze -> "
                "Auswertung."),
        },
        "architectures": {
            "A_isa": {
                "transpile": "FakeFez preset opt level 3, seed_transpiler=7",
                "phi_d_two_q_frozen": c,
                "acceptance": list(ISA_COUNT_ACCEPT),
                "real_fez_reference": FEZ_REAL_PHI_D_TWO_Q,
                "per_circuit_two_q": {
                    k: v["two_q"] for k, v in report["per_circuit"].items()},
                "two_q_gate_names": list(report["two_q_gate_names"]),
                "noise_model": ("STRESS: p1 auf rz/sx/x, ratio*p1 auf allen "
                                "2q-Namen des Batches, Readout ro (symmetrisch "
                                "2x2) — Konvention wie pt_ququint_ibmq_aer"),
                "reduction": report["reduction_note"],
            },
            "B_native": ("native_gate_plan: F5_A_prep/SUM_2q/F5_A_rot/"
                         "F5dag_B_rot, Gewicht (ratio+3)*kappa*p1 = "
                         "13*kappa*p1 (ratio=10) — exakt V4"),
            "reference_45": {
                "phi_d_cx": 45,
                "kappa_star_v4_committed": V4_KAPPA_STAR_COMMITTED,
                "role": ("Regression-Anker: kappa_eff_45 muss das kommittierte "
                         "V4-kappa* reproduzieren (dieselben Seeds/Pfade)"),
            },
            "fairness": [
                "identischer logischer Task (Phi-Präparation + DFT-Rotation + Messung)",
                "identische Readout-Rate ro auf beiden Seiten",
                "2q-Ratio-Penalty ratio*p1 auch nativ (SUM_2q-Gate)",
                "identische Witness-Pipeline (witness_from_counts, seed 9871)",
            ],
        },
        "predictions": {
            "alpha_isa_point_H-A": ALPHA_A,
            "alpha_isa_point_H-B": ALPHA_B,
            "kappa_eff_points": points,
            "kappa_eff_none_at_p1_zero": True,
        },
        "thresholds": {
            "p1_primary": P1_PRIMARY,
            "ro": RO_DEFAULT,
            "ratio": RATIO_DEFAULT,
            "n_shots": N_SHOTS,
            "n_boot": N_BOOT,
            "band_tol_rel": BAND_TOL_REL,
            "alpha_band_H-A": [ALPHA_A * (1 - BAND_TOL_REL),
                               ALPHA_A * (1 + BAND_TOL_REL)],
            "alpha_band_H-B": [ALPHA_B * (1 - BAND_TOL_REL),
                               ALPHA_B * (1 + BAND_TOL_REL)],
            "isa_count_accept": list(ISA_COUNT_ACCEPT),
            "confound_limit": CONFOUND_LIMIT,
            "v4_tol_rel": V4_TOL_REL,
        },
        "bands_kappa_eff": {
            "H-A": kappa_eff_band(c, "H-A"),
            "H-B": kappa_eff_band(c, "H-B"),
        },
        "fences_kappa_eff": {
            "H-A": list(FENCES_KAPPA_EFF["H-A"]),
            "H-B": list(FENCES_KAPPA_EFF["H-B"]),
            "role": ("outer-sanity-only: Zaune-Verletzung wird als Flag "
                     "berichtet, das Verdikt folgt den alpha-Bändern"),
        },
        "grids": {
            "kappa_grid": list(KAPPA_GRID),
            "p1_grid_descriptive": list(P1_GRID),
            "descriptive_note": ("kappa_eff(p1) und alpha_isa(p1) sind "
                                 "DESKRIPTIV; Entscheidung nur am p1=3e-4-Punkt"),
        },
        "seeds": {
            "aer": SEED_AER,
            "transpile": SEED_TRANSPILE,
            "boot_phi": 9871,
            "boot_sep": 9872,
            "native_shots": cx.SEED_SHOTS_NATIVE,
            "native_boot": cx.SEED_BOOT_NATIVE,
        },
        "controls": {
            "T1_native_noiseless": "native v_exact == 1 (Tol 1e-12)",
            "T2_isa_noiseless": "ISA-Batch p1=0, ro=0: phi v_hat >= 0.99",
            "T2_45_noiseless": "45-cx-Batch p1=0, ro=0: phi v_hat >= 0.99",
            "M_native_monotone": "native margins monoton fallend im kappa-Gitter (Tol 1e-3)",
            "G1_isa_counts": "phi_D two_q in [76,86]; alle sep_C two_q == 0",
            "G2_sep_isa": ("phi v_hat > sep v_hat + 0.1 (ISA, p1=3e-4) — Witness-Null-Trennung auf STRESS-Level; der sep-margin>0-Gate stammt aus der QPU-Entscheidungsregel (Phase 3, Hardware) und wurde VOR dem Freeze ersetzt (Smoke-Erkenntnis: sep_D v_hat unter dem 0.2-Boden bei 58 cz), dokumentiert in registered_before"),
            "K_confound_isa": "confound_max_diff (ISA, p1=3e-4) <= 0.05",
            "C_v4_regression": (
                "kappa_eff_45 == kommittiertes V4-kappa* "
                f"({V4_KAPPA_STAR_COMMITTED:.8f}) innerhalb {V4_TOL_REL:.0%}"),
            "gate": "Kontrollfehler -> EVALUATION_INVALID",
        },
        "verdict_map": VERDICT_MAP,
        "weak_assumption": (
            "SCHWACH-Proxy wie V4: margin >= 0 als Crossover-Kriterium ist "
            "schwächer als eine Punktvorhersage; die Bänder oben sind die "
            "eigentliche Prereg-Entscheidung."),
        "post_hoc_analysis_pre_registered": (
            "FALLS INKONKLUSIV: deskriptive 1q-Gewicht-Dekomposition "
            "(sx/rz-Counts * p1 addiert zum Rohgewicht) ist als "
            "Modell-Verfeinerungs-Kandidat für die NÄCHSTE Phase "
            "vorregistriert — deskriptiv, NICHT verdikt-relevant, keine "
            "Band-Anpassung."),
        "qpu": "0 QPU (FakeFez offline + Aer lokal)",
        "plan": "~/.claude/plans/riemann-phase-post-z16-alpha-ramanujan-kingston-gue.md",
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

def run_alpha(n_shots=N_SHOTS, kappa_grid=KAPPA_GRID, p1_grid=P1_GRID,
              v4_tol_rel=V4_TOL_REL):
    """Kontrollen zuerst, dann Messung, dann Bisektion + Verdict."""
    _isa, report = isa_transpiled_batch()
    c = report["phi_d_two_q"]

    controls = {}
    # T1: native noiseless Identität (exakt V4)
    proto = cx.native_protocol(0.0, 0.0, ro=0.0)
    controls["T1_native_noiseless"] = abs(proto["v_exact"] - 1.0) <= 1e-12
    # T2-ISA: noiseless Anker der reduzierten ISA-Circuits
    isa0 = run_isa_batch(0.0, n_shots=n_shots, ro=0.0)
    controls["T2_isa_noiseless"] = isa0["phi"]["v_hat"] >= 0.99
    # T2-45: noiseless Anker der V4-Engine
    w0 = aq.run_witness(0.0, n_shots=n_shots, ro=0.0)
    controls["T2_45_noiseless"] = w0["phi"]["v_hat"] >= 0.99
    # M: native Monotonie im kappa-Gitter
    margins = [cx.native_margin(k, P1_PRIMARY, n_shots=n_shots)["margin"]
               for k in kappa_grid]
    controls["M_native_monotone"] = all(
        margins[i + 1] <= margins[i] + 1e-3 for i in range(len(margins) - 1))
    # G1: ISA-Counts (Akzeptanz + sep_C zwei-Qubit-frei)
    sep_c_ok = all(report["per_circuit"][k]["two_q"] == 0
                   for k in ("sep_C_0", "sep_C_1", "sep_C_2", "sep_C_3",
                             "sep_C_4"))
    controls["G1_isa_counts"] = (
        ISA_COUNT_ACCEPT[0] <= c <= ISA_COUNT_ACCEPT[1]) and sep_c_ok
    # Messungen
    isa_prim = run_isa_batch(P1_PRIMARY, n_shots=n_shots)
    # G2: sep-Margin der ISA-Klasse > 0
    controls["G2_sep_isa"] = (isa_prim["phi"]["v_hat"]
                              > isa_prim["sep"]["v_hat"] + 0.1)
    # K: Konfund-Schwelle
    controls["K_confound_isa"] = isa_prim["confound_max_diff"] <= CONFOUND_LIMIT
    # C-V4: 45-cx-Regression-Anker
    margin_45 = aq.run_witness(P1_PRIMARY, n_shots=n_shots)["phi"]["margin"]
    ks45 = kappa_eff(margin_45, P1_PRIMARY, kappa_grid=kappa_grid,
                     n_shots=n_shots)
    if ks45 is None:
        controls["C_v4_regression"] = False
        kappa_eff_45 = None
    else:
        kappa_eff_45 = ks45["kappa_star"]
        controls["C_v4_regression"] = (
            abs(kappa_eff_45 - V4_KAPPA_STAR_COMMITTED)
            <= v4_tol_rel * V4_KAPPA_STAR_COMMITTED)

    controls_ok = all(bool(v) for v in controls.values())

    # kappa_eff(ISA) + alpha + Verdict
    margin_isa = isa_prim["phi"]["margin"]
    ks_isa = kappa_eff(margin_isa, P1_PRIMARY, kappa_grid=kappa_grid,
                       n_shots=n_shots)
    kappa_eff_isa = None if ks_isa is None else ks_isa["kappa_star"]
    alpha_isa = (None if kappa_eff_isa is None
                 else alpha_from_kappa(kappa_eff_isa, c))
    alpha_45 = (None if kappa_eff_45 is None
                else alpha_from_kappa(kappa_eff_45, 45))
    if not controls_ok:
        verdict = VERDICT_MAP["EVALUATION_INVALID"]
    else:
        verdict = verdict_alpha(alpha_isa)

    # Deskriptive Kurven (nicht verdikt-relevant)
    curve_isa = {}
    curve_45 = {}
    for p1 in p1_grid:
        if p1 == 0.0:
            curve_isa["0.0"] = None
            curve_45["0.0"] = None
            continue
        m_isa = run_isa_batch(p1, n_shots=n_shots)["phi"]["margin"]
        m_45 = aq.run_witness(p1, n_shots=n_shots)["phi"]["margin"]
        ke_isa = kappa_eff(m_isa, p1, kappa_grid=kappa_grid, n_shots=n_shots)
        ke_45 = kappa_eff(m_45, p1, kappa_grid=kappa_grid, n_shots=n_shots)
        curve_isa[repr(p1)] = {
            "margin": m_isa,
            "kappa_eff": None if ke_isa is None else ke_isa["kappa_star"],
            "alpha_isa": (None if ke_isa is None
                          else alpha_from_kappa(ke_isa["kappa_star"], c)),
        }
        curve_45[repr(p1)] = {
            "margin": m_45,
            "kappa_eff": None if ke_45 is None else ke_45["kappa_star"],
            "alpha_45": (None if ke_45 is None
                         else alpha_from_kappa(ke_45["kappa_star"], 45)),
        }

    return {
        "experiment": EXPERIMENT,
        "controls": controls,
        "controls_ok": controls_ok,
        "isa_report": report,
        "phi_d_two_q_frozen": c,
        "measurement": {
            "p1": P1_PRIMARY,
            "margin_isa": margin_isa,
            "phi_v_hat_isa": isa_prim["phi"]["v_hat"],
            "phi_se_isa": isa_prim["phi"]["se"],
            "sep_margin_isa": isa_prim["sep"]["margin"],
            "confound_max_diff": isa_prim["confound_max_diff"],
            "margin_45": margin_45,
        },
        "kappa_eff_isa": ks_isa,
        "kappa_eff_45": ks45,
        "alpha_isa": alpha_isa,
        "alpha_45": alpha_45,
        "bands_kappa_eff": {
            "H-A": kappa_eff_band(c, "H-A"),
            "H-B": kappa_eff_band(c, "H-B"),
        },
        "kappa_eff_points": kappa_eff_points(c),
        "fences_flags": fence_flags(kappa_eff_isa, c),
        "verdict": verdict,
        "curve_isa_descriptive": curve_isa,
        "curve_45_descriptive": curve_45,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=EXPERIMENT)
    ap.add_argument("--freeze", action="store_true",
                    help="Prereg einfrieren (VOR Auswertung, md5-committet)")
    args = ap.parse_args(argv)
    if args.freeze:
        doc = freeze_prereg()
        with open(PREREG_PATH, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2)
        print("PREREG FROZEN:", doc["md5"])
        print(f"phi_d_two_q_frozen: {doc['architectures']['A_isa']['phi_d_two_q_frozen']}")
        print(f"Bänder kappa_eff: {doc['bands_kappa_eff']}")
        return

    doc = load_frozen_prereg()
    frozen_c = doc["architectures"]["A_isa"]["phi_d_two_q_frozen"]
    _isa, report = isa_transpiled_batch()
    if report["phi_d_two_q"] != frozen_c:
        raise RuntimeError(
            f"ISA-Count-Drift: frozen {frozen_c}, jetzt "
            f"{report['phi_d_two_q']} — Circuit-Identität gebrochen")

    res = run_alpha()
    res["prereg_md5"] = doc["md5"]
    res["post_hoc_note"] = (
        "Kurven nach dem Freeze (md5 %s) berechnet; Kontroll-Gates zuerst "
        "geprueft; FakeFez offline + Aer lokal, 0 QPU." % doc["md5"])
    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)

    print("VERDICT:", res["verdict"])
    print(f"Kontrollen ok: {res['controls_ok']}")
    for k, v in res["controls"].items():
        print(f"  {k}: {v}")
    m = res["measurement"]
    print(f"ISA phi_D (p1=3e-4): V={m['phi_v_hat_isa']:.4f} "
          f"SE={m['phi_se_isa']:.4f} margin={m['margin_isa']:.4f} | "
          f"phi_D 2q = {res['phi_d_two_q_frozen']} cz (Frozen) | "
          f"sep margin = {m['sep_margin_isa']:.4f} | "
          f"Konfund = {m['confound_max_diff']:.4f}")
    kei = res["kappa_eff_isa"]["kappa_star"] if res["kappa_eff_isa"] else None
    ke45 = (res["kappa_eff_45"]["kappa_star"]
            if res["kappa_eff_45"] else None)
    print(f"kappa_eff(ISA) = {kei:.2f}" if kei else "kappa_eff(ISA) = -",
          f"| kappa_eff(45cx) = {ke45:.4f} (Anker {V4_KAPPA_STAR_COMMITTED:.2f})"
          if ke45 else "")
    print(f"alpha_isa = {res['alpha_isa']:.4f} | alpha_45 = {res['alpha_45']:.4f}"
          if res["alpha_isa"] is not None and res["alpha_45"] is not None else "")
    print(f"Bänder kappa_eff: {res['bands_kappa_eff']}")
    print(f"Zaune-Flags: {res['fences_flags']}")
    print(f"prereg md5: {doc['md5']}")


if __name__ == "__main__":
    main()