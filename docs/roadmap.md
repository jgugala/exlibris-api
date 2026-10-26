# Roadmap

Ex Libris is built in stages. Each stage adds one major FastAPI capability and leaves the application in a working state.

## Product

Users create accounts and add books to their shelf by ISBN. Each book on a shelf has a reading status (want to read / reading / read), an optional rating and review. Book details (title, author, page count) are fetched from the free Open Library API, which needs no key. An admin can moderate reviews, and a live feed streams new reviews as they are posted.

## Stage 0: Project setup

- Git repository, GitHub repo and GitHub Projects board with one milestone per stage.
- `uv`, `ruff`, `pre-commit`, `pytest`.
- `CLAUDE.md` with project conventions; ADRs in `docs/adr/`.

## Stage 1: CRUD and Pydantic

`Book` model (SQLite + SQLAlchemy, synchronous) and `GET/POST/PATCH/DELETE /books`. `Book` is a catalog entry with a globally unique ISBN.

- Path and query parameters.
- Database session provided through a `get_session` dependency with `yield`.
- Separate `BookCreate`, `BookUpdate` (all fields optional, for `PATCH`) and `BookRead` schemas.
- Validation with `Field` (rating 1–5, ISBN length).
- `response_model`, status codes, `HTTPException` (404, 409 on duplicate ISBN).
- Tooling: first GitHub Actions workflow (lint and tests), ERD in Mermaid.

## Stage 2: Structure and dependency injection

Split into `routers/`, `models/`, `schemas/` and `services/`.

- Session dependency moved to its own module.
- Pagination (`skip`/`limit`) and a `BookFilters` class dependency (status, minimum rating, author).
- `APIRouter` with `prefix` and `tags`, dependency aliases with `Annotated`.

## Stage 3: Users and authentication

Registration, login returning a JWT, `GET /me`. Books stay a shared catalog; per-user data (reading status, rating, review) moves out of `Book` into per-user tables, starting with a shelf table linking users to books (unique per user and book), so each user sees only their own shelf. `is_admin` flag and an `/admin` router protected as a whole.

- `OAuth2PasswordBearer` and the "Authorize" button in `/docs`.
- Dependency chain `get_current_user` → `get_admin`; `dependencies=[...]` on the router.
- `response_model` hiding `password_hash`; relationships between tables.
- Libraries: `pyjwt`, `pwdlib`.
- Tooling: sequence diagram of the JWT login flow.

## Stage 4: Async where it pays off

Adding a book takes only an ISBN; the rest is fetched from Open Library (`https://openlibrary.org/isbn/{isbn}.json`). A bulk import endpoint fetches many books concurrently with `asyncio.gather`.

- `async def` and `httpx.AsyncClient`, created once in `lifespan` and provided through a dependency.
- Handling upstream failures (timeout → 502).
- Optional: move the database to `AsyncSession` with `aiosqlite` and compare the diff.

## Stage 5: Background tasks and WebSocket

- After a review is posted, a notification (log or file write) runs as a `BackgroundTasks` job so the response does not wait.
- `WebSocket` endpoint `/ws/reviews` broadcasting new reviews in real time through a simple connection manager.

## Stage 6: Testing with dependency overrides

- In-memory SQLite injected via `app.dependency_overrides[get_session]`.
- Fake authenticated user instead of real login.
- Fake Open Library client returning fixed data.
- Tooling: branch protection on `main`, merges only on green CI.

## Extras

- [ ] Custom exception handlers for domain errors (e.g. `BookNotFound`)
- [ ] Middleware adding response time to a header
- [ ] Alembic migrations instead of `create_all`
- [ ] Statistics endpoint (pages read per year, average rating)
- [ ] Docker Compose with PostgreSQL

## Stage 7: Deployment on AWS

- Small EC2 instance running Docker Compose (FastAPI + PostgreSQL).
- Images in ECR, logs in CloudWatch Logs, secrets in SSM Parameter Store.
- `/health` endpoint for health checks.
- Infrastructure in Terraform/OpenTofu, created for a session and destroyed afterwards.
- GitHub Actions: build image, push to ECR, deploy to EC2, authenticating with OIDC. Dependabot for dependency updates.
- Later: RDS instead of the containerized database, Sentry for error tracking.

Why not Lambda: the WebSocket feed keeps connected clients in memory, and SQLite does not survive between invocations. A stateless function does not fit.

## Stage 8: Frontend

Separate project `exlibris-web` (React or Vue + TypeScript + Vite) with an API client generated from `/openapi.json`.

- Screens: login and registration, my shelf with filters, add book by ISBN, book details with reviews, live review feed, admin moderation.
- Backend changes: `CORSMiddleware`, JWT lifecycle (expiry, refresh token), authenticating WebSocket connections, API versioning (`/api/v1`).
- Hosting: static files on S3 + CloudFront, or Cloudflare Pages / Netlify / GitHub Pages.
- Lighter alternative: Jinja2 + HTMX served by FastAPI itself.

## Tooling

- Project management: one milestone per stage, issues per task, `Closes #N` in PRs. A GitHub Projects board (Backlog → In progress → Review → Done) is managed by hand in the browser; built-in workflows add new issues and PRs from this repo and move closed items to Done.
- Diagrams: Mermaid in the repo (ERD, sequence diagrams), Excalidraw for sketches, draw.io for AWS infrastructure.
- AI agent: Claude Code with MCP servers where they add value (GitHub, AWS read-only, Terraform, Sentry). CLI tools (`uv`, `gh`, `aws`, `terraform`) run directly; `gh` uses a fine-grained token limited to this repository. Infrastructure changes only through reviewed Terraform plans; GitHub credentials are scoped to this repo; cloud credentials (AWS) are read-only.
