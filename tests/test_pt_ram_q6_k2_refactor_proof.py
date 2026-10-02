# -*- coding: utf-8 -*-
"""EXPERIMENT 051 (H-RAM-Q-6 Leg D2/D3) — Refaktor-Beweis + K2-Einheiten.

Beweis-Kette (Phase H-RAM-Q-6-K2):
  * Builder-Defaultpfad bit-identisch nach der pts/cal-Refaktorierung
    (committeter Fingerprint 13d78d1f..., VOR Refaktor aufgenommen;
    Konvention: pro Circuit sha256 aus Instruktionstupeln, dann sha256
    ueber name+circuit-sha in Reihenfolge).
  * Eval-Defaultpfad bit-identisch (committeter Fingerprint 37925a1e...
    des 044-Eval-Dokuments nach Abzug von evaluated_at_utc).
  * Run-4-Rotationsregel: Kalibrier = Run-3-Verdict (Liste UND Records
    bit-exakt), frisch = strikt kleinste Primzahl > letzte+30 ueber der
    erweiterten Union; d-Invarianz (d=q^2, q^3).
  * Zugtabelle aus den DREI committeten Sessions: 15 Pool / 11 excluded,
    M0 = (+1, -1); die gefrorenen ex-ante-Meldungen werden heute wieder
    GLEICH erzeugt (Freeze-Guard).
  * Scoring-Reinheit: Mehrheit/Tiefe, 12/13-Kante, M0-Guard, D3-Drop,
    K2-Verdict-Reihenfolge.
"""
import hashlib
import json

import pt_ram_q_hardware3_aer as h3a
import pt_ram_q_hardware3_eval as h3e
import pt_ram_q6_k2 as k2
import pt_ram_q6_kingston as k6

BUILDER_FP = "13d78d1fcd03d4f7d343b62fda282a1052b772d1142a019f3baa06eaf3aa9d0e"
EVAL_FP = "37925a1e602370127ceb4f254982467b43e2ffd2c03a9afc3383c869f6557da6"
RUN4_Q3 = [223, 263, 317, 419, 503, 647, 727, 829]
RUN4_Q5 = [503, 587, 647, 709, 727]


def _fp_qc(qc):
    parts = [str(qc.num_qubits), str(qc.num_clbits)]
    for inst in qc.data:
        parts.append("|".join([
            inst.operation.name,
            ",".join(repr(float(complex(p).real))
                     for p in inst.operation.params),
            ",".join(str(qc.find_bit(q).index) for q in inst.qubits),
            ",".join(str(qc.find_bit(c).index) for c in inst.clbits)]))
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def _builder_fp(pts=None, cal=None):
    h = hashlib.sha256()
    for c in h3a.build_hardware_circuit_set(pts, cal):
        h.update(c["name"].encode("utf-8"))
        h.update(_fp_qc(c["circuit"]).encode("utf-8"))
    return h.hexdigest()


def _circuit_tups(circuits):
    return [(c["name"], _fp_qc(c["circuit"])) for c in circuits]


def test_builder_defaultpfad_bit_identisch():
    assert len(h3a.build_hardware_circuit_set()) == 116
    assert _builder_fp() == BUILDER_FP


def test_builder_dual_path_default_gleich_explicit_old():
    """Der Refaktor-Explicits-Pfad MUSS den Default reproduzieren — sonst
    waere der Default ein Sonderfaall, den die pts/cal-Parametrisierung
    nicht erfasst."""
    default = h3a.build_hardware_circuit_set()
    via_path = h3a.build_hardware_circuit_set(h3a._point_pts(),
                                              h3a._cal_pts())
    assert _circuit_tups(default) == _circuit_tups(via_path)


def test_builder_frisch_steuert_neues_grid():
    pts, cal = k2.fresh_points()
    circ = h3a.build_hardware_circuit_set(pts, cal)
    assert len(circ) == 116
    # frisches Verdict-P kommt mit eigenem struct/loschmidt vor
    names = [c["name"] for c in circ]
    assert any(n.startswith("struct_q3_d3_223_") for n in names)
    assert any(n.startswith("loschmidt_q5_d5_709") for n in names)
    # Anker/Kontrollen UNVERAENDERT an 181/467 (Vertrag)
    assert any(n.startswith("ladder_q3_d3_181_r") for n in names)
    assert any(c.get("kind") == "negative_control" for c in circ)
    # der frische Pfad ist NICHT der Default (anderes Grid)
    assert _builder_fp(pts, cal) != BUILDER_FP


def test_eval_defaultpfad_bit_identisch():
    doc = h3e.evaluate()
    doc.pop("evaluated_at_utc", None)
    fp = hashlib.sha256(json.dumps(doc, sort_keys=True,
                                   separators=(",", ":")).encode()).hexdigest()
    assert fp == EVAL_FP


def test_run4_rotationsregel():
    grid = k2.run4_grid()
    assert grid["q3_d3"]["cal"] == list(k2.h3.NEW_Q3_POINTS)
    assert grid["q5_d5"]["cal"] == list(k2.h3.NEW_Q5_POINTS)
    assert grid["q3_d3"]["verdict"] == RUN4_Q3
    assert grid["q5_d5"]["verdict"] == RUN4_Q5
    # frische P liegen UEBERHAUPT nicht in der 30er-Union (strikte Regel)
    ext = k2.extended_union()
    for P in RUN4_Q3 + RUN4_Q5:
        assert P not in ext
    # Run-3-Praezedenz: Kreuz-arm-Schnitt erlaubt (044: 467/613/691)
    assert set(k2.h3.NEW_Q3_POINTS) & set(k2.h3.NEW_Q5_POINTS) == \
        {467, 613, 691}


def test_fresh_grid_structure():
    pts, cal = k2.fresh_points()
    assert len(pts) == 13 and len(cal) == 13
    assert sorted(P for (a, P) in pts if a == "q3_d3") == RUN4_Q3
    assert sorted(P for (a, P) in pts if a == "q5_d5") == RUN4_Q5
    # Anker 181 (q3) und 467 (beide Arme) liegen im frischen KALIBRIER-Bein
    assert ("q3_d3", 181) in cal and ("q5_d5", 467) in cal
    assert len(k2.extended_union()) == 30


def test_cP_freeze_rotation_bit_exakt():
    pts, cal = k2.fresh_points()
    cP = k2.cP_freeze_fresh(pts, cal)   # assertet intern 1e-12-Rotation
    assert len(cP) == 26
    src = k2.h3.load_frozen_prereg()["prediction_freeze"]["cP_freeze"]
    for key, v in cP.items():
        set_, arm, P = key.split("|")
        if set_ == "cal":
            assert abs(v - float(src["verdict|%s|%s" % (arm, P)])) < 1e-12


def test_prereg_frozen_selbstconsistent():
    doc = k2.load_frozen_prereg()
    assert doc["status"] == "REGISTERED_NOT_MEASURED"
    assert k6.self_md5(k2.PREREG_PATH) == k2.PREREG_MD5
    assert doc["zugtabelle"]["train"]["n_pool"] == 15
    assert doc["zugtabelle"]["train"]["n_excluded"] == 11
    m0 = doc["zugtabelle"]["m0_predictions"]
    assert m0["q3_d3"] == 1.0 and m0["q5_d5"] == -1.0
    for entry in k2.source_md5s():
        with open(entry["path"], "rb") as fh:
            assert hashlib.md5(fh.read()).hexdigest() == entry["md5"]


def test_zugtabelle_und_meldungen_reproduzieren_freeze():
    """Freeze-Guard: ex-ante-Tabellen aus den committeten Quellen sind
    HEUTE bit-gleich den gefrorenen (keinDrift nach dem Freeze)."""
    doc = k2.load_frozen_prereg()
    evals = [(p, k2._load_json(p)) for p in k2.FROZEN_INPUTS]
    train = k2.build_train_table(evals)
    assert json.dumps(train, sort_keys=True) == \
        json.dumps(doc["zugtabelle"]["train"], sort_keys=True)
    pts, _ = k2.fresh_points()
    assert k2.d2_predictions(train, pts) == \
        json.loads(json.dumps(doc["d2_leg"]["predictions"]))
    assert k2.d3_predictions(train, pts) == \
        json.loads(json.dumps(doc["d3_leg"]["predictions"]))


def test_train_table_mehrheit_tiefe():
    assert k2.majority([1.0, -1.0, 1.0]) == 1.0
    assert k2.majority([-1.0, -1.0, 1.0]) == -1.0
    assert k2.majority([1.0, -1.0]) is None       # 2-eligible-Gleichstand
    assert k2.majority([]) is None
    assert k2.majority([None, 1.0]) == 1.0        # None ist kein Votum


def test_pool_groesse_und_exklusion():
    evals = [(p, k2._load_json(p)) for p in k2.FROZEN_INPUTS]
    train = k2.build_train_table(evals)
    assert train["n_pool"] == 15 and train["n_excluded"] == 11
    # Pool-Zeichen sind +/-1.
    assert all(r["sign"] in (1.0, -1.0) for r in train["pool"].values())
    # Anker-467 in BEIDEN Armen im Pool — mit ENTGEGENGESSETZEN Zeichen
    # (467-Flip der Phase 11d/047):
    assert train["pool"]["verdict|q3_d3|467"]["sign"] == 1.0
    assert train["pool"]["verdict|q5_d5|467"]["sign"] == -1.0
    # Session-Anker-181 (q3) nicht poolfaehig; Grund-Dokumentation exakt
    assert train["excluded"]["verdict|q3_d3|181"]["reason"] == \
        "weniger als 2 eligible Sessions"
    # 3-Session-Punkte (sowohl Fez als auch Kingston eligible):
    for pk, s in (("verdict|q3_d3|797", 1.0), ("cal|q5_d5|499", 1.0),
                  ("verdict|q5_d5|673", -1.0)):
        assert train["pool"][pk]["n_eligible"] == 3, pk
        assert train["pool"][pk]["sign"] == s, pk


def test_score_d2_thresholds():
    a = k2.ALPHA_FAMILY2
    assert k2.binom_sf_one_sided(12, 13) <= a     # 0.001709
    assert k2.binom_sf_one_sided(11, 13) > a      # 0.011226
    assert k2.binom_sf_one_sided(5, 5) > a        # 0.03125 (q5-allein)
    preds = {"prediction": {}}
    for arm, plist in (("q3_d3", RUN4_Q3), ("q5_d5", RUN4_Q5)):
        preds["prediction"][arm] = {}
        for f in k2.D2_FAMILY:
            preds["prediction"][arm][f] = {str(P): 1.0 if arm == "q3_d3"
                                           else -1.0 for P in plist}
    res = {"verdict|q3_d3|%d" % P: +0.5 for P in RUN4_Q3}
    res.update({"verdict|q5_d5|%d" % P: -0.5 for P in RUN4_Q5})
    # M0 NICHT vergleichbar (None-Zeichen) -> 13/13 nur ueber alpha'
    out = k2.score_d2(res, preds, {"q3_d3": None, "q5_d5": None})
    assert out["verdict"] == k2.V_D2_PARTIAL
    assert all(not r["beats_m0"] for r in out["members"].values())
    # M0 entgegengesetzt gefroren -> 13/13 schlaegt M0 -> CONFIRMED
    out2 = k2.score_d2(res, preds, {"q3_d3": -1.0, "q5_d5": +1.0})
    assert out2["verdict"] == k2.V_D2_CONFIRMED
    for f in k2.D2_FAMILY:
        assert out2["members"][f]["hits"] == 13
        assert out2["members"][f]["m0"]["hits"] == 0
    # 10/13: kein Member ueber alpha' -> REFUTED (Bestaetigung schwer)
    res10 = dict(res)
    for pk in ("verdict|q3_d3|223", "verdict|q3_d3|263",
               "verdict|q5_d5|503"):
        res10[pk] = -res10[pk]
    out3 = k2.score_d2(res10, preds, {"q3_d3": -1.0, "q5_d5": +1.0})
    assert out3["verdict"] == k2.V_D2_REFUTED
    for f in k2.D2_FAMILY:
        assert out3["members"][f]["hits"] == 10
        assert k2.binom_sf_one_sided(10, 13) > a


def test_score_d3_thresholds_and_drop():
    preds = {"prediction": {}}
    for arm, plist in (("q3_d3", RUN4_Q3), ("q5_d5", RUN4_Q5)):
        preds["prediction"][arm] = {str(P): 1.0 if arm == "q3_d3" else -1.0
                                    for P in plist}
    res = {"verdict|q3_d3|%d" % P: +0.5 for P in RUN4_Q3}
    res.update({"verdict|q5_d5|%d" % P: -0.5 for P in RUN4_Q5})
    out = k2.score_d3(res, preds)
    assert out["n"] == 13 and out["hits"] == 13
    assert out["p"] == k2.binom_sf_one_sided(13, 13) <= k2.D3_ALPHA
    assert out["verdict"] == k2.V_D3_CONFIRMED
    # Kante n = 7 < n_elig_floor -> VOID (ohne Wertung)
    keep = ["verdict|q3_d3|%d" % P for P in RUN4_Q3[:4]] + \
        ["verdict|q5_d5|%d" % P for P in RUN4_Q5[:3]]
    res7 = {r: v for r, v in res.items() if r in keep}
    out7 = k2.score_d3(res7, preds)
    assert out7["n"] == 7 and out7["verdict"] == k2.V_D3_VOID_FILTER
    # Ohne-Meldung (Gleichstand) faellt WEG — weder n noch hits
    predst = {"prediction": {"q3_d3": {"223": None},
                             "q5_d5": {str(P): -1.0 for P in RUN4_Q5}}}
    resT = {"verdict|q3_d3|223": 0.5}
    resT.update({"verdict|q5_d5|%d" % P: -0.5 for P in RUN4_Q5})
    outT = k2.score_d3(resT, predst)
    assert outT["n"] == 5 and outT["n_dropped_ohne_meldung"] == 1
    assert all(r.get("dropped_ohne_meldung")
               for r in outT["rows"] if r["pred"] is None)


def test_k2_verdict_reihenfolge():
    d2 = {"verdict": k2.V_D2_REFUTED}
    d3 = {"verdict": k2.V_D3_REFUTED}
    d2c = {"verdict": k2.V_D2_CONFIRMED}
    assert k2.decide_k2(True, "x", 13, d2, d3) == k2.V_DEGENERAT
    assert k2.decide_k2(False, h3e.V_VOID, 13, d2, d3) == k2.V_VOID_KAPPA
    assert k2.decide_k2(False, h3e.V_CONFIRMED, 7, d2, d3) == k2.V_VOID_NOISE
    assert k2.decide_k2(False, h3e.V_REFUTED, 13, d2, d3) == \
        "D2:%s|D3:%s" % (k2.V_D2_REFUTED, k2.V_D3_REFUTED)
    assert k2.decide_k2(False, h3e.V_REFUTED, 13, d2c, d3) == \
        "D2:%s|D3:%s" % (k2.V_D2_CONFIRMED, k2.V_D3_REFUTED)


def test_k2_binom_delegiert_wie_k6():
    for k in (8, 10, 12, 13):
        assert k2.binom_sf_one_sided(k, 13) == k6.binom_sf_one_sided(k, 13)