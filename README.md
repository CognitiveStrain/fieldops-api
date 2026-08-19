# FieldOps API

A production-style REST API for managing field-service jobs, technicians, assignments, and operational status.

## Why this project

This repository demonstrates backend engineering fundamentals relevant to junior software, automation, and support-oriented roles:

- clear domain modeling and API contracts
- persistent relational data
- validation and predictable error handling
- authentication and authorization boundaries
- automated unit and integration tests
- containerized local development
- continuous integration

## Planned stack

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy + Alembic
- Pytest
- Docker Compose
- GitHub Actions

## Initial scope

1. Create and manage customers, technicians, and work orders.
2. Assign work orders and track their lifecycle.
3. Record operational notes and timestamps.
4. Expose health and readiness endpoints.
5. Provide OpenAPI documentation and reproducible setup.

## Quality bar

The first release is complete only when a new contributor can clone the repository, start it with one command, run the full test suite, and understand the architectural tradeoffs from the documentation.

## Status

Architecture and implementation are in progress.
