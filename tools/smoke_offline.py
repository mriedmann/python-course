"""Offline smoke test: first visit installs the service worker, then the page must work with the network off.

Usage:  uv run python tools/smoke_offline.py [units/00-demo/]

Serves site/_site under /python-course/ (like GitHub Pages), waits for the service worker to be active
(= precache complete), goes offline, reloads and checks: Pyodide ready, exercise check passes, and
`while True` + Stop recovers. Prints the offline payload (sum of cached response sizes).
Exit code 1 on any failure.
"""

import functools
import http.server
import sys
import threading
import time

from playwright.sync_api import expect, sync_playwright
from smoke_browser import BUSY, RUN_READY, SITE, TIMEOUT_MS, grade_of, open_page, run_cell

PREFIX = "/python-course/"


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        return super().translate_path(path[len(PREFIX) - 1 :] if path.startswith(PREFIX) else "/__missing__")

    def log_message(self, *args):
        pass


def serve() -> str:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=SITE))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_port}{PREFIX}"


CACHE_STATS = """async () => {
  let n = 0, bytes = 0;
  for (const key of await caches.keys()) {
    const cache = await caches.open(key);
    for (const req of await cache.keys()) { n++; bytes += (await (await cache.match(req)).blob()).size; }
  }
  return [await caches.keys(), n, bytes];
}"""


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "units/00-demo/"
    url = serve() + path
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context()
        page = context.new_page()
        try:
            print(f"online: first cell ready after {open_page(page, url):.1f} s")
            t0 = time.monotonic()
            page.evaluate("navigator.serviceWorker.ready.then(() => 0)")  # active only after precache succeeded
            page.wait_for_function("navigator.serviceWorker.controller !== null", timeout=TIMEOUT_MS)
            keys, n, size = page.evaluate(CACHE_STATS)
            print(f"service worker active {time.monotonic() - t0:.1f} s after ready; caches {keys}")
            print(f"offline payload: {n} responses, {size / 1e6:.1f} MB")
            assert n > 30 and size > 20e6, "precache looks incomplete"

            context.set_offline(True)
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector(RUN_READY, timeout=TIMEOUT_MS)
            print("offline: first cell ready after reload")
            cell = page.locator(".exercise-cell:has([aria-label='Show Hint'])").first
            cell = page.locator("#" + cell.get_attribute("id"))
            run_cell(page, cell, page.locator(".exercise-solution code").first.text_content())
            result, message = grade_of(cell)
            print(f"offline: check with solution: {result}: {message.strip()!r}")
            assert result == "pass"

            loop = page.locator(".exercise-cell", has_text="while True").first
            loop.locator(RUN_READY).click()
            expect(loop.locator(BUSY)).to_be_visible()
            time.sleep(2)
            with page.expect_navigation(wait_until="domcontentloaded"):
                loop.locator(".btn-exercise-stop").click()
            page.wait_for_selector(RUN_READY, timeout=TIMEOUT_MS)
            run_cell(page, cell, "print(len(quotes))")
            expect(cell.locator(".cell-output-stdout")).to_contain_text("20", timeout=TIMEOUT_MS)
            print("offline: Stop recovered, Python usable again")
        except Exception as e:
            print(f"FAIL: {type(e).__name__}: {e}")
            return 1
        finally:
            browser.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
