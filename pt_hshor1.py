"""EXPERIMENT 038 — H-SHOR-1: Fermat-Grid-Orakel-Bru-cke (HYPOTHESE + Prereg-Freeze + Auswertung, 0 QPU).

Branch: shor-ququint-oracle. Hypothesen-Layer des Plans
(~/.claude/plans/parallel-zooming-nova.md, Denkmodus:
QuantumHypothesisEngineerMind v1.0_20260924_qhe-mix).

Fit-Verdict zu H-STAR-5 (md5 f915729e, registriert und UNANGETASTET):
H-STAR-5 ist an die prime-gefalzten Hamiltonian-Ensembles gebunden —
die Shor-Unitaries sind ein anderes Objekt. UEBERNOMMEN wird die
ARCHITEKTUR (Kontrollfamilie, O1/O2-Muster, Verdict-Map, Prereg-Freeze,
Steelman-Discipline), NICHT die These. Neuer eigenstaendiger Name:
H-SHOR-1. Kein stilles Upgrade (synthesis_auditor).

These (Bru-cke): Die Groesse, die wandert, ist das ORDNUNGSRASTER
{r : a^r = 1 mod N} der Shor-Permutation U_{a,N} — aus der Kategorie
Ordnungsarithmetik in die Kategorie Register-Spektroskopie: als
Interferenzraster der QPE-Readout-Verteilung (Peaks bei k = s*Q/r) und
als Trace-Kamm Tr U^t = sum_L L*[L | t].

Registrierte Blindheit (CAGE, aus der Implementierung gelernt UND gegen
Primaerliteratur verankert): Das Fermat-Grid (ord_a(N) | N-1) ist blind
auf EXAKT der Korselt-Klasse: Korselt ⟺ N quadratfrei und p-1 | N-1
fuer alle p | N ⟺ lambda(N) | N-1 ⟺ ALLE Orders teilen N-1. 561 = 3*11*17
(lambda = 80 teilt 560) feuert als Blindheits-Kontrolle MUST-FIRE
(Rate 0 wie Primes). Schaerferes Kriterium: max_order(N) = N-1 ⟺ prim
(zyklische Gruppe / primitive Wurzel) — trennt auch die Korselt-Klasse.

DISZIPLIN: Freeze VOR Auswertung (md5). run_evaluation() laedt das
GEFRORENE Prereg (md5-Verifikation, wirft bei Verletzung) und wertet
ausschliesslich mit den gefrorenen Fenstern/Schwellen aus.
"""

import json
import hashlib
from math import gcd

import numpy as np

import pt_shor_ququint as sq

EXPERIMENT = "EXPERIMENT_038_HSHOR1_FERMAT_GRID_BRIDGE"
HYPOTHESIS = "H-SHOR-1"
NAME = "Fermat-Grid-Orakel-Bru-cke (Shor-Oracle auf Ququint/GF(5))"
QPU_THIS_PHASE = 0
STATUS = "HYPOTHESE_PREREG_GEFROREN_VOR_AUSWERTUNG"

# ECREE: klassische Trennung ist Theorem-Niveau (Fermat/Korselt);
# getestet wird NUR die Oracle-Readout-Realisierung + strukturelle Null.
EXTRAORDINARINESS_SCORE = 5
EVIDENCE_STANDARD = (
    "Standard (Score 5/10, ECREE-Verhaeltnis: die algebraische Trennung "
    "prim/composite ist Theorem-Niveau — Fermat, Korselt; getestet wird "
    "die BRUECKE: liest der QPE-Readout das Ordnungsraster exakt genug, "
    "und haelt die strukturelle CRT-Null)")

PREREG_PATH = "pt_hshor1_prereg.json"

# === These ===

THESIS = {
    "id": "H-SHOR-1",
    "name": NAME,
    "bridge": (
        "Die Groesse, die wandert: das Ordnungsraster {r : a^r = 1 mod N} "
        "der Shor-Permutation U_{a,N} — in der Kategorie "
        "Ordnungsarithmetik definiert — erscheint im Ququint-Register "
        "als Interferenzraster der QPE-Readout-Verteilung (Peaks bei "
        "k = s*Q/r, Tr U^t = sum_L L*[L|t] als Trace-Kamm) und damit in "
        "der Kategorie Register-Spektroskopie. Die Bruecke ist dieselbe "
        "Bewegung wie in H-STAR-5 (Tensor-Summen-Identitaet), hier auf "
        "PERMUTATIONS-UNITARIES statt auf gefalzten Hamiltonians."),
    "bridge_assumptions": [
        "Register-Axiome: 5^n_x >= N (x-Register) und 5^n_count >= N^2 "
        "(Zaehlregister); die Modulus-Aktion gilt nur auf dem encodierten "
        "Traeger {0..N-1}",
        "Idle-Subraum-Axiom: x >= N bleibt unberuehrt "
        "(Permutationseinbettung U_{a,N} in das 5^n_x-Register)",
        "Rekonstruktions-Axiom: Kettenbruch-Rekonstruktion liest r aus "
        "den endlichen QPE-Peaks exakt genug (Peak-Nenner teilen r; LCM "
        "+ Verifikation a^r = 1 mod N + exakte Reduktion)",
    ],
    "claim": (
        "Der QPE-Readout auf dem Ququint-Register reproduziert das "
        "Ordnungsraster exakt (Bridge-Match 1.0 im gefrorenen Fenster); "
        "die Grid-Statistik trennt prim/composite theorem-niveau (Prime: "
        "Rate 0, nicht-Korselt-Composite: Rate > Schwelle); der volle "
        "Shor-Weg faktorisiert die Composites im Fenster und liefert "
        "NIE einen nichttrivialen Faktor fuer Primes; die CRT-"
        "Faktorisierung ist die exakte strukturelle Null."),
    "falsifiable_form": (
        "O1: Grid-Verletzungsrate (ord_a(N) | N-1?) — Prime exakt 0 "
        "(Theorem-Fehler -> INVALID), nicht-Korselt-Composite > 0.05, "
        "561 (Korselt) = 0 als Blindheits-Kontrolle. O1': QPE-Readout — "
        "Bridge-Match (qpe_order.r == order_mod) = 1.0 im Fenster und "
        "shor_factor: Composites faktorisiert, Primes None. O2: CRT- "
        "und Trace-Identitaet <= 1e-9. Shuffle-Null: Label-Permutation, "
        "p <= 0.05. Verletzung von O1'/O2/Shuffle -> REFUTED auch bei "
        "klassisch korrekter Algebra (Steelman-Runde-Lektion)."),
}

# === Cage-Diagnose (blinde Stelle der Mess-Schiene) ===

CAGE_DIAGNOSIS = {
    "structural_identity": (
        "CRT-Faktorisierung C U_{a,pq} C^T = U_{a,p} (x) U_{a,q} und "
        "Trace-Produkt-Identitaet Tr U_{a,pq}^t = Tr U_{a,p}^t * "
        "Tr U_{a,q}^t — EXAKT (dev 0.0, TDD-verifiziert VOR "
        "Registrierung, Fenster " + str(sq.TS_CHECK) + ", tol 1e-9). "
        "Formaler Zwillingsbruder der H-STAR-5 Tensor-Summen-Identitaet."),
    "blindness_1_fermat_grid_korselt": (
        "Das O1-Fermat-Grid (ord_a(N) | N-1) ist blind auf EXAKT der "
        "Korselt-Klasse: Korselt ⟺ N quadratfrei ∧ p-1 | N-1 fuer alle "
        "p | N ⟺ lambda(N) | N-1 ⟺ alle Orders teilen N-1. 561 = 3*11*17: "
        "lambda = 80 teilt 560 -> Rate 0 wie bei Primes. Die Blindheit "
        "ist THEOREM-genau abgegrenzt und feuert als must-fire-Blindheits-"
        "Kontrolle: schlaegt sie an (Rate != 0), ist die Diagnose falsch "
        "-> INVALID."),
    "blindness_2_unitary_invariance": (
        "Basis-/Unitaer-Rotationen des Registers sind spektral blind "
        "(H-STAR-5a-Lektion, geerbt): jeder Kandidat, der nur auf einer "
        "rotierten Darstellung basiert, bleibt VOID (H-SHOR-1a)."),
    "sharper_discriminator": (
        "max_order(N) = N-1 ⟺ prim (zyklische Einheitengruppe, "
        "primitive Wurzel existiert) — trennt auch die Korselt-Klasse "
        "(561: max_order = 80 != 560) und ist das registrierte "
        "Ersatz-Kriterium, wo O1 blind ist."),
}

# === Steelman (staerkstes etabliertes Alternativmodell, NICHT Zufall) ===

STEELMAN = {
    "classical_primality": (
        "Klassische Primalitaets-Tests (Miller-Rabin, Trial Division) "
        "entscheiden prim/composite billiger und deterministischer — der "
        "Claim ist NICHT Rechen-Vorteil, sondern die strukturelle "
        "Aequivalenz Oracle-Readout ↔ Ordnungsraster auf der "
        "Ququint-Architektur."),
    "korselt_carmichael": (
        "Die Korselt-Klasse (Karmichael-Zahlen, 561 registriert) ist die "
        "theorem-bekannte blinde Klasse von Fermat-Gittern — der "
        "staerkste etablierte Einwand gegen O1. Er wird als must-fire-"
        "Blindheits-Kontrolle REGISTRIERT, nicht wegdefiniert."),
    "not_the_claim": (
        "Kein Claim ueber kryptografische Praxisrelevanz (N <= 561, "
        "Statevector); kein Claim ueber Shor-Skalierung auf echte "
        "RSA-Groessen; kein Claim ueber QPU-Vorteil (0 QPU)."),
}

# === Kontrollfamilie (voll: positiv/negativ/strukturell/blindheit) ===

CONTROL_FAMILY = {
    "positive_must_fire": (
        "Primes im Fenster: Grid-Rate EXAKT 0 (Fermat, Theorem) und "
        "shor_factor -> None (a^{r/2} = +-1 im Koerper). Zündet nicht "
        "-> INVALID (Setup falsch) bzw. VOID (strukturell gebrochen)."),
    "negative_must_not_fire": (
        "Shuffle-Null: Label-Permutation prime/composite ueber das "
        "klassische Fenster (Gruppengroessen fix, 200 Permutationen, "
        "seed 0) — die beobachtete Trennung muss oberhalb des "
        "0.95-Quantils liegen (p <= 0.05)."),
    "structural_exact": (
        "CRT-Faktorisierung + Trace-Produkt-Identitaet fuer (3,5), "
        "(3,7), (5,7): dev <= 1e-9 im Fenster TS_CHECK = "
        + str(sq.TS_CHECK) + ". Verletzt -> VOID."),
    "blindness_control": (
        "561 (Korselt): Grid-Rate 0 UND max_order 80 != 560. Feuert "
        "nicht -> die registrierte CAGE-Diagnose ist falsch -> INVALID."),
}

# === Falsifikator mit GEFRORENEN Fenstern/Schwellen (Anti-Sharpshooter) ===

QPE_WINDOW = {
    "n_count": 4, "n_x": 2, "Q": 625, "XD": 25,
    "primes": [7, 11, 13, 17, 19, 23],
    "composites": [15, 21],
    "a_samples": "alle Coprime a in [2, N-1]",
    "max_attempts": 5,
    "readout": "exakte Statevector-Wahrscheinlichkeiten (Phase A, kein Sampling-Noise)",
}

CLASSICAL_WINDOW = {
    "primes": [7, 11, 13, 17, 19, 23],
    "composites": [9, 15, 21, 25, 33, 35, 39, 561],
    "korselt_excluded": [561],      # registrierte blinde Klasse (Theorem)
    "method": "Order-Enumeration via Zyklen (keine Matrizen)",
}

THRESHOLDS = {
    "composite_min_rate": 0.05,     # pro nicht-Korselt-Composite (klassisch)
    "prime_max_rate": 0.0,          # exakt (Theorem)
    "tol_identity": 1e-9,           # O2 (CRT + Trace)
    "crt_pairs": [[3, 5], [3, 7], [5, 7]],
    "shuffle_max_p": 0.05,
    "n_shuffle": 200,
    "shuffle_seed": 0,
    "bridge_match_min": 1.0,        # QPE-Readout == exakte Ordnung, jedes a
}

FALSIFIER = {
    "windows": {"qpe": QPE_WINDOW, "classical": CLASSICAL_WINDOW},
    "thresholds": THRESHOLDS,
    "observables": {
        "O1_grid_rate": (
            "Grid-Verletzungsrate: Anteil der Coprime-a mit "
            "ord_a(N) NICHT teiler von N-1 (klassisch exakt aus Orders). "
            "Prime: 0 (Theorem); nicht-Korselt-Composite: > 0.05; "
            "561 (Korselt): 0 als registrierte Blindheit."),
        "O1p_oracle_output": (
            "Voller Shor-Weg (shor_factor) im QPE-Fenster: Composites "
            "faktorisiert (nichttrivialer Faktor in <= 5 Attempts), "
            "Primes None. DAS ist die Oracle-Ebene des Bruecken-Claims."),
        "O1b_bridge_match": (
            "QPE-Readout-Ordnung qpe_order(a,N).r == order_mod(a,N) fuer "
            "JEDES Coprime-a im QPE-Fenster (Bridge-Match = 1.0): die "
            "KERN-Aussage der Bruecke (Readout = Ordnungsraster)."),
        "O2_crt_residual": (
            "CRT-Faktorisierungs-Deviation + Trace-Produkt-Identitaet "
            "fuer N = pq: strukturelle Null, exakt 0 — misst, dass die "
            "Faktorisierungs-Struktur Identitaet ist, nicht Fluktuation."),
    },
    "verdict_map": {
        "CONFIRMED": "HSHOR1_CONFIRMED_GRID_BRIDGE_REALISIERT",
        "REFUTED": "HSHOR1_REFUTED_READOUT_TRAEGT_RASTER_NICHT",
        "DEGENERAT": "HSHOR1_DEGENERAT_KEINE_TRENNUNG_IM_FENSTER",
        "VOID": "HSHOR1_VOID_STRUKTURELL_IDENTITAET_GEBROCHEN",
        "INVALID": "HSHOR1_INVALID_KONTROLLE_GESCHEITERT",
    },
    "decision_rules": [
        "1. Kontrollen zuerst: strukturelle Null (O2) exakt UND "
        "Positivkontrolle (Prime-Rate 0, Theorem) UND Blindheits-Kontrolle "
        "(561: Rate 0, max_order 80) — sonst VOID/INVALID.",
        "2. CONFIRMED: O1-Trennung im klassischen Fenster (nicht-Korselt-"
        "Composite > 0.05, Prime = 0) UND O1' (Oracle-Output) im QPE-"
        "Fenster UND O1b Bridge-Match = 1.0 UND Shuffle p <= 0.05.",
        "3. REFUTED: der QPE-Readout traegt das Raster nicht (Bridge-"
        "Match < 1.0, Prime faktorisiert, oder Composite nicht faktorisiert) "
        "— REFUTED-zulaessig auch bei klassisch korrekter Algebra "
        "(Steelman-Runde-Lektion: unter der Null ist REFUTED zulaessig).",
        "4. DEGENERAT: keine Trennung im klassischen Fenster (Composite-"
        "Rate unter Schwelle) — Bruecke ohne Inhalt.",
        "5. Kein post-hoc Patch: Fenster/Schwellen sind in DIESEM Prereg "
        "gefroren (md5), VOR der ersten Auswertung; Luecken werden "
        "dokumentiert, nicht still korrigiert.",
    ],
}

# === Runden-Alternativen ===

ALTERNATIVES = {
    "H-SHOR-1a-UNITARY_INVARIANCE": {
        "status": "VOID", "score": None,
        "note": "Basis-/Unitaer-Rotationen sind SFF-blind "
                "(H-STAR-5a-Lektion) — vorab als VOID registriert.",
    },
    "H-SHOR-1b-SCALING": {
        "status": "HELD", "score": 4,
        "note": "Ausweitung: Q = 3125 (5 Count-Ququints), groessere N "
                "und mehr Karmichael-Fenster — held, eigenes Prereg bei "
                "Ausfuehrung.",
    },
}

VECTORS = {
    "SHOR_QUQUINT_ORACLE": {"grade": "PENDING_VERDICT",
                            "note": "Vektor nach Auswertung gem. Verdict"},
    "H_STAR_5": {"grade": "unveraendert (registriert, md5 f915729e)",
                 "note": "KEIN stilles Upgrade — Ausfuehrung bleibt "
                         "eigene Phase (PLAN.md Phase 6)"},
}


# === Prereg (Freeze VOR Auswertung) ===

PREREG_PATH = "pt_hshor1_prereg.json"


def build_prereg_skeleton():
    """Voll-Freeze: Architektur UND numerische Fenster/Schwellen —
    VOR der ersten Auswertung (Anti-Sharpshooter)."""
    return {
        "experiment": EXPERIMENT,
        "hypothesis": HYPOTHESIS,
        "name": NAME,
        "status": STATUS,
        "qpu": ("0 QPU in dieser Phase (klassische Enumeration + "
                "Statevector-QPE); QPU-Spot-Check nur spaeter bei "
                "sichtbarer Trennung"),
        "thesis": THESIS,
        "cage_diagnosis": CAGE_DIAGNOSIS,
        "steelman": STEELMAN,
        "control_family": CONTROL_FAMILY,
        "falsifier": FALSIFIER,
        "alternatives": ALTERNATIVES,
        "extraordinariness": {
            "score": EXTRAORDINARINESS_SCORE,
            "standard": EVIDENCE_STANDARD,
        },
        "registered_before": {
            "pipeline": (
                "Plan (QuantumHypothesisEngineerMind v1.0_20260924_qhe-"
                "mix, Pfad B) -> Engineering-Layer EXPERIMENT 037 TDD "
                "(611 Tests gruen) -> DIESER Freeze (md5) -> Auswertung "
                "mit gefrorenen Schwellen"),
            "anti_sharpshooter": (
                "Fenster UND Schwellen freeze VOR der ersten Auswertung; "
                "run_evaluation laedt das GEFRORENE Prereg mit "
                "md5-Verifikation und bricht bei Verletzung ab"),
            "reference_check": (
                "Bruecken-Konstanten gegen Primaerliteratur: Fermat "
                "(kleiner Satz), Korselt-Kriterium (1899: N Karmichael "
                "⟺ quadratfrei ∧ p-1 | N-1 fuer alle p | N ⟺ lambda | "
                "N-1), Shor (Ordnungsfindung + Kettenbrueche), CRT "
                "(Ring-Isomorphie)"),
            "korselt_correction": (
                "KORREKTUR ggue. Plan-Entwurf: 561 ist KEIN Gegenbeispiel "
                "fuer die Grid-Schaerfe (lambda = 80 TEILT 560) — die "
                "Grid-Blindheit ist genau die Korselt-Klasse (Theorem). "
                "Registriert als Blindheit + Schaerferes Kriterium "
                "max_order; geaendert VOR dem Freeze, nicht nach Daten."),
            "degenerat_lesson": (
                "Klasse UNTER der Null als REFUTED-zulaessig registriert "
                "(Steelman-Runde-Lektion, verbindlich)"),
            "structural_null_verified": (
                "CRT-Identitaeten TDD-verifiziert VOR Registrierung "
                "(EXPERIMENT 037: dev 0.000000 fuer (3,5), (3,7), (5,7); "
                "Fenster " + str(sq.TS_CHECK) + ", tol 1e-9)"),
            "vectors": (
                "H-STAR-5 bleibt unverändert registriert (md5 f915729e); "
                "H-SHOR-1 ist eigenstaendiger Kandidat-Pfad mit eigenem "
                "Namen (User-Vorgabe: 'nenne es anders')"),
        },
    }


def payload_md5(payload):
    return hashlib.md5(
        json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def freeze_prereg(payload=None, path=PREREG_PATH):
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


# === Auswertung (NUR mit gefrorenem Prereg) ===

def korselt_criterion_check(N):
    """Registrierte Referenz (Korselt 1899) als Code: True ⟺ N quadratfrei
    ∧ p-1 | N-1 fuer alle Primteiler p | N ⟺ lambda(N) | N-1. Dient im
    Test als unabhaengige Verifikation der gefrorenen Ausschlussliste."""
    # Faktorisierung per Trial Division (N <= 561 im Fenster)
    primes = []
    m = N
    d = 2
    while d * d <= m:
        if m % d == 0:
            if N % (d * d) == 0:      # nicht quadratfrei
                return False
            primes.append(d)
            while m % d == 0:
                m //= d
        d += 1
    if m > 1:
        primes.append(m)
    return all((N - 1) % (p - 1) == 0 for p in primes)


def qpe_order_grid_match(N, n_count=4, n_x=2):
    """O1b: Bridge-Match — QPE-Readout-Ordnung vs. exakte Ordnung fuer
    ALLE Coprime-a. Gibt aggregate + mismatch list zurueck."""
    matches, mismatches = 0, []
    total = 0
    for a in sq.coprime_units(N):
        res = sq.qpe_order(a, N, n_count, n_x)
        r_q = res["r"]
        r_c = sq.order_mod(a, N)
        total += 1
        if r_q == r_c:
            matches += 1
        else:
            mismatches.append({"a": a, "r_classical": r_c, "r_qpe": r_q})
    return {"N": N, "total": total, "match_rate": matches / total,
            "mismatches": mismatches}


def _shuffle_null(rates_by_n, composite_set, n_shuffle=200, seed=0):
    """Negativkontrolle: Label-Permutation (Gruppengroessen fix).
    Labels werden aus dem Fenster abgeleitet (label=1 ⟺ N composite)
    und AUSGERICHTET auf die sortierten Schluessel.

    EVALUATIONS-LOG (dokumentiert, nicht still korrigiert): Run 1
    (gefrorenes Prereg md5 73bc664a) lieferte spuriously REFUTED — der
    Label-Vektor war als [1]*n_comp + [0]*n_prim konstruiert und damit
    an die sortierten Schluessel FALSCH ausgerichtet (primes sortieren
    vor composites): delta_obs = -0.308, p = 0.95. Der Fehler lag in
    DIESEM Statistik-Code, nicht in Fenstern/Schwellen (md5 unveraendert);
    behoben durch Ausrichtung der Labels auf die Fenstergliederschaft
    (= exakt die registrierte Statistik)."""
    rng = np.random.default_rng(seed)
    ns = sorted(rates_by_n.keys())
    rates = np.array([rates_by_n[n] for n in ns], dtype=float)
    labels = np.array([1 if n in composite_set else 0 for n in ns])
    assert labels.sum() == len(composite_set)

    def delta(lab):
        return rates[lab == 1].mean() - rates[lab == 0].mean()

    delta_obs = delta(labels)
    count = 0
    for _ in range(n_shuffle):
        perm = rng.permutation(labels)
        if delta(perm) >= delta_obs:
            count += 1
    return {"delta_obs": float(delta_obs),
            "p": count / n_shuffle, "n_shuffle": n_shuffle, "seed": seed}


def run_evaluation(path=PREREG_PATH, n_count=None, n_x=None):
    """Auswertung NUR gegen das GEFRORENE Prereg (md5-Verifikation,
    Abbruch bei Verletzung). Alle Fenster/Schwellen kommen aus dem
    Freeze — keine Laufzeit-Entscheidung."""
    prereg = load_frozen_prereg(path)
    windows = prereg["falsifier"]["windows"]
    th = prereg["falsifier"]["thresholds"]
    if n_count is None:
        n_count = windows["qpe"]["n_count"]
    if n_x is None:
        n_x = windows["qpe"]["n_x"]

    # O1: klassische Grid-Raten
    o1 = {}
    for n in windows["classical"]["primes"] + windows["classical"]["composites"]:
        o1[n] = sq.grid_violation_rate(n)
    prime_rates = [o1[n] for n in windows["classical"]["primes"]]
    excluded = set(windows["classical"]["korselt_excluded"])
    comp_n = [n for n in windows["classical"]["composites"]
              if n not in excluded]
    comp_rates_nonkorselt = [o1[n] for n in comp_n]
    rate_561 = o1[561]
    max_order_561 = sq.max_order(561)

    # O1': Oracle-Output (voller Shor-Weg) im QPE-Fenster
    o1p = {}
    for n in windows["qpe"]["primes"] + windows["qpe"]["composites"]:
        o1p[n] = sq.shor_factor(n, n_count=n_count, n_x=n_x,
                                max_attempts=windows["qpe"]["max_attempts"])
    comp_factored = all(
        o1p[n] is not None for n in windows["qpe"]["composites"])
    prime_factored = any(
        o1p[n] is not None for n in windows["qpe"]["primes"])

    # O1b: Bridge-Match (QPE-Readout == exakte Ordnung)
    o1b = {}
    for n in windows["qpe"]["primes"] + windows["qpe"]["composites"]:
        o1b[n] = qpe_order_grid_match(n, n_count, n_x)
    bridge_min = min(v["match_rate"] for v in o1b.values())

    # O2: CRT-Residuum (strukturelle Null)
    pairs = [tuple(p) for p in th["crt_pairs"]]
    o2_crt = max(sq.crt_factorization_dev(a, p, q)
                 for (p, q) in pairs for a in (2, 3)
                 if gcd(a, p * q) == 1)
    o2_trace = max(sq.trace_product_dev(a, p, q, ts=sq.TS_CHECK)
                   for (p, q) in pairs for a in (2, 3)
                   if gcd(a, p * q) == 1)

    # Negativkontrolle: Shuffle-Null ueber alle klassischen N
    shuffle = _shuffle_null(o1, set(windows["classical"]["composites"]),
                            n_shuffle=th["n_shuffle"], seed=th["shuffle_seed"])

    results = {
        "o1_grid_classical": o1,
        "o1_prime_rate_max": max(prime_rates),
        "o1_composite_rate_min_nonkorselt": min(comp_rates_nonkorselt),
        "o1_blindness_561_rate": rate_561,
        "o1_max_order_561": max_order_561,
        "o1_blindness_561_confirmed": (rate_561 == 0.0
                                       and max_order_561 != 560),
        "o1p_shor": {str(n): f for n, f in o1p.items()},
        "o1p_composite_factored_all": comp_factored,
        "o1p_prime_factored_any": prime_factored,
        "o1b_bridge_match_min": bridge_min,
        "o1b_bridge_mismatches": {str(n): o1b[n]["mismatches"]
                                  for n in o1b if o1b[n]["mismatches"]},
        "o2_crt_max_dev": o2_crt,
        "o2_trace_max_dev": o2_trace,
        "shuffle": shuffle,
    }
    verdict = _verdict(results, th)
    return {"verdict": verdict, "results": results,
            "prereg_md5": prereg["md5"], "md5_verified": True,
            "score": EXTRAORDINARINESS_SCORE,
            "standard": EVIDENCE_STANDARD}


def _verdict(res, th):
    """Gefrorene Verdict-Regeln (decision_rules 1-4)."""
    # Regel 1: Kontrollen zuerst
    if (res["o2_crt_max_dev"] > th["tol_identity"]
            or res["o2_trace_max_dev"] > th["tol_identity"]):
        return "VOID"
    if res["o1_prime_rate_max"] != th["prime_max_rate"]:
        return "INVALID"          # Theorem verletzt -> Setup falsch
    if not res["o1_blindness_561_confirmed"]:
        return "INVALID"          # registrierte Diagnose falsch
    # Regel 4: DEGENERAT — keine Trennung im klassischen Fenster
    if res["o1_composite_rate_min_nonkorselt"] < th["composite_min_rate"]:
        return "DEGENERAT"
    # Regel 3: REFUTED — Readout traegt das Raster nicht
    if not res["o1p_composite_factored_all"] or res["o1p_prime_factored_any"]:
        return "REFUTED"
    if res["o1b_bridge_match_min"] < th["bridge_match_min"]:
        return "REFUTED"
    if res["shuffle"]["p"] > th["shuffle_max_p"]:
        return "REFUTED"
    # Regel 2: CONFIRMED
    return "CONFIRMED"