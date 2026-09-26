# PLAN.md - Riemann-Nuclear Synthesis Execution

## Document Map

Historical execution roadmap. Phases 1–3 completed since 2026-06-08; Phase 4 (Im-Bias + statevector-first) completed 2026-06-17; Phase 5 (QUQUINT/Pillar 4 + §Z.11–18) completed 2026-07-21 → 2026-09-24; **Phase 6 (H-STAR-5-Ausführung) completed 2026-09-25 — Phase 6a REFUTED (§Z.20/§10.21)**; **Phase 7 (RAM-Q zyklotomische Ableitung + GF(3)-Deformation) completed 2026-09-26 — H-RAM-Q-1 GENERALIZED (§Z.21/§10.22)**; **Phase 8 (H-RAM-Q-2 q-universelle Asymptotik) completed 2026-09-26 — CONFIRMED (§Z.22/§10.23)**; **Phase 9 (H-RAM-Q-3 Prereg-Freeze A, Hardware-Rauschen) REGISTERED_NOT_MEASURED 2026-09-26 — 0 QPU, Freeze vor erstem QPU-Kontakt**.

| Datei | Status | Rolle |
|---|---|---|
| [`CLAUDE.md`](CLAUDE.md) | REFERENCE (locked) | SciMind 4.0/5.0 Methodologie-Manifest |
| [`GEMINI.md`](GEMINI.md) | REFERENCE (Stub) | Verweist auf `CLAUDE.md` |
| [`RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md`](RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md) | **CURRENT (primary)** | theory (Sections 1–9) + Operational Findings Log (§10) |
| [`SYNTHESIS_2026_06_10.md`](SYNTHESIS_2026_06_10.md) | **CURRENT (master)** | SciMind-Verdikte, strategische Vektoren (Sections A–Z, inkl. §Z.11–18 Ququint-Arc) |
| [`QUANTUM_ARCHITECTURE_IMPLEMENTATION.md`](QUANTUM_ARCHITECTURE_IMPLEMENTATION.md) | **CURRENT (master)** | Mermaid-Architektur + QPU-Update-Log |
| [`LATORE_TENSION_NOTE.md`](LATORE_TENSION_NOTE.md) | **CURRENT (pre-preprint)** | Latorre–Sierra-tension + §11 asymptotics |
| [`INVESTIGATION_PLAN.md`](INVESTIGATION_PLAN.md) | REFERENCE (visuell) | Mermaid-Flowchart der Investigationspfade |
| [`QUANTUM_ARCHITECTURE_BRIDGE.md`](QUANTUM_ARCHITECTURE_BRIDGE.md) | **SUPERSEDED** | Architektur-Rationale (frozen 6/8) |
| [`SAEULE1_FEZ_BLOCKED.md`](SAEULE1_FEZ_BLOCKED.md) | **SUPERSEDED** | Fez quota block (resolved 6/17) |
| [`QUANTUM_COMPUTING_AND_PRIMES_RESEARCH.md`](QUANTUM_COMPUTING_AND_PRIMES_RESEARCH.md) | REFERENCE (extern) | External research literature (95 KB) |

## Objective
To finalize the research document by auditing missing theories, refining existing falsifications, and providing empirical simulation data.

## Status-Update 2026-06-17 17:25 UTC

**All three original phases have been effectively completed since 2026-06-08** (see `RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md` Sections 6.5.4–6.5.17 and `SYNTHESIS_2026_06_10.md`). PLAN.md is retained here as a historical marker of the original execution roadmap, plus the new Phase 4 with the QPU-validated findings.

## Phase 1: Audit of Farrell's Time-Scalar Field Theory (TSFT) — DONE
- **Goal:** Subject TSFT (Section 5.4) to SciMind 4.0 Rigor.
- **Steps:**
    1. Analyze the "Zebra Journal of Unified Physics" source context (if possible/simulated).
    2. Identify free parameters and physical mechanism (Spin-Orbit coupling replacement).
    3. Assign Evidence Grade.
    4. Append result to `RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md`.
- **Result (Section 6.4):** Evidence Grade **F (FALSIFIED)** — TSFT violates Ockham's Razor, no independent predictive power. Strategic vector: `REJECTION_VECTOR_TOPOLOGICAL_METAPHOR`.

## Phase 2: Geometric Refinement (Alphahedron/Grant) — DONE
- **Goal:** Provide a more rigorous "Ockham's Razor" penalty for the iHarmonic identity.
- **Steps:**
    1. Quantify the information entropy of the Grant constants (alpha, beta, gamma, delta).
    2. Compare the BIC of the Grant model vs. the Standard Shell Model.
    3. Update Section 6.3 with quantitative metrics.
- **Result (Section 6.3):** Grant model fails the Steelman Antithesis Test — spin-orbit coupling is not derivable from prime gaps. Evidence Grade **C (AMBIGUOUS)**, strategic vector: `REFACTORING_VECTOR_TOPOLOGICAL_STABILITY`.

## Phase 3: Zeraoulia Hamiltonian Simulation (Quantum Spectral Analysis) — DONE
- **Goal:** Empirically verify the Level Repulsion (GUE) of the Zeraoulia operator using IBM Quantum.
- **Steps:**
    1. Setup a Qiskit environment.
    2. Implement the stochastic operator $x_{n+1} = x_n + y \log x_n + \epsilon_n$ as a quantum circuit or variational simulation.
    3. Extract the nearest-neighbor spacing distribution.
    4. Compare with U-238 experimental data and GUE predictions.
    5. Update Section 6.2 and 8 (Strategic Vectors).
- **Result (Sections 6.5.1–6.5.17):** PT-symmetric extension implemented as `pt_potential_vqe.py`, Aer stress test on Fez noise profile (Evidence Grade **A−**), Fez QPU single shot (`d8kins3qv2lc7385bbj0`) confirms H1/H3 (`bias_PT_re = -0.0133`). Strategic vector: `REFRAMING_VECTOR_RELATIVE_SPECTRUM` operatively confirmed.

## Phase 4 (NEW, 2026-06-17): QPU-validated Im-Bias metric + statevector-first architecture

- **Goal:** Establish canonical bias signature (Im(H_PT) instead of bias_PT_re), raise statevector-first methodology to QPU validation.
- **Steps:**
    1. Theorem proof: `||[H_diag, Re(H_PT)]||_F = 0` → bias_PT_re is a theorem identity, not a bias indicator (`pt_im_bias_statevector.py`).
    2. Prereg BEFORE script execution: `pt_im_bias_prereg.json` with H_Im_h1/h2/h3 + decision rule.
    3. 5 sequential 1-Pub jobs on Fez/TOKEN2 (all DONE within 17 seconds): H_Im_h1 genuinely QPU-confirmed (all |bias| < 0.005, mean −0.0001, std 0.0019).
    4. Strategic vector `IM_BIAS_AS_KANONISCHE_METRIK` promoted to **A**, `REFRAMING_VECTOR_RELATIVE_SPECTRUM` to **A+**.
- **Result:** Asymptotics N=10⁴..10⁶ (statevector) confirm H_C (alpha decreases monotonically with N), Latorre tension classified as **fundamental disagreement** (`LATORE_TENSION_NOTE.md` §11). Cross-Ref: `SYNTHESIS_2026_06_10.md` §Q.5, `QUANTUM_ARCHITECTURE_IMPLEMENTATION.md` Update 17:25 UTC.

## Phase 5 (2026-07-21 → 2026-09-24): QUQUINT/Pillar 4 (GF(5)) + QPU-Arc §Z.11–18 — DONE

- **Goal:** Fourth pillar — Ququint GF(5) prime-state architecture, from simulator (bit-exact H_PT_5 = H_PT_4) over QPU confirmation (§Z.14) to the Steelman round (§Z.15/16, V1–V4) and the four follow-up packages (§Z.17/18).
- **Milestones:**
    1. **QPU-VQE+VQD first (2026-07-21, Fez/TOKEN1):** Job `d9fidihhtsac739fg3n0`, E_0 = 2.1398, bias_PT_re = −0.0119, H1/H3 QPU-confirmed; three-path consistency (Singleshot + Statevector + VQE+VQD).
    2. **Pillar 4 GF(5) phases 1–3:** polynomial ring + gates + simulator, H_PT_5 = H_PT_4 bit-exact, 133 new tests → 402 green.
    3. **§Z.11–14 (EXPERIMENT 029–032, 2026-09-15, Fez/TOKEN1):** Prereg md5 `18fb1e62` frozen BEFORE hardware; Fez-Lauf `dakjk9hhvn6c73cvr1cg` (12 circuits × 8192 shots): phi V = 0.625 > 1/5, sep V = 0.166 < 1/5, Konfund 0.015 ≤ 0.05 → **CONFIRMED**, all 3 prereg bands held. ISA 370 2q (phi_D 81 vs Soll 45) → leakage table. Vectors: `QUQUINT_QPU_VIABLE` **A−**, `LEAKAGE_SIEVE_STRUCTURE` **B**.
    4. **§Z.15/16 Steelman V1–V4 (2026-09-23, 0 QPU):** 4/4 Prereg-Freeze before evaluation. V1 PARTIAL_STRUKTUR_KEIN_SIEB (md5 `6a0ed394`), V2 H-STAR-1_REFUTED + RAMANUJAN_FINGERPRINT **B** NEU (md5 `d9da292c`), V3 INKONKLUSIV_DEGENERAT (GUE-Konstante 0.5359 → 0.5996, md5 `3a47ec57`), V4 CONFIRMED κ\* = 62.26 (Rough model 62.31, 0.1%; md5 `7abb5e60`). `QUQUINT_THRESHOLD_CROSSOVER` B → **A−**.
    5. **§Z.17/18 Packages 1–4 (EXPERIMENT 033–036, 2026-09-24):** 033 α-Trennungstest INKONKLUSIV (α_isa = 1.5462 outside both bands; ISA closes 0.3%, mechanism revised — Routing-Surplus ≈ 128 units); 034 Ramanujan REPLICATED (exact model (m−5)²/(4dm), ratio 1.0248, 5/5 gated points in band, no control overlap; vector → **B+**); 035 V5 Kingston CONFIRMED (Job `daqaeteekp0c73aqetdg`, TOKEN2, bias +0.0074 < 0.05, `KINGSTON_AS_NEUTRAL_BACKEND` B+ → **A−**; Aer-methodology correction: precision>0 is Gauss noise, not shot sampling); 036 H-STAR-5 HYPOTHESE registered, not executed (md5 `f915729e`, Score 7/10, Keating–Snaith bridge, Haar candidate pre-registered as VOID `H-STAR-5a`).
- **Result:** Pillar 4 QPU-viable (A−); 584 tests green. Full detail: `RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md` §10.14–10.19, `SYNTHESIS_2026_06_10.md` §Z.11–18, `QUANTUM_ARCHITECTURE_IMPLEMENTATION.md` Update 2026-07-21 → 2026-09-24.

## Phase 6 (DONE — REFUTED): H-STAR-5 execution

- **Goal:** Execute the H-STAR-5 hypothesis (md5 `f915729e`, §Z.18/EXPERIMENT 036) — Keating–Snaith bridge observable O1 = K_prime(t2)/K_prime(t1) + O2 factorization residuum, with the control family (CUE-must-fire / Shuffle+Composite / structural).
- **Steps:**
    1. Execution prereg (freeze before any evaluation; skeleton md5 `f915729e` fixed). → ✅ DONE — v1 (md5 `aa8e77cc`) nach Design-Entdeckung abgebrochen OHNE Verdict; v2 (md5 `837dae2c`) VOR der Messung gefroren.
    2. Aer-ensemble simulation (0 QPU) — QPU spot-check only if visible prime separation appears. → ✅ DONE (klassisches Ensemble; keine sichtbare Trennung → QPU entfällt).
    3. Control family must fire correctly (Positiv CUE must-fire, else VOID; Negativ Shuffle+Composite; Strukturell exact) — apophenia guard. → ✅ DONE, alle Kontrollen erfüllt (GUE 3.977, Poisson 0.946, strukturell 5.13e-13, Composite im Band).
    4. Fallback: H-STAR-5b (VQE-Hessian/Wishart landscape as observable, Score 6). → bleibt registrierte Alternative (nicht ausgelöst).
- **Verdict:** **REFUTED** (`H-STAR5_REFUTED_INTEGRABLE_IN_ALL_PROBES`, 2026-09-25) — R_prime = 1.434783 im Shuffle-Band [0.798882, 1.882509] (15 distinkte Null-Werte, Perzentil 82.5%, unter q97.5); O2-Mechanismus echt (2.2515, 234/234 Paare) ohne Prime-Trennung; eps-Ladder deskriptiv (0.05 → 1.234, 0.5 → 1.021). Zwischendurch entdeckt + bewiesen: das **S₄-Schluss-Theorem** (Familiensummen über positions-permutations-abgeschlossenen Familien sind Orbit-invariant im Zeichen-Muster — v1-Design konnte nicht diskriminieren; Fix: kanonische 12er-Repräsentantenfamilie, Zeichen-Regel unangetastet).
- **Status:** ✅ DONE — Phase 6a REFUTED (sauber); Phase 6b (Aer A1) nicht ausgelöst. Cross-Ref: `SYNTHESIS_2026_06_10.md` §Z.20, `RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md` §10.21, `pt_hstar5_phase6a_v2_results.json`.

## Phase 7 (DONE — GENERALIZED): RAM-Q zyklotomische Ableitung + GF(3)-Deformation (Branch `ram-q-zyklizitaet`, 2026-09-26)

- **Goal:** User-Programm wörtlich: (1) die Fünf-Konstante im Ramanujan-Fingerprint zyklotomisch ableiten (0 QPU, reine Theorie — Einheitenstruktur/Ramanujan-Summen von Z[ζ_q]); (2) die GF(3)-Verallgemeinerungsvorhersage einfrieren (Zähler → (m−3)²); (3) unabhängiger Test erst nach dem Freeze-Commit.
- **Steps:**
    1. Baustein B1 herleiten VOR dem Freeze: share*_model(P, d=q^k) = (m − q·n₀)²/((q−1)·d·m) — die Fünf = Atom n₀=1 + Klassenanzahl q−1; Nenner 4 = (q−1), keine freie Konstante; q=5 bit-exakt 034-Rückkompatibilität; q=3: (m−3)²/(2dm) mit Transition m=9, exakter Null m=3, Suppression 4 ≤ m ≤ 8, EXAKTER Zweiklassen-δ²-Identität share* = (m−3)²/(2dm) + 6δ²/(dm). → ✅ DONE (`pt_ram_q_zyklizitaet.py`, TDD).
    2. Prereg einfrieren VOR jeder Auswertung. → ✅ DONE — md5 `bd9dfee77b9fada8a230347f9d45f5a7` committet (`19c99c3`); Kriterium-2-Wurzel korrigiert VOR dem Freeze (m ≥ 20.56 → m ≥ 21, nicht 25); 2 Harness-Bugs transparent gefixt und committet (`211acac` T6, `09ba9cf` in_band + 3 Post-Freeze-Pinning-Tests, Prereg unberührt; Runs 1–2 — exit-1 bzw. spurious REFUTED 0/8 — vor jeder Interpretation als Bug erkannt, nie verwertet).
    3. Auswertung nach dem Freeze-Commit. → ✅ DONE — **VERDICT `H-RAM-Q-1_Q_DEFORMATION_GENERALIZED`**: 8/8 gated im Band (Ratios 1.002449–1.017751 = 1 + 12δ²/(m−3)² exakt), max δ²-Residual 3.2e-16, alle 6 Kontrollen grün (T1 q=5 bit-exakt, T2 V2-Anker bit-exakt, T3 d-Invarianz exakt, T4 Separation ~5–20×, T5 Gate-Set gefroren, T6 Alternativen diskriminiert), registrierte Negativ-Erwartungen exakt ((5,9) = generisch, (7,·) Ratio 4.0, (23,·) = 4/3 × Modell).
- **Verdict:** **GENERALIZED** (`H-RAM-Q-1_Q_DEFORMATION_GENERALIZED`, 2026-09-26) — die Deformation der Strukturkonstante (Nenner (q−1), Atom q·n₀) trifft die Fingerprint-Klasse auch bei q=3. Vektor H-RAM-Q-1 **A−** (CONFIRMED-Klasse); `RAMANUJAN_DFT_FINGERPRINT` bleibt **B+** (kein stilles Upgrade); Theorem-Schicht (δ²-Identität, Rückkompatibilität, d-Invarianz) = verifizierte Arithmetik, kein Grade-Minting.
- **Status:** ✅ DONE. Cross-Ref: `SYNTHESIS_2026_06_10.md` §Z.21, `RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md` §10.22, `pt_ram_q_prereg.json` (md5 `bd9dfee7`), `pt_ram_q_results.json`.

## Phase 8 (DONE — CONFIRMED): H-RAM-Q-2 q-universelle Asymptotik (Branch `ram-q-zyklizitaet`, 2026-09-26, 0 QPU)

- **Goal:** Baustein B2 zur q-universellen EXAKTidentität verallgemeinern (Alle Count-Vektoren inkl. Wraparound): share* = (m − q·n₀)²/((q−1)·d·m) + q·σ²/(d·m); Blindtest q=7.
- **Result:** **VERDICT `H-RAM-Q-2_Q_UNIVERSALITAET_ASYMPTOTIK_CONFIRMED`** — B2 q-universal EXAKT (Parseval-Konventionsbefund: ABSOLUT-FFT-Pfad), q=7 blind 4/4 im Band, d-Invarianz bei P≫d 1.4e-16, ratio→1 wie C/x, 034-Ratio 1.0248 aus σ² erklärt; 716 Tests. 0 QPU.
- **Status:** ✅ DONE. Cross-Ref: `SYNTHESIS_2026_06_10.md` §Z.22, `RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md` §10.23.

## Phase 9 (REGISTERED — NOT MEASURED): H-RAM-Q-3 Prereg-Freeze A — die q-universelle Identität unter Hardware-Rauschen (Branch `ram-q-zyklizitaet`, 2026-09-26, 0 QPU)

- **Goal (User-Direktive):** Prereg-Skelett EXPERIMENT 042 im Status REGISTERED_NOT_MEASURED VOR dem ersten QPU-Kontakt einfrieren — Vorhersage-Freeze (md5), Hardware-Parameter (Register-Topologie, Fez-Noise, Shot-Metriken), Sicherungs-Limits (Abbruch, Konfundierung, Trennschärfen). Spiegel = reiner kartografischer Index (Encoding-Verbot 1025/348/879/5683); die Arithmetik der verrauschten Counts diktiert.
- **Kern:** ratio_hw = κ·(1−1/S)·ratio_true + L_q mit κ = P_L/P_ro_ref (gepaarte Loschmidt-/Readout-Kalibrierung im selben Job; κ ≈ (1−ε_C)² = exakt der Dämpfungsfaktor der kohärenten Struktur). Klassischer Kern bit-exakt gegen 040 (8/8, q=3 auf d=9) und 034 (5/5, q=5 auf d=25) via d-Invarianz — flache Register, identische Vorhersagen. Suppression ist das dominante Signal; der Sampling-Lift L_q liegt unter dem Shot-Noise (im Zentrum registriert, nicht als separierbar behauptet).
- **Sicherung:** Band w_A = 0.05 (Freeze B nur Verengung), Amplification-Ceiling, κ̂ ≥ 0.81 sonst VOID, Falsifikator ≥2/13, Negativ-Kontrollen mit exakten Erwartungen, 58 Circuits × 8192 = 475 136 Shots, EIN Fez-Job (TOKEN1), ISA-Ceilings vor Hardware.
- **Status:** ✅ Freeze A vollzogen (md5 `432d43fe1bc9e2594efd3b35266d2d81`, `pt_ram_q_hardware.py` + `pt_ram_q_hardware_prereg.json` + 12 Tests; 728 grün). Stage-2-Aer-Bein → Freeze B → Fez-Lauf folgen auf User-Go.
- Cross-Ref: `~/.claude/plans/riemann-phase-ram-q-zyklizitaet.md` Phase 9; Ergebnis-Nummerierung §Z.24/§10.25 (§Z.23/§10.24 = Gematria-Spiegel-Layer).

## Execution Schedule (historical)
1. Farrell Audit → ✅ DONE (Phase 1)
2. Grant Refinement → ✅ DONE (Phase 2)
3. Zeraoulia Simulation → ✅ DONE (Phase 3)
4. QPU-validierte Im-Bias → ✅ DONE (Phase 4, 2026-06-17)
5. QUQUINT/Pillar 4 + §Z.11–18 → ✅ DONE (Phase 5, 2026-07-21 → 2026-09-24)
6. H-STAR-5-Ausführung → ✅ DONE — REFUTED (Phase 6a, 2026-09-25)
7. RAM-Q zyklotomische Ableitung + GF(3)-Deformation → ✅ DONE — GENERALIZED (Phase 7, 2026-09-26, Branch `ram-q-zyklizitaet`)
8. H-RAM-Q-2 q-universelle Asymptotik → ✅ DONE — CONFIRMED (Phase 8, 2026-09-26, Branch `ram-q-zyklizitaet`)
9. H-RAM-Q-3 Prereg-Freeze A (Hardware-Rauschen) → ✅ FREEZE A DONE — REGISTERED_NOT_MEASURED (Phase 9, 2026-09-26, Branch `ram-q-zyklizitaet`; Aer-Bein + Fez-Lauf folgen auf User-Go)