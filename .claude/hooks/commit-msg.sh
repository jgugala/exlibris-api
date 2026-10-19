#!/usr/bin/env bash
# git commit-msg hook (run by pre-commit at the commit-msg stage): requires a
# Conventional Commits subject, e.g. "feat(books): add PATCH /books/{id}".
# Merge/revert/fixup/squash commits pass.
msg="$(head -n1 "$1")"
case "$msg" in
  Merge\ *|Revert\ *|fixup!\ *|squash!\ *|amend!\ *) exit 0 ;;
esac
types='feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert'
if ! printf '%s' "$msg" | grep -qE "^($types)(\([a-z0-9-]+\))?!?: .+"; then
  echo "commit-msg: subject must follow Conventional Commits, e.g. 'feat(books): add search', got: $msg" >&2
  exit 1
fi
