"""HTTP API: triage as a service. Run it with ``uv run uvicorn heron.api:app --reload``."""

import logging
import re
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from contextlib import asynccontextmanager
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from heron import __version__
from heron.config import Settings
from heron.logs import configure_logging, request_id
from heron.models import ParsedEmail, TriageResult, Verdict
from heron.parser import parse_eml
from heron.scorer import triage
from heron.storage import VerdictRepository, VerdictStore

logger = logging.getLogger("heron")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Runs once at startup (before ``yield``) and once at shutdown (after it)."""
    settings = Settings()  # a bad configuration stops the service at startup
    configure_logging(settings.log_level)
    logger.info("api starting", extra={"version": __version__, "store": bool(settings.db)})
    yield
    logger.info("api stopping")


app = FastAPI(title="heron", version=__version__, lifespan=lifespan)

_REQUEST_ID_RE = re.compile(r"[A-Za-z0-9._-]{1,64}")


@app.middleware("http")
async def request_context(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Give each request an id (a well-formed X-Request-ID, or a new one) and log it."""
    incoming = request.headers.get("x-request-id", "")
    rid = incoming if _REQUEST_ID_RE.fullmatch(incoming) else uuid.uuid4().hex[:12]
    token = request_id.set(rid)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        logger.info("request", extra={"path": request.url.path, "status": response.status_code})
        return response
    finally:
        request_id.reset(token)


# --- schemas: the wire format, kept apart from the domain dataclasses

MAX_EML_CHARS = 1_000_000  # the message is attacker-authored: cap its size before parsing
VerdictName = Literal["benign", "suspicious", "phishing"]
_WIRE_VERDICT: dict[Verdict, VerdictName] = {
    Verdict.BENIGN: "benign",
    Verdict.SUSPICIOUS: "suspicious",
    Verdict.PHISHING: "phishing",
}


class TriageRequest(BaseModel):
    raw_eml: str = Field(description="raw RFC 5322 message", min_length=1, max_length=MAX_EML_CHARS)
    email_id: str = Field(default="uploaded.eml", max_length=200)


class FindingOut(BaseModel):
    code: str
    detail: str
    weight: int


class TriageResponse(BaseModel):
    email_id: str
    sender: str
    score: int
    verdict: VerdictName
    findings: list[FindingOut]


class CountResponse(BaseModel):
    count: int


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


# --- dependencies: called by FastAPI for each request; a yield runs code after the response


def get_settings() -> Settings:
    return Settings()


def get_repository(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Iterator[VerdictRepository | None]:
    if not settings.db:
        yield None
        return
    store = VerdictStore(settings.db)
    try:
        yield store
    finally:
        store.close()


OptionalRepository = Annotated[VerdictRepository | None, Depends(get_repository)]


def require_repository(repo: OptionalRepository) -> VerdictRepository:
    """For endpoints that cannot work without storage: 503 if none is configured."""
    if repo is None:
        raise HTTPException(status_code=503, detail="no verdict store configured")
    return repo


Repository = Annotated[VerdictRepository, Depends(require_repository)]


# --- errors as RFC 9457 problem details

_TITLES = {
    404: "Not Found",
    405: "Method Not Allowed",
    422: "Unprocessable Content",
    503: "Service Unavailable",
}


def _problem(status: int, detail: str, **extra: Any) -> JSONResponse:
    title = _TITLES.get(status, "Error")
    body = {"type": "about:blank", "title": title, "status": status, "detail": detail, **extra}
    return JSONResponse(body, status_code=status, media_type="application/problem+json")


@app.exception_handler(StarletteHTTPException)
async def http_problem(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _problem(exc.status_code, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_problem(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]
    return _problem(422, "the request is not valid", errors=errors)


# --- endpoints


def _to_response(email: ParsedEmail, result: TriageResult) -> TriageResponse:
    """The only place that maps the domain objects to the wire format."""
    return TriageResponse(
        email_id=result.email_id,
        sender=email.sender,
        score=result.score,
        verdict=_WIRE_VERDICT[result.verdict],
        findings=[
            FindingOut(code=f.code, detail=f.detail, weight=f.weight) for f in result.findings
        ],
    )


@app.post("/triage")
def triage_email(request: TriageRequest, repo: OptionalRepository) -> TriageResponse:
    """Triage one message."""
    email = parse_eml(request.raw_eml, email_id=request.email_id)
    if not email.sender:
        raise HTTPException(status_code=422, detail="input does not look like an email message")
    result = triage(email)
    if repo is not None:
        repo.save([result])
    return _to_response(email, result)


@app.get("/verdicts/count")
def verdicts_count(repo: Repository, verdict: VerdictName | None = None) -> CountResponse:
    return CountResponse(count=repo.count(verdict=verdict))
