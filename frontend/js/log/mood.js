// log/mood.js: add moods. (The backend has no edit or delete for moods.)
//
// Backend calls:
//   GET  /mood?limit=10  -> newest first: [{ id, logged_at, mood_score, tags }]
//   POST /mood           { logged_at, mood_score, tags: ["tired", "calm"] }

import { api } from "../api.js";
import { fillList, formatDateTime, inputToTimestamp, listItem, nowForInput, setBusy, showAlert } from "../ui.js";

const MOOD_WORDS = { 1: "Very low", 2: "Low", 3: "Okay", 4: "Good", 5: "Very good" };

const form = document.getElementById("mood-form");
const message = document.getElementById("mood-message");
const submitButton = document.getElementById("mood-submit");
const list = document.getElementById("mood-list");

export function setupMood() {
  form.logged_at.value = nowForInput();  // the backend rejects times in the future
  form.addEventListener("submit", save);
  loadList();
}

async function loadList() {
  try {
    const moods = await api("/mood?limit=10");
    const rows = moods.map((m) => {
      const tags = m.tags.length > 0 ? " · " + m.tags.join(", ") : "";
      return listItem(MOOD_WORDS[m.mood_score] + " (" + m.mood_score + "/5)", formatDateTime(m.logged_at) + tags);
    });
    fillList(list, rows, "No moods logged yet.");
  } catch (error) {
    showAlert(message, "error", error.message);
  }
}

async function save(event) {
  event.preventDefault();

  // "tired, Calm ,," -> ["tired", "calm"]  (the backend also lower-cases and trims)
  const tags = form.tags.value
    .split(",")
    .map((t) => t.trim().toLowerCase())
    .filter((t) => t !== "");
  if (tags.length > 10) {
    showAlert(message, "error", "Use at most 10 tags.");
    return;
  }

  const body = {
    logged_at: inputToTimestamp(form.logged_at.value),
    mood_score: Number(form.mood_score.value),
    tags: tags,
  };

  showAlert(message, "", "");
  setBusy(submitButton, true, "Saving…");
  try {
    await api("/mood", { method: "POST", body: body });
    showAlert(message, "success", "Mood saved.");
    form.tags.value = "";
    form.logged_at.value = nowForInput();
    loadList();
  } catch (error) {
    showAlert(message, "error", error.message);
  }
  setBusy(submitButton, false);
}
