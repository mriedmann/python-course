"""Third-party smoke test: a cold lesson page must request nothing from any host but its own.

Usage:  uv run python tools/smoke_thirdparty.py [--base-url URL] [--browser firefox]

Loads units/07-functions/, smoke/pandas.html and units/00-demo/ with service workers blocked, waits for the
first cell (and the pandas summary line), then lists transferred bytes per host (page + worker requests).
Exit code 1 if any request went elsewhere.
"""

import argparse
import sys
from collections import defaultdict
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright
from smoke_browser import RUN_READY, TIMEOUT_MS, add_target_args, launch, site_url

PAGES = ["units/07-functions/", "smoke/pandas.html", "units/00-demo/"]
SUMMARY = r"SMOKE pandas rows=1073"


def check(browser, url: str) -> bool:
    context = browser.new_context(service_workers="block")
    page = context.new_page()
    done, urls = [], []
    context.on("request", lambda r: urls.append(r.url))
    context.on("requestfinished", lambda r: done.append(r))
    own = urlparse(url).netloc
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector(RUN_READY, state="attached", timeout=TIMEOUT_MS)
    if "pandas" in url:
        page.wait_for_function("p => new RegExp(p).test(document.body.innerText)", arg=SUMMARY, timeout=TIMEOUT_MS)
    by_host = defaultdict(int)
    for r in done:
        try:
            by_host[urlparse(r.url).netloc or "(data/blob)"] += r.sizes()["responseBodySize"]
        except Exception:
            pass
    foreign = sorted({u for u in urls if u.startswith("http") and urlparse(u).netloc != own})
    total = sum(by_host.values()) or 1
    print(f"{url}: " + ", ".join(f"{h} {n / 1e6:.1f} MB ({100 * n / total:.0f}%)" for h, n in by_host.items()))
    for u in foreign:
        print("  THIRD-PARTY REQUEST:", u)
    context.close()
    return not foreign


def main() -> int:
    parser = argparse.ArgumentParser()
    add_target_args(parser)
    args = parser.parse_args()
    base = site_url(args)
    with sync_playwright() as p:
        browser = launch(p, args)
        try:
            ok = [check(browser, base + path) for path in PAGES]
        except Exception as e:
            print(f"FAIL: {type(e).__name__}: {e}")
            return 1
        finally:
            browser.close()
    print("OK" if all(ok) else "FAIL")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
