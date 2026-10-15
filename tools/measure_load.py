"""Cold-load measurement of the deployed site under 50 Mbit/s throttling (gate G-A).

Usage:  uv run python tools/measure_load.py [--base-url URL] [--runs 3]

Per run: fresh browser context (no HTTP cache, service workers blocked), CDP
Network.emulateNetworkConditions (50 Mbit/s down, 10 Mbit/s up, 20 ms latency), then
  ready = navigation start -> Python engine ready (run button present and enabled in the DOM,
          even when a warm-up hides the cells), and
  summary = navigation start -> pandas page prints its `SMOKE pandas ...` line.
Transferred bytes = sum over all page and worker responses of Playwright's request.sizes()
(encoded body + response headers), split by origin. Also one unthrottled run per page.
"""

import argparse
import re
import statistics
import time
from collections import defaultdict
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from smoke_browser import RUN_READY, TIMEOUT_MS

PAGES = ["units/07-functions/", "smoke/pandas.html"]
SUMMARY = r"SMOKE pandas rows=1073 customers=36 cp1252_ok=True merge_rows=1073\b"
THROTTLE = {"offline": False, "latency": 20, "downloadThroughput": 50_000_000 / 8, "uploadThroughput": 10_000_000 / 8}


def run_once(browser, url: str, throttle: bool, summary: bool) -> dict:
    context = browser.new_context(service_workers="block")
    page = context.new_page()
    sizes = []
    context.on("requestfinished", lambda r: sizes.append(r))
    if throttle:
        cdp = context.new_cdp_session(page)
        cdp.send("Network.enable")
        cdp.send("Network.emulateNetworkConditions", THROTTLE)
    t0 = time.monotonic()
    page.goto(url, wait_until="commit")
    page.wait_for_selector(RUN_READY, state="attached", timeout=TIMEOUT_MS)
    out = {"ready": time.monotonic() - t0}
    if summary:
        page.wait_for_function("p => new RegExp(p).test(document.body.innerText)", arg=SUMMARY, timeout=TIMEOUT_MS)
        out["summary"] = time.monotonic() - t0
    by_origin, total = defaultdict(int), 0
    for r in sizes:
        try:
            s = r.sizes()
        except Exception:
            continue
        n = s["responseBodySize"] + s["responseHeadersSize"]
        host = urlparse(r.url).netloc
        by_origin[host] += n
        total += n
    out["bytes"], out["by_origin"] = total, dict(by_origin)
    context.close()
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="https://mriedmann.github.io/python-course/")
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    base = args.base_url.rstrip("/") + "/"
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        print(f"Chrome {browser.version}")
        for path in PAGES:
            summary = path.endswith("pandas.html")
            for label, throttle, n in (("throttled 50 Mbit/s", True, args.runs), ("unthrottled", False, 1)):
                results = [run_once(browser, base + path, throttle, summary) for _ in range(n)]
                for i, r in enumerate(results, 1):
                    mb = {h: round(b / 1e6, 2) for h, b in sorted(r["by_origin"].items(), key=lambda kv: -kv[1])}
                    extra = f" summary={r['summary']:.1f}s" if summary else ""
                    print(f"{path} {label} run {i}: ready={r['ready']:.1f}s{extra} transferred={r['bytes'] / 1e6:.1f} MB {mb}")
                keys = ["ready"] + (["summary"] if summary else [])
                for k in keys:
                    print(f"{path} {label} median {k}: {statistics.median(r[k] for r in results):.1f} s")
        browser.close()


if __name__ == "__main__":
    main()
