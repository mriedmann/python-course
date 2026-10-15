"""Browser smoke test for error explanations (components/errors.js).

Usage:  uv run python tools/smoke_errors.py [--base-url https://host/path/]

Runs every cell of the fixture page units/00-demo/errors.html (one error type each, the cell caption
names it) and asserts: a specific plain-language line above the output, a traceback with the learner's
frame ("your code", unless Python could not read the cell) and the final `Type: message` line, no
Pyodide/library frames. The first cell autoruns: the hook must be installed before it. Then U7's fix_order must show the unit's own .error-explain text.
Exit code 1 on any failure.
"""

import argparse
import sys

from playwright.sync_api import sync_playwright

from smoke_browser import RUN_READY, TIMEOUT_MS, add_target_args, launch, open_page, site_url

# caption -> (text the explanation must contain, final traceback line)
CASES = {
    "NameError on load": ("name `quote_count`", "NameError: name 'quote_count' is not defined"),  # autorun
    "NameError": ("name `quantity`", "NameError: name 'quantity' is not defined"),
    "NameError before def": ("`def net_price` block has not run", "NameError: name 'net_price' is not defined"),
    "TypeError missing argument": ("'unit_price' is missing", "TypeError: quote_value() missing 1 required positional argument: 'unit_price'"),
    "TypeError extra argument": ("passes 3 values", "TypeError: quote_value() takes 2 positional arguments but 3 were given"),
    "TypeError str plus int": ("join text with a whole number", 'TypeError: can only concatenate str (not "int") to str'),
    "TypeError NoneType": ("without `return` gives back `None`", "TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'"),
    "SyntaxError": ("needs a colon `:`", "SyntaxError: expected ':'"),
    "IndentationError": ("must be indented", "IndentationError: expected an indented block after function definition on line 1"),
    "KeyError": ("no key `unit_price`", "KeyError: 'unit_price'"),
    "IndexError": ("Positions start at 0", "IndexError: list index out of range"),
    "ValueError int": ("but '2150,44' is not one", "ValueError: invalid literal for int() with base 10: '2150,44'"),
    "ValueError raise": ("`raise ValueError` line ran", "ValueError: discount 45 % is above the 30 % limit"),
    "ZeroDivisionError": ("Line 2 divides by zero", "ZeroDivisionError: division by zero"),
    "AttributeError": ("no `.lowercase`", "AttributeError: 'str' object has no attribute 'lowercase'"),
    "FileNotFoundError": ("cannot find the file 'data/quote.csv'", "FileNotFoundError: [Errno 44] No such file or directory: 'data/quote.csv'"),
    "UnicodeDecodeError": ('`encoding="cp1252"`', "UnicodeDecodeError: 'utf-8' codec can't decode byte 0xfc in position 84: invalid start byte"),
    "ModuleNotFoundError": ("no module called `pandsa`", "ModuleNotFoundError: No module named 'pandsa'"),
}
UNPARSED = {"SyntaxError", "IndentationError"}  # Python could not read the cell: no frames, only the line
U7_TEXT = "Python runs a cell from top to bottom. product_name only exists after its def block has run"

# The explanation with `code` spans written back as backticks, so CASES can name code exactly.
HELP_JS = """cell => {
  const p = cell.querySelector('.error-help');
  if (!p) return null;
  return [...p.childNodes].map(n => n.nodeName === 'CODE' ? '`' + n.textContent + '`' : n.textContent).join('');
}"""


def run(cell, click=True):
    if click:
        cell.locator(RUN_READY).click()
    cell.locator(".error-help").wait_for(timeout=TIMEOUT_MS)
    return cell.evaluate(HELP_JS), cell.locator(".cell-output-stderr").inner_text().strip()


def check_case(caption: str, explanation: str, stderr: str) -> list[str]:
    want, final = CASES[caption]
    errors = []
    if want not in explanation:
        errors.append(f"explanation lacks {want!r}")
    if stderr.splitlines()[-1] != final:
        errors.append(f"last line is {stderr.splitlines()[-1]!r}")
    if caption not in UNPARSED and not stderr.startswith('Traceback (most recent call last):\n  File "your code", line'):
        errors.append("no learner frame")
    if caption in UNPARSED and not stderr.startswith('File "your code", line'):  # inner_text().strip()
        errors.append("no learner line")
    if any(s in stderr for s in ('File "/', "<exec>", "<cell-", "pyodide")):
        errors.append("internal frames shown")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    add_target_args(parser)
    args = parser.parse_args()
    base = site_url(args)
    failures = 0
    with sync_playwright() as p:
        browser = launch(p, args)
        page = browser.new_page()
        try:
            print(f"fixture ready after {open_page(page, base + 'units/00-demo/errors.html'):.1f} s")
            seen = set()
            for cell in page.locator(".exercise-cell").all():
                caption = cell.locator(".exercise-editor-header").inner_text().split("\n")[0].strip()
                explanation, stderr = run(cell, click="on load" not in caption)  # hook must beat autorun
                errors = check_case(caption, explanation, stderr)
                seen.add(caption)
                failures += bool(errors)
                print(f"{'ok  ' if not errors else 'FAIL'} {caption}: {explanation[:90]!r}{' ' + '; '.join(errors) if errors else ''}")
            missing = set(CASES) - seen
            failures += bool(missing)
            if missing:
                print(f"FAIL: no fixture cell for {sorted(missing)}")

            open_page(page, base + "units/07-functions/")
            cell = page.locator(".exercise-cell", has_text="first_name = product_name").first
            explanation, stderr = run(cell)
            ok = explanation.replace("`", "").startswith(U7_TEXT) and "NameError: name 'product_name' is not defined" in stderr
            failures += not ok
            print(f"{'ok  ' if ok else 'FAIL'} U7 fix_order: {explanation!r}")
        except Exception as e:  # report and fail the smoke test
            print(f"FAIL: {type(e).__name__}: {e}")
            return 1
        finally:
            browser.close()
    print("OK" if not failures else f"FAILED: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
