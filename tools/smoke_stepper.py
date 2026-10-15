"""Browser smoke test for the stepper (components/stepper.js + stepper.py).

Usage:  uv run python tools/smoke_stepper.py [--base-url URL] [--screenshots DIR]

U7 `retype` with the worked-example solution: a frame `quote_value` with `row` and `value` appears,
and after its return step those names are gone while `first_value` exists (M9). Fixture page
units/00-demo/stepper.html: two names on one list with 3 items (M7), operated with the keyboard only
(Enter, End, Home, arrows, Escape), `while True: pass` stops at the step cap without freezing, and
an error gets the errors.js explanation.
Exit code 1 on any failure.
"""

import argparse
import sys
import time

from playwright.sync_api import expect, sync_playwright

from smoke_browser import RUN_READY, TIMEOUT_MS, add_target_args, launch, open_page, site_url

# Panel state as text: status line, frame tables {caption: [[name, value], ...]}, object headings.
STATE_JS = """panel => ({
  status: panel.querySelector('.stepper-status').textContent,
  frames: Object.fromEntries([...panel.querySelectorAll('.stepper-frame')].map(t => [
    t.caption.textContent,
    [...t.querySelectorAll('tr')].filter(r => r.querySelector('th')).map(r => [r.querySelector('th').textContent, r.querySelector('td').textContent])])),
  objects: [...panel.querySelectorAll('.stepper-obj-head')].map(p => p.textContent),
})"""


def set_code(page, cell, code: str) -> None:
    cell.locator(".cm-content").click()
    page.keyboard.press("ControlOrMeta+A")
    page.keyboard.insert_text(code)


def open_stepper(cell, keyboard=False):
    button = cell.locator(".btn-exercise-step")
    expect(button).to_be_enabled(timeout=TIMEOUT_MS)
    if keyboard:
        button.focus()
        button.press("Enter")
    else:
        button.click()
    panel = cell.locator(".stepper")
    panel.locator(".stepper-controls").wait_for(timeout=TIMEOUT_MS)
    return panel


def check_u7(page, base: str, shots) -> list[str]:
    open_page(page, base + "units/07-functions/")
    cell = page.locator(".exercise-cell", has_text="Type the worked example here").first
    cell = page.locator("#" + cell.get_attribute("id"))  # stable after the editor text changes
    set_code(page, cell, page.locator('.exercise-solution[data-exercise="retype"] code').text_content())
    panel = open_stepper(cell)
    errors, seen_frame, returned = [], False, False
    for _ in range(100):
        s = panel.evaluate(STATE_JS)
        names = {c: [n for n, _ in rows] for c, rows in s["frames"].items()}
        call = names.get("quote_value (function call)")
        if call and {"row", "value"} <= set(call):
            seen_frame = True
        if returned:
            print(f"after return: {s['status']!r} frames {names}")
            if call or "first_value" not in names.get("Global names", []):
                errors.append(f"after the return step: {names}")
            break
        if "returns" in s["status"]:
            print(f"return step: {s['status']!r} frames {names}")
            returned = True
        panel.get_by_role("button", name="Next ▶").click()
    if not seen_frame:
        errors.append("no frame quote_value with row and value")
    if not returned:
        errors.append("no return step")
    if shots:
        page.keyboard.press("Home")
        for _ in range(3):
            page.keyboard.press("ArrowRight")
        panel.screenshot(path=f"{shots}/stepper_u7_frame.png")
    print(f"{'ok  ' if not errors else 'FAIL'} U7 retype: frame quote_value seen={seen_frame}, gone after return (M9)")
    return errors


def check_fixture(page, base: str, shots) -> list[str]:
    open_page(page, base + "units/00-demo/stepper.html")
    errors = []
    cell = page.locator(".exercise-cell", has_text="Shared list")
    panel = open_stepper(cell, keyboard=True)
    focused = page.evaluate("document.activeElement.textContent")
    page.keyboard.press("End")
    s = panel.evaluate(STATE_JS)
    rows = dict(s["frames"].get("Global names", []))
    print(f"last step: {s['status']!r} {rows} {s['objects']}")
    if not (rows.get("prices") == rows.get("backup") == "→ list #1"):
        errors.append(f"prices/backup not on one list: {rows}")
    if "list #1 · 3 items · names: prices, backup" not in s["objects"]:
        errors.append(f"shared list not shown with 3 items: {s['objects']}")
    page.keyboard.press("Home")
    page.keyboard.press("ArrowRight")
    if not panel.evaluate(STATE_JS)["status"].startswith("Step 2 of"):
        errors.append("ArrowRight did not go to step 2")
    if shots:
        page.keyboard.press("End")
        panel.screenshot(path=f"{shots}/stepper_shared_list.png")
    page.keyboard.press("Escape")
    if cell.locator(".stepper").count() or not page.evaluate("document.activeElement.classList.contains('btn-exercise-step')"):
        errors.append("Escape did not close the panel and return focus")
    print(f"{'ok  ' if not errors else 'FAIL'} shared list (M7), keyboard only (focus on open: {focused!r})")

    loop = page.locator(".exercise-cell", has_text="Endless loop")
    t0 = time.monotonic()
    panel = open_stepper(loop)
    took = time.monotonic() - t0
    note = panel.locator(".stepper-note").first.text_content()
    status = panel.evaluate(STATE_JS)["status"]
    alive = page.evaluate("1 + 1") == 2 and cell.locator(RUN_READY).count() == 1
    ok = "Stopped after 500 steps" in note and status.startswith("Step 1 of 500") and took < 30 and alive
    print(f"{'ok  ' if ok else 'FAIL'} while True: {note!r} after {took:.1f} s, page responsive={alive}")
    errors += [] if ok else ["while True did not stop at the step cap"]

    panel = open_stepper(page.locator(".exercise-cell", has_text="Error in a function"))
    help_text = panel.locator(".error-help").text_content(timeout=TIMEOUT_MS)
    last = panel.locator(".cell-output-stderr").inner_text().strip().splitlines()[-1]
    ok = "divides by zero" in help_text and last == "ZeroDivisionError: division by zero"
    print(f"{'ok  ' if ok else 'FAIL'} error: {help_text!r} / {last!r}")
    return errors + ([] if ok else ["error not explained by errors.js"])


def main() -> int:
    parser = argparse.ArgumentParser()
    add_target_args(parser)
    parser.add_argument("--screenshots", help="directory for two panel screenshots")
    args = parser.parse_args()
    base = site_url(args)
    with sync_playwright() as p:
        browser = launch(p, args)
        page = browser.new_page()
        try:
            errors = check_u7(page, base, args.screenshots) + check_fixture(page, base, args.screenshots)
        except Exception as e:  # report and fail the smoke test
            print(f"FAIL: {type(e).__name__}: {e}")
            return 1
        finally:
            browser.close()
    for e in errors:
        print(f"FAIL: {e}")
    print("OK" if not errors else f"FAILED: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
