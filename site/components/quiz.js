// Quiz card (docs/04 steps 1 and 8). Markup from components.lua: div.quiz > div.question with
// data-choice (0-based index of the correct list item) or data-answer ("a|b" alternatives), data-tags.
// A .quiz.warmup keeps the page's live cells hidden (CSS :has in components.css) until submitted.
(() => {
  const key = (id) => `pycourse:v1:${location.pathname}:${id}`;
  const load = (id) => { try { return JSON.parse(localStorage.getItem(key(id))); } catch { return null; } };
  const save = (id, state) => { try { localStorage.setItem(key(id), JSON.stringify(state)); } catch { /* storage off */ } };
  const report = (id, passed) =>
    document.dispatchEvent(new CustomEvent("pycourse:result", { detail: { id, kind: "quiz", passed } }));

  function el(tag, props = {}, ...children) {
    const e = Object.assign(document.createElement(tag), props);
    e.append(...children);
    return e;
  }

  // Turns one question div into labelled inputs; returns {get, set, grade} for that question.
  const instructor = document.documentElement.classList.contains("instructor"); // no answer reveal
  function setupQuestion(q, quizId, n) {
    const name = `${quizId}-q${n}`;
    const prompt = q.querySelector("p");
    if (prompt) prompt.id = `${name}-prompt`;
    q.setAttribute("role", "group");
    q.setAttribute("aria-labelledby", `${name}-prompt`);
    if (q.dataset.tags) q.prepend(el("span", { className: "quiz-tags", textContent: q.dataset.tags, title: "Goal / misconception IDs" }));
    const feedback = el("p", { className: "quiz-feedback" });
    let get, set, correct, message;

    if (q.dataset.choice !== undefined) {
      const answer = Number(q.dataset.choice);
      const items = [...q.querySelectorAll(":scope > ul > li")];
      const radios = items.map((li, i) => {
        const radio = el("input", { type: "radio", name, value: String(i) });
        li.replaceChildren(el("label", {}, radio, " ", ...li.childNodes));
        return radio;
      });
      q.querySelector(":scope > ul").classList.add("quiz-options");
      get = () => radios.findIndex((r) => r.checked);
      set = (v) => radios.forEach((r, i) => { r.checked = i === v; });
      correct = () => get() === answer;
      const solution = () => items[answer].querySelector("label").textContent.trim();
      message = () => {
        if (instructor) return correct() ? "Correct." : "Not quite.";
        items.forEach((li, i) => li.classList.toggle("quiz-answer", i === answer));
        return correct() ? "Correct." : `Not quite. The answer is ${solution()}.`;
      };
    } else {
      const answers = q.dataset.answer.split("|").map((a) => a.trim());
      const input = el("input", { type: "text", id: `${name}-input`, autocomplete: "off", spellcheck: false });
      q.append(el("p", { className: "quiz-short" }, el("label", { htmlFor: input.id, textContent: "Your answer " }), input));
      get = () => input.value;
      set = (v) => { input.value = v || ""; };
      correct = () => answers.includes(input.value.trim());
      message = () => (correct() ? "Correct." : instructor ? "Not quite." : `Not quite. The answer is ${answers[0]}.`);
    }
    q.append(feedback);
    return {
      get, set, correct,
      show: () => {
        const ok = correct();
        feedback.textContent = message();
        feedback.className = `quiz-feedback ${ok ? "pass" : "fail"}`;
        return ok;
      },
    };
  }

  function setupQuiz(quiz) {
    const id = quiz.id;
    const questions = [...quiz.querySelectorAll(".question")].map((q, n) => setupQuestion(q, id, n + 1));
    const score = el("p", { className: "quiz-score" });
    score.setAttribute("aria-live", "polite");
    const button = el("button", { type: "button", className: "btn btn-primary", textContent: "Check answers" });
    quiz.append(el("div", { className: "quiz-actions" }, button, score));

    function grade() {
      const right = questions.filter((q) => q.show()).length;
      score.textContent = `Score: ${right}/${questions.length}`;
      quiz.classList.add("submitted"); // un-hides the live cells of a .warmup page
      return right === questions.length;
    }

    button.addEventListener("click", () => {
      const passed = grade();
      save(id, { answers: questions.map((q) => q.get()), passed });
      report(id, passed);
    });

    const state = load(id);
    if (state && Array.isArray(state.answers)) {
      questions.forEach((q, i) => q.set(state.answers[i]));
      grade();
    }
  }

  document.querySelectorAll("div.quiz[id]").forEach(setupQuiz);
})();
