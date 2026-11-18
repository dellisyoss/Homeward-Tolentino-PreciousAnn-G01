(() => {
    const storageKey = "homeward-theme";
    const root = document.documentElement;
    const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");
    let preference = null;

    try {
        const savedTheme = localStorage.getItem(storageKey);
        if (savedTheme === "light" || savedTheme === "dark") {
            preference = savedTheme;
        }
    } catch {
        // Theme switching still works when browser storage is unavailable.
    }

    function updateToggle() {
        const toggle = document.getElementById("theme-toggle");
        if (!toggle) return;

        const nextTheme = root.dataset.bsTheme === "dark" ? "light" : "dark";
        toggle.setAttribute("aria-label", `Switch to ${nextTheme} mode`);
        toggle.hidden = false;
    }

    function applyTheme(theme) {
        root.dataset.bsTheme = theme;
        updateToggle();
    }

    applyTheme(preference ?? (systemTheme.matches ? "dark" : "light"));

    systemTheme.addEventListener("change", (event) => {
        if (preference === null) {
            applyTheme(event.matches ? "dark" : "light");
        }
    });

    document.addEventListener("DOMContentLoaded", () => {
        const toggle = document.getElementById("theme-toggle");
        if (!toggle) return;

        updateToggle();
        toggle.addEventListener("click", () => {
            preference = root.dataset.bsTheme === "dark" ? "light" : "dark";
            applyTheme(preference);
            try {
                localStorage.setItem(storageKey, preference);
            } catch {
                // Keep the selected theme for this page even without storage.
            }
        });
    });
})();
