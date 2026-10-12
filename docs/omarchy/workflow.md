# Orchestrator / executor / evaluator workflow

```text
Claude plan
   -> optional parallel research (Perplexity + Gemini)
   -> research synthesis (Gemini or Codex)
   -> Claude approves or adjusts plan
   -> Codex implementation
   -> Grok evaluation
        PASS -> short Claude diff review -> PR
        FAIL -> Codex rework -> Grok re-evaluation
```

After two failed executor/evaluator loops, return to Claude for replanning.

## Handoff files

- `PLAN.md`, `TASKS.md`, `ACCEPTANCE.md` written by Claude.
- `HANDOFF.md` written by the executor (exact test output).
- `EVALUATION.md` written by the evaluator (PASS or FAIL, blocking findings, evidence).

## Fallback routing

| Codex | Grok | Executor | Evaluator |
|---|---|---|---|
| available | available | Codex | Grok |
| exhausted | available | Gemini | Grok |
| available | exhausted | Codex | fresh Gemini session |
| exhausted | exhausted | Gemini | Claude diff-only review, or pause until quota resets |

When Gemini fills a role, keep it out of the other role. If it must do both, use independent sessions and give the evaluator only the plan, acceptance criteria, diff and test results.

## Contracts

**Claude (orchestrator):** do not implement routine code. Every task lists allowed files, required tests, stop conditions and rollback.

**Codex (executor):** execute only the assigned task, touch only allowed files, record test output in HANDOFF.md, commit but do not merge, report BLOCKED on architecture changes.

**Grok (evaluator):** read-only. Review the diff against PLAN.md and ACCEPTANCE.md, run tests, write EVALUATION.md.
