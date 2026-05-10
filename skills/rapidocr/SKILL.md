---
name: rapidocr
description: 使用 RapidOCR 对本地图片做 OCR。当用户要从 PNG/JPG/JPEG/WEBP/BMP/TIFF 图片中提取文字、返回结构化 JSON、标记低置信度或疑似金额数字，或把表格截图粗略还原成 Markdown 表格时使用；只处理本地文件，不下载远程 URL。
---

# RapidOCR

用本 skill 从本地图片中提取文字。运行入口是 Python 脚本，依赖通过 `uv tool` 安装和隔离。

## 适用场景

- 用户给出本地图片路径，要求 OCR / 识别文字 / 提取截图内容。
- 图片格式是 `png`、`jpg`、`jpeg`、`webp`、`bmp`、`tif`、`tiff`。
- 需要结构化 JSON，便于后续程序处理。
- 需要对低置信度文本、金额/数量/日期类数字做复核提示。
- 用户明确要“表格”“Markdown 表格”“CSV”时，可用 `--table` 做启发式表格还原。

## 不适用场景

- 远程图片 URL 下载后 OCR。
- PDF OCR。
- 需要法律/财务级准确性的金额或合同抽取，除非后续有人复核。
- 需要可靠表格结构还原；`--table` 只是基于 OCR 框的启发式重排。

## 依赖安装

Python 工具依赖统一使用 `uv tool`：

```bash
uv tool install --force rapidocr --with onnxruntime
```

不要改成 `python -m pip install ...`。

## 基本调用

```bash
python3 "$SKILL_DIR/scripts/run_rapidocr.py" "/absolute/path/to/image.png"
```

结构化输出：

```bash
python3 "$SKILL_DIR/scripts/run_rapidocr.py" "/absolute/path/to/image.png" --json
```

表格截图：

```bash
python3 "$SKILL_DIR/scripts/run_rapidocr.py" "/absolute/path/to/table.png" --json --table
```

脚本会先尝试当前 Python。如果当前 Python 没有 `rapidocr`，会自动 re-exec 到 uv tool 环境：

- macOS/Linux: `$(uv tool dir)/rapidocr/bin/python`
- Windows: `$(uv tool dir)/rapidocr/Scripts/python.exe`

## 输出说明

普通模式输出纯文本，一行一个识别文本块。

JSON 模式包含：

- `text`: 合并后的纯文本
- `lines`: 识别行数组
- `boxes`: OCR 框
- `scores`: 置信度
- `items`: 每行文本、框、置信度、中心点
- `review.low_confidence`: 低置信度行
- `review.amount_like`: 疑似金额/数量/日期等数字行
- `review.needs_review`: 是否建议人工复核
- `table.markdown`: 使用 `--table` 时的启发式 Markdown 表格

## 使用规则

1. 优先传绝对路径。
2. 如果用户要 JSON，保留脚本原始 JSON，不要把结构压扁。
3. 如果 `review.needs_review` 为 true，回复里要提醒用户复核低置信度或金额数字。
4. 如果使用 `--table`，明确说明这是启发式表格，还需要人工核对结构。
5. 对报价单、合同、发票、付款信息，默认提醒“金额和数量需要复核”。

## 验证

```bash
uv tool install --force rapidocr --with onnxruntime
python3 "$SKILL_DIR/scripts/run_rapidocr.py" "/absolute/path/to/image.png" --json
```

能输出可解析 JSON，且包含 `review` 字段，就算 wiring 正常。
