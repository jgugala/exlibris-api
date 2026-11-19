# 0004: Service layer between routers and the database

- Status: accepted
- Date: 2026-11-19

## Context

In stage 1 the book endpoints held the queries, commits and error handling themselves. Stage 4 adds Open Library lookups and stage 3 per-user shelves, so that logic will grow, and it should be testable without `TestClient`. A repository layer between services and SQLAlchemy was also considered.

## Decision

Routers translate HTTP into function calls and domain errors into status codes. They own path and query parameters, `response_model`, status codes and `HTTPException`. Services in `exlibris/services/` hold queries, transactions (`commit`/`rollback`) and business rules. They are plain functions that take a `Session` and plain or schema arguments, and they never import FastAPI. Failures are raised as domain exceptions (`BookNotFoundError`, `DuplicateIsbnError`), not `HTTPException`, because a status code is an HTTP concern and the same service will be called from places without HTTP semantics (bulk import, background tasks, a WebSocket). Routers map them with `try/except`. Global exception handlers are deferred to Extras.

No repository layer: the SQLAlchemy `Session` already provides the Repository and Unit of Work patterns, and with CRUD-only logic every service function would just forward to a repository method. Tests run against a real temporary SQLite database, which also checks constraints such as the unique ISBN, so a fake repository would not buy much.

## Consequences

Services are unit-tested with a `Session` and no HTTP client; routers stay a few lines per endpoint, with some repeated `try/except` until exception handlers arrive. A repository is worth revisiting when the same non-trivial queries repeat across services (likely with the shelf joins in stage 3) or when service logic needs testing in isolation from the database; an Open Library fake in stage 4 is a client fake, not a repository.
