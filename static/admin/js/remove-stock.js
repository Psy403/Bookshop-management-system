(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("remove-stock-form");
    const input = document.getElementById("quantity");
    if (!form || !input || input.value) {
      return;
    }

    const amount = window.prompt(
      "How many copies of " + form.dataset.bookTitle +
      " should be deleted? Current stock: " + form.dataset.currentStock
    );
    if (amount === null) {
      window.location.href = form.dataset.cancelUrl;
      return;
    }
    input.value = amount;
    form.requestSubmit();
  });
})();
