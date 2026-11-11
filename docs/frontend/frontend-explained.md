# The WellHer website in simple words

This page explains the website in the simplest words possible. Read it before you present the project.
For the full details, read [frontend-documentation.md](frontend-documentation.md).

## The big picture

Think of a restaurant:

| Restaurant | WellHer |
|---|---|
| The dining room that you see | The website (the `frontend/` folder) |
| The kitchen | The backend (the `backend/` folder, a FastAPI server) |
| The storeroom | The PostgreSQL database |
| The waiter | The file `frontend/js/api.js` |

You never walk into the kitchen. You tell the waiter what you want, and the waiter brings it back.
In the same way, a page never talks to the backend directly. It asks `api.js`, and `api.js` talks to the backend.

Another team wrote the backend. We wrote the website and connected it to the backend.

## The three languages of a web page

Each page uses three languages. Each language has one job:

1. HTML says what is on the page: headings, forms, buttons.
2. CSS says how the page looks: colors, sizes, spacing.
3. JavaScript says what the page does: it gets data, saves forms, and shows messages.

We used them in their plain form. There is no React, no npm, and no build step.
The browser reads the files exactly as they are in the folder.

## The files

There is one HTML file for each screen:

| File | Screen |
|---|---|
| `index.html` | The first page, with "Log in" and "Create an account" |
| `signup.html` | Create an account |
| `login.html` | Log in |
| `forgot.html` | Reset a forgotten password |
| `home.html` | A summary of your data |
| `log.html` | Add your periods, symptoms, sleep, and moods |
| `settings.html` | Your profile, your permissions, and your privacy tools |

There is one stylesheet, `css/style.css`, for all pages.

The JavaScript files are in `js/`. There are two kinds:

1. Page scripts. Each HTML page has one script with the same name, for example `home.html` uses `home.js`. The Log page and the Settings page are large, so their sections are in the folders `js/log/` and `js/settings/`.
2. Shared scripts. All pages use these four files:

| File | Its one job |
|---|---|
| `api.js` | Sends every request to the backend. It is the waiter. |
| `auth.js` | Remembers that you are logged in. |
| `layout.js` | Starts each private page. It sends you to Log in if you are not logged in, and it makes the "Log out" button work. |
| `ui.js` | Small helpers: show a message, disable a button while it saves, format a date. |

## The components

A component is a piece of the page that we use again and again. All components are classes in `style.css`:

| Component | Class | Where you see it |
|---|---|---|
| Card | `.card` | The white boxes that hold each section |
| Button | `.btn` | "Save", "Log in". There are also `.btn-secondary` and `.btn-danger` (red, for delete). |
| Form field | `.field` | A label, an input box, and a hint under it |
| Message box | `.alert` | Green for success, red for errors |
| List | `.list` | Recent entries, for example your last 10 moods |
| Bar chart | `.bars` | Sleep and mood for the last 7 days on Home |
| Header | `.site-header` | The top bar with the links Home, Log, and Settings |

To see all components on one page, open `styleguide.html`.

The colors are at the top of `style.css` as variables, for example `--primary`. If you change a variable, the color changes on every page.

## How we connected the website to the backend

We did five things.

1. One server for everything. We added a few lines to `backend/app/main.py`. These lines tell the backend to also send the files in `frontend/`. Now the website and the API both come from `http://127.0.0.1:8000`. Because they have the same address, the browser does not block the requests.

2. One waiter. Every page calls `api("/some/path")`. The function `api()` adds `/api/v1` to the start of the path, sends the request, and gives back the answer.

3. Login tokens. A token is a long code that proves who you are. When you log in, the backend gives the website two tokens. `auth.js` saves them in the browser. `api.js` sends the token with each request. The token expires after 15 minutes. Then `api.js` gets a new one, and you do not see this happen.

4. Permissions (consents). The backend saves health data only if you allow it. If you did not allow it, the Log page and the Home page show a box that explains this, instead of an error.

5. Readable errors. When the backend refuses a request, it sends an error code and a message. `api.js` changes the message into normal words, and the page shows it in a red box.

## One example from start to end

This is what happens when you save a mood on the Log page:

1. You choose a score and select "Save mood".
2. `js/log/mood.js` reads the form and calls `api("/mood", { method: "POST", body: ... })`.
3. `api.js` sends the request to `http://127.0.0.1:8000/api/v1/mood` with your token.
4. The backend makes sure that the token is valid and that you allowed health tracking.
5. The backend saves the mood in the database and sends it back.
6. `mood.js` shows "Mood saved." in a green box and loads the list again.

Every form on the website works in the same way.

## What we changed in the backend

We changed very little, because the backend belongs to the other team:

1. `backend/app/main.py`: a few lines that send the website files. We also told the browser to always get the newest version of a file.
2. `backend/tests/test_website.py`: new tests for those lines.
3. Test configuration: the tests use `127.0.0.1` instead of `localhost`, and one test is skipped on Windows because a library that it uses does not work on Windows.

We did not change any API endpoint.

## Questions you can expect

Why no React?
The project is small, and plain files are easier to read and explain. Each page is one HTML file and one script.

Why does only `api.js` call the backend?
Then the rules for tokens and errors are in one place. If a rule changes, we change one file.

Where does the data come from?
All data comes from the backend. The website calculates only small things for display, for example the cycle day and the average mood of one day.

Why are some features missing, such as predictions or chat?
The backend does not supply them yet. The website shows only what the backend can do today.

How does the website stop harmful text in a note?
It puts server text into the page with `textContent`. The browser then shows the text as text and does not run it as code.

What happens if you turn off health tracking?
The backend keeps your logs, but nobody can see or add logs until you turn it on again.
