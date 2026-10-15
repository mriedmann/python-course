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
CORE = ["pyodide.mjs", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"]
EXTRAS = ["micropip", "pyodide-http", "ipython"]  # installed by quarto-live (live.lua setupPyodide); only list
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


def get(name: str, sha: str | None) -> bool:
    """Download `name` unless present with matching hash. Returns True if downloaded."""
    dest = OUT / name
    if dest.exists() and (sha is None or sha256(dest) == sha):
        return False
    with urllib.request.urlopen(BASE + name) as r:
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
    print(f"{len(jobs)} files in {OUT.relative_to(ROOT)}, {downloaded} downloaded ({len(wheels)} wheels)")


if __name__ == "__main__":
    main()
