---
name: agent-preflight
description: Establish the current repo, instruction, branch, dirty-worktree, and linked live-object facts before non-trivial work. Use once at the start of repo work when current state or scope is unclear; do not stack it onto every later workflow phase.
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
5. Summarize in at most 6 lines and write the initial checkpoint:
   - repo and branch
   - dirty files
   - linked issue/MR/PR or CI object
   - likely validation command
   - blocker if any

## Checkpoint contract

Use one compact checkpoint that can be updated or handed off without replaying the whole thread:

```text
phase: DISCOVER | DECIDE | IMPLEMENT | VERIFY | SHIP | DONE
objective: <current intended outcome>
scope: <repo, branch, issue/PR/MR, environment>
authority: <read-only, edit, push, merge, deploy, cleanup>
evidence: <commands, URLs, exact SHA, results>
changes: <paths or external mutations>
next: <single next action or blocker>
drift_facts: <facts that must be refreshed on resume>
```

Normal progression is `DISCOVER -> DECIDE -> IMPLEMENT -> VERIFY -> SHIP -> DONE`; skip phases that do not apply. On resume, reuse stable evidence and refresh only `drift_facts`, such as branch head, dirty state, CI, mergeability, permissions, workflow inputs, deployment health, and remote SHA.

Preflight records authority but does not expand it. Merge, deploy, publishing, destructive cleanup, and remote branch deletion require explicit user authorization or a user request whose stated outcome necessarily includes that action.

## Shortcuts

- Exact path known: open it directly; skip semantic search.
- Vague code location: use `fast-context`, then confirm with `rg`.
- Structural refactor: use `ast-grep`, then confirm with exact reads.
- Remote command on macOS hosts: wrap in `zsh -lc` when a login shell is needed.

## Stop Conditions

Do not keep preflighting after the first actionable blocker is found. Fix or report that blocker.
