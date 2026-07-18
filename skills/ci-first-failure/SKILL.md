---
name: ci-first-failure
description: Isolate the first actionable failure in an already-red GitHub Actions or GitLab CI run. Use when a concrete PR, MR, workflow, job, or pipeline is failing; do not use for general repo preflight, local test selection, or healthy deploy verification.
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

Inspect the run's actual workflow revision when it may differ from the current default branch.

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

Do not edit from local assumptions until the failing job, step, exact SHA, and first useful error are identified. Later failures may be fallout; inspect them only if the first failure does not explain the run.
