# my-agent-skills

[English](README.md) | [简体中文](README.zh-CN.md)

个人维护的公共 Agent Skills 仓库。

## 仓库结构

- `skills/<skill-name>/`：每个目录对应一个 skill
- 每个 skill 必须包含 `SKILL.md`
- 可选资源包括 `scripts/`、`references/`、`assets/`
- 仓库级冒烟和治理测试位于 `tests/`

## Prompt 工作流方法论

普通任务优先使用短 prompt；只有在能够避免真实错误时才补充结构：

```text
objective + evidence + scope + authority + terminal_state
```

- `objective`：最终要实现的结果
- `evidence`：会影响判断的代码、日志、文件或线上对象
- `scope`：允许读取和修改的仓库、分支、对象与环境
- `authority`：用户已经明确授权的动作
- `terminal_state`：什么可观察状态才算真正完成

任务按实际需要经过以下阶段，不要求机械走完所有阶段：

```text
DISCOVER -> DECIDE -> IMPLEMENT -> VERIFY -> SHIP -> DONE
```

权限不传递。`read-only`、`edit`、`push`、`merge`、`deploy`、
`workflow-state`、`publish` 和 `cleanup` 是相互独立的授权。例如，允许
push 不代表允许 merge；允许 merge 也不代表允许 deploy、关闭 Issue、
发布内容或清理分支。

长任务或接力任务使用紧凑 checkpoint：保留已经稳定验证的证据，只刷新
branch head、dirty state、CI、mergeability、权限、workflow 输入、部署健康
状态和远端 SHA 等容易变化的事实。只有本地与远端终态都经过回读验证，
任务才可以进入 `DONE`。

完整方法、渐进授权示例和行业参考见
[Prompt 工作流契约](docs/prompt-workflow-contract.zh-CN.md)。

## Harness 可观测闭环

`harness-observe` 以 Codex 原生本地 session JSONL 作为唯一事实来源，构建默认隐私
安全的持续改进闭环。确定性 scanner 派生不含正文的 lifecycle、耗时、token、tool
使用、模型和权限指标；AI 审计只对高信号 session 复核 outcome、终态、skill 使用和
失败分类。

定时 AI 复核取代 per-turn hooks 和全局 prompt 日志指令，用户不需要手工轮询 JSONL
或运行报表命令。

汇总报表和重复失败候选都可以从原生 session JSONL 重新生成。候选必须回到源 session 确认真正
根因，并提升为脱敏、可复现的 eval，之后才可以作为修改 harness 的依据；原始观测
不能自动授权自我修改。

完整方法见[本地 Harness 可观测与持续改进闭环](docs/harness-observability-loop.zh-CN.md)。

## 当前 Skills

### `exa-tools`

通过内置 Exa API wrapper 进行实时网络调研、技术文档或代码查询，以及带来源链接的公司背景研究。

设计目标：

- 聚焦需要当前外部信息的研究任务
- 优先使用轻量本地 wrapper，避免不必要的 MCP 依赖
- 在 `SKILL.md` 中明确不同查询命令的选择方式
- 保留结构化输出，便于后续自动化处理

### `rapidocr`

使用 RapidOCR 提取本地图片文字，输出结构化 JSON，标记低置信度或疑似金额内容，并可按启发式规则还原 Markdown 表格。

设计目标：

- OCR 只在本地处理文件
- 通过 `uv tool` 安装 Python 工具依赖
- 对价格、数量和低置信度内容提供复核提示
- 明确表格重建属于启发式结果

### `glab`

用于 GitLab Issue、Merge Request、CI/CD、API、discussion 回复及 work item 层级操作的 CLI skill。

设计目标：

- `SKILL.md` 只负责路由和关键约束
- 详细命令放入 `references/`
- 可重复的自动化优先使用 `glab api`

### `opencli`

使用浏览器登录态读取网页，以及调用豆包、微信、知乎、YouTube、Bilibili 等已支持的站点命令。

设计目标：

- 优先使用站点专用命令，再回退到通用 `opencli web read`
- 保持只读、浏览器会话驱动的职责边界
- 明确 URL 校验和 bridge 前置条件

### `agent-preflight`

在非简单 Codex 仓库任务开始前，完成最小仓库、指令、分支、工作区和线上对象预检。

### `harness-observe`

记录和分析不含正文的本地 JSONL 事件，用于 workflow 可观测、重复失败发现和经过
人工复核的 eval 驱动 harness 改进。

### `agent-boundary-hardening`

审计和修复仓库级 Agent prompt 或权限配置越界，不与一般应用安全审查混用。

### `define-goal`

仅在明确需要 goal-backed 工作时，创建或完善可衡量目标。

### `codex-ship-loop`

将已验证的代码改动推进到 commit、push、PR/MR、经授权的 merge 和 cleanup。

### `ci-first-failure`

在修改代码前，定位 GitHub Actions 或 GitLab CI 中第一个可执行的真实失败。

### `release-deploy-preflight`

在 release、deploy、桌面打包或 workflow dispatch 前核对目标、输入、exact SHA、权限和验证方式。

### `artifact-verify`

验证已有构建产物的下载完整性、归档结构、内容和来源，不触发 build、release 或 deploy。

### `remote-health`

诊断 SSH、Tailscale、PATH、远端服务、锁和远端 Codex 环境问题。

### `tianbot-docs`

根据当前 Tianbot 官方文档回答产品问题，避免硬编码容易过期的版本信息。

## 独立维护的公共 Skills

部分公共 skill 已拥有独立源码仓库，因此不在本仓库重复 vendor：

- [`fast-context`](https://github.com/ferstar/fast-context)：Python-first 混合仓库上下文搜索工具，拥有独立 `SKILL.md`、运行时代码、测试和 lockfile；应直接从其上游仓库安装和更新。

## 维护约定

- 每个 skill 聚焦一个职责
- trigger 条件和核心流程写在 `SKILL.md`
- 运行时检查与冒烟测试放在 `tests/`，不塞进 skill 正文
- 不提交 `node_modules`、缓存或临时输出
- 已有独立公共源码仓库的 skill 不在这里维护第二份源码
- 优先使用标准库和小型依赖集
- 新建或导入的 skill 必须经过 `skill-creator` 规范检查

## 本地安装

macOS/Linux：

```bash
scripts/link-user-skills.sh
```

Windows PowerShell：

```powershell
.\scripts\link-user-skills.ps1
```

脚本会把本仓库的 skill 链接到用户安装目录。只有在明确需要替换现有本地副本时才使用 `--force` 或 `-Force`。
