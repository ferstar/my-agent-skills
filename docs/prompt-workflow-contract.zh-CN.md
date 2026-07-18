# Prompt 工作流契约

[English](prompt-workflow-contract.md) | [简体中文](prompt-workflow-contract.zh-CN.md)

普通任务优先使用短 prompt；只有在能够避免真实错误时才补充结构。一个任务契约包含五部分：

```text
objective: <需要实现的结果>
evidence: <会影响判断的线上对象、文件、日志或来源>
scope: <仓库、分支、对象、环境和允许修改的范围>
authority: <用户已经授权的动作>
terminal_state: <任务完成时必须满足的可观察状态>
```

不要求用户每次填写模板。已经明确的字段应直接推断；只在某个缺失选择会实质改变结果时说明假设或提问。

## 阶段

按任务需要选择最短适用路径：

```text
DISCOVER -> DECIDE -> IMPLEMENT -> VERIFY -> SHIP -> DONE
```

- `DISCOVER`：读取生效指令、仓库状态、线上对象和相关证据。
- `DECIDE`：识别真实 blocker，或确定有边界的实现方案。
- `IMPLEMENT`：只修改已授权范围。
- `VERIFY`：收集能够验证目标行为的证据。
- `SHIP`：执行已经单独授权的远端写操作。
- `DONE`：从最终本地和远端对象验证终态。

## 权限

下列权限相互独立：

```text
read-only | edit | push | merge | deploy | workflow-state | publish | cleanup
```

- `workflow-state`：Issue/Task 的 label、指派、评论、关闭、重开及类似流程状态变更。
- `publish`：release、外部消息、文档以及其他公开或第三方写操作。
- `cleanup`：删除本地或远端分支，以及破坏性环境清理。

权限不传递。edit 不代表 push，push 不代表 merge，merge 不代表 deploy、关闭 Issue、发布内容或 cleanup。如果线上状态或目标可能已变化，应在高影响动作执行前重新确认权限和目标。

## Checkpoint

长任务、恢复任务或接力任务应保留：

```text
phase: DISCOVER | DECIDE | IMPLEMENT | VERIFY | SHIP | DONE
objective: <当前目标>
scope: <仓库、分支、Issue/PR/MR、环境>
authority: <当前已授权动作>
evidence: <稳定事实、命令、URL、exact SHA 和结果>
changes: <已修改路径或外部对象>
verification: <已执行检查和最终对象回读>
terminal_state: <可观察的完成条件>
next: <唯一下一步或 blocker>
drift_facts: <继续前必须刷新的事实>
```

恢复时保留稳定证据，只刷新容易变化的事实：dirty state、branch head、PR/MR head SHA、discussion、CI、mergeability、权限、workflow 输入、部署健康状态和远端 SHA。handoff 应传递 checkpoint，不应重放整个会话。

## 渐进式 Prompt

可以用短 prompt 分阶段推进：

```text
Review 当前 MR，告诉我有哪些 blocker。
```

这只授权只读 review，不授权修改或远端写操作。

```text
修复已经确认的 blocker 并 push。不要 merge 或 deploy。
```

这只授权 edit 和 push。

```text
刷新并 merge exact head SHA。Issue 保持 open，切换到测试状态。
不要 deploy 或清理分支。
```

这只授权 merge 和指定的 workflow-state 变更。

```text
将 exact merge SHA 部署到指定环境。等待 workflow 完成，然后验证部署 SHA
和真实 health。不要 publish 或 cleanup。
```

这只授权指定 deploy。

## 验证与平台约束

- 优先使用 owning-module tests 和确定性检查，不依赖 Agent 自我评价。
- 所有远端写操作完成后都要回读最终对象。
- review、merge、artifact 和 deploy 证据都绑定 exact SHA。
- 高风险或主观任务可以使用独立 evaluator；普通改动不强制多 Agent review。
- 稳定规则应由保护分支、required checks、部署环境和最小权限凭据执行，而不是只依赖 prompt。
- 持久默认规则放在 `AGENTS.md`，可复用流程放在 skills，项目事实放在项目文档，当前执行状态放在 checkpoint。

## 主要参考资料

- [OpenAI Codex best practices](https://developers.openai.com/codex/learn/best-practices)
- [OpenAI prompting guidance](https://developers.openai.com/codex/prompting)
- [Anthropic skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Anthropic long-running agent harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [LangGraph interrupts and checkpointing](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [OWASP Excessive Agency](https://genai.owasp.org/llmrisk/llm06-sensitive-information-disclosure/)
- [GitHub protected branches](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub deployment environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
