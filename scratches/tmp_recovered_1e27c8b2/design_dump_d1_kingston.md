# D1 Kingston-Substrat-Bein (H-RAM-Q-6 / EXPERIMENT 050) — Design-Dump 2026-10-02

## Grundlagentatsachen aus dem Code (verifiziert)
- `pt_ram_q_hardware3_eval.evaluate(raw_path, stage3_path, isa_path)` ist FEZ-agnostisch —
  es prueft nur: raw["transpile"] == {optimization_level/seed_transpiler/isa_2q_total/
  isa_2q_max} == isa-Gate-Werte, isa["verdict"]=="ISA_OK", n_circuits==116, counts_md5,
  t3/t4/t5/t6 Kontrollen. Ein Kingston-ISA-Gate mit demselben Schema laesst den GEFRORENEN
  Eval unveraendert laufen (kein Gesetzes-Fork).
- `h3a.build_hardware_circuit_set()` (pt_ram_q_hardware3_aer.py) liefert denselben 116er
  Namens-/Kind-Set auf jedem Backend; die 26 (P,arm)-Injektionen kommen aus dem GEFRORENEN
  Payload pt_ram_q_hardware3_prereg.json (baaca1f6) — Punkte werden NICHT neu gerechnet.
- TOKEN2-Mechanik nach Haus-Muster: `pt_v5_kingston._make_service()`
  (QiskitRuntimeService, channel ibm_quantum_platform, token IBMQ_TOKEN2 aus .env,
  instance "open-instance", BACKEND ibm_kingston). TOKEN1 bleibt der Fez-Pfad,
  in diesem Bein wird NUR TOKEN2 gelesen, Token nie echo/commit.

## Neue Artefakte (nummerierte Iteration unter NEUEM Freeze)
- pt_ram_q6_kingston.py — Modul: Experiment-Konstanten, Prereg-Bauer + Freeze/Loader,
  ex-ante-Leg-Mathematik (Spearman+Permutations-Null, Vorzeichen-Binomial, Eligibility).
- pt_ram_q6_kingston_prereg.json — Freeze (REGISTERED_NOT_MEASURED), Legs L1/L2/L3,
  geerbtes Verdict als REGISTERTE Sekundaer-Lesart.
- pt_ram_q6_kingston_isa_stage.py — 0 QPU: transpiliert die 116 GEFRORENEN Circuits
  auf ibm_kingston (opt_lvl 3, seed 7) -> Gate-Artefakt (vom Eval-Schema validiert).
- pt_ram_q6_kingston_qpu.py — der EINZIGE QPU-Griff (EIN Kingston-Job, 116x8192 Shots,
  DD XX, raw counts, counts_md5, Commit VOR Auswertung; transpile-Totals aus dem
  committed Gate, NIE hartkodiert; ISA-Gate-vs-aktuelle Transpile Kreuzcheck
  vor Submission).
- pt_ram_q6_kingston_eval.py — ruft zunaechst pt_ram_q_hardware3_eval.evaluate() mit dem
  Kingston Raw (geerbtes Verdict, 044-Gesetz), bildet DANACH die ex-ante-Legs gegen
  S1 (11d) + S2 (047) und schreibt pt_ram_q6_kingston_eval.json (eigenes D1-Verdict).
- tests/test_pt_ram_q6_kingston.py — md5/Schema/Einheiten.

## Ex-Ante-Legs (VOR Messung registriert)
- L1 Substrat-Kohaerenz: Spearman ρ(res_Sx, res_K) ueber die 13 Holdout-P (x ∈ {S1,S2});
  Null = Permutation von res_K (2000 draws, seed S1 20261006 / S2 20261007), Schranke
  q95 der |rho|-Null; BEIDE Legs muessen q95 ueberschreiten.
- L2 Vorzeichen-Stabilitaet: rohe Vorzeichen-Gleichheit res_Sx vs res_K ueber ALLE 13;
  exakt einseitiger Binomial-p (H0: gleiche Chance) <= 0.05 (d.h. >= 10/13 pro Leg).
  Praezedenz-Basis S1<->S2: 11/13 roh, 9/9 eligible bei |res| >= 0.01 (§Z.29).
  Eligible-Lesarten (roh, |res_S1|>=0.01, Vereinigungskriterium) als Zweit-Lesare.
- L3 kappa-Floor-Union ueber 26 Kingston-Injektionen (geerbtes VOID-Kriterium
  n_kappa_low_union >= 2) + DIAGNOSTIK Spearman(κ̂_K, κ̂_S1) (NICHT verdict-tragend).
- Verdict-Ordnung: DEGENERAT (Kontrollen des geerbten Eval nicht gruen) ->
  VOID_SUBSTRAT (L3-Union fehlt) -> D1_REFUTED_SUBSTRAT_SPEZIFISCH -> D1_PARTIAL ->
  D1_CONFIRMED_SUBSTRAT_UNIVERSAL. Kein Re-Decide von S1/S2; das geerbte Verdict
  dokumentiert nur, ob die 044-REFUTED-Struktur auf dem anderen Substrat wiederkommt.

## Registrierte Erwartung (NICHT verdict-tragend)
S1<->S2 Praezedenz ρ = 0.8956; Echo-Kanal-Dominanz (res~delta_cal ~ −0.985 beide Arme)
legt nahe, dass ein drittes Substrat denselben Kanal widerspiegelt — Grade B−-Kandidat
bleibt die Session-stabile P-Struktur (§Z.30), NICHT eine "neue Arithmetik" (E/F, §10.31).

## Disziplinae
Raw committed VOR Auswertung; Prereg-md5 im Modul gepinnt; Job-ID sofort persistiert
(resume contract); KEIN kappa/ratio/gamma/verdict im Raw; Toleranz nie erhoeht;
Doku-Ketten §10.33/§Z.32 erst NACH Verdict mit committeten Zahlen.