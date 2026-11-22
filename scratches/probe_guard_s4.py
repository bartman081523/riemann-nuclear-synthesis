"""Mini-Probe S4: die vier letzten unbeobachteten Guard-Texte (File 4)."""
import sys

sys.path.insert(0, "src")
from fractions import Fraction as F

import primequant as pq
from primequant import observables as obs

konst13 = obs.punkt_konstanten(13, 3, 3, shots=12)

for label, aufruf in (
        ("quote_label", lambda: obs.quote_exakt({"10000": 12}, konst13,
                                                shots=12)),
        ("ring_dft", lambda: pq.ring_dft([0.5, 1, 1], 3)),
        ("norm_q1", lambda: pq.norm_galois((0, 1), 1)),
        ("norm_neg", lambda: pq.norm_galois((1, 1, -1), 3)),
        ("ramanujan_q1", lambda: pq.ramanujan_summe(1, 10)),
        ("ramanujan_q6", lambda: pq.ramanujan_summe(6, 10)),
        ("galois_q?", lambda: pq.galois_konjugiert((0, 1), 1, 0)),
        ("ring_int_neg?", lambda: pq.ring_dft([-1, 1, 1], 3)),
        ("quad_float?", lambda: pq.quad_magnitude((0.5,), 2))):
    try:
        ret = aufruf()
        print(label, "-> OK:", repr(ret)[:200])
    except Exception as exc:  # noqa: BLE001
        print(label, "->", type(exc).__name__, "|", exc)