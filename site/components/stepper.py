# Tracer for components/stepper.js (docs/04 "Stepper", P9 name tags). Runs a cell's code under
# sys.settrace in a fresh namespace and returns a JSON list of snapshots: the line about to run, the
# frames with their learner-visible names, the objects those names point to (by a stable #number, so
# two names on one list share it), and the printed output so far. Hidden setup code runs first, is
# not stepped, and its objects are shown collapsed ("list of 20 items"). Bounded: MAX_STEPS snapshots,
# MAX_ITEMS items per object, MAX_OBJECTS objects per snapshot.
# shortcut: a loop inside a C function (e.g. sum(range(10**12))) cannot be stopped by the step cap;
# upgrade when quarto-live can interrupt Pyodide.
import builtins
import contextlib
import io
import json
import linecache
import sys
import traceback
import types

FILENAME = "<stepper>"
MAX_STEPS, MAX_ITEMS, MAX_OBJECTS, MAX_TEXT = 500, 6, 40, 60
COMPOUND = (list, tuple, dict, set, frozenset)


class StepLimit(BaseException):  # BaseException: the learner's `except Exception` cannot catch it
    pass


def _short(text):
    return text if len(text) <= MAX_TEXT else text[: MAX_TEXT - 1] + "…"


class Tracer:
    def __init__(self, setup_ids):
        self.setup_ids = setup_ids  # ids of objects made by the hidden setup: shown collapsed
        self.labels, self.keep = {}, []  # id -> "#n"; keep refs alive so ids stay unique
        self.steps, self.out = [], io.StringIO()
        self.raising = set()  # frames an exception is leaving: their "return" is not a return

    def label(self, obj):
        if id(obj) not in self.labels:
            self.labels[id(obj)] = f"#{len(self.labels) + 1}"
            self.keep.append(obj)
        return self.labels[id(obj)]

    def value(self, obj, heap, todo):
        if isinstance(obj, COMPOUND):
            ref = self.label(obj)
            if ref not in heap and len(heap) + len(todo) < MAX_OBJECTS:
                todo.append(obj)
            return {"ref": ref}
        if isinstance(obj, (types.FunctionType, type)):
            return {"text": f"{'function' if isinstance(obj, types.FunctionType) else 'class'} {obj.__name__}"}
        if isinstance(obj, types.ModuleType):
            return {"text": f"module {obj.__name__}"}
        if obj is None or isinstance(obj, (bool, int, float, complex, str, bytes, range)):
            return {"text": _short(repr(obj))}
        return {"text": type(obj).__name__}  # e.g. a DataFrame: its repr is too big for a name tag

    def heap(self, roots):
        heap, todo = {}, list(roots)
        while todo:
            obj = todo.pop(0)
            ref = self.label(obj)
            if ref in heap:
                continue
            entry = {"type": type(obj).__name__, "len": len(obj)}
            if id(obj) not in self.setup_ids:
                pairs = list(obj.items()) if isinstance(obj, dict) else list(enumerate(obj))
                if isinstance(obj, (set, frozenset)):
                    pairs = [(None, v) for _, v in pairs]
                entry["items"] = [[None if k is None else _short(repr(k)), self.value(v, heap, todo)]
                                  for k, v in pairs[:MAX_ITEMS]]
            heap[ref] = entry
        return heap

    def snapshot(self, frame, event, arg=None):
        if len(self.steps) >= MAX_STEPS:
            raise StepLimit
        stack = []
        while frame is not None and frame.f_code.co_filename == FILENAME:
            stack.append(frame)
            frame = frame.f_back
        frames, roots, todo = [], [], []
        for f in reversed(stack):
            names = dict(f.f_locals) if f.f_code.co_name != "<module>" else f.f_globals
            shown = [(k, v) for k, v in names.items() if k.isidentifier() and not k.startswith("_")]
            frames.append({"name": "Global" if f.f_code.co_name == "<module>" else f.f_code.co_name,
                           "vars": [[k, self.value(v, {}, todo)] for k, v in shown]})
        roots.extend(todo)
        step = {"line": stack[0].f_lineno, "event": event, "frames": frames, "out": self.out.getvalue()}
        if event == "return":
            todo = []
            step["value"] = self.value(arg, {}, todo)
            roots.extend(todo)
        step["heap"] = self.heap(roots)
        self.steps.append(step)

    def trace(self, frame, event, arg):
        if frame.f_code.co_filename != FILENAME:
            return None  # library code: not stepped
        if event == "exception":
            self.raising.add(frame)
        elif event == "line":
            self.raising.discard(frame)  # caught inside this frame
            self.snapshot(frame, "line")
        elif event == "return" and frame in self.raising:
            self.raising.discard(frame)
            if frame.f_code.co_name != "<module>":
                self.snapshot(frame, "raise")
        elif event == "return" and frame.f_code.co_name != "<module>":
            self.snapshot(frame, "return", arg)
        elif event == "return":
            self.snapshot(frame, "done")
        return self.trace


def _error_text(err):
    te = traceback.TracebackException.from_exception(err)
    frames = [f for f in te.stack if f.filename == FILENAME]  # same format as errors.js
    lines = ["Traceback (most recent call last):\n", *traceback.StackSummary.from_list(frames).format()] if frames else []
    return "".join(lines + list(te.format_exception_only())).replace(f'"{FILENAME}"', '"your code"').rstrip()


def step_through(code, setup=""):
    """Trace `code` (after hidden `setup`) and return the snapshots as a JSON string."""
    ns = {"__name__": "__main__", "__builtins__": builtins}
    result = {"steps": [], "error": None, "limit": False, "max_steps": MAX_STEPS}
    linecache.cache[FILENAME] = (len(code), None, code.splitlines(True), FILENAME)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        try:
            if setup:
                exec(compile(setup, "<setup>", "exec"), ns)
        except Exception as err:
            result["error"] = f"The hidden setup code failed: {type(err).__name__}: {err}"
            return json.dumps(result)
    tracer = Tracer({id(v) for v in ns.values()})
    old = sys.gettrace()
    with contextlib.redirect_stdout(tracer.out), contextlib.redirect_stderr(tracer.out):
        try:
            compiled = compile(code, FILENAME, "exec")
            sys.settrace(tracer.trace)
            exec(compiled, ns)
        except StepLimit:
            result["limit"] = True
        except Exception as err:
            result["error"] = _error_text(err)
        finally:
            sys.settrace(old)
    result["steps"] = tracer.steps
    return json.dumps(result)
