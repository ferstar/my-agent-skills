---
name: opencli
description: 使用 OpenCLI 处理基于浏览器登录态的网页渠道与网页读取任务。只要用户是在网站内查资料、读取网页内容、导出网页正文、抓取登录后页面、读取前端渲染结果，或要使用 OpenCLI 已支持的网站/渠道命令（如 doubao、weixin、zhihu、youtube、bilibili），就优先使用这个 skill；先用站点/渠道专用命令，`web read` 仅作 fallback。不适用于桌面 App 控制、页面探索、录制/生成适配器、通用 UI 自动化或带副作用的写操作。
---

# OpenCLI Web Channels

这个 skill 负责两类能力：

1. 使用 OpenCLI 的站点/渠道专用网页命令
2. 在没有专用命令时，用 `opencli web read` 读取普通网页

如果任务目标是“看网页里有什么、提取网页内容、导出网页数据、借助网页登录态调用已支持的网站能力”，可以用它。
如果任务目标是“控制桌面应用、探索站点 API、录制交互、生成适配器、自动点击提交表单、发帖点赞评论关注”，不要用它。

还有一个优先级原则：
如果 OpenCLI 已经有现成的站点/渠道专用命令，优先用专用命令；`web read` 只作为兜底。

## 适用范围

优先用于这些场景：

- 目标页面必须复用本机 Chrome 的登录态
- 页面内容依赖前端渲染，普通 HTTP 抓取拿不到
- 需要把网页内容导出成 `md`、`json`、`yaml`、`csv` 或表格
- OpenCLI 已有站点命令，或者至少可以退回 `opencli web read`

执行时遵循这个顺序：

1. 先找站点/渠道专用命令
2. 如果没有合适命令，再用 `opencli web read`

例如：

- 用户说“用豆包查一下香港攻略”
  优先考虑 `opencli doubao ask "香港攻略"`
  而不是直接对豆包页面使用 `opencli web read`

- 用户说“把这篇公众号文章导出来”
  优先考虑 `opencli weixin download --url "..."`
  而不是直接使用 `opencli web read`

- 用户给了一个没有专用适配器的普通文章页
  这时再退回 `opencli web read --url "..."`

不要用于这些场景：

- 桌面 App / Electron App 控制
- `explore`、`record`、`generate` 这类站点探索与适配器生成工作流
- 带副作用的操作，例如发帖、点赞、评论、关注、发送消息
- 一般性的浏览器自动化测试或复杂多步 UI 操作

## 前置条件

运行前先确认：

1. Chrome 正在运行，且已登录目标网站
2. 已安装 `opencli Browser Bridge` 扩展
3. 本机已安装 `opencli`

如果这些条件不满足，先说明缺口，不要假装可以直接完成。

## 推荐工作流

1. 先判断是否有站点或渠道专用命令  
   例如 `doubao ask`、`bilibili hot`、`zhihu hot`、`youtube transcript`

2. 只有在没有合适专用命令时，才退回通用网页读取  
   使用 `opencli web read --url "<url>"`

3. 只请求当前任务所需的最小输出  
   例如限制条数、选择合适的 `--format`

4. 优先选择便于后续处理的格式  
   - 需要程序消费：`json`
   - 需要人读和总结：`md`
   - 需要粘贴到表格：`csv`

5. 在真正执行前，先做一次参数自检
   - 需要文本参数的命令，例如 `doubao ask`，传用户问题本身，不要伪造 `--url`
   - 需要 `--url` 的命令，只传真实网页 URL
   - 如果 URL 是 `data:`、`about:blank`、`javascript:`、空字符串、`<html>...</html>` 这类占位内容，视为无效参数，不要执行

6. 如果浏览器桥接异常，再用诊断命令  
   运行 `opencli doctor`

## 调用前 Checklist

每次真正执行 OpenCLI 前，先快速过这 4 项：

1. 这次该用站点/渠道专用命令，还是只能退回 `web read`
2. 当前命令要的是文本参数，还是 `--url`
3. 如果要 `--url`，这个值是不是用户明确给出的真实 `http(s)` 页面地址
4. 如果 URL 是 `data:`、`about:blank`、HTML 片段、空值或猜测值，立即停下，不要执行

## URL 硬规则

对所有带 `--url` 的 OpenCLI 命令，执行下面这条硬规则：

- 只有当 URL 明确以 `http://` 或 `https://` 开头时，才允许执行
- 只要不是 `http://` / `https://`，就直接判定为无效参数，不要调用命令

下面这些值一律禁止传给 `--url`：

- `data:text/html,<html></html>`
- 任意 `data:` URL
- `about:blank`
- 任意 `javascript:` URL
- 任意裸 HTML，例如 `<html>...</html>`
- 空字符串、`null`、`undefined`
- 模型自己猜出来的链接

如果 URL 不满足要求，按这个顺序处理：

1. 如果有站点/渠道专用命令，改用专用命令
2. 如果任务确实需要 URL，就明确说明“缺少可用的 http(s) 链接”，不要硬调
3. 不要为了把命令跑起来，临时拼 `data:`、空白页或占位 URL

## 参数安全检查

调用 OpenCLI 前，先判断当前命令到底需要“文本参数”还是“URL 参数”。

- 文本参数命令
  例如 `opencli doubao ask "香港攻略"`
  这里要传的是用户问题，不是网页地址

- URL 参数命令
  例如 `opencli weixin download --url "https://mp.weixin.qq.com/s/xxx"`
  这里要传的是真实文章链接

如果命令需要 URL，至少做这几个检查：

1. 必须是用户明确给出的真实 URL，或能从上下文可靠提取出的真实 URL
2. 优先是 `http://` 或 `https://` 链接
3. 不要把以下内容当 URL 传入：
   - `data:text/html,<html></html>`
   - `about:blank`
   - `javascript:...`
   - 单纯的 HTML 片段、DOM 片段、占位字符串
   - 站点首页以外的“猜测出来的详情页”

如果拿不到可靠 URL，就换用不需要 URL 的专用命令，或者直接说明缺少可用链接，不要硬拼参数。

可以直接按这个判断：

- 可以执行：`https://www.pudong.gov.cn/...`
- 可以执行：`http://example.com/...`
- 禁止执行：`data:text/html,<html></html>`
- 禁止执行：`about:blank`
- 禁止执行：`<html><body>...</body></html>`
- 禁止执行：`www.example.com`（缺少协议时先补充确认，不要直接调用）

## 常用命令

```bash
# 专用渠道 / 站点命令优先
opencli doubao ask "香港攻略"
opencli weixin download --url "https://mp.weixin.qq.com/s/xxx"

# 通用网页读取
opencli web read --url "https://example.com/article"

# 热榜 / 列表
opencli bilibili hot --limit 10
opencli zhihu hot --limit 10
opencli reddit hot --limit 10
opencli hackernews top --limit 10

# 搜索 / 页面读取
opencli xiaohongshu search "美食"
opencli youtube transcript "https://www.youtube.com/watch?v=xxx"
```

所有只读命令都可以配合输出格式：

```bash
opencli web read --url "https://example.com" -f md
opencli bilibili hot --limit 10 -f json
opencli reddit hot --limit 20 -f csv
```

## `web read` 何时使用

只有在下面这些情况下，才优先考虑 `web read`：

- OpenCLI 没有现成的站点/渠道专用命令
- 用户给的是普通文章页、公告页、详情页 URL
- 任务目标是读取页面正文，而不是调用某个站点的专用能力

如果用户说的是“用豆包查”“导出公众号文章”“读知乎问题”“拿 YouTube transcript”，先找专用命令，不要默认回落到 `web read`。

尤其不要因为缺少真实 URL，就临时拼一个 `data:` URL 或空白页 URL 去调用 `web read`。

如果拿到的不是 `http(s)` 链接，就说明现在还不满足 `web read` 的调用条件。

## `web read` 参数说明

`opencli web read` 不是普通的 HTTP 抓取器，它依赖本地 Chrome 页面上下文来读内容。
这在以下页面特别重要：

- 对 `curl` / 脚本请求有限制的站点
- 需要浏览器执行脚本后才出现正文的页面
- 需要复用浏览器 Cookie、会话或前端渲染结果的页面

例如下面这条命令：

```bash
opencli web read \
  --url "https://www.pudong.gov.cn/023004003/20251231/819733.html" \
  --output /tmp \
  --format yaml \
  --wait 30
```

建议按下面的方式理解：

- `--url`
  指定目标网页。优先传最终文章页、详情页、公告页，不要传列表页后再指望工具自己猜。

- `--output /tmp`
  指定导出目录。这里表示把抓到的结果文件写到 `/tmp`，适合临时分析或一次性提取。
  如果后续还要反复检查结果，换成明确目录更好，例如 `/tmp/pudong-web-read`。
  这里要特别注意：正文通常不会完整打印在终端里，而是落到这个目录下的文件里。

- `--format yaml`
  让终端输出变成结构化 YAML，便于后续再喂给脚本、日志系统或人工阅读。
  这个格式更适合看字段是否抓到了，例如 `title`、`author`、`publish_time`、`status`、`size`。

- `--wait 30`
  页面加载完成后额外等待 30 秒，再开始提取。
  这不是超时设置，而是给前端脚本、延迟注入内容、懒加载正文留时间。
  对政务站、媒体站、登录后页面、首屏先出框架再补正文的页面，示例里默认先给到 30 秒。

## `web read` 结果解读

`yaml` / `table` 输出里，至少要看这几个字段：

- `title`
  页面标题。是最基础的成功信号之一。

- `status`
  如果是 `ok`、`success` 或能看出正文已抓取，说明读取基本成功。
  如果像 `failed — no content` 这样，说明页面打开了，但正文没有被成功提取。

- `publish_time`、`author`
  有值更好，但不是所有网页都有。

- `size`
  通常能侧面反映抓到了多少正文内容；过小往往意味着只抓到壳子。

## `web read` 输出位置

模型不要把终端里的 `yaml` / `table` 当成完整正文。

- 终端输出通常只是摘要
  主要用于告诉你标题、状态、作者、时间、大小这些元信息

- 正文通常写入 `--output` 指定目录
  常见形式是“一个以页面标题命名的目录 + 里面的 Markdown 文件”

- 例如：
  `opencli web read --url "https://example.com" --output /tmp/opencli-web-read-check --format yaml`
  成功后，正文落在
  `/tmp/opencli-web-read-check/Example_Domain/Example_Domain.md`

- Windows 下同理
  例如 `--output "C:\\Temp\\opencli-web-read-check"`，
  则正文通常落在
  `C:\Temp\opencli-web-read-check\Example_Domain\Example_Domain.md`

- 如果用户要求“读取正文内容”或“总结文章内容”
  先去 `--output` 目录里找生成的 `.md` 文件，再基于文件内容处理

- 如果终端里显示 `success`，但你没有去磁盘里读生成文件
  那你看到的通常还只是摘要，不是完整文章内容

- 在 macOS 上，系统内部可能把 `/tmp` 解析成 `/private/tmp`
  但对使用者来说，优先按命令里传入的 `--output` 路径理解和查找，不要擅自改写成别的路径

- 在 Windows 上，优先直接使用用户传入的 Windows 路径
  例如 `C:\Temp\...`、`D:\work\...`
  不要擅自改写成 WSL 路径、MSYS 路径或类 Unix 路径

## `web read` 调参建议

遇到“页面能打开，但结果是 `no content`”时，优先这样处理：

1. 先把 `--wait` 从默认 `3` 提到 `30`
2. 改用独立输出目录，方便检查落盘文件
3. 加 `-v` 看调试输出
4. 确认目标页面已经在 Chrome 中可正常打开，而不是被验证页、重定向页、错误页替代

如果普通 `curl` / 脚本请求被站点拦截，而 `web read` 仍然拿不到正文，通常不是“网络不通”，而是以下几类问题：

- Browser Bridge 没连上
- Chrome 里实际打开的是拦截页或空白页
- 页面正文注入更慢，等待时间不够
- 页面结构特殊，当前提取策略没命中正文区域

## 输出约定

默认优先给出最适合当前任务的原始结果，再基于结果做摘要或整理。

- 用户要原始数据：输出 `json` 或 `csv`
- 用户要阅读总结：输出 `md`
- 用户没指定格式：优先 `md` 或 `json`，按任务判断

## 失败处理

如果命令失败，按这个顺序排查：

1. Chrome 是否已打开
2. 目标站点是否已登录
3. Browser Bridge 扩展是否可用
4. 检查调用参数是否类型正确
5. 如果传了 `--url`，确认它是明确的 `http(s)` 网页 URL，而不是 `data:`、`about:blank`、空 HTML、无协议字符串或占位值
6. 执行 `opencli doctor`
7. 如果站点专用命令不可用，再尝试 `opencli web read`

## 边界说明

这个 skill 故意收窄为“网页读取”能力。使用时不要扩展到以下命令或思路：

- 桌面端命令：`cursor`、`chatgpt`、`doubao-app`
- 探索类命令：`explore`、`record`、`generate`
- 写操作命令：发帖、点赞、评论、关注、发送消息、订阅、投票

这里的“网页读取”包含两类优先级明确的能力：

1. 已有站点/渠道专用命令的网页能力，例如 `doubao`、`weixin`、`zhihu`、`youtube`
2. 无专用命令时，再使用 `web read` 兜底

不要把它扩展成桌面 App 控制。更完整的只读命令列表见 [commands.md](./references/commands.md)。
