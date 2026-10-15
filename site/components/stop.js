// Stop button for quarto-live Pyodide cells (docs/04 "Robustness"). quarto-live 0.2.0 runs Pyodide
// in a Web Worker but offers no way to interrupt Python, and GitHub Pages cannot send the COOP/COEP
// headers that Pyodide's interrupt buffer needs. Reloading the page terminates the worker.
// Editor contents survive (drafts.js saves them first); Python variables do not.
// shortcut: reload loses Python state, upgrade when the page is cross-origin
// isolated AND quarto-live renders a KeyboardInterrupt (0.2.0 shows "OJS Error: l.get is not a function").
(() => {
  // Visible only while this cell runs (quarto-live un-hides its spinner then).
  const style = document.createElement("style");
  style.textContent = ".exercise-editor-eval-indicator.d-none + .btn-group .btn-exercise-stop { display: none; }";
  document.head.appendChild(style);

  function addStop(runButton) {
    if (runButton.parentElement.querySelector(".btn-exercise-stop")) return;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "btn btn-exercise-editor btn-exercise-stop btn-danger btn-sm text-nowrap";
    button.textContent = "Stop";
    button.title = "Stop Python by reloading the page (your code is kept, Python variables are lost)";
    button.addEventListener("click", () => {
      if (window.pycourseSaveDrafts) window.pycourseSaveDrafts();
      location.reload();
    });
    runButton.after(button);
  }

  const scan = () => document.querySelectorAll(".exercise-editor-btn-run-code").forEach(addStop);
  new MutationObserver(scan).observe(document.body, { childList: true, subtree: true });
  scan();
})();
