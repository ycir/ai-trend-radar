from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class TrendItem:
    source: str
    item_type: str
    title: str
    url: str
    description: str = ""
    created_at: datetime | None = None
    fetched_at: datetime = field(default_factory=utc_now)
    tags: list[str] = field(default_factory=list)
    metrics: dict[str, float | int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    score_reasons: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{self.source}:{self.url}".lower()


@dataclass(slots=True)
class RunConfig:
    days: int
    limit_per_source: int
    output_dir: str
    db_path: str
    keywords: list[str]
    offline: bool = False
    github_token: str | None = None
    hf_token: str | None = None
