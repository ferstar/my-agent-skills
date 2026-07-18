---
name: gitlab-mr-context
description: Compatibility alias for the GitLab MR context workflow now maintained in the glab skill. Invoke only when this legacy skill name is requested; otherwise use glab directly.
disable-model-invocation: true
argument-hint: "[project] [iid]"
---

# GitLab MR Context Compatibility Alias

Use `../glab/SKILL.md` and read `../glab/references/workflows.md` for issue, MR, discussion, pipeline, merge-readiness, and post-merge state handling. This alias keeps existing installations and prompts from breaking while preventing a second copy of the workflow from drifting.
