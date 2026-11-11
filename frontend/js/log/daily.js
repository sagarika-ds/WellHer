// log/daily.js: one entry per day for sleep, water, activity and stress.
//
// Backend calls:
//   GET  /lifestyle?limit=14  -> newest first: [{ id, date, sleep_hours, sleep_quality,
//                                                 activity_minutes, water_ml, stress_level }]
//   POST /lifestyle           { date, sleep_hours, sleep_quality, activity_minutes, water_ml, stress_level }
//   PUT  /lifestyle/{id}      same body: replaces the entry
//
// The backend allows only ONE entry per date (a second POST answers "conflict"). So when you save
// a date that already has an entry, we update that entry instead of creating a new one.
//
// Food notes ("nutrition_notes") are left out on purpose: the backend stores them encrypted and never
// sends them back, but an update overwrites them, so editing from here would silently erase them.

import { api } from "../api.js";
import { fillList, formatDate, listItem, numberOrNull, setBusy, showAlert, todayIso } from "../ui.js";

const form = document.getElementById("daily-form");
const message = document.getElementById("daily-message");
const submitButton = document.getElementById("daily-submit");
const cancelButton = document.getElementById("daily-cancel");
const list = document.getElementById("daily-list");

let entries = [];  // the entries currently shown, used to find an existing one for a date

export function setupDaily() {
  form.date.value = todayIso();
  form.date.max = todayIso();
  form.date.addEventListener("change", fillFromExisting);
  form.addEventListener("submit", save);
  cancelButton.addEventListener("click", resetForm);
  loadList();
}

async function loadList() {
  try {
    entries = await api("/lifestyle?limit=14");
    const rows = entries.map((e) =>
      listItem(formatDate(e.date), describe(e), [
        { label: "Edit", onClick: () => edit(e) },
      ]));
    fillList(list, rows, "No days logged yet.");
    fillFromExisting();
  } catch (error) {
    showAlert(message, "error", error.message);
  }
}

function describe(e) {
  const parts = [];
  if (e.sleep_hours !== null) parts.push("Sleep " + e.sleep_hours + " h");
  if (e.sleep_quality !== null) parts.push("quality " + e.sleep_quality + "/5");
  if (e.water_ml !== null) parts.push("Water " + e.water_ml + " ml");
  if (e.activity_minutes !== null) parts.push("Activity " + e.activity_minutes + " min");
  if (e.stress_level !== null) parts.push("Stress " + e.stress_level + "/5");
  return parts.join(" · ") || "Nothing recorded";
}

// If the chosen date already has an entry, show its values so saving updates them.
// If not, empty the fields so values from another day aren't saved by mistake.
function fillFromExisting() {
  const existing = entries.find((e) => e.date === form.date.value);
  if (existing) {
    edit(existing);
  } else {
    for (const name of ["sleep_hours", "sleep_quality", "water_ml", "activity_minutes", "stress_level"]) {
      form[name].value = "";
    }
    submitButton.textContent = "Save day";
    cancelButton.classList.add("hidden");
  }
}

function edit(e) {
  form.date.value = e.date;
  form.sleep_hours.value = e.sleep_hours ?? "";
  form.sleep_quality.value = e.sleep_quality ?? "";
  form.water_ml.value = e.water_ml ?? "";
  form.activity_minutes.value = e.activity_minutes ?? "";
  form.stress_level.value = e.stress_level ?? "";
  submitButton.textContent = "Update day";
  cancelButton.classList.remove("hidden");
}

function resetForm() {
  form.reset();
  form.date.value = todayIso();
  fillFromExisting();
}

async function save(event) {
  event.preventDefault();
  const body = {
    date: form.date.value,
    sleep_hours: numberOrNull(form.sleep_hours.value),
    sleep_quality: numberOrNull(form.sleep_quality.value),
    water_ml: numberOrNull(form.water_ml.value),
    activity_minutes: numberOrNull(form.activity_minutes.value),
    stress_level: numberOrNull(form.stress_level.value),
  };

  showAlert(message, "", "");
  setBusy(submitButton, true, "Saving…");
  const existing = entries.find((e) => e.date === body.date);
  try {
    if (existing) {
      await api("/lifestyle/" + existing.id, { method: "PUT", body: body });
    } else {
      await api("/lifestyle", { method: "POST", body: body });
    }
  } catch (error) {
    showAlert(message, "error", error.message);
    setBusy(submitButton, false);
    return;
  }
  // Un-busy first: it restores the old button label, which loadList() then sets correctly.
  setBusy(submitButton, false);
  showAlert(message, "success", formatDate(body.date) + (existing ? " updated." : " saved."));
  loadList();
}
