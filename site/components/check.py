# Included verbatim into every check block (see units/README.md); not imported as a module.
# Runs the unit's checks.py (shipped to the Pyodide VFS via the page's `resources:`) against the
# learner's namespace. `label` (the exercise label) is provided by quarto-live's grading env.
# No top-level def: quarto-live evaluates this with separate globals/locals.
import html
import checks

try:
    getattr(checks, "check_" + label)(globals())
    _feedback = {"correct": True, "type": "success", "message": "Correct. Well done!"}
except AssertionError as _err:
    _feedback = {"correct": False, "type": "error", "message": html.escape(str(_err) or "Not yet right.")}
except Exception as _err:
    _feedback = {"correct": False, "type": "error",
                 "message": html.escape(f"Your code raised {type(_err).__name__}: {_err}")}
_feedback
