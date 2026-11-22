# -*- coding: utf-8 -*-
"""RAM-Q Stage-3 ISA-Report (EXPERIMENT 044, H-RAM-Q-4, Phase 11c) —
Freeze-B''-Voraussetzung.

116 Circuits (pt_ram_q_hardware3_aer.build_hardware_circuit_set: 39 Verdict-
struct + 13 Verdict-loschmidt + 6 Echo-Leiter + 39 Kalibrier-struct + 13
Kalibrier-loschmidt + 4 negative Kontrollen + 2 Readout-Kalibrierung,
Minimalregister d=q) ISA gegen das ECHTE ibm_fez-Target transpiliert
(optimization_level 3, gefroren im Prereg run_config), 2q-Counts gegen die
Safeguard-Ceilings (per_circuit_2q_max 120, total_2q_max 6000; Erwartung
max ~84-96 2q (Leiter r=8, q5), total ~600-700 2q — Prognose aus der
Phase-10-Messung 493 2q/max 84).

Auth only — KEIN QPU-Job hier; der Fez-Job folgt erst nach Freeze B''
(zwei-Freeze-Architektur des Preregs: der Payload-md5 bleibt unangetastet —
w_B'' ist WIEDERVERWENDET, der ISA-Report wird committed).  Backend-Target-
Laden ist kein Quota-Kontakt (§Z.14-Phase-3b-Praezedenz).  TOKEN1-Disziplin:
IBMQ_TOKEN aus .env (pt_ququint_fez.load_token) — TOKEN2 wird NIE gelesen.
"""
import json

from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_aer as s3a

# 1q-/Non-Gate-Ops, die NICHT als 2q-Zaehler gehen (Phase-3c-Muster, §Z.14).
_RUNTIME_GATE_BASIS_1Q = {"rz", "sx", "x", "measure", "barrier", "delay",
                          "id", "reset"}

BACKEND_NAME = "ibm_fez"
TRANSPILE_SEED = s3a.TRANSPILE_SEED
ISA_PATH3 = "pt_ram_q_isa3_report.json"


def isa_report(backend, circuits=None):
    """Transpiliert den 116-Circuit-Satz ISA gegen das Backend-Target.

    Liefert (isa_circuits, report): report haelt per-Circuit-2q-Counts,
    Tiefe, Ops und die Summen — die ISA-Gate-Counts sind das Ist-Budget
    gegen die Safeguards (per_circuit_2q_max 120, total_2q_max 6000).
    """
    if circuits is None:
        circuits = s3a.build_hardware_circuit_set()
    names = [c["name"] for c in circuits]
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend,
                                      seed_transpiler=TRANSPILE_SEED)
    isa = pm.run([c["circuit"] for c in circuits])
    per_circuit = {}
    total_two_q = 0
    max_two_q = 0
    for c, circ in zip(circuits, isa):
        ops = circ.count_ops()
        two_q = int(sum(n for g, n in ops.items()
                        if g not in _RUNTIME_GATE_BASIS_1Q))
        per_circuit[c["name"]] = {"kind": c["kind"], "arm": c.get("arm"),
                                  "set": c.get("set"), "P": c.get("P"),
                                  "ops": {str(k): int(v)
                                          for k, v in ops.items()},
                                  "two_q": two_q, "depth": int(circ.depth())}
        total_two_q += two_q
        max_two_q = max(max_two_q, two_q)
    report = {"circuit_names": names, "per_circuit": per_circuit,
              "total_two_q": total_two_q, "max_two_q": max_two_q,
              "n_circuits": len(circuits)}
    return isa, report


def ceiling_check(report):
    """Safeguard-Pruefung: per-Circuit- und Total-Ceilings aus dem Prereg.

    Liefert {"ok", "violations", "per_circuit_max", "total_max"} —
    ok=False ist ein Freeze-B''-Stopper (kein QPU-Job bei Verletzung;
    safeguard_limits/isa_ceilings.abort: Abbruch, Re-Freeze).
    """
    viol = []
    for name, e in report["per_circuit"].items():
        if e["two_q"] > h3.ISA_2Q_PER_CIRCUIT_MAX:
            viol.append({"name": name, "two_q": e["two_q"],
                         "ceiling": h3.ISA_2Q_PER_CIRCUIT_MAX})
    if report["total_two_q"] > h3.ISA_2Q_TOTAL_MAX:
        viol.append({"name": "__total__", "two_q": report["total_two_q"],
                     "ceiling": h3.ISA_2Q_TOTAL_MAX})
    return {"ok": not viol, "violations": viol,
            "per_circuit_max": h3.ISA_2Q_PER_CIRCUIT_MAX,
            "total_max": h3.ISA_2Q_TOTAL_MAX}


def run_isa_report(backend_getter=None, results_path=ISA_PATH3):
    """Orchestrierung: 116 Circuits -> echtes Target -> Report JSON.

    backend_getter (Tests: FakeFez) ersetzt load_token/get_service/
    service.backend(BACKEND_NAME).  Default: ECHTES ibm_fez via TOKEN1
    (Auth only — kein Job).
    """
    if backend_getter is None:
        import pt_ququint_fez as fez
        backend_getter = lambda: fez.get_backend(fez.get_service(
            fez.load_token()))  # noqa: E731
    circuits = s3a.build_hardware_circuit_set()
    backend = backend_getter()
    _isa, report = isa_report(backend, circuits)
    check = ceiling_check(report)
    doc = {"experiment": h3.EXPERIMENT, "hypothesis": h3.HYPOTHESIS,
           "backend": backend.name,
           "transpile_seed": TRANSPILE_SEED,
           "optimization_level": 3,
           "run_config_frozen": h3.load_frozen_prereg(),
           "isa_ceilings": {"per_circuit_2q_max": h3.ISA_2Q_PER_CIRCUIT_MAX,
                            "total_2q_max": h3.ISA_2Q_TOTAL_MAX},
           "n_circuits": report["n_circuits"],
           "total_two_q": report["total_two_q"],
           "max_two_q": report["max_two_q"],
           "per_circuit": report["per_circuit"],
           "ceiling_check": check,
           "verdict": "ISA_OK" if check["ok"] else "ISA_CEILING_VIOLATED"}
    if results_path:
        with open(results_path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1, sort_keys=True)
    return doc


if __name__ == "__main__":
    doc = run_isa_report()
    check = doc["ceiling_check"]
    print(f"backend: {doc['backend']} | circuits: {doc['n_circuits']}")
    print(f"total 2q: {doc['total_two_q']} (ceiling "
          f"{h3.ISA_2Q_TOTAL_MAX}) | max per-circuit 2q: {doc['max_two_q']} "
          f"(ceiling {h3.ISA_2Q_PER_CIRCUIT_MAX})")
    print(f"verdict: {doc['verdict']}")
    if not check["ok"]:
        for v in check["violations"]:
            print("  VIOLATION:", v)