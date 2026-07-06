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

# Migrations run in Railway's pre-deploy phase. The Python entrypoint reads the
# dynamic PORT and binds to 0.0.0.0 without a shell-expansion dependency.
CMD ["python", "-m", "ui.dashboard"]
