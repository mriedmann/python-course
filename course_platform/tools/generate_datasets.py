"""Generate the artificial course datasets for the browser Python course.

All companies, people and numbers are fictional. The script uses only the
standard library and a fixed seed, so every run produces identical files.

Usage:  python generate_datasets.py [output_dir]      (default: ../data)

Files written:
  quotes.csv                  anchor dataset: sales quotes 2023-2025 (UTF-8)
  products.csv                side dataset: product catalogue with tech specs (UTF-8)
  customers.csv               side dataset: customer master data (Windows-1252!)
  pump_station_readings.csv   unseen dataset for the final task (UTF-8)

Deliberate "real-world mess" is documented in data/README.md.
"""

import csv
import math
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

SEED = 2026
rng = random.Random(SEED)

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "data"
OUT.mkdir(parents=True, exist_ok=True)


def de_num(x, decimals=2):
    """Format a number the way a German Excel export does: decimal comma."""
    return f"{x:.{decimals}f}".replace(".", ",")


def de_date(d):
    return d.strftime("%d.%m.%Y")


def write_csv(name, header, rows, encoding="utf-8"):
    with open(OUT / name, "w", newline="", encoding=encoding) as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(header)
        w.writerows(rows)


# --------------------------------------------------------------------------
# products.csv
# --------------------------------------------------------------------------
# (category, name stem, flow m3/h, head m, power kW, material, list price EUR)
PRODUCT_SPECS = [
    ("Centrifugal pump", "CP-40", 12, 32, 2.2, "1.4404 stainless", 3850),
    ("Centrifugal pump", "CP-65", 45, 40, 7.5, "1.4404 stainless", 6900),
    ("Centrifugal pump", "CP-80", 90, 50, 18.5, "1.4404 stainless", 11800),
    ("Centrifugal pump", "CP-100", 160, 55, 37.0, "Duplex 1.4462", 21500),
    ("Centrifugal pump", "CP-65H", 40, 38, 7.5, "Hastelloy C-22", 14900),
    ("Magnetic drive pump", "MD-25", 6, 20, 1.1, "PP", 2650),
    ("Magnetic drive pump", "MD-50", 25, 30, 4.0, "PVDF", 5400),
    ("Magnetic drive pump", "MD-80", 60, 35, 11.0, "PVDF", 9600),
    ("Dosing pump", "DP-1", 0.01, 100, 0.09, "PVDF", 980),
    ("Dosing pump", "DP-5", 0.05, 160, 0.18, "1.4571 stainless", 1650),
    ("Dosing pump", "DP-20", 0.2, 100, 0.37, "1.4571 stainless", 2900),
    ("Heat exchanger", "PHE-10", 10, None, None, "1.4404 stainless", 4200),
    ("Heat exchanger", "PHE-40", 40, None, None, "1.4404 stainless", 9800),
    ("Heat exchanger", "PHE-40T", 40, None, None, "Titanium", 17600),
    ("Heat exchanger", "STHE-120", 120, None, None, "Carbon steel", 26400),
    ("Agitator", "AG-200", None, None, 0.75, "1.4404 stainless", 5300),
    ("Agitator", "AG-1000", None, None, 4.0, "1.4404 stainless", 12700),
    ("Agitator", "AG-5000", None, None, 15.0, "Duplex 1.4462", 31800),
    ("Valve", "BV-50", None, None, None, "1.4408 cast stainless", 640),
    ("Valve", "BV-100", None, None, None, "1.4408 cast stainless", 1280),
    ("Valve", "CV-50", None, None, None, "1.4408 cast stainless", 2350),
    ("Valve", "CV-100", None, None, None, "1.4408 cast stainless", 4100),
    ("Service", "SRV-COMM", None, None, None, None, 1450),
    ("Service", "SRV-MAINT", None, None, None, None, 2200),
]
CATEGORY_WORD = {
    "Centrifugal pump": "Centrifugal pump",
    "Magnetic drive pump": "Mag-drive pump",
    "Dosing pump": "Dosing pump",
    "Heat exchanger": "Heat exchanger",
    "Agitator": "Agitator",
    "Valve": "Valve",
    "Service": "Service package",
}
SERVICE_NAMES = {"SRV-COMM": "Commissioning (2 days)", "SRV-MAINT": "Annual maintenance contract"}

products = []
for i, (cat, stem, flow, head, power, mat, price) in enumerate(PRODUCT_SPECS, start=1):
    pid = f"P{i:03d}"
    name = SERVICE_NAMES.get(stem, f"{CATEGORY_WORD[cat]} {stem}")
    launch = date(2015, 1, 1) + timedelta(days=rng.randint(0, 365 * 8))
    products.append(dict(id=pid, stem=stem, name=name, cat=cat, flow=flow, head=head,
                         power=power, mat=mat, price=price, launch=launch))

write_csv(
    "products.csv",
    ["product_id", "product_name", "category", "flow_m3h", "head_m", "power_kw",
     "material", "list_price_eur", "launch_date"],
    [[p["id"], p["name"], p["cat"],
      "" if p["flow"] is None else de_num(p["flow"], 2),
      "" if p["head"] is None else de_num(p["head"], 0),
      "" if p["power"] is None else de_num(p["power"], 2),
      p["mat"] or "", de_num(p["price"], 2), de_date(p["launch"])] for p in products],
)

# --------------------------------------------------------------------------
# customers.csv  (Windows-1252, as many Excel installations save CSV)
# --------------------------------------------------------------------------
CUSTOMER_NAMES = [
    ("Chemiewerk Süd AG", "AT", "Chemicals"), ("Donautal Pharma GmbH", "AT", "Pharma"),
    ("Brauerei Kühnhof", "AT", "Food & Beverage"), ("Wasserverband Unteres Murtal", "AT", "Water treatment"),
    ("Papierfabrik Lindenau", "AT", "Pulp & paper"), ("Alpenmilch eGen", "AT", "Food & Beverage"),
    ("Steirische Lackwerke GmbH", "AT", "Chemicals"), ("Biokraft Weinviertel GmbH", "AT", "Energy"),
    ("Rheinauer Spezialchemie GmbH", "DE", "Chemicals"), ("Hanseatische Pharmawerke AG", "DE", "Pharma"),
    ("Stadtwerke Grünberg", "DE", "Water treatment"), ("Fränkische Molkerei Weißach", "DE", "Food & Beverage"),
    ("Chemiepark Saalfurt GmbH", "DE", "Chemicals"), ("Kunststoffwerk Görlitzer & Söhne", "DE", "Chemicals"),
    ("Zellstoff Nordheide GmbH", "DE", "Pulp & paper"), ("Bayerische Getränke Union", "DE", "Food & Beverage"),
    ("Klärwerk Mittelland", "DE", "Water treatment"), ("Isarchem Feinchemie GmbH", "DE", "Pharma"),
    ("Thurgauer Aromen AG", "CH", "Food & Beverage"), ("Basler Wirkstoff AG", "CH", "Pharma"),
    ("Zürcher Wasserwerke Limmat", "CH", "Water treatment"), ("Ticino Chimica SA", "CH", "Chemicals"),
    ("Chimica Adriatica S.p.A.", "IT", "Chemicals"), ("Caseificio Valsugana", "IT", "Food & Beverage"),
    ("Farmaceutici Lombardi S.r.l.", "IT", "Pharma"), ("Acque Venete Servizi", "IT", "Water treatment"),
    ("Moravská chemie a.s.", "CZ", "Chemicals"), ("Pivovar Šumava", "CZ", "Food & Beverage"),
    ("Vodárny Vltava a.s.", "CZ", "Water treatment"), ("Tisza Vegyipari Zrt.", "HU", "Chemicals"),
    ("Balaton Élelmiszer Kft.", "HU", "Food & Beverage"), ("Duna Gyógyszer Zrt.", "HU", "Pharma"),
    ("Slovchem Bratislava a.s.", "SK", "Chemicals"), ("Tatra Mlieko s.r.o.", "SK", "Food & Beverage"),
    ("Ljubljanske Vode d.o.o.", "SI", "Water treatment"), ("Celjska Kemija d.d.", "SI", "Chemicals"),
]
customers = []
for i, (name, country, industry) in enumerate(CUSTOMER_NAMES, start=1):
    seg = "Key account" if rng.random() < 0.25 else "Standard"
    since = date(2005, 1, 1) + timedelta(days=rng.randint(0, 365 * 18))
    customers.append(dict(id=f"C{i:03d}", name=name, country=country, industry=industry,
                          seg=seg, since=since))

# check every name survives Windows-1252 (Czech/Slovak letters like Š, ň, á do;
# a few Central-European letters do not, those are transliterated)
for c in customers:
    c["name"] = c["name"].encode("cp1252", errors="replace").decode("cp1252")
    assert "?" not in c["name"], c["name"]

write_csv(
    "customers.csv",
    ["customer_id", "customer_name", "country", "industry", "segment", "customer_since"],
    [[c["id"], c["name"], c["country"], c["industry"], c["seg"], de_date(c["since"])]
     for c in customers],
    encoding="cp1252",
)

# --------------------------------------------------------------------------
# quotes.csv  (anchor dataset)
# --------------------------------------------------------------------------
REPS = {"AT": ["Anna Berger", "Lukas Hofer"], "DE": ["Jonas Richter", "Miriam Schulze"],
        "CH": ["Lukas Hofer"], "IT": ["Giulia Rossi"], "CZ": ["Petr Novák"],
        "HU": ["Petr Novák"], "SK": ["Petr Novák"], "SI": ["Giulia Rossi"]}
REGION = {"AT": "DACH", "DE": "DACH", "CH": "DACH", "IT": "South", "SI": "South",
          "CZ": "CEE", "HU": "CEE", "SK": "CEE"}
COMPETITORS = ["Pumpex", "Flowtech Industrie", "AquaMotion", "Hydrova"]
# which product categories each industry tends to ask for (weights)
INDUSTRY_MIX = {
    "Chemicals": {"Centrifugal pump": 4, "Magnetic drive pump": 4, "Dosing pump": 2, "Heat exchanger": 3, "Agitator": 3, "Valve": 4, "Service": 2},
    "Pharma": {"Centrifugal pump": 2, "Magnetic drive pump": 3, "Dosing pump": 4, "Heat exchanger": 2, "Agitator": 4, "Valve": 3, "Service": 2},
    "Food & Beverage": {"Centrifugal pump": 4, "Magnetic drive pump": 1, "Dosing pump": 2, "Heat exchanger": 4, "Agitator": 2, "Valve": 4, "Service": 2},
    "Water treatment": {"Centrifugal pump": 5, "Magnetic drive pump": 1, "Dosing pump": 5, "Heat exchanger": 0, "Agitator": 2, "Valve": 4, "Service": 3},
    "Pulp & paper": {"Centrifugal pump": 5, "Magnetic drive pump": 1, "Dosing pump": 2, "Heat exchanger": 3, "Agitator": 3, "Valve": 4, "Service": 2},
    "Energy": {"Centrifugal pump": 4, "Magnetic drive pump": 1, "Dosing pump": 2, "Heat exchanger": 4, "Agitator": 2, "Valve": 3, "Service": 2},
}
by_cat = {}
for p in products:
    by_cat.setdefault(p["cat"], []).append(p)

# key accounts ask for more quotes
cust_weights = [3 if c["seg"] == "Key account" else 1 for c in customers]
MONTH_FACTOR = {1: 0.8, 2: 0.9, 3: 1.1, 4: 1.0, 5: 1.0, 6: 1.05, 7: 0.85, 8: 0.6,
                9: 1.1, 10: 1.15, 11: 1.2, 12: 0.9}

quote_rows = []
qn = 0
day = date(2023, 1, 2)
end = date(2025, 12, 19)
while day <= end:
    if day.weekday() < 5:
        years = (day - date(2023, 1, 1)).days / 365
        lam = 1.25 * MONTH_FACTOR[day.month] * (1 + 0.08 * years)  # ~8 % growth/yr
        n = sum(1 for _ in range(6) if rng.random() < lam / 6)
        for _ in range(n):
            qn += 1
            c = rng.choices(customers, weights=cust_weights)[0]
            mix = INDUSTRY_MIX[c["industry"]]
            cat = rng.choices(list(mix), weights=list(mix.values()))[0]
            p = rng.choice(by_cat[cat])
            if cat in ("Valve", "Dosing pump"):
                qty = rng.choice([1, 2, 2, 4, 5, 6, 8, 10, 12, 20])
            elif cat == "Service":
                qty = 1
            else:
                qty = rng.choice([1, 1, 1, 2, 2, 3, 4])
            if c["seg"] == "Key account" and cat != "Service":
                qty = max(1, round(qty * rng.uniform(1.0, 2.0)))
            base_disc = 12 if c["seg"] == "Key account" else 5
            disc = max(0, min(30, round(rng.gauss(base_disc, 4))))
            # 2 % price increase per year on list price
            price = p["price"] * (1.02 ** int(years)) * (1 - disc / 100)
            price = round(price * rng.uniform(0.98, 1.02), 2)
            lead = {"Service": rng.randint(2, 6), "Valve": rng.randint(3, 8)}.get(cat, rng.randint(6, 18))
            # win probability rises with discount, falls with long lead times
            p_win = 0.30 + disc * 0.015 - (lead - 10) * 0.01 + (0.1 if c["seg"] == "Key account" else 0)
            age_days = (end - day).days
            if age_days < 60 and rng.random() < 0.7:
                status, decided = "Open", None
            else:
                status = "Won" if rng.random() < p_win else "Lost"
                decided = day + timedelta(days=rng.randint(7, 75))
            competitor = rng.choice(COMPETITORS) if status == "Lost" and rng.random() < 0.6 else ""
            quote_rows.append({
                "quote_id": f"Q{day.year}-{qn:05d}", "quote_date": day, "customer_id": c["id"],
                "product_id": p["id"], "quantity": qty, "unit_price_eur": price,
                "discount_pct": disc, "status": status, "decision_date": decided,
                "sales_rep": rng.choice(REPS[c["country"]]), "region": REGION[c["country"]],
                "lead_time_weeks": lead, "lost_to_competitor": competitor,
            })
    day += timedelta(days=1)

# ---- deliberate mess (documented in README.md) ----
# 1) status spelled inconsistently
for r in rng.sample(quote_rows, 25):
    r["status"] = rng.choice([" Won", "won", "WON", "Lost ", "lost"]) if r["status"] != "Open" else "open"
# 2) missing discount values
for r in rng.sample(quote_rows, 40):
    r["discount_pct"] = None
# 3) unit price typed 10x too high
for r in rng.sample(quote_rows, 3):
    r["unit_price_eur"] = round(r["unit_price_eur"] * 10, 2)
# 4) quantity 0 (placeholder quotes)
for r in rng.sample(quote_rows, 4):
    r["quantity"] = 0
# 5) exact duplicate rows (exported twice)
for r in rng.sample(quote_rows, 6):
    quote_rows.append(dict(r))
# 6) trailing spaces in sales rep names
for r in rng.sample(quote_rows, 15):
    r["sales_rep"] = r["sales_rep"] + " "
quote_rows.sort(key=lambda r: (r["quote_date"], r["quote_id"]))

write_csv(
    "quotes.csv",
    ["quote_id", "quote_date", "customer_id", "product_id", "quantity", "unit_price_eur",
     "discount_pct", "status", "decision_date", "sales_rep", "region", "lead_time_weeks",
     "lost_to_competitor"],
    [[r["quote_id"], de_date(r["quote_date"]), r["customer_id"], r["product_id"], r["quantity"],
      de_num(r["unit_price_eur"]), "" if r["discount_pct"] is None else r["discount_pct"],
      r["status"], "" if r["decision_date"] is None else de_date(r["decision_date"]),
      r["sales_rep"], r["region"], r["lead_time_weeks"], r["lost_to_competitor"]]
     for r in quote_rows],
)

# --------------------------------------------------------------------------
# pump_station_readings.csv  (unseen dataset for the final task)
# --------------------------------------------------------------------------
# Hourly SCADA export of two pumps (duty/standby) in a fictional water works,
# 1 Jan - 31 Mar 2025. Pump PU-02 shows slowly rising specific energy
# (impeller wear), PU-01 is healthy. Includes a sensor outage and spikes.
start = datetime(2025, 1, 1, 0, 0)
hours = 24 * 90
rows = []
for h in range(hours):
    ts = start + timedelta(hours=h)
    # daily demand curve: low at night, peaks morning and evening
    demand = 70 + 25 * math.sin((ts.hour - 6) / 24 * 2 * math.pi) + 10 * math.sin((ts.hour - 17) / 12 * 2 * math.pi)
    demand *= 0.92 if ts.weekday() >= 5 else 1.0
    duty = "PU-01" if (ts.date() - start.date()).days // 7 % 2 == 0 else "PU-02"  # weekly switch
    for pump in ("PU-01", "PU-02"):
        if pump != duty:
            rows.append([ts, pump, 0.0, 0.0, 0.0, 12 + rng.gauss(0, 0.5), "STOP"])
            continue
        flow = max(0.0, demand + rng.gauss(0, 3))
        pressure = 4.2 + 0.004 * flow + rng.gauss(0, 0.05)
        wear = 1 + (0.0012 * h / 24 if pump == "PU-02" else 0)  # up to ~11 % worse
        power = (flow * pressure * 100 / 3600) / 0.72 * wear + rng.gauss(0, 0.2)
        temp = 38 + power * 1.4 + rng.gauss(0, 1.0)
        rows.append([ts, pump, flow, pressure, power, temp, "RUN"])
# maintenance window for PU-01 on 11 Feb 08:00-14:00
for r in rows:
    if r[1] == "PU-01" and datetime(2025, 2, 11, 8) <= r[0] < datetime(2025, 2, 11, 14):
        r[2:5] = [0.0, 0.0, 0.0]
        r[6] = "MAINT"
# sensor outage: power meter blank for 30 h in March
for r in rows:
    if datetime(2025, 3, 3, 6) <= r[0] < datetime(2025, 3, 4, 12):
        r[4] = None
# spikes in the pressure transmitter
for r in rng.sample([r for r in rows if r[6] == "RUN"], 8):
    r[3] = rng.choice([0.0, 99.9])

write_csv(
    "pump_station_readings.csv",
    ["timestamp", "pump_id", "flow_m3h", "discharge_pressure_bar", "power_kw",
     "motor_temp_c", "state"],
    [[r[0].strftime("%d.%m.%Y %H:%M"), r[1], de_num(r[2], 1), de_num(r[3], 2),
      "" if r[4] is None else de_num(r[4], 2), de_num(r[5], 1), r[6]] for r in rows],
)

print(f"wrote {len(products)} products, {len(customers)} customers, "
      f"{len(quote_rows)} quotes, {len(rows)} readings to {OUT}")
