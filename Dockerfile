# syntax=docker/dockerfile:1.4
FROM python:3.11-slim AS base

ENV POETRY_VERSION=2.1.3 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Install system deps + Poetry
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl build-essential libpq-dev && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy lockfiles and install only prod deps
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-interaction --no-ansi

# Copy source
COPY . .

# Make `src/` importable as top-level
ENV PYTHONPATH=/app/src

EXPOSE 8000

# Run Uvicorn from the installed package
CMD ["python", "-m", "uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
