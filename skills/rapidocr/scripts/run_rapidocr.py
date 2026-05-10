import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import warnings

IMAGE_EXT_RE = re.compile(r"\.(png|jpg|jpeg|webp|bmp|tif|tiff)$", re.I)
POSIX_PATH_RE = re.compile(r"/(?:[^\s\"'<>|?*]+/)*[^\s\"'<>|?*]+\.(?:png|jpg|jpeg|webp|bmp|tif|tiff)", re.I)
WINDOWS_PATH_RE = re.compile(r"[A-Za-z]:\\[^\r\n\"'<>|?*]+?\.(?:png|jpg|jpeg|webp|bmp|tif|tiff)", re.I)
AMOUNT_RE = re.compile(r"(?<![A-Za-z0-9])(?:¥|￥)?\d{1,3}(?:[,.]\d{3})*(?:[,.]\d{2})?(?![A-Za-z0-9])|(?:¥|￥)?\d+(?:[,.]\d{2})")
LOW_CONF_THRESHOLD = 0.90


def clean_token(value):
    return str(value or "").strip().strip("'\"")


def try_existing_path(value):
    candidate = clean_token(value)
    if not candidate or not IMAGE_EXT_RE.search(candidate):
        return None
    return candidate if os.path.exists(candidate) else None


def iter_candidate_paths(text):
    text = str(text or "")
    yield from WINDOWS_PATH_RE.findall(text)
    yield from POSIX_PATH_RE.findall(text)
    for token in text.split():
        yield clean_token(token)


def extract_image_path_from_text(text):
    if not text:
        return None

    if not isinstance(text, str):
        try:
            text = json.dumps(text, ensure_ascii=False)
        except Exception:
            text = str(text)

    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            keys = ("img_path", "image_path", "path", "file", "file_path", "image")
            for key in keys:
                found = try_existing_path(obj.get(key))
                if found:
                    return found
            args = obj.get("args")
            if isinstance(args, dict):
                for key in keys:
                    found = try_existing_path(args.get(key))
                    if found:
                        return found
    except Exception:
        pass

    explicit_patterns = (
        re.compile(r"img_path\s*[=:]\s*([^\r\n]+)", re.I),
        re.compile(r"image_path\s*[=:]\s*([^\r\n]+)", re.I),
        re.compile(r"file_path\s*[=:]\s*([^\r\n]+)", re.I),
        re.compile(r"图片路径[是为：:]\s*([^\r\n]+)", re.I),
    )
    for pattern in explicit_patterns:
        match = pattern.search(text)
        if not match:
            continue
        segment = clean_token(match.group(1))
        found = try_existing_path(segment)
        if found:
            return found
        for candidate in iter_candidate_paths(segment):
            found = try_existing_path(candidate)
            if found:
                return found

    for candidate in iter_candidate_paths(text):
        found = try_existing_path(candidate)
        if found:
            return found
    return None


def wants_json(text):
    text = str(text or "")
    return bool(re.search(r"(^|\s)--json(\s|$)|\bjson输出\b|\b返回json\b|\bjson格式\b|\b结构化\b", text, re.I))


def wants_table(text):
    text = str(text or "")
    return bool(re.search(r"(^|\s)--table(\s|$)|表格|markdown table|markdown表格|csv", text, re.I))


def resolve_input(argv):
    positional = list(argv or [])
    raw_text = " ".join(positional)

    for arg in positional:
        found = try_existing_path(arg)
        if found:
            return found, wants_json(raw_text), wants_table(raw_text)

    for arg in positional:
        if arg in {"<用户原话>", "{input}", "{{input}}", "{user_prompt}", "{{user_prompt}}"}:
            continue
        found = extract_image_path_from_text(arg)
        if found:
            return found, wants_json(raw_text), wants_table(raw_text)

    env_texts = [
        os.environ.get("SKILL_ARGS"),
        os.environ.get("SKILL_INPUT"),
        os.environ.get("SKILL_USER_PROMPT"),
        os.environ.get("INPUT"),
        os.environ.get("USER_PROMPT"),
        os.environ.get("ARGS"),
        os.environ.get("ARGUMENTS"),
        os.environ.get("PROMPT"),
    ]
    combined = raw_text or " ".join(filter(None, env_texts))
    for text in filter(None, env_texts):
        found = extract_image_path_from_text(text)
        if found:
            return found, wants_json(combined), wants_table(combined)

    return None, wants_json(raw_text), wants_table(raw_text)


def uv_tool_python():
    uv = shutil.which("uv")
    if not uv:
        return None
    try:
        result = subprocess.run([uv, "tool", "dir"], text=True, capture_output=True, check=False)
    except Exception:
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    tool_dir = result.stdout.strip().splitlines()[0]
    candidate = (
        os.path.join(tool_dir, "rapidocr", "Scripts", "python.exe")
        if os.name == "nt"
        else os.path.join(tool_dir, "rapidocr", "bin", "python")
    )
    return candidate if os.path.exists(candidate) else None


def reexec_with_uv_tool_if_available():
    candidate = uv_tool_python()
    if not candidate:
        return False
    try:
        if os.path.samefile(candidate, sys.executable):
            return False
    except Exception:
        if os.path.abspath(candidate) == os.path.abspath(sys.executable):
            return False
    os.execv(candidate, [candidate, os.path.abspath(__file__), *sys.argv[1:]])
    return True


def box_to_list(box):
    if box is None:
        return None
    try:
        return box.tolist()
    except Exception:
        return box


def box_center(box):
    if box is None:
        return 0.0, 0.0
    pts = box_to_list(box) or []
    if not pts:
        return 0.0, 0.0
    xs = [float(p[0]) for p in pts if len(p) >= 2]
    ys = [float(p[1]) for p in pts if len(p) >= 2]
    return (sum(xs) / len(xs) if xs else 0.0, sum(ys) / len(ys) if ys else 0.0)


def normalize_result(result, img_path):
    lines = []
    boxes = []
    scores = []

    if result is None:
        return {"text": "", "lines": [], "boxes": [], "scores": [], "items": [], "source": img_path}

    if hasattr(result, "txts") and result.txts:
        lines = [str(x) for x in result.txts]

    if hasattr(result, "scores") and result.scores:
        try:
            scores = [float(x) for x in result.scores]
        except Exception:
            scores = [str(x) for x in result.scores]

    if hasattr(result, "boxes") and result.boxes is not None:
        try:
            boxes = result.boxes.tolist()
        except Exception:
            boxes = []

    if not lines and isinstance(result, (list, tuple)):
        for item in result:
            if not isinstance(item, (list, tuple)) or len(item) < 2:
                continue
            if item and isinstance(item[0], (list, tuple)):
                boxes.append(item[0])
            lines.append(str(item[1]))
            if len(item) >= 3:
                try:
                    scores.append(float(item[2]))
                except Exception:
                    scores.append(str(item[2]))

    items = []
    for idx, line in enumerate(lines):
        box = boxes[idx] if idx < len(boxes) else None
        score = scores[idx] if idx < len(scores) else None
        cx, cy = box_center(box)
        items.append({
            "index": idx,
            "text": line,
            "box": box,
            "score": score,
            "center": [cx, cy],
        })

    return {
        "text": "\n".join(lines),
        "lines": lines,
        "boxes": boxes,
        "scores": scores,
        "items": items,
        "source": img_path,
    }


def analyze_warnings(items):
    low_confidence = []
    amount_like = []
    for item in items:
        text = item.get("text", "")
        score = item.get("score")
        if isinstance(score, (int, float)) and score < LOW_CONF_THRESHOLD:
            low_confidence.append({
                "index": item["index"],
                "text": text,
                "score": round(float(score), 4),
            })
        if AMOUNT_RE.search(text):
            amount_like.append({
                "index": item["index"],
                "text": text,
                "score": round(float(score), 4) if isinstance(score, (int, float)) else score,
            })
    return {
        "low_confidence": low_confidence,
        "amount_like": amount_like,
        "needs_review": bool(low_confidence or amount_like),
    }


def cluster_rows(items):
    positioned = [item for item in items if item.get("box")]
    if not positioned:
        return []
    positioned.sort(key=lambda x: (x["center"][1], x["center"][0]))
    heights = []
    for item in positioned:
        pts = item.get("box") or []
        ys = [float(p[1]) for p in pts if len(p) >= 2]
        if ys:
            heights.append(max(ys) - min(ys))
    threshold = max(12.0, (sum(heights) / len(heights) if heights else 18.0) * 0.7)
    rows = []
    for item in positioned:
        y = item["center"][1]
        if not rows or abs(rows[-1]["y"] - y) > threshold:
            rows.append({"y": y, "items": [item]})
        else:
            row = rows[-1]
            row["items"].append(item)
            row["y"] = sum(x["center"][1] for x in row["items"]) / len(row["items"])
    for row in rows:
        row["items"].sort(key=lambda x: x["center"][0])
    return rows


def maybe_markdown_table(items):
    rows = cluster_rows(items)
    if len(rows) < 2:
        return None
    col_count = max(len(row["items"]) for row in rows)
    tableish_rows = [row for row in rows if len(row["items"]) >= 2]
    if col_count < 2 or len(tableish_rows) < 2:
        return None

    # Conservative layout reconstruction: keep row order, split cells by detected boxes.
    normalized = []
    for row in rows:
        cells = [cell["text"].replace("|", "\\|") for cell in row["items"]]
        if len(cells) == 1 and col_count > 2:
            normalized.append(cells)
        else:
            normalized.append(cells + [""] * (col_count - len(cells)))

    header = normalized[0]
    sep = ["---"] * len(header)
    body = normalized[1:]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return {
        "markdown": "\n".join(lines),
        "row_count": len(rows),
        "max_columns": col_count,
        "note": "Heuristic layout reconstruction from OCR boxes; verify table structure before using as source of truth.",
    }


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Run RapidOCR on a local image path.", add_help=True)
    parser.add_argument("input", nargs="*", help="Image path or natural-language request containing an image path")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON")
    parser.add_argument("--table", action="store_true", help="Include heuristic Markdown table reconstruction")
    return parser.parse_args(argv)


def main():
    args = parse_args(sys.argv[1:])
    img_path, json_mode_from_text, table_from_text = resolve_input(args.input)
    json_mode = args.json or json_mode_from_text
    table_mode = args.table or table_from_text
    if not img_path:
        print("Missing local image path.", file=sys.stderr)
        sys.exit(2)

    warnings.filterwarnings("ignore")
    for name in ["RapidOCR", "rapidocr", "onnxruntime"]:
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = False
        logger.setLevel(logging.CRITICAL)
    logging.disable(logging.CRITICAL)

    try:
        from rapidocr import RapidOCR
    except ImportError:
        reexec_with_uv_tool_if_available()
        print(
            "RapidOCR is not installed. Run: uv tool install --force rapidocr --with onnxruntime",
            file=sys.stderr,
        )
        sys.exit(1)

    engine = RapidOCR()
    output = normalize_result(engine(img_path), img_path)
    output["review"] = analyze_warnings(output.get("items") or [])
    if table_mode:
        output["table"] = maybe_markdown_table(output.get("items") or [])

    if json_mode:
        print(json.dumps(output, ensure_ascii=False))
        return

    print(output["text"])
    review = output.get("review") or {}
    if review.get("needs_review"):
        print("\n[Review hints]", file=sys.stderr)
        for item in review.get("low_confidence") or []:
            print(f"low confidence #{item['index']} score={item['score']}: {item['text']}", file=sys.stderr)
        for item in review.get("amount_like") or []:
            print(f"amount-like #{item['index']} score={item['score']}: {item['text']}", file=sys.stderr)
    if table_mode and output.get("table"):
        print("\n[Markdown table]\n" + output["table"]["markdown"])


if __name__ == "__main__":
    main()
