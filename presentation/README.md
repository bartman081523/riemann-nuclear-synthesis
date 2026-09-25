# presentation/ — "Prime States on a Quantum Machine"

A manim + pySlides deck of the project's main findings. The medium is a
fidelity instrument: every number shown on screen or on a slide is
recomputed from committed sources at build time — never copied from
memory, never hand-typed.

## Files

| file | role |
|---|---|
| `claims.py` | single source of truth: claim table, live recompute, data gate |
| `render_manim.py` | 10 scenes (`act1_title` … `act10_verdict_ladder`) |
| `build_deck.py` | pySlides deck (13 slides) around the rendered videos |
| `deck.html` | committed deliverable (reveal.js, videos relative) |
| `fidelity_report.md` | committed gate report (one row per claim) |
| `media/` | rendered mp4s — **gitignored**, re-render with the commands below |

## Pipeline

```bash
# 1. draft render (854x480, fast QC loop)
venv/bin/python presentation/render_manim.py --draft            # all scenes
venv/bin/python presentation/render_manim.py --draft --only act5_kappa

# 2. final render (1920x1080, 30 fps)
venv/bin/python presentation/render_manim.py --final

# 3. deck (runs the full gate first; verifies codec of every mp4)
venv/bin/python presentation/build_deck.py

# 4. fidelity tests (never render, never import manim/pyslides)
venv/bin/python -m pytest tests/test_presentation_fidelity.py -q
```

`render_manim.py --only` accepts a single slug; render scenes one at a
time or all at once.

## Fidelity model

- `claims.display(id)` recomputes the value from its source
  (`pt_*_results.json`, a module recompute, or a doc anchor with line
  number) and formats it — scenes and slides contain no literals.
- Before any production render or deck build, `check_gate(full=True)`
  compares recompute against the frozen expected value. Any mismatch
  raises `FidelityGateError` → exit code 2, nothing is written
  (publish-stop).
- Wording ladder: **A** claims say *shows* (measured, recomputed),
  **B** claims say *points to*, **C**/grey hypotheses say *speculates*.
  Registered failures appear with the same typographic dignity as
  successes (identical chip geometry).
- `tests/test_presentation_fidelity.py` enforces the model
  mechanically, including an AST scan that rejects any numeric or
  digit-bearing string literal in the render/deck scripts that is not
  whitelisted in `claims.py`.

## Viewing the deck

`deck.html` loads reveal.js and MathJax from a CDN — an internet
connection is needed to open it. The videos are referenced relatively
(`media/<slug>.mp4`), so keep the directory layout when moving the file.
PDF export is intentionally not provided: playwright is absent and a
PDF export would freeze the videos into empty boxes.