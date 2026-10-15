"""Browser smoke test for EVERY exercise of a built unit page (site/_site).

Usage:  uv run python tools/smoke_unit.py units/07-functions/ [--raises LABEL:TEXT ...]

For each quarto-live exercise on the page: insert the page's own solution, run the check, assert it
passes. With --raises, first run that exercise's starting code and assert the output shows the
error text, e.g. "fix_order:is not defined" (the "starts from a real traceback" exercise, P5;
quarto-live 0.2.0 shows the error message without its type name). Exit code 1 on any failure.
"""

import argparse
import sys

from playwright.sync_api import expect, sync_playwright

from smoke_browser import GRADE, RUN_READY, TIMEOUT_MS, grade_of, open_page, serve

LABEL_JS = """cell => {
  const s = document.querySelector(`script[type="${cell.id}-contents"]`);
  return JSON.parse(window._exercise_ojs_runtime.b64Decode(s.textContent)).attr.exercise || null;
}"""


def run_code(page, cell, code: str) -> None:
    editor = cell.locator(".cm-content")
    editor.click()
    page.keyboard.press("ControlOrMeta+A")
    page.keyboard.insert_text(code)  # one input event: no auto-indent or bracket closing
    # CodeMirror's inner_text doubles empty lines; compare without them.
    lines = [line for line in editor.inner_text().splitlines() if line.strip()]
    assert lines == [line for line in code.splitlines() if line.strip()], "editor did not take the code"
    cell.locator(GRADE).evaluate_all("els => els.forEach(e => e.remove())")
    cell.locator(RUN_READY).click()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="page path inside site/_site, e.g. units/07-functions/")
    parser.add_argument("--raises", action="append", default=[], metavar="LABEL:TEXT")
    args = parser.parse_args()
    raises = dict(item.split(":", 1) for item in args.raises)

    failures = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page()
        try:
            print(f"first Python cell ready after {open_page(page, serve() + args.path):.1f} s")
            cells = {}
            for cell in page.locator(".exercise-cell").all():
                label = cell.evaluate(LABEL_JS)
                if label:
                    cells[label] = page.locator("#" + cell.get_attribute("id"))
            assert cells, "no exercises found on the page"
            assert set(raises) <= set(cells), f"--raises names unknown exercises: {set(raises) - set(cells)}"
            for label, cell in cells.items():
                if label in raises:
                    start = cell.locator(".cm-content").inner_text()
                    cell.locator(RUN_READY).click()
                    try:
                        expect(cell).to_contain_text(raises[label], timeout=TIMEOUT_MS)
                        ok = True
                    except AssertionError:
                        ok = False
                    failures += not ok
                    print(f"{label}: starting code raises {raises[label]}: {'yes' if ok else 'NO'}")
                    if not ok:
                        print(f"  output was: {cell.inner_text()[len(start):].strip()[:300]!r}")
                solution = page.locator(f'.exercise-solution[data-exercise="{label}"] code').first.text_content()
                run_code(page, cell, solution)
                result, message = grade_of(cell)
                failures += result != "pass"
                print(f"{label}: check with page solution: {result}: {message.strip()!r}")
        except Exception as e:  # report and fail the smoke test
            print(f"FAIL: {type(e).__name__}: {e}")
            return 1
        finally:
            browser.close()
    print("OK" if not failures else f"FAILED: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
