"""
Tests für Säule 2: pt_transmission_sweep.py — G-Apparat.

Verspricht im Mermaid-Diagramm:
  - Sweep E_range = linspace(0.5, 6.0, 100)
  - H_probe(E) = H_diag - E*I + i*gamma*A
  - T(E) = |durchgelassene Amplitude|²
  - Resonanzpeaks bei E = 2.00, 2.69, 3.40, 4.14
  - find_peaks in T(E) mit prominence >= 0.05
  - Vergleich Peaks_meas mit Peaks_pred

Diese Tests prüfen die Sweep-Logik und Peak-Detektion offline.
"""
import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pt_structural import E_DIAG, jacobi_A


class TestGApparatusMath:
    """Prüft die mathematische Struktur des G-Apparats."""

    def test_E_range_spans_all_levels(self):
        """E_range = linspace(0.5, 6.0, 100) muss alle 4 Zeraoulia-Niveaus enthalten."""
        E_range = np.linspace(0.5, 6.0, 100)
        for E in E_DIAG:
            assert E in E_range or (E_range.min() <= E <= E_range.max()), \
                f"E={E} ausserhalb Sweep-Bereich"

    def test_E_range_resolution_sufficient(self):
        """Auflösung muss < 0.1 sein, um 4 Peaks zu trennen."""
        E_range = np.linspace(0.5, 6.0, 100)
        dE = E_range[1] - E_range[0]
        # kleinster Gap zwischen Zeraoulia-Niveaus:
        min_gap = min(E_DIAG[i+1] - E_DIAG[i] for i in range(3))
        assert dE < min_gap / 2, f"Auflösung {dE} zu grob für Gap {min_gap}"

    def test_H_probe_invertible_off_resonance(self):
        """H_probe(E) ausserhalb Resonanz muss invertierbar sein."""
        A = jacobi_A(E_DIAG, y=1.0)
        H_diag = np.diag(E_DIAG).astype(complex)
        gamma = 0.02
        E_off = 1.0  # weit weg von E_0 = 2.0
        H_probe = H_diag - E_off * np.eye(4) + 1j * gamma * A
        det = np.linalg.det(H_probe)
        assert abs(det) > 1e-6, f"H_probe bei E_off={E_off} singulär: det={det}"

    def test_H_probe_peaked_at_resonance(self):
        """T(E) = 1/|det(H_probe(E))| hat Peak nahe E = E_n."""
        A = jacobi_A(E_DIAG, y=1.0)
        H_diag = np.diag(E_DIAG).astype(complex)
        gamma = 0.02

        # Sweep E um E_0 = 2.0
        E_near = np.linspace(1.5, 2.5, 50)
        T_values = []
        for E in E_near:
            H_probe = H_diag - E * np.eye(4) + 1j * gamma * A
            # T(E) ~ 1/|det| — an Resonanz wird Matrix singulär
            det = np.linalg.det(H_probe)
            T_values.append(1.0 / max(abs(det), 1e-12))

        # Peak sollte nahe E_0 = 2.0 sein
        peak_idx = np.argmax(T_values)
        E_peak = E_near[peak_idx]
        assert abs(E_peak - 2.0) < 0.2, f"Peak bei E={E_peak}, erwartet ~2.0"


class TestGApparatusPeakDetection:
    """Prüft die Peak-Detektion in T(E)."""

    def test_synthetic_T_E_has_4_peaks(self):
        """Synthetisches T(E) mit 4 Lorentz-Peaks muss 4 detektierte Peaks liefern."""
        from scipy.signal import find_peaks

        # Synthetisches T(E) mit Peaks bei E_DIAG
        E = np.linspace(0.5, 6.0, 1000)
        T = np.ones_like(E) * 0.01
        for E_peak, width in zip(E_DIAG, [0.05, 0.08, 0.10, 0.12]):
            T += 1.0 / (1 + ((E - E_peak) / width) ** 2)

        # Peak-Detektion
        peaks, properties = find_peaks(T, prominence=0.05, distance=20)
        assert len(peaks) >= 4, f"Erwartet 4 Peaks, gefunden {len(peaks)}"

        # Peaks müssen nahe E_DIAG sein
        detected_E = sorted(E[peaks])
        for i, E_actual in enumerate(detected_E[:4]):
            assert abs(E_actual - E_DIAG[i]) < 0.1, \
                f"Peak {i} bei E={E_actual}, erwartet ~{E_DIAG[i]}"

    def test_gaps_extracted_from_peaks(self):
        """ΔE_n aus Peak-Abständen muss mit E_DIAG-Gaps übereinstimmen."""
        from scipy.signal import find_peaks

        E = np.linspace(0.5, 6.0, 1000)
        T = np.ones_like(E) * 0.01
        for E_peak in E_DIAG:
            T += 1.0 / (1 + ((E - E_peak) / 0.05) ** 2)

        peaks, _ = find_peaks(T, prominence=0.5, distance=20)
        detected_E = sorted(E[peaks])
        gaps = [detected_E[i+1] - detected_E[i] for i in range(3)]
        expected_gaps = [E_DIAG[i+1] - E_DIAG[i] for i in range(3)]

        for i in range(3):
            assert abs(gaps[i] - expected_gaps[i]) < 0.05, \
                f"Gap {i}: gemessen {gaps[i]}, erwartet {expected_gaps[i]}"


class TestGApparatusModule:
    """Prüft, dass pt_transmission_sweep.py importierbar ist."""

    def test_module_imports(self):
        try:
            import pt_transmission_sweep
            assert hasattr(pt_transmission_sweep, 'sweep_transmission')
            assert hasattr(pt_transmission_sweep, 'find_resonances')
            assert hasattr(pt_transmission_sweep, 'main')
        except ImportError:
            pytest.skip("pt_transmission_sweep noch nicht implementiert (erwartet bei TDD)")

    def test_sweep_returns_correct_length(self):
        try:
            import pt_transmission_sweep
            E_range, T_values = pt_transmission_sweep.sweep_transmission(
                E_min=0.5, E_max=6.0, n_steps=100, gamma=0.02
            )
            assert len(E_range) == 100
            assert len(T_values) == 100
        except ImportError:
            pytest.skip("pt_transmission_sweep noch nicht implementiert (erwartet bei TDD)")

    def test_find_resonances_returns_4_peaks(self):
        try:
            import pt_transmission_sweep
            E_range = np.linspace(0.5, 6.0, 1000)
            T_values = np.ones_like(E_range) * 0.01
            for E_peak in E_DIAG:
                T_values += 1.0 / (1 + ((E_range - E_peak) / 0.05) ** 2)

            peaks = pt_transmission_sweep.find_resonances(E_range, T_values)
            assert len(peaks) == 4
        except ImportError:
            pytest.skip("pt_transmission_sweep noch nicht implementiert (erwartet bei TDD)")
