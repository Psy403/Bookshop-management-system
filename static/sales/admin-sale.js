(function () {
  function updateTotals() {
    let grandTotal = 0;
    document.querySelectorAll(".dynamic-items .form-row").forEach(function (row) {
      const quantity = Number(row.querySelector('[name$="-quantity"]')?.value || 0);
      const unitPrice = Number(row.querySelector('[name$="-unit_price"]')?.value || 0);
      const total = quantity * unitPrice;
      const totalField = row.querySelector('[name$="-total_price"]');
      if (totalField) {
        totalField.value = total.toFixed(2);
      }
      grandTotal += total;
    });
    const totalField = document.querySelector("#id_total_price");
    if (totalField) {
      totalField.value = grandTotal.toFixed(2);
    }
  }

  document.addEventListener("input", function (event) {
    if (event.target.matches('[name$="-quantity"], [name$="-unit_price"]')) {
      updateTotals();
    }
  });
  document.addEventListener("formset:added", updateTotals);
  document.addEventListener("DOMContentLoaded", updateTotals);
})();
