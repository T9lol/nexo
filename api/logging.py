"""Structured logging for the API layer.

Emits one JSON object per log record on stderr so logs are machine-parseable in
production while staying readable in development. This is deliberately scoped to
the ``nexo.api`` logger tree and does not touch the root logger or the existing
trading ``observability`` output.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

LOGGER_NAME = "nexo.api"

# Attributes we lift from ``logging`` extras into the structured payload.
_CONTEXT_KEYS = (
    "event",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "client",
    "error_code",
)


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in _CONTEXT_KEYS:
            value = record.__dict__.get(key)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(
    *, level: str = "INFO", json_format: bool = True
) -> logging.Logger:
    """Configure and return the ``nexo.api`` logger.

    Idempotent: replaces existing handlers so repeated calls (e.g. app reloads,
    tests) do not stack duplicate output.
    """

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level.upper())
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
    logger.addHandler(handler)
    # Do not double-log through the root logger.
    logger.propagate = False
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return an API logger. ``name`` is appended under the ``nexo.api`` tree."""

    if name:
        return logging.getLogger(f"{LOGGER_NAME}.{name}")
    return logging.getLogger(LOGGER_NAME)
