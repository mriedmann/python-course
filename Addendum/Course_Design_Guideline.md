# Teaching Programming to Adult Technicians – Course Design Guideline

Oct 15, 2026 · @Michael

## Purpose and scope

This guideline sets the rules for designing a short Python addition course for adult technicians with no IT background. It sits beside the learning goals map, which defines **what** is taught; this document defines **how** it is taught and structured.

- **Learners:** working adults in technical presales, process engineering, economics and marketing. Strong domain and spreadsheet skills, no programming experience.
- **Goal of the addition course:** close the gaps in the existing Python course (collections, functions, hidden prerequisites, pandas) and prepare learners for a later data-analytics course.
- **Use:** each principle below is backed by research and turned into a concrete design rule, so lessons can be generated and reviewed against it.

## Evidence-based principles

Novices fail mainly from overload, not lack of ability: working memory holds only a few new items at once. Every principle below reduces that load or makes practice count.

| # | Principle | Evidence | Design rule |
| --- | --- | --- | --- |
| P1 | Limit cognitive load | Working memory is limited; programming stacks many new concepts at once (Sweller, summarised by [Raspberry Pi Foundation](https://www.raspberrypi.org/blog/research-seminar-cognitive-load-subgoal-labels/)) | One new concept per step; no unexplained syntax; reuse one dataset and one notebook layout |
| P2 | Worked examples with subgoal labels | 307 students: subgoal-labelled examples gave more complete answers and deeper understanding; largest gain for at-risk learners (Morrison et al., [same source](https://www.raspberrypi.org/blog/research-seminar-cognitive-load-subgoal-labels/)) | Every new pattern first appears as a full example with named steps, e.g. "load → inspect → clean → aggregate → plot" |
| P3 | Read before write (PRIMM) | Predict, Run, Investigate, Modify, Make; a 2018 study of about 500 learners showed improved outcomes after 8–12 weeks ([PRIMM summary](https://static.raspberrypi.org/files/curriculum/quickreads/11-Pedagogy_Summary_PRIMM_V4_2023.pdf)) | Each unit: predict output of given code → run → trace → change it → write a new one |
| P4 | Parsons problems before blank pages | Learners solved Parsons problems significantly faster than fixing or writing code, with the same learning gains (Ericson, [Georgia Tech](https://hg.gatech.edu/node/603172)) | Use reorder-the-lines tasks as the first exercise of each new pattern |
| P5 | Participatory live coding | Instructor types, narrates, goes slowly, makes and fixes mistakes; learners type along ([Carpentries live-coding tips](https://training.galaxyproject.org//topics/teaching/tutorials/live-coding/tutorial.html)) | No pre-filled solutions in class; show real error messages and how to read them |
| P6 | Relevance and problem focus (andragogy) | Adults need to know why, learn from experience, prefer problem-centred learning with immediate work relevance ([Knowles](https://en.wikipedia.org/wiki/Andragogy)) | Open each unit with a work task it solves; use process, sales and plant data, not toy examples |
| P7 | Retrieval practice | Repeated testing gave about 80% recall after one week vs about 35% when items were dropped from testing (Karpicke & Roediger 2008, [UBC summary](https://applied-science-cisdev.sites.olt.ubc.ca/files/2018/06/retrieval-and-spacing.pdf)) | Short recall quiz at the start of every session; no open-book for these |
| P8 | Spacing, with realistic expectations | Spaced quizzing across 9 STEM courses: +2.06% mean, highly variable between courses ([Bego et al. 2024](https://link.springer.com/article/10.1186/s40594-024-00468-5)) | Revisit each concept in at least 2 later sessions; treat it as cheap insurance, not a cure |
| P9 | Target known misconceptions | Box metaphor for variables helps simple cases but feeds the "variable holds several values" error; label metaphor reduces it ([Hermans et al. 2018](https://www.felienne.com/wp-content/uploads/2018/08/box-label-vars.pdf)) | Teach variables as name tags; add tracing tasks on reassignment, references and copies |
| P10 | Frequent formative checks | Carpentries practice: sticky notes and quick checks to see who is stuck ([live-coding tips](https://training.galaxyproject.org//topics/teaching/tutorials/live-coding/tutorial.html); [Teaching Tech Together](http://teachtogether.tech)) | A check question or mini-task at least every 15 minutes |

## Course structure rules

The course is a chain of short units, each built on the same fixed session pattern. Rules reference the principles above.

**Units and sequence**

- One unit = one concept or pattern, 45–90 minutes including practice (P1). The Carpentries pandas lesson uses 30–90 minute episodes ([example schedule](https://carpentry.library.ucsb.edu/truncated-python-ecology-lesson/)).
- Order units by dependency, as in the learning goals map; never use a construct before its unit (P1, P9).
- Total budget: at most 8 h of raw work, excluding side research and additional reading (R12). Split: collections and functions 2 h, files 1 h, pandas 2.5 h, classes and testing 1.5 h, final task 1 h; see the unit plan in the learning goals map.
- Each unit names its learning goals as verbs learners can check ("filter rows by a condition"), linked to the goal IDs.

**Session pattern**

1. Retrieval warm-up: 3–5 questions on earlier units, no notes (P7, P8).
2. Why: the work problem this unit solves, in one slide or cell (P6).
3. Worked example with subgoal labels, live-coded (P2, P5).
4. Predict and run: learners predict the output of a variant, then run it (P3).
5. Parsons problem on the same pattern (P4).
6. Modify: change the worked example to a new question (P3).
7. Make: a small task on a domain dataset, solution held back (P3, P6).
8. Exit check: one question that exposes the typical misconception (P9, P10).

**Exercises and feedback**

- Progress from reading to writing: predict → trace → reorder → fill gaps → modify → write (P3, P4).
- Include one exercise per unit that starts from a real error message (P5).
- Every exercise has a checkable result, ideally a value or `assert` in the notebook.

**Assessment**

- Formative only during units (P10). Final check = a small end-to-end task on unseen data, graded against the learning goals, not syntax recall.

## Data-analytics track specifics

The pandas part follows the same rules, with one real dataset running through all units so learners spend attention on methods, not new data (P1, P6).

- **One anchor dataset.** A realistic plant or sales export (e.g. hourly process readings, or quotes by customer and product), introduced in unit 1 and reused to the end. Smaller side datasets only for `merge`.
- **Bridge from Excel.** Map each step to the spreadsheet action learners know: filter, sort, `VLOOKUP` → `merge`, pivot table → `pivot_table` / `groupby` (P6).
- **Real-world mess.** Teach `;` delimiters, decimal commas, German date formats and missing values early: these are the first errors learners hit on their own files.
- **Notebook hygiene.** Run cells top to bottom; "Restart & Run All" before handing in; one notebook per unit. Out-of-order execution is a frequent source of confusing results.
- **Pandas misconceptions to target (P9).** Copy vs view (`SettingWithCopyWarning`); methods that return a new object instead of changing in place; `df["col"]` vs `df[["col"]]`; `and` vs `&` in filters.
- **Charts as checks.** Plot after every major step, so learners see whether cleaning or aggregation did what they intended.

## Lesson review checklist

Tick every item before a unit is released.

- [ ] Opens with a work problem the learner recognises (P6)
- [ ] Introduces at most one new concept; all other syntax was taught earlier (P1)
- [ ] Worked example has named subgoals (P2)
- [ ] Contains predict, Parsons, modify and make tasks, in that order (P3, P4)
- [ ] Starts with a retrieval warm-up on earlier units (P7, P8)
- [ ] Has a check at least every 15 minutes and an exit question (P10)
- [ ] Targets at least one named misconception (P9)
- [ ] Uses the anchor dataset; runs cleanly with "Restart & Run All"
- [ ] Every exercise has a checkable result
- [ ] Each learning goal links to a goal ID in the learning goals map

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

Open question: no study found here tests these methods specifically on adult technicians; most evidence comes from university and school learners.
