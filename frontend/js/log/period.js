// log/period.js: add, edit and delete periods.
//
// Backend calls:
//   GET    /cycles?limit=10   -> newest first: [{ id, start_date, end_date, cycle_length_days, flow_intensity, notes }]
//   POST   /cycles            { start_date, end_date, flow_intensity, notes }
//   PUT    /cycles/{id}       same body: replaces the record
//   DELETE /cycles/{id}
//
// Backend rules: periods can't overlap, can't start in the future, and can't last more than 21 days.
// cycle_length_days is worked out by the backend (days until the next period started).

import { api } from "../api.js";
import { fillList, formatDate, listItem, numberOrNull, setBusy, showAlert, todayIso } from "../ui.js";

const form = document.getElementById("period-form");
const message = document.getElementById("period-message");
const submitButton = document.getElementById("period-submit");
const cancelButton = document.getElementById("period-cancel");
const list = document.getElementById("period-list");

let editingId = null;  // the id of the period being edited, or null when adding a new one

export function setupPeriod() {
  form.start_date.max = todayIso();
  form.end_date.max = todayIso();
  form.addEventListener("submit", save);
  cancelButton.addEventListener("click", stopEditing);
  loadList();
}

async function loadList() {
  try {
    const periods = await api("/cycles?limit=10");
    const rows = periods.map((p) =>
      listItem(describe(p), detail(p), [
        { label: "Edit", onClick: () => startEditing(p) },
        { label: "Delete", onClick: () => remove(p), danger: true },
      ]));
    fillList(list, rows, "No periods logged yet.");
  } catch (error) {
    showAlert(message, "error", error.message);
  }
}

function describe(p) {
  const end = p.end_date ? formatDate(p.end_date) : "ongoing";
  return formatDate(p.start_date) + " – " + end;
}

function detail(p) {
  const parts = [];
  if (p.flow_intensity) parts.push("Flow " + p.flow_intensity + "/5");
  if (p.cycle_length_days) parts.push("Cycle length " + p.cycle_length_days + " days");
  if (p.notes) parts.push(p.notes);
  return parts.join(" · ");
}

async function save(event) {
  event.preventDefault();
  const body = {
    start_date: form.start_date.value,
    end_date: form.end_date.value || null,
    flow_intensity: numberOrNull(form.flow_intensity.value),
    notes: form.notes.value.trim() || null,
  };

  showAlert(message, "", "");
  setBusy(submitButton, true, "Saving…");
  const wasEditing = editingId !== null;
  try {
    if (wasEditing) {
      await api("/cycles/" + editingId, { method: "PUT", body: body });
    } else {
      await api("/cycles", { method: "POST", body: body });
    }
  } catch (error) {
    // e.g. "This period overlaps an existing record starting 2026-11-01."
    showAlert(message, "error", error.message);
    setBusy(submitButton, false);
    return;
  }
  // Un-busy first: it restores the old button label, which stopEditing() then sets correctly.
  setBusy(submitButton, false);
  stopEditing();
  showAlert(message, "success", wasEditing ? "Period updated." : "Period saved.");
  loadList();
}

function startEditing(p) {
  editingId = p.id;
  form.start_date.value = p.start_date;
  form.end_date.value = p.end_date || "";
  form.flow_intensity.value = p.flow_intensity || "";
  form.notes.value = p.notes || "";
  submitButton.textContent = "Update period";
  cancelButton.classList.remove("hidden");
  showAlert(message, "info", "Editing the period that started " + formatDate(p.start_date) + ".");
  form.start_date.focus();
}

function stopEditing() {
  editingId = null;
  form.reset();
  submitButton.textContent = "Save period";
  cancelButton.classList.add("hidden");
}

async function remove(p) {
  if (!confirm("Delete the period that started " + formatDate(p.start_date) + "?")) {
    return;
  }
  try {
    await api("/cycles/" + p.id, { method: "DELETE" });
    if (editingId === p.id) stopEditing();
    showAlert(message, "success", "Period deleted.");
    loadList();
  } catch (error) {
    showAlert(message, "error", error.message);
  }
}
