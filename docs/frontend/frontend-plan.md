# Website plan: plain HTML, CSS and JavaScript

The WellHer website is rebuilt with plain HTML, CSS and JavaScript and wired to the existing FastAPI backend.
The goal is a site where every line can be read and explained: no frameworks, no npm, no build step.

## Ground rules

- One HTML file per screen, one shared stylesheet, one small script per page.
- Only `js/api.js` talks to the server. Pages call `api(...)`; they never call `fetch` directly.
- FastAPI serves the website itself. One server, one address (`http://127.0.0.1:8000`), no CORS setup.
- **Only what the backend provides today.** No predictions calculated in the browser, no demo chat, no reminders.
Simple display maths on server data (for example "cycle day" from the last period start) is fine.
- Every screen ends with: "For awareness only, not a medical diagnosis."

## Folder layout

```
frontend/
  index.html          goes to Home if logged in, otherwise to Login
  login.html
  signup.html
  forgot.html         forgot and reset password
  home.html           today: cycle day, cycle stats, last 7 days, recent symptoms
  log.html            period, symptom, daily (sleep/water/activity/stress), mood
  settings.html       profile, consent, AI settings, access history, export, delete account
  styleguide.html     development only: every component from style.css on one page
  css/style.css       colours, spacing, buttons, cards, forms, navigation
  js/api.js           the only file that calls the server
  js/auth.js          keeps the login tokens, protects pages
  js/<page>.js        one script per page
```

## How a page works (the same pattern everywhere)

1. `auth.js` checks for a login; if there is none, it sends you to `login.html`.
2. The page script loads data with `api(...)`.
3. It draws that data into the page.
4. Forms send data with `api(...)`, show a success or error message, and redraw.

## Phases

### Phase 0: Foundation

1. FastAPI serves the `frontend/` folder (a few lines in `backend/app/main.py`, plus a backend test).
2. `style.css`: colours and spacing as CSS variables, then buttons, cards, forms and the navigation bar.

   Designed for phones first, then wider screens.
3. `api.js`: one `api()` function that adds `/api/v1` and the login token, turns the server's error envelope

   (`{"error": {"code", "message"}}`) into a readable message, and on an expired token renews it once
    (`/auth/refresh`) before sending you to Login.

### Phase 1: Accounts

4. Sign up: name, email, password, and the four consent choices (all off by default).

   Password rules from the backend: at least 12 characters, at least 5 different characters,
    and it must not contain the part of the email before the `@`.
5. Log in and log out.
6. Forgot and reset password. In development the reset link prints in the API window instead of being emailed.

### Phase 2: Logging

7. One Log page with four small forms:
   | Form | Fields | Endpoint |
    |---|---|---|
    | Period | start date, end date, flow 1–5, notes | `/cycles` |
    | Symptom | one of the server's 24 symptoms, severity 1–5, time | `/symptoms` |
    | Daily | sleep hours, sleep quality, water (ml), activity minutes, stress | `/lifestyle` |
    | Mood | score 1–5, tags | `/mood` |
8. Recent entries under each form, with edit and delete where the server allows it.
9. If the server answers `consent_required`, show a clear message with a link to Settings.

### Phase 3: Home

10. Today's view: cycle day (from the latest period start), cycle stats (`/cycles/stats`), the lifestyle summary

    (`/lifestyle/summary`), 7 days of sleep and mood as plain CSS bars, recent symptoms. No predictions.

### Phase 4: Settings and privacy

11. Profile (`/profile`).
12. Consent switches (`/consents`).
13. AI settings and access history (`/privacy/ai-settings`, `/privacy/access-history`).
14. Export my data as a JSON download (`/privacy/export`).
15. Delete account, with a confirmation step (`/privacy/account`).

### Phase 5: Polish and documentation

16. Loading, empty and error states on every page; accessibility (labels, colour contrast, keyboard use).
17. README: how to run everything. A manual test checklist that also serves as a demo script.

## Out of scope for now

Anything the backend does not provide yet: predictions, chat and voice, reminders/notifications, and the advanced  
features in `docs/api/endpoints.md`. They get pages when the backend gets the endpoints.  
The mobile app in `mobile/` is a separate client and is not changed by this work.
