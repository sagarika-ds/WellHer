// forgot.js: the two steps of resetting a password.
//
// Backend calls:
//   POST /auth/forgot-password  { email }                  -> always "ok", whether or not the email exists
//   POST /auth/reset-password   { token, new_password }    -> ok, or error "invalid_reset_token"
//
// The backend never says whether an email has an account (so nobody can use this page to
// find out who is registered). That's why step 1 shows the same message either way.

import { api } from "./api.js";
import { passwordProblem, setBusy, showAlert } from "./ui.js";

const requestForm = document.getElementById("request-form");
const requestMessage = document.getElementById("request-message");
const requestButton = document.getElementById("request-submit");

const resetForm = document.getElementById("reset-form");
const resetMessage = document.getElementById("reset-message");
const resetButton = document.getElementById("reset-submit");

// A reset link could carry the code as ?token=..., so fill it in if present.
const tokenFromLink = new URLSearchParams(location.search).get("token");
if (tokenFromLink) {
  resetForm.token.value = tokenFromLink;
}

requestForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  showAlert(requestMessage, "", "");
  setBusy(requestButton, true, "Sending…");
  try {
    await api("/auth/forgot-password", {
      method: "POST",
      auth: false,
      body: { email: requestForm.email.value.trim() },
    });
    showAlert(requestMessage, "success",
      "If an account exists for that email, a reset code is on its way. It is valid for 30 minutes.");
    resetForm.token.focus();
  } catch (error) {
    showAlert(requestMessage, "error", error.message);
  }
  setBusy(requestButton, false);
});

resetForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const newPassword = resetForm.new_password.value;
  const problem = passwordProblem(newPassword, requestForm.email.value);
  if (problem) {
    showAlert(resetMessage, "error", problem);
    return;
  }

  showAlert(resetMessage, "", "");
  setBusy(resetButton, true, "Changing…");
  try {
    await api("/auth/reset-password", {
      method: "POST",
      auth: false,
      body: { token: resetForm.token.value.trim(), new_password: newPassword },
    });
    location.href = "login.html?reset=done";
  } catch (error) {
    showAlert(resetMessage, "error", error.message);
    setBusy(resetButton, false);
  }
});
