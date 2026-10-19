#!/usr/bin/env bash
# Stop: when Python files under src/ or tests/ have uncommitted changes, runs the
# whole test suite. On failure Claude is blocked from stopping and gets the output.
# A passing state is remembered so unchanged code is not re-tested every turn.
set -uo pipefail

REPO="${CLAUDE_PROJECT_DIR:?}"
STATE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/claude-hooks"

input="$(cat)"
# Second stop attempt in a row: let Claude finish instead of looping on failures.
[ "$(echo "$input" | jq -r '.stop_hook_active // false')" = "true" ] && exit 0

cd "$REPO" || exit 0

# Before the first commit there is no HEAD: every file is untracked, so ls-files covers it.
changed="$( { git rev-parse --verify -q HEAD >/dev/null && git diff --name-only HEAD -- 'src/*.py' 'tests/*.py'
              git ls-files --others --exclude-standard -- 'src/*.py' 'tests/*.py'; } | sort -u)"
[ -n "$changed" ] || exit 0

mkdir -p "$STATE_DIR"
state_file="$STATE_DIR/$(basename "$REPO")-pytest.hash"
fingerprint="$( { git rev-parse --verify -q HEAD >/dev/null && git diff HEAD -- 'src/*.py' 'tests/*.py'
                  for f in $(git ls-files --others --exclude-standard -- 'src/*.py' 'tests/*.py'); do
                    cat "$f"; done; } | sha256sum | cut -d' ' -f1)"
[ -f "$state_file" ] && [ "$(cat "$state_file")" = "$fingerprint" ] && exit 0

out="$(uv run --quiet pytest -q --tb=short -p no:cacheprovider 2>&1)"
status=$?

# Exit code 5 = no tests collected; nothing to block on.
if [ $status -eq 0 ] || [ $status -eq 5 ]; then
  echo "$fingerprint" > "$state_file"
  exit 0
fi

reason="$(printf 'Tests fail after your changes. Fix them before finishing, or tell the user why they fail:\n%s' \
  "$(echo "$out" | tail -n 60)")"
jq -n --arg r "$reason" '{decision: "block", reason: $r}'
exit 0
