"""Quarto post-render: write sw-manifest.json (all site files) and stamp the build hash into sw.js."""

import hashlib
import json
import os
from pathlib import Path

out = Path(os.environ["QUARTO_PROJECT_OUTPUT_DIR"])
skip = {"sw.js", "sw-manifest.json"}
files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file() and p.name not in skip)
digest = hashlib.sha256()
for f in files:
    digest.update(f.encode() + (out / f).read_bytes())
build = digest.hexdigest()[:12]

(out / "sw-manifest.json").write_text(json.dumps({"build": build, "files": files}))
sw = out / "sw.js"
sw.write_text(sw.read_text().replace("__BUILD__", build))
print(f"sw-manifest.json: {len(files)} files, build {build}")
