"""
EXPERIMENT 032 - Ququint auf IBMQ, Phase 3a: Prereg-Freeze (simulator-only).

Anti-Sharpshooter: die Vorhersagen fuer den EINEN Fez-Job (Phase 3b/3c,
pt_ququint_fez) werden HIER registriert — bevor irgendein Hardware-Zugriff
dieses Experiments stattfindet. Die Predictions sind berechnet aus der
deterministischen Phase-2-STRESS-Kurve (pt_ququint_ibmq_aer, seed 42,
n=8192, Readout 1e-2, 2q-Ratio 10) — NICHT aus Hardware-Daten.

Prereg-Struktur (auditierbar via pt_prereg_audit):
  - decision_rule: "phi_margin_pass AND sep_margin_pass AND confound_pass"
    (sandboxed Grammatik: phi_Margin > 0 = Verschränkung bezeugt,
     sep_Margin < 0 = Kontrolle korrekt NICHT geflaggt,
     confound_max_diff <= 0.05 = §Z.11-Populations-Konfund kontrolliert)
  - predictions: 3 Sign-Konstanten (True) + 3 Fez-nahe Punkt-Prognosen
    (p1 = 3e-4, informativ)
  - prediction_bands: numerische Bänder über das Fez-nahe Fenster
    p1 in [1e-4, 3e-3] — das STRESS-Band, nicht ein Punktversprechen
  - md5 ueber kanonisches JSON des Payloads (KEIN Timestamp im gehashten
    Inhalt — der Freeze ist inhaltlich deterministisch, "Prereg MD5 stabil")

Der STRESS-Typ ist bewusst dokumentiert: not a calibrated Fez model — die
Bänder sind Vorhersagen unter konservativer Ueberzaehlung, die
Sign-Vorhersagen sind der harte preregistrierte Teil.
"""

import hashlib
import json
import os
import sys
from functools import lru_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pt_prereg_audit import audit_prereg_structure  # noqa: F401 (Re-Export)
from pt_ququint_ibmq_aer import (
    NOISE_GRID_DEFAULT,
    N_SHOTS_DEFAULT,
    READOUT_ERROR_DEFAULT,
    TWO_Q_RATIO_DEFAULT,
    run_witness,
)

# Fez-nahes STRESS-Fenster: p1 = 1q-Depolarisierungsrate; ratio*p1 = cx-Fehler.
# ratio=10 -> Fenster entspricht cx-Fehlerraten 1e-3 .. 3e-2; der Fez-nahe
# Referenzpunkt ist p1 = 3e-4 (cx ~ 3e-3), wie im §Z.13.5-Prereg-Draft.
STRESS_GRID_SLICE = (1e-4, 3e-4, 1e-3, 3e-3)
FEZ_POINT_P1 = 3e-4
N_SHOTS = N_SHOTS_DEFAULT          # 8192 pro Circuit
BACKEND_NAME = "ibm_fez"
N_CIRCUITS = 12
CIRCUIT_ORDER = (
    ["phi_C", "phi_D"] + [f"sep_C_{k}" for k in range(5)] + [f"sep_D_{k}" for k in range(5)]
)
DECISION_RULE = "phi_margin_pass AND sep_margin_pass AND confound_pass"
PREREG_PATH = "pt_ququint_fez_prereg.json"

_CONFOUND_LIMIT = 0.05   # §Z.11/§Z.13.4: Populations-Konfund-Schwelle


@lru_cache(maxsize=1)
def stress_predictions():
    """Deterministische STRESS-Vorhersagen aus Phase 2 (seed 42, 8192 Shots).

    Bänder = [min, max] der Margin-Werte über das Fez-nahe Fenster.
    fez_point = der p1=3e-4-Punkt (die §Z.13.5-Prereg-Draft-Grundlage).
    """
    points = [
        run_witness(p1, n_shots=N_SHOTS, seed=42,
                    ro=READOUT_ERROR_DEFAULT, ratio=TWO_Q_RATIO_DEFAULT)
        for p1 in STRESS_GRID_SLICE
    ]
    bands = {
        "phi_margin": [min(p["phi"]["margin"] for p in points),
                       max(p["phi"]["margin"] for p in points)],
        "sep_margin": [min(p["sep"]["margin"] for p in points),
                       max(p["sep"]["margin"] for p in points)],
        "confound_max_diff": [min(p["confound_max_diff"] for p in points),
                              max(p["confound_max_diff"] for p in points)],
    }
    fez_point = next(p for p in points if abs(p["p1"] - FEZ_POINT_P1) < 1e-15)
    return {"grid": list(STRESS_GRID_SLICE), "points": points,
            "bands": bands, "fez_point": fez_point}


def build_prereg_payload():
    """Der deterministische Prereg-Payload (KEIN Timestamp im gehashten Inhalt).

    Enthaelt die pt_prereg_audit-Pflichtfelder (md5 wird auf Payload-Ebene
    vom Freeze-Dokument getragen), die Run-Konfiguration VOR der Submission
    und die Vorhersagen aus Phase 2.
    """
    sp = stress_predictions()
    fez = sp["fez_point"]
    payload = {
        "experiment": "032-ququint-fez-phase3",
        "registered_before": (
            "Kein Hardware-Zugriff dieses Experiments fand vor diesem Freeze "
            "statt — alle Zahlen stammen aus der Phase-2-Aer-STRESS-Kurve."
        ),
        "backend": BACKEND_NAME,
        "token_account": "TOKEN1 (IBMQ_TOKEN); TOKEN2 unberuehrt",
        "n_shots": N_SHOTS,
        "n_circuits": N_CIRCUITS,
        "circuit_order": list(CIRCUIT_ORDER),
        "run_config": {
            "optimization_level": 3,
            "dynamical_decoupling": "XX",
            "resilience": "none (raw SamplerV2 counts)",
        },
        "decision_rule": DECISION_RULE,
        "predictions": {
            "phi_margin_pass": True,
            "sep_margin_pass": True,
            "confound_pass": True,
            "phi_margin": float(fez["phi"]["margin"]),
            "sep_margin": float(fez["sep"]["margin"]),
            "confound_max_diff": float(fez["confound_max_diff"]),
        },
        "prediction_bands": {
            "phi_margin": {
                "band": [float(sp["bands"]["phi_margin"][0]),
                         float(sp["bands"]["phi_margin"][1])],
                "prediction": "strikt positiv im ganzen Fenster (Verschränkung gewitzt)",
            },
            "sep_margin": {
                "band": [float(sp["bands"]["sep_margin"][0]),
                         float(sp["bands"]["sep_margin"][1])],
                "prediction": "strikt negativ im ganzen Fenster (Kontrolle nie geflaggt)",
            },
            "confound_max_diff": {
                "band": [float(sp["bands"]["confound_max_diff"][0]),
                         float(sp["bands"]["confound_max_diff"][1])],
                "prediction": "<= 0.05 im Fenster (Populations-Konfund kontrolliert)",
            },
        },
        "decision_rule_semantics": {
            "phi_margin_pass": "phi_margin = v_hat - 4*SE - 1/5 > 0",
            "sep_margin_pass": "sep_margin < 0 (Kontrolle korrekt NICHT geflaggt)",
            "confound_pass": "confound_max_diff <= 0.05",
        },
        "witness_definition": (
            "V = sum_a p~(a,a) nach Messung D (U = F (x) F-dagger); "
            "Separabilitaetsschranke 1/5; margin = v_hat - 4*SE - 1/5"
        ),
        "stress_model": {
            "type": "stress (not a calibrated Fez model)",
            "readout": READOUT_ERROR_DEFAULT,
            "two_q_ratio": TWO_Q_RATIO_DEFAULT,
            "grid_slice": list(STRESS_GRID_SLICE),
            "grid_full_phase2": list(NOISE_GRID_DEFAULT),
        },
    }
    return payload


def canonical_payload_json(payload):
    """Kanonisches JSON (sortiert, ohne Whitespace) als md5-Grundlage."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def payload_md5(payload):
    """md5 ueber das kanonische JSON des Payloads (deterministisch)."""
    return hashlib.md5(canonical_payload_json(payload).encode("utf-8")).hexdigest()


def freeze_prereg(path=PREREG_PATH):
    """Friert den Payload ein: FLAT-Format {"...payload...", "md5": ...}.

    pt_prereg_audit.audit_run verlangt die Pflichtfelder (md5, decision_rule,
    predictions) auf TOP-LEVEL der Prereg-Datei — daher wird das md5 direkt
    ins Payload-Top-Level geschrieben, ueber den Payload OHNE das md5-Feld
    (sonst selbst-referentiell). Die Datei wird VOR jedem Hardware-Zugriff
    erzeugt und committed (Anti-Sharpshooter: der Freeze liegt in git, bevor
    Fez-Daten existieren).
    """
    payload = build_prereg_payload()
    doc = dict(payload)
    doc["md5"] = payload_md5(payload)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
    return doc


def verify_prereg_md5(doc):
    """Recomputes md5 ueber doc OHNE das md5-Feld und vergleicht."""
    try:
        stripped = {k: v for k, v in doc.items() if k != "md5"}
        return payload_md5(stripped) == doc["md5"]
    except (KeyError, TypeError):
        return False


def load_frozen_prereg(path=PREREG_PATH):
    """Laedt das Freeze-Dokument (flat, mit top-level md5) und verifiziert es."""
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    if not verify_prereg_md5(doc):
        raise ValueError(f"Prereg-md5-MISMATCH in {path} — Payload wurde nach "
                         "dem Freeze veraendert (Tamper-Detektion)")
    return doc["payload"]


def build_emulated_result():
    """Ein ALS EMULIERT markiertes Pseudo-Result (Phase-2-STRESS-Punkt 3e-4).

    Zweck: Pipeline-Validierung von audit_run in Emulation (Tests) — niemals
    als Hardware-Datenausgabe verwenden (Marker 'emulated': True).
    """
    fez = stress_predictions()["fez_point"]
    return {
        "emulated": True,
        "source": "pt_ququint_ibmq_aer.witness_curve p1=3e-4 seed=42 (Phase 2)",
        "phi_margin_pass": bool(fez["phi"]["margin"] > 0.0),
        "sep_margin_pass": bool(fez["sep"]["margin"] < 0.0),
        "confound_pass": bool(fez["confound_max_diff"] <= _CONFOUND_LIMIT),
        "phi_margin": float(fez["phi"]["margin"]),
        "sep_margin": float(fez["sep"]["margin"]),
        "confound_max_diff": float(fez["confound_max_diff"]),
        "phi_v_hat": float(fez["phi"]["v_hat"]),
        "phi_se": float(fez["phi"]["se"]),
        "sep_v_hat": float(fez["sep"]["v_hat"]),
        "sep_se": float(fez["sep"]["se"]),
    }