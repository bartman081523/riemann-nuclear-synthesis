"""primequant — exakte, seed-freie Quanten-Numerik.

Sichtbare Schicht des Pakets: Garantie-Etiketten (EXAKT / ABGELEITET /
GESAMPFELT, Verkettungsregel exklusiv abwaerts), der generische
zyklotomische Ring Z[x]/(Phi_q(x)) und GF(q) nebst GF(q)[x] fuer alle
Primzahlen q. Der EXAKT-Kern dieser Datei-Ebene ist stdlib-only; numpy
wird nur in der separaten Float-Schicht (channels) importiert, sympy nur
als Anker-Orakel in tests/ — der Kern importiert nie sympy.

Fuehrende Unterstriche: interne Module (_cyc, _gfq, _guarantees) — die
oeffentliche API wird hier re-exportiert; Tests gehen bewusst auch intern
gegen die Quelltexte (Anker-Enforcement, siehe tests/).
"""

from __future__ import annotations

__version__ = "0.1.0"

from ._guarantees import (
    AnchorViolation,
    GUARANTEE_SCHEMA,
    Garantiert,
    Guarantee,
    garantiere,
    forder_garantie,
    klasse_rang,
    pruefe_verkettung,
)
from ._gfq import (
    ist_primzahl,
    gfq_add,
    gfq_div,
    gfq_inv,
    gfq_mul,
    gfq_norm,
    gfq_sub,
    phi_q_koeffs,
    poly_add,
    poly_divmod,
    poly_eval,
    poly_from_int_koeffs,
    poly_gcd,
    poly_grad,
    poly_mul,
    poly_norm,
    poly_pow,
    poly_sub,
)
from ._cyc import (
    Matrix,
    Element,
    NichtInvertierbar,
    cyc_add,
    cyc_conj,
    cyc_eq,
    cyc_from_int,
    cyc_from_json,
    cyc_inv,
    cyc_make,
    cyc_mat_adj,
    cyc_mat_eq,
    cyc_mat_id,
    cyc_mat_mul,
    cyc_mat_pow,
    cyc_mat_scalar_mul,
    cyc_mul,
    cyc_neg,
    cyc_one,
    cyc_omega,
    cyc_pow,
    cyc_rang,
    cyc_sub,
    cyc_to_json,
    cyc_zero,
)

__all__ = [
    "__version__",
    # Garantien
    "GUARANTEE_SCHEMA",
    "AnchorViolation",
    "Garantiert",
    "Guarantee",
    "garantiere",
    "forder_garantie",
    "klasse_rang",
    "pruefe_verkettung",
    # GF(q) + Polynomring
    "ist_primzahl",
    "gfq_add",
    "gfq_div",
    "gfq_inv",
    "gfq_mul",
    "gfq_norm",
    "gfq_sub",
    "phi_q_koeffs",
    "poly_add",
    "poly_divmod",
    "poly_eval",
    "poly_from_int_koeffs",
    "poly_gcd",
    "poly_grad",
    "poly_mul",
    "poly_norm",
    "poly_pow",
    "poly_sub",
    # Ring Z[x]/(Phi_q(x))
    "Element",
    "Matrix",
    "NichtInvertierbar",
    "cyc_add",
    "cyc_conj",
    "cyc_eq",
    "cyc_from_int",
    "cyc_from_json",
    "cyc_inv",
    "cyc_make",
    "cyc_mat_adj",
    "cyc_mat_eq",
    "cyc_mat_id",
    "cyc_mat_mul",
    "cyc_mat_pow",
    "cyc_mat_scalar_mul",
    "cyc_mul",
    "cyc_neg",
    "cyc_one",
    "cyc_omega",
    "cyc_pow",
    "cyc_rang",
    "cyc_sub",
    "cyc_to_json",
    "cyc_zero",
]