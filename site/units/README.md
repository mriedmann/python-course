# Unit conventions

One folder per unit, `site/units/<NN>-<slug>/`. Copy `00-demo/` (throwaway example) to start.

| File | Shipped? | Purpose |
| --- | --- | --- |
| `index.qmd` | yes | Lesson page; front matter `engine: markdown` and `resources: [checks.py, ...]` |
| `checks.py` | yes (Pyodide VFS) | `check_<label>(ns: dict)` per exercise, plain asserts with learner-facing messages |
| `setup.py` | inlined | Hidden setup code (e.g. `quotes`), included into each exercise's setup block |
| `solution.py` | no | Reference solutions, one section per exercise starting with `# exercise: <label>` |

**Exercise label.** `#| exercise: <label>` (a Python identifier) links the editor cell, its setup,
check, hints and solution, `check_<label>` in `checks.py` and the `# exercise: <label>` section in
`solution.py`.

**Checks (single source of truth).** The check block of every exercise is the same one line,
`{{< include ../../components/check.py >}}`. In the browser it imports the unit's `checks.py`
(listed under `resources:`) and calls `check_<label>(globals())` on the learner's namespace. A failed
`assert` shows its message as red quarto-live feedback, a pass shows "Correct. Well done!", any other
exception is reported by type and message. `uv run pytest -q` (`tests/test_checks.py`) runs setup +
each solution section + its check under CPython, and fails if checks and solution sections differ.

**Setup.** Put shared hidden code in `setup.py` and include it in a setup block per exercise
(`#| setup: true`). Before U8 it builds `quotes` from `data/quotes.csv`; the CSV reaches the browser
via `resources: [../../data/quotes.csv]` and lands at `data/quotes.csv` in the working directory,
the same relative path the CPython tests use (they run from the repository root).

**Hints and solution.** Up to three `::: {.hint exercise="<label>"}` divs and one
`::: {.solution exercise="<label>"}` div with a fenced `python` block. quarto-live reveals hints one
at a time ("Show Hint", "Next Hint") and offers "Show Solution" after the last hint.
`components/ladder.js` adds the second route: "Show Solution" after 2 failed checks. Keep the
solution in `index.qmd` identical to the `solution.py` section (the browser smoke test runs the
page's solution, pytest runs `solution.py`).

**Components** (`site/components/`, loaded on every page by `include-after-body` in `_quarto.yml`):
`ladder.js` (solution gate), `drafts.js` (saves editor code to localStorage, restores it on load),
`stop.js` (a Stop button next to Run while a cell runs; it saves drafts, then reloads the page because
quarto-live 0.2.0 cannot interrupt Pyodide) and `errors.js` (when a cell raises:
a plain-language explanation above the traceback of the learner's own code). Not shortcodes;
nothing to write per unit.

**Stepper** (`components/stepper.js` + `stepper.py`): a "Step through" button next to Run on every
editor. It traces the editor's code (after the exercise's hidden setup, which is not stepped and whose
objects stay collapsed) in a fresh namespace, max 500 steps, and shows the line, frames with name tags,
objects by `#n` (shared references) and output. Test: `uv run python tools/smoke_stepper.py`.

**Unit-specific error explanations** (optional). A hidden div replaces the generic explanation when
an error of type `exception` whose message contains `match` (optional) occurs anywhere on the page.
The build fails without `exception`. Use it for the exercise that starts from a real error (P5).

```markdown
::: {.error-explain exception="NameError" match="product_name"}
Python runs a cell from top to bottom. `product_name` only exists after its `def` block has run.
:::
```

Test: `uv run python tools/smoke_errors.py` (fixture page `00-demo/errors.qmd`, one cell per error
type, plus U7's `fix_order`).

````markdown
```{pyodide}
#| exercise: net_value
q = quotes[0]
net_value = ______
```

```{pyodide}
#| exercise: net_value
#| setup: true
{{< include setup.py >}}
```

```{pyodide}
#| exercise: net_value
#| check: true
{{< include ../../components/check.py >}}
```
````

Then three `.hint` divs and one `.solution` div as above. Smoke test a built page with
`uv run python tools/smoke_browser.py units/<NN>-<slug>/ [--mechanics]`.

**Lesson components** (`components/components.lua` + `quiz.js`, `predict.js`, `parsons.js`,
`anim.js`, `components.css`). Fenced divs, each with a unique `#id`; the build fails on malformed
markup. Full example: `00-demo/components.qmd`.

- `::: {.quiz #id .warmup}` (or `.exit`) with `::: {.question tags="U5 G4"}` divs. Multiple choice:
  a task list with exactly one `- [x]`. Short answer: `answer="None"` (alternatives `a|b`, compared
  after stripping, case-sensitive). A `.warmup` quiz hides the page's live cells until submitted.
- `::: {.predict #id}` around one `{pyodide}` block: Run stays disabled until the prediction is
  locked; the first run is compared with the prediction (lines stripped, trailing blank lines dropped). An optional child `::: {.explain}` is hidden until the comparison
  is shown, so it can state the output without spoiling the prediction.
- `::: {.parsons #id}`: one `python` block with the solution (4 spaces per level), optional
  `{.python .distractor}` blocks.
- `::: {.anim #id}`: `::: {.frame title="..."}` divs (picture plus text alternative) and an optional
  `::: {.reveal}` shown by "Show me the code" after the last frame was reached.

State and pass/fail are stored in `localStorage` (`pycourse:v1:<path>:<id>`); each result fires a
`pycourse:result` event (`{id, kind, passed}`). Test: `uv run python tools/smoke_components.py`.

**Unit lint** (`tests/test_unit_lint.py`, runs in CI on every push). For each `index.qmd` with a
`unit:` front-matter key it checks the machine-checkable Definition of Done: required keys; goal,
skill, misconception and retrieved-unit IDs exist in `docs/01`/`docs/03`; duration, pattern,
`retrieves`, goals and misconceptions match the unit's row in `docs/03`; duration limits and
`steps` summing to `duration_min`; `.step` sections in pattern order; a 3-5 question warm-up whose
tags span two retrieved units; a check at least every 15 minutes; per exercise an editor, setup and
check block, exactly 3 hints, 1 solution and a `check_<label>` in `checks.py`; an exit question
tagged with a unit misconception. Run: `uv run pytest -q tests/test_unit_lint.py`.

**Instructor mode** (`components/instructor.js`, CSS in `components.css`, flag set by an
`include-in-header` snippet in `_quarto.yml`). Open any page with `?instructor` (kept for the browser
tab, `?instructor=0` turns it off): hints, solutions, "Show Solution", the anim reveal, predict
`.explain` and quiz "The answer is ..." text are hidden (quizzes keep correct/incorrect), the warm-up
gate is lifted, and a badge offers a "Presenter" toggle (150 % text and code). Hidden, not secret:
quarto-live solutions stay in the page HTML. `solution.py` is never shipped. Test: `tools/smoke_instructor.py`.

**Progress** (`components/progress.js`): step bar from the page's `h2.step` sections plus the navbar
"Progress" panel. Keys (all `pycourse:v1:<path>:`): `<id>` (quiz/predict/parsons/anim, own formats),
`exercise:<label>` `{passed, at}` (a pass is never downgraded), `visited:<step>`, `complete`, `draft:<key>`.
A step is done when all its checks passed (predict: answered; steps without checks: visited).
Export file: `{format: "pycourse-progress", version: 1, exported_at, items: {key: string}}`, all
`pycourse:v1:` keys. Import accepts only that format, only such keys, < 2 MB, after a confirm. Test: `tools/smoke_progress.py`.

## Make notebook (workspace)

Full-pattern units can add `make.ipynb` next to `index.qmd` for the larger Make task. It is not a
Quarto page (`_quarto.yml` renders only `*.qmd`); `site/tools/lite_build.py` copies every
`units/*/make.ipynb` into the JupyterLite workspace at the same path, next to `data/` and `projects/`
(`site/workspace/projects/`, the course `.py` modules).

| Cell | Tag | Content |
| --- | --- | --- |
| markdown | | Brief, and how to check: the toolbar button **Restart & Run All** (*Kernel > Restart Kernel and Run All Cells…*) |
| code | `setup` | Before U8: "Setup, just run it" loading the data by relative path, e.g. `../../data/quotes.csv` |
| code | `exercise:<label>` | Skeleton; `...` placeholders so it runs and the self-check reports what is missing |
| code | `check` | Self-check: plain asserts with the same messages as `check_<label>` in `checks.py` (no imports from hidden files), ending with `print("All checks passed. Well done!")` |

**Solution.** No second notebook: the `# exercise: <label>` section of `solution.py` is the solution.
CI gate 3 (`tests/test_notebooks.py`) puts it into the `exercise:<label>` cell and runs the notebook top
to bottom under CPython in the unit folder; it also checks that the unsolved skeleton fails in the
`check` cell. `tools/smoke_workspace.py` does the same in the browser's Pyodide kernel for U7.
