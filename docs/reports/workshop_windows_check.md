# Workshop package: Windows check (P2-10)

Not verifiable on Linux: the real Windows run, SmartScreen behaviour, the batch file's port
fallback and browser auto-open. Check once on a standard Windows 10/11 laptop (no admin, no Python)
with the zip from the `deploy.yml` workflow artifact `python-course-workshop`.

1. Copy the zip to a USB stick, then to the laptop; right-click > Extract All (or run from the stick).
2. Double-click `start-course.bat`. Expect: a console window with "Close this window to stop the
   course", no admin prompt, no Windows Firewall prompt, and the default browser opening
   `http://127.0.0.1:8765/`. If SmartScreen warns, "More info" > "Run anyway" works as the README says.
3. Disconnect from the network. Open Unit 7: the first Python cell becomes ready; run a cell and
   the pandas smoke page (`/smoke/pandas.html`) shows `SMOKE pandas rows=1073 ...`.
4. Start a second copy: it should pick port 8766 and print that address (port fallback).
5. Close the console window: the page stops responding. Re-open and confirm learner progress is
   still there (same port, same browser).

Record the Windows version, browser and any deviation in the G-B report.
