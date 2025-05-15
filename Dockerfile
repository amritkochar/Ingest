# syntax=docker/dockerfile:1.4
FROM python:3.11-slim AS base

ENV POETRY_VERSION=2.1.3 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Use a separate layer to install Poetry
RUN apt-get update && apt-get install -y curl build-essential libpq-dev && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry install

COPY . .

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
