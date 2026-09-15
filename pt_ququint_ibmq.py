"""
EXPERIMENT 030 - Ququint auf IBMQ, Phase 1: 3-Qubit-Emulation + Weyl-Witness
(numpy-only, statevector/density-matrix, KEINE QPU-Kosten).

Fragestellung (User): "Können wir die Vorteile von Ququint auf IBMQ bringen —
die statistisch saubere Ququint-Architektur läuft auf IBMQ?"

Fundamentale Einschränkung: IBMQ exponiert über die öffentliche API nur Qubits
(2 Level). Die Transmon-Niveaus |2>,|3>,|4> eines echten Ququint sind nicht
ansteuerbar. Der saubere Weg ist EMULATION: ein Ququint wird in einen
3-Qubit-Registert kodiert (8 dim, 5 logische Zustände 000..100, 3 Leakage-
Zustände 101/110/111, die verworfen werden — Rejection-Rate wird gemeldet).

Struktur (Level-Trennung, im Geist von §Z.10/§Z.11):

  Logische Ebene (25 dim, §Z.11):  pt_ququint_entanglement (Schmidt,
      Concurrence, Negativity, Konfund) — unangetastet.
  Emulations-Ebene (64 dim):       DIESES Modul — Encoding, encoded
      Operatoren, Messungssimulation, Witness, Shots, Leakage-Rejection.

Encoded Operatoren (gegen die kernel-verifizierte Schicht geprüft, §Z.10):
  - x5_encoded: 8x8-Permutation, 5-Zyklus auf {0..4}, Fixpunkte auf Leakage
  - z5_encoded: diag(1, omega, ..., omega^4, 1, 1, 1), omega = exp(2 pi i/5)
  - dft5_encoded: DFT-5 im logischen Block, Identität auf Leakage

STRUKTURFUND (getestet, nicht versteckt): die GF(5)-Weyl-Relation
Z X = omega X Z gilt im 8-dim Encoded-Raum NUR auf dem logischen Subraum.
Auf Leakage-Zuständen bricht sie zwingend (X hat dort Fixpunkte oder
3-Zyklen; eine Ordnung-5-Phasen-Struktur kann dort nicht existieren —
die Relation verlangt Orbits der Länge 5 unter X bei Phasenfortschritt
omega). Emulation ist algebra-treu auf dem CODE-SPACE; Leakage ist nicht
nur "verlorene Amplitude", sondern ALGEBRA-BRECHEND. Daher:
Leakage-Rejection ist Pflicht, die Rate wird gemeldet.

Witness-Design (ehrlich, konditional):
  - Messung C (computational basis): Populationen. |phi> und rho_sep haben
    IDENTISCHE Populationen (§Z.11-Konfund, überlebt das Encoding exakt).
  - Messung D (DFT-Basis, U = F (x) F† auf den beiden 3-Qubit-Registern):
    die DFT-diagonale Gewichtssumme V = sum_a p~(a,a) trennt das
    preregistrierte Konfund-Paar scharf: V(|phi>) = 1, V(rho_sep) = 1/5.
  - SEPARABILITÄTSSCHRANKE: für Zustände mit maximal-korrelierten
    computational Populationen (Support auf {|kk>}) ist die EINZIGE
    separable Extension rho_sep(p) = sum_k p_k |kk><kk|, und deren
    DFT-Diagonalgewicht ist exakt sum_k p_k / 5 = 1/5. Daher: V > 1/5
    bezeugt Verschränkung — KONDITIONAL auf diesen Support (der aus
    Messung C verifiziert wird; Abweichung wird gemeldet, nicht
    kaschiert). KONDITIONAL heißt: V allein ist KEIN unbedingter Witness —
    es ist ein conditional coherence witness, gültig nur für Zustände mit
    maximally-correlated computational support (der Produktzustand
    chi_a (x) chi'_a erreicht V = 1, hat aber andere Computational-
    Populationen und wird von Messung C ausgeschlossen). Kein Ein-Setting-
    Witness fängt alle verschränkten
    Zustände (das wäre Tomographie); das preregistrierte Ziel ist das
    §Z.11-Konfund-Paar |phi> vs rho_sep.

Analytische Pins (in Tests fixiert):
  - (F (x) F†)|phi> = |phi>  -> DFT-Histogramm von |phi>: 5 x 1/5 diagonal
  - rho_sep in DFT-Basis: uniform 1/25 über die 25 logischen Outcomes
  - Produktzustand |0,0>: DFT-Histogramm identisch mit rho_sep (25 x 1/25)
    — beide separabel, beide exakt an der Schranke.

Anti-Sharpshooter: das Modul LIEFERT v_hat/SE/Schranke, entscheidet aber
NICHT — die Entscheidungsregel (z.B. v_hat − 4·SE > 1/5) gehört ins
PREREG (Phase 3, pt_prereg_audit-Felder md5/decision_rule/predictions).

Phase 2 (Aer + Transpilation-Stack: Readout-Noise, Gate-Counts) und
Phase 3 (Prereg → 1 QPU-Job auf Fez, 6 Qubits, 8192 Shots, beide
Zustände im selben Job) sind explizit NICHT Teil dieses Moduls.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pt_ququint_entanglement import (
    max_entangled_phi,
    populations,
    sample_shots_from_probs,
    separable_dephased_phi,
    weyl_bell_state,
)
from pt_ququint_simulator import pauli_x_5, pauli_z_5

D5 = 5
ENC_DIM = 8                      # 3 Qubits pro Ququint
TWO_DIM = ENC_DIM * ENC_DIM      # 64: zwei Ququints in 6 Qubits
LEAKAGE_INDICES = (5, 6, 7)      # 101, 110, 111 — verworfen, Rate gemeldet
WITNESS_BOUND = 1.0 / D5         # 1/5: Separabilitätsschranke (konditional)
_OMEGA = np.exp(2j * np.pi / 5)


# === ENCODING ===


def encode_ququint(k):
    """|k>_5 -> 3-Qubit-Basisvektor |k>_binary (8 dim), k in 0..4."""
    if not 0 <= int(k) <= 4:
        raise ValueError(f"k muss in 0..4 liegen, erhalten: {k}")
    v = np.zeros(ENC_DIM)
    v[int(k)] = 1.0
    return v


# === ENCODED OPERATOREN (8 x 8) ===


def x5_encoded():
    """X5 als 8x8-Permutation: 5-Zyklus auf 0..4, Fixpunkte auf 5,6,7."""
    X8 = np.zeros((ENC_DIM, ENC_DIM))
    for k in range(D5):
        X8[(k + 1) % D5, k] = 1.0
    for l in LEAKAGE_INDICES:
        X8[l, l] = 1.0
    return X8


def z5_encoded():
    """Z5 als 8x8-Diagonale: omega^k auf 0..4, 1 auf Leakage."""
    diag = np.ones(ENC_DIM, dtype=complex)
    for k in range(D5):
        diag[k] = _OMEGA ** k
    return np.diag(diag)


def dft5_encoded():
    """DFT-5 im logischen Block (omega^{jk}/sqrt(5)), Identität auf Leakage.

    Das ist die Basis-Rotation für Messung D: Ququint A mit F, Ququint B
    mit F† rotieren, dann in der Computational-Basis messen.
    """
    F = np.eye(ENC_DIM, dtype=complex)
    for j in range(D5):
        for k in range(D5):
            F[j, k] = _OMEGA ** (j * k) / np.sqrt(D5)
    return F


def weyl_omega():
    """Die primitive 5. Einheitswurzel (Konvention des Kernel-audited Stacks)."""
    return _OMEGA


def verify_encoded_against_kernel():
    """Encoded-Operatoren gegen die Kernel-auditierten 5x5-Operatoren prüfen.

    Liefert ein Checks-Dict; alle Werte müssen True sein. Der Weyl-Bruch auf
    Leakage ist KEIN Fehler, sondern das dokumentierte Strukturfundament
    (siehe Moduldocstring) — daher als eigener Check mit erwartungsgemäß
    True (der Bruch EXISTIERT).
    """
    X8, Z8 = x5_encoded(), z5_encoded()
    weyl_res = Z8 @ X8 - _OMEGA * X8 @ Z8
    return {
        "x_restriction_matches_kernel": bool(
            np.array_equal(X8[:D5, :D5], pauli_x_5())
        ),
        "z_restriction_matches_kernel": bool(
            np.allclose(Z8[:D5, :D5], pauli_z_5(), atol=1e-15)
        ),
        "x_pow5_identity": bool(
            np.array_equal(np.linalg.matrix_power(X8, D5), np.eye(ENC_DIM))
        ),
        "z_pow5_identity": bool(
            np.allclose(np.linalg.matrix_power(Z8, D5), np.eye(ENC_DIM), atol=1e-12)
        ),
        "weyl_on_logical_subspace": bool(
            np.allclose(weyl_res[:D5, :D5], 0.0, atol=1e-12)
        ),
        "weyl_breaks_on_leakage": bool(np.linalg.norm(weyl_res[D5:, D5:]) > 1.0),
    }


# === EMBEDDING: logische 25-dim -> encodierte 64-dim ===


def embed_logical_state(state):
    """Bettet einen logischen Zwei-Ququint-Zustand (25 dim rein, 64x64 gemischt)
    in das encodierte 6-Qubit-Register (64 dim rein, 64x64 gemischt).

    Die reshape-basierte Abbildung ist exakt die Kodierung |k>_5 -> |k>_bin
    pro Ququint: logischer Index k*5+l wird zu k*8+l.
    """
    s = np.asarray(state, dtype=complex)
    if s.ndim == 1:
        out = np.zeros(TWO_DIM, dtype=complex)
        out.reshape(ENC_DIM, ENC_DIM)[:D5, :D5] = s.reshape(D5, D5)
        return out
    out = np.zeros((TWO_DIM, TWO_DIM), dtype=complex)
    out.reshape(ENC_DIM, ENC_DIM, ENC_DIM, ENC_DIM)[:D5, :D5, :D5, :D5] = (
        s.reshape(D5, D5, D5, D5)
    )
    return out


def phi_max_encoded():
    """|phi> = (1/sqrt(5)) sum_k |k,k>, encodiert (64 dim)."""
    psi = np.zeros(TWO_DIM, dtype=complex)
    for k in range(D5):
        psi[k * ENC_DIM + k] = 1.0
    return psi / np.sqrt(D5)


def weyl_bell_encoded():
    """(|0,0> + |1,4>)/sqrt(2), encodiert — exakt das Embedding des
    kernel-algebraisch erzeugten §Z.11-Weyl-Bell-Zustands."""
    return embed_logical_state(weyl_bell_state(1))


def separable_dephased_encoded():
    """rho_sep = (1/5) sum_k |kk><kk|, encodiert (64x64) — die Konfund-Kontrolle."""
    return embed_logical_state(separable_dephased_phi())


def product_encoded(a, b):
    """Produkt-Basiszustand |a,b>, encodiert."""
    psi = np.zeros(TWO_DIM, dtype=complex)
    psi[int(a) * ENC_DIM + int(b)] = 1.0
    return psi


# === MESSUNGSSIMULATION ===


def histogram_computational(state):
    """Messung C: Computational-Basis-Histogramm über 64 Ausgänge."""
    return populations(state)


def histogram_dft(state):
    """Messung D: DFT-Basis-Histogramm — U = F (x) F† anwenden, dann diag.

    QPU-Äquivalent: F-embedded auf Register A, F†-embedded auf Register B,
    dann alle 6 Qubits messen (ein Setting, 64 Bins).
    """
    F = dft5_encoded()
    U = np.kron(F, F.conj().T)
    s = np.asarray(state, dtype=complex)
    if s.ndim == 1:
        psi = U @ s
        return np.real(psi * psi.conj())
    rho = U @ s @ U.conj().T
    return np.maximum(np.real(np.diag(rho)), 0.0)


def reject_leakage(counts):
    """Verwirft alle Shots, in denen mindestens ein Ququint auf einem
    Leakage-Zustand (5,6,7) gemessen wurde. Liefert kept_counts (25 logische
    Bins), n_kept, n_rejected, leakage_rate."""
    counts = np.asarray(counts)
    logical = np.array([a * D5 + b for a in range(D5) for b in range(D5)])
    kept_counts = np.array([int(counts[a * ENC_DIM + b])
                            for a in range(D5) for b in range(D5)])
    n_kept = int(kept_counts.sum())
    # Differenz statt Summe zweier Teilsummen: die 9 doppelt-leakigen
    # Positionen (a in {5,6,7} UND b in {5,6,7}) wären sonst doppelt
    # gezählt (Teilsumme A-leak + Teilsumme B-leak überlappen sich).
    n_rejected = int(counts.sum()) - n_kept
    total = n_kept + n_rejected
    return {
        "kept_counts": kept_counts,
        "n_kept": n_kept,
        "n_rejected": n_rejected,
        "leakage_rate": (n_rejected / total) if total else 0.0,
        "_logical": logical,  # Referenzabbildung logischer 25-dim-Index
    }


# === KOHÄRENZ-WITNESS (konditional, siehe Modul-Kopf) ===


def dft_diagonal_weight(probs):
    """V = sum_a p~(a,a) über die 5 logischen Diagonal-Outputs der
    DFT-Basis-Messung (Messung D). Schranke: WITNESS_BOUND = 1/5."""
    p = np.asarray(probs, dtype=float).reshape(ENC_DIM, ENC_DIM)
    return float(sum(p[a, a] for a in range(D5)))


def witness_from_shots(probs_dft, n_shots, seed, n_boot=1000):
    """Shot-basierte Witness-Schätzung mit vektorisiertem Bootstrap-SE.

    Liefert v_hat, se, bound, v_exact (aus der exakten Wahrscheinlichkeits-
    verteilung) — ENTSCHEIDUNG bleibt dem Prereg vorbehalten.
    """
    p = np.asarray(probs_dft, dtype=float)
    rng = np.random.default_rng(seed)
    counts = rng.multinomial(int(n_shots), p)
    v_hat = dft_diagonal_weight(counts / float(n_shots))
    boot = rng.multinomial(int(n_shots), p, size=int(n_boot)) / float(n_shots)
    boot = boot.reshape(int(n_boot), ENC_DIM, ENC_DIM)
    v_boot = np.einsum("nii->n", boot[:, :D5, :D5])
    v_exact = dft_diagonal_weight(p)
    return {
        "v_hat": float(v_hat),
        "se": float(np.std(v_boot, ddof=1)),
        "bound": float(WITNESS_BOUND),
        "v_exact": float(v_exact),
        "n_shots": int(n_shots),
        "n_boot": int(n_boot),
    }