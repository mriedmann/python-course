"""Browser smoke test: step progress bar, stored exercise results, export / import / reset.

Usage:  uv run python tools/smoke_progress.py [--base-url URL]   (U7 page of the built site)
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from smoke_browser import RUN_READY, TIMEOUT_MS, add_target_args, grade_of, launch, open_page, run_cell, site_url

PAGE = "units/07-functions/"
PREFIX = "pycourse:v1:"


def steps_done(page) -> int:
    return int(page.locator(".pc-count").inner_text().split(" of ")[0])


def reload(page) -> None:
    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector(RUN_READY, state="attached", timeout=TIMEOUT_MS)


def open_panel(page) -> None:
    page.get_by_role("link", name="Progress").first.click()
    expect(page.locator("#pc-panel")).to_be_visible()


def stored(page) -> dict:
    return page.evaluate("p => Object.fromEntries(Object.entries(localStorage).filter(([k]) => k.startsWith(p)))", PREFIX)


def main() -> int:
    parser = argparse.ArgumentParser()
    add_target_args(parser)
    args = parser.parse_args()
    tmp = Path(tempfile.mkdtemp())
    with sync_playwright() as p:
        browser = launch(p, args)
        page = browser.new_page(accept_downloads=True)
        try:
            open_page(page, site_url(args) + PAGE)  # submits the warm-up
            nav = page.get_by_role("navigation", name="Unit progress")
            expect(nav).to_be_visible()
            assert nav.get_by_role("listitem").count() == 8
            expect(nav.locator("li.done").first).to_contain_text("Warm-up")
            n = steps_done(page)
            assert n in (1, 2), f"after the warm-up: {n} of 8"
            print(f"warm-up done: {n} of 8 steps")

            cell = page.locator(".exercise-cell:has([aria-label='Show Hint'])").first
            cell = page.locator("#" + cell.get_attribute("id"))
            run_cell(page, cell, page.locator(".exercise-solution code").first.text_content())
            assert grade_of(cell)[0] == "pass"
            ex = {k: v for k, v in stored(page).items() if ":exercise:" in k}
            assert len(ex) == 1 and json.loads(next(iter(ex.values())))["passed"] is True, ex
            reload(page)
            assert {k for k in stored(page) if ":exercise:" in k} == set(ex)
            print(f"exercise result stored and kept after reload: {list(ex)}")

            before = stored(page)
            open_panel(page)
            with page.expect_download() as d:
                page.get_by_role("button", name="Export progress").click()
            out = tmp / "export.json"
            d.value.save_as(out)
            assert d.value.suggested_filename.startswith("python-course-progress-")
            data = json.loads(out.read_text())
            assert data["format"] == "pycourse-progress" and data["version"] == 1
            assert set(ex) <= set(data["items"]) and set(data["items"]) == set(before), "export keys"
            print(f"export: {len(data['items'])} items")

            page.get_by_role("button", name="Reset progress").click()
            page.get_by_role("button", name="Confirm reset").click()
            reload(page)
            assert not stored(page) or steps_done(page) <= 1
            assert not [k for k in stored(page) if ":exercise:" in k or k.endswith(":complete")]
            print(f"reset: bar shows {steps_done(page)} of 8")

            bad = {"foreign": {"format": "pycourse-progress", "version": 1, "items": {"other:x": "1"}},
                   "nonstring": {"format": "pycourse-progress", "version": 1, "items": {PREFIX + "x": 1}},
                   "version": {"format": "pycourse-progress", "version": 2, "items": {}},
                   "malformed": None}
            snapshot = stored(page)
            for name, content in bad.items():
                f = tmp / f"{name}.json"
                f.write_text("{not json" if content is None else json.dumps(content))
                open_panel(page)
                page.set_input_files("#pc-file", f)
                expect(page.locator(".pc-msg")).to_contain_text("Import rejected, nothing changed")
                assert stored(page) == snapshot, f"{name} changed storage"
                page.keyboard.press("Escape")
            print("malformed / foreign-key / non-string / wrong-version imports rejected, storage unchanged")

            open_panel(page)
            page.set_input_files("#pc-file", out)
            expect(page.locator(".pc-confirm")).to_contain_text(f"{len(data['items'])} items, will replace")
            assert stored(page) == snapshot, "changed before confirm"
            with page.expect_navigation(wait_until="domcontentloaded"):
                page.get_by_role("button", name="Confirm import").click()
            page.wait_for_selector(RUN_READY, state="attached", timeout=TIMEOUT_MS)
            assert set(ex) <= set(stored(page)), "exercise result not restored"
            print("import: state restored after reload")
        except Exception as e:
            print(f"FAIL: {type(e).__name__}: {e}")
            return 1
        finally:
            browser.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
