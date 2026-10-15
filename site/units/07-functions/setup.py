# Hidden setup for U7: `quotes` (the first 20 quote lines as a list of dicts) and `products`
# (the product catalogue as a dict by product_id), with numbers already converted.
# Runs in the browser (data/ is in the Pyodide VFS via `resources:`) and in the CPython tests
# (run from the repository root).
import csv


def _number(text):
    # Decimal comma to float; an empty field (missing value) becomes None.
    text = text.strip()
    return float(text.replace(",", ".")) if text else None


with open("data/quotes.csv", encoding="utf-8", newline="") as _f:
    quotes = list(csv.DictReader(_f, delimiter=";"))[:20]
for _q in quotes:
    _q["quantity"] = int(_q["quantity"])
    _q["unit_price_eur"] = _number(_q["unit_price_eur"])
    # The first 20 rows have no blank discount; one would count as "no discount" (0.0) here.
    _q["discount_pct"] = _number(_q["discount_pct"]) or 0.0
    _q["lead_time_weeks"] = int(_q["lead_time_weeks"])
    _q["status"] = _q["status"].strip().capitalize()
    _q["sales_rep"] = _q["sales_rep"].strip()

with open("data/products.csv", encoding="utf-8", newline="") as _f:
    products = {}
    for _p in csv.DictReader(_f, delimiter=";"):
        for _col in ("flow_m3h", "head_m", "power_kw", "list_price_eur"):
            _p[_col] = _number(_p[_col])
        products[_p["product_id"]] = _p
del csv, _f, _q, _p, _col, _number
