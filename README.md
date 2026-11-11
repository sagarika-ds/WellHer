# WellHer

AI-Driven Personalized Wellness and Healthcare System for Women.

WellHer is a university project. It is a website where a woman can track her menstrual cycle, symptoms, sleep and mood in one private place.

## Features

- Sign up, log in, and set a password
- Log periods, symptoms, daily sleep and activity, and moods
- See a summary: cycle day, average cycle length, and the last 7 days of sleep and mood
- Choose what your data can be used for (consent)
- Download all your data or delete your account

## Technologies

| Part | Technology |
|---|---|
| Website | HTML, CSS, JavaScript |
| Backend | Python, FastAPI |
| Database | PostgreSQL, Redis |

## Folders

```
backend/     the API server (FastAPI)
frontend/    the website (HTML, CSS, JavaScript)
docs/        documentation
```

The other folders (`mobile/`, `ml-engine/`, `infra/`) are for later parts of the project.

## How to run

You need Python 3.12 (we use Anaconda) and Docker Desktop.

1. Start the database and Redis. Do this one time:

   ```bash
   docker run -d --name postgres -e POSTGRES_USER=wellness -e POSTGRES_PASSWORD=testpw -e POSTGRES_DB=wellness -p 127.0.0.1:5432:5432 postgres:16
   docker run -d --name redis -p 127.0.0.1:6379:6379 redis:7
   ```

   After a restart of your computer, run `docker start postgres redis`.

2. Install the Python packages:

   ```bash
   conda create -n women-wellness python=3.12 -y
   conda activate women-wellness
   cd backend
   pip install -e ".[dev]"
   ```

3. Make a file `backend/.env` with this text:

   ```
   APP_ENV=development
   DATABASE_URL=postgresql+asyncpg://wellness:testpw@127.0.0.1:5432/wellness
   REDIS_URL=redis://127.0.0.1:6379/0
   JWT_SECRET=type-any-random-text-of-at-least-32-characters
   FIELD_ENCRYPTION_KEY=paste-your-key-here
   EVENTS_INLINE=true
   EMAIL_BACKEND=console
   ```

   To make a value for `FIELD_ENCRYPTION_KEY`, run this command and copy the output:

   ```bash
   python -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"
   ```

4. Make the database tables and start the server:

   ```bash
   alembic upgrade head
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. Open http://127.0.0.1:8000 in a browser.

The API reference is at http://127.0.0.1:8000/docs.

## Documentation

- [How the website works, in simple words](docs/frontend/frontend-explained.md)
- [Website documentation](docs/frontend/frontend-documentation.md)
- [Backend](backend/README.md)

For awareness only, not a medical diagnosis.
