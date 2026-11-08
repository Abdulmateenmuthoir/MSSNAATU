/* ------------------------------------------------------------------
   MSSN AATU — interface behaviours
   Small, dependency-free enhancements. Everything degrades gracefully
   when JavaScript is unavailable.
   ------------------------------------------------------------------ */
(function () {
  "use strict";

  var doc = document;
  var root = doc.documentElement;
  var THEME_KEY = "mssn-theme";

  /* ----------------------------------------------------------------
     Theme
     ---------------------------------------------------------------- */
  function systemTheme() {
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    doc.querySelectorAll("[data-theme-toggle]").forEach(function (button) {
      var isDark = theme === "dark";
      button.setAttribute("aria-pressed", isDark ? "true" : "false");
      button.setAttribute(
        "aria-label",
        isDark ? "Switch to light mode" : "Switch to dark mode"
      );
      button.setAttribute("title", isDark ? "Light mode" : "Dark mode");
    });
    var meta = doc.querySelector('meta[name="theme-color"]:not([media])');
    if (meta) {
      meta.setAttribute("content", theme === "dark" ? "#0a120f" : "#faf7f0");
    }
  }

  function storedTheme() {
    try {
      return localStorage.getItem(THEME_KEY);
    } catch (error) {
      return null;
    }
  }

  function saveTheme(theme) {
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch (error) {
      /* storage may be blocked — the theme still applies for this page */
    }
  }

  applyTheme(storedTheme() || root.getAttribute("data-theme") || systemTheme());

  doc.addEventListener("click", function (event) {
    var toggle = event.target.closest("[data-theme-toggle]");
    if (!toggle) return;
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    applyTheme(next);
    saveTheme(next);
  });

  if (window.matchMedia) {
    var media = window.matchMedia("(prefers-color-scheme: dark)");
    var onChange = function (event) {
      if (!storedTheme()) applyTheme(event.matches ? "dark" : "light");
    };
    if (media.addEventListener) media.addEventListener("change", onChange);
    else if (media.addListener) media.addListener(onChange);
  }

  /* ----------------------------------------------------------------
     Mobile navigation (public site)
     ---------------------------------------------------------------- */
  function closeMobileNav() {
    var menu = doc.getElementById("mobile-menu");
    if (!menu) return;
    menu.classList.add("hidden");
    doc.querySelectorAll("[data-mobile-toggle]").forEach(function (button) {
      button.setAttribute("aria-expanded", "false");
      button.setAttribute("aria-label", "Open menu");
    });
  }

  doc.addEventListener("click", function (event) {
    var toggle = event.target.closest("[data-mobile-toggle]");
    if (toggle) {
      var menu = doc.getElementById(toggle.getAttribute("aria-controls") || "mobile-menu");
      if (!menu) return;
      var isHidden = menu.classList.toggle("hidden");
      toggle.setAttribute("aria-expanded", isHidden ? "false" : "true");
      toggle.setAttribute("aria-label", isHidden ? "Open menu" : "Close menu");
      return;
    }
    if (!event.target.closest("#mobile-menu") && !event.target.closest("[data-mobile-toggle]")) {
      closeMobileNav();
    }
  });

  doc.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    closeMobileNav();
    closeSidebar();
    doc.querySelectorAll("details[open]").forEach(function (details) {
      if (details.querySelector("summary")) details.removeAttribute("open");
    });
  });

  /* ----------------------------------------------------------------
     Dashboard sidebar
     ---------------------------------------------------------------- */
  function sidebar() {
    return doc.querySelector("[data-sidebar]");
  }

  function scrim() {
    return doc.querySelector("[data-sidebar-scrim]");
  }

  function openSidebar() {
    var aside = sidebar();
    var overlay = scrim();
    if (aside) aside.classList.add("is-open");
    if (overlay) overlay.classList.add("is-open");
    doc.body.classList.add("overflow-hidden", "lg:overflow-auto");
  }

  function closeSidebar() {
    var aside = sidebar();
    var overlay = scrim();
    if (aside) aside.classList.remove("is-open");
    if (overlay) overlay.classList.remove("is-open");
    doc.body.classList.remove("overflow-hidden", "lg:overflow-auto");
  }

  doc.addEventListener("click", function (event) {
    if (event.target.closest("[data-sidebar-open]")) {
      openSidebar();
      return;
    }
    if (
      event.target.closest("[data-sidebar-close]") ||
      event.target.closest("[data-sidebar-scrim]")
    ) {
      closeSidebar();
      return;
    }
    if (
      event.target.closest("[data-sidebar] a") &&
      window.matchMedia("(max-width: 1023px)").matches
    ) {
      closeSidebar();
    }
  });

  window.addEventListener("resize", function () {
    if (window.innerWidth >= 1024) closeSidebar();
  });

  /* ----------------------------------------------------------------
     Password visibility
     ---------------------------------------------------------------- */
  doc.addEventListener("click", function (event) {
    var button = event.target.closest("[data-password-toggle]");
    if (!button) return;
    var field = doc.getElementById(button.getAttribute("data-password-toggle"));
    if (!field) return;
    var show = field.type === "password";
    field.type = show ? "text" : "password";
    button.setAttribute("aria-label", show ? "Hide password" : "Show password");
    button.classList.toggle("text-brand", show);
    var openEye = button.querySelector("[data-eye-open]");
    var closedEye = button.querySelector("[data-eye-closed]");
    if (openEye && closedEye) {
      openEye.classList.toggle("hidden", show);
      closedEye.classList.toggle("hidden", !show);
    }
  });

  /* ----------------------------------------------------------------
     Password strength meter
     ---------------------------------------------------------------- */
  function scorePassword(value) {
    var score = 0;
    if (!value) return 0;
    if (value.length >= 8) score += 1;
    if (value.length >= 12) score += 1;
    if (/[a-z]/.test(value) && /[A-Z]/.test(value)) score += 1;
    if (/\d/.test(value)) score += 1;
    if (/[^A-Za-z0-9]/.test(value)) score += 1;
    return Math.min(4, score);
  }

  var strengthLabels = [
    "Use at least 8 characters, with a mix of letters and numbers.",
    "Weak — add length and variety.",
    "Fair — a little more variety would help.",
    "Strong — good to go.",
    "Excellent password.",
  ];
  var strengthColours = ["bg-line", "bg-danger", "bg-gold", "bg-success", "bg-success"];

  doc.querySelectorAll("[data-password-form]").forEach(function (form) {
    var field = form.querySelector('input[type="password"]');
    var bars = form.querySelectorAll("[data-strength-bars] span");
    var label = form.querySelector("[data-strength-label]");
    if (!field || !bars.length) return;

    var update = function () {
      var score = scorePassword(field.value);
      bars.forEach(function (bar, index) {
        strengthColours.forEach(function (colour) {
          bar.classList.remove(colour);
        });
        bar.classList.add(index < score ? strengthColours[score] : "bg-line");
      });
      if (label) label.textContent = strengthLabels[score];
    };

    field.addEventListener("input", update);
    update();
  });

  /* ----------------------------------------------------------------
     Copy helpers
     ---------------------------------------------------------------- */
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      var area = doc.createElement("textarea");
      area.value = text;
      area.setAttribute("readonly", "");
      area.style.position = "fixed";
      area.style.opacity = "0";
      doc.body.appendChild(area);
      area.select();
      try {
        doc.execCommand("copy");
        resolve();
      } catch (error) {
        reject(error);
      } finally {
        doc.body.removeChild(area);
      }
    });
  }

  function flash(button, message) {
    var original = button.getAttribute("data-original-label") || button.textContent.trim();
    button.setAttribute("data-original-label", original);
    button.textContent = message;
    window.setTimeout(function () {
      button.textContent = original;
    }, 1800);
  }

  doc.addEventListener("click", function (event) {
    var copyButton = event.target.closest("[data-copy]");
    if (copyButton) {
      event.preventDefault();
      copyText(copyButton.getAttribute("data-copy")).then(
        function () {
          flash(copyButton, "Copied");
        },
        function () {
          flash(copyButton, "Copy failed");
        }
      );
      return;
    }

    if (event.target.closest("[data-copy-url]")) {
      event.preventDefault();
      var shareButton = event.target.closest("[data-copy-url]");
      copyText(window.location.href).then(
        function () {
          shareButton.classList.add("!text-success", "!border-success/40");
          window.setTimeout(function () {
            shareButton.classList.remove("!text-success", "!border-success/40");
          }, 1800);
        },
        function () {
          /* nothing useful to do */
        }
      );
      return;
    }

    var tableButton = event.target.closest("[data-copy-table]");
    if (tableButton) {
      event.preventDefault();
      var table = doc.querySelector("[data-credentials-table]");
      if (!table) return;
      var rows = [];
      table.querySelectorAll("tr").forEach(function (row) {
        var cells = [];
        row.querySelectorAll("th, td").forEach(function (cell) {
          cells.push(cell.innerText.replace(/\s+/g, " ").trim());
        });
        if (cells.length) rows.push(cells.join("\t"));
      });
      copyText(rows.join("\n")).then(
        function () {
          flash(tableButton, "Copied " + (rows.length - 1) + " rows");
        },
        function () {
          flash(tableButton, "Copy failed");
        }
      );
    }
  });

  /* ----------------------------------------------------------------
     Toasts
     ---------------------------------------------------------------- */
  function dismissToast(toast) {
    if (!toast || toast.classList.contains("is-leaving")) return;
    toast.classList.add("is-leaving", "opacity-0", "translate-x-4");
    toast.style.transition = "opacity .25s ease, transform .25s ease";
    window.setTimeout(function () {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 260);
  }

  doc.addEventListener("click", function (event) {
    var close = event.target.closest("[data-toast-close]");
    if (close) dismissToast(close.closest("[data-toast]"));
  });

  doc.querySelectorAll("[data-toast]").forEach(function (toast) {
    window.setTimeout(function () {
      dismissToast(toast);
    }, 6500);
  });

  /* ----------------------------------------------------------------
     Reveal on scroll
     ---------------------------------------------------------------- */
  var revealItems = doc.querySelectorAll(".reveal");
  if (revealItems.length) {
    if ("IntersectionObserver" in window) {
      var observer = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-visible");
              observer.unobserve(entry.target);
            }
          });
        },
        { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
      );
      revealItems.forEach(function (item) {
        observer.observe(item);
      });
    } else {
      revealItems.forEach(function (item) {
        item.classList.add("is-visible");
      });
    }
  }

  /* ----------------------------------------------------------------
     Confirm-before-submit forms
     ---------------------------------------------------------------- */
  doc.addEventListener("submit", function (event) {
    var form = event.target;
    var message = form.getAttribute("data-confirm");
    if (message && !window.confirm(message)) {
      event.preventDefault();
      return;
    }
    var button = form.querySelector('button[type="submit"]');
    if (button && !button.disabled && !form.hasAttribute("data-no-busy")) {
      var busy = button.getAttribute("data-busy-label") || "Working…";
      window.setTimeout(function () {
        if (!button.disabled) {
          button.dataset.originalHtml = button.innerHTML;
          button.disabled = true;
          button.classList.add("opacity-70");
          button.textContent = busy;
        }
      }, 10);
    }
  });

  /* ----------------------------------------------------------------
     Auto-submit for filter selects marked data-autosubmit
     ---------------------------------------------------------------- */
  doc.querySelectorAll("select[data-autosubmit]").forEach(function (select) {
    select.addEventListener("change", function () {
      if (select.form) select.form.submit();
    });
  });

  /* ----------------------------------------------------------------
     Dismiss <details> menus on outside click
     ---------------------------------------------------------------- */
  doc.addEventListener("click", function (event) {
    doc.querySelectorAll("details[open]").forEach(function (details) {
      if (!details.contains(event.target)) details.removeAttribute("open");
    });
  });
})();
