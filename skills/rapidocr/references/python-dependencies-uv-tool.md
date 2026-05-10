# RapidOCR Python dependencies via uv tool

Python CLI/tool dependencies for this skill are installed with `uv tool`.

## Install / reinstall

```bash
uv tool install --force rapidocr --with onnxruntime
```

Observed local result on macOS:

- Tool environment: `$(uv tool dir)/rapidocr`
- Python interpreter: `$(uv tool dir)/rapidocr/bin/python`
- Installed executable: `rapidocr`

## Use with the skill

```bash
python3 "$SKILL_DIR/scripts/run_rapidocr.py" /absolute/path/to/image.png --json
```

The script tries the current interpreter first. If `rapidocr` is missing, it re-execs through the uv-managed interpreter:

- macOS/Linux: `$(uv tool dir)/rapidocr/bin/python`
- Windows: `$(uv tool dir)/rapidocr/Scripts/python.exe`

## Pitfall

Installing the packages into system Python may make a one-off import work, but it makes the skill depend on whichever Python happens to be invoked. Use `uv tool`; the script handles uv tool fallback itself.
