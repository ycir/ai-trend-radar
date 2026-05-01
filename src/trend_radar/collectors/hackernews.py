from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from trend_radar.http import HttpClient
from trend_radar.models import TrendItem


def collect_hackernews(
    client: HttpClient,
    days: int,
    limit: int,
    keywords: list[str],
) -> list[TrendItem]:
    created_after = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    items: dict[str, TrendItem] = {}
    for keyword in keywords[:8]:
        payload = client.get_json(
            "https://hn.algolia.com/api/v1/search_by_date",
            params={
                "query": keyword,
                "tags": "story",
                "numericFilters": f"created_at_i>{created_after}",
                "hitsPerPage": max(5, limit),
            },
        )
        for hit in payload.get("hits", []):
            item = _hit_to_item(hit)
            if not _looks_relevant(item, keyword):
                continue
            items[item.key] = item
            if len(items) >= limit:
                break
        if len(items) >= limit:
            break
    return list(items.values())


def _hit_to_item(hit: dict) -> TrendItem:
    url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
    created_at = datetime.fromtimestamp(hit.get("created_at_i", 0), tz=timezone.utc)
    return TrendItem(
        source="hackernews",
        item_type="discussion",
        title=hit.get("title") or hit.get("story_title") or "Untitled HN story",
        url=url,
        description=f"HN discussion with {hit.get('num_comments') or 0} comments.",
        created_at=created_at,
        tags=["hacker-news"],
        metrics={
            "points": hit.get("points") or 0,
            "comments": hit.get("num_comments") or 0,
        },
        metadata={"hn_id": hit.get("objectID")},
    )


def _looks_relevant(item: TrendItem, keyword: str) -> bool:
    haystack = " ".join([item.title, item.url, item.description]).lower()
    normalized = keyword.lower()
    if len(normalized) <= 3:
        return bool(re.search(rf"\b{re.escape(normalized)}\b", haystack))
    return normalized in haystack
