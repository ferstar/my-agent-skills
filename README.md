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

### `gitlab-mr-context`

Reliable GitLab issue/MR/pipeline/comment context gathering with `glab api`.

### `ci-first-failure`

Find the first real failing GitHub Actions or GitLab CI job before editing.

### `path-verify`

Choose the smallest useful validation command from changed file paths.

### `release-deploy-preflight`

Preflight release, deploy, artifact, and desktop packaging workflows.

### `remote-health`

Diagnose SSH, Tailscale, PATH, service, lock, and remote Codex issues.

## Conventions

- Keep each skill focused on one job
- Put trigger conditions and workflow in `SKILL.md`
- Keep runtime checks and smoke tests in `tests/`, not inside skill directories
- Avoid committing `node_modules`, caches, or temporary outputs
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
