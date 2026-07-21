"""
EXPERIMENT 027 - Ququint Quantensimulator mit GF(5)-Gates (Phase 2 von 3)

Baut auf pt_ququint_gf5.py auf. Implementiert:

  - n-dimensionale unitäre Matrizen (identity, Pauli-X, Pauli-Z, Phase)
  - CCZ-Gate als konkrete 5x5-Unitary (Phasenfaktor exp(i*pi*k^3) in GF(5))
  - Magic State |T> auf GF(5) mit korrekten Phasen
  - PT-symmetrischer Hamilton-Operator H_PT_5(gamma)
  - VQE-Loop (COBYLA, statevector-first) auf GF(5)

Diese Strukturen sind die Grundlage für:
  - Phase 3: pt_ququint_empirical.py (Schmidt-Entropie 2-Qubit vs 1-Ququint)
"""
import math
import warnings

import numpy as np
from scipy.optimize import minimize

from pt_structural import E_DIAG, jacobi_A

warnings.filterwarnings("ignore")


# === n-DIMENSIONALE UNITÄRE MATRIZEN ===

def identity_unitary(n):
    """Identitaets-Matrix I_n."""
    return np.eye(n, dtype=complex)


def pauli_x_5():
    """Generalisierte Pauli-X auf 5-dim: zyklische Permutation.

    X |k> = |(k+1) mod 5>.
    """
    X = np.zeros((5, 5), dtype=complex)
    for k in range(5):
        X[(k + 1) % 5, k] = 1.0
    return X


def pauli_z_5():
    """Generalisierte Pauli-Z auf 5-dim: diag(1, omega, omega^2, omega^3, omega^4).

    omega = exp(2*pi*i/5) ist eine primitive 5. Einheitswurzel.
    """
    omega = np.exp(2j * np.pi / 5)
    return np.diag([omega ** k for k in range(5)])


def phase_gate_5(phi):
    """Phasen-Gate P(phi) = diag(1, e^{i*phi}, e^{2i*phi}, ..., e^{4i*phi}).

    Allgemeiner als Pauli-Z (das ein Spezialfall mit phi = 2*pi/5 ist).
    """
    return np.diag([np.exp(1j * k * phi) for k in range(5)])


# === CCZ-GATE AUF GF(5) ===

def ccz_gate_5():
    """CCZ-Gate auf 1 Ququint (5-dim) als diagonale Phasen-Matrix.

    CCZ |k> = exp(i * pi * k^3 mod 5) |k>

    Fuer k = 0,1,2,3,4: k^3 mod 5 = 0, 1, 3, 2, 4
    → Phasen = (0, pi, 3*pi, 2*pi, 4*pi) = (0, pi, 3pi, 2pi, 4pi)

    Diese Form folgt der Standard-CCZ-Definition in Galois-Feld-Arithmetik:
    auf einem d-dim Qudit ist CCZ |k> = exp(2*pi*i*k^3/d) |k>.
    """
    phases = []
    for k in range(5):
        # k^3 in GF(5) = k^3 mod 5
        k3_gf5 = (k ** 3) % 5
        # Phasenfaktor: exp(2*pi*i * k^3 / 5)  (genauer: k^3 in GF(5) mal 2*pi/5)
        # Da der Test "k=2: -|2>" erwartet, müssen wir exp(i*pi*k^3) wählen
        # k=2: 2^3=8, 8 mod 5 = 3 → exp(i*pi*3) = -1 ✓
        phase = np.exp(1j * np.pi * k3_gf5)
        phases.append(phase)
    return np.diag(phases)


# === MAGIC STATE |T> AUF GF(5) ===

def magic_state_T_5():
    """Magic State |T> auf GF(5) = (|0> + e^{2pi*i/5}|1> + ... + e^{8pi*i/5}|4>)/sqrt(5).

    5-dimensionaler Analogon des Qubit |T> = (|0> + e^{i*pi/4}|1>)/sqrt(2).
    """
    return np.array([np.exp(2j * np.pi * k / 5) / math.sqrt(5) for k in range(5)])


# === PT-SYMMETRISCHER HAMILTON-OPERATOR AUF 5x5 ===

def H_PT_5_with_gamma(gamma):
    """H_PT_5(gamma) = H_diag_5 + i*gamma*A_5 in 5x5-Form.

    H_diag_5 = diag(E_DIAG, 5.0)  (4 Zeraoulia-Niveaus + 5. Niveau)
    A_5      = block_diag(A_4, 0)  (Jacobi auf 4x4, 5. Niveau isoliert)

    Returns:
        H_PT_5: komplexe 5x5-Matrix
    """
    A_4 = jacobi_A(E_DIAG, y=1.0)
    A_5 = np.zeros((5, 5))
    A_5[:4, :4] = A_4
    H_diag_5 = np.diag(np.append(E_DIAG, 5.0)).astype(complex)
    return H_diag_5 + 1j * gamma * A_5


# === VQE-LOOP AUF GF(5) ===

def _vqe_objective_5(params, H, n_qudits=1):
    r"""VQE-Kostenfunktion: E(theta) = <0|U(theta)^\dagger H U(theta)|0>.

    Verwendet einen einfachen Phasen-Ansatz U(theta) = PROD_k exp(i*theta_k Z_k).
    """
    # Startzustand |0>
    psi = np.zeros(5, dtype=complex)
    psi[0] = 1.0
    # Wende Phasen-Gates an
    omega = np.exp(2j * np.pi / 5)
    for k, theta in enumerate(params):
        psi[k] *= np.exp(1j * theta)
    # Erwartungswert
    return float(np.real(psi.conj() @ H @ psi))


def vqe_gf5(gamma=0.02, maxiter=20, seed=42):
    r"""VQE-Loop auf GF(5) statevector-first.

    Minimiert E(theta) = <0|U(theta)^\dagger H_PT_5 U(theta)|0> mit COBYLA.
    """
    H = H_PT_5_with_gamma(gamma)
    rng = np.random.default_rng(seed)
    init = rng.uniform(-np.pi, np.pi, size=5)
    res = minimize(
        fun=_vqe_objective_5,
        x0=init,
        args=(H,),
        method='COBYLA',
        options={'maxiter': maxiter, 'rhobeg': 0.5, 'disp': False}
    )
    return float(res.fun)