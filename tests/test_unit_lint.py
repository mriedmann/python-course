"""Lint every unit page against the machine-checkable Unit Definition of Done (docs/02, docs/04).

Messages are written for the unit author. `lint()` takes the page text, so the negative tests below
break a copy of the real U7 by string replacement and assert that the specific rule fires.
"""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
UNITS = sorted(p.parent for p in (ROOT / "site" / "units").glob("*/index.qmd") if "unit:" in p.read_text(encoding="utf-8").split("\n---")[0])
REQUIRED = "unit title duration_min pattern goals misconceptions retrieves new_concept steps".split()
FULL = "warmup why worked predict parsons modify make exit".split()
LIGHT = "warmup why worked predict modify exit".split()
CHECK_STEPS = {"warmup", "predict", "parsons", "modify", "make", "exit"}  # worked counts only with an exercise


def catalogue() -> set[str]:
    text = (ROOT / "docs" / "01_learning_goals.md").read_text(encoding="utf-8")
    return set(re.findall(r"^### (G\d+) ", text, re.M)) | set(re.findall(r"^\| ([XM]\d+) \|", text, re.M))


def ids(text: str) -> set[str]:  # "G1, X1–X3" -> G1, X1, X2, X3
    out = set(re.findall(r"\b[GXM]\d+\b", text))
    for p, a, b in re.findall(r"([GXM])(\d+)\s*[–-]\s*[GXM]?(\d+)", text):
        out |= {f"{p}{n}" for n in range(int(a), int(b) + 1)}
    return out


def plan() -> tuple[dict, dict]:
    """(unit plan rows, retrieval map rows) from docs/03, keyed by unit ID."""
    rows, retrieval = {}, {}
    for line in (ROOT / "docs" / "03_course_plan.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not re.fullmatch(r"U\d+", cells[0]) or not line.startswith("|"):
            continue
        if len(cells) >= 8:
            rows[cells[0]] = dict(min=int(cells[2]), pattern=cells[3], goals=ids(cells[4]), miscs=ids(cells[6]))
        elif len(cells) == 2:
            retrieval[cells[0]] = set(re.findall(r"U\d+", cells[1])) if not cells[1].startswith("(none") else set()
    return rows, retrieval


def span(text: str, start: re.Pattern) -> str:
    m = start.search(text)
    return "" if not m else re.split(r"^## ", text[m.start():], maxsplit=1, flags=re.M)[0]


def lint(text: str, checks_py: str) -> list[str]:
    """All Definition-of-Done violations of one unit page."""
    fm_text = text.split("---")[1]
    fm = yaml.safe_load(fm_text)
    errs = [f"front matter: missing key '{k}'" for k in REQUIRED if k not in fm]
    if errs:
        return errs
    uid, known = fm["unit"], catalogue()
    rows, retrieval = plan()
    for kind in ("goals", "misconceptions"):
        for i in fm[kind]:
            if i not in known:
                errs.append(f"front matter: {kind} id {i} is not in docs/01_learning_goals.md")
    for u in fm["retrieves"]:
        if u not in rows:
            errs.append(f"front matter: retrieves {u}, which is not a unit in docs/03")
    row = rows.get(uid)
    if not row:
        return errs + [f"front matter: unit {uid} has no row in the docs/03 unit plan"]
    pattern = row["pattern"].lower()
    kind = "make" if pattern.startswith("make") else "light" if pattern.startswith("light") else "full"
    if fm["duration_min"] != row["min"]:
        errs.append(f"duration_min {fm['duration_min']} differs from the course plan ({row['min']})")
    if fm["pattern"] != kind:
        errs.append(f"pattern '{fm['pattern']}' differs from the course plan ('{kind}')")
    if set(fm["retrieves"]) != retrieval.get(uid, set()):
        errs.append(f"retrieves {fm['retrieves']} differs from the retrieval map {sorted(retrieval.get(uid, []))}")
    if not row["goals"] <= set(fm["goals"]):
        errs.append(f"goals {fm['goals']} lack course-plan goals {sorted(row['goals'] - set(fm['goals']))}")
    if not row["miscs"] <= set(fm["misconceptions"]):
        errs.append(f"misconceptions {fm['misconceptions']} lack course-plan ids {sorted(row['miscs'] - set(fm['misconceptions']))}")
    if not fm["misconceptions"]:
        errs.append("front matter: name at least one misconception")

    steps = fm["steps"]
    lo, hi = {"full": (30, 45), "light": (0, 25), "make": (0, 45)}[kind]
    if not lo <= fm["duration_min"] <= hi:
        errs.append(f"duration_min {fm['duration_min']} is outside the {kind} pattern limit {lo}-{hi}")
    if sum(steps.values()) != fm["duration_min"]:
        errs.append(f"steps add up to {sum(steps.values())} min, duration_min is {fm['duration_min']}")

    expected = ["make"] if kind == "make" else [s for s in (FULL if kind == "full" else LIGHT) if not (s == "warmup" and "no warm-up" in pattern)]
    found = re.findall(r"^## .*\{[^}]*#(\w+)[^}]*\.step[^}]*\}\s*$|^## .*\{[^}]*\.step[^}]*#(\w+)[^}]*\}\s*$", text, re.M)
    found = [a or b for a, b in found]
    if found != expected:
        errs.append(f"step sections (H2 with {{#id .step}}) are {found}, the {kind} pattern needs {expected}")
    if list(steps) != expected:
        errs.append(f"front matter steps keys {list(steps)} must match the sections {expected}")

    if "warmup" in expected:
        warm = span(text, re.compile(r"^::: \{\.quiz [^}]*\.warmup", re.M))
        qs = re.findall(r'^::: \{\.question ([^}]*)\}', warm, re.M)
        tags = [(re.search(r'tags="([^"]*)"', q) or [None, ""])[1].split() for q in qs]
        if not 3 <= len(qs) <= 5:
            errs.append(f"warm-up has {len(qs)} questions, it needs 3-5 (and a '.quiz .warmup' div)")
        if not all(tags):
            errs.append("warm-up: every question needs tags=\"...\"")
        seen = {t for ts in tags for t in ts if t in fm["retrieves"]}
        if len(seen) < min(2, len(fm["retrieves"])):
            errs.append(f"warm-up tags cover units {sorted(seen)}; draw on at least two units of retrieves {fm['retrieves']}")

    # spacing: a check ends each check step; no more than 15 min between two checks
    sections = re.split(r"^## .*\{[^}]*\.step[^}]*\}", text, flags=re.M)[1:]
    t, last, worst = 0, 0, 0
    for name, body in zip(expected, sections):
        t += steps.get(name, 0)
        if name in CHECK_STEPS or (name == "worked" and "#| exercise:" in body):
            worst, last = max(worst, t - last), t
    worst = max(worst, t - last)
    if worst > 15:
        errs.append(f"{worst} min pass between two checks (limit 15); add a check or shorten a step")

    for label in dict.fromkeys(re.findall(r"#\| exercise: (\w+)", text)):
        blocks = re.findall(r"```\{pyodide\}\n((?:#\|.*\n)+)", text)
        mine = [b for b in blocks if f"exercise: {label}\n" in b]
        for flag in ("setup", "check"):
            if sum(f"#| {flag}: true" in b for b in mine) != 1:
                errs.append(f"exercise {label}: needs exactly one '#| {flag}: true' block")
        if len(mine) != 3:
            errs.append(f"exercise {label}: has {len(mine)} pyodide blocks, it needs editor + setup + check")
        h, s = (len(re.findall(rf'\{{\.{k} exercise="{label}"\}}', text)) for k in ("hint", "solution"))
        if h != 3 or s != 1:
            errs.append(f"exercise {label}: has {h} hints and {s} solutions, it needs exactly 3 and 1")
        if not re.search(rf"^def check_{label}\(", checks_py, re.M):
            errs.append(f"exercise {label}: checks.py has no check_{label}")

    if "exit" in expected:
        ex = span(text, re.compile(r"^::: \{\.quiz [^}]*\.exit", re.M))
        tagged = {t for q in re.findall(r'^::: \{\.question [^}]*tags="([^"]*)"', ex, re.M) for t in q.split()}
        if not tagged & set(fm["misconceptions"]):
            errs.append(f"exit check: no question is tagged with a unit misconception {fm['misconceptions']}")
    return errs


def read(unit: Path):
    return (unit / "index.qmd").read_text(encoding="utf-8"), (unit / "checks.py").read_text(encoding="utf-8")


@pytest.mark.parametrize("unit", UNITS, ids=lambda u: u.name)
def test_unit_meets_definition_of_done(unit):
    assert lint(*read(unit)) == []


U7 = ROOT / "site" / "units" / "07-functions"
# (what to break in U7, expected fragment of the message)
DEFECTS = {
    "missing key": ("new_concept:", "x_new_concept:", "missing key 'new_concept'"),
    "unknown goal": ("goals: [G5, X4]", "goals: [G5, X4, G99]", "G99 is not in docs/01"),
    "unknown retrieves": ("retrieves: [U3, U5, U6]", "retrieves: [U3, U5, U6, U99]", "U99"),
    "retrieval map": ("retrieves: [U3, U5, U6]", "retrieves: [U3, U5]", "retrieval map"),
    "duration vs plan": ("duration_min: 45", "duration_min: 40", "differs from the course plan"),
    "steps sum": ("modify: 9", "modify: 8", "steps add up to 44"),
    "plan goals": ("goals: [G5, X4]", "goals: [G5]", "lack course-plan goals"),
    "step order": ("## Predict and run {#predict .step}", "## Predict and run {#predict2 .step}", "step sections"),
    "warm-up tags": ('tags="U3 G2"', 'tags="G2"', "tags cover"),  # applied to all U3/U5 tags, see below
    "hint count": ('::: {.hint exercise="retype"}', '::: {.hintx exercise="retype"}', "exercise retype: has 2 hints"),
    "solution count": ('::: {.solution exercise="retype"}', '::: {.solutionx exercise="retype"}', "0 solutions"),
    "check block": ("#| check: true", "#| checkx: true", "exactly one '#| check: true'"),
    "exit misconception": ('tags="M9"', 'tags="M3"', "exit check"),
}


@pytest.mark.parametrize("name", DEFECTS)
def test_defect_is_reported(name):
    old, new, message = DEFECTS[name]
    text, checks = read(U7)
    assert text.count(old) >= 1, f"fixture drifted: {old!r} not in U7"
    if name == "warm-up tags":  # leave only one retrieved unit (U6) in the tags
        text = text.replace('tags="U3 G2"', 'tags="G2"').replace('tags="U5 G4"', 'tags="G4"')
        errs = lint(text, checks)
    else:
        errs = lint(text.replace(old, new, 1), checks)
    assert any(message in e for e in errs), errs


def test_missing_check_function():
    text, checks = read(U7)
    errs = lint(text, checks.replace("def check_retype(", "def check_retypo("))
    assert any("no check_retype" in e for e in errs), errs


def test_warmup_too_small():
    text, checks = read(U7)
    cut = re.sub(r'(?s)::: \{\.question tags="U6 G4"( answer="0")?\}.*?\n:::\n', "", text)
    assert any("warm-up has" in e for e in lint(cut, checks))


def test_check_spacing():
    text, checks = read(U7)
    broken = text.replace("duration_min: 45", "duration_min: 80", 1).replace("modify: 9", "modify: 44", 1)
    assert any("between two checks" in e for e in lint(broken, checks))
