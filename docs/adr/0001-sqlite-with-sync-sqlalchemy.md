# 0001: SQLite with synchronous SQLAlchemy until stage 4

- Status: accepted
- Date: 2026-10-22

## Context

Stage 1 needs persistence for the `Book` CRUD. The project is built in stages, each adding one major FastAPI capability, and async I/O is the topic of stage 4. A database server would add setup work that teaches nothing about FastAPI at this point.

## Decision

Use SQLite with SQLAlchemy 2.x in the typed style (`Mapped`, `mapped_column`) and synchronous sessions. Endpoints that use the database are plain `def` functions, which FastAPI runs in a thread pool. The session reaches endpoints through a `get_session` dependency with `yield`, and the database URL comes from `DATABASE_URL`. Tables are created with `create_all` at startup.

## Consequences

The app runs with no external services, and tests can point `DATABASE_URL` at a temporary file. SQLite needs `check_same_thread=False` because requests are handled in worker threads. Stage 4 revisits this decision: endpoints that call Open Library become `async def`, and moving the database to `AsyncSession` is an optional comparison. PostgreSQL arrives with Docker and AWS; `create_all` is replaced by Alembic migrations if that extra is taken.
