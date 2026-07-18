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

## Task contract

Infer a compact contract from the user's prompt:

```text
objective: <result to achieve>
evidence: <facts that can change the decision>
scope: <objects and allowed changes>
authority: <authorized actions only>
terminal_state: <observable completion conditions>
```

Do not require the user to fill in a template when a short prompt is already
clear. State consequential assumptions and ask only when a missing choice would
materially change the result. Treat `read-only`, `edit`, `push`, `merge`,
`deploy`, `workflow-state`, `publish`, and `cleanup` as independent authorities.

## Checkpoint contract

Use one compact checkpoint that can be updated or handed off without replaying the whole thread:

```text
phase: DISCOVER | DECIDE | IMPLEMENT | VERIFY | SHIP | DONE
objective: <current intended outcome>
scope: <repo, branch, issue/PR/MR, environment>
authority: <read-only, edit, push, merge, deploy, workflow-state, publish, cleanup>
evidence: <commands, URLs, exact SHA, results>
changes: <paths or external mutations>
verification: <checks and final-object readbacks>
terminal_state: <observable completion conditions>
next: <single next action or blocker>
drift_facts: <facts that must be refreshed on resume>
```

Normal progression is `DISCOVER -> DECIDE -> IMPLEMENT -> VERIFY -> SHIP -> DONE`; skip phases that do not apply. On resume, reuse stable evidence and refresh only `drift_facts`, such as branch head, dirty state, CI, mergeability, permissions, workflow inputs, deployment health, and remote SHA.

Preflight records authority but does not expand it. Authority is not transitive:
edit does not imply push; push does not imply merge; merge does not imply deploy,
workflow-state mutation, publishing, or cleanup. Reconfirm high-impact authority
immediately before acting when the target or live state may have drifted.

The public rationale and progressive-prompt examples live in
[`docs/prompt-workflow-contract.md`](../../docs/prompt-workflow-contract.md).

## Shortcuts

- Exact path known: open it directly; skip semantic search.
- Vague code location: use `fast-context`, then confirm with `rg`.
- Structural refactor: use `ast-grep`, then confirm with exact reads.
- Remote command on macOS hosts: wrap in `zsh -lc` when a login shell is needed.

## Stop Conditions

Do not keep preflighting after the first actionable blocker is found. Fix or report that blocker.
