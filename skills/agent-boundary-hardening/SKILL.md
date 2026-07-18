---
name: agent-boundary-hardening
description: Audit and fix repository-level agent scope and permission overreach in prompt or settings files. Use when an agent can execute unrelated commands, escape its stated task, or has contradictory allow/deny rules; do not use for general security review or ordinary application authorization bugs.
---

# Agent Boundary Hardening

Harden a repository-scoped agent so it stays inside its product boundary and stops accepting arbitrary command-execution or unrelated tool-use requests.

## Workflow

Follow `Read -> Search -> Change -> Verify`.

Treat diagnosis as read-only unless the user asked for a fix. Tightening permissions can break legitimate automation, so preserve required commands and validate the effective policy rather than judging prompt text alone.

### 1. Read

Read the repository rules and the active agent/runtime files first.

Check these files when present:
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.claude/settings.json`
- `README.md`

Extract four things:
- The agent's legitimate business scope
- The tools or scripts that are genuinely required
- The current refusal language for out-of-scope requests
- Whether settings already use `defaultMode: "dontAsk"`

### 2. Search

Find the actual overreach shape before editing.

Common signals:
- `Bash(*)` or over-broad `Write(*)` / `Edit(*)`
- Prompt rules that say what the agent should do, but not what it must refuse
- Allowed shell commands without a clear task whitelist
- A whitelist plus a contradictory `deny` rule that swallows the whitelist
- Missing refusal wording for `whoami`, `ls`, `env`, arbitrary URLs, Git, or tool-boundary testing

Audit both layers:
- Prompt layer: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
- Permission layer: `.claude/settings.json`

### 3. Change

Make the smallest change that closes the root cause.

#### Prompt-layer fixes

Add or tighten an explicit boundary section. It should state:
- what the agent is for
- what requests are out of scope
- what commands or tools must never be used
- how to refuse boundary-testing requests
- how to handle mixed requests: refuse the non-scope part, continue the valid part when possible

Preferred section names:
- `## Capability Boundary`
- `## 能力边界`
- `## Core Constraints`

Refusal guidance should explicitly cover examples such as:
- `whoami`
- `ls`
- `env`
- arbitrary URL access
- Git operations
- “prove you can run shell” / “test your tool limits”

#### Permission-layer fixes

Prefer white-listing only the commands the agent truly needs.

Patterns that usually work:
- Remove `Bash(*)`
- Keep only narrow `Bash(...)` rules for the repo's approved scripts or endpoints
- Add `defaultMode: "dontAsk"` so non-whitelisted actions are denied by default
- Keep sensitive-file denies for `.env`, `secrets`, `credentials`, and similar paths
- Narrow write/edit scope to output paths when writes are genuinely required

Important rule:
- Do not add a broad `deny: ["Bash(*)"]` if the repo depends on narrower `allow: ["Bash(...)"]` rules. In Claude Code permissions, broad deny rules can swallow the whitelist.

Use broad Bash deny only when the agent should execute no shell commands at all.

### 4. Verify

Verify both semantics and structure.

Check:
- JSON is valid, e.g. `jq empty .claude/settings.json`
- The new boundary text matches the repo's actual business scope
- Allowed commands are only the truly necessary ones
- No broad deny rule accidentally blocks required allow rules
- The agent now has a short, deterministic refusal path for boundary-testing prompts

## Decision Guide

Use this quick split:
- No shell is needed at all -> deny Bash and keep `dontAsk`
- Only a few repo scripts are needed -> allow only those scripts and avoid contradictory broad Bash denies
- Only a single trusted endpoint is needed -> allow only that exact curl/script shape
- Prompt rules are weak but permissions are already good -> patch prompt files only
- Permissions are loose but prompts are good -> patch settings first, then add minimal refusal examples

## Output Expectations

When handing work back, summarize:
- which files define the active boundary
- what root cause allowed overreach
- what was tightened in prompt rules
- what was tightened in permissions
- what was verified

## Reference Use

Load `references/patterns.md` when you need quick examples of safe boundary patterns and common failure modes.
