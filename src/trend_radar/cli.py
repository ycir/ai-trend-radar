from __future__ import annotations

import argparse
import os
from pathlib import Path

from .collectors import collect_arxiv, collect_github, collect_hackernews, collect_huggingface
from .http import HttpClient
from .models import RunConfig, TrendItem
from .report import write_reports
from .sample_data import sample_items
from .scoring import score_items
from .storage import save_items


DEFAULT_KEYWORDS = [
    "ai",
    "llm",
    "agent",
    "rag",
    "mcp",
    "inference",
    "eval",
    "reasoning",
    "multimodal",
    "coding agent",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate an AI tools and projects trend radar report.")
    parser.add_argument("--days", type=int, default=1, help="Trend window: 1, 7, or 30 days.")
    parser.add_argument("--limit", type=int, default=25, help="Maximum items per source.")
    parser.add_argument("--output-dir", default="reports", help="Directory for HTML and Markdown reports.")
    parser.add_argument("--db", default="data/trends.sqlite3", help="SQLite database path.")
    parser.add_argument("--offline", action="store_true", help="Use bundled sample data instead of network APIs.")
    parser.add_argument(
        "--keywords",
        default=",".join(DEFAULT_KEYWORDS),
        help="Comma-separated discovery keywords.",
    )
    args = parser.parse_args(argv)

    config = RunConfig(
        days=max(1, args.days),
        limit_per_source=max(1, args.limit),
        output_dir=args.output_dir,
        db_path=args.db,
        keywords=[part.strip() for part in args.keywords.split(",") if part.strip()],
        offline=args.offline,
        github_token=os.getenv("GITHUB_TOKEN"),
        hf_token=os.getenv("HF_TOKEN"),
    )

    items = run(config)
    if not items:
        print("No items found. Try a larger --days window or broader --keywords.")
        return 1

    ranked = score_items(items, config.days)
    save_items(config.db_path, ranked)
    md_path, html_path = write_reports(ranked, config.output_dir, config.days)
    print(f"Saved {len(ranked)} items")
    print(f"Markdown: {Path(md_path).resolve()}")
    print(f"HTML: {Path(html_path).resolve()}")
    return 0


def run(config: RunConfig) -> list[TrendItem]:
    if config.offline:
        return sample_items()

    client = HttpClient()
    collectors = [
        ("github", lambda: collect_github(client, config.days, config.limit_per_source, config.keywords, config.github_token)),
        ("huggingface", lambda: collect_huggingface(client, config.days, config.limit_per_source, config.keywords, config.hf_token)),
        ("hackernews", lambda: collect_hackernews(client, config.days, config.limit_per_source, config.keywords)),
        ("arxiv", lambda: collect_arxiv(client, config.days, config.limit_per_source, config.keywords)),
    ]

    items: list[TrendItem] = []
    for name, collector in collectors:
        try:
            collected = collector()
            print(f"{name}: collected {len(collected)} items")
            items.extend(collected)
        except Exception as exc:
            print(f"{name}: skipped after error: {exc}")
    return _dedupe(items)


def _dedupe(items: list[TrendItem]) -> list[TrendItem]:
    deduped: dict[str, TrendItem] = {}
    for item in items:
        if item.url:
            deduped[item.key] = item
    return list(deduped.values())
