(function () {
  "use strict";

  const itemContainer = document.getElementById("sale-items");
  const addItemButton = document.getElementById("add-item");
  const firstItem = itemContainer?.querySelector(".sale-item");

  if (!itemContainer || !addItemButton || !firstItem) {
    return;
  }

  addItemButton.addEventListener("click", function () {
    const newItem = firstItem.cloneNode(true);
    newItem.querySelector("select").value = "";
    newItem.querySelector("input").value = "";
    itemContainer.appendChild(newItem);
  });

  itemContainer.addEventListener("click", function (event) {
    const removeButton = event.target.closest(".remove-item");
    if (removeButton && itemContainer.querySelectorAll(".sale-item").length > 1) {
      removeButton.closest(".sale-item").remove();
    }
  });
})();
