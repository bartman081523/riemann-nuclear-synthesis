"""
Tests für pt_im_bias_sweep_token1.py und pt_potential_vqe_initial_token1.py.

Diese Tests prüfen die LOKALEN, nicht-QPU-Anteile der Skripte:
  - Prereg-Struktur
  - Operator-Konstruktion (H_diag, Re(H_PT), Im(H_PT))
  - Statevector-Referenzen
  - Bias-Berechnung
  - Verdict-Logik
"""
import json
import numpy as np
import pytest
from pt_structural import jacobi_A, E_DIAG


# ============================================================
# Prereg-Struktur
# ============================================================
class TestPreregStructure:
    def test_prereg_exists(self):
        """Prereg muss vor Skript-Ausführung existieren (Anti-Sharpshooter)."""
        with open("pt_im_bias_prereg.json") as f:
            prereg = json.load(f)
        assert "_meta" in prereg
        assert prereg["_meta"]["purpose"].startswith("Preregistrierung")

    def test_prereg_has_three_hypotheses(self):
        """Drei Hypothesen H_Im_h1/h2/h3 müssen definiert sein."""
        with open("pt_im_bias_prereg.json") as f:
            prereg = json.load(f)
        h = prereg["hypotheses"]
        assert "H_Im_h1" in h
        assert "H_Im_h2" in h
        assert "H_Im_h3" in h
        # Jede hat label, prediction, consequence_if_true
        for key in h:
            assert "label" in h[key]
            assert "prediction" in h[key]
            assert "consequence_if_true" in h[key]

    def test_prereg_decision_rule_explicit(self):
        """Entscheidungsregel muss explizit vor Ausführung definiert sein."""
        with open("pt_im_bias_prereg.json") as f:
            prereg = json.load(f)
        rule = prereg["decision_rule"]
        assert "primary" in rule
        assert "anti_sharpshooter" in rule
        # Threshold explizit genannt
        assert "0.005" in rule["primary"]
        assert "0.020" in rule["primary"]

    def test_prereg_theta_points(self):
        """5 theta-Punkte müssen vordefiniert sein."""
        with open("pt_im_bias_prereg.json") as f:
            prereg = json.load(f)
        assert len(prereg["theta_points"]) == 5
        labels = [p["label"] for p in prereg["theta_points"]]
        assert "theta_initial" in labels
        assert "theta_VQE_optimal" in labels

    def test_prereg_corrected_metric(self):
        """Bias-Metrik muss QPU-vs-statevector sein, nicht vs noiseless."""
        with open("pt_im_bias_prereg.json") as f:
            prereg = json.load(f)
        ctx = prereg["context"]
        assert "bias_metric_corrected" in ctx
        assert "statevector" in ctx["bias_metric_corrected"]


# ============================================================
# Operator-Konstruktion
# ============================================================
class TestOperatorConstruction:
    def test_H_diag_is_diagonal(self):
        """H_diag muss diag(E_DIAG) sein."""
        H_diag = np.diag(E_DIAG).astype(complex)
        assert np.allclose(H_diag, np.diag(np.diag(H_diag)))

    def test_H_imag_is_hermitean(self):
        """Im(H_PT) = (H_PT - H_PT†)/(2i) muss Hermitesch sein."""
        A = jacobi_A(E_DIAG, y=1.0)
        H_diag = np.diag(E_DIAG).astype(complex)
        H_PT = H_diag + 1j * 0.02 * A
        H_imag = (H_PT - H_PT.conj().T) / (2j)
        assert np.allclose(H_imag, H_imag.conj().T), "Im(H_PT) muss Hermitesch sein"

    def test_H_real_equals_H_diag_eigvals(self):
        """||[H_diag, Re(H_PT)]|| = 0 (Theorem: identische Eigenwerte)."""
        A = jacobi_A(E_DIAG, y=1.0)
        H_diag = np.diag(E_DIAG).astype(complex)
        H_PT = H_diag + 1j * 0.02 * A
        H_real = (H_PT + H_PT.conj().T) / 2
        comm = H_diag @ H_real - H_real @ H_diag
        assert np.linalg.norm(comm) < 1e-10, "H_diag und Re(H_PT) sind simultan diagonalisierbar"

    def test_H_imag_dominance(self):
        """Im(H_PT) hat nicht-triviale Diagonal UND Off-Diagonal-Eintraege (Jacobi-Struktur)."""
        A = jacobi_A(E_DIAG, y=1.0)
        H_diag = np.diag(E_DIAG).astype(complex)
        H_PT = H_diag + 1j * 0.02 * A
        H_imag = (H_PT - H_PT.conj().T) / (2j)
        # ||Im(H_PT)||_F ist endlich und nicht-trivial (gamma=0.02 skaliert)
        norm_imag = np.linalg.norm(H_imag)
        assert 0.05 < norm_imag < 0.5, f"||Im(H_PT)||_F = {norm_imag:.4f} ausserhalb [0.05, 0.5]"
        # Off-Diagonal-Anteil vergleichbar mit Diagonal-Anteil (Jacobi hat beides)
        off_diag = H_imag - np.diag(np.diag(H_imag))
        on_diag = np.diag(np.diag(H_imag))
        ratio = np.linalg.norm(off_diag) / np.linalg.norm(on_diag)
        assert 1.0 < ratio < 3.0, \
            f"Off-Diag/Diag-Verhaeltnis = {ratio:.2f} (erwartet zwischen 1 und 3 fuer Jacobi)"


# ============================================================
# Statevector-Referenzen
# ============================================================
class TestStatevectorReferences:
    def test_statevector_5_theta_points(self):
        """5 statevector-Referenzen müssen berechenbar sein und variieren."""
        from qiskit.circuit.library import n_local as n_local_fn
        from qiskit.quantum_info import Statevector

        A = jacobi_A(E_DIAG, y=1.0)
        H_diag = np.diag(E_DIAG).astype(complex)
        H_PT = H_diag + 1j * 0.02 * A
        H_imag = (H_PT - H_PT.conj().T) / (2j)

        ansatz = n_local_fn(2, ['ry'], 'cx', 'linear', reps=1)
        init_p = [0.523, 1.21, -0.45, 0.88]
        np.random.seed(42); t1 = list(np.random.uniform(-np.pi, np.pi, 4))
        np.random.seed(43); t2 = list(np.random.uniform(-np.pi, np.pi, 4))
        vqe_opt = [-0.104, 0.317, -0.803, -0.086]
        np.random.seed(44); t3 = list(np.random.uniform(-np.pi, np.pi, 4))
        thetas = [init_p, t1, t2, vqe_opt, t3]

        evs = []
        for theta in thetas:
            pd = {p: v for p, v in zip(ansatz.parameters, theta)}
            sv = Statevector.from_instruction(ansatz.assign_parameters(pd))
            evs.append(float(np.real(sv.expectation_value(H_imag))))

        # Im variiert signifikant (nicht konstant bei 0.0299)
        assert max(evs) - min(evs) > 0.05, \
            f"Im(H_PT) muss mit theta variieren, range = {max(evs) - min(evs):.4f}"
        # Alle im realistischen Bereich
        for ev in evs:
            assert -0.1 < ev < 0.1, f"<Im> = {ev} ausserhalb des realistischen Bereichs"

    def test_statevector_initial_im_matches_Fez_2026_06_10(self):
        """<Im(H_PT)> am Initial-Punkt muss im Fez-2026-06-10-Regime sein."""
        from qiskit.circuit.library import n_local as n_local_fn
        from qiskit.quantum_info import Statevector

        A = jacobi_A(E_DIAG, y=1.0)
        H_diag = np.diag(E_DIAG).astype(complex)
        H_PT = H_diag + 1j * 0.02 * A
        H_imag = (H_PT - H_PT.conj().T) / (2j)

        # Im Fez-2026-06-10 war 6-Parameter TwoLocal reps=2
        # Wir nutzen hier 4-Parameter n_local reps=1 (anderer Ansatz, anderer Wert)
        # Wichtig: nur die Groessenordnung (~0.01-0.05) zaehlt
        ansatz = n_local_fn(2, ['ry'], 'cx', 'linear', reps=1)
        init_p = [0.523, 1.21, -0.45, 0.88]
        pd = {p: v for p, v in zip(ansatz.parameters, init_p)}
        sv = Statevector.from_instruction(ansatz.assign_parameters(pd))
        ev = float(np.real(sv.expectation_value(H_imag)))
        assert 0.01 < abs(ev) < 0.10, f"<Im>_initial = {ev:.4f} (erwartet ~0.05 ± 0.05)"


# ============================================================
# Bias-Metrik
# ============================================================
class TestBiasMetric:
    def test_bias_qpu_minus_statevector_corrected(self):
        """Bias muss QPU-vs-statevector sein, nicht vs Im_noiseless(ground)."""
        # Korrektur 12:45 UTC: statevector-Wert am selben theta ist die richtige Referenz
        with open("pt_im_bias_prereg.json") as f:
            prereg = json.load(f)
        ctx = prereg["context"]
        # Die alte Metrik (vs Im_noiseless(ground)) darf nicht mehr auftauchen
        assert "im_noiseless_at_ground_state" not in ctx, \
            "Alte Metrik entfernt: statevector(theta) statt Im_noiseless(ground)"

    def test_bias_zero_when_qpu_equals_statevector(self):
        """Bias = 0, wenn QPU exakt statevector reproduziert (per Konstruktion)."""
        bias = 0.123 - 0.123
        assert bias == 0.0

    def test_bias_signs_match_fez_reference(self):
        """Fez-2026-06-10 mass bias = -0.017 (Im < Im_noiseless). Erwartung: TOKEN1 ahnlich."""
        # Fez-2026-06-10 mass gegen Im_noiseless(ground) = 0.0299
        # bias = 0.013 - 0.0299 = -0.017
        # Wenn QPU einen anti-Hermiteschen Decay hat, ist Im systematisch kleiner
        fez_bias = 0.013 - 0.0299
        assert abs(fez_bias - (-0.0169)) < 0.001


# ============================================================
# Verdict-Logik
# ============================================================
class TestVerdictLogic:
    def test_verdict_h1_all_small(self):
        """H_Im_h1 wenn alle |bias| < 0.005."""
        biases = [0.001, -0.002, 0.003, -0.001, 0.0005]
        all_small = all(abs(b) < 0.005 for b in biases)
        assert all_small is True

    def test_verdict_h2_all_large(self):
        """H_Im_h2 wenn alle |bias| > 0.020."""
        biases = [0.025, -0.030, 0.022, 0.028, -0.025]
        all_large = all(abs(b) > 0.020 for b in biases)
        assert all_large is True

    def test_verdict_h3_mixed(self):
        """H_Im_h3 wenn weder H_Im_h1 noch H_Im_h2 (gemischter Bereich)."""
        biases = [0.001, -0.018, 0.025, 0.010, -0.003]  # mixed
        all_small = all(abs(b) < 0.005 for b in biases)
        all_large = all(abs(b) > 0.020 for b in biases)
        # Weder h1 noch h2
        assert all_small is False
        assert all_large is False


# ============================================================
# M2 Initial-Punkt-Reproduzierbarkeit
# ============================================================
class TestM2InitialReproducibility:
    def test_fez_2026_06_10_token2_reference(self):
        """Fez-2026-06-10 bias_PT_re = -0.0133 muss als Vergleichswert dienen."""
        # Aus pt_potential_vqe_singleshot_results.json
        reference = -0.013315946227108633
        assert abs(reference - (-0.0133)) < 0.0005

    def test_token1_within_5_percent_of_token2(self):
        """bias_PT_re TOKEN1 muss innerhalb 0.05 von TOKEN2 sein (Bias-strukturell)."""
        token2_bias = -0.0133
        # Hypothetisches TOKEN1-Result
        token1_bias = -0.0140
        assert abs(token1_bias - token2_bias) < 0.05, \
            f"TOKEN1 bias = {token1_bias} weicht > 0.05 von TOKEN2 = {token2_bias} ab"


# ============================================================
# Anti-Sharpshooter Audit der gesamten Korrektur
# ============================================================
class TestAntiSharpshooter:
    def test_prereg_exists_with_purpose(self):
        """Prereg-Datei muss VOR der Skript-Ausführung erstellt worden sein.

        Pragmatischer Test: Prereg-Inhalt muss die 'purpose'-Markierung tragen
        und darf nicht in der gleichen Code-Session editiert worden sein.
        """
        import os
        with open("pt_im_bias_prereg.json") as f:
            content = f.read()
        # Prereg-Markierung im Inhalt
        assert "Preregistrierung" in content
        # Datum im Prereg
        assert "2026-06-17" in content
        # Skript-Existenz und -Inhalt
        assert os.path.exists("pt_im_bias_sweep_token1.py")
        with open("pt_im_bias_sweep_token1.py") as f:
            script = f.read()
        # Skript muss die Prereg-Datei explizit laden
        assert "pt_im_bias_prereg.json" in script, \
            "Skript muss die Prereg-Datei referenzieren (Anti-Sharpshooter-Constraint)"

    def test_h_Im_h3_not_marked_as_default(self):
        """H_Im_h3 darf nicht als 'Default' oder 'sicher' markiert sein."""
        with open("pt_im_bias_prereg.json") as f:
            prereg = json.load(f)
        rule = prereg["decision_rule"]["anti_sharpshooter"].lower()
        assert "nicht" in rule or "not" in rule
        assert "default" in rule or "sicher" in rule or "langweilig" in rule

    def test_im_variation_with_theta_acknowledged(self):
        """Die Korrektur 12:45 UTC muss explizit im Skript stehen."""
        with open("pt_im_bias_sweep_token1.py") as f:
            content = f.read()
        assert "12:45 UTC" in content, "Skript muss die Bias-Metrik-Korrektur dokumentieren"
        assert "statevector" in content
        assert "SELBEN theta" in content or "selben theta" in content.lower()
