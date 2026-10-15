// Parsons problem (docs/04 step 5). div.parsons holds the solution code block (4 spaces per level)
// and optional pre.distractor blocks. Lines are shuffled deterministically (seeded by the id) into
// "Lines"; the learner builds "Your solution" by drag-and-drop or keyboard. Native HTML only.
(() => {
  const key = (id) => `pycourse:v1:${location.pathname}:${id}`;
  const load = (id) => { try { return JSON.parse(localStorage.getItem(key(id))); } catch { return null; } };
  const save = (id, state) => { try { localStorage.setItem(key(id), JSON.stringify(state)); } catch { /* storage off */ } };
  const report = (id, passed) =>
    document.dispatchEvent(new CustomEvent("pycourse:result", { detail: { id, kind: "parsons", passed } }));
  const MAX_INDENT = 4;
  const KEYS = "Keys: Enter or Space moves a line between the lists, Alt+Up / Alt+Down reorders it, " +
    "Left / Right changes its indentation, Up / Down moves the focus. You can also drag lines; " +
    "where you drop a line horizontally sets its indentation.";

  function el(tag, props = {}, ...children) {
    const e = Object.assign(document.createElement(tag), props);
    e.append(...children);
    return e;
  }

  // Deterministic shuffle: string hash seeds mulberry32, then Fisher-Yates.
  function shuffle(items, seedText) {
    let seed = [...seedText].reduce((h, c) => Math.imul(h ^ c.charCodeAt(0), 16777619), 2166136261);
    const rand = () => {
      seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    const out = [...items];
    for (let i = out.length - 1; i > 0; i--) {
      const j = Math.floor(rand() * (i + 1));
      [out[i], out[j]] = [out[j], out[i]];
    }
    return out;
  }

  const codeLines = (pre) => pre.querySelector("code").textContent.replace(/\n+$/, "").split("\n");

  function setupParsons(box) {
    const id = box.id;
    const pres = [...box.querySelectorAll("pre")];
    const solution = codeLines(pres.find((p) => !p.classList.contains("distractor"))).map((l) => ({
      text: l.trim(), indent: Math.floor((l.length - l.trimStart().length) / 4),
    }));
    const texts = [...solution.map((l) => l.text),
      ...pres.filter((p) => p.classList.contains("distractor")).flatMap(codeLines).map((l) => l.trim())];
    let order = shuffle(texts.map((_, i) => i), id);
    if (order.every((v, i) => v === i)) order.push(order.shift()); // never pre-solved

    const list = () => el("ul", { className: "parsons-list" });
    const source = list();
    const target = list();
    const result = el("p", { className: "parsons-result" });
    result.setAttribute("aria-live", "polite");
    const check = el("button", { type: "button", className: "btn btn-primary", textContent: "Check" });
    source.setAttribute("aria-label", "Lines");
    target.setAttribute("aria-label", "Your solution");
    pres.forEach((p) => (p.closest(".code-copy-outer-scaffold") || p).remove());
    box.append(
      el("div", { className: "parsons-lists" },
        el("div", {}, el("p", { className: "parsons-heading", textContent: "Lines" }), source),
        el("div", {}, el("p", { className: "parsons-heading", textContent: "Your solution" }), target)),
      el("p", { className: "parsons-keys", textContent: KEYS }),
      el("div", { className: "parsons-actions" }, check, result));

    const setIndent = (b, n) => {
      b.dataset.indent = String(Math.max(0, Math.min(MAX_INDENT, n)));
      b.style.setProperty("--indent", b.dataset.indent);
      b.setAttribute("aria-label", `${b.textContent}, ${target.contains(b) ? `indent ${b.dataset.indent}` : "unused"}`);
    };
    const lineButton = (i) => {
      const b = el("button", { type: "button", className: "parsons-line", textContent: texts[i], draggable: true });
      b.dataset.line = String(i);
      return b;
    };
    const place = (b, list, before = null, indent = 0) => {
      list.insertBefore(el("li", {}, b), before);
      setIndent(b, list === target ? indent : 0);
    };
    const move = (b, list, before, indent) => {
      const li = b.parentElement;
      place(b, list, before, indent);
      li.remove();
      b.focus();
      result.textContent = "";
      persist();
    };
    const arrangement = () => ({
      source: [...source.querySelectorAll("button")].map((b) => Number(b.dataset.line)),
      target: [...target.querySelectorAll("button")].map((b) => [Number(b.dataset.line), Number(b.dataset.indent)]),
    });
    let passed = null;
    const persist = () => save(id, { ...arrangement(), passed });

    function grade() {
      const got = arrangement().target.map(([i, indent]) => ({ text: texts[i], indent }));
      const bad = solution.findIndex((l, n) => !got[n] || got[n].text !== l.text || got[n].indent !== l.indent);
      passed = bad === -1 && got.length === solution.length;
      result.className = `parsons-result ${passed ? "pass" : "fail"}`;
      if (passed) result.textContent = "Correct. All lines are in place.";
      else if (bad === -1) result.textContent = `Line ${solution.length + 1} does not belong to the solution.`;
      else if (!got[bad]) result.textContent = `Line ${bad + 1} is missing.`;
      else result.textContent = `Line ${bad + 1} is in the wrong place or wrongly indented.`;
    }

    check.addEventListener("click", () => {
      grade();
      persist();
      report(id, passed);
    });

    box.addEventListener("click", (e) => {
      const b = e.target.closest(".parsons-line");
      if (!b) return;
      if (target.contains(b)) move(b, source, null, 0);
      else move(b, target, null, 0);
    });

    box.addEventListener("keydown", (e) => {
      const b = e.target.closest(".parsons-line");
      if (!b) return;
      const li = b.parentElement;
      const list = li.parentElement;
      const indent = Number(b.dataset.indent);
      const focusNext = (other) => other && other.querySelector("button").focus();
      if (e.altKey && e.key === "ArrowUp" && li.previousElementSibling) move(b, list, li.previousElementSibling, indent);
      else if (e.altKey && e.key === "ArrowDown" && li.nextElementSibling) move(b, list, li.nextElementSibling.nextElementSibling, indent);
      else if (e.key === "ArrowUp") focusNext(li.previousElementSibling);
      else if (e.key === "ArrowDown") focusNext(li.nextElementSibling);
      else if (list === target && (e.key === "ArrowLeft" || e.key === "ArrowRight")) {
        setIndent(b, indent + (e.key === "ArrowRight" ? 1 : -1));
        result.textContent = "";
        persist();
      } else return;
      e.preventDefault();
    });

    let dragged = null;
    box.addEventListener("dragstart", (e) => {
      dragged = e.target.closest(".parsons-line");
      if (dragged) e.dataTransfer.setData("text/plain", dragged.textContent);
    });
    for (const list of [source, target]) {
      list.addEventListener("dragover", (e) => { if (dragged) e.preventDefault(); });
      list.addEventListener("drop", (e) => {
        if (!dragged) return;
        e.preventDefault();
        const over = e.target.closest("li");
        // Drop on the upper half of a line inserts before it, on the lower half after it.
        const r = over && over.getBoundingClientRect();
        const before = over && (e.clientY < r.top + r.height / 2 ? over : over.nextElementSibling);
        const step = parseFloat(getComputedStyle(dragged).fontSize) * 2; // matches --indent step in CSS
        const indent = Math.round((e.clientX - list.getBoundingClientRect().left - step / 2) / step);
        move(dragged, list, before === dragged.parentElement ? before.nextElementSibling : before, indent);
        dragged = null;
      });
    }

    const state = load(id);
    const valid = state && Array.isArray(state.source) && Array.isArray(state.target) &&
      state.source.length + state.target.length === texts.length;
    if (valid) {
      state.source.forEach((i) => place(lineButton(i), source));
      state.target.forEach(([i, indent]) => place(lineButton(i), target, null, indent));
      if (state.passed !== null && state.passed !== undefined) grade();
    } else {
      order.forEach((i) => place(lineButton(i), source));
    }
  }

  document.querySelectorAll("div.parsons[id]").forEach(setupParsons);
})();
