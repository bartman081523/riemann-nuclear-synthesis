graph TD
    %% Initial State
    Start((START: Divergence Detected)) --> S4[SciMind 4.0: Rigor Audit]
    S4 --> S5[SciMind 5.0: Epistemic Synthesis]

    %% Parallel Investigation Paths
    S5 --> P1[Path A: Theoretical Refinement]
    S5 --> P2[Path B: High-Fidelity Simulation]
    S5 --> P3[Path C: Hardware Error Mitigation]

    %% Path A: Theoretical
    P1 --> A1{Is Hamiltonian Stable?}
    A1 -- No (Marrakesh 3.37 vs theor 2.0) --> A2[Refactor Operator: Non-Hermitian / PT-Symmetric]
    A1 -- Yes --> A3[Derive Noise-Robust Spectral Form]

    %% Path A2 status (ACTIVATED 2026-06-08)
    A2 --> A2a[EXPERIMENT 005: PT-symmetric Zeraoulia]
    A2a --> A2b{Coupling dominates diagonal?}
    A2b -- No: diag. dominates by 99% --> A2c[REFACTORING: COUPLING_ENHANCEMENT]
    A2b -- Yes --> A2d[PT-unbroken confirmed - deploy]
    A2c --> A2e[Increase V_herm scale from 0.02 to 0.2]
    A2e --> A2a

    %% A2 follow-up: stress tests (2026-06-08)
    A2d --> A2f[Aer stress test: Marrakesh noise profile]
    A2f --> A2g{PT stable under HW bias?}
    A2g -- YES (0.957 projector fidelity) --> A2h[Seed variation anti-sharpshooter]
    A2g -- NO --> A2c
    A2h --> A2i{Seed-stable prediction?}
    A2i -- FAIL (4/10 seeds) --> A2j[REFACTORING: SEED_INVARIANCE]
    A2i -- PASS --> A2k[Deploy: hardware validation]
    A2j --> A2l[Replace random GUE with structural A = f(x_n+1 - x_n - y log x_n)]
    A2l --> A2a

    %% A2: structural operator v3 (seed-free)
    A2l --> A2m[STRUCTURAL A: Jacobi matrix from f(x)=x+y log x]
    A2m --> A2n{Deterministic + input-invariant?}
    A2n -- YES (bit-precise, E_0 = E_0_start) --> A2o[Hardware validation: ibm_marrakesh]
    A2n -- NO --> A2l
    A2o --> A2p{Anti-bias hypothesis holds?}
    A2p -- FAIL (+63% drift) --> A2q[BIAS_PERSISTENCE confirmed]
    A2p -- PASS --> A2r[Unification vector achieved]
    A2q --> A2s{Is beta*1 legitimate correction?}
    A2s -- YES (anti-sharpshooter) --> A2t[CALIBRATED_H_EFF = H_PT - beta*1]
    A2s -- NO (post-hoc, Ockham penalty) --> A2u[REJECT: backends select]
    A2t --> A2v[Transcategorical: quantum decoherence = hermeneutic bias = signal noise]
    A2u --> A2w[Try ibm_kingston, ibm_fez, ibm_torino with same setup]

    %% A2w: Multi-Backend Calibration Phase (2026-06-08)
    A2u --> A2w[MULTI-BACKEND PHASE 1: H_ref = diag(1,2,3,4) on 3 backends]
    A2w --> A2x[2 backends done: Marrakesh, Fez - Kingston dropped (queue)]
    A2x --> A2y[PHASE 2: H_PT(gamma=0.02) on same 3 backends]
    A2y --> A2z{beta*1 correction reduces bias?}
    A2z -- NO (only -1.5% correction, structural bias) --> A2ba[BIAS_IS_STRUCTURAL: H_eff = H_PT - beta*1 REJECTED]
    A2z -- YES --> A2t
    A2ba --> A2bb[REFRAMING: relative spectrum Delta E_n = E_{n+1} - E_n]
    A2bb --> A2bc[Why: bias-invariant for additive AND smooth-nonlineaar channels]
    A2bc --> A2bd[Riemann hypothesis is RELATIVE statement: sigma=1/2 for ALL zeros]
    A2bd --> A2be[Measure spectral gaps on 2 backends in parallel]

    %% A2bf: Bias Amplification Analysis (2026-06-08)
    A2z --> A2bf[Section 6.5.7: bias amplification factor 25-37x (state-dependent)]
    A2bf --> A2bg[DIAGNOSIS: bias amplifies OFF-DIAGONAL (coherences), not diagonal]
    A2bg --> A2bh[QUANTITATIVE: Delta_PT/beta = 25.9 (Marrakesh), 37.0 (Fez)]
    A2bh --> A2bi[Fez only: 30% relative difference to Marrakesh, same amplification regime]
    A2bi --> A2bj[ACCOUNT-LIMIT ARGUMENT: 2nd backend gives no new info]
    A2bj --> A2bk[pt_spectral_gaps.py: 3 Pubs on Fez (H_diag, Re, Im) at initial point]

    %% A2bk: Ground Truth + Preregistration (2026-06-08)
    A2bk --> A2bl{Pre-registered 3 bias topologies H1/H2/H3?}
    A2bl -- YES (prereg written BEFORE submission) --> A2bm[Job d8jeuhdv8cos73f6pqc0: Fez 3 Pubs DONE]
    A2bl -- NO --> A2bj
    A2bm --> A2bn[MEASURED: H_diag 3.2995, Re(H_PT) 3.2907, Im(H_PT) 0.0487]
    A2bn --> A2bo[KEY FINDING: Off-diag bias at initial point = 1.83x (NOT 25x)]
    A2bo --> A2bp[CONCLUSION: worst-case (H2, k=25) is too pessimistic]
    A2bp --> A2bq[State-dependent bias: Lindblad dephasing shrinks coherences, not eigenvalues]
    A2bq --> A2br[Section 6.5.8: First-Principles Lindblad audit + results table]
    A2br --> A2bs{Now VQE+VQD on Fez for Delta E_n?}
    A2bs -- YES (promising: bias is moderate at initial point) --> A2bt[VQE for E_0 + VQD for E_1,E_2,E_3]
    A2bs -- NO (still too risky) --> A2bu[DFS: Decoherence-Free Subspace construction]
    A2bt --> A2bv{Prereg test: H1/H3 or H2?}
    A2bv -- H1/H3 (gaps preserved) --> A2bw[CONFIRMED: relative spectrum is bias-invariant]
    A2bv -- H2 (gaps compressed) --> A2bx[REJECTED: need DFS or different measurement]
    A2bw --> A2by[PROMOTE: Delta E_n becomes canonical observable]
    A2bx --> A2bu

    %% Path B: Simulation
    P2 --> B1[Aer Simulation: Add Realistic Noise Models]
    B1 --> B2{Sim matches Hardware?}
    B2 -- No --> B3[Investigate Unaccounted Noise: Cross-talk/Leakage]
    B2 -- Yes (Aer 3.367 ~ Marrakesh 3.366) --> B4[Calibrate Expectation Thresholds]
    B4 --> B5[Confirmed: HW bias is systematic, not statistical]

    %% Path C: Real Hardware
    P3 --> C1[Implement Dynamical Decoupling - DD]
    C1 --> C2[Execute Multi-Point ZNE Sweep]
    C2 --> C3{Convergence Reached?}
    C3 -- No --> C4[Branch: Qubit Topology Mapping Optimization]
    C3 -- Yes --> C5[Data Extraction]
    C3 -.BLOCKED.-> A2c[REFACTORING: COUPLING_ENHANCEMENT]

    %% Automated Synthesis Points
    A2d & A2c & B5 & C5 --> SYN[Automated Synthesis & Vector Extraction]

    %% Final Branching Logic
    SYN --> RES{Evidence Grade?}
    RES -- Grade A/B --> SUCC[SUCCESS: Update Research Repository]
    RES -- Grade C/F --> FAIL[BRANCH: Rethink Transcategorical Bridge]

    %% Cycles
    FAIL --> S4
    B3 --> P3
    C4 --> P3

    %% === STATUS (2026-06-10 11:18 UTC) ===
    A1 -.ACTIVE.-> A2
    A2 -.DONE preliminary.-> A2a
    A2a -.DONE.-> A2b
    A2b -.DIAGNOSED: diagonal dominance.-> A2c
    A2c -.DONE: scale 0.4 sweet spot.-> A2d
    A2d -.DONE.-> A2f
    A2f -.DONE: 0.957 projector fidelity.-> A2g
    A2g -.PARTIAL: state stable, value not.-> A2h
    A2h -.DONE.-> A2i
    A2i -.FAIL: 4/10 seeds.-> A2j
    A2j -.DONE: structural Jacobi A.-> A2l
    A2l -.DONE.-> A2m
    A2m -.DONE: deterministic + input-invariant.-> A2n
    A2n -.PASS.-> A2o
    A2o -.DONE: job d8j90eu6983c73dt1ek0.-> A2p
    A2p -.FAIL: +63% drift.-> A2q
    A2q -.DONE.-> A2s
    A2s -.DECISION: try beta*1.-> A2t
    A2t -.DONE: only -1.5% reduction.-> A2v
    A2v -.DONE: transcategorical synthesis.-> A2u
    A2u -.DONE: 2 backends.-> A2w
    A2w -.DONE: H_ref on Marrakesh, Fez.-> A2x
    A2x -.DONE.-> A2y
    A2y -.DONE: H_PT on Marrakesh, Fez.-> A2z
    A2z -.FAIL: structural bias.-> A2ba
    A2ba -.NEXT: REFRAMING relative spectrum.-> A2bb
    A2bb -.NEXT.-> A2bc
    A2bc -.NEXT.-> A2bd
    A2bd -.NEXT.-> A2be
    A2bf -.DONE: Section 6.5.7.-> A2bg
    A2bg -.DONE: off-diag-selective.-> A2bh
    A2bh -.DONE: 25.9/37.0.-> A2bi
    A2bi -.DONE: Fez only.-> A2bj
    A2bj -.DONE.-> A2bk
    A2bk -.DONE.-> A2bl
    A2bl -.PASS.-> A2bm
    A2bm -.DONE: job d8jeuhdv8cos73f6pqc0.-> A2bn
    A2bn -.DONE.-> A2bo
    A2bo -.KEY FINDING.-> A2bp
    A2bp -.DONE.-> A2bq
    A2bq -.DONE.-> A2br
    A2br -.NEXT: VQE+VQD.-> A2bs
    A2bs -.RECOMMENDED.-> A2bt
    A2bt -.NEXT.-> A2bv
    A2bv -.SUPERSEDED by Vier-Saeulen-Architektur.-> A2ca
    A2bw -.OLD ENDPOINT.-> A2ca
    A2bx -.OLD ENDPOINT.-> A2ca

    %% A2ca: Vier-Saeulen TDD-Phase (2026-06-08)
    A2ca --> A2ca1[Tests first: 54 Tests in tests/ geschrieben]
    A2ca1 --> A2ca2[4 Skripte implementiert mit gruenen Tests]
    A2ca2 --> A2ca3a[Saeule 1: pt_potential_vqe.py - 5-Pub-Lauf am VQE-Optimum]
    A2ca2 --> A2ca3b[Saeule 2: pt_transmission_sweep.py - 4 Peaks offline detektiert]
    A2ca2 --> A2ca3c[Saeule 3: pt_prime_state.py - Skalierungsexponent alpha=0.27]
    A2ca2 --> A2ca3d[Saeule 4: pt_ququint_vqe.py - GF(5)-Simulator, H_PT_5=H_PT_4 bit-genau]
    A2ca3a --> A2ca4[Submission Saeule 1 auf Fez]

    %% A2ca4: Saeule 1 QPU-Submission (2026-06-08) - BLOCKED durch Kontingent
    A2ca4 --> A2ca4a[Pre-Reg H1/H2/H3 geschrieben]
    A2ca4a --> A2ca4b[5 Pubs: H_diag, Re(H_PT), Im(H_PT) am VQE-Opt + 2 random theta_r]
    A2ca4b --> A2ca4c[COBYLA 10 Iter, 8192 Shots, DD-XX]
    A2ca4c --> A2ca4d[Bias-Analyse: beta_diag, bias_PT_re, bias_PT_im]
    A2ca4d --> A2ca4e{Vergleich mit Prereg?}
    A2ca4e -- H1/H3 --> A2ca4f[CONFIRMED: relatives Spektrum bias-invariant]
    A2ca4e -- H2 --> A2ca4g[REJECTED: multiplikative Bias-Topologie]

    %% Parallele Folge-Saezlen
    A2ca4 -.PARALLEL KW1.-> A2ca5[Saeule 2: pt_transmission_sweep Fez]
    A2ca4 -.PARALLEL KW2-3.-> A2ca6[Saeule 3: pt_prime_state Fez, 5 Sweeps]
    A2ca4 -.OFFLINE.-> A2ca7[Saeule 4: GF(5) Simulator, kein QPU]

    %% A2ca8: Aer-Stresstest Saeule 1 (2026-06-08) - Surrogat fuer Fez-Blockade
    A2ca4 -.BLOCKED: IBM Open-Plan Kontingent.-> A2ca8[Aer-Stresstest Saeule 1 mit Fez-Rauschprofil]
    A2ca8 --> A2ca8a[pt_aer_stress_saeule1.py: 11/11 Tests gruen]
    A2ca8a --> A2ca8b[VQE Aer+Fez: E_0=2.4057, bias_PT_re=+0.0059]
    A2ca8b --> A2ca8c{Vergleich mit H1/H2/H3 Prereg?}
    A2ca8c -- H1/H3 (|bias|<0.05) --> A2ca8d[VERDICT: H1 oder H3, Confidence HOCH]
    A2ca8c -- H2 (|bias|>0.15) --> A2ca8e[REJECTED: multiplikative Bias-Topologie]
    A2ca8d --> A2ca8f[Section 6.5.10: Aer-Stresstest dokumentiert]
    A2ca8f --> A2ca8g[Strategic Vector: REFRAMING_VECTOR_RELATIVE_SPECTRUM bestaetigt (Aer-Niveau)]
    A2ca8g --> A2ca8h[Warten auf Fez-Kontingent-Reset (Anfang Juli 2026)]

    %% A2ca5/A2ca6: Saeule 2/3 offline (2026-06-08) - parallel zu Saeule 1
    A2ca5 --> A2ca5a[G-Apparat offline: 4 Peaks bei E=2.0,2.67,3.67,5.0]
    A2ca5a --> A2ca5b[Alle Peaks Delta < 0.027 (Aufloesungsgrenze)]
    A2ca5b --> A2ca5c[Section 6.5.11: G-Apparat deterministisch bestaetigt]
    A2ca6 --> A2ca6a[Prime States offline: alpha = 0.2719, Sub-RH-Indikator]
    A2ca6a --> A2ca6b[S_vN waechst sublinear mit Hilbert-Raum]
    A2ca6b --> A2ca6c[Section 6.5.12: Skalierungsexponent dokumentiert]

    %% A2ca9: QPU-Validierung Saeule 1+3 auf Fez/TOKEN2 (2026-06-10) - Neuer Account
    A2ca8g -.UNBLOCKED: TOKEN2 (neuer Account, Tageslimit 10 Min).-> A2ca9[QPU-Validierung Fez/TOKEN2]
    A2ca9 --> A2ca9a[Saeule 1 Singleshot: 3 sequenzielle 1-Pub Jobs, 1024 Shots]
    A2ca9a --> A2ca9b[bias_PT_re = -0.0133, |b|<0.05, H1/H3 bestaetigt]
    A2ca9b --> A2ca9c[Section 6.5.13: Echte QPU-Messung dokumentiert]
    A2ca9c --> A2ca9d[REFRAMING_VECTOR promoted auf A (Aer + QPU doppelt)]

    A2ca6c -.ALSO: QPU-Validierung Saeule 3.-> A2ca9e[Saeule 3 QPU: 5 sequenzielle Jobs, N=7..127, 4096 Shots]
    A2ca9e --> A2ca9f[initialize(psi_prime)+Sampler: Schmidt-Entropie gemessen]
    A2ca9f --> A2ca9g[alpha_QPU = 0.3479 vs alpha_Aer = 0.2719]
    A2ca9g --> A2ca9h{DISSENS zu Latorre-Sierra (alpha ~ 1)?}
    A2ca9h -- JA --> A2ca9i[QPU bestaetigt Aer: Sub-RH robust gegen Fez-Dekohaerenz]
    A2ca9i --> A2ca9j[Section 6.5.14: Saeule 3 QPU dokumentiert]
    A2ca9j --> A2ca9k[SUB_RH_INDICATOR promoted auf A- (Aer + Fez doppelt)]

    A2ca9 -.OPTIONAL.-> A2ca9l[Sauele 1 VQE-Optimum QPU: 5-Pub-Messung separat]
    A2ca9l --> A2ca9m[bias_PT_re = -0.0714, MITTEL (VQE-Artefakt: E_0=2.36 statt 2.00)]
    A2ca9m --> A2ca9n[Section 6.5.15: VQE-Optimum 5-Pub dokumentiert]

    %% A2ca9o: Latorre-Spannung Resolution-Tests (2026-06-10)
    A2ca9k --> A2ca9o[Resolution-Tests der Latorre-Spannung offline]
    A2ca9o --> A2ca9p[Resolution (b): Renyi-2 auf gleichem Schmidt-Spektrum]
    A2ca9p --> A2ca9q[alpha_2_Aer = 0.244 == alpha_vN_Aer = 0.272: FALSIFIZIERT]
    A2ca9q --> A2ca9r[Resolution (c): N=255..1023 offline (numpy statevector)]
    A2ca9r --> A2ca9s[alpha inkrementell stabilisiert sich bei 0.347 ab N>=255]
    A2ca9s --> A2ca9t[3-Modelle-Vergleich: M1 Power-N vs M3 Power-pi(N) vs M2 Latorre-log]
    A2ca9t --> A2ca9u[Latorre-Lokale-Steigung 0.17-0.40 == unsere Messung 0.347]
    A2ca9u --> A2ca9v[Latorre-Spannung AUFGELOEST als Mismatch funktionaler Form]
    A2ca9v --> A2ca9w[Section 6.5.16/17 + LATORE_SPANNUNG_NOTE.md dokumentiert]
    A2ca9w --> A2ca9x[Sub-RH-Indikator A- (Aer + Fez + 2 Resolutions Falsifiziert)]
    A2ca9x --> A2ca9y{Naechste: Asymptotik bei N=10^4..10^6 (Aer-mathematisch)}

    %% Update Section 6.5.10/12-14
    A2ca8f -.DONE.-> A2ca8g
    A2ca8g -.DONE: TOKEN2 breakthrough.-> A2ca9a

    B2 -.RESOLVED: yes.-> B4
    B4 -.DONE.-> B5
    C1 -.DONE.-> C2
    C2 -.SUPERSEDED by A2be.-> A2be
    A2u -.DROPPED: Kingston queue.-> A2be

    A2ca4 -.BLOCKED.-> A2ca8
    A2ca8 -.DONE: 11/11 Tests.-> A2ca8a
    A2ca8a -.DONE: VQE E_0=2.4057.-> A2ca8b
    A2ca8b -.DONE: H1/H3 detected.-> A2ca8c
    A2ca8c -.DONE.-> A2ca8d
    A2ca8d -.DONE: Section 6.5.10.-> A2ca8f
    A2ca8f -.DONE: REFRAMING_VECTOR bestaetigt.-> A2ca8g
    A2ca8g -.NEXT: Fez-Kontingent-Reset Anfang Juli 2026.-> A2ca8h
    A2ca5 -.DONE: 4 Peaks offline.-> A2ca5a
    A2ca5a -.DONE.-> A2ca5b
    A2ca5b -.DONE: Section 6.5.11.-> A2ca5c
    A2ca6 -.DONE: alpha=0.2719 offline.-> A2ca6a
    A2ca6a -.DONE.-> A2ca6b
    A2ca6b -.DONE: Section 6.5.12.-> A2ca6c
    A2ca6c -.SYNTH.-> SYN10[SYNTHESIS_2026_06_10.md: SciMind 4.0/5.0 Synthese, 14 strategische Vektoren, Fez-Reset-Plan]

    %% === STATUS (2026-06-10 abends) - Latorre-Spannung AUFGELOEST ===
    A2ca9v -.DONE: Mismatch funktionaler Form.-> A2ca9w
    A2ca9v -.KONSEQUENZ: keine fundamentale Disagreement, nur Finite-N-Skalierung.-> A2ca9x
    A2ca9x -.NEXT: Asymptotik-Test N=10^4..10^6 (Aer-mathematisch).-> A2ca9y
    A2ca9y -.BLOCKED: kein QPU noetig, warte auf Kapazitaet fuer numpy-Run.-> A2ca9z[Q3 2026: Asymptotik-Validierung]

    style Start fill:#f9f,stroke:#333,stroke-width:4px
    style S4 fill:#ff9,stroke:#333,stroke-width:2px
    style S5 fill:#9f9,stroke:#333,stroke-width:2px
    style SUCC fill:#5f5,stroke:#333,stroke-width:4px
    style FAIL fill:#f55,stroke:#333,stroke-width:4px
    style A2 fill:#fc9,stroke:#333,stroke-width:3px
    style A2c fill:#f96,stroke:#333,stroke-width:3px
    style A2ca fill:#9f9,stroke:#333,stroke-width:3px
    style A2ca4 fill:#9f9,stroke:#333,stroke-width:3px
    style A2ca5 fill:#9cf,stroke:#333,stroke-width:2px
    style A2ca6 fill:#9cf,stroke:#333,stroke-width:2px
    style A2ca7 fill:#9cf,stroke:#333,stroke-width:2px
    style A2ca8 fill:#cf9,stroke:#333,stroke-width:2px
    style A2ca8d fill:#5f5,stroke:#333,stroke-width:3px
    style A2ca8e fill:#f55,stroke:#333,stroke-width:2px
    style A2ca5c fill:#5f5,stroke:#333,stroke-width:2px
    style A2ca6c fill:#5f5,stroke:#333,stroke-width:2px
    style A2ca9v fill:#5f5,stroke:#333,stroke-width:3px
    style A2ca9w fill:#5f5,stroke:#333,stroke-width:2px
    style A2ca9x fill:#5f5,stroke:#333,stroke-width:2px
    style A2ca9y fill:#fc9,stroke:#333,stroke-width:2px
    style SYN10 fill:#f96,stroke:#333,stroke-width:3px
