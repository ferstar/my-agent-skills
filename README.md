# my-agent-skills

Public repository of custom Agent Skills.

## Structure

- `skills/<skill-name>/` — one skill per directory
- each skill contains a required `SKILL.md`
- optional resources: `scripts/`, `references/`, `assets/`
- repository-level smoke tests live in `tests/`

## Current skills

### `exa-tools`

Use the bundled Exa API wrapper for live web research, technical documentation or code lookup, and company background research with source URLs.

Design goals:
- keep the skill focused on current external research and Exa-backed context gathering
- prefer a small local wrapper over MCP dependency
- make command selection obvious in `SKILL.md`
- preserve structured output paths for downstream automation

### `rapidocr`

Use RapidOCR to extract text from local images, return structured JSON, flag low-confidence or amount-like OCR lines for review, and optionally reconstruct a heuristic Markdown table.

Design goals:
- keep OCR execution local and file-only
- install Python tool dependencies with `uv tool`
- expose review hints for prices, quantities, and low-confidence text
- keep table reconstruction explicitly heuristic

### `glab`

GitLab CLI skill for issues, merge requests, CI/CD, API operations, threaded discussion replies, and work item conversion or hierarchy updates.

Design goals:
- keep `SKILL.md` as a routing layer
- move detail into `references/`
- prefer `glab api` for repeatable automation

### `opencli`

Use OpenCLI for browser-session-backed web reading and supported site/channel commands such as Doubao, Weixin, Zhihu, YouTube, and Bilibili.

Design goals:
- prefer site-specific commands before generic `opencli web read`
- keep the skill scoped to read-only, browser-backed web tasks
- document strict URL validation and bridge prerequisites

### `agent-preflight`

Minimal repo and environment preflight before non-trivial Codex work.

### `agent-boundary-hardening`

Audit and repair repository-level agent scope and permission overreach without turning general security review into a routing dependency.

### `define-goal`

Create or refine measurable goals only when goal-backed work is explicitly requested.

### `codex-ship-loop`

Ship verified Codex code changes through PR/MR, remote merge, and local cleanup.

### `ci-first-failure`

Find the first real failing GitHub Actions or GitLab CI job before editing.

### `release-deploy-preflight`

Preflight release, deploy, desktop packaging, and workflow-dispatch operations.

### `artifact-verify`

Verify downloaded build artifacts, archives, metadata, contents, and source provenance without triggering release or deploy workflows.

### `remote-health`

Diagnose SSH, Tailscale, PATH, service, lock, and remote Codex issues.

### `tianbot-docs`

Answer Tianbot product questions from current official documentation without hardcoding version-sensitive facts.

## Standalone public skills

Some public skills are maintained as complete standalone repositories rather than duplicated under `skills/`:

- [`fast-context`](https://github.com/ferstar/fast-context) — Python-first hybrid repository context search with its own `SKILL.md`, runtime source, tests, and lockfile. Install and update it from that upstream repository.

## Conventions

- Keep each skill focused on one job
- Put trigger conditions and workflow in `SKILL.md`
- Keep runtime checks and smoke tests in `tests/`, not inside skill directories
- Avoid committing `node_modules`, caches, or temporary outputs
- Do not vendor a second copy of a skill that already has a dedicated public source repository
- Prefer standard library and small dependency sets over legacy packages
- Run every new or imported skill through `skill-creator` conventions before treating it as done

## Local install

```bash
scripts/link-user-skills.sh
```

```powershell
.\scripts\link-user-skills.ps1
```

This links repo skills into `~/.agents/skills`. Use `--force` / `-Force` only when replacing an existing local copy is intentional.
