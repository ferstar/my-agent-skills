---
name: path-verify
description: Compatibility helper for explicitly choosing a minimal validation command when repository instructions and package scripts do not already provide one. Do not auto-invoke after every edit or combine with repo-specific verification guidance.
disable-model-invocation: true
argument-hint: "[repo]"
---

# Path Verify

Use changed paths to pick validation. Do not run the world unless the change is shared or risky.

## Start

```bash
git diff --name-only
git diff --cached --name-only
```

## Selection order

1. Follow the nearest in-scope instructions.
2. Prefer a documented `verify`, `check`, package, or module script.
3. Map changed paths to the owning module and run its narrow check.
4. Broaden only when exported contracts or shared behavior changed.
5. For docs-only changes, use available Markdown, frontmatter, and link checks; skip application suites.

## Rules

- One narrow check is enough for small, local changes.
- Shared protocol, runtime, auth, permission, persistence, or release-contract changes need a broader check.
- If a repo has a documented `just verify` or package script, prefer it over hand-assembled commands.
- Report skipped broad checks and why.
