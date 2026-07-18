---
name: codex-ship-loop
description: Carry already-scoped code changes through verification, commit, push, PR/MR, authorized merge, and authorized cleanup. Use when the requested outcome includes delivery actions; do not use for review-only work, initial repo discovery, CI diagnosis, or deploy execution.
---

# Codex Ship Loop

## Overview

Use this as the delivery loop after implementation is done or when the user asks Codex to carry a branch through review/merge. Keep it thin: route specialized work to existing skills, verify narrowly, and avoid project-specific lore unless current memory or live state confirms it.

## Scope Check

Say one short scope line before acting:

- repo or product area
- branch and target remote
- whether the action has external side effects
- whether release, deploy, or production systems are involved

Do not ask if the target is already clear from the user's request and live repo state.

## Route First

- Start with `agent-preflight` if repo state, branch, issue, PR/MR, CI, or remote target is unclear.
- Follow repository validation guidance after file changes; use the narrowest owning-module check and broaden only for shared contracts or release risk.
- Use `ci-first-failure` before editing for a red PR/MR/pipeline.
- Use `glab` for GitLab issue, MR, discussion, and merge commands.
- Use GitHub-specific skills or `gh` for GitHub PRs after confirming fork/upstream target.
- Use `release-deploy-preflight` before release, deploy, package, workflow-dispatch, or production actions.
- Use `artifact-verify` when the requested outcome is proof of an existing artifact's contents or provenance.
- Use Nowledge Mem for project history, then verify drift-prone facts from the live repo or remote service.

## Checkpoint and handoff contract

Maintain the same compact checkpoint used by preflight:

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

Advance through `DISCOVER -> DECIDE -> IMPLEMENT -> VERIFY -> SHIP -> DONE`, skipping phases that do not apply. A handoff includes the checkpoint, not a transcript recap. On resume, preserve stable implementation evidence and refresh only drift-prone facts: dirty state, branch/default-branch heads, PR/MR head SHA, discussions, CI, mergeability, permissions, workflow inputs, deployed health, and remote SHA.

## Default Loop

1. Read in-scope instructions and repo state.
2. Verify with the narrowest relevant command.
3. Stage only intended files.
4. Commit with a Conventional Commits message.
5. Push a topic branch to the intended remote.
6. Create or update the PR/MR with the real shipped scope.
7. Check the merge gate and exact head SHA when the platform supports it.
8. Merge remotely only when explicitly authorized by the user. A request to open or update a PR/MR is not merge authority.
9. Switch back to updated `main` or the repo's default branch.
10. Delete only merged local topic branches, and only when cleanup was requested or is explicit in the stated end-to-end outcome.
11. Report verification, PR/MR link, merge state, cleanup, and any leftovers.

## Guardrails

- Prefer remote PR/MR merge over local `main` merges unless the user explicitly asks for a local merge.
- Treat review-only as read-only: do not edit, push, merge, deploy, relabel, close, or clean up.
- Merge authority does not imply deploy authority. Deploy authority does not imply issue closure or branch cleanup.
- After merge, derive issue state from the requested workflow: an issue may intentionally remain open with a verification/testing label. Avoid auto-close syntax unless closure is intended.
- Do not delete remote branches unless explicitly requested or the merge command's source-branch removal is clearly part of the platform flow.
- Do not touch unrelated untracked files, planning docs, assets, or dirty worktree changes.
- Do not create Windows worktrees by default; use the current checkout and stash only when necessary.
- Do not broaden validation just because a broad command exists. Broaden for security boundaries, shared protocols, release, deploy, or CI reproduction.
- Do not turn project memories into facts without checking live state when remotes, versions, CI, releases, or permissions may have changed.

## Output

Keep the final response short:

- changed files
- verification command and result
- PR/MR or release link if created
- merge and cleanup result
- skipped checks or blocked actions
