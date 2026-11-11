// settings.js: the Settings page. Each section lives in its own small file in js/settings/,
// the same way the Log page's sections live in js/log/.

import { startPrivatePage } from "./layout.js";
import { setupProfile } from "./settings/profile.js";
import { setupConsents } from "./settings/consent.js";
import { setupAi } from "./settings/ai.js";
import { setupHistory } from "./settings/history.js";
import { setupAccount } from "./settings/account.js";

if (startPrivatePage()) {
  setupProfile();
  setupConsents();
  setupAi();
  setupHistory();
  setupAccount();
}
