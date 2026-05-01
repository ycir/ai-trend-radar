from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from .models import TrendItem


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


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)
