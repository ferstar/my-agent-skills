# Prompt Workflow Contract

[English](prompt-workflow-contract.md) | [简体中文](prompt-workflow-contract.zh-CN.md)

Use short prompts for ordinary work and add structure only when it prevents a
real mistake. A task contract has five parts:

```text
objective: <result to achieve>
evidence: <live objects, files, logs, or sources that can change the decision>
scope: <repositories, branches, objects, environments, and allowed changes>
authority: <actions the user has authorized>
terminal_state: <observable conditions that mean the task is done>
```

The user does not need to fill in this template. Infer fields that are already
clear, state consequential assumptions, and ask only when a missing choice would
materially change the result.

## Phases

Use the smallest applicable path through:

```text
DISCOVER -> DECIDE -> IMPLEMENT -> VERIFY -> SHIP -> DONE
```

- `DISCOVER`: read instructions, repo state, live objects, and relevant evidence.
- `DECIDE`: identify the actual blocker or choose the bounded implementation.
- `IMPLEMENT`: change only the authorized scope.
- `VERIFY`: collect evidence that tests the requested behavior.
- `SHIP`: perform separately authorized remote mutations.
- `DONE`: verify the terminal state from the final local and remote objects.

## Authority

Treat these authorities as independent:

```text
read-only | edit | push | merge | deploy | workflow-state | publish | cleanup
```

- `workflow-state` covers issue/task labels, assignment, comments, close/reopen,
  and similar tracking mutations.
- `publish` covers releases, external messages, documents, and other public or
  third-party writes.
- `cleanup` covers local or remote branch deletion and destructive teardown.

Authority is not transitive. Editing does not imply push; push does not imply
merge; merge does not imply deploy, issue closure, publishing, or cleanup.
Reconfirm high-impact authority immediately before the mutation when live state
or the target may have drifted.

## Checkpoint

For long, resumed, or handed-off work, persist:

```text
phase: DISCOVER | DECIDE | IMPLEMENT | VERIFY | SHIP | DONE
objective: <current intended outcome>
scope: <repo, branch, issue/PR/MR, environment>
authority: <authorized actions only>
evidence: <stable facts, commands, URLs, exact SHAs, and results>
changes: <paths or external mutations>
verification: <checks run and final-object readbacks>
terminal_state: <observable completion conditions>
next: <single next action or blocker>
drift_facts: <facts that must be refreshed before continuing>
```

On resume, preserve stable evidence and refresh only drift-prone facts: dirty
state, branch heads, PR/MR head SHA, discussions, CI, mergeability, permissions,
workflow inputs, deployed health, and remote SHA. A handoff should carry this
checkpoint, not replay the transcript.

## Progressive prompts

Short, staged prompts are valid:

```text
Review the current MR and report blockers.
```

This grants read-only review, not edits or remote mutations.

```text
Fix the confirmed blockers and push the branch. Do not merge or deploy.
```

This grants edit and push only.

```text
Merge the refreshed exact head SHA. Keep the issue open in its testing state.
Do not deploy or clean up branches.
```

This grants merge and the specified workflow-state mutation only.

```text
Deploy the exact merge SHA to the requested environment. Wait for the workflow,
then verify the deployed SHA and live health. Do not publish or clean up.
```

This grants the specified deploy only.

## Verification and enforcement

- Prefer owning-module tests and deterministic checks over self-assessment.
- Read back every mutated remote object before reporting success.
- Bind review, merge, artifact, and deploy evidence to exact SHAs.
- Use a separate evaluator for high-risk or subjective work when its added cost
  improves confidence; do not require multi-agent review for routine changes.
- Enforce stable rules in branch protections, required checks, deployment
  environments, and least-privilege credentials instead of relying on prompts.
- Keep durable defaults in `AGENTS.md`, reusable workflows in skills, project
  facts in project documentation, and current execution state in checkpoints.

## Primary references

- [OpenAI Codex best practices](https://developers.openai.com/codex/learn/best-practices)
- [OpenAI prompting guidance](https://developers.openai.com/codex/prompting)
- [Anthropic skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Anthropic long-running agent harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [LangGraph interrupts and checkpointing](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [OWASP Excessive Agency](https://genai.owasp.org/llmrisk/llm06-sensitive-information-disclosure/)
- [GitHub protected branches](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub deployment environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
