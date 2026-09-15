"""
EXPERIMENT 032 - Ququint auf IBMQ, Phase 3b: Fez-Runner (SamplerV2).

Der EINZIGE QPU-Griff des Experiments: EIN SamplerV2-Job auf ibm_fez,
12 Circuits (phi_C, phi_D, sep_C x5, sep_D x5 in Phase-2-Reihenfolge),
8192 Shots, TOKEN1 (IBMQ_TOKEN), TOKEN2 unberuehrt. Das gefrorene Prereg
(pt_ququint_prereg, md5 committed vor diesem Modul) wird im Pfad geladen
und md5-verifiziert, BEVOR submitted wird (Anti-Sharpshooter).

Struktur: alle Funktionen ausser run_phase3 sind reine Datentransformation
ohne Netz. run_phase3 ist die einzige Funktion, die Service/Backend/Sampler
instantiiert — KEIN Test ruft sie ungemockt (Tests: offline mit
GenericBackendV2/Aer/SimpleNamespace-Mocks).

Der lokale SamplerV2-Pfad (Tests, mode=AerSimulator) benutzt method=
"statevector": die density_matrix-Methode von Aer kennt 'cry' nicht
(gelernt beim ersten End-to-End-Versuch). Die ISA-Circuits fuer den echten
Job kennen nur rz/sx/x/ecr + measure — dort ist das unmaterial.
"""

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import SamplerV2

from pt_prereg_audit import audit_run as _audit_run
from pt_ququint_ibmq import reject_leakage
from pt_ququint_ibmq_aer import (
    _counts64_to_vec,
    sep_witness_from_counts,
    witness_from_counts,
    witness_job_layout,
)
from pt_ququint_prereg import (
    BACKEND_NAME,
    CIRCUIT_ORDER,
    DECISION_RULE,
    N_SHOTS,
    load_frozen_prereg,
)

CONFOUND_LIMIT = 0.05
PREREG_PATH = "pt_ququint_fez_prereg.json"
RESULTS_PATH = "pt_ququint_fez_results.json"
AUDIT_PATH = "pt_ququint_fez_audit.json"
_RUNTIME_GATE_BASIS_1Q = {"rz", "sx", "x", "measure", "barrier", "delay", "id", "reset"}


# === ZUGRIFF (nur von run_phase3 benutzt; Tests mocken diese Funktionen) ===


def load_token(env_path=".env"):
    """TOKEN1 (IBMQ_TOKEN) aus .env — TOKEN2 wird nie gelesen."""
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("IBMQ_TOKEN="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("IBMQ_TOKEN nicht in .env")


def get_service(token):
    from qiskit_ibm_runtime import QiskitRuntimeService
    return QiskitRuntimeService(channel="ibm_quantum_platform", token=token)


def get_backend(service):
    return service.backend(BACKEND_NAME)


# === ISA-BATCH (12 Circuits gegen das echte Target transpiliert) ===


def isa_batch(backend, circuits=None):
    """Transpiliert den 12-Circuit-Batch ISA gegen das Backend-Target.

    Reihenfolge = CIRCUIT_ORDER = Phase-2-Reihenfolge. Liefert (isa_circuits,
    report) mit per-Circuit-2q-Gate-Counts — die ISA-Gate-Counts gehen in
    das Result (§Z.14-Ist-Budget, ggü. Phase-2-Soll: 45 cx).
    """
    if circuits is None:
        layout = witness_job_layout()
        circuits = [layout["phi_C"], layout["phi_D"]] + layout["sep_C"] + layout["sep_D"]
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    isa = pm.run(list(circuits))
    per_circuit = {}
    total_two_q = 0
    for name, circ in zip(CIRCUIT_ORDER, isa):
        ops = circ.count_ops()
        two_q = int(sum(n for g, n in ops.items() if g not in _RUNTIME_GATE_BASIS_1Q))
        per_circuit[name] = {"ops": {str(k): int(v) for k, v in ops.items()},
                             "two_q": two_q, "depth": int(circ.depth())}
        total_two_q += two_q
    report = {"circuit_names": list(CIRCUIT_ORDER), "per_circuit": per_circuit,
              "total_two_q": total_two_q}
    return isa, report


# === SUBMISSION (nur von run_phase3 benutzt) ===


def submit(sampler, isa_circuits, shots=8192):
    """EIN SamplerV2-Job: alle 12 Circuits, default_shots, DD XX (Prereg)."""
    sampler.options.default_shots = int(shots)
    if hasattr(sampler.options, "dynamical_decoupling"):
        sampler.options.dynamical_decoupling.enable = True
        sampler.options.dynamical_decoupling.sequence_type = "XX"
    return sampler.run(list(isa_circuits))


def collect_counts(job_result, n_circuits=12):
    """V2-Result -> Liste von Counts-Dicts (result[i].data.meas.get_counts())."""
    return [job_result[i].data.meas.get_counts() for i in range(int(n_circuits))]


def counts_to_vec(counts_dict):
    """SamplerV2-Counts (Bitstring-Keys) -> 64-dim RAW-Counts-Vektor.

    int(key, 2) ist der qiskit little-endian Index == Phase-1 logical_index.
    """
    return _counts64_to_vec(counts_dict)


# === EVALUATION (pure Datentransformation — vom Prereg entschieden) ===


def _leakage_rate(counts_vec):
    rep = reject_leakage(np.asarray(counts_vec, dtype=float))
    return float(rep["leakage_rate"])


def evaluate(counts_list, prereg, job_meta=None):
    """Wertet den 12-Circuit-Counts-Batch gegen das gefrorene Prereg aus.

    Flat-Keys (phi_margin_pass/sep_margin_pass/confound_pass + Margin-Werte)
    auf Top-Level — genau die Aussagen-Menge, die pt_prereg_audit
    (compare_statement_sets + evaluate_decision_rule) benoetigt. bands_hold
    ist die SEKUNDAERE Band-Pruefung gegen die STRESS-Bänder (die Regel
    selbst ist die Sign-Prüfung).
    """
    counts = [counts_to_vec(c) for c in counts_list]
    n_shots = int(round(counts[0].sum()))
    phi_c, phi_d = counts[0], counts[1]
    sep_c, sep_d = counts[2:7], counts[7:12]

    phi = witness_from_counts(phi_d)
    sep = sep_witness_from_counts(sep_d)
    p_phi_c = phi_c / float(n_shots)
    p_sep_c = sum(c / float(n_shots) for c in sep_c) / float(len(sep_c))
    confound = float(np.max(np.abs(p_phi_c - p_sep_c)))

    phi_margin_pass = bool(phi["margin"] > 0.0)
    sep_margin_pass = bool(sep["margin"] < 0.0)
    confound_pass = bool(confound <= CONFOUND_LIMIT)

    result = {
        "phi_margin_pass": phi_margin_pass,
        "sep_margin_pass": sep_margin_pass,
        "confound_pass": confound_pass,
        "phi_margin": float(phi["margin"]),
        "sep_margin": float(sep["margin"]),
        "confound_max_diff": confound,
        "phi_v_hat": float(phi["v_hat"]),
        "phi_se": float(phi["se"]),
        "sep_v_hat": float(sep["v_hat"]),
        "sep_se": float(sep["se"]),
        "leakage_rate_phi_C": _leakage_rate(phi_c),
        "leakage_rate_sep_C": float(np.mean([_leakage_rate(c) for c in sep_c])),
        "leakage_rate_phi_D": _leakage_rate(phi_d),
        "leakage_rate_sep_D": float(np.mean([_leakage_rate(c) for c in sep_d])),
        "n_shots": n_shots,
        "n_circuits": len(counts),
        "emulated": False,
        "decision_rule": prereg["decision_rule"],
        "bands_hold": _check_bands(result=None, margins={
            "phi_margin": phi["margin"],
            "sep_margin": sep["margin"],
            "confound_max_diff": confound,
        }, prereg=prereg),
    }
    if job_meta:
        result.update(job_meta)
    result["rule_holds"] = bool(_evaluate_rule(prereg["decision_rule"], result))
    return result


def _evaluate_rule(rule_str, result):
    """Die Prereg-Regel via pt_prereg_audit-Sandbox auswerten."""
    from pt_prereg_audit import evaluate_decision_rule
    return evaluate_decision_rule(rule_str, dict(result))


def _check_bands(result, margins, prereg):
    """Band-Mitgliedschaft (sekundaer, STRESS-modell-basiert, dokumentiert)."""
    bands = prereg["prediction_bands"]
    out = {}
    for key in ("phi_margin", "sep_margin", "confound_max_diff"):
        lo, hi = bands[key]["band"]
        out[key] = bool(lo <= margins[key] <= hi)
    return out


def write_result(result, path=RESULTS_PATH):
    """Result-JSON ins Repo (Ergebnisse-ins-Repo-Mandat)."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1, ensure_ascii=False)
    return path


def audit_verdict(prereg_path, results_path, audit_path=AUDIT_PATH):
    """pt_prereg_audit.audit_run: Prereg (Challenge) vs. Result (Response)."""
    verdict = _audit_run(prereg_path, results_path)
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(verdict, f, indent=1, ensure_ascii=False)
    return verdict


# === DER EINZIGE QPU-GRIFF (nie in Tests ungemockt aufgerufen) ===


def run_phase3(prereg_path=PREREG_PATH, results_path=RESULTS_PATH,
               audit_path=AUDIT_PATH, shots=N_SHOTS):
    """Prereg (md5-verifiziert) -> ISA -> EIN Fez-Job -> Auswertung -> JSON.

    Die einzige Funktion mit Netz-Zugriff. Reihenfolge ist bewusst:
    load_frozen_prereg (Tamper-Check) VOR jedem Backend-Kontakt.
    """
    prereg = load_frozen_prereg(prereg_path)

    token = load_token()
    service = get_service(token)
    backend = get_backend(service)
    backend_name = str(getattr(backend, "name", BACKEND_NAME))
    print(f"[phase3] backend={backend_name}")

    isa, report = isa_batch(backend)
    print(f"[phase3] ISA total 2q gates: {report['total_two_q']} "
          f"(phi_D={report['per_circuit']['phi_D']['two_q']})")

    sampler = SamplerV2(mode=backend)
    job = submit(sampler, isa, shots=shots)
    job_id = job.job_id()
    print(f"[phase3] job submitted: {job_id} (12 circuits, {shots} shots each)")

    job_result = job.result()
    counts = collect_counts(job_result, len(CIRCUIT_ORDER))

    result = evaluate(counts, prereg, job_meta={
        "backend": backend_name,
        "job_id": job_id,
        "shots_per_circuit": int(shots),
        "isa_gate_report": report,
    })
    write_result(result, path=results_path)
    verdict = audit_verdict(prereg_path, results_path, audit_path=audit_path)
    print(f"[phase3] verdict: {verdict['status']} | rule_holds={result['rule_holds']} "
          f"| phi_margin={result['phi_margin']:+.4f} sep_margin={result['sep_margin']:+.4f} "
          f"| confound={result['confound_max_diff']:.4f}")
    return result