(function () {
  "use strict";

  const profileForm = document.querySelector("[data-profile-change-form]");

  function showValidationAlert(message, input) {
    if (window.Swal) {
      window.Swal.fire({ icon: "error", title: message });
    } else {
      window.alert(message);
    }
    input?.focus();
  }

  const serverValidationMessages = Array.from(
    document.querySelectorAll("[data-profile-validation-errors] [data-validation-message]")
  ).map(function (error) {
    return error.textContent.trim();
  });
  if (serverValidationMessages.length && window.Swal) {
    window.Swal.fire({
      icon: "error",
      title: serverValidationMessages[0],
      text: serverValidationMessages.slice(1).join(" "),
    });
  }

  if (profileForm) {
    profileForm.querySelectorAll("[data-add-entry]").forEach(function (button) {
      button.addEventListener("click", function () {
        const list = profileForm.querySelector('[data-entry-list="' + button.dataset.addEntry + '"]');
        const source = list?.querySelector("[data-entry-row]");
        const input = source?.querySelector("[data-entry-input]");
        if (!list || !source || !input) {
          return;
        }

        const row = source.cloneNode(true);
        const rowInput = row.querySelector("[data-entry-input]");
        rowInput.value = "";
        list.appendChild(row);
        rowInput.focus();
      });
    });

    profileForm.addEventListener("click", function (event) {
      const removeButton = event.target.closest("[data-remove-entry]");
      const row = removeButton?.closest("[data-entry-row]");
      const list = removeButton?.closest("[data-entry-list]");
      if (!row || !list) {
        return;
      }

      if (list.querySelectorAll("[data-entry-row]").length === 1) {
        row.querySelector("[data-entry-input]").value = "";
      } else {
        row.remove();
      }
    });

    profileForm.addEventListener("submit", function (event) {
      const emailInputs = Array.from(profileForm.querySelectorAll('[data-entry-input="email"]'));
      const contactInputs = Array.from(profileForm.querySelectorAll('[data-entry-input="contact"]'));
      const emailValues = emailInputs.map(function (input) { return input.value.trim(); }).filter(Boolean);
      const contactValues = contactInputs.map(function (input) { return input.value.trim(); }).filter(Boolean);
      const invalidEmail = emailInputs.find(function (input) {
        const email = input.value.trim();
        return email && !/^[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@gmail\.com$/i.test(email);
      });

      if (invalidEmail) {
        event.preventDefault();
        showValidationAlert("Not valid email address.", invalidEmail);
        return;
      }

      const invalidContact = contactInputs.find(function (input) {
        const number = input.value.trim();
        return number && !/^\d{10}$/.test(number);
      });
      if (invalidContact) {
        event.preventDefault();
        showValidationAlert("The contact number should be of 10 digits.", invalidContact);
        return;
      }

      profileForm.elements.namedItem("email").value = emailValues.join("\n");
      profileForm.elements.namedItem("contact_numbers").value = contactValues.join("\n");
    });
  }

  const form = document.querySelector("[data-profile-picture-form]");
  const editButton = form?.querySelector("[data-profile-picture-edit]");
  const pictureInput = form?.querySelector('input[name="profile_picture"]');
  const avatarInputs = form?.querySelectorAll('input[name="avatar_choice"]');
  const preview = form?.querySelector("#profile-picture-preview");
  const saveButton = form?.querySelector("[data-save-profile-picture]");

  if (!form || !editButton || !pictureInput || !avatarInputs || !preview || !saveButton) {
    return;
  }

  let previewUrl;

  editButton.addEventListener("click", function () {
    pictureInput.click();
  });

  pictureInput.addEventListener("change", function () {
    const file = pictureInput.files?.[0];
    if (!file) {
      return;
    }

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    previewUrl = URL.createObjectURL(file);
    preview.src = previewUrl;
    saveButton.classList.remove("hidden");
  });

  avatarInputs.forEach(function (avatarInput) {
    avatarInput.addEventListener("change", function () {
      const avatarImage = avatarInput.nextElementSibling;
      if (avatarInput.checked && avatarImage?.tagName === "IMG") {
        preview.src = avatarImage.src;
      }
      saveButton.classList.remove("hidden");
    });
  });

  window.addEventListener("pagehide", function () {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
  });
})();
