#!/usr/bin/env python3
"""EXPERIMENT 046b (H-V5RB) — Statevector-Identitaet des 046-Designs.

User-Direktive 2026-10-06: „mache einfach neuen prereg für 046b und 055b
für statevector-version, die kannst du neu schreiben, klar.“  Das
gebliebete 046-Prereg (md5 fcf4c2c58837bb7188c4e029d1841214) und der
QUEUED-Job dauassrojkfs738rrcsg bleiben UNANGETASTET.

Ausloeser (Kanal-Audit 2026-10-06): letzter DONE-Job auf ibm_fez/TOKEN1
war 2026-09-28 11:50 (dat3gpqhcrkc73dtjmt0); alle drei danach
eingereichten Jobs (QUQUINT-F4 daua5hahcrkc73dv9eh0 09-30 07:48,
046-Fez-Bein dauassrojkfs738rrcsg 09-30 08:38, 055
db0m71qvog1s73fh15og 10-03 22:20) haengen permanent QUEUED — bei
backend_pending 0 startet 046 trotzdem nicht, d. h. die Queue-Ueber-
fuellung ist ALS URSACHE falsifiziert und die Starvation ist am Kanal
(Juni-Praezedenz: erster echter Laut nach 31 Tagen).

Diese leg misst den IDEALEN Inhalt des 046-Designs exakt:
  G1 (EXAKT-STATEVECTOR, 0 QPU, kein Token, kein Service-Kontakt).
  - leg "fakefez_isa": v5.noiseless_observables_at(FEZ_PARAMS) — exakt
    die gefrorene C2-Mechanik (AerEstimator precision 0.0, FakeFez-ISA).
  - leg "logical": Statevector(bound ansatz_logical) + expectation_value
    der drei SparsePauliOps ohne Layout.
Die Distillations-Frage (Antwort auf „was ist an 046 bemerkenswert“):
traegt das Backend-Vorzeichen-Regime (H-V5R-2) idealen Inhalt?  Die
idealistische Antwort ist KONSTRUKTIV determiniert (bias = re - hd,
re ≡ hd, C1/Theorem-Identitaet) und wird hier gemessen statt behauptet.

Freeze-Disziplin: SHA-256 (Policy 2026-10-05), REGISTERED_NOT_MEASURED
VOR der Messung; Roh-Commit VOR Auswertung (RAW enthaelt KEINE Ver-
dicts); Kontrollen C1-C6 frisch vor jedem Verdict (sonst INVALID, nicht
REFUTED); KEINE Toleranz-Erhoehung.
"""
import hashlib
import json
import os
import sys

import numpy as np
from qiskit.quantum_info import Statevector

import pt_v5_kingston as v5

EXPERIMENT = "046b-v5-statevector-identity"
HYPOTHESIS = "H-V5RB"
PREREG_PATH = "pt_v5_sv_prereg.json"
RAW_PATH = "pt_v5_sv_raw.json"
EVAL_PATH = "pt_v5_sv_eval.json"
LEG = "SV-BOTH-LEGS-LOGICAL-AND-FAKEFEZ-ISA"
G_TYP = "G1 EXAKT-STATEVECTOR (0 QPU, kein Token, kein Service-Kontakt)"

TOL_ANCHOR = 1e-6      # == gefrorene C2-Toleranz (046/035-Kette)
TOL_ISA_ID = 1e-9      # ISA-Identitaet log vs fakefez (Numerik-Umgebung)
TOL_BIAS = 1e-12       # bias == 0 idealseitig (float-Umgebung)
PREREG_SHA256 = ("0394fb7288ac8cb2374b00fef50c3102"
                 "0c20f66090283147adcc36021d8170b6")  # Freeze 2026-10-06 (Policy 2026-10-05)

V_L1_HELD = "H-V5RB-1_NOISELESS_ANCHOR_HELD"
V_L1_REF = "H-V5RB-1_NOISELESS_ANCHOR_REFUTED"
V_L2_HELD = "H-V5RB-2_LOGICAL_ISA_BIAS_IDENTITY_HELD"
V_L2_REF = "H-V5RB-2_LOGICAL_ISA_BIAS_IDENTITY_REFUTED"
KERN_HELD = "H-V5RB_IDENTITY_HELD"
KERN_MIXED = "H-V5RB_MIXED"
KERN_REF = "H-V5RB_REFUTED"
KERN_INVALID = "H-V5RB_INVALID_KONTROLLE_GESCHEITERT"


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def payload_sha256(payload):
    """Kanonischer Payload-Hash (SHA-256, Policy 2026-10-05)."""
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def load_frozen(path=PREREG_PATH, expected_sha256=None):
    """Freeze-Loader: SHA-256 KANONISCH ueber den geparsten Inhalt —
    erzwungen am Lauf UND an der Auswertung (053-Lektion)."""
    with open(path, "rb") as f:
        raw_bytes = f.read()
    dig = payload_sha256(json.loads(raw_bytes.decode("utf-8")))
    if expected_sha256 is not None and dig != expected_sha256:
        raise SystemExit(
            f"PREREG-MISMATCH: {path} sha256 {dig} != {expected_sha256} "
            "- Freeze gebrochen, Abbruch.")
    return json.loads(raw_bytes.decode("utf-8")), dig


def build_prereg_payload():
    rep035 = json.load(open("pt_v5_kingston_rep_prereg.json",
                            encoding="utf-8"))
    bands = rep035["baender_und_schwellen"]["bands"]
    return {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "registered": "2026-10-06",
        "status": "REGISTERED_NOT_MEASURED",
        "branch": "h-test1-gap-invariance",
        "g_typ": G_TYP,
        "motivation": (
            "Fez-Kanal-Starvation seit 2026-09-28 11:50 (letzter DONE "
            "dat3gpqhcrkc73dtjmt0): ALLE drei danach eingereichten Token1-"
            "Jobs (daua5hahcrkc73dv9eh0 F4, dauassrojkfs738rrcsg 046, "
            "db0m71qvog1s73fh15og 055) permanent QUEUED; backend_pending "
            "0 ohne Start falsifiziert 'Queue ueberfuellt' als Ursache. "
            "Diese leg misst den IDEALEN Inhalt des 046-Designs exakt "
            "(0 QPU) und distilliert die Struktur/Noise-Frage: traegt "
            "H-V5R-2 (Backend-Vorzeichen-Regime) idealem Inhalt? "
            "Konkurrenz: C1/Theorem-Identitaet sagt bias = re - hd == 0 "
            "idealseitig — jedes nichtideale Vorzeichen ist Session-/"
            "Noise-Phaenomen. Die QPU-Beine bleiben QUEUED und "
            "verdict-tragend fuer die 046/035-Kette."),
        "parent_context": {
            "exp_035": {
                "experiment": "035-ququint-v5-kingston-drift",
                "prereg_md5_legacy": "d019d587c0d8ca28cfa0559057d590c8",
                "verdict": "H-V5_CONFIRMED_KINGSTON_NEUTRAL_BAND",
                "job_id": "daqaeteekp0c73aqetdg",
            },
            "exp_046": {
                "experiment": "046-ququint-v5-repetition-both-backends",
                "hypothesis": "H-V5R",
                "prereg_md5_legacy": "fcf4c2c58837bb7188c4e029d1841214",
                "fez_job_id": "dauassrojkfs738rrcsg",
                "fez_job_status": "QUEUED (unangetastet, kein Cancel)",
            },
            "kritik1_bezug": (
                "lebender Treffer 2 (Kapazitaets-Allokation): die "
                "Statevector-Ebene distilliert ohne QPU-Kontingent."),
        },
        "referenzkonstanten_035": {
            "noiseless_re": v5.NOISELESS_RE,
            "noiseless_im": v5.NOISELESS_IM,
            "noiseless_e0_diag": v5.NOISELESS_E0_DIAG,
            "noiseless_e0_h1": v5.NOISELESS_E0_H1,
            "se_re": v5.SE_RE, "se_hd": v5.SE_HD, "se_im": v5.SE_IM,
            "thresh_bias_confirmed": v5.THRESH_BIAS_CONFIRMED,
            "thresh_bias_refuted": v5.THRESH_BIAS_REFUTED,
            "fez_params": v5.FEZ_PARAMS,
            "bands_035": bands,
        },
        "design": {
            "leg_fakefez_isa": (
                "v5.noiseless_observables_at(v5.FEZ_PARAMS) VERBATIM "
                "(AerEstimator precision 0.0, method density_matrix, "
                "FakeFez-ISA opt-level 3 seed 7) — identische Mechanik "
                "zur gefrorenen C2; Messung statt Behauptung."),
            "leg_logical": (
                "Statevector(v5.ansatz_logical().assign_parameters("
                "v5.FEZ_PARAMS)) + expectation_value der drei Operators "
                "(ops_real/ops_diag/ops_imag OHNE Layout) — der Design-"
                "Inhalt vor jeder ISA-Transformation."),
            "kein_sampling": (
                "Precision-0.0-Erwartungswerte, kein Seed, "
                "deterministisch wiederholbar (kein Stochastic-Bein)."),
            "kein_token": (
                "0 QPU: kein Estimator/Sampler-Job, kein Service-Objekt, "
                "kein Token-Kontakt (FakeFez ist offline)."),
        },
        "hypotheses": {
            "H-V5RB-1": {
                "name": "NOISELESS_ANCHOR_REPRODUCED",
                "verdict_tragend": True,
                "statement": (
                    "Die frische Exact-Messung an leg fakefez_isa "
                    "reproduziert die gefrorenen 035-Noiseless-Anker: "
                    "|re - noiseless_re| <= 1e-6 UND "
                    "|hd - noiseless_re| <= 1e-6 UND "
                    "|im - noiseless_im| <= 1e-6 UND bias == 0.0 exakt"),
                "held": V_L1_HELD, "refuted": V_L1_REF,
                "toleranz": TOL_ANCHOR,
                "herkunft": ("1e-6 == gefrorene C2-Toleranz (046/035-"
                             "Kette); bias == 0 exakt == C2-Schwarze-Text, "
                             "gemessen als Verdict, nicht als Kontrolle."),
            },
            "H-V5RB-2": {
                "name": "LOGICAL_ISA_BIAS_IDENTITY",
                "verdict_tragend": True,
                "statement": (
                    "Der IDEALE Design-Inhalt ist ISA-invariant UND "
                    "vorzeichenfrei: |re_log - re_ff| <= 1e-9 UND "
                    "|hd_log - hd_ff| <= 1e-9 UND |im_log - im_ff| "
                    "<= 1e-9 UND |bias_log| <= 1e-12 UND |bias_ff| "
                    "<= 1e-12"),
                "held": V_L2_HELD, "refuted": V_L2_REF,
                "toleranz": TOL_ISA_ID,
                "interpretation": (
                    "HELD bedeutet: H-V5R-2's Vorzeichen-Regime hat "
                    "keinen idealen Inhalt — die Backend-Bias-Kontraste "
                    "sind Session-/Noise-Phaenomene (Distillations-"
                    "Ergebnis). REFUTED waere ein Transpile-/Layout-"
                    "Artefakt oder ein echter ISA-Effekt und muesste "
                    "im ISA-Detail verortet werden."),
            },
        },
        "kern": {
            "H-V5RB_IDENTITY_HELD": "beide H-V5RB-1 und H-V5RB-2 HELD",
            "H-V5RB_MIXED": "GENAU EINE gefallen",
            "H-V5RB_REFUTED": "beide REFUTED",
            "invalid": ("Kontrollen C1-C6 nicht alle gruen -> "
                        "H-V5RB_INVALID_KONTROLLE_GESCHEITERT (Verdicts "
                        "zurueckbehalten, offen diskulpiert)."),
        },
        "kontrollen": {
            "c_all": ("v5.run_controls() (C1-C6) frisch; ALLE muessen "
                      "gruen sein, sonst INVALID (046-Praezedenz)."),
            "c_isa_anker": ("isa_gate_counts(isa_ansatz_fakefez()) == "
                            "ISA-Frozen (C4: two_q 1 / one_q 18 / names "
                            "('cz',) / depth 11) — deterministisch."),
            "c_stress": ("C5: STRESS-SHIFT reproduziert "
                         "STRESS_SHIFT_RE/IM <= 1e-6 (deterministisch)."),
        },
        "descriptiv_mirror": {
            "form": ("v5.evaluate(meas, bands_046, controls_ok) je leg "
                     "(CONFIRMED/BIAS_MITTEL/... MIRROR auf exakt-Werte, "
                     "NICHT verdict-tragend fuer die 046/035-Kette)."),
            "band_context": ("Placement der exakt-Werte in den 035-"
                             "Baendern; hd-Marge zur Band-Unterkante; "
                             "re - E0-Abstaende (Grundzustands-Kontext)."),
        },
        "banned_from_raw": [
            "verdict", "H-V5RB-1_*", "H-V5RB-2_*", "kern",
            "band_platzierung", "classification"],
        "freeze_discipline": [
            "Prereg-Freeze (SHA-256) VOR jeder Messung "
            "(REGISTERED_NOT_MEASURED); Freeze-Vergleich an Run UND "
            "Auswertung erzwungen (053-Lektion).",
            "Roh-Commit VOR Auswertung (RAW enthaelt KEINE Verdicts).",
            "Gefrorene 046-/035-Preregs UNANGETASTET; kein Re-Decide; "
            "KEINE Toleranz-Erhoehung.",
        ],
        "anti_sharpshooter": (
            "Alle Konstanten (Anker, E0s, Bandober-, ISA-Counts, "
            "STRESS-SHIFT) sind committete 035/046-Konstanten; die b-"
            "Toleranzen sind Numerik-Umgebungs-Groessen (1e-6 == C2, "
            "1e-9/1e-12 unterhalb jeder Shot-Ungleichheit) — nichts "
            "betrachtet die QPU-Messdaten (die QUEUED sind)."),
        "numpy_build": np.__version__,
        "qiskit_build": __import__("qiskit").__version__,
    }


def freeze_prereg(path=PREREG_PATH):
    """Freeze: schreibe Prereg und returniere die SHA-256 (einziger
    Ort, an dem PREREG_SHA256 gesetzt wird — danach in die Konstante
    uebernehmen und committen)."""
    payload = build_prereg_payload()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, sort_keys=True, separators=(",", ":"),
                  ensure_ascii=False, indent=1)
    dig = payload_sha256(payload)
    print(f"PREREG_FROZEN sha256={dig}")
    return dig


# ---------- Messung (RAW: keine Verdicts) ----------

def run_measurement():
    if os.path.exists(RAW_PATH):
        raise SystemExit(
            f"RAW-EXISTIERT-BEREITS: {RAW_PATH} — kein stiller Re-Run "
            "(Roh-Commit-Disziplin). Loeschen ist ein expliziter Akt.")
    prereg, dig = load_frozen(expected_sha256=PREREG_SHA256)

    ops = v5.build_operators()

    # -- leg fakefez_isa: exakt die gefrorene C2-Mechanik --
    ff = v5.noiseless_observables_at(v5.FEZ_PARAMS)
    isa_ff = v5.isa_ansatz_fakefez()
    isa_counts = v5.isa_gate_counts(isa_ff)

    # -- leg logical: Statevector exakt, OHNE Layout --
    logical = v5.ansatz_logical()
    bound_log = logical.assign_parameters(v5.FEZ_PARAMS)
    sv = Statevector(bound_log)
    re_log = float(np.real(sv.expectation_value(ops["ops_real"])))
    hd_log = float(np.real(sv.expectation_value(ops["ops_diag"])))
    im_log = float(np.real(sv.expectation_value(ops["ops_imag"])))

    # -- Kontrollen C1-C6 frisch (booleans) --
    controls = v5.run_controls()

    raw = {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "leg": LEG,
        "status": "SV_RAW_FETCHED",
        "g_typ": G_TYP,
        "created_at_utc": os.environ.get("SV046B_STAMP"),
        "mechanik": (
            "v5.noiseless_observables_at precision 0.0 (leg "
            "fakefez_isa) + qiskit Statevector.expectation_value "
            "(leg logical); kein Sampling, kein Seed, "
            "deterministisch."),
        "params": list(v5.FEZ_PARAMS),
        "legs": {
            "fakefez_isa": {
                "re": float(ff["re"]), "hd": float(ff["hd"]),
                "im": float(ff["im"]), "bias": float(ff["bias"]),
            },
            "logical": {
                "re": re_log, "hd": hd_log, "im": im_log,
                "bias": re_log - hd_log,
            },
        },
        "isa_counts_fakefez": {
            "two_q": isa_counts["two_q"], "one_q": isa_counts["one_q"],
            "names": list(isa_counts["names"]),
            "depth": isa_counts["depth"],
        },
        "controls": controls,
        "prereg_sha256": dig,
        "numpy_build": np.__version__,
        "qiskit_build": __import__("qiskit").__version__,
    }
    with open(RAW_PATH, "w", encoding="utf-8") as f:
        json.dump(raw, f, sort_keys=True, separators=(",", ":"),
                  ensure_ascii=False, indent=1)
    print(f"RAW_WRITTEN {RAW_PATH} sha256={sha256_file(RAW_PATH)}")
    print("[run] fakefez_isa re/hd/im = %.12f/%.12f/%.12f bias %.1e"
          % (ff["re"], ff["hd"], ff["im"], ff["bias"]))
    print("[run] logical      re/hd/im = %.12f/%.12f/%.12f"
          % (re_log, hd_log, im_log))
    return raw


# ---------- gefrorene Auswertung ----------

def _descriptiv_band_platzierung(meas, bands):
    out = {}
    for k in ("re", "hd", "im"):
        lo, hi = bands[k]
        v = meas[k]
        out[k] = {"value": v, "band": [lo, hi],
                  "in_band": bool(lo <= v <= hi)}
    out["hd_marge_zur_unkante"] = float(meas["hd"] - bands["hd"][0])
    out["re_minus_e0_h1"] = float(meas["re"] - v5.NOISELESS_E0_H1)
    out["re_minus_e0_diag"] = float(meas["re"] - v5.NOISELESS_E0_DIAG)
    return out


def run_evaluation():
    prereg, dig = load_frozen(expected_sha256=PREREG_SHA256)
    ref = prereg["referenzkonstanten_035"]
    bands = ref["bands_035"]
    with open(RAW_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    if raw["prereg_sha256"] != dig:
        raise SystemExit("RAW-PREREG-MISMATCH: Freeze gebrochen.")

    controls_ok = bool(raw["controls"]) and all(raw["controls"].values())

    legs = raw["legs"]
    ff, lg = legs["fakefez_isa"], legs["logical"]
    d_re = abs(lg["re"] - ff["re"])
    d_hd = abs(lg["hd"] - ff["hd"])
    d_im = abs(lg["im"] - ff["im"])
    l1_checks = {
        "re": abs(ff["re"] - ref["noiseless_re"]) <= TOL_ANCHOR,
        "hd": abs(ff["hd"] - ref["noiseless_re"]) <= TOL_ANCHOR,
        "im": abs(ff["im"] - ref["noiseless_im"]) <= TOL_ANCHOR,
        "bias_exakt": bool(ff["bias"] == 0.0),
    }
    l2_checks = {
        "re": d_re <= TOL_ISA_ID, "hd": d_hd <= TOL_ISA_ID,
        "im": d_im <= TOL_ISA_ID,
        "bias_log": abs(lg["bias"]) <= TOL_BIAS,
        "bias_ff": abs(ff["bias"]) <= TOL_BIAS,
    }
    if not controls_ok:
        verdict_l1 = verdict_l2 = None
        kern = KERN_INVALID
        kontrolle_grund = ("run_controls nicht alle gruen: "
                           + json.dumps(raw["controls"]))
    else:
        verdict_l1 = V_L1_HELD if all(l1_checks.values()) else V_L1_REF
        verdict_l2 = V_L2_HELD if all(l2_checks.values()) else V_L2_REF
        kern = None
        if verdict_l1 == V_L1_HELD and verdict_l2 == V_L2_HELD:
            kern = KERN_HELD
        elif verdict_l1 == V_L1_REF and verdict_l2 == V_L2_REF:
            kern = KERN_REF
        else:
            kern = KERN_MIXED
        kontrolle_grund = None

    # descriptiv: QPU-law-Mirror je leg (046-Register, kein Verdict-Erlass)
    mirror = {}
    for legname, meas in (("fakefez_isa", ff), ("logical", lg)):
        verdict, detail = v5.evaluate(meas, bands, controls_ok=controls_ok)
        mirror[legname] = {"verdict_qpu_law_mirror": verdict,
                           "detail": detail,
                           "band_platzierung": _descriptiv_band_platzierung(
                               meas, bands),
                           "verdict_role": "DESCRIPTIV (kein Verdict-"
                                           "Erlass fuer die 046/035-Kette)"}

    eval_doc = {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "leg": LEG,
        "status": "SV_EVAL_COMPLETED",
        "evaluated_at_utc": os.environ.get("SV046B_EVAL_STAMP"),
        "prereg_sha256": dig,
        "controls_ok": controls_ok,
        "kontrolle_grund": kontrolle_grund,
        "deviations_logical_vs_fakefez": {"re": d_re, "hd": d_hd,
                                          "im": d_im},
        "checks_l1": l1_checks, "checks_l2": l2_checks,
        "verdicts": {
            "H-V5RB-1": verdict_l1,
            "H-V5RB-2": verdict_l2,
            "kern": kern,
            "verdict_tragend_fuer": ("046b (H-V5RB) — NICHT fuer die "
                                     "046/035-Kelle (die bleibt dem QPU-"
                                     "Bein vorbehalten)"),
        },
        "interpretation": prereg["hypotheses"]["H-V5RB-2"][
            "interpretation"] if verdict_l2 == V_L2_HELD else None,
        "qpu_law_mirror": mirror,
        "context": {
            "046_fez_job_id": "dauassrojkfs738rrcsg",
            "046_fez_job_status": "QUEUED (unangetastet)",
            "046_kanalaudit": (
                "letzter DONE 2026-09-28 11:50 dat3gpqhcrkc73dtjmt0; "
                "backend_pending 0 ohne Start -> Starvation am Kanal."),
        },
    }
    with open(EVAL_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_doc, f, sort_keys=True, separators=(",", ":"),
                  ensure_ascii=False, indent=1)
    print("EVAL_WRITTEN", EVAL_PATH)
    print("[eval] H-V5RB-1: %s" % verdict_l1)
    print("[eval] H-V5RB-2: %s" % verdict_l2)
    print("[eval] kern: %s" % kern)
    print("[eval] dev(log vs ff) re %.2e hd %.2e im %.2e"
          % (d_re, d_hd, d_im))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--freeze" in argv:
        freeze_prereg()
        return 0
    if "--run" in argv:
        run_measurement()
        return 0
    if "--eval" in argv:
        run_evaluation()
        return 0
    if "--verify" in argv:
        _, dig = load_frozen(expected_sha256=PREREG_SHA256)
        print("PREREG_VERIFIED sha256=%s" % dig)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise sys.exit(main())