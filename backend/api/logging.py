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
from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any

LOGGER_NAME = "nexo.api"

# In-memory audit trail: the most recent structured API log records. This is the
# real source of truth for the Admin Console's audit-log view (backtest runs,
# strategy enable/disable, emergency stops, risk saves, etc. all log here).
# Bounded so it never grows without limit; not durable across restarts.
_AUDIT_MAXLEN = 500
_audit_buffer: "deque[dict[str, Any]]" = deque(maxlen=_AUDIT_MAXLEN)
_audit_lock = Lock()

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


class AuditBufferHandler(logging.Handler):
    """Capture recent structured records into the in-memory audit buffer."""

    def emit(self, record: logging.LogRecord) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "event": record.__dict__.get("event"),
            "path": record.__dict__.get("path"),
        }
        with _audit_lock:
            _audit_buffer.append(entry)


def get_audit_records(
    *, limit: int | None = None, event: str | None = None
) -> list[dict[str, Any]]:
    """Return recent audit records (most recent first), optionally filtered."""

    with _audit_lock:
        records = list(_audit_buffer)
    records.reverse()
    if event:
        records = [r for r in records if r.get("event") == event]
    if limit is not None:
        records = records[:limit]
    return records


def clear_audit_records() -> None:
    with _audit_lock:
        _audit_buffer.clear()


def configure_logging(
    *, level: str = "INFO", json_format: bool = True
) -> logging.Logger:
    """Configure and return the ``nexo.api`` logger.

    Idempotent: replaces existing handlers so repeated calls (e.g. app reloads,
    tests) do not stack duplicate output.
    """

    configured = getattr(logging, level.upper(), logging.INFO)

    logger = logging.getLogger(LOGGER_NAME)
    # Keep the logger at INFO-or-lower so audit events (INFO) always reach the
    # buffer; per-handler levels then control console verbosity independently.
    logger.setLevel(min(configured, logging.INFO))
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(configured)  # console respects the requested verbosity
    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
    logger.addHandler(handler)

    # Fan records into the in-memory audit buffer for the Admin Console. Fixed at
    # INFO so the audit trail is captured regardless of console log level.
    audit = AuditBufferHandler()
    audit.setLevel(logging.INFO)
    logger.addHandler(audit)

    # Do not double-log through the root logger.
    logger.propagate = False
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return an API logger. ``name`` is appended under the ``nexo.api`` tree."""

    if name:
        return logging.getLogger(f"{LOGGER_NAME}.{name}")
    return logging.getLogger(LOGGER_NAME)
