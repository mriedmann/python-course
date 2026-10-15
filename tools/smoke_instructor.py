"""Browser smoke test for instructor mode on U7: no spoilers, warm-up lifted, flag kept, presenter toggle.

Usage:  uv run python tools/smoke_instructor.py [--base-url URL]
"""

import argparse
import sys

from playwright.sync_api import expect, sync_playwright

from smoke_browser import RUN_READY, TIMEOUT_MS, pass_warmup, add_target_args, grade_of, launch, run_cell, site_url

SPOILERS = ".exercise-hint, .exercise-solution, [aria-label*='Hint'], [aria-label*='Solution'], .btn-exercise-solution, .anim > .btn, .predict .explain"
WRONG = "q = quotes[0]\nnet_value = q['quantity'] * q['unit_price_eur']"


def visible_spoilers(page) -> int:
    return page.locator(SPOILERS).evaluate_all("els => els.filter(e => e.getClientRects().length > 0).length")


def main() -> int:
    parser = argparse.ArgumentParser()
    add_target_args(parser)
    args = parser.parse_args()
    base = site_url(args)
    url = base + "units/07-functions/"
    with sync_playwright() as p:
        browser = launch(p, args)
        page = browser.new_page()
        try:
            page.goto(url + "?instructor", wait_until="domcontentloaded")
            page.wait_for_selector(RUN_READY, timeout=TIMEOUT_MS)
            expect(page.locator(".exercise-cell .cm-editor").first).to_be_visible()  # no warm-up submitted
            print("cells visible without warm-up")
            cell = page.locator(".exercise-cell:has([aria-label='Show Hint'])").first
            cell = page.locator("#" + cell.get_attribute("id"))
            for _ in range(2):
                run_cell(page, cell, WRONG)
                assert grade_of(cell)[0] == "fail"
            assert visible_spoilers(page) == 0, "spoiler visible after 2 failed checks"
            assert page.locator(".btn-exercise-solution").count() == 0 or not page.locator(".btn-exercise-solution").first.is_visible()
            print("no hints, solutions, reveal or buttons after 2 failed checks")

            sizes = lambda: page.evaluate("[getComputedStyle(document.body).fontSize, getComputedStyle(document.querySelector('.cm-content')).fontSize].map(parseFloat)")
            before = sizes()
            page.get_by_role("button", name="Presenter").click()
            after = sizes()
            assert after[0] > before[0] and after[1] > before[1], (before, after)
            print(f"presenter toggle: {before} -> {after}")

            page.goto(base, wait_until="domcontentloaded")  # no query: flag kept for the tab
            page.get_by_role("link", name="U7 Functions").click()
            page.wait_for_selector(RUN_READY, timeout=TIMEOUT_MS)
            assert page.evaluate("document.documentElement.classList.contains('instructor')")
            assert page.evaluate("document.documentElement.classList.contains('presenter')")
            expect(page.locator(".exercise-cell .cm-editor").first).to_be_visible()
            print("flag and presenter state survive navigation")

            page.goto(url + "?instructor=0", wait_until="domcontentloaded")
            page.wait_for_selector(RUN_READY, state="attached", timeout=TIMEOUT_MS)
            assert not page.evaluate("document.documentElement.classList.contains('instructor')")
            expect(page.locator("[aria-label='Show Hint']").first).to_be_hidden()  # still behind warm-up
            expect(page.locator(".exercise-cell .cm-editor").first).to_be_hidden()
            pass_warmup(page)
            expect(page.locator("[aria-label='Show Hint']").first).to_be_visible()
            print("?instructor=0: normal mode (warm-up gate back, hints available)")
        except Exception as e:
            print(f"FAIL: {type(e).__name__}: {e}")
            return 1
        finally:
            browser.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
