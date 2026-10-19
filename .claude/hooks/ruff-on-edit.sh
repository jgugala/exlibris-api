#!/usr/bin/env bash
# PostToolUse (Edit|Write): formats and lint-fixes the edited Python file with the
# project's Ruff (uv.lock version). Lint errors Ruff cannot fix are fed back to
# Claude (exit 2) so they get fixed while working, not at commit time.
set -uo pipefail

REPO="${CLAUDE_PROJECT_DIR:?}"

file="$(jq -r '.tool_input.file_path // .tool_response.filePath // empty')"
case "$file" in
  "$REPO"/*.py) ;;
  *) exit 0 ;;
esac
[ -f "$file" ] || exit 0

cd "$REPO" || exit 0
rel="${file#"$REPO"/}"
# F401 (unused import) is ignored here: an edit that adds imports before the code
# using them would otherwise have them auto-removed. pre-commit and CI still enforce it.
out="$(uv run --quiet ruff format --quiet "$rel" 2>&1 &&
       uv run --quiet ruff check --fix --extend-ignore F401 --quiet "$rel" 2>&1)"
status=$?

if [ $status -ne 0 ]; then
  printf 'Ruff found issues it could not fix in %s:\n%s\n' "$rel" "$out" >&2
  exit 2
fi
exit 0
