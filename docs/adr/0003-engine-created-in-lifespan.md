# 0003: Database engine created in lifespan

- Status: accepted
- Date: 2026-10-28

## Context

ADR 0001 reads the database URL from `DATABASE_URL` and creates tables at startup. The SQLAlchemy engine could be created at module level when `database.py` is imported, or when the application starts. A module-level engine reads the configuration at import time, so tests would have to set `DATABASE_URL` before anything imports the app, and the engine would be a global singleton that code could import directly.

## Decision

The engine is created in the FastAPI `lifespan`: on startup it reads `Settings()`, creates the engine and the tables, and stores the engine and a `sessionmaker` on `app.state`; on shutdown it disposes the engine. `get_session` takes the session factory from `request.app.state`. Timestamps are stored in UTC.

## Consequences

The configuration is read when the app starts, so tests point each test at its own temporary SQLite file with `monkeypatch.setenv` and never touch `exlibris.db`. Tests must enter `TestClient` as a context manager, otherwise the lifespan does not run. Stage 4 creates the `httpx.AsyncClient` the same way, and stage 6 can still replace the session with `app.dependency_overrides[get_session]`. SQLite drops the UTC offset, so timestamp columns use a `UTCDateTime` type that converts values to UTC on write and marks them as UTC on read; API schemas get timezone-aware values without extra handling.
