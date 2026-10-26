---
name: task-solving-planner
description: Gated approach for implementing one GitHub issue, or one non-trivial change without an issue, in exlibris-api - branch, requirements, API contract, implementation, tests, review, summary. Use whenever the user asks to implement an issue ("zrób #12"), the next task of a stage ("zaimplementuj etap 2", "następne issue"), build new endpoints, or change behaviour across schemas, models and routers. Do NOT use for typo fixes, config tweaks, docs-only changes, or when the user says to skip planning and just do it.
---

# Task Solving Planner

Branch → understand → agree on the contract → implement → test → review → summarize. Two gates where the user decides; everything between them runs without stopping.

One run handles one issue. When the user names a stage instead, pick the lowest-numbered open issue of its milestone whose dependencies are closed (`gh issue list --milestone "<title>" --state open`) and confirm it with the user before starting.

## 0. Branch

Start from an up-to-date `main` (`git switch main && git pull`). Uncommitted changes → ask whether they belong to this issue before switching. Create the branch `N-short-name` (e.g. `4-create-read-books`).

## 1. Requirements

Read the source of the task: the stage in `docs/roadmap.md` and/or the issue (`gh issue view <N>`). Read the code it touches. List as a numbered checklist:
- explicit requirements from the stage/issue,
- implicit ones: validation, error cases and status codes, ownership/auth checks once stage 3 exists, tests.

Flag anything ambiguous as a question. Do not guess.

## 2. Contract — Gate 1

Present, compactly:
- endpoints: method, path, request/response schema, status codes, error cases;
- schema and model changes (fields, types, constraints);
- new dependencies (`Depends()`), libraries, config variables;
- files to create or change, one line each;
- any decision worth an ADR.

**Wait for approval.** This is the cheapest point to change direction.

## 3. Implementation

Implement in this order: models → schemas → services → dependencies → routers → wiring in `main.py`. Follow `CLAUDE.md` (typed SQLAlchemy, everything replaceable goes through `Depends()`, scope of the current stage only). Track sub-tasks with the task tools when there are more than three.

The `ruff-on-edit` hook formats each file and reports lint errors as you go; fix them immediately.

## 4. Tests

Cover every endpoint: the happy path, each validation and error case from the contract, and ownership/permission cases where they apply. Test names `test_<action>_<scenario>` (`test_create_book_duplicate_isbn_returns_409`). One behaviour per test, Arrange → Act → Assert. Use fakes over `unittest.mock` for anything injected.

Run `uv run pytest` and `uv run ruff check .`. The `pytest-on-stop` hook will block finishing on red tests anyway.

## 5. Review

Run the `code-review` skill at `high` effort on the change. Fix every must-fix and should-fix finding; if fixes were substantial, review once more (two rounds at most, then report what remains). Do not spawn subagents for this unless the user asks.

If no review ran, say so in the summary instead of presenting a self-check as a review.

## 6. Summary — Gate 2

Tell the user, briefly and in their language:
- the requirements checklist with ✅ / ❌,
- files changed, one line each,
- tests added and the result,
- what the review found and what was fixed,
- **what FastAPI mechanisms this used and why** (a few sentences — the project is also for learning).

Then propose the commit: list of files and the message (Conventional Commits, `Closes #N` in the body). Commit only after the user's "ok", then offer `/pr` to open the pull request.

## Notes

- A small task still goes through every step, with one or two lines per step.
- If the contract changes during implementation, stop and show the change before continuing.
