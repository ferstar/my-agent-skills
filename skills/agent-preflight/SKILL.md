---
name: agent-preflight
description: Run a minimal repository and environment preflight before starting non-trivial Codex work. Use when a task involves an existing repo, branch, issue, MR/PR, CI, deploy, remote host, dirty worktree, or unclear current state. This skill prevents repeated manual `git status`, auth, dependency, and context checks.
argument-hint: "[repo or task]"
---

# Agent Preflight

Use this before editing or diagnosing a repo when current state matters.

## Workflow

1. Read in-scope instructions first: `AGENTS.md`, `CLAUDE.md`, or repo README if present.
2. Capture repo state:

```bash
pwd
git status --short --branch
git remote -v
git log -1 --oneline
```

3. If the user mentioned an issue, MR, PR, CI, deploy, branch, or remote service, read that live object before reasoning from memory.
4. Check only tools needed for the task. Do not run broad version checks by default.
5. Summarize in at most 6 lines:
   - repo and branch
   - dirty files
   - linked issue/MR/PR or CI object
   - likely validation command
   - blocker if any

## Shortcuts

- Exact path known: open it directly; skip semantic search.
- Vague code location: use `fast-context`, then confirm with `rg`.
- Structural refactor: use `ast-grep`, then confirm with exact reads.
- Remote command on macOS hosts such as `my-mini`: wrap in `zsh -lc`.

## Stop Conditions

Do not keep preflighting after the first actionable blocker is found. Fix or report that blocker.
