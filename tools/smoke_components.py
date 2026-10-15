"""Browser smoke test for the lesson components on site/_site/units/00-demo/components.html.

Usage:  uv run python tools/smoke_components.py

Quiz (warm-up gate, score), predict (Run gated by the lock, comparison), Parsons (keyboard only,
pass and fail), animation (reveal gate), then a reload must restore every state and result.
Exit code 1 on any failure.
"""

import sys

from playwright.sync_api import expect, sync_playwright

from smoke_browser import RUN_READY, TIMEOUT_MS, serve

PAGE = "units/00-demo/components.html"
# Collects pycourse:result events into window.results (survives nothing: re-added on each load).
LISTEN = "window.results = []; document.addEventListener('pycourse:result', e => results.push(e.detail));"


def quiz(page) -> None:
    warmup = page.locator("#demo-warmup")
    cells = page.locator(".exercise-cell .cm-editor")
    expect(cells.first).to_be_attached(timeout=TIMEOUT_MS)
    assert cells.first.is_hidden(), "live cells visible before the warm-up"
    note = page.locator(".exercise-cell").first.evaluate("e => getComputedStyle(e, '::before').content")
    assert "Finish the warm-up first" in note, note
    warmup.get_by_label("[1, 2, 3]").check()
    warmup.get_by_label('"quantity" * "unit_price_eur"').check()  # wrong
    warmup.get_by_label("Your answer").fill(" None ")
    warmup.get_by_role("button", name="Check answers").click()
    expect(warmup.locator(".quiz-score")).to_have_text("Score: 2/3")
    expect(warmup.locator(".quiz-feedback.fail")).to_have_count(1)
    expect(cells.first).to_be_visible()
    print("quiz: cells hidden before, score 2/3, cells visible after")


def predict(page) -> None:
    box = page.locator("#demo-predict")
    run = box.locator(".exercise-editor-btn-run-code")
    page.wait_for_selector(RUN_READY, timeout=TIMEOUT_MS)  # Pyodide ready
    expect(run).to_have_attribute("aria-disabled", "true")
    run.click(force=True)  # must not run
    page.wait_for_timeout(1000)
    expect(box.locator(".exercise-cell-output")).to_have_count(0)
    expect(box.locator(".explain")).to_be_hidden()
    expect(box.get_by_role("button", name="Lock prediction")).to_be_disabled()
    box.get_by_label("Your prediction").fill("50")  # wrong: Python prints 50.0
    box.get_by_role("button", name="Lock prediction").click()
    expect(box.get_by_label("Your prediction")).not_to_be_editable()
    expect(run).not_to_have_attribute("aria-disabled", "true")
    run.click()
    expect(box.locator(".predict-verdict")).to_have_text("Compare: what differs?", timeout=TIMEOUT_MS)
    expect(box.locator(".predict-compare")).to_contain_text("50.0")
    expect(box.locator(".explain")).to_be_visible()
    print("predict: Run disabled before lock, comparison shown after run (fail as expected)")


def parsons(page) -> None:
    box = page.locator("#demo-parsons")
    solution = ['def quote_value(row):', '    value = row["quantity"] * row["unit_price_eur"]', '    return value']
    source = box.locator(".parsons-list").first
    for line in solution:
        text = line.strip()
        source.locator(".parsons-line", has_text=text).first.focus()
        page.keyboard.press("Enter")
        for _ in range((len(line) - len(text)) // 4):
            page.keyboard.press("ArrowRight")
    box.get_by_role("button", name="Check").click()
    expect(box.locator(".parsons-result")).to_have_text("Correct. All lines are in place.")
    results = page.evaluate("results.filter(r => r.kind === 'parsons')")
    assert results and results[-1]["passed"] is True, results
    target = box.locator(".parsons-list").nth(1).locator(".parsons-line")
    target.nth(2).focus()
    page.keyboard.press("Alt+ArrowUp")  # swap the last two lines
    box.get_by_role("button", name="Check").click()
    expect(box.locator(".parsons-result")).to_have_text("Line 2 is in the wrong place or wrongly indented.")
    target.nth(1).focus()
    page.keyboard.press("Alt+ArrowDown")  # undo the swap: the state saved for the reload is a pass
    box.get_by_role("button", name="Check").click()
    expect(box.locator(".parsons-result")).to_have_text("Correct. All lines are in place.")
    print("parsons: keyboard-only solve passes, swapped lines fail with a hint")


def anim(page) -> None:
    box = page.locator("#demo-anim")
    show = box.get_by_role("button", name="Show me the code")
    expect(box.locator(".anim-label")).to_have_text("Frame 1 of 3 — 1 Name the quantity")
    expect(show).to_be_disabled()
    expect(box.locator(".reveal")).to_be_hidden()
    box.get_by_role("button", name="Next").click()
    expect(show).to_be_disabled()
    box.get_by_role("button", name="Next").click()
    expect(box.locator(".anim-label")).to_have_text("Frame 3 of 3 — 3 Combine")
    expect(box.locator(".frame").nth(2)).to_contain_text("multiplies them")
    show.click()
    expect(box.locator(".reveal")).to_be_visible()
    print("anim: reveal disabled until the last frame, code shown after")


def restored(page) -> None:
    page.reload(wait_until="domcontentloaded")
    expect(page.locator("#demo-warmup .quiz-score")).to_have_text("Score: 2/3")
    expect(page.locator("#demo-warmup").get_by_label("[1, 2, 3]")).to_be_checked()
    expect(page.locator(".exercise-cell .cm-editor").first).to_be_visible(timeout=TIMEOUT_MS)
    box = page.locator("#demo-predict")
    expect(box.get_by_label("Your prediction")).to_have_value("50")
    expect(box.get_by_label("Your prediction")).not_to_be_editable()
    expect(box.locator(".predict-verdict")).to_have_text("Compare: what differs?")
    expect(box.locator(".explain")).to_be_visible()
    target = page.locator("#demo-parsons .parsons-list").nth(1).locator(".parsons-line")
    expect(target).to_have_count(3)
    expect(target.nth(1)).to_have_attribute("data-indent", "1")
    expect(page.locator("#demo-parsons .parsons-result")).to_have_text("Correct. All lines are in place.")
    expect(page.locator("#demo-anim").get_by_role("button", name="Show me the code")).to_be_enabled()
    print("reload: quiz, predict, parsons and anim states restored")


def main() -> int:
    url = serve() + PAGE
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page()
        page.add_init_script(LISTEN)
        try:
            page.goto(url, wait_until="domcontentloaded")
            quiz(page)
            predict(page)
            parsons(page)
            anim(page)
            events = page.evaluate("results")
            print(f"events: {events}")
            expected = [("demo-warmup", "quiz", False), ("demo-predict", "predict", False),
                        ("demo-parsons", "parsons", True), ("demo-parsons", "parsons", False),
                        ("demo-parsons", "parsons", True), ("demo-anim", "anim", True)]
            assert [(e["id"], e["kind"], e["passed"]) for e in events] == expected, "unexpected events"
            restored(page)
        except Exception as e:  # report and fail the smoke test
            print(f"FAIL: {type(e).__name__}: {e}")
            return 1
        finally:
            browser.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
