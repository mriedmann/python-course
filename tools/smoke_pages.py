"""Smoke test the pandas and web pages: summary lines + matplotlib figure.

Usage:  uv run python tools/smoke_pages.py [--base-url https://host/path/]
Without --base-url the built site (site/_site) is served locally. Exit code 1 on failure.
"""

import argparse
import re
import sys
import time

from playwright.sync_api import sync_playwright

from smoke_browser import RUN_READY, TIMEOUT_MS, add_target_args, launch, site_url

CHECKS = {
    "smoke/pandas.html": [r"SMOKE pandas rows=1073 customers=36 cp1252_ok=True merge_rows=1073\b"],
    "smoke/web.html": [r"SMOKE web frankfurter status=200 ok=True", r"SMOKE web open-meteo status=200 ok=True"],
}


def check(page, base: str, path: str, patterns: list[str]) -> list[str]:
    t0 = time.monotonic()
    page.goto(base + path, wait_until="domcontentloaded")
    page.wait_for_selector(RUN_READY, timeout=TIMEOUT_MS)
    errors, text = [], ""
    for pat in patterns:
        try:
            page.wait_for_function(
                "p => new RegExp(p).test(document.body.innerText)", arg=pat, timeout=TIMEOUT_MS
            )
        except Exception:
            errors.append(f"missing: {pat}")
    text = page.inner_text("body")
    for line in re.findall(r"^SMOKE .*$", text, re.M):
        print("  " + line)
    if path.endswith("pandas.html") and page.locator(".exercise-cell img, .exercise-cell canvas").count() == 0:
        errors.append("no matplotlib figure rendered")
    print(f"{path}: {'FAIL' if errors else 'ok'} after {time.monotonic() - t0:.1f} s")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    add_target_args(parser)
    args = parser.parse_args()
    base = site_url(args)
    failed = False
    with sync_playwright() as p:
        browser = launch(p, args)
        try:
            for path, patterns in CHECKS.items():
                errors = check(browser.new_page(), base, path, patterns)
                for e in errors:
                    print("  " + e)
                failed |= bool(errors)
        finally:
            browser.close()
    print("FAIL" if failed else "OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
