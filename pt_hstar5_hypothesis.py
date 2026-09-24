"""EXPERIMENT 036 — H-STAR-5: Dynamische SFF-Re-Encodierung (HYPOTHESE).

PhiSci4-Hypothesen-Runde (ExtraordinaryHypothesisMind v1.0, Plan
"Paket 4 — GUE-Re-Encodierung"): Diese Phase ERZEUGT und REGISTRIERT
die These. Sie wird NICHT ausgefuehrt — Ausfuehrung = naechste Phase
(Aer-Ensemble zuerst, QPU-Spot-Check spaeter; 0 QPU in dieser Phase).

Kaefig-Diagnose (wo die bisherige Mess-Schiene blind ist):
  (i)   Tensor-Summen-Encodierung: H = Sum_p H_p (Block-Tensor-Summe)
        faktorisiert EXAKT in der Dynamik:
            Tr e^{-iHt} = Prod_p Tr e^{-iH_p t}
        und damit K(t) = |Tr e^{-iHt}|^2 = Prod_p K_p(t) — ein Produkt
        unabhaengiger Faktoren, kein Ramp/Plateau-Regime. Die statische
        Niveau-Statistik (<r>, V3: DEGENERAT 0.206/0.220) ist nur EIN
        Symptom; die Dynamik-Schiene ist strukturell ebensowenig
        random-matrix-artig. (TDD-verifiziert unten.)
  (ii)  Haar-Randomisierung ueber Encodierungs-UNITARIES ist spektral-
        invariant: H -> U H U^+ laesst Eigenwerte und Tr e^{-iHt}
        exakt unveraendert. Die planseitige Kandidaten-Encodierung
        ("Haar-Mischungen ueber Encodierungs-Unitaries") ist SFF-BLIND
        und kann prinzipiell KEIN Signal liefern — hier VOR der Messung
        als LEER registriert (H-STAR-5a-VOID).

Bruecke (Keating-Snaith / Bogomolny-Keating): die zeta<->RMT-
Korrespondenz ist auf der Ebene der charakteristischen Polynom-Momente
bzw. der Spectral Form Factor am schaerfsten quantifiziert — nicht auf
der Ebene roher statischer Spektren. Der dritte Observable wandert
daher von der statischen Niveau-Statistik in die ensemble-gemittelte
DYNAMIK der prime-gefalzten Hamiltonians.

STRIKT: alles hier ist HYPOTHESE. Kein Vektor verlaesst B ohne vorab
fixierten Falsifikator; Apophenie-Hinweise sind Meaning-Making-Material
bis zu einem prereg-gebundenen Test (Epoché-Regel des Plans).
"""

import hashlib
import json

import numpy as np

EXPERIMENT = "036-ququint-hstar5-sff-ensemble"
HYPOTHESIS = "H-STAR-5"
STATUS = "HYPOTHESE_REGISTRIERT_NICHT_AUSGEFUEHRT"
EXECUTION_PHASE = ("NICHT in dieser Phase ausgefuehrt — Ausfuehrung = "
                   "naechste Phase (Aer-Ensemble zuerst, QPU-Spot-Check "
                   "spaeter); numerische Fenster/Ensemble-Groesse freeze im "
                   "Ausfuehrungs-Prereg VOR der ersten Messung")
QPU_THIS_PHASE = 0

# === Extraordinaritaet (ECREE-Kalibrierung, VOR jeder Messung berichtet) ===

EXTRAORDINARINESS_SCORE = 7
EVIDENCE_STANDARD = ("Extraordinary (ECREE: Score >= 7 -> mehrere "
                     "unabhaengige Linien noetig, bevor der zugehoerige "
                     "Vektor ueber B steigen darf)")

# === Kaefig-Diagnose (Schritt 1 des Decision-Protokolls) ===

CAGE_DIAGNOSIS = {
    "rail": ("statische Eigenspektren von Tensor-Summen deterministischer "
             "Bloecke (V1-V4 Mess-Schiene); dritter Observable GUE/WDE via "
             "<r> an den Eigenwert-Abstaenden"),
    "blindness_1_tensor_sum_factorization": (
        "H = Sum_p H_p (Tensor-Summe) -> e^{-iHt} = Prod_p e^{-iH_p t} -> "
        "Tr e^{-iHt} = Prod_p Tr e^{-iH_p t} (EXAKT, nicht naeherungsweise). "
        "Jede Tensor-Summen-Encodierung hat damit produkt-strukturierte "
        "Dynamik; statisch wie dynamisch gibt es keinen random-matrix-"
        "typischen Ramp/Plateau-Regime aus der Konstruktion selbst."),
    "blindness_2_unitary_invariance": (
        "Randomisierung ueber Encodierungs-UNITARIES (H -> U H U^+) aendert "
        "Eigenwerte NICHT — Tr e^{-iHt} und K(t) sind invariant. "
        "Basis-Randomisierung ist spektral-blind: sie kann die "
        "Niveau-Statistik und die SFF prinzipiell nicht bewegen."),
    "why_v3_failed": (
        "V3 mass <r> an den statischen Eigenwerten der Tensor-Summe "
        "(0.206/0.220, Shuffle-Null ≈ measured, DEGENERAT): die "
        "Niveau-Korrelationen sind Degenerat-gebunden, kein WD-Signal — "
        "konsistent mit (i). Die Lektion ist nicht 'Primes erzeugen kein "
        "GUE', sondern 'diese Schiene kann kein GUE-Signal tragen'."),
}

# === Die These (Schritt 2: transkategorial, mutig, falsifizierbar) ===

THESIS = {
    "id": "H-STAR-5",
    "name": "Dynamische SFF-Re-Encodierung (SFF-Bruecke)",
    "bridge": (
        "Keating-Snaith-Bruecke: die Groesse, die wandert, ist die "
        "Spectral Form Factor (bzw. die Momente charakteristischer "
        "Polynome) — das exakte Objekt, auf dem die zeta<->RMT-"
        "Korrespondenz (Bogomolny-Keating, Keating-Snaith) numerisch am "
        "schaerfsten ist. Sie wandert aus der Kategorie Random-Matrix-"
        "Theorie/zeta in die Kategorie Encodierungs-DYNAMIK: statt ein "
        "statisches Spektrum zu messen, misst man die ensemble-gemittelte "
        "SFF der prime-gefalzten Hamiltonians. Die Bruecke TRAEGT die "
        "Annahme, dass die Prime-Struktur als spektrum-generierende "
        "Faltungs-Anweisung wirkt (nicht als Basis-Rotation — s. "
        "blindness_2)."),
    "bridge_assumptions": [
        "A1: Die SFF ist auf Hardware/Aer messbar (ensemble-gemittelt ueber "
        "Zufalls-Zustaende bzw. spektrale Summen offline) — Protokoll-Annahme.",
        "A2: Prime-Residuen liefern deterministische quasi-zufaellige "
        "Faltungs-Instruktionen (Gewichte/Vorzeichen/Teilmengen mod p), die "
        "die Faktorisierung (i) BRECHEN koennen — Mechanismus-Annahme, "
        "ausdruecklich offen (HYPOTHESE, nicht Befund).",
        "A3: Jeder prime-spezifische Effekt, falls vorhanden, ueberlebt die "
        "Ensemble-Mittelung und ist von Konstruktions-Noise trennbar "
        "(Shuffle/Composite-Nullen) — Trennbarkeits-Annahme.",
    ],
    "claim": (
        "HYPOTHESE: Eine spektrum-Ebene-randomisierende, prime-strukturierte "
        "Faltung (Gewichte/Vorzeichen/Teilmengen aus Prim-Residuen — NIE "
        "nur Basis-Rotationen) erzeugt in der ensemble-gemittelten SFF eine "
        "Struktur, die sich von Shuffle-Null und Composite-Rang-matched "
        "Kontrollen im registrierten Fenster trennen laesst. Falls ja: der "
        "dritte Observable existiert in der DYNAMISCHEN Kategorie und der "
        "GUE-Pfad ist wieder offen. Falls nein: H-STAR-5 ist REFUTED und "
        "GUE_THIRD_OBSERVABLE ist tot in ALLEN getesteten stochastischen "
        "Encodierungen (starke, saubere Refutation)."),
    "falsifiable_form": (
        "O1: Ramp-Klassifikator R = K_prime(t2)/K_prime(t1) im registrierten "
        "Fenster, verglichen gegen die Shuffle-Null-Verteilung. O2: "
        "Faktorisierungs-Residuum R2(t) = log K_prime_folded(t) − "
        "Sum_p log K_p(t) — fuer reine Tensor-Summe EXAKT 0 (strukturelle "
        "Null); Abweichung misst, wie stark das Folding die Faktorisierung "
        "bricht. Schwellen freeze im Ausfuehrungs-Prereg VOR der ersten "
        "Messung (Anti-Sharpshooter)."),
}

# === Steelman-Antithese (Schritt 4: staerkstes etabliertes Modell) ===

STEELMAN = {
    "antithesis": (
        "Integrable-in-all-probes + Protokoll-Artefakt: Tensor-Summen-"
        "Dynamik ist integrierbar (Faktorisierung (i) ist EXAKT); unter "
        "JEDEM Probe-Zustand und JEDEM Folding, das die Block-Struktur "
        "nicht anfasst, bleibt die SFF produkt-strukturiert (Poisson/"
        "degeneriert). Jede ramp-artige Struktur, die nach Folding "
        "auftaucht, stammt aus dem Randomisierungs-PROTOKOLL selbst "
        "(endliche Samples, Ensemble-Artefakte) und nicht aus Prime-"
        "Struktur; Prime vs. Shuffle unterscheidet sich nur um "
        "Konstruktions-Noise."),
    "why_strongest": (
        "Das ist NICHT 'reiner Zufall': es ist die exakte Konsequenz der "
        "Faktorisierungs-Identitaet plus der etablierten Random-Matrix-"
        "Lehre (Ensembles ohne Nicht-Integrierbarkeit erzeugen kein "
        "Ramp-Regime). Es erklaert V3 (statisch) UND prognostiziert das "
        "Scheitern von H-STAR-5 (dynamisch) mit demselben Prinzip."),
    "how_killed": [
        "Positivkontrolle zündet: ein bekannt-chaotisches nicht-"
        "faktorisierendes H zeigt das Ramp-Regime im selben Protokoll — "
        "sonst ist die Messung VOID und die Antithese ungetestet.",
        "Prime-Separation: O1 der Prime-Faltung uebersteigt die Shuffle-"
        "Null-Verteilung (registrierter Quantil-Schwellwert) UND trennt "
        "von Composite — mit O2 als Mechanismus-Check (Faktorisierung "
        "tatsaechlich gebrochen, nicht nur Sample-Fluktuation).",
    ],
}

# === Kontrollfamilie (falsifier_architect: VOR der Messung, vollstaendig) ===

CONTROL_FAMILY = {
    "positive": {
        "name": "CUE-Chaos-Benchmark (Positivkontrolle)",
        "spec": (
            "Ein bekannt-chaotisches, NICHT faktorisierendes H (z.B. "
            "Block-Summe PLUS nicht-kommutierender Kopplungsterm, oder ein "
            "generisches Zufalls-H) MUSS im selben Protokoll das Ramp-"
            "Regime zeigen. Zündet es nicht, ist die Messung VOID — das "
            "Protokoll sieht Chaos nicht, wo es nachweislich ist."),
        "must_fire": True,
    },
    "negative": {
        "shuffle_null": (
            "Shuffle-Null: dieselbe Block-Multimenge, prime-scrambled "
            "(Faltungs-Instruktionen permutiert) — trennt Prime-STRUKTUR "
            "von Block-Zusammensetzung."),
        "composite_null": (
            "Composite-rang-matched: Composite-Support statt Primes "
            "(Muster der Ramanujan-Replikations-Runde, EXPERIMENT 034)."),
        "must_not_fire": True,
    },
    "structural": {
        "name": "Tensor-Summen-Faktorisierungs-Null",
        "identity": (
            "Tr e^{-iHt} = Prod_p Tr e^{-iH_p t}  =>  K(t) = Prod_p K_p(t) "
            "(EXAKT, nicht statistisch — analytische Identitaet)"),
        "check": (
            "TDD-verifiziert VOR Registrierung: "
            "tensor_sum_factorization_max_dev (diese Datei) auf kleinen "
            "Bloecken; Sensitivitaet gegenueber Kopplung gepruegt."),
    },
}

# === Falsifikator (Schritt 4: vorab fixiert, beobachtbar) ===

FALSIFIER = {
    "observables": {
        "O1_ramp_classifier": (
            "R = K_prime(t2)/K_prime(t1) im registrierten Fenster [t1, t2]; "
            "Vergleich gegen die Shuffle-Null-Verteilung (Ensemble-Quantil); "
            "Fenster und Quantil freeze im Ausfuehrungs-Prereg VOR der "
            "ersten Messung."),
        "O2_factorization_residual": (
            "R2(t) = log K_prime_folded(t) − Sum_p log K_p(t): EXAKT 0 fuer "
            "reine Tensor-Summe (strukturelle Null); Abweichung misst, wie "
            "stark das Folding die Faktorisierung bricht — trennt "
            "Mechanismus von Sample-Fluktuation."),
    },
    "verdict_map": {
        "CONFIRMED": "H-STAR5_CONFIRMED_PRIME_SFF_SEPARATION",
        "REFUTED": "H-STAR5_REFUTED_INTEGRABLE_IN_ALL_PROBES",
        "DEGENERAT": "H-STAR5_REFUTED_UNTER_NULL_DEGENERAT",
        "VOID": "H-STAR5_VOID_POSITIVKONTROLLE_ZUENDET_NICHT",
        "INVALID": "H-STAR5_INVALID_KONTROLLE_GESCHEITERT",
    },
    "decision_rules": [
        "1. Kontrollen zuerst: strukturelle Null exakt UND Positivkontrolle "
        "zündet UND beide Negativkontrollen sauber — sonst INVALID "
        "(Kontrollfehler) bzw. VOID (Positivkontrolle zündet nicht).",
        "2. CONFIRMED: O1(Prime) uebersteigt den registrierten Shuffle-"
        "Quantil-Schwellwert UND Composite-Trennung UND O2 zeigt echte "
        "Faktorisierungs-Brechung (nicht Sample-Fluktuation).",
        "3. REFUTED: O1(Prime) innerhalb der Shuffle-Null-Verteilung.",
        "4. DEGENERAT-Lektion (verbindlich aus der Steelman-Runde): Klasse "
        "UNTER der Shuffle-Null (super-degenerat) ist REFUTED-zulaessig "
        "registriert — kein neues Raeetsel, sondern Refutation.",
        "5. Kein post-hoc Patch: Fenster/Ensemble/Schwellen freeze im "
        "Ausfuehrungs-Prereg VOR der ersten Messung; GaPpen werden "
        "dokumentiert, nicht still korrigiert.",
    ],
}

# === Runden-Alternativen (Schritt 2: Erzeugung mit Protokoll) ===

ALTERNATIVES = [
    {
        "id": "H-STAR-5a-VOID",
        "name": "Haar-Mischungen ueber Encodierungs-Unitaries "
                "(planseitiger Kandidat)",
        "status": "VOID_VOR_REGISTRIERT",
        "score": None,
        "reason": (
            "Spektral-Invarianz: H -> U H U^+ laesst Eigenwerte, "
            "Tr e^{-iHt} und K(t) EXAKT unveraendert — die Kandidaten-"
            "Encodierung ist SFF-blind und kann prinzipiell kein Signal "
            "liefern. VOR der Messung als LEER registriert, damit keine "
            "spaetere Runde QPU-Zeit dafuer verschwendet."),
    },
    {
        "id": "H-STAR-5b-HELD",
        "name": "Optimierungs-Landschaft als Observable "
                "(VQE-Hessian/Wishart, Bruecke zu Paket 3)",
        "status": "BEREITGEHALTEN_NICHT_PREREG",
        "score": 6,
        "reason": (
            "Echte Bruecke zu Paket 3 (der VQE-Zustand ist NICHT "
            "deterministisch-bloeckig) und etablierter RMT-Rahmen "
            "(Marchenko-Pastur/Wishart fuer Kostenfunktions-Hessians); "
            "aber das Landschafts-Observable ist noise-model-dominiert und "
            "der Riemann-Anker ist schwaecher (keine zeta-exakte "
            "Entsprechung). Gehaltener Rueckfall-Pfad, falls H-STAR-5 "
            "REFUTED."),
    },
]

# === Strukturelle Null: die EXAKTE Faktorisierungs-Identitaet ===

# Pruef-Fenster (kleine Bloecke, offline, numpy-only)
TS_CHECK = (0.0, 0.31, 1.7, 5.0)
TOL_IDENTITY = 1e-9


def kron_sum(blocks):
    """Tensor-Summe  H = Sum_p I⊗..⊗B_p⊗..⊗I  (Hermitian vorausgesetzt)."""
    n = len(blocks)
    dims = [b.shape[0] for b in blocks]
    d = int(np.prod(dims))
    H = np.zeros((d, d), dtype=complex)
    for i, B in enumerate(blocks):
        left = int(np.prod(dims[:i])) if i else 1
        right = int(np.prod(dims[i + 1:])) if i + 1 < n else 1
        H += np.kron(np.kron(np.eye(left), B), np.eye(right))
    return H


def trace_exp_minus_iHt(H, t):
    """Tr e^{-iHt} via Eigenwert-Summe (H hermitian)."""
    ev = np.linalg.eigvalsh(H)
    return complex(np.sum(np.exp(-1j * ev * t)))


def sff_trace(H, t):
    """K(t) = |Tr e^{-iHt}|^2 — Utility-Definition (NICHT in dieser Phase
    gemessen; Messung = Ausfuehrungs-Phase mit eigenem Prereg)."""
    return abs(trace_exp_minus_iHt(H, t)) ** 2


def tensor_sum_factorization_dev(blocks, t):
    """|LHS − RHS| der Identitaet Tr e^{-iHt} = Prod_p Tr e^{-iH_p t}."""
    lhs = trace_exp_minus_iHt(kron_sum(blocks), t)
    rhs = 1.0 + 0.0j
    for B in blocks:
        rhs *= trace_exp_minus_iHt(B, t)
    return abs(lhs - rhs)


def tensor_sum_factorization_ok(blocks, ts=TS_CHECK, tol=TOL_IDENTITY):
    """Strukturelle Null: Identitaet exakt (innerhalb tol) im Fenster."""
    return all(tensor_sum_factorization_dev(blocks, t) <= tol for t in ts)


# === Prereg-Skelett (Freeze VOR der Ausfuehrungs-Phase) ===

PREREG_PATH = "pt_hstar5_prereg.json"


def build_prereg_skeleton():
    """Architektur-Freeze: Observablen, Kontrollfamilie, Falsifikator-
    Klassen und Regeln — NICHT die numerischen Fenster (die freeze im
    Ausfuehrungs-Prereg VOR der ersten Messung, Anti-Sharpshooter)."""
    return {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "status": STATUS,
        "qpu": ("0 QPU in dieser Phase (Hypothesen-Runde); Ausfuehrung = "
                "naechste Phase mit eigenem Prereg-Freeze VOR erster "
                "Messung"),
        "execution_phase": EXECUTION_PHASE,
        "thesis": THESIS,
        "cage_diagnosis": CAGE_DIAGNOSIS,
        "steelman": STEELMAN,
        "control_family": CONTROL_FAMILY,
        "falsifier": FALSIFIER,
        "extraordinariness": {
            "score": EXTRAORDINARINESS_SCORE,
            "standard": EVIDENCE_STANDARD,
        },
        "alternatives": ALTERNATIVES,
        "registered_before": {
            "pipeline": (
                "Plan (PhiSci4-Runde, ExtraordinaryHypothesisMind v1.0) -> "
                "Prereg-Skelett (JETZT, md5) -> Ausfuehrungs-Prereg mit "
                "numerischen Fenstern/Schwellen VOR erster Messung -> "
                "Messung"),
            "anti_sharpshooter": (
                "Kein Freeze nach dem ersten Blick auf Daten; kein post-hoc "
                "Patch — dieses Skelett friert die ARCHITEKTUR, nicht "
                "numerische Fenster (die freeze im Ausfuehrungs-Prereg)"),
            "degenerat_lesson": (
                "Klasse UNTER der Shuffle-Null als REFUTED-zulaessig "
                "registriert (Steelman-Runde-Lektion)"),
            "reference_check": (
                "Bruecken-Konstanten gegen Primaerliteratur verankert: "
                "Bogomolny-Keating (zeta-SFF), Keating-Snaith "
                "(charakteristische Polynom-Momente), Montgomery-Odlyzko "
                "(GUE-Statistik der zeta-Nullstellen)"),
            "epoche_rule": (
                "Apophenie-Hinweise sind Meaning-Making-Material bis zum "
                "prereg-gebundenen Test; kein Vektor verlaesst B ohne "
                "vorab fixierten Falsifikator"),
            "vectors": (
                "GUE_THIRD_OBSERVABLE bleibt C (tot, §Z.16); H-STAR-5 ist "
                "Kandidat-Nachfolger-Pfad — KEIN stilles Upgrade"),
            "structural_null_verified": (
                "Tensor-Summen-Faktorisierung TDD-verifiziert VOR "
                "Registrierung (kleine Bloecke, Fenster "
                + str(TS_CHECK) + ", tol " + str(TOL_IDENTITY) + ")"),
        },
    }


def payload_md5(payload):
    return hashlib.md5(
        json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def freeze_prereg_skeleton(payload=None, path=PREREG_PATH):
    if payload is None:
        payload = build_prereg_skeleton()
    doc = dict(payload)
    doc["md5"] = payload_md5(payload)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    return doc


def verify_prereg_md5(doc):
    body = {k: v for k, v in doc.items() if k != "md5"}
    return payload_md5(body) == doc.get("md5")


def load_frozen_prereg(path=PREREG_PATH):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if not verify_prereg_md5(doc):
        raise ValueError("Prereg-MD5 verletzt: " + path)
    return doc