"use strict";

// Apply the saved theme before CSS is painted; no inline script is needed.
(() => {
  let selected;
  try {
    selected = localStorage.getItem("aptutor-v0.5-theme")
      || localStorage.getItem("aptutor-v0.3-theme");
  } catch (_) { /* optional */ }
  if (selected !== "light" && selected !== "dark") {
    selected = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark" : "light";
  }
  document.documentElement.dataset.theme = selected;
})();
