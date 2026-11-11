# WellHer website documentation

This document explains the WellHer website: what it does, how to run it, and how the code works.
The website is in the `frontend/` folder. It uses plain HTML, CSS, and JavaScript.
It has no framework, no npm packages, and no build step. The browser reads the files exactly as they are in the folder.

The plan that we followed to build the website is in [frontend-plan.md](frontend-plan.md).

## What the website does

The website shows only the features that the backend supports today.
The backend is the FastAPI server in the `backend/` folder. It stores the data and applies the rules to every request.

| Page | File | What you can do |
|---|---|---|
| Landing | `index.html` | Choose "Log in" or "Create an account". If you are logged in, the page sends you to Home. |
| Sign up | `signup.html` | Create an account with a name, email, password, and four consent choices. |
| Log in | `login.html` | Log in with your email and password. |
| Forgot password | `forgot.html` | Ask for a reset code, then set a new password with that code. |
| Home | `home.html` | See your cycle day, cycle statistics, 30-day averages, sleep and mood for the last 7 days, and recent symptoms. |
| Log | `log.html` | Add, edit, and delete periods, symptoms, daily entries, and moods. |
| Settings | `settings.html` | Change your profile, consents, and AI configuration. See your access history. Download your data. Delete your account. |
| Style guide | `styleguide.html` | See every visual component on one page. This page is for development only. |

Every page ends with the text "For awareness only, not a medical diagnosis."

The website does not show predictions, chat, voice, or reminders. The backend does not supply these features yet.
When the backend adds an endpoint for a feature, the website can get a page for it.
An endpoint is one URL on the server that does one job, for example `GET /api/v1/cycles`.

## Run the website

The backend serves the website and the API from the same address. You start one server, not two.

Before you start, make sure that these items are ready:

1. Docker Desktop is open.
2. The conda environment `women-wellness` exists.
3. The file `backend/.env` exists. It holds the configuration for the database, Redis, and the secret keys.

To start the website, do these steps in a terminal:

1. Start the database containers. They stop when the computer restarts.

   ```bash
   docker start postgres redis
   ```

2. Activate the conda environment.

   ```bash
   conda activate women-wellness
   ```

3. Go to the backend folder.

   ```bash
   cd backend
   ```

4. Update the database tables to the newest version. You must do this step after you get new code from Git.

   ```bash
   alembic upgrade head
   ```

5. Start the server.

   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

6. Open `http://127.0.0.1:8000` in a browser.

Use `127.0.0.1`, not `localhost`. On Windows, `localhost` tries IPv6 first, and each request becomes slow.

The `--reload` flag restarts the server when you change a Python file.
You do not have to restart the server after you change a website file. Reload the page in the browser.

To stop the server, press `Ctrl+C` in the terminal.

### Reset a password in development

In development, the backend does not send email. It writes the email to the terminal instead.

To reset a password:

1. On the Log in page, select "Forgot your password?".
2. Type the email address of the account and send the form.
3. In the terminal that runs the server, find the line that starts with `DEV EMAIL`.
4. Copy the code that comes after `reset_token=`.
5. Paste the code into the second form, type a new password, and send the form.

The code is valid for 30 minutes.

## How the files are organized

```
frontend/
  index.html            landing page
  signup.html           create an account
  login.html            log in
  forgot.html           forgot and reset password
  home.html             summary of your data
  log.html              add and change your health records
  settings.html         profile, consents, privacy
  styleguide.html       development only: all visual components
  css/
    style.css           the one stylesheet for all pages
  js/
    api.js              the only file that sends requests to the backend
    auth.js             keeps the login tokens and protects private pages
    layout.js           shared start-up code for private pages
    ui.js               small helpers: messages, busy buttons, dates, list rows
    index.js            script for index.html
    signup.js           script for signup.html
    login.js            script for login.html
    forgot.js           script for forgot.html
    home.js             script for home.html
    log.js              script for log.html
    settings.js         script for settings.html
    log/
      period.js         Period section of the Log page
      symptom.js        Symptom section of the Log page
      daily.js          Daily section of the Log page
      mood.js           Mood section of the Log page
    settings/
      profile.js        Profile section of the Settings page
      consent.js        Consent section of the Settings page
      ai.js             AI section of the Settings page
      history.js        Access history section of the Settings page
      account.js        Download and delete sections of the Settings page
```

Each HTML page loads one script with `<script type="module">`.
A module is a JavaScript file that can use `import` and `export` to share functions with other files.
The Log page and the Settings page are large, so each of their sections has its own file.

## How the backend serves the website

The file `backend/app/main.py` connects the `frontend/` folder to the server. It does this with these rules:

1. The API routes, `/docs`, and `/health` come first.
2. The website is added last, at `/`. If no API route matches a path, the server looks for a file with that path in `frontend/`.
3. The path `/` returns `index.html`.
4. Every website file has the header `Cache-Control: no-cache`. This header tells the browser to ask the server for a newer version on each load. Because of this header, you see your changes when you reload a page.
5. If the `frontend/` folder does not exist, the server starts without the website. The backend-only Docker image uses this.

Because the website and the API have the same address, the browser does not need CORS.
CORS is a browser rule that blocks requests to a different address unless the server allows them.

The tests for these rules are in `backend/tests/test_website.py`.

## How a page works

Each private page follows the same four steps:

1. The page calls `startPrivatePage()` from `layout.js`. If you are not logged in, this function sends you to the Log in page.
2. The page script gets data from the backend with `api(...)`.
3. The script puts the data into the page.
4. When you send a form, the script sends the data with `api(...)`. Then it shows a success or error message and loads the list again.

The scripts put server data into the page with `textContent` and `createElement`. They never use `innerHTML`.
With `textContent`, the browser shows text as text. If a note contains HTML code, the browser does not run it.

## How the website talks to the backend

All requests go through one function: `api(path, options)` in `js/api.js`. No other file calls `fetch` directly.

For example:

```js
const me = await api("/auth/me");
await api("/mood", { method: "POST", body: { logged_at: "2026-11-11T08:30:00.000Z", mood_score: 4 } });
```

The function does these jobs:

1. It adds `/api/v1` to the start of the path.
2. It converts the body to JSON.
3. It adds the access token to the request.
4. If the access token expired, it gets new tokens and sends the request one more time.
5. If the backend sends an error, it throws an `ApiError` with a message that a person can read.

### Errors

The backend sends every error in the same shape:

```json
{"error": {"code": "consent_required", "message": "Consent for health_tracking is required.", "request_id": "..."}}
```

`api()` changes this into an `ApiError`. The `code` property holds the error code. The `message` property holds the text.
A page shows the message in a colored box with `showAlert()` from `ui.js`.
Some pages read the code to show a better message. For example, `settings/ai.js` looks for `consent_required`.

`api()` also makes validation messages easier to read.
For example, the backend sends `": Value error, end_date must not be before start_date"`.
The website shows "End date must not be before start date".

If the server does not answer at all, the message is "Cannot reach the server. Is it running?".

## Login and tokens

A token is a long code that proves who you are. The backend gives two tokens when you log in:

| Token | Use | How long it is valid |
|---|---|---|
| Access token | The website sends it with every request. | 15 minutes |
| Refresh token | The website uses it only to get a new pair of tokens. | 30 days, and it works one time only |

`auth.js` keeps both tokens in `localStorage`. `localStorage` is storage in the browser that stays after you close the tab.
Any script on the page can read `localStorage`. For this reason, the website must not load scripts from other websites.

When the access token expires, the backend answers `401`. Then `api.js` sends the refresh token to `/auth/refresh` and gets a new pair.
Each refresh token works one time only. If the backend sees an old refresh token again, it ends the whole session as a safety measure.
For this reason, `api.js` lets only one refresh run at a time. All waiting requests use the result of that one refresh.

If the refresh fails, `api.js` deletes the tokens and sends you to the Log in page.

When a private page sends you to the Log in page, it adds `?next=` with the page name.
After you log in, you go back to that page. `login.js` accepts only a simple page name like `home.html`.
This rule stops a link from sending you to a different website after login.

When you select "Log out", `layout.js` tells the backend to end the session. Then it deletes the tokens from the browser.

## Consent

A consent is a permission that you give for one use of your data. The backend has four consents:

| Purpose name | What it allows |
|---|---|
| `health_tracking` | Store your health logs. Every record endpoint needs this consent. |
| `ml_processing` | Use your logs to look for patterns. |
| `llm_external` | Send text without your identity to an external AI service. |
| `analytics` | Share anonymous usage statistics. |

All four consents are off when the Sign up page opens. You choose which ones to turn on.

If `health_tracking` is off, the backend answers `403 consent_required` to every record request.
The website reads this consent first, so it can explain the problem instead of showing an error:

1. On the Log page, a box asks you to allow storage of your health logs. One button turns the consent on.
2. On the Home page, a box tells you to turn the consent on in Settings.

If you turn `health_tracking` off, the backend keeps your logs. You cannot see or add logs until you turn the consent on again.

## The Home page

`home.js` gets the data for each card from the backend at the same time with `Promise.all`.

| Card | Backend call | What the page calculates |
|---|---|---|
| Cycle day | `GET /cycles?limit=1` | The number of days since the first day of the latest period. That first day is Day 1. |
| Average cycle length | `GET /cycles/stats` | Nothing. The backend calculates the average, shortest, and longest cycle. |
| Last 30 days | `GET /lifestyle/summary?days=30` | Nothing. The backend calculates the averages for sleep, activity, and stress. |
| Sleep, last 7 days | `GET /lifestyle?date_from=...` | Nothing. One bar shows the sleep hours for one day. |
| Mood, last 7 days | `GET /mood?date_from=...` | The average mood for each day, because you can log more than one mood on a day. |
| Recent symptoms | `GET /symptoms?limit=5` | Nothing. |

The bars are plain `div` elements. JavaScript sets the height of each bar as a percentage.
A full sleep bar is 12 hours. A full mood bar is a score of 5.
If a day has no entry, the bar shows "–".
Each bar has an `aria-label` with the full date and value, for example "Nov 10, 2026: 5.5 hours". A screen reader reads this label.

The page does not predict the next period. The backend does not supply predictions yet.

## The Log page

The Log page has four sections. Each section has a form and a list of recent entries.

| Section | File | Backend endpoint | Add | Edit | Delete |
|---|---|---|---|---|---|
| Period | `log/period.js` | `/cycles` | Yes | Yes | Yes |
| Symptom | `log/symptom.js` | `/symptoms` | Yes | No | Yes |
| Daily | `log/daily.js` | `/lifestyle` | Yes | Yes | No |
| Mood | `log/mood.js` | `/mood` | Yes | No | No |

If the backend does not allow an action, the page does not show a button for it.

The backend applies these rules. If you break a rule, the page shows the message from the backend:

1. Periods cannot overlap, cannot start in the future, and cannot be longer than 21 days.
2. The backend calculates the cycle length. It is the number of days from the start of one period to the start of the next period.
3. A symptom must be one of 24 codes. The list of codes is in `log/symptom.js`. It is a copy of `SYMPTOM_CODES` in `backend/app/core/ontology.py`. If the backend list changes, you must change the copy too.
4. Symptom and mood times cannot be in the future.
5. Each date can have only one daily entry. If you choose a date that has an entry, the form shows the values of that entry, and "Update day" saves the changes.
6. Mood tags are separated by commas. The page changes them to lowercase. You can add 10 tags at most.

The Daily form does not have a field for food notes (`nutrition_notes`).
The backend stores food notes encrypted and never sends them back.
But an update replaces all the fields of an entry. If an update does not include the old notes, the backend deletes them.

## The Settings page

| Section | File | Backend calls |
|---|---|---|
| Profile | `settings/profile.js` | `GET /profile`, `PUT /profile` |
| Consents | `settings/consent.js` | `GET /consents`, `PUT /consents/{purpose}` |
| AI | `settings/ai.js` | `GET /privacy/ai-settings`, `PUT /privacy/ai-settings` |
| Access history | `settings/history.js` | `GET /privacy/access-history` |
| Download my data | `settings/account.js` | `POST /privacy/export` |
| Delete my account | `settings/account.js` | `DELETE /privacy/account` |

Profile. All fields are optional. `PUT /profile` replaces the whole profile, so the page always sends all fields. An empty field becomes `null`.

Consents. Each switch saves when you change it. If the save fails, the switch goes back to its old position.

AI. The backend stores this configuration now. The AI features that use it do not exist yet.
To allow an external AI service, you must first turn on the `llm_external` consent.
If you do not, the page shows a warning that tells you which consent to turn on.

Access history. The backend records each time your data is read or changed. This record is called the audit log.
The page shows 20 entries at a time, newest first. "Show more" gets the next 20.
`history.js` changes the technical names into words. For example, `read` on `cycle_records` becomes "Viewed periods".

Download my data. The backend sends all your data in the response. The page saves it as a file named `wellher-data-YYYY-MM-DD.json`.

Delete my account. Do this only if you want to lose all your data. The deletion is permanent.
To delete the account, type your password, type `DELETE` in capital letters, and accept the last question.
The backend deletes the account and all its records, and ends all sessions. Then the page goes to the landing page and shows a message.

## Styles

All styles are in `css/style.css`. The file has six sections:

1. Design tokens: colors, spacing, and sizes as CSS variables, for example `--primary`.
2. Base: default styles for plain HTML elements.
3. Layout: page width, header, navigation, and footer.
4. Components: cards, buttons, forms, alerts, badges, and bars.
5. Helpers: small classes such as `.hidden` and `.muted`.
6. Wider screens: changes for screens that are 700 pixels wide or more.

The styles are mobile first. The normal rules are for phones. The `@media` block at the end changes the layout for wider screens.
On a phone, the page links are on a second row in the header. On a wider screen, they are on the same row as the logo.

To change a color everywhere, change its variable in section 1.
All text colors have a contrast ratio of 4.5:1 or more against their backgrounds. This is the WCAG AA level for normal text.

To see all components, open `http://127.0.0.1:8000/styleguide.html`.

## Testing

The backend tests include `backend/tests/test_website.py`. These tests make sure that:

1. `/` returns `index.html`.
2. CSS and JavaScript files have the correct content types.
3. Website files have the `Cache-Control: no-cache` header.
4. API routes and `/health` still work.
5. A missing page returns `404` in the normal error shape.
6. A path such as `/..%2Fbackend%2F.env` does not return files from outside `frontend/`.

To run all backend tests, run this command in the `backend/` folder:

```bash
python -m pytest -q
```

The website itself has no automatic tests. To test it by hand, do these steps on a running server:

1. Create an account and turn on "Store my health logs".
2. On the Log page, add two periods about four weeks apart. Add a symptom, a daily entry, and a mood.
3. On the Home page, make sure that the cycle day, the average cycle length, and the bars show your data.
4. On the Settings page, save the profile, change a consent, and download your data.
5. Delete the test account on the Settings page.

## Known limits

1. If two browser tabs refresh their tokens at the same moment, the backend can end the session. Then you must log in again. The backend does this because it sees the same refresh token two times.
2. The list of 24 symptom codes is in two places: the backend and `log/symptom.js`.
3. The Daily form cannot add or change food notes, for the reason in the Log page section.
4. The Home page shows no predictions, because the backend does not supply them.

## Add a new page

To add a page that needs a login:

1. Copy the header and footer from `home.html` into a new HTML file.
2. Add a link to the new page in the `nav` of every private page.
3. In the new page, set `aria-current="page"` on its own link.
4. Make a script in `js/` and load it with `<script type="module" src="js/<name>.js">`.
5. At the start of the script, call `startPrivatePage()`. Continue only if it returns `true`.
6. Get data with `api(...)`. Do not call `fetch` directly.
7. Put text into the page with `textContent`. Do not use `innerHTML` for server data.
