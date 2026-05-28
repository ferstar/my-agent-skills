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


def configure_stdio() -> None:
    """Prefer UTF-8 console output so Windows shells do not choke on results."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="backslashreplace")
            except ValueError:
                pass


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


def apply_search_filters(
    payload: dict[str, Any],
    args: argparse.Namespace,
    *,
    include_dates: bool = False,
) -> None:
    """Apply common search filters shared by search-based commands."""
    if getattr(args, "include_domains", None):
        payload["includeDomains"] = args.include_domains
    if getattr(args, "exclude_domains", None):
        payload["excludeDomains"] = args.exclude_domains
    if include_dates:
        if getattr(args, "start_published_date", ""):
            payload["startPublishedDate"] = args.start_published_date
        if getattr(args, "end_published_date", ""):
            payload["endPublishedDate"] = args.end_published_date


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
    if args.max_age_hours is not None and args.livecrawl:
        raise SystemExit(
            "Cannot use --livecrawl with --maxAgeHours. Prefer --maxAgeHours."
        )

    contents: dict[str, Any] = {
        "text": {
            "maxCharacters": args.context_max_characters,
        }
    }
    if args.livecrawl:
        contents["livecrawl"] = args.livecrawl
    if args.livecrawl_timeout is not None:
        contents["livecrawlTimeout"] = args.livecrawl_timeout
    if args.max_age_hours is not None:
        contents["maxAgeHours"] = args.max_age_hours

    payload: dict[str, Any] = {
        "query": args.query,
        "type": args.search_type,
        "numResults": args.num_results,
        "contents": contents,
    }
    apply_search_filters(payload, args, include_dates=True)
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
        "livecrawlTimeout": args.livecrawl_timeout,
        "maxAgeHours": args.max_age_hours,
        "numResults": args.num_results,
        "includeDomains": args.include_domains,
        "excludeDomains": args.exclude_domains,
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
            **(
                {"includeDomains": args.include_domains}
                if args.include_domains
                else {}
            ),
            **(
                {"excludeDomains": args.exclude_domains}
                if args.exclude_domains
                else {}
            ),
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
        "includeDomains": args.include_domains,
        "excludeDomains": args.exclude_domains,
        "results": results,
    }


def command_answer(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "query": args.query,
        "text": args.text,
    }
    if args.include_domains:
        payload["includeDomains"] = args.include_domains
    if args.exclude_domains:
        payload["excludeDomains"] = args.exclude_domains
    response = exa_post("/answer", payload)
    response["query"] = args.query
    response["text"] = args.text
    response["includeDomains"] = args.include_domains
    response["excludeDomains"] = args.exclude_domains
    return response


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
    elif command == "answer":
        answer = str(payload.get("answer", "")).strip()
        citations = payload.get("citations", [])
        print(answer)
        if citations:
            print("\nSources:")
            for idx, item in enumerate(citations, start=1):
                title = item.get("title") or item.get("url") or f"Result {idx}"
                url = item.get("url", "")
                published = item.get("publishedDate") or item.get("published_date") or ""
                header = f"{idx}. {title}"
                if published:
                    header += f" [{published}]"
                print(header)
                if url:
                    print(url)
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
    web_search.add_argument("--livecrawl", choices=["fallback", "preferred", "always", "never"], default="")
    web_search.add_argument("--livecrawl-timeout", "--livecrawlTimeout", dest="livecrawl_timeout", type=int)
    web_search.add_argument("--max-age-hours", "--maxAgeHours", dest="max_age_hours", type=int)
    web_search.add_argument("--include-domain", dest="include_domains", action="append", default=[])
    web_search.add_argument("--exclude-domain", dest="exclude_domains", action="append", default=[])
    web_search.add_argument("--start-published-date", dest="start_published_date", default="")
    web_search.add_argument("--end-published-date", dest="end_published_date", default="")
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
    code_context.add_argument("--include-domain", dest="include_domains", action="append", default=[])
    code_context.add_argument("--exclude-domain", dest="exclude_domains", action="append", default=[])
    code_context.add_argument("--json", action="store_true")

    answer = subparsers.add_parser("answer", help="Get a synthesized answer with citations")
    answer.add_argument("--query", required=True)
    answer.add_argument("--include-domain", dest="include_domains", action="append", default=[])
    answer.add_argument("--exclude-domain", dest="exclude_domains", action="append", default=[])
    answer.add_argument("--text", action="store_true")
    answer.add_argument("--json", action="store_true")

    company = subparsers.add_parser("company-research", help="Research a company")
    company.add_argument("--company", "--company-name", "--companyName", dest="company", required=True)
    company.add_argument("--num-results", "--numResults", dest="num_results", type=int, default=3)
    company.add_argument("--json", action="store_true")

    return parser


def main() -> None:
    configure_stdio()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "web-search":
        payload = command_web_search(args)
    elif args.command == "code-context":
        payload = command_code_context(args)
    elif args.command == "answer":
        payload = command_answer(args)
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
