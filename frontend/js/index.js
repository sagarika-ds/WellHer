// index.js: the landing page. If you are already logged in, skip it and go to Home.
import { isLoggedIn } from "./auth.js";
import { showAlert } from "./ui.js";

if (isLoggedIn()) {
  location.replace("home.html");  // replace() so the Back button doesn't return here
}

// Settings sends people here with ?deleted=1 after deleting their account.
if (new URLSearchParams(location.search).get("deleted") === "1") {
  showAlert(document.getElementById("message"), "success", "Your account and all your data have been deleted.");
}
