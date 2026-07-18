# 本地 Harness 可观测与持续改进闭环

[English](harness-observability-loop.md)

## 目标

个人 harness 的可观测体系需要回答四个问题：

1. 任务是否真正达到可观察终态？
2. 哪个工作流或权限边界起效了，哪个环节失败了？
3. 哪类失败重复到值得成为 eval？
4. 修改 harness 后，结果是否改善，同时没有引入不可接受的安全、耗时或 token 成本回退？

本仓库采用本地 append-only JSONL 作为唯一权威事实来源。报表、dashboard、
失败聚类和 eval 候选都是可以随时重新生成的派生视图。

## 架构

```text
Agent runtime / workflow checkpoint
                  |
                  v
          确定性 lifecycle hooks
                  |
                  v
        不含正文的 JSONL 事件流
             （唯一事实来源）
                  |
          +-------+-------+
          |               |
          v               v
       确定性汇总       重复失败候选
          |               |
          +-------+-------+
                  v
          人工复核后的 eval fixture
                  |
                  v
          baseline -> 修改 -> 回归门禁
```

JSONL 层记录 lifecycle 事实，以及 phase、authority、实际使用的 skill、可验证 outcome、标准化失败类型、
耗时和 token 数量等 harness 语义，但不复制完整 runtime trace。

## 为什么从 JSONL 开始

- Append-only 能保留历史，修正只能通过新增事件明确表达。
- 一行一个事件，便于检查、流式写入、校验、备份和处理。
- 不依赖服务，离线也能工作。
- 将来可以从权威事件流重新生成 OpenTelemetry 或其他后端数据。
- 只有一个事实来源，不会出现本地数据库、dashboard 与 eval backlog 互相矛盾。

OpenTelemetry 的 GenAI 约定适合作为未来交换格式，但目前仍在演进，而且 prompt
和 response 正文因为可能包含敏感信息而必须显式 opt-in。因此，本地契约优先记录
稳定且不含正文的 workflow outcome，而不是照搬某个厂商的全部字段。

## 观测什么

观测关键决策与结果，不观测每一次普通操作。

| 信号 | 示例 | 要回答的问题 |
| --- | --- | --- |
| Outcome | success、partial、failed、blocked | Harness 是否可靠地产生价值？ |
| Terminal state | 已验证或未验证 | Agent 是否过早宣布完成？ |
| Phase | DISCOVER 到 DONE | 工作主要卡在哪里？ |
| Skill use | 低基数 skill 名称 | 哪些路由有效，哪些发生叠栈？ |
| Authority | 独立授权动作 | 高风险动作是否被正确限制？ |
| Guard decision | allow 或 deny | 权限边界是在保护还是制造摩擦？ |
| Failure class | 标准化 `error_code` | 下一条 eval 应覆盖什么？ |
| Cost shape | 耗时、token 计数、重试 | 质量提升是否过于昂贵？ |
| Feedback | accepted、reworked、rejected | 用户是否接受最终结果？ |

不要记录 prompt、模型回复、reasoning、命令、路径、URL、host、branch、tool 参数、
tool 结果、密钥或客户数据。事件只保留 `event_id`；需要详细诊断时，由人回到原始
session 查证。

## 最小运行闭环

### 1. 安装确定性 Lifecycle Hooks

Codex 使用 `UserPromptSubmit` 和 `Stop` hooks：

```bash
python3 <skill-dir>/scripts/install_codex_hooks.py install
python3 <skill-dir>/scripts/install_codex_hooks.py check
```

安装或修改后，通过 Codex `/hooks` UI 对准确 hook 定义进行一次 review 和 trust。
Codex 会把 prompt 与最新 assistant message 传给对应事件，但 adapter 会刻意忽略两者，
只将 session/turn ID hash 成不透明 run ID，并记录 `turn_started`、`turn_stopped`、
runtime 标签和推导出的耗时。

Hook 比要求模型记住默认日志指令更稳定，但它仍无法判断任务是否成功、哪些 skill 在
语义上生效，或者真实终态是否得到验证。Adapter 不会从最终回复文本猜测这些事实。

### 2. 记录语义 Outcome

由 outcome-aware eval runner、workflow 或明确复核为非简单任务记录 `run_started`
和唯一一条 `run_finished`。只有当 phase 迁移、
权限判断或验证结果会影响未来改进时，才增加 `phase_changed`、`guard_decision`
或 `verification`。

```bash
python3 <skill-dir>/scripts/harness_observe.py record \
  --run-id task-20260718-01 \
  --event-type run_finished \
  --phase DONE \
  --status ok \
  --outcome success \
  --terminal-state-met true \
  --task-kind repo-change \
  --skill agent-preflight \
  --duration-ms 42000
```

默认日志路径依次读取 `HARNESS_OBSERVABILITY_LOG`、
`$CODEX_HOME/harness-observe/events.jsonl`，最后回退到
`~/.codex/harness-observe/events.jsonl`。这样 hook 配置与观测状态统一收敛在 Codex
控制面目录下。需要替换时，在子命令前传入 `--log`。

### 3. 校验与汇总

```bash
python3 <skill-dir>/scripts/harness_observe.py validate
python3 <skill-dir>/scripts/harness_observe.py summary --format markdown
```

报表只能从通过校验的事件流生成。报表本身可以删除，不是新的事实来源。

### 4. 生成候选

```bash
python3 <skill-dir>/scripts/harness_observe.py candidates --minimum-count 2
```

候选按标准化失败模式聚类，只包含 event ID，不反向拼接 prompt。候选也不等于 eval：
必须回看对应 session，确认真实根因，去除私有信息，并定义可观察的预期结果。

### 5. 提升为 Eval 并比较

维护两类 suite：

- capability eval 衡量当前能力上限，初始通过率可以较低；
- regression eval 保护已经具备、应接近全通过的行为。

每次修改 harness：

1. 通过多次 trial 建立 baseline；
2. 优先使用确定性的 outcome 和 tool-use grader；
3. 只有主观行为才使用独立、经过人工校准的模型 grader；
4. 同时比较成功率、安全性、耗时、重试和 token 计数；
5. 只有证据支持时才保留修改；
6. 将确认过的案例提升到 regression suite。

这属于受控进化，不是失控的自我修改。原始事件流不能自动授权修改 skill、commit、
push 或 deploy。

## 复盘节奏

- 每次失败：归一化一个有用的 `error_code`。
- 每周：检查 outcome、未验证终态、guard deny 和重复失败候选。
- 每月或切换模型前：运行稳定回归集和部分 capability case。
- 用户重复纠正同一问题后：记录 feedback、复现问题，再判断应该修改 skill、
  `AGENTS.md`、确定性脚本，还是不应进入 harness。

## 行业依据

- OpenAI 建议先用 trace 调试真实 workflow，再把高信号案例沉淀为系统 eval：
  [Integrations and observability](https://developers.openai.com/api/docs/guides/agents/integrations-observability)。
- OpenAI 的 improvement loop 将 trace、人工/模型反馈、可重复 eval、harness 修改排序
  和 Codex handoff 串成闭环：
  [Build an Agent Improvement Loop](https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop)。
- Anthropic 将 task、重复 trial、grader、trace 和环境 outcome 分开，并区分 capability
  与 regression suite：
  [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)。
- OpenTelemetry 提供厂商中立的 GenAI trace/metrics，并默认不采集 prompt 正文：
  [Inside the LLM Call](https://opentelemetry.io/blog/2026/genai-observability/)。
- Codex lifecycle hooks 提供确定性的 turn-scoped `UserPromptSubmit` 与 `Stop` 事件，
  并携带稳定的 session/turn 标识：
  [Codex Hooks](https://developers.openai.com/codex/hooks)。
