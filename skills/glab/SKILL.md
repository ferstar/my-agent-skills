---
name: glab
description: GitLab CLI workflows with `glab` for issues, merge requests, CI/CD, and GitLab API operations. Use when the user needs GitLab command-line automation, issue or MR triage, pipeline checks, API queries, discussion replies, release checks, or work item conversion and hierarchy updates, especially when `glab api` is more reliable than interactive GitLab flows.
---

# glab

Use `glab` for GitLab operations. Prefer `glab api` for automation and scripted updates.

## Routing

Read only the reference file needed for the task:

- Quick command lookup → `references/cli_quick_reference.md`
- Common issue/MR workflows → `references/workflows.md`
- REST and GraphQL command patterns → `references/rest_api_commands.md`
- Errors and recovery → `references/troubleshooting.md`

## Core rules

- Use `glab api` instead of interactive flows when repeatability matters.
- Use `-R owner/repo` when outside a git repository.
- URL-encode `<namespace>/<project>` as `<namespace>%2F<project>` in API paths.
- For long multiline Markdown fields, prefer `--raw-field description="$(cat file)"` and validate the rendered result afterward.
- Check command-specific flags with `glab <command> --help` before automating.
- For self-hosted GitLab, set `GITLAB_HOST` first.

## High-value patterns

### API-first issue update

```bash
glab api --method PUT projects/<namespace>%2F<project>/issues/123 \
  --raw-field description="$(cat /tmp/issue-description.md)"
```

### Threaded reply

```bash
DISC_ID=$(glab api "projects/<namespace>%2F<project>/issues/123/discussions" | jq -r '.[0].id')
glab api --method POST "projects/<namespace>%2F<project>/issues/123/discussions/$DISC_ID/notes" \
  --field body="Reply text"
```

### Work item conversion

Use GraphQL `workItemConvert` when REST cannot change the work item type. See `references/rest_api_commands.md` for full mutation examples.
