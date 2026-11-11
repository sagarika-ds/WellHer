// layout.js: shared set-up for pages that need a login (Home, Log and Settings).
//
// Each of those pages starts with:
//   import { startPrivatePage } from "./layout.js";
//   if (startPrivatePage()) { ...load the page... }

import { api } from "./api.js";
import { clearTokens, requireLogin } from "./auth.js";

export function startPrivatePage() {
  if (!requireLogin()) {
    return false;  // not logged in: requireLogin() already sent us to the login page
  }
  const logoutButton = document.getElementById("logout");
  if (logoutButton) {
    logoutButton.addEventListener("click", logOut);
  }
  return true;
}

async function logOut() {
  try {
    // Tell the backend to end this session, so the tokens stop working everywhere.
    await api("/auth/logout", { method: "POST" });
  } catch {
    // Even if the server can't be reached, we still forget the tokens below.
  }
  clearTokens();
  location.href = "index.html";
}
