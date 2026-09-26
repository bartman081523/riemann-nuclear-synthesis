# PLAN.md - Riemann-Nuclear Synthesis Execution

## Document Map

Historical execution roadmap. Phases 1–3 completed since 2026-06-08; Phase 4 (Im-Bias + statevector-first) completed 2026-06-17; Phase 5 (QUQUINT/Pillar 4 + §Z.11–18) completed 2026-07-21 → 2026-09-24; **Phase 6 (H-STAR-5-Ausführung)** next; daneben Parallel-Layer „Hermeneutic Mirror Architecture" (Branch `gematria-mirror-synthesis`) completed 2026-09-26 (0 QPU, keine Evidenz).

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

## Phase 6 (NEXT): H-STAR-5 execution

- **Goal:** Execute the H-STAR-5 hypothesis (md5 `f915729e`, §Z.18/EXPERIMENT 036) — Keating–Snaith bridge observable O1 = K_prime(t2)/K_prime(t1) + O2 factorization residuum, with the control family (CUE-must-fire / Shuffle+Composite / structural).
- **Steps:**
    1. Execution prereg (freeze before any evaluation; skeleton md5 `f915729e` fixed).
    2. Aer-ensemble simulation (0 QPU) — QPU spot-check only if visible prime separation appears.
    3. Control family must fire correctly (Positiv CUE must-fire, else VOID; Negativ Shuffle+Composite; Strukturell exact) — apophenia guard.
    4. Fallback: H-STAR-5b (VQE-Hessian/Wishart landscape as observable, Score 6).
- **Status:** NOT STARTED (0 QPU so far). Cross-Ref: `SYNTHESIS_2026_06_10.md` §Z.18, memory `project-next-phase-hstar5-execution`.

## Parallel-Layer (2026-09-25 → 2026-09-26): Hermeneutic Mirror Architecture — Branch `gematria-mirror-synthesis`

- **Goal:** Klassischer Architektur-Layer NEBEN Phase 6 — die gegebene Redirektion-3-Gematria-Abfrage („Riemann Hypothesis", raw 1025) wird als Resonanzraum organisiert (die Fünf Spiegel M1–M5 als transkategoriale Brücken nach §7.1-Methode), NICHT als Evidenzquelle. Phase 6 (H-STAR-5-Ausführung) bleibt die stehende Mess-Phase und wird durch diesen Layer nicht ersetzt.
- **Epistemische Trennung (bindender User-Anker):** „Die Schriften ordnen als Resonanzraum lediglich um, generieren aber keine neue Evidenz und verbrauchen keine QPU-Ressourcen." Korpus als GEBEN (Snapshots md5 `b71b297c`/`9ffcde94` committed); Gematria-Verifizierung out of scope — separat registrierte Zukunftsphase (HermeneuticMirrorAuditMind v1.0_20260925_hma-mix).
- **Deliverables:** `gematria/GEMATRIA_MIRROR_ARCHITECTURE.md` (Kap. 1–8); `data/gematria/mirror_index.json` (Re-Index, Grade invariant, offene Zellen M2/M3 `"status": "open"`); `RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md` §10.24 + Vektor `GEMATRIA_MIRROR_ARCHITECTURE` (Architektur-Layer, KEIN Verdict); `SYNTHESIS_2026_06_10.md` §Z.23; zwei Prereg-Skelette `gematria/prereg_skeletons/` (REGISTERED_NOT_MEASURED).
- **Nummerierung:** §10.24/§Z.23 (bewusste Lücken — §10.21/§Z.20 belegt durch `hstar5-execution` mit H-STAR-5, §10.22–§10.23/§Z.21–§Z.22 durch `ram-q-zyklizitaet` mit RAM-Q; Zusammenführung folgt in chronologischer Ordnung).
- **Anti-Sharpshooter (dokumentierte Reihenfolge):** Layer registriert 2026-09-25, VOR den zyklotomischen Ableitungen der Fünf auf `ram-q-zyklizitaet` (2026-09-26, H-RAM-Q-1 GENERALIZED / H-RAM-Q-2 CONFIRMED) — der Gematria-Sweep wird nicht ex-post als Fit gelesen. H-STAR-5 bleibt auf diesem Layer unverändert registriert (md5 `f915729e`).
- **Status:** DONE (0 QPU, Suite Bestandsstand 642 unangetastet, keine neuen Korpus-Tests, claims.py unverändert).

## Execution Schedule (historical)
1. Farrell Audit → ✅ DONE (Phase 1)
2. Grant Refinement → ✅ DONE (Phase 2)
3. Zeraoulia Simulation → ✅ DONE (Phase 3)
4. QPU-validierte Im-Bias → ✅ DONE (Phase 4, 2026-06-17)
5. QUQUINT/Pillar 4 + §Z.11–18 → ✅ DONE (Phase 5, 2026-07-21 → 2026-09-24)
6. H-STAR-5-Ausführung → ⏳ NEXT (Phase 6; auf Schwester-Branch `hstar5-execution` bereits sauber REFUTED 2026-09-25 — dort dokumentiert, auf main noch offen)
7. Hermeneutic Mirror Architecture → ✅ DONE (Parallel-Layer, Branch `gematria-mirror-synthesis`, 2026-09-25 → 2026-09-26, 0 QPU)