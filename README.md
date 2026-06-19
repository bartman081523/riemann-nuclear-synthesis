# Riemann–Nuclear Synthesis

[![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://github.com/bartman081523/riemann-nuclear-synthesis)
[![Tests](https://img.shields.io/badge/Tests-173%2F173%20passing-brightgreen.svg)](tests/)
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
| 3 — Asymptotic Sub-RH | statevector, `N ∈ [10⁴, 10⁶]` | α(10⁶) = 0.223, monotonically decreasing | **A−** |

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
python3 -m pytest tests/ -q   # 173/173 passing

# Reproduce the asymptotic scaling (statevector, no QPU cost)
python3 pt_asymptotic_N1e6.py   # alpha(N=10^6) = 0.223
```

For QPU reproduction details, see [Reproducibility](RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md#10-operational-findings-log-2026-06-08--2026-06-17) in the primary research repository.

---

## Hardware availability

| Account | Backend | Status | Last run |
|---|---|---|---|
| `IBMQ_TOKEN` | `ibm_fez` (156 qb) | ⚠️ False-positive quota (see §T) | 2026-06-19 |
| `IBMQ_TOKEN2` | `ibm_fez` (156 qb) | ⚠️ Quota-blocked | 2026-06-17 |

**Note 2026-06-19:** TOKEN1 diagnose returns `has_quota=true` but VQE+VQD (13 calls × 8192 shots) is still blocked. Diagnose-akzeptanz ≠ QPU-run-bereitschaft. Cron b3f26579 (1.7.2026) is the canonical reset trigger; `pt_vqe_vqd_statevector.py` is the statevector-first fallback (see `SYNTHESIS_2026_06_10.md` §T).

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
| [`PLAN.md`](PLAN.md) | Historical | Phases 1–3 done, Phase 4 active |
| [`QUANTUM_ARCHITECTURE_BRIDGE.md`](QUANTUM_ARCHITECTURE_BRIDGE.md) | Superseded | Architecture rationale (frozen 6/8) |
| [`SAEULE1_FEZ_BLOCKED.md`](SAEULE1_FEZ_BLOCKED.md) | Superseded | Fez quota block (resolved 6/17) |
| [`QUANTUM_COMPUTING_AND_PRIMES_RESEARCH.md`](QUANTUM_COMPUTING_AND_PRIMES_RESEARCH.md) | Reference | External research literature survey (95 KB) |

See the [Cross-Reference Index](RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md#10-operational-findings-log-2026-06-08--2026-06-17) in the primary research repository for the canonical detail.

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
  month        = jun,
  howpublished = {\url{https://github.com/bartman081523/riemann-nuclear-synthesis}},
  note         = {QPU-validated on ibm\_fez, SciMind 4.0/5.0 graded}
}
```

---

## License

CC-BY 4.0. See [`LICENSE`](LICENSE).

---

## Acknowledgments

IBM Quantum (Open Plan, `ibm_fez`); Latorre & Sierra (2013/2020) for the Prime State framework; Zeraoulia (2012) for the PT-symmetric Jacobi operator; the SciMind 4.0/5.0 cognitive architectures.
