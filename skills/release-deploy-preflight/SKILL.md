---
name: release-deploy-preflight
description: Preflight release, deploy, artifact, and dev desktop packaging work before triggering workflows. Use when the user asks to deploy, release, package desktop builds, trigger dev workflows, inspect artifacts, fix download links, or verify a deployed environment.
argument-hint: "[environment or sha]"
---

# Release Deploy Preflight

Never trigger a workflow before confirming the exact target.

## Required Facts

Collect:

- repo and workflow file
- target environment
- full 40-character SHA
- active GitHub/GitLab account and permission if workflow dispatch is needed
- artifact naming contract
- post-deploy health check

## Commands

```bash
git rev-parse HEAD
git status --short --branch
gh repo view <owner/repo> --json viewerPermission
gh workflow list
```

Use full SHA only:

```bash
case "$sha" in
  ????????-*) false ;;
esac
printf '%s\n' "$sha" | grep -Eq '^[0-9a-f]{40}$'
```

## TyClaw Defaults

- dev deploys are dispatched from `tyclaw-release`.
- run API Gateway before Console; Web only when needed.
- dev desktop packaging uses `build-desktop.yml` with empty `tag`, not `tag=dev`.
- dev desktop artifacts should be `TailOS-Dev-*`.

## Verification

Workflow success is not enough. Verify the real target: remote SHA, container command if relevant, API `/health`, Web response, Console `/login`, or artifact URL.
