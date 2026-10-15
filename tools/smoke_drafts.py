"""Browser smoke test: editor drafts survive Stop and reloads; the predict cell is read-only.

Usage:  uv run python tools/smoke_drafts.py [--base-url URL]   (U7 page of the built site)
"""

import argparse
import sys

from playwright.sync_api import expect, sync_playwright

from smoke_browser import BUSY, RUN_READY, TIMEOUT_MS, add_target_args, launch, open_page, site_url

PAGE = "units/07-functions/"
TYPED = "typed_by_learner = 1"


def text(cell) -> str:
    return "\n".join(l for l in cell.locator(".cm-content").inner_text().splitlines() if l.strip())


def after_reload(page) -> None:
    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector(RUN_READY, state="attached", timeout=TIMEOUT_MS)


def main() -> int:
    parser = argparse.ArgumentParser()
    add_target_args(parser)
    args = parser.parse_args()
    with sync_playwright() as p:
        browser = launch(p, args)
        page = browser.new_page()
        try:
            open_page(page, site_url(args) + PAGE)
            cell = page.locator(".exercise-cell:not(.predict .exercise-cell)").first
            original = text(cell)
            cell.locator(".cm-content").click()
            page.keyboard.press("ControlOrMeta+A")
            page.keyboard.insert_text("while True: pass")
            cell.locator(RUN_READY).click()
            expect(cell.locator(BUSY)).to_be_attached()
            cell.get_by_role("button", name="Stop").click()  # saves, then reloads
            after_reload(page)
            assert text(cell) == "while True: pass", f"draft lost after Stop: {text(cell)!r}"
            print("Stop: typed code is back after the reload")
            cell.locator(".cm-content").click()
            page.keyboard.press("ControlOrMeta+A")
            page.keyboard.insert_text(TYPED)
            page.wait_for_timeout(800)  # debounce
            after_reload(page)
            assert text(cell) == TYPED, f"draft lost after reload: {text(cell)!r}"
            after_reload(page)
            assert text(cell) == TYPED
            print("reload: draft still there")
            cell.get_by_role("button", name="Start Over").click()
            page.wait_for_timeout(800)
            assert text(cell) == original, "Start Over did not restore the original"
            after_reload(page)
            assert text(cell) == original, "draft came back after Start Over"
            print("Start Over: original code, draft gone")

            box = page.locator(".predict").first
            code = text(box)
            box.locator(".cm-content").click()
            page.keyboard.type("zzz")
            page.wait_for_timeout(300)
            assert text(box) == code, "predict code is editable"
            box.get_by_label("Your prediction").fill("x")
            box.get_by_role("button", name="Lock prediction").click()
            box.locator(".exercise-editor-btn-run-code").click()
            expect(box.locator(".predict-verdict")).to_be_visible(timeout=TIMEOUT_MS)
            assert text(box) == code
            print("predict: code not editable, Run works after the lock")
        except Exception as e:
            print(f"FAIL: {type(e).__name__}: {e}")
            return 1
        finally:
            browser.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
