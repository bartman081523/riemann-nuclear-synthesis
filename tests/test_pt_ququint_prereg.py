"""
Tests for pt_ququint_prereg.py — EXPERIMENT 032, Phase 3a (Prereg-Freeze).

Anti-Sharpshooter: die Vorhersagen für den Fez-Lauf werden VOR jedem
Hardware-Zugriff als Konstanten registriert — berechnet ausschliesslich aus
der deterministischen Phase-2-STRESS-Kurve (pt_ququint_ibmq_aer, seed 42),
niemals aus Hardware-Daten. Abgedeckt:

  - Predictions-Bänder über das Fez-nahe p1-Fenster [1e-4, 3e-3] mit den
    Phase-2-Zahlen als Pins (phi-Margin strikt positiv im ganzen Fenster,
    sep-Margin strikt negativ, Konfund <= 0.05)
  - Prereg-Payload mit den pt_prereg_audit-Pflichtfeldern (md5,
    decision_rule, predictions); Decision Rule in der sandboxed Grammatik
  - md5-Determinismus (KEIN Timestamp im gehashten Payload) + Tamper-Detektion
  - Freeze-Roundtrip ({"payload", "md5"}) + audit_prereg_structure
  - Pipeline-Validierung in Emulation: audit_run(frozen prereg, emuliertes
    Result aus Phase 2) -> CONFIRMED; phi-Fail -> REFUTED
  - Guard: simulator-only (kein IBM-Provider-Import im Prereg-Modul)
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Phase-2-STRESS-Zahlen (§Z.13.5 demo, seed=42, n=8192, ro=1e-2, ratio=10) —
# hier als externe Pins notiert, gegen die build_predictions() verifiziert wird.
# PROVENANZ (worktree-verifiziert am 3a-Freeze-Commit b77974f): phi_margin +
# confound_max_diff Bänder stammen bit-exakt aus der Phase-2-Stress-Kurve
# (pt_crossover_v4_results.json, encoded.curve, Slice p1∈[1e-4,3e-3] —
# testet test_bands_provenance_from_crossover_v4_curve). Das sep-Band stammt
# aus der Freeze-Zeit-Rekompuation (ibmq_aer-Kette; ihre Kurve wurde nicht
# persistiert, Abstand der Endpunkte 2.8e-4/4.9e-4). Die Rekompuation läuft
# über die ZWEITE Pipeline (ibmq_aer.run_witness, seed 42) — ein
# unabhängiger Sampling-Draw mit deterministischem Drift ≤ 1.2e-3 in phi
# (gemessen: 1.12e-3 am 3e-3-Ende); deshalb Toleranz 2e-3.
PHI_MARGIN_BAND = [0.0313, 0.6774]
SEP_MARGIN_BAND = [-0.0722, -0.0164]
CONFOUND_BAND = [0.0090, 0.0195]
FEZ_POINT_PHI_MARGIN = 0.5840
FEZ_POINT_SEP_MARGIN = -0.0229


# === PREDICTIONS (aus Phase 2, nicht aus Hardware) ===


class TestStressPredictions:
    def test_bands_match_phase2_numbers(self):
        import pt_ququint_prereg as pr
        sp = pr.stress_predictions()
        assert sp["bands"]["phi_margin"] == pytest.approx(PHI_MARGIN_BAND, abs=2e-3)
        assert sp["bands"]["sep_margin"] == pytest.approx(SEP_MARGIN_BAND, abs=2e-3)
        assert sp["bands"]["confound_max_diff"] == pytest.approx(CONFOUND_BAND, abs=2e-3)

    def test_bands_provenance_from_crossover_v4_curve(self):
        # PROVENANZ (worktree-verifiziert am 3a-Freeze-Commit b77974f):
        # Die FROZENEN JSON-Bänder (phi_margin + confound_max_diff) sind die
        # min/max der Phase-2-Stress-Kurve — bit-exakt aus der kommittierten
        # crossover-v4-Datei (encoded.curve, Slice p1∈[1e-4,3e-3]).
        # Die v4-Kurve trägt KEIN sep (nur sep_primary am Fez-Punkt,
        # margin -0.022891546221750825 — bit-exakt der Prereg-fez-point).
        # Das sep-Band stammt aus der Freeze-Zeit-Rekompuation (ibmq_aer-
        # Kette, unverändert seit 45ef401); ihre vollständige Kurve wurde
        # bei Phase 2 NICHT persistiert. Die gefrorene Kette reproduziert
        # die Endpunkte deterministisch innerhalb 4.9e-4 (gemessen).
        # Die Rekompuation über DIESE Kette (stress_predictions()) driftet
        # deterministisch gegen die JSON-Bänder: phi ≤ 1.12e-3 (gemessen
        # am 3e-3-Ende), sep ≤ 4.9e-4, confound bit-exakt — getestet in
        # test_bands_match_phase2_numbers (Toleranz 2e-3).
        with open("pt_ququint_fez_prereg.json", encoding="utf-8") as fh:
            doc = json.load(fh)
        with open("pt_crossover_v4_results.json", encoding="utf-8") as fh:
            curve = json.load(fh)["encoded"]["curve"]
        slice_pts = [c for c in curve
                     if c["p1"] in (1e-4, 3e-4, 1e-3, 3e-3)]
        bands = doc["prediction_bands"]
        # phi + confound: frozen JSON bit-exakt == v4-Kurven-min/max (1e-12)
        assert bands["phi_margin"]["band"] == pytest.approx(
            [min(c["phi"]["margin"] for c in slice_pts),
             max(c["phi"]["margin"] for c in slice_pts)], abs=1e-12)
        assert bands["confound_max_diff"]["band"] == pytest.approx(
            [min(c["confound_max_diff"] for c in slice_pts),
             max(c["confound_max_diff"] for c in slice_pts)], abs=1e-12)
        # sep: Freeze-Zeit-Kette (nicht persistiert) — Rekompuation nahe
        import pt_ququint_prereg as pr
        sp = pr.stress_predictions()
        assert bands["sep_margin"]["band"] == pytest.approx(
            sp["bands"]["sep_margin"], abs=2e-3)
        assert bands["sep_margin"]["band"] == pytest.approx(
            [-0.07217471655344979, -0.016394646652426598], abs=1e-12)

    def test_band_signs_robust_across_window(self):
        # der Kern der Preregistration: über dem GANZEN Fez-nahen Fenster
        # bleibt phi POSITIV und sep NEGATIV — die Sign-Vorhersage ist nicht
        # von einem einzelnen Grid-Punkt abhängig
        import pt_ququint_prereg as pr
        sp = pr.stress_predictions()
        assert sp["bands"]["phi_margin"][0] > 0.0
        assert sp["bands"]["sep_margin"][1] < 0.0
        assert sp["bands"]["confound_max_diff"][1] <= 0.05

    def test_grid_is_fez_near_window_of_phase2(self):
        import pt_ququint_ibmq_aer as qa
        import pt_ququint_prereg as pr
        assert pr.STRESS_GRID_SLICE == (1e-4, 3e-4, 1e-3, 3e-3)
        assert set(pr.STRESS_GRID_SLICE) <= set(qa.NOISE_GRID_DEFAULT)

    def test_fez_point_is_p1_3e4_with_pinned_values(self):
        import pt_ququint_prereg as pr
        sp = pr.stress_predictions()
        assert sp["fez_point"]["p1"] == pytest.approx(3e-4)
        assert sp["fez_point"]["phi"]["margin"] == pytest.approx(
            FEZ_POINT_PHI_MARGIN, abs=1e-3
        )
        assert sp["fez_point"]["sep"]["margin"] == pytest.approx(
            FEZ_POINT_SEP_MARGIN, abs=1e-3
        )

    def test_predictions_are_deterministic(self):
        import pt_ququint_prereg as pr
        sp1 = pr.stress_predictions()
        sp2 = pr.stress_predictions()
        assert sp1["bands"] == sp2["bands"]
        assert sp1["fez_point"]["phi"]["margin"] == sp2["fez_point"]["phi"]["margin"]


# === PREREG-PAYLOAD (pt_prereg_audit-Pflichtfelder) ===


class TestPreregPayload:
    def test_payload_passes_audit_structure(self):
        # das FROZENE Dokument (flat, md5 auf Top-Level) muss die
        # audit_prereg_structure-Pflichtfelder erfuellen
        import pt_prereg_audit as pa
        import pt_ququint_prereg as pr
        payload = pr.build_prereg_payload()
        doc = dict(payload)
        doc["md5"] = pr.payload_md5(payload)
        audit = pa.audit_prereg_structure(doc)
        assert audit["ok"] is True
        assert audit["missing_fields"] == []

    def test_decision_rule_in_sandbox_grammar(self):
        import pt_prereg_audit as pa
        import pt_ququint_prereg as pr
        payload = pr.build_prereg_payload()
        rule = payload["decision_rule"]
        # alle drei Aussagen erfüllt -> CONFIRMED-Pfad
        passing = {
            "phi_margin_pass": True,
            "sep_margin_pass": True,
            "confound_pass": True,
        }
        assert pa.evaluate_decision_rule(rule, passing) is True
        # phi fällt unter die Schranke -> Regel scheitert
        assert pa.evaluate_decision_rule(
            rule, {**passing, "phi_margin_pass": False}
        ) is False
        # Konfund-Verletzung -> Regel scheitert
        assert pa.evaluate_decision_rule(
            rule, {**passing, "confound_pass": False}
        ) is False
        # Kontroll-Zustand fälschlich geflaggt -> Regel scheitert
        assert pa.evaluate_decision_rule(
            rule, {**passing, "sep_margin_pass": False}
        ) is False

    def test_no_timestamp_in_hashed_payload(self):
        import pt_ququint_prereg as pr
        payload = pr.build_prereg_payload()
        text = json.dumps(payload).lower()
        assert "timestamp" not in text
        assert "frozen_at" not in text
        # zwei Builds (reale Zeit zwischen ihnen) -> identisches md5
        assert pr.payload_md5(payload) == pr.payload_md5(pr.build_prereg_payload())

    def test_run_config_pinned_before_submission(self):
        import pt_ququint_prereg as pr
        payload = pr.build_prereg_payload()
        assert payload["backend"] == "ibm_fez"
        assert payload["n_shots"] == 8192
        assert payload["n_circuits"] == 12
        assert payload["circuit_order"][0] == "phi_C"
        assert payload["circuit_order"][1] == "phi_D"
        assert len(payload["circuit_order"]) == 12
        assert payload["run_config"]["optimization_level"] == 3

    def test_predictions_registered_as_constants(self):
        # die Sign-Vorhersagen sind True-Konstanten im Payload — registriert
        # VOR jedem Hardware-Zugriff, nicht aus Daten abgeleitet
        import pt_ququint_prereg as pr
        payload = pr.build_prereg_payload()
        preds = payload["predictions"]
        assert preds["phi_margin_pass"] is True
        assert preds["sep_margin_pass"] is True
        assert preds["confound_pass"] is True


# === MD5 + FREEZE-ROUNTRIP ===


class TestFreeze:
    def test_freeze_roundtrip_verifies(self, tmp_path):
        import pt_ququint_prereg as pr
        doc = pr.freeze_prereg(path=str(tmp_path / "prereg.json"))
        assert pr.verify_prereg_md5(doc) is True
        reloaded = json.loads((tmp_path / "prereg.json").read_text())
        assert pr.verify_prereg_md5(reloaded) is True
        assert reloaded["md5"] == doc["md5"]
        # flat-Format: Pflichtfelder auf Top-Level (pt_prereg_audit-Kontrakt)
        assert "decision_rule" in reloaded and "predictions" in reloaded

    def test_tampered_payload_fails_md5(self, tmp_path):
        import pt_ququint_prereg as pr
        doc = pr.freeze_prereg(path=str(tmp_path / "prereg.json"))
        doc["predictions"]["phi_margin_pass"] = False
        assert pr.verify_prereg_md5(doc) is False

    def test_tampered_md5_fails_verification(self, tmp_path):
        import pt_ququint_prereg as pr
        doc = pr.freeze_prereg(path=str(tmp_path / "prereg.json"))
        doc["md5"] = "0" * 32
        assert pr.verify_prereg_md5(doc) is False

    def test_payload_md5_is_canonical_json(self):
        import hashlib
        import pt_ququint_prereg as pr
        payload = pr.build_prereg_payload()
        expected = hashlib.md5(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        assert pr.payload_md5(payload) == expected


# === PIPELINE-VALIDIERUNG IN EMULATION (audit_run) ===


class TestPipelineInEmulation:
    def test_audit_run_confirmed_on_emulated_result(self, tmp_path):
        import pt_prereg_audit as pa
        import pt_ququint_prereg as pr
        doc = pr.freeze_prereg(path=str(tmp_path / "prereg.json"))
        result = pr.build_emulated_result()
        result_path = tmp_path / "result.json"
        result_path.write_text(json.dumps(result), encoding="utf-8")
        audit = pa.audit_run(str(tmp_path / "prereg.json"), str(result_path))
        assert audit["status"] == "CONFIRMED"

    def test_audit_run_refuted_when_phi_fails(self, tmp_path):
        import pt_prereg_audit as pa
        import pt_ququint_prereg as pr
        doc = pr.freeze_prereg(path=str(tmp_path / "prereg.json"))
        result = pr.build_emulated_result()
        result["phi_margin_pass"] = False
        result_path = tmp_path / "result.json"
        result_path.write_text(json.dumps(result), encoding="utf-8")
        audit = pa.audit_run(str(tmp_path / "prereg.json"), str(result_path))
        assert audit["status"] == "REFUTED"

    def test_emulated_result_carries_all_prediction_keys(self):
        import pt_ququint_prereg as pr
        payload = pr.build_prereg_payload()
        result = pr.build_emulated_result()
        missing = [k for k in payload["predictions"] if k not in result]
        assert missing == []
        assert result["emulated"] is True  # niemals als Hardware-Datenausgabe tarnt


# === GUARDS ===


class TestPreregGuards:
    def test_prereg_module_is_simulator_only(self):
        # das Prereg-Modul darf KEINEN IBM-Provider-Import haben — die
        # Vorhersagen kommen ausschliesslich aus der Phase-2-Simulation
        import pt_ququint_prereg as pr
        src = open(pr.__file__, encoding="utf-8").read()
        assert "qiskit_ibm" not in src

    def test_stress_caveat_documented(self):
        import pt_ququint_prereg as pr
        src = open(pr.__file__, encoding="utf-8").read().lower()
        assert "stress" in src
        assert "not a calibrated" in src

    def test_anti_sharpshooter_documented(self):
        import pt_ququint_prereg as pr
        src = open(pr.__file__, encoding="utf-8").read().lower()
        assert "anti-sharpshooter" in src