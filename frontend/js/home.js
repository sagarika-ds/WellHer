// home.js: the Home page, a summary of what you have logged.
//
// Backend calls:
//   GET /auth/me                    -> { display_name, ... }               (for the greeting)
//   GET /consents                   -> [{ purpose, granted }]               (is "health_tracking" on?)
//   GET /cycles?limit=1             -> the latest period: [{ start_date, end_date, ... }]
//   GET /cycles/stats               -> { n_cycles, mean_length, min, max }  (worked out by the server)
//   GET /lifestyle/summary?days=30  -> { n_entries, avg_sleep_hours, avg_activity_minutes, avg_stress }
//   GET /lifestyle?date_from=...    -> daily entries of the last 7 days     (for the sleep bars)
//   GET /mood?date_from=...         -> moods of the last 7 days             (for the mood bars)
//   GET /symptoms?limit=5           -> the 5 newest symptoms
//
// Only display maths happens here (counting days, averaging a day's moods).
// There are no predictions: the backend doesn't provide them yet.

import { api } from "./api.js";
import { startPrivatePage } from "./layout.js";
import {
  daysBetween, fillList, formatDate, formatDateTime, inputToTimestamp, lastDays,
  listItem, localIsoDate, prettyCode, showAlert, todayIso, weekdayShort,
} from "./ui.js";

const message = document.getElementById("message");

async function loadPage() {
  try {
    const me = await api("/auth/me");
    document.getElementById("greeting").textContent = "Hello, " + me.display_name;

    // Every health endpoint needs the "health_tracking" consent, so check it first.
    const consents = await api("/consents");
    const tracking = consents.find((c) => c.purpose === "health_tracking");
    if (!tracking || !tracking.granted) {
      document.getElementById("consent-box").classList.remove("hidden");
      return;
    }
    document.getElementById("dashboard").classList.remove("hidden");

    // The sections don't depend on each other, so ask for them all at once.
    const week = lastDays(7);
    const [cycles, stats, summary, daily, moods, symptoms] = await Promise.all([
      api("/cycles?limit=1"),
      api("/cycles/stats"),
      api("/lifestyle/summary?days=30"),
      api("/lifestyle?date_from=" + week[0] + "&limit=7"),
      api("/mood?limit=200&date_from=" + encodeURIComponent(inputToTimestamp(week[0] + "T00:00"))),
      api("/symptoms?limit=5"),
    ]);

    showCycleDay(cycles[0]);
    showStats(stats);
    showSummary(summary);
    showSleep(week, daily);
    showMood(week, moods);
    showSymptoms(symptoms);
  } catch (error) {
    showAlert(message, "error", error.message);
  }
}

// ---- Cycle day ------------------------------------------------------------
// Day 1 is the first day of the latest period.
function showCycleDay(latest) {
  const value = document.getElementById("cycle-day");
  const detail = document.getElementById("cycle-detail");
  if (!latest) {
    value.textContent = "–";
    detail.textContent = "Log a period to see your cycle day.";
    return;
  }
  value.textContent = "Day " + (daysBetween(latest.start_date, todayIso()) + 1);
  if (latest.end_date) {
    detail.textContent = "Last period: " + formatDate(latest.start_date) + " to " + formatDate(latest.end_date);
  } else {
    detail.textContent = "Period started " + formatDate(latest.start_date) + " (no end date yet)";
  }
}

// ---- Cycle stats (calculated by the server) -------------------------------
function showStats(stats) {
  const value = document.getElementById("stats-mean");
  const detail = document.getElementById("stats-detail");
  if (stats.n_cycles === 0) {
    value.textContent = "–";
    detail.textContent = "Log at least two periods to see this.";
    return;
  }
  value.textContent = Math.round(stats.mean_length) + " days";
  const cycleWord = stats.n_cycles === 1 ? " cycle" : " cycles";
  detail.textContent = "From " + stats.n_cycles + cycleWord +
    " · shortest " + stats.min + ", longest " + stats.max + " days";
}

// ---- 30-day averages (calculated by the server) ---------------------------
function showSummary(summary) {
  const list = document.getElementById("summary-list");
  if (summary.n_entries === 0) {
    fillList(list, [], "No daily entries in the last 30 days.");
    return;
  }
  const rows = [
    summaryRow("Days logged", String(summary.n_entries)),
    summaryRow("Average sleep", orDash(summary.avg_sleep_hours, " h")),
    summaryRow("Average activity", orDash(summary.avg_activity_minutes, " min")),
    summaryRow("Average stress", orDash(summary.avg_stress, " / 5")),
  ];
  fillList(list, rows, "");
}

// One "label ........ value" row.
function summaryRow(label, value) {
  const li = document.createElement("li");
  const name = document.createElement("span");
  name.textContent = label;
  const number = document.createElement("strong");
  number.textContent = value;
  li.append(name, number);
  return li;
}

function orDash(number, unit) {
  return number === null ? "–" : (Math.round(number * 10) / 10) + unit;
}

// ---- Bars for the last 7 days ---------------------------------------------
function showSleep(week, entries) {
  const hoursByDay = {};
  for (const e of entries) {
    if (e.sleep_hours !== null) {
      hoursByDay[e.date] = e.sleep_hours;
    }
  }
  // 12 hours fills a bar to the top.
  drawBars(document.getElementById("sleep-bars"), week, hoursByDay, 12, " hours");
}

function showMood(week, moods) {
  // Several moods can be logged on one day: show that day's average.
  const scoresByDay = {};
  for (const m of moods) {
    const day = localIsoDate(m.logged_at);
    scoresByDay[day] = scoresByDay[day] || [];
    scoresByDay[day].push(m.mood_score);
  }
  const averageByDay = {};
  for (const day in scoresByDay) {
    const scores = scoresByDay[day];
    const total = scores.reduce((sum, score) => sum + score, 0);
    averageByDay[day] = Math.round((total / scores.length) * 10) / 10;
  }
  drawBars(document.getElementById("mood-bars"), week, averageByDay, 5, " out of 5");
}

// Draw one bar per day: the value on top, the bar, and the weekday underneath.
// `max` is the value that fills a bar to the top. Days with no value show "–".
function drawBars(container, days, valueByDay, max, unit) {
  const bars = days.map((day) => {
    const value = valueByDay[day];

    const bar = document.createElement("div");
    bar.className = "bar";

    const label = document.createElement("span");
    label.className = "bar-value";
    label.textContent = value === undefined ? "–" : String(value);

    const fill = document.createElement("div");
    fill.className = "bar-fill";
    fill.style.height = value === undefined ? "0" : Math.min(100, (value / max) * 100) + "%";

    const weekday = document.createElement("span");
    weekday.textContent = weekdayShort(day);

    // Screen readers get the full sentence instead of "7.5 Mon".
    bar.setAttribute("role", "img");
    bar.setAttribute("aria-label", formatDate(day) + ": " + (value === undefined ? "nothing logged" : value + unit));

    bar.append(label, fill, weekday);
    return bar;
  });
  container.replaceChildren(...bars);
}

// ---- Recent symptoms ------------------------------------------------------
function showSymptoms(symptoms) {
  const rows = symptoms.map((s) =>
    listItem(prettyCode(s.symptom_code) + " · severity " + s.severity + "/5", formatDateTime(s.logged_at)));
  fillList(document.getElementById("symptom-list"), rows, "No symptoms logged yet.");
}

if (startPrivatePage()) {
  loadPage();
}
