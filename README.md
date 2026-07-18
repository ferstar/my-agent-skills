# my-agent-skills

[English](README.md) | [简体中文](README.zh-CN.md)

Public repository of custom Agent Skills.

## Structure

- `skills/<skill-name>/` — one skill per directory
- each skill contains a required `SKILL.md`
- optional resources: `scripts/`, `references/`, `assets/`
- repository-level smoke tests live in `tests/`

## Prompt workflow methodology

Use short prompts for ordinary work. Add structure only when it prevents a real
mistake:

```text
objective + evidence + scope + authority + terminal_state
```

Work progresses through the smallest applicable path:

```text
DISCOVER -> DECIDE -> IMPLEMENT -> VERIFY -> SHIP -> DONE
```

Authority is not transitive. Treat `read-only`, `edit`, `push`, `merge`,
`deploy`, `workflow-state`, `publish`, and `cleanup` as separate grants. Long or
resumed work uses a compact checkpoint, reuses stable evidence, and refreshes
only drift-prone facts. A task reaches `DONE` only after its local and remote
terminal state has been read back and verified.

See the complete [prompt workflow contract](docs/prompt-workflow-contract.md).

## Harness observability

The `harness-observe` skill provides a privacy-safe improvement loop backed by
one local append-only JSONL source of truth. It records workflow outcomes,
terminal-state verification, skill use, authority decisions, normalized failure
classes, duration, and token counts without storing prompts, responses, commands,
paths, URLs, or tool payloads.

Codex lifecycle coverage is installed as deterministic `UserPromptSubmit` and
`Stop` hooks rather than a default global-prompt instruction. The hook adapter
ignores prompt and assistant-message content and does not infer success from prose.

Derived summaries and repeated-failure candidates are reproducible from the
event stream. A candidate must be confirmed against its source session and
promoted into a sanitized eval before it can justify a harness change; raw
events never authorize automatic self-modification.

See [local harness observability and improvement loop](docs/harness-observability-loop.md).

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

### `harness-observe`

Record and analyze content-free local JSONL events for workflow observability,
recurring-failure discovery, and reviewed eval-driven harness improvement.

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
