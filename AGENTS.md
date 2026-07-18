# AGENTS.md - my-agent-skills

## Scope

This repository is the public subset of local Agent Skills.

## Skill layout contract

- `skills/<skill>` in this repository is the real public skill source.
- `~/.agents/skills/<skill>` must be a symlink/junction to `skills/<skill>` for public skills.
- Do not reverse this relationship. Never make `skills/<skill>` point to `~/.agents/skills/<skill>`.
- Do not copy private, generated, system, or cache skills into this repository.
- Only keep skills here when they are safe to publish.

## Private skills

- Skills containing local service URLs, access tokens, private host names, or customer data stay only under `~/.agents/skills`.
- `1panel` is private unless its secrets and local paths are removed first.
- `.system` skills are managed system content and must not be copied into this repository.

## Standalone public skills

- A skill that already has a dedicated public source repository remains owned by that repository.
- Record the upstream in this repository when useful, but do not vendor generated environments, caches, build output, or a second copy of its source here.
- Install such a skill from its upstream source so there is still only one source of truth.

## Validation

- Run `scripts/link-user-skills.sh` on macOS/Linux to link public repo skills into `~/.agents/skills`.
- Run `scripts/link-user-skills.ps1` on Windows to link public repo skills into the local installed skills directory.
- Use `--force` / `-Force` only when replacing an existing local installed copy is intentional.

## Harness observability

- Local harness observation uses the `harness-observe` native-session scanner and AI audit contract.
- Prefer scheduled analysis of native session JSONL over global prompt instructions or per-turn hooks. Do not infer semantic success from aggregate metrics alone.
- Treat native Codex session JSONL as the sole source of truth. Content-free metrics, AI findings, reports, and eval candidates are derived views.
- Keep derived metrics and reports content-free. Do not export prompts, responses, commands, paths, URLs, host names, tool arguments, tool results, secrets, or customer data.
- Raw observations may propose an eval candidate but never authorize automatic skill edits, commits, pushes, merges, deploys, or publishing.

## Remote hosts

- Keep machine-specific SSH aliases and addresses in private configuration, not in this public repository.
- Pass the intended host as a task parameter and verify it from live SSH configuration before use.
