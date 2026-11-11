// settings/ai.js: AI settings. The backend stores these now; the AI features come later.
//
// Backend calls:
//   GET /privacy/ai-settings -> { personalization_enabled, external_llm_allowed,
//                                 context_allowlist: ["cycle_summary", ...], chat_retention_days }
//   PUT /privacy/ai-settings    same fields
//
// Turning on "external_llm_allowed" needs the llm_external consent; otherwise the backend
// answers 403 "consent_required".

import { api } from "../api.js";
import { setBusy, showAlert } from "../ui.js";

// The names the backend accepts in context_allowlist (CONTEXT_KEYS in backend/app/schemas/privacy.py).
const CONTEXT_CHOICES = {
  cycle_summary: "Cycle summary",
  symptom_summary: "Symptom summary",
  lifestyle_summary: "Sleep, activity and stress summary",
  mood_summary: "Mood summary",
  patterns: "Patterns found in my logs",
  deviations: "Changes from my usual pattern",
  preferences: "My preferences",
};

const form = document.getElementById("ai-form");
const message = document.getElementById("ai-message");
const submitButton = document.getElementById("ai-submit");
const contextBox = document.getElementById("ai-context");

export function setupAi() {
  // One checkbox per allowed name, built with createElement like the lists.
  for (const [value, text] of Object.entries(CONTEXT_CHOICES)) {
    const label = document.createElement("label");
    label.className = "check";
    const box = document.createElement("input");
    box.type = "checkbox";
    box.name = "context";
    box.value = value;
    const span = document.createElement("span");
    span.textContent = text;
    label.append(box, span);
    contextBox.appendChild(label);
  }
  form.addEventListener("submit", save);
  load();
}

async function load() {
  try {
    fill(await api("/privacy/ai-settings"));
  } catch (error) {
    showAlert(message, "error", error.message);
  }
}

function fill(settings) {
  form.personalization_enabled.checked = settings.personalization_enabled;
  form.external_llm_allowed.checked = settings.external_llm_allowed;
  for (const box of contextBox.querySelectorAll("input")) {
    box.checked = settings.context_allowlist.includes(box.value);
  }
  form.chat_retention_days.value = settings.chat_retention_days;
}

async function save(event) {
  event.preventDefault();
  const chosen = [...contextBox.querySelectorAll("input:checked")].map((box) => box.value);
  const body = {
    personalization_enabled: form.personalization_enabled.checked,
    external_llm_allowed: form.external_llm_allowed.checked,
    context_allowlist: chosen,
    chat_retention_days: Number(form.chat_retention_days.value),
  };

  showAlert(message, "", "");
  setBusy(submitButton, true, "Saving…");
  try {
    fill(await api("/privacy/ai-settings", { method: "PUT", body: body }));
    showAlert(message, "success", "AI settings saved.");
  } catch (error) {
    if (error.code === "consent_required") {
      showAlert(message, "warning",
        "To allow an external AI service, first turn on \"Allow de-identified text to be sent to an " +
        "external AI service\" in the section above.");
    } else {
      showAlert(message, "error", error.message);
    }
  }
  setBusy(submitButton, false);
}
