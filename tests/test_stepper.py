"""The stepper's tracer (site/components/stepper.py) under CPython: frames, shared objects, step cap."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("stepper", ROOT / "site" / "components" / "stepper.py")
stepper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stepper)


def trace(code, setup=""):
    return json.loads(stepper.step_through(code, setup))


def names(step):
    return {f["name"]: [k for k, _ in f["vars"]] for f in step["frames"]}


def test_function_frame_appears_and_vanishes():
    r = trace("def f(row):\n    value = row * 2\n    return value\n\nfirst = f(3)\nprint(first)\n")
    events = [(s["event"], names(s)) for s in r["steps"]]
    ret = next(i for i, (e, _) in enumerate(events) if e == "return")
    assert events[ret][1]["f"] == ["row", "value"] and r["steps"][ret]["value"] == {"text": "6"}
    assert "f" not in events[ret + 1][1] and "first" in events[ret + 1][1]["Global"]
    assert r["steps"][-1]["out"] == "6\n" and r["error"] is None


def test_two_names_share_one_list():
    last = trace("prices = [1200, 950]\nbackup = prices\nprices.append(400)\n")["steps"][-1]
    refs = dict(last["frames"][0]["vars"])
    assert refs["prices"] == refs["backup"] == {"ref": "#1"}
    assert last["heap"]["#1"]["len"] == 3


def test_setup_is_collapsed_and_not_stepped():
    r = trace("n = len(rows)\n", "rows = [{'a': 1}] * 20")
    assert [s["line"] for s in r["steps"]] == [1, 1]
    assert r["steps"][0]["heap"]["#1"] == {"type": "list", "len": 20}


def test_endless_loop_stops_at_cap_and_errors_are_formatted():
    r = trace("while True:\n    pass\n")
    assert r["limit"] and len(r["steps"]) == stepper.MAX_STEPS
    err = trace("x = 1 / 0\n")["error"]
    assert err.startswith('Traceback (most recent call last):\n  File "your code", line 1')
    assert err.endswith("ZeroDivisionError: division by zero")
