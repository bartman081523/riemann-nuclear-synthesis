# H9 — Kombinatorische Hypothesen und Steelman-Antithesen (2026-09-29)

**Status:** 0 QPU. Lese-only auf committeten Artefakten. **NICHT verdict-tragend**
(Praezedenz gamma_arm / Phase 11d / pt_s4_t5_diag): dieses Deck re-decided KEIN
bestehendes Verdict, aendert KEINE Toleranz und NOCHT KEINEN gefrorenen Prä-reg.
Jede hypothesis-tragende Umsetzung eines Punkts aus diesem Dokument braucht
VOR der ersten Messung ein eigenes REGISTERED_NOT_MEASURED-Freeze (Prereg-MD5),
Raw-Commit VOR Auswertung.

**Auftrag (User, 2026-09-29):** "denke über die gesamte Experimentierreihe nach …
mehrere nach den Sternen greifende aber valide Hypothesen und mehrere neue
valide Steelman-Antithesen … auch die ganz dummen Sachen, aber auch die ganz
schlauen", Python-Scratches in `scratches/`, alte Module einbinden/rekombinieren.

**Scratches (0 QPU, neu, committed):**
- `scratches/h9_ramq_sessions.py` (+ `h9_ramq_sessions_out.json`) — RAM-Q
  Session-Stuktur (Abschnitt B.1, Zahlen stand 2026-09-29).
- `scratches/h9_s4_source_unified.py` (+ `h9_s4_source_unified_out.json`)
  — S₄-Quellen-Einheitlichkeit (B.2/C.3, Ergebnis 2026-09-29:
  max_within_unified 6.423892529028308e-10 < SUM_TOL); Module:
  `pt_hstar5_execution`, `pt_s4_closure_theorem`, `pt_s4_t5_diag`.
- Ein Scratch-Bug (Hypergeometrie-Aufruf) ist in D-9 dokumentiert und korrigiert —
  die im Text verwendeten Zahlen sind die korrigierten.

**Suite/Artefakt-Basis:** 1225 Tests gruen (95.2 s); Phase-12-Endstand
(KOMPLETT bis auf 046-Fez-Bein) committet b5461fc; alle 17 Commits bis b5461fc
GEPUSHT 2026-09-29 (User-Freigabe "push"), Reststand 0.

---

## A. Inventar der Serie (Kurz-Tabelle, alle committet)

| Experiment | Frage | Verdict | Grade | Ort |
|---|---|---|---|---|
| Phase 8/9 RAM-Q-1/2 | Fünf-Fingerprint atomar abgeleitet; B2 q-universal EXAKT; Wraparound ABSOLUT | GENERALIZED / CONFIRMED | A−/B | §Z.20 ff. |
| Phase 9 H-RAM-Q-3 | 13 κ̂ auf Hardware | VOID_CALIBRATION | A− | dartdg5v… Vorläufer-Kette |
| Phase 10 H-RAM-Q-3b | Minimalregister d=q, Freeze A'/B' | REFUTED (13/13 unter c(κ̂)−w_B′, Suppression) | A− | 7483a11 |
| Phase 11 H-RAM-Q-4 | kohärentes Prep-Fehler-Gesetz v3/v3b | REFUTED — Falsifikator GENAU 3/13 am q5-Bein | A− | 2e348f1 |
| Phase 12 H-RAM-Q-5a | Session-Robustheit des REFUTED (047, Fez-Sampler) | SESSIONROBUST — REFUTED reproduziert | A− | 7a95cff |
| 045 H-S4-CLOSURE | S₄-Schluss-Theorem numerisch | H_S4_CLOSURE_DEVIATION_FOUND (GENAU EINE Verletzung, r_median) | A− | f91eb96 |
| 046 H-V5R | 035-Kingston-Repräs | bias −0.01370781714786462 = −2.22σ, VORZEICHEN-FLIP; Fez-Bein QUEUED | — | bbb2de5 |
| 023-EXT H_MOCS_EXT | N-Range-Stretch + §5.5 | HOLDS, 4 Claims gruen | A− | 60456f9 |
| H-STAR-5 Phase 6a | Prime-Ensemble vs Shuffle | REFUTED (R_prime in Shuffle-Band) | — | 837dae2c |
| Shor-Bridge H-SHOR-1 | Ququint-Oracle-Brücke | CONFIRMED (Korselt-Blindheit exakt) | — | Branch shor-ququint-oracle |
| V1–V4 Steelman | GF(5)-Familie | V4 CONFIRMED κ*=62.26; V2 REFUTED+Ramanujan; V1/V3 DEGENERAT | A−/B | Preregs 4/4 |

## B. Neue Empirie der H9-Scratches (alles 0 QPU, committete JSONs)

B.1 Residuen-Session-Stuktur (Scratch `h9_ramq_sessions.py`, Abschn. (A)-(G)):

| Messung | Wert | Gegenstück in committeten Verdicts |
|---|---|---|
| Spearman[res_S1(P), res_S2(P)] über 13 Holdout-Verdict-P | **+0.896** (Pearson +0.823) | beide Sessions verwendeten VERSCHIEDENE in-job γ_fits (S1 0.0091/0.0381, S2 0.0023/0.0160) |
| Vorzeichen-gleich | **11/13** (P(≥11/13 unter symm. Null) ≈ 92/8192 ≈ 0.0112) | Falsifikator-Schnitt {467, 673} |
| Vorzeichen-stabil bei \|res_S1\| ≥ 0.01 | **9/9** (nur 2 Vorzeichen-Wechsel ueberhaupt: q3 181 −0.0005→+0.0069, 283 +0.0031→−0.0077; beide in der \|res_S1\| < 0.004-Klasse; die 4 Kleinen \|res_S1\| < 0.01: 691/q5 −0.0013→−0.0074, 181, 229 +0.0039→+0.0113, 283) | 467/547/673 (↓) und 613 (↑) beide Sessions |
| per-Bahn spearman | q5 +0.500 (pearson 0.799), q3 +0.810 (pearson 0.773) | — |
| κ̂-Rank der Falsifikatoren S1 | 3./4./5. von 5 (alle untersten) | passt zur κ̂-Tail-Lesart |
| κ̂-Rank der Falsifikatoren S2 | 4./2. von 5 — **467 hat κ̂ 0.8686 = NICHT das Minimum bei Residuum −0.0841, das Maximum |ref| ist 613 (+0.0768) bei κ̂ 0.8708** | widerspricht κ̂-Tail |
| spearman[res, κ̂] q5 | S1 −1.000 → S2 **+0.100** | die κ̂-Tail-Beziehung KIPPT zwischen Sessions |
| spearman[res, ISA two_q / depth] (13 verdict-P) | S1 −0.286/−0.341, S2 −0.258/−0.286 | kein Tiefe-Träger der session-stabilen Komponente |
| Hypergeometrie Schnitt {467,673} (N=13, \|S1\|=3, \|S2\|=2) | **3/78 = 0.0385** | Schnittmenge ist klein, aber kein Proof-by-itself |
| P(\|z\| ≥ 2.22) | 0.0264; P(≥1 in 4 Sessions) = **0.102** | 046-Kingston unter Multipl.-Vergleich unauffällig |
| γ-ARM-Kalibrier q5 (5 cal-P, LSQ-durch-0) | resid-SD **0.0239** vs w_B″ 0.0279 | Kalibrier-Streite ~ das Band selbst; SE(γ)·c_p ≈ 0.011 |
| γ-LSQ-ohne-Achse (Frei-Achse OLS, n = 5/8) | q5 +0.216 ± 0.125 (R² 0.50), q3 +0.041 ± 0.012 (R² 0.65) | Konventions-Differenz zur committeten Formel (<cP,δ>/<cP,cP>) — reproduziert 0.0381 exakt |
| Echo-r8 q5 | **0.098154** (S1) vs **0.098027** (S2) — Session-identisch auf 1.3e-3 | r1 bewegt sich 0.827→0.869, r8 NICHT |
| Echo-r8 q3 | 0.9118 / 0.8964 — driftet | kein q3-Floor sichtbar |
| Echo-Gesetzesform B^r (OLS, 4 Rungen) | q5 B 0.7678/0.7691, SSE 0.0378/0.0498; q3 B 0.9870/0.9847 | committed fit_kappa_block 0.7314/0.7270 (anderes Fit-Verfahren: r1 teilt Loschmidt-Anker, nicht B^r-OLS) |

B.2 S₄-Quellen-uniformer Re-Run (Scratch `h9_s4_source_unified.py`, in-flight
beim Schreiben; Ergebnis-JSON: Job-tmp `h9_s4_unified.json`):
Die 045-Verletzung (T5 max_within 1.0260516436488842e-08 am r_median) wird
gegen dieselbe 78er-Familie nochmal gerechnet mit r auf EINHEITLICHER
t_H-Quelle: `r_unified = K(evs, τ2·t_cache)/K(evs, τ1·t_cache)` — genau die
Quelle, an der k1/k2/k3 bereits bewertet werden. Replik-Arm (per-instanz,
identisch zur 045-Spur): erste 3 Muster-Medians 1.9147852141/56/32 —
**Bit-Ebene reproduziert die 045-Mediane auf ~1e-9** (die 045-Referenz
r_median_p(6) = 1.9147852243778032 — letzte Ziffern des Rundungs-Bodens).
Zwischenstand (Muster 0-2, in-flight beim ersten Schreiben): die Cache-Quelle
liegt an einem VOLL anderen Betriebspunkt der Oszillatorkette
(t_cache/t_eig = 8.02, 045-Diagnose). Das finale Ergebnis ist in C.3
nachgetragen.

---

## C. Hypothesen (nach den Sternen greifend, valide, falsifizierbar)

Nummerierung H-H9-nn (kein Konflikt mit H-RAM-Q-5a/5b — 5b existiert als
Echo-Mechanismus-Guard in pt_ram_q_hardware3_rep_eval.json und bleibt ungetastet).

### C.1 H-H9-1 "P-Struktur-Komponente" (der Kern-Deck)

**Aussage.** Die v3b-Residuen res_v3(P, Arm) tragen eine SESSION-STABILE,
P-abhaengige Komponente s(leg, P) mit Amplitude bis ≥ 3·w_B″ auf dem q5-Bein
(467: −0.032/−0.084; 547: −0.044/−0.005; 613: +0.062/+0.077; 673: −0.055/−0.033)
und +0.02…+0.04 im q3-Kern (379/467/613/797 beide Sessions). Die v3b-Zentren
(κ̂-Term + γ-ARM, beide session-spezifisch gefittet) absorbieren die
Session-Kalibrier, lassen aber die P-Struktur unberuehrt — deshalb ist die
Session-Konsistanz (r=0.896, 11/13, 9/9 bei |res|≥0.01) NICHT Session-Rauschen,
sondern fehlender Term.

**Herkunft (Kombination):** 047 (SESSIONROBUST) + 11d-Verlauf + γ-ARM-Zeilen;
das ist die erste Richtung, in der die zweimalige REFUTED-Serie NICHT als
"Wiederholung derselben Falsifikation" endet, sondern als SIGNAL: dasselbe P
bricht in beiden Sessions gleichsinnig aus.

**Falsifizierbarer Test (Prereg-Pflicht, 1 QPU-Job oder 0 QPU bei Re-Read):**
(A) Offline-Teil: fit s(P) NUR auf den q5-Kalibrier-P (5 Punkte, beide
Sessions gepoolt, session-zentriert) → Prädiktion der 5 Verdict-P.
(B) Hardware-Teil (Session 3 oder 11d-Re-Read): s(P) mit Kalibrier-P EINER
Session fitten, auf Verdict-P des ARMS vorhersagen, Band w_B″; falsifiziert,
wenn s(P)-predigt die below_sharp-Menge nicht oder wenn die Vorzeichen-
Stabilität nicht auf den |res| ≥ 0.01 Punkten reproduziert.
(C) Kontrolle gegen Transpile-Konstruiertheit: ISA-Artefakte sind zwischen den
Sessions DETERMINISTISCH identisch (seed_transpiler 7) — deshalb P-Shuffle-
Kontrolle: die c_p->ISA-Zuordnung gegen ISA-Shuffle des GLEICHEN Reports testen
(sauberer als eine neue Messung zu erfinden): wenn die Residuen der ISA-
Geometrie folgen, folgt s(P) dem Report, nicht dem P.

**"Nach den Sternen":** dies ist der erste KANDIDAT auf ein echtes
P-zahlensystematisches (damit primzahlsystematisches) Signal im QPU-Ratio
der Serie — ausdruecklich KOMPATIBEL mit der harmlosen Lesart (P-abhaengiger
Detuning/Ladungsdetektor der chosen P), was der Grund ist, warum (C) die
Kontrolle ist. Wenn s(P) nach P-Zerlegung sortiert Cluster gibt (prime vs
composite auf demselben Kalibrier-P-Gitter!), aendert das die
Verdict-Lesart der REFUTED-Serie von "Kalibrier-Versagen" zu
"unmodellierter Struktur" — das waere die Rueckkehr des Falsifikators als
Entdeckung.

### C.2 H-H9-2 "Echo-r8-Floor" (q5 Tiefen-Leiter hat einen session-invarianten Boden)

**Aussage.** Auf dem q5-Bein ist κ_r(r=8) session-invariant:
0.098154 vs 0.098027 (Differenz 1.3e-3), waehrend r1 um +0.041 driftet
(0.8274→0.8686) und q3-r8 KEINEN Floor zeigt (0.9118/0.8964). Formlos: die
8-Rungen-Echo liefert eine Tiefen-refokussierte Groesse, die von der
Session-Kalibrier ENTKOPELT ist am tiefsten Rung, aber r1 (Anker,
Loschmidt-geteilt) folgt der Kalibrier-Epoche (+0.041, gleich wie der
κ̂-Floor-Shift +0.0357).

**Herkunft (Kombination):** Echo-Leiter 11d + 047 + Floor-Union der
Holdout-κ̂-Bänder [0.8245-0.9725] vs [0.8602-0.9623] — der Shift +0.0357 am
Boden entspricht dem r1-Shift am Anker.

**Falsifizierbarer Test (0 QPU + 1 Session):** in Session 3 (047-Kette)
muss κ_r8(q5) 0.098 ± 0.004 halten, waehrend r1 innerhalb ±0.05 wandert;
falsifiziert, wenn r8 um > 0.006 drifft ODER r1 NICHT mitverlaeuft.
Bei Bestätigung ist κ_r8_q5 ein KANDIDAT fuer einen "Struktur-Fingerprint",
der vom Kalibrier-Zustand entkoppelt ist.

### C.3 H-H9-3 "S₄-Quellen-Einheitlichkeit" (T5-Verletzung als Quellen-Rest)

**Aussage.** Wenn die EINZIGE 045-Verletzung (r_median-Muster) unter
quellen-einheitlicher r-Bewertung (Cache-t_H, wie k1/k2/k3) auf unter
SUM_TOL (1e-9) faltet, dann ist H_S4_CLOSURE_DEVIATION_FOUND ein reines
Quellen-Artefakt der _config_stats-Asymmetrie (k1/k2/k3 am Cache-t_H,
r_median am per-Instanz-t_H — 045-Diagnose, committet). Wenn die
Abweichung auf ~1e-8 BLEIBT, ist sie ein echter struktureller Rest
(und die S₄-Orbit-Invarianz hat ein reales, nicht-quellbares Bruch).

**Test:** scratches/h9_s4_source_unified.py, alle 15 Muster, Replik-Sanity
(per-Instanz-Mediane ↔ 045) — Ergebnis (Ergebnis-JSON:
scratches/h9_s4_source_unified_out.json).

**ERGEBNIS (2026-09-29, 538.8 s, alle 15 Muster):**

| Arm | adjacent (6,10) | disjoint (4,7) |
|---|---|---|
| r_inst (045-Quelle, Replik) | medians 1.9147852243778032 / 1.9147852129934473, diff **1.1384355902421817e-08** | 0.6631421891746621 / 0.6631421923778792, diff 3.2032171359830386e-09 |
| r_unified (Cache-t_H) | 1.0841032865605666 / 1.084103287202956, diff **6.423892529028308e-10** | 0.6259193254381626 / 0.6259193254649533, diff 2.679068078492719e-11 |
| kollaps-Faktor | 17.7 | 119.5 |

- **max_within_unified = 6.423892529028308e-10 < SUM_TOL 1e-9** — das
  registrierte Entscheidungs-Kriterium der Antithese ist ERFÜLLT: die
  einzige 045-r_median-Verletzung kollabiert unter quellen-einheitlicher
  Bewertung unter die Toleranz (Faktor 17.7 am adjacent-Bein).
- **Muster 6 inst_median = 1.9147852243778032** — bit-gleich mit der
  045-Referenz r_median_p(6). Der inst-Arm IST die 045-Verletzung (derselbe
  BAHNEN-Schnittpunkt, 1.138e-8 > 1.026e-8 = 045 max_within_orbit_dev,
  beide > 10× SUM_TOL am adjacent-Bein), nicht ein Nachbar-Artefakt.
- Konsequenz-Kette (jetzt numerisch geschlossen): t_cache/t_eig = 8.02 →
  die 78er-Familie hat einen Betriebspunkt-Wechsel zwischen den zwei
  r-Quellen; die Orbit-Invarianz hält in der 1.084e0-Lage (Cache-Quelle)
  auf 6.4e-10, in der 0.195e2-Lage (per-Instanz) auf nur 1.14e-8 — die
  Violation lebt GENAU in der per-Instanz-Quelle, nicht in der Physik.

**Honest-Befund** (Grade B+): der Kollaps ist 17.7-fach, nicht bis auf
numerische Null — 6.4e-10 liegt nur um Faktor 1.6 unter SUM_TOL (ein
Rest an der Toleranz-Kante bleibt sichtbar; unter der Cache-Quelle sind
die Muster-Mediane nicht exakt identisch, weil EPS_PRIMARY 0.25
zeichen-abhaengig in die Eigenwerte koppelt und die Atom-Gleichheit eine
Empirie, kein Theorem ist). Und: KEIN Verdict-Re-Decide — der 045-Verdict
(H_S4_CLOSURE_DEVIATION_FOUND) bleibt committet; die Quellen-Artefakt-
Lesart ist als H-H9-3-Befund DOKUMENTIERT (Prazedenz pt_s4_t5_diag,
Diagnostik non-verdict) und braucht fuer eine Einstufungs-Aenderung ein
eigenes gefrorenes Re-Rechnung-artefakt (0 QPU moeglich).

### C.4 H-H9-4 "Orbit-Atome über n" (T9-Formel-Extrapolation mit Atom-Skala)

**Aussage.** Die daten-abgeleiteten Orbit-Atome (adjacent 1.082954809,
disjunct 1.188107949; max R-dev in Klasse 3.699196504669544e-10; R-Gap
0.10515314008685372) sind die n=4-Kanten einer n-Familie, deren
Muster-Zahlen exakt via T9 laufen (15/45/105 fuer n=4/5/6; adjacent n·C(n−1,2),
disjunct 3·C(n,4)). "Nach den Sternen": die zwei Atome bilden zyklotomisch
skalierte Niveaus — ihr GAP 0.10515 sollte als Funktion von n auf dem
T9-Raster mit der 105er/135er-Erweiterung zusammenpassen (n=5: 105 Muster,
davon adjacent 5·C(4,2)=30, disjunct 3·C(5,4)=15).

**Falsifizierbarer Test (0 QPU):** Offline-Re-Run der T9-Familie bei n=5
(135 Muster) auf derselben S₄-Pipeline-Konvention; vorhersage die R-Mediane
der 30+15 Klassenzugehoerigkeiten a priori (kein Fit) und teste max_within
gegen die 045-Basis-Toleranz 5.8e-11 (Empirie-Basis der Modulkopfs, NICHT
SUM_TOL). **Falsifiziert,** wenn die n=5-Klassen sich nicht in zwei Atome
scheiden, die auf 1e-8 an die n=4-Atome-Rangordnung anknuepfen.

### C.5 H-H9-5 "α-Säule ist effektive Paarzahl" (023-EXT Kombination)

**Aussage.** Die alpha-Kette (Asymptotik-Säule 0.347→0.223, alpha_combined
0.210355, ext-only 0.1326 bei N=65535) folgt der aus der DIRECT gemessenen
Korrelation ρ_ab = 0.573626 abgeleiteten effektiven Paarzaehlung
(effective_total 2.426374) als Grenzwert-Zeile, NICHT einer Freiform-Abnahme.
Kombiniert mit cv-Mean 0.09599648443361233 als konstantem Träger.

**Falsifizierbarer Test (0 QPU, klassisch):** klassischer N-Sweep 10^7 …
10^8 mit v1-Thresholds UNVERÄNDERT; Prädiktion: alpha(N) liegt im Band, das
aus dem fit 0.210(±) + 1/effective_total-Struktur folgt; falsifiziert, wenn
alpha unter das MOCS_ext-Band [0.0864, 0.0882] abfallt, ohne dass omega auf
dem v1-Band bleibt.

### C.6 H-H9-6 "Kalibrier-Epochen-Regime" (V5/035/046 + Fez-Bein-Kette)

**Aussage.** Das V5-re-hd-Bias ist eine Funktion der KALIBRIER-EPOCHE
(Job-Metadaten: last-calibration-Zeitpunkt), nicht der Backend-Identitaet:
035-Kingston +1.20σ, FEZ_RUN1 −1.93σ, FEZ_RUN2 −1.38σ, 046-Kingston −2.22σ.
Die Vier-Messungen muessen konsistent vorzeichen-stabil je EPOCHE sein;
ein Vorzeichen-Flip auf DEMSELBEN Backend (Kingston) zwischen zwei Epochen
ist das registrierte Experiment 046's Zentralbefund und praediziert, dass
DASSELBE Backend in derselben Epoche bei einer 046-Wiederholung
wieder DASSELBE Vorzeichen zeigt (session-stabil, wie die RAM-Q-Residuen).

**Falsifizierbarer Test:** (a) 0 QPU: Korrelation der 4 gemessenen Biases
mit dem Kalibrier-Alter aus den committeten Job-Metadaten (VORZEICHEN-
Konsistenz je Epoche); (b) 046-Fez-Bein (QUEUED, warte auf Raw, cron) unter
dem gefrorenen Prereg (fcf4c2c…): wenn das Fez-Bein in ±2σ-Floor faellt,
ist die Epoch-Lesart CONFIRMED-maessig gestaerkt; wenn ein NEUER
Vorzeichen-Flip (FEZ drittes Vorzeichen oder Kingston in neuer Epoche)
auftaucht, kippt "Backend-Identitaet" endgueltig. Nullanker: der
Mehrvergleich P(≥1 von 4) = 0.102 — die −2.22σ ist UNTER der
Multipl.-Korrektur unauffaellig, deshalb MUSS die Epoch-Lesart die
Vorzeichen-Struktur tragen, nicht die Magnitude.

### C.7 H-H9-7 "q5-Refokussierung ist Gesetzes-Objekt, nicht Fehler-Objekt"

**Aussage.** Der q5-Echo-Anker (fit_kappa_block 0.7314/0.7270, unter
κ̂-Ceiling 0.81) ist session-robust NICHT WEIL der Fehler gross ist, sondern
weil die Tiefen-Struktur des q5-CZ-Baums refokussierend strukturiert ist
(k1/k2/R-Mittelung gruen, nur Rang-Statistik kippt — Struktur der
Echo-Leiter, NICHT der Counts-Gruesse). Praediziert: κ_r8 session-invariant
(C.2), kappa-Block-Fit-Verhalten unter einem SEED-SCAN des Transpiliers
bleibt im Band (der ±1-ulp-Zweig-Differenzen-Report der Phase-11c sagt
761-op-Fingerabdruck mit x-Gate — dieselbe Gate-Familie, KEINE
Primzahl-Signatur).

**Falsifizierbar:** ein seed-Scan (5 Seeds, offline-Aer) der q5-Leiter muss
κ_r8 im Band 0.098 ± 0.004 halten; sonst ist der "Floor" ein
Transpile-Struktur-Artefakt.

---

## D. Steelman-Antithesen (valide, mit Zahlen)

### D.1 SA-H9-1 "κ̂-Tail" — GESTESTET, TOT in Session 2
Die Antithese lautete: der Falsifikator feuert, weil die below-sharp-P die
κ̂-niedrigsten ihrer Bahn sind (S1 q5 spearman −1.000, Raenge 3/4/5) → der
REFUTED könnte ein Rand-Statistik-Artefakt sein. **Session 2 kippt die
Beziehung: spearman +0.100; 467 hat κ̂ 0.8686 (4./5) bei −0.0841, 613 hat
κ̂ 0.8708 bei +0.0768.** Die Antithese ist mit den committeten Daten
GEFAELSCHT — sie stärkt die P-Struktur-Lesart (C.1). (Notiert als
Antithese mit Ergebnis-Pruefung, keine Vertrags-Aenderung.)

### D.2 SA-H9-2 "Residuen sitzen in der ISA/Tiefe"
spearman[res, two_q] = −0.286/−0.258, [res, depth] = −0.341/−0.286 (n=13
Verdict-P): kein Tiefe-Träger. Die session-stabile Komponente ist NICHT
Tiefen-skalierend. (Schwach-Punkt: n=13, keine Kontrollarm-Pair-Korrelation
auf demselben P.)

### D.3 SA-H9-3 "Multiple Comparison −2.22σ"
P(|z|≥2.22) = 0.0264 zweiseitig; P(≥1 von 4 Sessions) = 0.102. Der 046-
Kingston-Bias ist EINZELN jenseits des 2σ-Floors, aber UNTER der
Multiplikations-Korrektur unauffaellig. Die registrierte Lesart darf
VORZEICHEN-Flip nicht Magnitude als Entdeckung buchen — deshalb C.6.

### D.4 SA-H9-4 "Band-Erbfolge" (w_B″ = w_B′)
Das Verdict-Band w_B″ 0.02787029633307472 ist ERBT von Phase 10b (Aer,
3-Job-Kette, SE_BIAS 0.006177172466334955 → 2σ-Floor 0.0124). Es wurde auf
eine andere Session-Struktur (11d, 047) uebertragen OHNE Neukalibrierung.
Antithese: die REFUTED-Selektivitaet misst Teil das Band-Budget, nicht
allein Physik. (Das ist die Registrierungsmotivation fuer C.1-(B)+(C).)

### D.5 SA-H9-5 "γ-ARM-Power"
q5: 5 Kalibrier-Zeilen, resid-SD 0.0239 ≈ Band 0.0279; SE(γ)·c_p ≈ 0.011
(unter Band). Die Zentren-Aenderung ist kleinvolumig, aber die
Kalibrier-Streuung um das gefittete Zentrum IST Band-Groesse: Ein-
Punkt-Entscheidungen am q5-Bein laufen bei 1-3σ der eigenen Arm-Streuung.
Neufit mit n_cal ≥ 16 (C.1-B) ist der registrierte Reparaturweg.

### D.6 SA-H9-6 "Estimator- vs Sampler-Kanal-Mischung"
046 misst mit Estimator (resilience_level 1, DD XX), 047 mit Sampler (DD XX,
8192 Shots), Phase 9/10/11 ebenfalls Sampler. Die REFUTED-Serie mischt
Kanaele mit VERSCHIEDENEN Fehlerkanal-Profilen. Valide Antithese: die
Falsifikator-Menge koennte Kanal-abhaengig sein. Kontrolle (0 QPU): die
047-Sampler-K κ_r8 0.0980 vs 11d-Sampler-κ_r8 0.0982 — GLEICH, obwohl
der BEIN-Kontext Estimator (046) ist: der Floor ist Kanal-stabil,
die Antithese ist GESCHWAECHT, aber die γ-ARM-Divergenz (S1 0.0381 vs
S2 0.0160) kann Kanal-Beimischung nicht ausschliessen.

### D.7 SA-H9-7 "Konstruktions-Spiegel der P-Menge"
Die 26 P (GF(5)/ququint-Ansatz) wurden HAND-picked; der Falsifikator-Muster
{467/547/673} koennte die Konstruktionsvorschrift spiegeln, nicht die RH-
Struktur. Valide bis zur Kontrolle (C.1-C: P-Shuffle der ISA-Zuordnung /
P-zahlensystematische Cluster-Struktur). Diese Antithese ist NICHT mit den
vorhandenen Daten tötbar — sie ist die Registrierungsmotivation fuer
eine Shuffle-Kontrolle im naechsten Freeze.

---

## E. Methodische Schwächen-Register (die dummen und die schlauen)

1. **t_H-Quellen-Asymmetrie in `_config_stats`** (pt_hstar5_execution.py):
   k1/k2/k3 am Cache-t_H, r_median via ratio_stat am per-Instanz-t_H.
   Die 045-Verletzung lebt GENAU hier — C.3-Test 2026-09-29:
   kollabiert 17.7-fach unter die Toleranz (Kriterium erfüllt, B+).
   *Dumm, weil* es ein One-Line-Design-Entscheid war, der die ganze
   H_S4_CLOSURE-Verletzung produzieren kann. *Schlau*, weil die T5-Diagnose
   (Kette Entry→Eigenwert→t_H→r, 4 Glieder auf 0.05 %) es bit-agnostisch
   isolieren konnte.
2. **Namensschuld "r_median"**: `ratio_stat` ist KEIN Median — es ist ein
   K-Ratio AT t_H; der Median kommt spaeter über die 78er-Familie. Jede
   Code-Leserung, die "r_median" als Median per Instanz liest, verwechselt
   die Ebene. Umbenennen waere Re-Name eines committet-Konstanten-Namens —
   nur DOKUMENTIEREN, nicht umbenennen (Freeze-Disziplin).
3. **Band-Wahlkalibrier**: w_B″ = w_B′ (10b Aer), SE_BIAS-Floor aus der
   035-Job-Kette (3 Punkte + Aer-Gauss-SE-Artefakt-Geschichte); kein
   Session-spezifisches Band-Update (D.4).
4. **Probe-b "0.05 %"-Kette ist ein Monotonie-Scale-Check** — die Kette
   FUTTERT die beobachtete l3-Deviation als Eingang; ihr echtes
   Unabhaengig-Teil ist die QUOTIENT-Struktur der 4 Kettenglieder (3.55e-15 →
   2.8e-13 → 2.0e-9 → 1.14e-8), die auf einen nicht-zirkulaeren Vergleich
   gegen die Beobachtung (0.05 %) hinauslauft. Keine unabhaengige
   Bestaetigung der Konstruktion, sondern eine Skalen-Praediktion.
5. **"23 distinkte R"-Ghost** (D64-Doku): eine nicht-reproduzierbare
   Dok-Ziffer in einem aelteren Abschnitt; bleibt unbetrieben, weil die
   D64-Struktur (30 distinkte k-Paare, Burnside 11) es uebernimmt.
   Lehre: Dokumentations-Ziffern brauchen Provenienz-Pin im selben Commit.
6. **Scratch-Bug im Hypergeometrie-Aufruf (dieses Deck)**: erster Lauf
   meldete 0.012821 (= 1/78); korrekt ist 3/78 = 0.0385 (die Funktion
   bekam overlap=2 statt |S1|=3). Korrektur dokumentiert im selben Abschnitt,
   Zahlen im Text sind die korrigierten.
7. **ISA-Determinismus zwischen Sessions**: seed_transpiler 7 → die
   transpilierten Schaltkreise sind Bit-identisch; deshalb ist die
   Session-Struktur der Residuen NICHT ein Blind-Test gegen Transpile-Zweige
   (±1-ulp-Story der Phase 11c bleibt ein Ein-Job-Phaenomen im Artefakt).
   Eine echte P-Shuffle-Control braucht einen NEUEN job mit
   ISAs der gleichen P bei verblocktem seed (registrierbar, 1 Job).
8. **Ein-Job-Auswertungs-Gate mit gepinnten Ausnahmen**: die drei
   Phase-11d-Ausnahme-Punkte (0.0275…/0.0271…/0.0076…) sind GEPINNT statt
   durch eine Toleranz-Erhoehung aufgeloest — das ist Regelkonform, erzeugt
   aber eine "Ausnahmen-Buchfuehrung", die bei einer Session-3-Wertung
   ZU ERST anfaellig fuer still Re-Decide ist. Abhilfe: der gefrorene
   Ausnahmen-BLOCK muss in der Session-3-Auswertung vorgeladen werden
   (vom Prereg-Reader), nicht aus dem Kopf.
9. **Queue-Politik/Determinismus (18 h-Fez-Warte-Auge)**: der 046-Fez-Job
   stand >18 h in einer fast leeren Queue (pending_jobs 2 am offenen Plan,
   kein Job unseres Kontos nach unserem) — die Blockade ist ein fremder
   laufender Job, unsichtbar auf dem offenen Plan. Antithese gegen
   "IBMQ-Priorisierung": wir haben KEINEN Ueberhol-Vorgang in unserem
   Konto, d.h. die 18 h sind NICHT durch unseren Job-Status veranlasst.
10. **Doc-Drift/Claim-Lebenslinien**: claims.py test_count (Live-Recompute)
    + "gerenderte Medien zeigen weiterhin den 046c1cc-Snapshot 642" — die
    Trennung von Live-Zahl und Render-Stand ist die einzige Scharniere,
    die Doc-Nummern von Tests trennen; jede neue Doku-Runde muss beide
    Ziffern nennen (Praxis der letzten 4 Commits, einhalten).

---

## F. Prereg-faehige naechste Pruefungen (Prioritaet, Kosten, falsifizierende Grenze)

| Prio | Pruefung | Kosten | gefrorene Grenze / Kriterium | Anknuepfung |
|---|---|---|---|---|
| 1 | 046-Fez-Bein abwickeln (cron aktiv) | 0 (Job QUEUED) | H-V5R-1/-2 nach Prereg fcf4c2c58…, Bande SE_BIAS 0.00617717…, 2σ-Floor 0.0123543…; KEIN Vektor-Verdict vor beiden Beinen | 046 (C.6) |
| 2 | ~~S₄-Quellen-Einheitlichkeit (C.3)~~ ERLEDIGT 2026-09-29: max_within_unified 6.4239e-10 < 1e-9, Kriterium erfüllt (C.3) | 0 QPU ✓ | Kriterium erfüllt; Follow-up: gefrorenes Re-Rechnungs-Artefakt (0 QPU) für die offizielle 045-Einstufung — KEIN stilles Re-Decide | 045 |
| 3 | s(P)-Offline-Fit an Kalibrier-P beider Sessions + Prädiktion auf Verdict-P | 0 QPU | Band w_B″ 0.02787; falsifiziert, wenn s(P) die Verdict-P nicht in-band vorhersagt | C.1 |
| 4 | P-Shuffle-Kontrolle (1 Job, neues Prereg, gemaeuserte ISA-Geometrie) | 1 QPU-Job | falsifiziert, wenn die Session-Konsistenz mit der ISA/Geometrie wandert statt mit dem P | C.1 / D.7 |
| 5 | Echo-r8-Session-3 (mit jedem neuen RAM-Q-Job, keine Extra-Shots nötig) | 0 Zusatz | κ_r8(q5) 0.098 ± 0.006 beide Sessions bereits; Session-3-Tol 0.004 (C.2) | C.2 |
| 6 | n=5-Atom-Familie offline (T9-Extrapolation, 0 QPU, Stunden) | 0 QPU (CPU) | Atome des n=5-Orbits in der n=4-Rangordnung (C.4) | 045/T9 |
| 7 | N-Sweep 10^7 (023-EXT-Kette) | CPU-Batch | alpha im Band, das aus effective_total 2.426374 folgt (C.5) | 023-EXT |
| 8 | Kalibrier-Ber-Vergrößerung n_cal ≥ 16 (nur Kalibrier-P, keine Verdict-Aenderung) | 1 QPU-Job | RESID-SD am q5-Bein unter 0.01 (D.5) | 047 |

**Hinweis zum Deck-Charakter:** keine der Pruefungen 2-7 aendert ein
committetes Verdict; die 1-QPU-Pruefungen (4, 8) brauchen eigenes
REGISTERED_NOT_MEASURED + Job-Disziplin (ein Job, ISA-Gate vor Submission,
Raw-Commit VOR Auswertung).

## G. Quellen (committet, Lese-Basis dieses Decks)

- Verdicts/Endstand: PLAN.md (Phase 12), §10.30, §Z.29, Commits e8dae59…b5461fc.
- Eval-Artefakte: pt_ram_q_hardware3_eval.json (11d), pt_ram_q_hardware3_eval_rep.json
  (047), pt_ram_q_hardware3_rep_eval.json (Session-Rapport),
  pt_ram_q_hardware2_eval.json (10b), pt_ram_q_isa3_report.json (ISA-Per-Circuit),
  pt_s4_closure_theorem_results.json (045), pt_s4_t5_diag_results.json.
- Prereg-Kette: pt_ram_q_hardware3_rep_prereg.json (047),
  pt_v5_kingston_rep_prereg.json (046, md5 fcf4c2c58837bb7188c4e029d1841214),
  pt_ram_q_hardware3_prereg.json (11), pt_s4_closure_theorem prereg (045).
- Scratches (dieses Deck, 0 QPU): scratches/h9_ramq_sessions.py (+ out.json),
  scratches/h9_s4_source_unified.py (+ h9_s4_source_unified_out.json —
  Kopie des Job-tmp-Ergebnisses 2026-09-29; das Run-Log bleibt im Job-tmp,
  `*.run.log` ist .gitignore'd).

**Endnote (Bewertung):** H-H9-1 ist der einzige Befund dieses Decks, der
eine NEUE Struktur annimmt (Grade: Empirie, noch keine Verdict-Faehigkeit —
D-Basis: die Session-Konsistanz ist eine 2-Punkte-Messreihe pro P; ohne
Shuffle-Kontrolle (D.7) ist apophenisches Lesen nicht ausgeschlossen —
SciMind-4.0-Regel ex ante anwendbar). Alle uebrigen Hypothesen/Antithesen
sind Re-Lesungen committeter Zahlen mit ex-ante-Kriterien.