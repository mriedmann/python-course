// Step progress bar, exercise results, and progress export/import (docs/04 "Pacing", "Progress").
// Storage: pycourse:v1:<path>:<id> (quiz/predict/parsons/anim, own formats), :exercise:<label> {passed, at},
// :visited:<step>, :complete, :draft:<key>. Everything stays in localStorage; export/import is a local file.
(() => {
  const PREFIX = "pycourse:v1:";
  const MAX_BYTES = 2 * 1024 * 1024;
  const key = (id) => `${PREFIX}${location.pathname}:${id}`;
  const get = (k) => { try { return localStorage.getItem(k); } catch { return null; } };
  const set = (k, v) => { try { localStorage.setItem(k, v); } catch { /* storage off */ } };
  const json = (k) => { try { return JSON.parse(get(k)); } catch { return null; } };
  let storageOk = true;
  try { localStorage.setItem(PREFIX + "probe", "1"); localStorage.removeItem(PREFIX + "probe"); } catch { storageOk = false; }
  const allKeys = () => { try { return Object.keys(localStorage).filter((k) => k.startsWith(PREFIX)); } catch { return []; } };
  const el = (tag, props = {}, ...kids) => { const e = Object.assign(document.createElement(tag), props); e.append(...kids); return e; };

  function exerciseLabel(cellId) {
    try { return JSON.parse(atob(document.querySelector(`script[type="${cellId}-contents"]`).textContent.trim())).attr.exercise || null; }
    catch { return null; }
  }

  // Persist quarto-live grades. A pass is never downgraded by a later fail.
  function onGrade(grade) {
    const cell = grade.closest(".exercise-cell");
    const label = cell && exerciseLabel(cell.id);
    if (!label) return;
    const passed = grade.classList.contains("alert-success");
    if (!passed && (json(key(`exercise:${label}`)) || {}).passed) return;
    set(key(`exercise:${label}`), JSON.stringify({ passed: passed || (json(key(`exercise:${label}`)) || {}).passed === true, at: new Date().toISOString() }));
    document.dispatchEvent(new CustomEvent("pycourse:result", { detail: { id: label, kind: "exercise", passed } }));
  }
  new MutationObserver((ms) => ms.forEach((m) => m.addedNodes.forEach((n) => {
    if (n.nodeType !== Node.ELEMENT_NODE) return;
    if (n.matches(".exercise-grade")) onGrade(n);
    n.querySelectorAll(".exercise-grade").forEach(onGrade);
  }))).observe(document.body, { childList: true, subtree: true });

  // ---- progress bar ----
  const sections = [...document.querySelectorAll("section.step")];
  const bar = sections.length && el("nav", { className: "pc-progress" });
  if (bar) buildBar();

  // Checkable items of a section: [{ok: () => bool}]
  function itemsOf(section) {
    const items = [];
    const stored = (id, test) => items.push(() => test(json(key(id)) || {}));
    section.querySelectorAll("div.quiz[id], div.parsons[id]").forEach((d) => stored(d.id, (s) => s.passed === true));
    section.querySelectorAll("div.predict[id]").forEach((d) => stored(d.id, (s) => s.printed != null)); // answered, right or wrong
    section.querySelectorAll("div.anim[id]").forEach((d) => stored(d.id, (s) => s.seen === true));
    const labels = new Set();
    section.querySelectorAll('script[type$="-contents"]').forEach((s) => {
      const l = exerciseLabel(s.type.replace("-contents", ""));
      if (l) labels.add(l);
    });
    labels.forEach((l) => items.push(() => (json(key(`exercise:${l}`)) || {}).passed === true));
    return items;
  }

  function buildBar() {
    const list = el("ol", { className: "pc-steps" });
    const count = el("p", { className: "pc-count", role: "status" });
    bar.setAttribute("aria-label", "Unit progress");
    bar.append(count, list);
    const steps = sections.map((s) => {
      const state = el("span", { className: "pc-state" });
      const a = el("a", { href: `#${s.id}` }, el("span", { className: "pc-name", textContent: s.querySelector("h2").textContent.trim() }), state);
      const li = el("li", {}, a);
      list.append(li);
      return { s, li, state, a, items: itemsOf(s) };
    });
    const seen = new IntersectionObserver((es) => es.forEach((e) => {
      if (e.isIntersecting) { set(key(`visited:${e.target.id}`), "1"); seen.unobserve(e.target); update(); }
    }));
    steps.forEach((st) => seen.observe(st.s));

    function update() {
      let done = 0;
      steps.forEach((st) => {
        const ok = st.items.length ? st.items.every((f) => f()) : get(key(`visited:${st.s.id}`)) === "1";
        st.li.classList.toggle("done", ok);
        st.state.textContent = ok ? "done" : "to do";
        st.a.setAttribute("aria-label", `${st.s.querySelector("h2").textContent.trim()}, ${ok ? "done" : "to do"}`);
        done += ok;
      });
      count.textContent = `${done} of ${steps.length} steps` + (storageOk ? "" : " (progress cannot be saved: browser storage is off)");
      if (done === steps.length && !get(key("complete"))) set(key("complete"), JSON.stringify({ at: new Date().toISOString() }));
    }
    // Late-rendered cells (quarto-live) are known from the static scripts already; just refresh.
    document.addEventListener("pycourse:result", update);
    update();
    const main = document.querySelector("main.content") || document.body;
    main.prepend(bar);
    const header = document.getElementById("quarto-header");
    const place = () => { bar.style.top = `${header ? header.offsetHeight : 0}px`; };
    place(); addEventListener("resize", place);
  }

  // ---- export / import / reset panel ----
  const dlg = el("dialog", { className: "pc-panel", id: "pc-panel" });
  const msg = el("p", { className: "pc-msg", role: "status" });
  const file = el("input", { type: "file", accept: ".json,application/json", id: "pc-file" });
  const confirmRow = el("div", { className: "pc-confirm" });
  const say = (t) => { msg.textContent = t; };
  const exportBtn = el("button", { type: "button", className: "btn btn-primary btn-sm", textContent: "Export progress" });
  const resetBtn = el("button", { type: "button", className: "btn btn-outline-danger btn-sm", textContent: "Reset progress" });
  const closeBtn = el("button", { type: "button", className: "btn btn-outline-secondary btn-sm", textContent: "Close" });
  dlg.append(el("h2", { textContent: "Progress" }),
    el("p", { textContent: "Your progress lives only in this browser. Export it as a file to move it to another browser." }),
    storageOk ? "" : el("p", { className: "pc-warn", textContent: "Browser storage is unavailable (private mode or blocked): progress cannot be saved or restored." }),
    el("p", {}, exportBtn),
    el("p", {}, el("label", { htmlFor: "pc-file", textContent: "Import progress (JSON file) " }), file),
    confirmRow, el("p", {}, resetBtn), msg, el("p", {}, closeBtn));
  document.body.append(dlg);
  closeBtn.onclick = () => dlg.close();
  document.addEventListener("click", (e) => {
    const a = e.target.closest('a[href$="#pc-panel"]');
    if (!a) return;
    e.preventDefault();
    say(""); confirmRow.replaceChildren(); file.value = "";
    dlg.showModal();
  });

  function confirmAction(text, label, action) {
    const go = el("button", { type: "button", className: "btn btn-danger btn-sm", textContent: label });
    const no = el("button", { type: "button", className: "btn btn-outline-secondary btn-sm", textContent: "Cancel" });
    go.onclick = action;
    no.onclick = () => { confirmRow.replaceChildren(); say("Nothing changed."); };
    confirmRow.replaceChildren(el("p", { textContent: text }), go, " ", no);
    go.focus();
  }

  exportBtn.onclick = () => {
    if (!storageOk) return say("Storage is unavailable: nothing to export.");
    if (window.pycourseSaveDrafts) window.pycourseSaveDrafts();
    const items = {};
    allKeys().forEach((k) => { items[k] = get(k); });
    const data = { format: "pycourse-progress", version: 1, exported_at: new Date().toISOString(), items };
    const a = el("a", { download: `python-course-progress-${data.exported_at.slice(0, 10)}.json`,
      href: URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" })) });
    a.click();
    URL.revokeObjectURL(a.href);
    say(`Exported ${Object.keys(items).length} items.`);
  };

  resetBtn.onclick = () => {
    if (!storageOk) return say("Storage is unavailable: nothing to reset.");
    const n = allKeys().length;
    confirmAction(`Delete all ${n} saved items (results and code drafts) from this browser?`, "Confirm reset", () => {
      allKeys().forEach((k) => { try { localStorage.removeItem(k); } catch { /* ignore */ } });
      location.reload();
    });
  };

  file.onchange = async () => {
    confirmRow.replaceChildren();
    const f = file.files[0];
    if (!f) return;
    const reject = (why) => { file.value = ""; say(`Import rejected, nothing changed: ${why}`); };
    if (!storageOk) return reject("browser storage is unavailable.");
    if (f.size >= MAX_BYTES) return reject("file is 2 MB or larger.");
    let data;
    try { data = JSON.parse(await f.text()); } catch { return reject("not valid JSON."); }
    if (!data || data.format !== "pycourse-progress") return reject("not a python-course progress file.");
    if (data.version !== 1) return reject(`unsupported version ${data.version}.`);
    const items = data.items;
    if (!items || typeof items !== "object" || Array.isArray(items)) return reject("items missing.");
    for (const [k, v] of Object.entries(items)) {
      if (!k.startsWith(PREFIX)) return reject(`foreign key "${k.slice(0, 40)}".`);
      if (typeof v !== "string") return reject(`value of "${k.slice(0, 40)}" is not a string.`);
    }
    const keys = Object.keys(items);
    const existing = keys.filter((k) => get(k) !== null).length;
    confirmAction(`${keys.length} items, will replace ${existing} existing. Other saved items stay.`, "Confirm import", () => {
      keys.forEach((k) => set(k, items[k]));
      location.reload();
    });
  };
})();
