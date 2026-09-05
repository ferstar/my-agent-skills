---
name: glab
description: GitLab CLI workflows with `glab` for issues, merge requests, CI/CD, and GitLab API operations. Use when the user needs GitLab command-line automation, issue or MR triage, pipeline checks, API queries, threaded discussion replies, release checks, or work item conversion and hierarchy updates. Prefer `glab api` for reliable scripted flows, while keeping direct CLI commands and local helper scripts available for common MR and pipeline tasks.
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
- After a merge that auto-closes an issue via `Closes #<iid>`, verify both issue state and labels. Apply label changes only when the requested workflow covers them; otherwise report the mismatch.
- Do not create a narrowly worded issue before the problem boundary is stable. If the work starts from a symptom and new evidence expands or changes the scope before merge, update the issue title/body and MR description to the actual shipped scope before marking it done or merging. A stale issue is worse than no issue because it misrecords the decision trail.
- Issue move only works for real issues. GitLab work items shown as `Task` can fail with `Moving 'Task' is not supported.` When the source URL is `/-/work_items/<iid>` or the API object is a task/work item, check move support first and be ready to recreate it manually in the target project while preserving the source link, state, and any important discussion.

## Command examples

Read [task-command-patterns.md](references/task-command-patterns.md) for concrete command examples, attachments, work-item conversions, and helper scripts. Examples are not authorization to execute every action in a block.
