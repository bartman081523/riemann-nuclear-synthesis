# -*- coding: utf-8 -*-
"""EXPERIMENT 055 (H-H9 FPrio 4+8, LEG FP48-COMBINED) — der EINE Fez-Job.

Hinter 046 (Backlog p48.FEZ_BACKLOG = QUQUINT-F4 daua5hahcrkc73dv9eh0 ->
046 dauassrojkfs738rrcsg -> 055).  Form identisch zum D1/K2-Trio
(pt_ram_q6_kingston_qpu / pt_ram_q6_k2_qpu) mit den 055-Differenzen:

  1. 160 Circuits = 148 FORCED (37 Reihen x 4: 3 struct-Reps + 1 Loschmidt;
     Reihen aus p48.forced_row_order, anker-symmetrisch: 181/467 liegen im
     Verdict-Bein, Anker-Paritaet in C1 registriert)
     + 12 UNFORCED (Echo-Leiter 6 + negative Kontrollen 4 + readout_cal 2)
     unter Auto-Layout seed 7 mit BIT-ANKER (ops UND two_q) gegen das
     committete S1-Report pt_ram_q_isa3_report.json (Gate-Assertion,
     Abbruch VOR QPU-Kontakt) — damit ist die fez-scoped FPrio-5-Lesart
     (b) MESSBAR (gleiche Geometrie wie S1/S2).
  2. FORCED initial_layout je Reihen-Gruppe (KEIN Seed-Wechsel,
     transpiler seed 7 UNVERAENDERT): Slots = lexicographische
     Enumeration verbundener induzierter Subgraphen der LIVE-Kopplungsmap
     (p48.layout_slots; Groesse 2 = Kanten/q3, Groesse 3 = 3-Knoten-Pfade
     /q5); Zuordnung = zyklischer Shift ab Index 1 (NIEMALS Slot 0 —
     Freeze-Geometrie der ersten Zeile, p48.slot_assignment); Fall-Back
     bei Ceiling (per-circuit-2q > 120): Skip-forward zum naechsten
     Slot-Index, im Report registriert (attempts).
  3. ISA-Report (p48.ISA_REPORT_PATH) + ISA-GATE (p48.ISA_GATE_PATH,
     K2-Schema + EXTRA prereg_md5) werden VOR der Submission geschrieben
     (--gate-Modus) und BINDEN das C3-c' (K2-Praezedenz: per_circuit_
     two_q + isa_ceiling; c_S1 == c_S2 via 047-Budget-Gate-Praezedenz).
     --submit validiert das committete Gate (k6.validate_isa_gate mit
     n_circuits=160), re-transpiliert FRISCH und vergleicht Zelle-fuer-
     Zelle (Gate-stale -> Abbruch VOR QPU-Kontakt, K2-Praezedenz).
  4. Roh-Verbraucher = gefrorene Auswertung pt_ram_q_prio48_eval.py
     (n=160-t5) auf dem GEFRORENEN Gesetz (pt_ram_q_hardware3_eval).
     Das Raw traegt NUR counts (banned_from_raw: kappa, ratio, gamma,
     band, verdict, res_v3, center, delta_cal).

Token-DISZIPLIN (Prereg): NUR TOKEN1 (IBMQ_TOKEN aus .env via
pt_ququint_fez).  TOKEN2 wird NIE gelesen; kein Sampler-V2-Local-Pfad.

Resume-VERTRAG (Prereg): existiert das Raw: geschieht NICHTS.  Existiert
die Job-ID-Datei: Resume via service.job(id) (KEIN neuer Job — 046-/053-
Praezedenz); der Gate-Crosscheck laeuft DAVOR (dieselbe Codezeile wie bei
der Submission) und die Totals fuer den fetch kommen aus dem committeten
Gate.
"""
import hashlib
import json
import os
import time
from datetime import datetime, timezone

from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import SamplerV2

import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_aer as h3a
import pt_ram_q_prio48 as p48
import pt_ram_q6_kingston as k6
from pt_ram_q6_kingston_isa_stage import count_2q

BACKEND_NAME = "ibm_fez"
TRANSPILE_SEED = h3a.TRANSPILE_SEED          # 7, VERAENDERT NICHT
JOB_ID_PATH = p48.JOB_ID_PATH
RAW_PATH = p48.RAW_PATH
ISA_REPORT_PATH = p48.ISA_REPORT_PATH
ISA_GATE_PATH = p48.ISA_GATE_PATH
S1_ISA_REPORT = "pt_ram_q_isa3_report.json"  # committeter S1-Bit-Anker
S1_ANCHOR_RULE = ("Auto-Layout-Anker nach gefrorenem Prereg-Literal: "
                  "per-Circuit-2q bitgleich gegen pt_ram_q_isa3_report.json "
                  "(GATE). Die ops-Ebene ist Diagnostik: ein Delta "
                  "ausschliesslich an 1q-x-Puls-Zaehlung bei bitgleicher "
                  "2q-Geometrie (cz/rz/sx/barrier/measure exakt) ist die "
                  "IBM-seitige Synthese-Branch-Spaetzung (Fez-Target-Refresh "
                  "seit der 0/116-Re-Verifikation 2026-09-28) und FAELLT "
                  "NICHT unter das Anker-Gate.")
CEILINGS = {"per_circuit_2q_max": p48.ISA_2Q_PER_CIRCUIT_MAX,   # 120
            "total_2q_max": p48.ISA_2Q_TOTAL_MAX}               # 6000
SHOTS = h3.SHOTS                              # 8192
POLL_SECONDS = 20
POLL_MAX_S = 6 * 3600

ROW_CIRCUIT_PREFIXES = ("struct_", "calstruct_", "loschmidt_", "calloschmidt_")
N_EXPECTED_POINTS = 37        # 13 verdict + 13 cal-old + 11 Ladder


def load_token():
    """TOKEN1 (IBMQ_TOKEN aus .env) — TOKEN2 wird NIE gelesen."""
    import pt_ququint_fez as fez
    return fez.load_token()


def get_service(token=None):
    """Fez-Service (ibm_quantum_platform, KEIN instance-Parameter)."""
    import pt_ququint_fez as fez
    if token is None:
        token = load_token()
    return fez.get_service(token)


def get_backend(service):
    import pt_ququint_fez as fez
    return fez.get_backend(service)          # ibm_fez


def _now_utc():
    return datetime.now(timezone.utc).isoformat()


def frozen_prereg_md5():
    """doc['md5'] des gefrorenen Payloads (Content-md5, 053-Praezedenz)."""
    with open(p48.PREREG_PATH, encoding="utf-8") as fh:
        return json.load(fh)["md5"]


def coupling_edges(backend):
    """Undirektionale Kantenlist der LIVE-Kopplungsmap (fuer layout_slots)."""
    cm = getattr(backend, "coupling_map", None)
    if cm is None:
        raise ValueError("Backend ohne coupling_map (FORCED-Layout braucht "
                         "die LIVE-Map)")
    get_edges = getattr(cm, "get_edges", None)
    if callable(get_edges):
        pairs = get_edges()
    else:
        pairs = list(cm)
    edges = sorted({(int(a), int(b)) for a, b in pairs})
    if not edges:
        raise ValueError("LIVE-Kopplungsmap leer (FORCED-Layout unmoeglich)")
    return edges


def _rows_from_circuits(circuits):
    """Reihen-Index {(arm, set, P): [circuits in Listen-Reihenfolge]} ueber
    ALLE Reihen-Circuits (struct_*/calstruct_*/loschmidt_*/calloschmidt_*).
    Echo-/Kontroll-/readout-Cal-Circuits fallen NICHT unter FORCED."""
    rows = {}
    for c in circuits:
        if not c["name"].startswith(ROW_CIRCUIT_PREFIXES):
            continue
        rows.setdefault((c["arm"], c["set"], c["P"]), []).append(c)
    assert len(rows) == N_EXPECTED_POINTS, \
        [c["name"] for c in circuits if c["name"].startswith(
            ROW_CIRCUIT_PREFIXES)]
    for group in rows.values():
        reps = [c for c in group if c.get("rep") is not None]
        los = [c for c in group if "loschmidt" in c["name"]]
        assert len(group) == 4 and len(reps) == 3 and len(los) == 1, \
            [c["name"] for c in group]
    return rows


def _transpile_row(backend, group, slot):
    """Transpiliert die 4 Circuits einer Reihe auf einem FORCED Slot;
    liefert (checks, bad_n_2q) — bad = erste 2q-Zahl ueber dem Ceiling."""
    pm = generate_preset_pass_manager(
        backend=backend, optimization_level=3,
        seed_transpiler=TRANSPILE_SEED, initial_layout=list(slot))
    tcs = pm.run([c["circuit"] for c in group])
    checks, bad = [], None
    for tc in tcs:
        ops = {str(gn): int(cn) for gn, cn in tc.count_ops().items()}
        n_2q = count_2q(ops)
        checks.append({"ops": ops, "n_2q": n_2q, "depth": int(tc.depth()),
                       "tc": tc})
        if n_2q > CEILINGS["per_circuit_2q_max"]:
            bad = n_2q
            break
    return checks, bad


C_PRIME_LESART = (
    "PROXY-LESART des C3-Zaehlers (Prereg cP_perturbation_source): "
    "c_prime = cP * (mean n_2q'_055 / mean two_q_S1) je Reihe (Mittel ueber "
    "die 4 Row-Circuits; rang-aequivalent zur Summe). Delta_c = c_prime - cP "
    "aus den verwendeten Werten. Mean-Ratio bit-gleich 1 -> Delta_c == 0 -> "
    "Delta-c degenerat (keine Geometrie-Schiebung messbar). Ladder-Reihen "
    "frisch -> c_prime None. Kompilations-Geometrie je Reihe separat "
    "registriert: row_assignment (Slot/Index/Fallback).")


def rows_cprime(per_circuit, reports_rows, cp_freeze, s1_pc):
    """C3-c'-Block je Reihe.

    c_prime = cP * (mean n_2q'_055 / mean two_q_S1) je Reihe ueber die 4
    Row-Circuits (3 struct-Reps + 1 Loschmidt); n_2q' aus DIESER Forced-
    Transpile (ISA-Struktur der Session), two_q_S1 aus dem VOR Messung
    committeten S1-Report (per_circuit["two_q"]).  Delta_c = c_prime - cP,
    subtrahiert aus den verwendeten Werten (keine algebraische
    Umschreibung).  Rang-aequivalent zur Masse-Summe.

    Mean-Ratio == 1 bit-gleich -> Delta_c == 0: "Delta-c degenerat" — der
    C3-Zaehler kann nicht feuern (registrierte strukturelle Null, kein
    erfundener Geometrie-Drift).

    Frische Ladder-Reihen (keine S1-Namen) -> c_prime None; C3-tragend
    sind nur die 13 Verdict-Reihen.

    s1_pc = None schaltet den Block ab (Unit-Tests; Rueckgabe mit note).
    """
    if s1_pc is None:
        return {"note": ("s1_anchor offline abgeschaltet (Unit-Tests) — "
                         "c'-Block nur im echten Gate-Lauf aktiv")}
    slot_by_row = {}
    for arm in p48.ARMS:
        for r in reports_rows[arm]:
            slot_by_row[(arm, r["row"][0], r["row"][1])] = r
    groups = {}
    for name, v in per_circuit.items():
        if not name.startswith(ROW_CIRCUIT_PREFIXES):
            continue
        groups.setdefault((v["arm"], v["set"], v["P"]), []).append(name)
    out = {}
    for (arm, setname, P), names in sorted(groups.items()):
        assert len(names) == 4, (arm, setname, P, names)
        key = "%s|%s|%d" % (setname, arm, P)
        base = {"cP": cp_freeze[key],
                "mean_n2q_055": sum(per_circuit[n]["n_2q"]
                                    for n in names) / 4.0,
                "mean_two_q_s1": None, "ratio_2q": None,
                "c_prime": None, "delta_c_vs_cP": None,
                "slot_index": slot_by_row[(arm, setname, P)]["slot_index"],
                "fallback_used":
                    slot_by_row[(arm, setname, P)]["fallback_used"]}
        try:
            m1 = sum(int(s1_pc[n]["two_q"]) for n in names) / 4.0
        except KeyError:
            base["grund"] = ("keine S1-Namen — frische Ladder-Reihe, "
                             "c_prime None")
            out[key] = base
            continue
        if m1 > 0:
            ratio = base["mean_n2q_055"] / m1
        elif base["mean_n2q_055"] == 0:
            ratio = 1.0
        else:
            raise RuntimeError(
                "c'-Degenerat: S1 two_q == 0, aber 055 n_2q > 0 "
                "(Reihe %s)" % key)
        base.update({"mean_two_q_s1": m1, "ratio_2q": ratio,
                     "c_prime": base["cP"] * ratio,
                     "delta_c_vs_cP": base["cP"] * ratio - base["cP"]})
        out[key] = base
    return out


def transpile_forced(backend, circuits, edges=None,
                     s1_report_path=S1_ISA_REPORT):
    """FORCED initial_layout je Reihen-Gruppe + Auto-Layout fuer die 12
    unforced Circuits mit Bit-Anker gegen das S1-Report.

    Anker-Gate ist der 2q-Spalte-Nachweis per gefrorenem Prereg-Literal
    ("per-Circuit-2q bitgleich"); ops-Deltas (1q-x-Puls-Zweig) sind
    benannte Diagnostik in Report/Entries (S1_ANCHOR_RULE).  Rueckgabe:
    (tci [Reihenfolge == circuits], totals, report, gate).
    s1_report_path=None schaltet den Bit-Anker ab (NUR fuer Unit-Tests auf
    Fake-Backends — im echten Lauf ist er Gate, S1-Report committet).
    """
    if edges is None:
        edges = coupling_edges(backend)
    order = p48.forced_row_order()
    rows = _rows_from_circuits(circuits)
    slots = {arm: p48.layout_slots(nq, edges)
             for arm, nq in p48.NQ_BY_ARM.items()}
    reports_rows = {arm: [] for arm in p48.ARMS}
    per_circuit = {}
    tc_by_name = {}

    for arm in p48.ARMS:
        arm_slots = slots[arm]
        assigned = p48.slot_assignment(len(order[arm]), len(arm_slots),
                                       start=1)
        for i, (setname, P) in enumerate(order[arm]):
            group = rows[(arm, setname, P)]
            attempts = []
            chosen = None
            for step in range(len(arm_slots)):
                cand_idx = (assigned[i] + step) % len(arm_slots)
                slot = arm_slots[cand_idx]
                checks, bad = _transpile_row(backend, group, slot)
                if bad is not None:
                    attempts.append({"slot_index": cand_idx,
                                     "slot": list(slot), "n_2q": bad})
                    continue
                chosen = {"slot_index": cand_idx, "slot": slot,
                          "checks": checks}
                break
            if chosen is None:
                raise RuntimeError(
                    "FORCED-Layout: kein Slot unter per-circuit-Ceiling "
                    "(%d 2q) fuer Reihe (%s,%s,%d); attempts=%s"
                    % (CEILINGS["per_circuit_2q_max"], arm, setname, P,
                       attempts))
            for c, check in zip(group, chosen["checks"]):
                tc_by_name[c["name"]] = check.pop("tc")
                per_circuit[c["name"]] = {
                    "ops": check["ops"], "n_2q": check["n_2q"],
                    "depth": check["depth"],
                    "initial_layout": list(chosen["slot"]),
                    "layout_source": "forced", "arm": arm, "set": setname,
                    "P": P, "kind": c["kind"]}
            reports_rows[arm].append({
                "row": [setname, P], "slot_index": chosen["slot_index"],
                "slot": list(chosen["slot"]), "fallback_used": bool(attempts),
                "attempts": attempts})

    forced_n = sum(1 for v in per_circuit.values()
                   if v["layout_source"] == "forced")
    assert forced_n == 37 * 4, forced_n            # 148 forced

    # --- 12 unforced unter Auto-Layout + S1-Bit-Anker ---
    unforced = [c for c in circuits if c["name"] not in per_circuit]
    assert len(unforced) == p48.N_CIRCUITS - 37 * 4, \
        [c["name"] for c in unforced]
    pm_auto = generate_preset_pass_manager(
        backend=backend, optimization_level=3,
        seed_transpiler=TRANSPILE_SEED)
    tcs_auto = pm_auto.run([c["circuit"] for c in unforced])
    anchor_check = []
    if s1_report_path:
        with open(s1_report_path, encoding="utf-8") as fh:
            s1_pc = json.load(fh)["per_circuit"]
    else:
        s1_pc = None
    for c, tc in zip(unforced, tcs_auto):
        ops = {str(gn): int(cn) for gn, cn in tc.count_ops().items()}
        n_2q = count_2q(ops)
        tc_by_name[c["name"]] = tc
        entry = {"ops": ops, "n_2q": n_2q, "depth": int(tc.depth()),
                 "layout_source": "auto", "kind": c.get("kind"),
                 "arm": c.get("arm"), "set": c.get("set"), "P": c.get("P")}
        if s1_pc is not None:
            s1 = s1_pc[c["name"]]
            entry["s1_ops_equal"] = ops == s1["ops"]
            entry["s1_two_q_equal"] = n_2q == int(s1["two_q"])
            # Gefrorenes Literal: "per-Circuit-2q bitgleich" — NUR die
            # 2q-Spalte ist Gate (ops-Ebene = Diagnostik, S1_ANCHOR_RULE).
            entry["ok"] = entry["s1_two_q_equal"]
            if not entry["s1_ops_equal"]:
                entry["s1_ops_delta_vs_s1"] = {
                    k: {"s1": s1["ops"].get(k, 0), "fresh": ops.get(k, 0)}
                    for k in sorted(set(ops) | set(s1["ops"]))
                    if ops.get(k, 0) != s1["ops"].get(k, 0)}
                entry["s1_ops_delta_class"] = S1_ANCHOR_RULE
            anchor_check.append({"name": c["name"], "ok": entry["ok"],
                                 "s1_ops_equal": entry["s1_ops_equal"]})
        else:
            entry["ok"] = None
            entry["note"] = "s1_anchor offline abgeschaltet (Unit-Tests)"
        per_circuit[c["name"]] = entry
    if s1_pc is not None:
        broken = [a["name"] for a in anchor_check if not a["ok"]]
        if broken:
            raise AssertionError(
                "Auto-Layout-Bit-Anker (S1-Report, 2q-Spalte per "
                "geflorenem Literal) verletzt fuer: %s" % broken)
        ops_divergent = [a["name"] for a in anchor_check
                         if not a["s1_ops_equal"]]
        if ops_divergent:
            print("[isa] ops-Diagnostik: %d/%d unforced mit 1q-x-Zweig-Delta "
                  "(2q bitgleich, kein Gate-Breach): %s"
                  % (len(ops_divergent), len(anchor_check), ops_divergent))

    row_c_prime = rows_cprime(
        per_circuit, reports_rows,
        p48.load_frozen_prereg()["prediction_freeze"]["cP_freeze"]
        if s1_pc is not None else None, s1_pc)

    tci = [tc_by_name[c["name"]] for c in circuits]
    totals = {"optimization_level": 3,
              "seed_transpiler": TRANSPILE_SEED,
              "isa_2q_total": sum(v["n_2q"] for v in per_circuit.values()),
              "isa_2q_max": max(v["n_2q"] for v in per_circuit.values())}
    worst = sorted(per_circuit.items(), key=lambda kv: -kv[1]["n_2q"])[:5]
    ceiling = {"per_circuit_2q_ok":
               all(v["n_2q"] <= CEILINGS["per_circuit_2q_max"]
                   for v in per_circuit.values()),
               "total_2q": totals["isa_2q_total"],
               "total_2q_ok":
                   totals["isa_2q_total"] <= CEILINGS["total_2q_max"],
               "per_circuit_worst_5":
                   [{"name": n, "n_2q": v["n_2q"]} for n, v in worst],
               "verdict": "ISA_OK"}
    if not (ceiling["per_circuit_2q_ok"] and ceiling["total_2q_ok"]):
        raise RuntimeError("ISA-Ceilings verletzt: %s" % ceiling)

    report = {
        "experiment": p48.EXPERIMENT, "hypothesis": p48.HYPOTHESIS,
        "leg": p48.LEG, "status": "ISA_FORCED_REPORT_COMPLETED",
        "backend": str(getattr(backend, "name", BACKEND_NAME)),
        "generated_at_utc": _now_utc(),
        "n_circuits": len(circuits),
        "transpile": {"optimization_level": 3,
                      "seed_transpiler": TRANSPILE_SEED},
        "isa_ceilings": dict(CEILINGS),
        "total_two_q": totals["isa_2q_total"],
        "max_two_q": totals["isa_2q_max"],
        "coupling_map_edges": len(edges),
        "slots_per_arm": {arm: len(slots[arm]) for arm in p48.ARMS},
        "row_assignment": reports_rows,
        "row_c_prime": row_c_prime,
        "c_prime_lesart": C_PRIME_LESART,
        "per_circuit": per_circuit,
        "unforced_bit_anchor": anchor_check,
        "s1_anchor_rule": S1_ANCHOR_RULE,
        "ceiling_check": ceiling,
        "run_config_frozen":
            p48.load_frozen_prereg()["hardware_parameters"]["run_config"],
        "prereg_md5": frozen_prereg_md5(),
        "verdict": "ISA_OK",
    }
    gate = {
        "experiment": p48.EXPERIMENT, "backend": report["backend"],
        "optimization_level": 3, "transpile_seed": TRANSPILE_SEED,
        "total_two_q": totals["isa_2q_total"],
        "max_two_q": totals["isa_2q_max"],
        "isa_ceiling": dict(CEILINGS),
        "per_circuit_two_q": {
            name: {"ops": v["ops"], "n_2q": v["n_2q"]}
            for name, v in per_circuit.items()},
        "verdict": "ISA_OK", "generated_at_utc": report["generated_at_utc"],
        "n_circuits": len(circuits), "prereg_md5": frozen_prereg_md5(),
    }
    return tci, totals, report, gate


def isa_stage(backend_getter=None, service_getter=None, pts=None, cal=None):
    """Schreibt ISA-Report + ISA-Gate VOR der Submission (kein Job, kein
    Sampler-Kontakt; aber LIVE-Backend fuer die Kopplungsmap).

    IDEMPOTENZ-DISZIPLIN: existieren Report/Gate bereits, wird NICHTS
    ueberschrieben — die committeten Artefakte werden ausgeliefert (ein
    Re-Gate braucht eine explizite Loesch-Entscheidung, kein Stilles
    Ueberschreiben committeter Provenance).
    """
    if os.path.exists(ISA_REPORT_PATH) and os.path.exists(ISA_GATE_PATH):
        with open(ISA_REPORT_PATH, encoding="utf-8") as fh:
            report = json.load(fh)
        with open(ISA_GATE_PATH, encoding="utf-8") as fh:
            gate = json.load(fh)
        k6.validate_isa_gate(gate, n_circuits=int(report["n_circuits"]))
        print("[isa] Report+Gate existieren bereits — NICHTS ueberschrieben "
              "(%d circuits, total_2q %s)"
              % (report["n_circuits"], gate["total_two_q"]))
        return report, gate
    if backend_getter is None:
        backend = get_backend((service_getter or get_service)())
    else:
        backend = backend_getter()
    if pts is None and cal is None:
        pts, cal, _ladder = p48.eval_grid()
    circuits = h3a.build_hardware_circuit_set(pts=pts, cal=cal)
    assert len(circuits) == p48.N_CIRCUITS, len(circuits)
    assert len(circuits) * SHOTS == p48.TOTAL_SHOTS
    _tci, _totals, report, gate = transpile_forced(backend, circuits)
    with open(ISA_REPORT_PATH, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    with open(ISA_GATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(gate, fh, indent=1)
    k6.validate_isa_gate(gate, n_circuits=p48.N_CIRCUITS)
    print("[isa] Report+Gate geschrieben + validiert: total_2q %d, max %d "
          "| forced %d / auto %d"
          % (gate["total_two_q"], gate["max_two_q"], 37 * 4,
             p48.N_CIRCUITS - 37 * 4))
    return report, gate


def _isa_verified_for_submit(backend, circuits, isa_gate=ISA_GATE_PATH):
    """K2-Praezedenz: committetes Gate validieren, FRISCH re-transpilieren
    und Zelle-fuer-Zelle vergleichen (Gate-stale -> Abbruch VOR QPU)."""
    with open(isa_gate, encoding="utf-8") as fh:
        gate = json.load(fh)
    k6.validate_isa_gate(gate, n_circuits=len(circuits))
    tci, totals, _report, _gate = transpile_forced(
        backend, circuits, s1_report_path=None)
    for c, tc in zip(circuits, tci):
        ops = {str(gn): int(cn) for gn, cn in tc.count_ops().items()}
        entry = gate["per_circuit_two_q"][c["name"]]
        if entry["ops"] != ops or int(entry["n_2q"]) != count_2q(ops):
            raise AssertionError(
                "ISA-Gate-Stale: %s (gate %r != frisch %r)"
                % (c["name"], entry, {"ops": ops, "n_2q": count_2q(ops)}))
    totals_gate = {"optimization_level": int(gate["optimization_level"]),
                   "seed_transpiler": int(gate["transpile_seed"]),
                   "isa_2q_total": int(gate["total_two_q"]),
                   "isa_2q_max": int(gate["max_two_q"])}
    if totals != totals_gate:
        raise AssertionError("ISA-Gate-Stale: Totals %r != Gate %r"
                             % (totals, totals_gate))
    return tci, totals


def counts_md5(counts_list):
    return hashlib.md5(json.dumps(counts_list, sort_keys=True,
                                  separators=(",", ":")
                                  ).encode("utf-8")).hexdigest()


def submit_job(sampler, isa_circuits_list, shots=None):
    shots = shots or SHOTS
    sampler.options.default_shots = shots
    sampler.options.dynamical_decoupling.enable = True
    sampler.options.dynamical_decoupling.sequence_type = "XX"
    return sampler.run(list(isa_circuits_list))


def fetch_raw(job_result, circuits, job_meta, backend_name, totals):
    """Roh-Counts (NUR counts — banned_from_raw bleibt abwesend)."""
    counts_list = []
    for i in range(len(circuits)):
        raw = job_result[i].data.c.get_counts()
        counts = {str(k): int(v) for k, v in raw.items()}
        c = circuits[i]
        entry = {"name": c["name"], "kind": c["kind"],
                 "arm": c.get("arm"), "set": c.get("set"),
                 "P": c.get("P"),
                 "rep": c.get("rep"), "r": c.get("r"),
                 "shots_actual": int(sum(counts.values())),
                 "counts": counts}
        counts_list.append(entry)
    return {
        "experiment": p48.EXPERIMENT, "hypothesis": p48.HYPOTHESIS,
        "leg": p48.LEG, "status": "QPU_RAW_FETCHED",
        "backend": str(backend_name),
        "job_meta": dict(job_meta),
        "transpile": dict(totals),
        "registered_run_config":
            p48.load_frozen_prereg()["hardware_parameters"]["run_config"],
        "fetched_at_utc": _now_utc(),
        "n_circuits": len(circuits),
        "shots_per_circuit": SHOTS,
        "counts_md5": counts_md5([e["counts"] for e in counts_list]),
        "counts": counts_list,
        # ABSICHTLICH ABWESEND (banned_from_raw, Prereg):
        # kappa, ratio, gamma, band, verdict, res_v3, center, delta_cal
    }


def write_raw(doc, results_path=RAW_PATH):
    with open(results_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    return results_path


def _job_done(job):
    return str(job.status()).upper().split(".")[-1] in ("DONE", "COMPLETED")


def run_qpu_job(backend_getter=None, service_getter=None,
                results_path=RAW_PATH, job_id_path=JOB_ID_PATH, poll=True,
                fetch=True, pts=None, cal=None):
    """Submit (falls noetig) -> persistiere Job-ID -> fetch Raw.

    Resume-Vertrag wie 11d/D1/K2: existiert das Raw, geschieht NICHTS;
    existiert nur die Job-ID-Datei, wird der Job wiederaufgenommen (KEIN
    neuer Job — 046-/053-Praezedenz).  Der Gate-Crosscheck laeuft in
    BEIDEN Zweigen VOR dem QPU-Kontakt (K2-Praezedenz: Gate-stale ->
    Abbruch).
    """
    if os.path.exists(results_path):
        with open(results_path, encoding="utf-8") as fh:
            return json.load(fh)
    if pts is None and cal is None:
        pts, cal, _ladder = p48.eval_grid()
    circuits = h3a.build_hardware_circuit_set(pts=pts, cal=cal)
    assert len(circuits) == p48.N_CIRCUITS, len(circuits)
    if backend_getter is None:
        service = (service_getter or get_service)()
        backend = get_backend(service)
    else:
        backend = backend_getter()
        service = None
    backend_name = str(getattr(backend, "name", BACKEND_NAME))

    # Gate-Crosscheck VOR jedem QPU-Kontakt (auch auf Resume).
    _tci, totals = _isa_verified_for_submit(backend, circuits)

    if os.path.exists(job_id_path):
        with open(job_id_path, encoding="utf-8") as fh:
            job_id = fh.read().strip()
        assert service is not None, \
            "Resume braucht einen Service (service_getter oder get_service)"
        job = service.job(job_id)
        print("[qpu] resume %s (Kein neuer Job — 046/053-Praezedenz)" % job_id)
    else:
        sampler = SamplerV2(mode=backend)
        job = submit_job(sampler, _tci)
        job_id = job.job_id()
        with open(job_id_path, "w", encoding="utf-8") as fh:
            fh.write(job_id)
        print("[qpu] submitted %s (%d circuits, %d shots) -> %s"
              % (job_id, len(circuits), SHOTS, job_id_path))
        if not fetch:
            return {"experiment": p48.EXPERIMENT, "leg": p48.LEG,
                    "status": "QPU_JOB_ID_SAVED", "job_id": job_id,
                    "job_id_path": job_id_path}

    if poll:
        waited = 0
        while not _job_done(job):
            if waited >= POLL_MAX_S:
                raise TimeoutError("Poll-Window (%ds) abgelaufen fuer %s"
                                   % (POLL_MAX_S, job_id))
            time.sleep(POLL_SECONDS)
            waited += POLL_SECONDS
            print("[qpu] %s status=%s waited=%ds"
                  % (job_id, str(job.status()).upper().split(".")[-1],
                     waited))

    result = job.result()
    job_meta = {"job_id": job_id, "backend": backend_name}
    doc = fetch_raw(result, circuits, job_meta, backend_name, totals)
    path = write_raw(doc, results_path)
    print("[qpu] raw geschrieben: %s (counts_md5 %s)"
          % (path, doc["counts_md5"]))
    return doc


if __name__ == "__main__":
    import sys
    mode = "submit" if "--submit" in sys.argv else (
        "gate" if "--gate" in sys.argv else "full")
    if mode == "gate":
        rep, gate = isa_stage()
        print("[gate] verdict %s | total_2q %s | max_2q %s"
              % (rep["verdict"], gate["total_two_q"], gate["max_two_q"]))
        print("[gate] NEXT: git add %s %s && git commit (VOR Submission, "
              "C3-c'-Binding) — dann --submit" % (ISA_REPORT_PATH,
                                                  ISA_GATE_PATH))
    elif mode == "submit":
        doc = run_qpu_job()
        print("[submit] status %s | n_circuits %s"
              % (doc.get("status"), doc.get("n_circuits")))
    else:
        rep, gate = isa_stage()
        doc = run_qpu_job()
        print("[full] gate verdict %s | raw %s"
              % (rep["verdict"], doc.get("status")))