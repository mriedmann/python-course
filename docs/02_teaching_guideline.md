# Teaching Guideline

15 Oct 2026 · Defines **how** units are built. Applies to every unit in the course plan (`03`) and is
enforced by the Unit Definition of Done at the end of this document. Goal, skill and misconception
IDs refer to the learning goals catalogue (`01`).

## Starting point

- **Learners** are adults with strong domain and spreadsheet skills and no programming experience.
- **Mode** is self-paced in the browser. Nobody is in the room, so every explanation, check and hint
  must work without a trainer. Instructor-led workshops are an optional add-on (see instructor mode
  in the platform spec), never a precondition.
- **Failure mode to design against:** overload, not lack of ability. Working memory holds only a few
  new items; programming stacks many at once. Every rule below reduces load or makes practice count.

## Evidence-based principles

| # | Principle | Evidence | Design rule |
| --- | --- | --- | --- |
| P1 | Limit cognitive load | Working memory is limited; programming stacks many new concepts at once (Sweller, summarised by the [Raspberry Pi Foundation](https://www.raspberrypi.org/blog/research-seminar-cognitive-load-subgoal-labels/)) | One new concept per unit; no syntax before its unit; one dataset and one page layout throughout |
| P2 | Worked examples with subgoal labels | 307 students: subgoal-labelled examples gave more complete answers and deeper understanding, largest gain for at-risk learners (Morrison et al., same source) | Every new pattern first appears as a complete example with named steps, e.g. "load → inspect → clean → aggregate → plot" |
| P3 | Read before write (PRIMM) | Predict, Run, Investigate, Modify, Make; a 2018 study with about 500 learners showed improved outcomes ([PRIMM summary](https://static.raspberrypi.org/files/curriculum/quickreads/11-Pedagogy_Summary_PRIMM_V4_2023.pdf)) | Each unit: predict the output of given code → run → trace → modify it → make something new |
| P4 | Parsons problems before blank pages | Learners solved Parsons problems significantly faster than fixing or writing code, with the same learning gains (Ericson, [Georgia Tech](https://hg.gatech.edu/node/603172)) | A reorder-the-lines task is the first writing exercise of each new pattern |
| P5 | Type along, see real errors | Participatory live coding: slow, narrated, with mistakes made and fixed ([Carpentries practice](https://training.galaxyproject.org//topics/teaching/tutorials/live-coding/tutorial.html)) | Self-paced form: the worked example is a step-through animation the learner retypes, not a finished cell; every unit has one exercise that starts from a real traceback |
| P6 | Relevance and problem focus (andragogy) | Adults need to know why, learn from experience and prefer problem-centred learning with immediate work relevance ([Knowles](https://en.wikipedia.org/wiki/Andragogy)) | Each unit opens with a work task it solves; all examples use the Fluvia quote book and plant data, never toy data |
| P7 | Retrieval practice | Repeated testing gave about 80% recall after a week vs about 35% for dropped items (Karpicke & Roediger 2008, [UBC summary](https://applied-science-cisdev.sites.olt.ubc.ca/files/2018/06/retrieval-and-spacing.pdf)) | A short recall quiz starts every unit; code cells are hidden while it is open |
| P8 | Spacing, with realistic expectations | Spaced quizzing across 9 STEM courses: +2.06% mean, highly variable ([Bego et al. 2024](https://link.springer.com/article/10.1186/s40594-024-00468-5)) | Every goal group reappears in the warm-up of at least two later units; cheap insurance, not a cure |
| P9 | Target known misconceptions | The box metaphor for variables feeds the "holds several values" error; the label metaphor reduces it ([Hermans et al. 2018](https://www.felienne.com/wp-content/uploads/2018/08/box-label-vars.pdf)) | Variables are name tags; every unit names one misconception from the register and tests it in the exit check |
| P10 | Frequent formative checks | Carpentries practice: quick checks show who is stuck ([Teaching Tech Together](http://teachtogether.tech)) | An auto-checked question or task at least every 15 minutes; a progress bar shows the steps |

Open question on evidence: no study found tests these methods specifically on adult technicians;
most evidence comes from university and school learners. The pilot (roadmap phase 4) is the check.

## Unit pattern

A unit teaches one concept or pattern in 15–45 minutes. Every unit follows the same step sequence,
so learners always know where they are. Each step maps to one page component (platform spec).

| Step | Name | What happens | Learner output | Principle |
| --- | --- | --- | --- | --- |
| 1 | Retrieval warm-up | 3–5 questions on earlier units; code cells hidden | Quiz score | P7, P8 |
| 2 | Why | The work problem this unit solves, in one paragraph and one spreadsheet screenshot | none | P6 |
| 3 | Worked example | Step-through animation of the pattern with subgoal labels, then the learner retypes it into a live cell | Running cell | P2, P5 |
| 4 | Predict and run | A variant of the example; the learner locks in a prediction before the cell can run | Prediction vs output | P3 |
| 5 | Parsons problem | Shuffled lines of the pattern, dragged into order and indentation, then run | Pass/fail | P4 |
| 6 | Modify | Editable copy of the example with a new question; hidden checks | Pass/fail | P3 |
| 7 | Make | Skeleton or blank cell on the anchor dataset; hidden checks; solution held back until three hints are used | Pass/fail | P3, P6 |
| 8 | Exit check | One question that exposes the unit's named misconception | Auto-marked | P9, P10 |

**Full and light pattern.** Units of 30 minutes or more use all eight steps. Units of 25 minutes or
less use the light pattern: steps 1, 2, 3, 4, 6 and 8 (no Parsons, no Make). The welcome unit U0 has
no warm-up; the final task U16 is a single Make with a self-check.

Time guide for a 40-minute full unit: warm-up 3, why 2, worked example 8, predict 4, Parsons 5,
modify 6, make 10, exit 2. Any unit that needs more than 45 minutes is split.

**Sequencing rules**

- One new concept per unit (P1). If a second concept is unavoidable, it is marked in the front
  matter and the review decides whether to split.
- Never use a construct before its unit. Cross-cutting skills X1–X8 are taught in their listed unit
  before any later unit uses them.
- Each unit names its learning goals as checkable verbs ("filter rows by a condition") with goal IDs.
- Each unit's warm-up draws from at least two earlier units, chosen so that every goal group is
  retrieved in at least two later units over the course (P8). The course plan records the mapping.

## Exercise ladder and feedback

Exercises progress from reading to writing: predict → trace → reorder → fill gaps → modify → write
(P3, P4). Rules for every exercise:

- **Checkable result.** Every exercise ends in a value or state the checker can assert. "Look at the
  output" is not a check.
- **Checks are Python asserts** with a learner-facing message, e.g.
  `assert total == 42.5, "Check the unit: the price is per piece, multiply by quantity"`.
- **Feedback ladder.** A failed check shows one plain-language sentence first, then up to three hints
  revealed one at a time, then the solution. Hints name the next subgoal, not the code.
- **Error messages.** Tracebacks are shown in full, with a plain-language explanation above them.
  One exercise per unit starts from a real error that the learner must read and fix (P5).
- **Predictions are committed.** The predict step locks the prediction before the run button works,
  so the learner compares, not rationalises.
- **No solution before effort.** The solution opens only after the third hint has been used or two
  failed attempts, whichever comes first.
- **Warm-up and exit questions** are multiple choice or short answer with one correct answer; each
  is tagged with the goal or misconception ID it tests.

## Misconception targeting (P9)

- Each unit names at least one ID from the misconception register (`01`) in its front matter.
- The worked example or predict step makes the misconception visible (e.g. `b = a; a.append(4);
  print(b)`), the explanation gives the correct model, the exit check tests it.
- Explanations use the agreed models: variables are name tags; a list of dicts is a table; a
  DataFrame method returns a new object; a filter mask is an AutoFilter.
- Tracing tasks (step through the stepper and write down the state) are the standard tool for
  reference-vs-copy, scope and run-order misconceptions.

## Data track rules

The pandas units (U11–U13) and the final task follow the same unit pattern, with extra rules:

- **One anchor dataset.** The Fluvia quote book (`data/quotes.csv`) runs from U5 to U15. Side
  datasets (`products.csv`, `customers.csv`) appear only for `merge`, encodings and classes. The
  final task uses a dataset the learner has never seen.
- **Data before files.** Units before U8 cannot read files yet. They receive the data as a Python
  list or list of dicts from a hidden setup cell, described in the text as "the first 20 rows of the
  quote book". Learners meet the CSV file itself in U8.
- **Bridge from spreadsheets.** Every pandas step is introduced against the spreadsheet action the
  learner knows (see bridges table in `01`).
- **Real-world mess early.** `;` delimiters, decimal commas, `dd.mm.yyyy` dates, Windows-1252 and
  missing values appear in U8 and U11, because these are the first errors learners hit on their own
  exports.
- **Charts as checks.** Plot after every major cleaning or aggregation step so the learner sees
  whether it did what they intended.
- **Notebook hygiene.** Make tasks in the workspace are checked only after "Restart & Run All"
  (M16). One notebook per unit.

## Unit Definition of Done

A unit is released only when every item holds. The CI lint in the platform spec checks the items
marked *(CI)*; a human reviewer checks the rest.

Content

- [ ] Front matter names unit ID, duration, goal IDs, cross-cutting skill IDs, misconception IDs,
      pattern (full/light) and the units its warm-up retrieves *(CI)*
- [ ] Opens with a work problem the learner recognises (P6)
- [ ] Introduces one new concept; all other syntax was taught in an earlier unit (P1)
- [ ] Worked example has named subgoals and a step-through animation (P2, P5)
- [ ] All steps of the unit's pattern are present, in order *(CI)* (P3, P4)
- [ ] Warm-up has 3–5 tagged questions drawn from at least two earlier units *(CI)* (P7, P8)
- [ ] A check occurs at least every 15 minutes of planned time *(CI)* (P10)
- [ ] One exercise starts from a real error message (P5)
- [ ] Exit check tests the named misconception (P9)
- [ ] Uses the anchor dataset or its side datasets; no toy data (P6)
- [ ] Text, code and data are original (R15)

Checks and build

- [ ] Every exercise has a checkable result; hidden checks are asserts with learner-facing messages
- [ ] Every exercise has three hints and a solution; the solution passes its own checks *(CI)*
- [ ] Make notebook runs clean with "Restart & Run All" under CPython and Pyodide *(CI)*
- [ ] Planned duration is within the unit pattern limits and the course plan total *(CI)*
- [ ] Page passes the accessibility checks in the platform spec (keyboard, contrast, no autoplay)

## Sources

- [Reducing the load: ways to support novice programmers](https://www.raspberrypi.org/blog/research-seminar-cognitive-load-subgoal-labels/) – Raspberry Pi Foundation, on Sweller and Morrison et al.
- [PRIMM pedagogy summary](https://static.raspberrypi.org/files/curriculum/quickreads/11-Pedagogy_Summary_PRIMM_V4_2023.pdf) – Raspberry Pi Foundation, 2023
- [Parsons problems dissertation abstract](https://hg.gatech.edu/node/603172) – B. Ericson, Georgia Tech
- [Live coding is a skill](https://training.galaxyproject.org//topics/teaching/tutorials/live-coding/tutorial.html) – Galaxy Training, based on Carpentries practice
- [Andragogy](https://en.wikipedia.org/wiki/Andragogy) – Knowles' six assumptions
- [Retrieval and spacing](https://applied-science-cisdev.sites.olt.ubc.ca/files/2018/06/retrieval-and-spacing.pdf) – Soderstrom, Kerr & Bjork 2016 replication of Karpicke & Roediger 2008
- [Spaced retrieval practice in nine STEM courses](https://link.springer.com/article/10.1186/s40594-024-00468-5) – Bego et al., IJ STEM Ed. 2024
- [Thinking out of the box: metaphors for variables](https://www.felienne.com/wp-content/uploads/2018/08/box-label-vars.pdf) – Hermans et al. 2018
- [Data Analysis and Visualization in Python for Ecologists](https://carpentry.library.ucsb.edu/truncated-python-ecology-lesson/) – Data Carpentry lesson schedule
- [Teaching Tech Together](http://teachtogether.tech) – G. Wilson, 2019
- [futurecoder](https://github.com/alexmojaki/futurecoder) – reference for the hint ladder and predict-the-output design
