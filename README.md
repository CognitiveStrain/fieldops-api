# FieldOps API

Authenticated REST backend for tracking work orders in engineering and operations teams.

FieldOps is the backend half of a two-repository portfolio system: [QAForge](https://github.com/CognitiveStrain/qaforge) runs automated API and browser testing against it.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/CognitiveStrain/fieldops-api)

## Engineering focus

- FastAPI + Pydantic REST contracts
- SQLAlchemy 2.x persistence
- PostgreSQL production path with SQLite test fallback
- Alembic database migrations
- JWT bearer authentication
- scrypt password hashing with per-user random salts
- role-based authorization (`viewer`, `technician`, `manager`, `admin`)
- work-order creator ownership metadata
- filtering, pagination, sorting, and `X-Total-Count`
- structured JSON request logging
- readiness and health probes
- Docker Compose and Render infrastructure-as-code
- GitHub Actions CI with a real PostgreSQL service

## Authorization model

| Role | Read | Create/update | Delete | Manage users/roles |
| --- | --- | --- | --- | --- |
| `viewer` | yes | no | no | no |
| `technician` | yes | yes | no | no |
| `manager` | yes | yes | yes | no |
| `admin` | yes | yes | yes | yes |

Public registration always creates a `viewer`. Elevated roles can only be assigned by an authenticated admin.

## API

| Method | Endpoint | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/` | public | Service metadata |
| `GET` | `/health` | public | Process health |
| `GET` | `/ready` | public | Database readiness |
| `POST` | `/auth/register` | public | Register a viewer account |
| `POST` | `/auth/token` | public | Exchange email/password for a JWT |
| `GET` | `/auth/me` | authenticated | Current user |
| `GET` | `/users` | admin | List users |
| `PATCH` | `/users/{id}/role` | admin | Change a role |
| `POST` | `/work-orders` | technician+ | Create a work order |
| `GET` | `/work-orders` | authenticated | Filter, paginate, and sort |
| `GET` | `/work-orders/{id}` | authenticated | Get one work order |
| `PATCH` | `/work-orders/{id}` | technician+ | Partially update |
| `DELETE` | `/work-orders/{id}` | manager+ | Delete |

List queries support `status`, `priority`, `assignee`, `offset`, `limit`, `sort_by`, and `sort_order`.

## Local PostgreSQL stack

Copy the example environment file and replace the placeholders:

```bash
cp .env.example .env
```

Then run:

```bash
docker compose --env-file .env up --build
```

Compose waits for PostgreSQL, applies `alembic upgrade head`, then starts the API at `http://localhost:8000`. Interactive OpenAPI documentation is at `/docs`.

## Authenticate

Register a viewer:

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"viewer@example.com","password":"a-strong-password","full_name":"Example User"}'
```

Obtain a token using OAuth2 form fields (`username` contains the email):

```bash
curl -X POST http://127.0.0.1:8000/auth/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=your-admin-password'
```

Use the returned access token:

```bash
curl http://127.0.0.1:8000/work-orders \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

## Local SQLite workflow

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

For admin-only operations, set `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` before starting the app.

## Tests

```bash
python -m pytest -q
```

The suite covers registration, login, invalid credentials/tokens, RBAC boundaries, admin role management, work-order ownership, lifecycle behavior, filtering, pagination, and validation. CI separately provisions PostgreSQL and validates the full migration chain.

## Deploy to Render

The repository contains a `render.yaml` Blueprint that provisions a public FastAPI web service and managed PostgreSQL database in Frankfurt. The Blueprint generates `JWT_SECRET` and prompts for the bootstrap admin email/password rather than committing credentials.

The free Render database is suitable for portfolio/demo use but currently expires after 30 days; use a persistent paid database for anything long-lived.

## Security

See [SECURITY.md](SECURITY.md) for implemented controls, design decisions, and known limitations.

## Next steps

- refresh-token rotation and explicit token revocation
- persistent audit events for privileged actions
- metrics/tracing
- deployed QAForge smoke tests against the public environment
