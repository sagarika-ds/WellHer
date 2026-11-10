FROM python:3.12-slim
WORKDIR /srv
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
RUN useradd -m app && chown -R app /srv
USER app
EXPOSE 8000
# Migrations run once at start; for multi-replica deployments run them as a separate job instead.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
