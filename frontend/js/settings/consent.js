// settings/consent.js: the four consent switches. Each one is saved as soon as it changes.
//
// Backend calls:
//   GET /consents             -> [{ purpose, granted, version, granted_at, revoked_at }]
//   PUT /consents/{purpose}   { granted: true | false }
//
// Purposes: health_tracking, ml_processing, llm_external, analytics.

import { api } from "../api.js";
import { showAlert } from "../ui.js";

const message = document.getElementById("consent-message");
const boxes = document.querySelectorAll('input[name="consent"]');

export function setupConsents() {
  for (const box of boxes) {
    box.disabled = true;  // until we know the current values
    box.addEventListener("change", () => save(box));
  }
  load();
}

async function load() {
  try {
    const consents = await api("/consents");
    for (const box of boxes) {
      const consent = consents.find((c) => c.purpose === box.value);
      box.checked = Boolean(consent && consent.granted);
      box.disabled = false;
    }
  } catch (error) {
    showAlert(message, "error", error.message);
  }
}

async function save(box) {
  const granted = box.checked;
  box.disabled = true;
  try {
    await api("/consents/" + box.value, { method: "PUT", body: { granted: granted } });
    const name = box.parentElement.textContent.trim().split(".")[0];  // the first sentence of the label
    showAlert(message, "success", (granted ? "Turned on: " : "Turned off: ") + name + ".");
  } catch (error) {
    box.checked = !granted;  // the change didn't happen, so put the switch back
    showAlert(message, "error", error.message);
  }
  box.disabled = false;
}
