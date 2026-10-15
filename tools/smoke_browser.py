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


class QuietServer(http.server.ThreadingHTTPServer):
    def handle_error(self, request, client_address):  # browsers abort requests: BrokenPipe is noise
        if not isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError)):
            super().handle_error(request, client_address)


def serve() -> str:
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    server = QuietServer(("127.0.0.1", 0), functools.partial(Handler, directory=SITE))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_port}/"


def add_target_args(parser) -> None:
    parser.add_argument("--base-url", help="deployed site root, e.g. https://mriedmann.github.io/python-course/ (skips the local server)")
    parser.add_argument("--browser", choices=["chrome", "firefox"], default="chrome")


def site_url(args) -> str:
    return args.base_url.rstrip("/") + "/" if args.base_url else serve()


def launch(p, args):
    if args.browser == "firefox":
        return p.firefox.launch(headless=True)
    return p.chromium.launch(channel="chrome", headless=True)


def open_page(page, url: str) -> float:
    t0 = time.monotonic()
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector(RUN_READY, state="attached", timeout=TIMEOUT_MS)  # hidden behind a warm-up
    pass_warmup(page)
    return time.monotonic() - t0


def submit_quiz(quiz) -> str:
    """Answer every question correctly (from data-choice / data-answer), submit, return the score text."""
    for q in quiz.locator(".question").all():
        choice = q.get_attribute("data-choice")
        if choice is not None:
            q.locator("input[type=radio]").nth(int(choice)).check()
        else:
            q.locator("input[type=text]").fill(q.get_attribute("data-answer").split("|")[0].strip())
    quiz.get_by_role("button", name="Check answers").click()
    n = quiz.locator(".question").count()
    expect(quiz.locator(".quiz-score")).to_have_text(f"Score: {n}/{n}")
    return f"Score: {n}/{n}"


def pass_warmup(page) -> None:
    """Submit the page's warm-up quiz, if it has one, so that its live cells become visible."""
    warmup = page.locator(".quiz.warmup")
    if warmup.count():
        submit_quiz(warmup)
        expect(page.locator(".exercise-cell .cm-editor").first).to_be_visible(timeout=TIMEOUT_MS)


def run_cell(page, cell, code: str) -> None:
    editor = cell.locator(".cm-content")
    editor.click()
    page.keyboard.press("ControlOrMeta+A")
    page.keyboard.insert_text(code)  # one input event: no auto-indent or bracket closing
    # CodeMirror's inner_text doubles empty lines; compare without them.
    lines = [line for line in editor.inner_text().splitlines() if line.strip()]
    assert lines == [line for line in code.splitlines() if line.strip()], "editor did not take the code"
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
    add_target_args(parser)
    args = parser.parse_args()

    url = site_url(args) + args.path
    with sync_playwright() as p:
        browser = launch(p, args)
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
