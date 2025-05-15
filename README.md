# Ingest - Project Overview

This service ingests "feedback" data from multiple external platforms (Google Play Store, Twitter, Discourse, Intercom) into a unified PostgreSQL-backed store. It uses a pull-adapter pattern (each source implements a BaseFetcher interface) and a push-handler pattern for webhooks. Core engineering practices include:

- Modular, reusable blocks: each adapter/service is self-contained
- Dependency injection & fixtures: easy mocking in tests
- Asynchronous I/O with httpx and asyncio for high throughput
- Database upserts using PostgreSQL's unique constraints to ensure idempotency
- Scheduler via APScheduler for periodic pulls
- 12-factor configuration with Pydantic BaseSettings

> **Points to Note**:  
> - The current implementation uses stubbed data and is not connected to real-world sources with valid tokens or credentials.  
> - Integration with actual platform APIs will require updating the configuration with correct app IDs, API keys, and secrets.
> - Multi-tenancy is currently managed through `settings.py`, which is static.
> - Error handling is deliberately minimal for clarity.
> - Rate limiting, pagination handling, and backoff strategies are not yet implemented in the pull adapters.
> - The ingestion logic assumes a single unique constraint on `(tenant_id, source_type, external_id, source_instance)`.
> - Webhook validation (e.g., HMAC signatures for Intercom) is stubbed and should be implemented before going live.
> - All timestamps use naive `datetime.utcnow()` rather than timezone-aware alternatives.
> - APScheduler is run in-process and not persisted; scheduled jobs are not restored on container restarts or crashes.


## Improvements & Future Work

- Integrate with real-world credentials for each platform source, right now we have stubbed data.
- Move sensitive data (e.g., API keys, tokens) to `.env` files for better security and separation of concerns.
- Improve security by implementing a lightweight authentication layer, such as JWT-based login, to prevent unauthorized cross-tenant data access.
- Introduce Role-Based Access Control (RBAC) to manage permissions and ensure fine-grained access control.
- Create a lightweight UI to visualize and interact with ingested feedback data.
- Use Tenacity to add retry mechanism properly.
- Switch to Celery (or RQ) for more robust, distributed scheduling & retries.
- Persist tenant & platform config in a database table rather than in settings, with runtime reloading capability.
- Modularize adapters further—e.g., shared HTTP client, retry/backoff policies.
- Add structured logging (JSON) and centralized log aggregation.
- GraphQL or gRPC API for richer queries & subscriptions.
- Better error handling and metrics (Prometheus, healthchecks), including retries, circuit breakers, and alerting.
- Support dynamic tenant onboarding via an admin UI.
- Add end-to-end performance/load testing.
- Implement proper rate limiting, pagination handling, and backoff strategies in the pull adapters.
- Refine unique constraints if upstream platforms evolve (e.g., nested threads or duplicate IDs).
- Move to a distributed approach for large-scale deployments rather than using a centralized scheduler.
- Implement proper webhook validation (e.g., HMAC signatures for Intercom).
- Use timezone-aware timestamps (`datetime.now(timezone.utc)`) to avoid subtle bugs in time filtering.


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
export PYTHONPATH=src # without this it might lead to errors

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