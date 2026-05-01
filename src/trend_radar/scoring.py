from __future__ import annotations

import math
from datetime import datetime, timezone

from .models import TrendItem


SOURCE_WEIGHTS = {
    "github": 1.0,
    "huggingface": 0.92,
    "hackernews": 0.82,
    "arxiv": 0.68,
}


def score_items(items: list[TrendItem], days: int) -> list[TrendItem]:
    now = datetime.now(timezone.utc)
    for item in items:
        score = 0.0
        reasons: list[str] = []

        age_days = None
        if item.created_at:
            age_seconds = max(0.0, (now - item.created_at).total_seconds())
            age_days = max(age_seconds / 86400, 0.05)
            freshness = max(0.0, 1.0 - min(age_days, days * 1.5) / max(days * 1.5, 1))
            score += 20 * freshness
            if age_days <= 2:
                reasons.append("very fresh")
            elif age_days <= 7:
                reasons.append("new this week")

        metric_score, metric_reasons = _metric_score(item)
        score += metric_score
        reasons.extend(metric_reasons)

        if item.source in {"github", "huggingface", "hackernews"} and metric_score <= 0:
            score -= 8
            reasons.append("no engagement yet")

        keyword_hits = _keyword_hits(item)
        if keyword_hits:
            score += min(15, 3 * len(keyword_hits))
            reasons.append("AI keywords: " + ", ".join(keyword_hits[:4]))

        source_weight = SOURCE_WEIGHTS.get(item.source, 0.6)
        item.score = round(score * source_weight, 2)
        item.score_reasons = reasons[:5]

    return sorted(items, key=lambda value: value.score, reverse=True)


def _metric_score(item: TrendItem) -> tuple[float, list[str]]:
    metrics = item.metrics
    score = 0.0
    reasons: list[str] = []

    stars = _number(metrics.get("stars"))
    forks = _number(metrics.get("forks"))
    likes = _number(metrics.get("likes"))
    downloads = _number(metrics.get("downloads"))
    points = _number(metrics.get("points"))
    comments = _number(metrics.get("comments"))

    if stars:
        score += min(42, 7 * math.log10(stars + 1))
        reasons.append(f"{int(stars)} stars")
    if forks:
        score += min(16, 4 * math.log10(forks + 1))
        reasons.append(f"{int(forks)} forks")
    if likes:
        score += min(32, 6 * math.log10(likes + 1))
        reasons.append(f"{int(likes)} HF likes")
    if downloads:
        score += min(20, 3 * math.log10(downloads + 1))
        reasons.append(f"{int(downloads)} downloads")
    if points:
        score += min(28, 6 * math.log10(points + 1))
        reasons.append(f"{int(points)} HN points")
    if comments:
        score += min(18, 5 * math.log10(comments + 1))
        reasons.append(f"{int(comments)} comments")

    if item.item_type == "paper":
        score += 10
        reasons.append("recent paper")

    return score, reasons


def _number(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _keyword_hits(item: TrendItem) -> list[str]:
    haystack = " ".join([item.title, item.description, " ".join(item.tags)]).lower()
    keywords = [
        "agent",
        "llm",
        "rag",
        "mcp",
        "inference",
        "eval",
        "reasoning",
        "multimodal",
        "voice",
        "coding",
        "video",
    ]
    return [keyword for keyword in keywords if keyword in haystack]
