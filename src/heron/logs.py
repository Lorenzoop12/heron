"""Structured logging: one JSON object per line on stderr."""

import json
import logging
import sys
from contextvars import ContextVar

request_id: ContextVar[str] = ContextVar("request_id", default="-")

_STANDARD = set(vars(logging.makeLogRecord({}))) | {"message", "asctime"}  # not from extra=


class JsonFormatter(logging.Formatter):
    """Format a record as one JSON object; json.dumps escapes quotes and backslashes."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "msg": record.getMessage(),
            "request_id": request_id.get(),
        }
        payload.update({k: v for k, v in vars(record).items() if k not in _STANDARD})
        return json.dumps(payload, default=str)


def configure_logging(level: str) -> None:
    """Send the ``heron`` loggers to stderr as JSON lines from ``level`` up."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("heron")
    logger.handlers[:] = [handler]
    logger.setLevel(level)
