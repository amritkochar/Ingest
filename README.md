# Ingest - Project Overview

This service ingests "feedback" data from multiple external platforms (Google Play Store, Twitter, Discourse, Intercom) into a unified PostgreSQL-backed store. It uses a pull-adapter pattern (each source implements a BaseFetcher interface) and a push-handler pattern for webhooks. Core engineering practices include:

- Modular, reusable blocks: each adapter/service is self-contained
- Dependency injection & fixtures: easy mocking in tests
- Asynchronous I/O with httpx and asyncio for high throughput
- Database upserts using PostgreSQL's unique constraints to ensure idempotency
- Scheduler via APScheduler for periodic pulls
- 12-factor configuration with Pydantic BaseSettings

## Repository Structure

```
.
├── src/
│   ├── app/
│   │   └── main.py                 # FastAPI app, endpoints & startup
│   ├── adapters/                   # Pull adapters for each platform
│   │   ├── playstore.py
│   │   ├── twitter.py
│   │   ├── discourse.py
│   │   └── intercom.py
│   ├── ports/                      # Adapter & handler interfaces
│   │   ├── fetcher.py
│   │   └── push_handler.py
│   ├── services/
│   │   └── ingest.py               # DB upsert logic
│   ├── workers/
│   │   └── scheduler.py            # APScheduler job setup
│   ├── config/
│   │   └── settings.py             # Pydantic settings & multi-tenant config
│   ├── db/
│   │   ├── models.py               # SQLAlchemy ORM definitions
│   │   └── session.py              # AsyncSessionLocal
│   └── core/
│       ├── models.py               # Pydantic Feedback schema
│       └── exceptions.py           # AdapterError, etc.
├── tests/
│   ├── adapters/                   # Unit tests for each adapter
│   ├── services/
│   ├── integration/
│   └── test_dry_run.py             # End-to-end "dry run" assertions
├── scripts/
│   ├── create_tables.py            # Initialize DB tables
│   └── dry_run.py                  # Populate & query sample data
├── docker-compose.yml
├── pyproject.toml                  # Poetry config
├── Makefile
└── README.md                       # ← this file
```

## Getting Started

### Prerequisites

- Poetry for dependency & virtual-env management
- Docker & docker-compose for Postgres

### 1. Install & Activate

```bash
# ensure in-project venv
poetry config virtualenvs.in-project true

# install dependencies & create venv
poetry install

# activate the venv (bash/zsh)
source .venv/bin/activate

# verify
which python   # .venv/bin/python
python --version  # 3.11.x
```

### 2. Start Database

```bash
docker-compose up -d db
```

Wait until db is healthy (→ `docker-compose ps`).

### 3. Initialize Schema

```bash
poetry run python scripts/create_tables.py
```

### 4. Populate & Smoke-Test

```bash
# dry_run: insert sample data across tenants & platforms
poetry run python scripts/dry_run.py

# run the FastAPI app
docker-compose up -d app

# or locally:
poetry run uvicorn src.app.main:app --reload
```

### 5. Try the Endpoints

```bash
# Intercom webhook push
curl -X POST http://localhost:8000/webhook/intercom/tenant1 \
  -H "Content-Type: application/json" \
  -d @tests/adapters/mock_intercom_push.json

# List feedback
curl "http://localhost:8000/feedback?tenant_id=tenant1&source_type=playstore"

# Fetch one by UUID
curl "http://localhost:8000/feedback/<FEEDBACK_UUID>?tenant_id=tenant1"
```

## Testing

```bash
# run all unit & integration tests
poetry run pytest -q
```

## Configuration

All settings live in `src/config/settings.py` (and `.env`). Key sections:
- `TENANTS`: list of tenant IDs
- `PLATFORM_CONFIG`: per-tenant app IDs, API keys, base URLs, tokens, secrets
- `POLL_INTERVALS`: frequency per platform
- `DISPATCH_INTERVAL_SEC`: how often to run the full dispatch job

## Improvements & Future Work

- Switch to Celery (or RQ) for more robust, distributed scheduling & retries
- Persist tenant & platform config in a database table rather than in settings
- Modularize adapters further—e.g. shared HTTP client, retry/backoff policies
- Add structured logging (JSON) and centralized log aggregation
- GraphQL or gRPC API for richer queries & subscriptions
- Better error handling and metrics (Prometheus, healthchecks)
- Support dynamic tenant onboarding via an admin UI
- Add end-to-end performance/load testing