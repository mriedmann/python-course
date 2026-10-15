// Step-through animation (docs/04 step 3). div.anim > div.frame[title] (picture + text alternative)
// and an optional div.reveal shown by "Show me the code" once the last frame has been reached.
// Silent, never autoplays: Play advances every PLAY_MS and stops at the last frame.
(() => {
  const key = (id) => `pycourse:v1:${location.pathname}:${id}`;
  const load = (id) => { try { return JSON.parse(localStorage.getItem(key(id))); } catch { return null; } };
  const save = (id, state) => { try { localStorage.setItem(key(id), JSON.stringify(state)); } catch { /* storage off */ } };
  const report = (id, passed) =>
    document.dispatchEvent(new CustomEvent("pycourse:result", { detail: { id, kind: "anim", passed } }));
  const PLAY_MS = 3000;

  function el(tag, props = {}, ...children) {
    const e = Object.assign(document.createElement(tag), props);
    e.append(...children);
    return e;
  }

  function setupAnim(box) {
    const id = box.id;
    const frames = [...box.querySelectorAll(":scope > .frame")];
    const titles = frames.map((f) => f.getAttribute("title") || "");
    frames.forEach((f) => f.removeAttribute("title")); // no hover tooltip; the label shows it
    const reveal = box.querySelector(":scope > .reveal");
    const button = (text) => el("button", { type: "button", className: "btn btn-outline-primary btn-sm", textContent: text });
    const back = button("Back");
    const next = button("Next");
    const play = button("Play");
    const label = el("p", { className: "anim-label" });
    const stage = el("div", { className: "anim-stage" }, ...frames);
    stage.setAttribute("aria-live", "polite");
    box.prepend(stage, el("div", { className: "anim-controls" }, back, next, play, label));

    let state = load(id) || {};
    let current = 0;
    let timer = null;
    let show = null;
    if (reveal) {
      reveal.hidden = true;
      show = button("Show me the code");
      show.title = "Available after you have stepped to the last frame";
      show.addEventListener("click", () => { reveal.hidden = false; show.remove(); });
      reveal.before(show);
    }

    function render() {
      frames.forEach((f, i) => { f.hidden = i !== current; });
      label.textContent = `Frame ${current + 1} of ${frames.length} — ${titles[current]}`;
      back.disabled = current === 0;
      next.disabled = current === frames.length - 1;
      if (current === frames.length - 1 && !state.seen) {
        state = { seen: true };
        save(id, state);
        report(id, true);
      }
      if (show) show.disabled = !state.seen;
      // A disabled button loses keyboard focus; hand it to the other direction.
      if (next.disabled && document.activeElement === next) back.focus();
      if (back.disabled && document.activeElement === back) next.focus();
    }

    function stop() {
      clearInterval(timer);
      timer = null;
      play.textContent = "Play";
    }

    function go(i) {
      current = Math.max(0, Math.min(frames.length - 1, i));
      render();
    }

    back.addEventListener("click", () => { stop(); go(current - 1); });
    next.addEventListener("click", () => { stop(); go(current + 1); });
    play.addEventListener("click", () => {
      if (timer) return stop();
      if (current === frames.length - 1) go(0);
      play.textContent = "Pause";
      timer = setInterval(() => {
        go(current + 1);
        if (current === frames.length - 1) stop();
      }, PLAY_MS);
    });

    stop();
    render();
  }

  document.querySelectorAll("div.anim[id]").forEach(setupAnim);
})();
