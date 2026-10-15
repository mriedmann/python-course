"""Browser smoke test for a quarto-live page of the built site (site/_site).

Usage:  uv run python tools/smoke_browser.py units/00-demo/ [--mechanics]

Default: time to first Python cell ready, then the first exercise with hints is run with its own
solution and must pass its hidden check. --mechanics also checks the fail path (assert message),
the hint ladder, the solution gate and the Stop button on `while True: pass`.
Exit code 1 on any failure.
"""

import argparse
import functools
import http.server
import sys
import threading
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

SITE = Path(__file__).resolve().parent.parent / "site" / "_site"
# DOM signals (quarto-live 0.2.0)
RUN_READY = ".exercise-editor-btn-run-code:not(.disabled)"  # Pyodide loaded and no cell busy
BUSY = ".exercise-editor-eval-indicator:not(.d-none)"  # spinner of a running cell
GRADE = ".exercise-grade"  # check feedback; .alert-success = pass, .alert-danger = fail
TIMEOUT_MS = 120_000


def serve() -> str:
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=SITE))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_port}/"


def open_page(page, url: str) -> float:
    t0 = time.monotonic()
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector(RUN_READY, timeout=TIMEOUT_MS)
    return time.monotonic() - t0


def run_cell(page, cell, code: str) -> None:
    editor = cell.locator(".cm-content")
    editor.click()
    page.keyboard.press("ControlOrMeta+A")
    page.keyboard.insert_text(code)  # one input event: no auto-indent or bracket closing
    assert editor.inner_text() == code, f"editor did not take the code: {editor.inner_text()!r}"
    cell.locator(GRADE).evaluate_all("els => els.forEach(e => e.remove())")  # wait for fresh feedback
    cell.locator(RUN_READY).click()


def grade_of(cell):
    grade = cell.locator(GRADE)
    grade.wait_for(timeout=TIMEOUT_MS)
    return ("pass" if "alert-success" in grade.get_attribute("class") else "fail"), grade.inner_text()


def mechanics(page, url: str, cell) -> None:
    label = page.locator(".exercise-solution").first.get_attribute("data-exercise")
    solution = page.locator(f'.exercise-solution[data-exercise="{label}"]')
    header = cell.locator(".exercise-editor-header")

    # Fail path: assert message shown; solution offered only from the 2nd failed check on.
    for attempt in (1, 2):
        run_cell(page, cell, "q = quotes[0]\nnet_value = q['quantity'] * q['unit_price_eur']")
        result, message = grade_of(cell)
        has_button = header.get_by_text("Show Solution").count() > 0
        print(f"fail attempt {attempt}: {result}: {message.strip()!r}; solution button: {has_button}")
        assert result == "fail" and "gross value" in message
        assert has_button == (attempt == 2)
    expect(solution).to_be_hidden()
    header.get_by_text("Show Solution").click()
    expect(solution).to_be_visible()
    print("solution revealed after 2 failed checks")

    # Hint ladder on a fresh page: one hint at a time, solution only after the 3rd.
    open_page(page, url)
    hints = page.locator(f'.exercise-hint[data-exercise="{label}"]')
    expect(solution).to_be_hidden()
    header.get_by_text("Show Hint").click()
    for i in range(hints.count()):
        visible = [hints.nth(j).is_visible() for j in range(hints.count())]
        offered = header.get_by_text("Show Solution").count() > 0
        print(f"hint {i + 1}: visible hints {visible}; solution button: {offered}")
        assert visible == [j == i for j in range(hints.count())]
        assert offered == (i == hints.count() - 1)
        if i < hints.count() - 1:
            header.get_by_text("Next Hint").click()
    header.get_by_text("Show Solution").click()
    expect(solution).to_be_visible()
    print(f"solution revealed after hint {hints.count()}")

    # Autorun matplotlib cell rendered a figure (quarto-live draws it as <img> or <canvas>).
    chart = page.locator(".exercise-cell", has_text="Chart").locator("img, canvas").first
    expect(chart).to_be_visible(timeout=TIMEOUT_MS)
    print(f"matplotlib figure rendered ({chart.evaluate('e => e.tagName')})")

    # Stop: run an endless loop for 2 s, press Stop; Python must be usable again.
    loop = page.locator(".exercise-cell", has_text="while True").first
    loop.locator(RUN_READY).click()
    expect(loop.locator(BUSY)).to_be_visible()
    time.sleep(2)
    expect(loop.locator(BUSY)).to_be_visible()  # still running
    t0 = time.monotonic()
    with page.expect_navigation(wait_until="domcontentloaded"):
        loop.locator(".btn-exercise-stop").click()
    page.wait_for_selector(RUN_READY, timeout=TIMEOUT_MS)
    run_cell(page, cell, "print(len(quotes))")
    expect(cell.locator(".cell-output-stdout")).to_contain_text("20", timeout=TIMEOUT_MS)
    print(f"Stop: loop terminated, Python ready again after {time.monotonic() - t0:.1f} s")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="page path inside site/_site, e.g. units/00-demo/")
    parser.add_argument("--mechanics", action="store_true")
    args = parser.parse_args()

    url = serve() + args.path
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page()
        try:
            print(f"first Python cell ready after {open_page(page, url):.1f} s")
            # First exercise with hints; its solution is the first .exercise-solution on the page.
            cell = page.locator(".exercise-cell:has([aria-label='Show Hint'])").first
            cell = page.locator("#" + cell.get_attribute("id"))  # stable once hint buttons change
            run_cell(page, cell, page.locator(".exercise-solution code").first.text_content())
            result, message = grade_of(cell)
            print(f"check with solution: {result}: {message.strip()!r}")
            if result != "pass":
                return 1
            if args.mechanics:
                mechanics(page, url, cell)
        except Exception as e:  # report and fail the smoke test
            print(f"FAIL: {type(e).__name__}: {e}")
            return 1
        finally:
            browser.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
