"""
EXPERIMENT 029 - Zwei-Ququint-Verschränkung (genuine 5 x 5, statevector only).

Motivation (siehe SYNTHESIS §Z.11): bislang existierte im Ququint-Stack nur
eine eingeschränkte Form von "Verschränkung" — die Schmidt-Entropie eines
EINZELNen 5-dim Qudits über eine aufgeprägte 2x3-Bipartition mit 5->6
Zero-Padding (pt_ququint_empirical.schmidt_entropy_qubit_vs_ququint), und
ccz_gate_5 ist eine Single-Qudit-Diagonalphase, also NICHT verschränkend.
Dieses Modul liefert erstmals echte Zwei-Ququint-Zustände im genuinen
Tensorprodukt 5 (x) 5 = 25 dim — ohne Padding, ohne künstliche Bipartition.

Zustände
--------
- max_entangled_phi:      (1/sqrt(5)) sum_k |k,k>  — maximal verschränkt
- ghz_two_ququint:        (|0,0> + |4,4>)/sqrt(2)  — Katzenzustand d=5
- weyl_bell_state(k):     normiertes (I + (X (x) X†)^k)|0,0>
                          (Weyl-Verschiebungen aus der kernel-verifizierten
                          Algebra, pt_finite_kernel_check: X^5=I, X†X=I exakt)
- phi_from_weyl:          (1/sqrt(5)) sum_k (X (x) X†)^k |0,0> = (1/sqrt(5)) sum_k |k, -k mod 5>
- separable_dephased_phi: rho_sep = (1/5) sum_k |kk><kk|  — der KONFUND:
                          identische Computational-Basis-Populationen wie |phi>,
                          aber N = 0 (klassisch korreliert, nicht verschränkt)

Maße
----
- Schmidt-Koeffizienten/Entropie über die NATÜRLICH Bipartition A = erster
  Ququint, B = zweiter Ququint (reshape 25 -> 5x5); natürlicher Logarithmus
  (konsistent mit pt_ququint_empirical).
- Concurrence-Analog für reine Zustände (universal, d-unabhängig):
  C = sqrt(2 (1 - Tr rho_A^2)); Maximum sqrt(2(1 - 1/5)) = sqrt(1.6) ~ 1.2649
  (C=1 wie beim Qubit-GHZ entspricht dem zweiter-Höchst-Wert, nicht dem
  d=5-Maximum — die Skala ist NICHT die Qubit-Skala).
- Negativity via Partialtransposition über B: N = (||rho^T_B||_1 - 1)/2.
  PPT ist in 5x5 necessary-but-NOT-sufficient; für die hier verwendeten
  Zustände ist Separabilität aber konstruktiv manifest (rho_sep ist explizit
  eine Konvexkombination von Produktprojektoren).

Shot-Sampling
-------------
rng.multinomial in EINEM vektorisierten Aufruf (kein Per-Shot-Loop), seeded
und reproduzierbar; Standardfehler SE = sqrt(p(1-p)/n) pro Bin.

Epistemische Lektion (Apophenia-Management für spätere QPU-Shots)
-----------------------------------------------------------------
|phi> und rho_sep haben IDENTISCHE Computational-Basis-Populationen und
liefern mit gleichem Seed IDENTISCHE Shot-Counts — aber Negativity 2 vs 0.
Populations-Daten allein bezeugen keine Verschränkung; erst Kohärenz-
sensitive Maße (Partialtransposition, Mehrbasen-Messungen) können das.

Alles statevector/numpy — KEINE QPU-Kosten, keine Shots auf Hardware.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pt_ququint_simulator import pauli_x_5

D5 = 5
DIM = D5 * D5  # 25


# === ZUSTÄNDE ===


def max_entangled_phi():
    """(1/sqrt(5)) sum_k |k,k> — 25-dim reiner Zustand.

    Äquivalent zur Weyl-Darstellung (1/sqrt(5)) sum_k (X (x) X)^k |0,0>,
    da (X (x) X)^k |0,0> = |k,k>.
    """
    psi = np.zeros(DIM, dtype=complex)
    for k in range(D5):
        psi[k * D5 + k] = 1.0
    return psi / np.sqrt(D5)


def ghz_two_ququint():
    """(|0,0> + |4,4>)/sqrt(2) — zwei-ququint GHZ/Katzenzustand."""
    psi = np.zeros(DIM, dtype=complex)
    psi[0 * D5 + 0] = 1.0
    psi[4 * D5 + 4] = 1.0
    return psi / np.sqrt(2.0)


def _weyl_displacement_x_xdag():
    """X (x) X† als 25x25-Matrix — X aus dem kernel-verifizierten Simulator."""
    x = np.asarray(pauli_x_5(), dtype=complex)
    return np.kron(x, x.conj().T)


def weyl_bell_state(k=1):
    """Normiertes (I + (X (x) X†)^k)|0,0> = (|0,0> + |k, -k mod 5>)/sqrt(2).

    k=0 reduziert auf den Produktzustand |0,0> (eine einzelne Weyl-
    Verschiebung eines Basiszustands ist nie verschränkend).
    """
    e0 = np.zeros(DIM, dtype=complex)
    e0[0] = 1.0
    disp = np.linalg.matrix_power(_weyl_displacement_x_xdag(), int(k) % D5)
    psi = e0 + disp @ e0
    return psi / np.linalg.norm(psi)


def phi_from_weyl():
    """(1/sqrt(5)) sum_k (X (x) X†)^k |0,0> = (1/sqrt(5)) sum_k |k, -k mod 5>.

    Uniforme Superposition über die Weyl-Orbit — maximal verschränkt mit
    demselben Schmidt-Spektrum wie max_entangled_phi (B-Seite relabelt).
    """
    e0 = np.zeros(DIM, dtype=complex)
    e0[0] = 1.0
    disp = _weyl_displacement_x_xdag()
    acc = np.zeros(DIM, dtype=complex)
    v = e0.copy()
    for _ in range(D5):
        acc += v
        v = disp @ v
    return acc / np.linalg.norm(acc)


def separable_dephased_phi():
    """rho_sep = (1/5) sum_k |kk><kk| — 25x25 Dichtematrix.

    Der Konfund-Zustand: klassisch korreliert, manifest separabel, aber mit
    denselben Computational-Basis-Populationen wie |phi>.
    """
    rho = np.zeros((DIM, DIM), dtype=complex)
    for k in range(D5):
        i = k * D5 + k
        rho[i, i] = 1.0 / D5
    return rho


def density_matrix(psi):
    """|psi><psi| als (DIM, DIM)-Matrix; akzeptiert auch bereits-gemischte (n,n)."""
    psi = np.asarray(psi, dtype=complex)
    if psi.ndim == 2:
        return psi
    return np.outer(psi, psi.conj())


# === MAßE ===


def schmidt_coefficients(psi, d=D5):
    """Singular values der (d,d)-Reshape — Schmidt-Spektrum der natürlichen
    Bipartition A = Ququint 1, B = Ququint 2 (KEIN Padding)."""
    mat = np.asarray(psi, dtype=complex).reshape(d, d)
    return np.linalg.svd(mat, compute_uv=False)


def schmidt_entropy(psi, d=D5):
    """Von-Neumann-Entropie des Reduzierten (natürlicher Log, Cutoff 1e-12)."""
    lam = schmidt_coefficients(psi, d)
    p = lam**2
    p = p[p > 1e-12]
    return float(-np.sum(p * np.log(p)))


def concurrence_pure(psi, d=D5):
    """Universal-Concurrence für reine Zustände: C = sqrt(2 (1 - Tr rho_A^2)).

    Bereich [0, sqrt(2(1 - 1/d))] = [0, sqrt(1.6)] für d = 5 — NICHT die
    Qubit-Skala (dort Maximum 1); C = 1 entspricht dem 2-term-GHZ.
    """
    lam = schmidt_coefficients(psi, d)
    p = lam**2
    tr2 = float(np.sum(p**2))
    return float(np.sqrt(max(0.0, 2.0 * (1.0 - tr2))))


def negativity(rho, d=D5):
    """N = (||rho^T_B||_1 - 1)/2 via Partialtransposition über Ququint B.

    Partialtransposition = reshape (d,d,d,d), Achsen (0,2,1,3) transponieren.
    """
    rho = np.asarray(rho, dtype=complex)
    rho_tb = rho.reshape(d, d, d, d).transpose(0, 2, 1, 3).reshape(d * d, d * d)
    singular_values = np.linalg.svd(rho_tb, compute_uv=False)
    trace_norm = float(np.sum(singular_values))
    return (trace_norm - 1.0) / 2.0


def populations(state):
    """Diagonale in der Computational-Basis: |amp|^2 für rein, diag für gemischt."""
    state = np.asarray(state, dtype=complex)
    if state.ndim == 2:
        return np.real(np.diag(state)).copy()
    return np.real(state * state.conj())


# === VEKORIZED SHOT-SAMPLING ===


def sample_shots_from_probs(probs, n_shots, seed):
    """Multinomial-Stichprobe in EINEM vektorisierten Aufruf; seeded reproduzierbar."""
    rng = np.random.default_rng(seed)
    probs = np.asarray(probs, dtype=float)
    counts = rng.multinomial(int(n_shots), probs)
    return counts


def sampling_standard_error(probs, n_shots):
    """SE pro Bin: sqrt(p (1 - p) / n)."""
    probs = np.asarray(probs, dtype=float)
    return np.sqrt(probs * (1.0 - probs) / float(n_shots))


# === KONFUND-BERICHT (Apophenia-Management) ===


def confound_report(n_shots, seed):
    """Belegt: identische Populationen + identische Counts, aber N = 2 vs 0."""
    phi = max_entangled_phi()
    rho_sep = separable_dephased_phi()
    # Kanonisierung: |1/sqrt(5)|^2 = 0.20000000000000004 vs 1/5 = 0.2
    # unterscheiden sich in der letzten ULP — mathematisch exakt gleich.
    # Für den Bit-exakten Sampling-Vergleich wird auf 12 Dezimalstellen
    # kanonisiert (weit unter jeder physikalischen Skala).
    p_phi = np.round(populations(phi), 12)
    p_sep = np.round(populations(rho_sep), 12)
    counts_phi = sample_shots_from_probs(p_phi, n_shots, seed=seed)
    counts_sep = sample_shots_from_probs(p_sep, n_shots, seed=seed)
    return {
        "n_shots": int(n_shots),
        "seed": int(seed),
        "max_entangled_phi": {
            "negativity": negativity(density_matrix(phi)),
            "populations": p_phi,
            "counts": counts_phi,
        },
        "separable_mixture": {
            "negativity": negativity(rho_sep),
            "populations": p_sep,
            "counts": counts_sep,
        },
        "populations_identical": bool(np.array_equal(p_phi, p_sep)),
        "sampled_counts_identical": bool(np.array_equal(counts_phi, counts_sep)),
        "negativity_differs": bool(
            negativity(density_matrix(phi)) > 0.5
            and negativity(rho_sep) < 1e-12
        ),
    }