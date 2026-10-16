"""Quarto post-render: build the JupyterLite workspace into <output>/workspace/ (before sw_manifest.py).

Contents (staged in a temp folder, nothing duplicated in git): data/*.csv from the repository,
workspace/projects/ and every units/*/make.ipynb at the same relative path as in the site.
The kernel loads the site's self-hosted Pyodide (workspace/jupyter-lite.json, `pyodideUrl`); the extra wheels
it needs (workspace/pypi/, filled by tools/fetch_pyodide.py) are indexed for piplite by the build itself.

Service workers: the site's sw.js must stay the only cache. JupyterLite registers
workspace/service-worker.js when no worker controls the page, so that file is replaced by a shim that
runs sw.js (which also speaks JupyterLite's drive protocol). And JupyterLite unregisters *all* workers
when "<controller scriptURL>-version" in localStorage differs from its version, so every lab page
presets that key for both workers. shortcut: relies on JupyterLite 0.7 internals, re-check on upgrade
(tools/smoke_workspace.py covers it).
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
OUT = Path(os.environ["QUARTO_PROJECT_OUTPUT_DIR"]).resolve() / "workspace"
LITE = SITE / "workspace"

SHIM = '// Course: run the site service worker (sw.js) with the site root as its root.\nself.SW_ROOT = "../";\nimportScripts("../sw.js");\n'
PRESET = """<script>
  // Course: keep JupyterLite from unregistering the site's service workers (see site/tools/lite_build.py).
  try {
    const root = new URL(document.getElementById("jupyter-config-data").dataset.jupyterLiteRoot + "/", location);
    for (const sw of ["../sw.js", "service-worker.js?enableCache=false"])
      localStorage.setItem(new URL(sw, root).href + "-version", "%s");
  } catch (e) { console.warn(e); }
</script>
"""

with tempfile.TemporaryDirectory() as tmp:
    stage = Path(tmp)
    (stage / "data").mkdir()
    for csv in sorted((SITE.parent / "data").glob("*.csv")):
        shutil.copy(csv, stage / "data")
    shutil.copytree(LITE / "projects", stage / "projects")
    for nb in sorted((SITE / "units").glob("*/make.ipynb")):
        (stage / nb.parent.relative_to(SITE)).mkdir(parents=True)
        shutil.copy(nb, stage / nb.relative_to(SITE))
    shutil.rmtree(OUT, ignore_errors=True)
    for db in LITE.glob(".jupyterlite.doit.db*"):  # doit's task cache: always a full build
        db.unlink()
    subprocess.run(
        ["uv", "run", "--frozen", "jupyter", "lite", "build", "--lite-dir", str(LITE), "--contents", str(stage),
         "--output-dir", str(OUT), "--apps", "lab", "--no-sourcemaps", "--no-unused-shared-packages",
         "--log-level", "WARN"],
        cwd=LITE, check=True, stdout=subprocess.DEVNULL, env=os.environ | {"PYTHONWARNINGS": "ignore"},
    )

for f in OUT.rglob("*.map"):  # --no-sourcemaps keeps the app's own maps (40 MB)
    f.unlink()
(OUT / "service-worker.js").write_text(SHIM)
# CSV files keep their exact bytes (customers.csv is cp1252 on purpose): JupyterLite reads a file as UTF-8 text
# when its type is "text" or its mimetype contains "text", which turns the byte 0xFC into U+FFFD.
config = json.loads((OUT / "jupyter-lite.json").read_text())
config["jupyter-config-data"]["fileTypes"]["csv"]["fileFormat"] = "base64"
(OUT / "jupyter-lite.json").write_text(json.dumps(config, indent=2))
for listing in (OUT / "api" / "contents").rglob("all.json"):
    model = json.loads(listing.read_text())
    for item in model["content"]:
        if item["name"].endswith(".csv"):
            item["mimetype"] = "application/octet-stream"
    listing.write_text(json.dumps(model))
version = config["jupyter-config-data"]["appVersion"]
pages = [p for p in OUT.rglob("index.html") if 'id="jupyter-config-data"' in p.read_text()]
for page in pages:
    html = page.read_text()
    assert html.count("</head>") == 1, page
    page.write_text(html.replace("</head>", PRESET % version + "</head>"))
size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
print(f"workspace: JupyterLite {version}, {len(pages)} pages patched, {size / 1e6:.1f} MB")
