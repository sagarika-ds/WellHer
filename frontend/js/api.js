// api.js: the ONLY file that talks to the backend.
//
// Every page calls `api(path, options)` instead of using fetch() directly, so the
// rules below are written once:
//   1. Prefix the path with /api/v1 (the website and API come from the same server).
//   2. Send JSON and the login token.
//   3. If the token has expired (HTTP 401), renew it once and retry the request.
//   4. Turn the backend's error format into a JavaScript error with a readable message.
//
// Example:
//   const me = await api("/auth/me");
//   await api("/mood", { method: "POST", body: { logged_at: "...", mood_score: 4 } });

import { clearTokens, getAccessToken, getRefreshToken, goToLogin, saveTokens } from "./auth.js";

const API_BASE = "/api/v1";

// An error from the backend. The backend always answers errors as
//   { "error": { "code": "consent_required", "message": "...", "request_id": "..." } }
// so pages can check `err.code` (e.g. "consent_required") and show `err.message`.
export class ApiError extends Error {
  constructor(status, code, message) {
    super(message);
    this.status = status;  // HTTP status, e.g. 400, 403, 409
    this.code = code;      // the backend's error code, e.g. "validation_error"
  }
}

export async function api(path, options = {}) {
  const method = options.method || "GET";
  const body = options.body;            // a plain object; we convert it to JSON
  const auth = options.auth !== false;  // pass { auth: false } for login/register

  let response = await send(path, method, body, auth);

  // 401 = our access token expired. Renew it once and try again.
  if (response.status === 401 && auth && getRefreshToken()) {
    const renewed = await refreshTokens();
    if (renewed) {
      response = await send(path, method, body, auth);
    }
  }

  // Still 401 on a page that needs a login: the session is over.
  if (response.status === 401 && auth) {
    clearTokens();
    goToLogin();
    throw new ApiError(401, "unauthenticated", "Your session has ended. Please log in again.");
  }

  return readResponse(response);
}

// Build and send one HTTP request.
async function send(path, method, body, auth) {
  const headers = {};
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (auth && getAccessToken()) {
    headers["Authorization"] = "Bearer " + getAccessToken();
  }
  try {
    return await fetch(API_BASE + path, {
      method: method,
      headers: headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (networkProblem) {
    // fetch() only throws when the server could not be reached at all.
    throw new ApiError(0, "network_error", "Cannot reach the server. Is it running?");
  }
}

// Turn a response into data (success) or an ApiError (failure).
async function readResponse(response) {
  let data = null;
  const text = await response.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (response.ok) {
    return data;
  }

  const error = data && data.error;
  if (error) {
    throw new ApiError(response.status, error.code, tidyMessage(error.message));
  }
  throw new ApiError(response.status, "http_error", "Something went wrong (HTTP " + response.status + ").");
}

// Validation errors come from the backend's checks as "field: Value error, the rule", e.g.
//   "logged_at: Value error, timestamp must not be in the future"
//   ": Value error, end_date must not be before start_date"   (rules that involve two fields)
// Remove the technical "Value error, " part and an empty field name, turn field names like
// "end_date" into "end date", and start with a capital:
//   "Logged at: timestamp must not be in the future"
//   "End date must not be before start date"
function tidyMessage(message) {
  const tidy = String(message)
    .replace(/Value error, /g, "")
    .replace(/^:\s*/, "")
    .replace(/_/g, " ");
  return tidy.charAt(0).toUpperCase() + tidy.slice(1);
}

// The backend's refresh tokens work ONCE. If two requests renewed at the same moment,
// the second would reuse an old token, and the backend would end the whole session
// (it treats reuse as theft). So all callers share a single renewal in progress.
let refreshInProgress = null;

function refreshTokens() {
  if (refreshInProgress === null) {
    refreshInProgress = doRefresh().finally(() => {
      refreshInProgress = null;
    });
  }
  return refreshInProgress;
}

async function doRefresh() {
  try {
    const response = await fetch(API_BASE + "/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: getRefreshToken() }),
    });
    if (!response.ok) {
      return false;
    }
    saveTokens(await response.json());
    return true;
  } catch {
    return false;
  }
}
