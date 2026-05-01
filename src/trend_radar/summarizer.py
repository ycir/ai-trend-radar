from __future__ import annotations

import json

from .http import HttpClient
from .models import TrendItem


def add_llm_summaries(
    items: list[TrendItem],
    api_key: str | None,
    model: str,
    limit: int = 8,
) -> list[TrendItem]:
    if not api_key:
        print("summaries: skipped because OPENAI_API_KEY is not set")
        return items

    selected = items[: max(1, limit)]
    if not selected:
        return items

    client = HttpClient(timeout=45)
    prompt = _build_prompt(selected)
    payload = {
        "model": model,
        "input": prompt,
        "max_output_tokens": 1800,
    }
    response = client.post_json(
        "https://api.openai.com/v1/responses",
        payload=payload,
        headers={"Authorization": f"Bearer {api_key}"},
    )
    summaries = _parse_summaries(response)
    if not summaries:
        print("summaries: model returned no parseable summaries")
        return items

    by_url = {summary.get("url"): summary for summary in summaries if summary.get("url")}
    for item in items:
        summary = by_url.get(item.url)
        if summary:
            item.metadata["llm_summary"] = {
                "what": summary.get("what", ""),
                "why": summary.get("why", ""),
                "risk": summary.get("risk", ""),
            }
    print(f"summaries: added {len(by_url)} summaries")
    return items


def _build_prompt(items: list[TrendItem]) -> str:
    compact_items = []
    for item in items:
        compact_items.append(
            {
                "title": item.title,
                "url": item.url,
                "source": item.source,
                "type": item.item_type,
                "description": item.description[:700],
                "tags": item.tags[:10],
                "metrics": item.metrics,
                "score_reasons": item.score_reasons,
            }
        )

    return (
        "You are an AI industry trend analyst. Summarize each item for a concise trend radar report. "
        "Return strict JSON only, with this shape: "
        "{\"items\":[{\"url\":\"...\",\"what\":\"...\",\"why\":\"...\",\"risk\":\"...\"}]}. "
        "Use short, practical English. Do not invent facts beyond the provided data. "
        "Keep each field under 30 words.\n\n"
        f"Items:\n{json.dumps(compact_items, ensure_ascii=False)}"
    )


def _parse_summaries(response: dict) -> list[dict]:
    text = response.get("output_text") or _extract_output_text(response)
    if not text:
        return []
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.removeprefix("json").strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []
    items = payload.get("items")
    return items if isinstance(items, list) else []


def _extract_output_text(response: dict) -> str:
    parts: list[str] = []
    for output in response.get("output", []):
        for content in output.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                parts.append(content["text"])
    return "\n".join(parts)
