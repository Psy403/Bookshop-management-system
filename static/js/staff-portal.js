(function () {
  "use strict";

  const profileButton = document.getElementById("profile-button");
  const profileMenu = document.getElementById("profile-menu");
  const notificationButton = document.getElementById("notification-button");
  const notificationMenu = document.getElementById("notification-menu");
  const themeToggleButton = document.getElementById("theme-toggle");
  const themeToggleIcon = document.getElementById("theme-toggle-icon");

  function applyTheme(theme) {
    document.body.setAttribute("data-theme", theme);
    const isLight = theme === "light";
    if (themeToggleIcon) {
      themeToggleIcon.classList.toggle("fa-moon", !isLight);
      themeToggleIcon.classList.toggle("fa-sun", isLight);
    }
    window.localStorage.setItem("bookshop-theme", theme);
  }

  applyTheme(window.localStorage.getItem("bookshop-theme") || "dark");

  themeToggleButton?.addEventListener("click", function () {
    const nextTheme = document.body.getAttribute("data-theme") === "dark" ? "light" : "dark";
    applyTheme(nextTheme);
  });

  profileButton?.addEventListener("click", function () {
    profileMenu?.classList.toggle("hidden");
  });
  notificationButton?.addEventListener("click", function () {
    notificationMenu?.classList.toggle("hidden");
  });

  document.addEventListener("click", function (event) {
    if (!profileButton?.contains(event.target) && !profileMenu?.contains(event.target)) {
      profileMenu?.classList.add("hidden");
    }
    if (!notificationButton?.contains(event.target) && !notificationMenu?.contains(event.target)) {
      notificationMenu?.classList.add("hidden");
    }
  });

  function getCookie(name) {
    return document.cookie
      .split(";")
      .map(function (cookie) { return cookie.trim(); })
      .find(function (cookie) { return cookie.startsWith(name + "="); })
      ?.split("=")[1];
  }

  document.querySelectorAll(".notification-read-form").forEach(function (form) {
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      try {
        const response = await fetch(form.action, {
          method: "POST",
          body: new FormData(form),
          credentials: "same-origin",
          headers: {
            "X-CSRFToken": decodeURIComponent(getCookie("csrftoken") || ""),
          },
        });
        if (!response.ok) {
          form.submit();
          return;
        }
        window.location.assign(response.url);
      } catch (error) {
        form.submit();
      }
    });
  });

  document.querySelectorAll("#staff-toast-messages [data-icon]").forEach(function (message) {
    if (window.Swal) {
      window.Swal.fire({
        toast: true,
        position: "top-end",
        icon: message.dataset.icon,
        title: message.textContent.trim(),
        showConfirmButton: false,
        timer: 3500,
        timerProgressBar: true,
      });
    }
  });

  const menuButton = document.getElementById("menu-btn");
  const sidebar = document.getElementById("sidebar");
  const menuOverlay = document.getElementById("menu-overlay");

  menuButton?.addEventListener("click", function () {
    sidebar?.classList.remove("hidden");
    menuOverlay?.classList.remove("hidden");
  });
  menuOverlay?.addEventListener("click", function () {
    sidebar?.classList.add("hidden");
    menuOverlay.classList.add("hidden");
  });
})();
