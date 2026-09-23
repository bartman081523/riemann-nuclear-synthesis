"""EXPERIMENT 032 - Ququint V3 (H-STAR-3): GUE-r-Statistik als drittes
Observable (Montgomery/Odlyzko) im encodierten H_PT-Spektrum.

Frage: Ist das encodierte Spektrum (Tensor-Summe der 5x5-PT-Bloecke im
25-dim bzw. 625-dim Logikraum) in der Wigner-Dyson-Repulsions-Klasse
(GOE/GUE, <r> ≈ 0.53) — wie die Zeta-Nullstellen (Odlyzko) — oder
Poisson/integrabel (<r> ≈ 0.386) bzw. quasi-harmonisch regulaer?

Anti-Sharpshooter: das Prereg (Klassen-Baender, gamma-Familie, Kontroll-
Gates, Falsifikator-Erwartung) wird VOR der Kurven-Berechnung gefroren
(md5). Reine numpy-Mathematik, kein qiskit, 0 QPU.

Geometrie (registrierte Encodierung):
  Block:   H_PT_5(gamma) = H_diag_5 + i*gamma*A_5  (Experiment 011,
           entkoppeltes 5. Niveau: block_diag(A_4, 0), E_4 = 5.0 exakt)
  25-dim:  H = H_PT_5(g1) (x) I + I (x) H_PT_5(g2)
           Eigenwerte = {E_i + F_j} exakt (Tensor-Summe)
  625-dim: 4-fache Tensor-Summe -> {E_i + E_j + E_k + E_l}, 5^4 = 625
  Wiederholte gamma-Werte erzeugen exakte Zwillingssummen E_i + E_j =
  E_j + E_i (Float-additiv kommutativ) -> Kollaps; registrierte Geometrie.
  Konvention wie pt_spectral_gaps: Abstands-Statistik auf den REAL-Teilen
  (Sortierung nach Re), exakte Re-Degenerationen kollabiert (tol 1e-9).

r-Statistik (Oganesyan-Huse, unfolding-frei):
  r_n = min(d_n, d_{n+1}) / max(d_n, d_{n+1}),  <r> = Mittelwert
  Referenzkonstanten (Atas-Bogomolny-Giraud-Roux, PRL 110, 084101 (2013),
  arXiv:1212.5611, large-N-Fits):
    Poisson 2 ln 2 - 1 = 0.38629 | GOE 0.5307 | GUE 0.5996 | GSE 0.6744
  KORREKTUR VOR dem Freeze: der Plan §Z.15 fuehrt 0.5359 als "<r>_GUE" —
  das ist laut Atas et al. die GOE-SURMISE-Konstante (4 - 2 sqrt(3) =
  0.53590), fehlinterpretiert. Eigene Schaetzer-Validierung (Ginibre,
  d = 1000): GOE -> 0.5314, GUE -> 0.6013, Poisson -> 0.3857 — konsistent
  mit den korrigierten Werten. Ohne die Korrektur haette das geplante
  GUE-Band [0.50, 0.58] ein ECHTES GUE-Spektrum (<r> = 0.60) als
  REGULAER (>= 0.60) FALSCH-FALSIFIZIERT. Mit den korrigierten Werten
  sind GOE (0.5307) und GUE (0.5996) getrennt aufloesbar (Differenz
  0.069 >> Kontrolltoleranz 0.01). Zeta-Referenzklasse (Montgomery/
  Odlyzko): GUE (beta = 2).

Klassen-Baender (Prereg, VOR der Berechnung, auf die korrigierten
Referenzwerte zentriert):
  GUE-Klasse   [0.565, 0.63]    GOE-Band      [0.50, 0.565]
  Poisson-Band [0.34, 0.45]
  REGULAER     >= 0.70 (quasi-harmonisch/Drei-Abstaende, NICHT WD)
  DEGENERAT    < 0.34           GRAU sonst ([0.45,0.50) ∪ [0.63,0.70))

gamma-Familie (registriert): {0.002, 0.02, 0.2} (niedrig / etabliert
(Experiment 006) / stark). 25-dim: alle Paare g1 < g2 (3 Konfigurationen —
(g1,g2) und (g2,g1) geben bei Tensor-Summen IDENTISCHE Spektren);
625-dim: alle 4-Tupel mit mindestens 2 verschiedenen Werten (78). Diagonal-
Konfigurationen (alle gamma gleich) sind aus der Primaerfamilie
ausgeschlossen (exakte Tensor-Symmetrie-Degenerationen E_i+E_j = E_j+E_i).

Falsifikator-Erwartung (Prereg): t25_gue = False, t625_gue = False —
die Tensor-Summe DETERMINISTISCHER strukturierter Spektren erzeugt
generisch KEINE Wigner-Dyson-Repulsion (erwartet: REGULAER oder POISSON).
Ein GUE-Befund waere die Ueberraschung (Kern-Isomorphie ueberlebt die
Encodierung).

Kontroll-Gates (Validierung des Schaetzers auf dieser Maschine):
  GUE-Positivkontrolle (Ginibre-Hermitisch beta=2, 25/625-dim, 200/50):
      |<r> - 0.5996| <= 0.01
  GOE-Positivkontrolle (Ginibre-Reell beta=1, 200/50 Samples):
      |<r> - 0.5307| <= 0.01
  Poisson-Negativkontrolle (iid-uniform sortiert, 200/50 Samples):
      |<r> - 0.3863| <= 0.01
  Kontrollfehler -> EVALUATION_INVALID (vor Hypothesen-Verdict).

Sekundaer (deskriptiv): Per-Konfiguration <r>, Block-Spektra-Luecken,
Shuffle-Null (gaps permutiert, seed 20260923, 200 Permutationen — trennt
Repulsions-Information von reiner Gap-Dispersion).
"""

import hashlib
import itertools
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pt_ququint_vqe import H_PT_ququint

PREREG_PATH = "pt_gue_prereg_v3.json"
EXPERIMENT = "032-ququint-v3-gue-rstat"
DECISION_RULE = "t25_gue_band AND t625_gue_band (nach Kontroll-Gates)"

GUE_R = 0.5996   # Atas et al. (arXiv:1212.5611) large-N; Surmise 0.60266
GOE_R = 0.5307   # large-N; Surmise 4 - 2*sqrt(3) = 0.53590
POISSON_R = 0.3863  # exakt 2 ln 2 - 1 = 0.38629
GSE_R = 0.6744   # dokumentiert, hier nicht erwartet (nur beta <= 2)

GOE_BAND = (0.50, 0.565)
GUE_BAND = (0.565, 0.63)
POISSON_BAND = (0.34, 0.45)
REGULAR_MIN = 0.70
DEGENERATE_MAX = 0.34

GAMMA_FAMILY = (0.002, 0.02, 0.2)
COLLAPSE_TOL = 1e-9

CONTROL_TOL = 0.01
N_CONTROLS_25 = 200
N_CONTROLS_625 = 50

NULL_SEED = 20260923
N_SHUFFLE = 200


# === Bloecke + encodierte Spektren ===

def block_spectrum(gamma):
    """Re-Teile des 5x5-PT-Blocks (aufsteigend sortiert, 5 Werte)."""
    H, _, _ = H_PT_ququint(gamma=gamma)
    eig = np.linalg.eigvals(H)
    return np.sort(eig.real)


def collapse_sorted(vals, tol=COLLAPSE_TOL):
    """Aufsteigend sortieren und Werte innerhalb tol kollabieren."""
    x = np.sort(np.asarray(vals, dtype=float))
    out = []
    for v in x:
        if not out or v - out[-1] > tol:
            out.append(v)
    return np.array(out)


def r_statistic(distinct):
    """<r> der Oganesyan-Huse-Statistik (None falls M < 3)."""
    x = np.asarray(distinct, dtype=float)
    if x.size < 3:
        return None
    d = np.diff(x)
    denom = np.maximum(d[:-1], d[1:])
    r = np.minimum(d[:-1], d[1:]) / denom
    return float(r.mean())


def encoded_re_spectrum(gammas):
    """Tensor-Summen-Spektrum (Re-Teile): alle Summen ueber die Bloecke."""
    blocks = [block_spectrum(g) for g in gammas]
    acc = blocks[0]
    for nxt in blocks[1:]:
        acc = np.asarray(acc)[:, None] + np.asarray(nxt)[None, :]
        acc = acc.ravel()
    return np.asarray(acc, dtype=float)


def family_configs_25():
    """Primärfamilie 25-dim: alle Paare g1 < g2."""
    return [(g1, g2) for g1, g2 in itertools.combinations(GAMMA_FAMILY, 2)]


def family_configs_625():
    """Primärfamilie 625-dim: 4-Tupel mit mindestens 2 verschiedenen Werten."""
    out = []
    for combo in itertools.product(GAMMA_FAMILY, repeat=4):
        if len(set(combo)) >= 2:
            out.append(combo)
    return out


# === Kontrollen ===

def gue_control(d, n, seed=NULL_SEED):
    """Positivkontrolle GUE: Ginibre-Hermitisch (G+G^dagger)/2, d-dim."""
    rng = np.random.default_rng(seed)
    rs = []
    for _ in range(n):
        g = (rng.standard_normal((d, d))
             + 1j * rng.standard_normal((d, d))) / np.sqrt(2.0)
        h = (g + g.conj().T) / 2.0
        rs.append(r_statistic(collapse_sorted(np.linalg.eigvalsh(h))))
    return float(np.mean(rs))


def goe_control(d, n, seed=NULL_SEED):
    """Positivkontrolle GOE: reell-symmetrisch (G+G^T)/2, d-dim."""
    rng = np.random.default_rng(seed)
    rs = []
    for _ in range(n):
        g = rng.standard_normal((d, d))
        h = (g + g.T) / 2.0
        rs.append(r_statistic(collapse_sorted(np.linalg.eigvalsh(h))))
    return float(np.mean(rs))


def poisson_control(d, n, seed=NULL_SEED):
    """Negativkontrolle: iid-uniform sortierte Punkte (Poisson-Prozess)."""
    rng = np.random.default_rng(seed)
    rs = []
    for _ in range(n):
        pts = np.sort(rng.uniform(0.0, float(d), size=d))
        rs.append(r_statistic(collapse_sorted(pts)))
    return float(np.mean(rs))


def shuffle_null(distinct, n_perm=N_SHUFFLE, seed=NULL_SEED):
    """Strukturelle Null: Gap-Folge permutiert (zerstoert Ordnungs-
    korrelationen, erhaelt die Gap-Dispersion)."""
    rng = np.random.default_rng(seed)
    x = np.asarray(distinct, dtype=float)
    if x.size < 3:
        return None
    gaps = np.diff(x)
    vals = np.empty(n_perm)
    for j in range(n_perm):
        perm = rng.permutation(gaps)
        r = np.minimum(perm[:-1], perm[1:]) / np.maximum(perm[:-1], perm[1:])
        vals[j] = r.mean()
    return float(vals.mean())


# === Klassen + Verdict ===

def classify(r):
    """Klassenzuordnung nach den registrierten Baendern."""
    if r is None:
        return "LEER"
    if r < DEGENERATE_MAX:
        return "DEGENERAT"
    if POISSON_BAND[0] <= r <= POISSON_BAND[1]:
        return "POISSON"
    if GUE_BAND[0] <= r <= GUE_BAND[1]:
        return "GUE"
    if GOE_BAND[0] <= r <= GOE_BAND[1]:
        return "GOE"
    if r >= REGULAR_MIN:
        return "REGULAER"
    return "GRAU"


def verdict(cls25, cls625):
    if cls25 in ("POISSON", "REGULAER") or cls625 in ("POISSON", "REGULAER"):
        return "H-STAR-3_REFUTED"
    if cls25 == "GUE" and cls625 == "GUE":
        return "H-STAR-3_CONFIRMED_GUE_KLASSE"
    if cls25 in ("GUE", "GOE") and cls625 in ("GUE", "GOE"):
        return "H-STAR-3_TEILWEISE_WD_GOE"
    return "H-STAR-3_INKONKLUSIV"


# === Prereg ===

def build_prereg_payload():
    """Deterministischer Prereg-Payload (KEIN Timestamp im gehashten Inhalt)."""
    return {
        "experiment": EXPERIMENT,
        "registered_before": (
            "Die encodierten r-Statistiken (25/625-dim) wurden vor diesem "
            "Freeze NICHT berechnet; nur die Referenzkonstanten (GUE 0.5359, "
            "Poisson 0.3863, GOE 0.5307) und die 5x5-Blockstruktur aus "
            "Experiment 005/006/011 sind Vorwissen. Die Falsifikator-"
            "Erwartung (REGULAER/POISSON, nicht GUE) ist als Vorhersage "
            "fixiert — ein GUE-Befund waere die Ueberraschung."
        ),
        "hypothesis": (
            "H-STAR-3: Das encodierte H_PT-Spektrum liegt in der Wigner-"
            "Dyson-Repulsions-Klasse (wie die Zeta-Nullstellen, "
            "Montgomery/Odlyzko) -> drittes unabhaengiges MOCS-Observable. "
            "Annahme: die Encodierung erhaelt die Universalklasse."
        ),
        "steelman": (
            "Tensor-Summen DETERMINISTISCHER strukturierter 5x5-Spektren "
            "erzeugen generisch keine WD-Repulsion: erwartet REGULAER "
            "(quasi-harmonisch) oder POISSON."
        ),
        "encoding": {
            "block": "H_PT_5(gamma) = H_diag_5 + i*gamma*A_5 (Experiment 011; "
                     "entkoppeltes 5. Niveau E=5.0 exakt)",
            "d25": "H_PT_5(g1) (x) I + I (x) H_PT_5(g2) -> {E_i + F_j}",
            "d625": "4-fache Tensor-Summe -> 5^4 = 625 Summen",
            "statistic_convention": "Re-Teile, Sortierung nach Re (wie "
                                    "pt_spectral_gaps Delta-E-Konvention)",
        },
        "decision_rule": DECISION_RULE,
        "reference_correction": (
            "Der Plan §Z.15 fuehrt <r>_GUE = 0.5359 — laut Atas et al. "
            "(arXiv:1212.5611, PRL 110, 084101 (2013)) ist das die GOE-"
            "SURMISE-Konstante (4 - 2 sqrt(3) = 0.53590); GUE ist 0.5996 "
            "(large-N). Eigene Schaetzer-Validierung vor dem Freeze: "
            "GOE d=1000 -> 0.5314, GUE d=1000 -> 0.6013, Poisson -> 0.3857. "
            "Die Baender sind auf die korrigierten Werte zentriert; ohne "
            "die Korrektur wuerde ein echtes GUE-Spektrum (0.60) als "
            "REGULAER falsch-falsifiziert. Korrigiert VOR der Kurven-"
            "berechnung und VOR diesem Freeze."
        ),
        "gamma_family": list(GAMMA_FAMILY),
        "families": {
            "d25": "alle Paare g1 < g2 (3 Konfigurationen; (g1,g2) und "
                   "(g2,g1) sind spektral identisch)",
            "d625": "alle 4-Tupel mit >= 2 verschiedenen Werten (78; "
                    "wiederholte gamma erzeugen exakte Zwillingssummen, "
                    "Kollaps vor der Statistik)",
            "diag_configs_excluded_reason": "exakte Tensor-Symmetrie-"
                                            "Degenerationen",
        },
        "predictions": {"t25_gue": False, "t625_gue": False},
        "thresholds": {
            "gue_band": list(GUE_BAND),
            "goe_band": list(GOE_BAND),
            "poisson_band": list(POISSON_BAND),
            "regular_min": REGULAR_MIN,
            "degenerate_max": DEGENERATE_MAX,
            "collapse_tol": COLLAPSE_TOL,
            "control_tol": CONTROL_TOL,
            "control_references": {"gue": GUE_R, "goe": GOE_R,
                                   "poisson": POISSON_R,
                                   "gse_documented": GSE_R},
        },
        "controls": {
            "gue_25": [N_CONTROLS_25, "Ginibre-Hermitisch (beta=2)"],
            "goe_25": [N_CONTROLS_25, "Ginibre-Reell (beta=1)"],
            "poisson_25": [N_CONTROLS_25, "iid-uniform sortiert"],
            "gue_625": [N_CONTROLS_625, "Ginibre-Hermitisch (beta=2)"],
            "goe_625": [N_CONTROLS_625, "Ginibre-Reell (beta=1)"],
            "poisson_625": [N_CONTROLS_625, "iid-uniform sortiert"],
            "gate": "Kontrollfehler -> EVALUATION_INVALID",
        },
        "nulls": {
            "shuffle": "Gap-Folge permutiert x %d (seed %d), deskriptiv — "
                       "trennt Repulsion von Gap-Dispersion" % (N_SHUFFLE, NULL_SEED),
        },
        "verdict_map": {
            "H-STAR-3_CONFIRMED_GUE_KLASSE": "cls25 == GUE AND cls625 == GUE",
            "H-STAR-3_TEILWEISE_WD_GOE": "beide in {GUE, GOE}, mind. 1x GOE",
            "H-STAR-3_REFUTED": "cls in {POISSON, REGULAER} (mind. 1 dim)",
            "H-STAR-3_INKONKLUSIV": "sonst (GRAU/DEGENERAT/LEER)",
        },
    }


def canonical_payload_json(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def payload_md5(payload):
    return hashlib.md5(canonical_payload_json(payload).encode("utf-8")).hexdigest()


def freeze_prereg(payload=None):
    if payload is None:
        payload = build_prereg_payload()
    doc = dict(payload)
    doc["md5"] = payload_md5(payload)
    return doc


def verify_prereg_md5(doc):
    stripped = {k: v for k, v in doc.items() if k != "md5"}
    return payload_md5(stripped) == doc["md5"]


def load_frozen_prereg(path=PREREG_PATH):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if not verify_prereg_md5(doc):
        raise ValueError(f"Prereg-md5-MISMATCH in {path}")
    return doc


# === Evaluation ===

def _family_mean(gammas_list):
    rs, per_config = [], []
    for gammas in gammas_list:
        spec = collapse_sorted(encoded_re_spectrum(gammas))
        r = r_statistic(spec)
        if r is None:
            per_config.append({"gammas": list(gammas), "r": None,
                               "levels": int(spec.size)})
            continue
        rs.append(r)
        per_config.append({"gammas": list(gammas), "r": r,
                           "levels": int(spec.size)})
    mean = float(np.mean(rs)) if rs else None
    return mean, per_config


def run_v3():
    """Volle V3-Evaluation (deterministisch, seeded, 0 QPU)."""
    controls = {
        "gue_25": gue_control(25, N_CONTROLS_25),
        "goe_25": goe_control(25, N_CONTROLS_25),
        "poisson_25": poisson_control(25, N_CONTROLS_25),
        "gue_625": gue_control(625, N_CONTROLS_625),
        "goe_625": goe_control(625, N_CONTROLS_625),
        "poisson_625": poisson_control(625, N_CONTROLS_625),
    }
    controls_ok = (
        abs(controls["gue_25"] - GUE_R) <= CONTROL_TOL
        and abs(controls["goe_25"] - GOE_R) <= CONTROL_TOL
        and abs(controls["poisson_25"] - POISSON_R) <= CONTROL_TOL
        and abs(controls["gue_625"] - GUE_R) <= CONTROL_TOL
        and abs(controls["goe_625"] - GOE_R) <= CONTROL_TOL
        and abs(controls["poisson_625"] - POISSON_R) <= CONTROL_TOL
    )

    mean25, per25 = _family_mean(family_configs_25())
    mean625, per625 = _family_mean(family_configs_625())
    cls25 = classify(mean25)
    cls625 = classify(mean625)

    # Shuffle-Null (deskriptiv) auf der ersten Konfiguration je Dimension
    spec25 = collapse_sorted(encoded_re_spectrum(family_configs_25()[0]))
    spec625 = collapse_sorted(encoded_re_spectrum(family_configs_625()[0]))
    shuffle = {
        "d25": shuffle_null(spec25),
        "d625": shuffle_null(spec625),
        "note": "deskriptiv, kein Gate",
    }

    blocks = {g: block_spectrum(g).tolist() for g in GAMMA_FAMILY}

    return {
        "experiment": EXPERIMENT,
        "prereg_path": PREREG_PATH,
        "controls": controls,
        "controls_ok": bool(controls_ok),
        "mean_r_d25": mean25,
        "mean_r_d625": mean625,
        "class_d25": cls25,
        "class_d625": cls625,
        "per_config_d25": per25,
        "per_config_d625": per625,
        "shuffle_null": shuffle,
        "block_spectra_re": blocks,
        "references": {"gue": GUE_R, "goe": GOE_R, "poisson": POISSON_R,
                       "gse": GSE_R},
        "decision_rule": DECISION_RULE,
        "verdict": (verdict(cls25, cls625) if controls_ok
                    else "EVALUATION_INVALID_KONTROLLEN_FEHLEN"),
    }


def main():
    res = run_v3()
    with open("pt_gue_v3_results.json", "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    doc = load_frozen_prereg()
    print("VERDICT:", res["verdict"])
    print(f"Kontrollen ok: {res['controls_ok']} | "
          f"GUE25={res['controls']['gue_25']:.4f} "
          f"GOE25={res['controls']['goe_25']:.4f} "
          f"POIS25={res['controls']['poisson_25']:.4f} "
          f"GUE625={res['controls']['gue_625']:.4f} "
          f"GOE625={res['controls']['goe_625']:.4f} "
          f"POIS625={res['controls']['poisson_625']:.4f}")
    print(f"<r> d25 = {res['mean_r_d25']:.4f} -> {res['class_d25']} | "
          f"<r> d625 = {res['mean_r_d625']:.4f} -> {res['class_d625']} "
          f"(GUE {GUE_R}, Poisson {POISSON_R})")
    print(f"Shuffle-Null: d25={res['shuffle_null']['d25']:.4f} "
          f"d625={res['shuffle_null']['d625']:.4f} (deskriptiv)")
    print(f"prereg md5: {doc['md5']}")


if __name__ == "__main__":
    main()