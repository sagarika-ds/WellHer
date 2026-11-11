// log/symptom.js: add and delete symptoms. (The backend has no "edit" for symptoms.)
//
// Backend calls:
//   GET    /symptoms?limit=10  -> newest first: [{ id, logged_at, symptom_code, severity, cycle_id }]
//   POST   /symptoms           { logged_at, symptom_code, severity }
//   DELETE /symptoms/{id}

import { api } from "../api.js";
import {
  fillList, formatDateTime, inputToTimestamp, listItem, nowForInput, prettyCode, setBusy, showAlert,
} from "../ui.js";

// The backend only accepts these 24 codes (backend/app/core/ontology.py, SYMPTOM_CODES).
// If they ever change there, update this list too.
const SYMPTOM_CODES = [
  "fatigue", "headache", "cramps", "bloating", "nausea", "back_pain", "pelvic_pain",
  "breast_tenderness", "mood_swings", "irritability", "anxiety", "low_mood", "insomnia",
  "acne", "dizziness", "hot_flashes", "appetite_change", "cravings", "joint_pain",
  "muscle_pain", "spotting", "heavy_bleeding", "constipation", "diarrhea",
];

const form = document.getElementById("symptom-form");
const message = document.getElementById("symptom-message");
const submitButton = document.getElementById("symptom-submit");
const list = document.getElementById("symptom-list");

export function setupSymptoms() {
  // Fill the drop-down, sorted by the label people read.
  const sorted = [...SYMPTOM_CODES].sort((a, b) => prettyCode(a).localeCompare(prettyCode(b)));
  for (const code of sorted) {
    const option = document.createElement("option");
    option.value = code;               // what the backend expects, e.g. "back_pain"
    option.textContent = prettyCode(code);  // what people see, e.g. "Back pain"
    form.symptom_code.appendChild(option);
  }
  form.logged_at.value = nowForInput();  // the backend rejects times in the future
  form.addEventListener("submit", save);
  loadList();
}

async function loadList() {
  try {
    const symptoms = await api("/symptoms?limit=10");
    const rows = symptoms.map((s) =>
      listItem(prettyCode(s.symptom_code) + " · " + s.severity + "/5", formatDateTime(s.logged_at), [
        { label: "Delete", onClick: () => remove(s), danger: true },
      ]));
    fillList(list, rows, "No symptoms logged yet.");
  } catch (error) {
    showAlert(message, "error", error.message);
  }
}

async function save(event) {
  event.preventDefault();
  const body = {
    logged_at: inputToTimestamp(form.logged_at.value),
    symptom_code: form.symptom_code.value,
    severity: Number(form.severity.value),
  };

  showAlert(message, "", "");
  setBusy(submitButton, true, "Saving…");
  try {
    await api("/symptoms", { method: "POST", body: body });
    showAlert(message, "success", prettyCode(body.symptom_code) + " saved.");
    form.logged_at.value = nowForInput();
    loadList();
  } catch (error) {
    showAlert(message, "error", error.message);
  }
  setBusy(submitButton, false);
}

async function remove(s) {
  if (!confirm("Delete " + prettyCode(s.symptom_code) + " from " + formatDateTime(s.logged_at) + "?")) {
    return;
  }
  try {
    await api("/symptoms/" + s.id, { method: "DELETE" });
    showAlert(message, "success", "Symptom deleted.");
    loadList();
  } catch (error) {
    showAlert(message, "error", error.message);
  }
}
