"""Download Pyodide 0.28.1 core files and the wheels the site needs into site/pyodide/ (gitignored).

Usage:  uv run python tools/fetch_pyodide.py

Packages = `pyodide.packages` in site/_quarto.yml + the ones quarto-live always installs (EXTRAS),
plus their dependencies from pyodide-lock.json. Files already present with the right sha256 are skipped.
"""

import hashlib
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

VERSION = "0.28.1"  # keep equal to the version pinned in site/_quarto.yml
BASE = f"https://cdn.jsdelivr.net/pyodide/v{VERSION}/full/"
CORE = ["pyodide.mjs", "pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"]
EXTRAS = ["micropip", "pyodide-http", "ipython"]  # installed by quarto-live (live.lua setupPyodide); only list
# pyodide.js: the classic loader for the JupyterLite kernel (its .mjs path is broken in kernel 0.7.2).
# Pure-Python wheels the JupyterLite kernel installs that Pyodide 0.28.1 does not ship (else piplite asks PyPI);
# they go to site/workspace/pypi/ (gitignored), which site/tools/lite_build.py indexes for piplite.
PYPI = {"comm-0.2.3-py3-none-any.whl": ("https://files.pythonhosted.org/packages/60/97/"
        "891a0971e1e4a8c5d2b20bbe0e524dc04548d2307fee33cdeba148fd4fc7/", "c615d91d75f7f04f095b30d1c1711babd43bdc6419c1be9886a85f2f4e489417")}
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "pyodide"


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.lower())


def site_packages() -> list[str]:
    """`packages:` list under the top-level `pyodide:` key of _quarto.yml (stdlib only, no YAML parser)."""
    text = (ROOT / "site" / "_quarto.yml").read_text()
    block = re.search(r"^pyodide:\n((?:[ \t].*\n?|\n)*)", text, re.M).group(1)
    items = re.search(r"^[ \t]+packages:\n((?:[ \t]+-[ \t]+\S+.*\n?)+)", block, re.M).group(1)
    return [m.group(1) for m in re.finditer(r"-[ \t]+([A-Za-z0-9_.-]+)", items)]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get(name: str, sha: str | None, base: str = BASE, out: Path = OUT) -> bool:
    """Download base + `name` into `out` unless present with matching hash. Returns True if downloaded."""
    dest = out / name
    if dest.exists() and (sha is None or sha256(dest) == sha):
        return False
    with urllib.request.urlopen(base + name) as r:
        data = r.read()
    if sha and hashlib.sha256(data).hexdigest() != sha:
        raise SystemExit(f"sha256 mismatch for {name}")
    dest.write_bytes(data)
    return True


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lock_path = OUT / "pyodide-lock.json"
    if not lock_path.exists():
        get("pyodide-lock.json", None)
    lock = json.loads(lock_path.read_text())["packages"]
    by_name = {norm(k): v for k, v in lock.items()}

    wheels, todo, seen = {}, site_packages() + EXTRAS, set()
    while todo:
        name = norm(todo.pop())
        if name in seen:
            continue
        seen.add(name)
        if name not in by_name:
            raise SystemExit(f"package not in pyodide-lock.json: {name}")
        pkg = by_name[name]
        wheels[pkg["file_name"]] = pkg["sha256"]
        todo += pkg["depends"]

    jobs = {n: None for n in CORE} | wheels
    jobs["pyodide-lock.json"] = None
    with ThreadPoolExecutor(6) as pool:
        downloaded = sum(pool.map(lambda kv: get(*kv), jobs.items()))
    (PIPLITE := ROOT / "site" / "workspace" / "pypi").mkdir(exist_ok=True)
    downloaded += sum(get(name, sha, base, PIPLITE) for name, (base, sha) in PYPI.items())
    print(f"{len(jobs)} + {len(PYPI)} files in {OUT.relative_to(ROOT)}, {downloaded} downloaded ({len(wheels)} wheels)")


if __name__ == "__main__":
    main()
