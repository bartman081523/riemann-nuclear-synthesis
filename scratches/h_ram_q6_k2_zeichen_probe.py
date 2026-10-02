# -*- coding: utf-8 -*-
"""EXPERIMENT 051 Diagnostik-Nachtrag (0 QPU, NICHT verdict-tragend).

Mitgebracht als disclosed Probe — der registrierte Diagnostik-Slot
"diagnostik_nicht_verdict_tragend.zeichen_stabilitaet_kalibrier" aus
pt_ram_q6_k2_prereg.json (md5 ef7029764f0c192d69712674bd161822) wurde
von der gefrorenen Auswertung (Commit 808883f) NICHT gefuellt (Eval-Key
"diagnostik" ABWESEND, kein diagnostik-Block in pt_ram_q6_k2_eval.json).
Hier nachgeholt, ohne das frozen Artefakt anzufassen.

Frage: misst Session K2 (Kingston, 4. Session der Serie) die
Run-3-Verdict-P mit stabilen Vorzeichen?  Abgleich an den 13
Kalibrier-P (= Run-3-Verdict-P, kalibrier_p_equals_run3_verdict: true)
gegen

  (a) die GEFRORENE m0-Meldung der Zugtabelle (q3_d3 +1 / q5_d5 -1),
  (b) die Session-Majoritaet S1 (11d, Fez) / S2 (047, Fez) /
      K (Kingston-D1) an denselben Punkten — die Session-Dokumente
      tragen die Run-3-Verdict-P unter "verdict|"-Keys in punkte,
  (c) paarweise K2 vs. S1 / S2 / K.

DISCLOSURE: keine Aggregations-Lesart wurde im Freeze festgelegt —
(a)/(b)/(c) sind als ablesbare Ueberblicke gewaehlt, kein
Prereg-Bedingung und NICHT verdict-tragend.  Vorzeichenregel: zeichen
des res_v3-bzw. res-Werts (res >= 0 -> +1, res < 0 -> -1).
"""
import json
from pathlib import Path

EV_PATH = Path("pt_ram_q6_k2_eval.json")
INH_PATH = Path("pt_ram_q6_k2_inherited_eval.json")
SESSION_DOCS = [
    ("S1", Path("pt_ram_q_hardware3_eval.json")),
    ("S2", Path("pt_ram_q_hardware3_eval_rep.json")),
    ("K", Path("pt_ram_q6_kingston_inherited_eval.json")),
]


def zeich(v):
    return 1.0 if v > 0 else -1.0


def main():
    ev = json.loads(EV_PATH.read_text(encoding="utf-8"))
    inh = json.loads(INH_PATH.read_text(encoding="utf-8"))
    sessions = [(n, json.loads(p.read_text(encoding="utf-8")))
                for n, p in SESSION_DOCS]

    # K2-Kalibrier-P (die 13 'cal|'-Keys des frischen Runs 4)
    cal_keys = sorted(k for k in ev["res_fresh"] if k.startswith("cal|"))
    assert len(cal_keys) == 13, len(cal_keys)

    m0 = ev["m0_predictions"]["signs"]          # {"q3_d3": 1.0, "q5_d5": -1.0}
    assert m0 == {"q3_d3": 1.0, "q5_d5": -1.0}, m0
    # Kreuzcheck: m0 kommt aus der Zugtabelle des Freeze (nie re-fit)
    prereg = json.loads(Path("pt_ram_q6_k2_prereg.json").read_text(
        encoding="utf-8"))
    zug_m0 = prereg["zugtabelle"]["m0_predictions"]
    for arm in ("q3_d3", "q5_d5"):
        assert float(zug_m0[arm]) == m0[arm], arm

    rows, g_m0, f_m0, g_maj, f_maj = [], 0, 0, 0, 0
    pairwise = {name: {"gleich": 0, "flip": 0} for name, _ in sessions}
    for key in cal_keys:
        _, arm, P = key.split("|")
        k2s = zeich(ev["res_fresh"][key])
        vals = []
        for name, doc in sessions:
            roww = doc["punkte"].get(f"verdict|{arm}|{P}")
            assert roww is not None, (name, key)
            s = zeich(roww["res_v3"])
            vals.append(s)
            if s == k2s:
                pairwise[name]["gleich"] += 1
            else:
                pairwise[name]["flip"] += 1
        c1, c_1 = vals.count(1.0), vals.count(-1.0)
        maj = 1.0 if c1 > c_1 else (-1.0 if c_1 > c1 else 0.0)
        ok_m0, ok_maj = (m0[arm] == k2s), (maj == k2s)
        g_m0 += bool(ok_m0)
        f_m0 += not ok_m0
        g_maj += bool(ok_maj)
        f_maj += not ok_maj
        rows.append({"key": key, "arm": arm, "P": int(P), "k2": k2s,
                     "sessions": dict(zip((n for n, _ in sessions), vals)),
                     "maj": maj, "m0": m0[arm],
                     "gleich_m0": ok_m0, "gleich_maj": ok_maj})

    unanim_breaks = [r["key"] for r in rows
                     if not r["gleich_maj"]
                     and len(set(r["sessions"].values())) == 1]
    out = {"_disclosure": (
        "0-QPU-Probe, NICHT verdict-tragend; registrierter Slot "
        "zeichen_stabilitaet_kalibrier vom gefrorenen Eval (808883f) "
        "unbefuellt gelassen — hier nachgeholt mit NACHGELAGERTEN "
        "Aggregations-Lesarten (a) gefrorene m0-Meldung, (b) Session-"
        "Majoritaet, (c) paarweise; keine war im Freeze als Bedingung "
        "fixiert"),
        "prereg_md5": "ef7029764f0c192d69712674bd161822",
        "n_points": len(rows),
        "a_vs_m0_gefroren": {"gleich": g_m0, "flip": f_m0},
        "b_vs_session_majoritaet": {"gleich": g_maj, "flip": f_maj},
        "c_pairwise": {name: dict(pairwise[name], n=len(rows))
                       for name, _ in sessions},
        "unanimitaets_breche": unanim_breaks,
        "rows": rows}
    Path("scratches/h_ram_q6_k2_zeichen_probe_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, sort_keys=False) + "\n",
        encoding="utf-8")

    print("K2-Kalibrier-Zeichen (13 Punkte):")
    print("  (a) vs gefrorene m0-Meldung:", g_m0, "gleich |", f_m0, "flip")
    print("  (b) vs Session-Majoritaet :",
          g_maj, "gleich |", f_maj, "flip")
    for name, _ in sessions:
        print(f"  (c) vs {name}: {pairwise[name]['gleich']} gleich | "
              f"{pairwise[name]['flip']} flip")
    print("  m0-Abgleich gegen Prereg-Zugtabelle: OK")
    print("  Unanimitaets-Breche (K2 bricht einstimmiges Tripel):",
          len(unanim_breaks), unanim_breaks)
    for r in rows:
        sess = " ".join(f"{n}{int(v):+d}" for n, v in r["sessions"].items())
        print(f"    {r['key']:20s} k2 {int(r['k2']):+d}  {sess}  "
              f"maj {int(r['maj']):+d}  "
              f"{'GLEICH' if r['gleich_maj'] else 'FLIP'}")


if __name__ == "__main__":
    main()