"""
Tests for pt_qpu_job_inventory_retroactive.py — retroactive QPU job fetch.

These tests verify:
  - Job-ID scanning from JSON/log files
  - False-positive filtering (MD5 hash fragments, path contexts)
  - Already-downloaded cross-referencing
  - Idempotency: a second run finds nothing new after the first
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestScanJobIds:
    """Verify scanning of pt_*.json + *.log files."""

    def test_scan_returns_dict(self):
        from pt_qpu_job_inventory_retroactive import scan_job_ids_in_files
        records = scan_job_ids_in_files()
        assert isinstance(records, dict)
        # Known IDs from SYNTHESIS must appear
        assert "d8j9chtv8cos73f6i060" in records  # ibm_fez
        assert "d8j9ch1e8nrc73bj8r80" in records  # ibm_marrakesh
        assert "d8j9ch9e8nrc73bj8r9g" in records  # ibm_kingston

    def test_scan_finds_all_three_kingston_jobs(self):
        from pt_qpu_job_inventory_retroactive import scan_job_ids_in_files
        records = scan_job_ids_in_files()
        for jid in ["d8j9ch9e8nrc73bj8r9g", "d8j9li5v8cos73f6ics0",
                    "d8j5j7u6983c73dste00"]:
            assert jid in records

    def test_job_ids_are_20_chars(self):
        from pt_qpu_job_inventory_retroactive import scan_job_ids_in_files
        records = scan_job_ids_in_files()
        for jid in records:
            assert len(jid) == 20
            assert jid.startswith("d")


class TestFilterFalsePositives:
    """Verify MD5 hash fragments are filtered out."""

    def test_filter_removes_md5_fragments(self):
        from pt_qpu_job_inventory_retroactive import filter_false_positives
        # Simulate a MD5 hash fragment context
        records = {
            "d33c2d89ca07720f11be": [
                ("some_doc.md", "md5=`5a45d33c2d89ca07720f11bee00...`"),
            ],
            "d8j9chtv8cos73f6i060": [
                ("some_results.json", '"job_id": "d8j9chtv8cos73f6i060"'),
            ],
        }
        real, fake = filter_false_positives(records)
        assert "d8j9chtv8cos73f6i060" in real
        assert "d33c2d89ca07720f11be" in fake

    def test_filter_keeps_path_false_positives(self):
        from pt_qpu_job_inventory_retroactive import filter_false_positives
        records = {
            "d58c346ab90fdee98f30": [
                ("log.txt", "/home/julian/.local/lib/python3.14/site-packages"),
            ],
            "d8j9chtv8cos73f6i060": [
                ("some_results.json", '"job_id": "d8j9chtv8cos73f6i060"'),
            ],
        }
        real, fake = filter_false_positives(records)
        assert "d8j9chtv8cos73f6i060" in real
        assert "d58c346ab90fdee98f30" in fake

    def test_filter_removes_hex_continuation_fragment(self):
        # REGRESSION (EXPERIMENT 042, Fez-Raw): der 32-stellige counts_md5
        # ("d19f4a563d88e0cf3ffd4b187a10ca73") liefert beim Scan ein
        # 20-Zeichen-Fragment ohne "md5="-Kontext ("raw fetched: d19f...").
        # Ein echter Job-ID ist GENAU 20 Zeichen — folgt dem Match eine
        # Hex-Fortsetzung (>= 6 Zeichen), ist es ein Hash-Fragment.
        from pt_qpu_job_inventory_retroactive import filter_false_positives
        records = {
            "d19f4a563d88e0cf3ffd": [
                ("pt_ram_q_fez_run.log",
                 "[qpu] raw fetched: d19f4a563d88e0cf3ffd4b187a10ca73 "
                 "(58 circuits)"),
                ("pt_ram_q_hardware_raw.json",
                 '"counts_md5": "d19f4a563d88e0cf3ffd4b187a10ca73"'),
            ],
            "darq1stvr3kc73ej96ig": [
                ("pt_ram_q_fez_run.log",
                 "[qpu] submitted darq1stvr3kc73ej96ig (58 circuits)"),
                ("pt_downloaded_job_results.json",
                 '"job_id": "darq1stvr3kc73ej96ig"'),
            ],
        }
        real, fake = filter_false_positives(records)
        assert "darq1stvr3kc73ej96ig" in real
        assert "d19f4a563d88e0cf3ffd" in fake

    def test_filter_keeps_real_job_with_mixed_contexts(self):
        # Eine echte Job-ID mit EINEM md5-Kontext und EINEM job_id-Kontext
        # bleibt real (All-Quantil: nur wenn ALLE Kontexte md5/pfadig sind).
        from pt_qpu_job_inventory_retroactive import filter_false_positives
        records = {
            "darq1stvr3kc73ej96ig": [
                ("log.txt", "counts_md5: darq1stvr3kc73ej96ig"),
                ("res.json", '"job_id": "darq1stvr3kc73ej96ig"'),
            ],
        }
        real, _ = filter_false_positives(records)
        assert "darq1stvr3kc73ej96ig" in real


class TestFindDownloaded:
    """Verify cross-referencing with already-downloaded results."""

    def test_downloaded_includes_known_ids(self):
        from pt_qpu_job_inventory_retroactive import find_downloaded_ids
        downloaded = find_downloaded_ids()
        # These 18 were downloaded on 2026-07-21
        for jid in ["d8j9chtv8cos73f6i060", "d8j9ch1e8nrc73bj8r80",
                    "d8j5j7u6983c73dste00", "d9fh0bqneu4c739pivh0"]:
            assert jid in downloaded, f"{jid} should be downloaded"

    def test_downloaded_is_set(self):
        from pt_qpu_job_inventory_retroactive import find_downloaded_ids
        downloaded = find_downloaded_ids()
        assert isinstance(downloaded, set)


class TestIdempotency:
    """Verify a second dry-run finds nothing new after the first."""

    def test_dry_run_finds_zero_missing_after_initial_download(self):
        from pt_qpu_job_inventory_retroactive import (
            scan_job_ids_in_files, filter_false_positives,
            find_downloaded_ids,
        )
        records = scan_job_ids_in_files()
        real, _ = filter_false_positives(records)
        downloaded = find_downloaded_ids()
        missing = {jid: srcs for jid, srcs in real.items() if jid not in downloaded}
        # On 2026-07-21, after the initial download, this must be empty
        assert len(missing) == 0, f"Missing job IDs: {sorted(missing)[:5]}"


class TestTokenLoading:
    """Verify token loading from .env (no token in output)."""

    def test_load_tokens_returns_dict(self):
        from pt_qpu_job_inventory_retroactive import load_tokens
        tokens = load_tokens()
        assert "IBMQ_TOKEN" in tokens
        assert "IBMQ_TOKEN2" in tokens
        # Tokens must never be empty
        assert len(tokens["IBMQ_TOKEN"]) > 10
        assert len(tokens["IBMQ_TOKEN2"]) > 10

    def test_tokens_are_not_logged(self):
        """Constitutional principle: tokens NEVER enter output files."""
        # Verify the downloaded results file does NOT contain any token string
        from pt_qpu_job_inventory_retroactive import load_tokens
        tokens = load_tokens()
        path = Path("pt_downloaded_job_results.json")
        if not path.exists():
            pytest.skip("No downloaded results file yet")
        text = path.read_text()
        for name, tok in tokens.items():
            assert tok not in text, f"Token {name} leaked into pt_downloaded_job_results.json"


class TestModuleImports:
    """Verify module is importable."""

    def test_module_imports(self):
        import pt_qpu_job_inventory_retroactive
        for name in ["scan_job_ids_in_files", "filter_false_positives",
                     "find_downloaded_ids", "load_tokens",
                     "probe_and_fetch"]:
            assert hasattr(pt_qpu_job_inventory_retroactive, name)