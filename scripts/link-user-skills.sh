#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skills_dir="$repo_root/skills"
target_dir="${AGENTS_SKILLS_DIR:-$HOME/.agents/skills}"
force=0

if [[ "${1:-}" == "--force" ]]; then
  force=1
fi

mkdir -p "$target_dir"

for skill in "$skills_dir"/*; do
  [[ -f "$skill/SKILL.md" ]] || continue
  name="$(basename "$skill")"
  target="$target_dir/$name"

  if [[ -L "$target" ]]; then
    current="$(readlink "$target")"
    if [[ "$current" == "$skill" ]]; then
      printf 'ok %s -> %s\n' "$target" "$skill"
      continue
    fi
    rm "$target"
  elif [[ -e "$target" ]]; then
    if [[ "$force" -eq 0 ]]; then
      printf 'skip %s exists; use --force to replace\n' "$target" >&2
      continue
    fi
    rm -rf "$target"
  fi

  ln -s "$skill" "$target"
  printf 'link %s -> %s\n' "$target" "$skill"
done
