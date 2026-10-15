// Predict and run (docs/04 step 4, docs/02 "Predictions are committed"). div.predict wraps one
// quarto-live {pyodide} editor (no autorun by default in quarto-live 0.2.0). Its Run button and
// Ctrl/Cmd+Enter both dispatch an "input" event with detail.commit on the cell container; a capture
// listener on the wrapper swallows those until the prediction is locked. The first run after the
// lock is compared with the prediction and decides pass/fail (later edits cannot change it).
(() => {
  const key = (id) => `pycourse:v1:${location.pathname}:${id}`;
  const load = (id) => { try { return JSON.parse(localStorage.getItem(key(id))); } catch { return null; } };
  const save = (id, state) => { try { localStorage.setItem(key(id), JSON.stringify(state)); } catch { /* storage off */ } };
  const report = (id, passed) =>
    document.dispatchEvent(new CustomEvent("pycourse:result", { detail: { id, kind: "predict", passed } }));

  // Strip each line, drop empty trailing lines.
  const normalise = (text) => text.split("\n").map((l) => l.trim()).join("\n").replace(/\n+$/, "");

  function el(tag, props = {}, ...children) {
    const e = Object.assign(document.createElement(tag), props);
    e.append(...children);
    return e;
  }

  function setupPredict(box) {
    const id = box.id;
    const state = load(id) || {};
    const textarea = el("textarea", { id: `${id}-text`, rows: 3, spellcheck: false, className: "form-control" });
    const lock = el("button", { type: "button", className: "btn btn-primary", textContent: "Lock prediction", disabled: true });
    const status = el("p", { className: "predict-status" });
    const result = el("div", { className: "predict-result" });
    result.setAttribute("aria-live", "polite");
    box.prepend(el("div", { className: "predict-form" },
      el("label", { htmlFor: textarea.id, textContent: "Your prediction: what will Python print?" }),
      textarea, el("div", { className: "predict-actions" }, lock, status)));
    box.append(result);

    let pending = false; // a locked run has started and its output is not compared yet
    let timer;

    function syncRunButton() {
      box.querySelectorAll(".exercise-editor-btn-run-code").forEach((b) => {
        if (state.locked) b.removeAttribute("aria-disabled");
        else b.setAttribute("aria-disabled", "true");
      });
    }

    function applyLock() {
      textarea.value = state.prediction;
      textarea.readOnly = true;
      lock.disabled = true;
      box.classList.add("locked");
      status.textContent = "Prediction locked. Now run the cell.";
      syncRunButton();
    }

    function showResult() {
      const pre = (text) => el("pre", { textContent: text || "(nothing)" });
      result.replaceChildren(
        el("p", { className: `predict-verdict ${state.passed ? "pass" : "fail"}`,
          textContent: state.passed ? "Your prediction matches." : "Compare: what differs?" }),
        el("div", { className: "predict-compare" },
          el("div", {}, el("strong", { textContent: "You predicted" }), pre(state.prediction)),
          el("div", {}, el("strong", { textContent: "Python printed" }), pre(state.printed))));
    }

    function compare() {
      const outputs = [...box.querySelectorAll(".exercise-cell-output")];
      state.printed = outputs.map((o) => o.innerText).join("\n");
      state.passed = normalise(state.prediction) === normalise(state.printed);
      pending = false;
      save(id, state);
      showResult();
      report(id, state.passed);
    }

    textarea.addEventListener("input", () => { lock.disabled = textarea.value.trim() === ""; });
    lock.addEventListener("click", () => {
      state.prediction = textarea.value;
      state.locked = true;
      save(id, state);
      applyLock();
    });

    box.addEventListener("input", (e) => {
      if (!e.detail || !e.detail.commit) return; // typing in the editor
      if (!state.locked) {
        e.stopImmediatePropagation();
        e.preventDefault();
        status.textContent = "Lock your prediction first.";
        textarea.focus();
      } else if (!("printed" in state)) {
        pending = true;
      }
    }, true);

    // quarto-live renders the cell asynchronously and replaces the output after each run.
    new MutationObserver(() => {
      syncRunButton();
      const busy = box.querySelector(".exercise-editor-eval-indicator:not(.d-none)");
      clearTimeout(timer);
      if (pending && !busy && box.querySelector(".exercise-cell-output")) timer = setTimeout(compare, 300);
    }).observe(box, { childList: true, subtree: true, attributes: true, attributeFilter: ["class"] });

    if (state.locked) applyLock();
    if ("printed" in state) showResult();
  }

  document.querySelectorAll("div.predict[id]").forEach(setupPredict);
})();
