---
name: codex-ship-loop
description: Ship verified Codex code changes through the shortest safe PR/MR path and clean up local state. Use when the user asks to push, merge, open or update a PR/MR, finish a branch, continue after verification, or clean up after a successful remote merge.
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
- Use `path-verify` after file changes to choose the smallest useful check.
- Use `ci-first-failure` before editing for a red PR/MR/pipeline.
- Use `glab` for GitLab issue, MR, discussion, and merge commands.
- Use GitHub-specific skills or `gh` for GitHub PRs after confirming fork/upstream target.
- Use `release-deploy-preflight` before release, deploy, package, artifact, workflow-dispatch, or production actions.
- Use Nowledge Mem for project history, then verify drift-prone facts from the live repo or remote service.

## Default Loop

1. Read in-scope instructions and repo state.
2. Verify with the narrowest relevant command.
3. Stage only intended files.
4. Commit with a Conventional Commits message.
5. Push a topic branch to the intended remote.
6. Create or update the PR/MR with the real shipped scope.
7. Check the merge gate and exact head SHA when the platform supports it.
8. Merge remotely when the user has asked for merge or the task requires end-to-end delivery.
9. Switch back to updated `main` or the repo's default branch.
10. Delete only merged local topic branches.
11. Report verification, PR/MR link, merge state, cleanup, and any leftovers.

## Guardrails

- Prefer remote PR/MR merge over local `main` merges unless the user explicitly asks for a local merge.
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
