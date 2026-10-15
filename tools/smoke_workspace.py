"""Browser smoke test for the JupyterLite workspace (site/_site/workspace, Pyodide kernel).

Usage:  uv run python tools/smoke_workspace.py [--base-url URL] [--browser firefox]

Two visitors, each in a fresh browser profile:
1. Course first: open the home page (installs the site service worker), then the workspace. Open
   units/07-functions/make.ipynb, put the solution from solution.py into the exercise cell, press the
   toolbar's "Restart & Run All" and expect the self-check to pass. Then, in a new cell: import
   quote_tools from projects/ and read data/customers.csv (cp1252) with pandas. data/quotes.csv must be
   listed in the file browser. Save, go offline, reload: Restart & Run All passes again.
2. Workspace first (no service worker yet: JupyterLite registers workspace/service-worker.js):
   Restart & Run All with the solution passes.
Any request to a host other than the site's fails the test. Exit code 1 on any failure.
"""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import expect, sync_playwright
from smoke_browser import TIMEOUT_MS, add_target_args, launch
from smoke_offline import serve

ROOT = Path(__file__).resolve().parent.parent
UNIT = ROOT / "site" / "units" / "07-functions"
NOTEBOOK = "workspace/lab/index.html?path=units/07-functions/make.ipynb"
PASSED = "All checks passed."
EXTRA = """import sys
sys.path.insert(0, "../../projects")
import quote_tools
import pandas as pd
customers = pd.read_csv("../../data/customers.csv", sep=";", encoding="cp1252")
print("SMOKE", quote_tools.discount_class(12.5), len(customers), customers["customer_name"][0])"""


def solution(label: str) -> str:
    parts = re.split(r"^# exercise: (\w+)\s*$", (UNIT / "solution.py").read_text(encoding="utf-8"), flags=re.M)
    return dict(zip(parts[1::2], parts[2::2]))[label].strip()


def cells(page):
    return page.locator(".jp-NotebookPanel:not(.lm-mod-hidden) .jp-Notebook .jp-Cell")


def open_notebook(page, url: str) -> None:
    page.goto(url, wait_until="domcontentloaded")
    expect(cells(page).nth(4)).to_be_visible(timeout=TIMEOUT_MS)
    # Kernel ready: the status bar shows "Python (Pyodide) | Idle".
    expect(page.locator(".jp-StatusBar-Widget", has_text="Idle").first).to_be_visible(timeout=TIMEOUT_MS)


def type_into(page, cell, code: str) -> None:
    cell.locator(".cm-content").click()
    page.keyboard.press("ControlOrMeta+A")
    page.keyboard.insert_text(code)  # one input event: no auto-indent or bracket closing


def restart_and_run_all(page) -> str:
    """Clear old outputs, click the toolbar button, confirm, return the text of the last cell's output."""
    last = cells(page).nth(4).locator(".jp-OutputArea")
    page.locator(".lm-MenuBar-itemLabel", has_text="Edit").click()
    page.locator(".lm-Menu-itemLabel", has_text="Clear Outputs of All Cells").click()
    expect(last).to_have_text("")
    button = page.locator(".jp-NotebookPanel:not(.lm-mod-hidden) [data-jp-item-name='restart-and-run']")
    expect(button).to_be_visible()
    button.click()
    accept = page.locator(".jp-Dialog .jp-mod-accept")
    assert accept.inner_text() == "Restart", accept.inner_text()  # the notebook's first cell names it
    accept.click()
    expect(last).to_contain_text(re.compile(f"{PASSED}|Error"), timeout=TIMEOUT_MS)
    return last.inner_text()


def run_solution(page, url: str) -> None:
    open_notebook(page, url)
    type_into(page, cells(page).nth(2), solution("discount_classes"))
    out = restart_and_run_all(page)
    print(f"Restart & Run All with the solution: {out.strip().splitlines()[-1]!r}")
    assert PASSED in out, out


def extras(page) -> None:
    cells(page).nth(4).locator(".jp-InputArea-prompt").click()  # select the last cell (command mode)
    page.keyboard.press("b")  # new cell below
    expect(cells(page)).to_have_count(6)
    type_into(page, cells(page).nth(5), EXTRA)
    page.keyboard.press("Shift+Enter")
    out = cells(page).nth(5).locator(".jp-OutputArea")
    expect(out).to_contain_text(re.compile("SMOKE|Error"), timeout=TIMEOUT_MS)
    text = out.inner_text().strip()
    rows = len((ROOT / "data" / "customers.csv").read_bytes().splitlines()) - 1
    print(f"quote_tools + pandas cp1252: {text!r}")
    assert text == f"SMOKE high {rows} Chemiewerk Süd AG", text  # ü is 0xFC in cp1252

    page.locator(".jp-BreadCrumbs-home").click()
    listing = page.locator(".jp-DirListing-content")
    listing.locator(".jp-DirListing-item", has_text="data").dblclick()
    expect(listing).to_contain_text("quotes.csv")
    print("file browser: data/quotes.csv listed")


def course_first(browser, base: str, requests: list) -> None:
    context = browser.new_context()
    context.on("request", lambda r: requests.append(r.url))
    page = context.new_page()
    page.goto(base, wait_until="domcontentloaded")
    page.wait_for_function("navigator.serviceWorker.controller !== null", timeout=TIMEOUT_MS)
    page.evaluate("navigator.serviceWorker.ready.then(() => 0)")  # precache complete
    print("course service worker active")
    run_solution(page, base + NOTEBOOK)
    extras(page)
    scope = page.evaluate("navigator.serviceWorker.getRegistrations().then(rs => rs.map(r => r.scope))")
    print(f"service worker registrations: {scope}")
    assert scope == [base], "JupyterLite must use the course service worker"
    page.keyboard.press("ControlOrMeta+S")
    expect(page.locator(".jp-NotebookPanel:not(.lm-mod-hidden) .jp-mod-dirty")).to_have_count(0)

    context.set_offline(True)
    open_notebook(page, base + NOTEBOOK)
    out = restart_and_run_all(page)
    print(f"offline: Restart & Run All after reload: {out.strip().splitlines()[-1]!r}")
    assert PASSED in out, out
    context.close()


def workspace_first(browser, base: str, requests: list) -> None:
    context = browser.new_context()
    context.on("request", lambda r: requests.append(r.url))
    page = context.new_page()
    run_solution(page, base + NOTEBOOK)
    scope = page.evaluate("navigator.serviceWorker.getRegistrations().then(rs => rs.map(r => r.scope))")
    print(f"workspace first: service worker registrations: {scope}")
    context.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    add_target_args(parser)
    args = parser.parse_args()
    base = args.base_url.rstrip("/") + "/" if args.base_url else serve()  # local: under /python-course/
    requests: list[str] = []
    with sync_playwright() as p:
        browser = launch(p, args)
        try:
            course_first(browser, base, requests)
            workspace_first(browser, base, requests)
        except Exception as e:
            print(f"FAIL: {type(e).__name__}: {e}")
            return 1
        finally:
            browser.close()
    own = urlparse(base).netloc
    foreign = sorted({u for u in requests if u.startswith("http") and urlparse(u).netloc != own})
    for u in foreign:
        print("THIRD-PARTY REQUEST:", u)
    print(f"{len(requests)} requests, {len(foreign)} to other hosts")
    if foreign:
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
