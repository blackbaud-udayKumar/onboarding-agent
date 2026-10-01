"""
Local web server for the onboarding agent.

Run with:  uvicorn server:app --reload
Then open: http://localhost:8000

Serves a single-page chat UI (static/index.html) and one API endpoint,
POST /api/ask, that the page calls. This is intentionally minimal --
swap this out for a Slack bot or VS Code extension later without touching
qa_engine.py, chunking.py, or vectorstore.py at all.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Onboarding Agent")

_engine = None  # lazy-loaded so the server can start even before ANTHROPIC_API_KEY is set


def get_engine():
    global _engine
    if _engine is None:
        from qa_engine import QAEngine

        _engine = QAEngine()
    return _engine


class AskRequest(BaseModel):
    question: str


class SourceOut(BaseModel):
    source: str
    url: str | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceOut]


@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")
    try:
        engine = get_engine()
        result = engine.ask(req.question.strip())
    except RuntimeError as e:
        # e.g. missing API key, or nothing indexed yet
        raise HTTPException(status_code=400, detail=str(e))
    return result


@app.get("/")
def index():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
