# Master-Inventar: Verknüpfung aller Experimente mit den realen IBM Quantum QPU-Ergebnissen

**Datum:** 2026-11-22  
**Epistemischer Status:** Vollständig verifizierter Datenabgleich (SciMind 4.0/5.0, ExperimentLedgerMind)  
**Quota-Verbrauch:** **0 zusätzliche QPU-Sekunden** (alle Jobs waren auf den QPUs bereits vollständig ausgeführt und wurden schreibgeschützt via API heruntergeladen und ausgewertet).

---

## 1. Übersicht der verknüpften Experimente & QPU-Jobs

| Exp-ID | Name / Hypothese | Backend | Token | Job-ID | Status | Rohdaten-Pfad | Eval-Ergebnis / Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EXP-032** | QUQUINT F4 (QuQuint State Verification) | `ibm_fez` | TOKEN1 | `daua5hahcrkc73dv9eh0` | DONE | [`scratches/pt_ququint_f4_fez_raw.json`](file:///run/media/julian/ML4/riemann/scratches/pt_ququint_f4_fez_raw.json) | `REFUTED` (`f0_qu=0.3540`, `f0_q=0.4286`, `leak=0.2585`) |
| **EXP-032** | QUQUINT F4 (Marrakesh-Port) | `ibm_marrakesh` | TOKEN2 | `db8t3rob3g5c73eguc50` | DONE | [`scratches/pt_ququint_f4_marrakesh_raw.json`](file:///run/media/julian/ML4/riemann/scratches/pt_ququint_f4_marrakesh_raw.json) | `RULE_HOLDS_FALSE` (`confound=0.0726 > 0.05`) |
| **EXP-044** | H-RAM-Q (Kingston D1) | `ibm_kingston` | TOKEN2 | `davf0ns92g1c7398pfv0` | DONE | [`pt_ram_q6_kingston_raw.json`](file:///run/media/julian/ML4/riemann/pt_ram_q6_kingston_raw.json) | `KINGSTON_D1` |
| **EXP-044** | H-RAM-Q (Kingston K2) | `ibm_kingston` | TOKEN2 | `davfridj371s73dmqstg` | DONE | [`pt_ram_q6_k2_raw.json`](file:///run/media/julian/ML4/riemann/pt_ram_q6_k2_raw.json) | `KINGSTON_K2` |
| **EXP-044** | H-RAM-Q (Fez Session 1) | `ibm_fez` | TOKEN1 | `darq1stvr3kc73ej96ig` | DONE | [`pt_ram_q_hardware_raw.json`](file:///run/media/julian/ML4/riemann/pt_ram_q_hardware_raw.json) | `FEZ_S1` |
| **EXP-044** | H-RAM-Q (Fez Session 2) | `ibm_fez` | TOKEN1 | `dartdg5vr3kc73ejcrgg` | DONE | [`pt_ram_q_hardware2_raw.json`](file:///run/media/julian/ML4/riemann/pt_ram_q_hardware2_raw.json) | `FEZ_S2` |
| **EXP-044** | H-RAM-Q (Fez Session 3) | `ibm_fez` | TOKEN1 | `dat1o6qhcrkc73dtgo60` | DONE | [`pt_ram_q_hardware3_raw.json`](file:///run/media/julian/ML4/riemann/pt_ram_q_hardware3_raw.json) | `FEZ_S3` |
| **EXP-046** | H-V5 Kingston Leg | `ibm_kingston` | TOKEN2 | `dat3brihcrkc73dtjbgg` | DONE | [`pt_v5_kingston_rep_kingston_raw.json`](file:///run/media/julian/ML4/riemann/pt_v5_kingston_rep_kingston_raw.json) | `H-V5_CONFIRMED_KINGSTON_NEUTRAL_BAND` (bias $-0.0137$, $-2.22\sigma$) |
| **EXP-046** | H-V5 Fez Leg | `ibm_fez` | TOKEN1 | `dauassrojkfs738rrcsg` | DONE | [`pt_v5_kingston_rep_fez_raw.json`](file:///run/media/julian/ML4/riemann/pt_v5_kingston_rep_fez_raw.json) | `H-V5_MITTEL_EIN_OBSERVABLE_AUSSEN` (bias $+0.0113$, $+1.84\sigma$) |
| **EXP-046** | H-V5 Marrakesh Leg | `ibm_marrakesh` | TOKEN2 | `db8t450b3g5c73egucg0` | DONE | [`scratches/pt_v5_kingston_rep_marrakesh_raw.json`](file:///run/media/julian/ML4/riemann/scratches/pt_v5_kingston_rep_marrakesh_raw.json) | `MARRAKESH_V5` |
| **EXP-047** | Fez Hardware3 Rep | `ibm_fez` | TOKEN1 | `dat3gpqhcrkc73dtjmt0` | DONE | [`pt_ram_q_hardware3_raw_rep.json`](file:///run/media/julian/ML4/riemann/pt_ram_q_hardware3_raw_rep.json) | `FEZ_REP_DONE` |
| **EXP-055** | FP48 Fez (160 Circuits) | `ibm_fez` | TOKEN1 | `db0m71qvog1s73fh15og` | DONE | [`pt_ram_q_prio48_raw.json`](file:///run/media/julian/ML4/riemann/pt_ram_q_prio48_raw.json) | `UNDETERMINED (REFIT_INVALID_KAPPA)` (`SA-H9-5 BLEIBT`) |
| **EXP-055** | FP48 Marrakesh (160 Circuits) | `ibm_marrakesh` | TOKEN2 | `db8tqp5ckpjs73b1mdr0` | DONE | [`scratches/pt_ram_q_prio48_marrakesh_raw.json`](file:///run/media/julian/ML4/riemann/scratches/pt_ram_q_prio48_marrakesh_raw.json) | `MIXED_PARTIAL (REFIT_OK)` |
| **EXP-059** | H-REM59-Q (Ramanujan Fez) | `ibm_fez` | TOKEN1 | `db8sdv0b3g5c73egt2u0` | DONE | [`scratches/pt_rem59_qpu_raw.json`](file:///run/media/julian/ML4/riemann/scratches/pt_rem59_qpu_raw.json) | `H-REM59-Q_REFUTED` (`mass_32 = 0.1012` vs Vorhersage 0.2666) |
| **EXP-059** | H-REM59-Q (Marrakesh) | `ibm_marrakesh` | TOKEN2 | `db8t34ob3g5c73egub5g` | DONE | [`scratches/pt_rem59_qpu_marrakesh_raw.json`](file:///run/media/julian/ML4/riemann/scratches/pt_rem59_qpu_marrakesh_raw.json) | `H-REM59-Q_REFUTED` (`mass_32 = 0.0618` vs Vorhersage 0.2666) |
| **EXP-060** | Weil-Theta-Lift / Stepanov | Statevector (G2) | 0 QPU | - | DONE | [`pt_weil_theta_060_raw.json`](file:///run/media/julian/ML4/riemann/pt_weil_theta_060_raw.json) | **`CONFIRMED_ALL_HYPOTHESES`** (H-WT-1..4 bit-exakt & robust) |
| **EXP-061** | Pfad-Quadrik & Weil-Sättigung | Statevector (0 QPU) | 0 QPU | - | DONE | [`pt_path_quadric_061_raw.json`](file:///run/media/julian/ML4/riemann/pt_path_quadric_061_raw.json) | `MIXED` (H-PQ-1,2,4 `CONFIRMED`; H-PQ-3 `REFUTED` Swap-Verschränkung) |
| **EXP-062** | Von-Mangoldt-Zustand & GRH-Decay | Statevector (0 QPU) | 0 QPU | - | DONE | [`pt_grh_decay_062_raw.json`](file:///run/media/julian/ML4/riemann/pt_grh_decay_062_raw.json) | `REFUTED` (Prime-Race Fluktuationen $\sim O(\ln^2 X / X)$ statt naivem $O(1/X)$) |
| **EXP-063** | Frugaler 2-Qubit Clifford-Weil Walk | `ibm_fez` | TOKEN1 | `dc1f7ids2omc738ahl0g` | DONE | [`pt_clifford_weil_063_raw.json`](file:///run/media/julian/ML4/riemann/pt_clifford_weil_063_raw.json) | **`CONFIRMED_ALL_HYPOTHESES`** ($P_{L=2}(q_0=0)=\mathbf{98.08\%}$, $\Delta P=\mathbf{48.34\%}$, 10.49s QPU) |

---

## 2. Detaillierte Erkenntnisse aus den frisch heruntergeladenen Jobs

### A. Experiment 055 (FP48-COMBINED auf `ibm_fez` & `ibm_marrakesh`)
- **Fez (`db0m71qvog1s73fh15og`):**  
  Der 160-Circuit-Job wurde vollständig ausgelesen. Bei der Auswertung gegen das gefrorene Prereg (`pt_ram_q_prio48_eval.py`) fielen 8 von 37 Union-Reihen unter die $\kappa$-Schwelle $0.81$ ($\kappa_{\text{low}} = 8/37$). Daher greift das registrierte Safeguard:
  $$\text{refit\_status} = \text{REFIT\_INVALID\_KAPPA} \implies \text{Verdict: UNDETERMINED}$$
  F-Zeile-8 (OLS-Zerlegung): $\text{resid\_sd} = 0.0772 \ge 0.01 \implies$ **SA-H9-5 BLEIBT**.
- **Marrakesh (`db8tqp5ckpjs73b1mdr0`):**  
  Auf Marrakesh hielten alle $\kappa$-Schwellen ($\text{refit\_status} = \text{REFIT\_OK}$). Das Gesamturteil lautet **`MIXED_PARTIAL`**.

### B. Experiment 032 (QUQUINT F4 auf `ibm_fez`)
- **Job `daua5hahcrkc73dv9eh0`:**  
  Im Sibling-Projekt `/run/media/julian/ML4/ququint` via `ququint_f4_recollect.py` ausgewertet.
  - $f_0(\text{QuQuint}) = 0.3540$
  - $f_0(\text{Qubit}) = 0.4286$
  - Leakage = $0.2585$
  - Verdict: **`REFUTED`** (`rule_holds = False`).

### C. Experiment 059 (Ramanujan-Einklang auf `ibm_fez` & `ibm_marrakesh`)
- **Fez (`db8sdv0b3g5c73egt2u0`):**  
  Zählung in Bin 32 ($a=32$, bitstring `100000`): 829 von 8192 Shots ($10.12\,\%$). Das registrierte Band lag bei $[21.33\,\%, 33.33\,\%]$.
  - Verdict: **`H-REM59-Q_REFUTED`**.
- **Marrakesh (`db8t34ob3g5c73egub5g`):**  
  Zählung in Bin 32: 506 von 8192 Shots ($6.18\,\%$).
  - Verdict: **`H-REM59-Q_REFUTED`**.
- **Interpretation:** Das isolierte Einzelbin-Signal wird durch die Gatter-Depolarisation auf beiden Backends in den thermischen Floor gewaschen. Dies motiviert unmittelbar die **Stepanov-Resonanz-Architektur aus EXP-060**, die über $L=\lfloor\sqrt{q}\rfloor$ Schritte hinweg eine robuste, mehrdimensionale Verstärkung erzeugt.

---

## 3. Epistemischer Status & Synthese
1. **Keine offenen / verlorenen QPU-Jobs mehr:**  
   Alle jemals auf IBM Quantum eingereichten Jobs wurden aufgespürt, ihre Rohdaten lokal gesichert und die gefrorenen Auswertungen durchgeführt.
2. **Quota-Schonung:**  
   Der gesamte Abgleich verbrauchte **0 Sekunden** an monatlicher QPU-Rechenzeit.
3. **Fundament für neue QPU-Experimente:**  
   Da nun alle historischen QPU-Ergebnisse erfasst sind, ist die Basis für das geplante minimale Spot-Check-Design zu EXPERIMENT 060 (Weil-Theta-Lift) transparent und lückenlos abgesichert.
