# CLAUDE.md

Ex Libris (`exlibris-api`) is a FastAPI service for tracking books you read: a personal shelf, reading status, ratings and reviews, with book metadata fetched from Open Library.

Scope and stages: `docs/roadmap.md`. It is the source of truth for what gets built. Update it when the scope changes.

## How we work

- Before implementing a stage, agree on the contract: endpoints, schemas, status codes and error cases. Then implement it.
- Stay within the current stage. Do not pull in mechanisms planned for later stages (e.g. async DB access before stage 4) without agreement.
- Record design decisions as ADRs in `docs/adr/NNNN-short-title.md` (context, decision, consequences; a few sentences each).
- Do not commit, push or open PRs unless asked.

## Workflow

- One stage = one GitHub milestone with issues (`/plan-stage`) = one branch `stage-N-short-name` with a PR to `main` (`/pr`).
- Implementing a stage or issue goes through `/task-solving-planner`.
- Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`), enforced by a `commit-msg` hook. Issues are referenced as `#N` in the commit body or PR (`Closes #N`), not in the subject. No `Co-Authored-By` or other AI attribution trailers in commits or PRs.
- Hooks: Ruff formats and lints every edited Python file; the test suite runs when a turn ends with uncommitted changes in `src/` or `tests/` and blocks on failures.
- Before handing work back, run lint, format and tests (commands below). Work is done when they pass.

## Stack and decisions

- Python 3.13, dependencies and venv managed by `uv` (`uv add`, never `pip install`).
- FastAPI, Pydantic v2, SQLAlchemy 2.x in the typed style (`Mapped`, `mapped_column`).
- Database: SQLite with synchronous sessions until stage 4. PostgreSQL arrives with Docker (extras) and AWS (stage 7).
- `src/` layout with the package `src/exlibris/`. From stage 2 it is split into `routers/`, `models/`, `schemas/` and `services/`.
- Anything that tests need to replace (DB session, current user, Open Library client) is provided through `Depends()`. No module-level singletons imported directly by endpoints.
- Configuration through environment variables (`pydantic-settings`). No secrets in the repo; `.env.example` documents the variables.
- Tests: `pytest` with `TestClient`, written from stage 1 alongside features. Stage 6 adds `dependency_overrides` and fakes.
- Code, identifiers, API messages, commits and repo docs are in English.

## Commands

```bash
uv sync                                  # install dependencies
uv run fastapi dev src/exlibris/main.py  # dev server, docs at /docs
uv run ruff check --fix . && uv run ruff format .
uv run pytest
uv run pre-commit run --all-files
```
