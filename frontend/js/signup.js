// signup.js: create an account, then log straight in.
//
// Backend calls:
//   POST /auth/register  { email, password, display_name, consents: [{purpose, granted}] }  -> the new user
//   POST /auth/login     { email, password }                                                -> tokens

import { api } from "./api.js";
import { isLoggedIn, saveTokens } from "./auth.js";
import { passwordProblem, setBusy, showAlert } from "./ui.js";

if (isLoggedIn()) {
  location.replace("home.html");
}

const form = document.getElementById("signup-form");
const message = document.getElementById("message");
const submitButton = document.getElementById("submit");

form.addEventListener("submit", async (event) => {
  event.preventDefault();  // stop the browser's own form submit; we send it with fetch instead

  const displayName = form.display_name.value.trim();
  const email = form.email.value.trim();
  const password = form.password.value;

  // One entry per purpose: granted = whether its checkbox is ticked.
  const consents = [];
  for (const box of form.querySelectorAll('input[name="consent"]')) {
    consents.push({ purpose: box.value, granted: box.checked });
  }

  const problem = passwordProblem(password, email);
  if (problem) {
    showAlert(message, "error", problem);
    form.password.focus();
    return;
  }

  showAlert(message, "", "");
  setBusy(submitButton, true, "Creating account…");
  try {
    await api("/auth/register", {
      method: "POST",
      auth: false,
      body: { email: email, password: password, display_name: displayName, consents: consents },
    });
    const tokens = await api("/auth/login", {
      method: "POST",
      auth: false,
      body: { email: email, password: password },
    });
    saveTokens(tokens);
    location.href = "home.html";
  } catch (error) {
    if (error.code === "conflict") {
      showAlert(message, "error", "An account with this email already exists. Try logging in.");
    } else {
      showAlert(message, "error", error.message);
    }
    setBusy(submitButton, false);
  }
});
