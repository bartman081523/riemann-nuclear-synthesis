# -*- coding: utf-8 -*-
"""Deck-Update EXPERIMENT 052: baut aus der HEAD-Blob-Kopie (stable, md5
423b909069b5f709057e604dbb5e5f3a) das gemischte Deck und schreibt es in
den TRACKED worktree-Pfad HYPOTHESEN_UND_ANTITHESEN_H9_2026_09_29.md
(C.5a-Repair von f0fdd4c's bypass-commit + 052-Zusatz in einem Zug).
KEIN git restore/checkout — content write via python."""
import hashlib
import io
import os

SRC = os.path.join(os.environ["CLAUDE_JOB_DIR"], "tmp", "deck_head.md")
DST = "HYPOTHESEN_UND_ANTITHESES_H9_2026_09_29.md"
WANT_HEAD = "423b909069b5f709057e604dbb5e5f3a"

C3A = """
#### C.3a ERGEBNIS (Experiment 052, H-S4CLOSURE-R2 045-Einstufung, 2026-10-02, 0 QPU, verdict-tragend fuer die Einstufungs-Tabelle, NICHT fuer das committete 045-Verdict)

- **Kette:** Prereg-Freeze `56312a7` (pt_s4_r2_prereg.json, md5
  51d5f255259d443a35f68fe5e771a208, REGISTERED_NOT_MEASURED, +22 Tests:
  Kanonik/md5/Basis-Pins/Verdict-Zweige/Konsistenz-Gate; schmalste Kante ex
  ante disclosed 8.393228334568903e-10 am Paar (3,12), Faktor ~1.19, Flip
  vor-klassifiziert H_S4CLOSURE_R2_STRUKTURELL_REST) -> EIN Lauf `b04d7bb`
  (Roh pt_s4_r2_results.json, md5 0a1856a7a5a2a1a93f17e1b101a16c0d,
  committed VOR Auswertung, 5912.0 s gesamt) -> gefrorene Auswertung
  `0a4cf15` (pt_s4_r2_eval.json, entscheidet NUR aus committeten
  Artefakten).
- **Verdict: H_S4CLOSURE_R2_QUELLEN_ARTEFAKT.** L1 wörtlich
  `s4.check_t5_t6` (Cache): das Maximum 1.0260516436488842e-08
  reproduziert BIT-IDENTISCH (Faktor 10.26 über TOL, repr-verankert,
  Star-Worst-Paar (0, 6); disjoint Star-Arm max 3.2032171359830386e-09 am
  Paar (4, 7)). L2 (unified-Lesart, k_norm-Quotient mit Cache-t_H) hebt
  die Verletzung in ALLEN vier Lesarten unter TOL: full-adjacent
  8.393228334568903e-10 (Faktor 1.19, Nicht-Bahnen-Paar (3, 12)),
  full-disjoint 2.679068078492719e-11 (Faktor 37.3), Bahn adjacent
  6.423892529028308e-10 (Faktor 1.56), Bahn disjoint 2.679068078492719e-11
  (Faktor 37.3).
- **Mechanismus (dreistufig, §10.35-D):** (1) 045 misst repr-verankert
  (max_within_orbit_dev zum repr, idxs[0] = 0) — im committeten Scratch
  ist das Maximum Paarungs-Struktur ((6, 10) 1.138e-8, inst_reproduziert
  = false); (2) t_H-Quelle — Cache-Eigen 3096.93 s vs per-Instanz
  386.08 s (Quotient 8.02) kippt die ratio-Mediane von ~1e-8 nach ~1e-10;
  (3) Voll-Grid-Verstärker — der Scratch-Vergleich war Bahn-beschnitten,
  das volle 12-Paar-Grid hebt den unified-Worst von (6, 10) 6.42e-10 auf
  (3, 12) 8.39e-10.
- **Integrität:** 8/8 Bit-Pins gegen 045-Erste-Messung + committeten
  Scratch mit delta 0.000e+00 (049b-Cross-Build-Furcht materialisiert
  NICHT; numpy 2.4.6, QISKIT_PARALLEL=FALSE); Konsistenz-Gate re-der die
  Mediane/Maxima bit-exakt aus den Roh-Arrays (Boundary strikt: '>'
  faellt bei Gleichheit, '<' faellt bei Gleichheit).
- **Governance:** committetes 045-Verdict H_S4_CLOSURE_DEVIATION_FOUND
  UNVERÄNDERT (kein Re-Decide, keine Toleranz-Änderung); Margin-Disclosure
  verpflichtend für künftige 045-Nachrechnungen; Doku §10.35/§Z.34.

"""

F_OLD = ("| 2 | ~~S₄-Quellen-Einheitlichkeit (C.3)~~ ERLEDIGT 2026-09-29: "
         "max_within_unified 6.4239e-10 < 1e-9, Kriterium erfüllt (C.3) "
         "| 0 QPU ✓ | Kriterium erfüllt; Follow-up: gefrorenes "
         "Re-Rechnungs-Artefakt (0 QPU) für die offizielle 045-Einstufung — "
         "KEIN stilles Re-Decide | 045 |")
F_NEW = ("| 2 | ~~S₄-Quellen-Einheitlichkeit (C.3)~~ ERLEDIGT 2026-09-29: "
         "max_within_unified 6.4239e-10 < 1e-9, Kriterium erfüllt (C.3); "
         "~~Follow-up: offizielle 045-Einstufung~~ ERLEDIGT 2026-10-02: "
         "Experiment 052 H-S4CLOSURE-R2 (Prereg md5 51d5f2552…, EIN Lauf "
         "5912.0 s) → **H_S4CLOSURE_R2_QUELLEN_ARTEFAKT** — alle 4 "
         "L2-Lesarten < TOL (Margin ≥ 1.19) (C.3a) | 0 QPU ✓ | Einstufung "
         "statt stillem Re-Decide; 045-Verdict unverändert; "
         "Margin-Disclosure verpflichtend (schmalste Kante (3,12)) | 045 |")

G_OLD = "pt_ram_q_hardware3_prereg.json (11), pt_s4_closure_theorem prereg (045).\n- Scratches"
G_NEW = (
    "pt_ram_q_hardware3_prereg.json (11), pt_s4_closure_theorem prereg (045).\n"
    "- 052-Kette (C.3a, 045-Einstufung): pt_s4_r2_prereg.json (md5\n"
    "  51d5f255259d443a35f68fe5e771a208, +22 Tests),\n"
    "  pt_s4_r2_results.json (Roh md5 0a1856a7a5a2a1a93f17e1b101a16c0d,\n"
    "  committed VOR Auswertung), pt_s4_r2_eval.json (Verdict\n"
    "  H_S4CLOSURE_R2_QUELLEN_ARTEFAKT) + pt_s4_r2_recompute.py /\n"
    "  pt_s4_r2_eval.py / tests/test_pt_s4_r2.py; Commits 56312a7 /\n"
    "  b04d7bb / 0a4cf15; Doku §10.35 (Haupt-Doku) + §Z.34 (SYNTHESIS).\n"
    "- Scratches")


def sub_once(text, old, new, tag):
    n = text.count(old)
    assert n == 1, "Anchor %s: %d Treffer" % (tag, n)
    return text.replace(old, new)


def main():
    with open(SRC, encoding="utf-8") as fh:
        head = fh.read()
    got = hashlib.md5(head.encode("utf-8")).hexdigest()
    assert got == WANT_HEAD, "Basis-md5 %s != HEAD %s" % (got, WANT_HEAD)

    merged = head
    merged = sub_once(merged, "0 QPU moeglich).\n\n### C.4",
                      "0 QPU moeglich).\n" + C3A + "### C.4", "C3a")
    merged = sub_once(merged, F_OLD, F_NEW, "F-Zeile2")
    merged = sub_once(merged, G_OLD, G_NEW, "G-Quellen")

    with open(DST, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(merged)
    new_md5 = hashlib.md5(io.open(DST, "rb").read()).hexdigest()
    print("geschrieben:", DST, len(merged.encode("utf-8")), "Bytes, md5",
          new_md5)
    print("C3a:", "#### C.3a ERGEBNIS" in merged)
    print("F2-ERLEDIGT:", "H_S4CLOSURE_R2_QUELLEN_ARTEFAKT" in
          merged.split("| 2 |")[1][:400] if "| 2 |" in merged else False)
    print("Zeilen:", merged.count("\n"))


main()