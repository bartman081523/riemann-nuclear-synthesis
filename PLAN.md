# PLAN.md - Riemann-Nuclear Synthesis Execution

## Document Map

Historische Execution-Roadmap. Phases 1–3 seit 2026-06-08 abgeschlossen; **Phase 4 (Im-Bias + statevector-first)** seit 2026-06-17 aktiv.

| Datei | Status | Rolle |
|---|---|---|
| [`CLAUDE.md`](CLAUDE.md) | REFERENCE (locked) | SciMind 4.0/5.0 Methodologie-Manifest |
| [`GEMINI.md`](GEMINI.md) | REFERENCE (Stub) | Verweist auf `CLAUDE.md` |
| [`RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md`](RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md) | **CURRENT (primary)** | Theorie (Sections 1–9) + Operational Findings Log (§10) |
| [`SYNTHESIS_2026_06_10.md`](SYNTHESIS_2026_06_10.md) | **CURRENT (master)** | SciMind-Verdikte, strategische Vektoren (Sections A–Q) |
| [`QUANTUM_ARCHITECTURE_IMPLEMENTATION.md`](QUANTUM_ARCHITECTURE_IMPLEMENTATION.md) | **CURRENT (master)** | Mermaid-Architektur + QPU-Update-Log |
| [`LATORE_TENSION_NOTE.md`](LATORE_TENSION_NOTE.md) | **CURRENT (pre-preprint)** | Latorre–Sierra-Spannung + §11 Asymptotik |
| [`INVESTIGATION_PLAN.md`](INVESTIGATION_PLAN.md) | REFERENCE (visuell) | Mermaid-Flowchart der Investigationspfade |
| [`QUANTUM_ARCHITECTURE_BRIDGE.md`](QUANTUM_ARCHITECTURE_BRIDGE.md) | **SUPERSEDED** | Architektur-Rationale (frozen 6/8) |
| [`SAEULE1_FEZ_BLOCKED.md`](SAEULE1_FEZ_BLOCKED.md) | **SUPERSEDED** | Fez-Kontingent-Block (resolved 6/17) |
| [`QUANTUM_COMPUTING_AND_PRIMES_RESEARCH.md`](QUANTUM_COMPUTING_AND_PRIMES_RESEARCH.md) | REFERENCE (extern) | Externe Forschungs-Literatur (95 KB) |

## Objective
To finalize the research document by auditing missing theories, refining existing falsifications, and providing empirical simulation data.

## Status-Update 2026-06-17 17:25 UTC

**Alle drei ursprünglichen Phasen sind seit 2026-06-08 faktisch abgeschlossen** (siehe `RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md` Sections 6.5.4–6.5.17 und `SYNTHESIS_2026_06_10.md`). PLAN.md wird hier als historischer Marker der ursprünglichen Execution-Roadmap beibehalten, plus die neuen Phase 4 mit den QPU-validierten Befunden.

## Phase 1: Audit of Farrell's Time-Scalar Field Theory (TSFT) — DONE
- **Goal:** Subject TSFT (Section 5.4) to SciMind 4.0 Rigor.
- **Steps:**
    1. Analyze the "Zebra Journal of Unified Physics" source context (if possible/simulated).
    2. Identify free parameters and physical mechanism (Spin-Orbit coupling replacement).
    3. Assign Evidence Grade.
    4. Append result to `RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md`.
- **Result (Section 6.4):** Evidence Grade **F (FALSIFIED)** — TSFT verstößt gegen Ockham's Razor, keine unabhängige Vorhersagekraft. Strategischer Vektor: `REJECTION_VECTOR_TOPOLOGICAL_METAPHOR`.

## Phase 2: Geometric Refinement (Alphahedron/Grant) — DONE
- **Goal:** Provide a more rigorous "Ockham's Razor" penalty for the iHarmonic identity.
- **Steps:**
    1. Quantify the information entropy of the Grant constants (alpha, beta, gamma, delta).
    2. Compare the BIC of the Grant model vs. the Standard Shell Model.
    3. Update Section 6.3 with quantitative metrics.
- **Result (Section 6.3):** Grant-Modell scheitert am Steelman-Antithesis-Test — Spin-Bahn-Kopplung ist nicht aus Primzahlabständen ableitbar. Evidence Grade **C (AMBIGUOUS)**, Strategischer Vektor: `REFACTORING_VECTOR_TOPOLOGICAL_STABILITY`.

## Phase 3: Zeraoulia Hamiltonian Simulation (Quantum Spectral Analysis) — DONE
- **Goal:** Empirically verify the Level Repulsion (GUE) of the Zeraoulia operator using IBM Quantum.
- **Steps:**
    1. Setup a Qiskit environment.
    2. Implement the stochastic operator $x_{n+1} = x_n + y \log x_n + \epsilon_n$ as a quantum circuit or variational simulation.
    3. Extract the nearest-neighbor spacing distribution.
    4. Compare with U-238 experimental data and GUE predictions.
    5. Update Section 6.2 and 8 (Strategic Vectors).
- **Result (Sections 6.5.1–6.5.17):** PT-symmetrische Erweiterung als `pt_potential_vqe.py` implementiert, Aer-Stresstest auf Fez-Rauschprofil (Evidence Grade **A−**), Fez QPU Singleshot (`d8kins3qv2lc7385bbj0`) bestätigt H1/H3 (`bias_PT_re = -0.0133`). Strategischer Vektor: `REFRAMING_VECTOR_RELATIVE_SPECTRUM` operativ bestätigt.

## Phase 4 (NEU, 2026-06-17): QPU-validierte Im-Bias-Metrik + statevector-first-Architektur

- **Goal:** Kanonische Bias-Signatur etablieren (Im(H_PT) statt bias_PT_re), statevector-First-Methodik auf QPU-Validierung heben.
- **Steps:**
    1. Theorem-Beweis: `||[H_diag, Re(H_PT)]||_F = 0` → bias_PT_re ist Theorem-Identität, nicht Bias-Indikator (`pt_im_bias_statevector.py`).
    2. Prereg VOR Skript-Ausführung: `pt_im_bias_prereg.json` mit H_Im_h1/h2/h3 + Entscheidungsregel.
    3. 5 sequenzielle 1-Pub-Jobs auf Fez/TOKEN2 (in 17 Sekunden alle DONE): H_Im_h1 echt QPU-bestätigt (alle |bias| < 0.005, mean −0.0001, std 0.0019).
    4. Strategischer Vektor `IM_BIAS_AS_KANONISCHE_METRIK` auf **A** promoviert, `REFRAMING_VECTOR_RELATIVE_SPECTRUM` auf **A+**.
- **Result:** Asymptotik N=10⁴..10⁶ (statevector) bestätigt H_C (alpha sinkt monoton mit N), Latorre-Spannung als **fundamentale Disagreement** klassifiziert (`LATORE_TENSION_NOTE.md` §11). Cross-Ref: `SYNTHESIS_2026_06_10.md` §Q.5, `QUANTUM_ARCHITECTURE_IMPLEMENTATION.md` Update 17:25 UTC.

## Execution Schedule (historisch)
1. Farrell Audit → ✅ DONE (Phase 1)
2. Grant Refinement → ✅ DONE (Phase 2)
3. Zeraoulia Simulation → ✅ DONE (Phase 3)
4. QPU-validierte Im-Bias → ✅ DONE (Phase 4, 2026-06-17)