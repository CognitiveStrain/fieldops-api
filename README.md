# FieldOps API

Production-style REST backend for tracking work orders in engineering and operations teams.

FieldOps is the backend half of a small portfolio system: the separate [QAForge](https://github.com/CognitiveStrain/qaforge) repository runs automated API and browser tests against it.

## Engineering focus

- REST API design with FastAPI and Pydantic
- SQLAlchemy 2.x persistence
- PostgreSQL production path with SQLite test/dev fallback
- Alembic database migrations
- Filtering, pagination, sorting, and total-count metadata
- Structured JSON request logging
- Pytest API coverage
- Docker + Docker Compose
- GitHub Actions CI with a real PostgreSQL service

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `POST` | `/work-orders` | Create a work order |
| `GET` | `/work-orders` | Filter, paginate, and sort work orders |
| `GET` | `/work-orders/{id}` | Get one work order |
| `PATCH` | `/work-orders/{id}` | Partially update a work order |
| `DELETE` | `/work-orders/{id}` | Delete a work order |

List queries support `status`, `priority`, `assignee`, `offset`, `limit`, `sort_by`, and `sort_order`. The response includes `X-Total-Count` so clients can implement pagination without changing the original list response shape.

## Run with PostgreSQL

```bash
docker compose up --build
```

The API becomes available at `http://localhost:8000` and interactive OpenAPI documentation at `http://localhost:8000/docs`.

Compose waits for PostgreSQL, applies `alembic upgrade head`, then starts the API.

## Local SQLite workflow

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Test

```bash
pytest -q
```

CI additionally starts PostgreSQL and verifies that the migration chain reaches the current Alembic head before running the API test suite.

## Example

```bash
curl -X POST http://127.0.0.1:8000/work-orders \
  -H "Content-Type: application/json" \
  -d '{"title":"Inspect compressor","priority":"high","assignee":"Kamal"}'
```

```bash
curl 'http://127.0.0.1:8000/work-orders?priority=high&sort_by=created_at&sort_order=desc&limit=20'
```

## Why migrations instead of `create_all()`

`Base.metadata.create_all()` is useful for disposable databases and tests, but a long-lived application needs explicit, reviewable schema history. Alembic owns the application database lifecycle; tests may still create disposable SQLite tables directly for isolation and speed.

## Next steps

- JWT authentication and role-based authorization
- deployment to a public environment
- observability/metrics
- PostgreSQL-backed integration tests for more query paths
