"""Build the offline workshop zip: site/_site + a pinned static server for Windows x64.

Usage:  uv run python tools/build_workshop.py        (run `quarto render site` first)
Output: dist/python-course-workshop-<date>.zip; the Linux binary of the same release is cached
in dist/cache/ and only used by tools/smoke_workshop.py (never packaged).
Server: static-web-server (MIT/Apache-2.0, ~7 MB exe, Rust, maintained; serves .wasm as
application/wasm and .mjs as text/javascript; binds to the given --host).
"""
import datetime
import hashlib
import io
import pathlib
import tarfile
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site" / "_site"
DIST = ROOT / "dist"
CACHE = DIST / "cache"
VERSION = "v2.44.1"
BASE = f"https://github.com/static-web-server/static-web-server/releases/download/{VERSION}/static-web-server-{VERSION}-x86_64-"
# sha256 from the release's published static-web-server-v2.44.1-SHA256SUM
WIN = ("pc-windows-msvc.zip", "0ac7ecb75baa1b367b5d9acac36535906d37383a99be1fb64dce8d2f07a2ab8c")
LINUX = ("unknown-linux-gnu.tar.gz", "a71fb43143d0964f82417178fa56d8f6ee4b33f49ddde4b2263d97404fdfbbc4")
PORT = 8765
# Shared by start-course.bat and tools/smoke_workshop.py. {port} is filled in by the caller.
ARGS = ["--host", "127.0.0.1", "--port", "{port}", "--root", "site", "--log-level", "warn"]

README = f"""PYTHON COURSE - OFFLINE WORKSHOP PACKAGE

1. Copy this whole folder (or the zip, then right-click > Extract All) to the laptop, or keep it on the USB stick.
2. Double-click start-course.bat. A black window opens and your browser shows the course.
3. No internet, no installation and no administrator rights are needed. Use Chrome, Edge or Firefox.
4. The first page load takes a few seconds while Python starts in the browser.
5. Only the unit that calls web APIs (U13) needs internet; everything else works offline.
6. If Windows SmartScreen says "Windows protected your PC", click "More info", then "Run anyway".
   If start-course.bat or server\\static-web-server.exe is blocked, right-click it > Properties > Unblock.
7. If the browser does not open, type the address shown in the black window into the address bar
   (normally http://127.0.0.1:{PORT}/ ; the next free port is used if {PORT} is busy).
8. Keep the black window open while teaching. Close this window to stop the course.
9. Learner progress is stored in each browser on that laptop; it does not travel with the USB stick.
10. Server: static-web-server {VERSION} (MIT / Apache-2.0); licences are in the server folder.
"""

BAT = r"""@echo off
setlocal
cd /d "%~dp0"
set PORT={port}
:find
rem No parenthesized block here: cmd expands %PORT% inside ( ) when the block is parsed.
netstat -ano | findstr /R /C:":%PORT% .*LISTENING" >nul
if errorlevel 1 goto found
set /a PORT+=1
if %PORT% LSS {limit} goto find
echo No free port found between {port} and {limit}.
pause
exit /b 1
:found
echo Python course is running at http://127.0.0.1:%PORT%/
echo Close this window to stop the course.
start "" /min cmd /c "ping -n 3 127.0.0.1 >nul & start "" http://127.0.0.1:%PORT%/"
server\static-web-server.exe {args}
pause
"""


def fetch(suffix: str, sha: str) -> bytes:
    cached = CACHE / f"sws-{VERSION}-{suffix}"
    if not cached.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(BASE + suffix, timeout=120) as r:
            cached.write_bytes(r.read())
    data = cached.read_bytes()
    if hashlib.sha256(data).hexdigest() != sha:
        cached.unlink()
        raise SystemExit(f"sha256 mismatch for {suffix}")
    return data


def linux_binary() -> pathlib.Path:
    out = CACHE / f"static-web-server-{VERSION}"
    if not out.exists():
        with tarfile.open(fileobj=io.BytesIO(fetch(*LINUX))) as t:
            member = next(m for m in t.getmembers() if m.name.endswith("/static-web-server"))
            out.write_bytes(t.extractfile(member).read())
        out.chmod(0o755)
    return out


def main() -> None:
    if not (SITE / "index.html").exists():
        raise SystemExit("site/_site missing: run `quarto render site` first")
    linux_binary()
    win = zipfile.ZipFile(io.BytesIO(fetch(*WIN)))
    DIST.mkdir(exist_ok=True)
    out = DIST / f"python-course-workshop-{datetime.date.today():%Y-%m-%d}.zip"
    top = "python-course-workshop/"
    bat = BAT.format(port=PORT, limit=PORT + 20, args=" ".join(ARGS).format(port="%PORT%"))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(SITE.rglob("*")):
            if f.is_file():
                z.write(f, top + "site/" + f.relative_to(SITE).as_posix())
        for name in win.namelist():
            base = name.rsplit("/", 1)[-1]
            if base in ("static-web-server.exe", "LICENSE-MIT", "LICENSE-APACHE"):
                z.writestr(top + "server/" + base, win.read(name))
        z.writestr(top + "start-course.bat", bat.replace("\n", "\r\n"))
        z.writestr(top + "README.txt", README.replace("\n", "\r\n"))
    print(f"{out} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
