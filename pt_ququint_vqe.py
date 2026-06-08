"""
EXPERIMENT 011 - SÄULE 4: Prime-Qudits GF(5) (Ququint).

Verspricht im Mermaid-Diagramm:
  - GF(5) = endlicher Koerper mit 5 Elementen (Primzahl-Dimension)
  - Keine Nullteiler (im Gegensatz zu GF(4) = 2^2 oder 2-Qubit)
  - Jacobi-A in 5x5-Form (block_diag A_4x4, 0)
  - H_PT_5 = H_diag_5 + i*gamma*A_ququint
  - 36.3% Magic State Distillation Threshold (Campbell et al.)
  - CCZ-Gate in 4 M-Gates statt 7 T-Gates

Diese Implementierung laeuft komplett offline als Simulator. Sie bereitet
die Architektur fuer zukuenftige native Ququint-Hardware (Quantinuum H2)
vor und ermoeglicht den Vergleich 2-Qubit vs 5-Qudit ohne QPU-Run.
"""
import json
import numpy as np
from pt_structural import jacobi_A, E_DIAG

GAMMA = 0.02


# === GF(5) ARITHMETIK ===

def gf5_add(a, b):
    """Addition in GF(5): (a + b) mod 5."""
    return (a + b) % 5


def gf5_mul(a, b):
    """Multiplikation in GF(5): (a * b) mod 5."""
    return (a * b) % 5


def gf5_inverse(a):
    """Multiplikatives Inverses in GF(5). Wirft ZeroDivisionError wenn a=0."""
    if a == 0:
        raise ZeroDivisionError("0 hat kein Inverses in GF(5)")
    for b in range(1, 5):
        if gf5_mul(a, b) == 1:
            return b
    raise ValueError(f"Kein Inverses fuer {a} in GF(5) gefunden")


# === 5x5 JACOBI-ERWEITERUNG ===

def extend_jacobi_to_5x5(A_4):
    """Erweitere 4x4 Jacobi-Matrix auf 5x5: block_diag(A_4, 0).

    Args:
        A_4: 4x4 reell-symmetrische Jacobi-Matrix

    Returns:
        A_5: 5x5 Matrix mit A_4 als oberem Block und einem isolierten 5. Niveau
    """
    A_5 = np.zeros((5, 5))
    A_5[:4, :4] = A_4
    return A_5


# === H_PT_5 KONSTRUKTION ===

def H_PT_ququint(gamma=GAMMA, y=1.0, A_4=None):
    """H_PT_5 = H_diag_5 + i*gamma*A_ququint in 5x5-Form.

    Args:
        gamma: Imaginaer-Kopplungsstaerke
        y: Zeraoulia-Iterationsparameter
        A_4: optional 4x4 Jacobi-Matrix (default: neu berechnet)

    Returns:
        (H_PT_5, A_5, H_diag_5) — komplexe 5x5, reelle 5x5, reelle 5x5
    """
    if A_4 is None:
        A_4 = jacobi_A(E_DIAG, y=y)
    A_5 = extend_jacobi_to_5x5(A_4)
    H_diag_5 = np.diag(np.append(E_DIAG, 5.0)).astype(complex)
    H_PT_5 = H_diag_5 + 1j * gamma * A_5
    return H_PT_5, A_5, H_diag_5


# === MAGIC STATE DISTILLATION THRESHOLD ===

THRESHOLD_QUQUINT = 0.363  # Campbell et al. (2012)
THRESHOLD_QUBIT = 0.01  # Approx. 2-Qubit-Schwelle (~1%)


def threshold_improvement_factor():
    """Faktor-Verbesserung der Magic State Distillation: 36.3% / 1% = 36.3x."""
    return THRESHOLD_QUQUINT / THRESHOLD_QUBIT


# === CCZ-GATE-VERGLEICH ===

CCZ_M_GATES_QUQUINT = 4  # GF(5) braucht 4 M-Gates
CCZ_T_GATES_QUBIT = 7  # 2-Qubit braucht 7 T-Gates


def ccz_gate_reduction_factor():
    """Faktor-Reduktion der Gate-Anzahl fuer CCZ: 7/4 = 1.75."""
    return CCZ_T_GATES_QUBIT / CCZ_M_GATES_QUQUINT


# === PRE-REGISTRIERUNG ===

def precompute_predictions():
    """Berechne H_PT_5-Spektrum + Vergleiche mit 2-Qubit (4x4)."""
    A_4 = jacobi_A(E_DIAG, y=1.0)
    H_PT_5, A_5, H_diag_5 = H_PT_ququint(gamma=GAMMA, A_4=A_4)

    eigs_5 = sorted(np.linalg.eigvals(H_PT_5), key=lambda z: z.real)
    H_PT_4 = np.diag(E_DIAG).astype(complex) + 1j * GAMMA * A_4
    eigs_4 = sorted(np.linalg.eigvals(H_PT_4), key=lambda z: z.real)

    # Konvertiere komplexe Eigenwerte zu JSON-serialisierbaren Tupeln
    eigs_5_json = [{"re": e.real, "im": e.imag} for e in eigs_5]
    eigs_4_json = [{"re": e.real, "im": e.imag} for e in eigs_4]

    return {
        "H_PT_5_eigenvalues": eigs_5_json,
        "H_PT_4_eigenvalues": eigs_4_json,
        "E_DIAG_5": np.append(E_DIAG, 5.0).tolist(),
        "threshold_ququint": THRESHOLD_QUQUINT,
        "threshold_qubit": THRESHOLD_QUBIT,
        "improvement_factor": threshold_improvement_factor(),
        "ccz_M_gates_ququint": CCZ_M_GATES_QUQUINT,
        "ccz_T_gates_qubit": CCZ_T_GATES_QUBIT,
        "ccz_reduction": ccz_gate_reduction_factor(),
        "decision_rule": (
            "CONFIRMED: GF(5) ist bias-invariant, wenn E_n(H_PT_5) fuer n=0..3 "
            "mit E_n(H_PT_4) uebereinstimmt (innerhalb 1e-10). "
            "36.3%-Threshold (Ququint) ist 36x besser als 1% (Qubit). "
            "CCZ in 4 M-Gates statt 7 T-Gates: 1.75x weniger Decoherence."
        )
    }


def main():
    """Hauptfunktion: GF(5)-Architektur-Analyse offline."""
    prereg = precompute_predictions()
    with open("pt_ququint_vqe_prereg.json", "w") as f:
        json.dump(prereg, f, indent=2)
    print(f"Praeregistrierung geschrieben: pt_ququint_vqe_prereg.json")

    # === GF(5)-Verifikation ===
    print("\nGF(5) Arithmetik-Test:")
    print(f"  3 + 4 = {gf5_add(3, 4)}")
    print(f"  3 * 4 = {gf5_mul(3, 4)}")
    print(f"  Inverses von 3: {gf5_inverse(3)}")
    print(f"  Inverses von 2: {gf5_inverse(2)}")

    # === H_PT_5 Eigenwerte ===
    print(f"\nH_PT_5 (5x5) Eigenwerte (Real-Teile):")
    for i, e in enumerate(prereg['H_PT_5_eigenvalues']):
        print(f"  E_{i} = {e['re']:.6f} + {e['im']:.6f}j")

    # === Magic State Distillation Threshold ===
    print(f"\nMagic State Distillation Threshold:")
    print(f"  Ququint (GF(5)): {prereg['threshold_ququint']*100:.1f}%")
    print(f"  2-Qubit:         {prereg['threshold_qubit']*100:.1f}%")
    print(f"  Improvement:     {prereg['improvement_factor']:.1f}x")

    # === CCZ-Gate-Vergleich ===
    print(f"\nCCZ-Gate Anzahl:")
    print(f"  Ququint: {prereg['ccz_M_gates_ququint']} M-Gates")
    print(f"  2-Qubit: {prereg['ccz_T_gates_qubit']} T-Gates")
    print(f"  Reduktion: {prereg['ccz_reduction']:.2f}x")

    # === Speichern ===
    output = {
        "predictions": prereg,
        "gf5_verification": {
            "3_plus_4": gf5_add(3, 4),
            "3_times_4": gf5_mul(3, 4),
            "inverse_3": gf5_inverse(3),
            "inverse_2": gf5_inverse(2)
        }
    }
    with open("pt_ququint_vqe_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nErgebnisse gespeichert: pt_ququint_vqe_results.json")


if __name__ == "__main__":
    main()
