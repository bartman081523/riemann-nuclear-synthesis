# -*- coding: utf-8 -*-
"""h9_echo_r8_session3.py — Deck F-Prio 5: Echo-r8-Floor, Session 3.

0 QPU, READ-ONLY auf committeten Eval-Artefakten. Kein Re-Decide, keine
Toleranz-Aenderung (H-H9-2 ist Deck-Kombinations-Hypothese, NICHT RAM-Q-Verdict).

C.2-Registrierung (Deck-Zeile 159 ff., 2026-09-29): Auf dem q5-Bein waere
κ_r(r=8) "session-invariant" — S1 (11d) 0.098154, S2 (047) 0.098027
(Delta 1.3e-3), waehrend r1 (Anker, Loschmidt-geteilt) um +0.041 driftet
(0.8274 -> 0.8686) und q3-r8 KEINEN Floor zeigt (0.9118/0.8964).
Falsifizierbare Grenze: Session 3 haelt κ_r8(q5) 0.098 ± 0.004, sonst
falsifiziert, wenn r8 um > 0.006 driftet ODER r1 NICHT mitverlaeuft (±0.05).

Session 3: der erste neue RAM-Q-Job nach 047 = EXPERIMENT 051
(K2-D2/D3-Kingston, davfridj371s73dmqstg, pt_ram_q6_k2_inherited_eval.json,
frisches Run-4-Gitter + dieselben Ladder-Anker P=181/P=467, repeats [1,2,4,8]).

ZUSATZ-Betrachtung (Kontext, kein Gate-Kriterium): D1 (EXPERIMENT 050)
maκ den κ̂-Floor auf Kingston [0.8780, 0.9846] vs Fez [0.8245, 0.9725]/[0.8602,
0.9623] — Substrat-Shift +0.0178..+0.0535 an der Unter-/Oberkante. Die
Session-3-Pruefung auf Kingston konfundiert dadurch Substrat mit Kalibrier-
Epoche; die Fez-Scopes-Auswertung (b) ist die engere Fassung des C.2-Claims.
"""
import json

S1 = "pt_ram_q_hardware3_eval.json"          # 11d (044), fez, TOKEN1
S2 = "pt_ram_q_hardware3_eval_rep.json"      # 047 rep, fez, TOKEN1
S3 = "pt_ram_q6_k2_inherited_eval.json"      # 051 K2, kingston, TOKEN2
OUT = "scratches/h9_echo_r8_session3_out.json"

KAPPA_BAND = (0.094, 0.102)   # 0.098 ± 0.004 (F-Zeile 5, Session-3-Tol)
DRIFT_MAX_R8 = 0.006          # "wenn r8 um > 0.006 drifft"
R1_WANDER = 0.05              # "r1 ... innerhalb ±0.05"


def kappa(path):
    d = json.load(open(path))
    out = {}
    for leg, dd in d["echo_ladder"].items():
        kr = dd["kappa_r"]
        out[leg] = {
            "P": dd.get("P"),
            "repeats": dd.get("repeats"),
            "r1_shared_with_loschmidt": dd.get("r1_shared_with_loschmidt"),
            "r1": float(kr["r1"]), "r2": float(kr["r2"]),
            "r4": float(kr["r4"]), "r8": float(kr["r8"]),
            "fit_kappa_block": dd.get("fit_kappa_block"),
        }
    return out


def main():
    t1, t2, t3 = kappa(S1), kappa(S2), kappa(S3)
    tab = {"S1_11d_fez": t1, "S2_047_fez": t2, "S3_k2_kingston": t3}

    q5_r8 = [t1["q5_d5"]["r8"], t2["q5_d5"]["r8"], t3["q5_d5"]["r8"]]
    q5_r1 = [t1["q5_d5"]["r1"], t2["q5_d5"]["r1"], t3["q5_d5"]["r1"]]
    q3_r8 = [t1["q3_d3"]["r8"], t2["q3_d3"]["r8"], t3["q3_d3"]["r8"]]

    # Deck-Pins S1/S2 (Deck schreibt 6 Dezimal; K2 aus dem committeten
    # Eval voll repr-gepinnt)
    pins_ok = {
        "s1_r8_0.098154": abs(q5_r8[0] - 0.09815425987043148) < 1e-12,
        "s2_r8_0.098027": abs(q5_r8[1] - 0.09802712700369914) < 1e-12,
        "s1_vs_s2_delta_1.3e-3": abs(q5_r8[0] - q5_r8[1]) < 3e-3,
        "s1_r1_0.8274": abs(q5_r1[0] - 0.8274049627184941) < 1e-12,
        "s2_r1_0.8686": abs(q5_r1[1] - 0.868557336621455) < 1e-12,
        "s3_k2_r8_0.4655": abs(q5_r8[2] - 0.46546656869948566) < 1e-12,
        "s3_k2_r1_0.8886": abs(q5_r1[2] - 0.8885623316189076) < 1e-12,
    }

    band_q5_r8 = KAPPA_BAND[0] <= q5_r8[2] <= KAPPA_BAND[1]
    drift_r8_vs_s2 = abs(q5_r8[2] - q5_r8[1])
    drift_r8_vs_s1 = abs(q5_r8[2] - q5_r8[0])
    r1_move_s2 = q5_r1[2] - q5_r1[1]
    r1_move_s1 = q5_r1[2] - q5_r1[0]
    r1_mit = (abs(r1_move_s2) <= R1_WANDER) and (abs(r1_move_s1) <= R1_WANDER)

    as_written = {
        "kappa_r8_q5_in_band_0.098_pm_0.004": band_q5_r8,
        "r8_drift_vs_S2": drift_r8_vs_s2,
        "r8_drift_vs_S1": drift_r8_vs_s1,
        "r8_drift_kleiner_gleich_0.006": drift_r8_vs_s2 <= DRIFT_MAX_R8
            and drift_r8_vs_s1 <= DRIFT_MAX_R8,
        "r1_move_vs_S2": r1_move_s2,
        "r1_move_vs_S1": r1_move_s1,
        "r1_mitverlauf_bei_pm_0.05": r1_mit,
        "falsifikator_r8_drift": (drift_r8_vs_s2 > DRIFT_MAX_R8)
            or (drift_r8_vs_s1 > DRIFT_MAX_R8),
        "falsifikator_r1_nicht_mit": not r1_mit,
    }
    as_written["verdict_lesart_a_wie_geschrieben"] = (
        "H-H9-2-Floor KIPPT auf Session 3 (K2-Kingston): r8 0.098 -> 0.4655"
        if (as_written["falsifikator_r8_drift"]
            or not band_q5_r8)
        else "H-H9-2-Floor HAELT")

    fez_scoped = {
        "lesart": "same-substrate (fez) Session-3-Invarianz — K2-Kingston "
                  "konfundiert Substrat mit Kalibrier-Epoche (D1-Band-Shift "
                  "[0.8780, 0.9846]); der Fez-scope Test braucht einen dritten"
                  " Fez-RAM-Q-Job = kombiniertes F-Prio-4+8-Job hinter 046",
        "getestet": False,
    }

    q3_verhaelt = {
        "kein_q3_floor_pattern": (max(q3_r8) - min(q3_r8)) > 0.05,
        "q3_r8_s1_s2_s3": q3_r8,
    }

    out = {
        "experiment": "051-K2-Session-3 (F-Prio 5, 0 QPU)",
        "hypothesis": "H-H9-2 Echo-r8-Floor (C.2)",
        "daten": [S1, S2, S3],
        "tab": tab,
        "deck_pins": pins_ok,
        "lesart_a_wie_geschrieben": as_written,
        "lesart_b_fez_scope": fez_scoped,
        "q3_probe": q3_verhaelt,
        "integritaet": {
            "read_only_commits": True,
            "verdict_re_decide": False,
            "toleranz_aenderung": False,
        },
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)

    print("== Echo-r8-Floor, 3 Sessions ==")
    for name, t in tab.items():
        for leg in ("q5_d5", "q3_d3"):
            print(f"{name}/{leg}: r1={t[leg]['r1']:.6f} "
                  f"r2={t[leg]['r2']:.6f} r4={t[leg]['r4']:.6f} "
                  f"r8={t[leg]['r8']:.6f}  "
                  f"(fit_b {t[leg]['fit_kappa_block']:.4f})")
    print()
    print("deck_pins:", all(pins_ok.values()), pins_ok)
    print("band [0.094, 0.102] haelt:", as_written[
        "kappa_r8_q5_in_band_0.098_pm_0.004"])
    print("r8-drift vs S2/S1:", drift_r8_vs_s2, drift_r8_vs_s1,
          "| falsifikator_drift:", as_written["falsifikator_r8_drift"])
    print("r1-Verlauf vs S2/S1:", r1_move_s2, r1_move_s1,
          "| falsifikator_kein_Verlauf:", as_written[
              "falsifikator_r1_nicht_mit"])
    print(as_written["verdict_lesart_a_wie_geschrieben"])
    print("Fez-scope (b):", "UNTESTED — braucht dritten Fez-RAM-Q-Job")
    print("geschrieben:", OUT)


if __name__ == "__main__":
    main()