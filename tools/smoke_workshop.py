"""Verify the workshop zip on Linux: extract, serve with the same server + args as start-course.bat,
check .wasm/.mjs MIME types, then run the smoke tests against it via --base-url.

Usage:  uv run python tools/smoke_workshop.py [dist/python-course-workshop-<date>.zip]
(run tools/build_workshop.py first). The web (CORS) page needs internet: reported, not failed.
"""
import pathlib
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

from build_workshop import ARGS, CACHE, DIST, VERSION

TOOLS = pathlib.Path(__file__).resolve().parent
SMOKES = [
    ["smoke_unit.py", "units/07-functions/", "--raises", "fix_order:is not defined", "--predict", r"u7-predict:18701.1\nNone"],
    ["smoke_offline.py"],
]


def head(url: str) -> tuple[int, str]:
    with urllib.request.urlopen(urllib.request.Request(url, method="HEAD")) as r:
        return r.status, r.headers.get("content-type", "")


def main() -> int:
    zips = sorted(DIST.glob("python-course-workshop-*.zip"))
    zip_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else zips[-1]
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    failed = False
    with tempfile.TemporaryDirectory() as tmp:
        zipfile.ZipFile(zip_path).extractall(tmp)
        root = pathlib.Path(tmp) / "python-course-workshop"
        for need in ("start-course.bat", "README.txt", "server/static-web-server.exe", "server/LICENSE-MIT", "site/index.html"):
            if not (root / need).exists():
                print(f"FAIL missing in zip: {need}")
                return 1
        server = subprocess.Popen(
            [str(CACHE / f"static-web-server-{VERSION}")] + [a.format(port=port) for a in ARGS], cwd=root
        )
        base = f"http://127.0.0.1:{port}/"
        try:
            for _ in range(50):
                try:
                    head(base)
                    break
                except OSError:
                    time.sleep(0.1)
            wasm = next((root / "site").rglob("*.wasm")).relative_to(root / "site").as_posix()
            mjs = next((root / "site").rglob("*.mjs"), None)
            checks = [(wasm, "application/wasm"), ("sw.js", "javascript")]
            if mjs:
                checks.append((mjs.relative_to(root / "site").as_posix(), "javascript"))
            for path, want in checks:
                status, ctype = head(base + path)
                ok = status == 200 and want in ctype
                failed |= not ok
                print(f"{'ok' if ok else 'FAIL'} {path}: {status} {ctype}")
            for cmd in SMOKES:
                r = subprocess.run([sys.executable, str(TOOLS / cmd[0]), *cmd[1:], "--base-url", base],
                                   capture_output=True, text=True, cwd=TOOLS.parent)
                out = r.stdout + r.stderr
                ok = r.returncode == 0
                print(f"{'ok' if ok else 'FAIL'} {cmd[0]}")
                if not ok:
                    print(out[-1500:])
                failed |= not ok
        finally:
            server.terminate()
    print("FAIL" if failed else "OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
