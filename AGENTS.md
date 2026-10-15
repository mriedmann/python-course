# AGENTS.md

Working agreement for every coding agent (and human) in this repository. Read it before your first
change. The specification in `docs/` is the source of truth for *what* to build; this file defines
*how* we build it.

## 1. Project in one paragraph

A self-paced, zero-install Python course that runs in the browser (Quarto + quarto-live + Pyodide),
hosted on GitHub Pages from `github.com/mriedmann/python-course`
(<https://mriedmann.github.io/python-course/>). Current phase: **Phase 2 platform**, exit at gate
**G-B** (`docs/05_roadmap_and_poc.md`; G-A passed, see `docs/reports/g-a_report.md`). Read the docs in order the first time:

| Read when you work on… | Document |
| --- | --- |
| anything | `README.md`, this file, `docs/05_roadmap_and_poc.md` (scope + acceptance criteria) |
| site, components, CI, deploy | `docs/04_platform_spec.md` |
| unit content | `docs/02_teaching_guideline.md` (unit pattern, Definition of Done), `docs/03_course_plan.md` (unit row), `docs/01_learning_goals.md` (IDs G/X/M) |
| data | `data/README.md` (data card) |

## 2. Non-negotiable rules

1. **Spec first.** Do not change `docs/01`–`docs/04` or `data/` unless your task says so. If the spec
   is wrong or impossible, stop and report it; the orchestrator updates the spec and the decision log.
2. **Python only via uv.** `uv sync`, `uv run …`, `uv add [--dev] …`. Never `pip install`, never the
   system Python. Commit `pyproject.toml` and `uv.lock` together.
3. **Pinned versions** (change only via an explicit task and a decision-log entry):
   Quarto CLI **1.10.19** · quarto-live **0.2.0** · Pyodide = the version quarto-live 0.2.0 ships
   (recorded in `site/_quarto.yml` once known) · chrome-devtools-mcp **1.11.0**.
4. **Smallest complete change** (the `ponytail` skill, always on): reuse what exists, standard
   library and platform features before dependencies, no speculative abstractions, no framework.
   JS components are vanilla, one file each, **under 200 lines**. Never cut validation,
   error handling, accessibility (keyboard, contrast, no autoplay) or anything the spec asks for.
5. **Original content only (R15).** Write all course text and code new. Use only the artificial
   Fluvia datasets in `data/`; no toy data, nothing copied from other courses.
6. **English** for all content, code, comments and commits.
7. **No secrets, no analytics, no cookies.** Progress lives in `localStorage` only.
8. **Do not stop the deploy pipeline or rewrite git history** on `main`. No force-push.

## 3. Roles and workflow

```text
orchestrator (Opus)  ── writes task brief ──▶  worker agent (Sonnet or Opus)
       ▲                                              │ works on its own branch
       └──── reviews diff + verifies criteria ◀───────┘ reports: done / blocked + evidence
```

- **Orchestrator** owns the plan, the task briefs, branch merges, `docs/05` decision log and the
  G-A report sign-off. It does not hand-wave review: it re-runs the verification commands.
- **Workers** implement exactly one task brief. Model choice:
  - **Sonnet:** well-specified mechanical work (CI workflow, shortcode wiring, smoke pages, scripts,
    measurement runs, lint/test plumbing).
  - **Opus:** work needing judgement (stack spike with unknown APIs, pedagogical unit content against
    the Definition of Done, component design, debugging cross-cutting failures, reviews).

### Task brief format (orchestrator → worker)

```markdown
## Task <ID>: <title>
Branch: poc/<slug>        Model: sonnet|opus        Depends on: <IDs>
Goal: one sentence.
Context: files/sections to read (paths + headings).
Deliverables: exact files to create/change.
Acceptance criteria: checkable bullet list (commands + expected results).
Out of scope: what not to touch.
Report back: summary, files changed, verification output, open issues/deviations.
```

### Worker loop

1. Work on the branch named in the brief, branched from the phase integration branch. Parallel workers
   get a git worktree **next to** the repo (`../python_course-<slug>`), never under `.claude/`:
   Quarto silently renders nothing when the path contains a dot-directory.
2. Read the context listed in the brief. Load the `ponytail` skill; load `quarto-authoring` for any
   `.qmd`/`_quarto.yml` work.
3. Implement the smallest change that meets every acceptance criterion.
4. Run the verification commands (section 5); fix until green. Evidence beats claims.
5. Commit in small logical commits (section 6). Push the branch: `git push -u origin poc/<slug>`.
6. Report back in the brief's format. List deviations from the spec explicitly; never silently
   descope.

### Review and merge (orchestrator)

- Review with the `ponytail-review` skill (correct, safe, tested, lean) plus the task's acceptance
  criteria and, for units, the Unit Definition of Done (`docs/02`).
- Re-run verification locally, then merge the task branch into the phase integration branch
  (`poc/g-a` in phase 1, `p2/g-b` in phase 2) with `git merge --no-ff`.
- Only the **course owner merges into `main`** (via PR from the integration branch). A push to
  `main` deploys to Pages. Agents never merge into `main` themselves.

## 4. Repository layout (target, from `docs/04`)

```text
site/                     Quarto project
  _quarto.yml             site config, pinned quarto-live/Pyodide, package list
  _extensions/            quarto-live (pinned, committed)
  components/             quiz, predict, parsons shortcodes (Lua + JS + CSS, vanilla)
  units/07-functions/     index.qmd, setup.py, checks.py, solution.py, anim/
  smoke/                  pandas smoke page, web (CORS) smoke page
  sw.js                   service worker (offline)
tests/                    pytest: solutions vs checks, front-matter lint
tools/                    dataset generator, measurement scripts
docs/reports/             g-a_report.md
.github/workflows/        deploy.yml
.claude/skills/           vendored skills (ponytail, ponytail-review, quarto-authoring)
```

## 5. Commands

```bash
uv sync                                   # Python env (pandas, matplotlib, requests, pytest, playwright, pyyaml)
uv run pytest -q                          # all CPython checks
quarto render site                        # build to site/_site
quarto preview site --no-browser          # live preview
uv run python -m http.server -d site/_site 8000   # serve the build (service workers need http://, not file://)
uv run python tools/<script>.py           # measurement / helper scripts
bash tools/smoke_all.sh                   # render + all headless-browser smoke suites
```

Browser automation: Python Playwright with the installed Chrome
(`p.chromium.launch(channel="chrome", headless=True)`); no browser download needed. Exact network
throttling (50 Mbit/s) via a CDP session: `Network.emulateNetworkConditions`.

## 6. Git conventions

- Branches: `<phase>/<slug>` (`poc/…`, `p2/…`), one task per branch, merged `--no-ff` into the phase
  integration branch (`p2/g-b`); the course owner merges it into `main` via PR.
- Commit messages: imperative, ≤ 72-char subject, body says *why*. Reference IDs where useful
  (`U7`, `G-A`, `R15`). Agents append the attribution trailer given by their harness.
- Never commit `site/_site/`, `.quarto/`, `.venv/`, downloaded Pyodide tarballs outside the
  intended self-hosting path, or scratch files.

## 7. Tooling available to agents

| Tool | Use |
| --- | --- |
| Skill `ponytail` / `ponytail-review` (`.claude/skills/`, MIT, DietrichGebert/ponytail@84740e3) | Minimal-change coding rules; structured review |
| Skill `quarto-authoring` (`.claude/skills/`, MIT, posit-dev/skills@7cef2d7) | Quarto syntax, shortcodes, extensions, YAML |
| MCP `chrome-devtools` (`.mcp.json`) | Interactive debugging, performance traces, network list, offline emulation |
| Python Playwright + Chrome | Repeatable smoke tests and measurements (scripts in `tools/`) |
| `gh` CLI | PRs, Actions runs, Pages status |

## 8. Definition of Done for any task

- [ ] All acceptance criteria in the brief verified with command output.
- [ ] `uv run pytest -q` green; `quarto render site` succeeds without warnings you introduced.
- [ ] No files outside the brief's deliverables changed (or the deviation is reported).
- [ ] Spec deviations, known limits (`shortcut: <limit>, <when to upgrade>`) and open questions listed in the report.
