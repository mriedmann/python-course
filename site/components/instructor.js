// Instructor mode UI (docs/04). The flag itself is set early by the inline snippet in _quarto.yml
// (?instructor / ?instructor=1 on, ?instructor=0 off, kept in sessionStorage); CSS in components.css
// hides hints, solutions and spoilers. This file adds the badge with the Presenter toggle.
// Not a security boundary: solutions stay in the page HTML, they are only hidden.
(() => {
  const root = document.documentElement;
  if (!root.classList.contains("instructor")) return;
  const KEY = "pycourse:instructor-presenter";
  const get = () => { try { return sessionStorage.getItem(KEY) === "1"; } catch { return false; } };
  const put = (on) => { try { sessionStorage.setItem(KEY, on ? "1" : "0"); } catch { /* storage off */ } };

  const badge = document.createElement("div");
  badge.className = "instructor-badge";
  const label = document.createElement("span");
  label.textContent = "Instructor";
  const toggle = document.createElement("button");
  toggle.type = "button";
  toggle.className = "btn btn-sm btn-light";
  const render = (on) => {
    root.classList.toggle("presenter", on);
    toggle.setAttribute("aria-pressed", String(on));
    toggle.textContent = "Presenter";
  };
  toggle.addEventListener("click", () => {
    const on = !root.classList.contains("presenter");
    put(on);
    render(on);
  });
  badge.append(label, toggle);
  document.body.appendChild(badge);
  render(get());
})();
