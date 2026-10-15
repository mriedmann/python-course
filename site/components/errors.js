// Error explanations (docs/04 "Error messages", docs/02 "Exercise ladder and feedback").
// quarto-live 0.2.0 runs a cell with `except Exception as err: print(err, file=sys.stderr)`, so the
// learner only sees str(err). HOOK (installed once, before the first cell runs) redefines `print` in
// Pyodide's __main__, the only namespace that wrapper sees, to print the traceback of the learner's
// own code instead, with source lines. Each stderr output ending in `Type: message` then gets a
// plain-language line above it: the page's `.error-explain` text if one fits, else the first RULES match.
(() => {
  const HOOK = `
import builtins, hashlib, linecache, re, sys, traceback
import pyodide.code

def _pycourse_install():
    run = pyodide.code.eval_code_async
    main = sys.modules["__main__"].__dict__

    def eval_code_async(source, globals=None, locals=None, *args, filename="<exec>", **kwargs):
        # Cell code (own dicts, not __main__) gets a unique file name, so tracebacks show its lines.
        if filename == "<exec>" and globals is not None and globals is not main:
            filename = "<cell-%s>" % hashlib.sha1(source.encode()).hexdigest()[:12]
            linecache.cache[filename] = (len(source), None, source.splitlines(True), filename)
        return run(source, globals, locals, *args, filename=filename, **kwargs)

    def print(*args, **kwargs):
        err = args[0] if len(args) == 1 else None
        if isinstance(err, BaseException) and kwargs.get("file") is sys.stderr:
            te = traceback.TracebackException.from_exception(err)
            frames = [f for f in te.stack if f.filename.startswith("<cell-")]  # hide Pyodide/library frames
            lines = ["Traceback (most recent call last):\\n", *traceback.StackSummary.from_list(frames).format()] if frames else []
            text = "".join(lines + list(te.format_exception_only()))
            args = (re.sub(r'"<cell-[0-9a-f]+>"', '"your code"', text).rstrip(),)
        builtins.print(*args, **kwargs)

    pyodide.code.eval_code_async = eval_code_async
    main["print"] = print

_pycourse_install()
`;

  const TYPES = { str: "text (str)", int: "a whole number (int)", float: "a decimal number (float)",
    NoneType: "None (no value)", list: "a list", dict: "a dictionary (dict)", tuple: "a tuple" };
  const kind = (t) => TYPES[t] || `a ${t}`;
  const NONE = "A function without `return` gives back `None`, and so do methods that change a list in place, such as `.sort()`. Check that the function returns its result.";

  // [exception type, message pattern, explanation(match, ctx)]; the first fitting rule wins.
  // ctx: line (number, "?" if unknown), code (the cell's code), stderr (the full output).
  const RULES = [
    ["NameError", /name '(\w+)' is not defined/, (m, c) => new RegExp(`^\\s*def ${m[1]}\\b`, "m").test(c.code)
      ? `Python runs a cell from top to bottom. Line ${c.line} uses \`${m[1]}\`, but its \`def ${m[1]}\` block has not run at that point, so the function does not exist yet.`
      : `Python does not know the name \`${m[1]}\` in line ${c.line}. Check the spelling and capital letters, put it in quotes if you meant text, and make sure the line that creates \`${m[1]}\` has run (run the cells above first).`],
    ["TypeError", /^(\w+)\(\) missing \d+ required positional arguments?: (.*)/, (m) =>
      `The call to \`${m[1]}()\` gives it too few values: ${m[2]} is missing. Compare the call with the \`def ${m[1]}(...)\` line and pass one value for each parameter.`],
    ["TypeError", /^(\w+)\(\) takes (\d+) positional arguments? but (\d+) (?:was|were) given/, (m) =>
      `The call to \`${m[1]}()\` passes ${m[3]} values, but its \`def\` line has room for only ${m[2]}. Remove the extra value or add a parameter to the \`def\` line.`],
    ["TypeError", /^(\w+)\(\) got an unexpected keyword argument '(\w+)'/, (m) =>
      `\`${m[1]}()\` has no parameter called \`${m[2]}\`. Check the spelling against its \`def\` line.`],
    ["TypeError", /can only concatenate str \(not "(\w+)"\) to str/, (m) =>
      `You tried to join text with ${kind(m[1])} using \`+\`. Python does not convert automatically: use \`str(...)\` to turn the number into text, or an f-string such as \`f"{name}: {value}"\`.`],
    ["TypeError", /unsupported operand type\(s\) for (.+?): '(\w+)' and '(\w+)'/, (m) =>
      (m[2] === "NoneType" || m[3] === "NoneType") ? `One side of \`${m[1]}\` is \`None\`. ${NONE}`
        : `Python cannot use \`${m[1]}\` between ${kind(m[2])} and ${kind(m[3])}. Convert one side first, e.g. \`float(...)\` for text that holds a number.`],
    ["TypeError", /'NoneType' object/, () => `You used a value that is \`None\`. ${NONE}`],
    ["TypeError", /'(\w+)' object is not callable/, (m) =>
      `You put \`(...)\` after ${kind(m[1])}, but only functions can be called. Check whether a variable has the same name as a function.`],
    ["TypeError", /'(\w+)' object is not subscriptable/, (m) =>
      `You used \`[...]\` on ${kind(m[1])}, which has no positions or keys.`],
    ["TypeError", /./, (m, c) => `A value in line ${c.line} has the wrong type for what the line does with it. The last line below names the types involved.`],
    ["IndentationError", /expected an indented block/, (m, c) =>
      `The line after a line ending in \`:\` must be indented (4 spaces), because it belongs to that block. See line ${c.line}.`],
    ["IndentationError", /unexpected indent/, (m, c) =>
      `Line ${c.line} is indented, but nothing above it opens a block. Remove the spaces at its start, or line it up with its neighbours.`],
    ["IndentationError", /./, (m, c) =>
      `The spaces at the start of line ${c.line} do not match the lines around it. Lines in the same block need exactly the same indentation.`],
    ["SyntaxError", /expected ':'/, (m, c) =>
      `Line ${c.line} starts a block (\`if\`, \`for\`, \`def\`, ...) and needs a colon \`:\` at its end. Python read none of the cell, so nothing ran.`],
    ["SyntaxError", /'(.)' was never closed/, (m, c) =>
      `The bracket \`${m[1]}\` in line ${c.line} is opened but never closed. Python read none of the cell, so nothing ran.`],
    ["SyntaxError", /unterminated string literal/, (m, c) =>
      `A text in line ${c.line} starts with a quote mark but has no closing one. Python read none of the cell, so nothing ran.`],
    ["SyntaxError", /Maybe you meant '==' or ':=' instead of '='/, (m, c) =>
      `Line ${c.line} uses \`=\` where Python expects a comparison. \`=\` stores a value, \`==\` compares two values.`],
    ["SyntaxError", /./, (m, c) =>
      `Python could not read line ${c.line}, so none of the cell ran. The \`^\` marks where it got stuck: look for a missing colon, bracket, quote mark or comma there or just before.`],
    ["KeyError", /^'?(.*?)'?$/, (m) =>
      `There is no key \`${m[1]}\` here (in a table: no column \`${m[1]}\`). Check the spelling and capital letters against the keys or column names, e.g. with \`print(row.keys())\`.`],
    ["IndexError", /./, () =>
      "You asked for a position that does not exist. Positions start at 0, so a list of 5 items has positions 0 to 4; `len(...)` tells you how many there are."],
    ["ValueError", /invalid literal for int\(\) with base 10: (.*)/, (m) =>
      `\`int()\` turns text such as \`'42'\` into a whole number, but ${m[1]} is not one. Clean the text first, or use \`float()\` for decimals.`],
    ["ValueError", /could not convert string to float: (.*)/, (m) =>
      `\`float()\` cannot read ${m[1]} as a number. Python expects a dot as decimal mark: replace a comma first, e.g. \`text.replace(",", ".")\`.`],
    ["ValueError", /(.*)/, (m, c) => /^\s*raise ValueError\b/m.test(c.stderr)
      ? `Your code refused a value on purpose: its \`raise ValueError\` line ran. The reason is: "${m[1]}". Check the value you passed in.`
      : `The value has the right type but cannot be used here: "${m[1]}". Check the value going into line ${c.line}.`],
    ["ZeroDivisionError", /./, (m, c) =>
      `Line ${c.line} divides by zero. A count or total can be 0 (for example an empty list); check it with \`if\` before you divide.`],
    ["AttributeError", /'NoneType' object has no attribute/, () => `You used a value that is \`None\`. ${NONE}`],
    ["AttributeError", /'(\w+)' object has no attribute '(\w+)'/, (m) =>
      `${kind(m[1])[0].toUpperCase() + kind(m[1]).slice(1)} has no \`.${m[2]}\`. Check the spelling, and check that the value is of the type you expect.`],
    ["AttributeError", /(.*)/, (m) => `That name after the dot does not exist: ${m[1]}. Check the spelling.`],
    ["FileNotFoundError", /No such file or directory: (.*)/, (m) =>
      `Python cannot find the file ${m[1]}. The path is relative to the working folder: check the folder and the spelling, e.g. \`data/quotes.csv\`.`],
    ["UnicodeDecodeError", /./, () =>
      "The file is not saved as UTF-8 text. Files exported from older Windows programs, such as Excel, often use the cp1252 encoding: open them with `encoding=\"cp1252\"`, e.g. `pd.read_csv(path, encoding=\"cp1252\")`."],
    ["ModuleNotFoundError", /No module named '([\w.]+)'/, (m) =>
      `There is no module called \`${m[1]}\` here. Check the spelling (e.g. \`pandas\`, \`matplotlib.pyplot\`); this course has the standard library, pandas, matplotlib and requests.`],
  ];

  // Text with `code` spans -> DOM nodes, without innerHTML (the message is learner data).
  function render(p, text) {
    text.split("`").forEach((part, i) => p.append(i % 2 ? Object.assign(document.createElement("code"), { textContent: part }) : part));
  }

  function explain(stderr) {
    const out = stderr.querySelector("code") || stderr;
    const text = out.textContent.trimEnd();
    const last = text.split("\n").pop();
    const m = last.match(/^([A-Za-z_]\w*(?:Error|Exception|Interrupt|Exit|Iteration)): ?(.*)$/);
    if (!m || stderr.previousElementSibling?.classList.contains("error-help")) return;
    const [, type, message] = m;
    const lines = [...text.matchAll(/File "your code", line (\d+)/g)];
    const cell = stderr.closest(".exercise-cell, .cell");
    const editor = cell?.querySelector(".cm-content");
    const ctx = { line: lines.length ? lines[lines.length - 1][1] : "?", stderr: text,
      code: editor ? editor.innerText : (cell?.querySelector("pre.sourceCode")?.innerText || "") };
    const p = document.createElement("p");
    p.className = "error-help";
    p.setAttribute("aria-live", "polite");
    const own = [...document.querySelectorAll(".error-explain")].find((d) =>
      d.dataset.exception === type && message.includes(d.dataset.match || ""));
    if (own) {
      own.querySelectorAll(":scope > p").forEach((q, i) => p.append(i ? " " : "", ...q.cloneNode(true).childNodes));
    } else {
      const rule = RULES.find(([t, re]) => t === type && re.test(message));
      const r = rule ? message.match(rule[1]) : null;
      render(p, rule ? rule[2](r, ctx) : `Python stopped with a ${type}. The last line below says what went wrong; the lines above it show where in your code.`);
    }
    stderr.before(p);
  }

  function installHook() {
    const proto = window._exercise_ojs_runtime.PyodideEvaluator.prototype;
    const evaluate = proto.evaluate;
    let ready;
    proto.evaluate = async function (...args) {
      ready ||= this.pyodide.runPythonAsync(HOOK).catch(console.error);
      await ready;
      return evaluate.apply(this, args);
    };
  }
  // live-runtime.js is a module script: it has run by DOMContentLoaded.
  if (window._exercise_ojs_runtime) installHook();
  else document.addEventListener("DOMContentLoaded", installHook);

  const scan = (node) => {
    if (node.matches(".cell-output-stderr")) explain(node);
    node.querySelectorAll(".cell-output-stderr").forEach(explain);
  };
  new MutationObserver((mutations) => mutations.forEach((m) => m.addedNodes.forEach((n) => n.nodeType === 1 && scan(n))))
    .observe(document.body, { childList: true, subtree: true });
  scan(document.body);
})();
