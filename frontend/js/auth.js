// auth.js: remembers who is logged in, and protects pages that need a login.
//
// After login the backend gives us two tokens:
//   - access token:  sent with every request, valid for 15 minutes
//   - refresh token: used only to get a new pair when the access token expires
//
// We keep both in localStorage so you stay logged in after closing the tab.
// Trade-off (fine for this project, worth knowing for the viva): any script running
// on our page could read localStorage, so the site must never include untrusted scripts.

const ACCESS_KEY = "wellher.access";
const REFRESH_KEY = "wellher.refresh";

export function saveTokens(tokens) {
  // `tokens` is the backend's TokenPair: { access_token, refresh_token, expires_in }
  localStorage.setItem(ACCESS_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function isLoggedIn() {
  return getRefreshToken() !== null;
}

// Send the visitor to the login page, remembering where they wanted to go.
export function goToLogin() {
  const here = location.pathname.split("/").pop() || "index.html";
  location.href = "login.html?next=" + encodeURIComponent(here);
}

// Call this at the top of every page that needs a login (home, log, settings).
// Returns true if the page may continue; otherwise it has already redirected.
export function requireLogin() {
  if (isLoggedIn()) {
    return true;
  }
  goToLogin();
  return false;
}
