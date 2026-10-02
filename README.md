# Riemann–Nuclear Synthesis

[![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://github.com/bartman081523/riemann-nuclear-synthesis)
[![Tests](https://img.shields.io/badge/Tests-1342%2F1342%20passing-brightgreen.svg)](tests/)
[![License: CC-BY 4.0](https://img.shields.io/badge/License-CC--BY%204.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org)
[![Qiskit](https://img.shields.io/badge/Qiskit-1.0%2B-6433ff.svg)](https://qiskit.org)
[![IBM Fez QPU](https://img.shields.io/badge/IBM%20Fez%20QPU-validated-0066cc.svg)](https://quantum.ibm.com)

**An open-science investigation of the trans-categorical isomorphisms between the Riemann Hypothesis and nuclear shell stability, validated on real quantum hardware.**

---

## Key findings

| Pillar | Observable | Result | Evidence |
|---|---|---:|:-:|
| 1 — PT-symmetric `Im(H_PT)` | 5 sequential 1-Pub VQE on `ibm_fez` | all \|bias\| < 0.005, mean −0.0001, std 0.0019 | **A+** |
| 3 — Schmidt entropy scaling | QPU single-shot tomography, `N ≤ 127` | α_QPU = 0.348 (vs α_Aer = 0.272) | **A−** |
| 3 — Asymptotic Sub-RH | statevector, `N ∈ [10⁴, 10⁶]` | power-law α(10⁶) = 0.223 = fit artifact; §X-Lesart: entropy growth S/log(N) → 0.55, R(10⁶) = 0.669 | **A−** |
| 4 — QUQUINT on QPU (§Z.14) | Fez/TOKEN1, prereg md5 `18fb1e62` | phi V = 0.625 > 1/5, sep V = 0.166 < 1/5, all 3 prereg bands held | **A−** |
| 4 — Margin crossover (§Z.16/V4) | Aer, 0 QPU | κ\* = 62.26 (Rough model 62.31, 0.1%) | **A−** |
| 4 — Ramanujan fingerprint (§Z.17/034) | d₆₂₅ grid + gated replication | exakt model (m−5)²/(4dm), 5/5 gated points in band, no control overlap | **B+** |
| 4 — Kingston drift test (§Z.18/V5) | `ibm_kingston`, prereg md5 `d019d587` | all 3 observables in frozen bands, bias +0.0074 < 0.05 | **A−** |
| 4 — Shor-Oracle + H-SHOR-1 (§Z.19/037–038) | Ququint statevector, 0 QPU, prereg md5 `73bc664a` | Verdict CONFIRMED: CRT null exactly 0, QPE↔order bridge match 1.0 (102 pairs), factors (3,5)/(3,7), Korselt blindness theorem-exact | **B** |
| 4 — RAM-Q zyklotomic core (ram-q-zyklizitaet, Phases 7–8) | Ququint statevector, 0 QPU + Fez/TOKEN1 | H-RAM-Q-1/2 CONFIRMED: zyklotomische Basis n₀=1 + (q−1), B2 q-universell EXAKT, q=7 blind 4/4, Wraparound \|G\|²/(dm) | **A−** |
| 4 — RAM-Q refutation line (§Z.25–Z.33/042–051) | Fez/TOKEN1 + Kingston/TOKEN2, preregs frozen VOR hardware | H-RAM-Q-3a VOID_CALIBRATION (κ̂ < 0.81 = Loschmidt-Echo), H-RAM-Q-3b/4 REFUTED (frozen falsifier exactly 3/13 am q5-Bein), D1/D2/D3 — P-Vorzeichen-Lesart dreifach widerlegt | **B+** |
| 3 — S₄-Schluss-Theorem (045 → 052) | statevector, 0 QPU | H_S4_CLOSURE_DEVIATION_FOUND (r_median-Verletzung 1.026e-08 on-chain) → 052 Re-Rechnung hebt sie quellen-einheitlich unter TOL: H_S4CLOSURE_R2_QUELLEN_ARTEFAKT (Einstufung, kein Re-Decide) | **B+** |
| 6 — Z/qZ closed family (H-ZQZ, §10.38/053) | statevector 0 QPU, prereg md5 `53c801d8` | L1 HELD bit-exakt (α_class 12/12 < 0.5, R_a ≤ 1+2·2⁻⁵²); L2 REDUNDANT_WITH_S_VN (ρ = 0.970); L3 REFUSED_OUT_OF_BAND (r_unf = 0.514, GOE-adjacent) — kein drittes Observable, stützt §X.3 | **B+** |

The **Latorre–Sierra prediction** of linear entanglement scaling (`α → 1`) is **empirically excluded** in `N ∈ [10³, 10⁶]`. See [`LATORE_TENSION_NOTE.md`](LATORE_TENSION_NOTE.md) §11.

All conclusions are graded using the **SciMind 4.0 Evidence Grading Scale (A–F)** with the Steelman Mandate, Ockham's Quantified Razor, and Anti-Sharpshooter Protocol. See [`PRIMARY_HYPOTHESIS_AUDIT.md`](PRIMARY_HYPOTHESIS_AUDIT.md) for the formal RH-orthogonality audit.

---

## Quickstart

```bash
git clone https://github.com/bartman081523/riemann-nuclear-synthesis.git
cd riemann-nuclear-synthesis

python3 -m venv .venv && source .venv/bin/activate
pip install qiskit>=1.0 qiskit-aer>=0.13 qiskit-ibm-runtime numpy scipy matplotlib pytest

# Credentials (DO NOT commit)
echo "IBMQ_TOKEN=your_token_here" > .env
echo "IBMQ_TOKEN2=your_second_token_here" >> .env

# Run the test suite
python3 -m pytest tests/ -q   # 1342/1342 passing

# Reproduce the asymptotic scaling (statevector, no QPU cost)
python3 pt_asymptotic_N1e6.py   # power-law alpha(N=10^6) = 0.223 (fit artifact; claims.py pin R(10^6) = 0.669, §X-Lesart S/log -> 0.55)
```

For QPU reproduction details, see [Reproducibility](RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md#10-operational-findings-log-2026-06-08--2026-10-02) in the primary research repository.

---

## Hardware availability

| Account | Backend | Status | Last run |
|---|---|---|---|
| `IBMQ_TOKEN` | `ibm_fez` (156 qb) | ✅ Open (046-repeat job queued, raw committed before eval) | 2026-09-29 |
| `IBMQ_TOKEN2` | `ibm_kingston` (156 qb) | ✅ Open | 2026-10-02 |

**Update 2026-09-24:** Ququint-Arc complete (§Z.11–18). TOKEN1 carried the §Z.11–14 QPU confirmation (Job `dakjk9hhvn6c73cvr1cg`, 12 circuits × 8192 shots, all 3 prereg bands held, md5 `18fb1e62` frozen before hardware); the 2026-07-21 **first real QPU-VQE+VQD run on Fez/TOKEN1** (Job `d9fidihhtsac739fg3n0`, E_0 = 2.1398, bias_PT_re = −0.0119, H1/H3 QPU-confirmed) preceded it. TOKEN2 moved to `ibm_kingston` for the V5 drift test (Job `daqaeteekp0c73aqetdg`, all 3 observables inside frozen bands, bias +0.0074 — backend-neutral, bias sign flips backend-dependently). Three-path consistency: Fez/TOKEN2 Singleshot 2026-06-10 + Statevector VQE-opt + Fez/TOKEN1 VQE+VQD. See [`SYNTHESIS_2026_06_10.md`](SYNTHESIS_2026_06_10.md) §Z.11–18.

**Branch `shor-ququint-oracle` (2026-09-24, 0 QPU):** Shor-Oracle on the Ququint/GF(5) architecture (EXPERIMENT 037, TDD) + registered hypothesis **H-SHOR-1 "Fermat-Grid-Oracle-Bridge"** (EXPERIMENT 038): prereg frozen BEFORE evaluation (md5 `73bc664a`), verdict **CONFIRMED** — CRT structural null exactly 0, QPE-readout ↔ order-grid bridge match **1.0** (102 (a,N) pairs, 0 mismatches), shor_factor(15) = (3,5) / (21) = (3,7) with primes → None, Korselt/Carmichael blindness theorem-exact (561: λ = 80 | 560), shuffle p = 0.000. H-STAR-5 (md5 `f915729e`) remains unchanged — architecture reuse only, no silent upgrade. See §Z.19 / §10.20.

**Update 2026-09-28 → 2026-10-02 (RAM-Q + H-TEST + ZQZ arc, Phases 7–16):**
- **RAM-Q (Z/qZ-Zyklotomik):** H-RAM-Q-1/2 **CONFIRMED** (the five cyclotomic primitives derived: atom n₀=1 + (q−1); B2 q-universal exact; blind q=7 checks 4/4; wraparound \|G\|²/(dm)). Then three independent hardware falsifications: H-RAM-Q-3a **VOID_CALIBRATION** (κ̂ deficit 0.81 = Loschmidt echo, not readout), H-RAM-Q-3b **REFUTED** (calibration target met, all 13 arms suppressed one-sided), H-RAM-Q-4 **REFUTED** (frozen falsifier exactly 3/13 on the q5 arm; κ̂-Floor union 0/26 real → coherent prep-error lift), all with frozen preregs and raw-committed-before-eval (§10.26–10.28, §10.30).
- **Wiederholungen → Session/Substrat:** 047 reproduced the Phase-11 verdict cross-session (H-RAM-Q-5a): session-robust P-structure; 046 Kingston bias −0.0137 (−2.22σ) flipped the 035 sign — no verdict until both legs; H-RAM-Q-6 (050/051): D1_PARTIAL (κ̂-lift substrate-universal) but D2/D3 **REFUTED** — the residual sign is *not* a function of P (third independent defeat of the sign-reading).
- **S₄-Schluss-Theorem → Einstufung:** 045 flagged `H_S4_CLOSURE_DEVIATION_FOUND` (chain-exact r_median violation 1.026e-08, no tolerance change); Phase 15/052 re-computation shows it collapses quellen-unified 17.7× under tolerance → official classification `H_S4CLOSURE_R2_QUELLEN_ARTEFAKT` (classification, not silent re-decide, §10.35/§Z.34).
- **H-TEST1/H-TEST2:** 048 CONFIRMED → diagnostics flip as normalization artifacts → 048b REFUTED 0/8 (no GF(5) advantage); 049 DEGENERATE (float64 GATE-A edge), 049b rank-controlled verdict `RANGGETRAGEN`; the conflation resolved bit-exact as a numpy-build delta (interpreter pinned per run).
- **H9 combination deck:** 7 hypotheses + 7 steelman antitheses + weaknesses registry ([`HYPOTHESEN_UND_ANTITHESEN_H9_2026_09_29.md`](HYPOTHESEN_UND_ANTITHESEN_H9_2026_09_29.md)); first falsifiers: smooth s(P)-extrapolation falls away, n=5 atom family falsified (t′-lattice discontinuity, ±1-ulp structure class), N-sweep `UEBER_BAND` (α still above the band edge, convergence missing, N > 10⁸ is the path).
- **Kritik1-Umsetzung + EXPERIMENT 053 (H-ZQZ):** measurement diagram E/G-layers + closed-family/quantor-coverage rule (§10.36/§10.37); α-coherence (claims.py alpha_1e6 → §X-Lesart) landed; the closed Z/qZ statevector family holds L1 **bit-exakt** (α_class 12/12 < 0.5, R_a max 1+2·2⁻⁵²), L2 **REDUNDANT** (ρ 0.970 with S_vN) and L3 **REFUSED_OUT_OF_BAND** (r_unf 0.514, GOE-adjacent C−) — the third-observable program is negative, only distillation remains (§10.38, §Z.35).
- **Suite:** 1079 → **1342 tests green** (97.2 s); claims.py live pin updated accordingly.

**Operational policy:** QPU time is scarce — all statevector-first validations must precede any QPU submission. Preregistration before `main()` is required for every QPU script (Anti-Sharpshooter Protocol).

---

## Document map

| Document | Status | Role |
|---|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Reference | SciMind 4.0/5.0 methodology manifest |
| [`RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md`](RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md) | **Primary** | Theory (§1–9) + Operational Findings Log (§10) |
| [`SYNTHESIS_2026_06_10.md`](SYNTHESIS_2026_06_10.md) | **Master** | SciMind verdicts, strategic vectors |
| [`QUANTUM_ARCHITECTURE_IMPLEMENTATION.md`](QUANTUM_ARCHITECTURE_IMPLEMENTATION.md) | **Master** | Statevector-first architecture + QPU-update log |
| [`LATORE_TENSION_NOTE.md`](LATORE_TENSION_NOTE.md) | Pre-print | Latorre–Sierra tension + §11 asymptotics |
| [`PRIMARY_HYPOTHESIS_AUDIT.md`](PRIMARY_HYPOTHESIS_AUDIT.md) | **Current** | Theorem audit + RH-orthogonality + multi-observable convergence |
| [`INVESTIGATION_PLAN.md`](INVESTIGATION_PLAN.md) | Reference | Mermaid flowchart of investigation paths |
| [`HYPOTHESEN_UND_ANTITHESEN_H9_2026_09_29.md`](HYPOTHESEN_UND_ANTITHESEN_H9_2026_09_29.md) | **Current** | Kombinations-Deck: H-H9-1..7 + Steelman-Antithesen SA-H9-1..7, Schwächen-Register + F-Zeilen (falsifier ledger) |
| [`PLAN.md`](PLAN.md) | Historical + local working copy | Phase-ledger 1–16 done (RAM-Q 7–16, ZQZ); the committed copy lags at Phase 5 — the live ledger stays working-tree-only by project policy |
| [`QUANTUM_ARCHITECTURE_BRIDGE.md`](QUANTUM_ARCHITECTURE_BRIDGE.md) | Superseded | Architecture rationale (frozen 6/8) |
| [`SAEULE1_FEZ_BLOCKED.md`](SAEULE1_FEZ_BLOCKED.md) | Superseded | Fez quota block (resolved 6/17) |
| [`QUANTUM_COMPUTING_AND_PRIMES_RESEARCH.md`](QUANTUM_COMPUTING_AND_PRIMES_RESEARCH.md) | Reference | External research literature survey (95 KB) |

See the [Cross-Reference Index](RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md#10-operational-findings-log-2026-06-08--2026-10-02) in the primary research repository for the canonical detail.

---

## Citation

```bibtex
@misc{riemann-nuclear-synthesis-2026,
  author       = {Julian H. and Claude},
  title        = {Riemann--Nuclear Synthesis: A Four-Pillar TDD-Validated
                  Quantum-Spectral Investigation of the Trans-Categorical
                  Isomorphisms between the Riemann Hypothesis and Nuclear
                  Shell Stability},
  year         = {2026},
  month        = sep,
  howpublished = {\url{https://github.com/bartman081523/riemann-nuclear-synthesis}},
  note         = {QPU-validated on ibm\_fez and ibm\_kingston, SciMind 4.0/5.0 graded}
}
```

---

## License

CC-BY 4.0. See [`LICENSE`](LICENSE).

---

## Acknowledgments

IBM Quantum (Open Plan, `ibm_fez`); Latorre & Sierra (2013/2020) for the Prime State framework; Zeraoulia (2012) for the PT-symmetric Jacobi operator; the SciMind 4.0/5.0 cognitive architectures.
