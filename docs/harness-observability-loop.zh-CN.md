# 本地 Harness 可观测与持续改进闭环

[English](harness-observability-loop.md)

## 架构

```text
Codex 原生 session JSONL（唯一事实来源）
                   |
                   v
          确定性无正文 scanner
                   |
                   v
          定时 AI 高信号复核
                   |
          +--------+--------+
          |                 |
          v                 v
      inbox 简报        脱敏 eval 候选
                            |
                            v
                 baseline -> 修改 -> 回归
```

Codex 原生 session JSONL 已包含任务生命周期、耗时、TTFT、token、tool call、模型、
approval policy 和 sandbox policy。直接使用它可以避免低保真重复事件流，也不会给每个
turn 增加 hook 延迟或递归风险。

## 确定性指标

```bash
PYTHONDONTWRITEBYTECODE=1 \
  python3 <skill-dir>/scripts/scan_codex_sessions.py --days 7
```

Scanner 只输出聚合指标和未完成 turn 的不透明引用，不导出 prompt、回复、reasoning、
命令、路径、URL、tool 参数或 tool 结果。

指标本身不能证明任务成功、实际使用的 skill 或真实终态。定时 AI 只对重复或其他高
信号异常最小化回看源 session，最后给出确认过的发现，或一条简洁健康状态。

## 自主复核

定时 Codex 任务应当：

1. 扫描稳定的近期窗口；
2. 发现源数据损坏时立即报告；
3. 比较完成率、P50/P95 耗时、TTFT、token 和 tool-use 形态；
4. 只对可行动异常最小化回看源 session；
5. 给出唯一处置：继续观察、提升为 eval、修改 skill、修改确定性工具或修复观测；
6. 未获得独立授权时不编辑、不交付。

这是受控进化。审计可以建议脱敏 eval，但不能自动授权自我修改、commit、push、
merge、deploy、publish 或 cleanup。

## 复盘节奏

- 每周：扫描近期 session，并投递一份低噪声 inbox 简报。
- 用户重复纠正后：确认源模式，再考虑提升为 eval。
- 修改 harness 前：记录可比较 baseline。
- 修改 harness 后：重跑 capability 与 regression trials。

## 行业依据

- [OpenAI Integrations and observability](https://developers.openai.com/api/docs/guides/agents/integrations-observability)
- [OpenAI Agent improvement loop](https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop)
- [Anthropic：Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [OpenTelemetry GenAI observability](https://opentelemetry.io/blog/2026/genai-observability/)
