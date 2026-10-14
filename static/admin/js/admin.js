(function () {
    "use strict";

    function applyAdminTheme(theme) {
        var normalizedTheme = theme === "light" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", normalizedTheme);

        var toggle = document.getElementById("admin-theme-toggle");
        if (toggle) {
            var lightMode = normalizedTheme === "dark";
            var label = lightMode ? "Light mode" : "Dark mode";
            toggle.setAttribute("aria-label", "Switch to " + label.toLowerCase());
            toggle.setAttribute("title", "Switch to " + label.toLowerCase());
            toggle.querySelector(".admin-theme-toggle-icon").textContent = lightMode ? "☀" : "☾";
            toggle.querySelector(".admin-theme-toggle-label").textContent = label;
        }
    }

    applyAdminTheme(window.localStorage.getItem("bookshop-theme") || "dark");

    document.addEventListener("DOMContentLoaded", function () {
        var toastRegion = document.createElement("div");
        toastRegion.className = "admin-toast-region";
        toastRegion.setAttribute("aria-label", "Notifications");
        document.body.appendChild(toastRegion);

        document.querySelectorAll("#nav-sidebar .module a.addlink").forEach(function (link) {
            var icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            var vertical = document.createElementNS("http://www.w3.org/2000/svg", "path");
            var horizontal = document.createElementNS("http://www.w3.org/2000/svg", "path");

            icon.setAttribute("viewBox", "0 0 16 16");
            icon.setAttribute("class", "admin-sidebar-add-icon");
            icon.setAttribute("aria-hidden", "true");
            icon.setAttribute("focusable", "false");
            vertical.setAttribute("d", "M8 3v10");
            horizontal.setAttribute("d", "M3 8h10");
            icon.appendChild(vertical);
            icon.appendChild(horizontal);
            link.insertBefore(icon, link.firstChild);
        });

        var sidebarToggle = document.getElementById("toggle-nav-sidebar");
        var adminSidebar = document.getElementById("nav-sidebar");
        var adminMain = document.getElementById("main");
        if (sidebarToggle && adminSidebar && adminMain) {
            var sidebarBreakpoint = window.matchMedia("(max-width: 1024px)");
            var sidebarPreferenceKey = "bookshop-admin-sidebar-collapsed";

            function syncSidebarState() {
                var isOpen = adminMain.classList.contains("shifted");
                var compact = sidebarBreakpoint.matches;
                var label = compact
                    ? (isOpen ? "Close navigation" : "Open navigation")
                    : (isOpen ? "Collapse sidebar" : "Expand sidebar");

                sidebarToggle.setAttribute("aria-expanded", String(isOpen));
                sidebarToggle.setAttribute("aria-label", label);
                sidebarToggle.setAttribute("title", label);
                document.body.classList.toggle("admin-sidebar-collapsed", !isOpen);
            }

            function setSidebarOpen(isOpen) {
                if (adminMain.classList.contains("shifted") !== isOpen) {
                    sidebarToggle.click();
                } else {
                    syncSidebarState();
                }
            }

            function restoreSidebarForViewport() {
                if (sidebarBreakpoint.matches) {
                    setSidebarOpen(false);
                    return;
                }

                var savedPreference = window.localStorage.getItem(sidebarPreferenceKey);
                setSidebarOpen(savedPreference !== "true");
            }

            restoreSidebarForViewport();
            syncSidebarState();
            sidebarToggle.addEventListener("click", function () {
                window.requestAnimationFrame(function () {
                    syncSidebarState();
                    if (!sidebarBreakpoint.matches) {
                        window.localStorage.setItem(
                            sidebarPreferenceKey,
                            String(!adminMain.classList.contains("shifted"))
                        );
                    }
                });
            });

            document.addEventListener("click", function (event) {
                if (
                    sidebarBreakpoint.matches &&
                    adminMain.classList.contains("shifted") &&
                    !adminSidebar.contains(event.target) &&
                    !sidebarToggle.contains(event.target)
                ) {
                    sidebarToggle.click();
                }
            });

            document.addEventListener("keydown", function (event) {
                if (event.key === "Escape" && sidebarBreakpoint.matches && adminMain.classList.contains("shifted")) {
                    sidebarToggle.click();
                    sidebarToggle.focus();
                }
            });

            sidebarBreakpoint.addEventListener("change", function (event) {
                restoreSidebarForViewport();
                window.requestAnimationFrame(syncSidebarState);
            });
        }

        function showToast(level, title, detail, duration) {
            var toast = document.createElement("div");
            var icon = document.createElement("span");
            var content = document.createElement("div");
            var heading = document.createElement("strong");
            var message = document.createElement("div");
            var dismiss = document.createElement("button");
            var iconByLevel = {
                success: "✓",
                warning: "!",
                error: "!",
                info: "i",
                debug: "i"
            };

            toast.className = "admin-toast";
            toast.dataset.level = level;
            toast.setAttribute("role", level === "error" ? "alert" : "status");
            icon.className = "admin-toast-icon";
            icon.setAttribute("aria-hidden", "true");
            icon.textContent = iconByLevel[level] || "i";
            content.className = "admin-toast-content";
            heading.textContent = title;
            content.appendChild(heading);

            if (detail) {
                message.textContent = detail;
                content.appendChild(message);
            }

            dismiss.className = "admin-toast-dismiss";
            dismiss.type = "button";
            dismiss.setAttribute("aria-label", "Dismiss notification");
            dismiss.textContent = "×";
            dismiss.addEventListener("click", function () {
                toast.remove();
            });

            toast.appendChild(icon);
            toast.appendChild(content);
            toast.appendChild(dismiss);
            toastRegion.appendChild(toast);
            window.requestAnimationFrame(function () {
                toast.classList.add("is-visible");
            });

            if (duration > 0) {
                window.setTimeout(function () {
                    toast.classList.remove("is-visible");
                    window.setTimeout(function () {
                        toast.remove();
                    }, 180);
                }, duration);
            }
        }

        document.querySelectorAll(".messagelist li").forEach(function (message) {
            var level = ["success", "warning", "error", "info", "debug"]
                .find(function (tag) { return message.classList.contains(tag); }) || "success";
            showToast(level, message.textContent.trim(), "", 5000);
        });
        document.querySelectorAll(".messagelist").forEach(function (list) {
            list.remove();
        });

        var validationErrors = new Map();
        document.querySelectorAll("#content .errornote, #content .errorlist li").forEach(function (error) {
            var form = error.closest("form");
            var key = form || document;
            var text = error.textContent.trim();
            if (!text) {
                return;
            }
            if (!validationErrors.has(key)) {
                validationErrors.set(key, []);
            }
            if (!validationErrors.get(key).includes(text)) {
                validationErrors.get(key).push(text);
            }
        });

        validationErrors.forEach(function (errors) {
            var firstError = errors[0];
            var additionalErrors = errors.length > 1
                ? errors.length + " validation issues. "
                : "";
            showToast("error", "Please review the form", additionalErrors + firstError, 8000);
        });

        var invalidToastTimer;
        document.addEventListener("invalid", function () {
            window.clearTimeout(invalidToastTimer);
            invalidToastTimer = window.setTimeout(function () {
                showToast("error", "Please check this form", "Complete required fields and correct any invalid values.", 5000);
            }, 0);
        }, true);

        var themeToggle = document.getElementById("admin-theme-toggle");
        if (themeToggle) {
            themeToggle.addEventListener("click", function () {
                var nextTheme = document.documentElement.getAttribute("data-theme") === "dark"
                    ? "light"
                    : "dark";
                window.localStorage.setItem("bookshop-theme", nextTheme);
                applyAdminTheme(nextTheme);
            });
        }

        document.querySelectorAll("#result_list tbody tr").forEach(function (row) {
            row.addEventListener("click", function (event) {
                if (event.target.closest("a, button, input, select, textarea, label")) {
                    return;
                }
                var link = row.querySelector("th a, td a");
                if (link) {
                    link.click();
                }
            });
        });

        document.querySelectorAll(".actions select").forEach(function (select) {
            select.addEventListener("change", function () {
                select.closest(".actions").classList.add("has-selection");
            });
        });
    });
})();
