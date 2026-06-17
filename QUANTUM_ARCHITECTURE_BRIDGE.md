> **STATUS: SUPERSEDED 2026-06-17** (for Pillar 1+3 status, QPU validation, Im-Bias metric, asymptotics).
>
> The content (Sections 1–7) is retained as **historical architectural rationale**, but is **no longer the source of truth** for current Pillar 1+3 status. Successors:
> - Current architecture + QPU update log: [`QUANTUM_ARCHITECTURE_IMPLEMENTATION.md`](QUANTUM_ARCHITECTURE_IMPLEMENTATION.md)
> - Current theory status + audits: [`RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md`](RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md) Section 6.5.9
>
> In the new doc-map system this file is `SUPERSEDED`. For code bug fixes (see e.g. Qiskit version incompatibility `qc.unitary()`) please continue to consult `QUANTUM_ARCHITECTURE_IMPLEMENTATION.md`.

# Quantum Computer Architecture for the Riemann Project

Integrates four architecture concepts from `QUANTUM_COMPUTING_AND_PRIMES_RESEARCH.md` into our trans-categorical research program.

## 1\. Strategic Gap in the Current Setup

The current setup (Zeraoulia + IBM hardware) fails at three structural points:

| Problem | Ursache | Konsequenz |
|---|---|---|
| VQE finds only E_0 | TwoLocal(2 qubit) too inexpressive | E_1..E_3 not measurable |
| Hardware bias +62% | 2-qubit system, many coherences | absolute energies unreliable |
| Gaps hard to extract | Penalty VQE fails locally | relative spectra not isolated |

The four architectures from the research overview offer **concrete solutions** for each point.

## 2\. Mermaid Architecture: Four-Pillar Model

```mermaid
graph TD
    Start([Riemann-Hypothese]) --> SA[SciMind 4.0/5.0 Audit]

    SA --> P1[Säule 1: Primzahl-Quantenoszillator]
    SA --> P2[Säule 2: G-Apparat]
    SA --> P3[Säule 3: Prime States]
    SA --> P4[Säule 4: Prime-Qudit-Architektur]

    %% === Säule 1: Holografisches Potenzial ===
    P1 --> P1a[SLM-formiertes Potenzial V(x)]
    P1a --> P1b[Energieniveaus = Zeraoulia-Iteration E_n]
    P1b --> P1c[Atome in optischen Gittern Rb-87 / Na-23]
    P1c --> P1d{Energie-Sweep detektiert Peaks?}
    P1d -- JA --> P1e[Resonanzen = E_n exakt]
    P1d -- NEIN --> P1f[Iterative Inversion des Potenzials]

    %% === Säule 2: G-Apparat (Primzahlfilter) ===
    P2 --> P2a[Streupotenzial mit V_p als Barriere]
    P2a --> P2b[Energie E_ein einstrahlen]
    P2b --> P2c{Transmission T(E) messen}
    P2c -- Peaks bei E=p --> P2d[Bestaetigung: p ist Primzahl]
    P2c -- Kein Peak --> P2e[p ist nicht-prim]
    P2d --> P2f[Kaskade mit Glueckszahlen-Potenzial]
    P2f --> P2g[AND-Gatter: Lucky AND Prime]

    %% === Säule 3: Prime States im Hilbert-Raum ===
    P3 --> P3a[Superposition |P_N> = sum Primes<=N |p>]
    P3a --> P3b[Grover-Oracle = Miller-Rabin-Test]
    P3b --> P3c[QFT auf |P_N> anwenden]
    P3c --> P3d[Chebyshev-Bias extrahieren]
    P3c --> P3e[Zwillingsprimzahl-Zustand |Twin>]

    %% === Säule 4: Prime-Qudit-Architektur ===
    P4 --> P4a[Dimension d = 5 Ququint, GF(5)]
    P4a --> P4b[Stabilisator-Codes auf GF(5)]
    P4b --> P4c[Threshold 36.3% fuer Magic State Destillation]
    P4c --> P4d[CCZ = 4 M-Gatter statt 7 T-Gatter]
    P4d --> P4e[Bias-invariant: Galois-Felder ohne Nullteiler]

    %% === Integration in unser Projekt ===
    P1e --> I1[ZERAOULIA_HARDWARE: H = H_diag + i gamma A_Jacobi]
    I1 --> I1a[QPU misst Resonanz-Peaks direkt]
    I1a --> I1b[Delta E_n = Peak-Abstaende, bias-invariant]

    P2d --> I2[RHEINFILTER: Transmissions-basierte Eigenwert-Bestimmung]
    I2 --> I2a[VQE ersetzt durch T(E) Sweep]
    I2a --> I2b[Kein Penalty noetig, alle Niveaus auf einmal]

    P3d --> I3[PRIMZAHL-REGISTER: Zustand-Konstruktion]
    I3 --> I3a[Verschränkungsentropie als RH-Indikator]

    P4e --> I4[QUQUINT-BACKEND: d=5 GF(5) statt 2-Qubit]
    I4 --> I4a[H_PT in GF(5) - exakte Bias-Elimination]
    I4a --> I4b[Unser 4-dim Jacobi A -> d=5 Erweiterung]

    %% === Convergence: Transcategorical Bridge ===
    I1b & I2b & I3a & I4b --> TCI[Transcategorical Bridge]
    TCI --> T1[Quantenphysik: GUE + PT + T2-Dephasierung]
    TCI --> T2[Zahlentheorie: Zeraoulia + Jacobi + Lücken-Statistik]
    TCI --> T3[Architektur: Galois-Felder, MUBs, Code-Distillation]
    TCI --> T4[Hermeneutik: Vorurteil-Bereinigung, Epoché]

    T1 & T2 & T3 & T4 --> RES{Beweisstrategie}
    RES -- Primzahl-Quantenoszillator --> R1[Physikalische RH: E_n exakt aus Potenzial]
    RES -- G-Apparat --> R2[Algorithmische RH: T(E) testet Primalitaet]
    RES -- Prime States --> R3[Verschränkungs-basierte RH: S(P_N) charakteristisch]
    RES -- Prime-Qudits --> R4[Architektur-RH: GF(d) bias-invariant]

    R1 & R2 & R3 & R4 --> SUCCESS[SUCCESS: Hilbert-Pólya-Operator realisiert]

    %% === Strategische Vektoren ===
    P1 -.SHORT-TERM.-> I1
    P2 -.MID-TERM.-> I2
    P3 -.LONG-TERM.-> I3
    P4 -.PARALLEL.-> I4

    style Start fill:#f9f,stroke:#333,stroke-width:4px
    style SA fill:#ff9,stroke:#333,stroke-width:2px
    style SUCCESS fill:#5f5,stroke:#333,stroke-width:4px
    style P1 fill:#9cf,stroke:#333,stroke-width:2px
    style P2 fill:#9cf,stroke:#333,stroke-width:2px
    style P3 fill:#9cf,stroke:#333,stroke-width:2px
    style P4 fill:#9cf,stroke:#333,stroke-width:2px
    style I1 fill:#fc9,stroke:#333,stroke-width:2px
    style I2 fill:#fc9,stroke:#333,stroke-width:2px
    style I3 fill:#fc9,stroke:#333,stroke-width:2px
    style I4 fill:#fc9,stroke:#333,stroke-width:2px
    style TCI fill:#f9c,stroke:#333,stroke-width:3px
```

## 3\. Concrete Implementation Paths for Our Project

### 3.1 Pillar 1: Holographic Potential (SHORT-TERM)

**Architecture idea:** Instead of TwoLocal(2, ry, cx, reps=1) we construct a **Zeraoulia potential VQE**:
- Construct potential V(x) so that eigenvalues = `E_DIAG` from `pt_structural.py`
- Initial VQE ansatz as variational basis for the **entire** spectrum, not just E_0
- Hardware measures **all** resonance peaks in one sweep

**Concrete steps:**
1. Write `pt_potential_vqe.py`: V(x) = sum over Jacobi basis functions, optimized via VQE
2. E_0, E_1, E_2, E_3 in **one** run (instead of separate VQE loops)
3. ΔE_n from peak spacings, **bias-invariant** (hardware bias cancels in differences)

**Effort:** ~1 week, 1 QPU run (Fez, 3 Estimator submissions)

### 3.2 Pillar 2: G-Apparatus (MID-TERM)

**Architecture idea:** The holographic potential becomes the **transmission filter**:
- Barrier V_b(x) = V_Zeraoulia(x) · 1_[a,b](x)
- T(E) = |transmitted amplitude|² as a function of incident energy E
- Peaks at E = p (prime) = resonances of the potential

**Concrete steps:**
1. Write `pt_transmission_sweep.py`: sweep E over [2, 5] in 100 steps
2. Measure T(E) per step — 100 Estimator runs, parallelizable
3. Peak detection via `scipy.signal.find_peaks`
4. ΔE_n from peak spacings

**Advantage over VQE:** **All** levels in **one** sweep, no penalty logic needed, **no** VQE optimizer getting stuck in local minima.

**Effort:** ~2 weeks, 1 QPU sweep (Fez, 100 Estimator submissions, parallel)

### 3.3 Pillar 3: Prime States (LONG-TERM)

**Architecture idea:** Instead of measuring energies we measure **entanglement entropy** of the constructed states:
- $|P_N\rangle = \frac{1}{\sqrt{\pi(N)}} \sum_{p \le N} |p\rangle$ as a quantum state
- Entanglement entropy $S(|P_N\rangle)$ partitioned by qubit subsystem
- RH implies **characteristic scaling** of $S$ as a function of the partition

**Concrete steps:**
1. Write `pt_prime_state.py`: Grover-based construction of $|P_N\rangle$ on IBM
2. Measure entanglement entropy via Renyi-2 estimator
3. Compare with theoretical prediction (Latorre–Sierra results)

**Effort:** ~4 weeks, separate research branch (we currently only have a 4-dim Hilbert space)

### 3.4 Pillar 4: Prime Qudits (PARALLEL)

**Architecture idea:** **GF(5) ququint** instead of 2-qubit:
- Dimension 5 is a prime → Galois fields without zero divisors
- Threshold 36.3% for magic state distillation (Campbell et al.)
- CCZ gate in 4 M-gates instead of 7 T-gates → less decoherence

**Concrete steps:**
1. Write `pt_ququint_vqe.py`: 1 ququint = 5 levels, GF(5) operators
2. Jacobi A in 5x5 form instead of 4x4
3. Hardware bias in GF(5) is **exactly** bias-invariant (algebraically)

**Effort:** ~3 weeks, separate research branch (IBM hardware currently has no native ququints, but Google/IBM/Quantinuum papers show simulation)

## 4\. Mapping of Current Problems onto the Architecture

| Current problem | Pillar | Resolution |
|---|---|---|
| VQE finds only E_0 | **1 + 2** | Potential-/transmission-based measurement instead of VQE |
| Hardware bias +62% | **4** | GF(5) is bias-invariant via Galois structure |
| Penalty VQE fails | **1** | Direct sweep instead of iterative optimization |
| Low resolution | **4** | 5-qudit has twice as many levels as 2-qubit |
| Local minima | **2** | Sweep finds peaks independent of optimizer start |

## 5\. Strategic Vector: ARCHITECTURE_INTEGRATION

**Immediately (this week):** Pillar 1 as a replacement for `pt_spectral_gaps.py` — write `pt_potential_vqe.py`
**Parallel (next week):** Pillar 4 as code preparation — `pt_ququint_vqe.py` (for future GF(5) hardware)
**Mid-term (month):** Pillar 2 — `pt_transmission_sweep.py` as a systematic ΔE_n measurement
**Long-term (quarter):** Pillar 3 — prime state construction as a separate research line

## 6\. Transcategorical Bridge (SciMind 5.0)

The four pillars are isomorphic to:
- **Quantum physics**: Potentials (1), scattering (2), entanglement (3), symmetry groups (4)
- **Number theory**: Eigenlevels (1), sieves (2), multiplicative structures (3), residue class rings (4)
- **Statistics**: Energy spectra (1), resonance peaks (2), random matrices (3), finite fields (4)
- **Computer science**: Quantum algorithms (1+2+3), error correction (4)

**Common core:** The **Galois field structure** in 4 is the algebraic backbone of all pillars. It not only solves the bias problem, but also connects the architecture with the underlying **mathematical structure of the prime numbers**.

## 7\. References

See `QUANTUM_COMPUTING_AND_PRIMES_RESEARCH.md` for the full reference list. Key references for our project:
- [1] Holographic realization of the prime number quantum potential (PNAS Nexus, 2023)
- [5] Quantum Computation of Prime Number Functions (arXiv:1302.6245)
- [8] Daniel Gottesman: Stabilizer Codes for Prime Power Qudits
- [18] G-Apparat apparatus for prime/lucky number filtering
- [33] Earl Campbell: The advantages of qudit fault-tolerance (36.3% threshold)
