# Forschungs- und Experiment-Dokumentation (Alpöge-Claude Beweis-Synthese)

Dieses Verzeichnis enthält die strukturierte Dokumentation, Vergleiche und Resultats-Matrizen für die Riemann-Hypothese-Quantensynthese auf dem Beweisstand des Alpöge-Claude Lean-4-Beweises (Stepanov-Methode, Weil-Schranken und algebraische Theta-Ketten).

## Dokumenten-Index

1. **[Alpöge-Claude vs. Riemann-Synthese Vergleich](comparison_alpoge_riemann_synthesis.md)**
   - Detaillierter Vergleich der 4 Kernsäulen des Alpöge-Claude Lean-4-Beweises mit der quantenmechanischen Umsetzung in `primequant`.
   - Übersetzungstabelle: Stepanov-Multiplizität $\leftrightarrow$ Pfadtiefe $L = \lfloor\sqrt{q}\rfloor$, Weil-Gauss-Summen $\leftrightarrow$ Quadratische Phasen $e_q(h Q(x))$, Deligne-Schranke $\leftrightarrow$ GGP-Spektrallücke.

2. **[Preregistrierungs-Schärfungsplan (Weil-Theta-Lift)](prereg_sharpening_weil_theta.md)**
   - Mathematische Definition der Weil-Darstellung $Mp_2(\mathbb{F}_q)$ über zyklotomischen Ringen $\mathbb{Z}[\zeta_q]$.
   - Galois-Projektor $\Pi_G$, Trace-Gram-Matrizen und quantitative Falsifikationskriterien.

3. **[Master-Matrix aller Experimente & QPU-Ergebnisse](experiments_and_qpu_results_matrix.md)**
   - Lückenlose Zuordnung aller historischen und aktuellen IBM Quantum Jobs (Backends, Job-IDs, Tokens, Rohdaten und Evaluations-Verdicts).
   - Inklusive der 160-Circuit-Jobs (EXP-055), Ramanujan-Einklang (EXP-059) und der neuen Serie EXP-060 bis EXP-063.

4. **[Beweis- und Aufgaben-Ledger](task_alpoge_proof_ladder.md)**
   - Vollständiger Task- und Status-Tracker über alle Phasen der Implementierung, Verifikation und Hardware-Validierung.

## Zusammenfassung der Experiment-Serie EXP-060 bis EXP-063

| Experiment | Bezeichnung | Methode / Backend | Status / Urteil | Kernaussage |
|---|---|---|---|---|
| **EXP-060** | Weil-Theta-Lift / Stepanov-Resonanz | Statevector ($q \in \{2,3,5,7,11\}$) | **`CONFIRMED_ALL_HYPOTHESES`** | Exakte Trace-Gram-Invarianz, resonanter Peak bei $L=\lfloor\sqrt{q}\rfloor$, Entanglement-Entropie robust unter Depolarisation. |
| **EXP-061** | Pfad-Quadriken & Weil-Sättigung | Statevector / Clifford-Kette | `MIXED` | Bit-exakte Gleichheit von Ramanujan-Summen mit Deligne-Charaktersummen ($|G|^2 = q^k$); Inversions-Swap präzise aufgedeckt. |
| **EXP-062** | Von-Mangoldt-Zustand & GRH-Decay | Statevector / Exakte Arithmetik | `REFUTED` (Popperianisch) | Chebyshev-Bias / Prime-Race-Fluktuationen identifiziert: Skalierung folgt $O(\ln^2 X / X)$ statt naivem $O(1/X)$. |
| **EXP-063** | Clifford-Weil Walk auf Hardware | Real QPU (`ibm_fez`, Job `dc1f7ids2omc738ahl0g`) | **`CONFIRMED_ALL_HYPOTHESES`** | Reale Extinktions-Resonanz von $P_{L=2}(q_0=0) = \mathbf{98.08\%}$ bei nur $10.49\text{ s}$ Quota-Verbrauch. |
| **EXP-064** | Artin-Schreier & Deligne-Schranken | Statevector / $\mathbb{Z}[\zeta_q]$ ($q \le 19$) | **`CONFIRMED_ALL_HYPOTHESES`** | Exakte Gauß-Sättigung $|S|^2 = q \cdot 1$; Deligne-Schranke $\le 4q$ für Weierstraß-Kubiken über alle Galois-Einbettungen lückenlos verifiziert. |
| **EXP-065** | Logarithmische Entropie-Asymptotik | Statevector ($N \le 16383$) | **`CONFIRMED_ALL_HYPOTHESES`** | Latorre-Sierra-Spannung analytisch geschlossen: $S_{vN} = 0.5967 \ln(N) - 0.8972$ mit $R^2=0.9955$; $\alpha \to 1$ fundamental widerlegt. |
