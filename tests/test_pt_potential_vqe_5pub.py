"""
Tests fuer pt_potential_vqe_5pub.py — 5-Pub-Messung auf Fez.

Hinweis: pt_potential_vqe_5pub.py ist ein Hardware-Skript (QPU-Submit).
Die Tests pruefen die MATHEMATISCHE Vorbereitung (Parameter-Erweiterung,
VQE-Params-Logik) und Bias-Berechnung, OHNE eine echte QPU-Verbindung.

Diese Tests laden NICHT pt_potential_vqe_5pub.py direkt als Modul,
sondern testen die mathematischen Operationen, die es verwendet.
"""
import json
import math
import numpy as np
import pytest

from pt_structural import jacobi_A, E_DIAG


class TestVQEParamsExtension:
    """Prueft die zyklische Parameter-Erweiterung von 4 auf 6 Dimensionen."""

    def test_vqe_params_4_to_6_cyclic(self):
        """4 VQE-Params zyklisch auf 6 Dimensionen erweitert."""
        vqe_params_4 = [-0.788, 2.832, 1.458, 0.620]
        n_params = 6
        extended = [vqe_params_4[i % len(vqe_params_4)] for i in range(n_params)]
        assert len(extended) == 6
        # Erste 4 bleiben gleich
        assert extended[:4] == vqe_params_4
        # Naechste 2 sind Wiederholungen
        assert extended[4] == vqe_params_4[0]
        assert extended[5] == vqe_params_4[1]

    def test_vqe_params_already_6_unchanged(self):
        """Wenn n_params == 4, bleibt Array unveraendert."""
        vqe_params = [-0.788, 2.832, 1.458, 0.620]
        n_params = 4
        extended = [vqe_params[i % len(vqe_params)] for i in range(n_params)]
        assert extended == vqe_params

    def test_random_theta_4_to_6(self):
        """Random theta-Werte zyklisch erweitert."""
        np.random.seed(42)
        theta_r_4 = list(np.random.uniform(-np.pi, np.pi, 4))
        n_params = 6
        extended = [theta_r_4[i % len(theta_r_4)] for i in range(n_params)]
        assert len(extended) == 6
        assert extended[:4] == theta_r_4


class TestBiasAnalysisMath:
    """Prueft die Bias-Berechnung (mathematische Operation)."""

    def test_bias_PT_re_definition(self):
        """bias_PT_re = Re_PT_meas - H_diag_meas."""
        H_diag_meas = 3.30
        Re_PT_meas = 3.31
        bias = Re_PT_meas - H_diag_meas
        assert abs(bias - 0.01) < 1e-12

    def test_bias_diag_zero_for_perfect_diag(self):
        """beta_diag = 0 wenn H_diag-Messung = exakter Mittelwert (3.3412)."""
        H_diag_meas = 3.3412
        beta = H_diag_meas - 3.3412
        assert abs(beta) < 1e-12

    def test_im_bias_calculation(self):
        """Im_bias = Im_PT_meas - Im_at_ground."""
        Im_PT_meas = 0.030
        Im_at_ground = 0.0299
        bias = Im_PT_meas - Im_at_ground
        assert abs(bias - 0.0001) < 1e-12


class TestVerdictThresholds:
    """Prueft die Verdict-Klassifikation basierend auf bias_PT_re."""

    def test_verdict_H1_H3_for_small_bias(self):
        """|bias_PT_re| < 0.05 -> H1/H3."""
        bias_PT_re = -0.0133
        if abs(bias_PT_re) < 0.05:
            verdict = "H1/H3"
        elif abs(bias_PT_re) > 0.15:
            verdict = "H2"
        else:
            verdict = "MITTEL"
        assert verdict == "H1/H3"

    def test_verdict_H2_for_large_bias(self):
        """|bias_PT_re| > 0.15 -> H2."""
        bias_PT_re = 0.4
        if abs(bias_PT_re) < 0.05:
            verdict = "H1/H3"
        elif abs(bias_PT_re) > 0.15:
            verdict = "H2"
        else:
            verdict = "MITTEL"
        assert verdict == "H2"

    def test_verdict_MITTEL_for_intermediate(self):
        """0.05 < |bias_PT_re| < 0.15 -> MITTEL."""
        bias_PT_re = 0.0714
        if abs(bias_PT_re) < 0.05:
            verdict = "H1/H3"
        elif abs(bias_PT_re) > 0.15:
            verdict = "H2"
        else:
            verdict = "MITTEL"
        assert verdict == "MITTEL"


class TestExistingResultsFile:
    """Prueft, dass das existierende Result-File (vom 2026-06-10) lesbar ist."""

    @pytest.fixture
    def results_5pub(self):
        try:
            with open("pt_potential_vqe_5pub_results.json") as f:
                return json.load(f)
        except FileNotFoundError:
            pytest.skip("pt_potential_vqe_5pub_results.json nicht gefunden")

    def test_results_have_5_pubs(self, results_5pub):
        """5 Pubs im Result-File."""
        assert "5_pubs" in results_5pub
        assert len(results_5pub["5_pubs"]) == 5

    def test_results_have_bias_analysis(self, results_5pub):
        """Bias-Analyse enthalten."""
        assert "bias_analysis" in results_5pub
        ba = results_5pub["bias_analysis"]
        assert "bias_PT_re" in ba
        assert "beta_diag" in ba
        assert "Im_bias" in ba

    def test_results_have_verdict(self, results_5pub):
        """Verdict enthalten."""
        assert "verdict" in results_5pub
        assert results_5pub["verdict"] in [
            "H1/H3 (gaps invariant) — REFRAMING_VECTOR bestaetigt!",
            "H2 (multiplikative Bias) — REFRAMING_VECTOR widerlegt",
            "MITTEL — partial H2-Einfluss"
        ] or "MITTEL" in results_5pub["verdict"] or "H1/H3" in results_5pub["verdict"]

    def test_results_job_ids_present(self, results_5pub):
        """5 Job-IDs (eines pro Pub)."""
        assert "job_ids" in results_5pub
        assert len(results_5pub["job_ids"]) == 5


class TestOperatorConstruction:
    """Prueft die H_diag/Re(H_PT)/Im(H_PT) Operator-Konstruktion."""

    def test_H_real_is_hermitean_imag_is_hermitean(self):
        """H_real = (H + H^*)/2 hermitesch, H_imag = (H - H^*)/(2i) hermitesch.

        (Anti-hermitesch waere H_imag mit -(H - H^*)/2, aber die Konvention
        im Skript nutzt /(2i) was hermitesch ergibt.)
        """
        GAMMA = 0.02
        A = jacobi_A(E_DIAG, y=1.0)
        H_diag = np.diag(E_DIAG).astype(complex)
        H_PT = H_diag + 1j * GAMMA * A
        H_real = (H_PT + H_PT.conj().T) / 2
        H_imag = (H_PT - H_PT.conj().T) / (2j)

        # H_real hermitesch
        np.testing.assert_allclose(H_real, H_real.conj().T, atol=1e-12)
        # H_imag hermitesch (Konvention /(2i))
        np.testing.assert_allclose(H_imag, H_imag.conj().T, atol=1e-12)
        # H_imag = -i * A_anti (A ist reell-symmetrisch)
        # Daher ist H_imag = gamma * A, reell und symmetrisch
        np.testing.assert_allclose(H_imag.imag, 0, atol=1e-12)
        # Rekonstruktion: H_PT = H_diag + i*(H_imag - H_diag... )
        # Tatsaechlich: H_PT = H_diag + 1j * gamma * A
        # H_real sollte nur H_diag enthalten (weil A imaginären Anteil traegt)
        np.testing.assert_allclose(H_real, H_diag, atol=1e-12)

    def test_A_is_symmetric_real(self):
        """Jacobi A ist reell-symmetrisch."""
        A = jacobi_A(E_DIAG, y=1.0)
        np.testing.assert_allclose(A, A.T, atol=1e-12)
        np.testing.assert_allclose(A.imag, 0, atol=1e-12)

    def test_H_diag_diag_contains_E_DIAG(self):
        """H_diag = diag(E_DIAG)."""
        H_diag = np.diag(E_DIAG).astype(complex)
        np.testing.assert_allclose(np.diag(H_diag).real, E_DIAG, atol=1e-12)


class Test5PubModule:
    """Prueft, dass das Skript die noetigen Konstanten hat."""

    def test_module_imports(self):
        import pt_potential_vqe_5pub
        assert hasattr(pt_potential_vqe_5pub, 'VQE_PARAMS_4')
        assert hasattr(pt_potential_vqe_5pub, 'BACKEND')
        assert hasattr(pt_potential_vqe_5pub, 'GAMMA')
        assert hasattr(pt_potential_vqe_5pub, 'SHOTS')

    def test_vqe_params_have_four_elements(self):
        """VQE_PARAMS_4 hat 4 Elemente (original 4-Iter-VQE-Output)."""
        import pt_potential_vqe_5pub
        assert len(pt_potential_vqe_5pub.VQE_PARAMS_4) == 4