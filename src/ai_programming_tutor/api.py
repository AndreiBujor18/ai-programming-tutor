from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ai_programming_tutor.catalog import get_exercise, list_exercises
from ai_programming_tutor.exam import get_practice_exam
from ai_programming_tutor.solutions import reference_answer
from ai_programming_tutor.style_profile import learn_c_style
from ai_programming_tutor.webserver import public_exercise, submit_payload


app = FastAPI(
    title="AI Programming Tutor API",
    version="0.6.3",
    description="Local PCLP1 learning prototype. The runner is not a public execution sandbox.",
    docs_url=None,
    redoc_url=None,
)
WEB_ROOT = Path(__file__).resolve().parent / "web"
app.mount("/static", StaticFiles(directory=WEB_ROOT), name="static")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; script-src 'self'; style-src 'self'; "
        "connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'"
    )
    if request.url.path.endswith(("/submit", "/solution", "/learn")):
        response.headers["Cache-Control"] = "no-store"
    return response


class Submission(BaseModel):
    source: str = Field(min_length=1, max_length=50_000)
    hint_level: int = Field(default=1, ge=1, le=3)
    dialect: Literal["c17"] = "c17"


class SolutionRequest(BaseModel):
    style: Literal[
        "auto", "personalized_c", "pclp1_classic", "classic_c", "commented_c"
    ] = "personalized_c"
    source: str = Field(default="", max_length=50_000)
    profile: dict[str, object] | None = None


class StyleLearnRequest(BaseModel):
    source: str = Field(min_length=1, max_length=50_000)
    profile: dict[str, object] | None = None


def _public_exercise(exercise_id: str) -> dict[str, object]:
    try:
        return public_exercise(exercise_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _local_execution_allowed(request: Request) -> bool:
    return os.getenv("APTUTOR_ENABLE_LOCAL_EXECUTION") == "1" and (
        request.client is not None and request.client.host in {"127.0.0.1", "::1"}
    )


@app.get("/", include_in_schema=False)
def homepage() -> FileResponse:
    return FileResponse(WEB_ROOT / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/exercises")
def exercises() -> list[dict[str, object]]:
    return [_public_exercise(exercise.id) for exercise in list_exercises()]


@app.get("/exam")
def practice_exam() -> dict[str, object]:
    return get_practice_exam().public_view()


@app.get("/exercises/{exercise_id}")
def exercise(exercise_id: str) -> dict[str, object]:
    return _public_exercise(exercise_id)


@app.post("/exercises/{exercise_id}/submit")
def submit(exercise_id: str, submission: Submission, request: Request) -> dict[str, object]:
    if not _local_execution_allowed(request):
        raise HTTPException(
            status_code=403,
            detail=(
                "Local code execution is disabled. Start on 127.0.0.1 with "
                "APTUTOR_ENABLE_LOCAL_EXECUTION=1; never expose the runner publicly."
            ),
        )
    try:
        return submit_payload(
            exercise_id, submission.source, submission.dialect, hint_level=submission.hint_level
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/exercises/{exercise_id}/solution")
def solution(exercise_id: str, body: SolutionRequest) -> dict[str, object]:
    try:
        return reference_answer(
            get_exercise(exercise_id),
            style=body.style,
            source=body.source,
            profile=body.profile,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/style-profile/learn")
def learn_style(body: StyleLearnRequest) -> dict[str, object]:
    return learn_c_style(body.source, body.profile)
