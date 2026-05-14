#!/bin/sh
set -u

HOOK_NAME="${1:-hook}"

if [ "${GITNEXUS_AUTO_ANALYZE_DISABLED:-0}" = "1" ]; then
  echo "[gitnexus] ${HOOK_NAME}: auto-refresh disabled"
  exit 0
fi

if [ -n "${CI:-}" ]; then
  echo "[gitnexus] ${HOOK_NAME}: skipping in CI"
  exit 0
fi

if ! command -v git >/dev/null 2>&1; then
  echo "[gitnexus] ${HOOK_NAME}: git not available"
  exit 0
fi

if ! command -v npx >/dev/null 2>&1; then
  echo "[gitnexus] ${HOOK_NAME}: npx not available"
  exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || printf '')"
if [ -z "${REPO_ROOT}" ]; then
  echo "[gitnexus] ${HOOK_NAME}: not inside a git repository"
  exit 0
fi

cd "${REPO_ROOT}" || exit 0

CHANGED_FILES=''
case "${HOOK_NAME}" in
  post-commit)
    CHANGED_FILES="$(git show --pretty='' --name-only HEAD 2>/dev/null || printf '')"
    ;;
  post-merge)
    if git rev-parse --verify ORIG_HEAD >/dev/null 2>&1; then
      CHANGED_FILES="$(git diff --name-only ORIG_HEAD HEAD 2>/dev/null || printf '')"
    fi
    ;;
esac

if [ -n "${CHANGED_FILES}" ]; then
  MARKDOWN_ONLY_CHANGES=1
  OLD_IFS=$IFS
  IFS='
'
  for path in ${CHANGED_FILES}; do
    case "${path}" in
      *.[mM][dD]) ;;
      *)
        MARKDOWN_ONLY_CHANGES=0
        break
        ;;
    esac
  done
  IFS=$OLD_IFS

  if [ "${MARKDOWN_ONLY_CHANGES}" = "1" ]; then
    echo "[gitnexus] ${HOOK_NAME}: skipping index refresh for Markdown-only changes"
    exit 0
  fi
fi

set -- -y gitnexus@latest analyze
if [ -f .gitnexus/meta.json ] && grep -Eq '"embeddings"[[:space:]]*:[[:space:]]*[1-9][0-9]*' .gitnexus/meta.json; then
  set -- -y gitnexus@latest analyze --embeddings
fi

echo "[gitnexus] ${HOOK_NAME}: refreshing index from ${REPO_ROOT}"
if npx "$@"; then
  echo "[gitnexus] ${HOOK_NAME}: index refresh complete"
else
  status=$?
  echo "[gitnexus] ${HOOK_NAME}: index refresh failed with exit code ${status}" >&2
fi

exit 0
