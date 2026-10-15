# Course Plan

15 Oct 2026 · Turns the learning goals (`01`) and the teaching guideline (`02`) into a sequence of
units with durations, datasets and misconceptions. This is the document content authors work from.

## Requirements

| ID | Requirement | Reason |
| --- | --- | --- |
| R1 | Audience: adults with a technical or business background, strong spreadsheet skills, no programming experience, little IT background | Who the course is for |
| R2 | Standalone and complete: starts from zero, every goal group G0–G11 has at least one unit, no prior course is assumed | Decision of 15 Oct 2026; replaces the earlier "addition course" scope |
| R3 | Bottleneck emphasis: G4 Collections (two units) and G5 Functions (longest unit) get the most practice and are retrieved in at least two later warm-ups each | Every group from level 3 on needs them |
| R4 | Cross-cutting skills X1–X8 are taught explicitly, each before its first use | They were unexplained prerequisites in the original course |
| R5 | A full files unit: relative paths, `with open`, `csv`, decimal commas, encodings, `try/except` | Prerequisite for pandas; where learners' own exports first break |
| R6 | pandas is a core track: load, inspect, clean, transform, group/pivot, merge, export, plot | Entry requirement of the follow-up data-analytics course |
| R7 | Real-world data formats throughout: `;` delimiter, decimal comma, `dd.mm.yyyy`, missing values, one Windows-1252 file | Learners' Excel exports look like this |
| R8 | Domain examples only: the Fluvia quote book, product catalogue, customer list and plant readings; no toy data | Adult learners need immediate work relevance (P6) |
| R9 | Format: one browser lesson page per unit, a Make notebook in the browser workspace, and small `.py` projects for modules and tests | Lesson pages carry the pattern; notebooks and projects mirror real work |
| R10 | Traceability: every unit names goal IDs, skill IDs, misconception IDs, duration and the units its warm-up retrieves | Generating, linting and reviewing content against the catalogue |
| R11 | Final task on an unseen dataset: from CSV to cleaned data, a chart and a written conclusion, self-checked | Proves readiness for the data-analytics course |
| R12 | Time budget: 10 h 00 of planned learner work time; measured 9–11 h in the pilot is acceptable | Fixed by the course owner on 15 Oct 2026 (was 8 h for the addition course) |
| R13 | Classes (G9) and unit testing (G11) stay in scope | Needed for the follow-up course's project work |
| R14 | Self-paced: every unit can be completed alone in the browser; every exercise auto-checks; no step requires a trainer | Decision of 15 Oct 2026 |
| R15 | Original content: all text, code and data are written new; data is artificial and CC0; nothing is copied from the original course notebooks | Copyright and privacy |
| R16 | Zero install, no account: open a link and learn; progress stays in the browser | Platform promise (see `04`) |

## Unit plan

Seventeen units, U0–U16, in dependency order. "Pattern" is full (8 steps) or light (6 steps) as
defined in the teaching guideline. Durations are planned learner work time including exercises.

| # | Unit | Min | Pattern | Goals | Covers | Misconception | Data |
| --- | --- | --- | --- | --- | --- | --- | --- |
| U0 | Welcome and tour | 15 | light, no warm-up | G0 | What a page, a cell and the workspace are; Run and Stop; `print`; comments; notebook vs script; how checks and hints work | M16 | none |
| U1 | Variables and numbers | 40 | full | G1 | Assignment as a name tag; reassignment, `+=`; `int`, `float`, `str`, `bool`, `type()`; `+ - * / // % **`; float inaccuracy, `round`; `int()`/`float()`/`str()`; `input()` (recognise) | M1, M10 | pump duty point: flow, head, power (inline values) |
| U2 | Text | 30 | full | G1, X1–X3 | f-strings with `:.2f` and `:.1%`; `.strip .lower .upper .replace .split .join`; slicing; `len`, `in` | M6 | product and customer names (inline) |
| U3 | Decisions | 30 | full | G2 | Comparisons; `if/elif/else`; indentation; `and`, `or`, `not`; separate `if`s vs `elif` | M2, M3, M5 | discount rule by segment and quantity |
| U4 | Loops | 40 | full | G3 | `for` with `range`; `for item in items` (preview); accumulator pattern; `while`; `break`, `continue`; Stop button; nested loops (read) | M4, M3 | quote values of one month (inline list) |
| U5 | Lists and tuples: a list is a column | 40 | full | G4 | Create, index, negative index, slice; `append insert extend remove del`; `len sum min max sorted in`; tuples, unpacking; reference vs copy | M7 | first 20 quote values and quantities (setup cell) |
| U6 | Dictionaries and sets: a dict is a lookup table | 40 | full | G4 | Key access, `.get`, add/update/delete; `.items()` loop; nested data; list of dicts as a table; dict of dicts as catalogue; sets and set operations; choosing a collection; `deepcopy` | M7 | first 20 quotes as list of dicts; products as dict by ID (setup cell) |
| U7 | Functions: a reusable formula | 45 | full | G5, X4 | `def`, call, order of execution; parameters vs arguments; `return` vs `print`, `None`; defaults and keyword arguments; scope; `raise ValueError`; docstring; `*args` (recognise) | M8, M9 | `quote_value(row)`, `discount_class(pct)` on the quote list |
| U8 | Files, CSV, encodings and errors | 40 | full | G7 | Relative paths, `os.path.exists`, `os.listdir`; `with open`; read and write text; `csv.DictReader`/`csv.writer` with `delimiter=";"`; decimal comma to float; `encoding="cp1252"`; `try/except FileNotFoundError, ValueError` | M10 | `quotes.csv`, `customers.csv` |
| U9 | Comprehensions | 25 | light | G8, X7 | Loop ↔ comprehension; filter; `a if c else b`; `enumerate`; dict comprehension; `any`/`all` with a generator | M7 (revisited: a comprehension builds a new list) | quote list from U8 |
| U10 | Modules, packages and the terminal | 25 | light | G6, X8 | `import` forms; `math`, `random`, `datetime`; own module `quote_tools.py` from U7 functions; `__main__` guard and `main()`; `%pip` vs `pip`, `requirements.txt`; `cd`, `python file.py` (recorded demo) | M9 (revisited: import runs the module once) | `quote_tools.py` project |
| U11 | pandas I: load, inspect, clean | 45 | full | G10 | `read_csv(sep, decimal, encoding)`; `head info describe shape dtypes`; column and row selection; masks with `&`/`|`; `sort_values`; `.str.strip().str.capitalize()`; `to_datetime`; `drop_duplicates`; `isna fillna dropna`; outliers found with a plot | M11, M12 | `quotes.csv`, `customers.csv` |
| U12 | pandas II: derive, group, pivot, merge, export, plot | 45 | full | G10 | Derived column `value_eur`; `groupby().agg`; `pivot_table`; monthly totals via `dt.month`/`resample`; `merge` with products and customers; `concat`; `to_csv`, `to_excel`; `df.plot` bar and line with labels and date axis | M13, M14 | all three quote-book files |
| U13 | Web data: requests and JSON | 25 | light | G10 | `requests.get`, `status_code`, `.json()`; nested JSON; `params`; API keys and limits (concept); DataFrame from JSON; snapshot fallback | M10 (revisited: JSON values vs text) | exchange rates to convert quote values to CZK/HUF/CHF; snapshot in `data/api/` |
| U14 | Classes: an equipment datasheet | 40 | full | G9, X5, X6 | `class Pump`; `__init__`, `self`, `__str__`; state-changing method; `@property` with validation; `@classmethod` from a CSV row; class vs instance attributes; inheritance `ServicePackage(Product)`; `__add__` (recognise) | M9 (class vs instance: which code runs when) | `products.csv` |
| U15 | Unit testing | 35 | full | G11 | Why tests; `unittest.TestCase`; `test_` methods; `assertEqual assertAlmostEqual assertTrue assertIn assertRaises`; edge cases; `tests/` folder; run in the workspace; terminal command (recognise) | M15 | tests for `quote_tools.py` (U7/U10) and `Pump` (U14) |
| U16 | Final task: pump station energy check | 40 | Make only | all | Load, clean and filter `pump_station_readings.csv`; compute kWh/m³ per pump per month; chart; one-paragraph conclusion; self-check asserts on the key numbers | M16 | `pump_station_readings.csv` (unseen) |

**Total: 600 min = 10 h 00** (R12).

| Level | Units | Time |
| --- | --- | --- |
| 0–1 Basics | U0–U4 | 2 h 35 |
| 2 Organising data and code | U5–U10 | 3 h 35 |
| 3 Real data | U11–U13 | 1 h 55 |
| 4 Classes and tests | U14–U15 | 1 h 15 |
| Final task | U16 | 0 h 40 |

Order notes:

- Text (U2) comes before decisions so that every later unit can print results with f-strings.
- Collections are split into two 40-minute units because they are the biggest conceptual jump
  (R3). Both end with a reference-vs-copy check (M7).
- Comprehensions (U9) follow files (U8) so the comprehension exercises filter real rows.
- Modules (U10) sit directly before pandas so the `import` habit is fresh.
- Web data (U13) is short and self-contained; if an API is unavailable the snapshot keeps the unit working.

## Retrieval map (P8)

Each warm-up draws questions from at least two earlier units. The map guarantees that every goal group
is retrieved in at least two later units.

| Unit | Warm-up retrieves |
| --- | --- |
| U1 | U0 |
| U2 | U1 |
| U3 | U1, U2 |
| U4 | U2, U3 |
| U5 | U1, U4 |
| U6 | U4, U5 |
| U7 | U3, U5, U6 |
| U8 | U2, U6, U7 |
| U9 | U4, U5, U7 |
| U10 | U7, U8 |
| U11 | U6, U8, U9 |
| U12 | U7, U11 |
| U13 | U6, U8, U11 |
| U14 | U7, U10, U12 |
| U15 | U7, U9, U14 |
| U16 | (none; the task itself retrieves U8, U11, U12) |

## Dataset use by unit

All data is artificial and documented in `data/README.md`. The anchor dataset is the quote book of
*Fluvia Process Systems GmbH*, a fictional maker of pumps, heat exchangers, agitators and valves.
Learners play an analyst in presales and later look at a customer's plant data.

| File | Role | Rows | Encoding | First seen | Used in |
| --- | --- | --- | --- | --- | --- |
| `quotes.csv` | Anchor: one row per quote line, Jan 2023 – Dec 2025 | 1,073 | UTF-8 | U5 (as a list, via setup cell) | U5–U12, U15 |
| `products.csv` | Catalogue with flow, head, power, material, list price | 24 | UTF-8 | U6 (as a dict) | U6, U12, U14 |
| `customers.csv` | Customers in AT, DE, CH, IT, CZ, HU, SK, SI | 36 | Windows-1252 | U8 | U8, U11, U12 |
| `data/api/*.json` | Snapshots of the web APIs used in U13 (to be generated) | – | UTF-8 | U13 | U13 |
| `pump_station_readings.csv` | Unseen: hourly SCADA export, 2 pumps, Q1 2025 | 4,320 | UTF-8 | U16 | U16 only |

Patterns the exercises lead learners to find (verified against the generated files on 15 Oct 2026):

- 47.7% of decided quotes are won; higher discounts win more often, long lead times less often.
- Win rate by region: CEE 41%, DACH 49%, South 51%.
- Quotes dip in August and December, peak in October–November, and grow about 8% a year.
- Key accounts get about 12% discount vs about 5% for standard customers.
- Final task: PU-02's specific energy rises from 0.177 to 0.189 kWh/m³ (about +7%) from January to
  March 2025; PU-01 stays at 0.173. The expected conclusion is to inspect PU-02.

Deliberate mess for cleaning exercises (counts verified): 25 inconsistent status spellings, 40 missing
discounts, 3 prices typed 10× too high, 4 zero quantities, 6 duplicate rows, 15 sales-rep names with a
trailing space; in the readings a 30-hour power-meter outage, 8 pressure spikes and a 6-hour
maintenance window.

## Final task (U16)

The learner receives `pump_station_readings.csv` and this brief: "The water works suspects one of its
two pumps is wearing. Show whether that is true." Expected steps, each covered by an earlier unit:

1. Load with `sep=";"`, `decimal=","`, parse `timestamp` with `format="%d.%m.%Y %H:%M"` (U11).
2. Keep rows with `state == "RUN"`, drop rows with blank `power_kw`, drop pressure readings of
   `0.00` and `99.90` (U11).
3. Compute specific energy per pump per month as the sum of `power_kw` divided by the sum of
   `flow_m3h` (U12).
4. Plot one line per pump over the three months (U12).
5. Write three sentences: what the chart shows, which pump to inspect, what data would confirm it.

Self-check: hidden asserts on the number of rows kept, PU-01's March value (0.173 ± 0.002) and
PU-02's March value (0.189 ± 0.002). The written conclusion is not auto-marked; a model answer is
shown after the asserts pass.

## Deliberately out of scope

Kept out to protect the 10-hour budget. Each item is at most mentioned as "(recognise)" where it
appears in the goals catalogue.

- Writing `*args`/`**kwargs`, lambda functions, generators, type hints
- Operator overloading beyond reading `__add__`
- `@staticmethod`, multiple inheritance, abstract classes
- Virtual environments, packaging, Git
- Regular expressions, dates beyond `to_datetime` and monthly grouping
- Statistics beyond `describe`, machine learning, interactive dashboards
