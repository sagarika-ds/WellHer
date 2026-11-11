// settings/history.js: who viewed or changed your data, and when (the backend's audit log).
//
// Backend call:
//   GET /privacy/access-history?limit=20&offset=0
//     -> newest first: [{ timestamp, action, resource, outcome, ip }]
//
// The backend uses short technical names ("read", "cycle_records"). We show plain words.

import { api } from "../api.js";
import { fillList, formatDateTime, listItem, prettyCode, setBusy, showAlert } from "../ui.js";

const PAGE_SIZE = 20;

const ACTIONS = {
  read: "Viewed",
  create: "Added",
  update: "Changed",
  delete: "Deleted",
  login: "Logged in",
  logout: "Logged out",
  refresh: "Session renewed",
  register: "Account created",
  consent_granted: "Consent turned on",
  consent_revoked: "Consent turned off",
  ai_settings_update: "AI settings changed",
  export: "Data downloaded",
  password_reset_requested: "Password reset requested",
  password_reset: "Password changed",
  account_delete: "Account deletion attempted",
  refresh_reuse_detected: "Old session token reused: all sessions ended",
};

const RESOURCES = {
  cycle_records: "periods",
  symptom_logs: "symptoms",
  lifestyle_records: "daily entries",
  mood_records: "moods",
  health_profile: "profile",
  ai_settings: "AI settings",
  consent: "",    // already clear from the action, e.g. "Consent turned on"
  session: "",
  user: "",
  account: "",
};

const message = document.getElementById("history-message");
const list = document.getElementById("history-list");
const moreButton = document.getElementById("history-more");

let shown = 0;  // how many entries are on screen, i.e. the offset for "Show more"

export function setupHistory() {
  moreButton.addEventListener("click", loadMore);
  loadMore();
}

async function loadMore() {
  setBusy(moreButton, true, "Loading…");
  try {
    const items = await api("/privacy/access-history?limit=" + PAGE_SIZE + "&offset=" + shown);
    const rows = items.map((item) => listItem(describe(item), detail(item)));
    if (shown === 0) {
      fillList(list, rows, "Nothing recorded yet.");
    } else {
      list.append(...rows);
    }
    shown += items.length;
    // A full page means there may be more.
    moreButton.classList.toggle("hidden", items.length < PAGE_SIZE);
  } catch (error) {
    showAlert(message, "error", error.message);
  }
  setBusy(moreButton, false);
}

// { action: "read", resource: "cycle_records" } -> "Viewed periods"
function describe(item) {
  const action = ACTIONS[item.action] || prettyCode(item.action);
  let resource = item.resource;
  if (resource !== null && resource in RESOURCES) {
    resource = RESOURCES[resource];
  }
  return resource ? action + " " + resource : action;
}

function detail(item) {
  let text = formatDateTime(item.timestamp);
  if (item.outcome !== "success") {
    text += " · " + (item.outcome === "failure" ? "failed" : item.outcome);  // e.g. a wrong password
  }
  if (item.ip) {
    text += " · from " + item.ip;
  }
  return text;
}
