#!/usr/bin/env bash
# Print which agent should take a role given quota state.
# Usage: route-agent.sh executor|evaluator
# Quota state is read from env: CODEX_EXHAUSTED=1, GROK_EXHAUSTED=1
set -euo pipefail

role="${1:-}"
codex_out="${CODEX_EXHAUSTED:-0}"
grok_out="${GROK_EXHAUSTED:-0}"

case "$role" in
  executor)
    if [[ "$codex_out" == "1" ]]; then echo "gemini"; else echo "codex"; fi
    ;;
  evaluator)
    if [[ "$grok_out" == "1" ]]; then
      if [[ "$codex_out" == "1" ]]; then echo "claude-diff-only"; else echo "gemini-fresh-session"; fi
    else
      echo "grok"
    fi
    ;;
  *)
    echo "usage: $0 executor|evaluator" >&2
    exit 2
    ;;
esac
