// Stepper (docs/04 "Learner experience", docs/02 P9 name tags): a "Step through" button next to Run
// on every quarto-live editor. It runs the editor's current code (after the exercise's hidden setup,
// which is not stepped) in the page's own Pyodide under components/stepper.py, in a fresh namespace,
// and shows the snapshots one by one: the line about to run, every frame as a table of name tags,
// the objects they point to (#n: two names with the same #n share one object) and the output so far.
// Keyboard: buttons, the step slider, Left/Right/Home/End anywhere in the panel, Escape closes.
// The text is plain HTML (no canvas), and the status line is announced. A failing run ends with a
// .cell-output-stderr block, which errors.js explains like any cell error.
(() => {
  let pyodide = null; // the page's Pyodide (a Comlink proxy), taken from the first evaluator
  let loaded = null;

  function capture() {
    const proto = window._exercise_ojs_runtime.PyodideEvaluator.prototype;
    for (const name of ["process", "evaluate"]) {
      const original = proto[name];
      proto[name] = function (...args) {
        pyodide ||= this.pyodide;
        return original.apply(this, args);
      };
    }
  }
  if (window._exercise_ojs_runtime) capture(); // live-runtime.js is a module script: run by DOMContentLoaded
  else document.addEventListener("DOMContentLoaded", capture);

  const el = (tag, props = {}, ...kids) => {
    const e = Object.assign(document.createElement(tag), props);
    e.append(...kids);
    return e;
  };

  // Hidden setup code of the cell's exercise (the same script tag quarto-live reads), or "".
  function setupCode(cell) {
    try {
      const decode = window._exercise_ojs_runtime.b64Decode;
      const meta = JSON.parse(decode(document.querySelector(`script[type="${cell.id}-contents"]`).textContent));
      const tag = meta.attr.exercise && document.querySelector(`script[type="exercise-setup-${meta.attr.exercise}-contents"]`);
      return tag ? JSON.parse(decode(tag.textContent)).code : "";
    } catch { return ""; }
  }

  async function trace(code, setup) {
    if (!pyodide) throw new Error("Python is still loading. Try again in a moment.");
    const offset = document.querySelector('meta[name="quarto:offset"]').content;
    loaded ||= fetch(offset + "components/stepper.py")
      .then((r) => { if (!r.ok) throw new Error(`Could not load the stepper (${r.status}).`); return r.text(); })
      .then((src) => pyodide.runPythonAsync(`import sys, types
_pycourse_m = types.ModuleType("pycourse_stepper")
exec(${JSON.stringify(src)}, _pycourse_m.__dict__)
sys.modules["pycourse_stepper"] = _pycourse_m
del _pycourse_m`))
      .catch((e) => { loaded = null; throw e; });
    await loaded;
    // JSON string literals are valid Python string literals: the code reaches Python unchanged.
    return JSON.parse(await pyodide.runPythonAsync(
      `__import__("pycourse_stepper").step_through(${JSON.stringify(code)}, ${JSON.stringify(setup)})`));
  }

  const show = (v, heap) => v.ref ? `${heap[v.ref].type} ${v.ref}` : v.text;
  const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;

  function status(step, i, n, frame) {
    const where = frame.name === "Global" ? "" : ` (inside ${frame.name})`;
    const what = {
      line: `Line ${step.line} runs next${where}.`,
      return: `Line ${step.line}: ${frame.name} returns ${step.value && show(step.value, step.heap)}. Its names vanish after this step.`,
      raise: `Line ${step.line}: an error leaves ${frame.name}.`,
      done: "Finished: every line has run.",
    }[step.event];
    return `Step ${i + 1} of ${n}. ${what}`;
  }

  function frameTable(frame, step, last) {
    const table = el("table", { className: "stepper-frame" },
      el("caption", { textContent: frame.name === "Global" ? "Global names" : `${frame.name} (function call)` }));
    const rows = frame.vars.map(([name, v]) => [name, v]);
    if (last && step.event === "return") rows.push(["Return value", step.value]);
    if (!rows.length) table.append(el("tr", {}, el("td", { colSpan: 2, textContent: "(no names yet)" })));
    for (const [name, v] of rows) {
      table.append(el("tr", {},
        el("th", { scope: "row" }, el("span", { className: "stepper-tag", textContent: name })),
        el("td", { className: v.ref ? "stepper-ref" : "", textContent: `→ ${show(v, step.heap)}` })));
    }
    return table;
  }

  function objectBox(ref, obj, step) {
    const names = step.frames.flatMap((f) => f.vars.filter(([, v]) => v.ref === ref)
      .map(([n]) => f.name === "Global" ? n : `${n} (${f.name})`));
    const what = obj.type === "dict" ? plural(obj.len, "key") : plural(obj.len, "item");
    const box = el("div", { className: "stepper-obj" },
      el("p", { className: "stepper-obj-head", textContent:
        `${obj.type} ${ref} · ${what}${names.length ? ` · names: ${names.join(", ")}` : ""}` }));
    if (!obj.items) {
      box.append(el("p", { className: "stepper-muted", textContent: "From the hidden setup, not expanded." }));
      return box;
    }
    const table = el("table", {});
    obj.items.forEach(([key, v], i) => table.append(el("tr", {},
      el("th", { scope: "row", textContent: key ?? (obj.type.endsWith("set") ? "" : String(i)) }),
      el("td", { className: v.ref ? "stepper-ref" : "", textContent: show(v, step.heap) }))));
    if (obj.len > obj.items.length) {
      table.append(el("tr", {}, el("td", { colSpan: 2, textContent: `… ${obj.len - obj.items.length} more` })));
    }
    box.append(table);
    return box;
  }

  function panel(cell, button, code, result) {
    const steps = result.steps;
    const lines = code.split("\n");
    const btn = (text, label, onclick) => el("button", { type: "button", className: "btn btn-outline-secondary btn-sm", textContent: text, onclick, ...(label && { ariaLabel: label }) });
    const slider = el("input", { type: "range", min: 1, max: Math.max(steps.length, 1), value: 1, ariaLabel: "Step" });
    const counter = el("span", { className: "stepper-count" });
    const live = el("p", { className: "stepper-status", role: "status", ariaLive: "polite" });
    const codeView = el("ol", { className: "stepper-code", ariaLabel: "Your code" },
      ...lines.map((text) => el("li", {}, el("code", { textContent: text || " " }))));
    const state = el("div", { className: "stepper-state" });
    let i = 0;

    function go(to) {
      if (!steps.length) return;
      i = Math.max(0, Math.min(steps.length - 1, to));
      const step = steps[i];
      const frame = step.frames[step.frames.length - 1];
      slider.value = i + 1;
      counter.textContent = `${i + 1} / ${steps.length}`;
      live.textContent = status(step, i, steps.length, frame);
      [...codeView.children].forEach((li, n) => {
        const current = step.event !== "done" && n + 1 === step.line;
        li.classList.toggle("current", current);
        if (current) li.setAttribute("aria-current", "step");
        else li.removeAttribute("aria-current");
      });
      const refs = Object.entries(step.heap);
      state.replaceChildren(
        ...step.frames.map((f, n) => frameTable(f, step, n === step.frames.length - 1)),
        ...(refs.length ? [el("h4", { textContent: "Objects" }), ...refs.map(([ref, obj]) => objectBox(ref, obj, step))] : []),
        el("h4", { textContent: "Printed so far" }),
        el("pre", { className: "stepper-out", textContent: step.out || "(nothing yet)" }));
    }

    const close = () => { box.remove(); button.focus(); };
    const box = el("section", { className: "stepper", ariaLabel: "Step through your code" },
      el("div", { className: "stepper-controls" },
        btn("⏮", "First step", () => go(0)), btn("◀ Back", "", () => go(i - 1)),
        btn("Next ▶", "", () => go(i + 1)), btn("⏭", "Last step", () => go(steps.length - 1)),
        slider, counter, btn("Close", "Close the stepper", close)),
      live, el("div", { className: "stepper-body" }, codeView, state));
    slider.addEventListener("input", () => go(Number(slider.value) - 1));
    box.addEventListener("keydown", (e) => {
      if (e.key === "Escape") return close();
      if (e.target === slider) return; // the slider handles its own arrow keys
      const to = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: steps.length - 1 }[e.key];
      if (to !== undefined) { e.preventDefault(); go(to); }
    });
    if (result.limit) {
      box.append(el("p", { className: "stepper-note", textContent:
        `Stopped after ${result.max_steps} steps: the code may run forever (for example while True). These are the first ${result.max_steps} steps.` }));
    }
    if (result.error) {
      box.append(el("p", { className: "stepper-note", textContent: "After the last step the code stops with an error:" }),
        el("div", { className: "cell-output-stderr" }, el("pre", {}, el("code", { textContent: result.error }))));
    }
    if (!steps.length) live.textContent = "No line ran.";
    go(0);
    return box;
  }

  async function step(cell, button) {
    const view = cell.querySelector(".cm-content")?.cmView?.view;
    if (!view) return;
    const code = view.state.doc.toString();
    const old = cell.querySelector(".stepper");
    const card = cell.querySelector(".exercise-editor");
    const note = (text) => el("section", { className: "stepper", ariaLabel: "Step through your code" },
      el("p", { className: "stepper-status", role: "status", ariaLive: "polite", textContent: text }));
    const waiting = note("Tracing your code …");
    old ? old.replaceWith(waiting) : card.after(waiting);
    button.dataset.busy = "1";
    button.disabled = true;
    try {
      const box = panel(cell, button, code, await trace(code, setupCode(cell)));
      waiting.replaceWith(box);
      box.querySelector(".stepper-controls button:nth-child(3)").focus(); // Next
    } catch (e) {
      waiting.replaceWith(note(`The stepper could not run: ${e.message}`));
    } finally {
      delete button.dataset.busy;
      button.sync();
    }
  }

  function addButton(run) {
    if (run.parentElement.querySelector(".btn-exercise-step")) return;
    const cell = run.closest(".exercise-cell");
    if (!cell) return;
    const button = el("button", { type: "button", textContent: "Step through",
      className: "btn btn-exercise-editor btn-exercise-step btn-outline-dark btn-sm text-nowrap",
      title: "Run the code line by line and see the names and values" });
    // Usable exactly when Run is (Pyodide ready, no cell busy, prediction locked in a predict cell).
    button.sync = () => {
      button.disabled = !!button.dataset.busy || run.classList.contains("disabled") || run.getAttribute("aria-disabled") === "true";
    };
    new MutationObserver(button.sync).observe(run, { attributes: true, attributeFilter: ["class", "aria-disabled"] });
    button.sync();
    button.addEventListener("click", () => step(cell, button));
    run.after(button);
  }

  const scan = () => document.querySelectorAll(".exercise-editor-btn-run-code").forEach(addButton);
  new MutationObserver(scan).observe(document.body, { childList: true, subtree: true });
  scan();
})();
