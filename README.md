# Browser Python Course for Technical Professionals

A self-paced Python course that runs entirely in the browser. It takes adults with a technical or
business background, strong spreadsheet skills and **no programming experience** from their first
variable to cleaning, aggregating and plotting real-looking plant and sales data with pandas.
Python runs locally in the browser via WebAssembly (Pyodide), so learners install nothing.

Status (15 Oct 2026): specification complete, ready for the first proof of concept (PoC).
See `docs/05_roadmap_and_poc.md` for what the PoC must prove and how to start it.

## Document map

Read the documents in order the first time; afterwards each one stands alone.

| Document | Question it answers | Owns |
| --- | --- | --- |
| `docs/01_learning_goals.md` | **What** is taught? | Goal groups G0–G11, cross-cutting skills X1–X8, misconception register M1–M16, spreadsheet bridges |
| `docs/02_teaching_guideline.md` | **How** is it taught? | Principles P1–P10, unit pattern, exercise ladder, feedback rules, Unit Definition of Done |
| `docs/03_course_plan.md` | **Which units, in which order, how long?** | Requirements R1–R16, unit plan U0–U16, time budget, dataset use per unit, final task |
| `docs/04_platform_spec.md` | **On what** does it run? | Learner experience components, architecture, tooling, repository layout, authoring rules, non-functional requirements |
| `docs/05_roadmap_and_poc.md` | **In what order is it built?** | Phases and gates, PoC definition, decision log, open questions |
| `data/README.md` | What is in the datasets? | Data card: files, columns, built-in patterns, deliberate mess |

ID conventions used across all documents: `G` goal group, `X` cross-cutting skill, `M` misconception,
`P` teaching principle, `R` requirement, `U` unit, `G-A/G-B/G-C` roadmap gates.

## Repository layout

```text
README.md                this file
pyproject.toml, uv.lock  Python dependencies, managed with uv
docs/                    the specification set (see map above)
data/                    generated datasets and data card (CC0, artificial)
tools/generate_datasets.py   seeded generator; `python tools/generate_datasets.py` rewrites data/
site/                    Quarto project with the course site (created in the PoC, see roadmap)
archive/first_draft_2026-10-15/   the three original draft documents, kept for reference
```

## Working with the data

## Development setup

All Python work uses a project virtual environment managed with [uv](https://docs.astral.sh/uv/);
never install into the system Python. The repository lives at `github.com/mriedmann/python-course`.

```bash
uv sync                 # creates .venv from uv.lock (pandas, matplotlib, requests, pytest)
uv run pytest           # run the checks (once tests/ exists)
uv add <package>        # add a dependency; commit pyproject.toml and uv.lock
```

The datasets are artificial, reproducible and licensed CC0. To regenerate them after a change to the
generator, run the script from the repository root; it writes to `data/` and needs only the Python
standard library:

```bash
uv run python tools/generate_datasets.py
```

Keep the deliberate mess (inconsistent spellings, missing values, duplicates, a Windows-1252 file).
The cleaning exercises depend on it; the data card lists every item.

## Next step

Start the PoC described in `docs/05_roadmap_and_poc.md`: a Quarto + quarto-live + Pyodide site with
one complete unit (U7 Functions) and a pandas smoke test, measured against gate G-A.
