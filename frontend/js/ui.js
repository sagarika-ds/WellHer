// ui.js: small helpers that several pages use to show messages and busy buttons.

// Show a coloured message box. `kind` is "success", "error", "warning" or "info"
// (the matching .alert-* classes are in style.css). Pass an empty text to hide it.
export function showAlert(box, kind, text) {
  if (!text) {
    box.className = "alert hidden";
    box.textContent = "";
    return;
  }
  box.className = "alert alert-" + kind;
  // Errors are announced immediately by screen readers; other messages politely.
  box.setAttribute("role", kind === "error" ? "alert" : "status");
  box.textContent = text;  // textContent (not innerHTML) so server text can never inject HTML
}

// Disable a button while a request runs, so it can't be submitted twice.
export function setBusy(button, busy, busyLabel) {
  if (busy) {
    button.dataset.label = button.textContent;
    button.textContent = busyLabel;
    button.disabled = true;
  } else {
    button.textContent = button.dataset.label || button.textContent;
    button.disabled = false;
  }
}

// Build one row for a .list: main text, a muted detail line, and optional buttons.
// `actions` is a list like [{ label: "Delete", onClick: fn, danger: true }].
// Everything is created with createElement/textContent, so data is never treated as HTML.
export function listItem(text, detail, actions = []) {
  const li = document.createElement("li");

  const info = document.createElement("div");
  const main = document.createElement("div");
  main.textContent = text;
  info.appendChild(main);
  if (detail) {
    const small = document.createElement("div");
    small.className = "muted small";
    small.textContent = detail;
    info.appendChild(small);
  }
  li.appendChild(info);

  if (actions.length > 0) {
    const buttons = document.createElement("div");
    buttons.className = "row";
    for (const action of actions) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = action.danger ? "btn btn-small btn-danger" : "btn btn-small btn-secondary";
      button.textContent = action.label;
      button.addEventListener("click", action.onClick);
      buttons.appendChild(button);
    }
    li.appendChild(buttons);
  }
  return li;
}

// Replace a list's contents with rows, or with a muted message if there are none.
export function fillList(list, rows, emptyText) {
  list.replaceChildren(...rows);
  if (rows.length === 0) {
    const li = document.createElement("li");
    li.className = "muted";
    li.textContent = emptyText;
    list.appendChild(li);
  }
}

// ---- Dates ----------------------------------------------------------------
// The backend uses two formats:
//   dates:      "2026-11-12"                  (periods, daily entries)
//   timestamps: "2026-11-12T08:30:00.000Z"    (symptoms, mood) - must include a timezone

// Today as "YYYY-MM-DD" in the visitor's own timezone (for <input type="date">).
export function todayIso() {
  return localIsoDate(new Date());
}

// Any Date (or timestamp string) -> "YYYY-MM-DD" in the visitor's own timezone.
// Used to group mood entries by the day they happened for the visitor.
export function localIsoDate(value) {
  const d = new Date(value);
  return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
}

// The last `count` days as "YYYY-MM-DD", oldest first, ending with today.
export function lastDays(count) {
  const days = [];
  for (let back = count - 1; back >= 0; back--) {
    const d = new Date();
    d.setDate(d.getDate() - back);
    days.push(localIsoDate(d));
  }
  return days;
}

// Whole days from one "YYYY-MM-DD" to another (e.g. "2026-11-01" -> "2026-11-03" is 2).
export function daysBetween(fromIso, toIso) {
  const [y1, m1, d1] = fromIso.split("-").map(Number);
  const [y2, m2, d2] = toIso.split("-").map(Number);
  // Date.UTC ignores daylight-saving changes, so every day is exactly 24 hours.
  return Math.round((Date.UTC(y2, m2 - 1, d2) - Date.UTC(y1, m1 - 1, d1)) / 86400000);
}

// "2026-11-12" -> "Thu"
export function weekdayShort(isoDate) {
  const [y, m, d] = isoDate.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(undefined, { weekday: "short" });
}

// Now as "YYYY-MM-DDTHH:MM" (the format <input type="datetime-local"> expects).
export function nowForInput() {
  const d = new Date();
  return todayIso() + "T" + pad(d.getHours()) + ":" + pad(d.getMinutes());
}

// A datetime-local value (local time, no timezone) -> a UTC timestamp the backend accepts.
export function inputToTimestamp(value) {
  return new Date(value).toISOString();
}

// "2026-11-12" -> "12 Nov 2026"
export function formatDate(isoDate) {
  const [y, m, d] = isoDate.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

// A timestamp -> "12 Nov, 08:30" in the visitor's timezone.
export function formatDateTime(timestamp) {
  return new Date(timestamp).toLocaleString(undefined, {
    day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
  });
}

function pad(n) {
  return String(n).padStart(2, "0");
}

// "back_pain" -> "Back pain"
export function prettyCode(code) {
  const words = code.replace(/_/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

// Empty input -> null (the backend's "not given"), otherwise a number.
export function numberOrNull(value) {
  return value === "" ? null : Number(value);
}

// The backend's password rules (see RegisterRequest in backend/app/schemas/auth.py).
// Checking them here gives a clear message before anything is sent.
// Returns an error message, or "" if the password is acceptable.
export function passwordProblem(password, email) {
  if (password.length < 12) {
    return "Password must be at least 12 characters.";
  }
  if (new Set(password).size < 5) {
    return "Password is too repetitive: use at least 5 different characters.";
  }
  const namePart = (email || "").split("@")[0].toLowerCase();
  if (namePart.length >= 4 && password.toLowerCase().includes(namePart)) {
    return "Password must not contain the part of your email before the @.";
  }
  return "";
}
