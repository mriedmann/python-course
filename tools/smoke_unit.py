"""Browser smoke test for EVERY exercise of a built unit page (site/_site).

Usage:  uv run python tools/smoke_unit.py units/07-functions/ [--raises LABEL:TEXT ...]
                                            [--predict ID:TEXT ...]

Walks the page like a learner: warm-up quiz (answered from the DOM, score must be full), then for each quarto-live exercise: insert the page's own solution, run the check, assert it
passes. With --raises, first run that exercise's starting code and assert the output shows the
error text, e.g. "fix_order:is not defined" (the "starts from a real traceback" exercise, P5;
quarto-live 0.2.0 shows the error message without its type name). Then: every animation to its last frame ("Show me the code"), each --predict (correct text passes; on
a fresh context a wrong text fails; `\\n` = newline), every Parsons problem solved by keyboard (solution
read from the unit's index.qmd), every exit quiz. Each must emit pycourse:result passed=true, and a
reload must restore all states. Exit code 1 on any failure.
"""

import argparse
import re
import sys

from playwright.sync_api import expect, sync_playwright

from smoke_browser import RUN_READY, SITE, TIMEOUT_MS, add_target_args, grade_of, launch, open_page, run_cell, site_url, submit_quiz

LABEL_JS = """cell => {
  const s = document.querySelector(`script[type="${cell.id}-contents"]`);
  return JSON.parse(window._exercise_ojs_runtime.b64Decode(s.textContent)).attr.exercise || null;
}"""


LISTEN = "window.results = []; document.addEventListener('pycourse:result', e => results.push(e.detail));"
DONE = "Correct. All lines are in place."


def solution_lines(path: str, box_id: str) -> list[str]:
    """Solution of a Parsons problem: the first python fence after `.parsons #id` in the unit's source."""
    source = (SITE.parent / path / "index.qmd").read_text()
    m = re.search(r"\{\.parsons #" + re.escape(box_id) + r"\}\n```python\n(.*?)```", source, re.S)
    assert m, f"no parsons problem #{box_id} in the source"
    return m.group(1).rstrip().splitlines()


def parsons(page, box, lines: list[str]) -> None:
    source = box.locator(".parsons-list").first
    for line in lines:
        text = line.strip()
        source.locator(".parsons-line", has_text=re.compile(f"^{re.escape(text)}$")).first.focus()
        page.keyboard.press("Enter")
        for _ in range((len(line) - len(text)) // 4):
            page.keyboard.press("ArrowRight")
    box.get_by_role("button", name="Check").click()
    expect(box.locator(".parsons-result")).to_have_text(DONE)


def walkthrough(page, path: str, predicts: dict) -> None:
    """Everything except the exercises; returns after asserting events. Each step prints one line."""
    ids = []  # component ids that must report passed=true
    for quiz in page.locator(".quiz.exit").all():
        print(f"exit quiz {quiz.get_attribute('id')}: {submit_quiz(quiz)}")
        ids.append(quiz.get_attribute("id"))
    for box in page.locator(".anim").all():
        show = box.get_by_role("button", name="Show me the code")
        expect(show).to_be_disabled()
        frames = box.locator(".frame").count()
        for _ in range(frames - 1):
            box.get_by_role("button", name="Next").click()
        expect(show).to_be_enabled()
        show.click()
        expect(box.locator(".reveal")).to_be_visible()
        assert box.locator(".reveal").inner_text().strip(), "reveal is empty"
        print(f"anim {box.get_attribute('id')}: {frames} frames, code revealed")
        ids.append(box.get_attribute("id"))
    for box in page.locator(".predict").all():
        pid = box.get_attribute("id")
        box.get_by_label("Your prediction").fill(predicts[pid])
        box.get_by_role("button", name="Lock prediction").click()
        box.locator(".exercise-editor-btn-run-code").click()
        expect(box.locator(".predict-verdict")).to_have_text("Your prediction matches.", timeout=TIMEOUT_MS)
        print(f"predict {pid}: correct prediction passes")
        ids.append(pid)
    for box in page.locator(".parsons").all():
        parsons(page, box, solution_lines(path, box.get_attribute("id")))
        print(f"parsons {box.get_attribute('id')}: keyboard solve passes")
        ids.append(box.get_attribute("id"))
    events = page.evaluate("results")
    # the warm-up fired during open_page, before the listener of this page was read: it is in the list too
    missing = [i for i in ids + [q.get_attribute("id") for q in page.locator(".quiz.warmup").all()]
               if not any(e["id"] == i and e["passed"] for e in events)]
    assert not missing, f"no passed=true pycourse:result for {missing}; events: {events}"
    print(f"events: passed=true for {len(ids) + page.locator('.quiz.warmup').count()} components")


def restored(page) -> None:
    page.reload(wait_until="domcontentloaded")
    for quiz in page.locator(".quiz").all():
        n = quiz.locator(".question").count()
        expect(quiz.locator(".quiz-score")).to_have_text(f"Score: {n}/{n}")
    for box in page.locator(".anim").all():
        expect(box.get_by_role("button", name="Show me the code")).to_be_enabled()
    for box in page.locator(".predict").all():
        expect(box.locator(".predict-verdict")).to_have_text("Your prediction matches.")
        expect(box.get_by_label("Your prediction")).not_to_be_editable()
    for box in page.locator(".parsons").all():
        expect(box.locator(".parsons-result")).to_have_text(DONE)
    print("reload: all component states restored")


def wrong_prediction(browser, url: str, predicts: dict) -> None:
    page = browser.new_context().new_page()  # fresh localStorage
    open_page(page, url)
    for pid in predicts:
        box = page.locator("#" + pid)
        box.get_by_label("Your prediction").fill("nothing useful")
        box.get_by_role("button", name="Lock prediction").click()
        box.locator(".exercise-editor-btn-run-code").click()
        expect(box.locator(".predict-verdict")).to_have_text("Compare: what differs?", timeout=TIMEOUT_MS)
        print(f"predict {pid}: wrong prediction fails (fresh context)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="page path inside site/_site, e.g. units/07-functions/")
    parser.add_argument("--raises", action="append", default=[], metavar="LABEL:TEXT")
    parser.add_argument("--predict", action="append", default=[], metavar="ID:TEXT")
    add_target_args(parser)
    args = parser.parse_args()
    raises = dict(item.split(":", 1) for item in args.raises)
    predicts = {k: v.replace("\\n", "\n") for k, v in (item.split(":", 1) for item in args.predict)}

    failures = 0
    with sync_playwright() as p:
        browser = launch(p, args)
        page = browser.new_page()
        page.add_init_script(LISTEN)
        try:
            url = site_url(args) + args.path
            print(f"first Python cell ready after {open_page(page, url):.1f} s; warm-up passed, cells visible")
            assert {b.get_attribute("id") for b in page.locator(".predict").all()} == set(predicts), \
                "pass --predict ID:TEXT for every predict box on the page"
            cells = {}
            for cell in page.locator(".exercise-cell").all():
                label = cell.evaluate(LABEL_JS)
                if label:
                    cells[label] = page.locator("#" + cell.get_attribute("id"))
            assert cells, "no exercises found on the page"
            assert set(raises) <= set(cells), f"--raises names unknown exercises: {set(raises) - set(cells)}"
            for label, cell in cells.items():
                if label in raises:
                    start = cell.locator(".cm-content").inner_text()
                    cell.locator(RUN_READY).click()
                    try:
                        expect(cell).to_contain_text(raises[label], timeout=TIMEOUT_MS)
                        ok = True
                    except AssertionError:
                        ok = False
                    failures += not ok
                    print(f"{label}: starting code raises {raises[label]}: {'yes' if ok else 'NO'}")
                    if not ok:
                        print(f"  output was: {cell.inner_text()[len(start):].strip()[:300]!r}")
                solution = page.locator(f'.exercise-solution[data-exercise="{label}"] code').first.text_content()
                run_cell(page, cell, solution)
                result, message = grade_of(cell)
                failures += result != "pass"
                print(f"{label}: check with page solution: {result}: {message.strip()!r}")
            walkthrough(page, args.path, predicts)
            restored(page)
            wrong_prediction(browser, url, predicts)
        except Exception as e:  # report and fail the smoke test
            print(f"FAIL: {type(e).__name__}: {e}")
            return 1
        finally:
            browser.close()
    print("OK" if not failures else f"FAILED: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
