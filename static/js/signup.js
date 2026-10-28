(function () {
  "use strict";

  const form = document.getElementById("signup-form");
  if (!form) {
    if (document.querySelector(".signup-success")) {
      window.sessionStorage.removeItem("bookshop-signup-draft");
    }
    return;
  }

  const steps = [...form.querySelectorAll("[data-step]")];
  const labels = [...form.querySelectorAll("[data-step-label]")];
  const dots = [...form.querySelectorAll(".step-dots span")];
  const backButton = form.querySelector("[data-back]");
  const continueButton = form.querySelector("[data-continue]");
  const submitButton = form.querySelector("[data-submit]");
  const stepChip = form.querySelector("[data-step-chip]");
  const progress = form.querySelector(".progress-track");
  const progressFill = form.querySelector(".progress-fill");
  const autosaveText = form.querySelector("[data-autosave-status]");
  const draftKey = "bookshop-signup-draft";
  const fieldNames = ["first_name", "middle_name", "last_name", "username", "email", "phone_number"];
  let currentStep = Number(form.dataset.activeStep || 0);

  function field(name) {
    return form.elements.namedItem(name);
  }

  function saveDraft() {
    const draft = Object.fromEntries(
      fieldNames.map((name) => [name, field(name).value])
    );
    draft.currentStep = currentStep;
    window.sessionStorage.setItem(draftKey, JSON.stringify(draft));
    autosaveText.textContent = "Progress saved automatically";
  }

  function restoreDraft() {
    const rawDraft = window.sessionStorage.getItem(draftKey);
    if (!rawDraft) {
      return;
    }

    const draft = JSON.parse(rawDraft);
    fieldNames.forEach((name) => {
      const input = field(name);
      if (!input.value && typeof draft[name] === "string") {
        input.value = draft[name];
      }
    });
    if (
      form.dataset.hasErrors !== "true" &&
      Number.isInteger(draft.currentStep) &&
      draft.currentStep >= 0 &&
      draft.currentStep < steps.length
    ) {
      currentStep = Math.max(currentStep, draft.currentStep);
    }
  }

  function updateReview() {
    const fullName = ["first_name", "middle_name", "last_name"]
      .map((name) => field(name).value.trim())
      .filter(Boolean)
      .join(" ");
    form.querySelector('[data-review="name"]').textContent = fullName;
    form.querySelector('[data-review="username"]').textContent = field("username").value.trim();
    form.querySelector('[data-review="email"]').textContent = field("email").value.trim();
    form.querySelector('[data-review="phone"]').textContent = field("phone_number").value.trim();
  }

  function updateStep() {
    steps.forEach((step, index) => {
      step.hidden = index !== currentStep;
    });
    labels.forEach((label, index) => {
      label.classList.toggle("is-active", index === currentStep);
      label.setAttribute("aria-current", index === currentStep ? "step" : "false");
      const mobileCount = label.querySelector(".mobile-step-count");
      if (mobileCount) {
        mobileCount.textContent = `· Step ${currentStep + 1}/4`;
      }
    });
    dots.forEach((dot, index) => {
      dot.classList.toggle("is-active", index === currentStep);
    });

    const stepNumber = currentStep + 1;
    stepChip.textContent = `Step ${stepNumber} / 4`;
    progress.setAttribute("aria-valuenow", String(stepNumber));
    progress.setAttribute("aria-label", `Registration progress, step ${stepNumber} of 4`);
    progressFill.style.width = `${stepNumber * 25}%`;
    form.querySelector(".step-dots").setAttribute("aria-label", `Step ${stepNumber} of 4`);
    backButton.disabled = currentStep === 0;
    continueButton.hidden = currentStep === steps.length - 1;
    submitButton.hidden = currentStep !== steps.length - 1;
    if (currentStep === steps.length - 1) {
      updateReview();
    }
    saveDraft();
  }

  function validateCurrentStep() {
    const inputs = [...steps[currentStep].querySelectorAll("input")];
    if (currentStep === 2) {
      const password = field("password");
      const confirmation = field("confirm_password");
      confirmation.setCustomValidity(
        confirmation.value && confirmation.value !== password.value
          ? "The passwords do not match."
          : ""
      );
    }
    if (currentStep === 1) {
      validateEmail();
    }

    const invalidInput = inputs.find((input) => !input.checkValidity());
    if (invalidInput) {
      invalidInput.reportValidity();
      invalidInput.focus();
      return false;
    }

    function validateEmail() {
      const email = field("email");
      if (email.value && !/^[^@\s]+@gmail\.com$/i.test(email.value.trim())) {
        email.setCustomValidity("Not valid email address.");
      } else {
        email.setCustomValidity("");
      }
    }
    return true;
  }

  restoreDraft();
  updateStep();

  form.addEventListener("input", (event) => {
    if (event.target.name === "email") {
      validateEmail();
    }
    if (event.target.name === "password" || event.target.name === "confirm_password") {
      field("confirm_password").setCustomValidity("");
    }
    saveDraft();
  });

  continueButton.addEventListener("click", () => {
    if (!validateCurrentStep()) {
      return;
    }
    currentStep = Math.min(currentStep + 1, steps.length - 1);
    updateStep();
    steps[currentStep].querySelector("input")?.focus();
  });

  backButton.addEventListener("click", () => {
    currentStep = Math.max(currentStep - 1, 0);
    updateStep();
    steps[currentStep].querySelector("input")?.focus();
  });

  form.addEventListener("submit", (event) => {
    validateEmail();
    field("confirm_password").setCustomValidity(
      field("confirm_password").value !== field("password").value
        ? "The passwords do not match."
        : ""
    );
    const invalidInput = [...form.querySelectorAll("input")].find(
      (input) => !input.checkValidity()
    );
    if (invalidInput) {
      event.preventDefault();
      currentStep = Number(invalidInput.closest("[data-step]").dataset.step);
      updateStep();
      invalidInput.reportValidity();
      invalidInput.focus();
      return;
    }
    window.sessionStorage.removeItem(draftKey);
  });
})();
