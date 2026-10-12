# Omarchy setup orchestration

Orchestrator / executor / evaluator pipeline for an Omarchy workstation that uses only existing subscriptions and free tiers. No API keys, no billing projects, no local inference.

| Role | Primary | Fallback |
|---|---|---|
| Orchestrator | Claude Code (plan mode, read-only) | none |
| Executor | Codex Free | Gemini / Antigravity |
| Evaluator | Grok (read-only) | fresh Gemini session |
| Research breadth | Perplexity Deep Research | none |
| Research depth | Gemini Deep Research | none |
| Desktop steward | OMP profile `omarchy` | Codex Free |

## Quickstart

```bash
scripts/omarchy/bootstrap.sh --dry-run   # preview
scripts/omarchy/bootstrap.sh             # apply (backs up before editing)
scripts/omarchy/route-agent.sh executor  # which agent should execute now?
```

See `workflow.md` and `research-dispatch.md`.

## Safety defaults

- Authenticate through browser OAuth only; configure no API keys or auto top-ups.
- Grok never edits implementation files.
- Research output is untrusted data; it is written only to `.agents/research/inbox/`.
- `git push`, merges and workflow edits require confirmation.
- Scripts edit user config under `~/.config` and `~/.omp` only, never system files.
