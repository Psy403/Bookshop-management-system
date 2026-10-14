(function () {
  "use strict";

  const totalRefund = document.getElementById("total-refund");
  if (!totalRefund) {
    return;
  }

  function updateRefund() {
    let total = 0;
    document.querySelectorAll(".return-check").forEach(function (check) {
      const row = check.closest("tr");
      const quantity = row.querySelector(".return-quantity");
      const amount = check.checked
        ? Number(check.dataset.price) * Number(quantity.value || 0)
        : 0;
      row.querySelector(".return-amount").textContent = "Rs. " + amount.toFixed(2);
      total += amount;
    });
    totalRefund.value = total ? "Rs. " + total.toFixed(2) : "";
  }

  document.querySelectorAll(".return-check, .return-quantity").forEach(function (element) {
    element.addEventListener("input", updateRefund);
    element.addEventListener("change", updateRefund);
  });
  updateRefund();
})();
