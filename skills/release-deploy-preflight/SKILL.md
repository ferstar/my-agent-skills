---
name: release-deploy-preflight
description: Resolve target, workflow inputs, exact source SHA, authority, and live verification before release, deploy, packaging, or workflow dispatch. Use for operations that may mutate a release or environment; use artifact-verify instead when only inspecting artifact contents.
argument-hint: "[environment or sha]"
---

# Release Deploy Preflight

Confirm the exact target before any external mutation. This skill ends at preflight and verification guidance; it does not grant dispatch, release, deploy, or publish authority.

## Required Facts

Collect:

- repo and workflow file
- target environment
- full 40-character SHA
- active GitHub/GitLab account and permission if workflow dispatch is needed
- artifact naming contract and expected source provenance
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

Read project-specific workflow names, ordering, channels, and artifact naming from the live repository or private configuration. Do not infer them from a familiar product or environment name.

## Boundaries

- Use `ci-first-failure` when an existing run is red.
- Use `artifact-verify` for complete download, archive integrity, unpacked contents, metadata, and lock/provenance checks.
- Use `remote-health` only when host reachability or remote services are the failing layer.
- Reconfirm authority immediately before dispatch. Merge, deploy, release, publish, and cleanup are separate mutations and must each be covered by the user's request.

## Verification

Workflow success is not enough. Verify the real target using the checks defined by that repository: for example remote SHA, service or container state, health endpoint, public response, or artifact provenance. Report the exact deployed SHA.
