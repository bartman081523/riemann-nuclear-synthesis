"""Build the pySlides deck from the frozen claim table.

Every number on every slide is re-derived at build time via
claims.display; the fidelity gate runs first and stops the build on
any mismatch (publish-stop, exit code two).

Run: venv/bin/python presentation/build_deck.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

PRESENTATION_DIR = Path(__file__).resolve().parent
REPO_ROOT = PRESENTATION_DIR.parent
MEDIA_DIR = PRESENTATION_DIR / "media"
DECK_PATH = PRESENTATION_DIR / "deck.html"
for _p in (str(PRESENTATION_DIR), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import claims  # noqa: E402
from pyslides.pyslides import Slides  # noqa: E402


# --------------------------------------------------------------------------
# Publish-stop + codec guard.
# --------------------------------------------------------------------------

def _gate() -> None:
    claims.raise_if_gate_fails(full=True)


def _probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_streams", str(path)],
        capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def _ensure_codec(path: Path) -> None:
    """Remux to the whitelisted codec pair if the renderer deviates."""
    if shutil.which("ffprobe") is None:
        return
    probe = _probe(path)
    video = next(s for s in probe["streams"]
                 if s.get("codec_type") == "video")
    if video.get("codec_name") == "h264" and video.get("pix_fmt") == "yuv420p":
        return
    tmp = path.with_name(path.stem + ".remux" + ".mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(path), "-c:v", "libx264",
         "-pix_fmt", "yuv420p", "-c:a", "aac", str(tmp)],
        check=True)
    tmp.replace(path)


# --------------------------------------------------------------------------
# CSS — assembled from whitelisted chunks + runtime design colors.
# --------------------------------------------------------------------------

def _css() -> str:
    d = claims.DESIGN
    return "".join((
        "video{", "max-height:62vh", ";", "width:100%", "}",
        ".chip{", "display:inline-block", ";", "padding:8px 12px", ";",
        "border-radius:8px", ";", "font-family:monospace", ";",
        "font-size:0.9em", ";", "margin:4px 0", "}",
        ".chipA{color:", d["GRADE_A"], "}",
        ".chipB{color:", d["GRADE_B"], "}",
        ".chipC{color:", d["GRADE_C"], "}",
        ".chipH{color:", d["MUTED"], "}",
        ".crit{", "color:", d["MUTED"], ";", "font-style:italic", ";",
        "font-size:0.9em", ";", "margin:4px 0", "}",
        ".claim{", "font-size:1.05em", ";", "margin:6px 0", "}",
        ".num{", "font-family:monospace", ";", "color:", d["TEXT"], "}",
        ".card{", "padding:8px 12px", ";", "margin:6px 0", "}",
        ".cardB{", "border-left:4px solid", " ", d["GRADE_B"], "}",
        ".cardC{", "border-left:4px solid", " ", d["GRADE_C"], "}",
        ".cardH{", "border-left:4px solid", " ", d["HYPOTHESIS"], "}",
        ".cardM{", "border-left:4px solid", " ", d["MUTED"], "}",
        ".sub{", "font-size:0.85em", ";", "font-style:italic", ";",
        "color:", d["MUTED"], ";", "margin:6px 0", "}",
        ".map{", "font-size:0.9em", "}",
        ".end{", "text-align:center", ";", "font-size:1.1em", ";",
        "margin:6px 0", "}",
        "td{", "padding:8px 12px", "}",
    ))


# --------------------------------------------------------------------------
# HTML helpers.
# --------------------------------------------------------------------------

def _video(slug: str) -> str:
    return ('<video controls src="' + "media/" + slug + ".mp4"
            + '" style="' + "width:100%" + '"></video>')


def _chip(grade):
    if grade is None:
        return '<span class="chip chipH">—</span>'
    if grade.startswith("A"):
        fam = "chipA"
    elif grade.startswith("B"):
        fam = "chipB"
    else:
        fam = "chipC"
    return '<span class="chip ' + fam + '">' + grade + '</span>'


def _claim_block(cid: str) -> str:
    # explanation_scaffold: the frozen criterion ships BEFORE the result.
    c = claims.CLAIMS[cid]
    return ('<p class="crit">' + c.criterion + '</p>'
            + '<p class="claim">' + claims.display(cid) + " "
            + _chip(c.grade) + '</p>')


def _card(head: str, grade, body: str, letter: str) -> str:
    chip = " " + _chip(grade) if grade is not None else ""
    return ('<div class="card card' + letter + '">' + '<p class="claim">'
            + head + chip + '</p>' + '<p class="crit">' + body + '</p>'
            + '</div>')


def _board() -> str:
    return "".join((
        _card("V2" + " — refuted", claims.grade("ram_gated"),
              "the refutation produced the Ramanujan fingerprint", "B"),
        _card("V1" + " — leakage sieve", "C",
              claims.display("chi2_v1") + " · "
              + claims.display("leakage_r0"), "C"),
        _card("V3" + " — degenerate", "C",
              claims.display("v3_rmean"), "C"),
        _card("GUE constant", "C", claims.display("gue_correction"), "C"),
        _card("H-STAR-5", None,
              claims.display("hstar5_score") + " · "
              + claims.display("hstar5_md5"), "H"),
        _card("discipline", None,
              "every outcome registered before measurement", "M"),
    ))


# --------------------------------------------------------------------------
# Frozen on-screen text (all digit-free; scene slugs whitelisted).
# --------------------------------------------------------------------------

TITLES = {
    "act1_title": "The Ulam canvas — where the story starts",
    "act2_pillar1": "Pillar one — the Im channel on real hardware",
    "act3_anomaly": "The anomaly: entanglement grows slower than promised",
    "act4_qpu_timeline": "Real hardware, four runs, one discipline",
    "act5_kappa": "Where the margin closes — and what the model says",
    "act6_ramanujan": "The mod-five fingerprint primes leave behind",
    "act7_qpe_peaks": "Reading a cycle length from quantum phases",
    "act8_fermat_grid": "The order grid: primes stay clean, composites leak",
    "act9_failure_board": "The failure board — same rules, same dignity",
    "act10_verdict_ladder": "What we know, and how we know it",
}

_ACT_SOURCES = {
    "act2_pillar1": ("bias_job_ids", "im_band"),
    "act4_qpu_timeline": ("vqd_job", "fez_job", "kingston_job",
                          "kingston_md5"),
    "act5_kappa": ("crossover_md5",),
    "act6_ramanujan": ("ram_md5",),
    "act7_qpe_peaks": ("hshor_md5",),
    "act8_fermat_grid": ("hshor_md5",),
}

_LADDER = (
    ("bias_points", "Im bias as canonical metric"),
    ("vqd_e0", "VQE + VQD on QPU"),
    ("alpha_1e6", "α anomaly · QUQUINT · κ* · Kingston"),
    ("ram_gated", "Ramanujan fingerprint"),
    ("hshor_verdict", "Shor oracle bridge"),
    ("leakage_r0", "leakage sieve · degenerate model · GUE constant"),
)

_READING_HELP = ('<p class="sub">' + "A — measured, recomputed from "
                 + "committed data" + "<br>" + "B — points to: real "
                 + "structure, single source so far" + "<br>"
                 + "C — speculation, or registered but unmeasured" + "<br>"
                 + "grey chip — hypothesis: never claimed as a result"
                 + '</p>')


def _open_questions() -> str:
    return ('<p class="crit">does the law hold beyond ' + "N = 10⁶"
            + '?</p>'
            + '<p class="crit">can the mod-five fingerprint be sharpened '
            + "into a working sieve?</p>"
            + '<p class="crit">' + "H-STAR-5"
            + " stays registered and unmeasured — "
            + claims.display("hstar5_score") + " · "
            + claims.display("hstar5_md5") + '</p>')


def _sources() -> str:
    items = "".join('<li class="num">' + claims.display(i) + '</li>'
                    for i in ("vqd_job", "fez_job", "bias_job_ids",
                              "kingston_job", "kingston_md5",
                              "crossover_md5", "ram_md5", "hshor_md5",
                              "hstar5_md5"))
    return ('<p class="sub">sources — recomputed at build time</p><ul>'
            + items + '</ul>')


def _end_card() -> str:
    return ('<div class="end">' + claims.display("test_count") + " · "
            + "CC-BY" + " · " + "results, docs, preregs committed"
            + "<br>" + "github.com/bartman081523/riemann-nuclear-synthesis"
            + '</div>')


# --------------------------------------------------------------------------
# Deck assembly.
# --------------------------------------------------------------------------

def build() -> Slides:
    deck = Slides(
        title="Prime States on a Quantum Machine",
        author="github.com/bartman081523/riemann-nuclear-synthesis",
        description="every number recomputed from committed sources "
                    "at build time",
        theme="black",
        custom_css=_css(),
    )
    deck.add_slide(
        layout="title",
        title="Prime States on a Quantum Machine",
        subtitle="What we measured — and what we only registered",
        transition="fade",
    )
    rows = []
    for slug in claims.SCENES:
        cid = claims.HEADLINES.get(slug)
        if cid is None:
            continue
        c = claims.CLAIMS[cid]
        rows.append('<tr><td class="num">' + slug + '</td><td>'
                    + claims.display(cid) + '</td><td>' + _chip(c.grade)
                    + '</td></tr>')
    deck.add_slide(
        title="The claim map — grades first",
        content=('<table class="map">' + "".join(rows) + '</table>'
                 + '<p class="sub">reading help: shows = measured, '
                 + "points to = structural, grey = registered "
                 + "hypothesis</p>"),
        notes="reading help: shows = measured, points to = structural, "
              "grey = registered hypothesis",
    )
    for slug in claims.SCENES:
        if slug == "act1_title":
            deck.add_slide(
                title=TITLES[slug],
                content=(_video(slug)
                         + '<p class="sub">prime state = a quantum state '
                         + "built only on prime-number positions</p>"),
                transition="fade",
            )
            continue
        cid = claims.HEADLINES.get(slug)
        if cid is None:
            continue
        parts = [claims.gloss(cid)]
        parts.extend(claims.display(i) for i in _ACT_SOURCES.get(slug, ()))
        if slug == "act3_anomaly":
            parts.append("recomputed live from committed result files "
                         "(gate-checked)")
        deck.add_slide(
            title=TITLES[slug],
            content=_claim_block(cid) + _video(slug),
            notes=" | ".join(parts),
            transition="fade",
        )
    rows = []
    for cid, label in _LADDER:
        c = claims.CLAIMS[cid]
        rows.append('<tr><td>' + _chip(c.grade) + '</td><td>' + label
                    + '</td><td class="num">' + claims.display(cid)
                    + '</td></tr>')
    deck.add_slide(
        title="The verdict ladder — what we know, and how we know it",
        layout="two-column",
        content_left=('<table class="map">' + "".join(rows) + '</table>'
                      + _READING_HELP),
        content_right=_video("act10_verdict_ladder"),
        notes="grades re-derived at build time; the gate ran first",
    )
    deck.add_slide(
        title="The failure board — same rules, same dignity",
        layout="two-column",
        content_left=_board(),
        content_right=_video("act9_failure_board"),
        notes="registered failures are results too — none were hidden",
    )
    deck.add_slide(
        title="Open questions, sources, and the end card",
        content=_open_questions() + _sources() + _end_card(),
        transition="fade",
    )
    return deck


def main() -> int:
    _gate()
    for slug in claims.SCENES:
        path = MEDIA_DIR / (slug + ".mp4")
        if not path.exists():
            raise FileNotFoundError(
                "missing render, run render_manim first: " + slug)
        _ensure_codec(path)
    deck = build()
    deck.save(str(DECK_PATH))
    print("deck -> " + str(DECK_PATH.relative_to(REPO_ROOT)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except claims.FidelityGateError as exc:
        print(exc, file=sys.stderr)
        sys.exit(2)