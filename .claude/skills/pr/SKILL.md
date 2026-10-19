---
name: pr
description: Open a GitHub pull request for the current exlibris-api branch - Conventional Commits title, a short description from .github/PULL_REQUEST_TEMPLATE.md, base main, linked issues, the user as assignee. Use whenever the user asks to open, create or prepare a PR ("zrób PR", "otwórz pull request", "wystaw PR-a") or to draft or rewrite a PR description. Do NOT use for reviewing someone else's PR.
---

# Pull request

A reviewer should be able to read the whole description before opening the diff. Keep it short.

## 1. Gather facts

- `git log --oneline main..HEAD` and `git diff --stat main...HEAD`, then read the diff. Describe what the code does, not what the commit messages claim.
- Issues the branch resolves: from the user, the branch name, commit bodies, or `gh issue list --milestone ...`. None found → ask.
- Uncommitted changes → tell the user and ask whether they belong in the PR.
- Run `uv run pre-commit run --all-files` and `uv run pytest`. If they fail, report and stop.

## 2. Write title and body

**Title:** Conventional Commits, imperative (`feat(books): add CRUD endpoints`). On a single-commit branch, reuse the commit subject.

**Body:** fill `.github/PULL_REQUEST_TEMPLATE.md`:
- **Why:** one or two bullets: the goal and which stage it belongs to.
- **How:** a handful of one-line bullets with the decisions a reviewer needs (new dependency, where logic lives, non-obvious behaviour, error handling). Not a file-by-file tour.
- **Closes:** `Closes #N` per issue, so merging closes them and moves the cards.
- Delete template sections that don't apply instead of explaining why.
- No test output, no "tested locally".

Re-read the draft as a reviewer would and cut what they would skim past.

## 3. Confirm, then create

Show title and body and ask for the go-ahead (pushing is visible to others), unless the user already said to just create it.

```bash
git push -u origin HEAD
gh pr create --base main --assignee @me --title "<title>" --body-file <scratchpad>/pr-body.md
```

Write the body to a file in the scratchpad directory so backticks survive. If `gh` cannot read that path (snap confinement), use `--body-file - < <file>`. Reply with the PR URL.

When the user only wants the description, stop after step 2. For an existing PR, offer `gh pr edit <n> --body-file ...`.
