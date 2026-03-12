---
name: glab
description: GitLab CLI workflows with `glab` for issues, merge requests, CI/CD, and GitLab API operations. Use when the user needs GitLab command-line automation, issue or MR triage, pipeline checks, API queries, threaded discussion replies, release checks, or work item conversion and hierarchy updates. Prefer `glab api` for reliable scripted flows, while keeping direct CLI commands and local helper scripts available for common MR and pipeline tasks.
homepage: https://github.com/ferstar/my-agent-skills/tree/main/skills/glab
metadata:
  openclaw:
    requires:
      bins: [glab, jq]
      envs:
        - name: GITLAB_TOKEN
          description: GitLab personal access token. Recommend minimal scopes such as read_api for read-only work, and api only when write operations are required.
          secret: true
          required: true
        - name: GITLAB_HOST
          description: GitLab instance hostname (for example gitlab.example.org). Defaults to gitlab.com when unset.
          required: false
        - name: TIMEOUT
          description: Timeout in seconds used by helper scripts and wait/watch workflows.
          required: false
        - name: INTERVAL
          description: Polling interval in seconds for helper scripts. Typical default is 5-10 seconds.
          required: false
    install:
      - id: brew
        kind: brew
        package: glab
        label: Install glab via Homebrew
      - id: apt
        kind: apt
        package: glab
        label: Install glab via apt
      - id: jq-brew
        kind: brew
        package: jq
        label: Install jq via Homebrew
      - id: jq-apt
        kind: apt
        package: jq
        label: Install jq via apt
---

# glab

Use `glab` for GitLab operations. Prefer `glab api` for automation and scripted updates, but use direct `glab` subcommands when they are faster and clearer for standard merge request, issue, or CI flows.

## Routing

Read only the reference file needed for the task:

- Quick command lookup → `references/cli_quick_reference.md`
- Common issue/MR workflows → `references/workflows.md`
- REST and GraphQL command patterns → `references/rest_api_commands.md`
- Advanced API usage and safety notes → `references/api-advanced.md`
- Detailed command coverage and flags → `references/commands-detailed.md`
- Errors and recovery → `references/troubleshooting.md`

## Security Notice

The `glab api` command can perform arbitrary GitLab API operations with the active token.

- Prefer minimally scoped tokens.
- Use `read_api` for read-only tasks when possible.
- Use `api` only when write operations are actually needed.
- Avoid highly privileged tokens unless the task explicitly requires them.
- For automation, consider project or bot tokens with limited scope.

## Prerequisites

Required binaries:
- `glab`
- `jq`

Required credential:
- `GITLAB_TOKEN`

Optional configuration:
- `GITLAB_HOST` for self-hosted GitLab
- `TIMEOUT` and `INTERVAL` for helper scripts

Quick verification:

```bash
glab --version
jq --version
glab auth status
```

## Core rules

- Use `glab api` instead of interactive flows when repeatability matters.
- Use `-R owner/repo` when outside a git repository.
- URL-encode `<namespace>/<project>` as `<namespace>%2F<project>` in API paths.
- For long multiline Markdown fields, prefer `--raw-field description="$(cat file)"` and validate the rendered result afterward.
- Check command-specific flags with `glab <command> --help` before automating.
- For self-hosted GitLab, set `GITLAB_HOST` first.
- Prefer `--output=json` or `glab api` + `jq` for scripting and validation.

## Quick reference

### Merge requests

```bash
glab mr create --title "Fix" --description "Closes #123"
glab mr list --reviewer=@me
glab mr checkout 123
glab mr approve 123
glab mr merge 123 --remove-source-branch
```

### Issues

```bash
glab issue create --title "Bug" --label bug
glab issue list --assignee=@me --all
glab issue view 123
glab issue close 123
```

### CI/CD

```bash
glab ci status
glab ci view
glab ci trace
glab ci retry <job-id|job-name>
glab ci lint
```

### Outside a repo

```bash
glab mr list -R owner/repo
glab issue list -R owner/repo
glab api -R owner/repo projects/owner%2Frepo
```

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

Use GraphQL `workItemConvert` when REST cannot change the work item type. See `references/rest_api_commands.md` for mutation examples.

## Core workflows

### Create and merge an MR

```bash
git push -u origin feature-branch
glab mr create --title "Add feature" --description "Implements X"
glab mr approve 123
glab mr merge 123 --remove-source-branch
```

### Review an MR

```bash
glab mr list --reviewer=@me
glab mr checkout 123
glab mr note 123 -m "Looks good overall; one suggestion below."
glab mr approve 123
```

### Monitor or wait for CI

```bash
glab ci view
glab ci trace
glab ci retry <job-id|job-name>
```

If local helper scripts are present, use:

```bash
./scripts/glab-mr-await.sh 123 --timeout 600
./scripts/glab-pipeline-watch.sh --timeout 300
```

## Helper scripts

If this skill includes local scripts, prefer them for repeatable watch/wait flows:

- `scripts/glab-mr-await.sh` — wait for MR approval and successful pipeline
- `scripts/glab-pipeline-watch.sh` — monitor pipelines with CI-friendly exit codes

Environment variables commonly used by scripts:
- `TIMEOUT`
- `INTERVAL`

## Self-hosted GitLab

```bash
export GITLAB_HOST=gitlab.example.org
glab auth status
glab mr list -R group/project
```

## Troubleshooting

Common examples:

- `command not found: glab` → install `glab`
- `command not found: jq` → install `jq`
- `401 Unauthorized` → verify `GITLAB_TOKEN` or `glab auth login`
- `404 Project Not Found` → verify project path and permissions
- `not a git repository` → use `-R owner/repo`
- `Unknown flag` → check `glab <command> --help`; flags differ across versions
- `HTTP 415` on `glab api --input` → retry with `--field` or `--raw-field`

For detailed recovery steps, read `references/troubleshooting.md`.

## Best practices

1. Verify authentication before making changes.
2. Prefer API-first automation for repeatability.
3. Use minimal token scopes.
4. Prefer structured output for scripts.
5. Validate rendered issue/MR descriptions after multiline updates.
6. Keep `-R owner/repo` explicit when outside a repository.
7. Use helper scripts for CI polling when available.
