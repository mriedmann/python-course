# Gate G-A report: stack confirmed

15 Oct 2026 · Phase 1 (PoC) · Decides gate G-A from `docs/05_roadmap_and_poc.md` on evidence.
Raw numbers, commands and method: `docs/reports/g-a_measurements.md`. U7 review: `docs/reports/u7_dod_review.md`.

**Decision: G-A passed. The quarto-live stack is confirmed; no switch to pyodide-mkdocs-theme.**
One known deviation is accepted: Pyodide and its wheels still load from the jsDelivr CDN and move to
self-hosting at G-B.

## What was built

| Item | Where |
| --- | --- |
| Quarto site, quarto-live v0.2.0, Pyodide 0.28.1, pandas/matplotlib/requests | `site/_quarto.yml`, `site/_extensions/` |
| Exercise mechanics: hidden checks from `checks.py`, hint ladder, solution gate, Stop | `site/components/{check.py,ladder.js,stop.js}` |
| Components as fenced divs + one Lua filter: quiz, predict-lock, Parsons, step-through animation | `site/components/` |
| Unit U7 *Functions: a reusable formula* (45 min, full pattern) | `site/units/07-functions/` |
| pandas and web smoke pages | `site/smoke/` |
| GitHub Actions: test, build, deploy to Pages; service worker for offline use | `.github/workflows/deploy.yml`, `site/sw.js` |
| Tests: solutions vs checks (pytest), six headless-browser suites, load measurement | `tests/`, `tools/smoke_all.sh`, `tools/measure_load.py` |

Deployed at <https://mriedmann.github.io/python-course/> from `main` (a5fb3e6).

## Acceptance criteria

All measurements on the deployed site, Chrome 153 (headless) unless stated; Firefox 157 where stated.

| # | Criterion | Evidence | Result |
| --- | --- | --- | --- |
| 1 | Exercise with hidden check, hint ladder, solution reveal works in Chrome and Firefox | `smoke_browser --mechanics` and `smoke_unit` U7 pass in both browsers: assert message shown on fail, hints one at a time, solution after hint 3 or 2 failed checks | Pass |
| 2 | Quiz, predict-lock, Parsons run in the page, report pass/fail, survive reload | `smoke_components` and the U7 walkthrough pass in both browsers; `pycourse:result` events for all 5 U7 components; states restored after reload | Pass |
| 3 | U7 passes the Unit Definition of Done (reviewer) | Orchestrator review of source and rendered page; two spoilers found and fixed (T7). Exceptions: `make.ipynb` not applicable without JupyterLite; full traceback display is a phase-2 component (below) | Pass, with noted exceptions |
| 4 | pandas reads both CSVs incl. Windows-1252, chart renders | `rows=1073 customers=36 cp1252_ok=True merge_rows=1073`, figure present | Pass |
| 5 | First Python cell ready ≤ 15 s at 50 Mbit/s | Cold, no cache, no service worker, CDP throttle 50/10 Mbit/s, 20 ms: U7 median 11.1 s (11.5/11.1/11.1), pandas page 12.5 s incl. all cells run. Orchestrator re-run: 11.8 s / 12.5 s | Pass |
| 6 | Total payload < 300 MB; Pyodide self-hosted or CDN documented | Site 3.1 MB; cold page load transfers 27.5 MB (26.8 MB from jsDelivr); offline cache 37.4 MB | Pass, **known deviation:** CDN loading |
| 7 | Works offline after the first visit | `smoke_offline` against the deployed site: offline reload, exercise check passes, Stop recovers | Pass (Chrome; Firefox not tested) |
| 8 | Stop terminates `while True: pass` | Python usable again 6.7 s (Chrome) / 7.4 s (Firefox) after Stop | Pass, with limit (below) |
| 9 | Both candidate U13 APIs answer `requests.get` from the deployed page (CORS) | Frankfurter (`api.frankfurter.dev/v1`) and Open-Meteo: status 200 from the github.io origin; orchestrator re-run confirms | Pass |
| 10 | G-A report written, decision recorded | This file; decision log in `docs/05` | Pass |

## Findings that shape phase 2

Must fix at G-B:

1. **Self-host Pyodide.** Set `pyodide: engine-url:` to a same-origin copy of Pyodide 0.28.1, holding only
   the core files plus the wheels the course uses (about 27 MB, well inside the 300 MB budget). The service
   worker's CDN rule then goes away.
2. **Self-host fonts.** The Cosmo theme loads Source Sans from `fonts.googleapis.com`. That is a third-party
   request (privacy rule in `docs/04`) and is not cached for offline use. Bundle the font or use a system stack.
3. **Error explanations.** quarto-live 0.2.0 shows only the error message, without the type or traceback.
   The planned error-explanation component must render the full traceback plus a plain-language line.
4. **Stop loses edits.** Stop reloads the page because quarto-live has no interrupt and Pages cannot send
   cross-origin isolation headers. At minimum, save editor contents to `localStorage` before reloading.
5. **CI gates 1 and 4.** Add the front-matter/structure lint and run `tools/smoke_all.sh` (headless Chrome)
   in GitHub Actions.

Should fix:

6. Predict cell stays editable before the first run; lock its editor until the prediction is locked.
7. Quiz has no per-question explanation after checking; add an optional `.explain` like predict has.
8. Every quarto-live exercise needs at least one hint, otherwise "Show Solution" appears at once; the lint
   should enforce three. Two "Show Solution" buttons can appear after 2 fails plus all hints.
9. The Pyodide package list is duplicated in `site/_quarto.yml` and `site/tools/sw_manifest.py`.
10. Delete the throwaway demo unit `units/00-demo` (its net-value formula applies the discount twice) once
    the component demo moves to a test fixture.
11. Untested: Edge, Safari, offline in Firefox, narrow screens (Parsons layout cramped; mobile is view-only).

Spec updates (done with this report): components are fenced divs, not shortcodes; Parsons is native, not
js-parsons; Frankfurter's endpoint is `api.frankfurter.dev/v1`.

Process note: Quarto renders nothing when the project path contains a dot-directory, so agent worktrees
must live outside `.claude/`.
