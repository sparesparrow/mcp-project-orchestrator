#!/usr/bin/env bash
# Idempotent Omarchy orchestration bootstrap. Use --dry-run to preview.
set -euo pipefail

DRY=0
[[ "${1:-}" == "--dry-run" ]] && DRY=1

run() {
  if (( DRY )); then echo "[dry-run] $*"; else "$@"; fi
}

TS="$(date +%Y%m%d-%H%M%S)"
BACKUP="$HOME/.local/share/omarchy-orchestration/backups/$TS"
PROFILE="$HOME/.omp/profiles/omarchy/agent"
INBOX=".agents/research/inbox"
CODEX_CFG="$HOME/.codex/config.toml"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

run mkdir -p "$BACKUP" "$PROFILE"/{agents,commands,skills} "$REPO_ROOT/$INBOX"

if [[ -f "$CODEX_CFG" ]]; then
  run cp -a "$CODEX_CFG" "$BACKUP/codex-config.toml"
fi

if [[ -f "$CODEX_CFG" ]] && grep -q 'mcp_servers.playwright' "$CODEX_CFG"; then
  echo "Playwright MCP already configured; skipping."
else
  run mkdir -p "$(dirname "$CODEX_CFG")"
  if (( DRY )); then
    echo "[dry-run] append config/omarchy/codex-config.example.toml to $CODEX_CFG"
  else
    { echo; cat "$REPO_ROOT/config/omarchy/codex-config.example.toml"; } >> "$CODEX_CFG"
  fi
fi

run cp -n "$REPO_ROOT/.claude/agents/omarchy-steward.md" "$PROFILE/agents/omarchy-steward.md"

cat <<'EOF'

Done. Manual steps (not automated on purpose):
  1. Authenticate each agent with browser OAuth. Do not add API keys.
  2. Create Perplexity and Gemini web apps via Omarchy Menu -> Install -> Web App.
  3. Move both to workspace 4 (Super+Shift+4) and arrange them side by side.
EOF
