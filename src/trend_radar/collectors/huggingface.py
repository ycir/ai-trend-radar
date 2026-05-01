from __future__ import annotations

from datetime import datetime, timedelta, timezone

from trend_radar.http import HttpClient
from trend_radar.models import TrendItem


def collect_huggingface(
    client: HttpClient,
    days: int,
    limit: int,
    keywords: list[str],
    token: str | None = None,
) -> list[TrendItem]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    items: dict[str, TrendItem] = {}
    since = datetime.now(timezone.utc) - timedelta(days=days)

    search_terms = [keyword for keyword in keywords if keyword.lower() not in {"ai"}]
    for keyword in search_terms[:8]:
        models = client.get_json(
            "https://huggingface.co/api/models",
            headers=headers,
            params={
                "search": keyword,
                "sort": "createdAt",
                "direction": "-1",
                "limit": max(5, limit),
                "full": "true",
            },
        )
        for model in models:
            item = _model_to_item(model)
            if item.created_at and item.created_at < since:
                continue
            if not _looks_relevant(item, keyword):
                continue
            items[item.key] = item
            if len(items) >= limit:
                break
        if len(items) >= limit:
            break
    return list(items.values())


def _model_to_item(model: dict) -> TrendItem:
    model_id = model.get("modelId") or model.get("id") or "unknown/model"
    created_at = _parse_dt(model.get("createdAt") or model.get("lastModified"))
    tags = [tag for tag in model.get("tags", []) if isinstance(tag, str)]
    return TrendItem(
        source="huggingface",
        item_type="model",
        title=model_id,
        url=f"https://huggingface.co/{model_id}",
        description=_short_description(tags),
        created_at=created_at,
        tags=tags,
        metrics={
            "likes": model.get("likes") or 0,
            "downloads": model.get("downloads") or 0,
        },
        metadata={
            "pipeline_tag": model.get("pipeline_tag"),
            "library_name": model.get("library_name"),
        },
    )


def _looks_relevant(item: TrendItem, keyword: str) -> bool:
    model_name = item.title.split("/")[-1]
    haystack = " ".join([model_name, item.description, " ".join(item.tags)]).lower()
    return keyword.lower() in haystack or bool(item.metrics.get("likes")) or bool(item.metrics.get("downloads"))


def _short_description(tags: list[str]) -> str:
    important = [tag for tag in tags if tag and not tag.startswith("region:")]
    return "Hugging Face model tagged: " + ", ".join(important[:8]) if important else ""


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
