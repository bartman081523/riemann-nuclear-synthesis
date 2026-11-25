# Master Inventory: Mapping All Experiments to Physical IBM Quantum QPU Results

**Date:** November 22, 2026 (Updated November 25, 2026)  
**Epistemic Status:** Fully Verified Data Cross-Reference (SciMind 4.0/5.0, ExperimentLedgerMind)  
**Quota Consumption:** **0 additional QPU seconds** for historical harvests (all jobs were previously completed on IBM Quantum backends and downloaded read-only via API).

---

## 1. Inventory of Linked Experiments & QPU Jobs

| Exp ID | Name / Hypothesis | Backend | Token | Job ID | Status | Raw Data Path | Evaluation Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EXP-032** | QUQUINT F4 (QuQuint State Verification) | `ibm_fez` | TOKEN1 | `daua5hahcrkc73dv9eh0` | DONE | [`scratches/pt_ququint_f4_fez_raw.json`](../scratches/pt_ququint_f4_fez_raw.json) | `REFUTED` (`f0_qu=0.3540`, `f0_q=0.4286`, `leak=0.2585`) |
| **EXP-032** | QUQUINT F4 (Marrakesh Port) | `ibm_marrakesh` | TOKEN2 | `db8t3rob3g5c73eguc50` | DONE | [`scratches/pt_ququint_f4_marrakesh_raw.json`](../scratches/pt_ququint_f4_marrakesh_raw.json) | `RULE_HOLDS_FALSE` (`confound=0.0726 > 0.05`) |
| **EXP-044** | H-RAM-Q (Kingston D1) | `ibm_kingston` | TOKEN2 | `davf0ns92g1c7398pfv0` | DONE | [`pt_ram_q6_kingston_raw.json`](../pt_ram_q6_kingston_raw.json) | `KINGSTON_D1` |
| **EXP-044** | H-RAM-Q (Kingston K2) | `ibm_kingston` | TOKEN2 | `davfridj371s73dmqstg` | DONE | [`pt_ram_q6_k2_raw.json`](../pt_ram_q6_k2_raw.json) | `KINGSTON_K2` |
| **EXP-044** | H-RAM-Q (Fez Session 1) | `ibm_fez` | TOKEN1 | `darq1stvr3kc73ej96ig` | DONE | [`pt_ram_q_hardware_raw.json`](../pt_ram_q_hardware_raw.json) | `FEZ_S1` |
| **EXP-044** | H-RAM-Q (Fez Session 2) | `ibm_fez` | TOKEN1 | `dartdg5vr3kc73ejcrgg` | DONE | [`pt_ram_q_hardware2_raw.json`](../pt_ram_q_hardware2_raw.json) | `FEZ_S2` |
| **EXP-044** | H-RAM-Q (Fez Session 3) | `ibm_fez` | TOKEN1 | `dat1o6qhcrkc73dtgo60` | DONE | [`pt_ram_q_hardware3_raw.json`](../pt_ram_q_hardware3_raw.json) | `FEZ_S3` |
| **EXP-046** | H-V5 Kingston Leg | `ibm_kingston` | TOKEN2 | `dat3brihcrkc73dtjbgg` | DONE | [`pt_v5_kingston_rep_kingston_raw.json`](../pt_v5_kingston_rep_kingston_raw.json) | `H-V5_CONFIRMED_KINGSTON_NEUTRAL_BAND` (bias $-0.0137$, $-2.22\sigma$) |
| **EXP-046** | H-V5 Fez Leg | `ibm_fez` | TOKEN1 | `dauassrojkfs738rrcsg` | DONE | [`pt_v5_kingston_rep_fez_raw.json`](../pt_v5_kingston_rep_fez_raw.json) | `H-V5_MITTEL_EIN_OBSERVABLE_AUSSEN` (bias $+0.0113$, $+1.84\sigma$) |
| **EXP-046** | H-V5 Marrakesh Leg | `ibm_marrakesh` | TOKEN2 | `db8t450b3g5c73egucg0` | DONE | [`scratches/pt_v5_kingston_rep_marrakesh_raw.json`](../scratches/pt_v5_kingston_rep_marrakesh_raw.json) | `MARRAKESH_V5` |
| **EXP-047** | Fez Hardware3 Rep | `ibm_fez` | TOKEN1 | `dat3gpqhcrkc73dtjmt0` | DONE | [`pt_ram_q_hardware3_raw_rep.json`](../pt_ram_q_hardware3_raw_rep.json) | `FEZ_REP_DONE` |
| **EXP-055** | FP48 Fez (160 Circuits) | `ibm_fez` | TOKEN1 | `db0m71qvog1s73fh15og` | DONE | [`pt_ram_q_prio48_raw.json`](../pt_ram_q_prio48_raw.json) | `UNDETERMINED (REFIT_INVALID_KAPPA)` (`SA-H9-5 REMAINS`) |
| **EXP-055** | FP48 Marrakesh (160 Circuits) | `ibm_marrakesh` | TOKEN2 | `db8tqp5ckpjs73b1mdr0` | DONE | [`scratches/pt_ram_q_prio48_marrakesh_raw.json`](../scratches/pt_ram_q_prio48_marrakesh_raw.json) | `MIXED_PARTIAL (REFIT_OK)` |
| **EXP-059** | H-REM59-Q (Ramanujan Fez) | `ibm_fez` | TOKEN1 | `db8sdv0b3g5c73egt2u0` | DONE | [`scratches/pt_rem59_qpu_raw.json`](../scratches/pt_rem59_qpu_raw.json) | `H-REM59-Q_REFUTED` (`mass_32 = 0.1012` vs predicted 0.2666) |
| **EXP-059** | H-REM59-Q (Marrakesh) | `ibm_marrakesh` | TOKEN2 | `db8t34ob3g5c73egub5g` | DONE | [`scratches/pt_rem59_qpu_marrakesh_raw.json`](../scratches/pt_rem59_qpu_marrakesh_raw.json) | `H-REM59-Q_REFUTED` (`mass_32 = 0.0618` vs predicted 0.2666) |
| **EXP-060** | Weil–Theta Lift / Stepanov | Statevector (G2) | 0 QPU | - | DONE | [`pt_weil_theta_060_raw.json`](../pt_weil_theta_060_raw.json) | **`CONFIRMED_ALL_HYPOTHESES`** (H-WT-1..4 bit-exact & robust) |
| **EXP-061** | Path Quadrics & Weil Saturation | Statevector (0 QPU) | 0 QPU | - | DONE | [`pt_path_quadric_061_raw.json`](../pt_path_quadric_061_raw.json) | `MIXED` (H-PQ-1,2,4 `CONFIRMED`; H-PQ-3 `REFUTED` swap entanglement) |
| **EXP-062** | Von Mangoldt State & GRH Decay | Statevector (0 QPU) | 0 QPU | - | DONE | [`pt_grh_decay_062_raw.json`](../pt_grh_decay_062_raw.json) | `REFUTED` (Prime-race fluctuations $\sim O(\ln^2 X / X)$ instead of naive $O(1/X)$) |
| **EXP-063** | Frugal 2-Qubit Clifford–Weil Walk | `ibm_fez` | TOKEN1 | `dc1f7ids2omc738ahl0g` | DONE | [`pt_clifford_weil_063_raw.json`](../pt_clifford_weil_063_raw.json) | **`CONFIRMED_ALL_HYPOTHESES`** ($P_{L=2}(q_0=0)=\mathbf{98.08\%}$, $\Delta P=\mathbf{48.34\%}$, 10.49s QPU) |
| **EXP-064** | Artin–Schreier & Deligne–Weil Bounds | Statevector (G2) | 0 QPU | - | DONE | [`pt_artin_schreier_064_raw.json`](../pt_artin_schreier_064_raw.json) | **`CONFIRMED_ALL_HYPOTHESES`** (H-ASD-1..4 bit-exact, Deligne ratio $\le 0.9554$) |
| **EXP-065** | Logarithmic Entropy Asymptotics | Statevector (SVD) | 0 QPU | - | DONE | [`pt_entanglement_log_065_raw.json`](../pt_entanglement_log_065_raw.json) | **`CONFIRMED_ALL_HYPOTHESES`** ($R^2=\mathbf{0.9955}$, $\alpha_{\text{eff}}=\mathbf{0.2081}$, Latorre–Sierra tension resolved) |
| **EXP-066** | Wigner Semicircle & Sato–Tate Emergence | Statevector ($q \le 1009$) | 0 QPU | - | DONE | [`pt_wigner_sato_tate_066_raw.json`](../pt_wigner_sato_tate_066_raw.json) | `MIXED` ($m_2, m_4, m_6$ `CONFIRMED` Catalan moments; KS test detects $\mu_3$ ramification at $q \equiv 1 \pmod 3$) |
| **EXP-067** | Frobenius–Bell Interferometer | `ibm_fez` | TOKEN1 | `dc1kabqnj2vs73dffch0` | DONE | [`pt_frobenius_bell_067_raw.json`](../pt_frobenius_bell_067_raw.json) | **`CONFIRMED_ALL_HYPOTHESES`** (Dev. $P_{00}(2,3)$ only $\mathbf{0.38\%}$, $P_{00}(4,2)$ only $\mathbf{0.07\%}$, $\Delta P=\mathbf{19.32\%}$, 10.50s QPU) |
| **EXP-068** | Frobenius Monodromy Pair Correlation | Statevector ($q \le 20000$) | 0 QPU | - | DONE | [`pt_frobenius_pair_corr_068_raw.json`](../pt_frobenius_pair_corr_068_raw.json) | **`CONFIRMED_ALL_HYPOTHESES`** (GUE level repulsion $P(s<0.2)=0.012$, Montgomery curve match) |
| **EXP-069** | Jacobi–Frobenius Symplectic Asymptotics | Statevector ($\text{USp}(2g)$) | 0 QPU | - | DONE | [`pt_jacobi_frobenius_069_raw.json`](../pt_jacobi_frobenius_069_raw.json) | **`CONFIRMED_ALL_HYPOTHESES`** (Quadratic level repulsion in $\text{USp}(2g)$, $P(s<0.2)=0.74\%$) |
| **EXP-070** | CUE Wigner Surmise Synthesis | Statevector ($N=1000$) | 0 QPU | - | DONE | **`CONFIRMED_ALL_HYPOTHESES`** (Wigner surmise RMSD ratio $0.0435$ vs Poisson baseline) |
| **EXP-071** | Prime-GUE Spectral Duality | Statevector & Numerical | 0 QPU | - | DONE | [`pt_prime_gue_071_raw.json`](../pt_prime_gue_071_raw.json) | **`CONFIRMED_ALL_HYPOTHESES`** (Zeta zeros repulsion $P(s<0.2)=0.00$, prime cross-correlation $C=1.491$) |
| **EXP-072** | Metaplectic Simplification Proof | Statevector & Symbolic | 0 QPU | - | DONE | [`pt_metaplectic_simplification_072_raw.json`](../pt_metaplectic_simplification_072_raw.json) | `MIXED_PARTIAL` (H-MSP-1,2,3 `CONFIRMED`, projector idempotence verified, 29.08x condensation) |
| **EXP-073** | Ultra-Compression Master Kernel | Statevector & SVD | 0 QPU | - | DONE | [`pt_ultra_compression_073_raw.json`](../pt_ultra_compression_073_raw.json) | **`CONFIRMED_ALL_HYPOTHESES`** (Strict rank-2 master operator proven, **109.6x code condensation factor**) |

---

## 2. Key Findings from QPU Harvests

### A. Experiment 055 (FP48-COMBINED on `ibm_fez` & `ibm_marrakesh`)
- **Fez (`db0m71qvog1s73fh15og`):**  
  The 160-circuit job was fully analyzed. Under evaluation against the frozen preregistration (`pt_ram_q_prio48_eval.py`), 8 out of 37 union rows fell below the $\kappa$ threshold $0.81$ ($\kappa_{\text{low}} = 8/37$). The registered safeguard triggered:
  $$\text{refit\_status} = \text{REFIT\_INVALID\_KAPPA} \implies \text{Verdict: UNDETERMINED}$$
  F-row-8 (OLS decomposition): $\text{resid\_sd} = 0.0772 \ge 0.01 \implies$ **SA-H9-5 REMAINS**.
- **Marrakesh (`db8tqp5ckpjs73b1mdr0`):**  
  On Marrakesh, all $\kappa$ bounds held ($\text{refit\_status} = \text{REFIT\_OK}$). The overall verdict is **`MIXED_PARTIAL`**.

### B. Experiment 032 (QUQUINT F4 on `ibm_fez`)
- **Job `daua5hahcrkc73dv9eh0`:**  
  Evaluated in sibling workspace `/run/media/julian/ML4/ququint` via `ququint_f4_recollect.py`:
  - $f_0(\text{QuQuint}) = 0.3540$
  - $f_0(\text{Qubit}) = 0.4286$
  - Leakage = $0.2585$
  - Verdict: **`REFUTED`** (`rule_holds = False`).

### C. Experiment 059 (Ramanujan Resonance on `ibm_fez` & `ibm_marrakesh`)
- **Fez (`db8sdv0b3g5c73egt2u0`):**  
  Counts in bin 32 ($a=32$, bitstring `100000`): 829 out of 8192 shots ($10.12\,\%$). The registered interval was $[21.33\,\%, 33.33\,\%]$.
  - Verdict: **`H-REM59-Q_REFUTED`**.
- **Marrakesh (`db8t34ob3g5c73egub5g`):**  
  Counts in bin 32: 506 out of 8192 shots ($6.18\,\%$).
  - Verdict: **`H-REM59-Q_REFUTED`**.
- **Interpretation:** The isolated single-bin signal is attenuated by gate depolarization into the thermal floor on both backends. This directly motivated the **Stepanov resonance architecture in EXP-060**, creating robust, multidimensional amplification across $L=\lfloor\sqrt{q}\rfloor$ steps.

---

## 3. Epistemic Status & Synthesis
1. **Zero Open / Lost QPU Jobs:**  
   Every job submitted to IBM Quantum across all project phases has been catalogued, with raw data persisted locally and evaluations evaluated against frozen preregistrations.
2. **Quota Conservation:**  
   The harvest required **0 seconds** of monthly QPU runtime.
3. **Rigorous Foundation for Hardware Validation:**  
   With the historical QPU results established, the frugal spot-check designs for EXPERIMENT 063 (Clifford–Weil walk) and EXPERIMENT 067 (Frobenius–Bell spectroscopy) demonstrated near-theoretical fidelities ($98.08\%$ and $99.62\%$) on `ibm_fez`.
