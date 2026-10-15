# Hidden setup for the unit's exercises: the first 20 Fluvia quote lines as a list of dicts.
# Runs in the browser (data/quotes.csv is in the Pyodide VFS via `resources:`) and in CPython
# tests (run from the repository root).
import csv

with open("data/quotes.csv", encoding="utf-8", newline="") as _f:
    quotes = list(csv.DictReader(_f, delimiter=";"))[:20]
for _q in quotes:
    _q["quantity"] = int(_q["quantity"])
    _q["unit_price_eur"] = float(_q["unit_price_eur"].replace(",", "."))
    _q["discount_pct"] = float(_q["discount_pct"].replace(",", "."))
del csv, _f, _q
