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

- Local harness observation uses the `harness-observe` event contract.
- Prefer deterministic runtime hooks for lifecycle coverage over global prompt instructions. Keep outcome classification in an outcome-aware producer; do not infer success from assistant prose.
- Treat its append-only JSONL file as the sole source of truth; reports and eval candidates are derived views.
- Keep events content-free. Do not record prompts, responses, commands, paths, URLs, host names, tool arguments, tool results, secrets, or customer data.
- Raw events may propose an eval candidate but never authorize automatic skill edits, commits, pushes, merges, deploys, or publishing.

## Remote hosts

- Keep machine-specific SSH aliases and addresses in private configuration, not in this public repository.
- Pass the intended host as a task parameter and verify it from live SSH configuration before use.
