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

## Validation

- Run `scripts/link-user-skills.sh` on macOS/Linux to link public repo skills into `~/.agents/skills`.
- Run `scripts/link-user-skills.ps1` on Windows to link public repo skills into the local installed skills directory.
- Use `--force` / `-Force` only when replacing an existing local installed copy is intentional.

## Windows remote

- The Windows host is reached with `ssh my-win`.
- Use `ssh my-win` for Windows-side checks instead of guessing hostnames or paths.
