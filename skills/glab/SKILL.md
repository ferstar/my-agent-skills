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
          required: false
        - name: GITLAB_ACCESS_TOKEN
          description: Alternative token variable recognized by `glab auth login` and runtime auth precedence.
          secret: true
          required: false
        - name: OAUTH_TOKEN
          description: OAuth token variable recognized by `glab auth login` and runtime auth precedence.
          secret: true
          required: false
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

Authentication:
- an authenticated `glab` session from `glab auth login`, or
- one of `GITLAB_TOKEN`, `GITLAB_ACCESS_TOKEN`, `OAUTH_TOKEN`

Optional configuration:
- `GITLAB_HOST` for self-hosted GitLab
- `TIMEOUT` and `INTERVAL` for helper scripts

Do not start normal tasks with standalone `glab --version`, `jq --version`, or `glab auth status` checks. Let the first task-specific command prove tool availability and authentication. Run diagnostic checks only after a command fails, when a host/auth mismatch is likely, or when the user explicitly asks for environment verification.

## Core rules

- Use `glab api` instead of interactive flows when repeatability matters.
- Use `-R owner/repo` when outside a git repository.
- URL-encode `<namespace>/<project>` as `<namespace>%2F<project>` in API paths.
- GitLab UI 的 `/-/work_items/<iid>` 在 REST 评论、notes、discussions 场景下通常仍走 `issues/<iid>` 接口；不要假设存在 `work_items/<iid>/notes` 这类 REST 路径。
- For long multiline Markdown fields, prefer `--raw-field description="$(cat file)"` and validate the rendered result afterward.
- Use the known command patterns in this skill first. Do not run `glab <command> --help` while executing documented workflows. If a command fails with an unsupported/unknown flag, inspect that exact subcommand help once, correct the invocation, and only then retry.
- Treat `glab auth status` as human-readable diagnostic output. Do not build automation around exact wording; use command exit status, configured auth, or explicit env vars as the machine-facing signal.
- For self-hosted GitLab, set `GITLAB_HOST` first.
- Prefer `--output=json` or `glab api` + `jq` for scripting and validation.
- `glab issue list` defaults to open issues. Use `--closed` or `--all` when needed. `--opened` is accepted but deprecated and can prefix a warning into stdout even with `--output json`; do not introduce new usage. `--state` is unsupported.
- Use `glab issue update --unlabel` instead of `--remove-label`.
- Do not assume `glab issue delete` has a `--yes` flag. For scripted deletion, pipe confirmation on stdin or use `glab api` if you need a fully non-interactive path.
- For MR creation, use `--source-branch` / `--target-branch`. Do not use `--source` / `--target`; the local CLI rejects those flags. For file-authored MR bodies, pass `--description "$(cat file)"`; do not use `--description-file` unless that exact subcommand help shows it.
- `glab mr note` may include experimental `list`, `resolve`, and `reopen` subcommands. Prefer those for MR discussion state changes when available, and fall back to `glab api` when you need a stable non-experimental path.
- Do not use `glab mr checks`; inspect MR mergeability with `glab mr view` or `glab api`, and inspect pipelines with `glab ci list` / `glab ci view`.
- For pipelines, prefer `glab ci list --ref <branch>` when filtering by branch or source ref. Use `--per-page <n>` / `--page <n>` to bound list results. Do not invent `--branch` or `--limit` for `glab ci list`; if the command rejects the flag, use `glab api` for pipeline lookup instead of trying nearby flags.
- When creating an MR that must auto-close an issue, keep `Closes #<iid>` in the MR description body. Do not rely on `--related-issue` alone for auto-close semantics.
- Do not mix `glab mr create --related-issue` with an already-authored MR body that contains `Closes #<iid>` unless you explicitly want `glab` to mutate the result. In the current CLI/server combination, `--related-issue` can still add coupling side effects such as a duplicated `Closes #<iid>` line and an unexpected Draft MR. If title/description are already finalized, prefer plain `glab mr create`, then verify with `glab mr view` and patch via `glab mr update` or `glab api` if needed.
- Treat `warning: failed to fetch target branch rules: 404 Not Found` during `glab mr create` as non-fatal when the command still returns an MR URL. Verify the created MR afterward instead of retrying with guessed flags.
- Treat the terminal line `No pipeline running` during `glab mr merge` as informational, not an automatic merge failure. The real gate is MR mergeability from `glab api` / `glab mr view`, plus the final merged state.
- After a merge that auto-closes an issue via `Closes #<iid>`, verify both issue state and labels. GitLab can close the issue but leave workflow labels like `doing` behind; update them explicitly to the true terminal state such as `done`.
- Do not create a narrowly worded issue before the problem boundary is stable. If the work starts from a symptom and new evidence expands or changes the scope before merge, update the issue title/body and MR description to the actual shipped scope before marking it done or merging. A stale issue is worse than no issue because it misrecords the decision trail.
- Issue move only works for real issues. GitLab work items shown as `Task` can fail with `Moving 'Task' is not supported.` When the source URL is `/-/work_items/<iid>` or the API object is a task/work item, check move support first and be ready to recreate it manually in the target project while preserving the source link, state, and any important discussion.

## Quick reference

### Merge requests

```bash
glab mr create --title "Fix" --description "Closes #123"
glab mr list --reviewer=@me
glab mr checkout 123
glab mr approve 123
glab mr note resolve 3107030349
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
glab ci list --ref main
glab ci trace
glab ci retry <job-id|job-name>
glab ci lint
```

### Outside a repo

```bash
glab mr list -R owner/repo
glab issue list -R owner/repo
glab api projects/owner%2Frepo
```

## High-value patterns

### API-first issue update

```bash
glab api --method PUT projects/<namespace>%2F<project>/issues/123 \
  --raw-field description="$(cat /tmp/issue-description.md)"
```

### MR status and pipelines

```bash
# Inspect MR summary in terminal
glab mr view 123

# Inspect mergeability and pipeline fields via API
glab api "projects/<namespace>%2F<project>/merge_requests/123" \
  | jq '{state, merge_status, detailed_merge_status, pipeline, head_pipeline}'

# List pipelines for a ref when you need current CI state
glab ci list --ref my-branch
```

### Threaded reply

```bash
DISC_ID=$(glab api "projects/<namespace>%2F<project>/issues/123/discussions" | jq -r '.[0].id')
glab api --method POST "projects/<namespace>%2F<project>/issues/123/discussions/$DISC_ID/notes" \
  --field body="Reply text"
```

If the user gives a work item URL such as `/-/work_items/163#note_3612`, map it like this before replying:

```bash
# 1. Resolve the work item through the issues API.
glab api "projects/<namespace>%2F<project>/issues/163"

# 2. Find the discussion that contains note 3612.
DISC_ID=$(glab api "projects/<namespace>%2F<project>/issues/163/discussions" \
  | jq -r '.[] | select(any(.notes[]; .id == 3612)) | .id')

# 3. Reply in that discussion thread.
glab api --method POST "projects/<namespace>%2F<project>/issues/163/discussions/$DISC_ID/notes" \
  --field body="Reply text"
```

### Download attachments from issue / note threads

When an issue note or discussion note contains `/uploads/...` links and the files must enter the repository, do not rely on the UI URL with plain `curl`. On self-hosted GitLab that often returns an HTML login page instead of the binary file.

Preferred flow:

```bash
# 1. Read the note body and extract the upload paths you need.
glab api "projects/<project-id>/issues/<iid>/notes/<note_id>"

# 2. Download the binary through the uploads API, not the UI path.
glab api "projects/<project-id>/uploads/<secret>/<filename>" > "docs/<Tender>/attachment/<flattened-name>"

# 3. Verify the file type before wiring references.
file "docs/<Tender>/attachment/<flattened-name>"
```

Rules:

- Land repo-bound evidence in the target tender's `attachment/` directory before updating正文 or appendix references.
- Flatten the filename to the repo's attachment naming scheme; do not keep issue-thread URLs in draft text.
- After download, verify the artifact is really a PDF/image/document and not HTML.
- If the attachment came from a note URL like `.../issues/40#note_6105`, use the note API first to recover the exact `/uploads/<secret>/<filename>` path.

### Work item conversion

Use GraphQL `workItemConvert` when REST cannot change the work item type. See `references/rest_api_commands.md` for mutation examples.

### Moving issues between projects

Before moving, confirm the source is a movable issue:

```bash
glab api "projects/<namespace>%2F<project>/issues/<iid>" | jq '{iid, issue_type, type, web_url}'
```

If GitLab rejects the move with `Moving 'Task' is not supported.`, treat it as a manual migration:

```bash
# 1. Read the source issue / work item and notes.
glab api "projects/<src>/issues/<iid>"
glab api "projects/<src>/issues/<iid>/notes?per_page=100"

# 2. Recreate it in the target project as a normal issue.
glab issue create -R <target-owner>/<target-repo> \
  --title "..." \
  --description "$(cat /tmp/body.md)"

# 3. Reapply state explicitly if the source was closed.
glab issue close <new-iid> -R <target-owner>/<target-repo>
```

Rules:

- Do not assume child tasks under a moved parent can also be moved.
- Preserve the original work item URL in the recreated issue body.
- Summarize important discussion when recreating manually.
- Re-check the target project after migration; parent moves can auto-create or auto-link child items.

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
glab mr note create 123 -m "Looks good overall; one suggestion below."
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
glab mr list -R group/project
```

## Troubleshooting

Common examples:

- `command not found: glab` → install `glab`
- `command not found: jq` → install `jq`
- `401 Unauthorized` → verify `GITLAB_TOKEN` or `glab auth login`
- `404 Project Not Found` → verify project path and permissions
- `not a git repository` → use `-R owner/repo`
- `Unknown flag` → use the documented pattern first; inspect exact subcommand help once only if the error remains
- `HTTP 415` on `glab api --input` → retry with `--field` or `--raw-field`

For detailed recovery steps, read `references/troubleshooting.md`.

## Best practices

1. Let the first task-specific command verify auth; run separate auth checks only after auth/host errors or explicit user request.
2. Prefer API-first automation for repeatability.
3. Use minimal token scopes.
4. Prefer structured output for scripts.
5. Validate rendered issue/MR descriptions after multiline updates.
6. Keep `-R owner/repo` explicit when outside a repository.
7. Use helper scripts for CI polling when available.
