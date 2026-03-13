#!/usr/bin/env python3
"""Direct Exa API wrapper used by the exa-tools skill."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API_BASE = "https://api.exa.ai"


def load_api_key() -> str:
    """Load Exa API key from environment or config file."""
    key = os.environ.get("EXA_API_KEY", "").strip()
    if key:
        return key

    key_file = Path.home() / ".config" / "exa" / "api_key"
    if key_file.exists():
        value = key_file.read_text(encoding="utf-8").strip()
        if value:
            return value

    raise SystemExit(
        "Missing Exa API key. Set EXA_API_KEY or write the key to ~/.config/exa/api_key."
    )


def exa_post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": load_api_key(),
            "User-Agent": "exa-tools-skill/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Exa API HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Exa API request failed: {exc}") from exc


def trim(text: str, limit: int = 300) -> str:
    """Truncate text to specified character limit, adding ellipsis if needed."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def summarize_search_results(results: list[dict[str, Any]]) -> str:
    """Generate human-readable summary of search results."""
    if not results:
        return "No results."

    lines: list[str] = []
    for idx, item in enumerate(results, start=1):
        title = item.get("title") or item.get("url") or f"Result {idx}"
        url = item.get("url", "")
        published = item.get("publishedDate") or item.get("published_date") or ""
        text = ""
        if isinstance(item.get("text"), str):
            text = item["text"]
        elif isinstance(item.get("highlights"), list):
            text = " ".join(str(x) for x in item["highlights"][:3])

        header = f"{idx}. {title}"
        if published:
            header += f" [{published}]"
        lines.append(header)
        if url:
            lines.append(f"   {url}")
        if text:
            lines.append(f"   {trim(text)}")
    return "\n".join(lines)


def command_web_search(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "query": args.query,
        "type": args.search_type,
        "numResults": args.num_results,
        "contents": {
            "text": {
                "maxCharacters": args.context_max_characters,
            }
        },
    }
    if args.livecrawl:
        payload["livecrawl"] = args.livecrawl
    response = exa_post("/search", payload)
    results = response.get("results", [])
    text_blocks: list[str] = []
    for item in results:
        title = item.get("title") or item.get("url") or "Untitled"
        url = item.get("url", "")
        text = trim(str(item.get("text", "")), args.context_max_characters)
        block = f"{title}\n{url}\n{text}".strip()
        text_blocks.append(block)
    return {
        "query": args.query,
        "type": args.search_type,
        "livecrawl": args.livecrawl,
        "numResults": args.num_results,
        "contextMaxCharacters": args.context_max_characters,
        "results": results,
        "content": "\n\n".join(text_blocks),
    }


def command_code_context(args: argparse.Namespace) -> dict[str, Any]:
    payload = {
        "query": args.query,
        "tokensNum": args.tokens_num,
    }
    if args.livecrawl:
        payload["livecrawl"] = args.livecrawl
    response = exa_post("/context", payload)
    context = response.get("response", "")
    if context:
        return {
            "query": args.query,
            "tokensNum": args.tokens_num,
            "source": "context",
            "context": context,
            "results": [],
        }

    fallback = exa_post(
        "/search",
        {
            "query": args.query,
            "numResults": 5,
            "type": "auto",
            "contents": {"text": {"maxCharacters": 1200}},
        },
    )
    results = fallback.get("results", [])
    snippets: list[str] = []
    for item in results:
        title = item.get("title") or item.get("url") or "Untitled"
        url = item.get("url", "")
        text = trim(str(item.get("text", "")), 800)
        block = f"{title}\n{url}\n{text}".strip()
        snippets.append(block)

    return {
        "query": args.query,
        "tokensNum": args.tokens_num,
        "source": "search_fallback",
        "context": "\n\n".join(snippets),
        "results": results,
    }


def command_company_research(args: argparse.Namespace) -> dict[str, Any]:
    """Search for company information with category filter."""
    response = exa_post(
        "/search",
        {
            "query": f"{args.company} company",
            "type": "auto",
            "category": "company",
            "numResults": args.num_results,
            "contents": {"text": {"maxCharacters": 7000}},
        }
    )
    return response


def print_human_readable(command: str, payload: dict[str, Any]) -> None:
    if command == "web-search":
        print(payload.get("content", "").strip())
    elif command == "code-context":
        print(payload.get("context", "").strip())
    elif command == "company-research":
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Exa API wrapper for the exa-tools skill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    web_search = subparsers.add_parser("web-search", help="Run Exa web research")
    web_search.add_argument("--query", required=True)
    web_search.add_argument("--num-results", "--numResults", dest="num_results", type=int, default=8)
    web_search.add_argument(
        "--context-max-characters",
        "--contextMaxCharacters",
        dest="context_max_characters",
        type=int,
        default=10000,
    )
    web_search.add_argument("--livecrawl", choices=["fallback", "preferred", "always", "never"], default="fallback")
    web_search.add_argument(
        "--type",
        dest="search_type",
        choices=["auto", "fast", "neural", "deep", "deep-reasoning", "instant"],
        default="auto",
    )
    web_search.add_argument("--json", action="store_true")

    code_context = subparsers.add_parser("code-context", help="Fetch technical/code context")
    code_context.add_argument("--query", required=True)
    code_context.add_argument("--tokens", "--tokens-num", "--tokensNum", dest="tokens_num", type=int, default=5000)
    code_context.add_argument("--livecrawl", choices=["fallback", "preferred", "always", "never"], default="")
    code_context.add_argument("--json", action="store_true")

    company = subparsers.add_parser("company-research", help="Research a company")
    company.add_argument("--company", "--company-name", "--companyName", dest="company", required=True)
    company.add_argument("--num-results", "--numResults", dest="num_results", type=int, default=3)
    company.add_argument("--json", action="store_true")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "web-search":
        payload = command_web_search(args)
    elif args.command == "code-context":
        payload = command_code_context(args)
    elif args.command == "company-research":
        payload = command_company_research(args)
    else:
        parser.error(f"Unsupported command: {args.command}")
        return

    if getattr(args, "json", False):
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return

    print_human_readable(args.command, payload)


if __name__ == "__main__":
    main()
