#!/usr/bin/env python3
"""EXPERIMENT 055b (H-055B) — Statevector-IDEAL-Bein des 055-Circuitsatzes.

User-Direktive 2026-10-06 („neuen prereg für 046b und 055b für
statevector-version“): denselben 160-Circuit-Budget (h3a.
build_hardware_circuit_set, bit-identisch zur QPU-Mechanik) auf
AerSimulator(method="statevector") IDEAL messen — Pre-Submission-
Mechanik mit read-only Service-Kontakt (get_service/get_backend, KEIN
Job, KEIN Submit).  Der QUEUED-QPU-Job db0m71qvog1s73fh15og und das
QPU-055-Ensemble (Prereg legacy md5 b7afc42c..., gefrorenes
Gesetz pt_ram_q_prio48_eval.evaluate) bleiben UNANGETASTET.

Distillations-Frage: was traegt das 055-Design IDEAL — separiert vom
QPU-Noise und von der S1/S2-Session-Variabilitaet?
  H-055B-1 IDEAL_KAPPA: alle 37 kappa_hat >= 0.81 (Struktur).
  H-055B-2 IDEAL_SHARPNESS: C2-Kern {467, 673} below_sharp (Verlaufs-
          Richtung der Vorhersage im IDEAL).
  H-055B-3 ECHO_IDEAL: kappa_block(q3) >= 0.99 UND kappa_block(q5)
          >= 0.99 (Echo-Leiter; S1/S2-Kontext q3 0.9927/q5 0.7314).
  H-055B-4 C1_IDEAL: rho_fresh_vs_s1 >= Arm-Anker (Session-Struktur
          im IDEAL).
Gelesen über den descriptiven MIRROR durch das GEFRORENE Gesetz
(pt_ram_q_prio48_eval.evaluate(raw_path=SV_RAW, stage3_path=committed,
isa_path=frischer SV-ISA-Report, gate_path=frisches SV-Gate,
prereg_path=None)) — descriptiv: kein Verdict-Erlass, 055-Verdicts
bleiben dem QPU-Job vorbehalten.

ISA-Status: der committete 055-ISA-Report traegt ops als Op-COUNTS-
Dict (keine Instruktions-Quelle) — die Submission-ISA ist NICHT
rekonstruierbar.  Deshalb transpiliert 055b FRISCH am Live-Backend
(dieselbe transpile_forced-Mechanik) und vergleicht die Zellen
(ops/n_2q/initial_layout) gegen committet als DIAGNOSTIK
(ISA_CELL_IDENTICAL / ISA_CELL_DRIFT) — bei Drift laeuft die leg
WEITER (registrierte Regel, dokumentiert): die IDEAL-Messung haengt
an der FRISCHEN Transformation.

Re-Freeze R1 (2026-10-06, 0 QPU, VOR jeder Auswertung): der R0-Freeze
(sha256 de15ffb8...) trug eine defekte c_seed-Kontrolle — Aer-Batch-
RNG-Stroeme sind batch-kontextabhaengig, Einzeln-Replay reproduziert
nur Position 0 (Bell-Referenzprobe: Voll-Batch-Sofort-Replay
bit-identisch, Positionsinvarianz der Nachbarn, Einzel-Replay von
Position > 0 nicht reproduktiv).  R1-Mechanik: c_seed = EIN Sofort-
Replay desselben vollen Batches im selben Prozess (alle 160 Zeilen
bit-identisch erwartet).  Das R0-Raw ist NIEMALS ausgewertet und nie
committet; es geht als *_R0-Suffix in den Freeze-Commit ein.  Kein
Metrik-Weakening (Schwellen/Budgets/Hypothesen UNVERAENDERT);
Praezedenz Phase-10b (EXPERIMENT 043, MD5 5b91119b -> 0b9c9968).

Aktiv-Qubit-Reduktion: active = Vereinigung der Instruktions-Qubits
(inkl. Messen); QuantumCircuit(len(active), num_clbits UNVERAENDERT);
nur Qubit-Indizes werden remappt, Clbit-Indizes bleiben — Counts-Keys
byte-identisch zum QPU-Keyspace.
"""
import hashlib
import json
import os
import sys

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

import pt_ram_q_hardware3 as h3
import pt_ram_q_hardware3_aer as h3a
import pt_ram_q_prio48 as p48
import pt_ram_q_prio48_eval as ev
import pt_ram_q_prio48_qpu as qpu

EXPERIMENT = "055b-fp48-statevector-ideal"
HYPOTHESIS = "H-055B"
PREREG_PATH = "pt_ram_q_prio48_sv_prereg.json"
RAW_PATH = "pt_ram_q_prio48_sv_raw.json"
EVAL_PATH = "pt_ram_q_prio48_sv_eval.json"
SV_ISA_REPORT = "pt_ram_q_prio48_sv_isa_report.json"
SV_ISA_GATE = "pt_ram_q_prio48_sv_isa_gate.json"
STAGE3_PATH = "pt_ram_q_prio48_stage3_results.json"   # committed
COMMITTED_ISA_REPORT = qpu.ISA_REPORT_PATH            # committet
COMMITTED_ISA_GATE = qpu.ISA_GATE_PATH                # committet
LEG = "SV-IDEAL-MIRROR (Aer statevector, Pre-Submission-Mechanik)"
G_TYP = "G2 AER-STATEVECTOR-IDEAL (0 QPU-Gewicht; read-only Service-Kontakt)"

SEED_SIMULATOR = 20261006   # ex ante gepinnt
MAX_ACTIVE_QUBITS = 24      # Sicherheits-Grenze der Reduktion
TOL_SEED = 0                # c_seed: counts BIT-IDENTISCH
KAPPA_CEILING = h3.KAPPA_CEILING  # 0.81
ECHO_FLOOR_IDEAL = 0.99
PREREG_SHA256 = ("c708d9054a325381914a1436dadaa0a2"
                 "bf4d33eefe79cb2cde73274dc0a43b2f")  # Re-Freeze R1 2026-10-06

V_H1_HELD = "H-055B-1_IDEAL_KAPPA_HELD"
V_H1_REF = "H-055B-1_IDEAL_KAPPA_REFUTED"
V_H2_HELD = "H-055B-2_IDEAL_SHARPNESS_HELD"
V_H2_REF = "H-055B-2_IDEAL_SHARPNESS_REFUTED"
V_H3_HELD = "H-055B-3_ECHO_IDEAL_HELD"
V_H3_REF = "H-055B-3_ECHO_IDEAL_REFUTED"
V_H4_HELD = "H-055B-4_C1_IDEAL_HELD"
V_H4_REF = "H-055B-4_C1_IDEAL_REFUTED"
KERN_ALL = "H-055B_IDEAL_REPRODUCIBLE"
KERN_MIXED = "H-055B_IDEAL_MIXED"
KERN_NONE = "H-055B_IDEAL_REFUTED"
KERN_INVALID = "H-055B_MIRROR_INVALID_VERDICTS_AUS_DOC"


def payload_sha256(payload):
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_frozen(path=PREREG_PATH, expected_sha256=None):
    """Freeze-Loader (SHA-256, kanonisch ueber den Inhalt) — erzwungen
    an Lauf UND Auswertung (053-Lektion)."""
    with open(path, "rb") as f:
        raw_bytes = f.read()
    dig = payload_sha256(json.loads(raw_bytes.decode("utf-8")))
    if expected_sha256 is not None and dig != expected_sha256:
        raise SystemExit(
            f"PREREG-MISMATCH: {path} sha256 {dig} != {expected_sha256} "
            "- Freeze gebrochen, Abbruch.")
    return json.loads(raw_bytes.decode("utf-8")), dig


def _constants_embed():
    import pt_ram_q_hardware2_eval as h3e
    return {
        "shots": h3.SHOTS,
        "kappa_ceiling": h3.KAPPA_CEILING,
        "ladder_repeats": list(h3.LADDER_REPEATS),
        "ladder_anchors": {k: list(v) if isinstance(v, (list, tuple)) else v
                           for k, v in h3.LADDER_ANCHORS.items()},
        "k_repeats": h3a.K_REPEATS,
        "w_a": h3a.W_A,
        "w_b_doubleprime": float(h3e.load_w_b()),
        "arms": list(p48.ARMS),
        "anchor_rho_q5": p48.ANCHOR_RHO_Q5,
        "anchor_rho_q3": p48.ANCHOR_RHO_Q3,
        "anchor_rho_pooled": p48.ANCHOR_RHO_POOLED,
        "n_circuits": p48.N_CIRCUITS,
        "transpile_seed": qpu.TRANSPILE_SEED,
        "transpile_optimization_level": 3,
        "seed_simulator": SEED_SIMULATOR,
        "max_active_qubits": MAX_ACTIVE_QUBITS,
        "echo_floor_ideal": ECHO_FLOOR_IDEAL,
    }


def build_prereg_payload():
    c = _constants_embed()
    return {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "registered": "2026-10-06",
        "status": "REGISTERED_NOT_MEASURED",
        "branch": "h-test1-gap-invariance",
        "g_typ": G_TYP,
        "version_regie": {
            "version": "R1",
            "R0_freeze_sha256":
                "de15ffb8ff6b5884cac13af2a13567a0833"
                "c6b2b5c5e459747562c89b4099f84",
            "delta_vs_R0": [
                "c_seed-Mechanik korrigiert: R0 = 'Rerun EINES Circuits' "
                "-> R1 = 'Sofort-Replay des GESAMTEN Batches im selben "
                "Prozess' (Einzeln-Replay ist in AerStatevector nicht "
                "position-stabil — Batch-RNG-Stroeme haengen am Kontext).",
                "design.seed_mechanik_lesson ergaenzt (R0-Lektion "
                "dokumentiert); design.simulation nennt den Replay.",
                "KEINE Veraenderung an Hypothesen, Schwellen, Design-"
                "Budget, Mirror-Contract, banned_from_raw.",
            ],
            "R0_raw_fate": (
                "R0-Raw (c_seed False aus R0-Mechanik, counts_md5 "
                "5c5c4441616b1f199df1336b0d433d17, sha256 "
                "a48467f9...) NIE evaluiert: uncommitted "
                "verschoben in *_R0-Superseded-Artefakte und im "
                "Re-Freeze-Commit dem Ledger uebergeben; ISA-2q-Tally "
                "830/84 bit-gleich committet, Zell-Drift 46/160 nur "
                "1q-ops (Fez-Target-Refresh-Signatur)."),
            "kein_metrik_weakening": True,
        },
        "motivation": (
            "Fez-Kanal-Starvation (QUEUED db0m71qvog1s73fh15og 055, "
            "dauassrojkfs738rrcsg 046, daua5hahcrkc73dv9eh0 F4; letzter "
            "DONE 2026-09-28 11:50).  User-Direktive: Statevector-"
            "Version der QPU-Experimente.  055b misst den IDEALEN Inhalt "
            "des 055-Designs auf DEMSELBEN 160-Circuit-Budget (bit-"
            "identischer Builder) und distilliert Struktur/Noise: "
            "kappa_hat im IDEAL (= strukturale Loschmidt-Return, "
            "Readout-Defizit separiert), Sharpness des Verlaufs, Echo-"
            "Leiter, Session-Struktur C1.  MIRROR durch das GEFRORENE "
            "Gesetz evaluate() — descriptiv, kein Verdict-Erlass "
            "(055-Verdicts bleiben dem QPU-Job vorbehalten)."),
        "parent_context": {
            "exp_055": {
                "experiment": "055-fp48-combined",
                "hypothesis": "H-FP48",
                "prereg_md5_legacy":
                    "b7afc42c62a6da75b2e43dd3674f8965",
                "fez_job_id": "db0m71qvog1s73fh15og",
                "fez_job_status": "QUEUED (unangetastet, kein Cancel)",
            },
            "s1_044": {
                "experiment": "044",
                "verdict": "H-RAM-Q-4_REFUTED",
                "anchoren": ["ANCHOR_RHO_Q5 0.49999999999999994",
                             "ANCHOR_RHO_Q3 0.8095238095238096"],
            },
            "fprio4_8": (
                "055b leistet die IDEAL-Seite zu FPrio-4/8 (Höhere "
                "Session-Substrat-/Kalibrier-Frage): Echo-r8-Floor kippte "
                "auf Kingston 0.098→0.4655 — hier: was sagt das IDEAL?"),
        },
        "referenzkonstanten": c,
        "design": {
            "circuits": (
                "h3a.build_hardware_circuit_set(pts, cal) mit pts/cal = "
                "p48.eval_grid() — DERSSELBE deterministische Builder wie "
                "die QPU-Submission; assert len == 160."),
            "isa_frisch": (
                "qpu.transpile_forced(live_backend, circuits) FRISCH "
                "(FORCED-Layouts + 12 unforced Auto; S1-2q-Bit-Anker "
                "bleibt Gate) — weil die Submission-ISA nicht rekon-"
                "struktierbar ist (committete ops = Counts-Dict)."),
            "isa_cell_diagnostik": (
                "Vergleich frischer Report (ops/n_2q/initial_layout per "
                "Circuit) gegen committet: ISA_CELL_IDENTICAL oder "
                "ISA_CELL_DRIFT (mit Zell-Delta-Dokumentation); bei "
                "Drift WEITERLAUF (registriert, dokumentiert) — kein "
                "Abbruch, keine Toleranz-Erhoehung."),
            "reduktion": (
                "Aktiv-Qubit-Reduktion: active = Instruktions-Qubits; "
                "num_clbits UNVERAENDERT (Keys byte-identisch), Qubit-"
                "Indizes remappt, max_active <= 24 (assert)."),
            "simulation": (
                "AerSimulator(method='statevector'), IDEAL (kein Noise "
                "Model), shots h3.SHOTS = 8192, seed_simulator "
                "20261006 ex ante, EIN run() ueber alle 160 + EIN "
                "Sofort-Replay desselben Batches im selben Prozess "
                "(c_seed, R1-Mechanik)."),
            "seed_mechanik_lesson": (
                "Einzeln-Replay eines Batch-Experiments mit demselben "
                "Seed ist in AerStatevector NICHT position-stabil: die "
                "per-Experiment-RNG-Stroeme haengen am Batch-Kontext "
                "(nicht an seed+i — weder roher Seed noch Position-"
                "Offset reproduziert pos>0; pos 0 schon).  Der volle "
                "Sofort-Replay im selben Prozess ist bit-identisch. "
                "Interpreter je Lauf pinnen (049b-Metrologie-Lektion)."),
            "kein_qpu_job": (
                "0 QPU-Gewicht: KEIN Sampler/Estimator-Job, KEIN Submit; "
                "read-only Service-Kontakt (get_service/get_backend) "
                "nur fuer die frische Transpile-Diagnostik."),
        },
        "mirror_contract": {
            "law": "pt_ram_q_prio48_eval.evaluate (gefloren, unangetastet)",
            "call": ("evaluate(raw_path=SV_RAW, stage3_path=STAGE3_PATH"
                     " (committed), isa_path=SV_ISA_REPORT (frisch), "
                     "gate_path=SV_ISA_GATE (frisch), prereg_path=None)"),
            "verdict_rolle": (
                "descriptiv (Mirror-Status + alle t-Checks eingeordnet); "
                "die 055-Verdicts bleiben dem QPU-Job vorbehalten; die "
                "055b-Verdicts (H-055B-1..4) sind von DEM MIRROR-DOC "
                "abgeleitet (Felder punkte/echo_ladder/c1_sessions_anker/"
                "c2_transfer) und verdict-tragend fuer 055b."),
            "fallback": (
                "Nur wenn der MIRROR EVALUATION_INVALID meldet: "
                "Fallback-Mini-Loop mit oeffentlichen Helpers (aer."
                "ratio_from_counts/aer.p0_fraction/h3e.center_v3/h3e."
                "load_w_b, frisches cP) — dokumentiert als "
                "MIRROR_VOID_FALLBACK."),
        },
        "hypotheses": {
            "H-055B-1": {
                "name": "IDEAL_KAPPA",
                "statement": (
                    "Im IDEAL sind alle 37 kappa_hat (13 verdict + 24 "
                    "cal) >= kappa_ceiling 0.81 — kappa = P_L (ideales "
                    "p_ro).  Separated das strukturelle Loschmidt-Defizit "
                    "vom QPU-Noise: HELD bedeutet, das 0.8-Gate ist "
                    "Noise-Bedingt an den Zeilen, wo die Session-Arme "
                    "es verfehlen; REFUTED bedeutet strukturell "
                    "unterschritten (Loschmidt-Return strukturell "
                    "unter 0.81)."),
                "statistic": "min kappa_hat ueber alle 37 Punkte (Mirror-Doc)",
                "held": V_H1_HELD, "refuted": V_H1_REF,
                "verdict_tragend": True,
            },
            "H-055B-2": {
                "name": "IDEAL_SHARPNESS",
                "statement": (
                    "C2-Kern im IDEAL: {467, 673} BEIDE below_sharp auf "
                    "q5 verdict (Verlaufs-Richtung der Vorhersage) — "
                    "identisch zum gefrorenen C2-Kriterium; Struktur-"
                    "vs-Noise-Frage: unter 0.81-Floor auch ideal?"),
                "statistic": "doc['c2_transfer']['kern_ok']",
                "held": V_H2_HELD, "refuted": V_H2_REF,
                "verdict_tragend": True,
            },
            "H-055B-3": {
                "name": "ECHO_IDEAL",
                "statement": (
                    "Echo-Leiter im IDEAL: kappa_block(q3) >= 0.99 UND "
                    "kappa_block(q5) >= 0.99 (S1-/S2-Kontext q3 0.9927 / "
                    "q5 0.7314 auf QPU; Kingston-Echo-r8-Floor-Kippen "
                    "0.098→0.4655)."),
                "statistic": "doc['echo_ladder'][arm]['fit_kappa_block']",
                "held": V_H3_HELD, "refuted": V_H3_REF,
                "verdict_tragend": True,
            },
            "H-055B-4": {
                "name": "C1_IDEAL",
                "statement": (
                    "Session-Struktur im IDEAL: rho_fresh_vs_s1 auf q5 "
                    ">= ANCHOR_RHO_Q5 (0.49999999999999994) UND auf q3 "
                    ">= ANCHOR_RHO_Q3 (0.8095238095238096)."),
                "statistic": "doc['c1_sessions_anker'][arm]['rho_fresh_vs_s1']",
                "held": V_H4_HELD, "refuted": V_H4_REF,
                "verdict_tragend": True,
            },
        },
        "kern": {
            KERN_ALL: "alle vier H-055B-1..4 HELD",
            KERN_MIXED: "mindestens ein REFUTED, mindestens ein HELD",
            KERN_NONE: "alle vier REFUTED",
            KERN_INVALID: "Mirror EVALUATION_INVALID -> Fallback; "
                          "Verdicts TROTZDEM aus Mirror-DOC-Feldern "
                          "(dokumentiert) — invalid ist kein Verdict.",
        },
        "kontrollen": {
            "c_seed": (
                "Sofort-Replay des GESAMTEN Batches IM SELBEN PROZESS "
                "(identische reduced-Circuits, identischer Seed) -> alle "
                "160 counts BIT-IDENTISCH (Determinismus).  R0-Lektion: "
                "Einzeln-Replay EINES Circuits mit demselben Seed "
                "reproduziert Batch-Positionen > 0 NICHT (AerStatevector-"
                "RNG-Stroeme haengen am Batch-Kontext, nicht an seed+i; "
                "Bell-Referenzprobe b1==b2==b3 bit-identisch, "
                "Einzeln-Replay von pos>0 verfehlt beide Seed-Mappings)."),
            "c_cal_ideal": (
                "Readout-Kalibrier im IDEAL: p0_fraction(cal_2q) == 1.0 "
                "UND p0_fraction(cal_3q) == 1.0 (All-nuller; sonst "
                "dokumentiert, was der Kalibrier-Circuit wirklich "
                "praeperiert)."),
            "c_cell": "ISA-Zell-Diagnostik (s. design.isa_cell_diagnostik).",
            "c_law_bindings": (
                "Die gefrorenen t-Checks des Gesetzes (md5, t3, t4, t5, "
                "t6) laufen im Mirror und werden dokumentiert."),
        },
        "banned_from_raw": [
            "kappa", "ratio", "gamma", "band", "verdict", "res_v3",
            "center", "delta_cal"],
        "freeze_discipline": [
            "Prereg-Freeze (SHA-256) VOR jeder Messung "
            "(REGISTERED_NOT_MEASURED); Freeze-Vergleich an Run UND "
            "Auswertung erzwungen (053-Lektion).",
            "Roh-Commit VOR Auswertung (RAW enthaelt KEINE Verdicts).",
            "Gefrorene 055-Preregs/jobs UNANGETASTET; KEIN Re-Decide; "
            "KEINE Toleranz-Erhoehung; Mirror descriptiv.",
        ],
        "anti_sharpshooter": (
            "Alle Schwellen (0.81, 0.99, Arm-Anker) sind committete "
            "Konstanten der 044/055-Kette (KAPPA_CEILING, ANCHOR_RHO_*); "
            "die Echo-Floor 0.99 ist die IDEAL-Grenze (echo = 1 im "
            "idealen Loschmidt-Grenzwert); kein Threshold wurde neu "
            "gewaehlt um die Daten zu treffen; der Mirror ist das "
            "GEOFRORENE Gesetz selbst."),
        "runtime_abort_branches": (
            "transpile_forced kann (a) RuntimeError werfen, wenn ein "
            "FORCED-Row kein slot-2q-Ceiling erfuellt (Live-Targets "
            "driftet) oder (b) AssertionError der 12-unforced-2q-Bit-"
            "Anker (S1-Report) — beides Abbruch der runs (kein Verdict); "
            "Restart nach Reparatur."),
        "numpy_build": np.__version__,
        "qiskit_build": __import__("qiskit").__version__,
        "aer_build": __import__("qiskit_aer").__version__,
    }


def freeze_prereg(path=PREREG_PATH):
    payload = build_prereg_payload()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, sort_keys=True, separators=(",", ":"),
                  ensure_ascii=False, indent=1)
    dig = payload_sha256(payload)
    print(f"PREREG_FROZEN sha256={dig}")
    return dig


# ---------- Messung (RAW: keine Verdicts) ----------

def reduce_active(tc):
    """Aktiv-Qubit-Reduktion: qubits auf Instruktions-Qubits, clbits
    UNVERAENDERT (bit-identischer Keyspace zum QPU-Run)."""
    idx = sorted({tc.find_bit(q).index for inst in tc.data
                  for q in inst.qubits})
    if not (1 <= len(idx) <= MAX_ACTIVE_QUBITS):
        raise RuntimeError(f"Reduktions-Grenze verletzt: {len(idx)} "
                           f"aktiv (Grenze {MAX_ACTIVE_QUBITS})")
    remap = {old: new for new, old in enumerate(idx)}
    red = QuantumCircuit(len(idx), tc.num_clbits)
    for inst in tc.data:
        qi = [remap[tc.find_bit(q).index] for q in inst.qubits]
        ci = [tc.find_bit(b).index for b in inst.clbits]
        red.append(inst.operation, qi, ci)
    return red


def cell_compare(fresh_report, fresh_gate):
    """Zell-Diagnostik: frischer Report vs committeter Report/Gate
    (ops/n_2q/initial_layout je Circuit). DIAGNOSTIK, kein Gate."""
    with open(COMMITTED_ISA_REPORT, encoding="utf-8") as f:
        committed = json.load(f)
    with open(COMMITTED_ISA_GATE, encoding="utf-8") as f:
        committed_gate = json.load(f)
    fp = fresh_report["per_circuit"]
    cp = committed["per_circuit"]
    if set(fp) != set(cp):
        return {"verdict": "ISA_CELL_SET_DRIFT",
                "names_fresh_only": sorted(set(fp) - set(cp)),
                "names_committed_only": sorted(set(cp) - set(fp))}
    ops_diff = sorted(n for n in fp
                      if fp[n]["ops"] != cp[n]["ops"])
    n2q_diff = sorted(n for n in fp
                      if fp[n]["n_2q"] != cp[n]["n_2q"])
    # 12 UNFORCED (layout_source auto) tragen initial_layout in BEIDEN
    # Reports NICHT (Konvention, z.B. ladder_*). Absent-ab-sent =
    # identisch; asymmetrisch (nur eine Traeger-Seite) = echtes Delta.
    lay_diff = sorted(n for n in fp
                      if ("initial_layout" in fp[n])
                      != ("initial_layout" in cp[n])
                      or ("initial_layout" in fp[n]
                          and "initial_layout" in cp[n]
                          and list(map(int, fp[n]["initial_layout"]))
                          != list(map(int, cp[n]["initial_layout"]))))
    lay_absent_both = sorted(n for n in fp if "initial_layout" not in fp[n]
                             and "initial_layout" not in cp[n])
    verdict = ("ISA_CELL_IDENTICAL"
               if not (ops_diff or n2q_diff or lay_diff)
               else "ISA_CELL_DRIFT")
    return {
        "verdict": verdict,
        "committed_report_ref": {
            "status_committed": committed.get("status"),
            "n_circuits_committed": committed.get("n_circuits"),
            "total_two_q_committed": committed.get("total_two_q"),
            "max_two_q_committed": committed.get("max_two_q"),
        },
        "gate_tally": {
            "total_two_q_frisch_eq_committed": fresh_gate.get("total_two_q")
            == committed_gate.get("total_two_q"),
            "max_two_q_frisch_eq_committed": fresh_gate.get("max_two_q")
            == committed_gate.get("max_two_q"),
            "total_frisch": fresh_gate.get("total_two_q"),
            "total_committed": committed_gate.get("total_two_q"),
        },
        "names_alle_gleich": True,
        "ops_diff_names": ops_diff,
        "n_2q_diff_names": n2q_diff,
        "initial_layout_diff_names": lay_diff,
        "initial_layout_absent_beide": lay_absent_both,
        "n_diff": len(set(ops_diff) | set(n2q_diff) | set(lay_diff)),
        "ops_delta": {
            n: {"committed": cp[n]["ops"], "fresh": fp[n]["ops"]}
            for n in ops_diff[:12]},
        "verdict_rolle": ("DIAGNOSTIK (kein Gate): bei Drift WEITER-"
                          "LAUF (registriert) — die IDEAL-Messung haengt "
                          "an der FRISCHEN Transformation"),
    }


def run_measurement():
    if os.path.exists(RAW_PATH):
        raise SystemExit(
            f"RAW-EXISTIERT-BEREITS: {RAW_PATH} — kein stiller Re-Run "
            "(Roh-Commit-Disziplin). Loeschen ist ein expliziter Akt.")
    prereg, dig = load_frozen(expected_sha256=PREREG_SHA256)

    pts_e, cal_e, _ladder = p48.eval_grid()
    circuits = h3a.build_hardware_circuit_set(pts=pts_e, cal=cal_e)
    assert len(circuits) == p48.N_CIRCUITS

    # frische Transpile (read-only Service-Kontakt, KEIN Job)
    backend = qpu.get_backend(qpu.get_service())
    tci, totals, report, gate = qpu.transpile_forced(backend, circuits)
    with open(SV_ISA_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    with open(SV_ISA_GATE, "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=1)
    cell = cell_compare(report, gate)

    # Kontrollen c_cal_ideal + c_seed vorbereiten; Aktiv-Maximum im Loop
    reduced = []
    active_max = 0
    for tc in tci:
        red = reduce_active(tc)
        reduced.append(red)
        active_max = max(active_max, red.num_qubits)
    sim = AerSimulator(method="statevector")
    result = sim.run(reduced, shots=h3.SHOTS,
                     seed_simulator=SEED_SIMULATOR).result()
    counts_list = []
    for i, c in enumerate(circuits):
        raw_counts = result.get_counts(i)
        counts = {str(k): int(v) for k, v in raw_counts.items()}
        counts_list.append({
            "name": c["name"], "kind": c["kind"],
            "arm": c.get("arm"), "set": c.get("set"), "P": c.get("P"),
            "rep": c.get("rep"), "r": c.get("r"),
            "shots_actual": int(sum(counts.values())),
            "counts": counts,
        })
    # c_seed (R1-Mechanik): Sofort-Replay des GESAMTEN Batches im selben
    # Prozess (identische reduced-Circuits, identischer Seed) — alle 160
    # counts bit-identisch.  R0-Lektion: Einzeln-Replay EINES Circuits
    # reproduziert Batch-Positionen > 0 NICHT (die Aer-Statevector-
    # RNG-Stroeme der Experimente haengen am Batch-Kontext, nicht an
    # seed+i; bewiesen am Bell-Referenzbatch: b1==b2==b3 bit-identisch,
    # Einzeln-Replay von pos>0 verfehlt beide Seed-Mappings).
    result2 = sim.run(reduced, shots=h3.SHOTS,
                      seed_simulator=SEED_SIMULATOR).result()
    diffs = []
    for i in range(len(reduced)):
        rc = {str(k): int(v) for k, v in result2.get_counts(i).items()}
        if rc != counts_list[i]["counts"]:
            diffs.append(i)
    c_seed = {
        "mechanik": "batch-replay-im-prozess (alle 160, identischer Seed)",
        "bit_identisch": not diffs,
        "n_diff": len(diffs),
        "erste_diff_position": (diffs[0] if diffs else None),
        "erste_diff_name": (circuits[diffs[0]]["name"] if diffs else None),
        "verdict_rolle": "Kontrolle (nur booleans im RAW)",
    }
    # c_cal_ideal: Readout-Kalibrier im IDEAL (Namen aus NQ_BY_ARM abgeleitet)
    import pt_ram_q_hardware_aer as aer
    c_cal = {}
    for arm in p48.ARMS:
        nq = h3a.NQ_BY_ARM[arm]
        name = f"cal_{nq}q"
        c_cal[name] = aer.p0_fraction(
            next(e["counts"] for e in counts_list if e["name"] == name), nq)
    c_cal["ok"] = (c_cal[f"cal_{h3a.NQ_BY_ARM['q3_d3']}q"] == 1.0
                   and c_cal[f"cal_{h3a.NQ_BY_ARM['q5_d5']}q"] == 1.0)

    raw = {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "leg": LEG,
        "status": "SV_RAW_FETCHED",
        "backend": "AER_STATEVECTOR_LOCAL",
        "g_typ": G_TYP,
        "job_meta": {
            "sv": "AerSimulator(method='statevector') IDEAL — kein Noise "
                  "Model, kein QPU-Job; read-only Service-Kontakt fuer "
                  "die frische ISA-Transformation.",
            "seed_simulator": SEED_SIMULATOR,
            "sim_method": "statevector",
            "reduction": "Aktiv-Qubit-Reduktion (clbits unveraendert)",
            "dynamical_decoupling": (
                "ABWESEND (QPU-Runtime-Option DD XX; im IDEAL ohne "
                "Pulse-Ebene nicht definiert)"),
        },
        "transpile": dict(totals),
        "registered_run_config":
            p48.load_frozen_prereg()["hardware_parameters"]["run_config"],
        "fetched_at_utc": None,
        "n_circuits": len(circuits),
        "shots_per_circuit": h3.SHOTS,
        "counts_md5": qpu.counts_md5([e["counts"] for e in counts_list]),
        "sv_meta": {
            "active_qubits_max": active_max,
            "cell_diagnostik": cell,
            "c_seed": c_seed,
            "c_cal_ideal": c_cal,
        },
        "counts": counts_list,
        # ABSICHTLICH ABWESEND (banned_from_raw): kappa, ratio, gamma,
        # band, verdict, res_v3, center, delta_cal
        "prereg_sha256": dig,
        "numpy_build": np.__version__,
    }
    with open(RAW_PATH, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=1)
    print(f"RAW_WRITTEN {RAW_PATH} sha256={sha256_file(RAW_PATH)}")
    print("[run] counts_md5=%s" % raw["counts_md5"])
    print("[run] cell=%s c_seed=%s c_cal_ideal=%s"
          % (cell["verdict"], c_seed["bit_identisch"], c_cal["ok"]))
    print("[run] isa_2q_total=%s max=%s"
          % (totals["isa_2q_total"], totals["isa_2q_max"]))
    return raw


# ---------- gefrorene Auswertung ----------

def _h_verdicts_from_mirror(doc, prereg):
    ref = prereg["referenzkonstanten"]
    punkte = doc["punkte"]
    def kappa_all():
        return {k: v["kappa_hat"] for k, v in punkte.items()
                if v.get("kappa_hat") is not None}
    kas = kappa_all()
    viol = sorted(k for k, ka in kas.items() if ka < ref["kappa_ceiling"])
    v1 = V_H1_HELD if not viol and len(kas) == 37 else V_H1_REF
    h2_ok = bool(doc["c2_transfer"].get("kern_ok"))
    v2 = V_H2_HELD if h2_ok else V_H2_REF
    lad = doc["echo_ladder"]
    kb = {arm: lad.get(arm, {}).get("fit_kappa_block")
          for arm in p48.ARMS}          # fit_kappa_block ist ein float
    v3 = (V_H3_HELD
          if all(ka is not None and ka >= ref["echo_floor_ideal"]
                 for ka in kb.values()) else V_H3_REF)
    c1 = doc["c1_sessions_anker"]
    rh = {arm: (c1.get(arm) or {}).get("rho_fresh_vs_s1")
          for arm in p48.ARMS}
    v4 = (V_H4_HELD
          if (rh["q5_d5"] is not None
              and rh["q5_d5"] >= ref["anchor_rho_q5"]
              and rh["q3_d3"] is not None
              and rh["q3_d3"] >= ref["anchor_rho_q3"]) else V_H4_REF)
    vals = [v1, v2, v3, v4]
    held = sum(1 for x in vals if x.endswith("_HELD"))
    if held == 4:
        kern = KERN_ALL
    elif held == 0:
        kern = KERN_NONE
    else:
        kern = KERN_MIXED
    return (v1, v2, v3, v4, kern), {
        "H-055B-1": {"verdict": v1, "n_kappas": len(kas),
                     "kappa_min": (min(kas.values()) if kas else None),
                     "kappa_max": (max(kas.values()) if kas else None),
                     "violated": viol},
        "H-055B-2": {"verdict": v2, "kern_ok": h2_ok,
                     "below_fresh_q5": doc["c2_transfer"].get(
                         "below_fresh_q5")},
        "H-055B-3": {"verdict": v3, "kappa_block": kb,
                     "floor": ref["echo_floor_ideal"]},
        "H-055B-4": {"verdict": v4, "rho_fresh_vs_s1": rh,
                     "anchoren": {"q5": ref["anchor_rho_q5"],
                                  "q3": ref["anchor_rho_q3"]}},
    }


def run_evaluation():
    prereg, dig = load_frozen(expected_sha256=PREREG_SHA256)
    with open(RAW_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    doc = ev.evaluate(raw_path=RAW_PATH, stage3_path=STAGE3_PATH,
                      isa_path=SV_ISA_REPORT, gate_path=SV_ISA_GATE,
                      prereg_path=None)
    (v1, v2, v3, v4, kern), details = _h_verdicts_from_mirror(doc, prereg)
    ts = {k: (v.get("ok") if isinstance(v, dict) else None)
          for k, v in doc["kontrollen"].items()
          if k.startswith("t")}
    control_ok = (doc["counts_md5_verified"]
                  and all(ts.get(k) for k in ("t3_identity_two_ways",
                                              "t4_negative_must_not_fire",
                                              "t5_gate_set_frozen",
                                              "t6_mass_conservation")))
    # 055b-eigene Kontrollen aus dem RAW (R1-Mechanik) — ein Fehlbetrag
    # ist INVALID, nicht REFUTED (Kontrollen-Disziplin, 046b-Praezedenz).
    sv_meta = raw["sv_meta"]
    k055b = {
        "c_seed": sv_meta["c_seed"]["bit_identisch"],
        "c_cal_ideal": sv_meta["c_cal_ideal"]["ok"],
        "c_cell_verdict": sv_meta["cell_diagnostik"]["verdict"],
    }
    invalid = (
        isinstance(doc.get("verdict"), str)
        and doc["verdict"].startswith("EVALUATION_INVALID"))
    if invalid or not (k055b["c_seed"] and k055b["c_cal_ideal"]):
        kern = KERN_INVALID
    eval_doc = {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "leg": LEG,
        "status": "SV_EVAL_COMPLETED",
        "prereg_sha256": dig,
        "mirror_status": {
            "law_verdict": doc["verdict"],
            "verdict_map_text": doc["verdict_map_text"],
            "refit_status": doc["refit_status"],
            "t_checks": ts,
            "control_ok": control_ok,
            "counts_md5_verified": doc["counts_md5_verified"],
            "verdict_rolle": "descriptiv — kein Verdict-Erlass, 055-"
                             "Verdicts bleiben dem QPU-Job vorbehalten",
        },
        "verdicts": {
            "H-055B-1": v1, "H-055B-2": v2, "H-055B-3": v3,
            "H-055B-4": v4, "kern": kern,
            "verdict_tragend_fuer": "055b (H-055B) — NICHT fuer die "
                                    "055-QPU-Kette (deren Verdicts "
                                    "bleiben dem QUEUED Job vorbehalten)",
        },
        "details": details,
        "kontrollen_055b": {
            **k055b,
            "controls_055b_ok": k055b["c_seed"] and k055b["c_cal_ideal"],
            "invalid_grund": (doc.get("verdict") if invalid
                              else ("kontrollen_055b_fehl" if not (
                                  k055b["c_seed"] and k055b["c_cal_ideal"])
                              else None)),
            "c_cal_ideal_werte": sv_meta["c_cal_ideal"],
            "c_seed_streng": sv_meta["c_seed"],
            "active_qubits_max": sv_meta["active_qubits_max"],
            "verdict_rolle": ("Kontrollen INVALID, nicht REFUTED "
                              "(046b-Praezedenz); c_cell ist descriptiv "
                              "DIAGNOSTIK (WEITERLAUF-Regel)"),
        },
        "sv_meta_from_raw": {
            "cell_diagnostik": doc.get("isa_leg_dokumentation"),
            "mirrored_from": RAW_PATH,
        },
        "context": {
            "055_fez_job_id": "db0m71qvog1s73fh15og",
            "055_fez_job_status": "QUEUED (unangetastet)",
            "s1_s2_verdict_kontext": (
                "047 S2 fez VERDICT (H-RAM-Q-5a_SESSIONROBUST); S1 044 "
                "H-RAM-Q-4_REFUTED — 055b ist IDEAL-Referenz zu beiden"),
        },
        "integritaet": [
            "Mirror durch das GEFRORENE Gesetz (evaluate) — alle t-Checks "
            "laufend; KEINE Toleranz-Erhoehung; kein Re-Decide.",
            "Verdicts H-055B-1..4 sind von DEM GEFRORENEN Prereg ex ante "
            "festgelegt; Details aus dem Mirror-DOC.",
        ],
    }
    with open(EVAL_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_doc, f, sort_keys=True, separators=(",", ":"),
                  ensure_ascii=False, indent=1)
    print("EVAL_WRITTEN", EVAL_PATH)
    print("[eval] mirror legal verdict: %s" % doc["verdict"])
    print("[eval] H-055B-1 %s | H-055B-2 %s | H-055B-3 %s | H-055B-4 %s"
          % (v1, v2, v3, v4))
    print("[eval] kern: %s" % kern)
    return eval_doc


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