# -*- coding: utf-8 -*-
"""pt_v5_kingston_rep.py — EXPERIMENT 046 (H-V5R): V5-Wiederholung auf
BEIDEN Backends, Prereg pt_v5_kingston_rep_prereg.json (md5-gepinnt,
REGISTERED_NOT_MEASURED VOR jedem Job).

Unvorhergesehenes Resultat von Experiment 035 (md5 d019d587): das
Bias-Vorzeichen flippte backend-abhaengig (Fez RUN1/RUN2 beide negativ,
Kingston positiv). Diese Wiederholung misst JEDES Bein ein zweites Mal:

- kingston:  TOKEN2 (IBMQ_TOKEN2, instance "open-instance"), ibm_kingston,
             ISA-Gate = gefrorene v5.isa_accept_online-Regel.
- fez:       TOKEN1 (IBMQ_TOKEN via pt_ququint_fez), ibm_fez, KEIN
             instance-Parameter. ISA-Gate = abgeschwaechte Regel
             (names ⊆ ONLINE_2Q_NAMES, depth <= ONLINE_DEPTH_MAX) —
             ABWEICHUNG EX ANTE im Prereg dokumentiert: der FakeFez-ISA-
             Anker (two_q == 1) ist kein Kingston-Soll.

Protokoll IDENTISCH zu 035 (kein Parameter-Fontaenelewesen): ansatz_logical
-> isa_ansatz_for(backend, seed 7) -> FEZ_PARAMS gebunden -> 3 Pubs
(ops_real/ops_diag/ops_imag) -> Estimator(mode=backend), resilience_level 1,
DD XX, default_shots 8192, EIN est.run(pubs)-Aufruf. Baender/Schwellen
UNVERAENDERT aus dem gefrorenen 035-Prereg (md5 d019d587) — KEINE
Toleranz-Erhoehung (Phase-11c-Praezedenz).

Raw-Dokumente werden VOR der Auswertung geschrieben und committed
(§Z.14-Disziplin); die Auswertung (--eval) rechnet gegen die gefrorenen
Baender und die im Prereg REGISTRIERTEN H-V5R-1/H-V5R-2-Klassifikationen.
"""
import argparse
import hashlib
import json
import os

from qiskit_ibm_runtime import Estimator, QiskitRuntimeService

import pt_ququint_fez as fez
import pt_v5_kingston as v5

EXPERIMENT = "046-ququint-v5-repetition-both-backends"
HYPOTHESIS = "H-V5R"
PREREG_PATH = "pt_v5_kingston_rep_prereg.json"
RAW_PATHS = {
    "kingston": "pt_v5_kingston_rep_kingston_raw.json",
    "fez": "pt_v5_kingston_rep_fez_raw.json",
}
JOBID_PATHS = {
    "kingston": "pt_v5_kingston_rep_kingston_job_id.txt",
    "fez": "pt_v5_kingston_rep_fez_job_id.txt",
}
EVAL_PATH = "pt_v5_kingston_rep_eval.json"

BACKEND_NAMES = {"kingston": "ibm_kingston", "fez": "ibm_fez"}


def prereg_md5(path=PREREG_PATH):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def load_rep_prereg(path=PREREG_PATH):
    """Repetitions-Prereg laden, md5 des INHALTS nicht pinnen (die Datei
    IST das Freeze); md5 wird beim Laden gemeldet."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def make_service_for(leg):
    """TOKEN-DISZIPLIN: kingston -> TOKEN2 + instance "open-instance";
    fez -> TOKEN1 via pt_ququint_fez, KEIN instance-Parameter
    (Praezedenz pt_ququint_fez)."""
    if leg == "kingston":
        return v5._make_service()
    if leg == "fez":
        token = fez.load_token()
        return QiskitRuntimeService(channel="ibm_quantum_platform",
                                    token=token)
    raise ValueError(leg)


def isa_gate_for(leg, counts):
    """Registrierte ISA-Gates (EX ANTE im Prereg)."""
    if leg == "kingston":
        return {"rule": "v5.isa_accept_online (gefroren, 035)",
                "ok": bool(v5.isa_accept_online(counts))}
    if leg == "fez":
        names = set(counts.get("names", []))
        ok = (names <= set(v5.ONLINE_2Q_NAMES)
              and counts.get("depth", 10 ** 9) <= v5.ONLINE_DEPTH_MAX)
        return {"rule": "names ⊆ ONLINE_2Q_NAMES und depth ≤ "
                        "ONLINE_DEPTH_MAX (EX ANTE abgeschaecht: "
                        "two_q == 1 NICHT gefordert, FakeFez-Anker)",
                "ok": bool(ok)}
    raise ValueError(leg)


def run_leg(leg, service=None, poll=True):
    """EIN Job pro Bein, Mechanik bit-identisch zu v5.run_kingston_job."""
    if service is None:
        service = make_service_for(leg)
    backend = service.backend(BACKEND_NAMES[leg])
    real_name = str(getattr(backend, "name", BACKEND_NAMES[leg]))
    ops = v5.build_operators()
    isa = v5.isa_ansatz_for(backend)
    counts = v5.isa_gate_counts(isa)
    bound = isa.assign_parameters(v5.FEZ_PARAMS)
    pubs = [(bound, v5._laid_out(ops["ops_real"], isa)),
            (bound, v5._laid_out(ops["ops_diag"], isa)),
            (bound, v5._laid_out(ops["ops_imag"], isa))]
    est = Estimator(mode=backend)
    est.options.resilience_level = 1
    est.options.dynamical_decoupling.enable = True
    est.options.dynamical_decoupling.sequence_type = "XX"
    est.options.default_shots = v5.SHOTS
    job = est.run(pubs)  # EIN Aufruf, drei Pubs
    return {"leg": leg, "backend": real_name, "isa": counts, "_job": job}


def fetch_leg(leg, job, real_name, counts):
    """Result in das Raw-Dokument ueberfuehren (KEIN Verdict hier)."""
    result = job.result()
    re, hd, im = (float(result[i].data.evs) for i in range(3))
    return {
        "experiment": EXPERIMENT,
        "leg": leg,
        "backend": real_name,
        "job_id": job.job_id(),
        "isa": counts,
        "meas": {"re": re, "hd": hd, "im": im, "bias": re - hd},
        "options": {"resilience_level": 1, "dd": "XX",
                    "shots": int(v5.SHOTS),
                    "transpile_seed": int(v5.TRANSPILE_SEED)},
        "params": list(v5.FEZ_PARAMS),
    }


def submit_leg(leg, poll=True):
    """Resume-Vertrag: Raw existiert -> return; job_id existiert ->
    resume; sonst submit + job_id sofort persistieren."""
    raw_path = RAW_PATHS[leg]
    if os.path.exists(raw_path):
        with open(raw_path, encoding="utf-8") as fh:
            return json.load(fh)
    jobid_path = JOBID_PATHS[leg]
    service = make_service_for(leg)
    if os.path.exists(jobid_path):
        with open(jobid_path, encoding="utf-8") as fh:
            job_id = fh.read().strip()
        print(f"[{leg}] resume job {job_id}")
        job = service.job(job_id)
        result = job.result()
        re, hd, im = (float(result[i].data.evs) for i in range(3))
        doc = {
            "experiment": EXPERIMENT, "leg": leg,
            "backend": BACKEND_NAMES[leg], "job_id": job_id,
            "isa": json.load(open("pt_v5_kingston_rep_%s_isa.json" % leg,
                                  encoding="utf-8")),
            "meas": {"re": re, "hd": hd, "im": im, "bias": re - hd},
            "options": {"resilience_level": 1, "dd": "XX",
                        "shots": int(v5.SHOTS),
                        "transpile_seed": int(v5.TRANSPILE_SEED)},
            "params": list(v5.FEZ_PARAMS),
        }
    else:
        pre = run_leg(leg, service=service)
        job = pre["_job"]
        with open(jobid_path, "w", encoding="utf-8") as fh:
            fh.write(job.job_id())
        # ISA-Counts sofort persistieren (Resume braucht sie)
        with open("pt_v5_kingston_rep_%s_isa.json" % leg, "w",
                  encoding="utf-8") as fh:
            json.dump(pre["isa"], fh, indent=1)
        print(f"[{leg}] submitted {job.job_id()} (backend {pre['backend']})")
        if not poll:
            return {"status": "QPU_JOB_ID_SAVED",
                    "job_id": job.job_id(), "leg": leg,
                    "backend": pre["backend"]}
        doc = fetch_leg(leg, job, pre["backend"], pre["isa"])
    with open(raw_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    print(f"[{leg}] raw: {json.dumps(doc['meas'])}")
    return doc


def quota_check(leg):
    service = make_service_for(leg)
    backend = service.backend(BACKEND_NAMES[leg])
    status = backend.status()
    info = {"leg": leg, "backend": BACKEND_NAMES[leg],
            "operational": bool(status.operational),
            "pending_jobs": int(status.pending_jobs)}
    try:
        jobs = service.jobs(backend_name=BACKEND_NAMES[leg], limit=20)
        info["recent_jobs"] = len(jobs)
        info["active_recent"] = sum(
            1 for j in jobs if "DONE" not in str(j.status())
            and "ERROR" not in str(j.status())
            and "CANCELLED" not in str(j.status()))
    except Exception as exc:  # noqa: BLE001 — Historie optional
        info["recent_jobs_error"] = type(exc).__name__
    return info


# === Auswertung (gegen die UNVERAENDERTEN 035-Baender + H-V5R-Regeln) ===

def sign_class(bias, floor):
    """Registrierte 2-Sigma-Klassifikation (md5 d019d587-Konstanten:
    SE_BIAS, SHOT_SIGMA_FACTOR). '0' = Vorzeichen bei 2 Sigma
    UNENTSCHIEDEN."""
    if bias >= floor:
        return "+"
    if bias <= -floor:
        return "-"
    return "0"


def evaluate():
    prereg_v5 = v5.load_frozen_prereg()  # md5-gepinnt, d019d587
    prereg_rep = load_rep_prereg()
    floor = (v5.SHOT_SIGMA_FACTOR * v5.SE_BIAS)

    legs = {}
    for leg in ("kingston", "fez"):
        raw = json.load(open(RAW_PATHS[leg], encoding="utf-8"))
        controls = v5.run_controls()
        gate = isa_gate_for(leg, raw["isa"])
        controls_ok = all(controls.values()) and gate["ok"]
        verdict, detail = v5.evaluate(raw["meas"], prereg_v5["bands"],
                                      controls_ok=controls_ok)
        legs[leg] = {
            "job_id": raw["job_id"], "backend": raw["backend"],
            "meas": raw["meas"], "isa": raw["isa"],
            "isa_gate": gate, "controls": controls,
            "controls_ok": controls_ok, "verdict": verdict,
            "detail": detail,
            "sign_class": sign_class(raw["meas"]["bias"], floor),
            "bias_over_se": raw["meas"]["bias"] / v5.SE_BIAS,
        }

    vk, vf = legs["kingston"]["verdict"], legs["fez"]["verdict"]
    ok_set = {v5.VERDICT_MAP["CONFIRMED"], v5.VERDICT_MAP["BIAS_MITTEL"]}
    if vk == v5.VERDICT_MAP["REFUTED"] or vf == v5.VERDICT_MAP["REFUTED"]:
        h1 = "H-V5R-1_REFUTED_EIN_BEIN_DRIFT"
    elif vk in ok_set and vf in ok_set:
        h1 = "H-V5R-1_HOLDS_BANDREPRODUZIERBAR"
    else:
        h1 = "H-V5R-1_MIXED"

    sk, sf = legs["kingston"]["sign_class"], legs["fez"]["sign_class"]
    if sk == "+" and sf == "-":
        h2 = "H-V5R-2_BACKEND_REGIME_BESTAETIGT"
    elif sk == "-" and sf == "+":
        h2 = "H-V5R-2_BACKEND_REGIME_INVERTIERT"
    elif sk == sf and sk != "0":
        h2 = "H-V5R-2_SESSION_REGIME"
    else:
        h2 = "H-V5R-2_UNDETERMINED_UNTER_2SIGMA"

    doc = {
        "experiment": EXPERIMENT,
        "prereg_v5_md5": prereg_v5["md5"],
        "prereg_rep_md5": prereg_md5(),
        "sign_floor_2sigma": floor,
        "legs": legs,
        "h_v5r_1": h1,
        "h_v5r_2": h2,
        "pooled_descriptiv": {
            "fez_sessions": ["d9fidihhtsac739fg3n0", "d9fjbraneu4c739pmaqg",
                             legs["fez"]["job_id"]],
            "fez_biases": [v5.FEZ_RUN1["bias"], v5.FEZ_RUN2["bias"],
                           legs["fez"]["meas"]["bias"]],
            "kingston_sessions": [None, legs["kingston"]["job_id"]],
            "kingston_biases": [
                -0.011922308405310833 * 0.0 + 0.0  # Platzhalter-Vermeidung
            ],
            "note": "Kingston-Bias der 035-Session in "
                    "pt_v5_kingston_results.json; Pooling rein "
                    "deskriptiv, NICHT verdict-tragend.",
        },
    }
    # Kingston-035-Bias korrekt einsetzen (Quelle: committetes Ergebnis)
    with open("pt_v5_kingston_results.json", encoding="utf-8") as fh:
        r035 = json.load(fh)
    doc["pooled_descriptiv"]["kingston_biases"] = [
        r035["meas"]["bias"], legs["kingston"]["meas"]["bias"]]
    doc["pooled_descriptiv"]["kingston_sessions"] = [
        r035["job_id"], legs["kingston"]["job_id"]]
    return doc


def write_eval(doc, path=EVAL_PATH):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=EXPERIMENT)
    parser.add_argument("--quota", action="store_true",
                        help="Quota-Pruefung beide Beine")
    parser.add_argument("--leg", choices=["kingston", "fez"],
                        help="Bein fuer --submit")
    parser.add_argument("--submit", action="store_true",
                        help="EIN Job im Bein (Resume-Vertrag) + Raw, "
                             "OHNE Verdict")
    parser.add_argument("--eval", action="store_true",
                        help="Auswertung gegen gefrorene Baender + "
                             "H-V5R-Regeln (NACH Raw-Commit)")
    args = parser.parse_args(argv)

    if args.quota:
        for leg in ("kingston", "fez"):
            print(json.dumps(quota_check(leg)))
        return 0
    if args.submit:
        if not args.leg:
            parser.error("--submit braucht --leg")
        doc = submit_leg(args.leg)
        if "job_id" in doc:
            print(f"job_id: {doc['job_id']}")
        return 0
    if args.eval:
        doc = evaluate()
        write_eval(doc)
        for leg in ("kingston", "fez"):
            l = doc["legs"][leg]
            print(f"[{leg}] verdict: {l['verdict']} | bias "
                  f"{l['meas']['bias']:+.6f} ({l['sign_class']}, "
                  f"{l['bias_over_se']:+.2f} sigma)")
        print(f"H-V5R-1: {doc['h_v5r_1']}")
        print(f"H-V5R-2: {doc['h_v5r_2']}")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())