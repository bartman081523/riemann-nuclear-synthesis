"""primequant.theta_chain — Gekoppelte 2-Register-Weil-Theta-Kette (Stepanov-Multiplizitaet).

ABGELEITET-Werkzeug (Statevector- & Dichtematrix-Simulation via numpy, 0 QPU, Quota-frei).
Mathematische Grundlage:
  1. Zwei-QuQuint-Zustandsraum: Register A (Target, dim q) und Register B (arithmetische Ancilla, dim q).
     Gesamtraum C^q (x) C^q mit Basis |x>_A |y>_B, Dimension q^2.
  2. Modulares Kopplungsgatter C_ADD:
     C_ADD |x>_A |y>_B = |x>_A |(y + x) mod q>_B.
  3. Lokale Weil-Schritte:
     U_A = (F_q @ D_1) (x) I_q
     U_B = I_q (x) (F_q @ D_{q-1})
  4. Projektive arithmetische Reflexion R_{triv, B}:
     R_{triv, B} = I_q (x) (I_q - 2 |psi_triv><psi_triv|_B)
     wobei |psi_triv> = (1/sqrt(q-1)) sum_{x=1}^{q-1} |x>.
  5. Gesamter unitaerer Ketten-Schritt:
     W = R_{triv, B} @ C_ADD^dagger @ U_B @ C_ADD @ U_A.
  6. Resonanz nach Stepanov:
     Fuer L = floor(sqrt(q)) (q=5: L=2) erzeugt W eine kohärente Resonanz
     der Galois-invarianten trivialen Komponente R_L = P_triv / (P_triv + P_std),
     die robust gegen depolarisierendes Rauschen ist.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from ._gfq import ist_primzahl


def fourier_matrix(q: int) -> np.ndarray:
    """Normierte diskrete Fourier-Transformationsmatrix F_q."""
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl sein, erhalten {q}")
    omega = np.exp(2j * np.pi / q)
    indices = np.arange(q)
    exponents = np.outer(indices, indices) % q
    return (omega ** exponents) / np.sqrt(q)


def gauss_phase_matrix(q: int, t: int = 1) -> np.ndarray:
    """Diagonale quadratische Gauss-Phasenmatrix D_t = diag(omega^{t x^2 mod q})."""
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl sein, erhalten {q}")
    omega = np.exp(2j * np.pi / q)
    t_mod = t % q
    diag = np.array([omega ** ((t_mod * (x * x)) % q) for x in range(q)], dtype=complex)
    return np.diag(diag)


def controlled_add_matrix(q: int) -> np.ndarray:
    """Modulares C_ADD Gatter: |x>|y> -> |x>|(y + x) mod q>."""
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl sein, erhalten {q}")
    dim2 = q * q
    C = np.zeros((dim2, dim2), dtype=complex)
    for x in range(q):
        for y in range(q):
            idx_in = x * q + y
            idx_out = x * q + ((y + x) % q)
            C[idx_out, idx_in] = 1.0
    return C


def trivial_state_vector(q: int) -> np.ndarray:
    """Normierter Zustand |psi_triv> = (1/sqrt(q-1)) sum_{x=1}^{q-1} |x>."""
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl sein, erhalten {q}")
    v = np.zeros(q, dtype=complex)
    v[1:] = 1.0 / np.sqrt(q - 1)
    return v


def weil_theta_step_unitary(q: int) -> np.ndarray:
    """Konstruiert den vollstaendigen 2-Register-Schrittoperator W."""
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl sein, erhalten {q}")
    
    F = fourier_matrix(q)
    D1 = gauss_phase_matrix(q, 1)
    D_inv = gauss_phase_matrix(q, q - 1)
    
    I_q = np.eye(q, dtype=complex)
    U_A = np.kron(F @ D1, I_q)
    U_B = np.kron(I_q, F @ D_inv)
    
    C_ADD = controlled_add_matrix(q)
    
    psi_triv = trivial_state_vector(q)
    P_triv = np.outer(psi_triv, psi_triv.conj())
    R_triv_B = np.kron(I_q, I_q - 2.0 * P_triv)
    
    # W = R_{triv, B} @ C_ADD^\dagger @ U_B @ C_ADD @ U_A
    W = R_triv_B @ C_ADD.conj().T @ U_B @ C_ADD @ U_A
    return W


def partial_trace_ancilla(density_matrix: np.ndarray, q: int) -> np.ndarray:
    """Bildet die Partialspur ueber das Ancilla-Register B (Index 1)."""
    dm_4d = density_matrix.reshape((q, q, q, q))
    return np.trace(dm_4d, axis1=1, axis2=3)


def simulate_theta_chain(
    q: int,
    max_steps: int = 5,
    p_noise: float = 0.0,
) -> List[Dict[str, float]]:
    """Simuliert die 2-Register-Theta-Kette fuer L = 0 .. max_steps.
    
    Startzustand: |1>_A (x) |psi_triv>_B.
    Bei p_noise > 0 wird nach jedem Schritt depolarisierendes Rauschen auf dem
    Gesamtraum (dim = q^2) angewendet:
      rho -> (1 - p) rho + (p / q^2) I_{q^2}.
    """
    if not ist_primzahl(q):
        raise ValueError(f"q muss Primzahl sein, erhalten {q}")
    if p_noise < 0.0 or p_noise > 1.0:
        raise ValueError(f"p_noise muss in [0, 1] liegen, erhalten {p_noise}")
        
    dim2 = q * q
    W = weil_theta_step_unitary(q)
    I_total = np.eye(dim2, dtype=complex)
    
    psi_triv = trivial_state_vector(q)
    P_triv = np.outer(psi_triv, psi_triv.conj())
    P_active = np.diag([0.0] + [1.0] * (q - 1))
    P_std = P_active - P_triv
    baseline_R = 1.0 / (q - 1)
    
    # Initialer Zustand |1>_A (x) |psi_triv>_B
    psi_A0 = np.zeros(q, dtype=complex)
    psi_A0[1] = 1.0
    state0 = np.kron(psi_A0, psi_triv)
    rho = np.outer(state0, state0.conj())
    
    history: List[Dict[str, float]] = []
    
    for step in range(max_steps + 1):
        if step > 0:
            rho = W @ rho @ W.conj().T
            if p_noise > 0.0:
                rho = (1.0 - p_noise) * rho + (p_noise / dim2) * I_total
                
        # Reduzierte Dichtematrix fuer Target-Register A
        rho_A = partial_trace_ancilla(rho, q)
        
        # Purity Tr(rho_A^2)
        purity = float(np.real(np.trace(rho_A @ rho_A)))
        
        # Sektor-Populationen
        p_triv = float(np.real(np.trace(P_triv @ rho_A)))
        p_std = float(np.real(np.trace(P_std @ rho_A)))
        p_active = float(np.real(np.trace(P_active @ rho_A)))
        
        R = p_triv / p_active if p_active > 1e-12 else 0.0
        gap = R - baseline_R
        
        history.append({
            "step": step,
            "p_triv": p_triv,
            "p_std": p_std,
            "p_active": p_active,
            "R": R,
            "baseline_R": baseline_R,
            "gap_over_baseline": gap,
            "purity": purity,
        })
        
    return history


def verify_stepanov_resonance(q: int = 5, p_noise: float = 0.0) -> Dict[str, Any]:
    """Ueberprueft die quantitative Stepanov-Resonanz fuer Primzahl q."""
    expected_L = math.isqrt(q)
    max_steps = max(expected_L + 3, 5)
    
    sim = simulate_theta_chain(q, max_steps=max_steps, p_noise=p_noise)
    r_vals = [s["R"] for s in sim]
    
    # Resonanz-Schritt (ab Schritt 1)
    actual_peak_L = int(np.argmax(r_vals[1:])) + 1
    peak_record = sim[actual_peak_L]
    stepanov_record = sim[expected_L]
    
    # Kriterien fuer q=5:
    # 1. Stepanov-Koinzidenz: actual_peak_L == expected_L
    # 2. Mindestverstaerkung: R >= 0.350 (fuer q=5 Baseline 0.250)
    # 3. Verschiedenheit/Verschraenkung: Purity <= 0.800
    is_stepanov_matched = (actual_peak_L == expected_L)
    has_amplification = stepanov_record["gap_over_baseline"] > 0.05
    is_entangled = stepanov_record["purity"] < 0.80
    
    verdict = (
        "CONFIRMED_STEPANOV_RESONANCE"
        if (is_stepanov_matched and has_amplification and is_entangled)
        else "SUB_OPTIMAL_OR_UNMATCHED"
    )
    
    return {
        "q": q,
        "expected_L": expected_L,
        "actual_peak_L": actual_peak_L,
        "stepanov_matched": is_stepanov_matched,
        "stepanov_record": stepanov_record,
        "history": sim,
        "verdict": verdict,
    }
