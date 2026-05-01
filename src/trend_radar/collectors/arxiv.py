from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime

from trend_radar.http import HttpClient
from trend_radar.models import TrendItem


ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"


def collect_arxiv(
    client: HttpClient,
    days: int,
    limit: int,
    keywords: list[str],
) -> list[TrendItem]:
    terms = " OR ".join(f'all:"{keyword}"' for keyword in keywords[:8])
    raw = client.get_text(
        "https://export.arxiv.org/api/query",
        headers={"Accept": "application/atom+xml"},
        params={
            "search_query": terms,
            "start": 0,
            "max_results": limit,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        },
    )
    root = ET.fromstring(raw)

    items: list[TrendItem] = []
    for entry in root.findall(f"{ATOM}entry"):
        title = _text(entry, f"{ATOM}title")
        summary = " ".join(_text(entry, f"{ATOM}summary").split())
        published = _parse_dt(_text(entry, f"{ATOM}published"))
        url = _text(entry, f"{ATOM}id")
        categories = [
            category.attrib.get("term", "")
            for category in entry.findall(f"{ATOM}category")
            if category.attrib.get("term")
        ]
        authors = [
            _text(author, f"{ATOM}name")
            for author in entry.findall(f"{ATOM}author")
            if _text(author, f"{ATOM}name")
        ]
        items.append(
            TrendItem(
                source="arxiv",
                item_type="paper",
                title=" ".join(title.split()),
                url=url,
                description=summary[:500],
                created_at=published,
                tags=categories,
                metrics={"authors": len(authors)},
                metadata={"authors": authors[:8]},
            )
        )
    return items[:limit]


def _text(node: ET.Element, path: str) -> str:
    found = node.find(path)
    return found.text.strip() if found is not None and found.text else ""


def _parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
