# Ex Libris API

[![CI](https://github.com/jgugala/exlibris-api/actions/workflows/ci.yml/badge.svg)](https://github.com/jgugala/exlibris-api/actions/workflows/ci.yml)

A FastAPI service for tracking the books you read: keep a personal shelf, mark reading status, rate books and write reviews. Book metadata is fetched automatically from [Open Library](https://openlibrary.org/developers/api).

The name comes from the bookplate that marks who a book belongs to: every book on a shelf here belongs to a specific user.

Work in progress. See the [roadmap](docs/roadmap.md) for the planned stages.

## Getting started

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pre-commit install
uv run fastapi dev src/exlibris/main.py
```

Interactive API docs: http://127.0.0.1:8000/docs

## Development

```bash
uv run ruff check --fix . && uv run ruff format .
uv run pytest
uv run pre-commit run --all-files  # all pre-commit hooks on the whole repo
```
