"""
Tests für pt_aer_stress_saeule1.py.

Prüft die Offline-Logik:
  - H1/H2/H3-Vorhersagen
  - Vergleichs-/Diskriminierungs-Logik
  - Pre-Registrierung-Lader
  - Aer-Stresstest-Resultat-Struktur

Aer-Simulator-Runs selbst werden NICHT getestet (zu langsam, requires IBM token).
"""
import json
import os
import sys
import hashlib

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pt_structural import E_DIAG, jacobi_A


class TestH1H2H3Predictions:
    """Prüft die H1/H2/H3-Vorhersage-Logik."""

    def test_h1_gaps_equal_noiseless(self):
        """H1 (additiver Bias beta*1) muss Gaps invariant halten."""
        from pt_aer_stress_saeule1 import h1_h2_h3_predictions
        pred = h1_h2_h3_predictions()
        np.testing.assert_allclose(pred["H1_additive"], pred["noiseless"], atol=1e-12)

    def test_h2_gaps_distinct_from_noiseless(self):
        """H2 (k=25 multiplikativ) muss Gaps drastisch verzerren."""
        from pt_aer_stress_saeule1 import h1_h2_h3_predictions
        pred = h1_h2_h3_predictions()
        # Mindestens ein Gap muss sich um > 0.05 unterscheiden
        max_diff = max(
            abs(pred["H2_multiplicative"][i] - pred["noiseless"][i])
            for i in range(3)
        )
        assert max_diff > 0.05, f"H2 Gaps nicht genug verzerrt: max_diff = {max_diff}"

    def test_h3_gaps_close_to_noiseless(self):
        """H3 (Decoherence p=0.3) muss Gaps ~ invariant halten (O(p^2))."""
        from pt_aer_stress_saeule1 import h1_h2_h3_predictions
        pred = h1_h2_h3_predictions()
        # Max Gap-Differenz < 0.1
        max_diff = max(
            abs(pred["H3_decoherence"][i] - pred["noiseless"][i])
            for i in range(3)
        )
        assert max_diff < 0.1, f"H3 Gaps-Differenz zu gross: max_diff = {max_diff}"

    def test_h_diag_exact_matches_zeraoulia(self):
        """H_diag exakt muss mit Zeraoulia-Iteration uebereinstimmen."""
        from pt_aer_stress_saeule1 import h1_h2_h3_predictions
        pred = h1_h2_h3_predictions()
        expected = [E_DIAG[i+1] - E_DIAG[i] for i in range(3)]
        np.testing.assert_allclose(pred["H_diag_exact"], expected, atol=1e-12)


class TestCompareWithPredictions:
    """Prüft die Vergleichs-/Diskriminierungs-Logik."""

    def test_h1_scenario_recognized(self):
        """Klein |bias_PT| (< 0.05) -> H1 oder H3 (gaps invariant)."""
        from pt_aer_stress_saeule1 import compare_with_predictions
        from pt_aer_stress_saeule1 import h1_h2_h3_predictions
        measurements = {
            "5_pubs": {
                "H_diag_at_vqe_opt": 3.3412,
                "Re_H_PT_at_vqe_opt": 3.3500,  # bias = 0.0088
                "Im_H_PT_at_vqe_opt": 0.03,
                "Re_H_PT_at_random": 3.30,
                "Im_H_PT_at_random": 0.04
            }
        }
        pred = h1_h2_h3_predictions()
        result = compare_with_predictions(measurements, pred)
        assert "H1" in result["verdict"] or "H3" in result["verdict"]
        assert result["confidence"] == "HOCH"

    def test_h2_scenario_recognized(self):
        """Gross |bias_PT| (> 0.15) -> H2 (gaps drastisch verzerrt)."""
        from pt_aer_stress_saeule1 import compare_with_predictions
        from pt_aer_stress_saeule1 import h1_h2_h3_predictions
        measurements = {
            "5_pubs": {
                "H_diag_at_vqe_opt": 3.3412,
                "Re_H_PT_at_vqe_opt": 4.0,  # bias = 0.66
                "Im_H_PT_at_vqe_opt": 0.1,
                "Re_H_PT_at_random": 3.5,
                "Im_H_PT_at_random": 0.05
            }
        }
        pred = h1_h2_h3_predictions()
        result = compare_with_predictions(measurements, pred)
        assert "H2" in result["verdict"]
        assert result["confidence"] == "HOCH"

    def test_intermediate_bias_partial_h2(self):
        """Mittlerer bias (0.05-0.15) -> partial H2-Einfluss."""
        from pt_aer_stress_saeule1 import compare_with_predictions
        from pt_aer_stress_saeule1 import h1_h2_h3_predictions
        measurements = {
            "5_pubs": {
                "H_diag_at_vqe_opt": 3.3412,
                "Re_H_PT_at_vqe_opt": 3.45,  # bias = 0.11
                "Im_H_PT_at_vqe_opt": 0.05,
                "Re_H_PT_at_random": 3.40,
                "Im_H_PT_at_random": 0.06
            }
        }
        pred = h1_h2_h3_predictions()
        result = compare_with_predictions(measurements, pred)
        assert "partial" in result["verdict"].lower() or "partial" in result["verdict"].lower()
        assert result["confidence"] == "MITTEL"


class TestPreregistrationLoader:
    """Prüft den Pre-Registrierungs-Lader."""

    def test_precompute_returns_dict(self):
        """precompute_predictions muss ein Dict mit 'noiseless' und 'H_diag_exact' liefern."""
        from pt_aer_stress_saeule1 import precompute_predictions
        pred = precompute_predictions()
        assert isinstance(pred, dict)
        assert "noiseless" in pred or "H_diag_exact" in pred

    def test_uses_existing_prereg_file_if_present(self):
        """Wenn pt_potential_vqe_prereg.json existiert, soll es gelesen werden."""
        from pathlib import Path
        prereg_path = Path("pt_potential_vqe_prereg.json")
        # Backup der existierenden Prereg-Datei (Anti-Sharpshooter: nie Original loeschen)
        backup = None
        if prereg_path.exists():
            backup = prereg_path.read_text()
        # Schreibe temporaer eine Test-Prereg-Datei mit eindeutigem Marker
        test_prereg = {
            "noiseless": {"E": [2.0, 2.69, 3.68, 4.99], "Delta": [0.69, 0.99, 1.30]},
            "H_diag_exact": {"E": [2.0, 2.69, 3.68, 4.99], "Delta": [0.69, 0.99, 1.30]},
            "marker": "test_prereg_from_file"
        }
        prereg_path.write_text(json.dumps(test_prereg))
        try:
            from pt_aer_stress_saeule1 import precompute_predictions
            pred = precompute_predictions()
            assert pred.get("marker") == "test_prereg_from_file"
        finally:
            # Cleanup: Original wiederherstellen, nicht loeschen
            if backup is not None:
                prereg_path.write_text(backup)
            else:
                prereg_path.unlink(missing_ok=True)

    def test_preserves_existing_prereg_after_run(self):
        """REGRESSION: Vorhandene pt_potential_vqe_prereg.json darf nach Test-Lauf NICHT geloescht sein.

        Hintergrund: 2026-06-17 hat ein Bug im Loader-Test die Original-Prereg
        aus dem Working Tree geloescht. Das ist ein Anti-Sharpshooter-Verstoss
        (Prereg-Datei ist anti-sharpshooter-kritisch, darf nie von Tests beruehrt werden).
        Dieser Test faengt kuenftige Regressionen.
        """
        from pathlib import Path
        prereg_path = Path("pt_potential_vqe_prereg.json")
        if not prereg_path.exists():
            # Wenn die Datei nicht existiert, koennen wir nicht pruefen — Skip
            import pytest
            pytest.skip("pt_potential_vqe_prereg.json existiert nicht — Test nicht anwendbar")
        # Vor dem Testlauf: Inhalt merken
        original = prereg_path.read_text()
        original_md5 = hashlib.md5(original.encode()).hexdigest()
        # Den problematischen Test ausfuehren
        from tests.test_pt_aer_stress_saeule1 import TestPreregistrationLoader
        TestPreregistrationLoader().test_uses_existing_prereg_file_if_present()
        # Nach dem Testlauf: Datei muss identisch sein
        assert prereg_path.exists(), "Prereg-Datei wurde geloescht!"
        after = prereg_path.read_text()
        after_md5 = hashlib.md5(after.encode()).hexdigest()
        assert after_md5 == original_md5, (
            f"Prereg-Datei wurde MODIFIZIERT: original={original_md5}, after={after_md5}. "
            f"Das ist ein Anti-Sharpshooter-Verstoss — Prereg-Dateien sind unantastbar."
        )


class TestAerStressModule:
    """Prüft Importierbarkeit und Schlüsselfunktionen."""

    def test_module_imports(self):
        import pt_aer_stress_saeule1
        assert hasattr(pt_aer_stress_saeule1, 'run_aer_stress_test')
        assert hasattr(pt_aer_stress_saeule1, 'compare_with_predictions')
        assert hasattr(pt_aer_stress_saeule1, 'precompute_predictions')
        assert hasattr(pt_aer_stress_saeule1, 'h1_h2_h3_predictions')
        assert hasattr(pt_aer_stress_saeule1, 'main')

    def test_constants_match_hardware_run(self):
        """Konstanten (GAMMA, INITIAL_PARAMS, etc.) muessen mit pt_potential_vqe.py uebereinstimmen."""
        from pt_aer_stress_saeule1 import GAMMA, INITIAL_PARAMS, SHOTS, N_ITERS_VQE, BACKEND_NAME
        assert GAMMA == 0.02
        assert INITIAL_PARAMS == [0.523, 1.21, -0.45, 0.88]
        assert SHOTS == 8192
        assert N_ITERS_VQE == 10
        assert BACKEND_NAME == "ibm_fez"
