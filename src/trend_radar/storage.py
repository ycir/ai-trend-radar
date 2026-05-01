from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import TrendItem


GROWTH_METRICS = ("stars", "forks", "watchers", "likes", "downloads", "points", "comments")


def init_db(path: str) -> None:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trend_items (
                item_key TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                item_type TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT,
                created_at TEXT,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                metrics_json TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                score REAL NOT NULL,
                score_reasons_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metric_snapshots (
                item_key TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                metrics_json TEXT NOT NULL,
                score REAL NOT NULL,
                PRIMARY KEY (item_key, fetched_at)
            )
            """
        )


def save_items(path: str, items: list[TrendItem]) -> None:
    init_db(path)
    with sqlite3.connect(path) as conn:
        for item in items:
            existing = conn.execute(
                "SELECT first_seen_at FROM trend_items WHERE item_key = ?",
                (item.key,),
            ).fetchone()
            first_seen_at = existing[0] if existing else item.fetched_at.isoformat()
            conn.execute(
                """
                INSERT OR REPLACE INTO trend_items (
                    item_key, source, item_type, title, url, description,
                    created_at, first_seen_at, last_seen_at, tags_json,
                    metrics_json, metadata_json, score, score_reasons_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.key,
                    item.source,
                    item.item_type,
                    item.title,
                    item.url,
                    item.description,
                    item.created_at.isoformat() if item.created_at else None,
                    first_seen_at,
                    item.fetched_at.isoformat(),
                    json.dumps(item.tags, ensure_ascii=False),
                    json.dumps(item.metrics, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                    item.score,
                    json.dumps(item.score_reasons, ensure_ascii=False),
                ),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO metric_snapshots (
                    item_key, fetched_at, metrics_json, score
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    item.key,
                    item.fetched_at.isoformat(),
                    json.dumps(item.metrics, ensure_ascii=False),
                    item.score,
                ),
            )


def annotate_growth(path: str, items: list[TrendItem]) -> list[TrendItem]:
    init_db(path)
    with sqlite3.connect(path) as conn:
        for item in items:
            row = conn.execute(
                """
                SELECT fetched_at, metrics_json, score
                FROM metric_snapshots
                WHERE item_key = ?
                ORDER BY fetched_at DESC
                LIMIT 1
                """,
                (item.key,),
            ).fetchone()
            if not row:
                continue

            previous_at, metrics_json, previous_score = row
            previous_metrics = json.loads(metrics_json)
            item.metadata["previous_metrics_at"] = previous_at
            item.metadata["previous_score"] = previous_score

            for metric in GROWTH_METRICS:
                current = _number(item.metrics.get(metric))
                previous = _number(previous_metrics.get(metric))
                if current is None or previous is None:
                    continue
                delta = current - previous
                item.metrics[f"{metric}_delta"] = int(delta) if float(delta).is_integer() else round(delta, 2)
                if previous > 0:
                    item.metrics[f"{metric}_growth_pct"] = round((delta / previous) * 100, 2)

            item.metrics["snapshot_age_hours"] = _snapshot_age_hours(previous_at, item.fetched_at)
    return items


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _snapshot_age_hours(previous_at: str, current_at: datetime) -> float:
    previous = parse_datetime(previous_at)
    if not previous:
        return 0.0
    if previous.tzinfo is None:
        previous = previous.replace(tzinfo=timezone.utc)
    current = current_at if current_at.tzinfo else current_at.replace(tzinfo=timezone.utc)
    return round(max(0.0, (current - previous).total_seconds() / 3600), 2)
