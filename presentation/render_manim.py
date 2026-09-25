"""Render the ten presentation scenes with manim.

SciComPresentationMind — visual_encoding + explanation_scaffold + gate.

Rules baked into this file:
- Every on-screen number flows through ``claims`` (display/raw/plot_data/
  frozen_value). The AST test enforces mechanically that no other digit
  reaches the screen — every string constant here must be digit-free or
  whitelisted, every numeric constant must sit in claims.DECORATIVE_NUMS.
- The frozen criterion is shown BEFORE the result in every headline scene.
- The failure board uses the same chip geometry as successes — no red.

CLI:
    python presentation/render_manim.py --draft [--only <slug>]
    python presentation/render_manim.py --final [--only <slug>]
    python presentation/render_manim.py --list

``--final`` renders at full size, thirty frames per second; the fidelity
gate runs before any production and stops with exit code two on a
mismatch (publish-stop).
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
PRESENTATION_DIR = Path(__file__).resolve().parent
for _p in (str(REPO_ROOT), str(PRESENTATION_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import claims  # noqa: E402

from manim import (  # noqa: E402
    DOWN, ITALIC, BOLD, LEFT, RIGHT, UP, UR, Axes, Arrow, Cross, Create,
    DashedLine, Dot, FadeIn, FadeOut, Indicate, LaggedStart, Line,
    ManimColor, Polygon, Rectangle,
    ReplacementTransform, RoundedRectangle, Scene, Text, ValueTracker,
    VMobject, VGroup, Write, always_redraw, config,
)

_COL = {key: ManimColor(value) for key, value in claims.DESIGN.items()}
config.background_color = _COL["BG"]

_TEXT_W = 12.0  # max on-screen text width before auto-shrink


# --------------------------------------------------------------------------
# Shared building blocks (one chip geometry everywhere — failure-board
# dignity comes from identical geometry, not from color coding).
# --------------------------------------------------------------------------

def _fit(mobj, max_width: float = _TEXT_W):
    if mobj.width > max_width:
        mobj.scale(max_width / mobj.width)
    return mobj


def _grade_color(grade) -> str:
    if grade is None:
        return "HYPOTHESIS"
    if grade.startswith("A"):
        return "GRADE_A"
    if grade.startswith("B"):
        return "GRADE_B"
    return "GRADE_C"


def _chip(label: str, color_key: str) -> VGroup:
    col = _COL[color_key]
    text = Text(label, font_size=24, color=col, weight=BOLD)
    box = RoundedRectangle(
        corner_radius=0.06, width=text.width + 0.4,
        height=text.height + 0.25, stroke_color=col, stroke_width=2.0,
        fill_color=col, fill_opacity=0.12)
    box.move_to(text)
    return VGroup(box, text)


def _header(title_text: str, cid: str | None = None) -> VGroup:
    title = _fit(Text(title_text, font_size=36, color=_COL["TEXT"],
                      weight=BOLD)).move_to(3.2 * UP)
    parts = VGroup(title)
    if cid is not None:
        crit = _fit(Text(claims.criterion(cid), font_size=26,
                         color=_COL["MUTED"], slant=ITALIC))
        crit.next_to(title, 0.3 * DOWN)
        parts.add(crit)
    return parts


def _takeaway(text: str, grade=None) -> VGroup:
    label = _fit(Text(text, font_size=26, color=_COL["TEXT"]))
    group = VGroup(label)
    if grade is not None:
        chip = _chip(grade, _grade_color(grade))
        chip.next_to(label, 0.4 * RIGHT)
        group.add(chip)
    group.move_to(3.2 * DOWN)
    return group


def _gloss(text: str) -> Text:
    return _fit(Text(text, font_size=24, color=_COL["MUTED"], slant=ITALIC))


def _polyline(axes, xs, ys, color_key: str, width: float = 3.0) -> VMobject:
    pts = [axes.c2p(x, y) for x, y in zip(xs, ys)]
    return VMobject(color=_COL[color_key], stroke_width=width) \
        .set_points_as_corners(pts)


# Runtime-built number strings: format specs are digit-bearing constants
# for the AST test, so rounding happens through these helpers instead.
def _fmt(v, nd: int) -> str:
    r = round(float(v), nd)
    return str(0.0 if r == 0 else r)


def _fmt_int(v) -> str:
    return str(int(round(float(v), 0)))


def _neg(v):
    return -v


def _tick_labels(axis, values, nd: int, signed: bool = False) -> VGroup:
    def _lab(v):
        s = _fmt_int(v) if nd == 0 else _fmt(v, nd)
        if signed and v > 0:
            s = "+" + s
        return Text(s, font_size=20, color=_COL["MUTED"])
    labs = {v: _lab(v) for v in values}
    axis.add_labels(labs)
    return VGroup(*(labs[v] for v in values))


# --------------------------------------------------------------------------
# act1_title — decorative Ulam grid, title, subtitle, gloss (20 s).
# --------------------------------------------------------------------------

def _ulam_points(count: int):
    """Square-spiral coordinates, ordered by the integer they encode."""
    dirs = ((1, 0), (0, 1), (_neg(1), 0), (0, _neg(1)))
    pts = []
    x = y = d = turns = 0
    seg = remaining = 1
    for _ in range(count):
        pts.append((x, y))
        x += dirs[d][0]
        y += dirs[d][1]
        remaining -= 1
        if remaining == 0:
            d = (d + 1) % 4
            turns += 1
            if turns % 2 == 0:
                seg += 1
            remaining = seg
    return pts


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    f = 2
    while f * f <= n:
        if n % f == 0:
            return False
        f += 1
    return True


class Act1Title(Scene):
    def construct(self):
        spacing = 0.15
        pts = _ulam_points(400)
        dots = VGroup(*(
            Dot(np.array([px, py, 0.0]) * spacing,
                radius=0.04 if _is_prime(n + 1) else 0.02,
                color=_COL["PRIME"] if _is_prime(n + 1) else _COL["MUTED"],
                fill_opacity=0.9 if _is_prime(n + 1) else 0.35)
            for n, (px, py) in enumerate(pts)))
        self.play(LaggedStart(*[Create(d) for d in dots], lag_ratio=0.15),
                  run_time=6.0)
        self.play(dots.animate.set_opacity(0.25), run_time=1.5)

        title = Text("Prime States on a Quantum Machine", font_size=48,
                     color=_COL["TEXT"], weight=BOLD)
        subtitle = Text("What we measured — and what we only registered",
                        font_size=32, color=_COL["MUTED"])
        subtitle.next_to(title, 0.5 * DOWN)
        self.play(Write(title), run_time=2.5)
        self.play(FadeIn(subtitle), run_time=1.0)

        gloss = _gloss("prime state = a quantum state built only on "
                       "prime-number positions")
        gloss.next_to(subtitle, 0.45 * DOWN)
        self.play(Write(gloss), run_time=1.5)

        foot = VGroup(
            Text(claims.display("test_count"), font_size=24,
                 color=_COL["MUTED"]),
            Text("github.com/bartman081523/riemann-nuclear-synthesis",
                 font_size=24, color=_COL["MUTED"]),
        ).arrange(1.0 * RIGHT).move_to(3.5 * DOWN)
        self.play(FadeIn(foot), run_time=1.0)
        self.wait(6.5)


# --------------------------------------------------------------------------
# act2_pillar1 — Im-channel bias bars inside the frozen band (30 s).
# --------------------------------------------------------------------------

class Act2Pillar1(Scene):
    def construct(self):
        self.play(FadeIn(_header(
            "Pillar one — the Im channel on real hardware", "bias_points")),
            run_time=2.0)

        values = list(claims.raw("bias_points"))
        band = claims.raw("im_band")
        axes = Axes(
            x_range=(0, 5, 1), y_range=(-0.006, 0.006, 0.003),
            x_length=10.0, y_length=3.0,
            axis_config={"color": _COL["AXIS"], "tick_size": 0.08,
                         "include_numbers": False})
        axes.move_to(0.3 * DOWN)
        x_lab = Text("theta points", font_size=24, color=_COL["MUTED"])
        x_lab.next_to(axes, 0.35 * DOWN)
        y_lab = Text("bias", font_size=24, color=_COL["MUTED"])
        y_lab.next_to(axes.y_axis, 0.5 * UP)
        _tick_labels(axes.y_axis,
                     [-0.006 + i * 0.003 for i in range(5)], 3, signed=True)
        self.play(Create(axes), FadeIn(x_lab), FadeIn(y_lab), run_time=2.0)

        # The frozen band FIRST (explanation_scaffold: criterion before
        # result — the band is the registered expectation, not the data).
        top = axes.c2p(0, band)
        bottom = axes.c2p(0, _neg(band))
        band_rect = Rectangle(
            width=axes.c2p(5, 0)[0] - axes.c2p(0, 0)[0],
            height=top[1] - bottom[1],
            stroke_color=_COL["FROZEN"], stroke_width=2.0,
            fill_color=_COL["FROZEN"], fill_opacity=0.12)
        band_rect.move_to(axes.c2p(2.5, 0))
        band_label = _fit(Text(claims.display("im_band"), font_size=24,
                               color=_COL["FROZEN"]))
        band_label.next_to(band_rect, 0.25 * UP)
        self.play(Create(band_rect), Write(band_label), run_time=2.5)

        bars = VGroup()
        for i, v in enumerate(values):
            base = axes.c2p(i + 0.5, 0)
            tip = axes.c2p(i + 0.5, v)
            bar = Polygon(
                [base[0] - 0.3, base[1], 0], [base[0] + 0.3, base[1], 0],
                [tip[0] + 0.3, tip[1], 0], [tip[0] - 0.3, tip[1], 0],
                fill_color=_COL["QPU"], fill_opacity=0.8,
                stroke_color=_COL["QPU"], stroke_width=2.0)
            bars.add(bar)
        self.play(LaggedStart(*[Create(b) for b in bars], lag_ratio=0.15),
                  run_time=5.0)

        readouts = VGroup(*(
            _fit(Text(claims.display(cid), font_size=24, color=_COL["QPU"]))
            for cid in ("bias_mean", "bias_std", "bias_max_abs")
        )).arrange(1.2 * RIGHT).move_to(2.0 * UP + 1.0 * RIGHT)
        self.play(FadeIn(readouts), run_time=3.0)

        takeaway = _takeaway(
            "shows: the quantum machine adds no measurable skew to the "
            "Im channel", claims.grade("bias_points"))
        gloss = _gloss(claims.gloss("bias_points")) \
            .next_to(takeaway, 0.25 * UP).to_edge(0.4 * LEFT)
        self.play(Write(gloss), run_time=1.5)
        self.play(FadeIn(takeaway), run_time=3.0)
        self.wait(9.0)


# --------------------------------------------------------------------------
# act3_anomaly — the alpha anomaly, log-x, Latorre line excluded (40 s).
# --------------------------------------------------------------------------

class Act3Anomaly(Scene):
    def construct(self):
        self.play(FadeIn(_header(
            "The anomaly: entanglement grows slower than promised",
            "alpha_1e6")), run_time=2.0)

        pts = list(claims.raw("alpha_curve"))
        ns = [n for n, _ in pts]
        alphas = [a for _, a in pts]
        xs = [np.log10(n) for n in ns]
        axes = Axes(
            x_range=(1.2, 6.5, 1), y_range=(0, 1.1, 0.25),
            x_length=10.0, y_length=3.5,
            axis_config={"color": _COL["AXIS"], "tick_size": 0.08,
                         "include_numbers": False})
        axes.move_to(0.2 * UP)
        x_lab = Text("x: log10 N", font_size=24, color=_COL["MUTED"])
        x_lab.move_to(axes.c2p(6.5, 0)).shift(1.0 * DOWN)
        y_lab = Text("S_vN", font_size=24, color=_COL["MUTED"])
        y_lab.next_to(axes.y_axis, 0.4 * UP)
        _tick_labels(axes.y_axis, [0 + i * 0.25 for i in range(5)], 2)
        decade = dict(zip([2, 3, 4, 5, 6],
                          ["10²", "10³", "10⁴", "10⁵", "10⁶"]))
        decade_labels = VGroup(*(
            Text(decade[k], font_size=20, color=_COL["MUTED"])
            .move_to(axes.c2p(k, 0) + 0.35 * DOWN) for k in decade))
        self.play(Create(axes), FadeIn(x_lab), FadeIn(y_lab),
                  FadeIn(decade_labels), run_time=3.0)

        # Latorre–Sierra promise FIRST (α = 1), then the measured curve.
        latorre = DashedLine(axes.c2p(1.2, 1), axes.c2p(6.5, 1),
                             color=_COL["FROZEN"], stroke_width=3.0)
        latorre_label = _fit(Text(claims.display("alpha_latorre"),
                                  font_size=24, color=_COL["FROZEN"]))
        latorre_label.next_to(axes.c2p(4.5, 1), 0.35 * UP)
        cross = Cross(stroke_color=_COL["FROZEN"], stroke_width=4.0) \
            .scale(0.2).move_to(axes.c2p(6.0, 1))
        self.play(Create(latorre), Write(latorre_label), Create(cross),
                  run_time=4.0)

        tracker = ValueTracker(2.0)
        curve = always_redraw(
            lambda: _polyline(axes, xs[:int(tracker.get_value())],
                              alphas[:int(tracker.get_value())], "QPU"))
        self.play(tracker.animate.set_value(9.0), run_time=6.0)
        dots = VGroup(*(Dot(axes.c2p(x, a), radius=0.06,
                            color=_COL["QPU"], fill_opacity=0.9)
                        for x, a in zip(xs, alphas)))
        self.play(LaggedStart(*[FadeIn(d, scale=1.5) for d in dots],
                              lag_ratio=0.15), run_time=3.0)

        readout = Text(claims.display("alpha_at_31"), font_size=26,
                       color=_COL["TEXT"])
        readout.move_to(axes.c2p(2.5, 0.6))
        self.play(Write(readout), run_time=1.5)
        readout_end = Text(claims.display("alpha_1e6"), font_size=26,
                           color=_COL["TEXT"])
        readout_end.move_to(readout)
        self.play(ReplacementTransform(readout, readout_end), run_time=1.5)

        # QPU point: same architecture, real hardware, same sub-linear law.
        x_qpu = np.log10(ns[2])
        qpu_dot = Dot(axes.c2p(x_qpu, claims.raw("alpha_qpu")), radius=0.08,
                      color=_COL["PRIME"], fill_opacity=0.95)
        qpu_label = _fit(Text(claims.display("alpha_qpu"), font_size=24,
                              color=_COL["PRIME"]))
        qpu_label.next_to(qpu_dot, 0.45 * UP)
        self.play(Create(qpu_dot), Indicate(qpu_dot, scale_factor=1.6),
                  Write(qpu_label), run_time=4.0)

        gloss_a = _gloss(claims.gloss("alpha_1e6"))
        gloss_s = _gloss("Schmidt entropy = how much quantum correlation "
                         "the prime state carries")
        glosses = VGroup(gloss_a, gloss_s).arrange(0.25 * DOWN) \
            .move_to(2.5 * DOWN).to_edge(0.4 * LEFT)
        self.play(FadeIn(glosses), run_time=3.0)

        a_end = claims.raw("alpha_1e6")
        self.play(FadeIn(_takeaway(
            "shows: entanglement grows like N^" + _fmt(a_end, 2)
            + ", not like N", claims.grade("alpha_1e6"))), run_time=3.0)
        self.wait(5.0)


# --------------------------------------------------------------------------
# act4_qpu_timeline — four hardware runs, backend cards, phi bars (30 s).
# --------------------------------------------------------------------------

class Act4QpuTimeline(Scene):
    def construct(self):
        self.play(FadeIn(_header(
            "Real hardware, four runs, one discipline", "fez_phi")),
            run_time=2.0)

        dates = [claims.display("date_fez_singleshot"),
                 claims.display("date_vqd"),
                 claims.display("date_fez_phi"),
                 claims.display("date_kingston")]
        events = ["singleshot tomography", "VQE + VQD", "phi crossover QPU",
                  "Kingston drift test"]
        colors = ["MUTED", "GRADE_A", "QPU", "QPU"]
        line = Line(5.5 * LEFT + 1.75 * UP, 5.5 * RIGHT + 1.75 * UP,
                    color=_COL["AXIS"], stroke_width=3.0)
        marks = VGroup()
        for i, (d, ev) in enumerate(zip(dates, events)):
            x = (i - 1.5) * 3.5
            mark = Dot(np.array([x, 1.75, 0.0]), radius=0.08,
                       color=_COL[colors[i]], fill_opacity=0.95)
            date_lab = Text(d, font_size=24, color=_COL[colors[i]])
            date_lab.move_to(mark.get_center() + 0.35 * UP)
            ev_lab = _fit(Text(ev, font_size=20, color=_COL[colors[i]]))
            ev_lab.move_to(mark.get_center() + 0.4 * DOWN)
            marks.add(VGroup(mark, date_lab, ev_lab))
        self.play(Create(line), run_time=2.0)
        self.play(LaggedStart(*[FadeIn(m, shift=0.3 * UP) for m in marks],
                              lag_ratio=0.15), run_time=5.0)

        # Backend cards carry the job IDs and the per-run readouts.
        cards = VGroup()
        card_lines = [
            ("ibm_fez", [claims.display("vqd_job"),
                         claims.display("fez_job"),
                         claims.display("fez_bands_hold")], "QPU"),
            ("ibm_fez", [claims.display("bias_job_ids"),
                         claims.display("bias_mean")], "QPU"),
            ("ibm_kingston", [claims.display("kingston_job"),
                              claims.display("kingston_bias")], "QPU"),
        ]
        for i, (name, lines, key) in enumerate(card_lines):
            body = VGroup(Text(name, font_size=24, color=_COL[key],
                               weight=BOLD),
                          *[_fit(Text(ln, font_size=20,
                                      color=_COL["MUTED"]), 3.5)
                            for ln in lines]).arrange(0.15 * DOWN)
            box = RoundedRectangle(corner_radius=0.06, width=4.0,
                                   height=1.75, stroke_color=_COL[key],
                                   stroke_width=2.0)
            box.move_to(body)
            card = VGroup(box, body)
            card.move_to(((i - 1) * 4.5) * RIGHT + 0.25 * UP)
            cards.add(card)
        self.play(LaggedStart(*[FadeIn(c, scale=0.9) for c in cards],
                              lag_ratio=0.15), run_time=6.0)

        # phi / sep bars against the frozen 1/5 bound (from the prereg).
        phi = claims.raw("fez_phi")
        sep = claims.raw("fez_sep")
        bound = claims.raw("ququint_bound")
        hmax = max(phi, sep, bound)
        base_y = _neg(2.2)
        bars = VGroup()
        for i, (v, cid) in enumerate(((phi, "fez_phi"),
                                      (sep, "fez_sep"))):
            h = v / hmax * 1.75
            bar = Rectangle(width=0.9, height=h,
                            fill_color=_COL["COMPOSITE"],
                            fill_opacity=0.8,
                            stroke_color=_COL["COMPOSITE"],
                            stroke_width=2.0)
            bar.move_to(((i - 3.5) * 1.4) * RIGHT + (base_y + h / 2) * UP)
            lab = _fit(Text(claims.display(cid), font_size=20,
                            color=_COL["TEXT"]))
            lab.move_to(bar.get_center())
            bars.add(VGroup(bar, lab))
        bline_y = base_y + bound / hmax * 1.75
        bline = DashedLine(6.5 * LEFT + bline_y * UP,
                           2.0 * LEFT + bline_y * UP,
                           color=_COL["FROZEN"], stroke_width=2.0)
        blab = _fit(Text(claims.display("ququint_bound"), font_size=20,
                         color=_COL["FROZEN"]))
        blab.next_to(bline.get_end(), 0.25 * DOWN).shift(1.5 * RIGHT)
        self.play(LaggedStart(*[FadeIn(b) for b in bars], lag_ratio=0.2),
                  Create(bline), Write(blab), run_time=6.0)

        takeaway = _takeaway(
            "real hardware lands inside every frozen band",
            claims.grade("fez_phi"))
        gloss = _gloss(claims.gloss("fez_phi")) \
            .next_to(takeaway, 0.25 * UP).to_edge(0.4 * LEFT)
        self.play(FadeIn(gloss), run_time=1.0)
        self.play(FadeIn(takeaway), run_time=3.0)
        self.wait(4.0)


# --------------------------------------------------------------------------
# act5_kappa — two frames: margin curve, then kappa* with bracket (40 s).
# --------------------------------------------------------------------------

class Act5Kappa(Scene):
    def construct(self):
        self.play(FadeIn(_header(
            "Where the margin closes — and what the model says",
            "kappa_star")), run_time=2.0)

        # Frame 1: margin vs noise level p1 (plotted as -log10 p1).
        pts = list(claims.raw("margin_curve"))
        noiseless = pts[0][1]
        rest = [(p, m) for p, m in pts if p > 0]
        xs = [-np.log10(p) for p, _ in rest]
        ys = [m for _, m in rest]
        axes = Axes(
            x_range=(2, 4.5, 0.5), y_range=(-0.15, 0.75, 0.25),
            x_length=7.0, y_length=3.5,
            axis_config={"color": _COL["AXIS"], "tick_size": 0.08,
                         "include_numbers": False})
        axes.move_to(0.1 * DOWN + 0.8 * LEFT)
        x_lab = Text("noise level (−log10 p1)", font_size=24,
                     color=_COL["MUTED"])
        x_lab.next_to(axes, 0.35 * DOWN).shift(0.4 * DOWN) \
            .align_to(axes, RIGHT)
        y_lab = Text("margin", font_size=24, color=_COL["MUTED"])
        y_lab.next_to(axes.y_axis, 0.4 * UP)
        _tick_labels(axes.x_axis, [2 + 0.5 * i for i in range(6)], 1)
        ylabs = _tick_labels(axes.y_axis,
                             [-0.15 + 0.25 * i for i in range(4)],
                             2, signed=True)
        ylabs[0].shift(0.4 * LEFT)  # clear of the 2.0 corner tick
        self.play(Create(axes), FadeIn(x_lab), FadeIn(y_lab), run_time=2.5)

        zero = DashedLine(axes.c2p(2, 0), axes.c2p(4.5, 0),
                          color=_COL["AXIS"], stroke_width=2.0)
        curve = _polyline(axes, xs, ys, "COMPOSITE")
        dots = VGroup(*(Dot(axes.c2p(x, y), radius=0.06,
                            color=_COL["COMPOSITE"], fill_opacity=0.9)
                        for x, y in zip(xs, ys)))
        self.play(Create(zero), Create(curve),
                  LaggedStart(*[FadeIn(d) for d in dots], lag_ratio=0.15),
                  run_time=4.0)
        note = _fit(Text("noiseless: margin = " + _fmt(noiseless, 3),
                         font_size=24, color=_COL["MUTED"], slant=ITALIC))
        note.move_to(axes.c2p(3.2, 0.6))
        cross_note = _fit(Text(claims.display("margin_sign_interval"),
                               font_size=24, color=_COL["FROZEN"]))
        cross_note.next_to(note, 0.2 * DOWN)
        self.play(Write(note), Write(cross_note), run_time=3.0)

        frame1 = VGroup(axes, x_lab, y_lab, zero, curve, dots, note,
                        cross_note)

        # Frame 2: kappa* per p1, bracket whisker, Rough marker inside.
        kpts = list(claims.raw("kappa_per_p1"))
        kxs = [-np.log10(p) for p, _ in kpts]
        kys = [k for _, k in kpts]
        axes2 = Axes(
            x_range=(2, 4.5, 0.5), y_range=(0, 100, 20),
            x_length=7.0, y_length=3.5,
            axis_config={"color": _COL["AXIS"], "tick_size": 0.08,
                         "include_numbers": False})
        axes2.move_to(0.1 * DOWN + 0.8 * LEFT)
        x_lab2 = Text("noise level (−log10 p1)", font_size=24,
                      color=_COL["MUTED"])
        x_lab2.next_to(axes2, 0.35 * DOWN).shift(0.4 * DOWN) \
            .align_to(axes2, RIGHT)
        y_lab2 = Text("kappa", font_size=24, color=_COL["MUTED"])
        y_lab2.next_to(axes2.y_axis, 0.4 * UP)
        _tick_labels(axes2.x_axis, [2 + 0.5 * i for i in range(6)], 1)
        _tick_labels(axes2.y_axis, [0 + 20 * i for i in range(6)], 0)

        k_star = claims.raw("kappa_star")
        i_star = int(np.argmin([abs(k - k_star) for _, k in kpts]))
        curve2 = _polyline(axes2, kxs, kys, "COMPOSITE")
        dots2 = VGroup(*(Dot(axes2.c2p(x, y), radius=0.06,
                             color=_COL["COMPOSITE"], fill_opacity=0.9)
                         for x, y in zip(kxs, kys)))
        self.play(FadeOut(frame1), run_time=2.0)
        self.play(Create(axes2), FadeIn(x_lab2), FadeIn(y_lab2),
                  Create(curve2),
                  LaggedStart(*[FadeIn(d) for d in dots2], lag_ratio=0.15),
                  run_time=5.0)

        whisker = Line(axes2.c2p(kxs[i_star], claims.raw("kappa_bracket")[0]),
                       axes2.c2p(kxs[i_star], claims.raw("kappa_bracket")[1]),
                       color=_COL["FROZEN"], stroke_width=4.0)
        star_dot = Dot(axes2.c2p(kxs[i_star], k_star), radius=0.08,
                       color=_COL["FROZEN"], fill_opacity=0.95)
        star_lab = _fit(Text(claims.display("kappa_star"), font_size=24,
                             color=_COL["FROZEN"], weight=BOLD))
        star_lab.next_to(star_dot, 0.45 * UP)
        self.play(Create(whisker), Create(star_dot), Write(star_lab),
                  run_time=3.0)

        rough = claims.frozen_value("kappa_rough")
        rough_dot = Dot(axes2.c2p(kxs[i_star], rough), radius=0.08,
                        color=_COL["HYPOTHESIS"], fill_opacity=0.9)
        rough_lab = _fit(Text(claims.display("kappa_rough"), font_size=24,
                              color=_COL["HYPOTHESIS"]))
        rough_lab.next_to(rough_dot, 0.5 * LEFT)
        self.play(Create(rough_dot), Write(rough_lab), run_time=3.0)

        pct = abs(k_star - rough) / rough * 100
        agreement = Text("agreement: " + _fmt(pct, 1) + " %",
                         font_size=26, color=_COL["TEXT"])
        agreement.move_to(2.0 * UP + 3.5 * RIGHT)
        self.play(Write(agreement), run_time=2.5)

        self.play(FadeIn(_takeaway(
            "the crossover lands where the theory model placed it",
            claims.grade("kappa_star"))), run_time=3.0)
        self.wait(7.0)


# --------------------------------------------------------------------------
# act6_ramanujan — gated fingerprint: band, model, primes only (30 s).
# --------------------------------------------------------------------------

class Act6Ramanujan(Scene):
    def construct(self):
        self.play(FadeIn(_header(
            "The mod-five fingerprint primes leave behind", "ram_gated")),
            run_time=2.0)

        pts = list(claims.raw("ram_gated"))
        model = list(claims.raw("ram_model"))
        band_lo, band_hi = claims.raw("ram_band")
        limit = claims.raw("ram_overlap_limit")
        xs = [float(p) for p, _ in pts]
        ys = [v for _, v in pts]
        mxs = [float(p) for p, _ in model]
        m_ys = [v for _, v in model]

        axes = Axes(
            x_range=(400, 626, 100), y_range=(0, 0.06, 0.02),
            x_length=10.0, y_length=3.5,
            axis_config={"color": _COL["AXIS"], "tick_size": 0.08,
                         "include_numbers": False})
        axes.move_to(0.2 * DOWN)
        x_lab = Text("P", font_size=24, color=_COL["MUTED"])
        x_lab.move_to(axes.c2p(626, 0)).shift(0.45 * DOWN)
        y_lab = Text("share_prime", font_size=24, color=_COL["MUTED"])
        y_lab.next_to(axes.y_axis, 0.4 * UP)
        _tick_labels(axes.x_axis, [400 + 100 * i for i in range(3)], 0)
        _tick_labels(axes.y_axis, [0 + 0.02 * i for i in range(4)], 2)
        self.play(Create(axes), FadeIn(x_lab), FadeIn(y_lab), run_time=3.0)

        # Pre-registered band [lo, hi] x model around the exact prediction.
        lo_pts = [axes.c2p(x, band_lo * m) for x, m in zip(mxs, m_ys)]
        hi_pts = [axes.c2p(x, band_hi * m) for x, m in zip(mxs, m_ys)]
        band = Polygon(*lo_pts, *reversed(hi_pts),
                       stroke_color=_COL["FROZEN"], stroke_width=2.0,
                       fill_color=_COL["FROZEN"], fill_opacity=0.15)
        band_lab = _fit(Text(claims.display("ram_band"), font_size=24,
                             color=_COL["FROZEN"]))
        band_lab.next_to(axes.c2p(mxs[0], band_hi * m_ys[0]),
                         0.35 * UP).shift(0.65 * UP)
        self.play(Create(band), Write(band_lab), run_time=3.0)

        model_line = _polyline(axes, mxs, m_ys, "FROZEN", width=2.5)
        model_lab = _fit(Text(claims.display("ram_model"), font_size=24,
                              color=_COL["FROZEN"], slant=ITALIC))
        model_lab.next_to(
            axes.c2p(mxs[len(mxs) - 1], m_ys[len(m_ys) - 1]),
            0.5 * DOWN).align_to(axes, RIGHT).shift(0.55 * DOWN)
        self.play(Create(model_line), Write(model_lab), run_time=3.0)

        dots = VGroup(*(Dot(axes.c2p(x, y), radius=0.08,
                            color=_COL["PRIME"], fill_opacity=0.95)
                        for x, y in zip(xs, ys)))
        self.play(LaggedStart(*[FadeIn(d, scale=1.5) for d in dots],
                              lag_ratio=0.2), run_time=4.0)

        control = DashedLine(axes.c2p(400, limit), axes.c2p(626, limit),
                             color=_COL["COMPOSITE"], stroke_width=2.0)
        control_lab = _fit(Text(claims.display("ram_overlap_limit"),
                                font_size=24, color=_COL["COMPOSITE"]))
        control_lab.next_to(axes.c2p(625, limit), 0.35 * DOWN)
        self.play(Create(control), Write(control_lab), run_time=3.0)

        counter = _fit(Text(claims.display("ram_gated"), font_size=26,
                            color=_COL["PRIME"], weight=BOLD))
        gate = _fit(Text(claims.display("ram_gate_pi"), font_size=24,
                         color=_COL["MUTED"]))
        annots = VGroup(counter, gate).arrange(0.3 * DOWN)
        annots.move_to(4.5 * RIGHT + 2.0 * UP)
        self.play(Write(annots), run_time=3.0)

        # Origin line stays on screen: the fingerprint came out of a
        # refuted run, and the failure board carries the same dignity.
        # It takes the annotation slot, so it appears only after the
        # counter fades (top-right is otherwise occupied).
        found = _gloss("found by an experiment that failed — see the "
                       "failure board").move_to(2.0 * UP) \
            .to_edge(0.2 * RIGHT)
        self.play(FadeOut(annots), run_time=1.0)
        self.play(Write(found), run_time=2.0)
        self.play(FadeIn(_takeaway(
            "points to: a residue band only primes stay inside",
            claims.grade("ram_gated"))), run_time=2.5)
        self.wait(2.0)


# --------------------------------------------------------------------------
# act7_qpe_peaks — live QPE distribution vs predicted peaks (30 s).
# --------------------------------------------------------------------------

class Act7QpePeaks(Scene):
    def construct(self):
        self.play(FadeIn(_header(
            "Reading a cycle length from quantum phases",
            "hshor_bridge_min")), run_time=2.0)

        summ = claims.raw("qpe_15")
        res = claims.plot_data("qpe_15")
        q_max = summ["Q"]
        order_r = summ["r"]
        peaks = list(summ["peak_ks"])
        probs = list(res["probs"])
        n_val = summ["N"]
        a_val = summ["a"]

        window = Text("system: N = {}, a = {}, Q = {}".format(
            n_val, a_val, q_max), font_size=26, color=_COL["TEXT"])
        window.move_to(2.0 * UP).to_edge(0.4 * LEFT)
        gloss = _gloss(claims.gloss("hshor_bridge_min")).scale(
            20 / 24).move_to(2.0 * UP).to_edge(0.2 * RIGHT)
        self.play(Write(window), FadeIn(gloss), run_time=2.0)

        axes = Axes(
            x_range=(0, q_max, 100), y_range=(0, 0.28, 0.1),
            x_length=10.0, y_length=3.2,
            axis_config={"color": _COL["AXIS"], "tick_size": 0.08,
                         "include_numbers": False})
        axes.move_to(0.1 * UP)
        x_lab = Text("k (readout bin)", font_size=24, color=_COL["MUTED"])
        x_lab.next_to(axes, 0.35 * DOWN).shift(0.45 * DOWN) \
            .align_to(axes, RIGHT)
        y_lab = Text("probability", font_size=24, color=_COL["MUTED"])
        y_lab.next_to(axes.y_axis, 0.4 * LEFT)
        _tick_labels(axes.x_axis, [0 + 100 * i for i in range(7)], 0)
        _tick_labels(axes.y_axis, [0 + 0.1 * i for i in range(3)], 2)
        dist = VGroup(*(
            Line(axes.c2p(k, 0), axes.c2p(k, p),
                 color=_COL["COMPOSITE"], stroke_width=2.0)
            for k, p in enumerate(probs)))
        self.play(Create(axes), FadeIn(x_lab), FadeIn(y_lab),
                  run_time=2.5)
        self.play(Create(dist), run_time=6.0)

        # Predicted peak positions k = s * Q / r, straight from the readout.
        predicted = VGroup(*(
            DashedLine(axes.c2p(s * q_max / order_r, 0),
                       axes.c2p(s * q_max / order_r, 0.28),
                       color=_COL["FROZEN"], stroke_width=2.5)
            for s in range(order_r)))
        predicted_lab = Text("predicted peaks: k = s·Q/r", font_size=24,
                             color=_COL["FROZEN"])
        predicted_lab.move_to(axes.c2p(q_max * 0.6, 0.25))
        self.play(Create(predicted), Write(predicted_lab), run_time=5.0)

        measured = VGroup(*(
            Dot(axes.c2p(k, probs[k]), radius=0.08,
                color=_COL["PRIME"], fill_opacity=0.95)
            for k in peaks))
        measured_lab = Text("measured bins", font_size=24,
                            color=_COL["PRIME"])
        measured_lab.next_to(predicted_lab, 0.35 * DOWN)
        self.play(LaggedStart(*[FadeIn(d, scale=1.5) for d in measured],
                              lag_ratio=0.2), Write(measured_lab),
                  run_time=5.0)

        readout = _fit(Text(claims.display("qpe_15"), font_size=26,
                            color=_COL["PRIME"], weight=BOLD))
        bridge = _fit(Text(claims.display("hshor_bridge_min"), font_size=24,
                           color=_COL["TEXT"]))
        readouts = VGroup(readout, bridge).arrange(0.6 * RIGHT) \
            .move_to(0.3 * UP)
        self.play(Write(readouts), run_time=3.0)

        self.play(FadeIn(_takeaway(
            "points to: quantum readout and classical orders agree, "
            "pair by pair", claims.grade("hshor_bridge_min"))),
            run_time=2.0)
        self.wait(1.5)


# --------------------------------------------------------------------------
# act8_fermat_grid — order-grid cells: primes clean, composites leak (35 s).
# --------------------------------------------------------------------------

class Act8FermatGrid(Scene):
    def construct(self):
        self.play(FadeIn(_header(
            "The order grid: primes stay clean, composites leak",
            "hshor_verdict")), run_time=2.0)

        o1 = claims.raw("hshor_o1")
        windows = sorted(o1, key=int)
        cells = VGroup()
        for i, k in enumerate(windows):
            v = o1[k]
            if k == "561":
                col_key = "HYPOTHESIS"
            elif v == 0.0:
                col_key = "PRIME"
            else:
                col_key = "COMPOSITE"
            col = _COL[col_key]
            text = Text(k + " → " + _fmt(v, 1), font_size=24, color=col)
            box = RoundedRectangle(corner_radius=0.06, width=2.0,
                                   height=0.7, stroke_color=col,
                                   stroke_width=2.0, fill_color=col,
                                   fill_opacity=0.12)
            box.move_to(text)
            cell = VGroup(box, text)
            row = i // 5
            cell.move_to(((i % 5) - 2) * 2.5 * RIGHT
                         + (1.2 - row * 0.95) * UP)
            cells.add(cell)
        self.play(LaggedStart(*[FadeIn(c, scale=0.9) for c in cells],
                              lag_ratio=0.08), run_time=10.0)

        callout = VGroup(
            _fit(Text(claims.display("hshor_561_order"), font_size=24,
                      color=_COL["HYPOTHESIS"])),
            _fit(Text(claims.display("korselt_561"), font_size=24,
                      color=_COL["HYPOTHESIS"])),
        ).arrange(0.9 * RIGHT).move_to(2.0 * DOWN)
        gloss_k = _gloss(claims.gloss("hshor_561_order")) \
            .next_to(callout, 0.35 * DOWN)
        self.play(Write(callout), FadeIn(gloss_k), run_time=5.0)

        self.play(FadeOut(callout), FadeOut(gloss_k), run_time=1.0)
        readouts = VGroup(*(
            _fit(Text(claims.display(cid), font_size=24, color=_COL["TEXT"]))
            for cid in ("hshor_crt_dev", "hshor_trace_dev",
                        "hshor_bridge_min", "hshor_shuffle_p")
        )).arrange(0.5 * RIGHT).move_to(2.5 * DOWN)
        self.play(FadeIn(readouts), run_time=4.0)

        line = "shows: {}; every prime unfactored".format(
            claims.display("hshor_shor"))
        self.play(FadeIn(_takeaway(line, claims.grade("hshor_verdict"))),
                  run_time=3.0)
        self.wait(9.0)


# --------------------------------------------------------------------------
# act9_failure_board — refuted/void/degraded, identical chip dignity (30 s).
# --------------------------------------------------------------------------

class Act9FailureBoard(Scene):
    def construct(self):
        self.play(FadeIn(_header("The failure board — same rules, same "
                                 "dignity")), run_time=2.0)

        specs = [
            ("V2" + " — refuted",
             ["the refutation produced", "the Ramanujan fingerprint"],
             claims.grade("ram_gated"), "GRADE_B"),
            ("V1" + " — leakage sieve",
             [claims.display("chi2_v1"), claims.display("leakage_r0")],
             claims.grade("leakage_r0"), "GRADE_C"),
            ("V3" + " — degenerate",
             [claims.display("v3_rmean"), "mean order barely moves"],
             claims.grade("v3_rmean"), "GRADE_C"),
            ("GUE constant",
             [claims.display("gue_correction")],
             claims.grade("gue_correction"), "GRADE_C"),
            ("H-STAR-5",
             [claims.display("hstar5_score"), claims.display("hstar5_md5")],
             None, "HYPOTHESIS"),
            ("discipline",
             ["every outcome registered before measurement",
              "no silent upgrades"],
             None, "MUTED"),
        ]
        cards = VGroup()
        for i, (head, body_lines, grade, col_key) in enumerate(specs):
            col = _COL[col_key]
            body = VGroup(Text(head, font_size=24, color=col, weight=BOLD),
                          *[_fit(Text(ln, font_size=20,
                                      color=_COL["TEXT"]))
                            for ln in body_lines]).arrange(0.15 * DOWN)
            box = RoundedRectangle(corner_radius=0.06, width=5.5,
                                   height=1.5, stroke_color=col,
                                   stroke_width=2.0)
            box.move_to(body)
            body.align_to(box, LEFT).shift(0.25 * RIGHT)
            card = VGroup(box, body)
            if grade is not None:
                chip = _chip(grade, _grade_color(grade))
                chip.move_to(card.get_corner(UR)
                             + 0.35 * LEFT + 0.3 * DOWN)
                card.add(chip)
            card.move_to(((i % 2) * 6.0 - 3.0) * RIGHT
                         + (1.4 - (i // 2) * 1.6) * UP)
            cards.add(card)
        self.play(LaggedStart(*[FadeIn(c, scale=0.9) for c in cards],
                              lag_ratio=0.1), run_time=10.0)

        arrow_lab = Text("see the fingerprint above", font_size=24,
                         color=_COL["GRADE_B"])
        arrow_lab.move_to(2.5 * UP)
        arrow = Arrow(cards[0].get_top() + 0.15 * UP,
                      arrow_lab.get_bottom() + 0.2 * DOWN,
                      color=_COL["GRADE_B"], stroke_width=3.0)
        self.play(Create(arrow), Write(arrow_lab), run_time=3.0)

        self.play(FadeOut(arrow), FadeOut(arrow_lab), run_time=1.0)
        self.play(FadeIn(_takeaway(
            "registered failures are results too — none were hidden")),
            run_time=3.0)
        self.wait(11.0)


# --------------------------------------------------------------------------
# act10_verdict_ladder — grades A+ → C, H-STAR-5 grey, end card (35 s).
# --------------------------------------------------------------------------

class Act10VerdictLadder(Scene):
    def construct(self):
        self.play(FadeIn(_header("What we know, and how we know it")),
                  run_time=2.0)
        gloss = _gloss("A = measured, B = points to, C = speculation") \
            .move_to(2.5 * UP).shift(0.1 * UP)
        self.play(Write(gloss), run_time=2.0)

        rows = [
            (claims.grade("bias_points"), "Im bias as canonical metric"),
            (claims.grade("vqd_e0"), "VQE + VQD on QPU"),
            (claims.grade("alpha_1e6"),
             "α anomaly · QUQUINT · κ* · Kingston"),
            (claims.grade("ram_gated"), "Ramanujan fingerprint"),
            (claims.grade("hshor_verdict"), "Shor oracle bridge"),
            (claims.grade("leakage_r0"),
             "leakage sieve · degenerate model · GUE constant"),
        ]
        ladder = VGroup()
        for i, (grade, label) in enumerate(rows):
            chip = _chip(grade, _grade_color(grade))
            chip.move_to(4.5 * LEFT + (2.0 - i * 0.6) * UP)
            text = _fit(Text(label, font_size=26, color=_COL["TEXT"]))
            text.next_to(chip, 0.5 * RIGHT)
            ladder.add(VGroup(chip, text))
        self.play(LaggedStart(*[FadeIn(row, shift=0.3 * RIGHT)
                                for row in ladder], lag_ratio=0.12),
                  run_time=12.0)

        # H-STAR-5 stays grey: registered, never measured.
        hstar = VGroup(
            Text("H-STAR-5", font_size=24, color=_COL["HYPOTHESIS"],
                 weight=BOLD),
            _fit(Text(claims.display("hstar5_score"), font_size=20,
                      color=_COL["HYPOTHESIS"])),
            _fit(Text(claims.display("hstar5_md5"), font_size=20,
                      color=_COL["HYPOTHESIS"]), 4.5),
        ).arrange(0.15 * DOWN)
        box = RoundedRectangle(corner_radius=0.06, width=5.0, height=1.25,
                               stroke_color=_COL["HYPOTHESIS"],
                               stroke_width=2.0)
        box.move_to(hstar)
        hstar_card = VGroup(box, hstar)
        hstar_card.move_to(4.5 * RIGHT + 2.0 * DOWN)
        self.play(FadeIn(hstar_card), run_time=4.0)

        end = VGroup(
            VGroup(Text(claims.display("test_count"), font_size=26,
                        color=_COL["GRADE_A"], weight=BOLD),
                   Text("CC-BY", font_size=24, color=_COL["MUTED"]),
                   ).arrange(0.6 * RIGHT),
            VGroup(Text("github.com/bartman081523/riemann-nuclear-synthesis",
                        font_size=24, color=_COL["MUTED"]),
                   Text("results, docs, preregs committed",
                        font_size=24, color=_COL["MUTED"]),
                   ).arrange(0.15 * DOWN),
        ).arrange(0.25 * DOWN).move_to(3.2 * DOWN + 1.5 * LEFT)
        self.play(Write(end), run_time=6.0)
        self.wait(9.0)


# --------------------------------------------------------------------------
# CLI driver (publish-stop gate BEFORE any production).
# --------------------------------------------------------------------------

SLUG_TO_CLASS = {
    "act1_title": Act1Title,
    "act2_pillar1": Act2Pillar1,
    "act3_anomaly": Act3Anomaly,
    "act4_qpu_timeline": Act4QpuTimeline,
    "act5_kappa": Act5Kappa,
    "act6_ramanujan": Act6Ramanujan,
    "act7_qpe_peaks": Act7QpePeaks,
    "act8_fermat_grid": Act8FermatGrid,
    "act9_failure_board": Act9FailureBoard,
    "act10_verdict_ladder": Act10VerdictLadder,
}

_DRAFT = ("-ql",)
_FINAL = ("-qh", "--fps", "30")


def _render_slug(slug: str, quality: tuple) -> Path:
    media = PRESENTATION_DIR / "media"
    quality_dir = "480p15" if quality == _DRAFT else "1080p30"
    subprocess.run(
        [sys.executable, "-m", "manim", "render", "-o", slug, *quality,
         "--media_dir", str(media), str(Path(__file__)),
         SLUG_TO_CLASS[slug].__name__],
        cwd=REPO_ROOT, check=True)
    produced = [p for p in (media / "videos").rglob(f"{slug}.mp4")
                if quality_dir in p.parts]
    if not produced:
        raise FileNotFoundError(f"manim produced no {slug}.mp4")
    dest = media / f"{slug}.mp4"
    shutil.copyfile(max(produced), dest)
    return dest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Render the presentation scenes (gate runs first).")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--draft", action="store_true",
                      help="small preview render")
    mode.add_argument("--final", action="store_true",
                      help="full production render")
    parser.add_argument("--only", choices=tuple(claims.SCENES),
                        help="render a single scene")
    parser.add_argument("--list", action="store_true",
                        help="list scene slugs and exit")
    args = parser.parse_args(argv)
    if args.list:
        for slug in claims.SCENES:
            print(slug)
        return 0

    claims.raise_if_gate_fails(full=True)  # publish-stop before production
    quality = _DRAFT if args.draft else _FINAL
    slugs = [args.only] if args.only else list(claims.SCENES)
    for slug in slugs:
        dest = _render_slug(slug, quality)
        print(f"{slug} -> {dest.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except claims.FidelityGateError as exc:
        print(exc, file=sys.stderr)
        sys.exit(2)