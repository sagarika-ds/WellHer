// settings/profile.js: the optional health profile.
//
// Backend calls:
//   GET /profile  -> { date_of_birth, height_cm, weight_kg, typical_cycle_length, contraceptive_use,
//                      activity_level, conditions_self_reported: [], dietary_prefs: [], goals: [] }
//   PUT /profile  same fields. It REPLACES the whole profile, so we always send every field.

import { api } from "../api.js";
import { numberOrNull, setBusy, showAlert, todayIso } from "../ui.js";

const form = document.getElementById("profile-form");
const message = document.getElementById("profile-message");
const submitButton = document.getElementById("profile-submit");

export function setupProfile() {
  form.date_of_birth.max = todayIso();
  form.addEventListener("submit", save);
  load();
}

async function load() {
  try {
    fill(await api("/profile"));
  } catch (error) {
    showAlert(message, "error", error.message);
  }
}

// Put the server's values into the form. null (not given) becomes an empty field.
function fill(p) {
  form.date_of_birth.value = p.date_of_birth ?? "";
  form.height_cm.value = p.height_cm ?? "";
  form.weight_kg.value = p.weight_kg ?? "";
  form.typical_cycle_length.value = p.typical_cycle_length ?? "";
  form.activity_level.value = p.activity_level ?? "";
  // The select has "yes", "no" and "" (not given); the backend has true, false and null.
  form.contraceptive_use.value = p.contraceptive_use === null ? "" : (p.contraceptive_use ? "yes" : "no");
  form.conditions_self_reported.value = p.conditions_self_reported.join(", ");
  form.dietary_prefs.value = p.dietary_prefs.join(", ");
  form.goals.value = p.goals.join(", ");
}

// "PCOS, asthma ,," -> ["PCOS", "asthma"]
function splitList(text) {
  return text.split(",").map((item) => item.trim()).filter((item) => item !== "");
}

async function save(event) {
  event.preventDefault();
  const contraceptive = form.contraceptive_use.value;
  const body = {
    date_of_birth: form.date_of_birth.value || null,
    height_cm: numberOrNull(form.height_cm.value),
    weight_kg: numberOrNull(form.weight_kg.value),
    typical_cycle_length: numberOrNull(form.typical_cycle_length.value),
    activity_level: form.activity_level.value || null,
    contraceptive_use: contraceptive === "" ? null : contraceptive === "yes",
    conditions_self_reported: splitList(form.conditions_self_reported.value),
    dietary_prefs: splitList(form.dietary_prefs.value),
    goals: splitList(form.goals.value),
  };

  showAlert(message, "", "");
  setBusy(submitButton, true, "Saving…");
  try {
    fill(await api("/profile", { method: "PUT", body: body }));  // show what the server stored
    showAlert(message, "success", "Profile saved.");
  } catch (error) {
    showAlert(message, "error", error.message);
  }
  setBusy(submitButton, false);
}
