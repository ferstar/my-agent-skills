---
name: path-verify
description: Choose the smallest useful validation command from changed file paths. Use after edits or during review when deciding what to run for TypeScript, React, Electron/Desktop, Rust, runtime schema, docs, tests, or monorepo work.
argument-hint: "[repo]"
---

# Path Verify

Use changed paths to pick validation. Do not run the world unless the change is shared or risky.

## Start

```bash
git diff --name-only
git diff --cached --name-only
```

## Common Mapping

- `apps/desktop/**`: desktop typecheck/tests, plus Electron or e2e only for UI/runtime behavior.
- `apps/console/**`: console typecheck/build and focused tests.
- `apps/api-gateway/**`: API build/tests and endpoint smoke if changed.
- `packages/**`: package-specific typecheck/tests; broaden to dependents only when exported contracts changed.
- `crates/**`: run Rust checks from the Rust workspace root, often `crates/`.
- `tailos-runtime.lock` or schema files: run schema/CLI ensure checks and a consumer smoke.
- docs only: markdown/frontmatter/link checks if available; skip app tests.

## Rules

- One narrow check is enough for small, local changes.
- Shared protocol, runtime, auth, billing, permission, or persistence changes need a broader check.
- If a repo has a documented `just verify` or package script, prefer it over hand-assembled commands.
- Report skipped broad checks and why.
