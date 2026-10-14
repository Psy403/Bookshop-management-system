(function () {
  "use strict";

  const password = document.getElementById("password");
  const passwordToggle = document.querySelector("[data-toggle-password]");
  const passwordIcon = document.getElementById("passwordIcon");

  passwordToggle?.addEventListener("click", function () {
    if (!password || !passwordIcon) {
      return;
    }
    const reveal = password.type === "password";
    password.type = reveal ? "text" : "password";
    passwordIcon.classList.toggle("fa-eye", !reveal);
    passwordIcon.classList.toggle("fa-eye-slash", reveal);
    passwordToggle.setAttribute("aria-label", reveal ? "Hide password" : "Show password");
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
