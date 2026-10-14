(function () {
  "use strict";

  const logoutMeta = document.querySelector('meta[name="staff-tab-logout-url"]');
  if (!logoutMeta) {
    return;
  }

  let navigationStarted = false;
  let navigationResetTimer;

  function markNavigation() {
    navigationStarted = true;
    window.clearTimeout(navigationResetTimer);
    navigationResetTimer = window.setTimeout(function () {
      navigationStarted = false;
    }, 2000);
  }

  document.addEventListener("click", function (event) {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return;
    }
    const link = event.target.closest("a[href]");
    if (!link || link.hasAttribute("download") || (link.target && link.target !== "_self")) {
      return;
    }

    const destination = new URL(link.href, window.location.href);
    if (destination.origin === window.location.origin &&
        (destination.pathname !== window.location.pathname || destination.search !== window.location.search)) {
      markNavigation();
    }
  }, true);

  document.addEventListener("submit", function (event) {
    if (!event.defaultPrevented && (!event.target.target || event.target.target === "_self")) {
      markNavigation();
    }
  }, true);

  window.addEventListener("pagehide", function (event) {
    if (event.persisted || navigationStarted) {
      return;
    }

    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    const csrfToken = csrfInput?.value || document.cookie
      .split(";")
      .map(function (cookie) { return cookie.trim(); })
      .find(function (cookie) { return cookie.startsWith("csrftoken="); })
      ?.split("=")[1];

    if (!csrfToken) {
      return;
    }

    const body = new URLSearchParams({ csrfmiddlewaretoken: decodeURIComponent(csrfToken) });
    if (!navigator.sendBeacon(logoutMeta.content, body)) {
      fetch(logoutMeta.content, {
        method: "POST",
        body: body,
        credentials: "same-origin",
        keepalive: true,
        headers: { "X-CSRFToken": decodeURIComponent(csrfToken) },
      });
    }
  });
})();
