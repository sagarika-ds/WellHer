// login.js: log in and go to the page the visitor wanted (or Home).
//
// Backend call:
//   POST /auth/login  { email, password }  -> { access_token, refresh_token, expires_in }

import { api } from "./api.js";
import { isLoggedIn, saveTokens } from "./auth.js";
import { setBusy, showAlert } from "./ui.js";

const form = document.getElementById("login-form");
const message = document.getElementById("message");
const submitButton = document.getElementById("submit");

// Where to go after logging in. auth.js adds ?next=home.html when it redirects here.
// Only accept a plain page name like "home.html", so a link can't send people to another website.
const params = new URLSearchParams(location.search);
const next = /^[a-z]+\.html$/.test(params.get("next") || "") ? params.get("next") : "home.html";

if (isLoggedIn()) {
  location.replace(next);
}

// forgot.js sends people here with ?reset=done after they change their password.
if (params.get("reset") === "done") {
  showAlert(message, "success", "Your password has been changed. Please log in.");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  showAlert(message, "", "");
  setBusy(submitButton, true, "Logging in…");
  try {
    const tokens = await api("/auth/login", {
      method: "POST",
      auth: false,
      body: { email: form.email.value.trim(), password: form.password.value },
    });
    saveTokens(tokens);
    location.href = next;
  } catch (error) {
    // The backend's messages are safe to show: e.g. "Invalid email or password." or
    // "Too many attempts. Try again later." (after 5 failed tries in 15 minutes).
    showAlert(message, "error", error.message);
    setBusy(submitButton, false);
  }
});
