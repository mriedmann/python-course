"""CI gate 3: run every unit's make.ipynb top to bottom ("Restart & Run All") under CPython.

The solution lives in the unit's solution.py, not in a second notebook: each code cell tagged
`exercise:<label>` is replaced by the `# exercise: <label>` section before the run. The notebook
runs in its own folder, so its relative data paths are the ones the workspace uses.
"""

from pathlib import Path

import nbformat
import pytest
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
from test_checks import solutions

NOTEBOOKS = sorted((Path(__file__).resolve().parent.parent / "site" / "units").glob("*/make.ipynb"))


def run(path: Path, solved: bool):
    nb = nbformat.read(path, as_version=4)
    slots = [c for c in nb.cells if any(t.startswith("exercise:") for t in c.metadata.get("tags", []))]
    assert slots, "make.ipynb needs a code cell tagged exercise:<label>"
    if solved:
        for cell in slots:
            label = next(t for t in cell.metadata["tags"] if t.startswith("exercise:")).split(":", 1)[1]
            cell.source = solutions(path.parent)[label]
    client = NotebookClient(nb, kernel_name="python3", timeout=60, resources={"metadata": {"path": str(path.parent)}})
    return nb, client


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.parent.name)
def test_make_notebook_runs_clean_with_solution(path):
    nb, client = run(path, solved=True)
    client.execute()


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.parent.name)
def test_make_notebook_skeleton_fails_at_self_check(path):
    nb, client = run(path, solved=False)
    with pytest.raises(CellExecutionError) as err:
        client.execute()
    assert err.value.ename == "AssertionError"
    failed = [c for c in nb.cells if any(o.get("output_type") == "error" for o in c.get("outputs", []))]
    assert len(failed) == 1 and "check" in failed[0].metadata.get("tags", []), "skeleton must run, the check must fail"
