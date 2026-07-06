# NeXo backend image (Railway). Build context = repo root (needs backend/ + database/).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install the backend package (runtime extras only; no test deps).
COPY backend/ ./backend/
COPY database/ ./database/
RUN pip install --upgrade pip && pip install -e "./backend[dashboard]"

WORKDIR /app/backend

# Run Alembic migrations, then serve. PORT is provided by Railway.
CMD ["sh", "-c", "alembic -c ../database/alembic.ini upgrade head && uvicorn ui.dashboard:app --host 0.0.0.0 --port ${PORT:-8000}"]
