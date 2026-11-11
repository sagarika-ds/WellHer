// log.js: the Log page. It checks the storage consent, then starts the four sections.
// Each section (period, symptom, daily, mood) lives in its own small file in js/log/.
//
// Backend calls made here:
//   GET /consents                        -> [{ purpose, granted, ... }]
//   PUT /consents/health_tracking  { granted: true }
//
// Why the consent check: every record endpoint answers 403 "consent_required" unless the
// "health_tracking" consent is on. Checking first lets us explain that instead of failing.

import { api } from "./api.js";
import { startPrivatePage } from "./layout.js";
import { setBusy, showAlert } from "./ui.js";
import { setupPeriod } from "./log/period.js";
import { setupSymptoms } from "./log/symptom.js";
import { setupDaily } from "./log/daily.js";
import { setupMood } from "./log/mood.js";

const pageMessage = document.getElementById("page-message");
const consentBox = document.getElementById("consent-box");
const consentButton = document.getElementById("consent-button");
const sections = document.getElementById("sections");

async function loadPage() {
  try {
    const consents = await api("/consents");
    const tracking = consents.find((c) => c.purpose === "health_tracking");
    if (tracking && tracking.granted) {
      showSections();
    } else {
      consentBox.classList.remove("hidden");
    }
  } catch (error) {
    showAlert(pageMessage, "error", error.message);
  }
}

consentButton.addEventListener("click", async () => {
  setBusy(consentButton, true, "Saving…");
  try {
    await api("/consents/health_tracking", { method: "PUT", body: { granted: true } });
    consentBox.classList.add("hidden");
    showSections();
  } catch (error) {
    showAlert(pageMessage, "error", error.message);
    setBusy(consentButton, false);
  }
});

function showSections() {
  sections.classList.remove("hidden");
  setupPeriod();
  setupSymptoms();
  setupDaily();
  setupMood();
}

if (startPrivatePage()) {
  loadPage();
}
