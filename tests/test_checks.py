"""Run every unit's reference solutions against its hidden checks under CPython.

Convention (site/units/README.md): solution.py holds one section per exercise, each starting with a
`# exercise: <label>` line; checks.py defines `check_<label>(ns)`; optional setup.py is the hidden
setup code. Each exercise runs in a fresh namespace (setup, then its solution), like quarto-live.
"""

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
UNITS = sorted(p.parent for p in (ROOT / "site" / "units").glob("*/solution.py"))
MARKER = re.compile(r"^# exercise: (\w+)\s*$", re.MULTILINE)


def solutions(unit: Path) -> dict[str, str]:
    parts = MARKER.split((unit / "solution.py").read_text(encoding="utf-8"))
    return dict(zip(parts[1::2], parts[2::2]))  # parts[0] is the text before the first marker


def load_checks(unit: Path):
    spec = importlib.util.spec_from_file_location(f"checks_{unit.name}", unit / "checks.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exercises():
    for unit in UNITS:
        for label, code in solutions(unit).items():
            yield pytest.param(unit, label, code, id=f"{unit.name}:{label}")


@pytest.mark.parametrize("unit", UNITS, ids=lambda u: u.name)
def test_every_check_has_a_solution(unit):
    checks = {name[len("check_"):] for name in dir(load_checks(unit)) if name.startswith("check_")}
    assert checks == set(solutions(unit)), "check_<label> functions and solution sections differ"


@pytest.mark.parametrize("unit,label,code", list(exercises()))
def test_solution_passes_check(unit, label, code, monkeypatch):
    monkeypatch.chdir(ROOT)  # setup code reads data/ by relative path, as in the browser
    ns: dict = {}
    setup = unit / "setup.py"
    if setup.exists():
        exec(compile(setup.read_text(encoding="utf-8"), str(setup), "exec"), ns)
    exec(compile(code, f"{unit / 'solution.py'}:{label}", "exec"), ns)
    getattr(load_checks(unit), f"check_{label}")(ns)
