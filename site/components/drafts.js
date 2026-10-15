// Keeps the learner's code (docs/04 "Progress"). Saves every quarto-live editor to localStorage as
// pycourse:v1:<path>:draft:<cell key> and restores it on load. quarto-live 0.2.0 exposes no editor
// object, but CodeMirror 6 stores its DocView on the .cm-content element (that is how
// EditorView.findFromDOM works): `contentDOM.cmView.view` is the EditorView. Edits and "Start Over"
// both go through view.dispatch, which is wrapped to schedule a save. Restoring is one ordinary
// transaction: nothing runs. Predict cells (div.predict) are read-only and keep no draft.
// shortcut: cells without an exercise label are keyed by position; upgrade when units add unlabelled
// editable cells and reorder them.
(() => {
  const key = (cell) => `pycourse:v1:${location.pathname}:draft:${cell}`;
  const read = (k) => { try { return localStorage.getItem(k); } catch { return null; } };
  const write = (k, v) => {
    try { if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch { /* storage off */ }
  };
  const editors = []; // { view, storageKey, original }

  function cellKey(content, index) {
    try {
      const id = content.closest(".exercise-cell").id;
      const meta = JSON.parse(atob(document.querySelector(`script[type="${id}-contents"]`).textContent));
      if (meta.attr.exercise) return meta.attr.exercise;
    } catch { /* fall through to the position */ }
    return `cell${index}`;
  }

  function save(e) {
    const text = e.view.state.doc.toString();
    write(e.storageKey, text === e.original ? null : text); // back to the original: no draft
  }

  function attach(content) {
    const view = content.cmView && content.cmView.view;
    if (!view || content.closest(".predict") || editors.some((e) => e.view === view)) return;
    const e = { view, storageKey: key(cellKey(content, editors.length)), original: view.state.doc.toString() };
    editors.push(e);
    const draft = read(e.storageKey);
    if (draft !== null && draft !== e.original) {
      view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: draft } });
    }
    let timer;
    const dispatch = view.dispatch.bind(view);
    view.dispatch = (...args) => {
      dispatch(...args);
      clearTimeout(timer);
      timer = setTimeout(() => save(e), 400);
    };
  }

  window.pycourseSaveDrafts = () => editors.forEach(save);
  addEventListener("pagehide", window.pycourseSaveDrafts);

  const scan = () => document.querySelectorAll(".cm-content").forEach(attach);
  new MutationObserver(scan).observe(document.body, { childList: true, subtree: true });
  scan();
})();
