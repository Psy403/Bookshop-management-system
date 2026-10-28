(function () {
  "use strict";

  const password = document.getElementById("password");
  const passwordToggle = document.querySelector("[data-toggle-password]");
  passwordToggle?.addEventListener("click", function () {
    if (!password) {
      return;
    }
    const reveal = password.type === "password";
    password.type = reveal ? "text" : "password";
    passwordToggle.textContent = reveal ? "Hide" : "Show";
    passwordToggle.setAttribute("aria-label", reveal ? "Hide password" : "Show password");
    passwordToggle.setAttribute("aria-pressed", String(reveal));
  });

  document.querySelectorAll("#staff-login-messages [data-icon]").forEach(function (message) {
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
})();
