"""ML Engine: ZIP 1 skeleton. Only /health exists; feature routes arrive in later milestones."""
from fastapi import FastAPI

app = FastAPI(title="Women's Wellness: ML Engine", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ml-engine", "version": "0.1.0"}
