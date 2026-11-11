// settings/account.js: download my data, and delete my account.
//
// Backend calls:
//   POST   /privacy/export   -> { job_id, status: "ready", data: { user, profile, cycles, ... } }
//   DELETE /privacy/account  { password, confirm: "DELETE" }   -> 204 (nothing back)

import { api } from "../api.js";
import { clearTokens } from "../auth.js";
import { setBusy, showAlert, todayIso } from "../ui.js";

const exportButton = document.getElementById("export-button");
const exportMessage = document.getElementById("export-message");

const deleteForm = document.getElementById("delete-form");
const deleteMessage = document.getElementById("delete-message");
const deleteButton = document.getElementById("delete-submit");

export function setupAccount() {
  exportButton.addEventListener("click", downloadData);
  deleteForm.addEventListener("submit", deleteAccount);
}

// The backend sends the data in the response; the browser saves it as a file.
async function downloadData() {
  showAlert(exportMessage, "", "");
  setBusy(exportButton, true, "Preparing…");
  try {
    const result = await api("/privacy/export", { method: "POST" });
    const text = JSON.stringify(result.data, null, 2);  // indented, so it is readable
    const file = new Blob([text], { type: "application/json" });

    // A temporary link with the "download" attribute makes the browser save the file.
    const link = document.createElement("a");
    link.href = URL.createObjectURL(file);
    link.download = "wellher-data-" + todayIso() + ".json";
    link.click();
    // Free the memory a moment later (revoking straight away can cancel the download in some browsers).
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);

    showAlert(exportMessage, "success", "Your data was downloaded as " + link.download + ".");
  } catch (error) {
    showAlert(exportMessage, "error", error.message);
  }
  setBusy(exportButton, false);
}

async function deleteAccount(event) {
  event.preventDefault();
  if (deleteForm.confirm.value !== "DELETE") {
    showAlert(deleteMessage, "error", "Type DELETE in capital letters to confirm.");
    return;
  }
  // A last check, because this cannot be undone.
  if (!confirm("Delete your account and all your data permanently?")) {
    return;
  }

  showAlert(deleteMessage, "", "");
  setBusy(deleteButton, true, "Deleting…");
  try {
    await api("/privacy/account", {
      method: "DELETE",
      body: { password: deleteForm.password.value, confirm: "DELETE" },
    });
  } catch (error) {
    showAlert(deleteMessage, "error", error.message);  // e.g. "Password is incorrect."
    setBusy(deleteButton, false);
    return;
  }
  // The account is gone and the backend has ended all its sessions.
  clearTokens();
  location.href = "index.html?deleted=1";
}
