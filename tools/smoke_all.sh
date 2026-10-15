#!/usr/bin/env bash
# Render the site once, run every browser smoke test, print a PASS/FAIL table. Non-zero if any fails.
cd "$(dirname "$0")/.." || exit 1
[ -n "$SKIP_RENDER" ] || quarto render site >/dev/null || { echo "quarto render failed"; exit 1; }  # CI renders earlier
run() { # name command...
  local name=$1; shift
  local t=$SECONDS
  if "$@" >"/tmp/smoke_$name.log" 2>&1; then echo "PASS $name ($((SECONDS - t)) s)"; else echo "FAIL $name ($((SECONDS - t)) s, log: /tmp/smoke_$name.log)"; fi
}
{
  run browser_demo uv run python tools/smoke_browser.py units/00-demo/ --mechanics
  run browser_u7 uv run python tools/smoke_browser.py units/07-functions/
  run drafts uv run python tools/smoke_drafts.py
  run components uv run python tools/smoke_components.py
  run errors uv run python tools/smoke_errors.py
  run pages uv run python tools/smoke_pages.py
  run offline uv run python tools/smoke_offline.py
  run thirdparty uv run python tools/smoke_thirdparty.py
  run unit_u7 uv run python tools/smoke_unit.py units/07-functions/ \
    --raises "fix_order:is not defined" --predict 'u7-predict:18701.1\nNone'
} | tee /tmp/smoke_table.txt
! grep -q '^FAIL' /tmp/smoke_table.txt
