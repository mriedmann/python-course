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
`ladder.js` (solution gate) and `stop.js` (a Stop button next to Run while a cell runs; it reloads
the page because quarto-live 0.2.0 cannot interrupt Pyodide). Not shortcodes; nothing to write per unit.

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
