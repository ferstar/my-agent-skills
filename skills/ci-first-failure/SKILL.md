---
name: ci-first-failure
description: Find the first real failing CI job or workflow step instead of guessing from symptoms. Use when the user mentions failing CI, GitHub Actions, GitLab pipeline, workflow logs, build failure, test failure, job failure, deploy failure, or asks why a PR/MR is red.
argument-hint: "[run url, pipeline url, branch, sha, or repo]"
---

# CI First Failure

Find the failing job before editing code.

## GitHub Actions

```bash
gh run list --limit 10
gh run view <run-id> --json status,conclusion,headSha,url,jobs
gh run view <run-id> --log-failed
```

Extract:

- run URL
- head SHA
- failing job name
- failing step
- first useful error block

## GitLab CI

Prefer `glab api` or bounded `glab ci` calls:

```bash
glab ci list --ref <branch> --per-page 10
glab ci view <pipeline-id>
glab api "projects/<project>/pipelines/<pipeline-id>/jobs" | jq '.[] | {id,name,status,web_url}'
glab api "projects/<project>/jobs/<job-id>/trace" | tail -n 120
```

## Output

Lead with:

1. failing job/step
2. exact SHA/ref
3. likely failing layer
4. next smallest fix or next log to inspect

Do not debug from local assumptions until the failing job is identified.
