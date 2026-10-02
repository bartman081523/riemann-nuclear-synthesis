# -*- coding: utf-8 -*-
"""EXPERIMENT 051 (H-RAM-Q-6 Leg D2/D3): gefrorene Auswertung des
Kingston-Raws (davfridj371s73dmqstg) auf dem FRISCHEN Run-4-Grid.

Drei Stufen, strikt getrennt (wie das D1-Bein, §10.32-Muster):
  1. Wrapper-Bindings — NUR in diesem Modul: raw experiment/hypothesis/
     leg == K2, backend == Kingston, job_id == Job-ID-File, transpile ==
     Gate-Totals (D1-Lesart 'transpile_seed' <-> 'seed_transpiler'),
     registered_run_config == Prereg, counts_md5 rekonsistent,
     ABWESEND-Liste hält (kein Verdict-Kanal im Raw).
  2. INHERIT — h3e.evaluate(...) auf dem FRISCHEN Grid mit den K2-
     Quellen; das GEFRORENE 044-v3b-Gesetz (baaca1f6) bleibt unberührt,
     w_b/w_a/Verdict-Map-Struktur kommen aus den 044-Konstanten.  Die
     Kontrollen t3/t4/t5/t6 des geerbten Docs entscheiden K2_DEGENERAT
     (gefrorener K2-verdict_map-Text: 'geerbte Kontrollen (t3/t4/t5/t6)
     verletzt -> keine Auswertung').
  3. D2/D3 — res_map_all über ALLE 26 frischen Punkte -> score_d2 (m0
     aus der Zugtabelle, NULL-MODELL, nie re-fit) + score_d3 (1-NN) ->
     decide_k2 (K2_DEGENERAT -> K2_VOID_KAPPA -> K2_VOID_NOISE ->
     Komposit).  n_elig_total zaehlt ueber die 13 VERDICT-P ('eligible
     gesamt < 8 von 13').

Kein Freeze-Nachtrag: alles hier steht so im Prereg (ef702976,
committet 08e022c VOR jeder Messung); dieses Modul NUR Auswertung.
"""
import json
import hashlib
from datetime import datetime, timezone

import pt_ram_q_hardware3_aer as h3a
import pt_ram_q_hardware3_eval as h3e
import pt_ram_q6_k2 as k2
import pt_ram_q6_k2_qpu as k2q
import pt_ram_q6_kingston as k6
import pt_ram_q6_kingston_qpu as k6q

STATUS_EVAL = "K2_EVALUATED"
BANNED_IN_RAW = ("kappa", "ratio", "gamma", "verdict", "band", "kappa_hat",
                 "res_v3")
KONTROLLEN_KEYS = ("t3_identity_two_ways", "t4_negative_must_not_fire",
                   "t5_gate_set_frozen", "t6_mass_conservation")


def check_raw(raw_path=k2.RAW_PATH, gate_path=k2.ISA_GATE_PATH,
              job_id_path=k2.JOB_ID_PATH, prereg_path=k2.PREREG_PATH):
    """Stufe 1: Wrapper-Bindings; AssertionError bei jeder Verletzung."""
    raw = k2._load_json(raw_path)
    with open(gate_path, encoding="utf-8") as fh:
        gate = json.load(fh)
    prereg = k2.load_frozen_prereg(prereg_path)

    assert raw["experiment"] == k2.EXPERIMENT, raw["experiment"]
    assert raw["hypothesis"] == k2.HYPOTHESIS, raw["hypothesis"]
    assert raw["leg"] == k2.LEG, raw["leg"]
    assert raw["backend"] == k2.BACKEND_NAME, raw["backend"]
    assert raw["status"] == "QPU_RAW_FETCHED", raw["status"]
    with open(job_id_path, encoding="utf-8") as fh:
        job_id = fh.read().strip()
    assert raw["job_meta"]["job_id"] == job_id, raw["job_meta"]["job_id"]

    assert k6.validate_isa_gate(gate) is True
    assert gate["experiment"] == k2.EXPERIMENT, gate["experiment"]
    assert gate["prereg_md5"] == k2.PREREG_MD5, gate["prereg_md5"]
    # D1-Lesart (13f): Gate-'transpile_seed' <-> Raw-'seed_transpiler'
    totals = {"optimization_level": int(gate["optimization_level"]),
              "seed_transpiler": int(gate["transpile_seed"]),
              "isa_2q_total": int(gate["total_two_q"]),
              "isa_2q_max": int(gate["max_two_q"])}
    assert raw["transpile"] == totals, raw["transpile"]
    assert raw["registered_run_config"] == \
        prereg["hardware_parameters"]["run_config"], raw["registered_run_config"]

    assert raw["n_circuits"] == 116, raw["n_circuits"]
    assert len(raw["counts"]) == raw["n_circuits"], len(raw["counts"])
    md5 = k2q.counts_md5([e["counts"] for e in raw["counts"]])
    assert md5 == raw["counts_md5"], \
        ("counts_md5 divergiert", md5, raw["counts_md5"])
    for banned in BANNED_IN_RAW:
        assert banned not in raw, banned
    return {"raw_binding_ok": True, "gate_binding_ok": True,
            "counts_md5_rekomputiert": md5, "job_id": job_id,
            "isa_totals": totals, "banned_abwesend": list(BANNED_IN_RAW)}


def degenerat_kontrollen(inherited):
    """Gefrorener K2-Verdict-Text: jede Verletzung der geerbten
    Kontrollen t3/t4/t5/t6 kippt in K2_DEGENERAT (keine Auswertung).
    t1/t2 sind inherited-Grautext (Office-Suite-Bein), nicht in der
    Liste."""
    kontrollen = inherited["kontrollen"]
    flags = {key: bool(kontrollen[key]["ok"]) for key in KONTROLLEN_KEYS}
    return (not all(flags.values()), flags)


def inherited_eval(points=None, cal=None):
    """Stufe 2: h3e.evaluate auf dem frischen Grid (K2-Quellen) und
    Schreiben unter k2.INHERITED_EVAL_PATH."""
    if points is None and cal is None:
        points, cal = k2.eval_grid()
    doc = h3e.evaluate(raw_path=k2.RAW_PATH, stage3_path=k2.STAGE3_PATH,
                       isa_path=k2.ISA_GATE_PATH,
                       prereg_path=k2.PREREG_PATH,
                       points=points, cal=cal,
                       stage3_prereg_md5=k2.PREREG_MD5)
    h3e.write_eval(doc, k2.INHERITED_EVAL_PATH)
    return doc


def res_fresh_from(inherited):
    res = k2.res_map_all(inherited)
    assert len(res) == 26, len(res)
    return res


def eligible_verdict(res_fresh):
    """'eligible gesamt < 8 von 13': Zaehlung NUR ueber die 13
    VERDICT-P (set 'verdict') — Kalibrier-P zaele NICHT hier."""
    n_elig = 0
    for pkey, res in sorted(res_fresh.items()):
        if pkey.startswith("verdict|") and abs(res) >= k2.ELIGIBLE_ABS_MIN:
            n_elig += 1
    return n_elig


def m0_signs_from_prereg(prereg):
    """Arm-Vorzeichen des NULL-MODELLS aus der Zugtabelle (freeze VOR
    Messung; nie re-fit, nicht in der Bonferroni-Familie)."""
    m0 = prereg["zugtabelle"]["m0_predictions"]
    return {arm: m0[arm] for arm in h3a.ARMS}


def write_eval(doc, path=k2.EVAL_PATH):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    return path


def vmap():
    """Gefrorene K2-verdict_map aus dem Prereg (keine Modul-Kopie)."""
    return k2.load_frozen_prereg()["k2_verdict_map"]


def run_eval(results_path=k2.EVAL_PATH, points=None, cal=None):
    """Komplette Kette: Bindings -> INHERIT -> D2/D3 -> Verdict."""
    binding = check_raw()
    inherited = inherited_eval(points=points, cal=cal)
    deg_failed, deg_flags = degenerat_kontrollen(inherited)
    res_fresh = res_fresh_from(inherited)
    n_elig = eligible_verdict(res_fresh)
    prereg = k2.load_frozen_prereg()
    m0 = m0_signs_from_prereg(prereg)
    d2 = k2.score_d2(res_fresh, prereg["d2_leg"]["predictions"], m0)
    d3 = k2.score_d3(res_fresh, prereg["d3_leg"]["predictions"])
    verdict = k2.decide_k2(deg_failed, inherited["verdict"], n_elig,
                           d2, d3)
    doc = {
        "experiment": k2.EXPERIMENT, "hypothesis": k2.HYPOTHESIS,
        "leg": k2.LEG, "status": STATUS_EVAL,
        "prereg_md5": k2.PREREG_MD5,
        "raw_provenance": {
            "path": k2.RAW_PATH,
            "job_id": binding["job_id"],
            "counts_md5": binding["counts_md5_rekomputiert"],
            "isa_totals": binding["isa_totals"],
        },
        "integritaet": binding,
        "inherited_eval": {
            "path": k2.INHERITED_EVAL_PATH,
            "law_binding": "044-v3b GEFROREN (baaca1f6), unberuehrt",
            "prereg_md5_bytes_liesart": inherited["prereg_md5"],
            "prereg_md5_notiz": "h3e hasht bei uebergebenem prereg_path "
                                "die DATEI-BYTES (3926b0c79); der "
                                "gefrorene Vertragswert (canonical ohne "
                                "md5-Feld) ist ef702976 — D1-Lesart "
                                "nutzte die Konstante, hier die Bytes; "
                                "beides MEINT dasselbe Prereg",
            "verdict": inherited["verdict"],
            "verdict_map_text": inherited["verdict_map_text"],
            "kontrollen": inherited["kontrollen"],
            "verdict_inputs": inherited["verdict_inputs"],
            "gamma_arm": inherited["gamma_arm"],
        },
        "k2_degenerat_kontrollen": {"failed": deg_failed,
                                    "flags": deg_flags,
                                    "regel": vmap()[k2.V_DEGENERAT]},
        "eligible_abs_min": k2.ELIGIBLE_ABS_MIN,
        "res_fresh": res_fresh,
        "n_elig_total": n_elig,
        "n_elig_regel": vmap()[k2.V_VOID_NOISE],
        "m0_predictions": {"signs": m0,
                           "source": "zugtabelle.m0_predictions "
                                     "(NULL-MODELL, freeze VOR Messung)"},
        "d2": d2, "d3": d3,
        "registered_expectation": {
            "d2": prereg["d2_leg"]["registered_expectation"],
            "d3": prereg["d3_leg"]["registered_expectation"],
        },
        "verdict": verdict,
        "verdict_map_text": vmap().get(
            verdict, vmap()["sonst"]),
        "decided_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    write_eval(doc, results_path)
    return doc


if __name__ == "__main__":
    doc = run_eval()
    print(f"inherited verdict: {doc['inherited_eval']['verdict']}")
    print(f"n_elig: {doc['n_elig_total']}/13")
    print(f"D2: {doc['d2']['verdict']} | D3: {doc['d3']['verdict']}")
    print(f"K2 verdict: {doc['verdict']}")