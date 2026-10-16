# G-A measurements (raw)

Date: 2026-10-15. Target: https://mriedmann.github.io/python-course/ (deployed from `main` a5fb3e6, service-worker build `f8c7af51f490`).
Tools: branch `poc/t8-measure` (adds `--base-url` / `--browser` to the smoke tools and `tools/measure_load.py`).

## Environment

- Machine: WSL2 (Linux 6.18.54.1-microsoft-standard-WSL2 x86_64), Intel i7-12800H, 20 logical CPUs, 15.8 GB RAM.
- Chrome 153.0.8010.36 (headless, Playwright `channel="chrome"`). Firefox 157.0 (Playwright build, `uv run playwright install firefox`, no sudo).
- Network: the machine's real uplink to GitHub Pages/jsDelivr, plus CDP throttling where stated.

## Method

- **Load time** (`tools/measure_load.py`): each run uses a fresh browser context (empty HTTP cache), `service_workers="block"`,
  CDP `Network.emulateNetworkConditions` 50 Mbit/s down (6.25 MB/s), 10 Mbit/s up, 20 ms latency. Timer starts before `page.goto`
  and stops when the selector `.exercise-editor-btn-run-code:not(.disabled)` is *attached* in the DOM (quarto-live enables the run
  button once Pyodide has loaded; on U7 the warm-up quiz hides the cells, so visibility is not required). For `smoke/pandas.html`
  the second stop is the `SMOKE pandas rows=1073 ...` line appearing in `document.body.innerText`.
- **Throttle reaches the Pyodide worker** (sanity check): the same pandas page at 5 Mbit/s took 51.8 s for 27.5 MB (>= 44 s expected), so
  the Web Worker's downloads are throttled, not only the main page.
- **Transferred bytes**: sum of Playwright `request.sizes()` (`responseBodySize` = encoded body + `responseHeadersSize`) over all
  finished requests of the context, which includes Web Worker requests (Pyodide, wheels); split by host.
- **Site payload**: sum of the bytes of the 48 files listed in the deployed `sw-manifest.json`, each fetched from the deployed site.
  Pyodide core and wheels are not on github.io (see below).
- **Offline cache**: `smoke_offline.py` against the deployed site: sum of `blob().size` of all Cache Storage responses after the
  service worker is active.

## Raw output

### Load time

`cd tools && uv run python measure_load.py`

```text
Chrome 153.0.8010.36
units/07-functions/ throttled 50 Mbit/s run 1: ready=11.5s transferred=27.5 MB {'cdn.jsdelivr.net': 26.82, 'mriedmann.github.io': 0.7, 'fonts.gstatic.com': 0.03, 'fonts.googleapis.com': 0.0}
units/07-functions/ throttled 50 Mbit/s run 2: ready=11.1s transferred=27.5 MB {'cdn.jsdelivr.net': 26.82, 'mriedmann.github.io': 0.7, 'fonts.gstatic.com': 0.03, 'fonts.googleapis.com': 0.0}
units/07-functions/ throttled 50 Mbit/s run 3: ready=11.1s transferred=27.5 MB {'cdn.jsdelivr.net': 26.82, 'mriedmann.github.io': 0.7, 'fonts.gstatic.com': 0.03, 'fonts.googleapis.com': 0.0}
units/07-functions/ throttled 50 Mbit/s median ready: 11.1 s
units/07-functions/ unthrottled run 1: ready=8.6s transferred=27.5 MB {'cdn.jsdelivr.net': 26.82, 'mriedmann.github.io': 0.69, 'fonts.gstatic.com': 0.03, 'fonts.googleapis.com': 0.0}
units/07-functions/ unthrottled median ready: 8.6 s
smoke/pandas.html throttled 50 Mbit/s run 1: ready=13.1s summary=13.1s transferred=27.5 MB {'cdn.jsdelivr.net': 26.82, 'mriedmann.github.io': 0.68, 'fonts.gstatic.com': 0.03, 'fonts.googleapis.com': 0.0}
smoke/pandas.html throttled 50 Mbit/s run 2: ready=12.5s summary=12.5s transferred=27.5 MB {'cdn.jsdelivr.net': 26.82, 'mriedmann.github.io': 0.68, 'fonts.gstatic.com': 0.03, 'fonts.googleapis.com': 0.0}
smoke/pandas.html throttled 50 Mbit/s run 3: ready=12.5s summary=12.5s transferred=27.5 MB {'cdn.jsdelivr.net': 26.82, 'mriedmann.github.io': 0.68, 'fonts.gstatic.com': 0.03, 'fonts.googleapis.com': 0.0}
smoke/pandas.html throttled 50 Mbit/s median ready: 12.5 s
smoke/pandas.html throttled 50 Mbit/s median summary: 12.5 s
smoke/pandas.html unthrottled run 1: ready=11.0s summary=11.0s transferred=27.5 MB {'cdn.jsdelivr.net': 26.82, 'mriedmann.github.io': 0.67, 'fonts.gstatic.com': 0.03, 'fonts.googleapis.com': 0.0}
smoke/pandas.html unthrottled median ready: 11.0 s
smoke/pandas.html unthrottled median summary: 11.0 s
exit 0
```

### Payload (deployed site)

```text
build f8c7af51f490 files 48 pyodide_packages ['pandas', 'matplotlib', 'requests', 'micropip', 'pyodide-http', 'ipython']
sum of manifest files fetched from deployed site: 3124544 bytes = 3.12 MB
```

Local `du -sb site/_site` (stale local build, for reference only): 3129463 bytes.

### smoke_unit, U7 (Chrome)

`uv run python tools/smoke_unit.py units/07-functions/ --raises "fix_order:is not defined" --predict 'u7-predict:18701.1\nNone' --base-url https://mriedmann.github.io/python-course/`

```text
first Python cell ready after 8.6 s; warm-up passed, cells visible
retype: check with page solution: pass: 'Correct. Well done!'
fix_order: starting code raises is not defined: yes
fix_order: check with page solution: pass: 'Correct. Well done!'
extra_discount: check with page solution: pass: 'Correct. Well done!'
discount_classes: check with page solution: pass: 'Correct. Well done!'
exit quiz u7-exit: Score: 1/1
anim u7-anim: 3 frames, code revealed
predict u7-predict: correct prediction passes
parsons u7-parsons: keyboard solve passes
events: passed=true for 5 components
reload: all component states restored
predict u7-predict: wrong prediction fails (fresh context)
OK
exit 0
```

### smoke_components (Chrome)

`uv run python tools/smoke_components.py --base-url https://mriedmann.github.io/python-course/`

```text
quiz: cells hidden before, score 2/3, cells visible after
predict: Run disabled before lock, comparison shown after run (fail as expected)
parsons: keyboard-only solve passes, swapped lines fail with a hint
anim: reveal disabled until the last frame, code shown after
events: [{'id': 'demo-warmup', 'kind': 'quiz', 'passed': False}, {'id': 'demo-predict', 'kind': 'predict', 'passed': False}, {'id': 'demo-parsons', 'kind': 'parsons', 'passed': True}, {'id': 'demo-parsons', 'kind': 'parsons', 'passed': False}, {'id': 'demo-parsons', 'kind': 'parsons', 'passed': True}, {'id': 'demo-anim', 'kind': 'anim', 'passed': True}]
reload: quiz, predict, parsons and anim states restored
OK
exit 0
```

### smoke_pages (Chrome; CORS from the github.io origin)

`uv run python tools/smoke_pages.py --base-url https://mriedmann.github.io/python-course/`

```text
SMOKE pandas rows=1073 customers=36 cp1252_ok=True merge_rows=1073
smoke/pandas.html: ok after 8.4 s
  SMOKE web frankfurter status=200 ok=True
  SMOKE web open-meteo status=200 ok=True
smoke/web.html: ok after 7.4 s
OK
exit 0
```

### smoke_offline (Chrome)

`uv run python tools/smoke_offline.py --base-url https://mriedmann.github.io/python-course/`

```text
online: first cell ready after 7.5 s
service worker active 0.0 s after ready; caches ['course-f8c7af51f490']
offline payload: 85 responses, 37.4 MB
offline: first cell ready after reload
offline: check with solution: pass: 'Correct. Well done!'
offline: Stop recovered, Python usable again
OK
exit 0
```

### smoke_browser --mechanics on units/00-demo/ (Chrome; hint ladder, solution reveal, Stop)

`uv run python tools/smoke_browser.py units/00-demo/ --mechanics --base-url https://mriedmann.github.io/python-course/`

```text
first Python cell ready after 7.0 s
check with solution: pass: 'Correct. Well done!'
fail attempt 1: fail: 'That is the gross value. Subtract the discount, which is given in percent.'; solution button: False
fail attempt 2: fail: 'That is the gross value. Subtract the discount, which is given in percent.'; solution button: True
solution revealed after 2 failed checks
hint 1: visible hints [True, False, False]; solution button: False
hint 2: visible hints [False, True, False]; solution button: False
hint 3: visible hints [False, False, True]; solution button: True
solution revealed after hint 3
matplotlib figure rendered (CANVAS)
Stop: loop terminated, Python ready again after 6.7 s
OK
exit 0
```

### Firefox 157

`uv run python tools/smoke_browser.py units/00-demo/ --mechanics --browser firefox --base-url https://mriedmann.github.io/python-course/`

```text
first Python cell ready after 8.5 s
check with solution: pass: 'Correct. Well done!'
fail attempt 1: fail: 'That is the gross value. Subtract the discount, which is given in percent.'; solution button: False
fail attempt 2: fail: 'That is the gross value. Subtract the discount, which is given in percent.'; solution button: True
solution revealed after 2 failed checks
hint 1: visible hints [True, False, False]; solution button: False
hint 2: visible hints [False, True, False]; solution button: False
hint 3: visible hints [False, False, True]; solution button: True
solution revealed after hint 3
matplotlib figure rendered (CANVAS)
Stop: loop terminated, Python ready again after 7.4 s
OK
```

`uv run python tools/smoke_unit.py units/07-functions/ --raises "fix_order:is not defined" --predict 'u7-predict:18701.1\nNone' --browser firefox --base-url https://mriedmann.github.io/python-course/`

```text
first Python cell ready after 10.4 s; warm-up passed, cells visible
retype: check with page solution: pass: 'Correct. Well done!'
fix_order: starting code raises is not defined: yes
fix_order: check with page solution: pass: 'Correct. Well done!'
extra_discount: check with page solution: pass: 'Correct. Well done!'
discount_classes: check with page solution: pass: 'Correct. Well done!'
exit quiz u7-exit: Score: 1/1
anim u7-anim: 3 frames, code revealed
predict u7-predict: correct prediction passes
parsons u7-parsons: keyboard solve passes
events: passed=true for 5 components
reload: all component states restored
predict u7-predict: wrong prediction fails (fresh context)
OK
```

`uv run python tools/smoke_components.py --browser firefox --base-url https://mriedmann.github.io/python-course/` (last lines)

```text
events: [{'id': 'demo-warmup', 'kind': 'quiz', 'passed': False}, {'id': 'demo-predict', 'kind': 'predict', 'passed': False}, {'id': 'demo-parsons', 'kind': 'parsons', 'passed': True}, {'id': 'demo-par
reload: quiz, predict, parsons and anim states restored
OK
```

## Criterion table

| G-A criterion | Measured | Result |
| --- | --- | --- |
| Exercise with hidden check, hint ladder, solution reveal in Chrome and Firefox | Chrome 153 and Firefox 157: check passes with solution, fail message shown, solution offered after 2nd failed check and after hint 3, one hint at a time | pass |
| Quiz, predict, Parsons run in the page, report pass/fail, survive reload | smoke_components + smoke_unit on deployed site, Chrome and Firefox: events emitted, states restored after reload | pass |
| U7 passes Unit Definition of Done | not script-measurable (reviewer check); U7 learner walkthrough passes (5 components, 4 exercises) | not measured |
| pandas reads both CSVs incl. Windows-1252, matplotlib chart renders | `SMOKE pandas rows=1073 customers=36 cp1252_ok=True merge_rows=1073`; figure present | pass |
| First Python cell ready <= 15 s at 50 Mbit/s, deployed | median 11.1 s (U7; runs 11.5/11.1/11.1), median 12.5 s (pandas; runs 13.1/12.5/12.5); pandas summary line median 12.5 s | pass (<= 15 s) |
| Total site payload < 300 MB | github.io files 3.12 MB (48 files); cold-load transfer 27.5 MB (26.82 MB from cdn.jsdelivr.net); offline cache 37.4 MB (85 responses) | pass |
| Pyodide/wheels self-hosted or CDN documented as known deviation | Pyodide + wheels come from cdn.jsdelivr.net (26.82 MB of 27.5 MB); not self-hosted | documented known deviation |
| Works offline after first visit | offline reload: Python ready, check passes, Stop recovers | pass |
| Stop terminates `while True: pass` | Chrome: loop terminated, Python ready again 6.7 s after Stop; Firefox: 7.4 s | pass |
| APIs answer `requests.get` from the deployed page (CORS) | Frankfurter status=200 ok=True; Open-Meteo status=200 ok=True | pass |
| G-A report written, decision logged | not script-measurable | not measured |

## Notes

- Unthrottled single runs: U7 ready 8.6 s, pandas ready/summary 11.0 s (same 27.5 MB), i.e. the throttle adds about 2.5 s / 1.5 s; the rest is Pyodide/pandas startup and package unpacking.
- Cold-load runs are single-machine, single-network samples; the three throttled runs agree within 0.6 s.
- `uv run pytest -q`: 9 passed.

## Addendum: re-measure after self-hosting (phase 2, 15 Oct 2026)

Deployed from `main` after PR #4 (Pyodide 0.28.1 self-hosted in `site/pyodide/`, no Google Fonts).
Same method and commands as above (`measure_load.py --runs 3`, `smoke_thirdparty.py`, `smoke_offline.py`,
all with `--base-url https://mriedmann.github.io/python-course/`).

| Measure | CDN (G-A) | Self-hosted |
| --- | --- | --- |
| U7 first cell ready, 50 Mbit/s, median of 3 | 11.1 s | 11.2 s (13.0 / 11.2 / 11.1) |
| pandas page summary, 50 Mbit/s, median of 3 | 12.5 s | 12.5 s (12.7 / 12.5 / 12.5) |
| Cold transfer per page | 27.5 MB, 26.8 MB from jsDelivr | 27.8 MB, 100 % mriedmann.github.io |
| Third-party requests (U7, pandas, demo) | jsDelivr, Google Fonts | none |
| Offline after first visit | pass | pass |
