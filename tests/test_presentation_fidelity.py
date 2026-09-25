"""Fidelity tests for the presentation pipeline.

These tests validate the claim table, the data gate, and (skip-if-absent)
the produced media. They NEVER import manim or pyslides and never render.

SciComPresentationMind: fidelity_audit as tests — a number that cannot be
re-derived from committed sources must not reach the screen.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PRESENTATION_DIR = REPO_ROOT / "presentation"
if str(PRESENTATION_DIR) not in sys.path:
    sys.path.insert(0, str(PRESENTATION_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import claims  # noqa: E402

A_FAMILY = ("A+", "A", "A−")
C_FAMILY = ("C", "C−", "D")


# --------------------------------------------------------------------------
# Claim-table structure.
# --------------------------------------------------------------------------

def test_claims_table_structure():
    assert set(claims.SCENES) == set(claims.HEADLINES)
    for cid, c in claims.CLAIMS.items():
        assert c.id == cid
        assert isinstance(c.display, str) and c.display
        assert isinstance(c.label, claims.Label)
        assert set(c.scenes) <= set(claims.SCENES), cid
        if c.source.kind is claims.Kind.DOC_FROZEN:
            assert c.source.anchor and c.source.line, cid
        if c.criterion is not None:
            assert len(c.criterion.split()) <= 30, cid


def test_glosses_within_word_budget():
    for cid, c in claims.CLAIMS.items():
        if c.gloss is not None:
            assert len(c.gloss.split()) <= 12, f"{cid}: {c.gloss!r}"


def test_headline_claims_carry_criterion_and_gloss():
    # explanation_scaffold: the frozen criterion is shown BEFORE the result,
    # first technical term is glossed (≤ 12 words, tested above).
    for slug in ("act2_pillar1", "act3_anomaly", "act4_qpu_timeline",
                 "act5_kappa", "act6_ramanujan", "act7_qpe_peaks",
                 "act8_fermat_grid"):
        cid = claims.HEADLINES[slug]
        assert cid is not None, slug
        c = claims.CLAIMS[cid]
        assert c.criterion, f"{slug}: headline {cid} lacks frozen criterion"
        assert c.gloss, f"{slug}: headline {cid} lacks gloss"
        assert c.scenes and slug in c.scenes


# --------------------------------------------------------------------------
# Wording ladder (audience_calibration).
# --------------------------------------------------------------------------

def test_grade_wording_matches_grade():
    for cid, c in claims.CLAIMS.items():
        if c.grade in A_FAMILY:
            assert c.label is claims.Label.MEASURED, \
                f"{cid}: grade {c.grade} must be MEASURED wording"
        if c.grade in C_FAMILY:
            assert c.label in (claims.Label.POINTS_TO,
                               claims.Label.DOC_FROZEN), \
                f"{cid}: grade {c.grade} must not be claimed as measured"
        if c.label is claims.Label.HYPOTHESIS:
            assert c.grade is None or c.grade in C_FAMILY, cid


# --------------------------------------------------------------------------
# Data gate (always-on).
# --------------------------------------------------------------------------

def test_data_gate_recompute_light():
    # full=False skips the pytest-collection cmd claim; JSON + module
    # claims (H-SHOR-1 ~6.6 s, lru_cached) recompute against frozen values.
    mismatches = claims.check_gate(full=False)
    assert mismatches == []


def test_hshor1_recompute_details():
    r = claims.raw("hshor_verdict")  # verdict claim — module recompute
    assert r == "CONFIRMED"
    assert claims.raw("hshor_bridge_min") == 1.0
    assert claims.raw("hshor_crt_dev") == 0.0
    assert claims.raw("hshor_trace_dev") == 0.0
    assert claims.raw("hshor_shuffle_p") == 0.0
    assert claims.raw("hshor_md5") == "73bc664ae3475a79a692cd7735b2b387"
    o1 = claims.raw("hshor_o1")
    primes = {k: v for k, v in o1.items() if k not in
              {"9", "15", "21", "25", "33", "35", "39", "561"}}
    assert set(primes.values()) == {0.0}
    assert o1["15"] == pytest.approx(4 / 7)
    assert o1["9"] == pytest.approx(0.8)
    assert o1["561"] == 0.0  # Korselt-blind, theorem-exact


def test_qpe_live_compute_matches_frozen_constants():
    v = claims.raw("qpe_15")
    assert v["Q"] == 625 and v["XD"] == 25
    assert v["r"] == 4
    # predicted peak bins: k = s * Q / r, s = 0..3 (measured bins sit next
    # to the fractional positions 0 / 156.25 / 312.5 / 468.75)
    for s in range(4):
        target = s * v["Q"] / v["r"]
        ks = [k for k in v["peak_ks"] if abs(k - target) <= 1]
        assert ks, f"no measured bin near {target}"
    assert set(v["peak_ks"]) == {0, 156, 157, 312, 313, 468, 469}


def test_korselt_blindness_control():
    assert claims.raw("korselt_561") is True
    assert claims.raw("hshor_561_order") == 80  # 80 | 560 — not 560
    assert claims.raw("hshor_prime_rate_max") == 0.0
    assert claims.raw("hshor_comp_rate_min") == pytest.approx(4 / 7)
    assert claims.raw("hshor_shor") == {"15": (3, 5), "21": (3, 7)}


def test_doc_frozen_claims_are_pinned_to_committed_docs():
    for cid, c in claims.CLAIMS.items():
        src = c.source
        if src.kind is not claims.Kind.DOC_FROZEN:
            continue
        path = REPO_ROOT / src.file
        assert path.exists(), cid
        lines = path.read_text(encoding="utf-8").splitlines()
        lo = max(0, (src.line or 1) - 41)
        hi = min(len(lines), (src.line or 1) + 40)
        window = "\n".join(lines[lo:hi])
        assert src.anchor in window, \
            f"{cid}: anchor {src.anchor!r} not near line {src.line}"
        # the on-screen number is part of the anchor itself
        assert str(c.value) in src.anchor, cid


# --------------------------------------------------------------------------
# Gate mechanics (publish-stop).
# --------------------------------------------------------------------------

def test_fidelity_gate_publish_stop(monkeypatch, tmp_path):
    c = claims.CLAIMS["bias_mean"]
    broken = claims.Claim(
        id=c.id, value=0.5, display=c.display, label=c.label,
        source=c.source, tol=c.tol, grade=c.grade, criterion=c.criterion,
        gloss=c.gloss, scenes=c.scenes, fmt=c.fmt)
    monkeypatch.setitem(claims.CLAIMS, "bias_mean", broken)
    mism = claims.check_gate(full=False)
    assert any("bias_mean" in m and "expected" in m and "recomputed" in m
               for m in mism)
    with pytest.raises(claims.FidelityGateError):
        claims.raise_if_gate_fails(full=False)


def test_check_gate_light_mode_skips_cmd_claims(monkeypatch):
    c = claims.CLAIMS["test_count"]
    broken = claims.Claim(
        id=c.id, value=999999, display=c.display, label=c.label,
        source=c.source, tol=c.tol, grade=c.grade, criterion=c.criterion,
        gloss=c.gloss, scenes=c.scenes, fmt=c.fmt)
    monkeypatch.setitem(claims.CLAIMS, "test_count", broken)
    # light gate: cmd claim skipped -> still passes
    assert claims.check_gate(full=False) == []
    # full gate: cmd claim checked -> mismatch reported
    assert any("test_count" in m for m in claims.check_gate(full=True))


# --------------------------------------------------------------------------
# AST scan: no unreachable on-screen numbers in the render scripts.
# --------------------------------------------------------------------------

def _digit_free(s: str) -> bool:
    return not any(ch.isdigit() for ch in s)


def _allowed_string(s: str) -> bool:
    return (_digit_free(s) or s in claims.DECORATIVE
            or s in claims.DECORATIVE_CSS or s in claims.CLAIM_IDS)


def _string_constants(tree):
    consts = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            consts.append(node.value)
    return consts


def _numeric_constants(tree):
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)) and not isinstance(
                    node.value, bool):
                out.append(node.value)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            if isinstance(node.operand, ast.Constant) and isinstance(
                    node.operand.value, (int, float)):
                out.append(-node.operand.value)
    return out


def _script_tree(name: str):
    path = PRESENTATION_DIR / name
    if not path.exists():
        return None
    return ast.parse(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("script", ["render_manim.py", "build_deck.py"])
def test_no_unreachable_on_screen_numbers(script):
    tree = _script_tree(script)
    if tree is None:
        pytest.skip(f"{script} not written yet")
    bad_strings, bad_nums = [], []
    for s in _string_constants(tree):
        if not _allowed_string(s):
            bad_strings.append(s)
    for n in _numeric_constants(tree):
        if n not in claims.DECORATIVE_NUMS:
            bad_nums.append(n)
    assert not bad_strings, f"{script}: digit strings outside whitelist: {bad_strings}"
    assert not bad_nums, f"{script}: numeric literals outside DECORATIVE_NUMS: {bad_nums}"


def test_scenes_registry_matches_render_script():
    tree = _script_tree("render_manim.py")
    if tree is None:
        pytest.skip("render_manim.py not written yet")
    defined = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            name = node.name
            snake = "".join(
                ("_" + ch.lower() if ch.isupper() else ch) for ch in name
            ).lstrip("_")
            if snake.startswith("act"):
                defined.add(snake)
    assert defined == set(claims.SCENES), \
        f"scene classes {sorted(defined)} != SCENES {sorted(claims.SCENES)}"


# --------------------------------------------------------------------------
# Medium gates (skip-if-absent; no rendering inside pytest).
# --------------------------------------------------------------------------

def _ffprobe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_streams", "-show_format", str(path)],
        capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


EXPECTED_MEDIA = {f"presentation/media/{slug}.mp4" for slug in claims.SCENES}


def test_medium_gate_media_present():
    media = sorted(PRESENTATION_DIR.glob("media/*.mp4"))
    if not media:
        pytest.skip("no rendered media yet")
    have = {str(p.relative_to(REPO_ROOT)) for p in media}
    assert have == EXPECTED_MEDIA, f"missing/extra: {have ^ EXPECTED_MEDIA}"
    for p in media:
        assert p.stat().st_size > 10_000, f"{p} suspiciously small"
        if subprocess.run(["which", "ffprobe"], capture_output=True).returncode:
            pytest.skip("ffprobe unavailable")
        probe = _ffprobe(p)
        vstream = next(s for s in probe["streams"]
                       if s["codec_type"] == "video")
        assert vstream["codec_name"] == "h264", p
        assert vstream["pix_fmt"] == "yuv420p", p
        dur = float(probe["format"]["duration"])
        assert 10.0 <= dur <= 60.0, f"{p}: duration {dur}s"


def test_medium_gate_deck_references_media():
    deck = PRESENTATION_DIR / "deck.html"
    if not deck.exists():
        pytest.skip("deck.html not built yet")
    html = deck.read_text(encoding="utf-8")
    for rel in EXPECTED_MEDIA:
        name = Path(rel).name
        assert name in html, f"deck does not reference {name}"


def test_deck_media_index_consistent():
    deck = PRESENTATION_DIR / "deck.html"
    media = sorted(PRESENTATION_DIR.glob("media/*.mp4"))
    if not deck.exists() or not media:
        pytest.skip("deck or media absent")
    html = deck.read_text(encoding="utf-8")
    refs = {m.stem for m in media if m.stem in html}
    assert refs == {m.stem for m in media}


def test_fidelity_report_writable(tmp_path):
    out = claims.write_report(path=tmp_path / "report.md")
    text = out.read_text(encoding="utf-8")
    assert "Gate:** PASS" in text
    assert "| id |" in text
    for cid in ("alpha_1e6", "kappa_star", "hshor_verdict", "ram_gated"):
        assert cid in text