# -*- coding: utf-8 -*-
"""pt_ram_q_hardware3_rep_eval.py — EXPERIMENT 047 (H-RAM-Q-5a/5b):
registrierte Klassifikation der Phase-11d-Wiederholung.

Die GEFRORENE Phase-11-Auswertung (pt_ram_q_hardware3_eval.evaluate,
Verdict-Map md5 baaca1f6) liefert auf dem neuen Raw
(pt_ram_q_hardware3_raw_rep.json, Job dat3gpqhcrkc73dtjmt0) automatisch
das Session-2-Verdict (pt_ram_q_hardware3_eval_rep.json) — dieses Modul
KLASSIFIZIERT es gegen die Prereg-Hypothesen
(pt_ram_q_hardware3_rep_prereg.json, REGISTERED_NOT_MEASURED, Amendment
2026-09-28 VOR Submission committet):

- H-RAM-Q-5a: Session-Robustheit des Falsifikators (verdict-tragend).
  Klassen (registriert): SESSIONROBUST (neues Verdict ==
  H-RAM-Q-4_REFUTED, n_below_sharp >= 2) / SESSION_SPEZIFISCH (neu in
  {NOISE_LIFT_CONFIRMED, COARSE_HOLD_SHARP_MISS}) / VOID_ERNEUT (neu ==
  VOID_CALIBRATION) / INVALID (Kontrollen oder Verdict-Map-Integritaet
  scheitern) / AMPL_ODER_DEGENERAT (registrierte Reservezweige).
- H-RAM-Q-5b: Echo-Leiter-Diagnostik (NICHT verdict-tragend): faellt
  fit_kappa_block am q5-Bein wieder unter 0.81 (11d: 0.7314, q3:
  0.9927)? Faellt die Holdout-kappa_hat-Floor-Union wieder in das
  committete 11d-Band [0.8245, 0.9725]?
- deskriptiv: punktweise Sessions-Differenz-Tabelle (res_v3, kappa_hat,
  gamma_arm) neu vs 11d + Falsifikator-Mengen-Vergleich.

Verdict-Governance (registriert): KEIN stilles Re-Decide — das
Phase-11-REFUTED bleibt committetes Session-1-Verdict; beide Verdicts
stehen als Sessions-Paar in der Kette; der Vektor-Update entscheidet
NACH Vorliegen beider, im Doku-Commit.
"""
import hashlib
import json

EVAL_REP_PATH = "pt_ram_q_hardware3_eval_rep.json"
EVAL_11D_PATH = "pt_ram_q_hardware3_eval.json"
PREREG_PATH = "pt_ram_q_hardware3_rep_prereg.json"
REP_EVAL_PATH = "pt_ram_q_hardware3_rep_eval.json"

FLOOR_KAPPA = 0.81            # kappa-Floor der gefrorenen Verdict-Map
W_B_DP = 0.02787029633307472  # gefrorenes w_B'' (== w_B', Freeze A'')

# Gefrorene Verdict-Strings (pt_ram_q_hardware3_eval.evaluate)
V_REFUTED = "H-RAM-Q-4_REFUTED"
V_CONFIRMED = "H-RAM-Q-4_NOISE_LIFT_CONFIRMED"
V_COARSE = "H-RAM-Q-4_COARSE_HOLD_SHARP_MISS"
V_AMPL = "H-RAM-Q-4_INVALID_AMPLIFICATION"
V_VOID = "H-RAM-Q-4_VOID_CALIBRATION"
V_DEGENERAT = "H-RAM-Q-4_DEGENERAT"
V_INVALID = "EVALUATION_INVALID_CONTROLS_FAILED"
V_UNMATCHED = "VERDICT_MAP_UNMATCHED"

# Registrierte H-RAM-Q-5a-Klassen
K_INVALID = "H-RAM-Q-5a_INVALID"
K_VOID_ERNEUT = "H-RAM-Q-5a_VOID_ERNEUT"
K_SESSIONROBUST = "H-RAM-Q-5a_SESSIONROBUST"
K_SESSION_SPEZIFISCH = "H-RAM-Q-5a_SESSION_SPEZIFISCH"
K_RESERVE = "H-RAM-Q-5a_AMPL_ODER_DEGENERAT"

KONTROLLEN = ("t3_identity_two_ways", "t4_negative_must_not_fire",
              "t5_gate_set_frozen", "t6_mass_conservation")


def file_md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def kontrollen_ok(doc):
    """t3/t4/t5/t6 ok UND counts-md5 verifiziert (INVALID-Praedikat)."""
    if not doc.get("counts_md5_verified"):
        return False
    for key in KONTROLLEN:
        entry = doc.get("kontrollen", {}).get(key)
        if not isinstance(entry, dict) or entry.get("ok") is not True:
            return False
    return True


def verdict_map_gleich(doc_neu, doc_alt):
    """Dieselbe gefrorene Verdict-Map in beiden Sessions (md5 baaca1f6):
    die Map wird als committeter Text gefuehrt — Byte-Gleichheit ist der
    Integritaetsnachweis, dass Session 2 unter DEMSELBEN Gesetz
    ausgewertet wurde."""
    return doc_neu.get("verdict_map_text") == doc_alt.get("verdict_map_text")


def classify_5a(doc_neu, doc_alt):
    """Registrierte Klassifikation (Praedikate laut Prereg, in der
    Reihenfolge INVALID -> VOID_ERNEUT -> SESSIONROBUST ->
    SESSION_SPEZIFISCH -> Reserve)."""
    verdict = doc_neu["verdict"]
    if not kontrollen_ok(doc_neu) or not verdict_map_gleich(doc_neu,
                                                            doc_alt):
        return K_INVALID, ("Kontrollen (t3/t4/t5/t6) oder Verdict-Map-"
                           "Integritaet scheitern — kein Aussagesubstrat, "
                           "dokumentierte Zurueckstellung der "
                           "Hypothesen-Klassifikation.")
    if verdict == V_VOID:
        return K_VOID_ERNEUT, ("kappa-Floor erneut >= 2 Punkte < 0.81 — "
                               "Kalibrier-Defizit session-robust; die "
                               "11d-kappa-Abdeckung (0/26) war die "
                               "Session-Anomalie.")
    if verdict == V_REFUTED:
        return K_SESSIONROBUST, ("Neues Verdict == H-RAM-Q-4_REFUTED "
                                 "(Falsifikator feuert wieder "
                                 "n_below_sharp >= %d). Das REFUTED-Muster "
                                 "ist session-unabhaengig — die "
                                 "Falsifikation des v3b-Gesetzes "
                                 "verfestigt sich."
                                 % doc_neu["verdict_inputs"]
                                 ["n_below_sharp"])
    if verdict in (V_CONFIRMED, V_COARSE):
        return K_SESSION_SPEZIFISCH, ("Neues Verdict in {CONFIRMED, "
                                      "COARSE} — das Phase-11-REFUTED "
                                      "war kalibrier-session-spezifisch. "
                                      "Dokumentiert EHRLICH: das 11d-"
                                      "Verdict wird NICHT stillschweigend "
                                      "geaendert; beide Verdicts stehen "
                                      "als Sessions-Paar in der Kette.")
    return K_RESERVE, ("registrierte Reservezweige (AMPL/DEGENERAT/"
                       "UNMATCHED): " + verdict)


def eval_5b(doc_neu, doc_alt):
    """Echo-Leiter-Diagnostik (NICHT verdict-tragend, Mechanismus)."""
    out = {"interpretationsguard": "Die Echo-Leiter ist Mechanismus-"
           "Diagnostik (Echo-Block-Struktur), NICHT Teil der gefrorenen "
           "Verdict-Map — eine Veraenderung veraendert KEIN Verdict."}
    for arm in ("q3_d3", "q5_d5"):
        fit_neu = doc_neu["echo_ladder"][arm]["fit_kappa_block"]
        fit_alt = doc_alt["echo_ladder"][arm]["fit_kappa_block"]
        out[arm] = {
            "fit_kappa_block_neu": fit_neu,
            "fit_kappa_block_11d": fit_alt,
            "unter_floor_081": bool(fit_neu < FLOOR_KAPPA),
            "session_robust_unter_floor": bool(fit_neu < FLOOR_KAPPA
                                               and fit_alt < FLOOR_KAPPA),
            "delta_vs_11d": fit_neu - fit_alt,
        }
    # Holdout-kappa_hat-Floor-Union (11d-Band committet: [0.8245, 0.9725])
    def union(doc):
        ks = [v["kappa_hat"] for v in doc["punkte"].values()
              if v["set"] == "verdict"]
        return [min(ks), max(ks)]
    u_neu, u_alt = union(doc_neu), union(doc_alt)
    out["floor_union_neu"] = u_neu
    out["floor_union_11d"] = u_alt
    out["union_im_band_11d"] = bool(u_neu[0] >= u_alt[0]
                                    and u_neu[1] <= u_alt[1])
    out["floor_shift_vs_11d"] = u_neu[0] - u_alt[0]
    out["gamma_arm"] = {
        arm: {"neu": doc_neu["gamma_arm"][arm]["gamma"],
              "alt_11d": doc_alt["gamma_arm"][arm]["gamma"],
              "delta": doc_neu["gamma_arm"][arm]["gamma"]
              - doc_alt["gamma_arm"][arm]["gamma"]}
        for arm in ("q3_d3", "q5_d5")}
    return out


def falsifikator_vergleich(doc_neu, doc_alt):
    """Deskriptiv: below_sharp-Mengen der HOLDOUT-Punkte beider Sessions."""
    def lows(doc):
        return sorted(k for k, v in doc["punkte"].items()
                      if v["set"] == "verdict" and v["below_sharp"])
    neu, alt = lows(doc_neu), lows(doc_alt)
    return {
        "below_sharp_neu": neu,
        "below_sharp_11d": alt,
        "schnitt": sorted(set(neu) & set(alt)),
        "nur_11d": sorted(set(alt) - set(neu)),
        "nur_neu": sorted(set(neu) - set(alt)),
        "set_identisch": bool(neu == alt),
        "residuen": {k: {"neu": doc_neu["punkte"][k]["res_v3"],
                         "alt_11d": doc_alt["punkte"][k]["res_v3"]}
                     for k in sorted(set(neu) | set(alt))},
    }


def diff_tabelle(doc_neu, doc_alt):
    """Deskriptiv (Prereg): punktweiser Vergleich res_v3 / kappa_hat,
    neu vs 11d."""
    rows = {}
    for k in sorted(doc_neu["punkte"]):
        a, b = doc_neu["punkte"][k], doc_alt["punkte"][k]
        rows[k] = {
            "res_v3_neu": a["res_v3"], "res_v3_11d": b["res_v3"],
            "res_v3_delta": a["res_v3"] - b["res_v3"],
            "kappa_hat_neu": a["kappa_hat"], "kappa_hat_11d": b["kappa_hat"],
            "kappa_hat_delta": a["kappa_hat"] - b["kappa_hat"],
            "below_sharp_neu": a["below_sharp"],
            "below_sharp_11d": b["below_sharp"],
            "in_band_sharp_neu": a["in_band_sharp"],
            "in_band_sharp_11d": b["in_band_sharp"],
        }
    return rows


def main():
    doc_neu = json.load(open(EVAL_REP_PATH, encoding="utf-8"))
    doc_alt = json.load(open(EVAL_11D_PATH, encoding="utf-8"))
    klasse, begruendung = classify_5a(doc_neu, doc_alt)
    d5b = eval_5b(doc_neu, doc_alt)
    falsi = falsifikator_vergleich(doc_neu, doc_alt)
    tab = diff_tabelle(doc_neu, doc_alt)
    out = {
        "experiment": "047-ram-q-phase11d-repetition",
        "hypothesis": "H-RAM-Q-5",
        "qpu": 0,
        "session2": {
            "job_id": doc_neu["raw_job_meta"]["job_id"],
            "backend": doc_neu["raw_backend"],
            "raw_counts_md5": doc_neu["raw_counts_md5"],
            "counts_md5_verified": doc_neu["counts_md5_verified"],
            "eval_doc": EVAL_REP_PATH,
        },
        "session1_anker": {
            "job_id": doc_alt["raw_job_meta"]["job_id"],
            "raw_counts_md5": doc_alt["raw_counts_md5"],
            "verdict": doc_alt["verdict"],
            "eval_doc": EVAL_11D_PATH,
        },
        "prereg_md5_file": file_md5(PREREG_PATH),
        "prereg_status": "REGISTERED_NOT_MEASURED (Amendment 2026-09-28 "
                         "VOR Submission committet;ISA3-Gate-Evidenz "
                         "pt_ram_q_hardware3_rep_isa_gate.json)",
        "integritaet": {
            "kontrollen_ok": kontrollen_ok(doc_neu),
            "verdict_map_gleich": verdict_map_gleich(doc_neu, doc_alt),
            "counts_md5_verified": doc_neu["counts_md5_verified"],
        },
        "h_ram_q_5a": {
            "klassifikation": klasse,
            "begruendung": begruendung,
            "verdict_neu": doc_neu["verdict"],
            "verdict_inputs_neu": doc_neu["verdict_inputs"],
            "verdict_tragend": True,
        },
        "h_ram_q_5b": d5b,
        "falsifikator_vergleich": falsi,
        "sessions_differenz_tabelle": tab,
        "verdict_governance": {
            "kein_stilles_re_decide": "Das Phase-11-REFUTED bleibt als "
                                      "committetes Session-1-Verdict "
                                      "stehen; Session 2 ist ein NEUES, "
                                      "unabhaengiges Session-Verdict unter "
                                      "DEMSELBEN gefrorenen Gesetz "
                                      "(Verdict-Map md5 baaca1f6, "
                                      "Byte-Gleichheit verifiziert).",
        },
    }
    with open(REP_EVAL_PATH, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("written:", REP_EVAL_PATH)
    print("H-RAM-Q-5a:", klasse)
    print("  verdict_neu:", doc_neu["verdict"], "| n_below_sharp:",
          doc_neu["verdict_inputs"]["n_below_sharp"], "(11d:",
          doc_alt["verdict_inputs"]["n_below_sharp"], ")")
    print("H-RAM-Q-5b (Diagnostik):")
    for arm in ("q3_d3", "q5_d5"):
        e = d5b[arm]
        print("  %s fit_kappa_block %.4f (11d %.4f, delta %+.4f) "
              "unter_floor %s session_robust %s"
              % (arm, e["fit_kappa_block_neu"], e["fit_kappa_block_11d"],
                 e["delta_vs_11d"], e["unter_floor_081"],
                 e["session_robust_unter_floor"]))
    print("  floor_union_neu:", d5b["floor_union_neu"],
          "im 11d-Band:", d5b["union_im_band_11d"],
          "floor_shift %+.4f" % d5b["floor_shift_vs_11d"])
    print("falsifikator: neu", falsi["below_sharp_neu"], "| 11d",
          falsi["below_sharp_11d"], "| Schnitt", falsi["schnitt"])
    return out


if __name__ == "__main__":
    main()