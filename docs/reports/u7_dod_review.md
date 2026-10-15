# U7 "Functions: a reusable formula" – Definition of Done self-review

15 Oct 2026 · Task T3 · Page: `site/units/07-functions/index.qmd`. Checklist from
`docs/02_teaching_guideline.md`, "Unit Definition of Done". Items marked *(CI)* have no lint yet
(phase 2); they were checked by hand.

## Planned time and check spacing

| Step | Min | Ends at | Check |
| --- | --- | --- | --- |
| Warm-up | 3 | 3 | quiz `#u7-warmup` (4 questions) |
| Why | 2 | 5 | none |
| Worked example | 8 | 13 | exercise `retype` (light check) |
| Predict and run | 4 | 17 | `.predict #u7-predict` |
| Parsons | 5 | 22 | `.parsons #u7-parsons` |
| Modify | 9 | 31 | exercises `fix_order` (~26) and `extra_discount` |
| Make | 11 | 42 | exercise `discount_classes` |
| Exit | 3 | 45 | quiz `#u7-exit` |

Sum 45 min = `duration_min`. Largest gap between checks: 10 min (warm-up → retype).

## Content

- [x] Front matter names unit, duration, goals, skill (X4), misconceptions, pattern, retrieves *(CI)* – front matter lines 2–10.
- [x] Opens with a work problem (P6) – "Why": quote values computed again and again; `why-sheet.svg` shows the copied `=B2*C2` column.
- [x] One new concept; all other syntax taught earlier (P1) – see construct table below.
- [x] Worked example has named subgoals and a step-through animation (P2, P5) – four numbered subgoals, `.anim #u7-anim` with 3 frames (`anim/frame1–3.svg`, name-tag model) and a `.reveal` block, then the `retype` cell.
- [x] All eight steps present, in order *(CI)* – H2s `#warmup .step` … `#exit .step`.
- [x] Warm-up has 3–5 tagged questions from ≥ 2 earlier units *(CI)* – 4 questions tagged U3 G2, U5 G4, U6 G4, U6 G4.
- [x] A check at least every 15 min *(CI)* – table above, max gap 10 min.
- [x] One exercise starts from a real error (P5) – `fix_order`: call before `def` raises `NameError` (verified in Pyodide by `tools/smoke_unit.py --raises`).
- [x] Exit check tests the named misconception (P9) – `#u7-exit`, tag M9: `print(value)` after an uncalled `def` → `NameError`, nothing printed. M8 is made visible in Predict (`print` vs `return`, `None`).
- [x] Anchor dataset, no toy data (P6) – `quotes` (first 20 rows of the quote book) and `products` from hidden `setup.py`; Predict uses quote line Q2023-00004 inline.
- [x] Original text, code and data (R15) – written new for this task; SVGs drawn by hand.

## Checks and build

- [x] Every exercise has a checkable result; checks are asserts with learner-facing messages – `checks.py`, messages name the next subgoal (e.g. "Hand the result back with return, not print").
- [x] Three hints and a solution per exercise; solution passes its checks *(CI)* – 4 exercises × 3 `.hint` + 1 `.solution`; `uv run pytest -q` and `tools/smoke_unit.py` pass; page solutions equal `solution.py` (pytest).
- [ ] Make notebook runs clean *(CI)* – not applicable in the PoC (no JupyterLite, `make.ipynb` out of scope); Make is a page exercise.
- [x] Planned duration within limits and course plan *(CI)* – 45 min, full pattern, matches U7 row.
- [~] Accessibility (keyboard, contrast, no autoplay) – images have alt text, SVGs have `<title>`/`<desc>`, dark text on white, white on #0b5394/#b45f06 (≥ 4.5:1), nothing autoplays. Keyboard behaviour of quiz/predict/parsons/anim depends on the T2 components; not audited here.

## Constructs used and where they are taught

| Construct | Taught in |
| --- | --- |
| `print`, comments | U0 |
| assignment, `int`/`float` numbers, `* / -`, parentheses, `+=` | U1 |
| strings, f-string with `:.2f` | U2 |
| `if / elif / else`, `<`, `>`, `>=`, `==` | U3 |
| `for item in items` loop, counter pattern | U4 |
| list indexing `quotes[0]`, negative index | U5 |
| dict literal, key access, `.get`, update `counts[key] += 1`, list of dicts, dict by ID (`products[id]["product_name"]`) | U6 |
| `def`, parameters/arguments, call order, `return`, `None`, docstring (triple-quoted string), default values, keyword arguments, local scope, `raise ValueError`, `*args` (recognise) | U7 (new) |

Not used: comprehensions, files, `try/except`, pandas, other format specs.

## Open points

- quarto-live 0.2.0 shows an error as its message only (`name 'product_name' is not defined`),
  without the type name or traceback. The spec wants the full traceback with a plain-language
  explanation; this needs a component (orchestrator decision). The page text says "read the error
  message" so it holds either way.
- Quiz, predict, Parsons and anim render as plain divs until T2's components are merged.
