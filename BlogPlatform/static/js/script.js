// ---------------------------------------------------------------------------
// Shared front-end behavior: dark/light mode, mobile nav toggle, loading
// spinner helpers, and toast notifications.
// ---------------------------------------------------------------------------

(function () {
  // ---- Dark / light mode ---------------------------------------------
  const root = document.documentElement;
  const themeToggle = document.getElementById("themeToggle");
  const themeIcon = document.getElementById("themeIcon");

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    if (themeIcon) themeIcon.textContent = theme === "dark" ? "☀️" : "🌙";
  }

  const savedTheme = getCookie("theme") || "light";
  applyTheme(savedTheme);

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      const current = root.getAttribute("data-theme");
      const next = current === "dark" ? "light" : "dark";
      applyTheme(next);
      setCookie("theme", next, 365);
    });
  }

  function setCookie(name, value, days) {
    const d = new Date();
    d.setTime(d.getTime() + days * 24 * 60 * 60 * 1000);
    document.cookie = `${name}=${value};expires=${d.toUTCString()};path=/`;
  }

  function getCookie(name) {
    const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return match ? match[2] : null;
  }

  // ---- Mobile nav toggle ------------------------------------------------
  const navToggle = document.getElementById("navToggle");
  const navLinks = document.getElementById("navLinks");
  if (navToggle && navLinks) {
    navToggle.addEventListener("click", function () {
      navLinks.classList.toggle("open");
    });
  }

  // Auto-dismiss flash messages after a few seconds
  document.querySelectorAll(".flash-message").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.4s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });
})();

// ---- Loading spinner helpers (global) -------------------------------------
function showSpinner() {
  const el = document.getElementById("loadingSpinner");
  if (el) el.classList.add("active");
}
function hideSpinner() {
  const el = document.getElementById("loadingSpinner");
  if (el) el.classList.remove("active");
}

// ---- Toast notifications (global) ------------------------------------------
function showToast(message, type) {
  const existing = document.querySelector(".toast");
  if (existing) existing.remove();
  const toast = document.createElement("div");
  toast.className = `toast toast-${type === "error" ? "error" : "success"}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.transition = "opacity 0.3s ease";
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}
