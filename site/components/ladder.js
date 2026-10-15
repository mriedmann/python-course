// Exercise ladder: solution gate (docs/02 "Exercise ladder and feedback", docs/04 "Feedback ladder").
// quarto-live 0.2.0 already reveals hints one at a time ("Show Hint" -> "Next Hint") and offers
// "Show Solution" only after the last hint. This file adds the second route to the solution:
// after FAILS_FOR_SOLUTION failed checks, a "Show Solution" button appears in the exercise header.
(() => {
  const FAILS_FOR_SOLUTION = 2;
  const fails = {};

  // Exercise label of a quarto-live cell (id "pyodide-N"), read from its base64 JSON contents script.
  function exerciseLabel(cell) {
    const script = document.querySelector(`script[type="${cell.id}-contents"]`);
    try {
      return JSON.parse(window._exercise_ojs_runtime.b64Decode(script.textContent)).attr.exercise;
    } catch {
      return null;
    }
  }

  function offerSolution(cell, label) {
    const solutions = document.querySelectorAll(`.exercise-solution.d-none[data-exercise="${label}"]`);
    const group = cell.querySelector(".exercise-editor-header .btn-group");
    if (!solutions.length || !group || cell.querySelector(".btn-exercise-solution")) return;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "btn btn-exercise-editor btn-exercise-solution btn-outline-dark btn-sm text-nowrap";
    button.textContent = "Show Solution";
    button.addEventListener("click", () => {
      solutions.forEach((el) => el.classList.remove("d-none"));
      button.remove();
    });
    group.appendChild(button);
  }

  function onGrade(grade) {
    const cell = grade.closest(".exercise-cell");
    const label = cell && exerciseLabel(cell);
    if (!label || !grade.classList.contains("alert-danger")) return;
    fails[label] = (fails[label] || 0) + 1;
    if (fails[label] >= FAILS_FOR_SOLUTION) offerSolution(cell, label);
  }

  new MutationObserver((mutations) => {
    for (const m of mutations) {
      for (const node of m.addedNodes) {
        if (node.nodeType !== Node.ELEMENT_NODE) continue;
        if (node.matches(".exercise-grade")) onGrade(node);
        node.querySelectorAll(".exercise-grade").forEach(onGrade);
      }
    }
  }).observe(document.body, { childList: true, subtree: true });
})();
