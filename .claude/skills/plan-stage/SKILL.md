---
name: plan-stage
description: Break a roadmap stage of exlibris-api into GitHub issues with acceptance criteria and create them, with a milestone, via gh. Use when the user wants to plan a stage, create issues or a milestone for it ("rozpisz etap 3 na issues", "zaplanuj etap"), or draft a single issue. Do NOT use for implementing the work (use task-solving-planner) or for organisational issues with no technical content.
---

# Plan Stage

Turns one stage of `docs/roadmap.md` into a milestone and a handful of issues that can each be implemented and reviewed on their own.

## 1. Read

Read the stage in `docs/roadmap.md` and the current code it builds on. Check what already exists on GitHub:

```bash
gh api repos/{owner}/{repo}/milestones --jq '.[] | "\(.number) \(.title)"'
gh issue list --milestone "<milestone title>" --state all
```

## 2. Draft

Propose 3–7 issues. Each issue is one reviewable piece of work (roughly one PR-sized change), not one bullet of the roadmap. Per issue:

```
### <imperative title, under 70 chars>

<1–2 sentences: what and why>

**Scope**
- concrete deliverables
- out of scope: what looks related but belongs elsewhere

**Acceptance criteria**
- [ ] GIVEN … WHEN … THEN … (concrete paths, status codes, field values)

**Notes**
- FastAPI mechanisms this exercises, gotchas, links to docs
```

Rules: at most 5 acceptance criteria per issue (more → split it); include negative cases (invalid input, missing resource, other user's data); no vague wording like "works correctly". Order the issues so each builds on the previous one, and say which depend on which.

Show the whole list as a table first (title, one-line goal, depends on), then the full issue texts. Ask for changes; iterate until the user approves.

## 3. Create

After approval:

```bash
gh api repos/{owner}/{repo}/milestones -f title="Stage N: <name>" -f description="<one line from the roadmap>"   # if missing
gh issue create --title "<title>" --body-file <scratchpad>/issue-K.md --milestone "Stage N: <name>"
```

Write each body to a file in the scratchpad directory so Markdown survives quoting. If the user has a GitHub Projects board, add each issue to it (`gh project item-add <project-number> --owner @me --url <issue-url>`).

Reply with a table: issue number, title, URL.

## Notes

- Issue text is in English (it lives in the public repo); talk to the user in their language.
- Updating `docs/roadmap.md` is in scope only if planning changed the stage's scope; show that diff too.
