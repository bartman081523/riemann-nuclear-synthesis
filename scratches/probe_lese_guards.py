"""Mini-Probe 3: unbenannte Guard-Texte von lese_readout_cal_reihen."""
import sys

sys.path.insert(0, "src")
import primequant as pq

SUM = {"counts": [{"kind": "readout_cal", "name": "g",
                   "counts": {"00": 7}, "shots_actual": 8}]}
MASSE = {"counts": [{"kind": "readout_cal", "name": "g",
                     "counts": {"01": 4.5, "00": 3.5}, "shots_actual": 8}]}
OK = {"counts": [{"kind": "readout_cal", "name": "g",
                  "counts": {"00": 6, "01": 2}, "shots_actual": 8}]}
NEGATIV = {"counts": [{"kind": "readout_cal", "name": "g",
                       "counts": {"00": 9}, "shots_actual": 8}]}
for label, dok in (("sum7", SUM), ("masse4.5", MASSE), ("ok", OK),
                   ("negativ9", NEGATIV)):
    try:
        ret = pq.lese_readout_cal_reihen(dok)
        print(label, "-> OK:", str(ret)[:260])
    except Exception as exc:  # noqa: BLE001
        print(label, "->", type(exc).__name__, "|", exc)